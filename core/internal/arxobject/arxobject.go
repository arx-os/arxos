// Package arxobject provides the core data model for building elements
// This is the consolidated implementation combining best features from all versions
package arxobject

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ArxObjectType represents the type of building element
type ArxObjectType string

// Core building element types
const (
	// Structural System (Priority 1)
	TypeWall           ArxObjectType = "wall"
	TypeColumn         ArxObjectType = "column"
	TypeBeam           ArxObjectType = "beam"
	TypeSlab           ArxObjectType = "slab"
	TypeFoundation     ArxObjectType = "foundation"
	TypeRoof           ArxObjectType = "roof"
	TypeStair          ArxObjectType = "stair"
	
	// Openings
	TypeDoor           ArxObjectType = "door"
	TypeWindow         ArxObjectType = "window"
	TypeOpening        ArxObjectType = "opening"
	
	// Spaces
	TypeRoom           ArxObjectType = "room"
	TypeFloor          ArxObjectType = "floor"
	TypeZone           ArxObjectType = "zone"
	TypeBuilding       ArxObjectType = "building"
	
	// MEP Systems
	TypeElectricalPanel   ArxObjectType = "electrical_panel"
	TypeElectricalOutlet  ArxObjectType = "electrical_outlet"
	TypeElectricalSwitch  ArxObjectType = "electrical_switch"
	TypeElectricalConduit ArxObjectType = "electrical_conduit"
	TypeLightFixture      ArxObjectType = "light_fixture"
	
	TypeHVACUnit       ArxObjectType = "hvac_unit"
	TypeHVACDuct       ArxObjectType = "hvac_duct"
	TypeHVACVent       ArxObjectType = "hvac_vent"
	TypeThermostat     ArxObjectType = "thermostat"
	
	TypePlumbingPipe   ArxObjectType = "plumbing_pipe"
	TypePlumbingFixture ArxObjectType = "plumbing_fixture"
	TypePlumbingValve   ArxObjectType = "plumbing_valve"
	TypeDrain          ArxObjectType = "drain"
	
	// Life Safety
	TypeFireSprinkler  ArxObjectType = "fire_sprinkler"
	TypeFireAlarm      ArxObjectType = "fire_alarm"
	TypeSmokeDetector  ArxObjectType = "smoke_detector"
	TypeEmergencyExit  ArxObjectType = "emergency_exit"
	TypeFireExtinguisher ArxObjectType = "fire_extinguisher"
	
	// Furniture & Equipment
	TypeFurniture      ArxObjectType = "furniture"
	TypeEquipment      ArxObjectType = "equipment"
	TypeAppliance      ArxObjectType = "appliance"
	
	// IoT/Smart Systems
	TypeSensor         ArxObjectType = "sensor"
	TypeActuator       ArxObjectType = "actuator"
	TypeController     ArxObjectType = "controller"
	TypeNetworkDevice  ArxObjectType = "network_device"
	
	// Generic
	TypeUnknown        ArxObjectType = "unknown"
	TypeCustom         ArxObjectType = "custom"
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
	Position    Point3D      `json:"position"`
	BoundingBox BoundingBox  `json:"bounding_box"`
	Rotation    float64      `json:"rotation"`     // Degrees
	Scale       float64      `json:"scale"`
	Points      []Point3D    `json:"points,omitempty"`      // For complex shapes
	Vertices    []Point3D    `json:"vertices,omitempty"`    // For 3D mesh
	Faces       [][]int      `json:"faces,omitempty"`       // Face indices
}

// Properties stores arbitrary key-value metadata
type Properties map[string]interface{}

// Relationship defines connections between ArxObjects
type Relationship struct {
	ID           string                 `json:"id"`
	Type         string                 `json:"type"`         // "contains", "connects_to", "adjacent_to", etc.
	TargetID     string                 `json:"target_id"`
	SourceID     string                 `json:"source_id"`
	Properties   map[string]interface{} `json:"properties,omitempty"`
	Confidence   float64                `json:"confidence"`
	CreatedAt    time.Time              `json:"created_at"`
}

