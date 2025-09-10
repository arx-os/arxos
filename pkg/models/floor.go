package models

import "time"

// FloorPlan represents a building floor with rooms and equipment
type FloorPlan struct {
	Name      string           `json:"name"`
	Building  string           `json:"building"`
	Level     int              `json:"level"`
	Rooms     []Room           `json:"rooms"`
	Equipment []Equipment      `json:"equipment"`
	CreatedAt time.Time        `json:"created_at"`
	UpdatedAt time.Time        `json:"updated_at"`
}

// Room represents a space on the floor plan
type Room struct {
	ID        string     `json:"id"`
	Name      string     `json:"name"`
	Bounds    Bounds     `json:"bounds"`
	Equipment []string   `json:"equipment_ids"` // References to Equipment.ID
}

// Equipment represents any marked item on the floor plan
type Equipment struct {
	ID         string         `json:"id"`
	Name       string         `json:"name"`
	Type       string         `json:"type"` // outlet, switch, panel, etc.
	Location   Point          `json:"location"`
	RoomID     string         `json:"room_id"`
	Status     EquipmentStatus `json:"status"`
	Notes      string         `json:"notes"`
	MarkedBy   string         `json:"marked_by"`
	MarkedAt   time.Time      `json:"marked_at"`
}

// EquipmentStatus represents the current state of equipment
type EquipmentStatus string

const (
	StatusNormal      EquipmentStatus = "normal"
	StatusNeedsRepair EquipmentStatus = "needs-repair"
	StatusFailed      EquipmentStatus = "failed"
	StatusUnknown     EquipmentStatus = "unknown"
)

// Point represents a 2D coordinate
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// Bounds represents a rectangular area
type Bounds struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
}

// Contains checks if a point is within bounds
func (b Bounds) Contains(p Point) bool {
	return p.X >= b.MinX && p.X <= b.MaxX &&
		   p.Y >= b.MinY && p.Y <= b.MaxY
}

// Width returns the width of the bounds
func (b Bounds) Width() float64 {
	return b.MaxX - b.MinX
}

// Height returns the height of the bounds
func (b Bounds) Height() float64 {
	return b.MaxY - b.MinY
}