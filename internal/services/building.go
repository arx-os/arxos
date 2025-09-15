package services

import (
	"context"
	"fmt"
	"time"

	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
)

// BuildingService handles building-related operations
type BuildingService struct {
	db database.DB
}

// NewBuildingService creates a new building service
func NewBuildingService(db database.DB) *BuildingService {
	return &BuildingService{
		db: db,
	}
}

// ListBuildings returns a paginated list of buildings for a user
func (bs *BuildingService) ListBuildings(ctx context.Context, userID string, limit, offset int) ([]*models.FloorPlan, error) {
	// In production, this would filter by user permissions
	return bs.db.GetAllFloorPlans(ctx)
}

// GetBuilding returns a specific building by ID
func (bs *BuildingService) GetBuilding(ctx context.Context, buildingID string) (*models.FloorPlan, error) {
	return bs.db.GetFloorPlan(ctx, buildingID)
}

// CreateBuilding creates a new building
func (bs *BuildingService) CreateBuilding(ctx context.Context, building *models.FloorPlan) error {
	// Set defaults
	if building.ID == "" {
		building.ID = generateBuildingID()
	}
	now := time.Now()
	building.CreatedAt = &now
	building.UpdatedAt = &now
	
	return bs.db.SaveFloorPlan(ctx, building)
}

// UpdateBuilding updates an existing building
func (bs *BuildingService) UpdateBuilding(ctx context.Context, building *models.FloorPlan) error {
	existing, err := bs.db.GetFloorPlan(ctx, building.ID)
	if err != nil {
		return fmt.Errorf("building not found: %w", err)
	}
	
	// Update only allowed fields
	existing.Name = building.Name
	existing.Building = building.Building
	existing.Level = building.Level
	now := time.Now()
	existing.UpdatedAt = &now
	
	return bs.db.SaveFloorPlan(ctx, existing)
}

// DeleteBuilding deletes a building
func (bs *BuildingService) DeleteBuilding(ctx context.Context, buildingID string) error {
	return bs.db.DeleteFloorPlan(ctx, buildingID)
}

// generateBuildingID generates a unique ID for new buildings
func generateBuildingID() string {
	return fmt.Sprintf("bld_%d", time.Now().UnixNano())
}

// Equipment operations

// GetEquipment returns a specific equipment by ID
func (bs *BuildingService) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	// Use database's optimized equipment lookup instead of scanning all plans
	return bs.db.GetEquipment(ctx, id)
}

// ListEquipment returns equipment for a building
func (bs *BuildingService) ListEquipment(ctx context.Context, buildingID string, filters map[string]interface{}) ([]*models.Equipment, error) {
	plan, err := bs.db.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return nil, err
	}
	
	// Convert to pointer slice
	var result []*models.Equipment
	for i := range plan.Equipment {
		// Apply filters if provided
		if filters != nil && len(filters) > 0 {
			// Simple status filter
			if status, ok := filters["status"].(string); ok {
				if string(plan.Equipment[i].Status) != status {
					continue
				}
			}
			// Type filter
			if eqType, ok := filters["type"].(string); ok {
				if plan.Equipment[i].Type != eqType {
					continue
				}
			}
		}
		result = append(result, plan.Equipment[i])
	}
	
	return result, nil
}

// CreateEquipment creates new equipment
func (bs *BuildingService) CreateEquipment(ctx context.Context, equipment *models.Equipment) error {
	if equipment.ID == "" {
		equipment.ID = fmt.Sprintf("eq_%d", time.Now().UnixNano())
	}
	
	// Find the building and add equipment
	// This would need to be properly implemented with building ID
	return fmt.Errorf("not implemented: equipment must be associated with a building")
}

// UpdateEquipment updates existing equipment
func (bs *BuildingService) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Use database's optimized equipment update instead of scanning all plans
	return bs.db.UpdateEquipment(ctx, equipment)
}

// DeleteEquipment deletes equipment
func (bs *BuildingService) DeleteEquipment(ctx context.Context, id string) error {
	// Use database's optimized equipment deletion instead of scanning all plans
	return bs.db.DeleteEquipment(ctx, id)
}

// Room operations

// GetRoom returns a specific room by ID
func (bs *BuildingService) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	// Use database's optimized room lookup instead of scanning all plans
	return bs.db.GetRoom(ctx, id)
}

// ListRooms returns rooms for a building
func (bs *BuildingService) ListRooms(ctx context.Context, buildingID string) ([]*models.Room, error) {
	plan, err := bs.db.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return nil, err
	}
	
	// Convert to pointer slice
	var result []*models.Room
	for i := range plan.Rooms {
		result = append(result, plan.Rooms[i])
	}
	return result, nil
}

// CreateRoom creates a new room
func (bs *BuildingService) CreateRoom(ctx context.Context, room *models.Room) error {
	if room.ID == "" {
		room.ID = fmt.Sprintf("rm_%d", time.Now().UnixNano())
	}
	
	// This would need to be properly implemented with building ID
	return fmt.Errorf("not implemented: room must be associated with a building")
}

// UpdateRoom updates an existing room
func (bs *BuildingService) UpdateRoom(ctx context.Context, room *models.Room) error {
	// Use database's optimized room update instead of scanning all plans
	return bs.db.UpdateRoom(ctx, room)
}

// DeleteRoom deletes a room
func (bs *BuildingService) DeleteRoom(ctx context.Context, id string) error {
	// Use database's optimized room deletion instead of scanning all plans
	return bs.db.DeleteRoom(ctx, id)
}