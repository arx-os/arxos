package bas

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// CSVParser parses BAS point list exports from various systems
type CSVParser struct{}

// NewCSVParser creates a new CSV parser
func NewCSVParser() *CSVParser {
	return &CSVParser{}
}

// ParsedBASData represents parsed BAS data from CSV
type ParsedBASData struct {
	Points      []ParsedBASPoint
	RowCount    int
	ParseErrors []string
}

// ParsedBASPoint represents a BAS point from CSV before domain entity creation
type ParsedBASPoint struct {
	PointName      string
	DeviceID       string
	ObjectType     string
	ObjectInstance *int
	Description    string
	Units          string
	PointType      string
	LocationText   string
	MinValue       *float64
	MaxValue       *float64
	Writeable      bool
}

// ParseCSV parses a BAS CSV export file
func (p *CSVParser) ParseCSV(filePath string) (*ParsedBASData, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	reader.TrimLeadingSpace = true
	reader.FieldsPerRecord = -1 // Allow variable number of fields

	records, err := reader.ReadAll()
	if err != nil {
		return nil, fmt.Errorf("failed to read CSV: %w", err)
	}

	if len(records) < 2 {
		return nil, fmt.Errorf("CSV file is empty or has no data rows (need header + at least 1 data row)")
	}

	// Parse header to find column positions
	header := records[0]
	columns := p.mapColumns(header)

	// Validate required columns exist
	if err := p.validateColumns(columns); err != nil {
		return nil, err
	}

	// Parse data rows
	result := &ParsedBASData{
		Points:      make([]ParsedBASPoint, 0, len(records)-1),
		RowCount:    len(records) - 1,
		ParseErrors: make([]string, 0),
	}

	for i := 1; i < len(records); i++ {
		record := records[i]

		// Skip empty rows
		if p.isEmptyRow(record) {
			continue
		}

		point, err := p.parseRow(record, columns, i+1)
		if err != nil {
			result.ParseErrors = append(result.ParseErrors, fmt.Sprintf("Row %d: %v", i+1, err))
			continue
		}

		result.Points = append(result.Points, point)
	}

	return result, nil
}

// mapColumns finds column positions by header names
func (p *CSVParser) mapColumns(header []string) map[string]int {
	columns := make(map[string]int)

	for i, col := range header {
		colLower := strings.ToLower(strings.TrimSpace(col))

		// Point name variants
		if p.matchesAny(colLower, []string{"point name", "pointname", "point_name", "name", "point id", "pointid"}) {
			columns["point_name"] = i
		}

		// Device variants
		if p.matchesAny(colLower, []string{"device", "device id", "deviceid", "device_id", "device instance"}) {
			columns["device"] = i
		}

		// Object type variants
		if p.matchesAny(colLower, []string{"object type", "objecttype", "object_type", "type", "point type"}) {
			columns["object_type"] = i
		}

		// Description variants
		if p.matchesAny(colLower, []string{"description", "desc", "label"}) {
			columns["description"] = i
		}

		// Units variants
		if p.matchesAny(colLower, []string{"units", "unit", "engineering units", "eu"}) {
			columns["units"] = i
		}

		// Location variants
		if p.matchesAny(colLower, []string{"location", "room", "space", "area", "zone"}) {
			columns["location"] = i
		}

		// Optional: Min/Max values
		if p.matchesAny(colLower, []string{"min", "min value", "minimum"}) {
			columns["min_value"] = i
		}
		if p.matchesAny(colLower, []string{"max", "max value", "maximum"}) {
			columns["max_value"] = i
		}

		// Optional: Writeable
		if p.matchesAny(colLower, []string{"writeable", "writable", "read only", "readonly"}) {
			columns["writeable"] = i
		}
	}

	return columns
}

// matchesAny checks if a string matches any of the patterns
func (p *CSVParser) matchesAny(text string, patterns []string) bool {
	for _, pattern := range patterns {
		if text == pattern || strings.Contains(text, pattern) {
			return true
		}
	}
	return false
}

