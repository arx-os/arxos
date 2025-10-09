package usecase

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
)

// DiffService handles calculating differences between versions
type DiffService struct {
	snapshotRepo building.SnapshotRepository
	objectRepo   building.ObjectRepository
	treeRepo     building.TreeRepository
	logger       domain.Logger
}

// NewDiffService creates a new diff service
func NewDiffService(
	snapshotRepo building.SnapshotRepository,
	objectRepo building.ObjectRepository,
	treeRepo building.TreeRepository,
	logger domain.Logger,
) *DiffService {
	return &DiffService{
		snapshotRepo: snapshotRepo,
		objectRepo:   objectRepo,
		treeRepo:     treeRepo,
		logger:       logger,
	}
}

// DiffVersions calculates the diff between two versions
// This implements the three-phase diff algorithm from ADR-007
func (s *DiffService) DiffVersions(ctx context.Context, fromVersion, toVersion *building.Version) (*building.DiffResult, error) {
	s.logger.Info("Calculating diff", "from", fromVersion.Tag, "to", toVersion.Tag)

	// Load snapshots
	fromSnapshot, err := s.snapshotRepo.GetByHash(ctx, fromVersion.Snapshot)
	if err != nil {
		return nil, fmt.Errorf("failed to load from snapshot: %w", err)
	}

	toSnapshot, err := s.snapshotRepo.GetByHash(ctx, toVersion.Snapshot)
	if err != nil {
		return nil, fmt.Errorf("failed to load to snapshot: %w", err)
	}

	return s.DiffSnapshots(ctx, fromVersion.Tag, toVersion.Tag, fromSnapshot, toSnapshot)
}

// DiffSnapshots calculates the diff between two snapshots
func (s *DiffService) DiffSnapshots(ctx context.Context, fromTag, toTag string, fromSnapshot, toSnapshot *building.Snapshot) (*building.DiffResult, error) {
	result := &building.DiffResult{
		FromVersion:  fromTag,
		ToVersion:    toTag,
		FromSnapshot: fromSnapshot.Hash,
		ToSnapshot:   toSnapshot.Hash,
		CreatedAt:    time.Now(),
		Changes:      []building.DetailedChange{},
	}

	// Phase 1: Tree-level diff (fast)
	snapshotDiff := s.phaseOneTreeDiff(fromSnapshot, toSnapshot)

	// Phase 2: Subtree-level diff (medium) - only for changed trees
	if snapshotDiff.BuildingChanged {
		buildingDiff, err := s.phaseTwoBuildingDiff(ctx, fromSnapshot.BuildingTree, toSnapshot.BuildingTree)
		if err != nil {
			return nil, fmt.Errorf("failed to diff building tree: %w", err)
		}
		result.BuildingDiff = buildingDiff
	}

	if snapshotDiff.EquipmentChanged {
		equipmentDiff, err := s.phaseTwoEquipmentDiff(ctx, fromSnapshot.EquipmentTree, toSnapshot.EquipmentTree)
		if err != nil {
			return nil, fmt.Errorf("failed to diff equipment tree: %w", err)
		}
		result.EquipmentDiff = equipmentDiff
	}

	if snapshotDiff.FilesChanged {
		filesDiff, err := s.phaseTwoFilesDiff(ctx, fromSnapshot.FilesTree, toSnapshot.FilesTree)
		if err != nil {
			return nil, fmt.Errorf("failed to diff files tree: %w", err)
		}
		result.FilesDiff = filesDiff
	}

	// Calculate summary
	result.Summary = s.calculateSummary(result)

	// Generate detailed changes list
	result.Changes = s.generateDetailedChanges(result)

	s.logger.Info("Diff calculated", "total_changes", result.Summary.TotalChanges)
	return result, nil
}

