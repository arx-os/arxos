package models

import (
	"fmt"
	"time"

	"github.com/arx-os/arxos/pkg/errors"
)

// Building represents a building in the system
type Building struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Address     string    `json:"address,omitempty"`
	Description string    `json:"description,omitempty"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// BuildingStatus represents the operational status of a building
type BuildingStatus string

const (
	BuildingStatusActive       BuildingStatus = "active"
	BuildingStatusInactive     BuildingStatus = "inactive"
	BuildingStatusMaintenance  BuildingStatus = "maintenance"
	BuildingStatusConstruction BuildingStatus = "construction"
	BuildingStatusDemolished   BuildingStatus = "demolished"
)

// BuildingType represents the type of building
type BuildingType string

const (
	BuildingTypeOffice      BuildingType = "office"
	BuildingTypeResidential BuildingType = "residential"
	BuildingTypeCommercial  BuildingType = "commercial"
	BuildingTypeIndustrial  BuildingType = "industrial"
	BuildingTypeEducational BuildingType = "educational"
	BuildingTypeHealthcare  BuildingType = "healthcare"
	BuildingTypeRetail      BuildingType = "retail"
	BuildingTypeWarehouse   BuildingType = "warehouse"
	BuildingTypeMixed       BuildingType = "mixed"
)

// Building represents an enhanced building with spatial and operational data
type EnhancedBuilding struct {
	// Core identification
	ID           string         `json:"id"`
	UUID         string         `json:"uuid"`
	Name         string         `json:"name"`
	Description  string         `json:"description"`
	Address      string         `json:"address"`
	BuildingType BuildingType   `json:"building_type"`
	Status       BuildingStatus `json:"status"`

	// Spatial data
	Origin      *Point3D     `json:"origin,omitempty"`
	BoundingBox *BoundingBox `json:"bounding_box,omitempty"`
	GridScale   float64      `json:"grid_scale"` // meters per grid unit

	// Hierarchical structure
	Floors  []FloorPlan `json:"floors"`
	Systems []string    `json:"systems"` // System IDs

	// Metadata
	Source     string                 `json:"source"`
	Confidence ConfidenceLevel        `json:"confidence"`
	ImportedAt time.Time              `json:"imported_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
	Properties map[string]interface{} `json:"properties,omitempty"`

	// Data quality
	ValidationIssues []string `json:"validation_issues,omitempty"`
	Coverage         float64  `json:"coverage"` // 0-100% of building covered
}

// BuildingCreateRequest represents a request to create a building
type BuildingCreateRequest struct {
	Name         string                 `json:"name" validate:"required,min=1,max=200"`
	Description  string                 `json:"description,omitempty"`
	Address      string                 `json:"address,omitempty"`
	BuildingType BuildingType           `json:"building_type,omitempty"`
	Status       BuildingStatus         `json:"status,omitempty"`
	Origin       *Point3D               `json:"origin,omitempty"`
	Properties   map[string]interface{} `json:"properties,omitempty"`
}

// BuildingUpdateRequest represents a request to update a building
type BuildingUpdateRequest struct {
	ID           string                 `json:"id" validate:"required"`
	Name         *string                `json:"name,omitempty" validate:"omitempty,min=1,max=200"`
	Description  *string                `json:"description,omitempty"`
	Address      *string                `json:"address,omitempty"`
	BuildingType *BuildingType          `json:"building_type,omitempty"`
	Status       *BuildingStatus        `json:"status,omitempty"`
	Origin       *Point3D               `json:"origin,omitempty"`
	Properties   map[string]interface{} `json:"properties,omitempty"`
}

// BuildingQuery represents a building search query
type BuildingQuery struct {
	// Text search
	Name        *string `json:"name,omitempty"`
	Description *string `json:"description,omitempty"`
	Address     *string `json:"address,omitempty"`

	// Filters
	BuildingType *BuildingType   `json:"building_type,omitempty"`
	Status       *BuildingStatus `json:"status,omitempty"`
	Source       *string         `json:"source,omitempty"`

	// Spatial filters
	NearPoint    *Point3D     `json:"near_point,omitempty"`
	NearRadius   float64      `json:"near_radius,omitempty"` // meters
	WithinBounds *BoundingBox `json:"within_bounds,omitempty"`

	// Pagination
	Limit  int `json:"limit,omitempty"`
	Offset int `json:"offset,omitempty"`

	// Sorting
	SortBy    string `json:"sort_by,omitempty"`    // name, created_at, updated_at, coverage
	SortOrder string `json:"sort_order,omitempty"` // asc, desc
}

