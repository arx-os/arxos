package converter

import (
	"bufio"
	"fmt"
	"io"
	"regexp"
	"strconv"
	"strings"
)

// IFCConverter handles IFC (Industry Foundation Classes) files
type IFCConverter struct{}

func NewIFCConverter() *IFCConverter {
	return &IFCConverter{}
}

func (c *IFCConverter) GetFormat() string {
	return "ifc"
}

func (c *IFCConverter) GetDescription() string {
	return "Industry Foundation Classes (IFC) - Open BIM standard"
}

func (c *IFCConverter) CanConvert(filename string) bool {
	lower := strings.ToLower(filename)
	return strings.HasSuffix(lower, ".ifc") ||
		strings.HasSuffix(lower, ".ifcxml") ||
		strings.HasSuffix(lower, ".ifczip")
}

func (c *IFCConverter) ConvertToBIM(input io.Reader, output io.Writer) error {
	building := &Building{
		Metadata: Metadata{
			Source: "IFC Import",
			Format: "IFC",
		},
		Floors: make([]Floor, 0),
	}

	// Parse IFC file
	scanner := bufio.NewScanner(input)
	ifcObjects := make(map[string]map[string]string)
	currentID := ""

	for scanner.Scan() {
		line := scanner.Text()

		// Parse IFC entities
		if strings.HasPrefix(line, "#") {
			// Extract entity ID
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				currentID = strings.TrimSpace(parts[0])
				entityData := strings.TrimSpace(parts[1])

				// Parse entity type and properties
				if match := regexp.MustCompile(`^(\w+)\((.*)\);?$`).FindStringSubmatch(entityData); match != nil {
					entityType := match[1]
					properties := parseIFCProperties(match[2])

					if ifcObjects[entityType] == nil {
						ifcObjects[entityType] = make(map[string]string)
					}
					ifcObjects[entityType][currentID] = properties

					// Process based on entity type
					switch entityType {
					case "IFCBUILDING":
						if name := extractIFCString(properties); name != "" {
							building.Name = name
						}

					case "IFCBUILDINGSTOREY":
						floor := Floor{
							ID:    fmt.Sprintf("%d", len(building.Floors)+1),
							Name:  extractIFCString(properties),
							Level: len(building.Floors),
							Rooms: make([]Room, 0),
						}

						// Extract elevation if available
						if elev := extractIFCNumber(properties); elev != 0 {
							floor.Elevation = elev
						}

						building.Floors = append(building.Floors, floor)

					case "IFCSPACE":
						if len(building.Floors) > 0 {
							room := Room{
								ID:     currentID,
								Number: fmt.Sprintf("%d", len(building.Floors[len(building.Floors)-1].Rooms)+100),
								Name:   extractIFCString(properties),
								Type:   "space",
							}
							building.Floors[len(building.Floors)-1].Rooms = append(
								building.Floors[len(building.Floors)-1].Rooms, room)
						}

					case "IFCBUILDINGELEMENTPROXY", "IFCFURNISHINGELEMENT",
						"IFCDISTRIBUTIONELEMENT", "IFCFLOWTERMINAL", "IFCFLOWCONTROLLER":
						// These are equipment
						name := extractIFCString(properties)
						if name != "" {
							if len(building.Floors) > 0 &&
								len(building.Floors[len(building.Floors)-1].Rooms) > 0 {
								eq := Equipment{
									ID:     currentID,
									Tag:    name,
									Name:   name,
									Type:   mapIFCToEquipmentType(entityType),
									Status: "operational",
								}

								floorIdx := len(building.Floors) - 1
								roomIdx := len(building.Floors[floorIdx].Rooms) - 1
								building.Floors[floorIdx].Rooms[roomIdx].Equipment = append(
									building.Floors[floorIdx].Rooms[roomIdx].Equipment, eq)
							}
						}
					}
				}
			}
		}
	}

	// Convert to BIM format
	bimText := building.ToBIM()
	_, err := output.Write([]byte(bimText))
	return err
}

func (c *IFCConverter) ConvertFromBIM(input io.Reader, output io.Writer) error {
	// Generate IFC from BIM
	// This would create a compliant IFC file
	// For now, we'll create a simplified IFC structure

	fmt.Fprintln(output, "ISO-10303-21;")
	fmt.Fprintln(output, "HEADER;")
	fmt.Fprintln(output, "FILE_DESCRIPTION(('ArxOS Export'),'2;1');")
	fmt.Fprintln(output, "FILE_NAME('export.ifc','',(''),('ArxOS'),'','','');")
	fmt.Fprintln(output, "FILE_SCHEMA(('IFC4'));")
	fmt.Fprintln(output, "ENDSEC;")
	fmt.Fprintln(output, "DATA;")

	// Parse BIM and generate IFC entities
	// ... (simplified for now)

	fmt.Fprintln(output, "ENDSEC;")
	fmt.Fprintln(output, "END-ISO-10303-21;")

	return nil
}

func (c *IFCConverter) ConvertToDB(input io.Reader, db interface{}) error {
	// Legacy converter - use ImprovedIFCConverter for direct database import
	return fmt.Errorf("direct database import not implemented in legacy converter")
}

// Helper functions for IFC parsing

func parseIFCProperties(props string) string {
	// Simplify IFC property parsing
	// In reality, this would be much more complex
	return props
}

func extractIFCString(props string) string {
	// Extract string values from IFC properties
	// IFC format: 'GUID',$,'Name','Description',...
	parts := splitIFCProperties(props)

	// Name is typically in position 2 (0-indexed)
	if len(parts) > 2 {
		name := strings.Trim(parts[2], " '\"")
		if name != "" && name != "$" {
			return name
		}
	}

	// Description is typically in position 3
	if len(parts) > 3 {
		desc := strings.Trim(parts[3], " '\"")
		if desc != "" && desc != "$" {
			return desc
		}
	}

	// Fall back to first non-empty string
	for _, part := range parts {
		cleaned := strings.Trim(part, " '\"")
		if cleaned != "" && cleaned != "$" && !strings.HasPrefix(cleaned, "#") {
			// Skip GUIDs (16+ char hex strings)
			if len(cleaned) < 16 {
				return cleaned
			}
		}
	}

	return ""
}

func extractIFCNumber(props string) float64 {
	// Extract numeric values from IFC properties
	if match := regexp.MustCompile(`([0-9.]+)`).FindStringSubmatch(props); match != nil {
		if val, err := strconv.ParseFloat(match[1], 64); err == nil {
			return val
		}
	}
	return 0
}

func mapIFCToEquipmentType(ifcType string) string {
	switch ifcType {
	case "IFCFLOWTERMINAL":
		return "hvac"
	case "IFCFURNISHINGELEMENT":
		return "furniture"
	case "IFCDISTRIBUTIONELEMENT":
		return "mechanical"
	case "IFCFLOWCONTROLLER":
		return "hvac"
	default:
		return "equipment"
	}
}

func splitIFCProperties(properties string) []string {
	var parts []string
	var current strings.Builder
	inQuote := false
	parenDepth := 0

	for _, ch := range properties {
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
				parts = append(parts, current.String())
				current.Reset()
			} else {
				current.WriteRune(ch)
			}
		default:
			current.WriteRune(ch)
		}
	}

	if current.Len() > 0 {
		parts = append(parts, current.String())
	}

	return parts
}