// phaseOneTreeDiff performs fast tree-level comparison (Phase 1)
func (s *DiffService) phaseOneTreeDiff(from, to *building.Snapshot) *building.SnapshotDiff {
	return &building.SnapshotDiff{
		FromHash:          from.Hash,
		ToHash:            to.Hash,
		BuildingChanged:   from.BuildingTree != to.BuildingTree,
		EquipmentChanged:  from.EquipmentTree != to.EquipmentTree,
		SpatialChanged:    from.SpatialTree != to.SpatialTree,
		FilesChanged:      from.FilesTree != to.FilesTree,
		OperationsChanged: from.OperationsTree != to.OperationsTree,
	}
}

// phaseTwoBuildingDiff performs subtree-level building comparison (Phase 2)
func (s *DiffService) phaseTwoBuildingDiff(ctx context.Context, fromTreeHash, toTreeHash string) (*building.BuildingDiff, error) {
	// Load both trees
	fromTree, err := s.treeRepo.Load(ctx, fromTreeHash)
	if err != nil {
		return nil, fmt.Errorf("failed to load from building tree: %w", err)
	}

	toTree, err := s.treeRepo.Load(ctx, toTreeHash)
	if err != nil {
		return nil, fmt.Errorf("failed to load to building tree: %w", err)
	}

	diff := &building.BuildingDiff{
		MetadataChanges: []building.FieldChange{},
		FloorsAdded:     []building.FloorChange{},
		FloorsRemoved:   []building.FloorChange{},
		FloorsModified:  []building.FloorDiff{},
		RoomsAdded:      []building.RoomChange{},
		RoomsRemoved:    []building.RoomChange{},
		RoomsModified:   []building.RoomDiff{},
	}

	// Build entry maps for fast lookup
	fromEntries := s.buildEntryMap(fromTree)
	toEntries := s.buildEntryMap(toTree)

	// Find added, removed, and modified entries
	for name, toEntry := range toEntries {
		fromEntry, exists := fromEntries[name]
		if !exists {
			// Entry was added
			if name == "floors" && toEntry.Type == building.ObjectTypeTree {
				// New floors subtree
				floors, err := s.extractFloors(ctx, toEntry.Hash)
				if err == nil {
					diff.FloorsAdded = append(diff.FloorsAdded, floors...)
				}
			}
		} else if fromEntry.Hash != toEntry.Hash {
			// Entry was modified
			if name == "floors" && toEntry.Type == building.ObjectTypeTree {
				// Floors subtree changed
				floorDiffs, err := s.diffFloorsSubtree(ctx, fromEntry.Hash, toEntry.Hash)
				if err == nil {
					diff.FloorsModified = append(diff.FloorsModified, floorDiffs...)
				}
			} else if name == "building" && toEntry.Type == building.ObjectTypeBlob {
				// Building metadata changed
				changes, err := s.diffBuildingMetadata(ctx, fromEntry.Hash, toEntry.Hash)
				if err == nil {
					diff.MetadataChanges = append(diff.MetadataChanges, changes...)
				}
			}
		}
	}

	// Find removed entries
	for name, fromEntry := range fromEntries {
		if _, exists := toEntries[name]; !exists {
			// Entry was removed
			if name == "floors" && fromEntry.Type == building.ObjectTypeTree {
				floors, err := s.extractFloors(ctx, fromEntry.Hash)
				if err == nil {
					diff.FloorsRemoved = append(diff.FloorsRemoved, floors...)
				}
			}
		}
	}

	return diff, nil
}

