package building

import (
	utesting "github.com/arx-os/arxos/internal/usecase/testing"
	"context"
	"errors"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// Reusing existing mocks from testing_helpers.go

func TestBuildingUseCase_CreateBuilding(t *testing.T) {
	t.Run("successful creation", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "Test Building",
			Address: "123 Test St",
			Coordinates: &domain.Location{
				X: -122.4194,
				Y: 37.7749,
				Z: 0,
			},
		}

		mockLogger.On("Info", "Creating building", mock.Anything).Return()
		mockBuildingRepo.On("Create", mock.Anything, mock.AnythingOfType("*domain.Building")).Return(nil)
		mockLogger.On("Info", "Building created successfully", mock.Anything).Return()

		// Act
		building, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		assert.NoError(t, err)
		assert.NotNil(t, building)
		assert.Equal(t, req.Name, building.Name)
		assert.Equal(t, req.Address, building.Address)
		assert.NotNil(t, building.Coordinates)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("validation error - empty name", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "",
			Address: "123 Test St",
		}

		mockLogger.On("Info", "Creating building", mock.Anything).Return()
		mockLogger.On("Error", "Building validation failed", mock.Anything).Return()

		// Act
		building, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, building)
		assert.Contains(t, err.Error(), "validation failed")
	})

	t.Run("repository error", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.CreateBuildingRequest{
			Name:    "Test Building",
			Address: "123 Test St",
		}

		repoError := errors.New("database connection error")
		mockLogger.On("Info", "Creating building", mock.Anything).Return()
		mockBuildingRepo.On("Create", mock.Anything, mock.AnythingOfType("*domain.Building")).Return(repoError)
		mockLogger.On("Error", "Failed to create building", mock.Anything).Return()

		// Act
		building, err := uc.CreateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, building)
		assert.Contains(t, err.Error(), "failed to create building")
		mockBuildingRepo.AssertExpectations(t)
	})
}

func TestBuildingUseCase_GetBuilding(t *testing.T) {
	t.Run("successful retrieval", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		buildingID := types.NewID()
		expectedBuilding := &domain.Building{
			ID:        buildingID,
			Name:      "Test Building",
			Address:   "123 Test St",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		mockLogger.On("Info", "Getting building", mock.Anything).Return()
		mockBuildingRepo.On("GetByID", mock.Anything, buildingID.String()).Return(expectedBuilding, nil)

		// Act
		building, err := uc.GetBuilding(context.Background(), buildingID)

		// Assert
		assert.NoError(t, err)
		assert.NotNil(t, building)
		assert.Equal(t, expectedBuilding.Name, building.Name)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("empty ID error", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		mockLogger.On("Info", "Getting building", mock.Anything).Return()

		// Act
		building, err := uc.GetBuilding(context.Background(), types.ID{})

		// Assert
		assert.Error(t, err)
		assert.Nil(t, building)
		assert.Contains(t, err.Error(), "building ID is required")
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		buildingID := types.NewID()
		notFoundError := errors.New("building not found")

		mockLogger.On("Info", "Getting building", mock.Anything).Return()
		mockBuildingRepo.On("GetByID", mock.Anything, buildingID.String()).Return(nil, notFoundError)
		mockLogger.On("Error", "Failed to get building", mock.Anything).Return()

		// Act
		building, err := uc.GetBuilding(context.Background(), buildingID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, building)
		assert.Contains(t, err.Error(), "failed to get building")
		mockBuildingRepo.AssertExpectations(t)
	})
}

func TestBuildingUseCase_UpdateBuilding(t *testing.T) {
	t.Run("successful update", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		buildingID := types.NewID()
		existingBuilding := &domain.Building{
			ID:        buildingID,
			Name:      "Old Name",
			Address:   "Old Address",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		newName := "New Name"
		newAddress := "New Address"
		req := &domain.UpdateBuildingRequest{
			ID:      buildingID,
			Name:    &newName,
			Address: &newAddress,
		}

		mockLogger.On("Info", "Updating building", mock.Anything).Return()
		mockBuildingRepo.On("GetByID", mock.Anything, buildingID.String()).Return(existingBuilding, nil)
		mockBuildingRepo.On("Update", mock.Anything, mock.AnythingOfType("*domain.Building")).Return(nil)
		mockLogger.On("Info", "Building updated successfully", mock.Anything).Return()

		// Act
		building, err := uc.UpdateBuilding(context.Background(), req)

		// Assert
		assert.NoError(t, err)
		assert.NotNil(t, building)
		assert.Equal(t, newName, building.Name)
		assert.Equal(t, newAddress, building.Address)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("building not found for update", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		buildingID := types.NewID()
		newName := "New Name"
		req := &domain.UpdateBuildingRequest{
			ID:   buildingID,
			Name: &newName,
		}

		notFoundError := errors.New("building not found")
		mockLogger.On("Info", "Updating building", mock.Anything).Return()
		mockBuildingRepo.On("GetByID", mock.Anything, buildingID.String()).Return(nil, notFoundError)
		mockLogger.On("Error", "Failed to get building for update", mock.Anything).Return()

		// Act
		building, err := uc.UpdateBuilding(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, building)
		assert.Contains(t, err.Error(), "failed to get building")
		mockBuildingRepo.AssertExpectations(t)
	})
}

func TestBuildingUseCase_DeleteBuilding(t *testing.T) {
	t.Run("successful deletion", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		buildingID := types.NewID().String()
		existingBuilding := &domain.Building{
			ID:   types.FromString(buildingID),
			Name: "Test Building",
		}

		mockLogger.On("Info", "Deleting building", mock.Anything).Return()
		mockBuildingRepo.On("GetByID", mock.Anything, buildingID).Return(existingBuilding, nil)
		mockBuildingRepo.On("Delete", mock.Anything, buildingID).Return(nil)
		mockLogger.On("Info", "Building deleted successfully", mock.Anything).Return()

		// Act
		err := uc.DeleteBuilding(context.Background(), buildingID)

		// Assert
		assert.NoError(t, err)
		mockBuildingRepo.AssertExpectations(t)
	})

	t.Run("empty ID error", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		mockLogger.On("Info", "Deleting building", mock.Anything).Return()

		// Act
		err := uc.DeleteBuilding(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "building ID is required")
	})
}

func TestBuildingUseCase_ListBuildings(t *testing.T) {
	t.Run("successful list", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := new(utesting.MockLogger)

		uc := NewBuildingUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		filter := &domain.BuildingFilter{
			Limit:  10,
			Offset: 0,
		}

		expectedBuildings := []*domain.Building{
			{ID: types.NewID(), Name: "Building 1"},
			{ID: types.NewID(), Name: "Building 2"},
		}

		mockLogger.On("Info", "Listing buildings", mock.Anything).Return()
		mockBuildingRepo.On("List", mock.Anything, filter).Return(expectedBuildings, nil)

		// Act
		buildings, err := uc.ListBuildings(context.Background(), filter)

		// Assert
		assert.NoError(t, err)
		assert.NotNil(t, buildings)
		assert.Len(t, buildings, 2)
		mockBuildingRepo.AssertExpectations(t)
	})
}
