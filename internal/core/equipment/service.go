package equipment

import (
	"context"
	"fmt"

	"github.com/google/uuid"
)

// Service provides business logic for equipment operations
type Service struct {
	repo Repository
}

// NewService creates a new equipment service
func NewService(repo Repository) *Service {
	return &Service{repo: repo}
}

// CreateEquipment creates new equipment
func (s *Service) CreateEquipment(ctx context.Context, buildingID uuid.UUID, path, name, equipType string) (*Equipment, error) {
	// Check if equipment already exists
	existing, err := s.repo.GetByPath(ctx, buildingID, path)
	if err == nil && existing != nil {
		return nil, ErrDuplicate
	}

	// Create new equipment
	equipment := NewEquipment(buildingID, path, name, equipType)

	// Validate
	if err := equipment.Validate(); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Save to repository
	if err := s.repo.Create(ctx, equipment); err != nil {
		return nil, fmt.Errorf("failed to create equipment: %w", err)
	}

	return equipment, nil
}

// GetEquipment retrieves equipment by ID
func (s *Service) GetEquipment(ctx context.Context, id uuid.UUID) (*Equipment, error) {
	return s.repo.GetByID(ctx, id)
}

// GetEquipmentByPath retrieves equipment by building ID and path
func (s *Service) GetEquipmentByPath(ctx context.Context, buildingID uuid.UUID, path string) (*Equipment, error) {
	return s.repo.GetByPath(ctx, buildingID, path)
}

// UpdateEquipment updates existing equipment
func (s *Service) UpdateEquipment(ctx context.Context, equipment *Equipment) error {
	// Validate
	if err := equipment.Validate(); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	return s.repo.Update(ctx, equipment)
}

// UpdateEquipmentStatus updates equipment status
func (s *Service) UpdateEquipmentStatus(ctx context.Context, id uuid.UUID, status string) error {
	equipment, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return err
	}

	equipment.Status = status
	return s.repo.Update(ctx, equipment)
}

// UpdateEquipmentPosition updates equipment position with confidence level
func (s *Service) UpdateEquipmentPosition(ctx context.Context, id uuid.UUID, position Position, confidence int) error {
	equipment, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return err
	}

	equipment.Position = &position
	equipment.Confidence = confidence
	return s.repo.Update(ctx, equipment)
}

// DeleteEquipment deletes equipment
func (s *Service) DeleteEquipment(ctx context.Context, id uuid.UUID) error {
	return s.repo.Delete(ctx, id)
}

// ListEquipment lists equipment with optional filtering
func (s *Service) ListEquipment(ctx context.Context, filter Filter) ([]*Equipment, error) {
	return s.repo.List(ctx, filter)
}

// FindNearbyEquipment finds equipment near a location
func (s *Service) FindNearbyEquipment(ctx context.Context, center Position, radiusMeters float64) ([]*Equipment, error) {
	if radiusMeters <= 0 {
		return nil, fmt.Errorf("radius must be positive")
	}

	return s.repo.FindNearby(ctx, center, radiusMeters)
}

// FindBuildingEquipment finds all equipment in a building
func (s *Service) FindBuildingEquipment(ctx context.Context, buildingID uuid.UUID) ([]*Equipment, error) {
	return s.repo.FindInBuilding(ctx, buildingID)
}