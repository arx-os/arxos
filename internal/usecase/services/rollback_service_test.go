package services

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	utesting "github.com/arx-os/arxos/internal/usecase/testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockRoomRepository for rollback tests
type MockRoomRepository struct {
	mock.Mock
}

// MockVersionRepository for rollback tests
type MockVersionRepository struct {
	mock.Mock
}

func TestRollbackService_PreviewRollback(t *testing.T) {
	ctx := context.Background()
	buildingID := "building-123"

	// Create mocks
	mockSnapshotRepo := new(MockSnapshotRepository)
	mockTreeRepo := new(MockTreeRepository)
	mockLogger := utesting.CreatePermissiveMockLogger()

	service := NewRollbackService(
		nil, nil, nil, nil, // Building repos not needed for preview
		mockSnapshotRepo,
		nil,
		mockTreeRepo,
		nil,
		mockLogger,
	)

	// Create test snapshot
	snapshot := &building.Snapshot{
		Hash:      "snapshot-123",
		SpaceTree: "space-tree-123",
		ItemTree:  "item-tree-123",
		Metadata: building.SnapshotMetadata{
			SpaceCount: 56, // 1 building + 5 floors + 50 rooms combined
			ItemCount:  50,
		},
	}

	// Mock tree loading
	buildingTree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{Name: "floors", Type: building.ObjectTypeTree, Hash: "floors-tree-123"},
		},
	}

	floorsTree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: []building.TreeEntry{{}, {}, {}}, // 3 floors
	}

	equipmentTree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{Name: "HVAC", Type: building.ObjectTypeTree, Hash: "hvac-tree"},
		},
	}

	hvacTree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: make([]building.TreeEntry, 50), // 50 equipment items
	}

	mockTreeRepo.On("Load", ctx, "space-tree-123").Return(buildingTree, nil)
	mockTreeRepo.On("Load", ctx, "floors-tree-123").Return(floorsTree, nil)
	mockTreeRepo.On("Load", ctx, "item-tree-123").Return(equipmentTree, nil)
	mockTreeRepo.On("Load", ctx, "hvac-tree").Return(hvacTree, nil)

	// Execute preview
	changes, err := service.previewRollback(ctx, buildingID, snapshot)

	// Verify
	assert.NoError(t, err)
	assert.NotNil(t, changes)
	assert.True(t, changes.BuildingRestored)
	assert.Equal(t, 3, changes.FloorsRestored)
	assert.Equal(t, 50, changes.EquipmentRestored)
	assert.NotEmpty(t, changes.Details)

	mockTreeRepo.AssertExpectations(t)
}

func TestRollbackService_RestoreBuilding(t *testing.T) {
	ctx := context.Background()
	buildingID := "building-123"

	// Create mocks
	mockBuildingRepo := new(utesting.MockBuildingRepository)
	mockObjectRepo := new(MockObjectRepository)
	mockTreeRepo := new(MockTreeRepository)

	service := &RollbackService{
		buildingRepo: mockBuildingRepo,
		objectRepo:   mockObjectRepo,
		treeRepo:     mockTreeRepo,
	}

	// Create test building
	testBuilding := &domain.Building{
		ID:      types.FromString(buildingID),
		Name:    "Restored Building",
		Address: "123 Restored St",
	}

	buildingData, _ := json.Marshal(testBuilding)

	buildingObj := &building.Object{
		Hash:     "building-obj-123",
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(buildingData)),
		Contents: buildingData,
	}

	buildingTree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{
				Name: "building",
				Type: building.ObjectTypeBlob,
				Hash: "building-obj-123",
			},
		},
	}

	// Mock expectations
	mockTreeRepo.On("Load", ctx, "building-tree-123").Return(buildingTree, nil)
	mockObjectRepo.On("Load", ctx, "building-obj-123").Return(buildingObj, nil)
	mockBuildingRepo.On("Update", ctx, mock.AnythingOfType("*domain.Building")).Return(nil)

	// Execute
	err := service.restoreBuilding(ctx, buildingID, "building-tree-123")

	// Verify
	assert.NoError(t, err)

	mockTreeRepo.AssertExpectations(t)
	mockObjectRepo.AssertExpectations(t)
	mockBuildingRepo.AssertExpectations(t)
}

