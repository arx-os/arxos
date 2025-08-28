package models

import (
	"fmt"
	"strings"
	"time"
)

// ArxObjectV2 represents the core building component with system hierarchy naming
type ArxObjectV2 struct {
	// Core Identity
	ID       string `json:"id"`       // System hierarchy path: building_id/system/path
	Type     string `json:"type"`     // Component type: breaker, vav, valve, etc.
	System   string `json:"system"`   // System category: electrical, hvac, plumbing, etc.
	Name     string `json:"name"`     // Human-readable name
	
	// Hierarchy
	Parent   string   `json:"parent,omitempty"`   // Parent in system hierarchy
	Children []string `json:"children,omitempty"` // Children in system hierarchy
	
	// Spatial Reference
	SpatialLocation string          `json:"spatial_location,omitempty"` // building_id/f1/r101
	Position        *Position       `json:"position,omitempty"`         // Physical position details
	Coordinates     *Coordinates    `json:"coordinates,omitempty"`      // 3D coordinates
	
	// System Properties (flexible for any system)
	Properties map[string]interface{} `json:"properties,omitempty"`
	
	// Relationships
	Relationships map[string][]string `json:"relationships,omitempty"`
	// Examples:
	// "fed_from": ["building_id/electrical/panel/mdf/breaker/12"]
	// "powers": ["building_id/hvac/ahu/1/fan/supply"]
	// "serves": ["building_id/f1/r101", "building_id/f1/r102"]
	// "controlled_by": ["building_id/bas/controller/vav_f1_101"]
	
	// Cross-System Connections
	PowerSource    string           `json:"power_source,omitempty"`    // Primary electrical feed
	PowerLoad      *LoadInformation `json:"power_load,omitempty"`      // Electrical load details
	DataConnection string           `json:"data_connection,omitempty"` // Network connection
	Critical       bool             `json:"critical,omitempty"`        // Critical infrastructure flag
	
	// Status & Validation
	Status           string     `json:"status"`                       // active, inactive, fault, maintenance
	Confidence       float64    `json:"confidence"`                   // 0.0 to 1.0
	ValidationStatus string     `json:"validation_status,omitempty"` // pending, validated, failed
	ValidatedAt      *time.Time `json:"validated_at,omitempty"`
	ValidatedBy      string     `json:"validated_by,omitempty"`
	
	// Metadata
	Created     time.Time              `json:"created"`
	Updated     time.Time              `json:"updated"`
	Version     int                    `json:"version"`
	Tags        []string               `json:"tags,omitempty"`
	Source      *SourceInfo            `json:"source,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"` // Additional flexible metadata
}

// Position represents physical position within a space
type Position struct {
	Wall      string  `json:"wall,omitempty"`       // north, south, east, west
	Height    float64 `json:"height,omitempty"`     // Height in inches from floor
	Distance  float64 `json:"distance,omitempty"`   // Distance from reference point
	Reference string  `json:"reference,omitempty"`  // Reference point description
	// Added for ASCII rendering compatibility
	X float64 `json:"x,omitempty"` // X coordinate
	Y float64 `json:"y,omitempty"` // Y coordinate
	Z float64 `json:"z,omitempty"` // Z coordinate
}

// Coordinates represents 3D spatial coordinates
type Coordinates struct {
	X float64 `json:"x"` // X coordinate in mm
	Y float64 `json:"y"` // Y coordinate in mm  
	Z float64 `json:"z"` // Z coordinate in mm
	Unit string `json:"unit,omitempty"` // Default: mm
}

// SourceInfo tracks where this object came from
type SourceInfo struct {
	Type       string    `json:"type"`       // pdf, ifc, scan, manual, sensor
	File       string    `json:"file,omitempty"`
	Page       int       `json:"page,omitempty"`
	ImportedAt time.Time `json:"imported_at"`
	ImportedBy string    `json:"imported_by,omitempty"`
}

// SystemType constants
const (
	SystemElectrical = "electrical"
	SystemHVAC       = "hvac"
	SystemPlumbing   = "plumbing"
	SystemFire       = "fire_alarm"
	SystemSprinkler  = "sprinkler"
	SystemSecurity   = "security"
	SystemAccess     = "access"
	SystemElevator   = "elevator"
	SystemBAS        = "bas"
	SystemIT         = "it"
	SystemNetwork    = "network"    // Network infrastructure
	SystemTelecom    = "telecom"
	SystemSite       = "site"
	SystemSolar      = "solar"
	SystemBattery    = "battery"
	SystemStructural = "structural"
	SystemEnvelope   = "envelope"
	SystemSpatial    = "spatial"    // For rooms, floors, areas
	SystemHardware   = "hardware"   // Hardware/DfM components
	SystemLighting   = "lighting"   // Lighting systems
)

// ComponentType represents specific component types within systems
type ComponentType struct {
	System      string
	Category    string
	Type        string
	Description string
}

