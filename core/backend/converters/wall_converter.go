package converters

import (
	"math"

	"github.com/arxos/arxos/core/arxobject"
)

// WallSegment represents a detected wall from the PDF parser
type WallSegment struct {
	X1         float64 `json:"x1"`         // Start X in pixels
	Y1         float64 `json:"y1"`         // Start Y in pixels
	X2         float64 `json:"x2"`         // End X in pixels
	Y2         float64 `json:"y2"`         // End Y in pixels
	Thickness  float64 `json:"thickness"`  // Wall thickness in pixels
	Confidence float64 `json:"confidence"` // Detection confidence (0-1)
	Type       string  `json:"type"`       // "detected" or "user"
}

// WallConverter handles conversion from PDF walls to ArxObjects
type WallConverter struct {
	// Conversion parameters
	PixelsPerMeter float64 // PDF pixels to real-world meters conversion
	FloorHeight    float64 // Default floor height in meters
	DefaultScale   uint8   // Default scale level for walls
}

// NewWallConverter creates a converter with sensible defaults
func NewWallConverter() *WallConverter {
	return &WallConverter{
		PixelsPerMeter: 100.0, // Assume 100 pixels = 1 meter (adjustable)
		FloorHeight:    3.0,   // 3 meters floor height
		DefaultScale:   1,     // Floor-level scale
	}
}

// ConvertWallToArxObject converts a wall segment to an ArxObject
func (wc *WallConverter) ConvertWallToArxObject(wall WallSegment) *arxobject.ArxObject {
	// Calculate wall center point
	centerX := (wall.X1 + wall.X2) / 2.0
	centerY := (wall.Y1 + wall.Y2) / 2.0

	// Calculate wall length
	dx := wall.X2 - wall.X1
	dy := wall.Y2 - wall.Y1
	length := math.Sqrt(dx*dx + dy*dy)

	// Calculate rotation angle (in degrees)
	angle := math.Atan2(dy, dx) * 180.0 / math.Pi

	// Convert pixels to nanometers for maximum precision
	// 1 meter = 1,000,000,000 nanometers
	nmPerPixel := (1.0 / wc.PixelsPerMeter) * 1000000000.0

	centerXNM := int64(centerX * nmPerPixel)
	centerYNM := int64(centerY * nmPerPixel)
	lengthNM := int64(length * nmPerPixel)
	thicknessNM := int64(wall.Thickness * nmPerPixel)
	heightNM := int64(wc.FloorHeight * 1000000000.0)

	// Create ArxObject with correct fields
	obj := &arxobject.ArxObject{
		ID:        1, // TODO: Generate unique ID
		Type:      arxobject.StructuralWall,
		X:         centerXNM,
		Y:         centerYNM,
		Z:         0, // Ground floor
		Length:    lengthNM,
		Width:     thicknessNM,
		Height:    heightNM,
		RotationZ: int32(angle * 1000), // Convert to millidegrees
		Confidence: arxobject.ConfidenceScore{
			Classification: float32(wall.Confidence),
			Position:       float32(wall.Confidence * 0.9), // Position slightly less certain
			Properties:     0.7,                            // Properties are estimated
			Relationships:  0.5,                            // Relationships not yet determined
			Overall:        float32(wall.Confidence * 0.8), // Overall confidence
		},
	}

	return obj
}

// ConvertBatch converts multiple walls at once
func (wc *WallConverter) ConvertBatch(walls []WallSegment) []*arxobject.ArxObject {
	objects := make([]*arxobject.ArxObject, 0, len(walls))

	for _, wall := range walls {
		obj := wc.ConvertWallToArxObject(wall)
		objects = append(objects, obj)
	}

	return objects
}

// SetScaleFromPDF adjusts the converter based on PDF metadata
func (wc *WallConverter) SetScaleFromPDF(pdfWidth, pdfHeight int, buildingWidthMeters, buildingHeightMeters float64) {
	// Calculate pixels per meter from the PDF dimensions
	pixelsPerMeterX := float64(pdfWidth) / buildingWidthMeters
	pixelsPerMeterY := float64(pdfHeight) / buildingHeightMeters

	// Use average for consistency
	wc.PixelsPerMeter = (pixelsPerMeterX + pixelsPerMeterY) / 2.0
}

