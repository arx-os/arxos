package converter

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
)

// IFCDatabaseInterface provides methods for storing IFC data with spatial information
type IFCDatabaseInterface interface {
	// Store building with spatial data
	StoreBuildingWithSpatial(ctx context.Context, building *Building, spatialData map[string]*SpatialData) error

	// Store equipment with precise 3D positions
	StoreEquipmentWithPosition(ctx context.Context, equipment *Equipment, position spatial.Point3D, confidence spatial.ConfidenceLevel) error

	// Store spatial relationships
	StoreSpatialRelationship(ctx context.Context, parentID, childID string, relType RelationshipType) error

	// Batch operations for performance
	BatchStoreEquipment(ctx context.Context, equipment []*EquipmentWithPosition) error

	// Query operations
	GetFloorPlanByGUID(ctx context.Context, guid string) (*models.FloorPlan, error)
	GetRoomByIFCID(ctx context.Context, ifcID string) (*models.Room, error)
}

// SpatialData contains spatial information extracted from IFC
type SpatialData struct {
	Position     spatial.Point3D
	BoundingBox  spatial.BoundingBox
	Rotation     float64
	LocalCoords  spatial.Point3D // Local coordinates within parent space
	GlobalCoords spatial.Point3D // Global building coordinates
	Transform    spatial.Transform
	Confidence   spatial.ConfidenceLevel
}

// RelationshipType represents the type of spatial relationship
type RelationshipType string

const (
	RelationshipContains    RelationshipType = "CONTAINS"
	RelationshipAggregates  RelationshipType = "AGGREGATES"
	RelationshipConnects    RelationshipType = "CONNECTS"
	RelationshipFills       RelationshipType = "FILLS"
	RelationshipVoids       RelationshipType = "VOIDS"
)

// EquipmentWithPosition combines equipment data with spatial position
type EquipmentWithPosition struct {
	Equipment  *Equipment
	Position   spatial.Point3D
	Confidence spatial.ConfidenceLevel
	ParentID   string // Room or floor ID
	IFCEntity  *IFCEntity // Original IFC data
}

// IFCDatabaseAdapter adapts the database interface for IFC operations
type IFCDatabaseAdapter struct {
	db        database.DB
	spatialDB database.SpatialDB
}

// NewIFCDatabaseAdapter creates a new adapter for IFC database operations
func NewIFCDatabaseAdapter(db database.DB) (*IFCDatabaseAdapter, error) {
	adapter := &IFCDatabaseAdapter{
		db: db,
	}

	// Check for spatial support
	if db.HasSpatialSupport() {
		spatialDB, err := db.GetSpatialDB()
		if err != nil {
			logger.Warn("Spatial database available but failed to get interface: %v", err)
		} else {
			adapter.spatialDB = spatialDB
			logger.Info("IFC adapter initialized with spatial support")
		}
	} else {
		logger.Warn("IFC adapter initialized without spatial support - positions will be stored but not spatially indexed")
	}

	return adapter, nil
}