// BuildingStats represents building statistics
type BuildingStats struct {
	TotalBuildings      int     `json:"total_buildings"`
	ActiveBuildings     int     `json:"active_buildings"`
	TotalFloors         int     `json:"total_floors"`
	TotalRooms          int     `json:"total_rooms"`
	TotalEquipment      int     `json:"total_equipment"`
	AverageCoverage     float64 `json:"average_coverage"`
	TotalFloorArea      float64 `json:"total_floor_area"`      // square meters
	TotalBuildingVolume float64 `json:"total_building_volume"` // cubic meters
}

// BuildingManager handles building operations
type BuildingManager struct {
	// This would typically be injected from a repository interface
	// For now, we'll define the interface that implementations should follow
}

// NewBuildingManager creates a new building manager
func NewBuildingManager() *BuildingManager {
	return &BuildingManager{}
}

// ValidationIssue represents a validation issue
type ValidationIssue struct {
	Level   string `json:"level"`             // error, warning, info
	Field   string `json:"field"`             // field name
	Message string `json:"message"`           // issue description
	Details string `json:"details,omitempty"` // additional details
}

// ValidateBuilding validates a building for business rules
func (bm *BuildingManager) ValidateBuilding(building *EnhancedBuilding) []ValidationIssue {
	var issues []ValidationIssue

	// Check required fields
	if building.ID == "" {
		issues = append(issues, ValidationIssue{
			Level:   "error",
			Field:   "ID",
			Message: "Building ID is required",
		})
	}

	if building.Name == "" {
		issues = append(issues, ValidationIssue{
			Level:   "warning",
			Field:   "Name",
			Message: "Building name is missing",
		})
	}

	// Validate building type
	if building.BuildingType != "" {
		if !isValidBuildingType(building.BuildingType) {
			issues = append(issues, ValidationIssue{
				Level:   "error",
				Field:   "BuildingType",
				Message: "Invalid building type",
				Details: string(building.BuildingType),
			})
		}
	}

	// Validate status
	if building.Status != "" {
		if !isValidBuildingStatus(building.Status) {
			issues = append(issues, ValidationIssue{
				Level:   "error",
				Field:   "Status",
				Message: "Invalid building status",
				Details: string(building.Status),
			})
		}
	}

	// Check floors
	if len(building.Floors) == 0 {
		issues = append(issues, ValidationIssue{
			Level:   "warning",
			Field:   "Floors",
			Message: "Building has no floors defined",
		})
	}

	// Check for duplicate floor numbers
	floorNumbers := make(map[int]bool)
	for _, floor := range building.Floors {
		if floorNumbers[floor.Level] {
			issues = append(issues, ValidationIssue{
				Level:   "error",
				Field:   "Floors",
				Message: "Duplicate floor number",
				Details: floor.Name,
			})
		}
		floorNumbers[floor.Level] = true
	}

	// Validate spatial data
	if building.Origin != nil {
		if err := bm.validateSpatialReference(building.Origin); err != nil {
			issues = append(issues, ValidationIssue{
				Level:   "error",
				Field:   "Origin",
				Message: "Invalid spatial reference",
				Details: err.Error(),
			})
		}
	}

	// Validate equipment references
	for _, floor := range building.Floors {
		for _, equipment := range floor.Equipment {
			if equipment.RoomID != "" {
				// Check if room exists in this floor
				roomExists := false
				for _, room := range floor.Rooms {
					if room.ID == equipment.RoomID {
						roomExists = true
						break
					}
				}
				if !roomExists {
					issues = append(issues, ValidationIssue{
						Level:   "warning",
						Field:   "Equipment",
						Message: "Equipment references non-existent room",
						Details: equipment.ID,
					})
				}
			}
		}
	}

	return issues
}

