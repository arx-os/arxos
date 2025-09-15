package converter

import (
	"regexp"
	"strconv"
	"strings"

	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/common/progress"
)

// SpatialIFCConverter handles IFC files with proper spatial containment relationships
type SpatialIFCConverter struct {
	*ImprovedIFCConverter
	spatialStructure map[string]*SpatialElement
	relationships    map[string]*IFCRelationship
	entities         map[string]*IFCEntity
}

// SpatialElement represents an element in the spatial hierarchy
type SpatialElement struct {
	Entity        *IFCEntity
	Children      []*SpatialElement
	Parent        *SpatialElement
	ContainedElements []*IFCEntity
	Level         int // Depth in hierarchy (0=project, 1=site, 2=building, 3=storey, 4=space)
}

// IFCRelationship represents relationships between IFC entities
type IFCRelationship struct {
	ID           string
	Type         string
	RelatingElement string  // Parent/container
	RelatedElements []string // Children/contained elements
	Name         string
	Description  string
}

// NewSpatialIFCConverter creates an enhanced IFC converter with spatial understanding
func NewSpatialIFCConverter() *SpatialIFCConverter {
	return &SpatialIFCConverter{
		ImprovedIFCConverter: NewImprovedIFCConverter(),
		spatialStructure:     make(map[string]*SpatialElement),
		relationships:        make(map[string]*IFCRelationship),
		entities:             make(map[string]*IFCEntity),
	}
}

func (c *SpatialIFCConverter) GetDescription() string {
	return "Industry Foundation Classes (IFC) - Enhanced spatial parsing with containment relationships"
}

// ConvertToBIMWithSpatial performs enhanced IFC conversion with proper spatial relationships
func (c *SpatialIFCConverter) ConvertToBIMWithSpatial(input []string) (*Building, error) {
	tracker := progress.New(6, "IFC Spatial Conversion")
	defer tracker.Finish()

	// Step 1: Parse all entities
	tracker.Step("Parsing IFC entities")
	c.parseAllEntities(input)

	// Step 2: Parse spatial relationships
	tracker.Step("Parsing spatial relationships")
	c.parseSpatialRelationships()

	// Step 3: Build spatial hierarchy
	tracker.Step("Building spatial hierarchy")
	c.buildSpatialHierarchy()

	// Step 4: Extract building information
	tracker.Step("Extracting building information")
	building := c.extractBuildingFromHierarchy()

	// Step 5: Process equipment and furnishing
	tracker.Step("Processing equipment and furnishing")
	c.processEquipmentWithContainment(building)

	// Step 6: Validate and finalize
	tracker.Step("Validating spatial structure")
	c.validateSpatialStructure(building)

	logger.Info("✅ IFC Spatial Conversion completed - found %d floors, %d rooms, %d equipment items",
		len(building.Floors), c.countRooms(building), c.countEquipment(building))

	return building, nil
}

// parseAllEntities parses all IFC entities into memory
func (c *SpatialIFCConverter) parseAllEntities(lines []string) {
	entityPattern := regexp.MustCompile(`^#(\d+)\s*=\s*([A-Z][A-Z0-9_]*)\s*\((.*)\)\s*;?\s*$`)

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if !strings.HasPrefix(line, "#") {
			continue
		}

		matches := entityPattern.FindStringSubmatch(line)
		if len(matches) != 4 {
			continue
		}

		entity := &IFCEntity{
			ID:         matches[1],
			Type:       matches[2],
			Properties: make(map[string]string),
			References: make([]string, 0),
		}

		// Parse properties based on entity type
		c.parseEntityProperties(entity, matches[3])
		c.entities[entity.ID] = entity
	}

	logger.Debug("Parsed %d IFC entities", len(c.entities))
}

// parseEntityProperties parses entity properties based on type
func (c *SpatialIFCConverter) parseEntityProperties(entity *IFCEntity, propsStr string) {
	switch entity.Type {
	case "IFCPROJECT", "IFCSITE", "IFCBUILDING", "IFCBUILDINGSTOREY", "IFCSPACE":
		c.parseSpatialElementProperties(entity, propsStr)
	case "IFCRELAGGREGATES", "IFCRELCONTAINEDINSPATIALSTRUCTURE":
		c.parseRelationshipProperties(entity, propsStr)
	default:
		c.parseGenericProperties(entity, propsStr)
	}
}