func TestRollbackService_RestoreFloors(t *testing.T) {
	ctx := context.Background()
	buildingID := "building-123"

	// Create mocks
	mockFloorRepo := new(MockFloorRepository)
	mockObjectRepo := new(MockObjectRepository)
	mockTreeRepo := new(MockTreeRepository)
	mockLogger := utesting.CreatePermissiveMockLogger()

	service := &RollbackService{
		floorRepo:  mockFloorRepo,
		objectRepo: mockObjectRepo,
		treeRepo:   mockTreeRepo,
		logger:     mockLogger,
	}

	// Create test floors
	floor1 := &domain.Floor{
		ID:    types.NewID(),
		Name:  "Floor 1",
		Level: 1,
	}
	floor2 := &domain.Floor{
		ID:    types.NewID(),
		Name:  "Floor 2",
		Level: 2,
	}

	floor1Data, _ := json.Marshal(floor1)
	floor2Data, _ := json.Marshal(floor2)

	floor1Obj := &building.Object{
		Hash:     "floor1-hash",
		Contents: floor1Data,
	}
	floor2Obj := &building.Object{
		Hash:     "floor2-hash",
		Contents: floor2Data,
	}

	buildingTree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{Name: "floors", Type: building.ObjectTypeTree, Hash: "floors-tree"},
		},
	}

	floorsTree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{Name: "floor-1", Hash: "floor1-hash"},
			{Name: "floor-2", Hash: "floor2-hash"},
		},
	}

	// Mock expectations
	mockTreeRepo.On("Load", ctx, "building-tree-123").Return(buildingTree, nil)
	mockTreeRepo.On("Load", ctx, "floors-tree").Return(floorsTree, nil)
	mockFloorRepo.On("GetByBuilding", ctx, buildingID).Return([]*domain.Floor{}, nil)
	mockObjectRepo.On("Load", ctx, "floor1-hash").Return(floor1Obj, nil)
	mockObjectRepo.On("Load", ctx, "floor2-hash").Return(floor2Obj, nil)
	mockFloorRepo.On("Create", ctx, mock.AnythingOfType("*domain.Floor")).Return(nil).Times(2)

	// Execute
	count, err := service.restoreFloors(ctx, buildingID, "building-tree-123")

	// Verify
	assert.NoError(t, err)
	assert.Equal(t, 2, count)

	mockTreeRepo.AssertExpectations(t)
	mockObjectRepo.AssertExpectations(t)
	mockFloorRepo.AssertExpectations(t)
}

func TestRollbackService_RestoreEquipment(t *testing.T) {
	ctx := context.Background()
	buildingID := "building-123"

	// Create mocks
	mockEquipmentRepo := new(utesting.MockEquipmentRepository)
	mockObjectRepo := new(MockObjectRepository)
	mockTreeRepo := new(MockTreeRepository)
	mockLogger := utesting.CreatePermissiveMockLogger()

	service := &RollbackService{
		equipmentRepo: mockEquipmentRepo,
		objectRepo:    mockObjectRepo,
		treeRepo:      mockTreeRepo,
		logger:        mockLogger,
	}

	// Create test equipment
	eq1 := &domain.Equipment{
		ID:   types.NewID(),
		Name: "AHU-101",
		Type: "HVAC",
	}
	eq2 := &domain.Equipment{
		ID:   types.NewID(),
		Name: "AHU-102",
		Type: "HVAC",
	}

	eq1Data, _ := json.Marshal(eq1)
	eq2Data, _ := json.Marshal(eq2)

	eq1Obj := &building.Object{Hash: "eq1-hash", Contents: eq1Data}
	eq2Obj := &building.Object{Hash: "eq2-hash", Contents: eq2Data}

	equipmentTree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{Name: "HVAC", Type: building.ObjectTypeTree, Hash: "hvac-tree"},
		},
	}

	hvacTree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{Name: "eq-1", Hash: "eq1-hash"},
			{Name: "eq-2", Hash: "eq2-hash"},
		},
	}

	// Mock expectations
	mockTreeRepo.On("Load", ctx, "equipment-tree-123").Return(equipmentTree, nil)
	mockTreeRepo.On("Load", ctx, "hvac-tree").Return(hvacTree, nil)
	mockEquipmentRepo.On("GetByBuilding", ctx, buildingID).Return([]*domain.Equipment{}, nil)
	mockObjectRepo.On("Load", ctx, "eq1-hash").Return(eq1Obj, nil)
	mockObjectRepo.On("Load", ctx, "eq2-hash").Return(eq2Obj, nil)
	mockEquipmentRepo.On("Create", ctx, mock.AnythingOfType("*domain.Equipment")).Return(nil).Times(2)

	// Execute
	count, err := service.restoreEquipment(ctx, buildingID, "equipment-tree-123")

	// Verify
	assert.NoError(t, err)
	assert.Equal(t, 2, count)

	mockTreeRepo.AssertExpectations(t)
	mockObjectRepo.AssertExpectations(t)
	mockEquipmentRepo.AssertExpectations(t)
}

