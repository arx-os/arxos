package building

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

// TestFloorUseCase_CreateFloor tests the CreateFloor method
func TestFloorUseCase_CreateFloor(t *testing.T) {
	t.Run("successful floor creation", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testBuilding := utesting.CreateTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockFloorRepo.On("Create", mock.Anything, mock.MatchedBy(func(f *domain.Floor) bool {
			return f.Name == "Ground Floor" && f.Level == 0
		})).Return(nil)

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateFloorRequest{
			BuildingID: testBuilding.ID,
			Name:       "Ground Floor",
			Level:      0,
		}

		// Act
		result, err := uc.CreateFloor(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "Ground Floor", result.Name)
		assert.Equal(t, 0, result.Level)
		mockBuildingRepo.AssertExpectations(t)
		mockFloorRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty floor name", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testBuilding := utesting.CreateTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateFloorRequest{
			BuildingID: testBuilding.ID,
			Name:       "",
			Level:      0,
		}

		// Act
		result, err := uc.CreateFloor(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "validation failed")
		mockBuildingRepo.AssertExpectations(t)
		mockFloorRepo.AssertNotCalled(t, "Create")
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testID := types.NewID()

		mockBuildingRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("building not found"))

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateFloorRequest{
			BuildingID: testID,
			Name:       "Ground Floor",
			Level:      0,
		}

		// Act
		result, err := uc.CreateFloor(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building not found")
		mockBuildingRepo.AssertExpectations(t)
		mockFloorRepo.AssertNotCalled(t, "Create")
	})

	t.Run("repository error", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testBuilding := utesting.CreateTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockFloorRepo.On("Create", mock.Anything, mock.Anything).
			Return(errors.New("database error"))

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateFloorRequest{
			BuildingID: testBuilding.ID,
			Name:       "Ground Floor",
			Level:      0,
		}

		// Act
		result, err := uc.CreateFloor(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to create floor")
		mockBuildingRepo.AssertExpectations(t)
		mockFloorRepo.AssertExpectations(t)
	})
}

// TestFloorUseCase_GetFloor tests the GetFloor method
func TestFloorUseCase_GetFloor(t *testing.T) {
	t.Run("successful floor retrieval", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testFloor := utesting.CreateTestFloor()

		mockFloorRepo.On("GetByID", mock.Anything, testFloor.ID.String()).
			Return(testFloor, nil)

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetFloor(context.Background(), testFloor.ID)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testFloor.Name, result.Name)
		assert.Equal(t, testFloor.Level, result.Level)
		mockFloorRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty floor ID", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetFloor(context.Background(), types.ID{})

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "floor ID is required")
		mockFloorRepo.AssertNotCalled(t, "GetByID")
	})

	t.Run("floor not found", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testID := types.NewID()

		mockFloorRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("floor not found"))

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetFloor(context.Background(), testID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to get floor")
		mockFloorRepo.AssertExpectations(t)
	})
}

// TestFloorUseCase_ListFloors tests the ListFloors method
func TestFloorUseCase_ListFloors(t *testing.T) {
	t.Run("successful floor list", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testBuilding := utesting.CreateTestBuilding()
		floors := []*domain.Floor{
			utesting.CreateTestFloor(),
			utesting.CreateTestFloor(),
		}

		// Mock building validation check
		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockFloorRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return(floors, nil)

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.ListFloors(context.Background(), testBuilding.ID, 100, 0)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 2)
		mockBuildingRepo.AssertExpectations(t)
		mockFloorRepo.AssertExpectations(t)
	})

	t.Run("empty result list", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testBuilding := utesting.CreateTestBuilding()

		// Mock building validation check
		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockFloorRepo.On("GetByBuilding", mock.Anything, testBuilding.ID.String()).
			Return([]*domain.Floor{}, nil)

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.ListFloors(context.Background(), testBuilding.ID, 100, 0)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 0)
		mockFloorRepo.AssertExpectations(t)
	})
}

// TestFloorUseCase_DeleteFloor tests the DeleteFloor method
func TestFloorUseCase_DeleteFloor(t *testing.T) {
	t.Run("successful floor deletion", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testFloor := utesting.CreateTestFloor()

		mockFloorRepo.On("GetByID", mock.Anything, testFloor.ID.String()).
			Return(testFloor, nil)
		mockFloorRepo.On("Delete", mock.Anything, testFloor.ID.String()).
			Return(nil)

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.DeleteFloor(context.Background(), testFloor.ID.String())

		// Assert
		require.NoError(t, err)
		mockFloorRepo.AssertExpectations(t)
	})

	t.Run("floor not found", func(t *testing.T) {
		// Arrange
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testID := types.NewID()

		mockFloorRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("floor not found"))

		uc := NewFloorUseCase(mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.DeleteFloor(context.Background(), testID.String())

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "floor not found")
		mockFloorRepo.AssertExpectations(t)
		mockFloorRepo.AssertNotCalled(t, "Delete")
	})
}