// parseSpatialElementProperties parses properties for spatial elements
func (c *SpatialIFCConverter) parseSpatialElementProperties(entity *IFCEntity, propsStr string) {
	props := c.parseIFCProperties(propsStr)

	if len(props) > 0 {
		entity.GUID = c.cleanString(props[0])
	}
	if len(props) > 2 {
		entity.Name = c.cleanString(props[2])
	}
	if len(props) > 3 {
		entity.Description = c.cleanString(props[3])
	}

	// Extract additional properties based on type
	switch entity.Type {
	case "IFCBUILDINGSTOREY":
		// Look for elevation in the last numeric property
		for i := len(props) - 1; i >= 0; i-- {
			if elevStr := c.cleanString(props[i]); elevStr != "" && elevStr != "$" {
				// Try to parse as float to verify it's numeric
				if _, err := strconv.ParseFloat(elevStr, 64); err == nil {
					entity.Properties["elevation"] = elevStr
					break
				}
			}
		}
	case "IFCSPACE":
		if len(props) > 9 {
			// Interior/exterior indicator
			entity.Properties["interior_exterior"] = c.cleanString(props[9])
		}
		if len(props) > 10 {
			// Elevation
			if elevStr := c.cleanString(props[10]); elevStr != "" && elevStr != "$" {
				entity.Properties["elevation"] = elevStr
			}
		}
	}
}

// parseRelationshipProperties parses properties for relationship entities
func (c *SpatialIFCConverter) parseRelationshipProperties(entity *IFCEntity, propsStr string) {
	props := c.parseIFCProperties(propsStr)

	relationship := &IFCRelationship{
		ID:              entity.ID,
		Type:            entity.Type,
		RelatedElements: make([]string, 0),
	}

	if len(props) > 0 {
		relationship.Name = c.cleanString(props[0])
	}
	if len(props) > 3 {
		relationship.Description = c.cleanString(props[3])
	}

	// Parse specific relationship properties
	switch entity.Type {
	case "IFCRELAGGREGATES":
		if len(props) > 4 {
			relationship.RelatingElement = c.extractReference(props[4])
		}
		if len(props) > 5 {
			relationship.RelatedElements = c.extractReferenceList(props[5])
		}
	case "IFCRELCONTAINEDINSPATIALSTRUCTURE":
		if len(props) > 4 {
			relationship.RelatedElements = c.extractReferenceList(props[4])
		}
		if len(props) > 5 {
			relationship.RelatingElement = c.extractReference(props[5])
		}
	}

	c.relationships[entity.ID] = relationship
}

// parseGenericProperties parses properties for general entities
func (c *SpatialIFCConverter) parseGenericProperties(entity *IFCEntity, propsStr string) {
	props := c.parseIFCProperties(propsStr)

	if len(props) > 0 {
		entity.GUID = c.cleanString(props[0])
	}
	if len(props) > 2 {
		entity.Name = c.cleanString(props[2])
	}
	if len(props) > 3 {
		entity.Description = c.cleanString(props[3])
	}

	// Extract type-specific properties
	switch entity.Type {
	case "IFCFLOWCONTROLLER", "IFCFLOWTERMINAL", "IFCDISTRIBUTIONELEMENT":
		entity.Properties["category"] = "hvac"
	case "IFCFURNISHINGELEMENT":
		entity.Properties["category"] = "furniture"
	case "IFCBUILDINGELEMENTPROXY":
		entity.Properties["category"] = "architectural"
	}
}

// parseSpatialRelationships builds relationship mappings
func (c *SpatialIFCConverter) parseSpatialRelationships() {
	logger.Debug("Found %d relationships", len(c.relationships))

	// Log relationship types for debugging
	relTypes := make(map[string]int)
	for _, rel := range c.relationships {
		relTypes[rel.Type]++
	}

	for relType, count := range relTypes {
		logger.Debug("  %s: %d", relType, count)
	}
}

