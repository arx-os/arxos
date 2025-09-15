package converter

import (
	"bufio"
	"fmt"
	"io"
	"regexp"
	"strconv"
	"strings"

	"github.com/joelpate/arxos/internal/common/logger"
)

// ImprovedIFCConverter handles IFC files with better entity parsing
type ImprovedIFCConverter struct{}

func NewImprovedIFCConverter() *ImprovedIFCConverter {
	return &ImprovedIFCConverter{}
}

func (c *ImprovedIFCConverter) GetFormat() string {
	return "ifc"
}

func (c *ImprovedIFCConverter) GetDescription() string {
	return "Industry Foundation Classes (IFC) - Open BIM standard"
}

func (c *ImprovedIFCConverter) CanConvert(filename string) bool {
	lower := strings.ToLower(filename)
	return strings.HasSuffix(lower, ".ifc") ||
		strings.HasSuffix(lower, ".ifcxml") ||
		strings.HasSuffix(lower, ".ifczip")
}

// IFCEntity represents a parsed IFC entity
type IFCEntity struct {
	ID         string
	Type       string
	GUID       string
	Name       string
	Description string
	Properties map[string]string
	References []string
}

func (c *ImprovedIFCConverter) ConvertToBIM(input io.Reader, output io.Writer) error {
	building := &Building{
		Metadata: Metadata{
			Source: "IFC Import",
			Format: "IFC",
		},
		Floors: make([]Floor, 0),
	}

	// Parse all IFC entities first
	entities := c.parseIFCEntities(input)

	// Extract building info
	for _, entity := range entities {
		if entity.Type == "IFCBUILDING" {
			building.Name = entity.Name
			if entity.Description != "" {
				building.Address = entity.Description
			}
			break
		}
	}

	// Process building storeys (floors)
	floorEntities := c.getEntitiesByType(entities, "IFCBUILDINGSTOREY")
	for _, floorEntity := range floorEntities {
		floor := Floor{
			ID:    floorEntity.ID,
			Name:  floorEntity.Name,
			Level: len(building.Floors),
			Rooms: make([]Room, 0),
		}

		// Extract elevation from properties
		if elevStr, ok := floorEntity.Properties["elevation"]; ok {
			if elev, err := strconv.ParseFloat(elevStr, 64); err == nil {
				floor.Elevation = elev
			}
		}

		building.Floors = append(building.Floors, floor)
	}

	// Process spaces (rooms)
	spaceEntities := c.getEntitiesByType(entities, "IFCSPACE")
	for _, spaceEntity := range spaceEntities {
		room := Room{
			ID:     spaceEntity.ID,
			Name:   spaceEntity.Name,
			Number: c.extractRoomNumber(spaceEntity.Name),
			Type:   "space",
		}

		// Try to determine which floor this space belongs to
		floorIdx := c.findSpaceFloor(spaceEntity, entities, len(building.Floors))
		if floorIdx >= 0 && floorIdx < len(building.Floors) {
			building.Floors[floorIdx].Rooms = append(building.Floors[floorIdx].Rooms, room)
		} else if len(building.Floors) > 0 {
			// Default to first floor if can't determine
			building.Floors[0].Rooms = append(building.Floors[0].Rooms, room)
		}
	}

	// Process equipment
	equipmentTypes := []string{
		"IFCFLOWCONTROLLER", "IFCFLOWTERMINAL", "IFCDISTRIBUTIONELEMENT",
		"IFCBUILDINGELEMENTPROXY", "IFCFURNISHINGELEMENT", "IFCFLOWFITTING",
		"IFCENERGYCONVERSIONDEVICE", "IFCFLOWMOVINGDEVICE", "IFCFLOWSTORAGEDEVICE",
	}

	for _, eqType := range equipmentTypes {
		equipmentEntities := c.getEntitiesByType(entities, eqType)
		for _, eqEntity := range equipmentEntities {
			if eqEntity.Name == "" {
				continue // Skip unnamed equipment
			}

			eq := Equipment{
				ID:     eqEntity.ID,
				Tag:    eqEntity.Name,
				Name:   eqEntity.Name,
				Type:   c.mapIFCToEquipmentType(eqEntity.Type),
				Status: "operational",
			}

			// Try to find which space/room this equipment belongs to
			spaceIdx, floorIdx := c.findEquipmentLocation(eqEntity, entities, building)
			if floorIdx >= 0 && spaceIdx >= 0 {
				building.Floors[floorIdx].Rooms[spaceIdx].Equipment = append(
					building.Floors[floorIdx].Rooms[spaceIdx].Equipment, eq)
			} else if floorIdx >= 0 {
				// Add to first room on the floor if can't determine exact room
				if len(building.Floors[floorIdx].Rooms) > 0 {
					building.Floors[floorIdx].Rooms[0].Equipment = append(
						building.Floors[floorIdx].Rooms[0].Equipment, eq)
				}
			} else {
				// Add to first available room as fallback
				for f := range building.Floors {
					if len(building.Floors[f].Rooms) > 0 {
						building.Floors[f].Rooms[0].Equipment = append(
							building.Floors[f].Rooms[0].Equipment, eq)
						break
					}
				}
			}
		}
	}

	// Validate building data before output
	if issues := building.Validate(); len(issues) > 0 {
		logger.Warn("Data quality issues found (%d issues):", len(issues))
		for _, issue := range issues {
			logger.Warn("  - %s", issue)
		}
	}

	// Convert to BIM format
	bimText := building.ToBIM()
	_, err := output.Write([]byte(bimText))
	return err
}

