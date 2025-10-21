package versioncontrol

import (
	"context"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// Mock service implementations for CLI testing
type MockSnapshotService struct {
	mock.Mock
}

func (m *MockSnapshotService) CaptureSnapshot(ctx context.Context, repoID string) (*building.Snapshot, error) {
	args := m.Called(ctx, repoID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.Snapshot), args.Error(1)
}

func (m *MockSnapshotService) ListSnapshots(ctx context.Context, repoID string) ([]*building.Snapshot, error) {
	args := m.Called(ctx, repoID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*building.Snapshot), args.Error(1)
}

func (m *MockSnapshotService) GetLatestSnapshot(ctx context.Context, repoID string) (*building.Snapshot, error) {
	args := m.Called(ctx, repoID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.Snapshot), args.Error(1)
}

type MockDiffService struct {
	mock.Mock
}

func (m *MockDiffService) DiffVersions(ctx context.Context, fromVersion, toVersion *building.Version) (*building.DiffResult, error) {
	args := m.Called(ctx, fromVersion, toVersion)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.DiffResult), args.Error(1)
}

type MockRollbackService struct {
	mock.Mock
}

func (m *MockRollbackService) Rollback(ctx context.Context, buildingID string, targetVersion *building.Version, opts *RollbackOptions) (*RollbackResult, error) {
	args := m.Called(ctx, buildingID, targetVersion, opts)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*RollbackResult), args.Error(1)
}

type MockVersionService struct {
	mock.Mock
}

func (m *MockVersionService) CreateVersion(ctx context.Context, repoID string, message string) (*building.Version, error) {
	args := m.Called(ctx, repoID, message)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.Version), args.Error(1)
}

func (m *MockVersionService) GetVersion(ctx context.Context, repoID string, versionTag string) (*building.Version, error) {
	args := m.Called(ctx, repoID, versionTag)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.Version), args.Error(1)
}

func (m *MockVersionService) ListVersions(ctx context.Context, repoID string) ([]building.Version, error) {
	args := m.Called(ctx, repoID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]building.Version), args.Error(1)
}

type MockVersionServiceProvider struct {
	snapshotService SnapshotService
	diffService     DiffService
	rollbackService RollbackService
	versionService  VersionService
	buildingID      string
}

func (m *MockVersionServiceProvider) GetSnapshotService() SnapshotService {
	return m.snapshotService
}

func (m *MockVersionServiceProvider) GetDiffService() DiffService {
	return m.diffService
}

func (m *MockVersionServiceProvider) GetRollbackService() RollbackService {
	return m.rollbackService
}

func (m *MockVersionServiceProvider) GetVersionService() VersionService {
	return m.versionService
}

func (m *MockVersionServiceProvider) GetBuildingID() string {
	return m.buildingID
}

func TestRepoCommitCommand(t *testing.T) {
	// Create mocks
	mockSnapshot := new(MockSnapshotService)
	mockVersion := new(MockVersionService)

	buildingID := "building-123"

	provider := &MockVersionServiceProvider{
		snapshotService: mockSnapshot,
		versionService:  mockVersion,
		buildingID:      buildingID,
	}

	// Test data
	snapshot := &building.Snapshot{
		Hash: "snapshot-abc123",
		Metadata: building.SnapshotMetadata{
			SpaceCount: 3,
			ItemCount:  50,
		},
	}

	version := &building.Version{
		ID:  "version-123",
		Tag: "v1.0.0",
		Author: building.Author{
			Name:  "test-user",
			Email: "test@example.com",
		},
		Hash:      "version-hash-123",
		Timestamp: time.Now(),
		Message:   "Test commit",
	}

	// Mock expectations
	mockSnapshot.On("CaptureSnapshot", mock.Anything, buildingID).Return(snapshot, nil)
	mockVersion.On("CreateVersion", mock.Anything, buildingID, "Test commit").Return(version, nil)

	// Create command
	cmd := createRepoCommitCommand2(provider)
	cmd.SetArgs([]string{"-m", "Test commit"})

	// Execute
	err := cmd.Execute()

	// Verify - command should execute successfully
	assert.NoError(t, err)

	// Verify mock expectations (services were called correctly)
	mockSnapshot.AssertExpectations(t)
	mockVersion.AssertExpectations(t)
}

