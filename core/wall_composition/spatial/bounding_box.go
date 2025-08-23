package spatial

import (
	"github.com/arxos/arxos/core/wall_composition/types"
)

// BoundingBox represents a 2D bounding box in nanometer coordinates
type BoundingBox struct {
	MinX, MinY int64
	MaxX, MaxY int64
}

// NewBoundingBox creates a new bounding box
func NewBoundingBox(minX, minY, maxX, maxY int64) BoundingBox {
	return BoundingBox{
		MinX: minX,
		MinY: minY,
		MaxX: maxX,
		MaxY: maxY,
	}
}

// Contains checks if a point is within the bounding box
func (bb BoundingBox) Contains(x, y int64) bool {
	return x >= bb.MinX && x <= bb.MaxX && y >= bb.MinY && y <= bb.MaxY
}

// Intersects checks if two bounding boxes intersect
func (bb BoundingBox) Intersects(other BoundingBox) bool {
	return !(bb.MaxX < other.MinX || bb.MinX > other.MaxX ||
		bb.MaxY < other.MinY || bb.MinY > other.MaxY)
}

// Expand expands the bounding box to include a point
func (bb *BoundingBox) Expand(x, y int64) {
	if x < bb.MinX {
		bb.MinX = x
	}
	if x > bb.MaxX {
		bb.MaxX = x
	}
	if y < bb.MinY {
		bb.MinY = y
	}
	if y > bb.MaxY {
		bb.MaxY = y
	}
}

// Width returns the width of the bounding box in nanometers
func (bb BoundingBox) Width() int64 {
	return bb.MaxX - bb.MinX
}

// Height returns the height of the bounding box in nanometers
func (bb BoundingBox) Height() int64 {
	return bb.MaxY - bb.MinY
}

// Area returns the area of the bounding box in square nanometers
func (bb BoundingBox) Area() int64 {
	return bb.Width() * bb.Height()
}

// Center returns the center point of the bounding box
func (bb BoundingBox) Center() types.SmartPoint3D {
	centerX := (bb.MinX + bb.MaxX) / 2
	centerY := (bb.MinY + bb.MaxY) / 2
	return types.NewSmartPoint3D(centerX, centerY, 0, types.Nanometer)
}

// ToMillimeters converts bounding box dimensions to millimeters
func (bb BoundingBox) ToMillimeters() (minX, minY, maxX, maxY float64) {
	return float64(bb.MinX) / 1e6, float64(bb.MinY) / 1e6,
		float64(bb.MaxX) / 1e6, float64(bb.MaxY) / 1e6
}
