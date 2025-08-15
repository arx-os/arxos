// Package arxobject provides the enhanced ArxObject design
// This file contains improvements to make the ArxObject design flawless
package arxobject

import (
	"time"
	"encoding/json"
)

// === MISSING ELEMENT 1: System Classification ===
// System represents the building system category
type System string

const (
	SystemStructural   System = "structural"
	SystemElectrical   System = "electrical"
	SystemMechanical   System = "mechanical"
	SystemPlumbing     System = "plumbing"
	SystemFireSafety   System = "fire_safety"
	SystemData         System = "data"
	SystemSecurity     System = "security"
	SystemAutomation   System = "automation"
	SystemManufacturing System = "manufacturing"
)

// === MISSING ELEMENT 2: Material Properties ===
type Material struct {
	Type           string  `json:"type"`           // concrete, steel, copper, silicon
	Grade          string  `json:"grade"`          // specific grade/alloy
	Conductivity   float64 `json:"conductivity"`   // electrical/thermal
	Resistance     float64 `json:"resistance"`     // ohms for electrical
	FireRating     string  `json:"fire_rating"`    // UL rating
	Manufacturer   string  `json:"manufacturer"`
	PartNumber     string  `json:"part_number"`
	Cost           float64 `json:"cost"`           // per unit
	LastUpdated    time.Time `json:"last_updated"`
}

// === MISSING ELEMENT 3: Topology/Connections ===
type ConnectionType uint8

const (
	ConnPhysical   ConnectionType = iota // Physically attached
	ConnElectrical                       // Electrical connection
	ConnData                             // Data/network connection
	ConnFluid                            // Pipe/duct connection
	ConnLogical                          // Logical relationship
	ConnContains                         // Parent-child containment
	ConnFeeds                            // Power/data/fluid feed
	ConnControls                         // Control relationship
)

type Connection struct {
	FromID     uint64         `json:"from_id"`
	ToID       uint64         `json:"to_id"`
	Type       ConnectionType `json:"type"`
	Port       string         `json:"port,omitempty"`      // For specific port connections
	Properties json.RawMessage `json:"properties,omitempty"` // Type-specific properties
}

// === MISSING ELEMENT 4: Lifecycle and Maintenance ===
type Lifecycle struct {
	Installed      time.Time  `json:"installed"`
	Commissioned   time.Time  `json:"commissioned"`
	LastMaintained time.Time  `json:"last_maintained"`
	NextMaintenance time.Time `json:"next_maintenance"`
	WarrantyExpiry time.Time  `json:"warranty_expiry"`
	ExpectedEOL    time.Time  `json:"expected_eol"`      // End of life
	MaintenanceHistory []Maintenance `json:"maintenance_history"`
	Condition      float32    `json:"condition"`         // 0.0 (failed) to 1.0 (new)
	MTBF           int64      `json:"mtbf_hours"`        // Mean time between failures
}

type Maintenance struct {
	Date        time.Time `json:"date"`
	Type        string    `json:"type"`        // preventive, corrective, predictive
	Technician  string    `json:"technician"`
	WorkOrderID string    `json:"work_order_id"`
	Notes       string    `json:"notes"`
	Cost        float64   `json:"cost"`
	PartsUsed   []string  `json:"parts_used"`
}

// === MISSING ELEMENT 5: Real-time Monitoring ===
type Telemetry struct {
	SensorID    string    `json:"sensor_id"`
	Value       float64   `json:"value"`
	Unit        string    `json:"unit"`
	Timestamp   time.Time `json:"timestamp"`
	Quality     float32   `json:"quality"`     // 0-1 data quality score
	Anomaly     bool      `json:"anomaly"`     // Detected anomaly
}

type Monitoring struct {
	Enabled       bool                `json:"enabled"`
	SensorPoints  []string            `json:"sensor_points"`
	CurrentValues map[string]Telemetry `json:"current_values"`
	Thresholds    map[string]Threshold `json:"thresholds"`
	Alerts        []Alert             `json:"alerts"`
}

type Threshold struct {
	Min      float64 `json:"min"`
	Max      float64 `json:"max"`
	Critical float64 `json:"critical"`
	Unit     string  `json:"unit"`
}

type Alert struct {
	ID        string    `json:"id"`
	Severity  string    `json:"severity"` // info, warning, critical
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
	Resolved  bool      `json:"resolved"`
}

// === MISSING ELEMENT 6: Compliance and Standards ===
type Compliance struct {
	Standards    []Standard    `json:"standards"`     // NEC, IBC, ASHRAE, etc.
	Certificates []Certificate `json:"certificates"`
	Inspections  []Inspection  `json:"inspections"`
	Violations   []Violation   `json:"violations"`
}

type Standard struct {
	Code    string `json:"code"`       // NEC-2020, IBC-2018
	Section string `json:"section"`    // Specific section
	Compliant bool `json:"compliant"`
}

type Certificate struct {
	Type       string    `json:"type"`        // UL, CE, Energy Star
	Number     string    `json:"number"`
	IssuedBy   string    `json:"issued_by"`
	IssuedDate time.Time `json:"issued_date"`
	ExpiryDate time.Time `json:"expiry_date"`
}

type Inspection struct {
	Date      time.Time `json:"date"`
	Inspector string    `json:"inspector"`
	Type      string    `json:"type"`
	Result    string    `json:"result"`
	Notes     string    `json:"notes"`
}

