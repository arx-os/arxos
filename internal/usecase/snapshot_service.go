package usecase

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
)

// SnapshotService handles capturing building state into snapshots
type SnapshotService struct {
	buildingRepo  domain.BuildingRepository
	equipmentRepo domain.EquipmentRepository
	floorRepo     domain.FloorRepository
	objectRepo    building.ObjectRepository
	snapshotRepo  building.SnapshotRepository
	treeRepo      building.TreeRepository
	logger        domain.Logger
}

// NewSnapshotService creates a new snapshot service
func NewSnapshotService(
	buildingRepo domain.BuildingRepository,
	equipmentRepo domain.EquipmentRepository,
	floorRepo domain.FloorRepository,
	objectRepo building.ObjectRepository,
	snapshotRepo building.SnapshotRepository,
	treeRepo building.TreeRepository,
	logger domain.Logger,
) *SnapshotService {
	return &SnapshotService{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		floorRepo:     floorRepo,
		objectRepo:    objectRepo,
		snapshotRepo:  snapshotRepo,
		treeRepo:      treeRepo,
		logger:        logger,
	}
}

// CaptureSnapshot captures the current state of a building repository
func (s *SnapshotService) CaptureSnapshot(ctx context.Context, repoID string) (*building.Snapshot, error) {
	s.logger.Info("Capturing snapshot for repository", "repo_id", repoID)

	// Create snapshot
	snapshot := &building.Snapshot{
		RepositoryID: repoID,
		CreatedAt:    time.Now(),
		Metadata:     building.SnapshotMetadata{},
	}

	// Capture building tree
	buildingTree, err := s.captureBuildingTree(ctx, repoID)
	if err != nil {
		return nil, fmt.Errorf("failed to capture building tree: %w", err)
	}
	snapshot.BuildingTree = buildingTree

	// Capture equipment tree
	equipmentTree, err := s.captureEquipmentTree(ctx, repoID)
	if err != nil {
		return nil, fmt.Errorf("failed to capture equipment tree: %w", err)
	}
	snapshot.EquipmentTree = equipmentTree

	// Capture spatial tree
	spatialTree, err := s.captureSpatialTree(ctx, repoID)
	if err != nil {
		return nil, fmt.Errorf("failed to capture spatial tree: %w", err)
	}
	snapshot.SpatialTree = spatialTree

	// Capture files tree (placeholder for now)
	filesTree, err := s.captureFilesTree(ctx, repoID)
	if err != nil {
		return nil, fmt.Errorf("failed to capture files tree: %w", err)
	}
	snapshot.FilesTree = filesTree

	// Capture operations tree (placeholder for now)
	operationsTree, err := s.captureOperationsTree(ctx, repoID)
	if err != nil {
		return nil, fmt.Errorf("failed to capture operations tree: %w", err)
	}
	snapshot.OperationsTree = operationsTree

	// Calculate snapshot hash
	snapshot.Hash = building.CalculateSnapshotHash(snapshot)

	// Store snapshot
	if err := s.snapshotRepo.Create(ctx, snapshot); err != nil {
		return nil, fmt.Errorf("failed to store snapshot: %w", err)
	}

	s.logger.Info("Snapshot captured successfully", "repo_id", repoID, "hash", snapshot.Hash)
	return snapshot, nil
}

// captureBuildingTree captures the building structure as a Merkle tree
func (s *SnapshotService) captureBuildingTree(ctx context.Context, buildingID string) (string, error) {
	// Get building
	bldg, err := s.buildingRepo.GetByID(ctx, buildingID)
	if err != nil {
		return "", fmt.Errorf("failed to get building: %w", err)
	}

	// Get floors
	floors, err := s.floorRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return "", fmt.Errorf("failed to get floors: %w", err)
	}

	// Update metadata
	// (metadata is a package-level variable, need to update this later)

	// Create tree entries
	tree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: []building.TreeEntry{},
	}

	// Add building metadata entry
	buildingBlob, err := s.createBuildingBlob(ctx, bldg)
	if err != nil {
		return "", fmt.Errorf("failed to create building blob: %w", err)
	}
	tree.Entries = append(tree.Entries, building.TreeEntry{
		Type: building.ObjectTypeBlob,
		Name: "building",
		Hash: buildingBlob,
		Size: 0, // Size will be calculated by object store
	})

	// Add floors subtree
	if len(floors) > 0 {
		floorsTree, err := s.createFloorsTree(ctx, floors)
		if err != nil {
			return "", fmt.Errorf("failed to create floors tree: %w", err)
		}
		tree.Entries = append(tree.Entries, building.TreeEntry{
			Type: building.ObjectTypeTree,
			Name: "floors",
			Hash: floorsTree,
			Size: int64(len(floors)),
		})
	}

	// Store tree
	treeHash, err := s.treeRepo.Store(ctx, tree)
	if err != nil {
		return "", fmt.Errorf("failed to store building tree: %w", err)
	}

	return treeHash, nil
}

// createBuildingBlob creates a blob object for building metadata
func (s *SnapshotService) createBuildingBlob(ctx context.Context, bldg *domain.Building) (string, error) {
	// Serialize building to JSON
	data, err := json.Marshal(bldg)
	if err != nil {
		return "", fmt.Errorf("failed to marshal building: %w", err)
	}

	// Create object
	obj := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(data)),
		Contents: data,
	}

	// Store object
	hash, err := s.objectRepo.Store(ctx, obj)
	if err != nil {
		return "", fmt.Errorf("failed to store building object: %w", err)
	}

	return hash, nil
}

