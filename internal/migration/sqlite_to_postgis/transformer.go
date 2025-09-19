package sqlite_to_postgis

import (
	"fmt"
	"math"
	"strings"
)

// Transformer handles data transformations during migration
type Transformer struct {
	config TransformConfig
}

// TransformConfig contains transformation configuration
type TransformConfig struct {
	CoordinateSystem string  // "local" or "wgs84"
	DefaultAltitude  float64 // Default altitude if not specified
	DefaultRotation  float64 // Default building rotation
}

// NewTransformer creates a new transformer
func NewTransformer(config TransformConfig) *Transformer {
	if config.CoordinateSystem == "" {
		config.CoordinateSystem = "wgs84"
	}
	return &Transformer{config: config}
}

// TransformCoordinates converts local coordinates to WGS84
func (t *Transformer) TransformCoordinates(localX, localY, localZ float64, origin Origin) (lon, lat, alt float64) {
	// If already in WGS84, return as-is
	if t.config.CoordinateSystem == "wgs84" {
		return localX, localY, localZ
	}

	// Convert local coordinates (in meters) to lat/lon offsets
	// Approximate conversion: 1 degree latitude = 111,111 meters
	// 1 degree longitude varies by latitude
	latOffset := localY / 111111.0
	lonOffset := localX / (111111.0 * math.Cos(origin.Latitude*math.Pi/180.0))

	// Apply rotation if building has one
	if origin.Rotation != 0 {
		rad := origin.Rotation * math.Pi / 180.0
		cosR := math.Cos(rad)
		sinR := math.Sin(rad)

		// Rotate coordinates
		rotatedX := lonOffset*cosR - latOffset*sinR
		rotatedY := lonOffset*sinR + latOffset*cosR

		lonOffset = rotatedX
		latOffset = rotatedY
	}

	lon = origin.Longitude + lonOffset
	lat = origin.Latitude + latOffset
	alt = origin.Altitude + localZ

	return lon, lat, alt
}

// TransformStatus normalizes equipment status values
func (t *Transformer) TransformStatus(status string) string {
	normalized := strings.ToLower(strings.TrimSpace(status))

	switch normalized {
	case "ok", "good", "active", "online", "operational":
		return "operational"
	case "warning", "warn", "degraded":
		return "degraded"
	case "error", "fail", "failed", "failure", "broken":
		return "failed"
	case "off", "offline", "disabled", "inactive":
		return "offline"
	case "maintenance", "servicing", "repair":
		return "maintenance"
	default:
		return "unknown"
	}
}

// TransformEquipmentType normalizes equipment type values
func (t *Transformer) TransformEquipmentType(eqType string) string {
	normalized := strings.ToLower(strings.TrimSpace(eqType))

	// Map common variations to standard types
	typeMap := map[string]string{
		"outlet":          "electrical.outlet",
		"power_outlet":    "electrical.outlet",
		"switch":          "electrical.switch",
		"light_switch":    "electrical.switch",
		"breaker":         "electrical.breaker",
		"panel":           "electrical.panel",
		"breaker_panel":   "electrical.panel",
		"light":           "lighting.fixture",
		"lamp":            "lighting.fixture",
		"fixture":         "lighting.fixture",
		"sensor":          "sensor.generic",
		"temp_sensor":     "sensor.temperature",
		"motion_sensor":   "sensor.motion",
		"smoke_detector":  "safety.smoke_detector",
		"fire_alarm":      "safety.fire_alarm",
		"sprinkler":       "safety.sprinkler",
		"camera":          "security.camera",
		"access_control":  "security.access",
		"hvac":            "hvac.unit",
		"ac":              "hvac.ac",
		"heater":          "hvac.heater",
		"thermostat":      "hvac.thermostat",
		"vent":            "hvac.vent",
		"pipe":            "plumbing.pipe",
		"valve":           "plumbing.valve",
		"faucet":          "plumbing.faucet",
		"drain":           "plumbing.drain",
		"network":         "it.network",
		"wifi":            "it.wifi_ap",
		"router":          "it.router",
		"server":          "it.server",
	}

	if mappedType, exists := typeMap[normalized]; exists {
		return mappedType
	}

	// If no mapping found, create a generic type
	if strings.Contains(normalized, ".") {
		return normalized // Already namespaced
	}
	return fmt.Sprintf("equipment.%s", normalized)
}