type Violation struct {
	Code        string    `json:"code"`
	Description string    `json:"description"`
	Severity    string    `json:"severity"`
	DateFound   time.Time `json:"date_found"`
	DateResolved *time.Time `json:"date_resolved,omitempty"`
}

// === MISSING ELEMENT 7: Economic Model (BILT Integration) ===
type Economics struct {
	ContributorID   string    `json:"contributor_id"`   // Who added this object
	CreationTime    time.Time `json:"creation_time"`
	VerificationCount int     `json:"verification_count"` // How many verified
	QualityScore    float32   `json:"quality_score"`      // 0-1 quality rating
	BILTReward      float64   `json:"bilt_reward"`        // Tokens earned
	DataValue       float64   `json:"data_value"`         // Estimated value
	AccessCount     int64     `json:"access_count"`       // Times accessed
	LastAccessed    time.Time `json:"last_accessed"`
}

// === MISSING ELEMENT 8: Version Control ===
type Version struct {
	Number      int       `json:"number"`
	Hash        string    `json:"hash"`         // Content hash
	Author      string    `json:"author"`
	Timestamp   time.Time `json:"timestamp"`
	ChangeType  string    `json:"change_type"`  // create, update, delete
	ChangedFields []string `json:"changed_fields"`
	Previous    *string   `json:"previous_hash,omitempty"`
}

// === ENHANCED ARXOBJECT ===
type ArxObjectEnhanced struct {
	// Core Identity
	ID         uint64        `json:"id"`
	Type       ArxObjectType `json:"type"`
	System     System        `json:"system"`
	Name       string        `json:"name"`        // Human-readable name
	
	// Spatial (nanometer precision)
	X, Y, Z       int64 `json:"x,y,z"`
	Length, Width int64 `json:"length,width"`
	Height        int64 `json:"height"`
	RotationZ     int32 `json:"rotation_z"`    // millidegrees
	ScaleLevel    uint8 `json:"scale_level"`
	
	// Physical Properties
	Material   *Material `json:"material,omitempty"`
	Weight     float32   `json:"weight_kg,omitempty"`
	Color      string    `json:"color,omitempty"`
	
	// Relationships
	ParentID    *uint64      `json:"parent_id,omitempty"`
	Connections []Connection `json:"connections,omitempty"`
	
	// Lifecycle
	Lifecycle  *Lifecycle  `json:"lifecycle,omitempty"`
	
	// Real-time
	Monitoring *Monitoring `json:"monitoring,omitempty"`
	
	// Compliance
	Compliance *Compliance `json:"compliance,omitempty"`
	
	// Economics
	Economics  *Economics  `json:"economics,omitempty"`
	
	// Version Control
	Version    Version     `json:"version"`
	
	// Metadata
	Properties json.RawMessage `json:"properties,omitempty"` // Type-specific data
	Tags       []string        `json:"tags,omitempty"`
	
	// Status
	Status     string    `json:"status"`      // active, inactive, maintenance, failed
	Locked     bool      `json:"locked"`
	LockedBy   string    `json:"locked_by,omitempty"`
	UpdatedAt  time.Time `json:"updated_at"`
	CreatedAt  time.Time `json:"created_at"`
}

// === VALIDATION ===
func (obj *ArxObjectEnhanced) Validate() error {
	// Implement validation logic
	// - Check required fields
	// - Validate coordinate ranges
	// - Ensure system matches type
	// - Validate connections reference valid IDs
	return nil
}

// === METHODS FOR SCALE-AWARE OPERATIONS ===
func (obj *ArxObjectEnhanced) IsVisibleAtScale(scale uint8) bool {
	return obj.ScaleLevel <= scale
}

func (obj *ArxObjectEnhanced) GetBoundingBox() (minX, minY, minZ, maxX, maxY, maxZ int64) {
	halfL := obj.Length / 2
	halfW := obj.Width / 2
	return obj.X - halfL, obj.Y - halfW, obj.Z,
	       obj.X + halfL, obj.Y + halfW, obj.Z + obj.Height
}

// === SERIALIZATION HELPERS ===
func (obj *ArxObjectEnhanced) ToGeoJSON() map[string]interface{} {
	// Convert to GeoJSON for mapping applications
	return map[string]interface{}{
		"type": "Feature",
		"geometry": map[string]interface{}{
			"type": "Point",
			"coordinates": []float64{
				float64(obj.X) / float64(Meter),
				float64(obj.Y) / float64(Meter),
				float64(obj.Z) / float64(Meter),
			},
		},
		"properties": map[string]interface{}{
			"id":     obj.ID,
			"type":   obj.Type,
			"system": obj.System,
			"name":   obj.Name,
			"status": obj.Status,
		},
	}
}

// === QUERY OPTIMIZATION ===
type ArxQuery struct {
	BoundingBox *BoundingBox    `json:"bounding_box,omitempty"`
	ScaleLevel  *uint8          `json:"scale_level,omitempty"`
	Systems     []System        `json:"systems,omitempty"`
	Types       []ArxObjectType `json:"types,omitempty"`
	Status      []string        `json:"status,omitempty"`
	Tags        []string        `json:"tags,omitempty"`
	MinQuality  *float32        `json:"min_quality,omitempty"`
	UpdatedSince *time.Time     `json:"updated_since,omitempty"`
}

type BoundingBox struct {
	MinX, MinY, MinZ int64
	MaxX, MaxY, MaxZ int64
}