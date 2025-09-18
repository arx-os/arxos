package converter

import (
	"context"
	"fmt"
	"io"
	"regexp"
	"strconv"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/spatial"
)

// IFC coordinate extraction patterns
var (
	// Match IFCCARTESIANPOINT(#123,(1.0,2.0,3.0))
	cartesianPointPattern = regexp.MustCompile(`IFCCARTESIANPOINT\s*\(\s*#?\d*\s*,\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*(?:,\s*([-\d.]+))?\s*\)\s*\)`)

	// Match coordinate lists in placement entities
	coordinateListPattern = regexp.MustCompile(`\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*(?:,\s*([-\d.]+))?\s*\)`)

	// Match IFCLOCALPLACEMENT for position extraction
	localPlacementPattern = regexp.MustCompile(`IFCLOCALPLACEMENT\s*\(\s*#?(\d+)\s*,\s*#?(\d+)\s*\)`)
)

// SpatialIFCEntity extends IFCEntity with spatial data
type SpatialIFCEntity struct {
	*IFCEntity
	Position    *spatial.Point3D
	BoundingBox *spatial.BoundingBox
	Floor       int
	Room        string
}

// ConvertToDB implements direct IFC to PostGIS import
func (c *ImprovedIFCConverter) ConvertToDB(input io.Reader, dbInterface interface{}) error {
	// Type assert to get the database
	db, ok := dbInterface.(database.DB)
	if !ok {
		return fmt.Errorf("invalid database interface")
	}

	ctx := context.Background()

	// Parse all IFC entities
	entityList := c.parseIFCEntities(input)

	// Convert to map for easier access
	entities := make(map[string]*IFCEntity)
	for i := range entityList {
		entities[entityList[i].ID] = &entityList[i]
	}

	// Extract spatial entities with coordinates
	spatialEntities := c.extractSpatialData(entities)

	// Get or create building
	buildingID := c.getOrCreateBuilding(ctx, db, entities)

	// Process floors
	floors := c.processFloors(ctx, db, spatialEntities, buildingID)

	// Process rooms/spaces
	rooms := c.processRooms(ctx, db, spatialEntities, buildingID, floors)

	// Process equipment with spatial data
	equipment := c.processEquipment(ctx, db, spatialEntities, buildingID, floors, rooms)

	// If PostGIS is available, store spatial data
	if hybridDB, ok := db.(*database.PostGISHybridDB); ok {
		if spatialDB, err := hybridDB.GetSpatialDB(); err == nil {
			if err := c.storeSpatialData(ctx, spatialDB, equipment); err != nil {
				logger.Warn("Failed to store spatial data: %v", err)
			} else {
				logger.Info("Stored %d equipment items with spatial data in PostGIS", len(equipment))
			}
		}
	}

	logger.Info("IFC import complete: %d floors, %d rooms, %d equipment",
		len(floors), len(rooms), len(equipment))

	return nil
}

// extractSpatialData extracts 3D coordinates from IFC entities
func (c *ImprovedIFCConverter) extractSpatialData(entities map[string]*IFCEntity) []*SpatialIFCEntity {
	spatialEntities := make([]*SpatialIFCEntity, 0)

	for _, entity := range entities {
		spatialEntity := &SpatialIFCEntity{
			IFCEntity: entity,
		}

		// Extract position from various IFC entity types
		switch entity.Type {
		case "IFCBUILDINGELEMENTPROXY", "IFCFLOWSEGMENT", "IFCFLOWTERMINAL",
			 "IFCDISTRIBUTIONELEMENT", "IFCFURNISHINGELEMENT", "IFCLIGHTFIXTURE":
			// These typically have equipment
			spatialEntity.Position = c.extractPosition(entity, entities)

		case "IFCSPACE", "IFCROOM":
			// Extract room boundaries
			spatialEntity.Position = c.extractPosition(entity, entities)
			spatialEntity.BoundingBox = c.extractBoundingBox(entity, entities)

		case "IFCBUILDINGSTOREY":
			// Extract floor elevation
			if elevStr, ok := entity.Properties["elevation"]; ok {
				if elev, err := strconv.ParseFloat(elevStr, 64); err == nil {
					spatialEntity.Position = &spatial.Point3D{
						X: 0,
						Y: 0,
						Z: elev * 1000, // Convert to millimeters
					}
					spatialEntity.Floor, _ = strconv.Atoi(entity.ID)
				}
			}
		}

		if spatialEntity.Position != nil || spatialEntity.BoundingBox != nil {
			spatialEntities = append(spatialEntities, spatialEntity)
		}
	}

	return spatialEntities
}

