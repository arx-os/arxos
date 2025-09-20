package api

import (
	"context"
	"time"

	"github.com/arx-os/arxos/pkg/models"
	syncpkg "github.com/arx-os/arxos/pkg/sync"
)

// RequestInfo contains metadata about the HTTP request
type RequestInfo struct {
	IPAddress string
	UserAgent string
	RequestID string
}

// BuildingService defines the interface for building operations
type BuildingService interface {
	// Building CRUD operations
	GetBuilding(ctx context.Context, id string) (*models.FloorPlan, error)
	ListBuildings(ctx context.Context, userID string, limit, offset int) ([]*models.FloorPlan, error)
	CreateBuilding(ctx context.Context, building *models.FloorPlan) error
	UpdateBuilding(ctx context.Context, building *models.FloorPlan) error
	DeleteBuilding(ctx context.Context, id string) error

	// Equipment operations
	GetEquipment(ctx context.Context, id string) (*models.Equipment, error)
	ListEquipment(ctx context.Context, buildingID string, filters map[string]interface{}) ([]*models.Equipment, error)
	CreateEquipment(ctx context.Context, equipment *models.Equipment) error
	UpdateEquipment(ctx context.Context, equipment *models.Equipment) error
	DeleteEquipment(ctx context.Context, id string) error

	// Room operations
	GetRoom(ctx context.Context, id string) (*models.Room, error)
	ListRooms(ctx context.Context, buildingID string) ([]*models.Room, error)
	CreateRoom(ctx context.Context, room *models.Room) error
	UpdateRoom(ctx context.Context, room *models.Room) error
	DeleteRoom(ctx context.Context, id string) error
}

// UserService defines the interface for user operations
type UserService interface {
	// User CRUD operations
	GetUser(ctx context.Context, userID string) (*User, error)
	CreateUser(ctx context.Context, req CreateUserRequest) (*User, error)
	UpdateUser(ctx context.Context, userID string, updates UserUpdate) (*User, error)
	DeleteUser(ctx context.Context, userID string) error
	ListUsers(ctx context.Context, filter UserFilter) ([]*User, error)
	GetUserByEmail(ctx context.Context, email string) (*User, error)
	GetUserPermissions(ctx context.Context, userID string) ([]string, error)
	UpdateUserActivity(ctx context.Context, userID string) error
	ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error
	RequestPasswordReset(ctx context.Context, email string) error
	ConfirmPasswordReset(ctx context.Context, token, newPassword string) error
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

// AuthService defines the interface for authentication operations
type AuthService interface {
	// Authentication
	Login(ctx context.Context, email, password string) (*AuthResponse, error)
	Logout(ctx context.Context, token string) error
	Register(ctx context.Context, email, password, name string) (*User, error)

	// Token operations
	ValidateToken(ctx context.Context, token string) (*TokenClaims, error)
	RefreshToken(ctx context.Context, refreshToken string) (*AuthResponse, error)
	RevokeToken(ctx context.Context, token string) error

	// Password operations
	ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error
	ResetPassword(ctx context.Context, email string) error
	ConfirmPasswordReset(ctx context.Context, token, newPassword string) error
}

// OrganizationService defines the interface for organization operations
type OrganizationService interface {
	// Organization CRUD operations
	GetOrganization(ctx context.Context, id string) (*models.Organization, error)
	GetOrganizationBySlug(ctx context.Context, slug string) (*models.Organization, error)
	ListOrganizations(ctx context.Context, userID string) ([]*models.Organization, error)
	CreateOrganization(ctx context.Context, org *models.Organization, ownerID string) error
	UpdateOrganization(ctx context.Context, org *models.Organization) error
	DeleteOrganization(ctx context.Context, id string) error

	// Member management
	AddMember(ctx context.Context, orgID, userID string, role models.Role) error
	RemoveMember(ctx context.Context, orgID, userID string) error
	UpdateMemberRole(ctx context.Context, orgID, userID string, role models.Role) error
	GetMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error)
	GetMemberRole(ctx context.Context, orgID, userID string) (*models.Role, error)

	// Invitation management
	CreateInvitation(ctx context.Context, orgID, email string, role models.Role, invitedBy string) (*models.OrganizationInvitation, error)
	AcceptInvitation(ctx context.Context, token string, userID string) error
	RevokeInvitation(ctx context.Context, invitationID string) error
	ListPendingInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error)

	// Permission and access control
	HasPermission(ctx context.Context, orgID, userID string, permission models.Permission) (bool, error)
	GetUserPermissions(ctx context.Context, orgID, userID string) ([]models.Permission, error)
	CanUserAccessOrganization(ctx context.Context, orgID, userID string) (bool, error)
}

// StorageService defines the interface for storage operations
type StorageService interface {
	// File operations
	UploadFile(ctx context.Context, key string, data []byte) error
	DownloadFile(ctx context.Context, key string) ([]byte, error)
	DeleteFile(ctx context.Context, key string) error
	ListFiles(ctx context.Context, prefix string) ([]string, error)

	// URL generation
	GenerateUploadURL(ctx context.Context, key string, expiry time.Duration) (string, error)
	GenerateDownloadURL(ctx context.Context, key string, expiry time.Duration) (string, error)
}

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

// Re-export sync types for backwards compatibility
type Change = syncpkg.Change
type Conflict = syncpkg.Conflict
type SyncRequest = syncpkg.SyncRequest
type SyncResponse = syncpkg.SyncResponse
type RejectedChange = syncpkg.RejectedChange
