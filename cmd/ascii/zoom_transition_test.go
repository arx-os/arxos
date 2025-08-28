package ascii

import (
	"fmt"
	"math"
	"testing"
	"time"

	"github.com/arxos/arxos/cmd/models"
)

// TestZoomLevelTransitions tests smooth transitions between zoom levels
func TestZoomLevelTransitions(t *testing.T) {
	viewer := NewInteractiveViewer(80, 24)
	
	// Test zoom in transition
	viewer.CurrentZoom = ZoomFloor
	viewer.ZoomIn()
	
	if viewer.TargetZoom != ZoomRoom {
		t.Errorf("Expected target zoom to be Room, got %v", viewer.TargetZoom)
	}
	
	// Simulate animation frames
	for i := 0; i < 10; i++ {
		viewer.Update()
		time.Sleep(time.Millisecond * 16) // Simulate 60fps
		
		// Check transition is progressing
		if i > 0 && viewer.ZoomTransition == 0.0 {
			t.Error("Zoom transition not progressing")
		}
	}
	
	// Test zoom out transition
	viewer.ZoomOut()
	if viewer.TargetZoom != ZoomFloor {
		t.Errorf("Expected target zoom to be Floor, got %v", viewer.TargetZoom)
	}
}

// TestZoomLevelConstraints tests zoom level boundaries
func TestZoomLevelConstraints(t *testing.T) {
	viewer := NewInteractiveViewer(80, 24)
	
	// Test maximum zoom in
	viewer.CurrentZoom = ZoomChip
	viewer.ZoomIn()
	if viewer.TargetZoom != ZoomChip {
		t.Error("Should not zoom in beyond Chip level")
	}
	
	// Test maximum zoom out
	viewer.CurrentZoom = ZoomCampus
	viewer.ZoomOut()
	if viewer.TargetZoom != ZoomCampus {
		t.Error("Should not zoom out beyond Campus level")
	}
}

// TestDirectZoomLevelJump tests jumping directly to a zoom level
func TestDirectZoomLevelJump(t *testing.T) {
	viewer := NewInteractiveViewer(80, 24)
	
	testCases := []struct {
		name     string
		level    ZoomLevel
		expected ZoomLevel
	}{
		{"Jump to Campus", ZoomCampus, ZoomCampus},
		{"Jump to Building", ZoomBuilding, ZoomBuilding},
		{"Jump to Floor", ZoomFloor, ZoomFloor},
		{"Jump to Room", ZoomRoom, ZoomRoom},
		{"Jump to Equipment", ZoomEquipment, ZoomEquipment},
		{"Jump to Component", ZoomComponent, ZoomComponent},
		{"Jump to Chip", ZoomChip, ZoomChip},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			viewer.ZoomToLevel(tc.level)
			if viewer.TargetZoom != tc.expected {
				t.Errorf("Expected zoom level %v, got %v", tc.expected, viewer.TargetZoom)
			}
		})
	}
}

// TestZoomScaling tests scale values for each zoom level
func TestZoomScaling(t *testing.T) {
	testCases := []struct {
		zoom     ZoomLevel
		expected float64
	}{
		{ZoomCampus, 0.01},      // 1 char = 100m
		{ZoomBuilding, 0.1},     // 1 char = 10m
		{ZoomFloor, 1.0},        // 1 char = 1m
		{ZoomRoom, 1.0},         // 1 char = 1m
		{ZoomEquipment, 10.0},   // 1 char = 10cm
		{ZoomComponent, 100.0},  // 1 char = 1cm
		{ZoomChip, 1000.0},      // 1 char = 1mm
	}
	
	for _, tc := range testCases {
		t.Run(getZoomName(tc.zoom), func(t *testing.T) {
			scale := getScaleForZoom(tc.zoom)
			if scale != tc.expected {
				t.Errorf("Expected scale %v for %s, got %v", 
					tc.expected, getZoomName(tc.zoom), scale)
			}
		})
	}
}

