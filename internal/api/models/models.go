package models

import (
	"time"

	"github.com/arx-os/arxos/pkg/models"
	syncpkg "github.com/arx-os/arxos/pkg/sync"
)

// User represents a user account
type User struct {
	ID             string    `json:"id"`
	Email          string    `json:"email"`
	Name           string    `json:"name"`
	PasswordHash   string    `json:"-"` // Never send password hash to client
	OrgID          string    `json:"org_id,omitempty"`
	Role           string    `json:"role"`
	Permissions    []string  `json:"permissions,omitempty"`
	Active         bool      `json:"active"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
	LastLoginAt    time.Time `json:"last_login_at,omitempty"`
	LastActivityAt time.Time `json:"last_activity_at,omitempty"`
}

// Organization represents an organization
type Organization struct {
	ID          string      `json:"id"`
	Name        string      `json:"name"`
	Description string      `json:"description"`
	Plan        string      `json:"plan"` // free, starter, professional, enterprise
	Active      bool        `json:"active"`
	Settings    OrgSettings `json:"settings"`
	CreatedAt   time.Time   `json:"created_at"`
	UpdatedAt   time.Time   `json:"updated_at"`
}

// OrgSettings contains organization-specific settings
type OrgSettings struct {
	MaxBuildings int                    `json:"max_buildings"`
	MaxUsers     int                    `json:"max_users"`
	Features     map[string]bool        `json:"features"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// AuthResponse contains authentication response data
type AuthResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
	User         *User  `json:"user"`
}

// TokenClaims contains JWT token claims
type TokenClaims struct {
	UserID    string    `json:"user_id"`
	Email     string    `json:"email"`
	OrgID     string    `json:"org_id"`
	Role      string    `json:"role"`
	ExpiresAt time.Time `json:"exp"`
	IssuedAt  time.Time `json:"iat"`
}

// UserFilter defines filtering options for listing users
type UserFilter struct {
	Role   string
	OrgID  string
	Active *bool
}

// CreateUserRequest defines the request for creating a user
type CreateUserRequest struct {
	Email       string   `json:"email"`
	Password    string   `json:"password"`
	Name        string   `json:"name"`
	Role        string   `json:"role"`
	OrgID       string   `json:"org_id"`
	Permissions []string `json:"permissions"`
}

// UserUpdate defines fields that can be updated on a user
type UserUpdate struct {
	Name        *string  `json:"name,omitempty"`
	Email       *string  `json:"email,omitempty"`
	Password    *string  `json:"password,omitempty"`
	Role        *string  `json:"role,omitempty"`
	OrgID       *string  `json:"org_id,omitempty"`
	Permissions []string `json:"permissions,omitempty"`
	Active      *bool    `json:"active,omitempty"`
}

// RequestInfo contains metadata about the HTTP request
type RequestInfo struct {
	IPAddress string
	UserAgent string
	RequestID string
}

// Re-export pkg/models types for convenience
type FloorPlan = models.FloorPlan
type Equipment = models.Equipment
type Room = models.Room
type Role = models.Role
type Permission = models.Permission
type OrganizationMember = models.OrganizationMember
type OrganizationInvitation = models.OrganizationInvitation

// Re-export sync types for backwards compatibility
type Change = syncpkg.Change
type Conflict = syncpkg.Conflict
type SyncRequest = syncpkg.SyncRequest
type SyncResponse = syncpkg.SyncResponse
type RejectedChange = syncpkg.RejectedChange