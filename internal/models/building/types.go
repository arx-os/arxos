package building

import (
	"time"
)

// ConfidenceLevel represents the confidence in data accuracy
type ConfidenceLevel int

const (
	ConfidenceUnknown ConfidenceLevel = iota
	ConfidenceEstimated
	ConfidenceLow
	ConfidenceMedium
	ConfidenceHigh
	ConfidenceVerified
)

// DataSource represents where the building data originated
type DataSource string

const (
	DataSourcePDF        DataSource = "pdf"
	DataSourceIFC        DataSource = "ifc"
	DataSourceBIM        DataSource = "bim"
	DataSourceDWG        DataSource = "dwg"
	DataSourceLiDAR      DataSource = "lidar"
	DataSourceARVerified DataSource = "ar_verified"
	DataSourceManual     DataSource = "manual"
)

// BuildingModel represents a complete building with all its data
type BuildingModel struct {
	// Core identification
	ID          string `json:"id"`
	UUID        string `json:"uuid"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Address     string `json:"address"`

	// Spatial data
	Origin      *SpatialReference `json:"origin,omitempty"`
	BoundingBox *BoundingBox      `json:"bounding_box,omitempty"`
	GridScale   float64           `json:"grid_scale"` // meters per grid unit

	// Hierarchical structure
	Floors  []Floor  `json:"floors"`
	Systems []System `json:"systems"`

	// Metadata
	Source     DataSource             `json:"source"`
	Confidence ConfidenceLevel        `json:"confidence"`
	ImportedAt time.Time              `json:"imported_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
	Properties map[string]interface{} `json:"properties,omitempty"`

	// Data quality
	ValidationIssues []ValidationIssue `json:"validation_issues,omitempty"`
	Coverage         float64           `json:"coverage"` // 0-100% of building covered
}

// Floor represents a single floor/level in a building
type Floor struct {
	ID          string  `json:"id"`
	Number      int     `json:"number"`
	Name        string  `json:"name"`
	Description string  `json:"description,omitempty"`
	Height      float64 `json:"height"`    // meters
	Elevation   float64 `json:"elevation"` // meters above ground

	// Spatial bounds for this floor
	BoundingBox *BoundingBox `json:"bounding_box,omitempty"`

	// Contents
	Rooms     []Room      `json:"rooms"`
	Equipment []Equipment `json:"equipment"`

	// Data quality
	Confidence ConfidenceLevel        `json:"confidence"`
	Properties map[string]interface{} `json:"properties,omitempty"`
}

// Room represents a space within a floor
type Room struct {
	ID     string `json:"id"`
	Number string `json:"number"`
	Name   string `json:"name"`
	Type   string `json:"type"` // office, conference, lobby, etc.

	// Spatial data
	Area     float64   `json:"area,omitempty"`     // square meters
	Height   float64   `json:"height,omitempty"`   // meters
	Position *Point3D  `json:"position,omitempty"` // center point
	Boundary []Point3D `json:"boundary,omitempty"` // polygon points

	// Relationships
	FloorID    string   `json:"floor_id"`
	AdjacentTo []string `json:"adjacent_to,omitempty"` // adjacent room IDs

	// Contents
	Equipment []string `json:"equipment_ids"` // equipment in this room

	// Data quality
	Confidence ConfidenceLevel        `json:"confidence"`
	Properties map[string]interface{} `json:"properties,omitempty"`
}

// Equipment represents any device or component in the building
type Equipment struct {
	ID      string `json:"id"`
	Tag     string `json:"tag,omitempty"` // equipment tag/code
	Name    string `json:"name"`
	Type    string `json:"type"`              // hvac, electrical, plumbing, etc.
	Subtype string `json:"subtype,omitempty"` // specific type
	Status  string `json:"status"`            // operational, maintenance, offline

	// Spatial data
	Position    *Point3D     `json:"position,omitempty"`    // 3D position
	Orientation *Orientation `json:"orientation,omitempty"` // rotation
	Size        *Size3D      `json:"size,omitempty"`        // dimensions

	// Relationships
	FloorID     string   `json:"floor_id,omitempty"`
	RoomID      string   `json:"room_id,omitempty"`
	SystemID    string   `json:"system_id,omitempty"`
	ConnectedTo []string `json:"connected_to,omitempty"` // other equipment

	// Technical specifications
	Manufacturer string     `json:"manufacturer,omitempty"`
	Model        string     `json:"model,omitempty"`
	SerialNumber string     `json:"serial_number,omitempty"`
	InstallDate  *time.Time `json:"install_date,omitempty"`

	// Data quality
	Confidence   ConfidenceLevel        `json:"confidence"`
	LastVerified *time.Time             `json:"last_verified,omitempty"`
	Properties   map[string]interface{} `json:"properties,omitempty"`
}

// System represents a building system (HVAC, electrical, plumbing, etc.)
type System struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Type        string `json:"type"` // hvac, electrical, plumbing, fire, security
	Description string `json:"description,omitempty"`

	// Components
	Equipment []string `json:"equipment_ids"` // equipment in this system

	// System topology
	Connections []Connection `json:"connections"` // how equipment is connected

	// Data quality
	Confidence ConfidenceLevel        `json:"confidence"`
	Properties map[string]interface{} `json:"properties,omitempty"`
}