// CalculateBuildingStats calculates statistics for a building
func (bm *BuildingManager) CalculateBuildingStats(building *EnhancedBuilding) *BuildingStats {
	stats := &BuildingStats{
		TotalBuildings: 1,
	}

	if building.Status == BuildingStatusActive {
		stats.ActiveBuildings = 1
	}

	stats.TotalFloors = len(building.Floors)

	totalRooms := 0
	totalEquipment := 0
	totalFloorArea := 0.0
	totalVolume := 0.0

	for _, floor := range building.Floors {
		totalRooms += len(floor.Rooms)
		totalEquipment += len(floor.Equipment)

		// Note: FloorPlan doesn't have BoundingBox or Height fields
		// These would need to be calculated from room data or added to FloorPlan
		// For now, we'll skip area/volume calculations
	}

	stats.TotalRooms = totalRooms
	stats.TotalEquipment = totalEquipment
	stats.TotalFloorArea = totalFloorArea
	stats.TotalBuildingVolume = totalVolume
	stats.AverageCoverage = building.Coverage

	return stats
}

// GetFloorByNumber returns a floor by its number
func (bm *BuildingManager) GetFloorByNumber(building *EnhancedBuilding, number int) *FloorPlan {
	for i := range building.Floors {
		if building.Floors[i].Level == number {
			return &building.Floors[i]
		}
	}
	return nil
}

// GetEquipmentByID returns equipment by its ID
func (bm *BuildingManager) GetEquipmentByID(building *EnhancedBuilding, id string) *Equipment {
	for _, floor := range building.Floors {
		for _, equipment := range floor.Equipment {
			if equipment.ID == id {
				return equipment
			}
		}
	}
	return nil
}

// GetAllEquipment returns all equipment across all floors
func (bm *BuildingManager) GetAllEquipment(building *EnhancedBuilding) []*Equipment {
	var allEquipment []*Equipment
	for _, floor := range building.Floors {
		allEquipment = append(allEquipment, floor.Equipment...)
	}
	return allEquipment
}

// AddFloor adds a floor to the building
func (bm *BuildingManager) AddFloor(building *EnhancedBuilding, floor FloorPlan) error {
	// Check for duplicate floor number
	for _, existingFloor := range building.Floors {
		if existingFloor.Level == floor.Level {
			return errors.New(errors.CodeConflict, fmt.Sprintf("Floor number %d already exists", floor.Level))
		}
	}

	// Validate floor
	if err := bm.validateFloor(&floor); err != nil {
		return err
	}

	building.Floors = append(building.Floors, floor)
	building.UpdatedAt = time.Now()

	return nil
}

// RemoveFloor removes a floor from the building
func (bm *BuildingManager) RemoveFloor(building *EnhancedBuilding, floorNumber int) error {
	for i, floor := range building.Floors {
		if floor.Level == floorNumber {
			// Check if floor has equipment
			if len(floor.Equipment) > 0 {
				return errors.New(errors.CodeConflict, "Cannot remove floor with equipment")
			}

			// Remove floor
			building.Floors = append(building.Floors[:i], building.Floors[i+1:]...)
			building.UpdatedAt = time.Now()
			return nil
		}
	}

	return errors.New(errors.CodeNotFound, fmt.Sprintf("Floor number %d not found", floorNumber))
}

// AddEquipment adds equipment to a floor
func (bm *BuildingManager) AddEquipment(building *EnhancedBuilding, floorNumber int, equipment Equipment) error {
	// Find the floor by number and get its index
	var floorIndex int = -1
	for i, floor := range building.Floors {
		if floor.Level == floorNumber {
			floorIndex = i
			break
		}
	}

	if floorIndex == -1 {
		return errors.New(errors.CodeNotFound, fmt.Sprintf("Floor number %d not found", floorNumber))
	}

	// Validate equipment
	if err := bm.validateEquipment(&equipment); err != nil {
		return err
	}

	// Add equipment to the floor
	building.Floors[floorIndex].Equipment = append(building.Floors[floorIndex].Equipment, &equipment)
	building.UpdatedAt = time.Now()

	return nil
}

