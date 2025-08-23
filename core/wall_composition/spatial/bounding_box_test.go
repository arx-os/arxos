package spatial

import (
	"testing"

	"github.com/arxos/arxos/core/wall_composition/types"
)

func TestNewBoundingBox(t *testing.T) {
	bb := NewBoundingBox(1000000, 2000000, 3000000, 4000000)

	if bb.MinX != 1000000 {
		t.Errorf("Expected MinX 1000000, got %d", bb.MinX)
	}

	if bb.MinY != 2000000 {
		t.Errorf("Expected MinY 2000000, got %d", bb.MinY)
	}

	if bb.MaxX != 3000000 {
		t.Errorf("Expected MaxX 3000000, got %d", bb.MaxX)
	}

	if bb.MaxY != 4000000 {
		t.Errorf("Expected MaxY 4000000, got %d", bb.MaxY)
	}
}

func TestBoundingBox_Contains(t *testing.T) {
	bb := NewBoundingBox(1000000, 2000000, 3000000, 4000000)

	// Test points inside the box
	testCases := []struct {
		x, y     int64
		expected bool
	}{
		{1500000, 2500000, true},  // Inside
		{1000000, 2000000, true},  // On edge (min)
		{3000000, 4000000, true},  // On edge (max)
		{2000000, 3000000, true},  // Inside
		{500000, 2500000, false},  // Outside (left)
		{3500000, 2500000, false}, // Outside (right)
		{2000000, 1500000, false}, // Outside (below)
		{2000000, 4500000, false}, // Outside (above)
	}

	for _, tc := range testCases {
		result := bb.Contains(tc.x, tc.y)
		if result != tc.expected {
			t.Errorf("Contains(%d, %d): expected %v, got %v",
				tc.x, tc.y, tc.expected, result)
		}
	}
}

func TestBoundingBox_Intersects(t *testing.T) {
	bb1 := NewBoundingBox(1000000, 2000000, 3000000, 4000000)

	testCases := []struct {
		bb2      BoundingBox
		expected bool
		desc     string
	}{
		{
			NewBoundingBox(2000000, 3000000, 4000000, 5000000), // Overlapping
			true, "overlapping",
		},
		{
			NewBoundingBox(500000, 1000000, 1500000, 2500000), // Overlapping
			true, "overlapping",
		},
		{
			NewBoundingBox(3500000, 4500000, 5000000, 5500000), // No overlap
			false, "no overlap",
		},
		{
			NewBoundingBox(500000, 4500000, 1500000, 5500000), // No overlap
			false, "no overlap",
		},
		{
			NewBoundingBox(1000000, 2000000, 3000000, 4000000), // Same box
			true, "same box",
		},
		{
			NewBoundingBox(2000000, 3000000, 2500000, 3500000), // Contained
			true, "contained",
		},
	}

	for _, tc := range testCases {
		result := bb1.Intersects(tc.bb2)
		if result != tc.expected {
			t.Errorf("Intersects with %s: expected %v, got %v",
				tc.desc, tc.expected, result)
		}
	}
}

func TestBoundingBox_Expand(t *testing.T) {
	bb := NewBoundingBox(1000000, 2000000, 3000000, 4000000)

	// Expand to include a point outside
	bb.Expand(500000, 1500000) // Left of current bounds

	if bb.MinX != 500000 {
		t.Errorf("Expected MinX to expand to 500000, got %d", bb.MinX)
	}

	if bb.MinY != 1500000 {
		t.Errorf("Expected MinY to expand to 1500000, got %d", bb.MinY)
	}

	// Expand to include a point above current bounds
	bb.Expand(2000000, 5000000)

	if bb.MaxY != 5000000 {
		t.Errorf("Expected MaxY to expand to 5000000, got %d", bb.MaxY)
	}

	// Expand to include a point to the right
	bb.Expand(4000000, 3000000)

	if bb.MaxX != 4000000 {
		t.Errorf("Expected MaxX to expand to 4000000, got %d", bb.MaxX)
	}
}

func TestBoundingBox_Width(t *testing.T) {
	bb := NewBoundingBox(1000000, 2000000, 3000000, 4000000)
	expected := int64(2000000) // 3000000 - 1000000

	if bb.Width() != expected {
		t.Errorf("Expected width %d, got %d", expected, bb.Width())
	}
}

func TestBoundingBox_Height(t *testing.T) {
	bb := NewBoundingBox(1000000, 2000000, 3000000, 4000000)
	expected := int64(2000000) // 4000000 - 2000000

	if bb.Height() != expected {
		t.Errorf("Expected height %d, got %d", expected, bb.Height())
	}
}

func TestBoundingBox_Area(t *testing.T) {
	bb := NewBoundingBox(1000000, 2000000, 3000000, 4000000)
	expected := int64(4000000000000) // 2000000 * 2000000

	if bb.Area() != expected {
		t.Errorf("Expected area %d, got %d", expected, bb.Area())
	}
}

func TestBoundingBox_Center(t *testing.T) {
	bb := NewBoundingBox(1000000, 2000000, 3000000, 4000000)
	center := bb.Center()

	expectedX := int64(2000000) // (1000000 + 3000000) / 2
	expectedY := int64(3000000) // (2000000 + 4000000) / 2

	if center.X != expectedX {
		t.Errorf("Expected center X %d, got %d", expectedX, center.X)
	}

	if center.Y != expectedY {
		t.Errorf("Expected center Y %d, got %d", expectedY, center.Y)
	}

	if center.GetUnit() != types.Nanometer {
		t.Errorf("Expected unit Nanometer, got %v", center.GetUnit())
	}
}

func TestBoundingBox_ToMillimeters(t *testing.T) {
	bb := NewBoundingBox(1000000, 2000000, 3000000, 4000000)
	minX, minY, maxX, maxY := bb.ToMillimeters()

	expectedMinX := 1.0 // 1000000 / 1e6
	expectedMinY := 2.0 // 2000000 / 1e6
	expectedMaxX := 3.0 // 3000000 / 1e6
	expectedMaxY := 4.0 // 4000000 / 1e6

	if minX != expectedMinX {
		t.Errorf("Expected MinX %.1f, got %.1f", expectedMinX, minX)
	}

	if minY != expectedMinY {
		t.Errorf("Expected MinY %.1f, got %.1f", expectedMinY, minY)
	}

	if maxX != expectedMaxX {
		t.Errorf("Expected MaxX %.1f, got %.1f", expectedMaxX, maxX)
	}

	if maxY != expectedMaxY {
		t.Errorf("Expected MaxY %.1f, got %.1f", expectedMaxY, maxY)
	}
}
