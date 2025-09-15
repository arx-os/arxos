package models

import "time"

// FloorPlan represents a building floor with rooms and equipment
type FloorPlan struct {
	ID             string                 `json:"id"`
	UUID           string                 `json:"uuid,omitempty"` // Universal UUID: ARXOS-NA-US-NY-NYC-0001
	OrganizationID string                 `json:"organization_id,omitempty"`
	Name           string                 `json:"name"`
	Description    string                 `json:"description,omitempty"`
	Building       string                 `json:"building,omitempty"`
	Level          int                    `json:"level"`
	Rooms          []*Room                `json:"rooms,omitempty"`
	Equipment      []*Equipment           `json:"equipment,omitempty"`
	Tags           []string               `json:"tags,omitempty"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
	CreatedBy      string                 `json:"created_by,omitempty"`
	CreatedAt      *time.Time             `json:"created_at,omitempty"`
	UpdatedAt      *time.Time             `json:"updated_at,omitempty"`
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
	ID         string            `json:"id"`
	Name       string            `json:"name"`
	Type       string            `json:"type"` // outlet, switch, panel, etc.
	Path       string            `json:"path"` // Universal path: N/3/A/301/E
	Location   *Point            `json:"location,omitempty"`
	RoomID     string            `json:"room_id,omitempty"`
	Status     string            `json:"status"`
	Model      string            `json:"model,omitempty"`
	Serial     string            `json:"serial,omitempty"`
	Installed  *time.Time        `json:"installed,omitempty"`
	Maintained *time.Time        `json:"maintained,omitempty"`
	Notes      string            `json:"notes,omitempty"`
	Tags       []string          `json:"tags,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
	MarkedBy   string            `json:"marked_by,omitempty"`
	MarkedAt   *time.Time        `json:"marked_at,omitempty"`
}

// Standard equipment status values (matches BIM v2.0 spec)
const (
	StatusOperational = "OPERATIONAL"
	StatusNormal      = "OPERATIONAL" // Alias for backward compatibility
	StatusDegraded    = "DEGRADED"
	StatusFailed      = "FAILED"
	StatusMaintenance = "MAINTENANCE"
	StatusOffline     = "OFFLINE"
	StatusUnknown     = "UNKNOWN"
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