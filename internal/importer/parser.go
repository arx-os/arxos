package importer

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// IFCParser handles parsing of IFC (Industry Foundation Classes) files
type IFCParser struct {
	entities map[string]*IFCEntity
	header   *IFCHeader
}

// IFCHeader contains metadata from the IFC file header
type IFCHeader struct {
	Description    []string `json:"description"`
	ImplementationLevel string   `json:"implementation_level"`
	Name           string   `json:"name"`
	TimeStamp      string   `json:"time_stamp"`
	Author         []string `json:"author"`
	Organization   []string `json:"organization"`
	PreprocessorVersion string `json:"preprocessor_version"`
	OriginatingSystem string   `json:"originating_system"`
	Authorization  string   `json:"authorization"`
	SchemaIdentifiers []string `json:"schema_identifiers"`
}

// IFCEntity represents a single entity in an IFC file
type IFCEntity struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	Attributes []interface{}          `json:"attributes"`
	References map[string]*IFCEntity  `json:"-"`
}

// NewIFCParser creates a new IFC parser
func NewIFCParser() *IFCParser {
	return &IFCParser{
		entities: make(map[string]*IFCEntity),
		header:   &IFCHeader{},
	}
}

// ParseFile parses an IFC file and converts it to an ArxOS floor plan
func (p *IFCParser) ParseFile(filePath string) (*models.FloorPlan, error) {
	logger.Info("Parsing IFC file: %s", filePath)
	
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open IFC file: %w", err)
	}
	defer file.Close()
	
	return p.Parse(file, filePath)
}

// Parse parses an IFC file from an io.Reader
func (p *IFCParser) Parse(reader io.Reader, sourceName string) (*models.FloorPlan, error) {
	scanner := bufio.NewScanner(reader)
	
	// Parse the file in sections
	var section string
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		
		// Skip empty lines and comments
		if line == "" || strings.HasPrefix(line, "/*") {
			continue
		}
		
		// Detect sections
		if line == "HEADER;" {
			section = "HEADER"
			continue
		} else if line == "DATA;" {
			section = "DATA"
			continue
		} else if line == "ENDSEC;" {
			section = ""
			continue
		}
		
		// Parse content based on section
		switch section {
		case "HEADER":
			if err := p.parseHeaderLine(line); err != nil {
				logger.Warn("Failed to parse header line: %s", line)
			}
		case "DATA":
			if err := p.parseDataLine(line); err != nil {
				logger.Warn("Failed to parse data line: %s", line)
			}
		}
	}
	
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading IFC file: %w", err)
	}
	
	// Convert IFC entities to ArxOS floor plan
	return p.convertToFloorPlan(sourceName)
}

// parseHeaderLine parses a line from the HEADER section
func (p *IFCParser) parseHeaderLine(line string) error {
	// Header lines follow the pattern: KEYWORD('value1','value2',...);
	if !strings.HasSuffix(line, ";") {
		return nil // Multi-line values not supported yet
	}
	
	// Extract keyword and values
	parts := strings.SplitN(line, "(", 2)
	if len(parts) != 2 {
		return fmt.Errorf("invalid header line format: %s", line)
	}
	
	keyword := strings.TrimSpace(parts[0])
	valuesPart := strings.TrimSuffix(parts[1], ");")
	
	// Parse values (simplified parsing)
	values := p.parseStringList(valuesPart)
	
	// Store in header based on keyword
	switch keyword {
	case "FILE_DESCRIPTION":
		if len(values) >= 1 {
			p.header.Description = strings.Split(values[0], ",")
		}
		if len(values) >= 2 {
			p.header.ImplementationLevel = values[1]
		}
	case "FILE_NAME":
		if len(values) >= 1 {
			p.header.Name = values[0]
		}
		if len(values) >= 2 {
			p.header.TimeStamp = values[1]
		}
		if len(values) >= 3 {
			p.header.Author = strings.Split(values[2], ",")
		}
		if len(values) >= 4 {
			p.header.Organization = strings.Split(values[3], ",")
		}
	case "FILE_SCHEMA":
		p.header.SchemaIdentifiers = values
	}
	
	return nil
}