// buildSpatialHierarchy constructs the spatial containment hierarchy
func (c *SpatialIFCConverter) buildSpatialHierarchy() {
	// Create spatial elements for all spatial entities
	spatialTypes := []string{"IFCPROJECT", "IFCSITE", "IFCBUILDING", "IFCBUILDINGSTOREY", "IFCSPACE"}

	for _, spatialType := range spatialTypes {
		for _, entity := range c.entities {
			if entity.Type == spatialType {
				spatial := &SpatialElement{
					Entity:            entity,
					Children:          make([]*SpatialElement, 0),
					ContainedElements: make([]*IFCEntity, 0),
					Level:             c.getSpatialLevel(spatialType),
				}
				c.spatialStructure[entity.ID] = spatial
			}
		}
	}

	// Build parent-child relationships using IFCRELAGGREGATES
	for _, rel := range c.relationships {
		if rel.Type == "IFCRELAGGREGATES" {
			if parent, exists := c.spatialStructure[rel.RelatingElement]; exists {
				for _, childID := range rel.RelatedElements {
					if child, exists := c.spatialStructure[childID]; exists {
						child.Parent = parent
						parent.Children = append(parent.Children, child)
					}
				}
			}
		}
	}

	// Build containment relationships using IFCRELCONTAINEDINSPATIALSTRUCTURE
	for _, rel := range c.relationships {
		if rel.Type == "IFCRELCONTAINEDINSPATIALSTRUCTURE" {
			if container, exists := c.spatialStructure[rel.RelatingElement]; exists {
				for _, containedID := range rel.RelatedElements {
					if entity, exists := c.entities[containedID]; exists {
						container.ContainedElements = append(container.ContainedElements, entity)
					}
				}
			}
		}
	}

	logger.Debug("Built spatial hierarchy with %d spatial elements", len(c.spatialStructure))
}

// getSpatialLevel returns the hierarchy level for a spatial type
func (c *SpatialIFCConverter) getSpatialLevel(spatialType string) int {
	levels := map[string]int{
		"IFCPROJECT":       0,
		"IFCSITE":          1,
		"IFCBUILDING":      2,
		"IFCBUILDINGSTOREY": 3,
		"IFCSPACE":         4,
	}
	return levels[spatialType]
}

// extractBuildingFromHierarchy creates Building from spatial hierarchy
func (c *SpatialIFCConverter) extractBuildingFromHierarchy() *Building {
	building := &Building{
		Metadata: Metadata{
			Source: "IFC Import (Spatial)",
			Format: "IFC",
			Properties: map[string]string{
				"spatial_parsing": "enabled",
			},
		},
		Floors: make([]Floor, 0),
	}

	// Find the building entity
	var buildingElement *SpatialElement
	for _, spatial := range c.spatialStructure {
		if spatial.Entity.Type == "IFCBUILDING" {
			buildingElement = spatial
			building.Name = spatial.Entity.Name
			if spatial.Entity.Description != "" {
				building.Address = spatial.Entity.Description
			}
			break
		}
	}

	if buildingElement == nil {
		logger.Warn("No IFCBUILDING entity found, using project-level information")
		for _, spatial := range c.spatialStructure {
			if spatial.Entity.Type == "IFCPROJECT" {
				building.Name = spatial.Entity.Name
				buildingElement = spatial
				break
			}
		}
	}

	// Extract floors from building storeys
	if buildingElement != nil {
		c.extractFloorsFromHierarchy(buildingElement, building)
	}

	return building
}

// extractFloorsFromHierarchy extracts floors from the spatial hierarchy
func (c *SpatialIFCConverter) extractFloorsFromHierarchy(buildingElement *SpatialElement, building *Building) {
	// Find all building storeys under this building
	storeys := c.findChildrenByType(buildingElement, "IFCBUILDINGSTOREY")

	for i, storey := range storeys {
		floor := Floor{
			ID:    storey.Entity.ID,
			Name:  storey.Entity.Name,
			Level: i,
			Rooms: make([]Room, 0),
		}

		// Extract elevation
		if elevStr, ok := storey.Entity.Properties["elevation"]; ok {
			if elev, err := strconv.ParseFloat(elevStr, 64); err == nil {
				floor.Elevation = elev
			}
		}

		// Extract spaces (rooms) from this storey
		spaces := c.findChildrenByType(storey, "IFCSPACE")
		for _, space := range spaces {
			room := Room{
				ID:        space.Entity.ID,
				Name:      space.Entity.Name,
				Number:    c.extractRoomNumber(space.Entity.Name),
				Type:      c.inferSpaceType(space.Entity),
				Equipment: make([]Equipment, 0),
			}

			// Extract area if available
			if areaStr, ok := space.Entity.Properties["area"]; ok {
				if area, err := strconv.ParseFloat(areaStr, 64); err == nil {
					room.Area = area
				}
			}

			floor.Rooms = append(floor.Rooms, room)
		}

		building.Floors = append(building.Floors, floor)
	}

	logger.Debug("Extracted %d floors with spatial hierarchy", len(building.Floors))
}

