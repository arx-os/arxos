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

// Test fixtures for EquipmentUseCase
func createTestEquipment() *domain.Equipment {
	return &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: types.NewID(),
		Name:       "Test HVAC Unit",
		Type:       "hvac",
		Model:      "HV-2000",
		Status:     "operational",
		Location: &domain.Location{
			X: 10.0,
			Y: 20.0,
			Z: 2.5,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// TestEquipmentUseCase_CreateEquipment tests the CreateEquipment method
func TestEquipmentUseCase_CreateEquipment(t *testing.T) {
	t.Run("successful creation", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testBuilding := createTestBuilding()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuilding.ID.String()).
			Return(testBuilding, nil)
		mockEquipmentRepo.On("Create", mock.Anything, mock.MatchedBy(func(e *domain.Equipment) bool {
			return e.Name == "New HVAC Unit" && e.Type == "hvac"
		})).Return(nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateEquipmentRequest{
			BuildingID: testBuilding.ID,
			Name:       "New HVAC Unit",
			Type:       "hvac",
			Model:      "HV-3000",
			Location: &domain.Location{
				X: 15.0,
				Y: 25.0,
				Z: 3.0,
			},
		}

		// Act
		result, err := uc.CreateEquipment(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "New HVAC Unit", result.Name)
		assert.Equal(t, "hvac", result.Type)
		assert.Equal(t, "operational", result.Status) // Default status
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty name", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateEquipmentRequest{
			BuildingID: types.NewID(),
			Name:       "",
			Type:       "hvac",
		}

		// Act
		result, err := uc.CreateEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "equipment name is required")
		mockEquipmentRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - empty type", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateEquipmentRequest{
			BuildingID: types.NewID(),
			Name:       "Test Equipment",
			Type:       "",
		}

		// Act
		result, err := uc.CreateEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "equipment type is required")
		mockEquipmentRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - invalid equipment type", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateEquipmentRequest{
			BuildingID: types.NewID(),
			Name:       "Test Equipment",
			Type:       "invalid_type",
		}

		// Act
		result, err := uc.CreateEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "invalid equipment type")
		mockEquipmentRepo.AssertNotCalled(t, "Create")
	})

	t.Run("validation fails - building not found", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testBuildingID := types.NewID()

		mockBuildingRepo.On("GetByID", mock.Anything, testBuildingID.String()).
			Return(nil, errors.New("building not found"))

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		req := &domain.CreateEquipmentRequest{
			BuildingID: testBuildingID,
			Name:       "Test Equipment",
			Type:       "hvac",
		}

		// Act
		result, err := uc.CreateEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building not found")
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertNotCalled(t, "Create")
	})
}

// TestEquipmentUseCase_GetEquipment tests the GetEquipment method
func TestEquipmentUseCase_GetEquipment(t *testing.T) {
	t.Run("successful retrieval", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testEquipment := createTestEquipment()

		mockEquipmentRepo.On("GetByID", mock.Anything, testEquipment.ID.String()).
			Return(testEquipment, nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetEquipment(context.Background(), testEquipment.ID.String())

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, testEquipment.Name, result.Name)
		assert.Equal(t, testEquipment.Type, result.Type)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty ID", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetEquipment(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "equipment ID is required")
		mockEquipmentRepo.AssertNotCalled(t, "GetByID")
	})

	t.Run("equipment not found", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testID := "nonexistent-id"

		mockEquipmentRepo.On("GetByID", mock.Anything, testID).
			Return(nil, errors.New("equipment not found"))

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetEquipment(context.Background(), testID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to get equipment")
		mockEquipmentRepo.AssertExpectations(t)
	})
}