// phaseTwoEquipmentDiff performs subtree-level equipment comparison (Phase 2)
func (s *DiffService) phaseTwoEquipmentDiff(ctx context.Context, fromTreeHash, toTreeHash string) (*building.EquipmentDiff, error) {
	// Load both trees
	fromTree, err := s.treeRepo.Load(ctx, fromTreeHash)
	if err != nil {
		return nil, fmt.Errorf("failed to load from equipment tree: %w", err)
	}

	toTree, err := s.treeRepo.Load(ctx, toTreeHash)
	if err != nil {
		return nil, fmt.Errorf("failed to load to equipment tree: %w", err)
	}

	diff := &building.EquipmentDiff{
		Added:        []building.EquipmentChange{},
		Removed:      []building.EquipmentChange{},
		Modified:     []building.EquipmentChange{},
		Moved:        []building.EquipmentMove{},
		Reclassified: []building.EquipmentReclass{},
	}

	// Build entry maps (equipment organized by type)
	fromEntries := s.buildEntryMap(fromTree)
	toEntries := s.buildEntryMap(toTree)

	// Process each equipment type subtree
	for typeName, toEntry := range toEntries {
		fromEntry, exists := fromEntries[typeName]
		if !exists {
			// New equipment type
			equipment, err := s.extractEquipment(ctx, toEntry.Hash, typeName)
			if err == nil {
				diff.Added = append(diff.Added, equipment...)
			}
		} else if fromEntry.Hash != toEntry.Hash {
			// Equipment type subtree changed
			eqDiffs, err := s.diffEquipmentSubtree(ctx, fromEntry.Hash, toEntry.Hash, typeName)
			if err == nil {
				diff.Added = append(diff.Added, eqDiffs.Added...)
				diff.Removed = append(diff.Removed, eqDiffs.Removed...)
				diff.Modified = append(diff.Modified, eqDiffs.Modified...)
			}
		}
	}

	// Find removed equipment types
	for typeName, fromEntry := range fromEntries {
		if _, exists := toEntries[typeName]; !exists {
			equipment, err := s.extractEquipment(ctx, fromEntry.Hash, typeName)
			if err == nil {
				diff.Removed = append(diff.Removed, equipment...)
			}
		}
	}

	return diff, nil
}

// phaseTwoFilesDiff performs subtree-level files comparison (Phase 2)
func (s *DiffService) phaseTwoFilesDiff(ctx context.Context, fromTreeHash, toTreeHash string) (*building.FilesDiff, error) {
	// Load both trees
	fromTree, err := s.treeRepo.Load(ctx, fromTreeHash)
	if err != nil {
		return nil, fmt.Errorf("failed to load from files tree: %w", err)
	}

	toTree, err := s.treeRepo.Load(ctx, toTreeHash)
	if err != nil {
		return nil, fmt.Errorf("failed to load to files tree: %w", err)
	}

	diff := &building.FilesDiff{
		Added:    []building.FileChange{},
		Removed:  []building.FileChange{},
		Modified: []building.FileChange{},
		Renamed:  []building.FileRename{},
		Moved:    []building.FileMove{},
	}

	// Build entry maps
	fromEntries := s.buildEntryMap(fromTree)
	toEntries := s.buildEntryMap(toTree)

	// Find added and modified files
	for path, toEntry := range toEntries {
		fromEntry, exists := fromEntries[path]
		if !exists {
			// File was added
			diff.Added = append(diff.Added, building.FileChange{
				Path:    path,
				Name:    path,
				NewHash: toEntry.Hash,
				NewSize: toEntry.Size,
			})
		} else if fromEntry.Hash != toEntry.Hash {
			// File was modified
			diff.Modified = append(diff.Modified, building.FileChange{
				Path:     path,
				Name:     path,
				OldHash:  fromEntry.Hash,
				NewHash:  toEntry.Hash,
				OldSize:  fromEntry.Size,
				NewSize:  toEntry.Size,
				SizeDiff: toEntry.Size - fromEntry.Size,
			})
		}
	}

	// Find removed files
	for path, fromEntry := range fromEntries {
		if _, exists := toEntries[path]; !exists {
			diff.Removed = append(diff.Removed, building.FileChange{
				Path:    path,
				Name:    path,
				OldHash: fromEntry.Hash,
				OldSize: fromEntry.Size,
			})
		}
	}

	return diff, nil
}

// Helper methods

// buildEntryMap builds a map of tree entries for fast lookup
func (s *DiffService) buildEntryMap(tree *building.Tree) map[string]building.TreeEntry {
	entries := make(map[string]building.TreeEntry)
	for _, entry := range tree.Entries {
		entries[entry.Name] = entry
	}
	return entries
}

