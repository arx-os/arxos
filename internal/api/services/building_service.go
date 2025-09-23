package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// BuildingServiceImpl implements the BuildingService interface
type BuildingServiceImpl struct {
	db database.DB
}

// NewBuildingService creates a new building service
func NewBuildingService(db database.DB) BuildingService {
	return &BuildingServiceImpl{
		db: db,
	}
}

// GetBuilding retrieves a building by ID
func (s *BuildingServiceImpl) GetBuilding(ctx context.Context, id string) (*models.FloorPlan, error) {
	building, err := s.db.GetFloorPlan(ctx, id)
	if err != nil {
		logger.Error("Failed to get building %s: %v", id, err)
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	return building, nil
}

// ListBuildings lists all buildings for a user
func (s *BuildingServiceImpl) ListBuildings(ctx context.Context, userID string, limit, offset int) ([]*models.FloorPlan, error) {
	// TODO: Implement user-based filtering
	buildings, err := s.db.GetAllFloorPlans(ctx)
	if err != nil {
		logger.Error("Failed to list buildings: %v", err)
		return nil, fmt.Errorf("failed to list buildings: %w", err)
	}

	// Apply pagination
	if offset >= len(buildings) {
		return []*models.FloorPlan{}, nil
	}

	end := offset + limit
	if end > len(buildings) {
		end = len(buildings)
	}

	return buildings[offset:end], nil
}

// CreateBuilding creates a new building
func (s *BuildingServiceImpl) CreateBuilding(ctx context.Context, building *models.FloorPlan) error {
	// Set timestamps
	now := time.Now()
	building.CreatedAt = &now
	building.UpdatedAt = &now

	if err := s.db.SaveFloorPlan(ctx, building); err != nil {
		logger.Error("Failed to create building: %v", err)
		return fmt.Errorf("failed to create building: %w", err)
	}

	logger.Info("Created building: %s", building.Name)
	return nil
}

// UpdateBuilding updates an existing building
func (s *BuildingServiceImpl) UpdateBuilding(ctx context.Context, building *models.FloorPlan) error {
	// Update timestamp
	now := time.Now()
	building.UpdatedAt = &now

	if err := s.db.UpdateFloorPlan(ctx, building); err != nil {
		logger.Error("Failed to update building: %v", err)
		return fmt.Errorf("failed to update building: %w", err)
	}

	logger.Info("Updated building: %s", building.Name)
	return nil
}

// DeleteBuilding deletes a building
func (s *BuildingServiceImpl) DeleteBuilding(ctx context.Context, id string) error {
	if err := s.db.DeleteFloorPlan(ctx, id); err != nil {
		logger.Error("Failed to delete building %s: %v", id, err)
		return fmt.Errorf("failed to delete building: %w", err)
	}

	logger.Info("Deleted building: %s", id)
	return nil
}

// GetEquipment retrieves equipment by ID
func (s *BuildingServiceImpl) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	equipment, err := s.db.GetEquipment(ctx, id)
	if err != nil {
		logger.Error("Failed to get equipment %s: %v", id, err)
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	return equipment, nil
}

// ListEquipment lists equipment for a building
func (s *BuildingServiceImpl) ListEquipment(ctx context.Context, buildingID string, filters map[string]interface{}) ([]*models.Equipment, error) {
	equipment, err := s.db.GetEquipmentByFloorPlan(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to list equipment for building %s: %v", buildingID, err)
		return nil, fmt.Errorf("failed to list equipment: %w", err)
	}

	// Apply filters
	filtered := make([]*models.Equipment, 0)
	for _, eq := range equipment {
		include := true

		// Check type filter
		if typeFilter, ok := filters["type"].(string); ok && typeFilter != "" {
			if eq.Type != typeFilter {
				include = false
			}
		}

		// Check status filter
		if statusFilter, ok := filters["status"].(string); ok && statusFilter != "" {
			if string(eq.Status) != statusFilter {
				include = false
			}
		}

		// Check room filter
		if roomFilter, ok := filters["room_id"].(string); ok && roomFilter != "" {
			if eq.RoomID != roomFilter {
				include = false
			}
		}

		if include {
			filtered = append(filtered, eq)
		}
	}

	return filtered, nil
}

// CreateEquipment creates new equipment
func (s *BuildingServiceImpl) CreateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Set timestamp
	now := time.Now()
	equipment.MarkedAt = &now

	if err := s.db.SaveEquipment(ctx, equipment); err != nil {
		logger.Error("Failed to create equipment: %v", err)
		return fmt.Errorf("failed to create equipment: %w", err)
	}

	logger.Info("Created equipment: %s", equipment.Name)
	return nil
}

// UpdateEquipment updates existing equipment
func (s *BuildingServiceImpl) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Update timestamp
	now := time.Now()
	equipment.MarkedAt = &now

	if err := s.db.UpdateEquipment(ctx, equipment); err != nil {
		logger.Error("Failed to update equipment: %v", err)
		return fmt.Errorf("failed to update equipment: %w", err)
	}

	logger.Info("Updated equipment: %s", equipment.Name)
	return nil
}

// DeleteEquipment deletes equipment
func (s *BuildingServiceImpl) DeleteEquipment(ctx context.Context, id string) error {
	if err := s.db.DeleteEquipment(ctx, id); err != nil {
		logger.Error("Failed to delete equipment %s: %v", id, err)
		return fmt.Errorf("failed to delete equipment: %w", err)
	}

	logger.Info("Deleted equipment: %s", id)
	return nil
}

// GetRoom retrieves a room by ID
func (s *BuildingServiceImpl) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	room, err := s.db.GetRoom(ctx, id)
	if err != nil {
		logger.Error("Failed to get room %s: %v", id, err)
		return nil, fmt.Errorf("failed to get room: %w", err)
	}

	return room, nil
}

// ListRooms lists rooms for a building
func (s *BuildingServiceImpl) ListRooms(ctx context.Context, buildingID string) ([]*models.Room, error) {
	rooms, err := s.db.GetRoomsByFloorPlan(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to list rooms for building %s: %v", buildingID, err)
		return nil, fmt.Errorf("failed to list rooms: %w", err)
	}

	return rooms, nil
}

// CreateRoom creates a new room
func (s *BuildingServiceImpl) CreateRoom(ctx context.Context, room *models.Room) error {
	if err := s.db.SaveRoom(ctx, room); err != nil {
		logger.Error("Failed to create room: %v", err)
		return fmt.Errorf("failed to create room: %w", err)
	}

	logger.Info("Created room: %s", room.Name)
	return nil
}

// UpdateRoom updates an existing room
func (s *BuildingServiceImpl) UpdateRoom(ctx context.Context, room *models.Room) error {
	if err := s.db.UpdateRoom(ctx, room); err != nil {
		logger.Error("Failed to update room: %v", err)
		return fmt.Errorf("failed to update room: %w", err)
	}

	logger.Info("Updated room: %s", room.Name)
	return nil
}

// DeleteRoom deletes a room
func (s *BuildingServiceImpl) DeleteRoom(ctx context.Context, id string) error {
	if err := s.db.DeleteRoom(ctx, id); err != nil {
		logger.Error("Failed to delete room %s: %v", id, err)
		return fmt.Errorf("failed to delete room: %w", err)
	}

	logger.Info("Deleted room: %s", id)
	return nil
}
