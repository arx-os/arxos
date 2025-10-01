package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// BuildingUseCase implements the building business logic following Clean Architecture
type BuildingUseCase struct {
	buildingRepo  domain.BuildingRepository
	equipmentRepo domain.EquipmentRepository
	logger        domain.Logger
}

// NewBuildingUseCase creates a new BuildingUseCase
func NewBuildingUseCase(buildingRepo domain.BuildingRepository, equipmentRepo domain.EquipmentRepository, logger domain.Logger) *BuildingUseCase {
	return &BuildingUseCase{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		logger:        logger,
	}
}

// CreateBuilding creates a new building
func (uc *BuildingUseCase) CreateBuilding(ctx context.Context, req *domain.CreateBuildingRequest) (*domain.Building, error) {
	uc.logger.Info("Creating building", "name", req.Name)

	// Validate business rules
	if err := uc.validateCreateBuilding(req); err != nil {
		uc.logger.Error("Building validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Create building entity
	building := &domain.Building{
		ID:          uc.generateBuildingID(),
		Name:        req.Name,
		Address:     req.Address,
		Coordinates: req.Coordinates,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Save to repository
	if err := uc.buildingRepo.Create(ctx, building); err != nil {
		uc.logger.Error("Failed to create building", "error", err)
		return nil, fmt.Errorf("failed to create building: %w", err)
	}

	uc.logger.Info("Building created successfully", "building_id", building.ID)
	return building, nil
}

// GetBuilding retrieves a building by ID
func (uc *BuildingUseCase) GetBuilding(ctx context.Context, id string) (*domain.Building, error) {
	uc.logger.Info("Getting building", "building_id", id)

	if id == "" {
		return nil, fmt.Errorf("building ID is required")
	}

	building, err := uc.buildingRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get building", "building_id", id, "error", err)
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	return building, nil
}

// UpdateBuilding updates an existing building
func (uc *BuildingUseCase) UpdateBuilding(ctx context.Context, req *domain.UpdateBuildingRequest) (*domain.Building, error) {
	uc.logger.Info("Updating building", "building_id", req.ID)

	// Get existing building
	building, err := uc.buildingRepo.GetByID(ctx, req.ID)
	if err != nil {
		uc.logger.Error("Failed to get building for update", "building_id", req.ID, "error", err)
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	// Update fields if provided
	if req.Name != nil {
		building.Name = *req.Name
	}
	if req.Address != nil {
		building.Address = *req.Address
	}
	if req.Coordinates != nil {
		building.Coordinates = req.Coordinates
	}
	building.UpdatedAt = time.Now()

	// Validate business rules
	if err := uc.validateUpdateBuilding(building); err != nil {
		uc.logger.Error("Building validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Save to repository
	if err := uc.buildingRepo.Update(ctx, building); err != nil {
		uc.logger.Error("Failed to update building", "building_id", req.ID, "error", err)
		return nil, fmt.Errorf("failed to update building: %w", err)
	}

	uc.logger.Info("Building updated successfully", "building_id", building.ID)
	return building, nil
}

// DeleteBuilding deletes a building
func (uc *BuildingUseCase) DeleteBuilding(ctx context.Context, id string) error {
	uc.logger.Info("Deleting building", "building_id", id)

	if id == "" {
		return fmt.Errorf("building ID is required")
	}

	// Check if building exists
	_, err := uc.buildingRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get building for deletion", "building_id", id, "error", err)
		return fmt.Errorf("failed to get building: %w", err)
	}

	// Business rule: Check if building has equipment
	equipment, err := uc.equipmentRepo.GetByBuilding(ctx, id)
	if err == nil && len(equipment) > 0 {
		return fmt.Errorf("cannot delete building with existing equipment")
	}

	// Delete from repository
	if err := uc.buildingRepo.Delete(ctx, id); err != nil {
		uc.logger.Error("Failed to delete building", "building_id", id, "error", err)
		return fmt.Errorf("failed to delete building: %w", err)
	}

	uc.logger.Info("Building deleted successfully", "building_id", id)
	return nil
}

// ListBuildings retrieves a list of buildings with optional filtering
func (uc *BuildingUseCase) ListBuildings(ctx context.Context, filter *domain.BuildingFilter) ([]*domain.Building, error) {
	uc.logger.Info("Listing buildings", "filter", filter)

	// Set default pagination if not provided
	if filter.Limit <= 0 {
		filter.Limit = 100
	}

	buildings, err := uc.buildingRepo.List(ctx, filter)
	if err != nil {
		uc.logger.Error("Failed to list buildings", "error", err)
		return nil, fmt.Errorf("failed to list buildings: %w", err)
	}

	uc.logger.Info("Buildings listed successfully", "count", len(buildings))
	return buildings, nil
}

// ImportBuilding imports a building from external data
func (uc *BuildingUseCase) ImportBuilding(ctx context.Context, req *domain.ImportBuildingRequest) (*domain.Building, error) {
	uc.logger.Info("Importing building", "format", req.Format)

	// TODO: Implement building import logic based on format
	// This would typically involve:
	// 1. Parse the data based on format (IFC, PDF, etc.)
	// 2. Validate the parsed data
	// 3. Create building entity
	// 4. Save to repository

	return nil, fmt.Errorf("building import not implemented for format: %s", req.Format)
}

// ExportBuilding exports a building to external format
func (uc *BuildingUseCase) ExportBuilding(ctx context.Context, id, format string) ([]byte, error) {
	uc.logger.Info("Exporting building", "building_id", id, "format", format)

	// Get building
	_, err := uc.buildingRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get building for export", "building_id", id, "error", err)
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	// TODO: Implement building export logic based on format
	// This would typically involve:
	// 1. Get building data and related entities
	// 2. Convert to target format
	// 3. Return serialized data

	return nil, fmt.Errorf("building export not implemented for format: %s", format)
}

// Private helper methods

func (uc *BuildingUseCase) validateCreateBuilding(req *domain.CreateBuildingRequest) error {
	if req.Name == "" {
		return fmt.Errorf("building name is required")
	}
	if req.Address == "" {
		return fmt.Errorf("building address is required")
	}

	return nil
}

func (uc *BuildingUseCase) validateUpdateBuilding(building *domain.Building) error {
	if building.Name == "" {
		return fmt.Errorf("building name cannot be empty")
	}
	if building.Address == "" {
		return fmt.Errorf("building address cannot be empty")
	}

	return nil
}

func (uc *BuildingUseCase) generateBuildingID() string {
	// TODO: Implement proper ID generation (UUID, etc.)
	return fmt.Sprintf("building_%d", time.Now().UnixNano())
}
