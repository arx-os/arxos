package types

import (
	"testing"
	"time"
)

func TestNewWallStructure(t *testing.T) {
	wall := NewWallStructure()

	if wall.ID != 0 {
		t.Errorf("Expected ID 0, got %d", wall.ID)
	}

	if len(wall.Segments) != 0 {
		t.Errorf("Expected 0 segments, got %d", len(wall.Segments))
	}

	if wall.Confidence != 0.0 {
		t.Errorf("Expected confidence 0.0, got %.2f", wall.Confidence)
	}

	if wall.Validation != ValidationPending {
		t.Errorf("Expected validation state ValidationPending, got %v", wall.Validation)
	}

	if len(wall.ArxObjects) != 0 {
		t.Errorf("Expected 0 ArxObjects, got %d", len(wall.ArxObjects))
	}

	// Check that timestamps are set
	if wall.CreatedAt.IsZero() {
		t.Error("Expected CreatedAt to be set")
	}

	if wall.UpdatedAt.IsZero() {
		t.Error("Expected UpdatedAt to be set")
	}
}

func TestWallStructure_AddSegment(t *testing.T) {
	wall := NewWallStructure()

	// Create a test segment
	segment := WallSegment{
		ID:          1,
		StartPoint:  NewSmartPoint3D(0, 0, 0, Nanometer),
		EndPoint:    NewSmartPoint3D(1000000, 0, 0, Nanometer), // 1mm
		Length:      1.0,                                       // 1mm
		Height:      2.7,                                       // 2.7mm
		Confidence:  0.8,
		Orientation: 0.0,
		CreatedAt:   time.Now(),
	}

	originalUpdatedAt := wall.UpdatedAt
	time.Sleep(1 * time.Millisecond) // Ensure time difference

	wall.AddSegment(segment)

	if len(wall.Segments) != 1 {
		t.Errorf("Expected 1 segment, got %d", len(wall.Segments))
	}

	if wall.Segments[0].ID != 1 {
		t.Errorf("Expected segment ID 1, got %d", wall.Segments[0].ID)
	}

	// Check that properties were recalculated
	if wall.Length != 1.0 {
		t.Errorf("Expected length 1.0, got %.2f", wall.Length)
	}

	if wall.Height != 2.7 {
		t.Errorf("Expected height 2.7, got %.2f", wall.Height)
	}

	if wall.Confidence != 0.8 {
		t.Errorf("Expected confidence 0.8, got %.2f", wall.Confidence)
	}

	// Check that UpdatedAt was updated
	if !wall.UpdatedAt.After(originalUpdatedAt) {
		t.Error("Expected UpdatedAt to be updated")
	}
}

func TestWallStructure_CalculateTotalLength(t *testing.T) {
	wall := NewWallStructure()

	// Add multiple segments
	segments := []WallSegment{
		{
			ID:     1,
			Length: 2.0, // 2mm
		},
		{
			ID:     2,
			Length: 3.0, // 3mm
		},
		{
			ID:     3,
			Length: 1.5, // 1.5mm
		},
	}

	for _, segment := range segments {
		wall.AddSegment(segment)
	}

	expectedLength := 6.5 // 2 + 3 + 1.5
	if wall.Length != expectedLength {
		t.Errorf("Expected total length %.1f, got %.1f", expectedLength, wall.Length)
	}
}

func TestWallStructure_CalculateMaxHeight(t *testing.T) {
	wall := NewWallStructure()

	// Add segments with different heights
	segments := []WallSegment{
		{
			ID:     1,
			Length: 1.0,
			Height: 2.0, // 2mm
		},
		{
			ID:     2,
			Length: 1.0,
			Height: 3.5, // 3.5mm (max)
		},
		{
			ID:     3,
			Length: 1.0,
			Height: 1.8, // 1.8mm
		},
	}

	for _, segment := range segments {
		wall.AddSegment(segment)
	}

	expectedHeight := 3.5 // Maximum height
	if wall.Height != expectedHeight {
		t.Errorf("Expected max height %.1f, got %.1f", expectedHeight, wall.Height)
	}
}

func TestWallStructure_CalculateOverallConfidence(t *testing.T) {
	wall := NewWallStructure()

	// Add segments with different confidences and lengths
	segments := []WallSegment{
		{
			ID:         1,
			Length:     2.0, // 2mm
			Confidence: 0.6, // 60%
		},
		{
			ID:         2,
			Length:     3.0, // 3mm
			Confidence: 0.8, // 80%
		},
		{
			ID:         3,
			Length:     1.0, // 1mm
			Confidence: 0.9, // 90%
		},
	}

	for _, segment := range segments {
		wall.AddSegment(segment)
	}

	// Weighted average: (2*0.6 + 3*0.8 + 1*0.9) / (2+3+1) = 0.75
	expectedConfidence := float32(0.75)
	if wall.Confidence != expectedConfidence {
		t.Errorf("Expected confidence %.2f, got %.2f", expectedConfidence, wall.Confidence)
	}
}

func TestWallStructure_UpdateEndpoints(t *testing.T) {
	wall := NewWallStructure()

	// Add segments with different coordinates
	segments := []WallSegment{
		{
			ID:         1,
			StartPoint: NewSmartPoint3D(1000000, 2000000, 0, Nanometer), // (1,2)mm
			EndPoint:   NewSmartPoint3D(3000000, 4000000, 0, Nanometer), // (3,4)mm
			Length:     1.0,
		},
		{
			ID:         2,
			StartPoint: NewSmartPoint3D(500000, 1000000, 0, Nanometer),  // (0.5,1)mm
			EndPoint:   NewSmartPoint3D(4000000, 5000000, 0, Nanometer), // (4,5)mm
			Length:     1.0,
		},
	}

	for _, segment := range segments {
		wall.AddSegment(segment)
	}

	// Expected bounds: min(0.5,1) to max(4,5)
	expectedMinX := int64(500000)  // 0.5mm
	expectedMinY := int64(1000000) // 1mm
	expectedMaxX := int64(4000000) // 4mm
	expectedMaxY := int64(5000000) // 5mm

	if wall.StartPoint.X != expectedMinX {
		t.Errorf("Expected StartPoint.X %d, got %d", expectedMinX, wall.StartPoint.X)
	}

	if wall.StartPoint.Y != expectedMinY {
		t.Errorf("Expected StartPoint.Y %d, got %d", expectedMinY, wall.StartPoint.Y)
	}

	if wall.EndPoint.X != expectedMaxX {
		t.Errorf("Expected EndPoint.X %d, got %d", expectedMaxX, wall.EndPoint.X)
	}

	if wall.EndPoint.Y != expectedMaxY {
		t.Errorf("Expected EndPoint.Y %d, got %d", expectedMaxY, wall.EndPoint.Y)
	}
}

func TestValidationState_String(t *testing.T) {
	testCases := []struct {
		state    ValidationState
		expected string
	}{
		{ValidationPending, "pending"},
		{ValidationPartial, "partial"},
		{ValidationComplete, "complete"},
		{ValidationConflict, "conflict"},
	}

	for _, tc := range testCases {
		if tc.state.String() != tc.expected {
			t.Errorf("ValidationState %v: expected '%s', got '%s'",
				tc.state, tc.expected, tc.state.String())
		}
	}
}
