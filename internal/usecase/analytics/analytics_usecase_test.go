package analytics

import (
	utesting "github.com/arx-os/arxos/internal/usecase/testing"
	"context"
	"errors"
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

// TestAnalyticsUseCase_GetBuildingAnalytics tests the GetBuildingAnalytics method
func TestAnalyticsUseCase_GetBuildingAnalytics(t *testing.T) {
	t.Run("successful analytics generation", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testBuilding := utesting.CreateTestBuilding()
		equipment := []*domain.Equipment{
			{ID: types.NewID(), Status: "operational"},
			{ID: types.NewID(), Status: "operational"},
			{ID: types.NewID(), Status: "maintenance"},
			{ID: types.NewID(), Status: "failed"},
		}

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockEquipmentRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return(equipment, nil)

		uc := NewAnalyticsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.GetBuildingAnalytics(context.Background(), testBuilding.ID)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, 4, result.TotalEquipment)
		assert.Equal(t, 2, result.OperationalEquipment)
		assert.Equal(t, 1, result.MaintenanceEquipment)
		assert.Equal(t, 1, result.FailedEquipment)
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty building ID", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		uc := NewAnalyticsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.GetBuildingAnalytics(context.Background(), types.ID{})

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building ID is required")
		mockBuildingRepo.AssertNotCalled(t, "GetByID")
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testID := types.NewID()

		mockBuildingRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("building not found"))

		uc := NewAnalyticsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.GetBuildingAnalytics(context.Background(), testID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building not found")
		mockBuildingRepo.AssertExpectations(t)
	})
}

// TestAnalyticsUseCase_GetSystemAnalytics tests the GetSystemAnalytics method
func TestAnalyticsUseCase_GetSystemAnalytics(t *testing.T) {
	t.Run("successful system analytics", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		buildings := []*domain.Building{
			utesting.CreateTestBuilding(),
			utesting.CreateTestBuilding(),
		}
		equipment := []*domain.Equipment{
			{ID: types.NewID(), Status: "operational"},
			{ID: types.NewID(), Status: "operational"},
			{ID: types.NewID(), Status: "maintenance"},
		}

		mockBuildingRepo.On("List", mock.Anything, mock.Anything).Return(buildings, nil)
		mockEquipmentRepo.On("List", mock.Anything, mock.Anything).Return(equipment, nil)

		uc := NewAnalyticsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.GetSystemAnalytics(context.Background())

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, 2, result.TotalBuildings)
		assert.Equal(t, 3, result.TotalEquipment)
		assert.Equal(t, 2, result.OperationalEquipment)
		assert.Equal(t, 1, result.MaintenanceEquipment)
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})
}

// TestAnalyticsUseCase_GetEquipmentAnalytics tests the GetEquipmentAnalytics method
func TestAnalyticsUseCase_GetEquipmentAnalytics(t *testing.T) {
	t.Run("successful equipment analytics", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockEquipmentRepo := new(utesting.MockEquipmentRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		equipment := []*domain.Equipment{
			{ID: types.NewID(), Type: "hvac", Status: "operational"},
			{ID: types.NewID(), Type: "hvac", Status: "maintenance"},
			{ID: types.NewID(), Type: "lighting", Status: "operational"},
		}

		mockEquipmentRepo.On("List", mock.Anything, mock.Anything).Return(equipment, nil)

		uc := NewAnalyticsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		filter := &domain.EquipmentFilter{}

		// Act
		result, err := uc.GetEquipmentAnalytics(context.Background(), filter)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, 3, result.TotalEquipment)
		assert.Equal(t, 2, result.ByType["hvac"])
		assert.Equal(t, 1, result.ByType["lighting"])
		assert.Equal(t, 2, result.ByStatus["operational"])
		assert.Equal(t, 1, result.ByStatus["maintenance"])
		mockEquipmentRepo.AssertExpectations(t)
	})
}