// parseDataLine parses a line from the DATA section
func (p *IFCParser) parseDataLine(line string) error {
	// Data lines follow the pattern: #ID=TYPE(attr1,attr2,...);
	if !strings.HasPrefix(line, "#") || !strings.HasSuffix(line, ";") {
		return nil
	}
	
	// Remove # and ;
	line = line[1 : len(line)-1]
	
	// Split at = to get ID and definition
	parts := strings.SplitN(line, "=", 2)
	if len(parts) != 2 {
		return fmt.Errorf("invalid entity line format: %s", line)
	}
	
	id := strings.TrimSpace(parts[0])
	definition := strings.TrimSpace(parts[1])
	
	// Parse entity type and attributes
	entity, err := p.parseEntity(id, definition)
	if err != nil {
		return err
	}
	
	p.entities[id] = entity
	return nil
}

// parseEntity parses an entity definition
func (p *IFCParser) parseEntity(id, definition string) (*IFCEntity, error) {
	// Extract type and attributes from TYPE(attr1,attr2,...)
	parenIndex := strings.Index(definition, "(")
	if parenIndex == -1 {
		return &IFCEntity{
			ID:         id,
			Type:       definition,
			Attributes: []interface{}{},
			References: make(map[string]*IFCEntity),
		}, nil
	}
	
	entityType := strings.TrimSpace(definition[:parenIndex])
	attributesPart := definition[parenIndex+1 : len(definition)-1]
	
	// Parse attributes (simplified parsing)
	attributes := p.parseAttributeList(attributesPart)
	
	return &IFCEntity{
		ID:         id,
		Type:       entityType,
		Attributes: attributes,
		References: make(map[string]*IFCEntity),
	}, nil
}

// parseStringList parses a comma-separated list of quoted strings
func (p *IFCParser) parseStringList(input string) []string {
	var result []string
	var current strings.Builder
	var inQuotes bool
	var escaped bool
	
	for _, char := range input {
		switch char {
		case '\\':
			if inQuotes && !escaped {
				escaped = true
				continue
			}
		case '\'':
			if !escaped {
				inQuotes = !inQuotes
				if !inQuotes {
					result = append(result, current.String())
					current.Reset()
				}
				continue
			}
		case ',':
			if !inQuotes {
				continue
			}
		}
		
		if inQuotes {
			current.WriteRune(char)
		}
		escaped = false
	}
	
	return result
}

// parseAttributeList parses a comma-separated list of attributes
func (p *IFCParser) parseAttributeList(input string) []interface{} {
	var result []interface{}
	var current strings.Builder
	var depth int
	var inQuotes bool
	var escaped bool
	
	for _, char := range input {
		switch char {
		case '\\':
			if inQuotes && !escaped {
				escaped = true
				current.WriteRune(char)
				continue
			}
		case '\'':
			if !escaped {
				inQuotes = !inQuotes
			}
		case '(':
			if !inQuotes {
				depth++
			}
		case ')':
			if !inQuotes {
				depth--
			}
		case ',':
			if !inQuotes && depth == 0 {
				result = append(result, p.parseAttribute(strings.TrimSpace(current.String())))
				current.Reset()
				continue
			}
		}
		
		current.WriteRune(char)
		escaped = false
	}
	
	// Add the last attribute
	if current.Len() > 0 {
		result = append(result, p.parseAttribute(strings.TrimSpace(current.String())))
	}
	
	return result
}