// WallIntersection finds where two walls intersect
type WallIntersection struct {
	X, Y       float64
	Wall1ID    uint64
	Wall2ID    uint64
	IntersectT float64 // Parameter t along wall 1 (0-1)
	IntersectS float64 // Parameter s along wall 2 (0-1)
}

// FindIntersection calculates if and where two wall segments intersect
func FindIntersection(w1, w2 WallSegment) (*WallIntersection, bool) {
	// Line segment intersection algorithm
	x1, y1, x2, y2 := w1.X1, w1.Y1, w1.X2, w1.Y2
	x3, y3, x4, y4 := w2.X1, w2.Y1, w2.X2, w2.Y2

	denom := (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
	if math.Abs(denom) < 0.0001 {
		return nil, false // Lines are parallel
	}

	t := ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / denom
	s := ((x1-x3)*(y1-y2) - (y1-y3)*(x1-x2)) / denom

	// Check if intersection is within both segments
	if t >= 0 && t <= 1 && s >= 0 && s <= 1 {
		intersectX := x1 + t*(x2-x1)
		intersectY := y1 + t*(y2-y1)

		return &WallIntersection{
			X:          intersectX,
			Y:          intersectY,
			IntersectT: t,
			IntersectS: s,
		}, true
	}

	return nil, false
}

// SplitWallAtPoint splits a wall segment at a given point
func SplitWallAtPoint(wall WallSegment, splitX, splitY float64) (WallSegment, WallSegment) {
	wall1 := WallSegment{
		X1:         wall.X1,
		Y1:         wall.Y1,
		X2:         splitX,
		Y2:         splitY,
		Thickness:  wall.Thickness,
		Confidence: wall.Confidence,
		Type:       wall.Type,
	}

	wall2 := WallSegment{
		X1:         splitX,
		Y1:         splitY,
		X2:         wall.X2,
		Y2:         wall.Y2,
		Thickness:  wall.Thickness,
		Confidence: wall.Confidence,
		Type:       wall.Type,
	}

	return wall1, wall2
}

// MergeCollinearWalls merges two walls that are collinear and close
func MergeCollinearWalls(w1, w2 WallSegment, tolerance float64) (*WallSegment, bool) {
	// Calculate angles
	angle1 := math.Atan2(w1.Y2-w1.Y1, w1.X2-w1.X1)
	angle2 := math.Atan2(w2.Y2-w2.Y1, w2.X2-w2.X1)

	// Check if angles are similar (allowing for 180 degree difference)
	angleDiff := math.Abs(angle1 - angle2)
	if angleDiff > math.Pi {
		angleDiff = 2*math.Pi - angleDiff
	}

	if angleDiff > 0.1 && math.Abs(angleDiff-math.Pi) > 0.1 {
		return nil, false // Not collinear
	}

	// Check if walls are close enough
	// Calculate distance from end of w1 to start of w2 (or vice versa)
	dist1 := math.Sqrt(math.Pow(w1.X2-w2.X1, 2) + math.Pow(w1.Y2-w2.Y1, 2))
	dist2 := math.Sqrt(math.Pow(w2.X2-w1.X1, 2) + math.Pow(w2.Y2-w1.Y1, 2))

	if dist1 > tolerance && dist2 > tolerance {
		return nil, false // Too far apart
	}

	// Merge the walls - find the extreme points
	points := []struct{ x, y float64 }{
		{w1.X1, w1.Y1},
		{w1.X2, w1.Y2},
		{w2.X1, w2.Y1},
		{w2.X2, w2.Y2},
	}

	// Find the two points that are farthest apart
	maxDist := 0.0
	var p1, p2 struct{ x, y float64 }

	for i := 0; i < len(points); i++ {
		for j := i + 1; j < len(points); j++ {
			dist := math.Sqrt(math.Pow(points[i].x-points[j].x, 2) + math.Pow(points[i].y-points[j].y, 2))
			if dist > maxDist {
				maxDist = dist
				p1 = points[i]
				p2 = points[j]
			}
		}
	}

	merged := &WallSegment{
		X1:         p1.x,
		Y1:         p1.y,
		X2:         p2.x,
		Y2:         p2.y,
		Thickness:  (w1.Thickness + w2.Thickness) / 2,
		Confidence: math.Max(w1.Confidence, w2.Confidence),
		Type:       w1.Type,
	}

	return merged, true
}
