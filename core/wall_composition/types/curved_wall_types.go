package types

import (
	"math"
)

// CurvedWallType represents the type of curved wall
type CurvedWallType int

const (
	CurvedWallTypeBezier CurvedWallType = iota
	CurvedWallTypeArc
	CurvedWallTypeSpline
)

// String returns the string representation of the curved wall type
func (cwt CurvedWallType) String() string {
	switch cwt {
	case CurvedWallTypeBezier:
		return "bezier"
	case CurvedWallTypeArc:
		return "arc"
	case CurvedWallTypeSpline:
		return "spline"
	default:
		return "unknown"
	}
}

// BezierCurve represents a Bézier curve with control points
type BezierCurve struct {
	StartPoint    SmartPoint3D   // Start point of the curve
	EndPoint      SmartPoint3D   // End point of the curve
	ControlPoints []SmartPoint3D // Control points (1 for quadratic, 2 for cubic)
	Degree        int            // Degree of the curve (2 for quadratic, 3 for cubic)
}

// NewQuadraticBezierCurve creates a quadratic Bézier curve (degree 2)
func NewQuadraticBezierCurve(start, control, end SmartPoint3D) *BezierCurve {
	return &BezierCurve{
		StartPoint:    start,
		EndPoint:      end,
		ControlPoints: []SmartPoint3D{control},
		Degree:        2,
	}
}

// NewCubicBezierCurve creates a cubic Bézier curve (degree 3)
func NewCubicBezierCurve(start, control1, control2, end SmartPoint3D) *BezierCurve {
	return &BezierCurve{
		StartPoint:    start,
		EndPoint:      end,
		ControlPoints: []SmartPoint3D{control1, control2},
		Degree:        3,
	}
}

// GetPointAt returns the point on the Bézier curve at parameter t (0.0 to 1.0)
func (bc *BezierCurve) GetPointAt(t float64) SmartPoint3D {
	if t < 0.0 {
		t = 0.0
	}
	if t > 1.0 {
		t = 1.0
	}

	switch bc.Degree {
	case 2: // Quadratic Bézier
		return bc.quadraticPointAt(t)
	case 3: // Cubic Bézier
		return bc.cubicPointAt(t)
	default:
		return bc.StartPoint
	}
}

// quadraticPointAt calculates point on quadratic Bézier curve
func (bc *BezierCurve) quadraticPointAt(t float64) SmartPoint3D {
	if len(bc.ControlPoints) < 1 {
		return bc.StartPoint
	}

	control := bc.ControlPoints[0]

	// B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
	oneMinusT := 1.0 - t
	oneMinusTSquared := oneMinusT * oneMinusT
	tSquared := t * t
	twoTOneMinusT := 2.0 * t * oneMinusT

	// Calculate in nanometers (internal storage)
	x := int64(oneMinusTSquared*float64(bc.StartPoint.X) + twoTOneMinusT*float64(control.X) + tSquared*float64(bc.EndPoint.X))
	y := int64(oneMinusTSquared*float64(bc.StartPoint.Y) + twoTOneMinusT*float64(control.Y) + tSquared*float64(bc.EndPoint.Y))
	z := int64(oneMinusTSquared*float64(bc.StartPoint.Z) + twoTOneMinusT*float64(control.Z) + tSquared*float64(bc.EndPoint.Z))

	return SmartPoint3D{
		X:    x,
		Y:    y,
		Z:    z,
		unit: bc.StartPoint.GetUnit(),
	}
}

// cubicPointAt calculates point on cubic Bézier curve
func (bc *BezierCurve) cubicPointAt(t float64) SmartPoint3D {
	if len(bc.ControlPoints) < 2 {
		return bc.StartPoint
	}

	control1 := bc.ControlPoints[0]
	control2 := bc.ControlPoints[1]

	// B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
	oneMinusT := 1.0 - t
	oneMinusTCubed := oneMinusT * oneMinusT * oneMinusT
	tCubed := t * t * t
	threeTOneMinusTSquared := 3.0 * t * oneMinusT * oneMinusT
	threeTSquaredOneMinusT := 3.0 * t * t * oneMinusT

	// Calculate in nanometers (internal storage)
	x := int64(oneMinusTCubed*float64(bc.StartPoint.X) + threeTOneMinusTSquared*float64(control1.X) +
		threeTSquaredOneMinusT*float64(control2.X) + tCubed*float64(bc.EndPoint.X))
	y := int64(oneMinusTCubed*float64(bc.StartPoint.Y) + threeTOneMinusTSquared*float64(control1.Y) +
		threeTSquaredOneMinusT*float64(control2.Y) + tCubed*float64(bc.EndPoint.Y))
	z := int64(oneMinusTCubed*float64(bc.StartPoint.Z) + threeTOneMinusTSquared*float64(control1.Z) +
		threeTSquaredOneMinusT*float64(control2.Z) + tCubed*float64(bc.EndPoint.Z))

	return SmartPoint3D{
		X:    x,
		Y:    y,
		Z:    z,
		unit: bc.StartPoint.GetUnit(),
	}
}

