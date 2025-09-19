package building

import (
	"errors"
	"time"

	"github.com/google/uuid"
)

var (
	// ErrNotFound is returned when a building is not found
	ErrNotFound = errors.New("building not found")
	// ErrInvalidID is returned when a building ID is invalid
	ErrInvalidID = errors.New("invalid building ID")
	// ErrDuplicate is returned when trying to create a duplicate building
	ErrDuplicate = errors.New("building already exists")
)

// GPSCoordinate represents WGS84 GPS coordinates
type GPSCoordinate struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Altitude  float64 `json:"altitude,omitempty"`
}

// Building represents a building entity in the domain
type Building struct {
	ID        uuid.UUID              `json:"id" db:"id"`
	ArxosID   string                 `json:"arxos_id" db:"arxos_id"`
	Name      string                 `json:"name" db:"name"`
	Address   string                 `json:"address,omitempty" db:"address"`
	Origin    GPSCoordinate          `json:"origin"`
	Rotation  float64                `json:"rotation" db:"rotation"` // degrees from north
	Metadata  map[string]interface{} `json:"metadata,omitempty" db:"metadata"`
	CreatedAt time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt time.Time              `json:"updated_at" db:"updated_at"`
}

// NewBuilding creates a new building with generated ID
func NewBuilding(arxosID, name string) *Building {
	return &Building{
		ID:        uuid.New(),
		ArxosID:   arxosID,
		Name:      name,
		Metadata:  make(map[string]interface{}),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// Validate checks if the building data is valid
func (b *Building) Validate() error {
	if b.ArxosID == "" {
		return errors.New("arxos_id is required")
	}
	if b.Name == "" {
		return errors.New("name is required")
	}
	if b.ID == uuid.Nil {
		return ErrInvalidID
	}
	return nil
}

// SetOrigin sets the GPS origin point for the building
func (b *Building) SetOrigin(lat, lon, alt float64) {
	b.Origin = GPSCoordinate{
		Latitude:  lat,
		Longitude: lon,
		Altitude:  alt,
	}
	b.UpdatedAt = time.Now()
}

// Filter represents filtering options for building queries
type Filter struct {
	Name   string
	Limit  int
	Offset int
}