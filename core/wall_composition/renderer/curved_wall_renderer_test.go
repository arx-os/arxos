package renderer

import (
	"strings"
	"testing"

	"github.com/arxos/arxos/core/wall_composition/types"
)

func TestNewCurvedWallRenderer(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())

	// Test with valid segments
	renderer := NewCurvedWallRenderer(baseRenderer, 20)
	if renderer == nil {
		t.Fatal("Expected renderer to be created, got nil")
	}

	if renderer.CurveSegments != 20 {
		t.Errorf("Expected 20 curve segments, got %d", renderer.CurveSegments)
	}

	// Test with minimum segments (should default to 10)
	renderer = NewCurvedWallRenderer(baseRenderer, 5)
	if renderer.CurveSegments != 10 {
		t.Errorf("Expected 10 curve segments for minimum, got %d", renderer.CurveSegments)
	}
}

func TestRenderCurvedWallStructures(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	// Test empty structures
	svg, err := renderer.RenderCurvedWallStructures([]*types.WallStructure{})
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !strings.Contains(svg, "<svg") {
		t.Error("Expected SVG output to contain <svg tag")
	}

	if !strings.Contains(svg, "</svg>") {
		t.Error("Expected SVG output to contain </svg> tag")
	}

	// Test with simple structure
	structure := createTestWallStructure()
	structures := []*types.WallStructure{structure}

	svg, err = renderer.RenderCurvedWallStructures(structures)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if !strings.Contains(svg, "wall-structure-0") {
		t.Error("Expected SVG output to contain wall structure group")
	}
}

func TestRenderCurvedWallStructure(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	structure := createTestWallStructure()
	svg := renderer.renderCurvedWallStructure(structure, 0)

	if !strings.Contains(svg, "wall-structure-0") {
		t.Error("Expected SVG output to contain wall structure group")
	}

	if !strings.Contains(svg, "wall-segment-0") {
		t.Error("Expected SVG output to contain wall segment")
	}
}

func TestRenderCurvedWallSegment(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	// Test regular wall segment
	segment := &types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	svg := renderer.renderCurvedWallSegment(segment, 0)
	if !strings.Contains(svg, "wall-segment-0") {
		t.Error("Expected SVG output to contain wall segment")
	}

	if !strings.Contains(svg, "line") {
		t.Error("Expected SVG output to contain line element")
	}
}

func TestRenderCurvedSegment(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	// Test Bézier curve segment
	baseSegment := &types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := types.NewCurvedWallSegment(baseSegment, types.CurvedWallTypeBezier)
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter)
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter)
	curve := types.NewQuadraticBezierCurve(start, control, end)
	curvedSegment.SetBezierCurve(curve)

	svg := renderer.renderCurvedSegment(curvedSegment, 0)
	if !strings.Contains(svg, "wall-segment-0") {
		t.Error("Expected SVG output to contain wall segment")
	}

	if !strings.Contains(svg, "path") {
		t.Error("Expected SVG output to contain path element for curve")
	}
}

func TestRenderBezierCurve(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	baseSegment := &types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := types.NewCurvedWallSegment(baseSegment, types.CurvedWallTypeBezier)
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter)
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter)
	curve := types.NewQuadraticBezierCurve(start, control, end)
	curvedSegment.SetBezierCurve(curve)

	// Test with high confidence
	svg := renderer.renderBezierCurve(curvedSegment, 0, "high")
	if !strings.Contains(svg, "path") {
		t.Error("Expected SVG output to contain path element")
	}

	if !strings.Contains(svg, "stroke=\"#00FF00\"") {
		t.Error("Expected SVG output to contain high confidence color")
	}

	// Test with low confidence
	svg = renderer.renderBezierCurve(curvedSegment, 0, "low")
	if !strings.Contains(svg, "stroke=\"#FF0000\"") {
		t.Error("Expected SVG output to contain low confidence color")
	}
}

func TestRenderArcWall(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	baseSegment := &types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := types.NewCurvedWallSegment(baseSegment, types.CurvedWallTypeArc)
	center := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter)
	start := types.NewSmartPoint3D(100000000, 50000000, 0, types.Millimeter)
	end := types.NewSmartPoint3D(50000000, 100000000, 0, types.Millimeter)
	arc := types.NewCircularArc(center, start, end, false)
	curvedSegment.SetArcWall(arc)

	svg := renderer.renderArcWall(curvedSegment, 0, "medium")
	if !strings.Contains(svg, "path") {
		t.Error("Expected SVG output to contain path element")
	}

	if !strings.Contains(svg, "stroke=\"#FFFF00\"") {
		t.Error("Expected SVG output to contain medium confidence color")
	}
}

func TestRenderCurvedThicknessRepresentation(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	baseSegment := &types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := types.NewCurvedWallSegment(baseSegment, types.CurvedWallTypeBezier)
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter)
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter)
	curve := types.NewQuadraticBezierCurve(start, control, end)
	curvedSegment.SetBezierCurve(curve)

	svg := renderer.renderCurvedThicknessRepresentation(curvedSegment)
	if !strings.Contains(svg, "line") {
		t.Error("Expected SVG output to contain line elements for thickness")
	}
}

func TestRenderCurvedDimensionLabels(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	structure := createTestWallStructure()
	structures := []*types.WallStructure{structure}

	var svgBuilder strings.Builder
	renderer.renderCurvedDimensionLabels(&svgBuilder, structures)

	svg := svgBuilder.String()
	if !strings.Contains(svg, "text") {
		t.Error("Expected SVG output to contain text elements for dimensions")
	}
}

func TestGetCurvedRenderStats(t *testing.T) {
	baseRenderer := NewSVGRenderer(DefaultRenderConfig())
	renderer := NewCurvedWallRenderer(baseRenderer, 20)

	stats := renderer.GetCurvedRenderStats()

	if stats.CurveSegments != 20 {
		t.Errorf("Expected 20 curve segments, got %d", stats.CurveSegments)
	}

	if stats.StructuresRendered != 0 {
		t.Errorf("Expected 0 structures rendered, got %d", stats.StructuresRendered)
	}

	if stats.CurvedSegmentsRendered != 0 {
		t.Errorf("Expected 0 curved segments rendered, got %d", stats.CurvedSegmentsRendered)
	}
}

// Helper function to create a test wall structure
func createTestWallStructure() *types.WallStructure {
	structure := types.NewWallStructure()

	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	structure.AddSegment(segment)
	return structure
}
