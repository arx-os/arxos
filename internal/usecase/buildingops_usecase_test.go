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

// TestBuildingOpsUseCase_ControlEquipment tests the ControlEquipment method
func TestBuildingOpsUseCase_ControlEquipment(t *testing.T) {
	t.Run("successful HVAC control", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testEquipment := createTestEquipment()
		testEquipment.Type = "hvac"

		mockEquipmentRepo.On("GetByID", mock.Anything, testEquipment.ID.String()).
			Return(testEquipment, nil)
		mockEquipmentRepo.On("Update", mock.Anything, mock.Anything).Return(nil)

		uc := NewBuildingOpsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.ControlEquipmentRequest{
			EquipmentID: testEquipment.ID,
			Action: &domain.ControlAction{
				Command: "cool",
			},
		}

		// Act
		err := uc.ControlEquipment(context.Background(), req)

		// Assert
		require.NoError(t, err)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("validation fails - invalid action for equipment type", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testEquipment := createTestEquipment()
		testEquipment.Type = "hvac"

		mockEquipmentRepo.On("GetByID", mock.Anything, testEquipment.ID.String()).
			Return(testEquipment, nil)

		uc := NewBuildingOpsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.ControlEquipmentRequest{
			EquipmentID: testEquipment.ID,
			Action: &domain.ControlAction{
				Command: "lock", // Invalid for HVAC
			},
		}

		// Act
		err := uc.ControlEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid HVAC action")
		mockEquipmentRepo.AssertNotCalled(t, "Update")
	})

	t.Run("equipment not found", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testID := types.NewID()

		mockEquipmentRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("equipment not found"))

		uc := NewBuildingOpsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.ControlEquipmentRequest{
			EquipmentID: testID,
			Action: &domain.ControlAction{
				Command: "on",
			},
		}

		// Act
		err := uc.ControlEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "equipment not found")
		mockEquipmentRepo.AssertExpectations(t)
	})
}

// TestBuildingOpsUseCase_SetBuildingMode tests the SetBuildingMode method
func TestBuildingOpsUseCase_SetBuildingMode(t *testing.T) {
	t.Run("successful mode change", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()
		equipment := []*domain.Equipment{
			createTestEquipment(),
			createTestEquipment(),
		}

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockEquipmentRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return(equipment, nil)

		uc := NewBuildingOpsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.SetBuildingModeRequest{
			BuildingID: testBuilding.ID,
			Mode:       "presentation",
		}

		// Act
		err := uc.SetBuildingMode(context.Background(), req)

		// Assert
		require.NoError(t, err)
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testID := types.NewID()

		mockBuildingRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("building not found"))

		uc := NewBuildingOpsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		req := &domain.SetBuildingModeRequest{
			BuildingID: testID,
			Mode:       "presentation",
		}

		// Act
		err := uc.SetBuildingMode(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "building not found")
		mockBuildingRepo.AssertExpectations(t)
	})
}

// TestBuildingOpsUseCase_MonitorBuildingHealth tests the MonitorBuildingHealth method
func TestBuildingOpsUseCase_MonitorBuildingHealth(t *testing.T) {
	t.Run("successful health report generation", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()
		equipment := []*domain.Equipment{
			{ID: types.NewID(), Status: "operational"},
			{ID: types.NewID(), Status: "operational"},
			{ID: types.NewID(), Status: "maintenance"},
		}

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockEquipmentRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return(equipment, nil)

		uc := NewBuildingOpsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.MonitorBuildingHealth(context.Background(), testBuilding.ID)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testBuilding.ID, result.BuildingID)
		assert.Equal(t, testBuilding.Name, result.BuildingName)
		assert.Equal(t, "healthy", result.OverallHealth)
		assert.Len(t, result.EquipmentHealth, 3)
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("degraded health with failed equipment", func(t *testing.T) {
		// Arrange
		mockBuildingRepo := new(MockBuildingRepository)
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()
		equipment := []*domain.Equipment{
			{ID: types.NewID(), Status: "operational"},
			{ID: types.NewID(), Status: "failed"},
		}

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockEquipmentRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return(equipment, nil)

		uc := NewBuildingOpsUseCase(mockBuildingRepo, mockEquipmentRepo, mockLogger)

		// Act
		result, err := uc.MonitorBuildingHealth(context.Background(), testBuilding.ID)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "degraded", result.OverallHealth)
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})
}
