// Package database provides a unified interface for database operations in ArxOS.
// It defines database interfaces and error types for consistent data access across
// the application, supporting floor plans, equipment, rooms, users, and organization management.
package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/joelpate/arxos/pkg/models"
)

// DB represents the database interface for ArxOS
type DB interface {
	// Core operations
	Connect(ctx context.Context, dbPath string) error
	Close() error
	
	// Transaction support
	BeginTx(ctx context.Context) (*sql.Tx, error)
	
	// Floor plan operations
	GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error)
	GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error)
	SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error
	UpdateFloorPlan(ctx context.Context, plan *models.FloorPlan) error
	DeleteFloorPlan(ctx context.Context, id string) error
	
	// Equipment operations
	GetEquipment(ctx context.Context, id string) (*models.Equipment, error)
	GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error)
	SaveEquipment(ctx context.Context, equipment *models.Equipment) error
	UpdateEquipment(ctx context.Context, equipment *models.Equipment) error
	DeleteEquipment(ctx context.Context, id string) error
	
	// Room operations
	GetRoom(ctx context.Context, id string) (*models.Room, error)
	GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error)
	SaveRoom(ctx context.Context, room *models.Room) error
	UpdateRoom(ctx context.Context, room *models.Room) error
	DeleteRoom(ctx context.Context, id string) error
	
	// User operations
	GetUser(ctx context.Context, id string) (*models.User, error)
	GetUserByEmail(ctx context.Context, email string) (*models.User, error)
	CreateUser(ctx context.Context, user *models.User) error
	UpdateUser(ctx context.Context, user *models.User) error
	DeleteUser(ctx context.Context, id string) error
	
	// Session operations
	CreateSession(ctx context.Context, session *models.UserSession) error
	GetSession(ctx context.Context, token string) (*models.UserSession, error)
	GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*models.UserSession, error)
	UpdateSession(ctx context.Context, session *models.UserSession) error
	DeleteSession(ctx context.Context, id string) error
	DeleteExpiredSessions(ctx context.Context) error
	DeleteUserSessions(ctx context.Context, userID string) error
	
	// Password reset operations
	CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error
	GetPasswordResetToken(ctx context.Context, token string) (*models.PasswordResetToken, error)
	MarkPasswordResetTokenUsed(ctx context.Context, token string) error
	DeleteExpiredPasswordResetTokens(ctx context.Context) error
	
	// Organization operations  
	GetOrganization(ctx context.Context, id string) (*models.Organization, error)
	GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error)
	CreateOrganization(ctx context.Context, org *models.Organization) error
	UpdateOrganization(ctx context.Context, org *models.Organization) error
	DeleteOrganization(ctx context.Context, id string) error
	
	// Organization member operations
	AddOrganizationMember(ctx context.Context, orgID, userID, role string) error
	RemoveOrganizationMember(ctx context.Context, orgID, userID string) error
	UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, role string) error
	GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error)
	GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error)
	
	// Organization invitation operations
	CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error
	GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error)
	GetOrganizationInvitation(ctx context.Context, id string) (*models.OrganizationInvitation, error)
	ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error)
	AcceptOrganizationInvitation(ctx context.Context, token, userID string) error
	RevokeOrganizationInvitation(ctx context.Context, id string) error
	
	// Query operations
	Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error)
	QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row
	Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error)
	
	// Migration operations
	Migrate(ctx context.Context) error
	GetVersion(ctx context.Context) (int, error)
}

// Config holds database configuration
type Config struct {
	DatabasePath string
	MaxOpenConns int
	MaxIdleConns int
	MaxLifetime  time.Duration
}

// NewConfig creates a new database configuration with defaults
func NewConfig(dbPath string) *Config {
	return &Config{
		DatabasePath: dbPath,
		MaxOpenConns: 25,
		MaxIdleConns: 5,
		MaxLifetime:  5 * time.Minute,
	}
}

// QueryResult represents the result of a custom query
type QueryResult struct {
	Columns []string
	Rows    [][]interface{}
}

// Change represents a change in the database for audit purposes
type Change struct {
	ID          string
	ObjectID    string
	ObjectType  string
	Operation   string // create, update, delete
	OldValue    string // JSON
	NewValue    string // JSON
	Timestamp   time.Time
	User        string
	Branch      string
	CommitHash  string
}

// Conflict represents a merge conflict between data sources
type Conflict struct {
	ID         string
	ObjectID   string
	ObjectType string
	Source     string
	OurValue   string // JSON
	TheirValue string // JSON
	Resolved   bool
	Resolution string // JSON of resolved value
	Timestamp  time.Time
}

// Error types
var (
	ErrNotFound      = fmt.Errorf("record not found")
	ErrAlreadyExists = fmt.Errorf("record already exists")
	ErrInvalidQuery  = fmt.Errorf("invalid query")
	ErrTransaction   = fmt.Errorf("transaction error")
)