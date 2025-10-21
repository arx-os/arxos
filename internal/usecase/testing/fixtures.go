package testing

import (
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/mock"
)

// =============================================================================
// Test Fixtures - Domain Entity Creators
// =============================================================================

// CreateTestBuilding creates a test building with sensible defaults
func CreateTestBuilding() *domain.Building {
	return &domain.Building{
		ID:        types.NewID(),
		Name:      "Test Building",
		Address:   "123 Test Street, Test City, TS 12345",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// CreateTestEquipment creates a test equipment with sensible defaults
func CreateTestEquipment() *domain.Equipment {
	buildingID := types.NewID()
	return &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: buildingID,
		Name:       "Test Equipment",
		Type:       "HVAC",
		Category:   "mechanical",
		Path:       "/B1/F1/R101/HVAC-1",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
}

// CreateTestUser creates a test user with sensible defaults
func CreateTestUser() *domain.User {
	return &domain.User{
		ID:        types.NewID(),
		Email:     "test@example.com",
		Name:      "Test User",
		Role:      "user",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// CreateTestFloor creates a test floor with sensible defaults
func CreateTestFloor() *domain.Floor {
	buildingID := types.NewID()
	return &domain.Floor{
		ID:         types.NewID(),
		BuildingID: buildingID,
		Level:      1,
		Name:       "First Floor",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
}

// CreateTestRoom creates a test room with sensible defaults
func CreateTestRoom() *domain.Room {
	floorID := types.NewID()
	return &domain.Room{
		ID:        types.NewID(),
		FloorID:   floorID,
		Number:    "101",
		Name:      "Test Room 101",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// CreateTestOrganization creates a test organization with sensible defaults
func CreateTestOrganization() *domain.Organization {
	return &domain.Organization{
		ID:          types.NewID(),
		Name:        "Test Organization",
		Description: "A test organization for unit testing",
		Plan:        "basic",
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
}

// CreatePermissiveMockLogger creates a mock logger that accepts all calls
func CreatePermissiveMockLogger() *MockLogger {
	mockLogger := new(MockLogger)
	mockLogger.On("Info", mock.Anything, mock.Anything).Maybe()
	mockLogger.On("Error", mock.Anything, mock.Anything).Maybe()
	mockLogger.On("Debug", mock.Anything, mock.Anything).Maybe()
	mockLogger.On("Warn", mock.Anything, mock.Anything).Maybe()
	mockLogger.On("Fatal", mock.Anything, mock.Anything).Maybe()
	mockLogger.On("WithFields", mock.Anything).Return(mockLogger).Maybe()
	mockLogger.On("WithField", mock.Anything, mock.Anything).Return(mockLogger).Maybe()
	return mockLogger
}

// =============================================================================
// Functional Options for Test Fixtures
// =============================================================================

// BuildingOption is a functional option for building creation
type BuildingOption func(*domain.Building)

// WithBuildingName sets the building name
func WithBuildingName(name string) BuildingOption {
	return func(b *domain.Building) {
		b.Name = name
	}
}

// WithBuildingID sets a specific building ID
func WithBuildingID(id types.ID) BuildingOption {
	return func(b *domain.Building) {
		b.ID = id
	}
}

// WithBuildingAddress sets the building address
func WithBuildingAddress(address string) BuildingOption {
	return func(b *domain.Building) {
		b.Address = address
	}
}

// CreateTestBuildingWith creates a building with custom options
func CreateTestBuildingWith(opts ...BuildingOption) *domain.Building {
	b := CreateTestBuilding()
	for _, opt := range opts {
		opt(b)
	}
	return b
}

// UserOption is a functional option for user creation
type UserOption func(*domain.User)

// WithUserEmail sets the user email
func WithUserEmail(email string) UserOption {
	return func(u *domain.User) {
		u.Email = email
	}
}

// WithUserName sets the user name
func WithUserName(name string) UserOption {
	return func(u *domain.User) {
		u.Name = name
	}
}

// WithUserRole sets the user role
func WithUserRole(role string) UserOption {
	return func(u *domain.User) {
		u.Role = role
	}
}

// CreateTestUserWith creates a user with custom options
func CreateTestUserWith(opts ...UserOption) *domain.User {
	u := CreateTestUser()
	for _, opt := range opts {
		opt(u)
	}
	return u
}

// OrganizationOption is a functional option for organization creation
type OrganizationOption func(*domain.Organization)

// WithOrgName sets the organization name
func WithOrgName(name string) OrganizationOption {
	return func(o *domain.Organization) {
		o.Name = name
	}
}

// WithOrgPlan sets the organization plan
func WithOrgPlan(plan string) OrganizationOption {
	return func(o *domain.Organization) {
		o.Plan = plan
	}
}

// CreateTestOrganizationWith creates an organization with custom options
func CreateTestOrganizationWith(opts ...OrganizationOption) *domain.Organization {
	o := CreateTestOrganization()
	for _, opt := range opts {
		opt(o)
	}
	return o
}