// RemoveEquipment removes equipment from a floor
func (bm *BuildingManager) RemoveEquipment(building *EnhancedBuilding, equipmentID string) error {
	for floorIndex, floor := range building.Floors {
		for i, equipment := range floor.Equipment {
			if equipment.ID == equipmentID {
				// Remove equipment from the floor
				building.Floors[floorIndex].Equipment = append(floor.Equipment[:i], floor.Equipment[i+1:]...)
				building.UpdatedAt = time.Now()
				return nil
			}
		}
	}

	return errors.New(errors.CodeNotFound, fmt.Sprintf("Equipment %s not found", equipmentID))
}

// UpdateEquipment updates equipment in the building
func (bm *BuildingManager) UpdateEquipment(building *EnhancedBuilding, equipmentID string, updates map[string]interface{}) error {
	equipment := bm.GetEquipmentByID(building, equipmentID)
	if equipment == nil {
		return errors.New(errors.CodeNotFound, fmt.Sprintf("Equipment %s not found", equipmentID))
	}

	// Apply updates
	if name, ok := updates["name"].(string); ok {
		equipment.Name = name
	}
	if status, ok := updates["status"].(string); ok {
		equipment.Status = status
	}
	if location, ok := updates["location"].(*Point3D); ok {
		equipment.Location = location
	}

	building.UpdatedAt = time.Now()
	return nil
}

// Helper methods

func isValidBuildingType(buildingType BuildingType) bool {
	validTypes := []BuildingType{
		BuildingTypeOffice, BuildingTypeResidential, BuildingTypeCommercial,
		BuildingTypeIndustrial, BuildingTypeEducational, BuildingTypeHealthcare,
		BuildingTypeRetail, BuildingTypeWarehouse, BuildingTypeMixed,
	}

	for _, validType := range validTypes {
		if buildingType == validType {
			return true
		}
	}
	return false
}

func isValidBuildingStatus(status BuildingStatus) bool {
	validStatuses := []BuildingStatus{
		BuildingStatusActive, BuildingStatusInactive, BuildingStatusMaintenance,
		BuildingStatusConstruction, BuildingStatusDemolished,
	}

	for _, validStatus := range validStatuses {
		if status == validStatus {
			return true
		}
	}
	return false
}

func (bm *BuildingManager) validateSpatialReference(ref *Point3D) error {
	if ref.X < 0 || ref.Y < 0 || ref.Z < 0 {
		return errors.New(errors.CodeInvalidInput, "Spatial reference coordinates must be positive")
	}

	return nil
}

func (bm *BuildingManager) validateFloor(floor *FloorPlan) error {
	if floor.ID == "" {
		return errors.New(errors.CodeInvalidInput, "Floor ID is required")
	}

	if floor.Name == "" {
		return errors.New(errors.CodeInvalidInput, "Floor name is required")
	}

	return nil
}

func (bm *BuildingManager) validateEquipment(equipment *Equipment) error {
	if equipment.ID == "" {
		return errors.New(errors.CodeInvalidInput, "Equipment ID is required")
	}

	if equipment.Name == "" {
		return errors.New(errors.CodeInvalidInput, "Equipment name is required")
	}

	if equipment.Type == "" {
		return errors.New(errors.CodeInvalidInput, "Equipment type is required")
	}

	return nil
}

// BuildingRepository defines the interface for building data persistence
type BuildingRepository interface {
	// Basic CRUD operations
	Create(building *EnhancedBuilding) error
	GetByID(id string) (*EnhancedBuilding, error)
	GetByUUID(uuid string) (*EnhancedBuilding, error)
	Update(building *EnhancedBuilding) error
	Delete(id string) error

	// Query operations
	Search(query *BuildingQuery) ([]*EnhancedBuilding, error)
	List(limit, offset int) ([]*EnhancedBuilding, error)
	Count() (int, error)

	// Spatial operations
	FindNear(point *Point3D, radius float64) ([]*EnhancedBuilding, error)
	FindWithinBounds(bounds *BoundingBox) ([]*EnhancedBuilding, error)

	// Statistics
	GetStats() (*BuildingStats, error)
	GetStatsByType(buildingType BuildingType) (*BuildingStats, error)
}