// TransformPath normalizes hierarchical equipment paths
func (t *Transformer) TransformPath(path string) string {
	// Clean up the path
	path = strings.TrimSpace(path)

	// Replace various separators with standard /
	path = strings.ReplaceAll(path, "\\", "/")
	path = strings.ReplaceAll(path, "->", "/")
	path = strings.ReplaceAll(path, " > ", "/")
	path = strings.ReplaceAll(path, " / ", "/")

	// Remove duplicate slashes
	for strings.Contains(path, "//") {
		path = strings.ReplaceAll(path, "//", "/")
	}

	// Ensure no leading or trailing slashes
	path = strings.Trim(path, "/")

	return path
}

// TransformConfidence converts various confidence representations to standard scale (0-3)
func (t *Transformer) TransformConfidence(confidence interface{}) int {
	switch v := confidence.(type) {
	case int:
		if v < 0 {
			return 0
		}
		if v > 3 {
			return 3
		}
		return v
	case int64:
		if v < 0 {
			return 0
		}
		if v > 3 {
			return 3
		}
		return int(v)
	case float64:
		// If percentage, convert to 0-3 scale
		if v > 10 {
			if v >= 90 {
				return 3 // Surveyed
			} else if v >= 70 {
				return 2 // Scanned
			} else if v >= 40 {
				return 1 // Estimated
			}
		}
		return 0 // Unknown
	case string:
		switch strings.ToLower(v) {
		case "high", "surveyed", "verified":
			return 3
		case "medium", "scanned":
			return 2
		case "low", "estimated", "approximate":
			return 1
		default:
			return 0
		}
	default:
		return 0
	}
}

// ValidateCoordinates checks if coordinates are valid WGS84
func (t *Transformer) ValidateCoordinates(lon, lat float64) error {
	if lon < -180 || lon > 180 {
		return fmt.Errorf("invalid longitude: %f (must be between -180 and 180)", lon)
	}
	if lat < -90 || lat > 90 {
		return fmt.Errorf("invalid latitude: %f (must be between -90 and 90)", lat)
	}
	return nil
}

// Origin represents a building's origin point
type Origin struct {
	Longitude float64
	Latitude  float64
	Altitude  float64
	Rotation  float64 // Rotation from north in degrees
}

// PathComponents breaks down a hierarchical path
type PathComponents struct {
	Building string
	Floor    string
	Room     string
	Equipment string
}

// ParsePath parses a hierarchical path into components
func (t *Transformer) ParsePath(path string) PathComponents {
	cleaned := t.TransformPath(path)
	parts := strings.Split(cleaned, "/")

	components := PathComponents{}

	if len(parts) > 0 {
		components.Building = parts[0]
	}
	if len(parts) > 1 {
		components.Floor = parts[1]
	}
	if len(parts) > 2 {
		components.Room = parts[2]
	}
	if len(parts) > 3 {
		components.Equipment = strings.Join(parts[3:], "/")
	}

	return components
}

// SanitizeString cleans string values for database insertion
func (t *Transformer) SanitizeString(s string) string {
	// Trim whitespace
	s = strings.TrimSpace(s)

	// Replace NULL strings with empty
	if strings.ToUpper(s) == "NULL" || s == "\\N" {
		return ""
	}

	// Remove or replace problematic characters
	replacements := map[string]string{
		"\n": " ",
		"\r": " ",
		"\t": " ",
		"'":  "'",
		// Remove smart quotes for now to fix syntax error
	}

	for old, new := range replacements {
		s = strings.ReplaceAll(s, old, new)
	}

	// Collapse multiple spaces
	for strings.Contains(s, "  ") {
		s = strings.ReplaceAll(s, "  ", " ")
	}

	return s
}

// EstimateCoordinatesFromGrid converts grid coordinates to approximate GPS
func (t *Transformer) EstimateCoordinatesFromGrid(gridX, gridY int, floorZ float64, origin Origin) (lon, lat, alt float64) {
	// Assume each grid unit is approximately 1 meter
	localX := float64(gridX)
	localY := float64(gridY)
	localZ := floorZ * 3.0 // Assume 3 meters per floor

	return t.TransformCoordinates(localX, localY, localZ, origin)
}