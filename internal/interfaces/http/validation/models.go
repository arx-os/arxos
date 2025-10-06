package validation

import "time"

// Request validation models with comprehensive validation tags

// UserRequest represents user-related request validation
type CreateUserRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Name     string `json:"name" validate:"required,min=2,max=100"`
	Role     string `json:"role" validate:"required,oneof=admin user manager viewer"`
	Password string `json:"password" validate:"required,min=8,max=128"`
}

type UpdateUserRequest struct {
	ID     string `json:"id" validate:"required,uuid"`
	Name   string `json:"name" validate:"min=2,max=100"`
	Role   string `json:"role" validate:"oneof=admin user manager viewer"`
	Active *bool  `json:"active"`
}

type UserQueryParams struct {
	Limit  int    `json:"limit" validate:"min=1,max=100"`
	Offset int    `json:"offset" validate:"min=0"`
	Role   string `json:"role" validate:"oneof=admin user manager viewer"`
	Active string `json:"active" validate:"oneof=true false"`
}

// OrganizationRequest represents organization-related request validation
type CreateOrganizationRequest struct {
	Name        string `json:"name" validate:"required,min=2,max=100"`
	Description string `json:"description" validate:"max=500"`
	Plan        string `json:"plan" validate:"required,oneof=free basic premium enterprise"`
}

type UpdateOrganizationRequest struct {
	ID          string `json:"id" validate:"required,uuid"`
	Name        string `json:"name" validate:"min=2,max=100"`
	Description string `json:"description" validate:"max=500"`
	Plan        string `json:"plan" validate:"oneof=free basic premium enterprise"`
	Active      *bool  `json:"active"`
}

type OrganizationQueryParams struct {
	Limit  int    `json:"limit" validate:"min=1,max=100"`
	Offset int    `json:"offset" validate:"min=0"`
	Plan   string `json:"plan" validate:"oneof=free basic premium enterprise"`
	Active string `json:"active" validate:"oneof=true false"`
}

// BuildingRequest represents building-related request validation
type CreateBuildingRequest struct {
	Name        string  `json:"name" validate:"required,min=2,max=100"`
	Address     string  `json:"address" validate:"required,min=5,max=200"`
	Latitude    float64 `json:"latitude" validate:"min=-90,max=90"`
	Longitude   float64 `json:"longitude" validate:"min=-180,max=180"`
	Description string  `json:"description" validate:"max=500"`
}

type UpdateBuildingRequest struct {
	ID          string   `json:"id" validate:"required,uuid"`
	Name        string   `json:"name" validate:"min=2,max=100"`
	Address     string   `json:"address" validate:"min=5,max=200"`
	Latitude    *float64 `json:"latitude" validate:"min=-90,max=90"`
	Longitude   *float64 `json:"longitude" validate:"min=-180,max=180"`
	Description string   `json:"description" validate:"max=500"`
}

type BuildingQueryParams struct {
	Limit   int    `json:"limit" validate:"min=1,max=100"`
	Offset  int    `json:"offset" validate:"min=0"`
	Name    string `json:"name" validate:"max=100"`
	Address string `json:"address" validate:"max=200"`
}

// EquipmentRequest represents equipment-related request validation
type CreateEquipmentRequest struct {
	Name             string `json:"name" validate:"required,min=2,max=100"`
	BuildingID       string `json:"building_id" validate:"required,uuid"`
	FloorID          string `json:"floor_id" validate:"uuid"`
	RoomID           string `json:"room_id" validate:"uuid"`
	Type             string `json:"type" validate:"required,equipment_type"`
	Manufacturer     string `json:"manufacturer" validate:"max=100"`
	Model            string `json:"model" validate:"max=100"`
	SerialNumber     string `json:"serial_number" validate:"max=100"`
	InstallationDate string `json:"installation_date" validate:"date"`
	WarrantyExpiry   string `json:"warranty_expiry" validate:"date"`
	Status           string `json:"status" validate:"oneof=operational maintenance offline retired"`
	Description      string `json:"description" validate:"max=500"`
}

type UpdateEquipmentRequest struct {
	ID               string `json:"id" validate:"required,uuid"`
	Name             string `json:"name" validate:"min=2,max=100"`
	FloorID          string `json:"floor_id" validate:"uuid"`
	RoomID           string `json:"room_id" validate:"uuid"`
	Type             string `json:"type" validate:"equipment_type"`
	Manufacturer     string `json:"manufacturer" validate:"max=100"`
	Model            string `json:"model" validate:"max=100"`
	SerialNumber     string `json:"serial_number" validate:"max=100"`
	InstallationDate string `json:"installation_date" validate:"date"`
	WarrantyExpiry   string `json:"warranty_expiry" validate:"date"`
	Status           string `json:"status" validate:"oneof=operational maintenance offline retired"`
	Description      string `json:"description" validate:"max=500"`
}

type EquipmentQueryParams struct {
	Limit      int    `json:"limit" validate:"min=1,max=100"`
	Offset     int    `json:"offset" validate:"min=0"`
	BuildingID string `json:"building_id" validate:"uuid"`
	FloorID    string `json:"floor_id" validate:"uuid"`
	RoomID     string `json:"room_id" validate:"uuid"`
	Type       string `json:"type" validate:"equipment_type"`
	Status     string `json:"status" validate:"oneof=operational maintenance offline retired"`
}

