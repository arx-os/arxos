package docs

import "time"

// LoginRequest represents login credentials
// @Description User login credentials
type LoginRequest struct {
	// Email address of the user
	// @example user@example.com
	Email string `json:"email" binding:"required" example:"user@example.com"`
	// User password
	// @example securepassword123
	Password string `json:"password" binding:"required" example:"securepassword123"`
}

// AuthResponse represents successful authentication
// @Description Authentication response with JWT tokens
type AuthResponse struct {
	// JWT access token
	AccessToken string `json:"access_token" example:"eyJhbGciOiJIUzI1NiIs..."`
	// JWT refresh token
	RefreshToken string `json:"refresh_token" example:"eyJhbGciOiJIUzI1NiIs..."`
	// Token expiration time in seconds
	ExpiresIn int `json:"expires_in" example:"3600"`
	// Token type
	TokenType string `json:"token_type" example:"Bearer"`
}

// BuildingRequest represents building creation/update data
// @Description Building information for creation or update
type BuildingRequest struct {
	// Building name
	Name string `json:"name" binding:"required" example:"Main Office Building"`
	// Building address
	Address string `json:"address" example:"123 Main St, City, State 12345"`
	// Building description
	Description string `json:"description" example:"5-story office building with parking garage"`
	// Number of floors
	Floors int `json:"floors" example:"5"`
	// Total area in square meters
	TotalArea float64 `json:"total_area" example:"10000.5"`
	// Building metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// BuildingResponse represents a building entity
// @Description Building information with metadata
type BuildingResponse struct {
	// Building ID
	ID string `json:"id" example:"bldg-123456"`
	// Building name
	Name string `json:"name" example:"Main Office Building"`
	// Building address
	Address string `json:"address" example:"123 Main St, City, State 12345"`
	// Building description
	Description string `json:"description" example:"5-story office building with parking garage"`
	// Number of floors
	Floors int `json:"floors" example:"5"`
	// Total area in square meters
	TotalArea float64 `json:"total_area" example:"10000.5"`
	// Organization ID
	OrganizationID string `json:"organization_id" example:"org-789012"`
	// Creation timestamp
	CreatedAt time.Time `json:"created_at" example:"2024-01-15T09:30:00Z"`
	// Last update timestamp
	UpdatedAt time.Time `json:"updated_at" example:"2024-01-20T14:45:00Z"`
	// Building metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// EquipmentRequest represents equipment creation/update data
// @Description Equipment information for creation or update
type EquipmentRequest struct {
	// Equipment name
	Name string `json:"name" binding:"required" example:"HVAC Unit 1"`
	// Equipment type
	Type string `json:"type" binding:"required" example:"hvac"`
	// Equipment model
	Model string `json:"model" example:"Carrier 38VRF"`
	// Serial number
	SerialNumber string `json:"serial_number" example:"SN-123456789"`
	// Installation date
	InstallationDate *time.Time `json:"installation_date" example:"2023-06-15T00:00:00Z"`
	// Room ID where equipment is located
	RoomID string `json:"room_id" example:"room-456"`
	// Equipment status
	Status string `json:"status" example:"operational"`
	// Equipment metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// EquipmentResponse represents an equipment entity
// @Description Equipment information with metadata
type EquipmentResponse struct {
	// Equipment ID
	ID string `json:"id" example:"equip-987654"`
	// Building ID
	BuildingID string `json:"building_id" example:"bldg-123456"`
	// Equipment name
	Name string `json:"name" example:"HVAC Unit 1"`
	// Equipment type
	Type string `json:"type" example:"hvac"`
	// Equipment model
	Model string `json:"model" example:"Carrier 38VRF"`
	// Serial number
	SerialNumber string `json:"serial_number" example:"SN-123456789"`
	// Installation date
	InstallationDate *time.Time `json:"installation_date" example:"2023-06-15T00:00:00Z"`
	// Room ID where equipment is located
	RoomID string `json:"room_id" example:"room-456"`
	// Equipment status
	Status string `json:"status" example:"operational"`
	// Creation timestamp
	CreatedAt time.Time `json:"created_at" example:"2024-01-15T09:30:00Z"`
	// Last update timestamp
	UpdatedAt time.Time `json:"updated_at" example:"2024-01-20T14:45:00Z"`
	// Equipment metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// RoomRequest represents room creation/update data
// @Description Room information for creation or update
type RoomRequest struct {
	// Room name or number
	Name string `json:"name" binding:"required" example:"Conference Room A"`
	// Room type
	Type string `json:"type" example:"conference"`
	// Floor number
	Floor int `json:"floor" example:"3"`
	// Room area in square meters
	Area float64 `json:"area" example:"50.5"`
	// Room capacity
	Capacity int `json:"capacity" example:"20"`
	// Room metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// RoomResponse represents a room entity
// @Description Room information with metadata
type RoomResponse struct {
	// Room ID
	ID string `json:"id" example:"room-456"`
	// Building ID
	BuildingID string `json:"building_id" example:"bldg-123456"`
	// Room name or number
	Name string `json:"name" example:"Conference Room A"`
	// Room type
	Type string `json:"type" example:"conference"`
	// Floor number
	Floor int `json:"floor" example:"3"`
	// Room area in square meters
	Area float64 `json:"area" example:"50.5"`
	// Room capacity
	Capacity int `json:"capacity" example:"20"`
	// Creation timestamp
	CreatedAt time.Time `json:"created_at" example:"2024-01-15T09:30:00Z"`
	// Last update timestamp
	UpdatedAt time.Time `json:"updated_at" example:"2024-01-20T14:45:00Z"`
	// Room metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// SearchRequest represents search parameters
// @Description Search query parameters
type SearchRequest struct {
	// Search query string
	Query string `json:"query" example:"conference room"`
	// Entity type to search
	Type string `json:"type" example:"room"`
	// Building ID to limit search
	BuildingID string `json:"building_id,omitempty" example:"bldg-123456"`
	// Maximum number of results
	Limit int `json:"limit" example:"20"`
	// Offset for pagination
	Offset int `json:"offset" example:"0"`
}

// SearchResult represents a search result item
// @Description Individual search result
type SearchResult struct {
	// Result ID
	ID string `json:"id" example:"room-456"`
	// Entity type
	Type string `json:"type" example:"room"`
	// Display name
	Name string `json:"name" example:"Conference Room A"`
	// Description or summary
	Description string `json:"description" example:"Large conference room on 3rd floor"`
	// Relevance score
	Score float64 `json:"score" example:"0.95"`
	// Additional metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// SearchResponse represents search results
// @Description Search results with pagination info
type SearchResponse struct {
	// Search results
	Results []SearchResult `json:"results"`
	// Total number of results
	Total int `json:"total" example:"42"`
	// Current limit
	Limit int `json:"limit" example:"20"`
	// Current offset
	Offset int `json:"offset" example:"0"`
	// Search query
	Query string `json:"query" example:"conference room"`
}

// ErrorResponse represents an API error
// @Description Standard error response
type ErrorResponse struct {
	// Error code
	Code string `json:"code" example:"VALIDATION_ERROR"`
	// Error message
	Message string `json:"message" example:"Invalid input data"`
	// Detailed error information
	Details map[string]interface{} `json:"details,omitempty"`
	// Request ID for tracking
	RequestID string `json:"request_id" example:"req-123456789"`
}

// HealthResponse represents health check status
// @Description System health status
type HealthResponse struct {
	// Service status
	Status string `json:"status" example:"healthy"`
	// Service version
	Version string `json:"version" example:"2.0.0"`
	// Current timestamp
	Timestamp time.Time `json:"timestamp" example:"2024-01-20T14:45:00Z"`
	// Component health status
	Components map[string]string `json:"components,omitempty"`
}

// PaginationParams represents common pagination parameters
// @Description Pagination parameters for list endpoints
type PaginationParams struct {
	// Page number (1-based)
	Page int `query:"page" example:"1"`
	// Items per page
	PageSize int `query:"page_size" example:"20"`
	// Sort field
	SortBy string `query:"sort_by" example:"name"`
	// Sort direction (asc/desc)
	SortOrder string `query:"sort_order" example:"asc"`
}

// RefreshRequest represents token refresh request
// @Description Request to refresh access token
type RefreshRequest struct {
	// Refresh token
	RefreshToken string `json:"refresh_token" binding:"required" example:"eyJhbGciOiJIUzI1NiIs..."`
}

// CreateBuildingRequest represents building creation data
// @Description Building information for creation
type CreateBuildingRequest struct {
	// Building name
	Name string `json:"name" binding:"required" example:"Main Office Building"`
	// Building address
	Address string `json:"address" example:"123 Main St"`
	// City
	City string `json:"city" example:"New York"`
	// State or province
	State string `json:"state" example:"NY"`
	// Postal code
	PostalCode string `json:"postal_code" example:"10001"`
	// Country
	Country string `json:"country" example:"USA"`
	// Number of floors
	Floors int `json:"floors" example:"5"`
	// Total area in square meters
	TotalArea float64 `json:"total_area" example:"10000.5"`
	// Building type
	BuildingType string `json:"building_type" example:"office"`
}

// UpdateBuildingRequest represents building update data
// @Description Building information for updates (all fields optional)
type UpdateBuildingRequest struct {
	// Building name
	Name *string `json:"name,omitempty" example:"Updated Building Name"`
	// Building address
	Address *string `json:"address,omitempty" example:"456 New St"`
	// City
	City *string `json:"city,omitempty" example:"Los Angeles"`
	// State or province
	State *string `json:"state,omitempty" example:"CA"`
	// Postal code
	PostalCode *string `json:"postal_code,omitempty" example:"90001"`
	// Country
	Country *string `json:"country,omitempty" example:"USA"`
	// Number of floors
	Floors *int `json:"floors,omitempty" example:"6"`
	// Total area in square meters
	TotalArea *float64 `json:"total_area,omitempty" example:"12000.5"`
	// Building type
	BuildingType *string `json:"building_type,omitempty" example:"mixed-use"`
}

// ChangePasswordRequest represents password change request
// @Description Request to change user password
type ChangePasswordRequest struct {
	// Current password
	OldPassword string `json:"old_password" binding:"required" example:"oldpassword123"`
	// New password (min 8 characters)
	NewPassword string `json:"new_password" binding:"required,min=8" example:"newsecurepassword456"`
}

// UserResponse represents user information
// @Description User profile information
type UserResponse struct {
	// User ID
	ID string `json:"id" example:"user-123456"`
	// User email
	Email string `json:"email" example:"user@example.com"`
	// User's full name
	Name string `json:"name" example:"John Doe"`
	// User role
	Role string `json:"role" example:"admin"`
	// Organization ID
	OrganizationID string `json:"organization_id" example:"org-789012"`
	// Account creation date
	CreatedAt time.Time `json:"created_at" example:"2024-01-15T09:30:00Z"`
	// Last update date
	UpdatedAt time.Time `json:"updated_at" example:"2024-01-20T14:45:00Z"`
	// User preferences
	Preferences map[string]interface{} `json:"preferences,omitempty"`
}

// UserUpdateRequest represents user update data
// @Description User profile update request
type UserUpdateRequest struct {
	// User's full name
	Name string `json:"name,omitempty" example:"Jane Doe"`
	// User's phone number
	Phone string `json:"phone,omitempty" example:"+1-555-123-4567"`
	// User's timezone
	Timezone string `json:"timezone,omitempty" example:"America/New_York"`
	// User preferences
	Preferences map[string]interface{} `json:"preferences,omitempty"`
}