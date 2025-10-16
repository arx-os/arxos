package domain

import (
	"context"
	"time"

	"github.com/arx-os/arxos/internal/domain/building"
)

// Repository interfaces define the contract for data access following Clean Architecture

// UserRepository defines the contract for user data operations
type UserRepository interface {
	Create(ctx context.Context, user *User) error
	GetByID(ctx context.Context, id string) (*User, error)
	GetByEmail(ctx context.Context, email string) (*User, error)
	List(ctx context.Context, filter *UserFilter) ([]*User, error)
	Update(ctx context.Context, user *User) error
	Delete(ctx context.Context, id string) error
	GetOrganizations(ctx context.Context, userID string) ([]*Organization, error)
}

// BuildingRepository defines the contract for building data operations
type BuildingRepository interface {
	Create(ctx context.Context, building *Building) error
	GetByID(ctx context.Context, id string) (*Building, error)
	GetByAddress(ctx context.Context, address string) (*Building, error)
	List(ctx context.Context, filter *BuildingFilter) ([]*Building, error)
	Update(ctx context.Context, building *Building) error
	Delete(ctx context.Context, id string) error
	GetEquipment(ctx context.Context, buildingID string) ([]*Equipment, error)
	GetFloors(ctx context.Context, buildingID string) ([]*Floor, error)
}

// EquipmentRepository defines the contract for equipment data operations
type EquipmentRepository interface {
	Create(ctx context.Context, equipment *Equipment) error
	GetByID(ctx context.Context, id string) (*Equipment, error)
	GetByBuilding(ctx context.Context, buildingID string) ([]*Equipment, error)
	GetByFloor(ctx context.Context, floorID string) ([]*Equipment, error)
	GetByRoom(ctx context.Context, roomID string) ([]*Equipment, error)
	GetByType(ctx context.Context, equipmentType string) ([]*Equipment, error)
	List(ctx context.Context, filter *EquipmentFilter) ([]*Equipment, error)
	Update(ctx context.Context, equipment *Equipment) error
	Delete(ctx context.Context, id string) error
	GetByLocation(ctx context.Context, buildingID string, floor string, room string) ([]*Equipment, error)

	// Path-based query methods
	GetByPath(ctx context.Context, exactPath string) (*Equipment, error)
	FindByPath(ctx context.Context, pathPattern string) ([]*Equipment, error)
}

// OrganizationRepository defines the contract for organization data operations
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

// FloorRepository defines the contract for floor data operations
type FloorRepository interface {
	Create(ctx context.Context, floor *Floor) error
	GetByID(ctx context.Context, id string) (*Floor, error)
	GetByBuilding(ctx context.Context, buildingID string) ([]*Floor, error)
	Update(ctx context.Context, floor *Floor) error
	Delete(ctx context.Context, id string) error
	List(ctx context.Context, buildingID string, limit, offset int) ([]*Floor, error)
	GetRooms(ctx context.Context, floorID string) ([]*Room, error)
	GetEquipment(ctx context.Context, floorID string) ([]*Equipment, error)
}

// RoomRepository defines the contract for room data operations
type RoomRepository interface {
	Create(ctx context.Context, room *Room) error
	GetByID(ctx context.Context, id string) (*Room, error)
	GetByFloor(ctx context.Context, floorID string) ([]*Room, error)
	GetByNumber(ctx context.Context, floorID, number string) (*Room, error)
	Update(ctx context.Context, room *Room) error
	Delete(ctx context.Context, id string) error
	List(ctx context.Context, floorID string, limit, offset int) ([]*Room, error)
	GetEquipment(ctx context.Context, roomID string) ([]*Equipment, error)
}

// Service interfaces define the contract for business logic

// UserService defines the contract for user business operations
type UserService interface {
	CreateUser(ctx context.Context, req *CreateUserRequest) (*User, error)
	GetUser(ctx context.Context, id string) (*User, error)
	UpdateUser(ctx context.Context, req *UpdateUserRequest) (*User, error)
	DeleteUser(ctx context.Context, id string) error
	ListUsers(ctx context.Context, filter *UserFilter) ([]*User, error)
	AuthenticateUser(ctx context.Context, email, password string) (*User, error)
	GetUserOrganizations(ctx context.Context, userID string) ([]*Organization, error)
}

