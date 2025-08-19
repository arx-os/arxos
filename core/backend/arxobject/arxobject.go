package arxobject

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
)

// ArxObject represents an intelligent building component
type ArxObject struct {
	// Core Identity
	ID   string `json:"id" db:"id"`
	UUID string `json:"uuid" db:"uuid"`
	Type string `json:"type" db:"type"`

	// Spatial Position (nanometer precision)
	X int64 `json:"x" db:"x"` // Nanometers from origin
	Y int64 `json:"y" db:"y"` // Nanometers from origin
	Z int64 `json:"z" db:"z"` // Nanometers from origin

	// Dimensions (nanometers)
	Width  int64 `json:"width" db:"width"`
	Height int64 `json:"height" db:"height"`
	Depth  int64 `json:"depth" db:"depth"`

	// Fractal Scale Levels (0-9)
	ScaleMin int `json:"scale_min" db:"scale_min"`
	ScaleMax int `json:"scale_max" db:"scale_max"`

	// System Classification
	System string `json:"system" db:"system"` // structural, electrical, hvac, plumbing

	// Intelligent Properties
	Properties json.RawMessage `json:"properties" db:"properties"`
	Confidence ConfidenceScore `json:"confidence" db:"confidence"`

	// Relationships
	ParentID      *string        `json:"parent_id" db:"parent_id"`
	BuildingID    *int64         `json:"building_id" db:"building_id"`
	FloorID       *int64         `json:"floor_id" db:"floor_id"`
	RoomID        *int64         `json:"room_id" db:"room_id"`
	Relationships []Relationship `json:"relationships" db:"relationships"`

	// Metadata
	ExtractionMethod string    `json:"extraction_method" db:"extraction_method"`
	Source           string    `json:"source" db:"source"`
	CreatedAt        time.Time `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time `json:"updated_at" db:"updated_at"`
	ValidatedAt      *time.Time `json:"validated_at" db:"validated_at"`
	ValidatedBy      *string   `json:"validated_by" db:"validated_by"`
}

// ConfidenceScore represents multi-dimensional confidence
type ConfidenceScore struct {
	Classification float32 `json:"classification"` // How certain about object type
	Position       float32 `json:"position"`       // Spatial accuracy confidence
	Properties     float32 `json:"properties"`     // Data accuracy confidence
	Relationships  float32 `json:"relationships"`  // Connection validity
	Overall        float32 `json:"overall"`        // Weighted average
}

// CalculateOverall computes the weighted overall confidence
func (c *ConfidenceScore) CalculateOverall() {
	// Weighted average based on importance
	c.Overall = (c.Classification*0.3 + 
				c.Position*0.3 + 
				c.Properties*0.2 + 
				c.Relationships*0.2)
}

// IsHighConfidence returns true if overall confidence > 0.85
func (c *ConfidenceScore) IsHighConfidence() bool {
	return c.Overall > 0.85
}

// IsMediumConfidence returns true if confidence is between 0.60 and 0.85
func (c *ConfidenceScore) IsMediumConfidence() bool {
	return c.Overall >= 0.60 && c.Overall <= 0.85
}

// IsLowConfidence returns true if overall confidence < 0.60
func (c *ConfidenceScore) IsLowConfidence() bool {
	return c.Overall < 0.60
}

// Relationship defines connections between ArxObjects
type Relationship struct {
	Type       string                 `json:"type"`       // contains, adjacent_to, powers, etc.
	TargetID   string                 `json:"target_id"`  
	Confidence float32                `json:"confidence"` 
	Properties map[string]interface{} `json:"properties"` 
	Metadata   RelationshipMetadata   `json:"metadata"`   
}

// RelationshipMetadata contains relationship source information
type RelationshipMetadata struct {
	Source      string    `json:"source"`
	InferredAt  time.Time `json:"inferred_at"`
	ValidatedAt *time.Time `json:"validated_at"`
}

// NewArxObject creates a new ArxObject with defaults
func NewArxObject(objType, system string) *ArxObject {
	now := time.Now()
	return &ArxObject{
		ID:        fmt.Sprintf("arx_%s", uuid.New().String()),
		UUID:      uuid.New().String(),
		Type:      objType,
		System:    system,
		ScaleMin:  0,
		ScaleMax:  9,
		CreatedAt: now,
		UpdatedAt: now,
		Confidence: ConfidenceScore{
			Classification: 0.5,
			Position:       0.5,
			Properties:     0.5,
			Relationships:  0.5,
			Overall:        0.5,
		},
		Relationships: make([]Relationship, 0),
	}
}

// SetPosition sets the position in millimeters and converts to nanometers
func (a *ArxObject) SetPosition(xMM, yMM, zMM float64) {
	a.X = int64(xMM * 1000000) // Convert mm to nm
	a.Y = int64(yMM * 1000000)
	a.Z = int64(zMM * 1000000)
}

// GetPositionMM returns position in millimeters
func (a *ArxObject) GetPositionMM() (float64, float64, float64) {
	return float64(a.X) / 1000000, float64(a.Y) / 1000000, float64(a.Z) / 1000000
}

// SetDimensions sets dimensions in millimeters and converts to nanometers
func (a *ArxObject) SetDimensions(widthMM, heightMM, depthMM float64) {
	a.Width = int64(widthMM * 1000000)
	a.Height = int64(heightMM * 1000000)
	a.Depth = int64(depthMM * 1000000)
}

// GetDimensionsMM returns dimensions in millimeters
func (a *ArxObject) GetDimensionsMM() (float64, float64, float64) {
	return float64(a.Width) / 1000000, float64(a.Height) / 1000000, float64(a.Depth) / 1000000
}

// IsVisibleAtScale checks if object should be rendered at given scale
func (a *ArxObject) IsVisibleAtScale(scale int) bool {
	return scale >= a.ScaleMin && scale <= a.ScaleMax
}

// AddRelationship adds a new relationship to another ArxObject
func (a *ArxObject) AddRelationship(relType string, targetID string, confidence float32) {
	rel := Relationship{
		Type:       relType,
		TargetID:   targetID,
		Confidence: confidence,
		Properties: make(map[string]interface{}),
		Metadata: RelationshipMetadata{
			Source:     "system",
			InferredAt: time.Now(),
		},
	}
	a.Relationships = append(a.Relationships, rel)
	
	// Update relationship confidence
	if len(a.Relationships) > 0 {
		var totalConf float32
		for _, r := range a.Relationships {
			totalConf += r.Confidence
		}
		a.Confidence.Relationships = totalConf / float32(len(a.Relationships))
		a.Confidence.CalculateOverall()
	}
}

// Validate marks the object as validated by a user
func (a *ArxObject) Validate(validatorID string) {
	now := time.Now()
	a.ValidatedAt = &now
	a.ValidatedBy = &validatorID
	
	// Boost confidence after validation
	a.Confidence.Classification = min(a.Confidence.Classification*1.2, 1.0)
	a.Confidence.Position = min(a.Confidence.Position*1.2, 1.0)
	a.Confidence.Properties = min(a.Confidence.Properties*1.2, 1.0)
	a.Confidence.CalculateOverall()
	
	a.UpdatedAt = now
}

// GetHierarchyPath returns the full hierarchy path
func (a *ArxObject) GetHierarchyPath() string {
	path := fmt.Sprintf("arx:%s", a.Type)
	
	if a.BuildingID != nil {
		path = fmt.Sprintf("building:%d/%s", *a.BuildingID, path)
	}
	if a.FloorID != nil {
		path = fmt.Sprintf("floor:%d/%s", *a.FloorID, path)
	}
	if a.RoomID != nil {
		path = fmt.Sprintf("room:%d/%s", *a.RoomID, path)
	}
	
	return path
}

// Helper function
func min(a, b float32) float32 {
	if a < b {
		return a
	}
	return b
}

// Object Type Constants
const (
	// Structural Elements
	TypeWall       = "wall"
	TypeColumn     = "column"
	TypeBeam       = "beam"
	TypeSlab       = "slab"
	TypeFoundation = "foundation"
	TypeRoof       = "roof"
	TypeDoor       = "door"
	TypeWindow     = "window"
	
	// Spatial Elements
	TypeBuilding      = "building"
	TypeFloor         = "floor"
	TypeRoom          = "room"
	TypeZone          = "zone"
	TypeCorridor      = "corridor"
	TypeStairwell     = "stairwell"
	TypeElevatorShaft = "elevator_shaft"
	
	// Electrical System
	TypeOutlet       = "electrical_outlet"
	TypeSwitch       = "electrical_switch"
	TypePanel        = "electrical_panel"
	TypeConduit      = "electrical_conduit"
	TypeLightFixture = "light_fixture"
	TypeCircuit      = "circuit"
	TypeTransformer  = "transformer"
	
	// HVAC System
	TypeDuct       = "hvac_duct"
	TypeVent       = "hvac_vent"
	TypeUnit       = "hvac_unit"
	TypeThermostat = "thermostat"
	TypeDamper     = "damper"
	TypeSensor     = "sensor"
	
	// Plumbing System
	TypePipe    = "plumbing_pipe"
	TypeFixture = "plumbing_fixture"
	TypeValve   = "valve"
	TypePump    = "pump"
	TypeDrain   = "drain"
	TypeTank    = "tank"
	
	// Equipment & Devices
	TypeEquipment     = "equipment"
	TypeActuator      = "actuator"
	TypeController    = "controller"
	TypeNetworkDevice = "network_device"
	TypeFireAlarm     = "fire_alarm"
	TypeSprinkler     = "sprinkler"
	TypeCamera        = "camera"
)

// System Constants
const (
	SystemStructural = "structural"
	SystemElectrical = "electrical"
	SystemHVAC       = "hvac"
	SystemPlumbing   = "plumbing"
	SystemFire       = "fire"
	SystemSecurity   = "security"
	SystemNetwork    = "network"
	SystemLighting   = "lighting"
)

// Relationship Type Constants
const (
	// Spatial Relationships
	RelContains    = "contains"
	RelContainedBy = "contained_by"
	RelAdjacentTo  = "adjacent_to"
	RelAbove       = "above"
	RelBelow       = "below"
	RelConnectedTo = "connected_to"
	
	// Functional Relationships
	RelPowers    = "powers"
	RelControls  = "controls"
	RelServes    = "serves"
	RelMonitors  = "monitors"
	RelPartOf    = "part_of"
	RelGroupedWith = "grouped_with"
	
	// System Relationships
	RelUpstream   = "upstream"
	RelDownstream = "downstream"
	RelPrimary    = "primary"
	RelBackup     = "backup"
	RelSupports   = "supports"
	RelSupportedBy = "supported_by"
)

// Scale Level Constants
const (
	ScaleGlobal     = 0  // Continental infrastructure
	ScaleRegional   = 1  // State/province level
	ScaleMunicipal  = 2  // City level
	ScaleCampus     = 3  // Multi-building site
	ScaleBuilding   = 4  // Individual building
	ScaleFloor      = 5  // Floor level
	ScaleRoom       = 6  // Room level
	ScaleComponent  = 7  // Equipment/fixture level
	ScaleCircuit    = 8  // Circuit board level
	ScaleTrace      = 9  // Nanometer precision
)