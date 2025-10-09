package usecase

import (
	"context"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/google/uuid"
	"github.com/stretchr/testify/mock"
)

// MockFloorRepository is a mock implementation of domain.FloorRepository
type MockFloorRepository struct {
	mock.Mock
}

func (m *MockFloorRepository) Create(ctx context.Context, floor *domain.Floor) error {
	args := m.Called(ctx, floor)
	return args.Error(0)
}

func (m *MockFloorRepository) GetByID(ctx context.Context, id string) (*domain.Floor, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Floor), args.Error(1)
}

func (m *MockFloorRepository) GetByBuilding(ctx context.Context, buildingID string) ([]*domain.Floor, error) {
	args := m.Called(ctx, buildingID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Floor), args.Error(1)
}

func (m *MockFloorRepository) Update(ctx context.Context, floor *domain.Floor) error {
	args := m.Called(ctx, floor)
	return args.Error(0)
}

func (m *MockFloorRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockFloorRepository) List(ctx context.Context, buildingID string, limit, offset int) ([]*domain.Floor, error) {
	args := m.Called(ctx, buildingID, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Floor), args.Error(1)
}

func (m *MockFloorRepository) GetRooms(ctx context.Context, floorID string) ([]*domain.Room, error) {
	args := m.Called(ctx, floorID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Room), args.Error(1)
}

func (m *MockFloorRepository) GetEquipment(ctx context.Context, floorID string) ([]*domain.Equipment, error) {
	args := m.Called(ctx, floorID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*domain.Equipment), args.Error(1)
}

// Mock repositories for snapshot service tests
type MockObjectRepository struct {
	mock.Mock
}

func (m *MockObjectRepository) Store(ctx any, obj *building.Object) (string, error) {
	args := m.Called(ctx, obj)
	return args.String(0), args.Error(1)
}

func (m *MockObjectRepository) Load(ctx any, hash string) (*building.Object, error) {
	args := m.Called(ctx, hash)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.Object), args.Error(1)
}

func (m *MockObjectRepository) Exists(ctx any, hash string) (bool, error) {
	args := m.Called(ctx, hash)
	return args.Bool(0), args.Error(1)
}

func (m *MockObjectRepository) IncrementRef(ctx any, hash string) error {
	args := m.Called(ctx, hash)
	return args.Error(0)
}

func (m *MockObjectRepository) DecrementRef(ctx any, hash string) error {
	args := m.Called(ctx, hash)
	return args.Error(0)
}

func (m *MockObjectRepository) ListByType(ctx any, objType building.ObjectType, limit, offset int) ([]*building.Object, error) {
	args := m.Called(ctx, objType, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*building.Object), args.Error(1)
}

func (m *MockObjectRepository) DeleteUnreferenced(ctx any, olderThan time.Time) (int, error) {
	args := m.Called(ctx, olderThan)
	return args.Int(0), args.Error(1)
}

type MockSnapshotRepository struct {
	mock.Mock
}

func (m *MockSnapshotRepository) Create(ctx any, snapshot *building.Snapshot) error {
	args := m.Called(ctx, snapshot)
	return args.Error(0)
}

func (m *MockSnapshotRepository) GetByHash(ctx any, hash string) (*building.Snapshot, error) {
	args := m.Called(ctx, hash)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.Snapshot), args.Error(1)
}

func (m *MockSnapshotRepository) ListByRepository(ctx any, repoID string) ([]*building.Snapshot, error) {
	args := m.Called(ctx, repoID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*building.Snapshot), args.Error(1)
}

func (m *MockSnapshotRepository) GetLatest(ctx any, repoID string) (*building.Snapshot, error) {
	args := m.Called(ctx, repoID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.Snapshot), args.Error(1)
}

func (m *MockSnapshotRepository) Delete(ctx any, hash string) error {
	args := m.Called(ctx, hash)
	return args.Error(0)
}

type MockTreeRepository struct {
	mock.Mock
}

func (m *MockTreeRepository) Store(ctx any, tree *building.Tree) (string, error) {
	args := m.Called(ctx, tree)
	return args.String(0), args.Error(1)
}

func (m *MockTreeRepository) Load(ctx any, hash string) (*building.Tree, error) {
	args := m.Called(ctx, hash)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*building.Tree), args.Error(1)
}

func (m *MockTreeRepository) Exists(ctx any, hash string) (bool, error) {
	args := m.Called(ctx, hash)
	return args.Bool(0), args.Error(1)
}

