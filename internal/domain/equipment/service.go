package equipment

import (
	"context"

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
