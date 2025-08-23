package types

import (
	"time"
)

// ValidationState represents wall validation status
type ValidationState int

const (
	ValidationPending ValidationState = iota
	ValidationPartial
	ValidationComplete
	ValidationConflict
)

// String representation of validation state
func (vs ValidationState) String() string {
	switch vs {
	case ValidationPending:
		return "pending"
	case ValidationPartial:
		return "partial"
	case ValidationComplete:
		return "complete"
	case ValidationConflict:
		return "conflict"
	default:
		return "unknown"
	}
}

// WallStructure represents a composed wall made of multiple segments
type WallStructure struct {
	ID         uint64
	Segments   []WallSegment
	StartPoint SmartPoint3D
	EndPoint   SmartPoint3D
	Length     float64 // Calculated from start/end points (mm)
	Height     float64 // Maximum height of all segments (mm)
	Thickness  float64 // Stubbed for future implementation
	Material   string  // Stubbed for future implementation
	FireRating string  // Stubbed for future implementation
	Confidence float32 // Overall wall confidence (0.0 - 1.0)
	Validation ValidationState
	ArxObjects []uint64 // IDs of composing ArxObjects
	Metadata   WallMetadata
	CreatedAt  time.Time
	UpdatedAt  time.Time
}

// WallSegment represents an individual wall piece within a structure
type WallSegment struct {
	ID          uint64
	StartPoint  SmartPoint3D
	EndPoint    SmartPoint3D
	Length      float64  // Segment length (mm)
	Height      float64  // Segment height (mm)
	Thickness   float64  // Stubbed for future implementation
	Material    string   // Stubbed for future implementation
	FireRating  string   // Stubbed for future implementation
	ArxObjects  []uint64 // IDs of composing ArxObjects
	Confidence  float32  // Individual segment confidence (0.0 - 1.0)
	Orientation float64  // Wall angle in degrees (0-360)
	CreatedAt   time.Time
}

// WallMetadata contains additional wall information
type WallMetadata struct {
	BuildingID   string
	FloorID      string
	RoomID       string
	WallType     string // interior, exterior, load-bearing, etc.
	Notes        string
	Tags         []string
	CustomFields map[string]interface{}
}

// NewWallStructure creates a new wall structure
func NewWallStructure() *WallStructure {
	now := time.Now()
	return &WallStructure{
		ID:         0,
		Segments:   make([]WallSegment, 0),
		Confidence: 0.0,
		Validation: ValidationPending,
		ArxObjects: make([]uint64, 0),
		Metadata:   WallMetadata{},
		CreatedAt:  now,
		UpdatedAt:  now,
	}
}

// AddSegment adds a segment to the wall structure
func (w *WallStructure) AddSegment(segment WallSegment) {
	w.Segments = append(w.Segments, segment)
	w.UpdatedAt = time.Now()
	w.recalculateProperties()
}

// recalculateProperties recalculates wall properties from segments
func (w *WallStructure) recalculateProperties() {
	if len(w.Segments) == 0 {
		return
	}

	// Calculate overall length
	w.Length = w.calculateTotalLength()

	// Calculate overall height
	w.Height = w.calculateMaxHeight()

	// Calculate overall confidence
	w.Confidence = w.calculateOverallConfidence()

	// Update start and end points
	w.updateEndpoints()
}

// calculateTotalLength calculates total wall length
func (w *WallStructure) calculateTotalLength() float64 {
	totalLength := 0.0
	for _, segment := range w.Segments {
		totalLength += segment.Length
	}
	return totalLength
}

// calculateMaxHeight calculates maximum height of all segments
func (w *WallStructure) calculateMaxHeight() float64 {
	maxHeight := 0.0
	for _, segment := range w.Segments {
		if segment.Height > maxHeight {
			maxHeight = segment.Height
		}
	}
	return maxHeight
}

// calculateOverallConfidence calculates weighted confidence
func (w *WallStructure) calculateOverallConfidence() float32 {
	if len(w.Segments) == 0 {
		return 0.0
	}

	// Weight by segment length
	totalLength := 0.0
	weightedConfidence := 0.0

	for _, segment := range w.Segments {
		totalLength += segment.Length
		weightedConfidence += float64(segment.Confidence) * segment.Length
	}

	if totalLength == 0 {
		return 0.0
	}

	return float32(weightedConfidence / totalLength)
}

// updateEndpoints updates start and end points based on segments
func (w *WallStructure) updateEndpoints() {
	if len(w.Segments) == 0 {
		return
	}

	// Find extreme points
	minX, minY := w.Segments[0].StartPoint.X, w.Segments[0].StartPoint.Y
	maxX, maxY := w.Segments[0].StartPoint.X, w.Segments[0].StartPoint.Y

	for _, segment := range w.Segments {
		// Check start point
		if segment.StartPoint.X < minX {
			minX = segment.StartPoint.X
		}
		if segment.StartPoint.X > maxX {
			maxX = segment.StartPoint.X
		}
		if segment.StartPoint.Y < minY {
			minY = segment.StartPoint.Y
		}
		if segment.StartPoint.Y > maxY {
			maxY = segment.StartPoint.Y
		}

		// Check end point
		if segment.EndPoint.X < minX {
			minX = segment.EndPoint.X
		}
		if segment.EndPoint.X > maxX {
			maxX = segment.EndPoint.X
		}
		if segment.EndPoint.Y < minY {
			minY = segment.EndPoint.Y
		}
		if segment.EndPoint.Y > maxY {
			maxY = segment.EndPoint.Y
		}
	}

	w.StartPoint = SmartPoint3D{X: minX, Y: minY, Z: w.Segments[0].StartPoint.Z}
	w.EndPoint = SmartPoint3D{X: maxX, Y: maxY, Z: w.Segments[0].StartPoint.Z}
}