func TestRollbackService_ValidateRollback(t *testing.T) {
	ctx := context.Background()
	buildingID := "building-123"

	// Create mocks
	mockBuildingRepo := new(utesting.MockBuildingRepository)
	mockFloorRepo := new(MockFloorRepository)
	mockEquipmentRepo := new(utesting.MockEquipmentRepository)

	service := &RollbackService{
		buildingRepo:  mockBuildingRepo,
		floorRepo:     mockFloorRepo,
		equipmentRepo: mockEquipmentRepo,
	}

	// Create test data
	testBuilding := &domain.Building{
		ID:   types.FromString(buildingID),
		Name: "Test Building",
	}

	testFloors := []*domain.Floor{
		{ID: types.NewID(), Name: "Floor 1"},
		{ID: types.NewID(), Name: "Floor 2"},
	}

	testEquipment := []*domain.Equipment{
		{ID: types.NewID(), Name: "AHU-101", BuildingID: types.FromString(buildingID)},
		{ID: types.NewID(), Name: "AHU-102", BuildingID: types.FromString(buildingID)},
	}

	snapshot := &building.Snapshot{
		Metadata: building.SnapshotMetadata{
			SpaceCount: 2,
			ItemCount:  2,
		},
	}

	// Mock expectations
	mockBuildingRepo.On("GetByID", ctx, buildingID).Return(testBuilding, nil)
	mockFloorRepo.On("GetByBuilding", ctx, buildingID).Return(testFloors, nil)
	mockEquipmentRepo.On("GetByBuilding", ctx, buildingID).Return(testEquipment, nil)

	// Execute
	result := service.validateRollback(ctx, buildingID, snapshot)

	// Verify
	assert.True(t, result.Valid)
	assert.NotEmpty(t, result.Checks)
	assert.Contains(t, result.Checks[0], "Building exists")
	assert.Contains(t, result.Checks, "Floors restored correctly (2)")
	assert.Contains(t, result.Checks, "Equipment restored correctly (2)")
	assert.Contains(t, result.Checks, "Referential integrity verified")

	mockBuildingRepo.AssertExpectations(t)
	mockFloorRepo.AssertExpectations(t)
	mockEquipmentRepo.AssertExpectations(t)
}

func TestRollbackService_ValidateRollback_CountMismatch(t *testing.T) {
	ctx := context.Background()
	buildingID := "building-123"

	// Create mocks
	mockBuildingRepo := new(utesting.MockBuildingRepository)
	mockFloorRepo := new(MockFloorRepository)
	mockEquipmentRepo := new(utesting.MockEquipmentRepository)

	service := &RollbackService{
		buildingRepo:  mockBuildingRepo,
		floorRepo:     mockFloorRepo,
		equipmentRepo: mockEquipmentRepo,
	}

	// Create test data with wrong counts
	testBuilding := &domain.Building{
		ID:   types.FromString(buildingID),
		Name: "Test Building",
	}

	testFloors := []*domain.Floor{
		{ID: types.NewID(), Name: "Floor 1"},
	}

	testEquipment := []*domain.Equipment{
		{ID: types.NewID(), Name: "AHU-101", BuildingID: types.FromString(buildingID)},
	}

	snapshot := &building.Snapshot{
		Metadata: building.SnapshotMetadata{
			SpaceCount: 3, // Expect 3, got 1
			ItemCount:  5, // Expect 5, got 1
		},
	}

	// Mock expectations
	mockBuildingRepo.On("GetByID", ctx, buildingID).Return(testBuilding, nil)
	mockFloorRepo.On("GetByBuilding", ctx, buildingID).Return(testFloors, nil)
	mockEquipmentRepo.On("GetByBuilding", ctx, buildingID).Return(testEquipment, nil)

	// Execute
	result := service.validateRollback(ctx, buildingID, snapshot)

	// Verify - should still be valid but with warnings
	assert.True(t, result.Valid)
	assert.NotEmpty(t, result.Warnings)
	assert.Contains(t, result.Warnings[0], "Floor count mismatch")
	assert.Contains(t, result.Warnings[1], "Equipment count mismatch")

	mockBuildingRepo.AssertExpectations(t)
	mockFloorRepo.AssertExpectations(t)
	mockEquipmentRepo.AssertExpectations(t)
}

