package models

import "time"

// LoginRequest represents a login request
type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required,min=1"`
}

// RefreshTokenRequest represents a token refresh request
type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}

// CreateBuildingRequest represents a request to create a building
type CreateBuildingRequest struct {
	ArxosID   string                 `json:"arxos_id" validate:"required,arxos_id"`
	Name      string                 `json:"name" validate:"required,min=1,max=200"`
	OrgID     string                 `json:"org_id" validate:"required,uuid"`
	Address   string                 `json:"address" validate:"max=500"`
	City      string                 `json:"city" validate:"max=100"`
	State     string                 `json:"state" validate:"max=100"`
	Country   string                 `json:"country" validate:"max=100"`
	Latitude  float64                `json:"latitude" validate:"omitempty,gps_latitude,gte=-90,lte=90"`
	Longitude float64                `json:"longitude" validate:"omitempty,gps_longitude,gte=-180,lte=180"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// UpdateBuildingRequest represents a request to update a building
type UpdateBuildingRequest struct {
	Name        *string                `json:"name,omitempty" validate:"omitempty,min=1,max=200"`
	Description *string                `json:"description,omitempty" validate:"omitempty,max=1000"`
	Status      *string                `json:"status,omitempty" validate:"omitempty,building_status"`
	Address     *string                `json:"address,omitempty" validate:"omitempty,max=500"`
	City        *string                `json:"city,omitempty" validate:"omitempty,max=100"`
	State       *string                `json:"state,omitempty" validate:"omitempty,max=100"`
	Country     *string                `json:"country,omitempty" validate:"omitempty,max=100"`
	Latitude    *float64               `json:"latitude,omitempty" validate:"omitempty,gps_latitude,gte=-90,lte=90"`
	Longitude   *float64               `json:"longitude,omitempty" validate:"omitempty,gps_longitude,gte=-180,lte=180"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// CreateEquipmentRequest represents a request to create equipment
type CreateEquipmentRequest struct {
	Name       string                 `json:"name" validate:"required,min=1,max=200"`
	Type       string                 `json:"type" validate:"required,min=1,max=100"`
	BuildingID string                 `json:"building_id" validate:"required,uuid"`
	Path       string                 `json:"path" validate:"omitempty,building_path"`
	FloorID    string                 `json:"floor_id" validate:"omitempty,uuid"`
	RoomID     string                 `json:"room_id" validate:"omitempty,uuid"`
	Status     string                 `json:"status" validate:"required,equipment_status"`
	Model      string                 `json:"model" validate:"max=200"`
	Serial     string                 `json:"serial" validate:"max=200"`
	Location   *Point3D               `json:"location,omitempty"`
	X          *float64               `json:"x,omitempty"`
	Y          *float64               `json:"y,omitempty"`
	Z          *float64               `json:"z,omitempty"`
	Metadata   map[string]interface{} `json:"metadata"`
}

// UpdateEquipmentRequest represents a request to update equipment
type UpdateEquipmentRequest struct {
	Name     *string                `json:"name,omitempty" validate:"omitempty,min=1,max=200"`
	Type     *string                `json:"type,omitempty" validate:"omitempty,min=1,max=100"`
	Status   *string                `json:"status,omitempty" validate:"omitempty,equipment_status"`
	Model    *string                `json:"model,omitempty" validate:"omitempty,max=200"`
	Serial   *string                `json:"serial,omitempty" validate:"omitempty,max=200"`
	Location *Point3D               `json:"location,omitempty"`
	X        *float64               `json:"x,omitempty"`
	Y        *float64               `json:"y,omitempty"`
	Z        *float64               `json:"z,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// Point3D represents a 3D point with validation
type Point3D struct {
	X float64 `json:"x" validate:"required"`
	Y float64 `json:"y" validate:"required"`
	Z float64 `json:"z" validate:"required"`
}

// SpatialQueryRequest represents a spatial query request
type SpatialQueryRequest struct {
	Center *Point3D `json:"center" validate:"required"`
	Radius float64  `json:"radius" validate:"required,gt=0,lte=100000"` // Max 100km
	Type   string   `json:"type" validate:"omitempty"`
	Limit  int      `json:"limit" validate:"omitempty,min=1,max=1000"`
	Offset int      `json:"offset" validate:"omitempty,min=0"`
}

// BoundingBoxRequest represents a bounding box query request
type BoundingBoxRequest struct {
	MinPoint *Point3D `json:"min_point" validate:"required"`
	MaxPoint *Point3D `json:"max_point" validate:"required"`
	Type     string   `json:"type" validate:"omitempty"`
	Limit    int      `json:"limit" validate:"omitempty,min=1,max=1000"`
}

// UploadRequest represents a file upload request
type UploadRequest struct {
	FileType   string `json:"file_type" validate:"required,oneof=ifc pdf csv json bim"`
	BuildingID string `json:"building_id" validate:"required,uuid"`
	FileName   string `json:"file_name" validate:"required,min=1,max=255"`
	FileSize   int64  `json:"file_size" validate:"required,gt=0,lte=104857600"` // Max 100MB
}

// CreateOrganizationRequest represents a request to create an organization
type CreateOrganizationRequest struct {
	Name        string `json:"name" validate:"required,min=2,max=200"`
	Description string `json:"description" validate:"max=1000"`
	Plan        string `json:"plan" validate:"required,oneof=free starter professional enterprise"`
}

// UpdateOrganizationRequest represents a request to update an organization
type UpdateOrganizationRequest struct {
	Name        *string `json:"name,omitempty" validate:"omitempty,min=2,max=200"`
	Description *string `json:"description,omitempty" validate:"omitempty,max=1000"`
	Plan        *string `json:"plan,omitempty" validate:"omitempty,oneof=free starter professional enterprise"`
	Website     *string `json:"website,omitempty" validate:"omitempty,url"`
	Address     *string `json:"address,omitempty" validate:"omitempty,max=500"`
	Phone       *string `json:"phone,omitempty" validate:"omitempty,max=20"`
}

// HealthResponse represents a health check response
type HealthResponse struct {
	Status    string                 `json:"status"`
	Version   string                 `json:"version"`
	Timestamp time.Time              `json:"timestamp"`
	Checks    map[string]interface{} `json:"checks"`
}

// ErrorResponse represents an API error response
type ErrorResponse struct {
	Error   string                 `json:"error"`
	Code    string                 `json:"code"`
	Details map[string]interface{} `json:"details,omitempty"`
}

// PaginationResponse represents pagination metadata
type PaginationResponse struct {
	Total  int `json:"total"`
	Limit  int `json:"limit"`
	Offset int `json:"offset"`
	Page   int `json:"page"`
	Pages  int `json:"pages"`
}

// SuccessResponse represents a generic success response
type SuccessResponse struct {
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data"`
}

// PaginatedResponse represents a paginated response
type PaginatedResponse struct {
	Data       interface{}    `json:"data"`
	Pagination PaginationInfo `json:"pagination"`
}

// PaginationInfo contains pagination metadata
type PaginationInfo struct {
	Page       int   `json:"page"`
	PageSize   int   `json:"page_size"`
	Total      int64 `json:"total"`
	TotalPages int   `json:"total_pages"`
}

// UpdateUserRequest represents a request to update a user
type UpdateUserRequest struct {
	Name     *string `json:"name,omitempty" validate:"omitempty,min=2,max=100"`
	Email    *string `json:"email,omitempty" validate:"omitempty,email"`
	Password *string `json:"password,omitempty" validate:"omitempty,min=8,max=72"`
	Role     *string `json:"role,omitempty" validate:"omitempty,oneof=admin manager technician viewer"`
	Status   *string `json:"status,omitempty" validate:"omitempty,oneof=active inactive suspended"`
	OrgID    *string `json:"org_id,omitempty" validate:"omitempty,uuid"`
}

// ChangePasswordRequest represents a password change request
type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password" validate:"required"`
	NewPassword     string `json:"new_password" validate:"required,min=8,max=72"`
}

