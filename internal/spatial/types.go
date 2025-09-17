package spatial

import (
	"fmt"
	"math"
	"time"
)

// Point3D represents a point in 3D space
type Point3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// NewPoint3D creates a new 3D point
func NewPoint3D(x, y, z float64) Point3D {
	return Point3D{X: x, Y: y, Z: z}
}

// DistanceTo calculates the Euclidean distance to another point
func (p Point3D) DistanceTo(other Point3D) float64 {
	dx := p.X - other.X
	dy := p.Y - other.Y
	dz := p.Z - other.Z
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// Add adds another point to this point
func (p Point3D) Add(other Point3D) Point3D {
	return Point3D{
		X: p.X + other.X,
		Y: p.Y + other.Y,
		Z: p.Z + other.Z,
	}
}

// Sub subtracts another point from this point
func (p Point3D) Sub(other Point3D) Point3D {
	return Point3D{
		X: p.X - other.X,
		Y: p.Y - other.Y,
		Z: p.Z - other.Z,
	}
}

// Scale multiplies the point by a scalar
func (p Point3D) Scale(factor float64) Point3D {
	return Point3D{
		X: p.X * factor,
		Y: p.Y * factor,
		Z: p.Z * factor,
	}
}

// String returns a string representation
func (p Point3D) String() string {
	return fmt.Sprintf("(%.3f, %.3f, %.3f)", p.X, p.Y, p.Z)
}

// Point2D represents a point in 2D space
type Point2D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// GridCoordinate represents a position in the grid-based system
type GridCoordinate struct {
	X     int `json:"x"`
	Y     int `json:"y"`
	Floor int `json:"floor"`
}

// BoundingBox represents a 3D bounding box
type BoundingBox struct {
	Min Point3D `json:"min"`
	Max Point3D `json:"max"`
}

// NewBoundingBox creates a bounding box from min and max points
func NewBoundingBox(min, max Point3D) BoundingBox {
	return BoundingBox{Min: min, Max: max}
}

// Contains checks if a point is inside the bounding box
func (b BoundingBox) Contains(p Point3D) bool {
	return p.X >= b.Min.X && p.X <= b.Max.X &&
		p.Y >= b.Min.Y && p.Y <= b.Max.Y &&
		p.Z >= b.Min.Z && p.Z <= b.Max.Z
}

// Volume calculates the volume of the bounding box
func (b BoundingBox) Volume() float64 {
	dx := b.Max.X - b.Min.X
	dy := b.Max.Y - b.Min.Y
	dz := b.Max.Z - b.Min.Z
	return dx * dy * dz
}

// Center returns the center point of the bounding box
func (b BoundingBox) Center() Point3D {
	return Point3D{
		X: (b.Min.X + b.Max.X) / 2,
		Y: (b.Min.Y + b.Max.Y) / 2,
		Z: (b.Min.Z + b.Max.Z) / 2,
	}
}

// GPSCoordinate represents a GPS location
type GPSCoordinate struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Altitude  float64 `json:"altitude"` // meters above sea level
}

// Transform represents a 3D transformation matrix
type Transform struct {
	Origin      GPSCoordinate `json:"origin"`      // GPS origin for building
	Translation Point3D       `json:"translation"`
	Rotation    float64       `json:"rotation"`    // Single rotation angle in degrees
	GridScale   float64       `json:"grid_scale"`  // Meters per grid unit
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

// ConfidenceLevel represents the confidence in spatial data
type ConfidenceLevel int

const (
	CONFIDENCE_ESTIMATED ConfidenceLevel = iota // PDF/IFC without verification
	CONFIDENCE_LOW                              // Automated detection
	CONFIDENCE_MEDIUM                           // Partial verification
	CONFIDENCE_HIGH                             // LiDAR or AR verified
)

// Alias names for backwards compatibility
const (
	ConfidenceEstimated = CONFIDENCE_ESTIMATED
	ConfidenceLow       = CONFIDENCE_LOW
	ConfidenceMedium    = CONFIDENCE_MEDIUM
	ConfidenceHigh      = CONFIDENCE_HIGH
)

// String returns the string representation of confidence level
func (c ConfidenceLevel) String() string {
	switch c {
	case ConfidenceEstimated:
		return "ESTIMATED"
	case ConfidenceLow:
		return "LOW"
	case ConfidenceMedium:
		return "MEDIUM"
	case ConfidenceHigh:
		return "HIGH"
	default:
		return "UNKNOWN"
	}
}

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
	Boundary     SpatialExtent `json:"boundary"`     // Simplified boundary for PostGIS
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
		// Calculate area of region (simplified - assumes rectangular)
		// TODO: Implement proper polygon area calculation
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
