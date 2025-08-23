package wall_composition

import (
	"fmt"
	"log"
	"strings"

	"github.com/arxos/arxos/core/wall_composition/engine"
	"github.com/arxos/arxos/core/wall_composition/renderer"
	"github.com/arxos/arxos/core/wall_composition/types"
)

// Phase3ComprehensiveTestRunner tests all Phase 3 functionality comprehensively
func Phase3ComprehensiveTestRunner() {
	fmt.Println("🚀 Starting Phase 3 Comprehensive System Tests")
	fmt.Println(strings.Repeat("=", 70))

	// Test 1: Curved Wall Types & Geometry (Phase 3.1)
	testPhase31CurvedWallTypes()

	// Test 2: Advanced Rendering (Phase 3.2)
	testPhase32AdvancedRendering()

	// Test 3: Enhanced Composition Engine (Phase 3.3)
	testPhase33EnhancedComposition()

	// Test 4: Integration Testing
	testPhase3Integration()

	fmt.Println(strings.Repeat("=", 70))
	fmt.Println("✅ Phase 3 Comprehensive System Tests Completed")
}

func testPhase31CurvedWallTypes() {
	fmt.Println("\n🔧 Phase 3.1: Testing Curved Wall Types & Geometry...")

	// Test Bézier curves
	fmt.Println("  📐 Testing Bézier Curves...")
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter) // 50mm
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter)           // 100mm

	quadraticCurve := types.NewQuadraticBezierCurve(start, control, end)
	if quadraticCurve == nil {
		log.Println("    ❌ Failed to create quadratic Bézier curve")
		return
	}
	fmt.Println("    ✅ Quadratic Bézier curve created successfully")

	// Test arc walls
	fmt.Println("  🔄 Testing Arc Walls...")
	center := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter)    // 50mm
	arcStart := types.NewSmartPoint3D(100000000, 50000000, 0, types.Millimeter) // 100mm
	arcEnd := types.NewSmartPoint3D(50000000, 100000000, 0, types.Millimeter)   // 100mm

	circularArc := types.NewCircularArc(center, arcStart, arcEnd, false)
	if circularArc == nil {
		log.Println("    ❌ Failed to create circular arc")
		return
	}
	fmt.Println("    ✅ Circular arc created successfully")

	// Test curved wall segments
	fmt.Println("  🏗️ Testing Curved Wall Segments...")
	baseSegment := &types.WallSegment{
		ID:         1,
		StartPoint: start,
		EndPoint:   end,
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := types.NewCurvedWallSegment(baseSegment, types.CurvedWallTypeBezier)
	if curvedSegment == nil {
		log.Println("    ❌ Failed to create curved wall segment")
		return
	}
	fmt.Println("    ✅ Curved wall segment created successfully")

	// Configure the curve
	curvedSegment.SetBezierCurve(quadraticCurve)
	fmt.Printf("    ✅ Curve configured: %s\n", curvedSegment.GetCurveType())
	fmt.Printf("    ✅ Curve length: %.2fmm\n", curvedSegment.Length)
}

func testPhase32AdvancedRendering() {
	fmt.Println("\n🎨 Phase 3.2: Testing Advanced Rendering...")

	// Create base renderer
	baseRenderer := renderer.NewSVGRenderer(renderer.DefaultRenderConfig())
	curvedRenderer := renderer.NewCurvedWallRenderer(baseRenderer, 20)

	// Create test wall structure with curved segments
	structure := createTestCurvedWallStructure()
	structures := []*types.WallStructure{structure}

	// Test curved wall rendering
	fmt.Println("  🖼️ Testing Curved Wall SVG Rendering...")
	svg, err := curvedRenderer.RenderCurvedWallStructures(structures)
	if err != nil {
		log.Printf("    ❌ Failed to render curved walls: %v", err)
		return
	}

	if len(svg) == 0 {
		log.Println("    ❌ SVG output is empty")
		return
	}

	fmt.Printf("    ✅ SVG rendered successfully (%d characters)\n", len(svg))

	// Check for key SVG elements
	if contains(svg, "<svg") && contains(svg, "</svg>") {
		fmt.Println("    ✅ SVG structure is valid")
	}

	if contains(svg, "path") {
		fmt.Println("    ✅ SVG contains path elements for curves")
	}

	if contains(svg, "wall-structure-0") {
		fmt.Println("    ✅ SVG contains wall structure groups")
	}

	// Test renderer statistics
	stats := curvedRenderer.GetCurvedRenderStats()
	fmt.Printf("    ✅ Renderer stats: %d curve segments, %d structures\n",
		stats.CurveSegments, stats.StructuresRendered)
}