// PasswordResetRequest represents a password reset request
type PasswordResetRequest struct {
	Email string `json:"email" validate:"required,email"`
}

// PasswordResetConfirmRequest represents a password reset confirmation
type PasswordResetConfirmRequest struct {
	Token       string `json:"token" validate:"required"`
	NewPassword string `json:"new_password" validate:"required,min=8,max=72"`
}

// AddMemberRequest represents a request to add a member to an organization
type AddMemberRequest struct {
	Email  string `json:"email" validate:"required,email"`
	UserID string `json:"user_id" validate:"omitempty,uuid"`
	Role   string `json:"role" validate:"required,oneof=admin manager member viewer"`
}

// UpdateMemberRoleRequest represents a request to update a member's role
type UpdateMemberRoleRequest struct {
	Role string `json:"role" validate:"required,oneof=admin manager member viewer"`
}

// CreateInvitationRequest represents a request to create an invitation
type CreateInvitationRequest struct {
	Email string `json:"email" validate:"required,email"`
	Role  string `json:"role" validate:"required,oneof=admin manager member viewer"`
}

// AcceptInvitationRequest represents a request to accept an invitation
type AcceptInvitationRequest struct {
	Token string `json:"token" validate:"required"`
}

// OrganizationFilter represents filters for listing organizations
type OrganizationFilter struct {
	Plan   string `json:"plan,omitempty"`
	Active *bool  `json:"active,omitempty"`
}
