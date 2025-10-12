package naming

import (
	"fmt"
	"regexp"
	"strings"
)

// PathComponents represents the components of an equipment path
type PathComponents struct {
	Building  string
	Floor     string
	Room      string // Optional - can be empty for building/floor level equipment
	System    string
	Equipment string
}

// GenerateEquipmentPath creates a universal path from components
// Format: /[BUILDING]/[FLOOR]/[ROOM]/[SYSTEM]/[EQUIPMENT]
// If room is empty, format is: /[BUILDING]/[FLOOR]/[SYSTEM]/[EQUIPMENT]
func GenerateEquipmentPath(building, floor, room, system, equipment string) string {
	// Sanitize inputs (uppercase, remove invalid characters)
	building = sanitizePathSegment(building)
	floor = sanitizePathSegment(floor)
	room = sanitizePathSegment(room)
	system = sanitizePathSegment(system)
	equipment = sanitizePathSegment(equipment)

	if room == "" {
		// Building/Floor level equipment (no room)
		return fmt.Sprintf("/%s/%s/%s/%s", building, floor, system, equipment)
	}

	// Full path with room
	return fmt.Sprintf("/%s/%s/%s/%s/%s", building, floor, room, system, equipment)
}

// ParseEquipmentPath parses a path string into components
func ParseEquipmentPath(path string) (*PathComponents, error) {
	if !strings.HasPrefix(path, "/") {
		return nil, fmt.Errorf("path must start with /")
	}

	segments := strings.Split(path[1:], "/")

	if len(segments) < 4 {
		return nil, fmt.Errorf("path must have at least 4 segments (building/floor/system/equipment)")
	}

	if len(segments) > 5 {
		return nil, fmt.Errorf("path cannot have more than 5 segments")
	}

	components := &PathComponents{
		Building: segments[0],
		Floor:    segments[1],
	}

	if len(segments) == 4 {
		// No room (building/floor level equipment)
		components.System = segments[2]
		components.Equipment = segments[3]
	} else {
		// Full path with room
		components.Room = segments[2]
		components.System = segments[3]
		components.Equipment = segments[4]
	}

	return components, nil
}

// IsValidPath validates that a path follows the universal naming convention
func IsValidPath(path string) bool {
	if !strings.HasPrefix(path, "/") {
		return false
	}

	segments := strings.Split(path[1:], "/")
	if len(segments) < 4 || len(segments) > 5 {
		return false // Must be 4 or 5 segments
	}

	// Each segment must be uppercase alphanumeric with optional hyphens
	validSegment := regexp.MustCompile(`^[A-Z0-9]+(-[A-Z0-9]+)*$`)

	for _, segment := range segments {
		if segment == "" {
			return false // No empty segments
		}
		if !validSegment.MatchString(segment) {
			return false
		}
	}

	return true
}

// MatchPathPattern checks if a path matches a pattern with wildcards
// Example: MatchPathPattern("/B1/3/301/HVAC/VAV-301", "/B1/3/*/HVAC/*") returns true
func MatchPathPattern(path, pattern string) bool {
	pathSegs := strings.Split(path, "/")
	patternSegs := strings.Split(pattern, "/")

	if len(pathSegs) != len(patternSegs) {
		return false
	}

	for i, patternSeg := range patternSegs {
		if patternSeg == "*" {
			continue // Wildcard matches anything
		}
		if patternSeg == "**" {
			return true // Double wildcard matches rest of path
		}
		if patternSeg != pathSegs[i] {
			return false
		}
	}

	return true
}

// ToSQLPattern converts a path pattern to SQL LIKE pattern
// Example: "/B1/3/*/HVAC/*" → "/B1/3/%/HVAC/%"
func ToSQLPattern(pattern string) string {
	return strings.ReplaceAll(pattern, "*", "%")
}

// sanitizePathSegment converts a segment to valid path format
// - Converts to uppercase
// - Removes invalid characters
// - Collapses multiple hyphens
func sanitizePathSegment(segment string) string {
	if segment == "" {
		return ""
	}

	// Convert to uppercase
	segment = strings.ToUpper(segment)

	// Replace spaces with hyphens
	segment = strings.ReplaceAll(segment, " ", "-")

	// Remove characters that aren't alphanumeric or hyphen
	validChars := regexp.MustCompile(`[^A-Z0-9-]`)
	segment = validChars.ReplaceAllString(segment, "")

	// Collapse multiple consecutive hyphens
	multiHyphen := regexp.MustCompile(`-+`)
	segment = multiHyphen.ReplaceAllString(segment, "-")

	// Remove leading/trailing hyphens
	segment = strings.Trim(segment, "-")

	return segment
}

// SystemCategoryToCode maps a system category to its standard path code
var SystemCategoryToCode = map[string]string{
	"electrical":  "ELEC",
	"hvac":        "HVAC",
	"plumbing":    "PLUMB",
	"network":     "NETWORK",
	"safety":      "SAFETY",
	"av":          "AV",
	"custodial":   "CUSTODIAL",
	"lighting":    "LIGHTING",
	"doors":       "DOORS",
	"energy":      "ENERGY",
	"bas":         "BAS",
	"fire":        "SAFETY",  // Alias for safety
	"security":    "SAFETY",  // Alias for safety
	"it":          "NETWORK", // Alias for network
	"audiovisual": "AV",      // Alias for AV
}

// GetSystemCode returns the standard system code for a category
// Falls back to uppercase category if not found in map
func GetSystemCode(category string) string {
	if code, exists := SystemCategoryToCode[strings.ToLower(category)]; exists {
		return code
	}
	// Fall back to sanitized uppercase category
	return sanitizePathSegment(category)
}