// parseAttribute parses a single attribute value
func (p *IFCParser) parseAttribute(attr string) interface{} {
	attr = strings.TrimSpace(attr)
	
	// Handle null values
	if attr == "$" || attr == "*" {
		return nil
	}
	
	// Handle string values
	if strings.HasPrefix(attr, "'") && strings.HasSuffix(attr, "'") {
		return attr[1 : len(attr)-1]
	}
	
	// Handle entity references
	if strings.HasPrefix(attr, "#") {
		return attr // Keep as reference for later resolution
	}
	
	// Handle boolean values
	if attr == ".T." {
		return true
	}
	if attr == ".F." {
		return false
	}
	
	// Handle numeric values
	if value, err := strconv.ParseFloat(attr, 64); err == nil {
		return value
	}
	if value, err := strconv.ParseInt(attr, 10, 64); err == nil {
		return value
	}
	
	// Handle enums (like .NOTDEFINED.)
	if strings.HasPrefix(attr, ".") && strings.HasSuffix(attr, ".") {
		return attr[1 : len(attr)-1]
	}
	
	// Return as string if nothing else matches
	return attr
}

// convertToFloorPlan converts parsed IFC entities to an ArxOS floor plan
func (p *IFCParser) convertToFloorPlan(sourceName string) (*models.FloorPlan, error) {
	logger.Info("Converting IFC entities to floor plan")
	
	// Extract building name from header or use source name
	buildingName := "IFC Imported Building"
	if p.header.Name != "" {
		buildingName = p.header.Name
	}
	
	now := time.Now()
	plan := &models.FloorPlan{
		Name:      extractFileName(sourceName),
		Building:  buildingName,
		Level:     1, // Default to level 1, will enhance with multi-floor support
		Rooms:     []*models.Room{},
		Equipment: []*models.Equipment{},
		CreatedAt: &now,
		UpdatedAt: &now,
	}
	
	// Convert spaces to rooms
	rooms := p.extractSpaces()
	for i := range rooms {
		plan.Rooms = append(plan.Rooms, &rooms[i])
	}
	
	// Convert building elements to equipment
	equipment := p.extractEquipment()
	for i := range equipment {
		plan.Equipment = append(plan.Equipment, &equipment[i])
	}
	
	logger.Info("Converted IFC file to floor plan: %d rooms, %d equipment items", 
		len(plan.Rooms), len(plan.Equipment))
	
	return plan, nil
}

// extractSpaces extracts room information from IFC spaces
func (p *IFCParser) extractSpaces() []models.Room {
	var rooms []models.Room
	
	for _, entity := range p.entities {
		if entity.Type == "IFCSPACE" {
			room := p.convertSpace(entity)
			if room != nil {
				rooms = append(rooms, *room)
			}
		}
	}
	
	// If no spaces found, create a default room
	if len(rooms) == 0 {
		rooms = append(rooms, models.Room{
			ID:   "ifc_space_1",
			Name: "Imported Space",
			Bounds: models.Bounds{
				MinX: 0, MinY: 0,
				MaxX: 100, MaxY: 100,
			},
			Equipment: []string{},
		})
	}
	
	return rooms
}

// convertSpace converts an IFCSPACE entity to a Room
func (p *IFCParser) convertSpace(entity *IFCEntity) *models.Room {
	// Get space name from attributes
	name := "Space"
	if len(entity.Attributes) > 2 {
		if nameAttr, ok := entity.Attributes[2].(string); ok && nameAttr != "" {
			name = nameAttr
		}
	}
	
	// Generate bounds (simplified - real IFC would need geometric processing)
	bounds := models.Bounds{
		MinX: 0, MinY: 0,
		MaxX: 50, MaxY: 50, // Default size
	}
	
	return &models.Room{
		ID:        fmt.Sprintf("ifc_space_%s", entity.ID),
		Name:      name,
		Bounds:    bounds,
		Equipment: []string{},
	}
}

