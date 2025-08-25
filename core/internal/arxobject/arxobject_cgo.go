// Package arxobject provides the core data model for building elements
// This is the CGO-optimized implementation using the ARXOS C core
package arxobject

import (
	"fmt"
	"sync"
	"time"

	"github.com/arxos/core/cgo"
	"github.com/google/uuid"
)

// ArxObjectType represents the type of building element
type ArxObjectType string

// Core building element types - mapped to C core enum values
const (
	// Structural System (Priority 1)
	TypeWall       ArxObjectType = "wall"
	TypeColumn     ArxObjectType = "column"
	TypeBeam       ArxObjectType = "beam"
	TypeSlab       ArxObjectType = "slab"
	TypeFoundation ArxObjectType = "foundation"
	TypeRoof       ArxObjectType = "roof"
	TypeStair      ArxObjectType = "stair"

	// Openings
	TypeDoor    ArxObjectType = "door"
	TypeWindow  ArxObjectType = "window"
	TypeOpening ArxObjectType = "opening"

	// Spaces
	TypeRoom     ArxObjectType = "room"
	TypeFloor    ArxObjectType = "floor"
	TypeZone     ArxObjectType = "zone"
	TypeBuilding ArxObjectType = "building"

	// MEP Systems
	TypeElectricalPanel   ArxObjectType = "electrical_panel"
	TypeElectricalOutlet  ArxObjectType = "electrical_outlet"
	TypeElectricalSwitch  ArxObjectType = "electrical_switch"
	TypeElectricalConduit ArxObjectType = "electrical_conduit"
	TypeLightFixture      ArxObjectType = "light_fixture"

	TypeHVACUnit   ArxObjectType = "hvac_unit"
	TypeHVACDuct   ArxObjectType = "hvac_duct"
	TypeHVACVent   ArxObjectType = "hvac_vent"
	TypeThermostat ArxObjectType = "thermostat"

	TypePlumbingPipe    ArxObjectType = "plumbing_pipe"
	TypePlumbingFixture ArxObjectType = "plumbing_fixture"
	TypePlumbingValve   ArxObjectType = "plumbing_valve"
	TypeDrain           ArxObjectType = "drain"

	// Life Safety
	TypeFireSprinkler    ArxObjectType = "fire_sprinkler"
	TypeFireAlarm        ArxObjectType = "fire_alarm"
	TypeSmokeDetector    ArxObjectType = "smoke_detector"
	TypeEmergencyExit    ArxObjectType = "emergency_exit"
	TypeFireExtinguisher ArxObjectType = "fire_extinguisher"

	// Furniture & Equipment
	TypeFurniture ArxObjectType = "furniture"
	TypeEquipment ArxObjectType = "equipment"
	TypeAppliance ArxObjectType = "appliance"

	// IoT/Smart Systems
	TypeSensor        ArxObjectType = "sensor"
	TypeActuator      ArxObjectType = "actuator"
	TypeController    ArxObjectType = "controller"
	TypeNetworkDevice ArxObjectType = "network_device"

	// Generic
	TypeUnknown ArxObjectType = "unknown"
	TypeCustom  ArxObjectType = "custom"
)

// ValidationStatus represents the validation state
type ValidationStatus string

const (
	ValidationPending   ValidationStatus = "pending"
	ValidationValidated ValidationStatus = "validated"
	ValidationFailed    ValidationStatus = "failed"
	ValidationPartial   ValidationStatus = "partial"
)

// Point3D represents a point in 3D space (millimeter precision)
type Point3D struct {
	X int64 `json:"x"`
	Y int64 `json:"y"`
	Z int64 `json:"z"`
}

// BoundingBox represents the spatial bounds of an object
type BoundingBox struct {
	Min Point3D `json:"min"`
	Max Point3D `json:"max"`
}

// Geometry represents the spatial properties of an object
type Geometry struct {
	Position    Point3D     `json:"position"`
	BoundingBox BoundingBox `json:"bounding_box"`
	Rotation    float64     `json:"rotation"` // Degrees
	Scale       float64     `json:"scale"`
	Points      []Point3D   `json:"points,omitempty"`   // For complex shapes
	Vertices    []Point3D   `json:"vertices,omitempty"` // For 3D mesh
	Faces       [][]int     `json:"faces,omitempty"`    // Face indices
}