// extractFloors extracts floor changes from a floors subtree
func (s *DiffService) extractFloors(ctx context.Context, treeHash string) ([]building.FloorChange, error) {
	tree, err := s.treeRepo.Load(ctx, treeHash)
	if err != nil {
		return nil, err
	}

	floors := []building.FloorChange{}
	for _, entry := range tree.Entries {
		// Load floor blob and extract basic info
		obj, err := s.objectRepo.Load(ctx, entry.Hash)
		if err != nil {
			continue
		}

		var floor domain.Floor
		if err := json.Unmarshal(obj.Contents, &floor); err != nil {
			continue
		}

		floors = append(floors, building.FloorChange{
			ID:    floor.ID.String(),
			Name:  floor.Name,
			Level: floor.Level,
		})
	}

	return floors, nil
}

// diffFloorsSubtree diffs two floors subtrees
func (s *DiffService) diffFloorsSubtree(ctx context.Context, fromHash, toHash string) ([]building.FloorDiff, error) {
	fromTree, err := s.treeRepo.Load(ctx, fromHash)
	if err != nil {
		return nil, err
	}

	toTree, err := s.treeRepo.Load(ctx, toHash)
	if err != nil {
		return nil, err
	}

	diffs := []building.FloorDiff{}
	fromEntries := s.buildEntryMap(fromTree)
	toEntries := s.buildEntryMap(toTree)

	// Find modified floors
	for name, toEntry := range toEntries {
		if fromEntry, exists := fromEntries[name]; exists && fromEntry.Hash != toEntry.Hash {
			// Floor was modified
			changes, err := s.diffFloorBlobs(ctx, fromEntry.Hash, toEntry.Hash)
			if err == nil && len(changes) > 0 {
				// Extract floor ID and name
				obj, _ := s.objectRepo.Load(ctx, toEntry.Hash)
				if obj != nil {
					var floor domain.Floor
					if json.Unmarshal(obj.Contents, &floor) == nil {
						diffs = append(diffs, building.FloorDiff{
							ID:      floor.ID.String(),
							Name:    floor.Name,
							Changes: changes,
						})
					}
				}
			}
		}
	}

	return diffs, nil
}

// diffBuildingMetadata diffs two building metadata blobs
func (s *DiffService) diffBuildingMetadata(ctx context.Context, fromHash, toHash string) ([]building.FieldChange, error) {
	fromObj, err := s.objectRepo.Load(ctx, fromHash)
	if err != nil {
		return nil, err
	}

	toObj, err := s.objectRepo.Load(ctx, toHash)
	if err != nil {
		return nil, err
	}

	var fromBuilding, toBuilding domain.Building
	if err := json.Unmarshal(fromObj.Contents, &fromBuilding); err != nil {
		return nil, err
	}
	if err := json.Unmarshal(toObj.Contents, &toBuilding); err != nil {
		return nil, err
	}

	changes := []building.FieldChange{}

	// Compare fields
	if fromBuilding.Name != toBuilding.Name {
		changes = append(changes, building.FieldChange{
			Field:    "name",
			OldValue: fromBuilding.Name,
			NewValue: toBuilding.Name,
			Path:     "building.name",
		})
	}

	if fromBuilding.Address != toBuilding.Address {
		changes = append(changes, building.FieldChange{
			Field:    "address",
			OldValue: fromBuilding.Address,
			NewValue: toBuilding.Address,
			Path:     "building.address",
		})
	}

	return changes, nil
}

