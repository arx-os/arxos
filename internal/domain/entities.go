package domain

import (
	"time"
)

// Core domain entities following Clean Architecture principles

// User represents a user in the system
type User struct {
	ID        string    `json:"id"`
	Email     string    `json:"email"`
	Name      string    `json:"name"`
	Role      string    `json:"role"`
	Active    bool      `json:"active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// Organization represents an organization in the system
type Organization struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Plan        string    `json:"plan"`
	Active      bool      `json:"active"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// Building represents a building in the system
type Building struct {
	ID          string       `json:"id"`
	Name        string       `json:"name"`
	Address     string       `json:"address"`
	Coordinates *Location    `json:"coordinates,omitempty"`
	Floors      []*Floor     `json:"floors,omitempty"`
	Equipment   []*Equipment `json:"equipment,omitempty"`
	CreatedAt   time.Time    `json:"created_at"`
	UpdatedAt   time.Time    `json:"updated_at"`
}

// Floor represents a floor within a building
type Floor struct {
	ID         string       `json:"id"`
	BuildingID string       `json:"building_id"`
	Name       string       `json:"name"`
	Level      int          `json:"level"`
	Rooms      []*Room      `json:"rooms,omitempty"`
	Equipment  []*Equipment `json:"equipment,omitempty"`
	CreatedAt  time.Time    `json:"created_at"`
	UpdatedAt  time.Time    `json:"updated_at"`
}

// Room represents a room within a floor
type Room struct {
	ID        string       `json:"id"`
	FloorID   string       `json:"floor_id"`
	Name      string       `json:"name"`
	Number    string       `json:"number"`
	Equipment []*Equipment `json:"equipment,omitempty"`
	CreatedAt time.Time    `json:"created_at"`
	UpdatedAt time.Time    `json:"updated_at"`
}

// Equipment represents equipment within a building
type Equipment struct {
	ID         string    `json:"id"`
	BuildingID string    `json:"building_id"`
	FloorID    string    `json:"floor_id,omitempty"`
	RoomID     string    `json:"room_id,omitempty"`
	Name       string    `json:"name"`
	Type       string    `json:"type"`
	Model      string    `json:"model,omitempty"`
	Location   *Location `json:"location,omitempty"`
	Status     string    `json:"status"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}

// Location represents spatial coordinates
type Location struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// Request/Response DTOs

// CreateUserRequest represents the request to create a user
type CreateUserRequest struct {
	Email string `json:"email" validate:"required,email"`
	Name  string `json:"name" validate:"required"`
	Role  string `json:"role" validate:"required"`
}

// UpdateUserRequest represents the request to update a user
type UpdateUserRequest struct {
	ID     string  `json:"id" validate:"required"`
	Name   *string `json:"name,omitempty"`
	Role   *string `json:"role,omitempty"`
	Active *bool   `json:"active,omitempty"`
}

// CreateOrganizationRequest represents the request to create an organization
type CreateOrganizationRequest struct {
	Name        string `json:"name" validate:"required"`
	Description string `json:"description,omitempty"`
	Plan        string `json:"plan" validate:"required"`
}

// UpdateOrganizationRequest represents the request to update an organization
type UpdateOrganizationRequest struct {
	ID          string  `json:"id" validate:"required"`
	Name        *string `json:"name,omitempty"`
	Description *string `json:"description,omitempty"`
	Plan        *string `json:"plan,omitempty"`
	Active      *bool   `json:"active,omitempty"`
}

// CreateBuildingRequest represents the request to create a building
type CreateBuildingRequest struct {
	Name        string    `json:"name" validate:"required"`
	Address     string    `json:"address" validate:"required"`
	Coordinates *Location `json:"coordinates,omitempty"`
}

// UpdateBuildingRequest represents the request to update a building
type UpdateBuildingRequest struct {
	ID          string    `json:"id" validate:"required"`
	Name        *string   `json:"name,omitempty"`
	Address     *string   `json:"address,omitempty"`
	Coordinates *Location `json:"coordinates,omitempty"`
}

// CreateEquipmentRequest represents the request to create equipment
type CreateEquipmentRequest struct {
	BuildingID string    `json:"building_id" validate:"required"`
	FloorID    string    `json:"floor_id,omitempty"`
	RoomID     string    `json:"room_id,omitempty"`
	Name       string    `json:"name" validate:"required"`
	Type       string    `json:"type" validate:"required"`
	Model      string    `json:"model,omitempty"`
	Location   *Location `json:"location,omitempty"`
}

// UpdateEquipmentRequest represents the request to update equipment
type UpdateEquipmentRequest struct {
	ID       string    `json:"id" validate:"required"`
	Name     *string   `json:"name,omitempty"`
	Type     *string   `json:"type,omitempty"`
	Model    *string   `json:"model,omitempty"`
	Location *Location `json:"location,omitempty"`
	Status   *string   `json:"status,omitempty"`
}

// ImportBuildingRequest represents the request to import a building
type ImportBuildingRequest struct {
	Format string `json:"format" validate:"required"`
	Data   []byte `json:"data" validate:"required"`
}

// Filter structures for querying

// UserFilter represents filters for user queries
type UserFilter struct {
	Email  *string `json:"email,omitempty"`
	Role   *string `json:"role,omitempty"`
	Active *bool   `json:"active,omitempty"`
	Limit  int     `json:"limit,omitempty"`
	Offset int     `json:"offset,omitempty"`
}

// OrganizationFilter represents filters for organization queries
type OrganizationFilter struct {
	Name   *string `json:"name,omitempty"`
	Plan   *string `json:"plan,omitempty"`
	Active *bool   `json:"active,omitempty"`
	Limit  int     `json:"limit,omitempty"`
	Offset int     `json:"offset,omitempty"`
}

// BuildingFilter represents filters for building queries
type BuildingFilter struct {
	Name    *string `json:"name,omitempty"`
	Address *string `json:"address,omitempty"`
	Limit   int     `json:"limit,omitempty"`
	Offset  int     `json:"offset,omitempty"`
}

// EquipmentFilter represents filters for equipment queries
type EquipmentFilter struct {
	BuildingID *string `json:"building_id,omitempty"`
	FloorID    *string `json:"floor_id,omitempty"`
	RoomID     *string `json:"room_id,omitempty"`
	Type       *string `json:"type,omitempty"`
	Status     *string `json:"status,omitempty"`
	Limit      int     `json:"limit,omitempty"`
	Offset     int     `json:"offset,omitempty"`
}

// Analytics entities

// BuildingAnalytics represents analytics for a specific building
type BuildingAnalytics struct {
	BuildingID           string    `json:"building_id"`
	BuildingName         string    `json:"building_name"`
	TotalEquipment       int       `json:"total_equipment"`
	OperationalEquipment int       `json:"operational_equipment"`
	MaintenanceEquipment int       `json:"maintenance_equipment"`
	FailedEquipment      int       `json:"failed_equipment"`
	GeneratedAt          time.Time `json:"generated_at"`
}

// SystemAnalytics represents system-wide analytics
type SystemAnalytics struct {
	TotalBuildings       int       `json:"total_buildings"`
	TotalEquipment       int       `json:"total_equipment"`
	OperationalEquipment int       `json:"operational_equipment"`
	MaintenanceEquipment int       `json:"maintenance_equipment"`
	FailedEquipment      int       `json:"failed_equipment"`
	GeneratedAt          time.Time `json:"generated_at"`
}

// EquipmentAnalytics represents equipment analytics
type EquipmentAnalytics struct {
	TotalEquipment int            `json:"total_equipment"`
	ByType         map[string]int `json:"by_type"`
	ByStatus       map[string]int `json:"by_status"`
	GeneratedAt    time.Time      `json:"generated_at"`
}

// BuildingOps entities

// ControlEquipmentRequest represents a request to control equipment
type ControlEquipmentRequest struct {
	EquipmentID string         `json:"equipment_id" validate:"required"`
	Action      *ControlAction `json:"action" validate:"required"`
}

// ControlAction represents a control action for equipment
type ControlAction struct {
	Command string            `json:"command" validate:"required"`
	Params  map[string]string `json:"params,omitempty"`
}

// SetBuildingModeRequest represents a request to set building mode
type SetBuildingModeRequest struct {
	BuildingID string `json:"building_id" validate:"required"`
	Mode       string `json:"mode" validate:"required"`
}

// BuildingHealthReport represents a building health report
type BuildingHealthReport struct {
	BuildingID      string            `json:"building_id"`
	BuildingName    string            `json:"building_name"`
	OverallHealth   string            `json:"overall_health"`
	EquipmentHealth map[string]string `json:"equipment_health"`
	GeneratedAt     time.Time         `json:"generated_at"`
}

// ServiceHealth represents the health of a service
type ServiceHealth struct {
	ServiceName string                 `json:"service_name"`
	Status      string                 `json:"status"`
	LastCheck   time.Time              `json:"last_check"`
	Details     map[string]interface{} `json:"details"`
}

// FileEvent represents a file change event
type FileEvent struct {
	Path   string `json:"path"`
	Action string `json:"action"` // created, modified, deleted
}
