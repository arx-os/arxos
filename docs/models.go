package docs

import "time"

// LoginRequest represents a user login request
type LoginRequest struct {
	Email    string `json:"email" example:"user@example.com" validate:"required,email"`
	Password string `json:"password" example:"password123" validate:"required,min=8"`
}

// RegisterRequest represents a user registration request
type RegisterRequest struct {
	Email    string `json:"email" example:"user@example.com" validate:"required,email"`
	Password string `json:"password" example:"password123" validate:"required,min=8"`
	Name     string `json:"name" example:"John Doe" validate:"required,min=2"`
}

// AuthResponse represents an authentication response
type AuthResponse struct {
	AccessToken  string `json:"accessToken" example:"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`
	RefreshToken string `json:"refreshToken" example:"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`
	User         User   `json:"user"`
}

// User represents a user in the system
type User struct {
	ID           string    `json:"id" example:"user_123"`
	Email        string    `json:"email" example:"user@example.com"`
	Name         string    `json:"name" example:"John Doe"`
	Role         string    `json:"role" example:"user" enum:"admin,user,viewer"`
	OrgID        string    `json:"orgId,omitempty" example:"org_456"`
	CreatedAt    time.Time `json:"createdAt" example:"2023-01-01T00:00:00Z"`
	UpdatedAt    time.Time `json:"updatedAt" example:"2023-01-01T00:00:00Z"`
}

// FloorPlan represents a building floor plan
type FloorPlan struct {
	ID          string      `json:"id" example:"building_123"`
	Name        string      `json:"name" example:"Office Building A"`
	Building    string      `json:"building" example:"Main Campus"`
	Level       int         `json:"level" example:"1"`
	OrgID       string      `json:"organization_id,omitempty" example:"org_456"`
	Rooms       []Room      `json:"rooms,omitempty"`
	Equipment   []Equipment `json:"equipment,omitempty"`
	CreatedAt   time.Time   `json:"created_at" example:"2023-01-01T00:00:00Z"`
	UpdatedAt   time.Time   `json:"updated_at" example:"2023-01-01T00:00:00Z"`
}

// Room represents a room within a building
type Room struct {
	ID           string   `json:"id" example:"room_123"`
	Name         string   `json:"name" example:"Conference Room A"`
	Bounds       Bounds   `json:"bounds"`
	EquipmentIDs []string `json:"equipment_ids,omitempty"`
}

// Bounds represents spatial boundaries of a room
type Bounds struct {
	MinX float64 `json:"min_x" example:"0.0"`
	MinY float64 `json:"min_y" example:"0.0"`
	MaxX float64 `json:"max_x" example:"10.5"`
	MaxY float64 `json:"max_y" example:"8.0"`
}

// Equipment represents equipment within a building
type Equipment struct {
	ID               string                 `json:"id" example:"eq_123"`
	Name             string                 `json:"name" example:"HVAC Unit 1"`
	Type             string                 `json:"type" example:"hvac"`
	Location         Location               `json:"location,omitempty"`
	RoomID           string                 `json:"room_id,omitempty" example:"room_123"`
	Status           string                 `json:"status" example:"normal" enum:"normal,needs-repair,failed,unknown"`
	Notes            string                 `json:"notes,omitempty" example:"Regular maintenance completed"`
	MarkedBy         string                 `json:"marked_by,omitempty" example:"user_123"`
	MarkedAt         time.Time              `json:"marked_at,omitempty" example:"2023-01-01T00:00:00Z"`
	Manufacturer     string                 `json:"manufacturer,omitempty" example:"ACME Corp"`
	Model            string                 `json:"model,omitempty" example:"AC-2000"`
	SerialNumber     string                 `json:"serial_number,omitempty" example:"SN123456789"`
	InstallDate      time.Time              `json:"install_date,omitempty" example:"2022-01-01T00:00:00Z"`
	LastServiceDate  time.Time              `json:"last_service_date,omitempty" example:"2023-06-01T00:00:00Z"`
	Specifications   map[string]interface{} `json:"specifications,omitempty"`
}

// Location represents a 2D or 3D location
type Location struct {
	X float64 `json:"x" example:"5.5"`
	Y float64 `json:"y" example:"3.2"`
	Z float64 `json:"z,omitempty" example:"2.0"`
}

// Organization represents an organization/company
type Organization struct {
	ID          string    `json:"id" example:"org_123"`
	Name        string    `json:"name" example:"ACME Corporation"`
	Description string    `json:"description,omitempty" example:"Leading provider of widgets"`
	Status      string    `json:"status" example:"active" enum:"active,inactive,suspended"`
	CreatedAt   time.Time `json:"created_at" example:"2023-01-01T00:00:00Z"`
	UpdatedAt   time.Time `json:"updated_at" example:"2023-01-01T00:00:00Z"`
}

// OrganizationMember represents a member of an organization
type OrganizationMember struct {
	UserID string `json:"user_id" example:"user_123"`
	OrgID  string `json:"org_id" example:"org_123"`
	Role   string `json:"role" example:"member" enum:"owner,admin,member,viewer"`
	User   User   `json:"user,omitempty"`
}

// CreateOrganizationRequest represents a request to create an organization
type CreateOrganizationRequest struct {
	Name        string `json:"name" example:"ACME Corporation" validate:"required,min=2"`
	Description string `json:"description,omitempty" example:"Leading provider of widgets"`
}

// UpdateOrganizationRequest represents a request to update an organization
type UpdateOrganizationRequest struct {
	Name        string `json:"name,omitempty" example:"ACME Corporation"`
	Description string `json:"description,omitempty" example:"Leading provider of widgets"`
}

// AddMemberRequest represents a request to add a member to an organization
type AddMemberRequest struct {
	UserID string `json:"user_id" example:"user_123" validate:"required"`
	Role   string `json:"role" example:"member" validate:"required" enum:"owner,admin,member,viewer"`
}

// InviteMemberRequest represents a request to invite someone to an organization
type InviteMemberRequest struct {
	Email string `json:"email" example:"newuser@example.com" validate:"required,email"`
	Role  string `json:"role" example:"member" validate:"required" enum:"owner,admin,member,viewer"`
}

// UploadResponse represents a file upload response
type UploadResponse struct {
	Success         bool     `json:"success" example:"true"`
	Message         string   `json:"message" example:"PDF imported successfully"`
	BuildingID      string   `json:"building_id,omitempty" example:"building_123"`
	RoomsImported   int      `json:"rooms_imported,omitempty" example:"5"`
	EquipImported   int      `json:"equip_imported,omitempty" example:"12"`
	ImportDuration  string   `json:"import_duration,omitempty" example:"2.5s"`
	Warnings        []string `json:"warnings,omitempty"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error   string                 `json:"error" example:"Invalid request"`
	Details map[string]interface{} `json:"details,omitempty"`
}

// SuccessResponse represents a generic success response
type SuccessResponse struct {
	Success bool   `json:"success" example:"true"`
	Message string `json:"message" example:"Operation completed successfully"`
}

// HealthResponse represents a health check response
type HealthResponse struct {
	Status    string    `json:"status" example:"healthy"`
	Timestamp time.Time `json:"time" example:"2023-01-01T00:00:00Z"`
}

// ReadyResponse represents a readiness check response
type ReadyResponse struct {
	Ready bool `json:"ready" example:"true"`
}

// APIRootResponse represents the API root response
type APIRootResponse struct {
	Version   string            `json:"version" example:"1.0.0"`
	Name      string            `json:"name" example:"ArxOS API"`
	Endpoints map[string]string `json:"endpoints"`
}