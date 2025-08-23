package types

import (
	"math"
	"testing"
)

func TestCurvedWallTypeString(t *testing.T) {
	tests := []struct {
		curvedType CurvedWallType
		expected   string
	}{
		{CurvedWallTypeBezier, "bezier"},
		{CurvedWallTypeArc, "arc"},
		{CurvedWallTypeSpline, "spline"},
		{CurvedWallType(99), "unknown"},
	}

	for _, test := range tests {
		result := test.curvedType.String()
		if result != test.expected {
			t.Errorf("Expected %s for CurvedWallType %d, got %s", test.expected, test.curvedType, result)
		}
	}
}

func TestNewQuadraticBezierCurve(t *testing.T) {
	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control := NewSmartPoint3D(100, 100, 0, Millimeter)
	end := NewSmartPoint3D(200, 0, 0, Millimeter)

	curve := NewQuadraticBezierCurve(start, control, end)

	if curve == nil {
		t.Fatal("Expected curve to be created, got nil")
	}

	if curve.Degree != 2 {
		t.Errorf("Expected degree 2, got %d", curve.Degree)
	}

	if len(curve.ControlPoints) != 1 {
		t.Errorf("Expected 1 control point, got %d", len(curve.ControlPoints))
	}

	if curve.StartPoint.X != start.X || curve.StartPoint.Y != start.Y || curve.StartPoint.Z != start.Z {
		t.Error("Start point not set correctly")
	}

	if curve.EndPoint.X != end.X || curve.EndPoint.Y != end.Y || curve.EndPoint.Z != end.Z {
		t.Error("End point not set correctly")
	}

	if curve.ControlPoints[0].X != control.X || curve.ControlPoints[0].Y != control.Y || curve.ControlPoints[0].Z != control.Z {
		t.Error("Control point not set correctly")
	}
}

func TestNewCubicBezierCurve(t *testing.T) {
	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control1 := NewSmartPoint3D(100, 100, 0, Millimeter)
	control2 := NewSmartPoint3D(100, -100, 0, Millimeter)
	end := NewSmartPoint3D(200, 0, 0, Millimeter)

	curve := NewCubicBezierCurve(start, control1, control2, end)

	if curve == nil {
		t.Fatal("Expected curve to be created, got nil")
	}

	if curve.Degree != 3 {
		t.Errorf("Expected degree 3, got %d", curve.Degree)
	}

	if len(curve.ControlPoints) != 2 {
		t.Errorf("Expected 2 control points, got %d", len(curve.ControlPoints))
	}

	if curve.StartPoint.X != start.X || curve.StartPoint.Y != start.Y || curve.StartPoint.Z != start.Z {
		t.Error("Start point not set correctly")
	}

	if curve.EndPoint.X != end.X || curve.EndPoint.Y != end.Y || curve.EndPoint.Z != end.Z {
		t.Error("End point not set correctly")
	}

	if curve.ControlPoints[0].X != control1.X || curve.ControlPoints[0].Y != control1.Y || curve.ControlPoints[0].Z != control1.Z {
		t.Error("First control point not set correctly")
	}

	if curve.ControlPoints[1].X != control2.X || curve.ControlPoints[1].Y != control2.Y || curve.ControlPoints[1].Z != control2.Z {
		t.Error("Second control point not set correctly")
	}
}

func TestBezierCurveGetPointAt(t *testing.T) {
	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control := NewSmartPoint3D(100, 100, 0, Millimeter)
	end := NewSmartPoint3D(200, 0, 0, Millimeter)

	curve := NewQuadraticBezierCurve(start, control, end)

	// Test start point (t=0)
	startPoint := curve.GetPointAt(0.0)
	if startPoint.X != start.X || startPoint.Y != start.Y || startPoint.Z != start.Z {
		t.Error("GetPointAt(0.0) should return start point")
	}

	// Test end point (t=1)
	endPoint := curve.GetPointAt(1.0)
	if endPoint.X != end.X || endPoint.Y != end.Y || endPoint.Z != end.Z {
		t.Error("GetPointAt(1.0) should return end point")
	}

	// Test middle point (t=0.5)
	midPoint := curve.GetPointAt(0.5)
	// For a quadratic Bézier curve with control point at (100,100), 
	// the middle point should be approximately at x=100mm (in nanometer coordinates)
	expectedMidX := int64(100000000) // 100mm in nanometers
	if math.Abs(float64(midPoint.X-expectedMidX)) > 10000000 { // Allow 10mm tolerance
		t.Errorf("Expected middle point X to be approximately %d, got %d", expectedMidX, midPoint.X)
	}

	// Test out of bounds (should clamp)
	clampedPoint := curve.GetPointAt(1.5)
	if clampedPoint.X != end.X || clampedPoint.Y != end.Y || clampedPoint.Z != end.Z {
		t.Error("GetPointAt(1.5) should clamp to end point")
	}

	clampedPoint2 := curve.GetPointAt(-0.5)
	if clampedPoint2.X != start.X || clampedPoint2.Y != start.Y || clampedPoint2.Z != start.Z {
		t.Error("GetPointAt(-0.5) should clamp to start point")
	}
}

