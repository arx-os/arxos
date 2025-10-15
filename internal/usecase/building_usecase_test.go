package usecase

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

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

func (m *MockBuildingRepository) GetByAddress(ctx context.Context, address string) (*domain.Building, error) {
	args := m.Called(ctx, address)
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

func (m *MockEquipmentRepository) GetByType(ctx context.Context, equipmentType string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, equipmentType)
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

func (m *MockEquipmentRepository) GetByLocation(ctx context.Context, buildingID string, floor string, room string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, buildingID, floor, room)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) GetByPath(ctx context.Context, exactPath string) (*domain.Equipment, error) {
	args := m.Called(ctx, exactPath)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Equipment), args.Error(1)
}

func (m *MockEquipmentRepository) FindByPath(ctx context.Context, pathPattern string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, pathPattern)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

// Test fixtures for BuildingUseCase
func createTestBuilding() *domain.Building {
	return &domain.Building{
		ID:      types.NewID(),
		Name:    "Test Building",
		Address: "123 Test St",
		Coordinates: &domain.Location{
			X: 10.0,
			Y: 20.0,
			Z: 0.0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// TestBuildingUseCase_CreateBuilding tests the CreateBuilding method
func TestBuildingUseCase_CreateBuilding(t *testing.T) {
	t.Run("successful creation", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		mockBuildingRepo.On("Create", mock.Anything, mock.MatchedBy(func(b *domain.Building) bool {
			return b.Name == "New Building" && b.Address == "456 New St"
		})).Return(nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "New Building",
			Address: "456 New St",
			Coordinates: &domain.Location{
				X: 15.0,
				Y: 25.0,
				Z: 0.0,
			},
		}

		// Act
		result, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "New Building", result.Name)
		assert.Equal(t, "456 New St", result.Address)
		assert.NotNil(t, result.Coordinates)
		assert.Equal(t, 15.0, result.Coordinates.X)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty name", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "",
			Address: "456 New St",
		}

		// Act
		result, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building name is required")
		mockBuildingRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - empty address", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "New Building",
			Address: "",
		}

		// Act
		result, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building address is required")
		mockBuildingRepo.AssertNotCalled(t, "Create")
	})

	t.Run("repository error", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		mockBuildingRepo.On("Create", mock.Anything, mock.Anything).
			Return(errors.New("database error"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "New Building",
			Address: "456 New St",
		}

		// Act
		result, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to create building")
		mockBuildingRepo.AssertExpectations(t)
	})
}

// TestBuildingUseCase_GetBuilding tests the GetBuilding method
func TestBuildingUseCase_GetBuilding(t *testing.T) {
	t.Run("successful retrieval", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.GetBuilding(context.Background(), testBuilding.ID)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testBuilding.Name, result.Name)
		assert.Equal(t, testBuilding.Address, result.Address)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty ID", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.GetBuilding(context.Background(), types.ID{})

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building ID is required")
		mockBuildingRepo.AssertNotCalled(t, "GetByID")
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testID := types.NewID()

		mockBuildingRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("building not found"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.GetBuilding(context.Background(), testID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to get building")
		mockBuildingRepo.AssertExpectations(t)
	})
}

