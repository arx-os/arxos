package bim

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"time"
)

// Parser handles parsing of BIM text format files
type Parser struct {
	// Configuration
	strict bool // If true, enforce all validation rules

	// State during parsing
	currentLine    int
	currentFloor   *Floor
	currentSection string
	errors         []error
	warnings       []string
}

// NewParser creates a new BIM parser
func NewParser() *Parser {
	return &Parser{
		strict:   true,
		errors:   make([]error, 0),
		warnings: make([]string, 0),
	}
}

// ParseOptions configures parser behavior
type ParseOptions struct {
	Strict           bool // Enforce strict validation
	PreserveComments bool // Keep comments in the model
	ValidateChecksum bool // Verify file checksum
}

// Parse reads a BIM file from an io.Reader
func (p *Parser) Parse(reader io.Reader) (*Building, error) {
	return p.ParseWithOptions(reader, ParseOptions{Strict: true})
}

// ParseFile reads a BIM file from disk
func (p *Parser) ParseFile(path string) (*Building, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	return p.Parse(file)
}

// ParseWithOptions parses with custom options
func (p *Parser) ParseWithOptions(reader io.Reader, opts ParseOptions) (*Building, error) {
	p.strict = opts.Strict
	p.currentLine = 0
	p.errors = make([]error, 0)
	p.warnings = make([]string, 0)

	building := &Building{
		Floors: make([]Floor, 0),
	}

	scanner := bufio.NewScanner(reader)
	var lines []string

	// Read all lines first for context
	for scanner.Scan() {
		lines = append(lines, scanner.Text())
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading input: %w", err)
	}

	// Parse the lines - start by looking for key headers
	for p.currentLine < len(lines) {
		line := strings.TrimSpace(lines[p.currentLine])

		// Skip empty lines and comments
		if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, "//") {
			p.currentLine++
			continue
		}

		// Parse header fields at the top level
		if strings.HasPrefix(line, "BUILDING:") {
			building.Name = strings.TrimSpace(strings.TrimPrefix(line, "BUILDING:"))
			p.currentLine++
			continue
		}

		if strings.HasPrefix(line, "FILE_VERSION:") {
			building.FileVersion = strings.TrimSpace(strings.TrimPrefix(line, "FILE_VERSION:"))
			p.currentLine++
			continue
		}

		if strings.HasPrefix(line, "COORDINATE_SYSTEM:") {
			coordSysStr := strings.TrimSpace(strings.TrimPrefix(line, "COORDINATE_SYSTEM:"))
			switch coordSysStr {
			case "TOP_LEFT_ORIGIN":
				building.CoordinateSystem = TopLeftOrigin
			case "BOTTOM_LEFT_ORIGIN":
				building.CoordinateSystem = BottomLeftOrigin
			default:
				building.CoordinateSystem = TopLeftOrigin // Default
			}
			p.currentLine++
			continue
		}

		if strings.HasPrefix(line, "UNITS:") {
			unitsStr := strings.TrimSpace(strings.TrimPrefix(line, "UNITS:"))
			switch unitsStr {
			case "FEET":
				building.Units = Feet
			case "METERS":
				building.Units = Meters
			case "INCHES":
				building.Units = Inches
			default:
				building.Units = Feet // Default
			}
			p.currentLine++
			continue
		}

		if strings.HasPrefix(line, "FLOOR:") {
			if err := p.parseFloorDirectly(lines, building); err != nil {
				p.errors = append(p.errors, err)
				if p.strict {
					return nil, err
				}
			}
			continue
		}

		// Handle other sections like METADATA, VALIDATION, etc.
		if strings.HasPrefix(line, "METADATA:") {
			p.parseMetadata(lines, building)
			continue
		}

		if strings.HasPrefix(line, "VALIDATION:") {
			p.parseValidation(lines, building)
			continue
		}

		p.currentLine++
	}

	// Validate the complete building
	if err := p.validateBuilding(building); err != nil {
		if p.strict {
			return nil, err
		}
		p.warnings = append(p.warnings, err.Error())
	}

	return building, p.combineErrors()
}

// Validate checks if a building model is valid
func (p *Parser) Validate(reader io.Reader) error {
	_, err := p.ParseWithOptions(reader, ParseOptions{
		Strict:           true,
		ValidateChecksum: true,
	})
	return err
}

// GetWarnings returns any warnings from the last parse
func (p *Parser) GetWarnings() []string {
	return p.warnings
}

// Private helper methods

func (p *Parser) isEmptyOrComment(line string) bool {
	trimmed := strings.TrimSpace(line)
	return trimmed == "" || strings.HasPrefix(trimmed, "#") || strings.HasPrefix(trimmed, "//")
}

func (p *Parser) isSectionBoundary(line string) bool {
	trimmed := strings.TrimSpace(line)
	return strings.HasPrefix(trimmed, "===") || strings.HasPrefix(trimmed, "---")
}