// BuildingService defines the contract for building business operations
type BuildingService interface {
	CreateBuilding(ctx context.Context, req *CreateBuildingRequest) (*Building, error)
	GetBuilding(ctx context.Context, id string) (*Building, error)
	UpdateBuilding(ctx context.Context, req *UpdateBuildingRequest) (*Building, error)
	DeleteBuilding(ctx context.Context, id string) error
	ListBuildings(ctx context.Context, filter *BuildingFilter) ([]*Building, error)
	ImportBuilding(ctx context.Context, req *ImportBuildingRequest) (*Building, error)
	ExportBuilding(ctx context.Context, id, format string) ([]byte, error)
}

// EquipmentService defines the contract for equipment business operations
type EquipmentService interface {
	CreateEquipment(ctx context.Context, req *CreateEquipmentRequest) (*Equipment, error)
	GetEquipment(ctx context.Context, id string) (*Equipment, error)
	UpdateEquipment(ctx context.Context, req *UpdateEquipmentRequest) (*Equipment, error)
	DeleteEquipment(ctx context.Context, id string) error
	ListEquipment(ctx context.Context, filter *EquipmentFilter) ([]*Equipment, error)
	MoveEquipment(ctx context.Context, id string, newLocation *Location) error
}

// BuildingRepositoryService defines the contract for building repository business operations
// This is the main service for the "Git of Buildings" concept
type BuildingRepositoryService interface {
	// Repository management
	CreateRepository(ctx context.Context, req *building.CreateRepositoryRequest) (*building.BuildingRepository, error)
	GetRepository(ctx context.Context, id string) (*building.BuildingRepository, error)
	UpdateRepository(ctx context.Context, id string, req *building.UpdateRepositoryRequest) error
	DeleteRepository(ctx context.Context, id string) error
	ListRepositories(ctx context.Context) ([]*building.BuildingRepository, error)

	// IFC import (PRIMARY FORMAT)
	ImportIFC(ctx context.Context, repoID string, ifcData []byte) (*building.IFCImportResult, error)

	// Repository validation
	ValidateRepository(ctx context.Context, repoID string) (*building.ValidationResult, error)

	// Version control
	CreateVersion(ctx context.Context, repoID string, message string) (*building.Version, error)
	GetVersion(ctx context.Context, repoID string, version string) (*building.Version, error)
	ListVersions(ctx context.Context, repoID string) ([]building.Version, error)
	CompareVersions(ctx context.Context, repoID string, v1, v2 string) (*building.VersionDiff, error)
	RollbackVersion(ctx context.Context, repoID string, version string) error
}

// OrganizationService defines the contract for organization business operations
type OrganizationService interface {
	CreateOrganization(ctx context.Context, req *CreateOrganizationRequest) (*Organization, error)
	GetOrganization(ctx context.Context, id string) (*Organization, error)
	UpdateOrganization(ctx context.Context, req *UpdateOrganizationRequest) (*Organization, error)
	DeleteOrganization(ctx context.Context, id string) error
	ListOrganizations(ctx context.Context, filter *OrganizationFilter) ([]*Organization, error)
	AddUserToOrganization(ctx context.Context, orgID, userID string) error
	RemoveUserFromOrganization(ctx context.Context, orgID, userID string) error
	GetOrganizationUsers(ctx context.Context, orgID string) ([]*User, error)
}

// Logger interface for logging operations
type Logger interface {
	Debug(msg string, fields ...any)
	Info(msg string, fields ...any)
	Warn(msg string, fields ...any)
	Error(msg string, fields ...any)
	Fatal(msg string, fields ...any)
}

// Cache interface for caching operations
type Cache interface {
	Get(ctx context.Context, key string) (any, error)
	Set(ctx context.Context, key string, value any, ttl time.Duration) error
	Delete(ctx context.Context, key string) error
	Clear(ctx context.Context) error
	Close() error
}

// Database interface for database operations
type Database interface {
	Connect(ctx context.Context) error
	Close() error
	Health(ctx context.Context) error
	BeginTx(ctx context.Context) (any, error)
	CommitTx(tx any) error
	RollbackTx(tx any) error
}