// Properties stores arbitrary key-value metadata
type Properties map[string]interface{}

// Relationship defines connections between ArxObjects
type Relationship struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"` // "contains", "connects_to", "adjacent_to", etc.
	TargetID   string                 `json:"target_id"`
	SourceID   string                 `json:"source_id"`
	Properties map[string]interface{} `json:"properties,omitempty"`
	Confidence float64                `json:"confidence"`
	CreatedAt  time.Time              `json:"created_at"`
}

// ValidationRecord tracks validation history
type ValidationRecord struct {
	ID          string                 `json:"id"`
	Timestamp   time.Time              `json:"timestamp"`
	ValidatedBy string                 `json:"validated_by"`
	Method      string                 `json:"method"`   // "photo", "lidar", "manual", etc.
	Evidence    map[string]interface{} `json:"evidence"` // Photo URLs, scan data, etc.
	Confidence  float64                `json:"confidence"`
	Notes       string                 `json:"notes"`
}

// ArxObject is the core building element representation
// Now optimized with CGO bridge for high-performance operations
type ArxObject struct {
	// Core Identity
	ID          string        `json:"id"`
	Type        ArxObjectType `json:"type"`
	Name        string        `json:"name"`
	Description string        `json:"description,omitempty"`

	// Hierarchy
	BuildingID string `json:"building_id"`
	FloorID    string `json:"floor_id,omitempty"`
	ZoneID     string `json:"zone_id,omitempty"`
	ParentID   string `json:"parent_id,omitempty"`

	// Spatial
	Geometry Geometry `json:"geometry"`

	// Properties
	Properties Properties `json:"properties"`
	Material   string     `json:"material,omitempty"`
	Color      string     `json:"color,omitempty"`

	// Relationships
	Relationships []Relationship `json:"relationships,omitempty"`

	// Validation & Confidence
	ValidationStatus  ValidationStatus   `json:"validation_status"`
	Validations       []ValidationRecord `json:"validations,omitempty"`
	Confidence        float64            `json:"confidence"` // 0.0 to 1.0
	ConfidenceFactors map[string]float64 `json:"confidence_factors,omitempty"`

	// Source & Versioning
	SourceType string `json:"source_type"` // "pdf", "ifc", "lidar", etc.
	SourceFile string `json:"source_file,omitempty"`
	SourcePage int    `json:"source_page,omitempty"`
	Version    int    `json:"version"`

	// Timestamps
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
	ValidatedAt *time.Time `json:"validated_at,omitempty"`

	// Metadata
	Tags  []string `json:"tags,omitempty"`
	Flags uint32   `json:"flags,omitempty"` // Bit flags for quick filtering
	Hash  string   `json:"hash,omitempty"`  // Content hash for deduplication

	// CGO Bridge Integration
	cgoObject *cgo.ArxObject `json:"-"` // High-performance C core object
	mu        sync.RWMutex   `json:"-"` // Thread safety
}

// NewArxObject creates a new ArxObject with defaults
// Now optimized with CGO bridge for instant creation
func NewArxObject(objType ArxObjectType, name string) *ArxObject {
	now := time.Now()

	// Create Go object
	goObj := &ArxObject{
		ID:               uuid.New().String(),
		Type:             objType,
		Name:             name,
		Properties:       make(Properties),
		Relationships:    []Relationship{},
		Validations:      []ValidationRecord{},
		ValidationStatus: ValidationPending,
		Confidence:       0.5, // Default medium confidence
		SourceType:       "manual",
		Version:          1,
		CreatedAt:        now,
		UpdatedAt:        now,
		Tags:             []string{},
		Flags:            0,
	}

	// Create corresponding CGO object for high-performance operations
	cgoType := mapArxObjectTypeToCGO(objType)
	cgoObj, err := cgo.CreateArxObject(goObj.ID, name, goObj.Description, cgoType)
	if err == nil {
		goObj.cgoObject = cgoObj
	} else {
		// Fallback to Go-only mode if CGO fails
		goObj.cgoObject = nil
	}

	return goObj
}