func TestRepoStatusCommand(t *testing.T) {
	// Create mocks
	mockSnapshot := new(MockSnapshotService)
	mockVersion := new(MockVersionService)

	buildingID := "building-123"

	provider := &MockVersionServiceProvider{
		snapshotService: mockSnapshot,
		versionService:  mockVersion,
		buildingID:      buildingID,
	}

	// Test data
	versions := []building.Version{
		{
			Tag:       "v1.0.0",
			Hash:      "hash-1",
			Message:   "Initial version",
			Timestamp: time.Now().Add(-2 * time.Hour),
		},
		{
			Tag:       "v1.1.0",
			Hash:      "hash-2",
			Message:   "Added equipment",
			Timestamp: time.Now().Add(-1 * time.Hour),
		},
	}

	snapshot := &building.Snapshot{
		Metadata: building.SnapshotMetadata{
			SpaceCount: 30,
			ItemCount:  100,
			FileCount:  10,
			TotalSize:  10485760, // 10 MB
		},
	}

	// Mock expectations
	mockVersion.On("ListVersions", mock.Anything, buildingID).Return(versions, nil)
	mockSnapshot.On("GetLatestSnapshot", mock.Anything, buildingID).Return(snapshot, nil)

	// Create command
	cmd := createRepoStatusCommand2(provider)

	// Execute
	err := cmd.Execute()

	// Verify - command should execute successfully
	assert.NoError(t, err)

	// Verify mock expectations (services were called correctly)
	mockVersion.AssertExpectations(t)
	mockSnapshot.AssertExpectations(t)
}

func TestRepoLogCommand(t *testing.T) {
	// Create mocks
	mockVersion := new(MockVersionService)

	buildingID := "building-123"

	provider := &MockVersionServiceProvider{
		versionService: mockVersion,
		buildingID:     buildingID,
	}

	// Test data
	versions := []building.Version{
		{
			Tag:       "v1.0.0",
			Hash:      "hash-1",
			Message:   "Initial version",
			Parent:    "",
			Timestamp: time.Now().Add(-2 * time.Hour),
			Author: building.Author{
				Name:  "test-user",
				Email: "test@example.com",
			},
			Metadata: building.VersionMetadata{
				Source: "manual",
			},
		},
		{
			Tag:       "v1.1.0",
			Hash:      "hash-2",
			Message:   "Added equipment",
			Parent:    "hash-1",
			Timestamp: time.Now().Add(-1 * time.Hour),
			Author: building.Author{
				Name:  "test-user",
				Email: "test@example.com",
			},
			Metadata: building.VersionMetadata{
				Source:      "manual",
				ChangeCount: 10,
			},
		},
	}

	// Mock expectations
	mockVersion.On("ListVersions", mock.Anything, buildingID).Return(versions, nil)

	// Create command
	cmd := createRepoLogCommand(provider)

	// Execute
	err := cmd.Execute()

	// Verify - command should execute successfully
	assert.NoError(t, err)

	// Verify mock expectations (services were called correctly)
	mockVersion.AssertExpectations(t)
}

func TestRepoLogCommand_Oneline(t *testing.T) {
	// Create mocks
	mockVersion := new(MockVersionService)

	buildingID := "building-123"

	provider := &MockVersionServiceProvider{
		versionService: mockVersion,
		buildingID:     buildingID,
	}

	// Test data
	versions := []building.Version{
		{
			Tag:       "v1.0.0",
			Hash:      "hash-123",
			Message:   "Initial version",
			Timestamp: time.Now(),
		},
	}

	// Mock expectations
	mockVersion.On("ListVersions", mock.Anything, buildingID).Return(versions, nil)

	// Create command with --oneline flag
	cmd := createRepoLogCommand(provider)
	cmd.SetArgs([]string{"--oneline"})

	// Execute
	err := cmd.Execute()

	// Verify - command should execute successfully
	assert.NoError(t, err)

	// Verify mock expectations (services were called correctly)
	mockVersion.AssertExpectations(t)
}

