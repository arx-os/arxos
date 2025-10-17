package usecase

import (
	"context"
	"errors"
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

// TestBuildingUseCase_CreateBuilding tests the CreateBuilding method
func TestBuildingUseCase_CreateBuilding(t *testing.T) {
	t.Run("successful building creation", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		mockBuildingRepo.On("Create", mock.Anything, mock.MatchedBy(func(b *domain.Building) bool {
			return b.Name == "Test Building" && b.Address == "123 Test Street"
		})).Return(nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "Test Building",
			Address: "123 Test Street",
			Coordinates: &domain.Location{
				X: 40.7128,
				Y: -74.0060,
				Z: 0,
			},
		}

		// Act
		result, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "Test Building", result.Name)
		assert.Equal(t, "123 Test Street", result.Address)
		assert.NotNil(t, result.Coordinates)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty building name", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "",
			Address: "123 Test Street",
		}

		// Act
		result, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "validation failed")
		mockBuildingRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - empty address", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "Test Building",
			Address: "",
		}

		// Act
		result, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "validation failed")
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
			Name:    "Test Building",
			Address: "123 Test Street",
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
	t.Run("successful building retrieval", func(t *testing.T) {
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

	t.Run("validation fails - empty building ID", func(t *testing.T) {
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
	t.Run("successful building update", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		existingBuilding := createTestBuilding()
		newName := "Updated Building"
		newAddress := "999 Updated Street"

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
		newName := "Updated Building"

		mockBuildingRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("building not found"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

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

	t.Run("repository update error", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		existingBuilding := createTestBuilding()
		newName := "Updated Building"

		mockBuildingRepo.On("GetByID", mock.Anything, existingBuilding.ID.String()).
			Return(existingBuilding, nil)
		mockBuildingRepo.On("Update", mock.Anything, mock.Anything).
			Return(errors.New("database error"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.UpdateBuildingRequest{
			ID:   existingBuilding.ID,
			Name: &newName,
		}

		// Act
		result, err := uc.UpdateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to update building")
		mockBuildingRepo.AssertExpectations(t)
	})
}

// TestBuildingUseCase_DeleteBuilding tests the DeleteBuilding method
func TestBuildingUseCase_DeleteBuilding(t *testing.T) {
	t.Run("successful building deletion", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		// Mock the equipment check - return empty list (no equipment blocking deletion)
		mockEquipmentRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return([]*domain.Equipment{}, nil)
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

		testID := types.NewID()

		mockBuildingRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("building not found"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		err := uc.DeleteBuilding(context.Background(), testID.String())

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get building")
		mockBuildingRepo.AssertExpectations(t)
		mockBuildingRepo.AssertNotCalled(t, "Delete")
	})

	t.Run("repository delete error", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		// Mock the equipment check - return empty list
		mockEquipmentRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return([]*domain.Equipment{}, nil)
		mockBuildingRepo.On("Delete", mock.Anything, testBuilding.ID.String()).
			Return(errors.New("database error"))

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		err := uc.DeleteBuilding(context.Background(), testBuilding.ID.String())

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to delete building")
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})
}

// TestBuildingUseCase_ListBuildings tests the ListBuildings method
func TestBuildingUseCase_ListBuildings(t *testing.T) {
	t.Run("successful building list", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		buildings := []*domain.Building{
			createTestBuilding(),
			createTestBuilding(),
		}

		mockBuildingRepo.On("List", mock.Anything, mock.Anything).
			Return(buildings, nil)

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

	t.Run("empty result list", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		mockBuildingRepo.On("List", mock.Anything, mock.Anything).
			Return([]*domain.Building{}, nil)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		filter := &domain.BuildingFilter{}

		// Act
		result, err := uc.ListBuildings(context.Background(), filter)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 0)
		mockBuildingRepo.AssertExpectations(t)
	})
}
