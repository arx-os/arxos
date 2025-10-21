package services

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
)

func TestDiffService_PhaseOneTreeDiff(t *testing.T) {
	service := &DiffService{}

	fromSnapshot := &building.Snapshot{
		Hash:           "snapshot1",
		SpaceTree:      "space-tree-1",
		ItemTree:       "item-tree-1",
		SpatialTree:    "spatial-tree-1",
		FilesTree:      "files-tree-1",
		OperationsTree: "operations-tree-1",
	}

	toSnapshot := &building.Snapshot{
		Hash:           "snapshot2",
		SpaceTree:      "space-tree-1",      // Same
		ItemTree:       "item-tree-2",       // Changed
		SpatialTree:    "spatial-tree-1",    // Same
		FilesTree:      "files-tree-2",      // Changed
		OperationsTree: "operations-tree-1", // Same
	}

	diff := service.phaseOneTreeDiff(fromSnapshot, toSnapshot)

	// Verify tree-level comparison
	assert.False(t, diff.SpaceChanged, "Space tree should not have changed")
	assert.True(t, diff.ItemChanged, "Item tree should have changed")
	assert.False(t, diff.SpatialChanged, "Spatial tree should not have changed")
	assert.True(t, diff.FilesChanged, "Files tree should have changed")
	assert.False(t, diff.OperationsChanged, "Operations tree should not have changed")
}

func TestDiffService_BuildEntryMap(t *testing.T) {
	service := &DiffService{}

	tree := &building.Tree{
		Type: building.ObjectTypeTree,
		Entries: []building.TreeEntry{
			{Name: "entry1", Hash: "hash1", Type: building.ObjectTypeBlob},
			{Name: "entry2", Hash: "hash2", Type: building.ObjectTypeTree},
			{Name: "entry3", Hash: "hash3", Type: building.ObjectTypeBlob},
		},
	}

	entryMap := service.buildEntryMap(tree)

	// Verify map was built correctly
	assert.Equal(t, 3, len(entryMap), "Should have 3 entries")
	assert.Equal(t, "hash1", entryMap["entry1"].Hash)
	assert.Equal(t, "hash2", entryMap["entry2"].Hash)
	assert.Equal(t, "hash3", entryMap["entry3"].Hash)
}

func TestDiffService_DiffBuildingMetadata(t *testing.T) {
	ctx := context.Background()

	// Create mock object repository
	mockObjectRepo := new(MockObjectRepository)
	service := &DiffService{
		objectRepo: mockObjectRepo,
	}

	// Create building objects
	fromBuilding := &domain.Building{
		ID:      types.NewID(),
		Name:    "Old Building Name",
		Address: "123 Old Street",
	}

	toBuilding := &domain.Building{
		ID:      fromBuilding.ID,
		Name:    "New Building Name",
		Address: "456 New Avenue",
	}

	fromData, _ := json.Marshal(fromBuilding)
	toData, _ := json.Marshal(toBuilding)

	fromObj := &building.Object{
		Hash:     "from-hash",
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(fromData)),
		Contents: fromData,
	}

	toObj := &building.Object{
		Hash:     "to-hash",
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(toData)),
		Contents: toData,
	}

	// Mock expectations
	mockObjectRepo.On("Load", ctx, "from-hash").Return(fromObj, nil)
	mockObjectRepo.On("Load", ctx, "to-hash").Return(toObj, nil)

	// Execute diff
	changes, err := service.diffBuildingMetadata(ctx, "from-hash", "to-hash")

	// Verify
	assert.NoError(t, err)
	assert.Equal(t, 2, len(changes), "Should have 2 changes (name and address)")

	// Verify name change
	nameChange := changes[0]
	assert.Equal(t, "name", nameChange.Field)
	assert.Equal(t, "Old Building Name", nameChange.OldValue)
	assert.Equal(t, "New Building Name", nameChange.NewValue)

	// Verify address change
	addressChange := changes[1]
	assert.Equal(t, "address", addressChange.Field)
	assert.Equal(t, "123 Old Street", addressChange.OldValue)
	assert.Equal(t, "456 New Avenue", addressChange.NewValue)

	mockObjectRepo.AssertExpectations(t)
}

