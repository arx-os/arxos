package building

import (
	"context"
	"errors"
	"testing"

	utesting "github.com/arx-os/arxos/internal/usecase/testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
)

// Note: utesting.MockEquipmentRepository is defined in building_usecase_test.go

// SimpleLogger is a no-op logger for testing that doesn't panic
type SimpleLogger struct{}

func (l *SimpleLogger) Debug(msg string, fields ...any) {}
func (l *SimpleLogger) Info(msg string, fields ...any)  {}
func (l *SimpleLogger) Warn(msg string, fields ...any)  {}
func (l *SimpleLogger) Error(msg string, fields ...any) {}
func (l *SimpleLogger) Fatal(msg string, fields ...any) {}

func (l *SimpleLogger) WithFields(fields map[string]any) domain.Logger {
	return l
}

// TestGetEquipmentByPath tests the GetEquipmentByPath use case method
func TestGetEquipmentByPath(t *testing.T) {
	ctx := context.Background()

	t.Run("Success - Get equipment by exact path", func(t *testing.T) {
		// Setup
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		expectedEquipment := &domain.Equipment{
			ID:         types.FromString("eq-001"),
			BuildingID: types.FromString("b-001"),
			Name:       "VAV Unit 301",
			Type:       "hvac",
			Path:       "/B1/3/301/HVAC/VAV-301",
			Status:     "OPERATIONAL",
		}

		mockRepo.On("GetByPath", ctx, "/B1/3/301/HVAC/VAV-301").Return(expectedEquipment, nil)

		// Execute
		result, err := uc.GetEquipmentByPath(ctx, "/B1/3/301/HVAC/VAV-301")

		// Assert
		assert.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "VAV Unit 301", result.Name)
		assert.Equal(t, "/B1/3/301/HVAC/VAV-301", result.Path)
		mockRepo.AssertExpectations(t)
	})

	t.Run("Error - Equipment not found", func(t *testing.T) {
		// Setup
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		mockRepo.On("GetByPath", ctx, "/NONEXISTENT/PATH").Return(nil, errors.New("equipment not found"))

		// Execute
		result, err := uc.GetEquipmentByPath(ctx, "/NONEXISTENT/PATH")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "not found")
		mockRepo.AssertExpectations(t)
	})

	t.Run("Error - Empty path", func(t *testing.T) {
		// Setup
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		// Execute
		result, err := uc.GetEquipmentByPath(ctx, "")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "required")
	})
}

