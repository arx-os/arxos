package equipment

import (
	"context"
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

// Equipment represents a piece of equipment in a building
type Equipment struct {
	ID        uuid.UUID              `json:"id" db:"id"`
	Name      string                 `json:"name" db:"name"`
	Type      string                 `json:"type" db:"type"`
	Tag       string                 `json:"tag" db:"tag"`
	Location  *Location              `json:"location" db:"location"`
	Status    string                 `json:"status" db:"status"`
	Metadata  map[string]interface{} `json:"metadata" db:"metadata"`
	CreatedAt time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt time.Time              `json:"updated_at" db:"updated_at"`
}

// Location represents equipment location
type Location struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// Repository defines the interface for equipment persistence
type Repository interface {
	// Create creates a new equipment
	Create(ctx context.Context, equipment *Equipment) error

	// GetByID retrieves equipment by its UUID
	GetByID(ctx context.Context, id uuid.UUID) (*Equipment, error)

	// GetByTag retrieves equipment by its tag
	GetByTag(ctx context.Context, tag string) (*Equipment, error)

	// Update updates an existing equipment
	Update(ctx context.Context, equipment *Equipment) error

	// Delete deletes equipment by ID
	Delete(ctx context.Context, id uuid.UUID) error

	// List retrieves equipment with optional filtering
	List(ctx context.Context, filter Filter) ([]*Equipment, error)

	// FindNearby finds equipment within a radius of a point
	FindNearby(ctx context.Context, x, y, z float64, radiusMeters float64) ([]*Equipment, error)
}

// Filter represents filtering options for equipment queries
type Filter struct {
	Type     string    `json:"type,omitempty"`
	Status   string    `json:"status,omitempty"`
	Location *Location `json:"location,omitempty"`
	Radius   float64   `json:"radius,omitempty"`
	Limit    int       `json:"limit,omitempty"`
	Offset   int       `json:"offset,omitempty"`
}

// SetCreatedAt sets the created at timestamp
func (e *Equipment) SetCreatedAt() {
	e.CreatedAt = time.Now()
}

// SetUpdatedAt sets the updated at timestamp
func (e *Equipment) SetUpdatedAt() {
	e.UpdatedAt = time.Now()
}

// Validate validates the equipment entity
func (e *Equipment) Validate() error {
	if e.Name == "" {
		return errors.New("name is required")
	}
	if e.Type == "" {
		return errors.New("type is required")
	}
	return nil
}

// NewEquipment creates a new equipment with default values
func NewEquipment(name, equipmentType, tag string) *Equipment {
	return &Equipment{
		ID:       uuid.New(),
		Name:     name,
		Type:     equipmentType,
		Tag:      tag,
		Status:   "operational",
		Metadata: make(map[string]interface{}),
	}
}