// TestEquipmentUseCase_UpdateEquipment tests the UpdateEquipment method
func TestEquipmentUseCase_UpdateEquipment(t *testing.T) {
	t.Run("successful update", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		existingEquipment := createTestEquipment()
		newName := "Updated HVAC Unit"
		newStatus := "maintenance"

		mockEquipmentRepo.On("GetByID", mock.Anything, existingEquipment.ID.String()).
			Return(existingEquipment, nil)
		mockEquipmentRepo.On("Update", mock.Anything, mock.MatchedBy(func(e *domain.Equipment) bool {
			return e.Name == newName && e.Status == newStatus
		})).Return(nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		req := &domain.UpdateEquipmentRequest{
			ID:     existingEquipment.ID,
			Name:   &newName,
			Status: &newStatus,
		}

		// Act
		result, err := uc.UpdateEquipment(context.Background(), req)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, newName, result.Name)
		assert.Equal(t, newStatus, result.Status)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("equipment not found", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testID := types.NewID()

		mockEquipmentRepo.On("GetByID", mock.Anything, testID.String()).
			Return(nil, errors.New("equipment not found"))

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		newName := "Updated Equipment"
		req := &domain.UpdateEquipmentRequest{
			ID:   testID,
			Name: &newName,
		}

		// Act
		result, err := uc.UpdateEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to get equipment")
		mockEquipmentRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertNotCalled(t, "Update")
	})

	t.Run("validation fails - invalid type", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		existingEquipment := createTestEquipment()
		invalidType := "invalid_type"

		mockEquipmentRepo.On("GetByID", mock.Anything, existingEquipment.ID.String()).
			Return(existingEquipment, nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		req := &domain.UpdateEquipmentRequest{
			ID:   existingEquipment.ID,
			Type: &invalidType,
		}

		// Act
		result, err := uc.UpdateEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "invalid equipment type")
		mockEquipmentRepo.AssertNotCalled(t, "Update")
	})

	t.Run("validation fails - invalid status", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		existingEquipment := createTestEquipment()
		invalidStatus := "invalid_status"

		mockEquipmentRepo.On("GetByID", mock.Anything, existingEquipment.ID.String()).
			Return(existingEquipment, nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		req := &domain.UpdateEquipmentRequest{
			ID:     existingEquipment.ID,
			Status: &invalidStatus,
		}

		// Act
		result, err := uc.UpdateEquipment(context.Background(), req)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "invalid equipment status")
		mockEquipmentRepo.AssertNotCalled(t, "Update")
	})
}

// TestEquipmentUseCase_DeleteEquipment tests the DeleteEquipment method
func TestEquipmentUseCase_DeleteEquipment(t *testing.T) {
	t.Run("successful deletion", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testEquipment := createTestEquipment()
		testEquipment.Status = "inactive" // Not active, so can be deleted

		mockEquipmentRepo.On("GetByID", mock.Anything, testEquipment.ID.String()).
			Return(testEquipment, nil)
		mockEquipmentRepo.On("Delete", mock.Anything, testEquipment.ID.String()).
			Return(nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.DeleteEquipment(context.Background(), testEquipment.ID.String())

		// Assert
		require.NoError(t, err)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty ID", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.DeleteEquipment(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "equipment ID is required")
		mockEquipmentRepo.AssertNotCalled(t, "Delete")
	})

	t.Run("equipment not found", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testID := "nonexistent-id"

		mockEquipmentRepo.On("GetByID", mock.Anything, testID).
			Return(nil, errors.New("equipment not found"))

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.DeleteEquipment(context.Background(), testID)

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get equipment")
		mockEquipmentRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertNotCalled(t, "Delete")
	})

	t.Run("business rule - cannot delete active equipment", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testEquipment := createTestEquipment()
		testEquipment.Status = "active" // Active status - cannot be deleted

		mockEquipmentRepo.On("GetByID", mock.Anything, testEquipment.ID.String()).
			Return(testEquipment, nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.DeleteEquipment(context.Background(), testEquipment.ID.String())

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "cannot delete equipment with active status")
		mockEquipmentRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertNotCalled(t, "Delete")
	})
}