// StoreBuildingWithSpatial stores a building with all spatial data
func (adapter *IFCDatabaseAdapter) StoreBuildingWithSpatial(ctx context.Context, building *Building, spatialData map[string]*SpatialData) error {
	// Begin transaction
	tx, err := adapter.db.BeginTx(ctx)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Building is represented as metadata at the floor level in ArxOS

	// No separate building entity in ArxOS - building info stored with floors

	// Store floors with spatial data
	for i := range building.Floors {
		floor := &building.Floors[i]
		modelFloor := adapter.convertToModelFloorPlan(floor, building)

		if err := adapter.storeFloorPlan(ctx, tx, modelFloor); err != nil {
			return fmt.Errorf("failed to store floor %s: %w", floor.Name, err)
		}

		// Store rooms for this floor
		for i := range floor.Rooms {
			room := &floor.Rooms[i]
			modelRoom := adapter.convertToModelRoom(room, modelFloor.ID)

			if err := adapter.storeRoom(ctx, tx, modelRoom); err != nil {
				return fmt.Errorf("failed to store room %s: %w", room.Name, err)
			}

			// Store room spatial data if available
			// Note: Room bounds would be stored as part of floor plan in ArxOS
			if spatialData != nil {
				if roomSpatial, exists := spatialData[room.GUID]; exists {
					// Update room bounds in the model
					modelRoom.Bounds = models.Bounds{
						MinX: roomSpatial.BoundingBox.Min.X,
						MinY: roomSpatial.BoundingBox.Min.Y,
						MaxX: roomSpatial.BoundingBox.Max.X,
						MaxY: roomSpatial.BoundingBox.Max.Y,
					}
				}
			}

			// Store equipment in this room
			for j := range room.Equipment {
				equipment := &room.Equipment[j]
				modelEquipment := adapter.convertToModelEquipment(equipment, modelRoom.ID)

				if err := adapter.storeEquipment(ctx, tx, modelEquipment); err != nil {
					return fmt.Errorf("failed to store equipment %s: %w", equipment.Name, err)
				}

				// Store equipment spatial position if available
				if spatialData != nil && adapter.spatialDB != nil {
					if eqSpatial, exists := spatialData[equipment.GUID]; exists {
						if err := adapter.spatialDB.UpdateEquipmentPosition(
							modelEquipment.ID,
							eqSpatial.Position,
							eqSpatial.Confidence,
							"IFC_Import",
						); err != nil {
							logger.Warn("Failed to store spatial position for equipment %s: %v",
								equipment.Name, err)
						}
					}
				}
			}
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	logger.Info("Successfully stored building %s with %d floors and spatial data",
		building.Name, len(building.Floors))

	return nil
}

// StoreEquipmentWithPosition stores equipment with its precise 3D position
func (adapter *IFCDatabaseAdapter) StoreEquipmentWithPosition(ctx context.Context, equipment *Equipment, position spatial.Point3D, confidence spatial.ConfidenceLevel) error {
	// Convert equipment model
	modelEquipment := adapter.convertToModelEquipment(equipment, "")

	// Store in regular database
	if err := adapter.db.SaveEquipment(ctx, modelEquipment); err != nil {
		return fmt.Errorf("failed to save equipment: %w", err)
	}

	// Store spatial position if available
	if adapter.spatialDB != nil {
		if err := adapter.spatialDB.UpdateEquipmentPosition(
			modelEquipment.ID,
			position,
			confidence,
			"IFC_Import",
		); err != nil {
			return fmt.Errorf("failed to store equipment position: %w", err)
		}
	} else {
		// Store position in metadata as fallback
		if modelEquipment.Metadata == nil {
			modelEquipment.Metadata = make(map[string]interface{})
		}
		modelEquipment.Metadata["position_x"] = position.X
		modelEquipment.Metadata["position_y"] = position.Y
		modelEquipment.Metadata["position_z"] = position.Z
		modelEquipment.Metadata["position_confidence"] = confidence.String()

		// Update equipment with position metadata
		if err := adapter.db.UpdateEquipment(ctx, modelEquipment); err != nil {
			return fmt.Errorf("failed to update equipment with position metadata: %w", err)
		}
	}

	return nil
}

// BatchStoreEquipment stores multiple equipment items efficiently
func (adapter *IFCDatabaseAdapter) BatchStoreEquipment(ctx context.Context, equipment []*EquipmentWithPosition) error {
	if len(equipment) == 0 {
		return nil
	}

	// Begin transaction for batch operation
	tx, err := adapter.db.BeginTx(ctx)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Batch store equipment
	for _, eq := range equipment {
		modelEquipment := adapter.convertToModelEquipment(eq.Equipment, eq.ParentID)

		// Store in database
		if err := adapter.storeEquipmentTx(ctx, tx, modelEquipment); err != nil {
			return fmt.Errorf("failed to store equipment %s: %w", eq.Equipment.Name, err)
		}

		// Store spatial position if available
		if adapter.spatialDB != nil {
			if err := adapter.spatialDB.UpdateEquipmentPosition(
				modelEquipment.ID,
				eq.Position,
				eq.Confidence,
				"IFC_Batch_Import",
			); err != nil {
				logger.Warn("Failed to store position for equipment %s: %v",
					eq.Equipment.Name, err)
			}
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit batch transaction: %w", err)
	}

	logger.Info("Successfully batch stored %d equipment items with positions", len(equipment))

	return nil
}

// convertToModelFloorPlan converts internal Floor to models.FloorPlan
func (adapter *IFCDatabaseAdapter) convertToModelFloorPlan(floor *Floor, building *Building) *models.FloorPlan {
	return &models.FloorPlan{
		ID:          floor.GUID,
		Name:        floor.Name,
		Building:    building.Name,
		Level:       floor.Level,
		Description: fmt.Sprintf("%s - Floor %d", building.Name, floor.Level),
		Metadata: map[string]interface{}{
			"ifc_id":        floor.IFCId,
			"elevation":     floor.Elevation,
			"building_guid": building.GUID,
			"address":       building.Address,
			"source":        "IFC",
		},
	}
}


// convertToModelRoom converts internal Room to models.Room
func (adapter *IFCDatabaseAdapter) convertToModelRoom(room *Room, floorID string) *models.Room {
	bounds := models.Bounds{}
	// Bounds would be calculated from spatial data if available

	return &models.Room{
		ID:     room.GUID,
		Name:   room.Name,
		Bounds: bounds,
	}
}

// convertToModelEquipment converts internal Equipment to models.Equipment
func (adapter *IFCDatabaseAdapter) convertToModelEquipment(equipment *Equipment, parentID string) *models.Equipment {
	// Determine equipment type from IFC type
	eqType := equipment.Type
	if eqType == "" && equipment.IFCType != "" {
		eqType = adapter.mapIFCTypeToEquipmentType(equipment.IFCType)
	}

	metadata := map[string]interface{}{
		"ifc_id":      equipment.IFCId,
		"ifc_type":    equipment.IFCType,
		"category":    equipment.Category,
	}

	// Add properties if present
	if len(equipment.Properties) > 0 {
		metadata["properties"] = equipment.Properties
	}

	return &models.Equipment{
		ID:       equipment.GUID,
		Name:     equipment.Name,
		Type:     eqType,
		Status:   "operational", // Default status
		Model:    equipment.Model,
		Serial:   equipment.SerialNumber,
		Metadata: metadata,
	}
}

// mapIFCTypeToEquipmentType maps IFC entity types to equipment types
func (adapter *IFCDatabaseAdapter) mapIFCTypeToEquipmentType(ifcType string) string {
	// Remove IFC prefix and convert to readable format
	eqType := strings.TrimPrefix(ifcType, "IFC")
	eqType = strings.ReplaceAll(eqType, "_", " ")
	eqType = strings.ToLower(eqType)

	// Map common IFC types
	switch {
	case strings.Contains(eqType, "flow"):
		return "HVAC"
	case strings.Contains(eqType, "furnish"):
		return "Furniture"
	case strings.Contains(eqType, "door"):
		return "Door"
	case strings.Contains(eqType, "window"):
		return "Window"
	case strings.Contains(eqType, "light"):
		return "Lighting"
	case strings.Contains(eqType, "electric"):
		return "Electrical"
	default:
		return eqType
	}
}

// Helper methods for transactional operations
func (adapter *IFCDatabaseAdapter) storeFloorPlan(ctx context.Context, tx *sql.Tx, floorPlan *models.FloorPlan) error {
	// Store floor plan in database
	query := `INSERT INTO floor_plans (id, name, description, building, level, metadata)
	          VALUES (?, ?, ?, ?, ?, ?)`
	_, err := tx.ExecContext(ctx, query, floorPlan.ID, floorPlan.Name,
		floorPlan.Description, floorPlan.Building, floorPlan.Level, floorPlan.Metadata)
	return err
}


func (adapter *IFCDatabaseAdapter) storeRoom(ctx context.Context, tx *sql.Tx, room *models.Room) error {
	// Rooms are stored as part of floor plan in ArxOS
	// This would typically update the floor plan's rooms array
	return nil
}

func (adapter *IFCDatabaseAdapter) storeEquipment(ctx context.Context, tx *sql.Tx, equipment *models.Equipment) error {
	query := `INSERT INTO equipment (id, name, type, status, model, serial, metadata)
	          VALUES (?, ?, ?, ?, ?, ?, ?)`
	_, err := tx.ExecContext(ctx, query, equipment.ID, equipment.Name,
		equipment.Type, equipment.Status, equipment.Model, equipment.Serial, equipment.Metadata)
	return err
}

func (adapter *IFCDatabaseAdapter) storeEquipmentTx(ctx context.Context, tx *sql.Tx, equipment *models.Equipment) error {
	return adapter.storeEquipment(ctx, tx, equipment)
}

// StoreSpatialRelationship stores a spatial relationship between entities
func (adapter *IFCDatabaseAdapter) StoreSpatialRelationship(ctx context.Context, parentID, childID string, relType RelationshipType) error {
	// Store in metadata for now - could be extended to dedicated relationship table
	query := `INSERT INTO spatial_relationships (parent_id, child_id, relationship_type, created_at)
	          VALUES (?, ?, ?, ?)`
	_, err := adapter.db.Exec(ctx, query, parentID, childID, string(relType), time.Now())
	if err != nil {
		return fmt.Errorf("failed to store spatial relationship: %w", err)
	}
	return nil
}

// Query methods implementation
func (adapter *IFCDatabaseAdapter) GetFloorPlanByGUID(ctx context.Context, guid string) (*models.FloorPlan, error) {
	return adapter.db.GetFloorPlan(ctx, guid)
}

func (adapter *IFCDatabaseAdapter) GetRoomByIFCID(ctx context.Context, ifcID string) (*models.Room, error) {
	// Rooms in ArxOS are part of floor plans
	// This would need to search through floor plans to find the room
	// For now, return a simplified implementation
	return nil, fmt.Errorf("room lookup by IFC ID not yet implemented")
}