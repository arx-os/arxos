package building

import (
	"time"
)

// IFCBuilding represents a parsed IFC building model
// This is the domain representation of IFC data
type IFCBuilding struct {
	ID              string              `json:"id"`
	Name            string              `json:"name"`
	Version         string              `json:"version"`    // IFC version (4.0, 4.3, etc.)
	Discipline      string              `json:"discipline"` // architectural, hvac, electrical, etc.
	Entities        []IFCEntity         `json:"entities"`
	Properties      []IFCProperty       `json:"properties"`
	Materials       []IFCMaterial       `json:"materials"`
	Classifications []IFCClassification `json:"classifications"`
	CreatedAt       time.Time           `json:"created_at"`
	UpdatedAt       time.Time           `json:"updated_at"`
}

// IFCEntity represents an IFC entity (building element)
type IFCEntity struct {
	ID          string         `json:"id"`
	Type        string         `json:"type"` // IfcWall, IfcDoor, IfcWindow, etc.
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Properties  map[string]any `json:"properties"`
	Geometry    Geometry       `json:"geometry"`
	Location    Location       `json:"location"`
	CreatedAt   time.Time      `json:"created_at"`
}

// IFCProperty represents an IFC property
type IFCProperty struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Value       string    `json:"value"`
	Type        string    `json:"type"`
	Unit        string    `json:"unit"`
	Description string    `json:"description"`
	CreatedAt   time.Time `json:"created_at"`
}

// IFCMaterial represents an IFC material
type IFCMaterial struct {
	ID         string         `json:"id"`
	Name       string         `json:"name"`
	Type       string         `json:"type"`
	Properties map[string]any `json:"properties"`
	CreatedAt  time.Time      `json:"created_at"`
}

// IFCClassification represents an IFC classification
type IFCClassification struct {
	ID          string    `json:"id"`
	System      string    `json:"system"` // OmniClass, Uniclass, etc.
	Code        string    `json:"code"`
	Description string    `json:"description"`
	CreatedAt   time.Time `json:"created_at"`
}

// Geometry represents 3D geometry data
type Geometry struct {
	Type        string    `json:"type"` // point, line, polygon, solid
	Coordinates []float64 `json:"coordinates"`
	Bounds      Bounds    `json:"bounds"`
	Volume      float64   `json:"volume"`
	Area        float64   `json:"area"`
}

// Location represents spatial location
type Location struct {
	X          float64 `json:"x"`
	Y          float64 `json:"y"`
	Z          float64 `json:"z"`
	Confidence int     `json:"confidence"` // Confidence level (1-100)
	Source     string  `json:"source"`     // Source of coordinates
	Accuracy   float64 `json:"accuracy"`   // Accuracy in millimeters
}

// Bounds represents bounding box
type Bounds struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MinZ float64 `json:"min_z"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
	MaxZ float64 `json:"max_z"`
}

// IFCImportRequest represents a request to import IFC data
type IFCImportRequest struct {
	RepositoryID string        `json:"repository_id" validate:"required"`
	FileName     string        `json:"file_name" validate:"required"`
	Data         []byte        `json:"data" validate:"required"`
	Options      ImportOptions `json:"options"`
}

// ImportOptions represents options for IFC import
type ImportOptions struct {
	Validate               bool     `json:"validate"` // Validate against buildingSMART standards
	Enhance                bool     `json:"enhance"`  // Enhance with spatial data
	Repair                 bool     `json:"repair"`   // Repair invalid data
	MergeDuplicates        bool     `json:"merge_duplicates"`
	IncludeEntities        []string `json:"include_entities"`
	ExcludeEntities        []string `json:"exclude_entities"`
	ExtractProperties      bool     `json:"extract_properties"`
	ExtractMaterials       bool     `json:"extract_materials"`
	ExtractClassifications bool     `json:"extract_classifications"`
}

// IFCImportResult represents the result of an IFC import
type IFCImportResult struct {
	Success         bool      `json:"success"`
	RepositoryID    string    `json:"repository_id"`
	IFCFileID       string    `json:"ifc_file_id"`
	Entities        int       `json:"entities"`
	Properties      int       `json:"properties"`
	Materials       int       `json:"materials"`
	Classifications int       `json:"classifications"`
	Warnings        []string  `json:"warnings"`
	Errors          []string  `json:"errors"`
	CreatedAt       time.Time `json:"created_at"`

	// NEW: Entity extraction tracking
	BuildingsCreated     int `json:"buildings_created"`
	FloorsCreated        int `json:"floors_created"`
	RoomsCreated         int `json:"rooms_created"`
	EquipmentCreated     int `json:"equipment_created"`
	RelationshipsCreated int `json:"relationships_created"`
}

// IFCValidationResult represents the result of IFC validation
type IFCValidationResult struct {
	Valid      bool             `json:"valid"`
	Version    string           `json:"version"`
	Compliance ComplianceResult `json:"compliance"`
	Schema     SchemaResult     `json:"schema"`
	Spatial    SpatialResult    `json:"spatial"`
	Warnings   []string         `json:"warnings"`
	Errors     []string         `json:"errors"`
	CreatedAt  time.Time        `json:"created_at"`
}

// ComplianceResult represents buildingSMART compliance check
type ComplianceResult struct {
	Passed    bool         `json:"passed"`
	Score     int          `json:"score"` // 0-100
	Tests     []TestResult `json:"tests"`
	CreatedAt time.Time    `json:"created_at"`
}

// SchemaResult represents IFC schema validation
type SchemaResult struct {
	Passed    bool      `json:"passed"`
	Version   string    `json:"version"`
	Errors    []string  `json:"errors"`
	CreatedAt time.Time `json:"created_at"`
}

// SpatialResult represents spatial validation
type SpatialResult struct {
	Passed    bool      `json:"passed"`
	Accuracy  float64   `json:"accuracy"`
	Coverage  float64   `json:"coverage"`
	Errors    []string  `json:"errors"`
	CreatedAt time.Time `json:"created_at"`
}

// TestResult represents a single compliance test result
type TestResult struct {
	Name      string    `json:"name"`
	Passed    bool      `json:"passed"`
	Message   string    `json:"message"`
	CreatedAt time.Time `json:"created_at"`
}