// extractEquipment extracts equipment from IFC building elements
func (p *IFCParser) extractEquipment() []models.Equipment {
	var equipment []models.Equipment
	
	// Common IFC types that represent equipment
	equipmentTypes := map[string]string{
		"IFCELECTRICDISTRIBUTIONBOARD": "panel",
		"IFCELECTRICALDISTRIBUTIONPOINT": "distribution_point",
		"IFCELECTRICAPPLIANCEUNIT": "appliance",
		"IFCELECTRICFLOWTREATMENTDEVICE": "treatment_device",
		"IFCELECTRICHEATER": "heater",
		"IFCELECTRICMOTORCONNECTION": "motor",
		"IFCELECTRICALTIMECONTROL": "timer",
		"IFCJUNCTIONBOX": "junction_box",
		"IFCOUTLET": "outlet",
		"IFCSWITCHINGDEVICE": "switch",
		"IFCLIGHTFIXTURE": "light_fixture",
		"IFCALARM": "alarm",
		"IFCAUDIOVISUALAPPLIANCE": "av_equipment",
		"IFCCOMMUNICATIONSAPPLIANCE": "communications",
		"IFCFIRESUPPRESSIONTERMINAL": "fire_suppression",
		"IFCLAMP": "lamp",
		"IFCMEDICALDEVICE": "medical_device",
		"IFCUNITARYEQUIPMENT": "unitary_equipment",
	}
	
	for _, entity := range p.entities {
		if equipmentType, exists := equipmentTypes[entity.Type]; exists {
			equip := p.convertEquipment(entity, equipmentType)
			if equip != nil {
				equipment = append(equipment, *equip)
			}
		}
	}
	
	// If no equipment found, add a note
	if len(equipment) == 0 {
		equipment = append(equipment, models.Equipment{
			ID:   "ifc_note",
			Name: "IFC file processed - use 'arx add' to add equipment",
			Type: "note",
			Location: &models.Point{X: 25, Y: 25},
			Status: models.StatusUnknown,
			Notes: "Equipment can be manually added using ArxOS commands",
		})
	}
	
	return equipment
}

// convertEquipment converts an IFC building element to Equipment
func (p *IFCParser) convertEquipment(entity *IFCEntity, equipmentType string) *models.Equipment {
	// Get equipment name from attributes
	name := equipmentType
	if len(entity.Attributes) > 2 {
		if nameAttr, ok := entity.Attributes[2].(string); ok && nameAttr != "" {
			name = nameAttr
		}
	}
	
	// Generate location (simplified - real IFC would need geometric processing)
	x := float64(25 + (len(p.entities)%8)*10)
	y := float64(25 + (len(p.entities)/8)*10)
	
	return &models.Equipment{
		ID:       fmt.Sprintf("ifc_%s_%s", equipmentType, entity.ID),
		Name:     name,
		Type:     equipmentType,
		Location: &models.Point{X: x, Y: y},
		Status:   models.StatusUnknown,
		Notes:    fmt.Sprintf("Imported from IFC entity %s", entity.ID),
		MarkedAt: func() *time.Time { t := time.Now(); return &t }(),
	}
}

// extractFileName extracts filename without extension
func extractFileName(path string) string {
	// Get base filename
	filename := path
	if lastSlash := strings.LastIndex(path, "/"); lastSlash != -1 {
		filename = path[lastSlash+1:]
	}
	if lastSlash := strings.LastIndex(filename, "\\"); lastSlash != -1 {
		filename = filename[lastSlash+1:]
	}
	
	// Remove extension
	if lastDot := strings.LastIndex(filename, "."); lastDot != -1 {
		filename = filename[:lastDot]
	}
	
	return filename
}

// GetHeader returns the parsed IFC header information
func (p *IFCParser) GetHeader() *IFCHeader {
	return p.header
}

// GetEntities returns all parsed IFC entities
func (p *IFCParser) GetEntities() map[string]*IFCEntity {
	return p.entities
}

// GetStats returns parsing statistics
func (p *IFCParser) GetStats() map[string]interface{} {
	entityTypes := make(map[string]int)
	for _, entity := range p.entities {
		entityTypes[entity.Type]++
	}
	
	return map[string]interface{}{
		"total_entities": len(p.entities),
		"entity_types":   entityTypes,
		"header_info":    p.header,
	}
}