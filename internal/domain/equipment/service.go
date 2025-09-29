package equipment

import (
	"context"
	"time"

	"github.com/google/uuid"
)

// Service defines the interface for equipment business logic following Clean Architecture principles
type Service interface {
	CreateEquipment(ctx context.Context, req CreateEquipmentRequest) (*Equipment, error)
	GetEquipment(ctx context.Context, id uuid.UUID) (*Equipment, error)
	UpdateEquipment(ctx context.Context, id uuid.UUID, req UpdateEquipmentRequest) (*Equipment, error)
	DeleteEquipment(ctx context.Context, id uuid.UUID) error
	ListEquipment(ctx context.Context, req ListEquipmentRequest) ([]*Equipment, error)
	SearchEquipment(ctx context.Context, query string) ([]*Equipment, error)
}

// Equipment represents an equipment entity
type Equipment struct {
	ID        uuid.UUID              `json:"id"`
	Name      string                 `json:"name"`
	Type      string                 `json:"type"`
	Location  *Location              `json:"location"`
	Metadata  map[string]interface{} `json:"metadata"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

// Location represents equipment location
type Location struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// CreateEquipmentRequest represents a request to create equipment
type CreateEquipmentRequest struct {
	Name     string                 `json:"name" validate:"required"`
	Type     string                 `json:"type" validate:"required"`
	Location *Location              `json:"location"`
	Metadata map[string]interface{} `json:"metadata"`
}

// UpdateEquipmentRequest represents a request to update equipment
type UpdateEquipmentRequest struct {
	Name     *string                `json:"name,omitempty"`
	Type     *string                `json:"type,omitempty"`
	Location *Location              `json:"location,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// ListEquipmentRequest represents a request to list equipment
type ListEquipmentRequest struct {
	Limit  int `json:"limit" validate:"min=1,max=100"`
	Offset int `json:"offset" validate:"min=0"`
}