// Connection represents how equipment is connected in a system
type Connection struct {
	FromID     string                 `json:"from_id"`
	ToID       string                 `json:"to_id"`
	Type       string                 `json:"type"` // power, data, pipe, duct, etc.
	Properties map[string]interface{} `json:"properties,omitempty"`
}

// SpatialReference defines the spatial coordinate system
type SpatialReference struct {
	// GPS coordinates (WGS84)
	GPSOrigin *GPSCoordinate `json:"gps_origin,omitempty"`

	// Local coordinate system
	LocalOrigin Point3D `json:"local_origin"`
	Rotation    float64 `json:"rotation"` // rotation from north in degrees

	// Coordinate system info
	SRID  int    `json:"srid,omitempty"` // Spatial Reference ID
	Units string `json:"units"`          // meters, feet, etc.
}

// GPSCoordinate represents WGS84 coordinates
type GPSCoordinate struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Altitude  float64 `json:"altitude,omitempty"`
}

// Point3D represents a 3D point
type Point3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// BoundingBox represents 3D bounds
type BoundingBox struct {
	Min Point3D `json:"min"`
	Max Point3D `json:"max"`
}

// Size3D represents 3D dimensions
type Size3D struct {
	Width  float64 `json:"width"`  // X dimension
	Depth  float64 `json:"depth"`  // Y dimension
	Height float64 `json:"height"` // Z dimension
}

// Orientation represents 3D rotation
type Orientation struct {
	Roll  float64 `json:"roll"`  // rotation around X axis
	Pitch float64 `json:"pitch"` // rotation around Y axis
	Yaw   float64 `json:"yaw"`   // rotation around Z axis
}

// ValidationIssue represents a data quality issue
type ValidationIssue struct {
	Level   string `json:"level"` // error, warning, info
	Field   string `json:"field"`
	Message string `json:"message"`
	Details string `json:"details,omitempty"`
}

// Methods for BuildingModel

// Validate checks the building model for issues
func (b *BuildingModel) Validate() []ValidationIssue {
	var issues []ValidationIssue

	// Check required fields
	if b.ID == "" {
		issues = append(issues, ValidationIssue{
			Level:   "error",
			Field:   "ID",
			Message: "Building ID is required",
		})
	}

	if b.Name == "" {
		issues = append(issues, ValidationIssue{
			Level:   "warning",
			Field:   "Name",
			Message: "Building name is missing",
		})
	}

	// Check floors
	if len(b.Floors) == 0 {
		issues = append(issues, ValidationIssue{
			Level:   "warning",
			Field:   "Floors",
			Message: "Building has no floors defined",
		})
	}

	// Check for duplicate floor numbers
	floorNumbers := make(map[int]bool)
	for _, floor := range b.Floors {
		if floorNumbers[floor.Number] {
			issues = append(issues, ValidationIssue{
				Level:   "error",
				Field:   "Floors",
				Message: "Duplicate floor number",
				Details: floor.Name,
			})
		}
		floorNumbers[floor.Number] = true
	}

	// Validate equipment references
	for _, floor := range b.Floors {
		for _, equipment := range floor.Equipment {
			if equipment.FloorID != floor.ID && equipment.FloorID != "" {
				issues = append(issues, ValidationIssue{
					Level:   "warning",
					Field:   "Equipment",
					Message: "Equipment floor mismatch",
					Details: equipment.ID,
				})
			}
		}
	}

	return issues
}

// GetAllEquipment returns all equipment across all floors
func (b *BuildingModel) GetAllEquipment() []Equipment {
	var allEquipment []Equipment
	for _, floor := range b.Floors {
		allEquipment = append(allEquipment, floor.Equipment...)
	}
	return allEquipment
}

// GetFloorByNumber returns a floor by its number
func (b *BuildingModel) GetFloorByNumber(number int) *Floor {
	for i := range b.Floors {
		if b.Floors[i].Number == number {
			return &b.Floors[i]
		}
	}
	return nil
}

// GetEquipmentByID returns equipment by its ID
func (b *BuildingModel) GetEquipmentByID(id string) *Equipment {
	for _, floor := range b.Floors {
		for i := range floor.Equipment {
			if floor.Equipment[i].ID == id {
				return &floor.Equipment[i]
			}
		}
	}
	return nil
}

// CalculateCoverage estimates how complete the building data is
func (b *BuildingModel) CalculateCoverage() float64 {
	if len(b.Floors) == 0 {
		return 0
	}

	totalScore := 0.0
	maxScore := 0.0

	// Check floors
	for _, floor := range b.Floors {
		maxScore += 3 // floor has rooms, equipment, spatial data

		if len(floor.Rooms) > 0 {
			totalScore += 1
		}
		if len(floor.Equipment) > 0 {
			totalScore += 1
		}
		if floor.BoundingBox != nil {
			totalScore += 1
		}
	}

	// Check spatial data
	if b.Origin != nil {
		totalScore += 2
	}
	maxScore += 2

	if b.BoundingBox != nil {
		totalScore += 2
	}
	maxScore += 2

	// Check systems
	if len(b.Systems) > 0 {
		totalScore += 1
	}
	maxScore += 1

	if maxScore == 0 {
		return 0
	}

	return (totalScore / maxScore) * 100
}
