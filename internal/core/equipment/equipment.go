package equipment

import (
	"errors"
	"time"

	"github.com/google/uuid"
)

var (
	// ErrNotFound is returned when equipment is not found
	ErrNotFound = errors.New("equipment not found")
	// ErrInvalidID is returned when equipment ID is invalid
	ErrInvalidID = errors.New("invalid equipment ID")
	// ErrDuplicate is returned when trying to create duplicate equipment
	ErrDuplicate = errors.New("equipment already exists")
)

// Confidence levels for spatial data
const (
	ConfidenceEstimated = 0 // Derived from PDF/IFC without verification
	ConfidenceLow       = 1 // Automated detection
	ConfidenceMedium    = 2 // Partial verification
	ConfidenceHigh      = 3 // LiDAR or AR verified
)

// Equipment status values
const (
	StatusUnknown     = "UNKNOWN"
	StatusOperational = "OPERATIONAL"
	StatusDegraded    = "DEGRADED"
	StatusFailed      = "FAILED"
	StatusMaintenance = "MAINTENANCE"
	StatusOffline     = "OFFLINE"
)

// Position represents 3D coordinates
type Position struct {
	X float64 `json:"x"` // Longitude or local X
	Y float64 `json:"y"` // Latitude or local Y
	Z float64 `json:"z"` // Altitude or local Z
}

// Equipment represents equipment entity in the domain
type Equipment struct {
	ID           uuid.UUID              `json:"id" db:"id"`
	BuildingID   uuid.UUID              `json:"building_id" db:"building_id"`
	Path         string                 `json:"path" db:"path"`
	Name         string                 `json:"name" db:"name"`
	Type         string                 `json:"type" db:"type"`
	Position     *Position              `json:"position,omitempty"`
	PositionLocal *Position             `json:"position_local,omitempty"`
	Confidence   int                    `json:"confidence" db:"confidence"`
	Status       string                 `json:"status" db:"status"`
	Metadata     map[string]interface{} `json:"metadata,omitempty" db:"metadata"`
	CreatedAt    time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at" db:"updated_at"`
}

// NewEquipment creates new equipment
func NewEquipment(buildingID uuid.UUID, path, name, equipType string) *Equipment {
	return &Equipment{
		ID:         uuid.New(),
		BuildingID: buildingID,
		Path:       path,
		Name:       name,
		Type:       equipType,
		Confidence: ConfidenceEstimated,
		Status:     StatusUnknown,
		Metadata:   make(map[string]interface{}),
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
}

// Validate checks if equipment data is valid
func (e *Equipment) Validate() error {
	if e.ID == uuid.Nil {
		return ErrInvalidID
	}
	if e.BuildingID == uuid.Nil {
		return errors.New("building_id is required")
	}
	if e.Path == "" {
		return errors.New("path is required")
	}
	if e.Name == "" {
		return errors.New("name is required")
	}
	if e.Type == "" {
		return errors.New("type is required")
	}
	if e.Confidence < 0 || e.Confidence > 3 {
		return errors.New("confidence must be between 0 and 3")
	}
	return nil
}

// Filter represents filtering options for equipment queries
type Filter struct {
	BuildingID uuid.UUID
	Type       string
	Status     string
	Limit      int
	Offset     int
}