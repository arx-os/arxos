package models

import (
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

// UpdateUserRequest defines the request for updating a user
type UpdateUserRequest struct {
	Name        *string  `json:"name,omitempty"`
	Email       *string  `json:"email,omitempty"`
	Password    *string  `json:"password,omitempty"`
	Role        *string  `json:"role,omitempty"`
	OrgID       *string  `json:"org_id,omitempty"`
	Permissions []string `json:"permissions,omitempty"`
	Active      *bool    `json:"active,omitempty"`
	Status      *string  `json:"status,omitempty"`
}

// ChangePasswordRequest defines the request for changing a password
type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password" validate:"required"`
	NewPassword     string `json:"new_password" validate:"required,min=8"`
}

// UserResponse represents a user in API responses
type UserResponse struct {
	ID        string    `json:"id"`
	Email     string    `json:"email"`
	Name      string    `json:"name"`
	Role      string    `json:"role"`
	Status    string    `json:"status"`
	OrgID     string    `json:"org_id,omitempty"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// OrganizationFilter defines filtering options for listing organizations
type OrganizationFilter struct {
	Plan   string `json:"plan,omitempty"`
	Active *bool  `json:"active,omitempty"`
}

// CreateOrganizationRequest defines the request for creating an organization
type CreateOrganizationRequest struct {
	Name        string `json:"name" validate:"required"`
	Description string `json:"description"`
	Plan        string `json:"plan" validate:"required,oneof=free starter professional enterprise"`
}

// UpdateOrganizationRequest defines the request for updating an organization
type UpdateOrganizationRequest struct {
	Name        *string `json:"name,omitempty"`
	Description *string `json:"description,omitempty"`
	Plan        *string `json:"plan,omitempty"`
	Active      *bool   `json:"active,omitempty"`
	Website     *string `json:"website,omitempty"`
	Address     *string `json:"address,omitempty"`
	Phone       *string `json:"phone,omitempty"`
}

// AddMemberRequest defines the request for adding a member to an organization
type AddMemberRequest struct {
	UserID string `json:"user_id" validate:"required"`
	Role   string `json:"role" validate:"required"`
}

// UpdateMemberRoleRequest defines the request for updating a member's role
type UpdateMemberRoleRequest struct {
	Role string `json:"role" validate:"required"`
}

// CreateInvitationRequest defines the request for creating an organization invitation
type CreateInvitationRequest struct {
	Email string `json:"email" validate:"required,email"`
	Role  string `json:"role" validate:"required"`
}

// AcceptInvitationRequest defines the request for accepting an organization invitation
type AcceptInvitationRequest struct {
	Token string `json:"token" validate:"required"`
}

// BuildingFilter defines filtering options for listing buildings
type BuildingFilter struct {
	OrgID  string `json:"org_id,omitempty"`
	Status string `json:"status,omitempty"`
}

// CreateBuildingRequest defines the request for creating a building
type CreateBuildingRequest struct {
	Name        string  `json:"name" validate:"required"`
	Description string  `json:"description"`
	Address     string  `json:"address"`
	Latitude    float64 `json:"latitude"`
	Longitude   float64 `json:"longitude"`
	OrgID       string  `json:"org_id,omitempty"`
}

// UpdateBuildingRequest defines the request for updating a building
type UpdateBuildingRequest struct {
	Name        *string  `json:"name,omitempty"`
	Description *string  `json:"description,omitempty"`
	Address     *string  `json:"address,omitempty"`
	Latitude    *float64 `json:"latitude,omitempty"`
	Longitude   *float64 `json:"longitude,omitempty"`
	Status      *string  `json:"status,omitempty"`
}

// CreateEquipmentRequest defines the request for creating equipment
type CreateEquipmentRequest struct {
	Name        string  `json:"name" validate:"required"`
	Type        string  `json:"type" validate:"required"`
	Description string  `json:"description"`
	BuildingID  string  `json:"building_id" validate:"required"`
	RoomID      string  `json:"room_id,omitempty"`
	Latitude    float64 `json:"latitude"`
	Longitude   float64 `json:"longitude"`
	Elevation   float64 `json:"elevation"`
	X           float64 `json:"x"`
	Y           float64 `json:"y"`
	Z           float64 `json:"z"`
}

// UpdateEquipmentRequest defines the request for updating equipment
type UpdateEquipmentRequest struct {
	Name        *string  `json:"name,omitempty"`
	Type        *string  `json:"type,omitempty"`
	Description *string  `json:"description,omitempty"`
	RoomID      *string  `json:"room_id,omitempty"`
	Latitude    *float64 `json:"latitude,omitempty"`
	Longitude   *float64 `json:"longitude,omitempty"`
	Elevation   *float64 `json:"elevation,omitempty"`
	Status      *string  `json:"status,omitempty"`
	X           *float64 `json:"x,omitempty"`
	Y           *float64 `json:"y,omitempty"`
	Z           *float64 `json:"z,omitempty"`
}

// HealthResponse represents health check response
type HealthResponse struct {
	Status    string                 `json:"status"`
	Version   string                 `json:"version"`
	Timestamp time.Time              `json:"timestamp"`
	Checks    map[string]interface{} `json:"checks,omitempty"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Code    string `json:"code"`
	Details string `json:"details,omitempty"`
}

// PaginationRequest represents pagination parameters
type PaginationRequest struct {
	Page     int `json:"page" form:"page"`
	PageSize int `json:"page_size" form:"page_size"`
}