// findChildrenByType finds all children of a specific type recursively
func (c *SpatialIFCConverter) findChildrenByType(parent *SpatialElement, entityType string) []*SpatialElement {
	var result []*SpatialElement

	for _, child := range parent.Children {
		if child.Entity.Type == entityType {
			result = append(result, child)
		}
		// Recursively search children
		result = append(result, c.findChildrenByType(child, entityType)...)
	}

	return result
}

// processEquipmentWithContainment processes equipment using spatial containment
func (c *SpatialIFCConverter) processEquipmentWithContainment(building *Building) {
	equipmentTypes := []string{
		"IFCFLOWCONTROLLER", "IFCFLOWTERMINAL", "IFCDISTRIBUTIONELEMENT",
		"IFCBUILDINGELEMENTPROXY", "IFCFURNISHINGELEMENT", "IFCFLOWFITTING",
		"IFCENERGYCONVERSIONDEVICE", "IFCFLOWMOVINGDEVICE", "IFCFLOWSTORAGEDEVICE",
	}

	equipmentCount := 0

	// Process equipment in each space
	for _, spatial := range c.spatialStructure {
		if spatial.Entity.Type == "IFCSPACE" {
			// Find which floor and room this corresponds to
			floorIdx, roomIdx := c.findRoomInBuilding(building, spatial.Entity.ID)
			if floorIdx < 0 || roomIdx < 0 {
				continue
			}

			// Add equipment contained in this space
			for _, containedEntity := range spatial.ContainedElements {
				for _, eqType := range equipmentTypes {
					if containedEntity.Type == eqType && containedEntity.Name != "" {
						eq := Equipment{
							ID:     containedEntity.ID,
							Tag:    containedEntity.Name,
							Name:   containedEntity.Name,
							Type:   c.mapIFCToEquipmentType(containedEntity.Type),
							Status: "operational",
							Location: Location{
								Floor: building.Floors[floorIdx].ID,
								Room:  building.Floors[floorIdx].Rooms[roomIdx].Number,
							},
						}

						// Add category from properties
						if category, ok := containedEntity.Properties["category"]; ok {
							eq.Category = category
						}

						building.Floors[floorIdx].Rooms[roomIdx].Equipment = append(
							building.Floors[floorIdx].Rooms[roomIdx].Equipment, eq)
						equipmentCount++
						break
					}
				}
			}
		}
	}

	logger.Debug("Processed %d equipment items using spatial containment", equipmentCount)
}

// findRoomInBuilding finds the floor and room indices for a given space ID
func (c *SpatialIFCConverter) findRoomInBuilding(building *Building, spaceID string) (int, int) {
	for floorIdx, floor := range building.Floors {
		for roomIdx, room := range floor.Rooms {
			if room.ID == spaceID {
				return floorIdx, roomIdx
			}
		}
	}
	return -1, -1
}

// inferSpaceType infers room type from IFC space properties
func (c *SpatialIFCConverter) inferSpaceType(entity *IFCEntity) string {
	name := strings.ToLower(entity.Name)

	// Common space type patterns
	patterns := map[string][]string{
		"office":     {"office", "bureau"},
		"conference": {"conference", "meeting", "boardroom"},
		"restroom":   {"restroom", "toilet", "wc", "bathroom"},
		"storage":    {"storage", "store", "warehouse"},
		"corridor":   {"corridor", "hallway", "hall"},
		"lobby":      {"lobby", "entrance", "foyer"},
		"kitchen":    {"kitchen", "break", "pantry"},
		"utility":    {"utility", "mechanical", "electrical", "telecom"},
		"stair":      {"stair", "step"},
		"elevator":   {"elevator", "lift"},
	}

	for roomType, keywords := range patterns {
		for _, keyword := range keywords {
			if strings.Contains(name, keyword) {
				return roomType
			}
		}
	}

	// Check interior/exterior property
	if intExt, ok := entity.Properties["interior_exterior"]; ok {
		if strings.ToUpper(intExt) == "EXTERNAL" || strings.ToLower(intExt) == "exterior" {
			return "external"
		}
	}

	return "space"
}