// diffFloorBlobs diffs two floor blobs
func (s *DiffService) diffFloorBlobs(ctx context.Context, fromHash, toHash string) ([]building.FieldChange, error) {
	fromObj, err := s.objectRepo.Load(ctx, fromHash)
	if err != nil {
		return nil, err
	}

	toObj, err := s.objectRepo.Load(ctx, toHash)
	if err != nil {
		return nil, err
	}

	var fromFloor, toFloor domain.Floor
	if err := json.Unmarshal(fromObj.Contents, &fromFloor); err != nil {
		return nil, err
	}
	if err := json.Unmarshal(toObj.Contents, &toFloor); err != nil {
		return nil, err
	}

	changes := []building.FieldChange{}

	if fromFloor.Name != toFloor.Name {
		changes = append(changes, building.FieldChange{
			Field:    "name",
			OldValue: fromFloor.Name,
			NewValue: toFloor.Name,
		})
	}

	if fromFloor.Level != toFloor.Level {
		changes = append(changes, building.FieldChange{
			Field:    "level",
			OldValue: fromFloor.Level,
			NewValue: toFloor.Level,
		})
	}

	return changes, nil
}

// extractEquipment extracts equipment from a subtree
func (s *DiffService) extractEquipment(ctx context.Context, treeHash, eqType string) ([]building.EquipmentChange, error) {
	tree, err := s.treeRepo.Load(ctx, treeHash)
	if err != nil {
		return nil, err
	}

	equipment := []building.EquipmentChange{}
	for _, entry := range tree.Entries {
		obj, err := s.objectRepo.Load(ctx, entry.Hash)
		if err != nil {
			continue
		}

		var eq domain.Equipment
		if err := json.Unmarshal(obj.Contents, &eq); err != nil {
			continue
		}

		location := ""
		if eq.Location != nil {
			location = fmt.Sprintf("(%.2f, %.2f, %.2f)", eq.Location.X, eq.Location.Y, eq.Location.Z)
		}

		equipment = append(equipment, building.EquipmentChange{
			ID:       eq.ID.String(),
			Name:     eq.Name,
			Type:     eq.Type,
			Location: location,
		})
	}

	return equipment, nil
}

// diffEquipmentSubtree diffs two equipment subtrees
func (s *DiffService) diffEquipmentSubtree(ctx context.Context, fromHash, toHash, eqType string) (*building.EquipmentDiff, error) {
	fromTree, err := s.treeRepo.Load(ctx, fromHash)
	if err != nil {
		return nil, err
	}

	toTree, err := s.treeRepo.Load(ctx, toHash)
	if err != nil {
		return nil, err
	}

	diff := &building.EquipmentDiff{
		Added:    []building.EquipmentChange{},
		Removed:  []building.EquipmentChange{},
		Modified: []building.EquipmentChange{},
	}

	fromEntries := s.buildEntryMap(fromTree)
	toEntries := s.buildEntryMap(toTree)

	// Find added and modified equipment
	for name, toEntry := range toEntries {
		if fromEntry, exists := fromEntries[name]; !exists {
			// Equipment was added
			obj, _ := s.objectRepo.Load(ctx, toEntry.Hash)
			if obj != nil {
				var eq domain.Equipment
				if json.Unmarshal(obj.Contents, &eq) == nil {
					location := ""
					if eq.Location != nil {
						location = fmt.Sprintf("(%.2f, %.2f, %.2f)", eq.Location.X, eq.Location.Y, eq.Location.Z)
					}

					diff.Added = append(diff.Added, building.EquipmentChange{
						ID:       eq.ID.String(),
						Name:     eq.Name,
						Type:     eq.Type,
						Location: location,
					})
				}
			}
		} else if fromEntry.Hash != toEntry.Hash {
			// Equipment was modified
			changes, _ := s.diffEquipmentBlobs(ctx, fromEntry.Hash, toEntry.Hash)
			if len(changes) > 0 {
				obj, _ := s.objectRepo.Load(ctx, toEntry.Hash)
				if obj != nil {
					var eq domain.Equipment
					if json.Unmarshal(obj.Contents, &eq) == nil {
						location := ""
						if eq.Location != nil {
							location = fmt.Sprintf("(%.2f, %.2f, %.2f)", eq.Location.X, eq.Location.Y, eq.Location.Z)
						}

						diff.Modified = append(diff.Modified, building.EquipmentChange{
							ID:       eq.ID.String(),
							Name:     eq.Name,
							Type:     eq.Type,
							Location: location,
							Changes:  changes,
						})
					}
				}
			}
		}
	}

	// Find removed equipment
	for name, fromEntry := range fromEntries {
		if _, exists := toEntries[name]; !exists {
			obj, _ := s.objectRepo.Load(ctx, fromEntry.Hash)
			if obj != nil {
				var eq domain.Equipment
				if json.Unmarshal(obj.Contents, &eq) == nil {
					location := ""
					if eq.Location != nil {
						location = fmt.Sprintf("(%.2f, %.2f, %.2f)", eq.Location.X, eq.Location.Y, eq.Location.Z)
					}

					diff.Removed = append(diff.Removed, building.EquipmentChange{
						ID:       eq.ID.String(),
						Name:     eq.Name,
						Type:     eq.Type,
						Location: location,
					})
				}
			}
		}
	}

	return diff, nil
}

