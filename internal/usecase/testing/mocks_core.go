package testing

import (
	"context"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/stretchr/testify/mock"
)

// =============================================================================
// Core Domain Repository Mocks
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

func (m *MockEquipmentRepository) Search(ctx context.Context, query string, filters map[string]any) ([]*domain.Equipment, error) {
	args := m.Called(ctx, query, filters)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) GetByPath(ctx context.Context, path string) (*domain.Equipment, error) {
	args := m.Called(ctx, path)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) BulkCreate(ctx context.Context, equipment []*domain.Equipment) error {
	args := m.Called(ctx, equipment)
	return args.Error(0)
}

func (m *MockEquipmentRepository) FindByPath(ctx context.Context, path string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, path)
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

func (m *MockEquipmentRepository) GetByLocation(ctx context.Context, buildingID, floor, room string) ([]*domain.Equipment, error) {
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

func (m *MockOrganizationRepository) GetByName(ctx context.Context, name string) (*domain.Organization, error) {
	args := m.Called(ctx, name)
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

func (m *MockOrganizationRepository) GetUsers(ctx context.Context, orgID string) ([]*domain.User, error) {
	args := m.Called(ctx, orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.User), args.Error(1)
}

func (m *MockOrganizationRepository) AddUser(ctx context.Context, orgID, userID string) error {
	args := m.Called(ctx, orgID, userID)
	return args.Error(0)
}

func (m *MockOrganizationRepository) RemoveUser(ctx context.Context, orgID, userID string) error {
	args := m.Called(ctx, orgID, userID)
	return args.Error(0)
}

// MockFloorRepository is a mock implementation of domain.FloorRepository
type MockFloorRepository struct {
	mock.Mock
}

func (m *MockFloorRepository) Create(ctx context.Context, floor *domain.Floor) error {
	args := m.Called(ctx, floor)
	return args.Error(0)
}

func (m *MockFloorRepository) GetByID(ctx context.Context, id string) (*domain.Floor, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Floor), args.Error(1)
}

func (m *MockFloorRepository) Update(ctx context.Context, floor *domain.Floor) error {
	args := m.Called(ctx, floor)
	return args.Error(0)
}

func (m *MockFloorRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockFloorRepository) List(ctx context.Context, buildingID string, limit, offset int) ([]*domain.Floor, error) {
	args := m.Called(ctx, buildingID, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Floor), args.Error(1)
}

func (m *MockFloorRepository) GetByBuilding(ctx context.Context, buildingID string) ([]*domain.Floor, error) {
	args := m.Called(ctx, buildingID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Floor), args.Error(1)
}

func (m *MockFloorRepository) GetEquipment(ctx context.Context, floorID string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, floorID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockFloorRepository) GetRooms(ctx context.Context, floorID string) ([]*domain.Room, error) {
	args := m.Called(ctx, floorID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Room), args.Error(1)
}

// MockRoomRepository is a mock implementation of domain.RoomRepository
type MockRoomRepository struct {
	mock.Mock
}

func (m *MockRoomRepository) Create(ctx context.Context, room *domain.Room) error {
	args := m.Called(ctx, room)
	return args.Error(0)
}

func (m *MockRoomRepository) GetByID(ctx context.Context, id string) (*domain.Room, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Room), args.Error(1)
}

func (m *MockRoomRepository) GetByNumber(ctx context.Context, floorID, number string) (*domain.Room, error) {
	args := m.Called(ctx, floorID, number)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Room), args.Error(1)
}

func (m *MockRoomRepository) Update(ctx context.Context, room *domain.Room) error {
	args := m.Called(ctx, room)
	return args.Error(0)
}

func (m *MockRoomRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockRoomRepository) List(ctx context.Context, floorID string, limit, offset int) ([]*domain.Room, error) {
	args := m.Called(ctx, floorID, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Room), args.Error(1)
}

func (m *MockRoomRepository) GetByFloor(ctx context.Context, floorID string) ([]*domain.Room, error) {
	args := m.Called(ctx, floorID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Room), args.Error(1)
}