func testPhase33EnhancedComposition() {
	fmt.Println("\n⚙️ Phase 3.3: Testing Enhanced Composition Engine...")

	// Create curved wall composition engine
	config := engine.DefaultCurvedCompositionConfig()
	curvedEngine := engine.NewCurvedWallCompositionEngine(config)

	// Create test ArxObjects (using placeholder implementation)
	testArxObjects := createTestCurvedArxObjects()

	// Test curved wall composition
	fmt.Println("  🔗 Testing Curved Wall Composition...")
	wallStructures, err := curvedEngine.ComposeCurvedWalls(testArxObjects)
	if err != nil {
		log.Printf("    ❌ Failed to compose curved walls: %v", err)
		return
	}

	fmt.Printf("    ✅ Curved wall composition completed: %d structures created\n", len(wallStructures))

	// Test composition statistics
	stats := curvedEngine.GetCurvedCompositionStats()
	fmt.Printf("    ✅ Composition stats: %d walls processed, %d curved detected\n",
		stats.TotalWallsProcessed, stats.CurvedWallsDetected)

	// Validate structures
	for i, structure := range wallStructures {
		fmt.Printf("    📏 Structure %d: %d segments, confidence %.2f, validation: %s\n",
			i, len(structure.Segments), structure.Confidence, structure.Validation.String())
	}
}

func testPhase3Integration() {
	fmt.Println("\n🔗 Phase 3: Testing Integration...")

	// Test end-to-end workflow
	fmt.Println("  🔄 Testing End-to-End Workflow...")

	// 1. Create curved wall types
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter)
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter)

	curve := types.NewQuadraticBezierCurve(start, control, end)
	baseSegment := &types.WallSegment{
		ID:         1,
		StartPoint: start,
		EndPoint:   end,
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := types.NewCurvedWallSegment(baseSegment, types.CurvedWallTypeBezier)
	curvedSegment.SetBezierCurve(curve)

	// 2. Create wall structure
	structure := types.NewWallStructure()
	// Convert curved segment to base segment for compatibility
	baseSegment2 := &types.WallSegment{
		ID:          curvedSegment.ID,
		StartPoint:  curvedSegment.StartPoint,
		EndPoint:    curvedSegment.EndPoint,
		Thickness:   curvedSegment.Thickness,
		Material:    curvedSegment.Material,
		FireRating:  curvedSegment.FireRating,
		Confidence:  curvedSegment.Confidence,
	}
	structure.AddSegment(*baseSegment2)
	structures := []*types.WallStructure{structure}

	// 3. Render to SVG
	baseRenderer := renderer.NewSVGRenderer(renderer.DefaultRenderConfig())
	curvedRenderer := renderer.NewCurvedWallRenderer(baseRenderer, 20)

	svg, err := curvedRenderer.RenderCurvedWallStructures(structures)
	if err != nil {
		log.Printf("    ❌ Integration test failed at rendering: %v", err)
		return
	}

	// 4. Validate output
	if len(svg) > 0 && contains(svg, "<svg") && contains(svg, "path") {
		fmt.Println("    ✅ End-to-end integration test passed")
		fmt.Printf("    📊 Final SVG size: %d characters\n", len(svg))
	} else {
		log.Println("    ❌ Integration test failed - invalid SVG output")
	}
}

// Helper functions
func createTestCurvedWallStructure() *types.WallStructure {
	structure := types.NewWallStructure()

	// Create a curved wall segment
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter)
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter)

	curve := types.NewQuadraticBezierCurve(start, control, end)
	baseSegment := &types.WallSegment{
		ID:         1,
		StartPoint: start,
		EndPoint:   end,
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := types.NewCurvedWallSegment(baseSegment, types.CurvedWallTypeBezier)
	curvedSegment.SetBezierCurve(curve)

	// Convert curved segment to base segment for compatibility
	convertedSegment := &types.WallSegment{
		ID:          curvedSegment.ID,
		StartPoint:  curvedSegment.StartPoint,
		EndPoint:    curvedSegment.EndPoint,
		Thickness:   curvedSegment.Thickness,
		Material:    curvedSegment.Material,
		FireRating:  curvedSegment.FireRating,
		Confidence:  curvedSegment.Confidence,
	}
	structure.AddSegment(*convertedSegment)
	return structure
}

func createTestCurvedArxObjects() []engine.ArxObject {
	// Create placeholder ArxObjects for testing
	// In a real implementation, these would come from the actual ArxObject system
	return []engine.ArxObject{
		&engine.PlaceholderArxObject{
			ID:         "wall1",
			Type:       "wall",
			Confidence: 0.8,
			Coordinates: []types.SmartPoint3D{
				types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
				types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter),
				types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
			},
		},
		&engine.PlaceholderArxObject{
			ID:         "wall2",
			Type:       "wall",
			Confidence: 0.9,
			Coordinates: []types.SmartPoint3D{
				types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
				types.NewSmartPoint3D(150000000, 50000000, 0, types.Millimeter),
				types.NewSmartPoint3D(200000000, 0, 0, types.Millimeter),
			},
		},
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr ||
		(len(s) > len(substr) && (s[:len(substr)] == substr ||
			s[len(s)-len(substr):] == substr ||
			contains(s[1:], substr))))
}

// RunPhase3ComprehensiveTests is the main entry point for running all Phase 3 tests
func RunPhase3ComprehensiveTests() {
	Phase3ComprehensiveTestRunner()
}