// TestFindEquipmentByPath tests the FindEquipmentByPath use case method
func TestFindEquipmentByPath(t *testing.T) {
	ctx := context.Background()

	t.Run("Success - Find HVAC equipment with wildcard", func(t *testing.T) {
		// Setup
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		expectedEquipment := []*domain.Equipment{
			{
				ID:         types.FromString("eq-001"),
				BuildingID: types.FromString("b-001"),
				Name:       "VAV Unit 301",
				Type:       "hvac",
				Path:       "/B1/3/301/HVAC/VAV-301",
				Status:     "OPERATIONAL",
			},
			{
				ID:         types.FromString("eq-002"),
				BuildingID: types.FromString("b-001"),
				Name:       "VAV Unit 302",
				Type:       "hvac",
				Path:       "/B1/3/302/HVAC/VAV-302",
				Status:     "OPERATIONAL",
			},
			{
				ID:         types.FromString("eq-003"),
				BuildingID: types.FromString("b-001"),
				Name:       "Air Handler 01",
				Type:       "hvac",
				Path:       "/B1/3/MECH/HVAC/AHU-01",
				Status:     "MAINTENANCE",
			},
		}

		mockRepo.On("FindByPath", ctx, "/B1/3/*/HVAC/*").Return(expectedEquipment, nil)

		// Execute
		result, err := uc.FindEquipmentByPath(ctx, "/B1/3/*/HVAC/*")

		// Assert
		assert.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 3)
		assert.Equal(t, "hvac", result[0].Type)
		assert.Equal(t, "hvac", result[1].Type)
		assert.Equal(t, "hvac", result[2].Type)
		mockRepo.AssertExpectations(t)
	})

	t.Run("Success - Find network equipment", func(t *testing.T) {
		// Setup
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		expectedEquipment := []*domain.Equipment{
			{
				ID:         types.FromString("eq-net-001"),
				BuildingID: types.FromString("b-001"),
				Name:       "Network Switch IDF 3A",
				Type:       "network",
				Path:       "/B1/3/IDF-3A/NETWORK/SW-01",
				Status:     "OPERATIONAL",
			},
			{
				ID:         types.FromString("eq-net-002"),
				BuildingID: types.FromString("b-001"),
				Name:       "Network Switch IDF 3B",
				Type:       "network",
				Path:       "/B1/3/IDF-3B/NETWORK/SW-01",
				Status:     "OPERATIONAL",
			},
		}

		mockRepo.On("FindByPath", ctx, "/B1/3/*/NETWORK/*").Return(expectedEquipment, nil)

		// Execute
		result, err := uc.FindEquipmentByPath(ctx, "/B1/3/*/NETWORK/*")

		// Assert
		assert.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 2)
		for _, eq := range result {
			assert.Equal(t, "network", eq.Type)
		}
		mockRepo.AssertExpectations(t)
	})

	t.Run("Success - No results found", func(t *testing.T) {
		// Setup
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		mockRepo.On("FindByPath", ctx, "/B1/99/*/HVAC/*").Return([]*domain.Equipment{}, nil)

		// Execute
		result, err := uc.FindEquipmentByPath(ctx, "/B1/99/*/HVAC/*")

		// Assert
		assert.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result, 0)
		mockRepo.AssertExpectations(t)
	})

	t.Run("Error - Empty pattern", func(t *testing.T) {
		// Setup
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		// Execute
		result, err := uc.FindEquipmentByPath(ctx, "")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "required")
	})

	t.Run("Error - Repository error", func(t *testing.T) {
		// Setup
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		mockRepo.On("FindByPath", ctx, "/B1/3/*/HVAC/*").Return(nil, errors.New("database error"))

		// Execute
		result, err := uc.FindEquipmentByPath(ctx, "/B1/3/*/HVAC/*")

		// Assert
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to query")
		mockRepo.AssertExpectations(t)
	})
}

// TestPathQueryEdgeCases tests edge cases and validation
func TestPathQueryEdgeCases(t *testing.T) {
	ctx := context.Background()

	t.Run("Path with special characters", func(t *testing.T) {
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		path := "/B1/3/ROOM-A1/HVAC/VAV-001"
		expectedEquipment := &domain.Equipment{
			ID:   types.FromString("eq-001"),
			Name: "Test Equipment",
			Path: path,
		}

		mockRepo.On("GetByPath", ctx, path).Return(expectedEquipment, nil)

		result, err := uc.GetEquipmentByPath(ctx, path)

		assert.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, path, result.Path)
	})

	t.Run("Multiple wildcards in pattern", func(t *testing.T) {
		mockRepo := new(utesting.MockEquipmentRepository)
		simpleLogger := &SimpleLogger{}
		uc := &EquipmentUseCase{
			equipmentRepo: mockRepo,
			logger:        simpleLogger,
		}

		pattern := "/B1/*/*/HVAC/*"
		expectedEquipment := []*domain.Equipment{
			{ID: types.FromString("eq-001"), Path: "/B1/1/101/HVAC/VAV-1"},
			{ID: types.FromString("eq-002"), Path: "/B1/2/201/HVAC/VAV-2"},
		}

		mockRepo.On("FindByPath", ctx, pattern).Return(expectedEquipment, nil)

		result, err := uc.FindEquipmentByPath(ctx, pattern)

		assert.NoError(t, err)
		assert.Len(t, result, 2)
	})
}