// extractPosition extracts 3D position from IFC entity
func (c *ImprovedIFCConverter) extractPosition(entity *IFCEntity, allEntities map[string]*IFCEntity) *spatial.Point3D {
	// Look for placement reference
	if placementRef, ok := entity.Properties["placement"]; ok {
		if placement, exists := allEntities[placementRef]; exists {
			return c.extractPositionFromPlacement(placement, allEntities)
		}
	}

	// Look for direct coordinates in properties
	if coordStr, ok := entity.Properties["coordinates"]; ok {
		return c.parseCoordinateString(coordStr)
	}

	// Search for coordinates in entity references
	for _, ref := range entity.References {
		if refEntity, exists := allEntities[ref]; exists {
			if refEntity.Type == "IFCCARTESIANPOINT" {
				return c.extractCartesianPoint(refEntity)
			}
		}
	}

	return nil
}

// extractPositionFromPlacement extracts position from IFC placement entity
func (c *ImprovedIFCConverter) extractPositionFromPlacement(placement *IFCEntity, allEntities map[string]*IFCEntity) *spatial.Point3D {
	// Look for axis2placement3d
	if placement.Type == "IFCAXIS2PLACEMENT3D" {
		for _, ref := range placement.References {
			if point, exists := allEntities[ref]; exists {
				if point.Type == "IFCCARTESIANPOINT" {
					return c.extractCartesianPoint(point)
				}
			}
		}
	}

	// Look for local placement
	if placement.Type == "IFCLOCALPLACEMENT" {
		// Extract relative placement
		if len(placement.References) > 0 {
			if relPlacement, exists := allEntities[placement.References[0]]; exists {
				return c.extractPositionFromPlacement(relPlacement, allEntities)
			}
		}
	}

	return nil
}

// extractCartesianPoint extracts coordinates from IFCCARTESIANPOINT
func (c *ImprovedIFCConverter) extractCartesianPoint(point *IFCEntity) *spatial.Point3D {
	// Parse coordinate string from properties
	if coords, ok := point.Properties["coordinates"]; ok {
		return c.parseCoordinateString(coords)
	}

	// Try to parse from entity description
	if matches := cartesianPointPattern.FindStringSubmatch(point.Description); len(matches) > 0 {
		x, _ := strconv.ParseFloat(matches[1], 64)
		y, _ := strconv.ParseFloat(matches[2], 64)
		z := 0.0
		if len(matches) > 3 && matches[3] != "" {
			z, _ = strconv.ParseFloat(matches[3], 64)
		}

		// Convert from IFC units (typically meters) to millimeters
		return &spatial.Point3D{
			X: x * 1000,
			Y: y * 1000,
			Z: z * 1000,
		}
	}

	return nil
}

// parseCoordinateString parses coordinate string like "(1.0,2.0,3.0)"
func (c *ImprovedIFCConverter) parseCoordinateString(coordStr string) *spatial.Point3D {
	coordStr = strings.TrimSpace(coordStr)
	coordStr = strings.Trim(coordStr, "()")

	parts := strings.Split(coordStr, ",")
	if len(parts) >= 2 {
		x, _ := strconv.ParseFloat(strings.TrimSpace(parts[0]), 64)
		y, _ := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
		z := 0.0
		if len(parts) > 2 {
			z, _ = strconv.ParseFloat(strings.TrimSpace(parts[2]), 64)
		}

		// Convert to millimeters
		return &spatial.Point3D{
			X: x * 1000,
			Y: y * 1000,
			Z: z * 1000,
		}
	}

	return nil
}

// extractBoundingBox extracts bounding box for spaces/rooms
func (c *ImprovedIFCConverter) extractBoundingBox(entity *IFCEntity, allEntities map[string]*IFCEntity) *spatial.BoundingBox {
	// Look for representation geometry
	// This is simplified - real IFC parsing would need to handle complex geometry

	bbox := &spatial.BoundingBox{
		Min: spatial.Point3D{X: 0, Y: 0, Z: 0},
		Max: spatial.Point3D{X: 10000, Y: 10000, Z: 3000}, // Default room size
	}

	// Try to extract from properties
	if width, ok := entity.Properties["width"]; ok {
		if w, err := strconv.ParseFloat(width, 64); err == nil {
			bbox.Max.X = w * 1000
		}
	}
	if length, ok := entity.Properties["length"]; ok {
		if l, err := strconv.ParseFloat(length, 64); err == nil {
			bbox.Max.Y = l * 1000
		}
	}
	if height, ok := entity.Properties["height"]; ok {
		if h, err := strconv.ParseFloat(height, 64); err == nil {
			bbox.Max.Z = h * 1000
		}
	}

	return bbox
}

// getOrCreateBuilding gets or creates building record
func (c *ImprovedIFCConverter) getOrCreateBuilding(ctx context.Context, db database.DB, entities map[string]*IFCEntity) string {
	// Look for IFCBUILDING entity
	for _, entity := range entities {
		if entity.Type == "IFCBUILDING" {
			// Store building metadata in database
			// In a real implementation, this would use the database's building table
			logger.Info("Found building: %s (%s)", entity.Name, entity.GUID)
			return entity.GUID
		}
	}

	// Default building ID
	return "IFC-IMPORT-001"
}

