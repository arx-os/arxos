package models

import (
	"fmt"
	"math"
)

// Point3D represents a point in 3D space with millimeter precision.
//
// This is the canonical spatial coordinate type for ArxOS. All coordinates
// are stored as float64 values representing millimeters from the building origin.
// This provides sub-millimeter precision for building-scale measurements.
//
// For 2D operations (floor plans, maps), use the To2D() method to project
// the point onto the XY plane.
type Point3D struct {
	X float64 `json:"x"` // X coordinate in millimeters
	Y float64 `json:"y"` // Y coordinate in millimeters
	Z float64 `json:"z"` // Z coordinate in millimeters
}

// NewPoint3D creates a new 3D point
func NewPoint3D(x, y, z float64) Point3D {
	return Point3D{X: x, Y: y, Z: z}
}

// NewPoint2D creates a 3D point with Z=0 (floor level)
func NewPoint2D(x, y float64) Point3D {
	return Point3D{X: x, Y: y, Z: 0}
}

// To2D projects the 3D point onto the XY plane (Z=0)
func (p Point3D) To2D() Point2D {
	return Point2D{X: p.X, Y: p.Y}
}

// DistanceTo calculates the Euclidean distance to another point
func (p Point3D) DistanceTo(other Point3D) float64 {
	dx := p.X - other.X
	dy := p.Y - other.Y
	dz := p.Z - other.Z
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// Distance2D calculates the 2D distance (ignoring Z coordinate)
func (p Point3D) Distance2D(other Point3D) float64 {
	dx := p.X - other.X
	dy := p.Y - other.Y
	return math.Sqrt(dx*dx + dy*dy)
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

// IsValid checks if the point has valid coordinates
func (p Point3D) IsValid() bool {
	return !math.IsNaN(p.X) && !math.IsNaN(p.Y) && !math.IsNaN(p.Z) &&
		!math.IsInf(p.X, 0) && !math.IsInf(p.Y, 0) && !math.IsInf(p.Z, 0)
}

// String returns a string representation of the point
func (p Point3D) String() string {
	return fmt.Sprintf("(%.3f, %.3f, %.3f)", p.X, p.Y, p.Z)
}

// Point2D represents a 2D point for floor plan operations.
//
// This is a lightweight type for 2D-only operations like floor plan
// rendering and basic geometric calculations. For spatial database
// operations, prefer Point3D with Z=0.
type Point2D struct {
	X float64 `json:"x"` // X coordinate in millimeters
	Y float64 `json:"y"` // Y coordinate in millimeters
}

// To3D converts the 2D point to 3D with specified Z coordinate
func (p Point2D) To3D(z float64) Point3D {
	return Point3D{X: p.X, Y: p.Y, Z: z}
}

// DistanceTo calculates the 2D Euclidean distance to another point
func (p Point2D) DistanceTo(other Point2D) float64 {
	dx := p.X - other.X
	dy := p.Y - other.Y
	return math.Sqrt(dx*dx + dy*dy)
}

// BoundingBox represents a 3D rectangular region
type BoundingBox struct {
	Min Point3D `json:"min"` // Minimum corner (lower-left-back)
	Max Point3D `json:"max"` // Maximum corner (upper-right-front)
}

// NewBoundingBox creates a bounding box from two points
func NewBoundingBox(min, max Point3D) BoundingBox {
	return BoundingBox{
		Min: Point3D{
			X: math.Min(min.X, max.X),
			Y: math.Min(min.Y, max.Y),
			Z: math.Min(min.Z, max.Z),
		},
		Max: Point3D{
			X: math.Max(min.X, max.X),
			Y: math.Max(min.Y, max.Y),
			Z: math.Max(min.Z, max.Z),
		},
	}
}

// Contains checks if a point is within the bounding box
func (b BoundingBox) Contains(p Point3D) bool {
	return p.X >= b.Min.X && p.X <= b.Max.X &&
		p.Y >= b.Min.Y && p.Y <= b.Max.Y &&
		p.Z >= b.Min.Z && p.Z <= b.Max.Z
}

// Contains2D checks if a point is within the XY projection of the bounding box
func (b BoundingBox) Contains2D(p Point3D) bool {
	return p.X >= b.Min.X && p.X <= b.Max.X &&
		p.Y >= b.Min.Y && p.Y <= b.Max.Y
}

// Center returns the center point of the bounding box
func (b BoundingBox) Center() Point3D {
	return Point3D{
		X: (b.Min.X + b.Max.X) / 2,
		Y: (b.Min.Y + b.Max.Y) / 2,
		Z: (b.Min.Z + b.Max.Z) / 2,
	}
}

// Width returns the width (X dimension) of the bounding box
func (b BoundingBox) Width() float64 {
	return b.Max.X - b.Min.X
}

// Height returns the height (Y dimension) of the bounding box
func (b BoundingBox) Height() float64 {
	return b.Max.Y - b.Min.Y
}

// Depth returns the depth (Z dimension) of the bounding box
func (b BoundingBox) Depth() float64 {
	return b.Max.Z - b.Min.Z
}

// Volume returns the volume of the bounding box
func (b BoundingBox) Volume() float64 {
	return b.Width() * b.Height() * b.Depth()
}

// Point represents a 2D coordinate (for backward compatibility)
//
// Deprecated: Use Point3D for new code. This type is maintained
// for compatibility with existing code.
type Point = Point2D

// Bounds represents a 2D rectangular area (for backward compatibility)
//
// Deprecated: Use BoundingBox for new code. This type is maintained
// for compatibility with existing floor plan code.
type Bounds struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
}

// ToBoundingBox converts Bounds to BoundingBox with Z=0
func (b Bounds) ToBoundingBox(z float64) BoundingBox {
	return BoundingBox{
		Min: Point3D{X: b.MinX, Y: b.MinY, Z: z},
		Max: Point3D{X: b.MaxX, Y: b.MaxY, Z: z},
	}
}

// Contains checks if a 2D point is within bounds
func (b Bounds) Contains(p Point2D) bool {
	return p.X >= b.MinX && p.X <= b.MaxX &&
		p.Y >= b.MinY && p.Y <= b.MaxY
}

// Width returns the width of the bounds
func (b Bounds) Width() float64 {
	return b.MaxX - b.MinX
}

// Height returns the height of the bounds
func (b Bounds) Height() float64 {
	return b.MaxY - b.MinY
}

// ConfidenceLevel represents the confidence in spatial data accuracy
type ConfidenceLevel int

const (
	// ConfidenceUnknown means the position accuracy is unknown
	ConfidenceUnknown ConfidenceLevel = iota

	// ConfidenceLow means position may be off by meters (rough estimate)
	ConfidenceLow

	// ConfidenceMedium means position accurate to ~1 meter (typical import)
	ConfidenceMedium

	// ConfidenceHigh means position accurate to centimeters (surveyed)
	ConfidenceHigh

	// ConfidencePrecise means position accurate to millimeters (laser measured)
	ConfidencePrecise
)

// String returns the string representation of confidence level
func (c ConfidenceLevel) String() string {
	switch c {
	case ConfidenceUnknown:
		return "UNKNOWN"
	case ConfidenceLow:
		return "LOW"
	case ConfidenceMedium:
		return "MEDIUM"
	case ConfidenceHigh:
		return "HIGH"
	case ConfidencePrecise:
		return "PRECISE"
	default:
		return "UNKNOWN"
	}
}

// AccuracyRange returns the typical accuracy range in millimeters
func (c ConfidenceLevel) AccuracyRange() float64 {
	switch c {
	case ConfidenceUnknown:
		return 10000.0 // ±10m
	case ConfidenceLow:
		return 5000.0 // ±5m
	case ConfidenceMedium:
		return 1000.0 // ±1m
	case ConfidenceHigh:
		return 100.0 // ±10cm
	case ConfidencePrecise:
		return 10.0 // ±1cm
	default:
		return 10000.0
	}
}