// ApproximateToLineSegments converts the Bézier curve to a series of line segments
func (bc *BezierCurve) ApproximateToLineSegments(segments int) []SmartPoint3D {
	if segments < 2 {
		segments = 2
	}

	var points []SmartPoint3D
	step := 1.0 / float64(segments-1)

	for i := 0; i < segments; i++ {
		t := float64(i) * step
		point := bc.GetPointAt(t)
		points = append(points, point)
	}

	return points
}

// CalculateLength approximates the length of the Bézier curve
func (bc *BezierCurve) CalculateLength(segments int) float64 {
	approximation := bc.ApproximateToLineSegments(segments)

	totalLength := 0.0
	for i := 1; i < len(approximation); i++ {
		totalLength += approximation[i-1].DistanceTo(approximation[i])
	}

	return totalLength
}

// ArcWall represents a circular or elliptical arc wall
type ArcWall struct {
	Center       SmartPoint3D // Center point of the arc
	StartPoint   SmartPoint3D // Start point of the arc
	EndPoint     SmartPoint3D // End point of the arc
	RadiusX      float64      // X radius (for elliptical arcs)
	RadiusY      float64      // Y radius (for elliptical arcs)
	StartAngle   float64      // Start angle in radians
	EndAngle     float64      // End angle in radians
	IsClockwise  bool         // Whether the arc is drawn clockwise
	IsElliptical bool         // Whether the arc is elliptical (not circular)
}

// NewCircularArc creates a circular arc wall
func NewCircularArc(center, start, end SmartPoint3D, isClockwise bool) *ArcWall {
	// Calculate radius from center to start point in nanometers
	dx := float64(start.X - center.X)
	dy := float64(start.Y - center.Y)
	radius := math.Sqrt(dx*dx + dy*dy)
	
	// Store radius in nanometers for consistency
	radiusInNanometers := radius

	// Calculate angles
	startAngle := math.Atan2(float64(start.Y-center.Y), float64(start.X-center.X))
	endAngle := math.Atan2(float64(end.Y-center.Y), float64(end.X-center.X))

	// Normalize angles to [0, 2π]
	if startAngle < 0 {
		startAngle += 2 * math.Pi
	}
	if endAngle < 0 {
		endAngle += 2 * math.Pi
	}

	// Handle clockwise vs counterclockwise
	if isClockwise {
		if endAngle >= startAngle {
			endAngle -= 2 * math.Pi
		}
	} else {
		if endAngle <= startAngle {
			endAngle += 2 * math.Pi
		}
	}

	return &ArcWall{
		Center:       center,
		StartPoint:   start,
		EndPoint:     end,
		RadiusX:      radiusInNanometers,
		RadiusY:      radiusInNanometers,
		StartAngle:   startAngle,
		EndAngle:     endAngle,
		IsClockwise:  isClockwise,
		IsElliptical: false,
	}
}

// NewEllipticalArc creates an elliptical arc wall
func NewEllipticalArc(center, start, end SmartPoint3D, radiusX, radiusY float64, isClockwise bool) *ArcWall {
	// Calculate angles for elliptical arc
	startAngle := math.Atan2(float64(start.Y-center.Y), float64(start.X-center.X))
	endAngle := math.Atan2(float64(end.Y-center.Y), float64(end.X-center.X))

	// Normalize angles to [0, 2π]
	if startAngle < 0 {
		startAngle += 2 * math.Pi
	}
	if endAngle < 0 {
		endAngle += 2 * math.Pi
	}

	// Handle clockwise vs counterclockwise
	if isClockwise {
		if endAngle >= startAngle {
			endAngle -= 2 * math.Pi
		}
	} else {
		if endAngle <= startAngle {
			endAngle += 2 * math.Pi
		}
	}

	return &ArcWall{
		Center:       center,
		StartPoint:   start,
		EndPoint:     end,
		RadiusX:      radiusX,
		RadiusY:      radiusY,
		StartAngle:   startAngle,
		EndAngle:     endAngle,
		IsClockwise:  isClockwise,
		IsElliptical: true,
	}
}

// GetPointAt returns the point on the arc at parameter t (0.0 to 1.0)
func (aw *ArcWall) GetPointAt(t float64) SmartPoint3D {
	if t < 0.0 {
		t = 0.0
	}
	if t > 1.0 {
		t = 1.0
	}

	// Interpolate angle
	angle := aw.StartAngle + t*(aw.EndAngle-aw.StartAngle)

	// Calculate point on arc
	// Radius is already in nanometers, so no conversion needed
	radiusX := aw.RadiusX
	radiusY := aw.RadiusY

	// Calculate the point on the arc using the correct trigonometric functions
	x := int64(float64(aw.Center.X) + radiusX*math.Cos(angle))
	y := int64(float64(aw.Center.Y) + radiusY*math.Sin(angle))
	z := aw.Center.Z

	return SmartPoint3D{
		X:    x,
		Y:    y,
		Z:    z,
		unit: aw.Center.GetUnit(),
	}
}