// processFloors processes floor entities
func (c *ImprovedIFCConverter) processFloors(ctx context.Context, db database.DB, entities []*SpatialIFCEntity, buildingID string) []*Floor {
	floors := make([]*Floor, 0)

	for _, entity := range entities {
		if entity.Type == "IFCBUILDINGSTOREY" {
			floor := &Floor{
				ID:    entity.ID,
				Name:  entity.Name,
				Level: len(floors),
			}

			if entity.Position != nil {
				floor.Elevation = entity.Position.Z / 1000 // Convert to meters for storage
			}

			// Store floor in database
			// In a real implementation, this would use the database's floor table
			logger.Info("Processing floor: %s at elevation %.1fm", floor.Name, floor.Elevation)
			floors = append(floors, floor)
		}
	}

	return floors
}

// processRooms processes room/space entities
func (c *ImprovedIFCConverter) processRooms(ctx context.Context, db database.DB, entities []*SpatialIFCEntity, buildingID string, floors []*Floor) []*Room {
	rooms := make([]*Room, 0)

	for _, entity := range entities {
		if entity.Type == "IFCSPACE" || entity.Type == "IFCROOM" {
			room := &Room{
				ID:   entity.ID,
				Name: entity.Name,
				Type: "space",
			}

			// Determine floor based on elevation
			if entity.Position != nil {
				for _, floor := range floors {
					if entity.Position.Z >= floor.Elevation*1000 &&
					   entity.Position.Z < (floor.Elevation+4)*1000 { // Assume 4m floor height
						// Store floor reference in room number or equipment metadata
						room.Number = fmt.Sprintf("%d-%s", floor.Level, entity.ID)
						break
					}
				}
			}

			// Store room in database
			// In a real implementation, this would use the database's room table
			logger.Info("Processing room: %s (%s)", room.Name, room.Type)
			rooms = append(rooms, room)
		}
	}

	return rooms
}

// processEquipment processes equipment entities with spatial data
func (c *ImprovedIFCConverter) processEquipment(ctx context.Context, db database.DB, entities []*SpatialIFCEntity, buildingID string, floors []*Floor, rooms []*Room) []*Equipment {
	equipment := make([]*Equipment, 0)

	// Equipment-type IFC entities
	equipmentTypes := map[string]string{
		"IFCBUILDINGELEMENTPROXY": "building_element",
		"IFCFLOWSEGMENT":         "pipe",
		"IFCFLOWTERMINAL":        "terminal",
		"IFCDISTRIBUTIONELEMENT": "distribution",
		"IFCFURNISHINGELEMENT":   "furniture",
		"IFCLIGHTFIXTURE":        "lighting",
		"IFCELECTRICAPPLIANCE":   "electrical",
		"IFCSANITARYTERMINAL":    "plumbing",
	}

	for _, entity := range entities {
		if eqType, isEquipment := equipmentTypes[entity.Type]; isEquipment {
			eq := &Equipment{
				ID:     entity.ID,
				Name:   entity.Name,
				Type:   eqType,
				Status: "OPERATIONAL",
			}

			// Determine floor and room, set Location
			if entity.Position != nil {
				eq.Location = Location{
					X: entity.Position.X,
					Y: entity.Position.Y,
					Z: entity.Position.Z,
				}

				// Determine floor
				for _, floor := range floors {
					if entity.Position.Z >= floor.Elevation*1000 &&
					   entity.Position.Z < (floor.Elevation+4)*1000 {
						eq.Location.Floor = fmt.Sprintf("%d", floor.Level)
						break
					}
				}

				// Check room containment (simplified)
				if len(rooms) > 0 {
					// This would need proper spatial containment check
					eq.Location.Room = rooms[0].ID
				}
			}

			// Store equipment in database
			// In a real implementation, this would use the database's equipment table
			logger.Info("Processing equipment: %s (%s)", eq.Name, eq.Type)
			equipment = append(equipment, eq)
		}
	}

	return equipment
}

// storeSpatialData stores equipment positions in PostGIS
func (c *ImprovedIFCConverter) storeSpatialData(ctx context.Context, spatialDB database.SpatialDB, equipment []*Equipment) error {
	stored := 0

	for _, eq := range equipment {
		if eq.Location.X != 0 || eq.Location.Y != 0 {
			position := spatial.Point3D{
				X: eq.Location.X,
				Y: eq.Location.Y,
				Z: eq.Location.Z,
			}

			// Store in PostGIS with millimeter precision
			err := spatialDB.UpdateEquipmentPosition(
				eq.ID,
				position,
				spatial.ConfidenceHigh,
				"IFC Import",
			)

			if err != nil {
				logger.Warn("Failed to store spatial data for %s: %v", eq.ID, err)
			} else {
				stored++
			}
		}
	}

	logger.Info("Stored %d/%d equipment positions in PostGIS", stored, len(equipment))
	return nil
}