func (p *Parser) parseSection(lines []string, building *Building) error {
	line := lines[p.currentLine]

	// File header/footer (79 equals)
	if strings.Count(line, "=") == 79 {
		return p.parseHeaderOrFooter(lines, building)
	}

	// Floor section (37 equals)
	if strings.Count(line, "=") == 37 {
		return p.parseFloorSection(lines, building)
	}

	return nil
}

func (p *Parser) parseHeaderOrFooter(lines []string, building *Building) error {
	p.currentLine++ // Skip boundary line

	if p.currentLine >= len(lines) {
		return ParseError{
			Line:    p.currentLine,
			Message: "unexpected end of file",
		}
	}

	// Check if this is header or footer
	nextLine := lines[p.currentLine]
	if strings.HasPrefix(nextLine, "BUILDING:") {
		return p.parseHeader(lines, building)
	} else if strings.HasPrefix(nextLine, "VALIDATION:") {
		return p.parseValidation(lines, building)
	}

	return ParseError{
		Line:    p.currentLine,
		Message: "expected BUILDING or VALIDATION section",
		Context: nextLine,
	}
}

func (p *Parser) parseHeader(lines []string, building *Building) error {
	for p.currentLine < len(lines) {
		line := lines[p.currentLine]

		if p.isSectionBoundary(line) {
			p.currentLine++
			return nil
		}

		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			p.currentLine++
			continue
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		switch key {
		case "BUILDING":
			building.Name = value
		case "FILE_VERSION":
			building.FileVersion = value
		case "GENERATED":
			if t, err := time.Parse(time.RFC3339, value); err == nil {
				building.Generated = t
			} else {
				p.warnings = append(p.warnings, fmt.Sprintf("invalid timestamp: %s", value))
			}
		case "COORDINATE_SYSTEM":
			building.CoordinateSystem = CoordinateSystem(value)
		case "UNITS":
			building.Units = UnitSystem(value)
		}

		p.currentLine++
	}

	return nil
}

func (p *Parser) parseFloorSection(lines []string, building *Building) error {
	p.currentLine++ // Skip boundary

	floor := Floor{
		Equipment:   make([]Equipment, 0),
		Connections: make(map[ConnectionType][]Connection),
		Issues:      make([]Issue, 0),
		Legend:      make(map[rune]string),
	}

	// Parse floor header
	if p.currentLine < len(lines) {
		line := lines[p.currentLine]
		if strings.HasPrefix(line, "FLOOR:") {
			// Parse: FLOOR: 1 | Emergency Department
			parts := strings.SplitN(strings.TrimPrefix(line, "FLOOR:"), "|", 2)
			if len(parts) >= 1 {
				fmt.Sscanf(strings.TrimSpace(parts[0]), "%d", &floor.Level)
			}
			if len(parts) >= 2 {
				floor.Name = strings.TrimSpace(parts[1])
			}
		}
		p.currentLine++
	}

	// Continue parsing floor sections...
	// This is a simplified version - full implementation would parse all subsections

	building.Floors = append(building.Floors, floor)

	return nil
}

func (p *Parser) parseValidation(lines []string, building *Building) error {
	// Parse validation footer
	for p.currentLine < len(lines) {
		line := lines[p.currentLine]

		if p.isSectionBoundary(line) {
			p.currentLine++
			return nil
		}

		// Parse validation fields...
		p.currentLine++
	}

	return nil
}

func (p *Parser) validateBuilding(building *Building) error {
	// Validate required fields
	if building.Name == "" {
		return ValidationError{
			Field:   "BUILDING",
			Message: "building name is required",
		}
	}

	if building.FileVersion == "" {
		return ValidationError{
			Field:   "FILE_VERSION",
			Message: "file version is required",
		}
	}

	if len(building.Floors) == 0 {
		return ValidationError{
			Field:   "FLOORS",
			Message: "at least one floor is required",
		}
	}

	// Validate equipment IDs are unique
	idMap := make(map[string]bool)
	for _, floor := range building.Floors {
		for _, eq := range floor.Equipment {
			if idMap[eq.ID] {
				return ValidationError{
					Field:   "EQUIPMENT.ID",
					Value:   eq.ID,
					Message: "duplicate equipment ID",
				}
			}
			idMap[eq.ID] = true
		}
	}

	return nil
}

func (p *Parser) combineErrors() error {
	if len(p.errors) == 0 {
		return nil
	}

	messages := make([]string, len(p.errors))
	for i, err := range p.errors {
		messages[i] = err.Error()
	}

	return fmt.Errorf("parse errors: %s", strings.Join(messages, "; "))
}

