package building

import (
	"context"
	"fmt"

	"github.com/google/uuid"
)

// Service provides business logic for building operations
type Service struct {
	repo Repository
}

// NewService creates a new building service
func NewService(repo Repository) *Service {
	return &Service{repo: repo}
}

// CreateBuilding creates a new building
func (s *Service) CreateBuilding(ctx context.Context, arxosID, name, address string) (*Building, error) {
	// Check if building already exists
	existing, err := s.repo.GetByArxosID(ctx, arxosID)
	if err == nil && existing != nil {
		return nil, ErrDuplicate
	}

	// Create new building
	building := NewBuilding(arxosID, name)
	building.Address = address

	// Validate
	if err := building.Validate(); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Save to repository
	if err := s.repo.Create(ctx, building); err != nil {
		return nil, fmt.Errorf("failed to create building: %w", err)
	}

	return building, nil
}

// GetBuilding retrieves a building by ID
func (s *Service) GetBuilding(ctx context.Context, id uuid.UUID) (*Building, error) {
	return s.repo.GetByID(ctx, id)
}

// GetBuildingByArxosID retrieves a building by ArxOS ID
func (s *Service) GetBuildingByArxosID(ctx context.Context, arxosID string) (*Building, error) {
	return s.repo.GetByArxosID(ctx, arxosID)
}

// UpdateBuilding updates an existing building
func (s *Service) UpdateBuilding(ctx context.Context, building *Building) error {
	// Validate
	if err := building.Validate(); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	return s.repo.Update(ctx, building)
}

// DeleteBuilding deletes a building
func (s *Service) DeleteBuilding(ctx context.Context, id uuid.UUID) error {
	return s.repo.Delete(ctx, id)
}

// ListBuildings lists buildings with optional filtering
func (s *Service) ListBuildings(ctx context.Context, filter Filter) ([]*Building, error) {
	return s.repo.List(ctx, filter)
}

// FindNearbyBuildings finds buildings near a location
func (s *Service) FindNearbyBuildings(ctx context.Context, lat, lon float64, radiusMeters float64) ([]*Building, error) {
	if radiusMeters <= 0 {
		return nil, fmt.Errorf("radius must be positive")
	}

	if lat < -90 || lat > 90 {
		return nil, fmt.Errorf("invalid latitude")
	}

	if lon < -180 || lon > 180 {
		return nil, fmt.Errorf("invalid longitude")
	}

	return s.repo.FindNearby(ctx, lon, lat, radiusMeters)
}

// SetBuildingOrigin sets the GPS origin for a building
func (s *Service) SetBuildingOrigin(ctx context.Context, id uuid.UUID, lat, lon, alt float64) error {
	building, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return err
	}

	building.SetOrigin(lat, lon, alt)
	return s.repo.Update(ctx, building)
}