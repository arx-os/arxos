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
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	FloorPlanID string   `json:"floor_plan_id,omitempty"`
	Bounds      Bounds   `json:"bounds"`
	Equipment   []string `json:"equipment_ids"` // References to Equipment.ID
}

// EquipmentStatus represents the status of equipment
type EquipmentStatus string

const (
	EquipmentStatusActive         EquipmentStatus = "active"
	EquipmentStatusInactive       EquipmentStatus = "inactive"
	EquipmentStatusMaintenance    EquipmentStatus = "maintenance"
	EquipmentStatusFaulty         EquipmentStatus = "faulty"
	EquipmentStatusDecommissioned EquipmentStatus = "decommissioned"
)

// Equipment represents any marked item on the floor plan
type Equipment struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`               // outlet, switch, panel, etc.
	Path       string                 `json:"path"`               // Universal path: N/3/A/301/E
	Location   *Point3D               `json:"location,omitempty"` // Use unified 3D coordinates
	RoomID     string                 `json:"room_id,omitempty"`
	Status     string                 `json:"status"`
	Model      string                 `json:"model,omitempty"`
	Serial     string                 `json:"serial,omitempty"`
	Installed  *time.Time             `json:"installed,omitempty"`
	Maintained *time.Time             `json:"maintained,omitempty"`
	Notes      string                 `json:"notes,omitempty"`
	Tags       []string               `json:"tags,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
	MarkedBy   string                 `json:"marked_by,omitempty"`
	MarkedAt   *time.Time             `json:"marked_at,omitempty"`
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

// Note: Point3D, Point2D, Bounds, and BoundingBox types are defined in spatial.go
