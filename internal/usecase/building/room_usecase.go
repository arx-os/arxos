package building

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/utils"
)

// RoomUseCase implements the room business logic following Clean Architecture
type RoomUseCase struct {
	roomRepo      domain.RoomRepository
	equipmentRepo domain.EquipmentRepository
	floorRepo     domain.FloorRepository
	buildingRepo  domain.BuildingRepository
	logger        domain.Logger
	idGenerator   *utils.IDGenerator
}

// NewRoomUseCase creates a new RoomUseCase
func NewRoomUseCase(roomRepo domain.RoomRepository, floorRepo domain.FloorRepository, buildingRepo domain.BuildingRepository, logger domain.Logger) *RoomUseCase {
	return &RoomUseCase{
		roomRepo:     roomRepo,
		floorRepo:    floorRepo,
		buildingRepo: buildingRepo,
		logger:       logger,
		idGenerator:  utils.NewIDGenerator(),
	}
}

// SetEquipmentRepository injects the equipment repository (for avoiding circular dependencies)
func (uc *RoomUseCase) SetEquipmentRepository(equipmentRepo domain.EquipmentRepository) {
	uc.equipmentRepo = equipmentRepo
}

// CreateRoom creates a new room on a floor
func (uc *RoomUseCase) CreateRoom(ctx context.Context, req *domain.CreateRoomRequest) (*domain.Room, error) {
	uc.logger.Info("Creating room", "floor_id", req.FloorID.String(), "number", req.Number)

	// Validate floor exists
	_, err := uc.floorRepo.GetByID(ctx, req.FloorID.String())
	if err != nil {
		uc.logger.Error("Floor not found", "floor_id", req.FloorID.String(), "error", err)
		return nil, fmt.Errorf("floor not found: %w", err)
	}

	// Validate request
	if err := uc.validateCreateRoom(req); err != nil {
		uc.logger.Error("Room validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check for duplicate room number on this floor
	existing, _ := uc.roomRepo.GetByNumber(ctx, req.FloorID.String(), req.Number)
	if existing != nil {
		return nil, fmt.Errorf("room %s already exists on this floor", req.Number)
	}

	// Create room entity
	room := &domain.Room{
		ID:        uc.idGenerator.GenerateRoomID(req.FloorID, req.Number),
		FloorID:   req.FloorID,
		Name:      req.Name,
		Number:    req.Number,
		Location:  req.Location,
		Width:     req.Width,
		Height:    req.Height,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Save to repository
	if err := uc.roomRepo.Create(ctx, room); err != nil {
		uc.logger.Error("Failed to create room", "error", err)
		return nil, fmt.Errorf("failed to create room: %w", err)
	}

	uc.logger.Info("Room created successfully", "room_id", room.ID.String())
	return room, nil
}

// GetRoom retrieves a room by ID
func (uc *RoomUseCase) GetRoom(ctx context.Context, id types.ID) (*domain.Room, error) {
	uc.logger.Info("Getting room", "room_id", id.String())

	if id.IsEmpty() {
		return nil, fmt.Errorf("room ID is required")
	}

	room, err := uc.roomRepo.GetByID(ctx, id.String())
	if err != nil {
		uc.logger.Error("Failed to get room", "room_id", id.String(), "error", err)
		return nil, fmt.Errorf("failed to get room: %w", err)
	}

	return room, nil
}

// ListRooms lists all rooms for a floor
func (uc *RoomUseCase) ListRooms(ctx context.Context, floorID types.ID, limit, offset int) ([]*domain.Room, error) {
	uc.logger.Info("Listing rooms", "floor_id", floorID.String())

	if floorID.IsEmpty() {
		return nil, fmt.Errorf("floor ID is required")
	}

	// Validate floor exists
	_, err := uc.floorRepo.GetByID(ctx, floorID.String())
	if err != nil {
		return nil, fmt.Errorf("floor not found: %w", err)
	}

	rooms, err := uc.roomRepo.GetByFloor(ctx, floorID.String())
	if err != nil {
		uc.logger.Error("Failed to list rooms", "floor_id", floorID.String(), "error", err)
		return nil, fmt.Errorf("failed to list rooms: %w", err)
	}

	uc.logger.Info("Rooms listed successfully", "count", len(rooms))
	return rooms, nil
}

// UpdateRoom updates an existing room
func (uc *RoomUseCase) UpdateRoom(ctx context.Context, req *domain.UpdateRoomRequest) (*domain.Room, error) {
	uc.logger.Info("Updating room", "room_id", req.ID.String())

	// Get existing room
	room, err := uc.roomRepo.GetByID(ctx, req.ID.String())
	if err != nil {
		return nil, fmt.Errorf("room not found: %w", err)
	}

	// Update fields
	if req.Name != nil {
		room.Name = *req.Name
	}
	if req.Number != nil {
		room.Number = *req.Number
	}
	if req.Location != nil {
		room.Location = req.Location
	}
	if req.Width != nil {
		room.Width = *req.Width
	}
	if req.Height != nil {
		room.Height = *req.Height
	}
	room.UpdatedAt = time.Now()

	// Save changes
	if err := uc.roomRepo.Update(ctx, room); err != nil {
		uc.logger.Error("Failed to update room", "error", err)
		return nil, fmt.Errorf("failed to update room: %w", err)
	}

	uc.logger.Info("Room updated successfully", "room_id", room.ID.String())
	return room, nil
}

// DeleteRoom deletes a room
func (uc *RoomUseCase) DeleteRoom(ctx context.Context, id string) error {
	uc.logger.Info("Deleting room", "room_id", id)

	if id == "" {
		return fmt.Errorf("room ID is required")
	}

	// Check if room exists
	_, err := uc.roomRepo.GetByID(ctx, id)
	if err != nil {
		return fmt.Errorf("room not found: %w", err)
	}

	if err := uc.roomRepo.Delete(ctx, id); err != nil {
		uc.logger.Error("Failed to delete room", "error", err)
		return fmt.Errorf("failed to delete room: %w", err)
	}

	uc.logger.Info("Room deleted successfully", "room_id", id)
	return nil
}

// GetRoomEquipment retrieves all equipment for a room
func (uc *RoomUseCase) GetRoomEquipment(ctx context.Context, roomID types.ID) ([]*domain.Equipment, error) {
	uc.logger.Info("Getting room equipment", "room_id", roomID.String())

	if roomID.IsEmpty() {
		return nil, fmt.Errorf("room ID is required")
	}

	if uc.equipmentRepo == nil {
		return nil, fmt.Errorf("equipment repository not initialized")
	}

	// Validate room exists
	_, err := uc.roomRepo.GetByID(ctx, roomID.String())
	if err != nil {
		return nil, fmt.Errorf("room not found: %w", err)
	}

	equipment, err := uc.equipmentRepo.GetByRoom(ctx, roomID.String())
	if err != nil {
		uc.logger.Error("Failed to get room equipment", "room_id", roomID.String(), "error", err)
		return nil, fmt.Errorf("failed to get room equipment: %w", err)
	}

	uc.logger.Info("Room equipment retrieved successfully", "count", len(equipment))
	return equipment, nil
}

// validateCreateRoom validates room creation request
func (uc *RoomUseCase) validateCreateRoom(req *domain.CreateRoomRequest) error {
	if req.FloorID.IsEmpty() {
		return fmt.Errorf("floor ID is required")
	}
	if req.Name == "" {
		return fmt.Errorf("room name is required")
	}
	if req.Number == "" {
		return fmt.Errorf("room number is required")
	}
	return nil
}