func TestBezierCurveApproximateToLineSegments(t *testing.T) {
	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control := NewSmartPoint3D(100, 100, 0, Millimeter)
	end := NewSmartPoint3D(200, 0, 0, Millimeter)

	curve := NewQuadraticBezierCurve(start, control, end)

	// Test with 3 segments
	segments := curve.ApproximateToLineSegments(3)
	if len(segments) != 3 {
		t.Errorf("Expected 3 segments, got %d", len(segments))
	}

	// First segment should be start point
	if !segments[0].Equals(start) {
		t.Error("First segment should be start point")
	}

	// Last segment should be end point
	if !segments[2].Equals(end) {
		t.Error("Last segment should be end point")
	}

	// Test with minimum segments (should default to 2)
	segments = curve.ApproximateToLineSegments(1)
	if len(segments) != 2 {
		t.Errorf("Expected 2 segments for minimum, got %d", len(segments))
	}
}

func TestBezierCurveCalculateLength(t *testing.T) {
	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control := NewSmartPoint3D(100, 100, 0, Millimeter)
	end := NewSmartPoint3D(200, 0, 0, Millimeter)

	curve := NewQuadraticBezierCurve(start, control, end)

	// Calculate length with different segment counts
	length10 := curve.CalculateLength(10)
	length50 := curve.CalculateLength(50)
	length100 := curve.CalculateLength(100)

	// Higher segment count should give more accurate length
	if length50 < length10 {
		t.Error("Higher segment count should give more accurate length")
	}

	if length100 < length50 {
		t.Error("Higher segment count should give more accurate length")
	}

	// Length should be reasonable (greater than straight line distance)
	straightDistance := start.DistanceTo(end)
	if length100 <= straightDistance {
		t.Errorf("Curve length should be greater than straight line distance. Got %f, expected > %f", length100, straightDistance)
	}
}

func TestNewCircularArc(t *testing.T) {
	center := NewSmartPoint3D(100, 100, 0, Millimeter)
	start := NewSmartPoint3D(200, 100, 0, Millimeter) // Right of center
	end := NewSmartPoint3D(100, 200, 0, Millimeter)   // Below center

	arc := NewCircularArc(center, start, end, false) // Counterclockwise

	if arc == nil {
		t.Fatal("Expected arc to be created, got nil")
	}

	if arc.IsElliptical {
		t.Error("Circular arc should not be elliptical")
	}

	// Radius is now stored in nanometers, so 100mm = 100000000nm
	expectedRadius := 100000000.0
	if arc.RadiusX != expectedRadius {
		t.Errorf("Expected radius %f, got %f", expectedRadius, arc.RadiusX)
	}

	if arc.RadiusY != expectedRadius {
		t.Errorf("Expected radius %f, got %f", expectedRadius, arc.RadiusY)
	}

	// Test clockwise arc
	arcClockwise := NewCircularArc(center, start, end, true)
	if !arcClockwise.IsClockwise {
		t.Error("Clockwise arc should have IsClockwise=true")
	}
}

func TestNewEllipticalArc(t *testing.T) {
	center := NewSmartPoint3D(100, 100, 0, Millimeter)
	start := NewSmartPoint3D(200, 100, 0, Millimeter)
	end := NewSmartPoint3D(100, 200, 0, Millimeter)
	radiusX := 100.0
	radiusY := 150.0

	arc := NewEllipticalArc(center, start, end, radiusX, radiusY, false)

	if arc == nil {
		t.Fatal("Expected arc to be created, got nil")
	}

	if !arc.IsElliptical {
		t.Error("Elliptical arc should be elliptical")
	}

	if arc.RadiusX != radiusX {
		t.Errorf("Expected radiusX %f, got %f", radiusX, arc.RadiusX)
	}

	if arc.RadiusY != radiusY {
		t.Errorf("Expected radiusY %f, got %f", radiusY, arc.RadiusY)
	}
}

