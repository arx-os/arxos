package building

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
)

// service implements the building service following Clean Architecture principles
type service struct {
	repo        Repository
	db          database.DB
	userService UserService
	orgService  OrganizationService
}

// UserService interface for user-related operations
type UserService interface {
	GetUserLegacy(ctx context.Context, userID string) (*models.User, error)
	GetUserOrganizationsLegacy(ctx context.Context, userID string) ([]*models.Organization, error)
}

// OrganizationService interface for organization-related operations
type OrganizationService interface {
	GetOrganizationLegacy(ctx context.Context, orgID string) (*models.Organization, error)
}

// NewService creates a new building service with dependency injection
func NewService(repo Repository) Service {
	return &service{
		repo: repo,
	}
}

// NewServiceWithDependencies creates a new building service with all dependencies
func NewServiceWithDependencies(repo Repository, db database.DB, userService UserService, orgService OrganizationService) Service {
	return &service{
		repo:        repo,
		db:          db,
		userService: userService,
		orgService:  orgService,
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

// Legacy building operations (for backward compatibility with existing code)

// ListBuildingsLegacy returns a paginated list of buildings for a user
func (s *service) ListBuildingsLegacy(ctx context.Context, userID string, limit, offset int) ([]*models.FloorPlan, error) {
	// Get all buildings first
	allBuildings, err := s.db.GetAllFloorPlans(ctx)
	if err != nil {
		return nil, err
	}

	// If no user service available, return all buildings (backward compatibility)
	if s.userService == nil {
		return s.paginateBuildings(allBuildings, limit, offset), nil
	}

	// Get user to check permissions
	user, err := s.userService.GetUserLegacy(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Admin users can see all buildings
	if user.Role == "admin" {
		return s.paginateBuildings(allBuildings, limit, offset), nil
	}

	// Filter buildings based on user's organization access
	filteredBuildings, err := s.filterBuildingsByUserAccess(ctx, allBuildings, user)
	if err != nil {
		return nil, fmt.Errorf("failed to filter buildings: %w", err)
	}

	return s.paginateBuildings(filteredBuildings, limit, offset), nil
}

// GetBuildingLegacy returns a specific building by ID (legacy method)
func (s *service) GetBuildingLegacy(ctx context.Context, buildingID string) (*models.FloorPlan, error) {
	return s.db.GetFloorPlan(ctx, buildingID)
}

// GetBuildingForUser returns a specific building by ID with user access check
func (s *service) GetBuildingForUser(ctx context.Context, userID, buildingID string) (*models.FloorPlan, error) {
	// Check if user has access to this building
	hasAccess, err := s.CheckBuildingAccess(ctx, userID, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to check building access: %w", err)
	}

	if !hasAccess {
		return nil, fmt.Errorf("user does not have access to building %s", buildingID)
	}

	// Get the building
	return s.db.GetFloorPlan(ctx, buildingID)
}

// CreateBuildingLegacy creates a new building (legacy method)
func (s *service) CreateBuildingLegacy(ctx context.Context, building *models.FloorPlan) error {
	// Set defaults
	if building.ID == "" {
		building.ID = generateBuildingID()
	}
	now := time.Now()
	building.CreatedAt = &now
	building.UpdatedAt = &now

	return s.db.SaveFloorPlan(ctx, building)
}

// UpdateBuildingLegacy updates an existing building (legacy method)
func (s *service) UpdateBuildingLegacy(ctx context.Context, building *models.FloorPlan) error {
	existing, err := s.db.GetFloorPlan(ctx, building.ID)
	if err != nil {
		return fmt.Errorf("building not found: %w", err)
	}

	// Update only allowed fields
	existing.Name = building.Name
	existing.Building = building.Building
	existing.Level = building.Level
	now := time.Now()
	existing.UpdatedAt = &now

	return s.db.SaveFloorPlan(ctx, existing)
}

// DeleteBuildingLegacy deletes a building (legacy method)
func (s *service) DeleteBuildingLegacy(ctx context.Context, buildingID string) error {
	return s.db.DeleteFloorPlan(ctx, buildingID)
}

// Equipment operations

// GetEquipment returns a specific equipment by ID
func (s *service) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	// Use database's optimized equipment lookup instead of scanning all plans
	return s.db.GetEquipment(ctx, id)
}

// ListEquipment returns equipment for a building
func (s *service) ListEquipment(ctx context.Context, buildingID string, filters map[string]interface{}) ([]*models.Equipment, error) {
	plan, err := s.db.GetFloorPlan(ctx, buildingID)
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
func (s *service) ListEquipmentForUser(ctx context.Context, userID, buildingID string, filters map[string]interface{}) ([]*models.Equipment, error) {
	// Check if user has access to this building
	hasAccess, err := s.CheckBuildingAccess(ctx, userID, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to check building access: %w", err)
	}

	if !hasAccess {
		return nil, fmt.Errorf("user does not have access to building %s", buildingID)
	}

	// Get equipment
	return s.ListEquipment(ctx, buildingID, filters)
}

// CreateEquipment creates new equipment
func (s *service) CreateEquipment(ctx context.Context, equipment *models.Equipment) error {
	if equipment.ID == "" {
		equipment.ID = fmt.Sprintf("eq_%d", time.Now().UnixNano())
	}

	// Equipment is associated with rooms, not directly with floor plans
	// The room validation happens at the database level
	// Simply save the equipment
	return s.db.SaveEquipment(ctx, equipment)
}

// UpdateEquipment updates existing equipment
func (s *service) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Use database's optimized equipment update instead of scanning all plans
	return s.db.UpdateEquipment(ctx, equipment)
}

// DeleteEquipment deletes equipment
func (s *service) DeleteEquipment(ctx context.Context, id string) error {
	// Use database's optimized equipment deletion instead of scanning all plans
	return s.db.DeleteEquipment(ctx, id)
}

// Room operations

// GetRoom returns a specific room by ID
func (s *service) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	// Use database's optimized room lookup instead of scanning all plans
	return s.db.GetRoom(ctx, id)
}

// ListRooms returns rooms for a building
func (s *service) ListRooms(ctx context.Context, buildingID string) ([]*models.Room, error) {
	plan, err := s.db.GetFloorPlan(ctx, buildingID)
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
func (s *service) ListRoomsForUser(ctx context.Context, userID, buildingID string) ([]*models.Room, error) {
	// Check if user has access to this building
	hasAccess, err := s.CheckBuildingAccess(ctx, userID, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to check building access: %w", err)
	}

	if !hasAccess {
		return nil, fmt.Errorf("user does not have access to building %s", buildingID)
	}

	// Get rooms
	return s.ListRooms(ctx, buildingID)
}

// CreateRoom creates a new room
func (s *service) CreateRoom(ctx context.Context, room *models.Room) error {
	if room.ID == "" {
		room.ID = fmt.Sprintf("rm_%d", time.Now().UnixNano())
	}

	// Rooms are stored directly in the database
	// The database handles the association with floor plans
	return s.db.SaveRoom(ctx, room)
}

// UpdateRoom updates an existing room
func (s *service) UpdateRoom(ctx context.Context, room *models.Room) error {
	// Use database's optimized room update instead of scanning all plans
	return s.db.UpdateRoom(ctx, room)
}

// DeleteRoom deletes a room
func (s *service) DeleteRoom(ctx context.Context, id string) error {
	// Use database's optimized room deletion instead of scanning all plans
	return s.db.DeleteRoom(ctx, id)
}

// Helper methods for user-based filtering

// filterBuildingsByUserAccess filters buildings based on user's organization access
func (s *service) filterBuildingsByUserAccess(ctx context.Context, buildings []*models.FloorPlan, user *models.User) ([]*models.FloorPlan, error) {
	var filteredBuildings []*models.FloorPlan

	for _, building := range buildings {
		// Check if user has access to this building
		hasAccess, err := s.userHasBuildingAccess(ctx, user, building)
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
func (s *service) userHasBuildingAccess(ctx context.Context, user *models.User, building *models.FloorPlan) (bool, error) {
	// Check if building has organization ID
	if building.OrganizationID == "" {
		// If no organization specified, only admin users can access
		return user.Role == "admin", nil
	}

	// If user service not available, allow access (backward compatibility)
	if s.userService == nil {
		return true, nil
	}

	// Check if user is a member of the building's organization
	userOrgs, err := s.userService.GetUserOrganizationsLegacy(ctx, user.ID)
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
func (s *service) paginateBuildings(buildings []*models.FloorPlan, limit, offset int) []*models.FloorPlan {
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
func (s *service) CheckBuildingAccess(ctx context.Context, userID, buildingID string) (bool, error) {
	// Get user
	user, err := s.userService.GetUserLegacy(ctx, userID)
	if err != nil {
		return false, fmt.Errorf("failed to get user: %w", err)
	}

	// Admin users have access to all buildings
	if user.Role == "admin" {
		return true, nil
	}

	// Get building
	building, err := s.db.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return false, fmt.Errorf("failed to get building: %w", err)
	}

	// Check access
	return s.userHasBuildingAccess(ctx, user, building)
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

// generateBuildingID generates a unique ID for new buildings
func generateBuildingID() string {
	return common.GenerateBuildingID()
}
