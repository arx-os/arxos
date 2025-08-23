package types

import (
	"math"
	"testing"
)

func TestSmartPoint3D_NewSmartPoint3D(t *testing.T) {
	point := NewSmartPoint3D(1000000, 2000000, 3000000, Nanometer)

	if point.X != 1000000 || point.Y != 2000000 || point.Z != 3000000 {
		t.Errorf("Expected (1000000, 2000000, 3000000), got (%d, %d, %d)",
			point.X, point.Y, point.Z)
	}

	if point.unit != Nanometer {
		t.Errorf("Expected unit Nanometer, got %v", point.unit)
	}
}

func TestSmartPoint3D_ToNanometers(t *testing.T) {
	point := NewSmartPoint3D(1000000, 2000000, 3000000, Nanometer)
	x, y, z := point.ToNanometers()

	if x != 1000000 || y != 2000000 || z != 3000000 {
		t.Errorf("Expected (1000000, 2000000, 3000000), got (%d, %d, %d)", x, y, z)
	}
}

func TestSmartPoint3D_ToMicrometers(t *testing.T) {
	// Create a point with micrometer coordinates (1, 2, 3 μm)
	// This will be stored internally as nanometers (1000, 2000, 3000 nm)
	point := NewSmartPoint3D(1, 2, 3, Micrometer)
	x, y, z := point.ToMicrometers()

	expectedX, expectedY, expectedZ := 1.0, 2.0, 3.0
	if x != expectedX || y != expectedY || z != expectedZ {
		t.Errorf("Expected (%.1f, %.1f, %.1f), got (%.1f, %.1f, %.1f)",
			expectedX, expectedY, expectedZ, x, y, z)
	}
}

func TestSmartPoint3D_ToMillimeters(t *testing.T) {
	point := NewSmartPoint3D(1000000, 2000000, 3000000, Nanometer)
	x, y, z := point.ToMillimeters()

	expectedX, expectedY, expectedZ := 1.0, 2.0, 3.0
	if x != expectedX || y != expectedY || z != expectedZ {
		t.Errorf("Expected (%.1f, %.1f, %.1f), got (%.1f, %.1f, %.1f)",
			expectedX, expectedY, expectedZ, x, y, z)
	}
}

func TestSmartPoint3D_ToMeters(t *testing.T) {
	point := NewSmartPoint3D(1000000000, 2000000000, 3000000000, Nanometer)
	x, y, z := point.ToMeters()

	expectedX, expectedY, expectedZ := 1.0, 2.0, 3.0
	if x != expectedX || y != expectedY || z != expectedZ {
		t.Errorf("Expected (%.1f, %.1f, %.1f), got (%.1f, %.1f, %.1f)",
			expectedX, expectedY, expectedZ, x, y, z)
	}
}

func TestSmartPoint3D_DistanceTo(t *testing.T) {
	point1 := NewSmartPoint3D(0, 0, 0, Nanometer)
	point2 := NewSmartPoint3D(3000000, 4000000, 0, Nanometer) // 3mm, 4mm

	distance := point1.DistanceTo(point2)
	expected := 5.0 // 5mm (3-4-5 triangle)

	if math.Abs(distance-expected) > 0.001 {
		t.Errorf("Expected distance %.3f, got %.3f", expected, distance)
	}
}

func TestSmartPoint3D_DistanceTo_SamePoint(t *testing.T) {
	point := NewSmartPoint3D(1000000, 2000000, 3000000, Nanometer)
	distance := point.DistanceTo(point)

	if distance != 0.0 {
		t.Errorf("Expected distance 0.0, got %.3f", distance)
	}
}

func TestSmartPoint3D_String(t *testing.T) {
	point := NewSmartPoint3D(1000000, 2000000, 3000000, Nanometer)
	str := point.String()

	expected := "(1.00, 2.00, 3.00) mm"
	if str != expected {
		t.Errorf("Expected string '%s', got '%s'", expected, str)
	}
}

func TestUnit_String(t *testing.T) {
	testCases := []struct {
		unit     Unit
		expected string
	}{
		{Nanometer, "nm"},
		{Micrometer, "μm"},
		{Millimeter, "mm"},
		{Centimeter, "cm"},
		{Meter, "m"},
		{Inch, "in"},
		{Foot, "ft"},
	}

	for _, tc := range testCases {
		if tc.unit.String() != tc.expected {
			t.Errorf("Unit %v: expected '%s', got '%s'", tc.unit, tc.expected, tc.unit.String())
		}
	}
}