// ComponentRequest represents component-related request validation
type CreateComponentRequest struct {
	Name       string         `json:"name" validate:"required,min=2,max=100"`
	Type       string         `json:"type" validate:"required,component_type"`
	Path       string         `json:"path" validate:"required,building_path"`
	Location   map[string]any `json:"location"`
	Properties map[string]any `json:"properties"`
	Building   string         `json:"building" validate:"required,uuid"`
	Floor      string         `json:"floor" validate:"uuid"`
	Room       string         `json:"room" validate:"uuid"`
}

type UpdateComponentRequest struct {
	ID         string         `json:"id" validate:"required,uuid"`
	Name       string         `json:"name" validate:"min=2,max=100"`
	Type       string         `json:"type" validate:"component_type"`
	Path       string         `json:"path" validate:"building_path"`
	Location   map[string]any `json:"location"`
	Properties map[string]any `json:"properties"`
	Building   string         `json:"building" validate:"uuid"`
	Floor      string         `json:"floor" validate:"uuid"`
	Room       string         `json:"room" validate:"uuid"`
}

type ComponentQueryParams struct {
	Limit    int    `json:"limit" validate:"min=1,max=100"`
	Offset   int    `json:"offset" validate:"min=0"`
	Type     string `json:"type" validate:"component_type"`
	Status   string `json:"status" validate:"oneof=active inactive maintenance"`
	Building string `json:"building" validate:"uuid"`
	Floor    string `json:"floor" validate:"uuid"`
	Room     string `json:"room" validate:"uuid"`
}

// IFCRequest represents IFC-related request validation
type ImportIFCRequest struct {
	RepositoryID string `json:"repository_id" validate:"required,uuid"`
	IFCData      string `json:"ifc_data" validate:"required"`
	FileName     string `json:"file_name" validate:"required,min=1,max=255"`
	FileSize     int64  `json:"file_size" validate:"min=1,max=1073741824"` // Max 1GB
	Version      string `json:"version" validate:"oneof=IFC2x3 IFC4 IFC4x1 IFC4x2 IFC4x3"`
	Discipline   string `json:"discipline" validate:"oneof=architectural structural hvac electrical plumbing fire_safety"`
}

type ExportIFCRequest struct {
	BuildingID string `json:"building_id" validate:"required,uuid"`
	Version    string `json:"version" validate:"required,oneof=IFC2x3 IFC4 IFC4x1 IFC4x2 IFC4x3"`
	Discipline string `json:"discipline" validate:"oneof=architectural structural hvac electrical plumbing fire_safety"`
	Format     string `json:"format" validate:"oneof=ifc step xml"`
}

type IFCQueryParams struct {
	Limit      int    `json:"limit" validate:"min=1,max=100"`
	Offset     int    `json:"offset" validate:"min=0"`
	BuildingID string `json:"building_id" validate:"uuid"`
	Version    string `json:"version" validate:"oneof=IFC2x3 IFC4 IFC4x1 IFC4x2 IFC4x3"`
	Discipline string `json:"discipline" validate:"oneof=architectural structural hvac electrical plumbing fire_safety"`
	Status     string `json:"status" validate:"oneof=pending processing completed failed"`
}

// AuthenticationRequest represents authentication-related request validation
type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required,min=8,max=128"`
}

type RegisterRequest struct {
	Email        string `json:"email" validate:"required,email"`
	Name         string `json:"name" validate:"required,min=2,max=100"`
	Password     string `json:"password" validate:"required,min=8,max=128"`
	Organization string `json:"organization" validate:"required,min=2,max=100"`
}

type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}

type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password" validate:"required"`
	NewPassword     string `json:"new_password" validate:"required,min=8,max=128"`
}

// Common query parameters for pagination
type PaginationParams struct {
	Limit  int `json:"limit" validate:"min=1,max=100"`
	Offset int `json:"offset" validate:"min=0"`
}

// Common query parameters for sorting
type SortParams struct {
	SortBy    string `json:"sort_by" validate:"alphanumeric"`
	SortOrder string `json:"sort_order" validate:"oneof=asc desc"`
}

// Common query parameters for filtering by date range
type DateRangeParams struct {
	StartDate string `json:"start_date" validate:"date"`
	EndDate   string `json:"end_date" validate:"date"`
}

// Validation helper functions

// ValidatePagination validates pagination parameters
func ValidatePagination(limit, offset int) map[string]string {
	errors := make(map[string]string)

	if limit < 1 || limit > 100 {
		errors["limit"] = "limit must be between 1 and 100"
	}

	if offset < 0 {
		errors["offset"] = "offset must be non-negative"
	}

	return errors
}

// ValidateDateRange validates date range parameters
func ValidateDateRange(startDate, endDate string) map[string]string {
	errors := make(map[string]string)

	if startDate != "" && endDate != "" {
		start, err1 := time.Parse("2006-01-02", startDate)
		end, err2 := time.Parse("2006-01-02", endDate)

		if err1 != nil {
			errors["start_date"] = "start_date must be a valid date (YYYY-MM-DD)"
		}
		if err2 != nil {
			errors["end_date"] = "end_date must be a valid date (YYYY-MM-DD)"
		}

		if err1 == nil && err2 == nil && start.After(end) {
			errors["date_range"] = "start_date must be before or equal to end_date"
		}
	}

	return errors
}
