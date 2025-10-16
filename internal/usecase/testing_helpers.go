package usecase

import (
	"context"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/mock"
)

// =============================================================================
// Mock Repositories
// =============================================================================

// MockBuildingRepository is a mock implementation of domain.BuildingRepository
type MockBuildingRepository struct {
	mock.Mock
}

func (m *MockBuildingRepository) Create(ctx context.Context, building *domain.Building) error {
	args := m.Called(ctx, building)
	return args.Error(0)
}

func (m *MockBuildingRepository) GetByID(ctx context.Context, id string) (*domain.Building, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Building), args.Error(1)
}

func (m *MockBuildingRepository) List(ctx context.Context, filter *domain.BuildingFilter) ([]*domain.Building, error) {
	args := m.Called(ctx, filter)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Building), args.Error(1)
}

func (m *MockBuildingRepository) Update(ctx context.Context, building *domain.Building) error {
	args := m.Called(ctx, building)
	return args.Error(0)
}

func (m *MockBuildingRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockBuildingRepository) GetByAddress(ctx context.Context, address string) (*domain.Building, error) {
	args := m.Called(ctx, address)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Building), args.Error(1)
}

func (m *MockBuildingRepository) GetEquipment(ctx context.Context, buildingID string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, buildingID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockBuildingRepository) GetFloors(ctx context.Context, buildingID string) ([]*domain.Floor, error) {
	args := m.Called(ctx, buildingID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Floor), args.Error(1)
}

// MockEquipmentRepository is a mock implementation of domain.EquipmentRepository
type MockEquipmentRepository struct {
	mock.Mock
}

func (m *MockEquipmentRepository) Create(ctx context.Context, equipment *domain.Equipment) error {
	args := m.Called(ctx, equipment)
	return args.Error(0)
}

func (m *MockEquipmentRepository) GetByID(ctx context.Context, id string) (*domain.Equipment, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) GetByBuilding(ctx context.Context, buildingID string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, buildingID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) List(ctx context.Context, filter *domain.EquipmentFilter) ([]*domain.Equipment, error) {
	args := m.Called(ctx, filter)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) Update(ctx context.Context, equipment *domain.Equipment) error {
	args := m.Called(ctx, equipment)
	return args.Error(0)
}

func (m *MockEquipmentRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockEquipmentRepository) GetByPath(ctx context.Context, path string) (*domain.Equipment, error) {
	args := m.Called(ctx, path)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) FindByPath(ctx context.Context, pattern string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, pattern)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) GetByFloor(ctx context.Context, floorID string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, floorID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) GetByRoom(ctx context.Context, roomID string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, roomID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) GetByType(ctx context.Context, equipmentType string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, equipmentType)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) GetByLocation(ctx context.Context, buildingID string, floor string, room string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, buildingID, floor, room)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

// MockUserRepository is a mock implementation of domain.UserRepository
type MockUserRepository struct {
	mock.Mock
}

func (m *MockUserRepository) Create(ctx context.Context, user *domain.User) error {
	args := m.Called(ctx, user)
	return args.Error(0)
}

func (m *MockUserRepository) GetByID(ctx context.Context, id string) (*domain.User, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.User), args.Error(1)
}

func (m *MockUserRepository) GetByEmail(ctx context.Context, email string) (*domain.User, error) {
	args := m.Called(ctx, email)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.User), args.Error(1)
}

func (m *MockUserRepository) List(ctx context.Context, filter *domain.UserFilter) ([]*domain.User, error) {
	args := m.Called(ctx, filter)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.User), args.Error(1)
}

func (m *MockUserRepository) Update(ctx context.Context, user *domain.User) error {
	args := m.Called(ctx, user)
	return args.Error(0)
}

func (m *MockUserRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockUserRepository) GetOrganizations(ctx context.Context, userID string) ([]*domain.Organization, error) {
	args := m.Called(ctx, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Organization), args.Error(1)
}

// MockOrganizationRepository is a mock implementation of domain.OrganizationRepository
type MockOrganizationRepository struct {
	mock.Mock
}

func (m *MockOrganizationRepository) Create(ctx context.Context, org *domain.Organization) error {
	args := m.Called(ctx, org)
	return args.Error(0)
}

func (m *MockOrganizationRepository) GetByID(ctx context.Context, id string) (*domain.Organization, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Organization), args.Error(1)
}

func (m *MockOrganizationRepository) List(ctx context.Context, filter *domain.OrganizationFilter) ([]*domain.Organization, error) {
	args := m.Called(ctx, filter)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Organization), args.Error(1)
}

func (m *MockOrganizationRepository) Update(ctx context.Context, org *domain.Organization) error {
	args := m.Called(ctx, org)
	return args.Error(0)
}

func (m *MockOrganizationRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

// MockLogger is a mock implementation of domain.Logger
type MockLogger struct {
	mock.Mock
}

func (m *MockLogger) Debug(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Info(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Warn(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Error(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Fatal(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) With(fields ...any) domain.Logger {
	args := m.Called(fields)
	return args.Get(0).(domain.Logger)
}

// =============================================================================
// Test Fixtures and Helpers
// =============================================================================

// createTestBuilding creates a test building for use in tests
func createTestBuilding() *domain.Building {
	return &domain.Building{
		ID:      types.NewID(),
		Name:    "Test Building",
		Address: "123 Test Street",
		Coordinates: &domain.Location{
			X: 40.7128,
			Y: -74.0060,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createTestEquipment creates test equipment for use in tests
func createTestEquipment() *domain.Equipment {
	return &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: types.NewID(),
		Name:       "Test Equipment",
		Type:       "HVAC",
		Model:      "Test Model 3000",
		Status:     "operational",
		Location: &domain.Location{
			X: 40.7128,
			Y: -74.0060,
			Z: 5.0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createTestUser creates a test user for use in tests
func createTestUser() *domain.User {
	return &domain.User{
		ID:        types.NewID(),
		Email:     "test@example.com",
		Name:      "Test User",
		Role:      "admin",
		Active:    true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createTestFloor creates a test floor for use in tests
func createTestFloor() *domain.Floor {
	return &domain.Floor{
		ID:         types.NewID(),
		BuildingID: types.NewID(),
		Name:       "Ground Floor",
		Level:      0,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
}

// createTestRoom creates a test room for use in tests
func createTestRoom() *domain.Room {
	return &domain.Room{
		ID:      types.NewID(),
		FloorID: types.NewID(),
		Number:  "101",
		Name:    "Test Room",
		Location: &domain.Location{
			X: 10.0,
			Y: 20.0,
			Z: 0,
		},
		Width:     7.0,
		Height:    2.7,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// createTestOrganization creates a test organization for use in tests
func createTestOrganization() *domain.Organization {
	return &domain.Organization{
		ID:          types.NewID(),
		Name:        "Test Organization",
		Description: "A test organization",
		Plan:        "professional",
		Active:      true,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
}

// createPermissiveMockLogger creates a mock logger that accepts all calls
func createPermissiveMockLogger() *MockLogger {
	logger := new(MockLogger)
	logger.On("Debug", mock.Anything, mock.Anything).Maybe()
	logger.On("Info", mock.Anything, mock.Anything).Maybe()
	logger.On("Warn", mock.Anything, mock.Anything).Maybe()
	logger.On("Error", mock.Anything, mock.Anything).Maybe()
	logger.On("Fatal", mock.Anything, mock.Anything).Maybe()
	logger.On("With", mock.Anything).Return(logger).Maybe()
	return logger
}