// TestPanTransition tests smooth panning transitions
func TestPanTransition(t *testing.T) {
	viewer := NewInteractiveViewer(80, 24)
	
	// Set initial position
	viewer.ViewportX = 0
	viewer.ViewportY = 0
	
	// Pan right
	viewer.Pan(10, 0)
	if viewer.TargetX == 0 {
		t.Error("Pan did not update target X")
	}
	
	// Simulate animation
	for i := 0; i < 20; i++ {
		oldX := viewer.ViewportX
		viewer.Update()
		
		// Check viewport is moving towards target
		if i > 0 && viewer.ViewportX <= oldX {
			t.Error("Viewport not moving towards target")
		}
		
		// Check if reached target
		if math.Abs(viewer.ViewportX-viewer.TargetX) < 0.1 {
			break
		}
	}
	
	// Verify pan completed
	if math.Abs(viewer.ViewportX-viewer.TargetX) > 0.1 {
		t.Error("Pan transition did not complete")
	}
}

// TestFocusObject tests focusing on objects during zoom
func TestFocusObject(t *testing.T) {
	viewer := NewInteractiveViewer(80, 24)
	
	// Create test objects
	viewer.Objects = []*models.ArxObject{
		{
			Path: "/electrical/panel",
			Type: "panel",
			Name: "Main Panel",
			Position: models.Position{X: 100, Y: 200},
		},
		{
			Path: "/hvac/unit",
			Type: "equipment",
			Name: "HVAC Unit",
			Position: models.Position{X: 300, Y: 400},
		},
	}
	
	// Center viewport at origin
	viewer.ViewportX = 0
	viewer.ViewportY = 0
	
	// Zoom in - should focus on nearest object
	viewer.ZoomIn()
	
	// Check focus object is set
	if viewer.FocusObject == nil {
		t.Error("Focus object not set when zooming in")
	}
	
	// Verify it found the closest object (Main Panel)
	if viewer.FocusObject.Name != "Main Panel" {
		t.Errorf("Expected focus on Main Panel, got %s", viewer.FocusObject.Name)
	}
}

// TestEasingFunction tests the cubic easing function
func TestEasingFunction(t *testing.T) {
	viewer := NewInteractiveViewer(80, 24)
	
	testCases := []struct {
		input    float64
		expected float64 // Approximate
	}{
		{0.0, 0.0},
		{0.25, 0.0625},   // Slow start
		{0.5, 0.5},       // Midpoint
		{0.75, 0.9375},   // Fast end
		{1.0, 1.0},
	}
	
	for _, tc := range testCases {
		result := viewer.easeInOutCubic(tc.input)
		if math.Abs(result-tc.expected) > 0.01 {
			t.Errorf("Easing function at %v: expected ~%v, got %v", 
				tc.input, tc.expected, result)
		}
	}
}

// TestCharacterSetSelection tests character set for each zoom level
func TestCharacterSetSelection(t *testing.T) {
	renderer := NewTerminalRenderer(80, 24)
	
	// Test each zoom level has unique character set
	zoomLevels := []ZoomLevel{
		ZoomCampus, ZoomBuilding, ZoomFloor, ZoomRoom,
		ZoomEquipment, ZoomComponent, ZoomChip,
	}
	
	for _, zoom := range zoomLevels {
		charSet, exists := renderer.CharSets[zoom]
		if !exists {
			t.Errorf("No character set defined for zoom level %s", getZoomName(zoom))
		}
		
		// Verify essential characters are defined
		if charSet.Wall == ' ' {
			t.Errorf("Wall character not defined for %s", getZoomName(zoom))
		}
		if charSet.Door == ' ' {
			t.Errorf("Door character not defined for %s", getZoomName(zoom))
		}
	}
}