// TestEquipmentUseCase_ListEquipment tests the ListEquipment method
func TestEquipmentUseCase_ListEquipment(t *testing.T) {
	t.Run("successful list with default pagination", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		equipment := []*domain.Equipment{
			createTestEquipment(),
			createTestEquipment(),
		}

		mockEquipmentRepo.On("List", mock.Anything, mock.MatchedBy(func(f *domain.EquipmentFilter) bool {
			return f.Limit == 100 // Default pagination
		})).Return(equipment, nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		filter := &domain.EquipmentFilter{}

		// Act
		result, err := uc.ListEquipment(context.Background(), filter)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 2)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("successful list with custom filter", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testType := "hvac"
		equipment := []*domain.Equipment{
			createTestEquipment(),
		}

		mockEquipmentRepo.On("List", mock.Anything, mock.MatchedBy(func(f *domain.EquipmentFilter) bool {
			return f.Type != nil && *f.Type == testType && f.Limit == 50
		})).Return(equipment, nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		filter := &domain.EquipmentFilter{
			Type:  &testType,
			Limit: 50,
		}

		// Act
		result, err := uc.ListEquipment(context.Background(), filter)

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 1)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("repository error", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		mockEquipmentRepo.On("List", mock.Anything, mock.Anything).
			Return(nil, errors.New("database error"))

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		filter := &domain.EquipmentFilter{}

		// Act
		result, err := uc.ListEquipment(context.Background(), filter)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to list equipment")
		mockEquipmentRepo.AssertExpectations(t)
	})
}

// TestEquipmentUseCase_MoveEquipment tests the MoveEquipment method
func TestEquipmentUseCase_MoveEquipment(t *testing.T) {
	t.Run("successful move", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testEquipment := createTestEquipment()
		newLocation := &domain.Location{
			X: 30.0,
			Y: 40.0,
			Z: 5.0,
		}

		mockEquipmentRepo.On("GetByID", mock.Anything, testEquipment.ID.String()).
			Return(testEquipment, nil)
		mockEquipmentRepo.On("Update", mock.Anything, mock.MatchedBy(func(e *domain.Equipment) bool {
			return e.Location != nil && e.Location.X == 30.0 && e.Location.Y == 40.0 && e.Location.Z == 5.0
		})).Return(nil)

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.MoveEquipment(context.Background(), testEquipment.ID.String(), newLocation)

		// Assert
		require.NoError(t, err)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("equipment not found", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testID := "nonexistent-id"
		newLocation := &domain.Location{X: 30.0, Y: 40.0, Z: 5.0}

		mockEquipmentRepo.On("GetByID", mock.Anything, testID).
			Return(nil, errors.New("equipment not found"))

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		err := uc.MoveEquipment(context.Background(), testID, newLocation)

		// Assert
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get equipment")
		mockEquipmentRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertNotCalled(t, "Update")
	})
}

// TestEquipmentUseCase_GetEquipmentByBuilding tests the GetEquipmentByBuilding method
func TestEquipmentUseCase_GetEquipmentByBuilding(t *testing.T) {
	t.Run("successful retrieval", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
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

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetEquipmentByBuilding(context.Background(), testBuilding.ID.String())

		// Assert
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 2)
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertExpectations(t)
	})

	t.Run("validation fails - empty building ID", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetEquipmentByBuilding(context.Background(), "")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building ID is required")
		mockBuildingRepo.AssertNotCalled(t, "GetByID")
	})

	t.Run("building not found", func(t *testing.T) {
		// Arrange
		mockEquipmentRepo := new(MockEquipmentRepository)
		mockBuildingRepo := new(MockBuildingRepository)
		mockLogger := createPermissiveMockLogger()

		testBuildingID := "nonexistent-id"

		mockBuildingRepo.On("GetByID", mock.Anything, testBuildingID).
			Return(nil, errors.New("building not found"))

		uc := NewEquipmentUseCase(mockEquipmentRepo, mockBuildingRepo, mockLogger)

		// Act
		result, err := uc.GetEquipmentByBuilding(context.Background(), testBuildingID)

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "building not found")
		mockBuildingRepo.AssertExpectations(t)
		mockEquipmentRepo.AssertNotCalled(t, "GetByBuilding")
	})
}