func TestRepoDiffCommand(t *testing.T) {
	// Create mocks
	mockDiff := new(MockDiffService)
	mockVersion := new(MockVersionService)

	buildingID := "building-123"

	provider := &MockVersionServiceProvider{
		diffService:    mockDiff,
		versionService: mockVersion,
		buildingID:     buildingID,
	}

	// Test data
	v1 := &building.Version{
		Tag:      "v1.0.0",
		Hash:     "hash-1",
		Snapshot: "snapshot-1",
	}

	v2 := &building.Version{
		Tag:      "v1.1.0",
		Hash:     "hash-2",
		Snapshot: "snapshot-2",
	}

	diffResult := &building.DiffResult{
		FromVersion: "v1.0.0",
		ToVersion:   "v1.1.0",
		Summary: building.DiffSummary{
			TotalChanges:   5,
			EquipmentAdded: 3,
			FloorsAdded:    2,
		},
		EquipmentDiff: &building.EquipmentDiff{
			Added: []building.EquipmentChange{
				{Name: "AHU-201", Type: "HVAC"},
			},
		},
		CreatedAt: time.Now(),
	}

	// Mock expectations
	mockVersion.On("GetVersion", mock.Anything, buildingID, "v1.0.0").Return(v1, nil)
	mockVersion.On("GetVersion", mock.Anything, buildingID, "v1.1.0").Return(v2, nil)
	mockDiff.On("DiffVersions", mock.Anything, v1, v2).Return(diffResult, nil)

	// Create command
	cmd := createRepoDiffCommand(provider)
	cmd.SetArgs([]string{"v1.0.0", "v1.1.0"})

	// Execute
	err := cmd.Execute()

	// Verify - command should execute successfully
	assert.NoError(t, err)

	// Verify mock expectations (services were called correctly)
	mockVersion.AssertExpectations(t)
	mockDiff.AssertExpectations(t)
}

func TestRepoCheckoutCommand_DryRun(t *testing.T) {
	// Create mocks
	mockRollback := new(MockRollbackService)
	mockVersion := new(MockVersionService)

	buildingID := "building-123"

	provider := &MockVersionServiceProvider{
		rollbackService: mockRollback,
		versionService:  mockVersion,
		buildingID:      buildingID,
	}

	// Test data
	targetVersion := &building.Version{
		Tag:      "v1.0.0",
		Hash:     "hash-1",
		Snapshot: "snapshot-1",
	}

	rollbackResult := &RollbackResult{
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

	// Mock expectations
	mockVersion.On("GetVersion", mock.Anything, buildingID, "v1.0.0").Return(targetVersion, nil)
	mockRollback.On("Rollback", mock.Anything, buildingID, targetVersion, mock.MatchedBy(func(opts *RollbackOptions) bool {
		return opts.DryRun == true
	})).Return(rollbackResult, nil)

	// Create command with --dry-run
	cmd := createRepoCheckoutCommand(provider)
	cmd.SetArgs([]string{"v1.0.0", "--dry-run"})

	// Execute
	err := cmd.Execute()

	// Verify - command should execute successfully
	assert.NoError(t, err)

	// Verify mock expectations (services were called correctly)
	mockVersion.AssertExpectations(t)
	mockRollback.AssertExpectations(t)
}

func TestRepoCheckoutCommand_Force(t *testing.T) {
	// Create mocks
	mockRollback := new(MockRollbackService)
	mockVersion := new(MockVersionService)

	buildingID := "building-123"

	provider := &MockVersionServiceProvider{
		rollbackService: mockRollback,
		versionService:  mockVersion,
		buildingID:      buildingID,
	}

	// Test data
	targetVersion := &building.Version{
		Tag:      "v1.0.0",
		Hash:     "hash-1",
		Snapshot: "snapshot-1",
	}

	rollbackResult := &RollbackResult{
		Success:         true,
		TargetVersion:   "v1.0.0",
		PreviousVersion: "v1.1.0",
		Changes: &RollbackChanges{
			BuildingRestored:  true,
			FloorsRestored:    3,
			EquipmentRestored: 50,
		},
		ValidationResult: &ValidationResult{
			Valid: true,
			Checks: []string{
				"Building exists",
				"Floors restored correctly (3)",
			},
		},
		Duration: 2 * time.Second,
	}

	// Mock expectations
	mockVersion.On("GetVersion", mock.Anything, buildingID, "v1.0.0").Return(targetVersion, nil)
	mockRollback.On("Rollback", mock.Anything, buildingID, targetVersion, mock.MatchedBy(func(opts *RollbackOptions) bool {
		return opts.DryRun == false && opts.CreateVersion == true && opts.ValidateAfter == true
	})).Return(rollbackResult, nil)

	// Create command with --force
	cmd := createRepoCheckoutCommand(provider)
	cmd.SetArgs([]string{"v1.0.0", "--force"})

	// Execute
	err := cmd.Execute()

	// Verify - command should execute successfully
	assert.NoError(t, err)

	// Verify mock expectations (services were called correctly)
	mockVersion.AssertExpectations(t)
	mockRollback.AssertExpectations(t)
}

func TestFormatBool(t *testing.T) {
	tests := []struct {
		name     string
		input    bool
		contains string
	}{
		{"true value", true, "restored"},
		{"false value", false, "unchanged"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := formatBool(tt.input)
			assert.Contains(t, result, tt.contains)
		})
	}
}
