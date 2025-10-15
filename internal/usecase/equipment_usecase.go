package usecase

import (
	"context"
	"fmt"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure/utils"
	"github.com/arx-os/arxos/pkg/naming"
)

// EquipmentUseCase implements the equipment business logic following Clean Architecture
type EquipmentUseCase struct {
	equipmentRepo domain.EquipmentRepository
	buildingRepo  domain.BuildingRepository
	floorRepo     domain.FloorRepository
	roomRepo      domain.RoomRepository
	logger        domain.Logger
	idGenerator   *utils.IDGenerator
}

// NewEquipmentUseCase creates a new EquipmentUseCase
func NewEquipmentUseCase(equipmentRepo domain.EquipmentRepository, buildingRepo domain.BuildingRepository, floorRepo domain.FloorRepository, roomRepo domain.RoomRepository, logger domain.Logger) *EquipmentUseCase {
	return &EquipmentUseCase{
		equipmentRepo: equipmentRepo,
		buildingRepo:  buildingRepo,
		floorRepo:     floorRepo,
		roomRepo:      roomRepo,
		logger:        logger,
		idGenerator:   utils.NewIDGenerator(),
	}
}

// GetRepository returns the equipment repository
// This allows handlers to access repository methods directly for simple queries
func (uc *EquipmentUseCase) GetRepository() domain.EquipmentRepository {
	return uc.equipmentRepo
}

