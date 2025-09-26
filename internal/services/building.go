package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// BuildingService handles building-related operations
type BuildingService struct {
	db          database.DB
	userService *UserService
	orgService  *OrganizationService
}

// NewBuildingService creates a new building service
func NewBuildingService(db database.DB) *BuildingService {
	return &BuildingService{
		db: db,
	}
}

// NewBuildingServiceWithDependencies creates a new building service with dependencies
func NewBuildingServiceWithDependencies(db database.DB, userService *UserService, orgService *OrganizationService) *BuildingService {
	return &BuildingService{
		db:          db,
		userService: userService,
		orgService:  orgService,
	}
}

// ListBuildings returns a paginated list of buildings for a user
func (bs *BuildingService) ListBuildings(ctx context.Context, userID string, limit, offset int) ([]*models.FloorPlan, error) {
	// Get all buildings first
	allBuildings, err := bs.db.GetAllFloorPlans(ctx)
	if err != nil {
		return nil, err
	}

	// If no user service available, return all buildings (backward compatibility)
	if bs.userService == nil {
		return bs.paginateBuildings(allBuildings, limit, offset), nil
	}

	// Get user to check permissions
	user, err := bs.userService.GetUser(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Admin users can see all buildings
	if user.Role == "admin" {
		return bs.paginateBuildings(allBuildings, limit, offset), nil
	}

	// Filter buildings based on user's organization access
	filteredBuildings, err := bs.filterBuildingsByUserAccess(ctx, allBuildings, user)
	if err != nil {
		return nil, fmt.Errorf("failed to filter buildings: %w", err)
	}

	return bs.paginateBuildings(filteredBuildings, limit, offset), nil
}

// GetBuilding returns a specific building by ID
func (bs *BuildingService) GetBuilding(ctx context.Context, buildingID string) (*models.FloorPlan, error) {
	return bs.db.GetFloorPlan(ctx, buildingID)
}

// GetBuildingForUser returns a specific building by ID with user access check
func (bs *BuildingService) GetBuildingForUser(ctx context.Context, userID, buildingID string) (*models.FloorPlan, error) {
	// Check if user has access to this building
	hasAccess, err := bs.CheckBuildingAccess(ctx, userID, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to check building access: %w", err)
	}

	if !hasAccess {
		return nil, fmt.Errorf("user does not have access to building %s", buildingID)
	}

	// Get the building
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
	return common.GenerateBuildingID()
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

// ListEquipmentForUser returns equipment for a building with user access check
func (bs *BuildingService) ListEquipmentForUser(ctx context.Context, userID, buildingID string, filters map[string]interface{}) ([]*models.Equipment, error) {
	// Check if user has access to this building
	hasAccess, err := bs.CheckBuildingAccess(ctx, userID, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to check building access: %w", err)
	}

	if !hasAccess {
		return nil, fmt.Errorf("user does not have access to building %s", buildingID)
	}

	// Get equipment
	return bs.ListEquipment(ctx, buildingID, filters)
}

// CreateEquipment creates new equipment
func (bs *BuildingService) CreateEquipment(ctx context.Context, equipment *models.Equipment) error {
	if equipment.ID == "" {
		equipment.ID = fmt.Sprintf("eq_%d", time.Now().UnixNano())
	}

	// Equipment is associated with rooms, not directly with floor plans
	// The room validation happens at the database level
	// Simply save the equipment
	return bs.db.SaveEquipment(ctx, equipment)
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

// ListRoomsForUser returns rooms for a building with user access check
func (bs *BuildingService) ListRoomsForUser(ctx context.Context, userID, buildingID string) ([]*models.Room, error) {
	// Check if user has access to this building
	hasAccess, err := bs.CheckBuildingAccess(ctx, userID, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to check building access: %w", err)
	}

	if !hasAccess {
		return nil, fmt.Errorf("user does not have access to building %s", buildingID)
	}

	// Get rooms
	return bs.ListRooms(ctx, buildingID)
}

// CreateRoom creates a new room
func (bs *BuildingService) CreateRoom(ctx context.Context, room *models.Room) error {
	if room.ID == "" {
		room.ID = fmt.Sprintf("rm_%d", time.Now().UnixNano())
	}

	// Rooms are stored directly in the database
	// The database handles the association with floor plans
	return bs.db.SaveRoom(ctx, room)
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

// Helper methods for user-based filtering

// filterBuildingsByUserAccess filters buildings based on user's organization access
func (bs *BuildingService) filterBuildingsByUserAccess(ctx context.Context, buildings []*models.FloorPlan, user *models.User) ([]*models.FloorPlan, error) {
	var filteredBuildings []*models.FloorPlan

	for _, building := range buildings {
		// Check if user has access to this building
		hasAccess, err := bs.userHasBuildingAccess(ctx, user, building)
		if err != nil {
			// Log error but continue with other buildings
			fmt.Printf("Error checking access for building %s: %v\n", building.ID, err)
			continue
		}

		if hasAccess {
			filteredBuildings = append(filteredBuildings, building)
		}
	}

	return filteredBuildings, nil
}

// userHasBuildingAccess checks if a user has access to a specific building
func (bs *BuildingService) userHasBuildingAccess(ctx context.Context, user *models.User, building *models.FloorPlan) (bool, error) {
	// Check if building has organization ID
	if building.OrganizationID == "" {
		// If no organization specified, only admin users can access
		return user.Role == "admin", nil
	}

	// If user service not available, allow access (backward compatibility)
	if bs.userService == nil {
		return true, nil
	}

	// Check if user is a member of the building's organization
	userOrgs, err := bs.userService.GetUserOrganizations(ctx, user.ID)
	if err != nil {
		return false, fmt.Errorf("failed to get user organizations: %w", err)
	}

	// Check if user belongs to the building's organization
	for _, org := range userOrgs {
		if org.ID == building.OrganizationID {
			return true, nil
		}
	}

	return false, nil
}

// paginateBuildings applies pagination to a list of buildings
func (bs *BuildingService) paginateBuildings(buildings []*models.FloorPlan, limit, offset int) []*models.FloorPlan {
	if limit <= 0 {
		limit = 50 // Default limit
	}

	start := offset
	end := offset + limit

	if start >= len(buildings) {
		return []*models.FloorPlan{}
	}

	if end > len(buildings) {
		end = len(buildings)
	}

	return buildings[start:end]
}

// CheckBuildingAccess checks if a user has access to a specific building
func (bs *BuildingService) CheckBuildingAccess(ctx context.Context, userID, buildingID string) (bool, error) {
	// Get user
	user, err := bs.userService.GetUser(ctx, userID)
	if err != nil {
		return false, fmt.Errorf("failed to get user: %w", err)
	}

	// Admin users have access to all buildings
	if user.Role == "admin" {
		return true, nil
	}

	// Get building
	building, err := bs.db.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return false, fmt.Errorf("failed to get building: %w", err)
	}

	// Check access
	return bs.userHasBuildingAccess(ctx, user, building)
}