// ApproximateToLineSegments converts the arc to a series of line segments
func (aw *ArcWall) ApproximateToLineSegments(segments int) []SmartPoint3D {
	if segments < 2 {
		segments = 2
	}

	var points []SmartPoint3D
	step := 1.0 / float64(segments-1)

	for i := 0; i < segments; i++ {
		t := float64(i) * step
		point := aw.GetPointAt(t)
		points = append(points, point)
	}

	return points
}

// CalculateLength approximates the length of the arc
func (aw *ArcWall) CalculateLength(segments int) float64 {
	approximation := aw.ApproximateToLineSegments(segments)

	totalLength := 0.0
	for i := 1; i < len(approximation); i++ {
		totalLength += approximation[i-1].DistanceTo(approximation[i])
	}

	return totalLength
}

// GetArcLength calculates the theoretical arc length
func (aw *ArcWall) GetArcLength() float64 {
	angleDiff := math.Abs(aw.EndAngle - aw.StartAngle)

	if aw.IsElliptical {
		// For elliptical arcs, use approximation
		// This is a simplified approximation - for more accuracy, use numerical integration
		return angleDiff * math.Sqrt((aw.RadiusX*aw.RadiusX+aw.RadiusY*aw.RadiusY)/2.0)
	} else {
		// For circular arcs, exact calculation
		return angleDiff * aw.RadiusX
	}
}

// CurvedWallSegment extends WallSegment to support curved geometry
type CurvedWallSegment struct {
	*WallSegment
	CurvedWallType CurvedWallType
	BezierCurve    *BezierCurve
	ArcWall        *ArcWall
	CurveQuality   float64 // Quality metric for curve approximation
}

// NewCurvedWallSegment creates a new curved wall segment
func NewCurvedWallSegment(base *WallSegment, curvedType CurvedWallType) *CurvedWallSegment {
	return &CurvedWallSegment{
		WallSegment:    base,
		CurvedWallType: curvedType,
		CurveQuality:   1.0, // Default high quality
	}
}

// SetBezierCurve sets the Bézier curve for this segment
func (cws *CurvedWallSegment) SetBezierCurve(curve *BezierCurve) {
	cws.CurvedWallType = CurvedWallTypeBezier
	cws.BezierCurve = curve
	cws.ArcWall = nil

	// Update start and end points
	cws.StartPoint = curve.StartPoint
	cws.EndPoint = curve.EndPoint

	// Calculate length
	cws.Length = curve.CalculateLength(50) // Use 50 segments for length calculation
}

// SetArcWall sets the arc wall for this segment
func (cws *CurvedWallSegment) SetArcWall(arc *ArcWall) {
	cws.CurvedWallType = CurvedWallTypeArc
	cws.ArcWall = arc
	cws.BezierCurve = nil

	// Update start and end points
	cws.StartPoint = arc.StartPoint
	cws.EndPoint = arc.EndPoint

	// Calculate length
	cws.Length = arc.CalculateLength(50) // Use 50 segments for length calculation
}

// IsCurved returns true if this segment represents a curved wall
func (cws *CurvedWallSegment) IsCurved() bool {
	return cws.CurvedWallType == CurvedWallTypeBezier || cws.CurvedWallType == CurvedWallTypeArc
}

// GetCurveType returns the type of curve this segment represents
func (cws *CurvedWallSegment) GetCurveType() string {
	switch cws.CurvedWallType {
	case CurvedWallTypeBezier:
		if cws.BezierCurve != nil {
			if cws.BezierCurve.Degree == 2 {
				return "quadratic_bezier"
			} else if cws.BezierCurve.Degree == 3 {
				return "cubic_bezier"
			}
		}
		return "bezier"
	case CurvedWallTypeArc:
		if cws.ArcWall != nil && cws.ArcWall.IsElliptical {
			return "elliptical_arc"
		}
		return "circular_arc"
	default:
		return "straight"
	}
}

// GetApproximationPoints returns the line segment approximation of the curve
func (cws *CurvedWallSegment) GetApproximationPoints(segments int) []SmartPoint3D {
	switch cws.CurvedWallType {
	case CurvedWallTypeBezier:
		if cws.BezierCurve != nil {
			return cws.BezierCurve.ApproximateToLineSegments(segments)
		}
	case CurvedWallTypeArc:
		if cws.ArcWall != nil {
			return cws.ArcWall.ApproximateToLineSegments(segments)
		}
	}

	// Fallback to straight line
	return []SmartPoint3D{cws.StartPoint, cws.EndPoint}
}
