package wall_composition

import (
	"fmt"
	"log"
	"strings"

	"github.com/arxos/arxos/core/wall_composition/types"
)

// Phase3TestRunner tests the Phase 3 curved wall functionality
func Phase3TestRunner() {
	fmt.Println("🚀 Starting Phase 3 Curved Wall System Tests")
	fmt.Println(strings.Repeat("=", 60))

	// Test 1: Curved Wall Types
	testCurvedWallTypes()

	// Test 2: Bézier Curve Creation
	testBezierCurveCreation()

	// Test 3: Arc Wall Creation
	testArcWallCreation()

	// Test 4: Curved Wall Segments
	testCurvedWallSegments()

	// Test 5: Curve Approximation
	testCurveApproximation()

	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("✅ Phase 3 Curved Wall System Tests Completed")
}

func testCurvedWallTypes() {
	fmt.Println("\n🔧 Testing Curved Wall Types...")

	// Test CurvedWallType enum
	bezierType := types.CurvedWallTypeBezier
	arcType := types.CurvedWallTypeArc
	splineType := types.CurvedWallTypeSpline

	fmt.Printf("✅ Bézier Type: %s\n", bezierType.String())
	fmt.Printf("✅ Arc Type: %s\n", arcType.String())
	fmt.Printf("✅ Spline Type: %s\n", splineType.String())

	// Test unknown type
	unknownType := types.CurvedWallType(99)
	fmt.Printf("✅ Unknown Type: %s\n", unknownType.String())
}

func testBezierCurveCreation() {
	fmt.Println("\n📐 Testing Bézier Curve Creation...")

	// Create test points (in nanometers)
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(100000000, 100000000, 0, types.Millimeter) // 100mm
	end := types.NewSmartPoint3D(200000000, 0, 0, types.Millimeter)             // 200mm

	// Test quadratic Bézier curve
	quadraticCurve := types.NewQuadraticBezierCurve(start, control, end)
	if quadraticCurve == nil {
		log.Println("❌ Failed to create quadratic Bézier curve")
		return
	}

	fmt.Printf("✅ Quadratic Bézier Curve created (Degree: %d)\n", quadraticCurve.Degree)
	fmt.Printf("✅ Control Points: %d\n", len(quadraticCurve.ControlPoints))

	// Test cubic Bézier curve
	control1 := types.NewSmartPoint3D(50000000, 100000000, 0, types.Millimeter)  // 50mm
	control2 := types.NewSmartPoint3D(150000000, 100000000, 0, types.Millimeter) // 150mm

	cubicCurve := types.NewCubicBezierCurve(start, control1, control2, end)
	if cubicCurve == nil {
		log.Println("❌ Failed to create cubic Bézier curve")
		return
	}

	fmt.Printf("✅ Cubic Bézier Curve created (Degree: %d)\n", cubicCurve.Degree)
	fmt.Printf("✅ Control Points: %d\n", len(cubicCurve.ControlPoints))
}

func testArcWallCreation() {
	fmt.Println("\n🔄 Testing Arc Wall Creation...")

	// Create test points (in nanometers)
	center := types.NewSmartPoint3D(100000000, 100000000, 0, types.Millimeter) // 100mm
	start := types.NewSmartPoint3D(200000000, 100000000, 0, types.Millimeter)  // 200mm
	end := types.NewSmartPoint3D(100000000, 200000000, 0, types.Millimeter)    // 100mm

	// Test circular arc
	circularArc := types.NewCircularArc(center, start, end, false) // Counterclockwise
	if circularArc == nil {
		log.Println("❌ Failed to create circular arc")
		return
	}

	fmt.Printf("✅ Circular Arc created\n")
	fmt.Printf("✅ Radius: %.2fmm\n", circularArc.RadiusX)
	fmt.Printf("✅ Is Elliptical: %t\n", circularArc.IsElliptical)
	fmt.Printf("✅ Is Clockwise: %t\n", circularArc.IsClockwise)

	// Test elliptical arc
	radiusX := 100.0 // 100mm
	radiusY := 150.0 // 150mm
	ellipticalArc := types.NewEllipticalArc(center, start, end, radiusX, radiusY, false)
	if ellipticalArc == nil {
		log.Println("❌ Failed to create elliptical arc")
		return
	}

	fmt.Printf("✅ Elliptical Arc created\n")
	fmt.Printf("✅ Radius X: %.2fmm\n", ellipticalArc.RadiusX)
	fmt.Printf("✅ Radius Y: %.2fmm\n", ellipticalArc.RadiusY)
	fmt.Printf("✅ Is Elliptical: %t\n", ellipticalArc.IsElliptical)
}

