package renderer

import (
	"strings"
	"testing"

	"github.com/arxos/arxos/core/wall_composition/types"
)

func TestNewSVGRenderer(t *testing.T) {
	config := DefaultRenderConfig()
	renderer := NewSVGRenderer(config)

	if renderer == nil {
		t.Fatal("Expected renderer to be created, got nil")
	}

	if renderer.config.Width != config.Width {
		t.Errorf("Expected Width %f, got %f", config.Width, renderer.config.Width)
	}
}

func TestDefaultRenderConfig(t *testing.T) {
	config := DefaultRenderConfig()

	expectedWidth := 297.0
	if config.Width != expectedWidth {
		t.Errorf("Expected Width %f, got %f", expectedWidth, config.Width)
	}

	expectedHeight := 210.0
	if config.Height != expectedHeight {
		t.Errorf("Expected Height %f, got %f", expectedHeight, config.Height)
	}

	expectedScale := 1.0
	if config.Scale != expectedScale {
		t.Errorf("Expected Scale %f, got %f", expectedScale, config.Scale)
	}
}

func TestRenderWallStructuresEmpty(t *testing.T) {
	renderer := NewSVGRenderer(DefaultRenderConfig())
	svg, err := renderer.RenderWallStructures([]*types.WallStructure{})

	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	if !strings.Contains(svg, "No wall structures to render") {
		t.Error("Expected SVG to contain 'No wall structures to render' message")
	}

	if !strings.Contains(svg, "<svg") {
		t.Error("Expected SVG to contain SVG tag")
	}
}

func TestRenderWallStructuresSingleStructure(t *testing.T) {
	renderer := NewSVGRenderer(DefaultRenderConfig())

	// Create a simple wall structure
	structure := types.NewWallStructure()
	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Confidence: 0.8,
	}
	structure.AddSegment(segment)

	svg, err := renderer.RenderWallStructures([]*types.WallStructure{structure})
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !strings.Contains(svg, "<svg") {
		t.Error("Expected SVG to contain SVG tag")
	}

	if !strings.Contains(svg, "wall-structure-0") {
		t.Error("Expected SVG to contain wall structure group")
	}
}

func TestRenderWallStructuresWithConfidence(t *testing.T) {
	config := DefaultRenderConfig()
	config.ShowConfidence = true
	renderer := NewSVGRenderer(config)

	// Create a wall structure with low confidence
	structure := types.NewWallStructure()
	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Confidence: 0.5, // Low confidence
	}
	structure.AddSegment(segment)

	svg, err := renderer.RenderWallStructures([]*types.WallStructure{structure})
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !strings.Contains(svg, "confidence-legend") {
		t.Error("Expected SVG to contain confidence legend")
	}

	if !strings.Contains(svg, "Low (&lt;60%)") {
		t.Error("Expected SVG to contain low confidence label")
	}
}

func TestRenderWallStructuresWithDimensions(t *testing.T) {
	config := DefaultRenderConfig()
	config.ShowDimensions = true
	renderer := NewSVGRenderer(config)

	// Create a wall structure
	structure := types.NewWallStructure()
	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Confidence: 0.8,
	}
	structure.AddSegment(segment)

	svg, err := renderer.RenderWallStructures([]*types.WallStructure{structure})
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !strings.Contains(svg, "<!-- Dimension Labels -->") {
		t.Error("Expected SVG to contain dimension labels section")
	}

	// The method converts 1000mm to 1.0m, so we should look for that
	if !strings.Contains(svg, "1.0m") {
		t.Error("Expected SVG to contain wall dimension")
	}
}

func TestRenderWallStructuresWithMetadata(t *testing.T) {
	config := DefaultRenderConfig()
	config.ShowMetadata = true
	renderer := NewSVGRenderer(config)

	// Create a wall structure with metadata
	structure := types.NewWallStructure()
	structure.Metadata.BuildingID = "Building A"
	structure.Metadata.FloorID = "Floor 1"
	structure.Metadata.WallType = "interior"

	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Confidence: 0.8,
	}
	structure.AddSegment(segment)

	svg, err := renderer.RenderWallStructures([]*types.WallStructure{structure})
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !strings.Contains(svg, "Building A") {
		t.Error("Expected SVG to contain building ID")
	}
}

func TestGetConfidenceClass(t *testing.T) {
	renderer := NewSVGRenderer(DefaultRenderConfig())

	// Test high confidence
	class := renderer.getConfidenceClass(0.9)
	if class != "confidence-high" {
		t.Errorf("Expected confidence-high, got %s", class)
	}

	// Test medium confidence
	class = renderer.getConfidenceClass(0.7)
	if class != "confidence-medium" {
		t.Errorf("Expected confidence-medium, got %s", class)
	}

	// Test low confidence
	class = renderer.getConfidenceClass(0.5)
	if class != "confidence-low" {
		t.Errorf("Expected confidence-low, got %s", class)
	}
}

func TestCalculateBoundingBox(t *testing.T) {
	renderer := NewSVGRenderer(DefaultRenderConfig())

	// Test empty structures
	bounds := renderer.calculateBoundingBox([]*types.WallStructure{})
	expectedWidth := renderer.config.Width * 1e6 // Convert mm to nm
	if float64(bounds.Width()) != expectedWidth {
		t.Errorf("Expected width %f, got %f", expectedWidth, float64(bounds.Width()))
	}

	// Test with single structure
	structure := types.NewWallStructure()
	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Confidence: 0.8,
	}
	structure.AddSegment(segment)

	bounds = renderer.calculateBoundingBox([]*types.WallStructure{structure})
	if bounds.Width() < 1000000000 { // 1000mm = 1,000,000,000nm
		t.Errorf("Expected width >= 1000000000, got %d", bounds.Width())
	}
}

func TestGetRenderStats(t *testing.T) {
	renderer := NewSVGRenderer(DefaultRenderConfig())

	stats := renderer.GetRenderStats()

	if stats.StructuresRendered != 0 {
		t.Errorf("Expected 0 structures rendered, got %d", stats.StructuresRendered)
	}

	if stats.SegmentsRendered != 0 {
		t.Errorf("Expected 0 segments rendered, got %d", stats.SegmentsRendered)
	}
}

func TestRenderThicknessRepresentation(t *testing.T) {
	renderer := NewSVGRenderer(DefaultRenderConfig())

	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Thickness:  200, // 200mm thickness
		Confidence: 0.8,
	}

	thicknessSVG := renderer.renderThicknessRepresentation(&segment)

	if thicknessSVG == "" {
		t.Error("Expected thickness representation to be rendered")
	}

	if !strings.Contains(thicknessSVG, "<line") {
		t.Error("Expected thickness SVG to contain line elements")
	}
}

func TestRenderSegmentDimension(t *testing.T) {
	renderer := NewSVGRenderer(DefaultRenderConfig())

	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Confidence: 0.8,
	}

	dimensionSVG := renderer.renderSegmentDimension(&segment)
	
	// Debug output
	t.Logf("Dimension SVG output: %s", dimensionSVG)
	t.Logf("StartPoint: %v", segment.StartPoint)
	t.Logf("EndPoint: %v", segment.EndPoint)
	t.Logf("Distance: %f", segment.StartPoint.DistanceTo(segment.EndPoint))

	if dimensionSVG == "" {
		t.Error("Expected dimension to be rendered")
	}

	// The method converts 1000mm to 1.0m, so we should look for that
	if !strings.Contains(dimensionSVG, "1.0m") {
		t.Error("Expected dimension SVG to contain wall length")
	}
}