// GenerateEquipmentCode creates an equipment identifier from name and optional suffix
// Example: ("Electrical Panel", "1A") → "PANEL-1A"
// Example: ("VAV Box", "301") → "VAV-301"
func GenerateEquipmentCode(name, identifier string) string {
	// Extract equipment type from name
	name = strings.ToUpper(name)

	// Common equipment type abbreviations
	abbreviations := map[string]string{
		"PANEL":         "PANEL",
		"TRANSFORMER":   "XFMR",
		"AIR HANDLER":   "AHU",
		"VAV BOX":       "VAV",
		"THERMOSTAT":    "STAT",
		"DIFFUSER":      "DIFFUSER",
		"SWITCH":        "SW",
		"ROUTER":        "RTR",
		"ACCESS POINT":  "WAP",
		"WIRELESS":      "WAP",
		"OUTLET":        "OUTLET",
		"RECEPTACLE":    "RECEP",
		"WATER HEATER":  "WH",
		"FIRE DETECTOR": "DETECTOR",
		"SPRINKLER":     "SPRINKLER",
		"EXTINGUISHER":  "EXTING",
		"PROJECTOR":     "PROJ",
		"DISPLAY":       "DISPLAY",
		"DAMPER":        "DAMPER",
		"CHILLER":       "CHILLER",
		"PUMP":          "PUMP",
		"VALVE":         "VALVE",
		"LIGHT":         "LIGHT",
		"FIXTURE":       "FIXTURE",
	}

	// Try to find a matching abbreviation
	code := ""
	for key, abbr := range abbreviations {
		if strings.Contains(name, key) {
			code = abbr
			break
		}
	}

	// If no abbreviation found, use first significant word
	if code == "" {
		words := strings.Fields(name)
		if len(words) > 0 {
			code = sanitizePathSegment(words[0])
		} else {
			code = "EQUIP"
		}
	}

	// Add identifier if provided
	if identifier != "" {
		identifier = sanitizePathSegment(identifier)
		return fmt.Sprintf("%s-%s", code, identifier)
	}

	return code
}

// BuildingCodeFromName generates a building code from building name
// Example: "Main Building" → "MAIN"
// Example: "North Wing" → "NORTH-WING"
func BuildingCodeFromName(name string) string {
	name = strings.TrimSpace(name)
	if name == "" {
		return "B1"
	}

	// Convert to uppercase first
	name = strings.ToUpper(name)

	// Common building type abbreviations (order matters - longer patterns first)
	replacements := []struct {
		pattern     string
		replacement string
	}{
		{"HIGH SCHOOL", "HS"},
		{"MIDDLE SCHOOL", "MS"},
		{"ELEMENTARY SCHOOL", "ES"},
		{"ELEMENTARY", "ES"},
		{"TOWER", "TWR"},
		{"BUILDING ", ""}, // Trailing space for "Building X"
		{" BUILDING", ""}, // Leading space for "X Building"
		{" WING", ""},
	}

	for _, r := range replacements {
		name = strings.ReplaceAll(name, r.pattern, r.replacement)
	}

	// Now sanitize
	code := sanitizePathSegment(name)

	// Clean up multiple hyphens and leading/trailing hyphens
	code = strings.Trim(code, "-")
	multiHyphen := regexp.MustCompile(`-+`)
	code = multiHyphen.ReplaceAllString(code, "-")

	// If code is too long, use first word
	if len(code) > 15 {
		words := strings.Split(code, "-")
		if len(words) > 0 {
			code = words[0]
		}
	}

	// Fall back to "B1" if code is empty
	if code == "" {
		code = "B1"
	}

	return code
}

// FloorCodeFromLevel generates a floor code from floor level/name
// Example: 1 → "1"
// Example: "Basement" → "B"
// Example: "Roof" → "R"
func FloorCodeFromLevel(level string) string {
	level = strings.ToUpper(strings.TrimSpace(level))

	// Common floor mappings
	floorMappings := map[string]string{
		"GROUND":       "1",
		"GROUND FLOOR": "1",
		"FIRST":        "1",
		"FIRST FLOOR":  "1",
		"BASEMENT":     "B",
		"CELLAR":       "B",
		"ROOF":         "R",
		"ROOFTOP":      "R",
		"PENTHOUSE":    "P",
		"MEZZANINE":    "M",
		"LEVEL":        "",
		"FLOOR":        "",
	}

	code := level
	for key, replacement := range floorMappings {
		if strings.Contains(level, key) {
			code = strings.ReplaceAll(code, key, replacement)
		}
	}

	code = sanitizePathSegment(code)

	// If code is empty or just whitespace after mapping, default to "1"
	if code == "" {
		code = "1"
	}

	return code
}

// RoomCodeFromName generates a room code from room name/number
// Example: "Room 101" → "101"
// Example: "Conference Room 301" → "CONF-301"
// Example: "Mechanical Room A" → "MECH-A"
func RoomCodeFromName(name string) string {
	name = strings.ToUpper(strings.TrimSpace(name))

	// Common room type abbreviations
	abbreviations := map[string]string{
		"CONFERENCE": "CONF",
		"MECHANICAL": "MECH",
		"ELECTRICAL": "ELEC",
		"ROOM":       "",
	}

	code := name
	for key, replacement := range abbreviations {
		code = strings.ReplaceAll(code, key, replacement)
	}

	code = sanitizePathSegment(code)

	// If code is empty, default to "GEN" (general)
	if code == "" {
		code = "GEN"
	}

	return code
}