// TestInterpolatedCharacterSet tests character set interpolation during transitions
func TestInterpolatedCharacterSet(t *testing.T) {
	viewer := NewInteractiveViewer(80, 24)
	
	// Test interpolation at different transition points
	fromZoom := ZoomFloor
	toZoom := ZoomRoom
	
	// At 0% transition - should use source character set
	charSet1 := viewer.getInterpolatedCharSet(fromZoom, toZoom, 0.0)
	if charSet1 != viewer.Renderer.CharSets[fromZoom] {
		t.Error("Should use source character set at 0% transition")
	}
	
	// At 49% transition - should still use source character set
	charSet2 := viewer.getInterpolatedCharSet(fromZoom, toZoom, 0.49)
	if charSet2 != viewer.Renderer.CharSets[fromZoom] {
		t.Error("Should use source character set below 50% transition")
	}
	
	// At 50% transition - should switch to target character set
	charSet3 := viewer.getInterpolatedCharSet(fromZoom, toZoom, 0.5)
	if charSet3 != viewer.Renderer.CharSets[toZoom] {
		t.Error("Should use target character set at 50% transition")
	}
	
	// At 100% transition - should use target character set
	charSet4 := viewer.getInterpolatedCharSet(fromZoom, toZoom, 1.0)
	if charSet4 != viewer.Renderer.CharSets[toZoom] {
		t.Error("Should use target character set at 100% transition")
	}
}

// TestViewportConstraints tests viewport boundary constraints
func TestViewportConstraints(t *testing.T) {
	viewer := NewInteractiveViewer(80, 24)
	
	// Test extreme pan values
	viewer.CurrentZoom = ZoomFloor
	viewer.Pan(10000, 10000)
	viewer.constrainViewport()
	
	maxBound := 1000.0 / getScaleForZoom(viewer.CurrentZoom)
	
	if viewer.TargetX > maxBound {
		t.Errorf("TargetX exceeds max bound: %v > %v", viewer.TargetX, maxBound)
	}
	if viewer.TargetY > maxBound {
		t.Errorf("TargetY exceeds max bound: %v > %v", viewer.TargetY, maxBound)
	}
	
	// Test negative extreme values
	viewer.Pan(-10000, -10000)
	viewer.constrainViewport()
	
	if viewer.TargetX < -maxBound {
		t.Errorf("TargetX below min bound: %v < %v", viewer.TargetX, -maxBound)
	}
	if viewer.TargetY < -maxBound {
		t.Errorf("TargetY below min bound: %v < %v", viewer.TargetY, -maxBound)
	}
}

// BenchmarkZoomTransition benchmarks zoom transition performance
func BenchmarkZoomTransition(b *testing.B) {
	viewer := NewInteractiveViewer(80, 24)
	
	// Create many objects for realistic scenario
	for i := 0; i < 1000; i++ {
		viewer.Objects = append(viewer.Objects, &models.ArxObject{
			Path: fmt.Sprintf("/obj/%d", i),
			Type: "equipment",
			Position: models.Position{
				X: float64(i % 100),
				Y: float64(i / 100),
			},
		})
	}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		// Zoom in
		viewer.ZoomIn()
		// Simulate transition
		for j := 0; j < 10; j++ {
			viewer.Update()
		}
		// Zoom out
		viewer.ZoomOut()
		// Simulate transition
		for j := 0; j < 10; j++ {
			viewer.Update()
		}
	}
}

// BenchmarkRenderWithScale benchmarks rendering at different scales
func BenchmarkRenderWithScale(b *testing.B) {
	viewer := NewInteractiveViewer(80, 24)
	
	// Create test objects
	for i := 0; i < 100; i++ {
		viewer.Objects = append(viewer.Objects, &models.ArxObject{
			Path: fmt.Sprintf("/obj/%d", i),
			Type: "wall",
			Position: models.Position{
				X: float64(i % 10 * 10),
				Y: float64(i / 10 * 10),
			},
		})
	}
	
	scales := []float64{0.01, 0.1, 1.0, 10.0, 100.0}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		scale := scales[i%len(scales)]
		charSet := viewer.Renderer.CharSets[ZoomFloor]
		_ = viewer.renderWithScale(scale, charSet)
	}
}