// mapArxObjectTypeToCGO maps Go ArxObjectType to CGO enum values
func mapArxObjectTypeToCGO(goType ArxObjectType) cgo.ArxObjectType {
	switch goType {
	case TypeWall:
		return 1 // ARX_OBJECT_TYPE_WALL
	case TypeColumn:
		return 2 // ARX_OBJECT_TYPE_COLUMN
	case TypeBeam:
		return 3 // ARX_OBJECT_TYPE_BEAM
	case TypeSlab:
		return 4 // ARX_OBJECT_TYPE_SLAB
	case TypeFoundation:
		return 5 // ARX_OBJECT_TYPE_FOUNDATION
	case TypeRoof:
		return 6 // ARX_OBJECT_TYPE_ROOF
	case TypeStair:
		return 7 // ARX_OBJECT_TYPE_STAIR
	case TypeDoor:
		return 8 // ARX_OBJECT_TYPE_DOOR
	case TypeWindow:
		return 9 // ARX_OBJECT_TYPE_WINDOW
	case TypeOpening:
		return 10 // ARX_OBJECT_TYPE_OPENING
	case TypeRoom:
		return 11 // ARX_OBJECT_TYPE_ROOM
	case TypeFloor:
		return 12 // ARX_OBJECT_TYPE_FLOOR
	case TypeZone:
		return 13 // ARX_OBJECT_TYPE_ZONE
	case TypeBuilding:
		return 14 // ARX_OBJECT_TYPE_BUILDING
	default:
		return 0 // ARX_OBJECT_TYPE_UNKNOWN
	}
}

// SetProperty sets a property with high-performance CGO bridge
func (obj *ArxObject) SetProperty(key string, value interface{}) {
	obj.mu.Lock()
	defer obj.mu.Unlock()

	// Update Go properties
	obj.Properties[key] = value
	obj.UpdatedAt = time.Now()

	// Update CGO object if available
	if obj.cgoObject != nil {
		// Convert value to string for CGO
		strValue := fmt.Sprintf("%v", value)
		err := obj.cgoObject.SetProperty(key, strValue)
		if err != nil {
			// Log error but continue with Go-only mode
			obj.cgoObject = nil
		}
	}
}

// GetProperty retrieves a property with high-performance CGO bridge
func (obj *ArxObject) GetProperty(key string) (interface{}, bool) {
	obj.mu.RLock()
	defer obj.mu.RUnlock()

	// Try CGO first for maximum performance
	if obj.cgoObject != nil {
		value, err := obj.cgoObject.GetProperty(key)
		if err == nil {
			return value, true
		}
		// Fallback to Go if CGO fails
		obj.cgoObject = nil
	}

	// Fallback to Go properties
	value, exists := obj.Properties[key]
	return value, exists
}

// SetGeometry updates the spatial properties with CGO optimization
func (obj *ArxObject) SetGeometry(geometry Geometry) {
	obj.mu.Lock()
	defer obj.mu.Unlock()

	obj.Geometry = geometry
	obj.UpdatedAt = time.Now()

	// TODO: Update CGO geometry when bridge supports it
	// This will provide sub-millisecond spatial operations
}

// GetGeometry returns the current geometry
func (obj *ArxObject) GetGeometry() Geometry {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	return obj.Geometry
}

// UpdatePosition updates the object position with CGO optimization
func (obj *ArxObject) UpdatePosition(x, y, z int64) {
	obj.mu.Lock()
	defer obj.mu.Unlock()

	obj.Geometry.Position = Point3D{X: x, Y: y, Z: z}
	obj.UpdatedAt = time.Now()

	// TODO: Update CGO position when bridge supports it
	// This will provide instant spatial updates
}

// AddRelationship adds a relationship to another ArxObject
func (obj *ArxObject) AddRelationship(relType, targetID string, confidence float64) {
	obj.mu.Lock()
	defer obj.mu.Unlock()

	relationship := Relationship{
		ID:         uuid.New().String(),
		Type:       relType,
		TargetID:   targetID,
		SourceID:   obj.ID,
		Confidence: confidence,
		CreatedAt:  time.Now(),
	}

	obj.Relationships = append(obj.Relationships, relationship)
	obj.UpdatedAt = time.Now()
}