// ValidationRecord tracks validation history
type ValidationRecord struct {
	ID           string                 `json:"id"`
	Timestamp    time.Time              `json:"timestamp"`
	ValidatedBy  string                 `json:"validated_by"`
	Method       string                 `json:"method"`       // "photo", "lidar", "manual", etc.
	Evidence     map[string]interface{} `json:"evidence"`     // Photo URLs, scan data, etc.
	Confidence   float64                `json:"confidence"`
	Notes        string                 `json:"notes"`
}

// ArxObject is the core building element representation
type ArxObject struct {
	// Core Identity
	ID           string        `json:"id"`
	Type         ArxObjectType `json:"type"`
	Name         string        `json:"name"`
	Description  string        `json:"description,omitempty"`
	
	// Hierarchy
	BuildingID   string        `json:"building_id"`
	FloorID      string        `json:"floor_id,omitempty"`
	ZoneID       string        `json:"zone_id,omitempty"`
	ParentID     string        `json:"parent_id,omitempty"`
	
	// Spatial
	Geometry     Geometry      `json:"geometry"`
	
	// Properties
	Properties   Properties    `json:"properties"`
	Material     string        `json:"material,omitempty"`
	Color        string        `json:"color,omitempty"`
	
	// Relationships
	Relationships []Relationship `json:"relationships,omitempty"`
	
	// Validation & Confidence
	ValidationStatus ValidationStatus    `json:"validation_status"`
	Validations      []ValidationRecord  `json:"validations,omitempty"`
	Confidence       float64             `json:"confidence"`       // 0.0 to 1.0
	ConfidenceFactors map[string]float64 `json:"confidence_factors,omitempty"`
	
	// Source & Versioning
	SourceType   string        `json:"source_type"`      // "pdf", "ifc", "lidar", etc.
	SourceFile   string        `json:"source_file,omitempty"`
	SourcePage   int           `json:"source_page,omitempty"`
	Version      int           `json:"version"`
	
	// Timestamps
	CreatedAt    time.Time     `json:"created_at"`
	UpdatedAt    time.Time     `json:"updated_at"`
	ValidatedAt  *time.Time    `json:"validated_at,omitempty"`
	
	// Metadata
	Tags         []string      `json:"tags,omitempty"`
	Flags        uint32        `json:"flags,omitempty"`   // Bit flags for quick filtering
	Hash         string        `json:"hash,omitempty"`    // Content hash for deduplication
	
	// Synchronization
	mu           sync.RWMutex  `json:"-"`
}

// NewArxObject creates a new ArxObject with defaults
func NewArxObject(objType ArxObjectType, name string) *ArxObject {
	now := time.Now()
	return &ArxObject{
		ID:               uuid.New().String(),
		Type:             objType,
		Name:             name,
		Properties:       make(Properties),
		Relationships:    []Relationship{},
		Validations:      []ValidationRecord{},
		ValidationStatus: ValidationPending,
		Confidence:       0.5, // Default medium confidence
		Version:          1,
		CreatedAt:        now,
		UpdatedAt:        now,
		ConfidenceFactors: make(map[string]float64),
	}
}

// SetGeometry sets the object's spatial properties
func (a *ArxObject) SetGeometry(g Geometry) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.Geometry = g
	a.UpdatedAt = time.Now()
}

// AddRelationship adds a relationship to another object
func (a *ArxObject) AddRelationship(rel Relationship) {
	a.mu.Lock()
	defer a.mu.Unlock()
	
	rel.ID = uuid.New().String()
	rel.CreatedAt = time.Now()
	a.Relationships = append(a.Relationships, rel)
	a.UpdatedAt = time.Now()
}

