package bim

import (
	"math"
	"time"

	"github.com/google/uuid"
)

// generateID creates a unique identifier with optional prefix
func generateID(prefix ...string) string {
	id := uuid.New().String()
	if len(prefix) > 0 {
		return prefix[0] + "-" + id
	}
	return id
}

// findWallIntersection finds the intersection point between two walls
func findWallIntersection(w1, w2 *Wall) (*Point3D, bool) {
	// Simple line intersection algorithm
	// Convert walls to line segments
	x1, y1 := w1.StartPoint.X, w1.StartPoint.Y
	x2, y2 := w1.EndPoint.X, w1.EndPoint.Y
	x3, y3 := w2.StartPoint.X, w2.StartPoint.Y
	x4, y4 := w2.EndPoint.X, w2.EndPoint.Y

	denom := (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
	if math.Abs(denom) < 0.0001 {
		return nil, false // Parallel lines
	}

	t := ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / denom
	u := -((x1-x2)*(y1-y3) - (y1-y2)*(x1-x3)) / denom

	if t >= 0 && t <= 1 && u >= 0 && u <= 1 {
		// Intersection exists
		intersectX := x1 + t*(x2-x1)
		intersectY := y1 + t*(y2-y1)
		return &Point3D{
			X: intersectX,
			Y: intersectY,
			Z: w1.StartPoint.Z,
		}, true
	}

	return nil, false
}

// splitWallsAtIntersection splits walls at their intersection point
func (f *Floor) splitWallsAtIntersection(w1, w2 *Wall, intersection *Point3D) {
	// This would split the walls at the intersection point
	// Creating new wall segments
	// For now, just a placeholder implementation
}

// updateRooms updates room definitions after wall changes
func (f *Floor) updateRooms() {
	// This would recalculate room boundaries based on wall positions
	// For now, just update the isDirty flag
	f.isDirty = true
}

// publishUpdate sends an update to all subscribers
func (bm *BuildingModel) publishUpdate(update Update) {
	for _, ch := range bm.subscribers {
		select {
		case ch <- update:
		case <-time.After(100 * time.Millisecond):
			// Skip if subscriber is not ready
		}
	}
}