// GetRelationships returns all relationships
func (obj *ArxObject) GetRelationships() []Relationship {
	obj.mu.RLock()
	defer obj.mu.RUnlock()

	// Return a copy to prevent external modification
	relationships := make([]Relationship, len(obj.Relationships))
	copy(relationships, obj.Relationships)
	return relationships
}

// Validate marks the object as validated
func (obj *ArxObject) Validate(validatedBy, method string, confidence float64, notes string) {
	obj.mu.Lock()
	defer obj.mu.Unlock()

	now := time.Now()
	validation := ValidationRecord{
		ID:          uuid.New().String(),
		Timestamp:   now,
		ValidatedBy: validatedBy,
		Method:      method,
		Confidence:  confidence,
		Notes:       notes,
	}

	obj.Validations = append(obj.Validations, validation)
	obj.ValidationStatus = ValidationValidated
	obj.ValidatedAt = &now
	obj.UpdatedAt = now
	obj.Confidence = confidence
}

// Clone creates a deep copy of the ArxObject
func (obj *ArxObject) Clone() *ArxObject {
	obj.mu.RLock()
	defer obj.mu.RUnlock()

	// Create new object with new ID
	clone := NewArxObject(obj.Type, obj.Name+" (Copy)")

	// Copy all fields
	clone.Description = obj.Description
	clone.BuildingID = obj.BuildingID
	clone.FloorID = obj.FloorID
	clone.ZoneID = obj.ZoneID
	clone.ParentID = obj.ParentID
	clone.Geometry = obj.Geometry
	clone.Material = obj.Material
	clone.Color = obj.Color
	clone.ValidationStatus = obj.ValidationStatus
	clone.Confidence = obj.Confidence
	clone.SourceType = obj.SourceType
	clone.SourceFile = obj.SourceFile
	clone.SourcePage = obj.SourcePage
	clone.Tags = append([]string{}, obj.Tags...)
	clone.Flags = obj.Flags

	// Deep copy properties
	for k, v := range obj.Properties {
		clone.Properties[k] = v
	}

	// Deep copy relationships
	for _, rel := range obj.Relationships {
		clone.AddRelationship(rel.Type, rel.TargetID, rel.Confidence)
	}

	// Deep copy validations
	for _, val := range obj.Validations {
		clone.Validate(val.ValidatedBy, val.Method, val.Confidence, val.Notes)
	}

	return clone
}

// Destroy cleans up the ArxObject and its CGO resources
func (obj *ArxObject) Destroy() {
	obj.mu.Lock()
	defer obj.mu.Unlock()

	// Clean up CGO object
	if obj.cgoObject != nil {
		obj.cgoObject.Destroy()
		obj.cgoObject = nil
	}

	// Clear Go references
	obj.Properties = nil
	obj.Relationships = nil
	obj.Validations = nil
	obj.Tags = nil
}

// IsValid checks if the object is in a valid state
func (obj *ArxObject) IsValid() bool {
	obj.mu.RLock()
	defer obj.mu.RUnlock()

	return obj.ID != "" && obj.Name != "" && obj.Type != ""
}

// GetCGOObject returns the underlying CGO object for advanced operations
// This enables direct access to C core functions when needed
func (obj *ArxObject) GetCGOObject() *cgo.ArxObject {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	return obj.cgoObject
}

// HasCGOBridge returns true if the object is using the CGO bridge
func (obj *ArxObject) HasCGOBridge() bool {
	obj.mu.RLock()
	defer obj.mu.RUnlock()
	return obj.cgoObject != nil
}

// Performance metrics for monitoring
func (obj *ArxObject) GetPerformanceMetrics() map[string]interface{} {
	obj.mu.RLock()
	defer obj.mu.RUnlock()

	metrics := map[string]interface{}{
		"has_cgo_bridge":     obj.cgoObject != nil,
		"property_count":     len(obj.Properties),
		"relationship_count": len(obj.Relationships),
		"validation_count":   len(obj.Validations),
		"last_updated":       obj.UpdatedAt,
	}

	return metrics
}