// createFloorsTree creates a tree of floor objects
func (s *SnapshotService) createFloorsTree(ctx context.Context, floors []*domain.Floor) (string, error) {
	tree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: []building.TreeEntry{},
	}

	// Create blob for each floor
	for _, floor := range floors {
		data, err := json.Marshal(floor)
		if err != nil {
			return "", fmt.Errorf("failed to marshal floor %s: %w", floor.ID, err)
		}

		obj := &building.Object{
			Type:     building.ObjectTypeBlob,
			Size:     int64(len(data)),
			Contents: data,
		}

		hash, err := s.objectRepo.Store(ctx, obj)
		if err != nil {
			return "", fmt.Errorf("failed to store floor object: %w", err)
		}

		tree.Entries = append(tree.Entries, building.TreeEntry{
			Type: building.ObjectTypeBlob,
			Name: fmt.Sprintf("floor-%s", floor.ID.String()),
			Hash: hash,
			Size: int64(len(data)),
		})
	}

	// Store tree
	treeHash, err := s.treeRepo.Store(ctx, tree)
	if err != nil {
		return "", fmt.Errorf("failed to store floors tree: %w", err)
	}

	return treeHash, nil
}

// captureEquipmentTree captures all equipment as a Merkle tree
func (s *SnapshotService) captureEquipmentTree(ctx context.Context, buildingID string) (string, error) {
	// Get all equipment for building
	equipment, err := s.equipmentRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return "", fmt.Errorf("failed to get equipment: %w", err)
	}

	tree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: []building.TreeEntry{},
	}

	// Group equipment by type for better organization
	equipmentByType := make(map[string][]*domain.Equipment)
	for _, eq := range equipment {
		equipmentByType[eq.Type] = append(equipmentByType[eq.Type], eq)
	}

	// Create subtree for each equipment type
	for eqType, eqList := range equipmentByType {
		subtreeHash, err := s.createEquipmentSubtree(ctx, eqList)
		if err != nil {
			return "", fmt.Errorf("failed to create equipment subtree for type %s: %w", eqType, err)
		}

		tree.Entries = append(tree.Entries, building.TreeEntry{
			Type: building.ObjectTypeTree,
			Name: eqType,
			Hash: subtreeHash,
			Size: int64(len(eqList)),
		})
	}

	// Store tree
	treeHash, err := s.treeRepo.Store(ctx, tree)
	if err != nil {
		return "", fmt.Errorf("failed to store equipment tree: %w", err)
	}

	return treeHash, nil
}

// createEquipmentSubtree creates a tree of equipment objects
func (s *SnapshotService) createEquipmentSubtree(ctx context.Context, equipment []*domain.Equipment) (string, error) {
	tree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: []building.TreeEntry{},
	}

	for _, eq := range equipment {
		data, err := json.Marshal(eq)
		if err != nil {
			return "", fmt.Errorf("failed to marshal equipment %s: %w", eq.ID, err)
		}

		obj := &building.Object{
			Type:     building.ObjectTypeBlob,
			Size:     int64(len(data)),
			Contents: data,
		}

		hash, err := s.objectRepo.Store(ctx, obj)
		if err != nil {
			return "", fmt.Errorf("failed to store equipment object: %w", err)
		}

		tree.Entries = append(tree.Entries, building.TreeEntry{
			Type: building.ObjectTypeBlob,
			Name: fmt.Sprintf("eq-%s", eq.ID.String()),
			Hash: hash,
			Size: int64(len(data)),
		})
	}

	// Store tree
	treeHash, err := s.treeRepo.Store(ctx, tree)
	if err != nil {
		return "", fmt.Errorf("failed to store equipment subtree: %w", err)
	}

	return treeHash, nil
}

// captureSpatialTree captures spatial data as a Merkle tree
func (s *SnapshotService) captureSpatialTree(ctx context.Context, buildingID string) (string, error) {
	// For now, create an empty tree
	// TODO: Implement full spatial data capture
	tree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: []building.TreeEntry{},
	}

	// Store tree
	treeHash, err := s.treeRepo.Store(ctx, tree)
	if err != nil {
		return "", fmt.Errorf("failed to store spatial tree: %w", err)
	}

	return treeHash, nil
}

// captureFilesTree captures files as a Merkle tree
func (s *SnapshotService) captureFilesTree(ctx context.Context, repoID string) (string, error) {
	// For now, create an empty tree
	// TODO: Implement file tracking
	tree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: []building.TreeEntry{},
	}

	// Store tree
	treeHash, err := s.treeRepo.Store(ctx, tree)
	if err != nil {
		return "", fmt.Errorf("failed to store files tree: %w", err)
	}

	return treeHash, nil
}

// captureOperationsTree captures operations data as a Merkle tree
func (s *SnapshotService) captureOperationsTree(ctx context.Context, repoID string) (string, error) {
	// For now, create an empty tree
	// TODO: Implement operations data capture
	tree := &building.Tree{
		Type:    building.ObjectTypeTree,
		Entries: []building.TreeEntry{},
	}

	// Store tree
	treeHash, err := s.treeRepo.Store(ctx, tree)
	if err != nil {
		return "", fmt.Errorf("failed to store operations tree: %w", err)
	}

	return treeHash, nil
}

// LoadSnapshot loads a snapshot by hash
func (s *SnapshotService) LoadSnapshot(ctx context.Context, hash string) (*building.Snapshot, error) {
	return s.snapshotRepo.GetByHash(ctx, hash)
}

// ListSnapshots lists all snapshots for a repository
func (s *SnapshotService) ListSnapshots(ctx context.Context, repoID string) ([]*building.Snapshot, error) {
	return s.snapshotRepo.ListByRepository(ctx, repoID)
}

// GetLatestSnapshot gets the latest snapshot for a repository
func (s *SnapshotService) GetLatestSnapshot(ctx context.Context, repoID string) (*building.Snapshot, error) {
	return s.snapshotRepo.GetLatest(ctx, repoID)
}