// validateSpatialStructure validates the extracted spatial structure
func (c *SpatialIFCConverter) validateSpatialStructure(building *Building) {
	issues := building.Validate()
	if len(issues) > 0 {
		logger.Warn("Spatial structure validation found %d issues:", len(issues))
		for _, issue := range issues {
			logger.Warn("  - %s", issue)
		}
	}

	// Additional spatial-specific validation
	orphanedSpaces := 0
	for _, spatial := range c.spatialStructure {
		if spatial.Entity.Type == "IFCSPACE" && spatial.Parent == nil {
			orphanedSpaces++
		}
	}

	if orphanedSpaces > 0 {
		logger.Warn("Found %d orphaned spaces without proper spatial containment", orphanedSpaces)
	}
}

// Helper functions

func (c *SpatialIFCConverter) extractReference(prop string) string {
	prop = strings.TrimSpace(prop)
	if strings.HasPrefix(prop, "#") {
		return strings.TrimPrefix(prop, "#")
	}
	return ""
}

func (c *SpatialIFCConverter) extractReferenceList(prop string) []string {
	var refs []string
	prop = strings.TrimSpace(prop)

	// Handle list format: (#123,#456,#789)
	if strings.HasPrefix(prop, "(") && strings.HasSuffix(prop, ")") {
		prop = strings.Trim(prop, "()")
		parts := strings.Split(prop, ",")
		for _, part := range parts {
			if ref := c.extractReference(strings.TrimSpace(part)); ref != "" {
				refs = append(refs, ref)
			}
		}
	}

	return refs
}

func (c *SpatialIFCConverter) cleanString(s string) string {
	// Remove quotes and clean whitespace
	s = strings.Trim(s, "'\"")
	s = strings.TrimSpace(s)
	return s
}

// extractRoomNumber overrides the base implementation with more sophisticated pattern matching
func (c *SpatialIFCConverter) extractRoomNumber(name string) string {
	// Enhanced room number extraction patterns
	patterns := []*regexp.Regexp{
		regexp.MustCompile(`(?i)(?:room|office|suite)\s+([A-Z]?\d+[A-Z]?)(?:\s|$)`), // "Room 205A", "Office 101"
		regexp.MustCompile(`(?i)(?:room|office|suite)\s+([A-Z]+)(?:\s|$)`),           // "Meeting Room Alpha"
		regexp.MustCompile(`([A-Z]-?\d+[A-Z]?)`),                                     // "W-203", "15B"
		regexp.MustCompile(`(\d+[A-Z])`),                                             // "205A"
		regexp.MustCompile(`(\d+)`),                                                  // Basic numbers as fallback
	}

	for _, pattern := range patterns {
		if match := pattern.FindStringSubmatch(name); len(match) > 1 {
			return match[1]
		}
	}

	// If no pattern matches and name is short and alphanumeric (likely a code), return it
	if len(strings.Fields(name)) == 1 && len(name) <= 20 && regexp.MustCompile(`^[A-Za-z0-9-]+$`).MatchString(name) {
		// But exclude common room type words
		excluded := []string{"kitchen", "lobby", "bathroom", "restroom", "office", "room"}
		lowerName := strings.ToLower(name)
		for _, excl := range excluded {
			if lowerName == excl {
				return ""
			}
		}
		return name
	}

	// For longer names without clear patterns, return empty
	return ""
}

func (c *SpatialIFCConverter) countRooms(building *Building) int {
	count := 0
	for _, floor := range building.Floors {
		count += len(floor.Rooms)
	}
	return count
}

func (c *SpatialIFCConverter) countEquipment(building *Building) int {
	count := 0
	for _, floor := range building.Floors {
		for _, room := range floor.Rooms {
			count += len(room.Equipment)
		}
	}
	return count
}