func TestArcWallGetPointAt(t *testing.T) {
	center := NewSmartPoint3D(100, 100, 0, Millimeter)
	start := NewSmartPoint3D(200, 100, 0, Millimeter)
	end := NewSmartPoint3D(100, 200, 0, Millimeter)

	arc := NewCircularArc(center, start, end, false)

	// Test start point (t=0)
	startPoint := arc.GetPointAt(0.0)
	if !startPoint.Equals(start) {
		t.Error("GetPointAt(0.0) should return start point")
	}

	// Test end point (t=1)
	endPoint := arc.GetPointAt(1.0)
	if !endPoint.Equals(end) {
		t.Error("GetPointAt(1.0) should return end point")
	}

	// Test middle point (t=0.5)
	midPoint := arc.GetPointAt(0.5)
	// For a quarter circle with radius 100mm from right to top, middle point should be approximately at (170.7, 170.7)
	// Since we're working in nanometer coordinates, 170.7mm = 170700000nm
	expectedMidX := int64(170700000) // 170.7mm in nanometers
	expectedMidY := int64(170700000) // 170.7mm in nanometers
	
	// Allow 10mm tolerance for both X and Y coordinates
	if math.Abs(float64(midPoint.X)-float64(expectedMidX)) > 10000000 {
		t.Errorf("Expected middle point X to be approximately %d, got %d", expectedMidX, midPoint.X)
	}
	if math.Abs(float64(midPoint.Y)-float64(expectedMidY)) > 10000000 {
		t.Errorf("Expected middle point Y to be approximately %d, got %d", expectedMidY, midPoint.Y)
	}

	// Test out of bounds (should clamp)
	clampedPoint := arc.GetPointAt(1.5)
	if !clampedPoint.Equals(end) {
		t.Error("GetPointAt(1.5) should clamp to end point")
	}

	clampedPoint2 := arc.GetPointAt(-0.5)
	if !clampedPoint2.Equals(start) {
		t.Error("GetPointAt(-0.5) should clamp to start point")
	}
}

func TestArcWallApproximateToLineSegments(t *testing.T) {
	center := NewSmartPoint3D(100, 100, 0, Millimeter)
	start := NewSmartPoint3D(200, 100, 0, Millimeter)
	end := NewSmartPoint3D(100, 200, 0, Millimeter)

	arc := NewCircularArc(center, start, end, false)

	// Test with 5 segments
	segments := arc.ApproximateToLineSegments(5)
	if len(segments) != 5 {
		t.Errorf("Expected 5 segments, got %d", len(segments))
	}

	// First segment should be start point
	if !segments[0].Equals(start) {
		t.Error("First segment should be start point")
	}

	// Last segment should be end point
	if !segments[4].Equals(end) {
		t.Error("Last segment should be end point")
	}

	// Test with minimum segments (should default to 2)
	segments = arc.ApproximateToLineSegments(1)
	if len(segments) != 2 {
		t.Errorf("Expected 2 segments for minimum, got %d", len(segments))
	}
}

func TestArcWallCalculateLength(t *testing.T) {
	center := NewSmartPoint3D(100, 100, 0, Millimeter)
	start := NewSmartPoint3D(200, 100, 0, Millimeter)
	end := NewSmartPoint3D(100, 200, 0, Millimeter)

	arc := NewCircularArc(center, start, end, false)

	// Calculate length with different segment counts
	length10 := arc.CalculateLength(10)
	length50 := arc.CalculateLength(50)
	length100 := arc.CalculateLength(100)

	// Higher segment count should give more accurate length
	if length50 < length10 {
		t.Error("Higher segment count should give more accurate length")
	}

	if length100 < length50 {
		t.Error("Higher segment count should give more accurate length")
	}

	// For a quarter circle with radius 100mm, length should be approximately π/2 * 100 ≈ 157mm
	// The DistanceTo method returns results in millimeters, so we expect millimeter-scale results
	expectedLength := math.Pi / 2.0 * 100.0
	tolerance := 10.0 // Allow some tolerance for approximation
	if math.Abs(length100-expectedLength) > tolerance {
		t.Errorf("Expected length approximately %f, got %f", expectedLength, length100)
	}
}