// CreateEquipment creates new equipment
func (uc *EquipmentUseCase) CreateEquipment(ctx context.Context, req *domain.CreateEquipmentRequest) (*domain.Equipment, error) {
	uc.logger.Info("Creating equipment", "name", req.Name, "building_id", req.BuildingID)

	// Validate business rules
	if err := uc.validateCreateEquipment(req); err != nil {
		uc.logger.Error("Equipment validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Verify building exists
	building, err := uc.buildingRepo.GetByID(ctx, req.BuildingID.String())
	if err != nil {
		uc.logger.Error("Failed to verify building exists", "building_id", req.BuildingID.String(), "error", err)
		return nil, fmt.Errorf("building not found: %w", err)
	}

	// Generate universal path
	equipmentPath := ""
	if !req.FloorID.IsEmpty() && !req.RoomID.IsEmpty() {
		// Get floor and room details for path generation
		floor, err := uc.floorRepo.GetByID(ctx, req.FloorID.String())
		if err == nil {
			room, err := uc.roomRepo.GetByID(ctx, req.RoomID.String())
			if err == nil {
				// Generate path components
				buildingCode := naming.BuildingCodeFromName(building.Name)
				floorCode := strconv.Itoa(floor.Level)
				roomCode := naming.RoomCodeFromName(room.Number)
				systemCode := naming.GetSystemCode(req.Type)
				equipmentCode := naming.GenerateEquipmentCode(req.Name, "")

				// Generate full path
				equipmentPath = naming.GenerateEquipmentPath(
					buildingCode,
					floorCode,
					roomCode,
					systemCode,
					equipmentCode,
				)

				uc.logger.Info("Generated equipment path", "path", equipmentPath)
			}
		}
	} else if !req.FloorID.IsEmpty() {
		// Floor-level equipment (no room)
		floor, err := uc.floorRepo.GetByID(ctx, req.FloorID.String())
		if err == nil {
			buildingCode := naming.BuildingCodeFromName(building.Name)
			floorCode := strconv.Itoa(floor.Level)
			systemCode := naming.GetSystemCode(req.Type)
			equipmentCode := naming.GenerateEquipmentCode(req.Name, "")

			equipmentPath = naming.GenerateEquipmentPath(
				buildingCode,
				floorCode,
				"", // No room
				systemCode,
				equipmentCode,
			)

			uc.logger.Info("Generated floor-level equipment path", "path", equipmentPath)
		}
	}

	// Create equipment entity
	equipment := &domain.Equipment{
		ID:         uc.idGenerator.GenerateEquipmentID(req.Name),
		BuildingID: req.BuildingID,
		FloorID:    req.FloorID,
		RoomID:     req.RoomID,
		Name:       req.Name,
		Path:       equipmentPath, // Store generated path
		Type:       req.Type,
		Model:      req.Model,
		Location:   req.Location,
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	// Save to repository
	if err := uc.equipmentRepo.Create(ctx, equipment); err != nil {
		uc.logger.Error("Failed to create equipment", "error", err)
		return nil, fmt.Errorf("failed to create equipment: %w", err)
	}

	uc.logger.Info("Equipment created successfully", "equipment_id", equipment.ID)
	return equipment, nil
}

// GetEquipment retrieves equipment by ID
func (uc *EquipmentUseCase) GetEquipment(ctx context.Context, id string) (*domain.Equipment, error) {
	uc.logger.Info("Getting equipment", "equipment_id", id)

	if id == "" {
		return nil, fmt.Errorf("equipment ID is required")
	}

	equipment, err := uc.equipmentRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get equipment", "equipment_id", id, "error", err)
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	return equipment, nil
}

// UpdateEquipment updates existing equipment
func (uc *EquipmentUseCase) UpdateEquipment(ctx context.Context, req *domain.UpdateEquipmentRequest) (*domain.Equipment, error) {
	uc.logger.Info("Updating equipment", "equipment_id", req.ID)

	// Get existing equipment
	equipment, err := uc.equipmentRepo.GetByID(ctx, req.ID.String())
	if err != nil {
		uc.logger.Error("Failed to get equipment for update", "equipment_id", req.ID.String(), "error", err)
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	// Update fields if provided
	if req.Name != nil {
		equipment.Name = *req.Name
	}
	if req.Type != nil {
		equipment.Type = *req.Type
	}
	if req.Model != nil {
		equipment.Model = *req.Model
	}
	if req.Location != nil {
		equipment.Location = req.Location
	}
	if req.Status != nil {
		equipment.Status = *req.Status
	}
	equipment.UpdatedAt = time.Now()

	// Validate business rules
	if err := uc.validateUpdateEquipment(equipment); err != nil {
		uc.logger.Error("Equipment validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Save to repository
	if err := uc.equipmentRepo.Update(ctx, equipment); err != nil {
		uc.logger.Error("Failed to update equipment", "equipment_id", req.ID, "error", err)
		return nil, fmt.Errorf("failed to update equipment: %w", err)
	}

	uc.logger.Info("Equipment updated successfully", "equipment_id", equipment.ID)
	return equipment, nil
}

// DeleteEquipment deletes equipment
func (uc *EquipmentUseCase) DeleteEquipment(ctx context.Context, id string) error {
	uc.logger.Info("Deleting equipment", "equipment_id", id)

	if id == "" {
		return fmt.Errorf("equipment ID is required")
	}

	// Check if equipment exists
	equipment, err := uc.equipmentRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get equipment for deletion", "equipment_id", id, "error", err)
		return fmt.Errorf("failed to get equipment: %w", err)
	}

	// Business rule: Don't allow deletion of equipment with active status
	if equipment.Status == "active" {
		return fmt.Errorf("cannot delete equipment with active status")
	}

	// Delete from repository
	if err := uc.equipmentRepo.Delete(ctx, id); err != nil {
		uc.logger.Error("Failed to delete equipment", "equipment_id", id, "error", err)
		return fmt.Errorf("failed to delete equipment: %w", err)
	}

	uc.logger.Info("Equipment deleted successfully", "equipment_id", id)
	return nil
}

// ListEquipment retrieves a list of equipment with optional filtering
func (uc *EquipmentUseCase) ListEquipment(ctx context.Context, filter *domain.EquipmentFilter) ([]*domain.Equipment, error) {
	uc.logger.Info("Listing equipment", "filter", filter)

	// Set default pagination if not provided
	if filter.Limit <= 0 {
		filter.Limit = 100
	}

	equipment, err := uc.equipmentRepo.List(ctx, filter)
	if err != nil {
		uc.logger.Error("Failed to list equipment", "error", err)
		return nil, fmt.Errorf("failed to list equipment: %w", err)
	}

	uc.logger.Info("Equipment listed successfully", "count", len(equipment))
	return equipment, nil
}

// MoveEquipment moves equipment to a new location
func (uc *EquipmentUseCase) MoveEquipment(ctx context.Context, id string, newLocation *domain.Location) error {
	uc.logger.Info("Moving equipment", "equipment_id", id, "new_location", newLocation)

	// Get existing equipment
	equipment, err := uc.equipmentRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get equipment for move", "equipment_id", id, "error", err)
		return fmt.Errorf("failed to get equipment: %w", err)
	}

	// Update location
	equipment.Location = newLocation
	equipment.UpdatedAt = time.Now()

	// Save to repository
	if err := uc.equipmentRepo.Update(ctx, equipment); err != nil {
		uc.logger.Error("Failed to move equipment", "equipment_id", id, "error", err)
		return fmt.Errorf("failed to move equipment: %w", err)
	}

	uc.logger.Info("Equipment moved successfully", "equipment_id", equipment.ID)
	return nil
}

// GetEquipmentByBuilding retrieves equipment for a specific building
func (uc *EquipmentUseCase) GetEquipmentByBuilding(ctx context.Context, buildingID string) ([]*domain.Equipment, error) {
	uc.logger.Info("Getting equipment by building", "building_id", buildingID)

	if buildingID == "" {
		return nil, fmt.Errorf("building ID is required")
	}

	// Verify building exists
	_, err := uc.buildingRepo.GetByID(ctx, buildingID)
	if err != nil {
		uc.logger.Error("Failed to verify building exists", "building_id", buildingID, "error", err)
		return nil, fmt.Errorf("building not found: %w", err)
	}

	equipment, err := uc.equipmentRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		uc.logger.Error("Failed to get equipment by building", "building_id", buildingID, "error", err)
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	return equipment, nil
}

// Private helper methods

func (uc *EquipmentUseCase) validateCreateEquipment(req *domain.CreateEquipmentRequest) error {
	if req.BuildingID.IsEmpty() {
		return fmt.Errorf("building ID is required")
	}
	if req.Name == "" {
		return fmt.Errorf("equipment name is required")
	}
	if req.Type == "" {
		return fmt.Errorf("equipment type is required")
	}

	// Validate equipment type
	validTypes := []string{"hvac", "electrical", "plumbing", "security", "fire_safety", "elevator", "lighting"}
	valid := false
	for _, t := range validTypes {
		if req.Type == t {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid equipment type: %s", req.Type)
	}

	return nil
}

func (uc *EquipmentUseCase) validateUpdateEquipment(equipment *domain.Equipment) error {
	if equipment.Name == "" {
		return fmt.Errorf("equipment name cannot be empty")
	}
	if equipment.Type == "" {
		return fmt.Errorf("equipment type cannot be empty")
	}

	// Validate equipment type
	validTypes := []string{"hvac", "electrical", "plumbing", "security", "fire_safety", "elevator", "lighting"}
	valid := false
	for _, t := range validTypes {
		if equipment.Type == t {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid equipment type: %s", equipment.Type)
	}

	// Validate status
	validStatuses := []string{"operational", "maintenance", "failed", "inactive"}
	valid = false
	for _, s := range validStatuses {
		if equipment.Status == s {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid equipment status: %s", equipment.Status)
	}

	return nil
}