// validateColumns ensures required columns are present
func (p *CSVParser) validateColumns(columns map[string]int) error {
	required := []string{"point_name", "device", "object_type"}

	missing := []string{}
	for _, col := range required {
		if _, exists := columns[col]; !exists {
			missing = append(missing, col)
		}
	}

	if len(missing) > 0 {
		return fmt.Errorf("missing required columns: %v (found: %v)", missing, p.getColumnNames(columns))
	}

	return nil
}

// getColumnNames returns the column names that were found
func (p *CSVParser) getColumnNames(columns map[string]int) []string {
	names := make([]string, 0, len(columns))
	for name := range columns {
		names = append(names, name)
	}
	return names
}

// isEmptyRow checks if a row is empty
func (p *CSVParser) isEmptyRow(record []string) bool {
	for _, field := range record {
		if strings.TrimSpace(field) != "" {
			return false
		}
	}
	return true
}

// parseRow parses a single data row
func (p *CSVParser) parseRow(record []string, columns map[string]int, rowNum int) (ParsedBASPoint, error) {
	point := ParsedBASPoint{}

	// Required fields
	point.PointName = strings.TrimSpace(p.getField(record, columns["point_name"]))
	if point.PointName == "" {
		return point, fmt.Errorf("point name is required")
	}

	point.DeviceID = strings.TrimSpace(p.getField(record, columns["device"]))
	if point.DeviceID == "" {
		return point, fmt.Errorf("device ID is required")
	}

	point.ObjectType = strings.TrimSpace(p.getField(record, columns["object_type"]))
	if point.ObjectType == "" {
		return point, fmt.Errorf("object type is required")
	}

	// Optional fields
	point.Description = strings.TrimSpace(p.getField(record, columns["description"]))
	point.Units = strings.TrimSpace(p.getField(record, columns["units"]))
	point.LocationText = strings.TrimSpace(p.getField(record, columns["location"]))

	// Infer point type from object type if not provided
	point.PointType = p.inferPointType(point.ObjectType, point.Description, point.Units)

	// Parse numeric fields
	if minStr := p.getField(record, columns["min_value"]); minStr != "" {
		if minVal, err := strconv.ParseFloat(minStr, 64); err == nil {
			point.MinValue = &minVal
		}
	}

	if maxStr := p.getField(record, columns["max_value"]); maxStr != "" {
		if maxVal, err := strconv.ParseFloat(maxStr, 64); err == nil {
			point.MaxValue = &maxVal
		}
	}

	// Parse writeable (default false for safety)
	if writeableStr := strings.ToLower(p.getField(record, columns["writeable"])); writeableStr != "" {
		point.Writeable = p.parseBool(writeableStr)
	}

	return point, nil
}

// getField safely gets a field from a record by index
func (p *CSVParser) getField(record []string, index int) string {
	if index >= 0 && index < len(record) {
		return record[index]
	}
	return ""
}

// inferPointType infers the point type from available information
func (p *CSVParser) inferPointType(objectType, description, units string) string {
	objLower := strings.ToLower(objectType)
	descLower := strings.ToLower(description)
	unitsLower := strings.ToLower(units)

	// Setpoints - check FIRST before temperature (setpoints often contain "temp")
	if strings.Contains(descLower, "setpoint") || strings.Contains(descLower, " sp") || strings.HasSuffix(descLower, "sp") {
		return "setpoint"
	}

	// Temperature sensors
	if strings.Contains(descLower, "temp") || strings.Contains(unitsLower, "degf") || strings.Contains(unitsLower, "degc") {
		return "temperature"
	}

	// Pressure sensors
	if strings.Contains(descLower, "pressure") || strings.Contains(unitsLower, "psi") || strings.Contains(unitsLower, "pa") {
		return "pressure"
	}

	// Flow sensors
	if strings.Contains(descLower, "flow") || strings.Contains(unitsLower, "cfm") || strings.Contains(unitsLower, "gpm") {
		return "flow"
	}

	// Damper/valve control
	if strings.Contains(descLower, "damper") || strings.Contains(descLower, "valve") {
		return "control"
	}

	// Fan status
	if strings.Contains(descLower, "fan") || strings.Contains(descLower, "blower") {
		return "fan_status"
	}

	// Generic based on object type
	if strings.Contains(objLower, "analog") && strings.Contains(objLower, "input") {
		return "analog_sensor"
	}
	if strings.Contains(objLower, "analog") && strings.Contains(objLower, "output") {
		return "analog_control"
	}
	if strings.Contains(objLower, "binary") && strings.Contains(objLower, "input") {
		return "binary_sensor"
	}
	if strings.Contains(objLower, "binary") && strings.Contains(objLower, "output") {
		return "binary_control"
	}

	return "unknown"
}

