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

// ConfidenceLevel represents confidence in position data
type ConfidenceLevel int

// Confidence levels for spatial data
const (
	ConfidenceUnknown   ConfidenceLevel = -1 // Unknown confidence level
	ConfidenceEstimated ConfidenceLevel = 0  // Derived from PDF/IFC without verification
	ConfidenceLow       ConfidenceLevel = 1  // Automated detection
	ConfidenceMedium    ConfidenceLevel = 2  // Partial verification
	ConfidenceHigh      ConfidenceLevel = 3  // LiDAR or AR verified
	ConfidenceScanned   ConfidenceLevel = 4  // Scanned data
	ConfidenceSurveyed  ConfidenceLevel = 5  // Professionally surveyed
)

// String returns the string representation of confidence level
func (c ConfidenceLevel) String() string {
	switch c {
	case ConfidenceUnknown:
		return "unknown"
	case ConfidenceEstimated:
		return "estimated"
	case ConfidenceLow:
		return "low"
	case ConfidenceMedium:
		return "medium"
	case ConfidenceHigh:
		return "high"
	case ConfidenceScanned:
		return "scanned"
	case ConfidenceSurveyed:
		return "surveyed"
	default:
		return "unknown"
	}
}

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

// IsValid checks if position coordinates are valid
func (p *Position) IsValid() bool {
	if p == nil {
		return false
	}
	// Check for reasonable coordinate ranges
	// Longitude: -180 to 180, Latitude: -90 to 90
	if p.X < -180 || p.X > 180 {
		return false
	}
	if p.Y < -90 || p.Y > 90 {
		return false
	}
	return true
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
	Confidence   ConfidenceLevel        `json:"confidence" db:"confidence"`
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
		Confidence: ConfidenceUnknown,
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
		return errors.New("building ID is required")
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
	// Validate status
	validStatuses := []string{StatusUnknown, StatusOperational, StatusDegraded, StatusFailed, StatusMaintenance, StatusOffline}
	isValidStatus := false
	for _, status := range validStatuses {
		if e.Status == status {
			isValidStatus = true
			break
		}
	}
	if !isValidStatus {
		return errors.New("invalid status")
	}
	if e.Confidence < ConfidenceUnknown || e.Confidence > ConfidenceSurveyed {
		return errors.New("invalid confidence level")
	}
	return nil
}

// SetPosition sets the position and confidence for equipment
func (e *Equipment) SetPosition(pos *Position, confidence ConfidenceLevel) {
	e.Position = pos
	e.Confidence = confidence
	e.UpdatedAt = time.Now()
}

// HasPosition returns true if equipment has a position set
func (e *Equipment) HasPosition() bool {
	return e.Position != nil
}

// IsOperational returns true if equipment is operational
func (e *Equipment) IsOperational() bool {
	return e.Status == StatusOperational
}

// NeedsAttention returns true if equipment needs attention
func (e *Equipment) NeedsAttention() bool {
	return e.Status == StatusFailed || e.Status == StatusDegraded || e.Status == StatusMaintenance
}

// Filter represents filtering options for equipment queries
type Filter struct {
	BuildingID uuid.UUID
	Type       string
	Status     string
	Limit      int
	Offset     int
}