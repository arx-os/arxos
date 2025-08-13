// Package arxoscore provides the foundational ArxObject data structure
// that represents any piece of building infrastructure.
package arxoscore

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// ArxObject is the DNA of building infrastructure.
// It represents ANY physical object from an entire campus down to a single screw.
// This is the single source of truth for all building data in Arxos.
type ArxObject struct {
	// === IDENTITY ===
	// ID uniquely identifies this object using hierarchical format:
	// Format: "arx:building:floor:room:object"
	// Example: "arx:plant-high:floor-1:room-201:outlet-1"
	ID string `json:"id" db:"id"`

	// Type describes what this object is
	// Examples: "building", "floor", "room", "outlet", "switch", "duct", "pipe"
	Type string `json:"type" db:"type"`

	// Name is the human-readable label
	// Example: "Room 201", "Main Panel A", "Outlet 1"
	Name string `json:"name" db:"name"`

	// System identifies which building system this belongs to
	// Values: "structural", "electrical", "hvac", "plumbing", "fire_protection", "networking"
	System string `json:"system" db:"system"`

	// === FRACTAL HIERARCHY ===
	// ParentID links to the containing object (fractal parent)
	// A room's parent is a floor, a floor's parent is a building, etc.
	ParentID string `json:"parent_id" db:"parent_id"`

	// ChildIDs lists all objects contained within this one (fractal children)
	// A room contains outlets, switches, lights, etc.
	ChildIDs []string `json:"child_ids" db:"child_ids"`

	// === SPATIAL LOCATION ===
	// Position in 3D space with millimeter precision
	Position Position `json:"position" db:"position"`

	// Dimensions of the object
	Dimensions Dimensions `json:"dimensions" db:"dimensions"`

	// Rotation in degrees (0-360)
	Rotation Rotation `json:"rotation" db:"rotation"`

	// === SYSTEM PLANE (For 2D Overlap Resolution) ===
	// How this object layers with others at the same X,Y position
	SystemPlane SystemPlane `json:"system_plane" db:"system_plane"`

	// Overlaps lists IDs of objects at the same X,Y position
	Overlaps []Overlap `json:"overlaps" db:"overlaps"`

	// === ZOOM VISIBILITY ===
	// ScaleMin is the minimum zoom level where this object becomes visible
	// 100 = campus view, 10 = building, 1 = floor, 0.1 = room, 0.01 = fixture
	ScaleMin float64 `json:"scale_min" db:"scale_min"`

	// ScaleMax is the maximum zoom level where this object remains visible
	ScaleMax float64 `json:"scale_max" db:"scale_max"`

	// OptimalScale is the best zoom level to view this object
	OptimalScale float64 `json:"optimal_scale" db:"optimal_scale"`

	// === VISUAL REPRESENTATION ===
	// Geometry contains the visual representation
	Geometry Geometry `json:"geometry" db:"geometry"`

	// === SYMBOL RECOGNITION ===
	// SymbolID references the symbol library entry used to identify this
	// Example: "symbol:electrical:outlet:duplex"
	SymbolID string `json:"symbol_id" db:"symbol_id"`

	// Source indicates how this object was created
	// Values: "pdf", "photo", "lidar", "manual", "ifc"
	Source string `json:"source" db:"source"`

	// Confidence is the recognition confidence (0.0 to 1.0)
	Confidence float64 `json:"confidence" db:"confidence"`

	// === PROPERTIES ===
	// Properties stores system-specific attributes
	// Electrical outlet: {"voltage": 120, "amperage": 20, "circuit": "A-5"}
	// HVAC diffuser: {"cfm": 150, "type": "supply"}
	Properties map[string]interface{} `json:"properties" db:"properties"`

	// === CONNECTIONS ===
	// What this object connects to and how
	Connections []Connection `json:"connections" db:"connections"`

	// === CONTRIBUTION TRACKING ===
	// CreatedBy is the user ID who created this object
	CreatedBy string `json:"created_by" db:"created_by"`

	// CreatedAt timestamp
	CreatedAt time.Time `json:"created_at" db:"created_at"`

	// UpdatedBy is the last user to modify
	UpdatedBy string `json:"updated_by" db:"updated_by"`

	// UpdatedAt timestamp
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`

	// BILTReward is the total BILT tokens earned for this object
	BILTReward float64 `json:"bilt_reward" db:"bilt_reward"`

	// === HISTORY ===
	// History tracks all changes to this object
	History []Change `json:"history" db:"history"`

	// Version for optimistic locking
	Version int `json:"version" db:"version"`

	// === STATUS ===
	// Active indicates if this object is currently in use
	Active bool `json:"active" db:"active"`

	// Verified indicates if a professional has verified this data
	Verified bool `json:"verified" db:"verified"`

	// Tags for searchability
	Tags []string `json:"tags" db:"tags"`
}

// Position represents a point in 3D space with millimeter precision
type Position struct {
	X float64 `json:"x" db:"x"` // Millimeters from origin
	Y float64 `json:"y" db:"y"` // Millimeters from origin
	Z float64 `json:"z" db:"z"` // Height in millimeters
}

// Dimensions represents the size of an object
type Dimensions struct {
	Width  float64 `json:"width" db:"width"`   // Millimeters
	Height float64 `json:"height" db:"height"` // Millimeters
	Depth  float64 `json:"depth" db:"depth"`   // Millimeters
}

// Rotation represents orientation in 3D space
type Rotation struct {
	X float64 `json:"x" db:"x"` // Degrees (0-360)
	Y float64 `json:"y" db:"y"` // Degrees (0-360)
	Z float64 `json:"z" db:"z"` // Degrees (0-360)
}

// SystemPlane defines how objects layer in 2D views
type SystemPlane struct {
	// Layer name: "electrical", "hvac", "plumbing", etc.
	Layer string `json:"layer" db:"layer"`

	// ZOrder for rendering (0 = bottom, 100 = top)
	ZOrder int `json:"z_order" db:"z_order"`

	// Elevation: "underground", "floor", "wall", "ceiling", "above_ceiling"
	Elevation string `json:"elevation" db:"elevation"`
}

// Overlap represents objects that share the same X,Y position
type Overlap struct {
	ObjectID     string `json:"object_id" db:"object_id"`
	Relationship string `json:"relationship" db:"relationship"` // "mounted_on", "inside", "adjacent", "controls"
}

// Geometry contains the visual representation
type Geometry struct {
	// SVGPath for 2D rendering
	SVGPath string `json:"svg_path" db:"svg_path"`

	// Style for rendering (CSS-like)
	Style string `json:"style" db:"style"`

	// Icon for low zoom levels
	Icon string `json:"icon" db:"icon"`
}

// Connection represents a relationship to another object
type Connection struct {
	// ToID is the connected object's ID
	ToID string `json:"to_id" db:"to_id"`

	// Type of connection: "electrical_feed", "control", "data", "physical"
	Type string `json:"type" db:"type"`

	// Properties specific to this connection
	Properties map[string]interface{} `json:"properties" db:"properties"`
}

// Change represents a modification to the object
type Change struct {
	Timestamp   time.Time              `json:"timestamp" db:"timestamp"`
	UserID      string                 `json:"user_id" db:"user_id"`
	Action      string                 `json:"action" db:"action"` // "created", "updated", "verified"
	Description string                 `json:"description" db:"description"`
	OldValues   map[string]interface{} `json:"old_values" db:"old_values"`
	NewValues   map[string]interface{} `json:"new_values" db:"new_values"`
	BILTReward  float64                `json:"bilt_reward" db:"bilt_reward"`
}

// === METHODS ===

// NewArxObject creates a new ArxObject with defaults
func NewArxObject(id, objType, name, system string) *ArxObject {
	now := time.Now()
	return &ArxObject{
		ID:         id,
		Type:       objType,
		Name:       name,
		System:     system,
		Properties: make(map[string]interface{}),
		CreatedAt:  now,
		UpdatedAt:  now,
		Active:     true,
		Version:    1,
		ScaleMin:   0.1,  // Default: visible at room level
		ScaleMax:   0.001, // Default: visible to component level
	}
}

// GetPath returns the hierarchical path components
// "arx:building:floor:room:outlet" -> ["building", "floor", "room", "outlet"]
func (a *ArxObject) GetPath() []string {
	parts := strings.Split(a.ID, ":")
	if len(parts) > 1 {
		return parts[1:] // Skip "arx" prefix
	}
	return []string{}
}

// GetDepth returns the hierarchy depth (how many levels deep)
func (a *ArxObject) GetDepth() int {
	return len(a.GetPath())
}

// IsVisibleAtScale checks if object should be shown at given zoom level
func (a *ArxObject) IsVisibleAtScale(scale float64) bool {
	return scale <= a.ScaleMin && scale >= a.ScaleMax
}

// AddChild adds a child object ID
func (a *ArxObject) AddChild(childID string) {
	for _, id := range a.ChildIDs {
		if id == childID {
			return // Already exists
		}
	}
	a.ChildIDs = append(a.ChildIDs, childID)
}

// RemoveChild removes a child object ID
func (a *ArxObject) RemoveChild(childID string) {
	filtered := []string{}
	for _, id := range a.ChildIDs {
		if id != childID {
			filtered = append(filtered, id)
		}
	}
	a.ChildIDs = filtered
}

// AddConnection adds a connection to another object
func (a *ArxObject) AddConnection(toID, connType string, properties map[string]interface{}) {
	conn := Connection{
		ToID:       toID,
		Type:       connType,
		Properties: properties,
	}
	a.Connections = append(a.Connections, conn)
}

// SetProperty sets a property value
func (a *ArxObject) SetProperty(key string, value interface{}) {
	if a.Properties == nil {
		a.Properties = make(map[string]interface{})
	}
	a.Properties[key] = value
}

// GetProperty retrieves a property value
func (a *ArxObject) GetProperty(key string) (interface{}, bool) {
	if a.Properties == nil {
		return nil, false
	}
	val, exists := a.Properties[key]
	return val, exists
}

// RecordChange adds a change to the history
func (a *ArxObject) RecordChange(userID, action, description string, biltReward float64) {
	change := Change{
		Timestamp:   time.Now(),
		UserID:      userID,
		Action:      action,
		Description: description,
		BILTReward:  biltReward,
	}
	a.History = append(a.History, change)
	a.UpdatedBy = userID
	a.UpdatedAt = time.Now()
	a.BILTReward += biltReward
	a.Version++
}

// CalculateBILTReward calculates the reward for a contribution
func CalculateBILTReward(contribution string, detail string) float64 {
	baseReward := 1.0

	// Detail level multiplier
	detailMultiplier := map[string]float64{
		"building":  1.0,
		"floor":     1.5,
		"room":      2.0,
		"fixture":   2.5,
		"component": 3.0,
		"wiring":    4.0,
	}

	// Contribution type multiplier
	contributionMultiplier := map[string]float64{
		"create":  1.0,
		"update":  0.5,
		"verify":  0.3,
		"photo":   0.5,
		"specify": 0.7,
	}

	dm := detailMultiplier[detail]
	if dm == 0 {
		dm = 1.0
	}

	cm := contributionMultiplier[contribution]
	if cm == 0 {
		cm = 1.0
	}

	return baseReward * dm * cm
}

// Validate checks if the ArxObject is valid
func (a *ArxObject) Validate() error {
	if a.ID == "" {
		return fmt.Errorf("ID is required")
	}
	if !strings.HasPrefix(a.ID, "arx:") {
		return fmt.Errorf("ID must start with 'arx:'")
	}
	if a.Type == "" {
		return fmt.Errorf("Type is required")
	}
	if a.System == "" {
		return fmt.Errorf("System is required")
	}
	if a.ScaleMin < a.ScaleMax {
		return fmt.Errorf("ScaleMin must be >= ScaleMax")
	}
	return nil
}

// ToJSON converts the ArxObject to JSON
func (a *ArxObject) ToJSON() ([]byte, error) {
	return json.MarshalIndent(a, "", "  ")
}

// FromJSON creates an ArxObject from JSON
func FromJSON(data []byte) (*ArxObject, error) {
	var obj ArxObject
	err := json.Unmarshal(data, &obj)
	if err != nil {
		return nil, err
	}
	return &obj, nil
}