func (c *ImprovedIFCConverter) ConvertFromBIM(input io.Reader, output io.Writer) error {
	return fmt.Errorf("IFC generation not implemented")
}

func (c *ImprovedIFCConverter) parseIFCEntities(input io.Reader) []IFCEntity {
	var entities []IFCEntity
	scanner := bufio.NewScanner(input)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())

		// Skip non-entity lines
		if !strings.HasPrefix(line, "#") {
			continue
		}

		// Parse entity line: #123=IFCENTITY('guid',$,'name','description',...);
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}

		entityID := strings.TrimSpace(parts[0])
		entityData := strings.TrimSpace(parts[1])

		// Extract entity type and properties
		if match := regexp.MustCompile(`^(\w+)\((.*)\);?$`).FindStringSubmatch(entityData); match != nil {
			entityType := match[1]
			propertiesStr := match[2]

			entity := IFCEntity{
				ID:         entityID,
				Type:       entityType,
				Properties: make(map[string]string),
			}

			// Parse properties
			props := c.parseIFCProperties(propertiesStr)
			if len(props) > 0 {
				entity.GUID = strings.Trim(props[0], "'")
			}
			if len(props) > 2 {
				entity.Name = strings.Trim(props[2], "'")
			}
			if len(props) > 3 {
				entity.Description = strings.Trim(props[3], "'")
			}

			// Store specific properties based on entity type
			switch entityType {
			case "IFCBUILDINGSTOREY":
				if len(props) > 9 {
					entity.Properties["elevation"] = strings.Trim(props[9], ".")
				}
			}

			entities = append(entities, entity)
		}
	}

	return entities
}

func (c *ImprovedIFCConverter) parseIFCProperties(propertiesStr string) []string {
	var props []string
	var current strings.Builder
	inQuote := false
	parenDepth := 0

	for _, ch := range propertiesStr {
		switch ch {
		case '\'':
			inQuote = !inQuote
			current.WriteRune(ch)
		case '(':
			parenDepth++
			current.WriteRune(ch)
		case ')':
			parenDepth--
			current.WriteRune(ch)
		case ',':
			if !inQuote && parenDepth == 0 {
				props = append(props, strings.TrimSpace(current.String()))
				current.Reset()
			} else {
				current.WriteRune(ch)
			}
		default:
			current.WriteRune(ch)
		}
	}

	if current.Len() > 0 {
		props = append(props, strings.TrimSpace(current.String()))
	}

	return props
}

func (c *ImprovedIFCConverter) getEntitiesByType(entities []IFCEntity, entityType string) []IFCEntity {
	var result []IFCEntity
	for _, entity := range entities {
		if entity.Type == entityType {
			result = append(result, entity)
		}
	}
	return result
}

func (c *ImprovedIFCConverter) extractRoomNumber(name string) string {
	// Try to extract room number from name like "Room 101", "101", etc.
	if match := regexp.MustCompile(`(\d+)`).FindString(name); match != "" {
		return match
	}
	return name
}

func (c *ImprovedIFCConverter) findSpaceFloor(spaceEntity IFCEntity, entities []IFCEntity, numFloors int) int {
	// Simple heuristic: try to match based on name patterns or return based on order
	spaceName := strings.ToLower(spaceEntity.Name)

	// Look for floor indicators in space name
	if strings.Contains(spaceName, "ground") || strings.Contains(spaceName, "first") || strings.Contains(spaceName, "1") {
		return 0
	}
	if strings.Contains(spaceName, "second") || strings.Contains(spaceName, "2") {
		return 1
	}

	// Default to distributing spaces across floors
	spaceNum := 0
	if match := regexp.MustCompile(`(\d+)`).FindString(spaceEntity.Name); match != "" {
		if num, err := strconv.Atoi(match); err == nil {
			spaceNum = num
		}
	}

	if numFloors > 0 {
		return spaceNum % numFloors
	}
	return 0
}

func (c *ImprovedIFCConverter) findEquipmentLocation(eqEntity IFCEntity, entities []IFCEntity, building *Building) (spaceIdx, floorIdx int) {
	// Try to match equipment to spaces based on naming patterns
	eqName := strings.ToLower(eqEntity.Name)

	for f, floor := range building.Floors {
		for r, room := range floor.Rooms {
			roomName := strings.ToLower(room.Name)
			roomNumber := strings.ToLower(room.Number)

			// Check if equipment name contains room number or name
			if strings.Contains(eqName, roomNumber) || strings.Contains(eqName, roomName) {
				return r, f
			}

			// Check for room number patterns in equipment name
			if roomNum := regexp.MustCompile(`(\d+)`).FindString(room.Number); roomNum != "" {
				if strings.Contains(eqName, roomNum) {
					return r, f
				}
			}
		}
	}

	return -1, -1
}

func (c *ImprovedIFCConverter) mapIFCToEquipmentType(ifcType string) string {
	switch ifcType {
	case "IFCFLOWCONTROLLER":
		return "hvac"
	case "IFCFLOWTERMINAL":
		return "hvac"
	case "IFCENERGYCONVERSIONDEVICE":
		return "hvac"
	case "IFCFLOWMOVINGDEVICE":
		return "hvac"
	case "IFCFURNISHINGELEMENT":
		return "furniture"
	case "IFCDISTRIBUTIONELEMENT":
		return "mechanical"
	case "IFCBUILDINGELEMENTPROXY":
		return "equipment"
	case "IFCFLOWFITTING":
		return "plumbing"
	case "IFCFLOWSTORAGEDEVICE":
		return "storage"
	default:
		return "equipment"
	}
}