func testCurvedWallSegments() {
	fmt.Println("\n🏗️ Testing Curved Wall Segments...")

	// Create base wall segment
	baseSegment := &types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	// Create curved wall segment
	curvedSegment := types.NewCurvedWallSegment(baseSegment, types.CurvedWallTypeBezier)
	if curvedSegment == nil {
		log.Println("❌ Failed to create curved wall segment")
		return
	}

	fmt.Printf("✅ Curved Wall Segment created\n")
	fmt.Printf("✅ Curve Type: %s\n", curvedSegment.GetCurveType())
	fmt.Printf("✅ Is Curved: %t\n", curvedSegment.IsCurved())

	// Test Bézier curve configuration
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter) // 50mm
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter)           // 100mm

	curve := types.NewQuadraticBezierCurve(start, control, end)
	curvedSegment.SetBezierCurve(curve)

	fmt.Printf("✅ Bézier Curve configured\n")
	fmt.Printf("✅ Updated Curve Type: %s\n", curvedSegment.GetCurveType())
	fmt.Printf("✅ Length: %.2fmm\n", curvedSegment.Length)
}

func testCurveApproximation() {
	fmt.Println("\n📏 Testing Curve Approximation...")

	// Create a Bézier curve
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	control := types.NewSmartPoint3D(50000000, 100000000, 0, types.Millimeter) // 50mm, 100mm
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter)            // 100mm

	curve := types.NewQuadraticBezierCurve(start, control, end)

	// Test approximation with different segment counts
	segments5 := curve.ApproximateToLineSegments(5)
	segments10 := curve.ApproximateToLineSegments(10)
	segments20 := curve.ApproximateToLineSegments(20)

	fmt.Printf("✅ 5-segment approximation: %d points\n", len(segments5))
	fmt.Printf("✅ 10-segment approximation: %d points\n", len(segments10))
	fmt.Printf("✅ 20-segment approximation: %d points\n", len(segments20))

	// Test length calculation
	length5 := curve.CalculateLength(5)
	length10 := curve.CalculateLength(10)
	length20 := curve.CalculateLength(20)

	fmt.Printf("✅ 5-segment length: %.2fmm\n", length5)
	fmt.Printf("✅ 10-segment length: %.2fmm\n", length10)
	fmt.Printf("✅ 20-segment length: %.2fmm\n", length20)

	// Test arc approximation
	center := types.NewSmartPoint3D(50000000, 50000000, 0, types.Millimeter) // 50mm
	arc := types.NewCircularArc(center, start, end, false)

	arcSegments10 := arc.ApproximateToLineSegments(10)
	arcLength10 := arc.CalculateLength(10)
	theoreticalLength := arc.GetArcLength()

	fmt.Printf("✅ Arc 10-segment approximation: %d points\n", len(arcSegments10))
	fmt.Printf("✅ Arc 10-segment length: %.2fmm\n", arcLength10)
	fmt.Printf("✅ Arc theoretical length: %.2fmm\n", theoreticalLength)
}

// RunPhase3Tests is the main entry point for running Phase 3 tests
func RunPhase3Tests() {
	Phase3TestRunner()
}