// diffEquipmentBlobs diffs two equipment blobs
func (s *DiffService) diffEquipmentBlobs(ctx context.Context, fromHash, toHash string) ([]building.FieldChange, error) {
	fromObj, err := s.objectRepo.Load(ctx, fromHash)
	if err != nil {
		return nil, err
	}

	toObj, err := s.objectRepo.Load(ctx, toHash)
	if err != nil {
		return nil, err
	}

	var fromEq, toEq domain.Equipment
	if err := json.Unmarshal(fromObj.Contents, &fromEq); err != nil {
		return nil, err
	}
	if err := json.Unmarshal(toObj.Contents, &toEq); err != nil {
		return nil, err
	}

	changes := []building.FieldChange{}

	if fromEq.Name != toEq.Name {
		changes = append(changes, building.FieldChange{
			Field:    "name",
			OldValue: fromEq.Name,
			NewValue: toEq.Name,
		})
	}

	if fromEq.Status != toEq.Status {
		changes = append(changes, building.FieldChange{
			Field:    "status",
			OldValue: fromEq.Status,
			NewValue: toEq.Status,
		})
	}

	// Compare location (convert to string for comparison)
	fromLoc := ""
	if fromEq.Location != nil {
		fromLoc = fmt.Sprintf("(%.2f, %.2f, %.2f)", fromEq.Location.X, fromEq.Location.Y, fromEq.Location.Z)
	}
	toLoc := ""
	if toEq.Location != nil {
		toLoc = fmt.Sprintf("(%.2f, %.2f, %.2f)", toEq.Location.X, toEq.Location.Y, toEq.Location.Z)
	}
	if fromLoc != toLoc {
		changes = append(changes, building.FieldChange{
			Field:    "location",
			OldValue: fromLoc,
			NewValue: toLoc,
		})
	}

	return changes, nil
}

