package equipment

import (
	"context"

	"github.com/google/uuid"
)

// Repository defines the interface for equipment persistence
type Repository interface {
	// Create creates new equipment
	Create(ctx context.Context, equipment *Equipment) error

	// GetByID retrieves equipment by UUID
	GetByID(ctx context.Context, id uuid.UUID) (*Equipment, error)

	// GetByPath retrieves equipment by building ID and path
	GetByPath(ctx context.Context, buildingID uuid.UUID, path string) (*Equipment, error)

	// Update updates existing equipment
	Update(ctx context.Context, equipment *Equipment) error

	// Delete deletes equipment by ID
	Delete(ctx context.Context, id uuid.UUID) error

	// List retrieves equipment with optional filtering
	List(ctx context.Context, filter Filter) ([]*Equipment, error)

	// FindNearby finds equipment within radius of a point
	FindNearby(ctx context.Context, center Position, radiusMeters float64) ([]*Equipment, error)

	// FindInBuilding finds all equipment in a building
	FindInBuilding(ctx context.Context, buildingID uuid.UUID) ([]*Equipment, error)
}