// parseBool parses various boolean representations
func (p *CSVParser) parseBool(value string) bool {
	value = strings.ToLower(strings.TrimSpace(value))

	trueValues := []string{"true", "yes", "y", "1", "on", "enabled", "writable"}
	for _, v := range trueValues {
		if value == v {
			return true
		}
	}

	return false
}

// ToBASPoints converts parsed data to domain BASPoint entities
func (p *CSVParser) ToBASPoints(parsed *ParsedBASData, buildingID, systemID types.ID) []*domain.BASPoint {
	points := make([]*domain.BASPoint, 0, len(parsed.Points))
	now := time.Now()

	for _, parsed := range parsed.Points {
		// Generate initial path (without room - unmapped)
		// Format: /B1/BAS/[POINT-NAME]
		// Will be updated to full path when mapped to room
		basPath := fmt.Sprintf("/B1/BAS/%s", parsed.PointName)

		point := &domain.BASPoint{
			ID:          types.NewID(),
			BuildingID:  buildingID,
			BASSystemID: systemID,

			PointName:      parsed.PointName,
			Path:           basPath, // Initial unmapped path
			DeviceID:       parsed.DeviceID,
			ObjectType:     parsed.ObjectType,
			ObjectInstance: parsed.ObjectInstance,

			Description:  parsed.Description,
			Units:        parsed.Units,
			PointType:    parsed.PointType,
			LocationText: parsed.LocationText,

			Writeable: parsed.Writeable,
			MinValue:  parsed.MinValue,
			MaxValue:  parsed.MaxValue,

			Mapped:            false, // Will be set during mapping
			MappingConfidence: 0,

			ImportedAt: now,
			CreatedAt:  now,
			UpdatedAt:  now,
		}

		points = append(points, point)
	}

	return points
}

// ParseLocationText attempts to parse location text into structured components
func (p *CSVParser) ParseLocationText(locationText string) *ParsedLocation {
	if locationText == "" {
		return nil
	}

	loc := &ParsedLocation{
		OriginalText: locationText,
	}

	text := strings.ToLower(locationText)

	// Parse floor
	loc.Floor = p.extractFloor(text)

	// Parse room
	loc.Room = p.extractRoom(text)

	// Parse building (if multi-building)
	loc.Building = p.extractBuilding(text)

	return loc
}

// ParsedLocation represents parsed location components
type ParsedLocation struct {
	OriginalText string
	Building     string
	Floor        string
	Room         string
}

// extractFloor attempts to extract floor information
func (p *CSVParser) extractFloor(text string) string {
	// Patterns: "floor 3", "3rd floor", "fl 3", "f3", "level 3"

	// First check for "Xrd floor" pattern (number before pattern)
	words := strings.Fields(text)
	for i, word := range words {
		// Check if word is a floor pattern
		wordLower := strings.ToLower(word)
		if wordLower == "floor" || wordLower == "fl" || wordLower == "level" || wordLower == "lvl" {
			// Check previous word for number with ordinal
			if i > 0 {
				prevWord := words[i-1]
				// Clean up ordinals (1st, 2nd, 3rd, 4th)
				floor := strings.TrimSuffix(prevWord, "st")
				floor = strings.TrimSuffix(floor, "nd")
				floor = strings.TrimSuffix(floor, "rd")
				floor = strings.TrimSuffix(floor, "th")
				if floor != prevWord {
					// Had ordinal suffix, return cleaned number
					return strings.ToLower(floor)
				}
			}
			// Check next word for number
			if i < len(words)-1 {
				return strings.ToLower(words[i+1])
			}
		}
	}

	return ""
}

