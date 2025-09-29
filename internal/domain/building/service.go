package building

import (
	"context"
	"fmt"

	"github.com/google/uuid"
)

// service implements the building service following Clean Architecture principles
type service struct {
	repo Repository
}

// NewService creates a new building service with dependency injection
func NewService(repo Repository) Service {
	return &service{
		repo: repo,
	}
}

// CreateBuilding creates a new building
func (s *service) CreateBuilding(ctx context.Context, req CreateBuildingRequest) (*Building, error) {
	// Validate request
	if err := s.validateCreateRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check if building with ArxosID already exists
	existing, err := s.repo.GetByArxosID(ctx, req.ArxosID)
	if err == nil && existing != nil {
		return nil, ErrDuplicate
	}

	// Create building entity
	building := &Building{
		ID:       uuid.New(),
		ArxosID:  req.ArxosID,
		Name:     req.Name,
		Address:  req.Address,
		Origin:   req.Origin,
		Rotation: req.Rotation,
		Metadata: req.Metadata,
	}

	// Set timestamps
	building.SetCreatedAt()

	// Validate entity
	if err := building.Validate(); err != nil {
		return nil, fmt.Errorf("entity validation failed: %w", err)
	}

	// Save to repository
	if err := s.repo.Create(ctx, building); err != nil {
		return nil, fmt.Errorf("failed to create building: %w", err)
	}

	return building, nil
}

// GetBuilding retrieves a building by ID
func (s *service) GetBuilding(ctx context.Context, id uuid.UUID) (*Building, error) {
	building, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get building: %w", err)
	}
	if building == nil {
		return nil, ErrNotFound
	}
	return building, nil
}

// GetBuildingByArxosID retrieves a building by ArxosID
func (s *service) GetBuildingByArxosID(ctx context.Context, arxosID string) (*Building, error) {
	building, err := s.repo.GetByArxosID(ctx, arxosID)
	if err != nil {
		return nil, fmt.Errorf("failed to get building by arxos_id: %w", err)
	}
	if building == nil {
		return nil, ErrNotFound
	}
	return building, nil
}

// UpdateBuilding updates an existing building
func (s *service) UpdateBuilding(ctx context.Context, id uuid.UUID, req UpdateBuildingRequest) (*Building, error) {
	// Get existing building
	building, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get building: %w", err)
	}
	if building == nil {
		return nil, ErrNotFound
	}

	// Update fields if provided
	if req.Name != nil {
		building.Name = *req.Name
	}
	if req.Address != nil {
		building.Address = *req.Address
	}
	if req.Origin != nil {
		building.Origin = req.Origin
	}
	if req.Rotation != nil {
		building.Rotation = *req.Rotation
	}
	if req.Metadata != nil {
		building.Metadata = req.Metadata
	}

	// Set updated timestamp
	building.SetUpdatedAt()

	// Validate entity
	if err := building.Validate(); err != nil {
		return nil, fmt.Errorf("entity validation failed: %w", err)
	}

	// Save to repository
	if err := s.repo.Update(ctx, building); err != nil {
		return nil, fmt.Errorf("failed to update building: %w", err)
	}

	return building, nil
}

// DeleteBuilding deletes a building
func (s *service) DeleteBuilding(ctx context.Context, id uuid.UUID) error {
	// Check if building exists
	building, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get building: %w", err)
	}
	if building == nil {
		return ErrNotFound
	}

	// Delete from repository
	if err := s.repo.Delete(ctx, id); err != nil {
		return fmt.Errorf("failed to delete building: %w", err)
	}

	return nil
}

// ListBuildings lists buildings with pagination
func (s *service) ListBuildings(ctx context.Context, req ListBuildingsRequest) ([]*Building, error) {
	// Validate request
	if err := s.validateListRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	buildings, err := s.repo.List(ctx, req.Limit, req.Offset)
	if err != nil {
		return nil, fmt.Errorf("failed to list buildings: %w", err)
	}

	return buildings, nil
}

// SearchBuildings searches buildings by query
func (s *service) SearchBuildings(ctx context.Context, query string) ([]*Building, error) {
	if query == "" {
		return nil, fmt.Errorf("search query is required")
	}

	buildings, err := s.repo.Search(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to search buildings: %w", err)
	}

	return buildings, nil
}

// Helper methods for validation
func (s *service) validateCreateRequest(req CreateBuildingRequest) error {
	if req.ArxosID == "" {
		return fmt.Errorf("arxos_id is required")
	}
	if req.Name == "" {
		return fmt.Errorf("name is required")
	}
	return nil
}

func (s *service) validateListRequest(req ListBuildingsRequest) error {
	if req.Limit <= 0 {
		req.Limit = 10 // Default limit
	}
	if req.Limit > 100 {
		return fmt.Errorf("limit cannot exceed 100")
	}
	if req.Offset < 0 {
		req.Offset = 0
	}
	return nil
}