// PaginationResponse represents pagination metadata
type PaginationResponse struct {
	Page       int   `json:"page"`
	PageSize   int   `json:"page_size"`
	Total      int64 `json:"total"`
	TotalPages int   `json:"total_pages"`
}

// OrganizationResponse represents an organization in API responses
type OrganizationResponse struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Plan        string    `json:"plan"`
	Status      string    `json:"status"`
	MemberCount int       `json:"member_count"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// BuildingResponse represents a building in API responses
type BuildingResponse struct {
	ID             string    `json:"id"`
	Name           string    `json:"name"`
	Description    string    `json:"description"`
	Address        string    `json:"address"`
	Latitude       float64   `json:"latitude"`
	Longitude      float64   `json:"longitude"`
	Origin         string    `json:"origin"`
	Status         string    `json:"status"`
	RoomCount      int       `json:"room_count"`
	EquipmentCount int       `json:"equipment_count"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

// EquipmentResponse represents equipment in API responses
type EquipmentResponse struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Type        string    `json:"type"`
	Description string    `json:"description"`
	BuildingID  string    `json:"building_id"`
	RoomID      string    `json:"room_id"`
	Latitude    float64   `json:"latitude"`
	Longitude   float64   `json:"longitude"`
	Elevation   float64   `json:"elevation"`
	Status      string    `json:"status"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// UploadRequest represents a file upload request
type UploadRequest struct {
	FileName   string `json:"file_name"`
	FileType   string `json:"file_type"`
	FileSize   int64  `json:"file_size"`
	BuildingID string `json:"building_id"`
}

// RefreshTokenRequest represents a token refresh request
type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}

// PasswordResetRequest represents a password reset request
type PasswordResetRequest struct {
	Email string `json:"email" validate:"required,email"`
}

// PasswordResetConfirmRequest represents password reset confirmation
type PasswordResetConfirmRequest struct {
	Token       string `json:"token" validate:"required"`
	NewPassword string `json:"new_password" validate:"required,min=8"`
}

// SuccessResponse represents a successful operation response
type SuccessResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Message string      `json:"message"`
}

// PaginatedResponse represents a paginated response
type PaginatedResponse struct {
	Data       interface{}    `json:"data"`
	Pagination PaginationInfo `json:"pagination"`
}

// PaginationInfo represents pagination metadata
type PaginationInfo struct {
	Page       int   `json:"page"`
	PageSize   int   `json:"page_size"`
	Total      int64 `json:"total"`
	TotalPages int   `json:"total_pages"`
}

// UserToResponse converts a domain User to UserResponse
func UserToResponse(user *models.User) UserResponse {
	return UserResponse{
		ID:        user.ID,
		Email:     user.Email,
		Name:      user.FullName,
		Role:      string(user.Role),
		Status:    "active", // Placeholder - domain model doesn't have status
		OrgID:     "",       // Placeholder - domain model doesn't have org_id directly
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}
}

// OrganizationToResponse converts a domain Organization to OrganizationResponse
func OrganizationToResponse(org *models.Organization) OrganizationResponse {
	return OrganizationResponse{
		ID:          org.ID,
		Name:        org.Name,
		Description: org.Description,
		Plan:        string(org.Plan), // Convert Plan type to string
		Status:      "active",         // Placeholder - domain model doesn't have status
		MemberCount: 0,                // Placeholder - domain model doesn't have Members field
		CreatedAt:   org.CreatedAt,
		UpdatedAt:   org.UpdatedAt,
	}
}

// BuildingToResponse converts a domain Building to BuildingResponse
func BuildingToResponse(building *models.Building) BuildingResponse {
	return BuildingResponse{
		ID:             building.ID,
		Name:           building.Name,
		Description:    building.Description,
		Address:        building.Address,
		Latitude:       0.0,      // Placeholder - domain model doesn't have Latitude field
		Longitude:      0.0,      // Placeholder - domain model doesn't have Longitude field
		Origin:         "manual", // Placeholder - domain model doesn't have Origin field
		Status:         "active", // Placeholder - domain model doesn't have Status field
		RoomCount:      0,        // Placeholder - domain model doesn't have Rooms field
		EquipmentCount: 0,        // Placeholder - domain model doesn't have Equipment field
		CreatedAt:      building.CreatedAt,
		UpdatedAt:      building.UpdatedAt,
	}
}

// EquipmentToResponse converts a domain Equipment to EquipmentResponse
func EquipmentToResponse(equipment *models.Equipment) EquipmentResponse {
	// Extract position data if available
	latitude := 0.0
	longitude := 0.0
	elevation := 0.0
	if equipment.Location != nil {
		latitude = equipment.Location.X  // Using X as latitude placeholder
		longitude = equipment.Location.Y // Using Y as longitude placeholder
		elevation = equipment.Location.Z // Using Z as elevation
	}

	return EquipmentResponse{
		ID:          equipment.ID,
		Name:        equipment.Name,
		Type:        equipment.Type,
		Description: equipment.Notes, // Using Notes as description
		BuildingID:  "",              // Placeholder - not directly available
		RoomID:      equipment.RoomID,
		Latitude:    latitude,
		Longitude:   longitude,
		Elevation:   elevation,
		Status:      equipment.Status,
		CreatedAt:   time.Time{}, // Placeholder - not available in domain model
		UpdatedAt:   time.Time{}, // Placeholder - not available in domain model
	}
}