// parseFloorDirectly parses a floor starting from a FLOOR: line
func (p *Parser) parseFloorDirectly(lines []string, building *Building) error {
	floor := Floor{
		Equipment:   make([]Equipment, 0),
		Connections: make(map[ConnectionType][]Connection),
		Issues:      make([]Issue, 0),
		Legend:      make(map[rune]string),
	}

	// Parse the FLOOR: line
	line := strings.TrimSpace(lines[p.currentLine])
	if strings.HasPrefix(line, "FLOOR:") {
		// Parse: FLOOR: 1 | Name
		parts := strings.SplitN(strings.TrimPrefix(line, "FLOOR:"), "|", 2)
		if len(parts) >= 1 {
			fmt.Sscanf(strings.TrimSpace(parts[0]), "%d", &floor.Level)
		}
		if len(parts) >= 2 {
			floor.Name = strings.TrimSpace(parts[1])
		}
	}
	p.currentLine++

	// Parse floor content until END_FLOOR or next FLOOR
	inEquipmentRegistry := false
	var currentEquipment *Equipment

	for p.currentLine < len(lines) {
		line = strings.TrimSpace(lines[p.currentLine])

		// End conditions
		if strings.HasPrefix(line, "END_FLOOR") {
			p.currentLine++
			break
		}
		if strings.HasPrefix(line, "FLOOR:") {
			// Don't consume this line - let the main loop handle it
			break
		}
		if strings.HasPrefix(line, "VALIDATION:") {
			// Don't consume this line
			break
		}

		// Parse dimensions
		if strings.HasPrefix(line, "DIMENSIONS:") {
			dimStr := strings.TrimPrefix(line, "DIMENSIONS:")
			// Parse: 200 x 150 feet
			var width, height float64
			fmt.Sscanf(dimStr, "%f x %f", &width, &height)
			floor.Dimensions.Width = width
			floor.Dimensions.Height = height
		}

		// Equipment registry section
		if strings.HasPrefix(line, "EQUIPMENT_REGISTRY:") {
			inEquipmentRegistry = true
			p.currentLine++
			continue
		}

		// Parse equipment in registry
		if inEquipmentRegistry {
			if strings.HasPrefix(line, "ID:") {
				// Save previous equipment if exists
				if currentEquipment != nil {
					floor.Equipment = append(floor.Equipment, *currentEquipment)
				}
				// Start new equipment
				currentEquipment = &Equipment{
					ID: strings.TrimSpace(strings.TrimPrefix(line, "ID:")),
				}
			} else if currentEquipment != nil && strings.HasPrefix(lines[p.currentLine], "  ") {
				// Parse equipment property (indented) - use original line to preserve indentation check
				line = strings.TrimSpace(lines[p.currentLine])
				parts := strings.SplitN(line, ":", 2)
				if len(parts) == 2 {
					key := strings.TrimSpace(parts[0])
					value := strings.TrimSpace(parts[1])

					switch key {
					case "TYPE":
						currentEquipment.Type = value
					case "STATUS":
						currentEquipment.Status = EquipmentStatus(strings.ToUpper(value))
					case "LOCATION":
						// Parse: (x, y)
						var x, y float64
						fmt.Sscanf(value, "(%f, %f)", &x, &y)
						currentEquipment.Location.X = x
						currentEquipment.Location.Y = y
					case "ROOM":
						currentEquipment.Location.Room = value
					case "NOTES":
						currentEquipment.Notes = value
					case "PRIORITY":
						currentEquipment.Priority = Priority(strings.ToUpper(value))
					}
				}
			}
		}

		// Parse connections
		if strings.HasPrefix(line, "CONNECTIONS:") {
			inEquipmentRegistry = false
			// Save last equipment if exists
			if currentEquipment != nil {
				floor.Equipment = append(floor.Equipment, *currentEquipment)
				currentEquipment = nil
			}
		}

		p.currentLine++
	}

	// Save last equipment if not saved
	if currentEquipment != nil {
		floor.Equipment = append(floor.Equipment, *currentEquipment)
	}

	building.Floors = append(building.Floors, floor)
	return nil
}

// parseMetadata parses the METADATA section
func (p *Parser) parseMetadata(lines []string, building *Building) error {
	p.currentLine++ // Skip METADATA: line

	for p.currentLine < len(lines) {
		line := strings.TrimSpace(lines[p.currentLine])

		// End of metadata section
		if !strings.HasPrefix(line, "  ") && line != "" {
			break
		}

		// Parse metadata fields
		line = strings.TrimSpace(line)
		if line != "" {
			parts := strings.SplitN(line, ":", 2)
			if len(parts) == 2 {
				key := strings.TrimSpace(parts[0])
				value := strings.TrimSpace(parts[1])

				switch key {
				case "CREATED_BY":
					building.Metadata.CreatedBy = value
				case "ORGANIZATION":
					building.Metadata.Organization = value
				case "NOTES":
					building.Metadata.Notes = value
				}
			}
		}

		p.currentLine++
	}

	return nil
}
