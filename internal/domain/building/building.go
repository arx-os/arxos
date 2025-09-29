package building

import (
	"context"
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

// Building represents a building entity in the domain following Clean Architecture principles
type Building struct {
	ID        uuid.UUID              `json:"id" db:"id"`
	ArxosID   string                 `json:"arxos_id" db:"arxos_id"`
	Name      string                 `json:"name" db:"name"`
	Address   string                 `json:"address" db:"address"`
	Origin    *GPSCoordinate         `json:"origin" db:"origin"`
	Rotation  float64                `json:"rotation" db:"rotation"`
	Metadata  map[string]interface{} `json:"metadata" db:"metadata"`
	CreatedAt time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt time.Time              `json:"updated_at" db:"updated_at"`
}

// Repository defines the interface for building data access following Clean Architecture principles
type Repository interface {
	Create(ctx context.Context, building *Building) error
	GetByID(ctx context.Context, id uuid.UUID) (*Building, error)
	GetByArxosID(ctx context.Context, arxosID string) (*Building, error)
	Update(ctx context.Context, building *Building) error
	Delete(ctx context.Context, id uuid.UUID) error
	List(ctx context.Context, limit, offset int) ([]*Building, error)
	Search(ctx context.Context, query string) ([]*Building, error)
}

// Service defines the interface for building business logic following Clean Architecture principles
type Service interface {
	CreateBuilding(ctx context.Context, req CreateBuildingRequest) (*Building, error)
	GetBuilding(ctx context.Context, id uuid.UUID) (*Building, error)
	GetBuildingByArxosID(ctx context.Context, arxosID string) (*Building, error)
	UpdateBuilding(ctx context.Context, id uuid.UUID, req UpdateBuildingRequest) (*Building, error)
	DeleteBuilding(ctx context.Context, id uuid.UUID) error
	ListBuildings(ctx context.Context, req ListBuildingsRequest) ([]*Building, error)
	SearchBuildings(ctx context.Context, query string) ([]*Building, error)
}

// CreateBuildingRequest represents a request to create a building
type CreateBuildingRequest struct {
	ArxosID  string                 `json:"arxos_id" validate:"required"`
	Name     string                 `json:"name" validate:"required"`
	Address  string                 `json:"address"`
	Origin   *GPSCoordinate         `json:"origin"`
	Rotation float64                `json:"rotation"`
	Metadata map[string]interface{} `json:"metadata"`
}

// UpdateBuildingRequest represents a request to update a building
type UpdateBuildingRequest struct {
	Name     *string                `json:"name,omitempty"`
	Address  *string                `json:"address,omitempty"`
	Origin   *GPSCoordinate         `json:"origin,omitempty"`
	Rotation *float64               `json:"rotation,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// ListBuildingsRequest represents a request to list buildings
type ListBuildingsRequest struct {
	Limit  int `json:"limit" validate:"min=1,max=100"`
	Offset int `json:"offset" validate:"min=0"`
}

// Validate validates the building entity
func (b *Building) Validate() error {
	if b.ArxosID == "" {
		return errors.New("arxos_id is required")
	}
	if b.Name == "" {
		return errors.New("name is required")
	}
	return nil
}

// SetUpdatedAt updates the UpdatedAt timestamp
func (b *Building) SetUpdatedAt() {
	b.UpdatedAt = time.Now()
}

// SetCreatedAt sets the CreatedAt timestamp
func (b *Building) SetCreatedAt() {
	now := time.Now()
	b.CreatedAt = now
	b.UpdatedAt = now
}
