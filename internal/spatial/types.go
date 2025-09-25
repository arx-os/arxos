package spatial

import (
	"math"
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

// Type aliases for public API types - ensures internal and public APIs stay synchronized
type Point3D = models.Point3D
type Point2D = models.Point2D
type BoundingBox = models.BoundingBox
type ConfidenceLevel = models.ConfidenceLevel

// Re-export public constructors for convenience
var (
	NewPoint3D     = models.NewPoint3D
	NewPoint2D     = models.NewPoint2D
	NewBoundingBox = models.NewBoundingBox
)

// Re-export confidence level constants
const (
	ConfidenceUnknown = models.ConfidenceUnknown
	ConfidenceLow     = models.ConfidenceLow
	ConfidenceMedium  = models.ConfidenceMedium
	ConfidenceHigh    = models.ConfidenceHigh
	ConfidencePrecise = models.ConfidencePrecise
)

// Note: Basic Point3D methods (DistanceTo, Add, Sub, Scale, etc.) are defined in pkg/models/spatial.go

// Distance calculates the Euclidean distance between two 3D points
func Distance(p1, p2 Point3D) float64 {
	dx := p2.X - p1.X
	dy := p2.Y - p1.Y
	dz := p2.Z - p1.Z
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// GridCoordinate represents a position in the grid-based system
type GridCoordinate struct {
	X     int `json:"x"`
	Y     int `json:"y"`
	Floor int `json:"floor"`
}

// Note: BoundingBox type and methods are defined in pkg/models/spatial.go

// GPSCoordinate represents a GPS location
type GPSCoordinate struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Altitude  float64 `json:"altitude"` // meters above sea level
}

// Transform represents a 3D transformation matrix
type Transform struct {
	Origin      GPSCoordinate `json:"origin"` // GPS origin for building
	Translation Point3D       `json:"translation"`
	Rotation    float64       `json:"rotation"`     // Single rotation angle in degrees
	GridScale   float64       `json:"grid_scale"`   // Meters per grid unit
	FloorHeight float64       `json:"floor_height"` // Meters between floors
	Scale       float64       `json:"scale"`
}

// Apply applies the transform to a point
func (t Transform) Apply(p Point3D) Point3D {
	// Apply scale
	scaled := p.Scale(t.Scale)

	// Apply rotation using Euler angles (X, Y, Z order)
	rotated := t.applyRotation(scaled)

	// Apply translation
	return rotated.Add(t.Translation)
}

// applyRotation applies rotation around Z axis (for building orientation)
func (t Transform) applyRotation(p Point3D) Point3D {
	// Convert degrees to radians
	theta := t.Rotation * math.Pi / 180

	// Rotation around Z axis (2D rotation in XY plane)
	cosTheta, sinTheta := math.Cos(theta), math.Sin(theta)
	x := p.X*cosTheta - p.Y*sinTheta
	y := p.X*sinTheta + p.Y*cosTheta

	return Point3D{X: x, Y: y, Z: p.Z}
}

// NewRotation3D creates a rotation value (for backward compatibility)
// In the current implementation, we use single angle rotation
func NewRotation3D(x, y, z float64) float64 {
	// For now, use Z rotation only (most common for building orientation)
	return z
}

// Note: ConfidenceLevel type and constants are defined in pkg/models/spatial.go

// Legacy confidence constants for backward compatibility
const (
	CONFIDENCE_ESTIMATED = ConfidenceUnknown // PDF/IFC without verification
	CONFIDENCE_LOW       = ConfidenceLow     // Automated detection
	CONFIDENCE_MEDIUM    = ConfidenceMedium  // Partial verification
	CONFIDENCE_HIGH      = ConfidenceHigh    // LiDAR or AR verified
)

// Alias names for backwards compatibility
const (
	ConfidenceEstimated = CONFIDENCE_ESTIMATED
)

// SpatialMetadata contains spatial information for equipment
type SpatialMetadata struct {
	Position           Point3D         `json:"position"`
	GridPosition       GridCoordinate  `json:"grid_position"`
	BoundingBox        *BoundingBox    `json:"bounding_box,omitempty"`
	PositionConfidence ConfidenceLevel `json:"position_confidence"`
	PositionSource     string          `json:"position_source"`
	PositionUpdated    time.Time       `json:"position_updated"`
	Orientation        [3]float64      `json:"orientation,omitempty"` // Euler angles
	LastUpdated        time.Time       `json:"last_updated"`
	Source             string          `json:"source"`
	DistanceFromQuery  float64         `json:"distance_from_query,omitempty"`
}

// SpatialExtent represents the spatial coverage of a region
type SpatialExtent struct {
	Boundary []Point2D `json:"boundary"` // 2D polygon boundary
	MinX     float64   `json:"min_x"`
	MinY     float64   `json:"min_y"`
	MaxX     float64   `json:"max_x"`
	MaxY     float64   `json:"max_y"`
	MinZ     float64   `json:"min_z"`
	MaxZ     float64   `json:"max_z"`
}

// ScannedRegion represents an area that has been scanned
type ScannedRegion struct {
	ID           string        `json:"id"`
	BuildingID   string        `json:"building_id"`
	Floor        int           `json:"floor"`
	Region       SpatialExtent `json:"region"`
	Boundary     SpatialExtent `json:"boundary"` // Simplified boundary for PostGIS
	ScanDate     time.Time     `json:"scan_date"`
	ScanType     string        `json:"scan_type"`     // "lidar", "photogrammetry", "ar_verify"
	PointDensity float64       `json:"point_density"` // points per square meter
	Confidence   float64       `json:"confidence"`
	DataURL      string        `json:"data_url,omitempty"` // reference to raw data
}

// CoverageMap tracks scanned areas of a building
type CoverageMap struct {
	BuildingID     string          `json:"building_id"`
	TotalArea      float64         `json:"total_area"` // square meters
	ScannedRegions []ScannedRegion `json:"scanned_regions"`
	LastUpdated    time.Time       `json:"last_updated"`
}

// GetCoveragePercentage calculates the percentage of area scanned
func (c *CoverageMap) GetCoveragePercentage() float64 {
	if c.TotalArea == 0 {
		return 0
	}

	scannedArea := 0.0
	for _, region := range c.ScannedRegions {
		// Calculate area of region using proper polygon area calculation
		scannedArea += calculatePolygonArea(region.Region.Boundary)
	}

	percentage := (scannedArea / c.TotalArea) * 100
	if percentage > 100 {
		return 100
	}
	return percentage
}

// MovementResult represents the result of analyzing equipment movement
type MovementResult struct {
	Distance          float64   `json:"distance"`
	GridUnitsMoved    GridDelta `json:"grid_units_moved"`
	RoomChanged       bool      `json:"room_changed"`
	FloorChanged      bool      `json:"floor_changed"`
	RequiresBIMUpdate bool      `json:"requires_bim_update"`
}

// GridDelta represents movement in grid units
type GridDelta struct {
	DX int `json:"dx"`
	DY int `json:"dy"`
	DZ int `json:"dz"` // floor change
}

// Magnitude returns the magnitude of the grid delta
func (g GridDelta) Magnitude() float64 {
	return math.Sqrt(float64(g.DX*g.DX + g.DY*g.DY + g.DZ*g.DZ))
}

// ARCoordinate represents coordinates in AR space
type ARCoordinate struct {
	Position Point3D `json:"position"`
	AnchorID string  `json:"anchor_id"`
}

// SpatialAnchor represents an AR spatial anchor
type SpatialAnchor struct {
	ID            string    `json:"id"`
	BuildingID    string    `json:"building_id"`
	Position      Point3D   `json:"position"`
	WorldPosition Point3D   `json:"world_position"`
	Type          string    `json:"type"`
	Created       time.Time `json:"created"`
	LastSeen      time.Time `json:"last_seen"`
	Confidence    float64   `json:"confidence"`
}

// calculatePolygonArea calculates the area of a 2D polygon using the shoelace formula
func calculatePolygonArea(points []Point2D) float64 {
	if len(points) < 3 {
		return 0
	}

	area := 0.0
	n := len(points)
	for i := 0; i < n; i++ {
		j := (i + 1) % n
		area += points[i].X * points[j].Y
		area -= points[j].X * points[i].Y
	}
	return math.Abs(area) / 2.0
}