func TestRollbackService_CountEquipment(t *testing.T) {
	ctx := context.Background()

	mockTreeRepo := new(MockTreeRepository)
	service := &RollbackService{
		treeRepo: mockTreeRepo,
	}

	// Create test trees
	equipmentTree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{Name: "HVAC", Type: building.ObjectTypeTree, Hash: "hvac-tree"},
			{Name: "Electrical", Type: building.ObjectTypeTree, Hash: "electrical-tree"},
		},
	}

	hvacTree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: make([]building.TreeEntry, 10), // 10 HVAC items
	}

	electricalTree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: make([]building.TreeEntry, 5), // 5 electrical items
	}

	// Mock expectations
	mockTreeRepo.On("Load", ctx, "equipment-tree-123").Return(equipmentTree, nil)
	mockTreeRepo.On("Load", ctx, "hvac-tree").Return(hvacTree, nil)
	mockTreeRepo.On("Load", ctx, "electrical-tree").Return(electricalTree, nil)

	// Execute
	count, err := service.countEquipment(ctx, "equipment-tree-123")

	// Verify
	assert.NoError(t, err)
	assert.Equal(t, 15, count) // 10 + 5

	mockTreeRepo.AssertExpectations(t)
}

func TestRollbackService_GenerateRollbackTag(t *testing.T) {
	service := &RollbackService{}

	tests := []struct {
		name       string
		currentTag string
	}{
		{"version 1.0.0", "v1.0.0"},
		{"version 2.3.4", "v2.3.4"},
		{"version with suffix", "v1.0.0-beta"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tag := service.generateRollbackTag(tt.currentTag)

			assert.NotEmpty(t, tag)
			assert.Contains(t, tag, tt.currentTag)
			assert.Contains(t, tag, "rollback")
		})
	}
}

func TestRollbackOptions_DryRun(t *testing.T) {
	opts := &RollbackOptions{
		DryRun:        true,
		CreateVersion: false,
		ValidateAfter: false,
	}

	assert.True(t, opts.DryRun)
	assert.False(t, opts.CreateVersion)
	assert.False(t, opts.ValidateAfter)
}

func TestRollbackResult_Structure(t *testing.T) {
	result := &RollbackResult{
		Success:         true,
		TargetVersion:   "v1.0.0",
		PreviousVersion: "v1.1.0",
		Changes: &RollbackChanges{
			BuildingRestored:  true,
			FloorsRestored:    3,
			EquipmentRestored: 50,
		},
		Duration: time.Second,
	}

	assert.True(t, result.Success)
	assert.Equal(t, "v1.0.0", result.TargetVersion)
	assert.Equal(t, "v1.1.0", result.PreviousVersion)
	assert.NotNil(t, result.Changes)
	assert.Equal(t, 3, result.Changes.FloorsRestored)
}

func TestValidationResult_Valid(t *testing.T) {
	result := &ValidationResult{
		Valid:    true,
		Checks:   []string{"Building exists", "Floors restored"},
		Warnings: []string{},
		Errors:   []string{},
	}

	assert.True(t, result.Valid)
	assert.Equal(t, 2, len(result.Checks))
	assert.Empty(t, result.Warnings)
	assert.Empty(t, result.Errors)
}

func TestValidationResult_Invalid(t *testing.T) {
	result := &ValidationResult{
		Valid:    false,
		Checks:   []string{"Building exists"},
		Warnings: []string{"Count mismatch"},
		Errors:   []string{"Building not found"},
	}

	assert.False(t, result.Valid)
	assert.NotEmpty(t, result.Checks)
	assert.NotEmpty(t, result.Warnings)
	assert.NotEmpty(t, result.Errors)
}
