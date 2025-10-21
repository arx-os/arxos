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

// TestRoomUseCase_CreateRoom tests the CreateRoom method
func TestRoomUseCase_CreateRoom(t *testing.T) {
	t.Run("successful room creation", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testFloor := utesting.CreateTestFloor()

		mockFloorRepo.On("GetByID", mock.Anything, testFloor.ID.String()).
			Return(testFloor, nil)
		// Mock duplicate check - room doesn't exist yet
		mockRoomRepo.On("GetByNumber", mock.Anything, testFloor.ID.String(), "101").
			Return(nil, errors.New("not found"))
		mockRoomRepo.On("Create", mock.Anything, mock.MatchedBy(func(r *domain.Room) bool {
			return r.Name == "Test Room" && r.Number == "101"
		})).Return(nil)

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateRoomRequest{
			FloorID: testFloor.ID,
			Number:  "101",
			Name:    "Test Room",
			Height:  2.7,
		}

		// Act
		result, err := uc.CreateRoom(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "Test Room", result.Name)
		assert.Equal(t, "101", result.Number)
		mockFloorRepo.AssertExpectations(t)
		mockRoomRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty room number", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testFloor := utesting.CreateTestFloor()

		mockFloorRepo.On("GetByID", mock.Anything, testFloor.ID.String()).
			Return(testFloor, nil)

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateRoomRequest{
			FloorID: testFloor.ID,
			Number:  "",
			Name:    "Test Room",
		}

		// Act
		result, err := uc.CreateRoom(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "validation failed")
		mockFloorRepo.AssertExpectations(t)
		mockRoomRepo.AssertNotCalled(t, "Create")
	})

	t.Run("floor not found", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testID := types.NewID()

		mockFloorRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("floor not found"))

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateRoomRequest{
			FloorID: testID,
			Number:  "101",
			Name:    "Test Room",
		}

		// Act
		result, err := uc.CreateRoom(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "floor not found")
		mockFloorRepo.AssertExpectations(t)
		mockRoomRepo.AssertNotCalled(t, "Create")
	})
}

// TestRoomUseCase_GetRoom tests the GetRoom method
func TestRoomUseCase_GetRoom(t *testing.T) {
	t.Run("successful room retrieval", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testRoom := utesting.CreateTestRoom()

		mockRoomRepo.On("GetByID", mock.Anything, testRoom.ID.String()).
			Return(testRoom, nil)

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetRoom(context.Background(), testRoom.ID)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testRoom.Name, result.Name)
		assert.Equal(t, testRoom.Number, result.Number)
		mockRoomRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty room ID", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetRoom(context.Background(), types.ID{})

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "room ID is required")
		mockRoomRepo.AssertNotCalled(t, "GetByID")
	})

	t.Run("room not found", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testID := types.NewID()

		mockRoomRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("room not found"))

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetRoom(context.Background(), testID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to get room")
		mockRoomRepo.AssertExpectations(t)
	})
}

// TestRoomUseCase_ListRooms tests the ListRooms method
func TestRoomUseCase_ListRooms(t *testing.T) {
	t.Run("successful room list by floor", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testFloor := utesting.CreateTestFloor()
		rooms := []*domain.Room{
			utesting.CreateTestRoom(),
			utesting.CreateTestRoom(),
		}

		// Mock floor validation check
		mockFloorRepo.On("GetByID", mock.Anything, testFloor.ID.String()).
			Return(testFloor, nil)
		mockRoomRepo.On("GetByFloor", mock.Anything, testFloor.ID.String()).
			Return(rooms, nil)

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.ListRooms(context.Background(), testFloor.ID, 100, 0)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 2)
		mockFloorRepo.AssertExpectations(t)
		mockRoomRepo.AssertExpectations(t)
	})

	t.Run("empty result list", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testFloor := utesting.CreateTestFloor()

		// Mock floor validation check
		mockFloorRepo.On("GetByID", mock.Anything, testFloor.ID.String()).
			Return(testFloor, nil)
		mockRoomRepo.On("GetByFloor", mock.Anything, testFloor.ID.String()).
			Return([]*domain.Room{}, nil)

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.ListRooms(context.Background(), testFloor.ID, 100, 0)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 0)
		mockRoomRepo.AssertExpectations(t)
	})
}

// TestRoomUseCase_DeleteRoom tests the DeleteRoom method
func TestRoomUseCase_DeleteRoom(t *testing.T) {
	t.Run("successful room deletion", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testRoom := utesting.CreateTestRoom()

		mockRoomRepo.On("GetByID", mock.Anything, testRoom.ID.String()).
			Return(testRoom, nil)
		mockRoomRepo.On("Delete", mock.Anything, testRoom.ID.String()).
			Return(nil)

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.DeleteRoom(context.Background(), testRoom.ID.String())

		// Assert
		require.NoError(t, err)
		mockRoomRepo.AssertExpectations(t)
	})

	t.Run("room not found", func(t *testing.T) {
		// Arrange
		mockRoomRepo := new(utesting.MockRoomRepository)
		mockFloorRepo := new(utesting.MockFloorRepository)
		mockBuildingRepo := new(utesting.MockBuildingRepository)
		mockLogger := utesting.CreatePermissiveMockLogger()

		testID := types.NewID()

		mockRoomRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("room not found"))

		uc := NewRoomUseCase(mockRoomRepo, mockFloorRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.DeleteRoom(context.Background(), testID.String())

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "room not found")
		mockRoomRepo.AssertExpectations(t)
		mockRoomRepo.AssertNotCalled(t, "Delete")
	})
}