func TestDiffService_DiffFloorBlobs(t *testing.T) {
	ctx := context.Background()

	// Create mock object repository
	mockObjectRepo := new(MockObjectRepository)
	service := &DiffService{
		objectRepo: mockObjectRepo,
	}

	// Create floor objects
	fromFloor := &domain.Floor{
		ID:    types.NewID(),
		Name:  "Ground Floor",
		Level: 0,
	}

	toFloor := &domain.Floor{
		ID:    fromFloor.ID,
		Name:  "First Floor",
		Level: 1,
	}

	fromData, _ := json.Marshal(fromFloor)
	toData, _ := json.Marshal(toFloor)

	fromObj := &building.Object{
		Hash:     "from-hash",
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(fromData)),
		Contents: fromData,
	}

	toObj := &building.Object{
		Hash:     "to-hash",
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(toData)),
		Contents: toData,
	}

	// Mock expectations
	mockObjectRepo.On("Load", ctx, "from-hash").Return(fromObj, nil)
	mockObjectRepo.On("Load", ctx, "to-hash").Return(toObj, nil)

	// Execute diff
	changes, err := service.diffFloorBlobs(ctx, "from-hash", "to-hash")

	// Verify
	assert.NoError(t, err)
	assert.Equal(t, 2, len(changes), "Should have 2 changes (name and level)")

	mockObjectRepo.AssertExpectations(t)
}

func TestDiffService_DiffEquipmentBlobs(t *testing.T) {
	ctx := context.Background()

	// Create mock object repository
	mockObjectRepo := new(MockObjectRepository)
	service := &DiffService{
		objectRepo: mockObjectRepo,
	}

	// Create equipment objects
	fromEquipment := &domain.Equipment{
		ID:     types.NewID(),
		Name:   "AHU-101",
		Type:   "HVAC",
		Status: "operational",
		Location: &domain.Location{
			X: 10.0,
			Y: 20.0,
			Z: 0.0,
		},
	}

	toEquipment := &domain.Equipment{
		ID:     fromEquipment.ID,
		Name:   "AHU-101",
		Type:   "HVAC",
		Status: "maintenance",
		Location: &domain.Location{
			X: 15.0,
			Y: 25.0,
			Z: 0.0,
		},
	}

	fromData, _ := json.Marshal(fromEquipment)
	toData, _ := json.Marshal(toEquipment)

	fromObj := &building.Object{
		Hash:     "from-hash",
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(fromData)),
		Contents: fromData,
	}

	toObj := &building.Object{
		Hash:     "to-hash",
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(toData)),
		Contents: toData,
	}

	// Mock expectations
	mockObjectRepo.On("Load", ctx, "from-hash").Return(fromObj, nil)
	mockObjectRepo.On("Load", ctx, "to-hash").Return(toObj, nil)

	// Execute diff
	changes, err := service.diffEquipmentBlobs(ctx, "from-hash", "to-hash")

	// Verify
	assert.NoError(t, err)
	assert.Equal(t, 2, len(changes), "Should have 2 changes (status and location)")

	// Verify status change
	var statusChange *building.FieldChange
	for i := range changes {
		if changes[i].Field == "status" {
			statusChange = &changes[i]
			break
		}
	}
	assert.NotNil(t, statusChange, "Should have status change")
	assert.Equal(t, "operational", statusChange.OldValue)
	assert.Equal(t, "maintenance", statusChange.NewValue)

	mockObjectRepo.AssertExpectations(t)
}