// calculateSummary generates the diff summary
func (s *DiffService) calculateSummary(result *building.DiffResult) building.DiffSummary {
	summary := building.DiffSummary{}

	// Building changes
	if result.BuildingDiff != nil {
		summary.FloorsAdded = len(result.BuildingDiff.FloorsAdded)
		summary.FloorsRemoved = len(result.BuildingDiff.FloorsRemoved)
		summary.FloorsModified = len(result.BuildingDiff.FloorsModified)
		summary.RoomsAdded = len(result.BuildingDiff.RoomsAdded)
		summary.RoomsRemoved = len(result.BuildingDiff.RoomsRemoved)
		summary.RoomsModified = len(result.BuildingDiff.RoomsModified)
		summary.BuildingsModified = 1 // Always 1 if there are building changes
	}

	// Equipment changes
	if result.EquipmentDiff != nil {
		summary.EquipmentAdded = len(result.EquipmentDiff.Added)
		summary.EquipmentRemoved = len(result.EquipmentDiff.Removed)
		summary.EquipmentModified = len(result.EquipmentDiff.Modified)
		summary.EquipmentMoved = len(result.EquipmentDiff.Moved)
	}

	// Files changes
	if result.FilesDiff != nil {
		summary.FilesAdded = len(result.FilesDiff.Added)
		summary.FilesRemoved = len(result.FilesDiff.Removed)
		summary.FilesModified = len(result.FilesDiff.Modified)

		// Calculate size changes
		for _, file := range result.FilesDiff.Added {
			summary.SizeChanged += file.NewSize
		}
		for _, file := range result.FilesDiff.Removed {
			summary.SizeChanged -= file.OldSize
		}
		for _, file := range result.FilesDiff.Modified {
			summary.SizeChanged += file.SizeDiff
		}
	}

	// Total changes
	summary.TotalChanges = summary.FloorsAdded + summary.FloorsRemoved + summary.FloorsModified +
		summary.RoomsAdded + summary.RoomsRemoved + summary.RoomsModified +
		summary.EquipmentAdded + summary.EquipmentRemoved + summary.EquipmentModified +
		summary.FilesAdded + summary.FilesRemoved + summary.FilesModified

	return summary
}

// generateDetailedChanges generates the detailed changes list
func (s *DiffService) generateDetailedChanges(result *building.DiffResult) []building.DetailedChange {
	changes := []building.DetailedChange{}

	// Equipment added
	if result.EquipmentDiff != nil {
		for _, eq := range result.EquipmentDiff.Added {
			changes = append(changes, building.DetailedChange{
				Type:        building.ChangeTypeAdded,
				Category:    "equipment",
				EntityType:  "equipment",
				EntityID:    eq.ID,
				EntityName:  eq.Name,
				Path:        fmt.Sprintf("equipment/%s/%s", eq.Type, eq.ID),
				Description: fmt.Sprintf("Added %s equipment: %s", eq.Type, eq.Name),
				NewValue:    eq.Name,
				Severity:    "info",
			})
		}

		for _, eq := range result.EquipmentDiff.Removed {
			changes = append(changes, building.DetailedChange{
				Type:        building.ChangeTypeDeleted,
				Category:    "equipment",
				EntityType:  "equipment",
				EntityID:    eq.ID,
				EntityName:  eq.Name,
				Path:        fmt.Sprintf("equipment/%s/%s", eq.Type, eq.ID),
				Description: fmt.Sprintf("Removed %s equipment: %s", eq.Type, eq.Name),
				OldValue:    eq.Name,
				Severity:    "minor",
			})
		}

		for _, eq := range result.EquipmentDiff.Modified {
			changes = append(changes, building.DetailedChange{
				Type:        building.ChangeTypeModified,
				Category:    "equipment",
				EntityType:  "equipment",
				EntityID:    eq.ID,
				EntityName:  eq.Name,
				Path:        fmt.Sprintf("equipment/%s/%s", eq.Type, eq.ID),
				Description: fmt.Sprintf("Modified %s equipment: %s", eq.Type, eq.Name),
				Severity:    "info",
			})
		}
	}

	// Building structure changes
	if result.BuildingDiff != nil {
		for _, floor := range result.BuildingDiff.FloorsAdded {
			changes = append(changes, building.DetailedChange{
				Type:        building.ChangeTypeAdded,
				Category:    "building",
				EntityType:  "floor",
				EntityID:    floor.ID,
				EntityName:  floor.Name,
				Path:        fmt.Sprintf("building/floors/%s", floor.ID),
				Description: fmt.Sprintf("Added floor: %s (Level %d)", floor.Name, floor.Level),
				Severity:    "major",
			})
		}
	}

	return changes
}

// Distance3D calculates 3D distance between two points
func Distance3D(from, to *building.Point3D) float64 {
	if from == nil || to == nil {
		return 0
	}
	dx := to.X - from.X
	dy := to.Y - from.Y
	dz := to.Z - from.Z
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}
