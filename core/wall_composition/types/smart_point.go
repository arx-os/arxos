package types

import (
	"fmt"
	"math"
)

// Unit represents measurement units
type Unit int

const (
	Nanometer Unit = iota
	Micrometer
	Millimeter
	Centimeter
	Meter
	Inch
	Foot
)

// String representation of units
func (u Unit) String() string {
	switch u {
	case Nanometer:
		return "nm"
	case Micrometer:
		return "μm"
	case Millimeter:
		return "mm"
	case Centimeter:
		return "cm"
	case Meter:
		return "m"
	case Inch:
		return "in"
	case Foot:
		return "ft"
	default:
		return "unknown"
	}
}

// Conversion factors (compile-time constants)
var conversionFactors = map[Unit]float64{
	Nanometer:  1.0,
	Micrometer: 1e3,
	Millimeter: 1e6,
	Centimeter: 1e7,
	Meter:      1e9,
	Inch:       2.54e7,
	Foot:       3.048e8,
}

// SmartPoint3D represents a 3D point with automatic unit conversion
type SmartPoint3D struct {
	X, Y, Z int64 // Stored in nanometers for precision
	unit    Unit  // What unit this represents
}

// NewSmartPoint3D creates a new SmartPoint3D
// Input coordinates are interpreted in the specified unit and converted to nanometers for storage
func NewSmartPoint3D(x, y, z int64, unit Unit) SmartPoint3D {
	// Convert input coordinates to nanometers based on the specified unit
	var xNm, yNm, zNm int64
	
	switch unit {
	case Nanometer:
		xNm, yNm, zNm = x, y, z
	case Micrometer:
		xNm, yNm, zNm = x*1000, y*1000, z*1000
	case Millimeter:
		xNm, yNm, zNm = x*1000000, y*1000000, z*1000000
	case Centimeter:
		xNm, yNm, zNm = x*10000000, y*10000000, z*10000000
	case Meter:
		xNm, yNm, zNm = x*1000000000, y*1000000000, z*1000000000
	case Inch:
		xNm, yNm, zNm = x*25400000, y*25400000, z*25400000
	case Foot:
		xNm, yNm, zNm = x*304800000, y*304800000, z*304800000
	default:
		xNm, yNm, zNm = x, y, z
	}
	
	return SmartPoint3D{
		X:    xNm,
		Y:    yNm,
		Z:    zNm,
		unit: unit,
	}
}

// ToNanometers converts to nanometers (no conversion needed)
func (p SmartPoint3D) ToNanometers() (x, y, z int64) {
	return p.X, p.Y, p.Z
}

// ToMicrometers converts to micrometers
func (p SmartPoint3D) ToMicrometers() (x, y, z float64) {
	// Convert from nanometers to micrometers
	return float64(p.X) / 1e3, float64(p.Y) / 1e3, float64(p.Z) / 1e3
}

// ToMillimeters converts to millimeters
func (p SmartPoint3D) ToMillimeters() (x, y, z float64) {
	// Convert from nanometers to millimeters
	return float64(p.X) / 1e6, float64(p.Y) / 1e6, float64(p.Z) / 1e6
}

// ToMeters converts to meters
func (p SmartPoint3D) ToMeters() (x, y, z float64) {
	// Convert from nanometers to meters
	return float64(p.X) / 1e9, float64(p.Y) / 1e9, float64(p.Z) / 1e9
}

// DistanceTo calculates distance to another point in millimeters
func (p SmartPoint3D) DistanceTo(other SmartPoint3D) float64 {
	dx := float64(p.X - other.X)
	dy := float64(p.Y - other.Y)
	dz := float64(p.Z - other.Z)
	return math.Sqrt(dx*dx+dy*dy+dz*dz) / 1e6
}

// String returns string representation
func (p SmartPoint3D) String() string {
	x, y, z := p.ToMillimeters()
	return fmt.Sprintf("(%.2f, %.2f, %.2f) mm", x, y, z)
}

// GetUnit returns the unit of the point
func (p SmartPoint3D) GetUnit() Unit {
	return p.unit
}

// Equals checks if two points are equal
func (p SmartPoint3D) Equals(other SmartPoint3D) bool {
	return p.X == other.X && p.Y == other.Y && p.Z == other.Z && p.unit == other.unit
}