func TestDiffService_CalculateSummary(t *testing.T) {
	service := &DiffService{}

	result := &building.DiffResult{
		BuildingDiff: &building.BuildingDiff{
			FloorsAdded:    []building.FloorChange{{}, {}},
			FloorsRemoved:  []building.FloorChange{{}},
			FloorsModified: []building.FloorDiff{{}},
			RoomsAdded:     []building.RoomChange{{}, {}, {}},
		},
		EquipmentDiff: &building.EquipmentDiff{
			Added:    []building.EquipmentChange{{}, {}, {}, {}, {}},
			Removed:  []building.EquipmentChange{{}, {}},
			Modified: []building.EquipmentChange{{}, {}, {}},
			Moved:    []building.EquipmentMove{{}},
		},
		FilesDiff: &building.FilesDiff{
			Added: []building.FileChange{
				{NewSize: 1000},
				{NewSize: 2000},
			},
			Removed: []building.FileChange{
				{OldSize: 500},
			},
			Modified: []building.FileChange{
				{SizeDiff: 100},
			},
		},
	}

	summary := service.calculateSummary(result)

	// Verify building summary
	assert.Equal(t, 2, summary.FloorsAdded)
	assert.Equal(t, 1, summary.FloorsRemoved)
	assert.Equal(t, 1, summary.FloorsModified)
	assert.Equal(t, 3, summary.RoomsAdded)

	// Verify equipment summary
	assert.Equal(t, 5, summary.EquipmentAdded)
	assert.Equal(t, 2, summary.EquipmentRemoved)
	assert.Equal(t, 3, summary.EquipmentModified)
	assert.Equal(t, 1, summary.EquipmentMoved)

	// Verify files summary
	assert.Equal(t, 2, summary.FilesAdded)
	assert.Equal(t, 1, summary.FilesRemoved)
	assert.Equal(t, 1, summary.FilesModified)

	// Verify size change (1000 + 2000 - 500 + 100 = 2600)
	assert.Equal(t, int64(2600), summary.SizeChanged)

	// Verify total changes
	expectedTotal := 2 + 1 + 1 + 3 + 5 + 2 + 3 + 2 + 1 + 1
	assert.Equal(t, expectedTotal, summary.TotalChanges)
}

func TestDiffService_GenerateDetailedChanges(t *testing.T) {
	service := &DiffService{}

	result := &building.DiffResult{
		EquipmentDiff: &building.EquipmentDiff{
			Added: []building.EquipmentChange{
				{
					ID:   "eq-123",
					Name: "AHU-201",
					Type: "HVAC",
				},
			},
			Removed: []building.EquipmentChange{
				{
					ID:   "eq-456",
					Name: "FCU-101",
					Type: "HVAC",
				},
			},
		},
		BuildingDiff: &building.BuildingDiff{
			FloorsAdded: []building.FloorChange{
				{
					ID:    "floor-789",
					Name:  "Basement",
					Level: -1,
				},
			},
		},
	}

	changes := service.generateDetailedChanges(result)

	// Verify changes were generated
	assert.Equal(t, 3, len(changes), "Should have 3 detailed changes")

	// Verify equipment added change
	addedChange := changes[0]
	assert.Equal(t, building.ChangeTypeAdded, addedChange.Type)
	assert.Equal(t, "equipment", addedChange.Category)
	assert.Equal(t, "AHU-201", addedChange.EntityName)

	// Verify equipment removed change
	removedChange := changes[1]
	assert.Equal(t, building.ChangeTypeDeleted, removedChange.Type)
	assert.Equal(t, "equipment", removedChange.Category)
	assert.Equal(t, "FCU-101", removedChange.EntityName)

	// Verify floor added change
	floorChange := changes[2]
	assert.Equal(t, building.ChangeTypeAdded, floorChange.Type)
	assert.Equal(t, "building", floorChange.Category)
	assert.Equal(t, "floor", floorChange.EntityType)
	assert.Equal(t, "Basement", floorChange.EntityName)
}

func TestDiffService_Distance3D(t *testing.T) {
	tests := []struct {
		name     string
		from     *building.Point3D
		to       *building.Point3D
		expected float64
	}{
		{
			name:     "same point",
			from:     &building.Point3D{X: 0, Y: 0, Z: 0},
			to:       &building.Point3D{X: 0, Y: 0, Z: 0},
			expected: 0,
		},
		{
			name:     "horizontal movement",
			from:     &building.Point3D{X: 0, Y: 0, Z: 0},
			to:       &building.Point3D{X: 3, Y: 4, Z: 0},
			expected: 5, // 3-4-5 triangle
		},
		{
			name:     "3D movement",
			from:     &building.Point3D{X: 0, Y: 0, Z: 0},
			to:       &building.Point3D{X: 1, Y: 1, Z: 1},
			expected: 1.732, // sqrt(3) ≈ 1.732
		},
		{
			name:     "nil from point",
			from:     nil,
			to:       &building.Point3D{X: 10, Y: 10, Z: 10},
			expected: 0,
		},
		{
			name:     "nil to point",
			from:     &building.Point3D{X: 10, Y: 10, Z: 10},
			to:       nil,
			expected: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			distance := Distance3D(tt.from, tt.to)

			// Use approximate equality for floating point
			if tt.expected == 0 {
				assert.Equal(t, tt.expected, distance)
			} else {
				assert.InDelta(t, tt.expected, distance, 0.01)
			}
		})
	}
}