func TestArcWallGetArcLength(t *testing.T) {
	center := NewSmartPoint3D(100, 100, 0, Millimeter)
	start := NewSmartPoint3D(200, 100, 0, Millimeter)
	end := NewSmartPoint3D(100, 200, 0, Millimeter)

	arc := NewCircularArc(center, start, end, false)

	// For a quarter circle with radius 100mm, length should be π/2 * 100mm
	// Since radius is stored in nanometers, we need to convert: 100mm = 100000000nm
	expectedLength := math.Pi / 2.0 * 100000000.0
	actualLength := arc.GetArcLength()

	if math.Abs(actualLength-expectedLength) > 1000000 { // Allow 1mm tolerance
		t.Errorf("Expected arc length %f, got %f", expectedLength, actualLength)
	}
}

func TestNewCurvedWallSegment(t *testing.T) {
	baseSegment := &WallSegment{
		ID:         1,
		StartPoint: NewSmartPoint3D(0, 0, 0, Millimeter),
		EndPoint:   NewSmartPoint3D(100, 0, 0, Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeBezier)

	if curvedSegment == nil {
		t.Fatal("Expected curved segment to be created, got nil")
	}

	if curvedSegment.WallSegment != baseSegment {
		t.Error("Base segment not set correctly")
	}

	if curvedSegment.CurvedWallType != CurvedWallTypeBezier {
		t.Errorf("Expected curved wall type %d, got %d", CurvedWallTypeBezier, curvedSegment.CurvedWallType)
	}

	if curvedSegment.CurveQuality != 1.0 {
		t.Errorf("Expected curve quality 1.0, got %f", curvedSegment.CurveQuality)
	}
}

func TestCurvedWallSegmentSetBezierCurve(t *testing.T) {
	baseSegment := &WallSegment{
		ID:         1,
		StartPoint: NewSmartPoint3D(0, 0, 0, Millimeter),
		EndPoint:   NewSmartPoint3D(100, 0, 0, Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeBezier)

	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control := NewSmartPoint3D(50, 50, 0, Millimeter)
	end := NewSmartPoint3D(100, 0, 0, Millimeter)

	curve := NewQuadraticBezierCurve(start, control, end)
	curvedSegment.SetBezierCurve(curve)

	if curvedSegment.CurvedWallType != CurvedWallTypeBezier {
		t.Error("Curved wall type not set correctly")
	}

	if curvedSegment.BezierCurve != curve {
		t.Error("Bézier curve not set correctly")
	}

	if curvedSegment.ArcWall != nil {
		t.Error("Arc wall should be nil when setting Bézier curve")
	}

	// Check that start and end points were updated
	if !curvedSegment.StartPoint.Equals(start) {
		t.Error("Start point not updated")
	}

	if !curvedSegment.EndPoint.Equals(end) {
		t.Error("End point not updated")
	}

	// Check that length was calculated
	if curvedSegment.Length <= 0 {
		t.Error("Length should be calculated and positive")
	}
}

func TestCurvedWallSegmentSetArcWall(t *testing.T) {
	baseSegment := &WallSegment{
		ID:         1,
		StartPoint: NewSmartPoint3D(0, 0, 0, Millimeter),
		EndPoint:   NewSmartPoint3D(100, 0, 0, Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	curvedSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeArc)

	center := NewSmartPoint3D(50, 50, 0, Millimeter)
	start := NewSmartPoint3D(100, 50, 0, Millimeter)
	end := NewSmartPoint3D(50, 100, 0, Millimeter)

	arc := NewCircularArc(center, start, end, false)
	curvedSegment.SetArcWall(arc)

	if curvedSegment.CurvedWallType != CurvedWallTypeArc {
		t.Error("Curved wall type not set correctly")
	}

	if curvedSegment.ArcWall != arc {
		t.Error("Arc wall not set correctly")
	}

	if curvedSegment.BezierCurve != nil {
		t.Error("Bézier curve should be nil when setting arc wall")
	}

	// Check that start and end points were updated
	if !curvedSegment.StartPoint.Equals(start) {
		t.Error("Start point not updated")
	}

	if !curvedSegment.EndPoint.Equals(end) {
		t.Error("End point not updated")
	}

	// Check that length was calculated
	if curvedSegment.Length <= 0 {
		t.Error("Length should be calculated and positive")
	}
}

func TestCurvedWallSegmentIsCurved(t *testing.T) {
	baseSegment := &WallSegment{
		ID:         1,
		StartPoint: NewSmartPoint3D(0, 0, 0, Millimeter),
		EndPoint:   NewSmartPoint3D(100, 0, 0, Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	// Test Bézier curve
	bezierSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeBezier)
	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control := NewSmartPoint3D(50, 50, 0, Millimeter)
	end := NewSmartPoint3D(100, 0, 0, Millimeter)
	curve := NewQuadraticBezierCurve(start, control, end)
	bezierSegment.SetBezierCurve(curve)

	if !bezierSegment.IsCurved() {
		t.Error("Bézier curve segment should be considered curved")
	}

	// Test arc wall
	arcSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeArc)
	center := NewSmartPoint3D(50, 50, 0, Millimeter)
	arc := NewCircularArc(center, start, end, false)
	arcSegment.SetArcWall(arc)

	if !arcSegment.IsCurved() {
		t.Error("Arc wall segment should be considered curved")
	}
}

func TestCurvedWallSegmentGetCurveType(t *testing.T) {
	baseSegment := &WallSegment{
		ID:         1,
		StartPoint: NewSmartPoint3D(0, 0, 0, Millimeter),
		EndPoint:   NewSmartPoint3D(100, 0, 0, Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	// Test quadratic Bézier
	quadraticSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeBezier)
	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control := NewSmartPoint3D(50, 50, 0, Millimeter)
	end := NewSmartPoint3D(100, 0, 0, Millimeter)
	curve := NewQuadraticBezierCurve(start, control, end)
	quadraticSegment.SetBezierCurve(curve)

	curveType := quadraticSegment.GetCurveType()
	if curveType != "quadratic_bezier" {
		t.Errorf("Expected curve type 'quadratic_bezier', got '%s'", curveType)
	}

	// Test cubic Bézier
	cubicSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeBezier)
	control1 := NewSmartPoint3D(25, 50, 0, Millimeter)
	control2 := NewSmartPoint3D(75, 50, 0, Millimeter)
	cubicCurve := NewCubicBezierCurve(start, control1, control2, end)
	cubicSegment.SetBezierCurve(cubicCurve)

	curveType = cubicSegment.GetCurveType()
	if curveType != "cubic_bezier" {
		t.Errorf("Expected curve type 'cubic_bezier', got '%s'", curveType)
	}

	// Test circular arc
	arcSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeArc)
	center := NewSmartPoint3D(50, 50, 0, Millimeter)
	arc := NewCircularArc(center, start, end, false)
	arcSegment.SetArcWall(arc)

	curveType = arcSegment.GetCurveType()
	if curveType != "circular_arc" {
		t.Errorf("Expected curve type 'circular_arc', got '%s'", curveType)
	}
}

func TestCurvedWallSegmentGetApproximationPoints(t *testing.T) {
	baseSegment := &WallSegment{
		ID:         1,
		StartPoint: NewSmartPoint3D(0, 0, 0, Millimeter),
		EndPoint:   NewSmartPoint3D(100, 0, 0, Millimeter),
		Thickness:  200,
		Material:   "Concrete",
		FireRating: "2 Hour",
		Confidence: 0.8,
	}

	// Test Bézier curve approximation
	bezierSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeBezier)
	start := NewSmartPoint3D(0, 0, 0, Millimeter)
	control := NewSmartPoint3D(50, 50, 0, Millimeter)
	end := NewSmartPoint3D(100, 0, 0, Millimeter)
	curve := NewQuadraticBezierCurve(start, control, end)
	bezierSegment.SetBezierCurve(curve)

	points := bezierSegment.GetApproximationPoints(5)
	if len(points) != 5 {
		t.Errorf("Expected 5 approximation points, got %d", len(points))
	}

	// Test arc wall approximation
	arcSegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeArc)
	center := NewSmartPoint3D(50, 50, 0, Millimeter)
	arc := NewCircularArc(center, start, end, false)
	arcSegment.SetArcWall(arc)

	points = arcSegment.GetApproximationPoints(7)
	if len(points) != 7 {
		t.Errorf("Expected 7 approximation points, got %d", len(points))
	}

	// Test fallback for uninitialized segment
	emptySegment := NewCurvedWallSegment(baseSegment, CurvedWallTypeBezier)
	points = emptySegment.GetApproximationPoints(3)
	if len(points) != 2 {
		t.Errorf("Expected 2 fallback points, got %d", len(points))
	}
}
