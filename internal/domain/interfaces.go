package domain

import (
	"context"
	"time"
)

// =============================================================================
// Core Infrastructure Interfaces
// =============================================================================

// Database represents the database connection interface
type Database interface {
	Close() error
	Ping() error
	// Note: Database is typically *sql.DB - specific query methods
	// are handled by repository implementations
}

// Cache represents the caching layer interface
type Cache interface {
	Get(ctx context.Context, key string) (any, error)
	Set(ctx context.Context, key string, value any, expiration time.Duration) error
	Delete(ctx context.Context, key string) error
	Clear(ctx context.Context) error
	Close() error
}

// Logger represents the logging interface
type Logger interface {
	Debug(msg string, fields ...any)
	Info(msg string, fields ...any)
	Warn(msg string, fields ...any)
	Error(msg string, fields ...any)
	Fatal(msg string, fields ...any)
	WithFields(fields map[string]any) Logger
}

// =============================================================================
// Core Domain Repository Interfaces
// =============================================================================

// BuildingRepository defines the interface for building data access
type BuildingRepository interface {
	Create(ctx context.Context, building *Building) error
	GetByID(ctx context.Context, id string) (*Building, error)
	GetByAddress(ctx context.Context, address string) (*Building, error)
	List(ctx context.Context, filter *BuildingFilter) ([]*Building, error)
	Update(ctx context.Context, building *Building) error
	Delete(ctx context.Context, id string) error
	GetFloors(ctx context.Context, buildingID string) ([]*Floor, error)
	GetEquipment(ctx context.Context, buildingID string) ([]*Equipment, error)
}

// FloorRepository defines the interface for floor data access
type FloorRepository interface {
	Create(ctx context.Context, floor *Floor) error
	GetByID(ctx context.Context, id string) (*Floor, error)
	Update(ctx context.Context, floor *Floor) error
	Delete(ctx context.Context, id string) error
	List(ctx context.Context, buildingID string, limit, offset int) ([]*Floor, error)
	GetByBuilding(ctx context.Context, buildingID string) ([]*Floor, error)
	GetEquipment(ctx context.Context, floorID string) ([]*Equipment, error)
	GetRooms(ctx context.Context, floorID string) ([]*Room, error)
}

// RoomRepository defines the interface for room data access
type RoomRepository interface {
	Create(ctx context.Context, room *Room) error
	GetByID(ctx context.Context, id string) (*Room, error)
	GetByNumber(ctx context.Context, floorID, number string) (*Room, error)
	Update(ctx context.Context, room *Room) error
	Delete(ctx context.Context, id string) error
	List(ctx context.Context, floorID string, limit, offset int) ([]*Room, error)
	GetByFloor(ctx context.Context, floorID string) ([]*Room, error)
}

// EquipmentRepository defines the interface for equipment data access
type EquipmentRepository interface {
	Create(ctx context.Context, equipment *Equipment) error
	GetByID(ctx context.Context, id string) (*Equipment, error)
	GetByBuilding(ctx context.Context, buildingID string) ([]*Equipment, error)
	GetByFloor(ctx context.Context, floorID string) ([]*Equipment, error)
	GetByRoom(ctx context.Context, roomID string) ([]*Equipment, error)
	GetByPath(ctx context.Context, path string) (*Equipment, error)
	GetByLocation(ctx context.Context, buildingID, floor, room string) ([]*Equipment, error)
	FindByPath(ctx context.Context, path string) ([]*Equipment, error)
	List(ctx context.Context, filter *EquipmentFilter) ([]*Equipment, error)
	Update(ctx context.Context, equipment *Equipment) error
	Delete(ctx context.Context, id string) error
	Search(ctx context.Context, query string, filters map[string]any) ([]*Equipment, error)
	BulkCreate(ctx context.Context, equipment []*Equipment) error
}

// UserRepository defines the interface for user data access
type UserRepository interface {
	Create(ctx context.Context, user *User) error
	GetByID(ctx context.Context, id string) (*User, error)
	GetByEmail(ctx context.Context, email string) (*User, error)
	List(ctx context.Context, filter *UserFilter) ([]*User, error)
	Update(ctx context.Context, user *User) error
	Delete(ctx context.Context, id string) error
	GetOrganizations(ctx context.Context, userID string) ([]*Organization, error)
}

// OrganizationRepository defines the interface for organization data access
type OrganizationRepository interface {
	Create(ctx context.Context, org *Organization) error
	GetByID(ctx context.Context, id string) (*Organization, error)
	GetByName(ctx context.Context, name string) (*Organization, error)
	List(ctx context.Context, filter *OrganizationFilter) ([]*Organization, error)
	Update(ctx context.Context, org *Organization) error
	Delete(ctx context.Context, id string) error
	GetUsers(ctx context.Context, orgID string) ([]*User, error)
	AddUser(ctx context.Context, orgID, userID string) error
	RemoveUser(ctx context.Context, orgID, userID string) error
}

// Note: RelationshipRepository is defined in relationship.go
// Note: Filter types (BuildingFilter, EquipmentFilter, UserFilter, OrganizationFilter) are defined in entities.go