func TestDiffFormatting(t *testing.T) {
	diff := &building.DiffResult{
		FromVersion:  "v1.0.0",
		ToVersion:    "v1.1.0",
		FromSnapshot: "snapshot-abc",
		ToSnapshot:   "snapshot-def",
		Summary: building.DiffSummary{
			TotalChanges:      10,
			EquipmentAdded:    3,
			EquipmentRemoved:  1,
			EquipmentModified: 2,
			FloorsAdded:       1,
		},
		EquipmentDiff: &building.EquipmentDiff{
			Added: []building.EquipmentChange{
				{Name: "AHU-301", Type: "HVAC", Location: "Roof"},
			},
		},
		CreatedAt: time.Now(),
	}

	tests := []struct {
		name   string
		format building.DiffOutputFormat
	}{
		{"unified format", building.DiffFormatUnified},
		{"JSON format", building.DiffFormatJSON},
		{"semantic format", building.DiffFormatSemantic},
		{"summary format", building.DiffFormatSummary},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			output, err := building.FormatDiff(diff, tt.format)

			assert.NoError(t, err)
			assert.NotEmpty(t, output, "Formatted output should not be empty")

			// Verify key elements appear in output
			if tt.format != building.DiffFormatJSON {
				assert.Contains(t, output, "v1.0.0")
				assert.Contains(t, output, "v1.1.0")
			}
		})
	}
}

func TestDiffFormatting_UnifiedDiff(t *testing.T) {
	diff := &building.DiffResult{
		FromVersion:  "v1.0.0",
		ToVersion:    "v1.1.0",
		FromSnapshot: "snapshot-abc",
		ToSnapshot:   "snapshot-def",
		Summary: building.DiffSummary{
			TotalChanges: 2,
		},
		EquipmentDiff: &building.EquipmentDiff{
			Added: []building.EquipmentChange{
				{Name: "AHU-201", Type: "HVAC"},
			},
			Removed: []building.EquipmentChange{
				{Name: "FCU-101", Type: "HVAC"},
			},
		},
	}

	output := building.FormatUnifiedDiff(diff)

	// Verify Git-style format elements
	assert.Contains(t, output, "diff --arx")
	assert.Contains(t, output, "---")
	assert.Contains(t, output, "+++")
	assert.Contains(t, output, "+ Added equipment: AHU-201")
	assert.Contains(t, output, "- Removed equipment: FCU-101")
}

func TestDiffFormatting_SemanticDiff(t *testing.T) {
	diff := &building.DiffResult{
		FromVersion: "v1.0.0",
		ToVersion:   "v1.1.0",
		Summary: building.DiffSummary{
			TotalChanges: 1,
		},
		EquipmentDiff: &building.EquipmentDiff{
			Added: []building.EquipmentChange{
				{Name: "AHU-201", Type: "HVAC", Location: "Roof"},
			},
		},
	}

	output := building.FormatSemanticDiff(diff)

	// Verify human-readable format
	assert.Contains(t, output, "Building Changes")
	assert.Contains(t, output, "Equipment Added")
	assert.Contains(t, output, "AHU-201")
	assert.Contains(t, output, "HVAC")
	assert.Contains(t, output, "Roof")
}

func TestDiffFormatting_SummaryDiff(t *testing.T) {
	diff := &building.DiffResult{
		FromVersion: "v1.0.0",
		ToVersion:   "v1.1.0",
		Summary: building.DiffSummary{
			TotalChanges:      15,
			FloorsAdded:       2,
			FloorsRemoved:     1,
			FloorsModified:    1,
			EquipmentAdded:    5,
			EquipmentRemoved:  3,
			EquipmentModified: 2,
			FilesAdded:        1,
			SizeChanged:       1048576, // 1 MB
		},
	}

	output := building.FormatSummaryDiff(diff)

	// Verify summary format
	assert.Contains(t, output, "Version Comparison")
	assert.Contains(t, output, "Total Changes: 15")
	assert.Contains(t, output, "Floors: +2 -1 ~1")
	assert.Contains(t, output, "Added: 5")
	assert.Contains(t, output, "Net Size Change")
}