// Common component types by system
var (
	// Electrical Components
	ElectricalPanel      = ComponentType{SystemElectrical, "distribution", "panel", "Electrical panel"}
	ElectricalBreaker    = ComponentType{SystemElectrical, "distribution", "breaker", "Circuit breaker"}
	ElectricalMeter      = ComponentType{SystemElectrical, "metering", "meter", "Electrical meter"}
	ElectricalOutlet     = ComponentType{SystemElectrical, "device", "outlet", "Electrical outlet"}
	ElectricalSwitch     = ComponentType{SystemElectrical, "device", "switch", "Light switch"}
	
	// HVAC Components
	HVACChiller    = ComponentType{SystemHVAC, "plant", "chiller", "Chiller unit"}
	HVACAHU        = ComponentType{SystemHVAC, "air", "ahu", "Air handling unit"}
	HVACVAV        = ComponentType{SystemHVAC, "terminal", "vav", "Variable air volume box"}
	HVACDiffuser   = ComponentType{SystemHVAC, "terminal", "diffuser", "Air diffuser"}
	
	// Plumbing Components
	PlumbingValve   = ComponentType{SystemPlumbing, "control", "valve", "Water valve"}
	PlumbingFixture = ComponentType{SystemPlumbing, "fixture", "fixture", "Plumbing fixture"}
	PlumbingPump    = ComponentType{SystemPlumbing, "equipment", "pump", "Water pump"}
)

// IDBuilder helps construct proper ArxObject IDs
type IDBuilder struct {
	parts []string
}

// NewIDBuilder creates a new ID builder
func NewIDBuilder(buildingID string) *IDBuilder {
	return &IDBuilder{
		parts: []string{buildingID},
	}
}

// Add adds a segment to the ID
func (b *IDBuilder) Add(segment string) *IDBuilder {
	if segment != "" {
		b.parts = append(b.parts, strings.ToLower(strings.ReplaceAll(segment, " ", "_")))
	}
	return b
}

// System adds a system segment
func (b *IDBuilder) System(system string) *IDBuilder {
	return b.Add(system)
}

// Floor adds a floor segment (f1, f2, b1, etc.)
func (b *IDBuilder) Floor(floor int) *IDBuilder {
	if floor < 0 {
		return b.Add(fmt.Sprintf("b%d", -floor)) // Basement
	}
	return b.Add(fmt.Sprintf("f%d", floor))
}

// Room adds a room segment
func (b *IDBuilder) Room(roomID string) *IDBuilder {
	b.Add("room")
	return b.Add(roomID)
}

// Component adds a component type and ID
func (b *IDBuilder) Component(compType, compID string) *IDBuilder {
	b.Add(compType)
	return b.Add(compID)
}

// Build returns the final ID
func (b *IDBuilder) Build() string {
	return strings.Join(b.parts, "/")
}

// ParseID breaks down an ArxObject ID into its components
func ParseID(id string) map[string]string {
	parts := strings.Split(id, "/")
	result := make(map[string]string)
	
	if len(parts) > 0 {
		result["building"] = parts[0]
	}
	
	// Try to identify common patterns
	for i, part := range parts {
		// Floor detection
		if strings.HasPrefix(part, "f") || strings.HasPrefix(part, "b") {
			if len(part) > 1 {
				if _, err := fmt.Sscanf(part[1:], "%d", new(int)); err == nil {
					result["floor"] = part
				}
			}
		}
		
		// System detection
		if i == 1 && isKnownSystem(part) {
			result["system"] = part
		}
		
		// Room detection
		if i > 0 && parts[i-1] == "room" {
			result["room"] = part
		}
	}
	
	result["full"] = id
	result["parts_count"] = fmt.Sprintf("%d", len(parts))
	
	return result
}

// isKnownSystem checks if a string is a known system
func isKnownSystem(s string) bool {
	systems := []string{
		SystemElectrical, SystemHVAC, SystemPlumbing, SystemFire,
		SystemSprinkler, SystemSecurity, SystemAccess, SystemElevator,
		SystemBAS, SystemIT, SystemTelecom, SystemSite,
		SystemSolar, SystemBattery, SystemStructural, SystemEnvelope,
	}
	
	for _, system := range systems {
		if s == system {
			return true
		}
	}
	return false
}

// GetParentID returns the parent ID by removing the last segment
func GetParentID(id string) string {
	parts := strings.Split(id, "/")
	if len(parts) <= 1 {
		return ""
	}
	return strings.Join(parts[:len(parts)-1], "/")
}

// GetSystemFromID extracts the system type from an ID
func GetSystemFromID(id string) string {
	parts := strings.Split(id, "/")
	if len(parts) > 1 && isKnownSystem(parts[1]) {
		return parts[1]
	}
	// Try to infer from component type
	for _, part := range parts {
		if isKnownSystem(part) {
			return part
		}
	}
	return "unknown"
}

// ValidateID checks if an ID follows the naming convention
func ValidateID(id string) error {
	if id == "" {
		return fmt.Errorf("ID cannot be empty")
	}
	
	parts := strings.Split(id, "/")
	if len(parts) < 2 {
		return fmt.Errorf("ID must have at least building and one component")
	}
	
	// Check for valid characters (lowercase, numbers, underscore)
	for _, part := range parts {
		if part == "" {
			return fmt.Errorf("ID cannot have empty segments")
		}
		for _, char := range part {
			if !((char >= 'a' && char <= 'z') || (char >= '0' && char <= '9') || char == '_') {
				return fmt.Errorf("ID can only contain lowercase letters, numbers, and underscores: %s", part)
			}
		}
	}
	
	return nil
}