// SetProperty sets a property value
func (a *ArxObject) SetProperty(key string, value interface{}) {
	a.mu.Lock()
	defer a.mu.Unlock()
	
	if a.Properties == nil {
		a.Properties = make(Properties)
	}
	a.Properties[key] = value
	a.UpdatedAt = time.Now()
}

// GetProperty retrieves a property value
func (a *ArxObject) GetProperty(key string) (interface{}, bool) {
	a.mu.RLock()
	defer a.mu.RUnlock()
	
	val, exists := a.Properties[key]
	return val, exists
}

// Validate adds a validation record and updates confidence
func (a *ArxObject) Validate(record ValidationRecord) {
	a.mu.Lock()
	defer a.mu.Unlock()
	
	record.ID = uuid.New().String()
	record.Timestamp = time.Now()
	
	a.Validations = append(a.Validations, record)
	
	// Update validation status
	if record.Confidence >= 0.9 {
		a.ValidationStatus = ValidationValidated
		now := time.Now()
		a.ValidatedAt = &now
	} else if record.Confidence >= 0.5 {
		a.ValidationStatus = ValidationPartial
	}
	
	// Update overall confidence (weighted average)
	a.updateConfidence()
	a.UpdatedAt = time.Now()
}

// updateConfidence recalculates the overall confidence score
func (a *ArxObject) updateConfidence() {
	if len(a.Validations) == 0 {
		return
	}
	
	var totalWeight float64
	var weightedSum float64
	
	for _, v := range a.Validations {
		// More recent validations have higher weight
		age := time.Since(v.Timestamp).Hours() / 24 // Days
		weight := 1.0 / (1.0 + age/30) // Decay over 30 days
		
		weightedSum += v.Confidence * weight
		totalWeight += weight
	}
	
	if totalWeight > 0 {
		a.Confidence = weightedSum / totalWeight
	}
}

// IsValidated checks if the object has been validated
func (a *ArxObject) IsValidated() bool {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.ValidationStatus == ValidationValidated
}

// GetRelationships returns relationships of a specific type
func (a *ArxObject) GetRelationships(relType string) []Relationship {
	a.mu.RLock()
	defer a.mu.RUnlock()
	
	var filtered []Relationship
	for _, rel := range a.Relationships {
		if rel.Type == relType {
			filtered = append(filtered, rel)
		}
	}
	return filtered
}

// Clone creates a deep copy of the ArxObject
func (a *ArxObject) Clone() *ArxObject {
	a.mu.RLock()
	defer a.mu.RUnlock()
	
	// Marshal and unmarshal for deep copy
	data, _ := json.Marshal(a)
	var clone ArxObject
	json.Unmarshal(data, &clone)
	
	clone.ID = uuid.New().String()
	clone.Version = 1
	clone.CreatedAt = time.Now()
	clone.UpdatedAt = time.Now()
	
	return &clone
}

// CalculateHash generates a content hash for deduplication
func (a *ArxObject) CalculateHash() string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	
	// Create hash from core properties
	hashData := fmt.Sprintf("%s-%s-%v-%v-%s",
		a.Type,
		a.Name,
		a.Geometry.Position,
		a.Geometry.BoundingBox,
		a.Material,
	)
	
	// Simple hash for now - should use crypto/sha256 in production
	return fmt.Sprintf("%x", hashData)
}

// ToJSON serializes the ArxObject to JSON
func (a *ArxObject) ToJSON() ([]byte, error) {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return json.Marshal(a)
}

// FromJSON deserializes an ArxObject from JSON
func FromJSON(data []byte) (*ArxObject, error) {
	var obj ArxObject
	if err := json.Unmarshal(data, &obj); err != nil {
		return nil, err
	}
	return &obj, nil
}

// String returns a string representation
func (a *ArxObject) String() string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return fmt.Sprintf("ArxObject[%s: %s (%s) - Confidence: %.2f]",
		a.ID, a.Name, a.Type, a.Confidence)
}