func TestSnapshotService_CaptureSnapshot(t *testing.T) {
	ctx := context.Background()
	buildingID := uuid.New().String()

	// Create mock repositories
	mockBuildingRepo := new(MockBuildingRepository)
	mockEquipmentRepo := new(MockEquipmentRepository)
	mockFloorRepo := new(MockFloorRepository)
	mockObjectRepo := new(MockObjectRepository)
	mockSnapshotRepo := new(MockSnapshotRepository)
	mockTreeRepo := new(MockTreeRepository)
	mockLogger := createPermissiveMockLogger()

	// Create service
	service := NewSnapshotService(
		mockBuildingRepo,
		mockEquipmentRepo,
		mockFloorRepo,
		mockObjectRepo,
		mockSnapshotRepo,
		mockTreeRepo,
		mockLogger,
	)

	// Set up test data
	building := &domain.Building{
		ID:        types.FromString(buildingID),
		Name:      "Test Building",
		Address:   "123 Test St",
		CreatedAt: time.Now(),
	}

	floors := []*domain.Floor{
		{
			ID:         types.NewID(),
			BuildingID: types.FromString(buildingID),
			Level:      1,
			Name:       "Floor 1",
		},
	}

	equipment := []*domain.Equipment{
		{
			ID:         types.NewID(),
			BuildingID: types.FromString(buildingID),
			Name:       "AHU-1",
			Type:       "HVAC",
		},
	}

	// Mock expectations
	mockBuildingRepo.On("GetByID", ctx, buildingID).Return(building, nil)
	mockFloorRepo.On("GetByBuilding", ctx, buildingID).Return(floors, nil)
	mockEquipmentRepo.On("GetByBuilding", ctx, buildingID).Return(equipment, nil)

	// Mock object/tree storage (return predictable hashes)
	mockObjectRepo.On("Store", ctx, mock.Anything).Return("object-hash", nil)
	mockTreeRepo.On("Store", ctx, mock.Anything).Return("tree-hash", nil)
	mockSnapshotRepo.On("Create", ctx, mock.Anything).Return(nil)

	// Execute
	snapshot, err := service.CaptureSnapshot(ctx, buildingID)

	// Verify
	if err != nil {
		t.Fatalf("CaptureSnapshot() error = %v", err)
	}

	if snapshot == nil {
		t.Fatal("CaptureSnapshot() returned nil snapshot")
	}

	if snapshot.RepositoryID != buildingID {
		t.Errorf("RepositoryID = %v, want %v", snapshot.RepositoryID, buildingID)
	}

	if snapshot.Hash == "" {
		t.Error("Snapshot hash is empty")
	}

	if snapshot.BuildingTree == "" {
		t.Error("Building tree hash is empty")
	}

	if snapshot.EquipmentTree == "" {
		t.Error("Equipment tree hash is empty")
	}

	// Verify mock calls
	mockBuildingRepo.AssertExpectations(t)
	mockFloorRepo.AssertExpectations(t)
	mockEquipmentRepo.AssertExpectations(t)
	mockObjectRepo.AssertExpectations(t)
	mockTreeRepo.AssertExpectations(t)
	mockSnapshotRepo.AssertExpectations(t)
}

func TestSnapshotService_CaptureSnapshot_EmptyBuilding(t *testing.T) {
	ctx := context.Background()
	buildingID := uuid.New().String()

	// Create mock repositories
	mockBuildingRepo := new(MockBuildingRepository)
	mockEquipmentRepo := new(MockEquipmentRepository)
	mockFloorRepo := new(MockFloorRepository)
	mockObjectRepo := new(MockObjectRepository)
	mockSnapshotRepo := new(MockSnapshotRepository)
	mockTreeRepo := new(MockTreeRepository)
	mockLogger := createPermissiveMockLogger()

	// Create service
	service := NewSnapshotService(
		mockBuildingRepo,
		mockEquipmentRepo,
		mockFloorRepo,
		mockObjectRepo,
		mockSnapshotRepo,
		mockTreeRepo,
		mockLogger,
	)

	// Set up test data (empty building)
	building := &domain.Building{
		ID:        types.FromString(buildingID),
		Name:      "Empty Building",
		Address:   "456 Empty St",
		CreatedAt: time.Now(),
	}

	// Mock expectations (no floors, no equipment)
	mockBuildingRepo.On("GetByID", ctx, buildingID).Return(building, nil)
	mockFloorRepo.On("GetByBuilding", ctx, buildingID).Return([]*domain.Floor{}, nil)
	mockEquipmentRepo.On("GetByBuilding", ctx, buildingID).Return([]*domain.Equipment{}, nil)

	// Mock object/tree storage
	mockObjectRepo.On("Store", ctx, mock.Anything).Return("object-hash", nil)
	mockTreeRepo.On("Store", ctx, mock.Anything).Return("tree-hash", nil)
	mockSnapshotRepo.On("Create", ctx, mock.Anything).Return(nil)

	// Execute
	snapshot, err := service.CaptureSnapshot(ctx, buildingID)

	// Verify
	if err != nil {
		t.Fatalf("CaptureSnapshot() error = %v", err)
	}

	if snapshot == nil {
		t.Fatal("CaptureSnapshot() returned nil snapshot")
	}

	// Empty building should still have valid tree hashes (empty trees)
	if snapshot.BuildingTree == "" {
		t.Error("Building tree hash is empty")
	}

	if snapshot.EquipmentTree == "" {
		t.Error("Equipment tree hash is empty")
	}

	// Verify mock calls
	mockBuildingRepo.AssertExpectations(t)
	mockFloorRepo.AssertExpectations(t)
	mockEquipmentRepo.AssertExpectations(t)
}

