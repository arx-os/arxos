package building

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/utils"
)

// FloorUseCase implements the floor business logic following Clean Architecture
type FloorUseCase struct {
	floorRepo     domain.FloorRepository
	roomRepo      domain.RoomRepository
	equipmentRepo domain.EquipmentRepository
	buildingRepo  domain.BuildingRepository
	logger        domain.Logger
	idGenerator   *utils.IDGenerator
}

// NewFloorUseCase creates a new FloorUseCase
func NewFloorUseCase(floorRepo domain.FloorRepository, buildingRepo domain.BuildingRepository, logger domain.Logger) *FloorUseCase {
	return &FloorUseCase{
		floorRepo:    floorRepo,
		buildingRepo: buildingRepo,
		logger:       logger,
		idGenerator:  utils.NewIDGenerator(),
	}
}

// SetRoomRepository injects the room repository (for avoiding circular dependencies)
func (uc *FloorUseCase) SetRoomRepository(roomRepo domain.RoomRepository) {
	uc.roomRepo = roomRepo
}

// SetEquipmentRepository injects the equipment repository (for avoiding circular dependencies)
func (uc *FloorUseCase) SetEquipmentRepository(equipmentRepo domain.EquipmentRepository) {
	uc.equipmentRepo = equipmentRepo
}

