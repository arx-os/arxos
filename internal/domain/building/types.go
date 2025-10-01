package building

// Data source constants
const (
	DataSourceIFC    = "IFC"
	DataSourcePDF    = "PDF"
	DataSourceJSON   = "JSON"
	DataSourceCSV    = "CSV"
	DataSourceManual = "Manual"
)

// ConfidenceLevel represents confidence in data accuracy
type ConfidenceLevel int

const (
	ConfidenceEstimated ConfidenceLevel = 0 // Derived from PDF/IFC without verification
	ConfidenceLow       ConfidenceLevel = 1 // Automated detection
	ConfidenceMedium    ConfidenceLevel = 2 // Partial verification
	ConfidenceHigh      ConfidenceLevel = 3 // LiDAR or AR verified
)

// Point3D represents a 3D point
type Point3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// SpatialReference represents spatial reference information
type SpatialReference struct {
	CoordinateSystem string   `json:"coordinate_system,omitempty"`
	SRID             int      `json:"srid,omitempty"` // Spatial Reference ID
	Rotation         float64  `json:"rotation,omitempty"`
	LocalOrigin      *Point3D `json:"local_origin,omitempty"`
	Units            string   `json:"units,omitempty"`
}

// BoundingBox represents a 3D bounding box
type BoundingBox struct {
	Min *Point3D `json:"min"`
	Max *Point3D `json:"max"`
	// Alternative representation for compatibility
	MinX float64 `json:"min_x,omitempty"`
	MinY float64 `json:"min_y,omitempty"`
	MinZ float64 `json:"min_z,omitempty"`
	MaxX float64 `json:"max_x,omitempty"`
	MaxY float64 `json:"max_y,omitempty"`
	MaxZ float64 `json:"max_z,omitempty"`
}

// System represents a building system (HVAC, electrical, plumbing, etc.)
type System struct {
	ID          string   `json:"id"`
	Type        string   `json:"type"` // HVAC, Electrical, Plumbing, etc.
	Name        string   `json:"name"`
	Description string   `json:"description,omitempty"`
	Equipment   []string `json:"equipment"` // Equipment IDs in this system
}

// Position3D represents a 3D position
type Position3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}
