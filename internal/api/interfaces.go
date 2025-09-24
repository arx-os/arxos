package api

import (
	"context"
	"time"

	apimodels "github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/pkg/models"
)

// RequestInfo re-exported from models
type RequestInfo = apimodels.RequestInfo

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
	GetUser(ctx context.Context, userID string) (*apimodels.User, error)
	CreateUser(ctx context.Context, req apimodels.CreateUserRequest) (*apimodels.User, error)
	UpdateUser(ctx context.Context, userID string, updates apimodels.UserUpdate) (*apimodels.User, error)
	DeleteUser(ctx context.Context, userID string) error
	ListUsers(ctx context.Context, filter apimodels.UserFilter) ([]*apimodels.User, error)
	GetUserByEmail(ctx context.Context, email string) (*apimodels.User, error)
	GetUserPermissions(ctx context.Context, userID string) ([]string, error)
	UpdateUserActivity(ctx context.Context, userID string) error
	ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error
	RequestPasswordReset(ctx context.Context, email string) error
	ConfirmPasswordReset(ctx context.Context, token, newPassword string) error
}

// Re-export user types from models package
type UserFilter = apimodels.UserFilter
type CreateUserRequest = apimodels.CreateUserRequest
type UserUpdate = apimodels.UserUpdate

// AuthService defines the interface for authentication operations
type AuthService interface {
	// Authentication
	Login(ctx context.Context, email, password string) (*apimodels.AuthResponse, error)
	Logout(ctx context.Context, token string) error
	Register(ctx context.Context, email, password, name string) (*apimodels.User, error)

	// Token operations
	ValidateToken(ctx context.Context, token string) (string, error) // returns userID
	ValidateTokenClaims(ctx context.Context, token string) (*apimodels.TokenClaims, error)
	RefreshToken(ctx context.Context, refreshToken string) (*apimodels.AuthResponse, error)
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

// EquipmentService defines the interface for equipment operations
type EquipmentService interface {
	CreateEquipment(ctx context.Context, equipment *models.Equipment) error
	GetEquipment(ctx context.Context, id string) (*models.Equipment, error)
	UpdateEquipment(ctx context.Context, equipment *models.Equipment) error
	DeleteEquipment(ctx context.Context, id string) error
	ListEquipment(ctx context.Context, buildingID string) ([]*models.Equipment, error)
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

// Re-export types from models package for backwards compatibility
type User = apimodels.User
type Organization = apimodels.Organization
type OrgSettings = apimodels.OrgSettings
type AuthResponse = apimodels.AuthResponse
type TokenClaims = apimodels.TokenClaims
type Change = apimodels.Change
type Conflict = apimodels.Conflict
type SyncRequest = apimodels.SyncRequest
type SyncResponse = apimodels.SyncResponse
type RejectedChange = apimodels.RejectedChange