// TestBuildingUseCase_UpdateBuilding tests the UpdateBuilding method
func TestBuildingUseCase_UpdateBuilding(t *testing.T) {
	t.Run("successful update", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		existingBuilding := createTestBuilding()
		newName := "Updated Building"
		newAddress := "789 Updated St"

		mockBuildingRepo.On("GetByID", mock.Anything, existingBuilding.ID.String()).
			Return(existingBuilding, nil)
		mockBuildingRepo.On("Update", mock.Anything, mock.MatchedBy(func(b *domain.Building) bool {
			return b.Name == newName && b.Address == newAddress
		})).Return(nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.UpdateBuildingRequest{
			ID:      existingBuilding.ID,
			Name:    &newName,
			Address: &newAddress,
		}

		// Act
		result, err := uc.UpdateBuilding(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, newName, result.Name)
		assert.Equal(t, newAddress, result.Address)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testID := types.NewID()

		mockBuildingRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("building not found"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		newName := "Updated Building"
		req := &domain.UpdateBuildingRequest{
			ID:   testID,
			Name: &newName,
		}

		// Act
		result, err := uc.UpdateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to get building")
		mockBuildingRepo.AssertExpectations(t)
		mockBuildingRepo.AssertNotCalled(t, "Update")
	})

	t.Run("validation fails - empty name", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		existingBuilding := createTestBuilding()
		emptyName := ""

		mockBuildingRepo.On("GetByID", mock.Anything, existingBuilding.ID.String()).
			Return(existingBuilding, nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.UpdateBuildingRequest{
			ID:   existingBuilding.ID,
			Name: &emptyName,
		}

		// Act
		result, err := uc.UpdateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building name cannot be empty")
		mockBuildingRepo.AssertNotCalled(t, "Update")
	})
}

// TestBuildingUseCase_DeleteBuilding tests the DeleteBuilding method
func TestBuildingUseCase_DeleteBuilding(t *testing.T) {
	t.Run("successful deletion", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockEquipmentRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return([]*domain.Equipment{}, nil) // No equipment
		mockBuildingRepo.On("Delete", mock.Anything, testBuilding.ID.String()).
			Return(nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		err := uc.DeleteBuilding(context.Background(), testBuilding.ID.String())

		// Assert
		require.NoError(t, err)
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty ID", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		err := uc.DeleteBuilding(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "building ID is required")
		mockBuildingRepo.AssertNotCalled(t, "Delete")
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testID := "nonexistent-id"

		mockBuildingRepo.On("GetByID", mock.Anything, testID).
			Return(nil, errors.New("building not found"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		err := uc.DeleteBuilding(context.Background(), testID)

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get building")
		mockBuildingRepo.AssertExpectations(t)
		mockBuildingRepo.AssertNotCalled(t, "Delete")
	})

	t.Run("business rule - cannot delete with equipment", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()
		equipment := []*domain.Equipment{
			{ID: types.NewID(), Name: "HVAC Unit 1"},
		}

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockEquipmentRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return(equipment, nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		err := uc.DeleteBuilding(context.Background(), testBuilding.ID.String())

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "cannot delete building with existing equipment")
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
		mockBuildingRepo.AssertNotCalled(t, "Delete")
	})
}

// TestBuildingUseCase_ListBuildings tests the ListBuildings method
func TestBuildingUseCase_ListBuildings(t *testing.T) {
	t.Run("successful list with default pagination", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		buildings := []*domain.Building{
			createTestBuilding(),
			createTestBuilding(),
		}

		mockBuildingRepo.On("List", mock.Anything, mock.MatchedBy(func(f *domain.BuildingFilter) bool {
			return f.Limit == 100 // Default pagination
		})).Return(buildings, nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		filter := &domain.BuildingFilter{}

		// Act
		result, err := uc.ListBuildings(context.Background(), filter)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 2)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("successful list with custom filter", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testName := "Test Building"
		buildings := []*domain.Building{
			createTestBuilding(),
		}

		mockBuildingRepo.On("List", mock.Anything, mock.MatchedBy(func(f *domain.BuildingFilter) bool {
			return f.Name != nil && *f.Name == testName && f.Limit == 50
		})).Return(buildings, nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		filter := &domain.BuildingFilter{
			Name:  &testName,
			Limit: 50,
		}

		// Act
		result, err := uc.ListBuildings(context.Background(), filter)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 1)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("repository error", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		mockBuildingRepo.On("List", mock.Anything, mock.Anything).
			Return(nil, errors.New("database error"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		filter := &domain.BuildingFilter{}

		// Act
		result, err := uc.ListBuildings(context.Background(), filter)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to list buildings")
		mockBuildingRepo.AssertExpectations(t)
	})
}

// TestBuildingUseCase_ImportBuilding tests the ImportBuilding method
func TestBuildingUseCase_ImportBuilding(t *testing.T) {
	t.Run("successful IFC import", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		ifcData := []byte("mock IFC data content")

		mockBuildingRepo.On("Create", mock.Anything, mock.MatchedBy(func(b *domain.Building) bool {
			return b.Name == "Imported IFC Building"
		})).Return(nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.ImportBuildingRequest{
			Format: "ifc",
			Data:   ifcData,
		}

		// Act
		result, err := uc.ImportBuilding(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "Imported IFC Building", result.Name)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("validation fails - unsupported format", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.ImportBuildingRequest{
			Format: "gbxml",
			Data:   []byte("some data"),
		}

		// Act
		result, err := uc.ImportBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "only IFC format is supported")
		mockBuildingRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - empty data", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.ImportBuildingRequest{
			Format: "ifc",
			Data:   []byte{},
		}

		// Act
		result, err := uc.ImportBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "IFC data is empty")
		mockBuildingRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - file too large", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Create data larger than 200MB
		largeData := make([]byte, 201*1024*1024)

		req := &domain.ImportBuildingRequest{
			Format: "ifc",
			Data:   largeData,
		}

		// Act
		result, err := uc.ImportBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "IFC file too large")
		mockBuildingRepo.AssertNotCalled(t, "Create")
	})
}

// TestBuildingUseCase_ExportBuilding tests the ExportBuilding method
func TestBuildingUseCase_ExportBuilding(t *testing.T) {
	t.Run("export not implemented", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.ExportBuilding(context.Background(), testBuilding.ID.String(), "json")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building export not implemented")
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testID := "nonexistent-id"

		mockBuildingRepo.On("GetByID", mock.Anything, testID).
			Return(nil, errors.New("building not found"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.ExportBuilding(context.Background(), testID, "json")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to get building")
		mockBuildingRepo.AssertExpectations(t)
	})
}
