package building

import (
	"context"

	"github.com/google/uuid"
)

// Repository defines the interface for building persistence
type Repository interface {
	// Create creates a new building
	Create(ctx context.Context, building *Building) error

	// GetByID retrieves a building by its UUID
	GetByID(ctx context.Context, id uuid.UUID) (*Building, error)

	// GetByArxosID retrieves a building by its ArxOS ID
	GetByArxosID(ctx context.Context, arxosID string) (*Building, error)

	// Update updates an existing building
	Update(ctx context.Context, building *Building) error

	// Delete deletes a building by ID
	Delete(ctx context.Context, id uuid.UUID) error

	// List retrieves buildings with optional filtering
	List(ctx context.Context, filter Filter) ([]*Building, error)

	// FindNearby finds buildings within a radius of a point
	FindNearby(ctx context.Context, lon, lat float64, radiusMeters float64) ([]*Building, error)
}