// CreateFloor creates a new floor in a building
func (uc *FloorUseCase) CreateFloor(ctx context.Context, req *domain.CreateFloorRequest) (*domain.Floor, error) {
	uc.logger.Info("Creating floor", "building_id", req.BuildingID.String(), "level", req.Level)

	// Validate building exists
	_, err := uc.buildingRepo.GetByID(ctx, req.BuildingID.String())
	if err != nil {
		uc.logger.Error("Building not found", "building_id", req.BuildingID.String(), "error", err)
		return nil, fmt.Errorf("building not found: %w", err)
	}

	// Validate request
	if err := uc.validateCreateFloor(req); err != nil {
		uc.logger.Error("Floor validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Create floor entity
	floor := &domain.Floor{
		ID:         uc.idGenerator.GenerateFloorID(req.BuildingID, req.Level),
		BuildingID: req.BuildingID,
		Name:       req.Name,
		Level:      req.Level,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	// Save to repository
	if err := uc.floorRepo.Create(ctx, floor); err != nil {
		uc.logger.Error("Failed to create floor", "error", err)
		return nil, fmt.Errorf("failed to create floor: %w", err)
	}

	uc.logger.Info("Floor created successfully", "floor_id", floor.ID.String())
	return floor, nil
}

// GetFloor retrieves a floor by ID
func (uc *FloorUseCase) GetFloor(ctx context.Context, id types.ID) (*domain.Floor, error) {
	uc.logger.Info("Getting floor", "floor_id", id.String())

	if id.IsEmpty() {
		return nil, fmt.Errorf("floor ID is required")
	}

	floor, err := uc.floorRepo.GetByID(ctx, id.String())
	if err != nil {
		uc.logger.Error("Failed to get floor", "floor_id", id.String(), "error", err)
		return nil, fmt.Errorf("failed to get floor: %w", err)
	}

	return floor, nil
}

// ListFloors lists all floors for a building
func (uc *FloorUseCase) ListFloors(ctx context.Context, buildingID types.ID, limit, offset int) ([]*domain.Floor, error) {
	uc.logger.Info("Listing floors", "building_id", buildingID.String())

	if buildingID.IsEmpty() {
		return nil, fmt.Errorf("building ID is required")
	}

	// Validate building exists
	_, err := uc.buildingRepo.GetByID(ctx, buildingID.String())
	if err != nil {
		return nil, fmt.Errorf("building not found: %w", err)
	}

	floors, err := uc.floorRepo.GetByBuilding(ctx, buildingID.String())
	if err != nil {
		uc.logger.Error("Failed to list floors", "building_id", buildingID.String(), "error", err)
		return nil, fmt.Errorf("failed to list floors: %w", err)
	}

	uc.logger.Info("Floors listed successfully", "count", len(floors))
	return floors, nil
}

// UpdateFloor updates an existing floor
func (uc *FloorUseCase) UpdateFloor(ctx context.Context, req *domain.UpdateFloorRequest) (*domain.Floor, error) {
	uc.logger.Info("Updating floor", "floor_id", req.ID.String())

	// Get existing floor
	floor, err := uc.floorRepo.GetByID(ctx, req.ID.String())
	if err != nil {
		return nil, fmt.Errorf("floor not found: %w", err)
	}

	// Update fields
	if req.Name != nil {
		floor.Name = *req.Name
	}
	if req.Level != nil {
		floor.Level = *req.Level
	}
	floor.UpdatedAt = time.Now()

	// Save changes
	if err := uc.floorRepo.Update(ctx, floor); err != nil {
		uc.logger.Error("Failed to update floor", "error", err)
		return nil, fmt.Errorf("failed to update floor: %w", err)
	}

	uc.logger.Info("Floor updated successfully", "floor_id", floor.ID.String())
	return floor, nil
}

// DeleteFloor deletes a floor
func (uc *FloorUseCase) DeleteFloor(ctx context.Context, id string) error {
	uc.logger.Info("Deleting floor", "floor_id", id)

	if id == "" {
		return fmt.Errorf("floor ID is required")
	}

	// Check if floor exists
	_, err := uc.floorRepo.GetByID(ctx, id)
	if err != nil {
		return fmt.Errorf("floor not found: %w", err)
	}

	if err := uc.floorRepo.Delete(ctx, id); err != nil {
		uc.logger.Error("Failed to delete floor", "error", err)
		return fmt.Errorf("failed to delete floor: %w", err)
	}

	uc.logger.Info("Floor deleted successfully", "floor_id", id)
	return nil
}

// GetFloorRooms retrieves all rooms for a floor
func (uc *FloorUseCase) GetFloorRooms(ctx context.Context, floorID types.ID) ([]*domain.Room, error) {
	uc.logger.Info("Getting floor rooms", "floor_id", floorID.String())

	if floorID.IsEmpty() {
		return nil, fmt.Errorf("floor ID is required")
	}

	if uc.roomRepo == nil {
		return nil, fmt.Errorf("room repository not initialized")
	}

	// Validate floor exists
	_, err := uc.floorRepo.GetByID(ctx, floorID.String())
	if err != nil {
		return nil, fmt.Errorf("floor not found: %w", err)
	}

	rooms, err := uc.roomRepo.GetByFloor(ctx, floorID.String())
	if err != nil {
		uc.logger.Error("Failed to get floor rooms", "floor_id", floorID.String(), "error", err)
		return nil, fmt.Errorf("failed to get floor rooms: %w", err)
	}

	uc.logger.Info("Floor rooms retrieved successfully", "count", len(rooms))
	return rooms, nil
}

// GetFloorEquipment retrieves all equipment for a floor
func (uc *FloorUseCase) GetFloorEquipment(ctx context.Context, floorID types.ID) ([]*domain.Equipment, error) {
	uc.logger.Info("Getting floor equipment", "floor_id", floorID.String())

	if floorID.IsEmpty() {
		return nil, fmt.Errorf("floor ID is required")
	}

	if uc.equipmentRepo == nil {
		return nil, fmt.Errorf("equipment repository not initialized")
	}

	// Validate floor exists
	_, err := uc.floorRepo.GetByID(ctx, floorID.String())
	if err != nil {
		return nil, fmt.Errorf("floor not found: %w", err)
	}

	equipment, err := uc.equipmentRepo.GetByFloor(ctx, floorID.String())
	if err != nil {
		uc.logger.Error("Failed to get floor equipment", "floor_id", floorID.String(), "error", err)
		return nil, fmt.Errorf("failed to get floor equipment: %w", err)
	}

	uc.logger.Info("Floor equipment retrieved successfully", "count", len(equipment))
	return equipment, nil
}

// validateCreateFloor validates floor creation request
func (uc *FloorUseCase) validateCreateFloor(req *domain.CreateFloorRequest) error {
	if req.BuildingID.IsEmpty() {
		return fmt.Errorf("building ID is required")
	}
	if req.Name == "" {
		return fmt.Errorf("floor name is required")
	}
	// Level can be negative (basement), zero (ground), or positive
	return nil
}