func TestSnapshotService_LoadSnapshot(t *testing.T) {
	ctx := context.Background()
	hash := "snapshot-hash-123"

	// Create mock repositories
	mockSnapshotRepo := new(MockSnapshotRepository)

	// Create service with minimal dependencies
	service := &SnapshotService{
		snapshotRepo: mockSnapshotRepo,
	}

	// Set up expected snapshot
	expectedSnapshot := &building.Snapshot{
		Hash:         hash,
		RepositoryID: "repo-123",
	}

	// Mock expectations
	mockSnapshotRepo.On("GetByHash", ctx, hash).Return(expectedSnapshot, nil)

	// Execute
	snapshot, err := service.LoadSnapshot(ctx, hash)

	// Verify
	if err != nil {
		t.Fatalf("LoadSnapshot() error = %v", err)
	}

	if snapshot == nil {
		t.Fatal("LoadSnapshot() returned nil snapshot")
	}

	if snapshot.Hash != hash {
		t.Errorf("Hash = %v, want %v", snapshot.Hash, hash)
	}

	// Verify mock calls
	mockSnapshotRepo.AssertExpectations(t)
}

func TestSnapshotService_ListSnapshots(t *testing.T) {
	ctx := context.Background()
	repoID := "repo-123"

	// Create mock repositories
	mockSnapshotRepo := new(MockSnapshotRepository)

	// Create service with minimal dependencies
	service := &SnapshotService{
		snapshotRepo: mockSnapshotRepo,
	}

	// Set up expected snapshots
	expectedSnapshots := []*building.Snapshot{
		{
			Hash:         "snapshot-1",
			RepositoryID: repoID,
		},
		{
			Hash:         "snapshot-2",
			RepositoryID: repoID,
		},
	}

	// Mock expectations
	mockSnapshotRepo.On("ListByRepository", ctx, repoID).Return(expectedSnapshots, nil)

	// Execute
	snapshots, err := service.ListSnapshots(ctx, repoID)

	// Verify
	if err != nil {
		t.Fatalf("ListSnapshots() error = %v", err)
	}

	if len(snapshots) != 2 {
		t.Errorf("Got %d snapshots, want 2", len(snapshots))
	}

	// Verify mock calls
	mockSnapshotRepo.AssertExpectations(t)
}

func TestSnapshotService_GetLatestSnapshot(t *testing.T) {
	ctx := context.Background()
	repoID := "repo-123"

	// Create mock repositories
	mockSnapshotRepo := new(MockSnapshotRepository)

	// Create service with minimal dependencies
	service := &SnapshotService{
		snapshotRepo: mockSnapshotRepo,
	}

	// Set up expected snapshot
	expectedSnapshot := &building.Snapshot{
		Hash:         "latest-snapshot",
		RepositoryID: repoID,
		CreatedAt:    time.Now(),
	}

	// Mock expectations
	mockSnapshotRepo.On("GetLatest", ctx, repoID).Return(expectedSnapshot, nil)

	// Execute
	snapshot, err := service.GetLatestSnapshot(ctx, repoID)

	// Verify
	if err != nil {
		t.Fatalf("GetLatestSnapshot() error = %v", err)
	}

	if snapshot == nil {
		t.Fatal("GetLatestSnapshot() returned nil snapshot")
	}

	if snapshot.Hash != "latest-snapshot" {
		t.Errorf("Hash = %v, want latest-snapshot", snapshot.Hash)
	}

	// Verify mock calls
	mockSnapshotRepo.AssertExpectations(t)
}