// extractRoom attempts to extract room number/name
func (p *CSVParser) extractRoom(text string) string {
	// Patterns: "room 301", "rm 301", "r301", "conf a", "conference room a"
	words := strings.Fields(text)

	for i, word := range words {
		wordLower := strings.ToLower(word)

		// Check if word matches room patterns
		if wordLower == "room" || wordLower == "rm" || wordLower == "conference" ||
			wordLower == "conf" || wordLower == "office" || wordLower == "lab" ||
			wordLower == "classroom" {
			// Get next word (room number/name)
			if i < len(words)-1 {
				nextWord := words[i+1]
				// Skip "room" in "conference room a" pattern
				if strings.ToLower(nextWord) == "room" {
					if i < len(words)-2 {
						return strings.ToLower(words[i+2])
					}
				} else {
					return strings.ToLower(nextWord)
				}
			}
		}
	}

	return ""
}

// extractBuilding attempts to extract building identifier
func (p *CSVParser) extractBuilding(text string) string {
	// Patterns: "building 1", "bldg 1", "b1"
	words := strings.Fields(text)

	for i, word := range words {
		wordLower := strings.ToLower(word)

		// Check if word matches building patterns
		if wordLower == "building" || wordLower == "bldg" || wordLower == "bld" {
			// Get next word (building number/identifier)
			if i < len(words)-1 {
				return strings.ToLower(words[i+1])
			}
		}
	}

	return ""
}

// DetectBASSystemType attempts to detect the BAS system type from CSV content
func (p *CSVParser) DetectBASSystemType(filePath string) (domain.BASSystemType, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	// Read first few lines
	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil || len(records) == 0 {
		return domain.BASSystemTypeOther, nil
	}

	// Check filename
	filename := strings.ToLower(filePath)
	if strings.Contains(filename, "metasys") {
		return domain.BASSystemTypeMetasys, nil
	}
	if strings.Contains(filename, "desigo") || strings.Contains(filename, "siemens") {
		return domain.BASSystemTypeDesigo, nil
	}
	if strings.Contains(filename, "honeywell") || strings.Contains(filename, "ebi") {
		return domain.BASSystemTypeHoneywell, nil
	}
	if strings.Contains(filename, "niagara") || strings.Contains(filename, "tridium") {
		return domain.BASSystemTypeNiagara, nil
	}

	// Check header for clues
	header := strings.ToLower(strings.Join(records[0], " "))
	if strings.Contains(header, "metasys") {
		return domain.BASSystemTypeMetasys, nil
	}
	if strings.Contains(header, "desigo") {
		return domain.BASSystemTypeDesigo, nil
	}
	if strings.Contains(header, "honeywell") {
		return domain.BASSystemTypeHoneywell, nil
	}

	return domain.BASSystemTypeOther, nil
}

// ValidateCSV validates a CSV file structure before parsing
func (p *CSVParser) ValidateCSV(filePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("cannot open file: %w", err)
	}
	defer file.Close()

	// Check file size (reasonable limits)
	stat, err := file.Stat()
	if err != nil {
		return fmt.Errorf("cannot stat file: %w", err)
	}

	if stat.Size() == 0 {
		return fmt.Errorf("file is empty")
	}

	if stat.Size() > 100*1024*1024 { // 100MB limit
		return fmt.Errorf("file too large (max 100MB)")
	}

	// Try to read header
	reader := csv.NewReader(file)
	header, err := reader.Read()
	if err != nil {
		return fmt.Errorf("cannot read CSV header: %w", err)
	}

	if len(header) < 3 {
		return fmt.Errorf("CSV must have at least 3 columns (point name, device, type)")
	}

	return nil
}
