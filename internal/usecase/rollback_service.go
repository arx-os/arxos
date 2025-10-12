package usecase

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/types"
)

// RollbackService handles rolling back to previous versions
type RollbackService struct {
	buildingRepo  domain.BuildingRepository
	equipmentRepo domain.EquipmentRepository
	floorRepo     domain.FloorRepository
	roomRepo      domain.RoomRepository
	snapshotRepo  building.SnapshotRepository
	objectRepo    building.ObjectRepository
	treeRepo      building.TreeRepository
	versionRepo   building.VersionRepository
	logger        domain.Logger
}

// NewRollbackService creates a new rollback service
func NewRollbackService(
	buildingRepo domain.BuildingRepository,
	equipmentRepo domain.EquipmentRepository,
	floorRepo domain.FloorRepository,
	roomRepo domain.RoomRepository,
	snapshotRepo building.SnapshotRepository,
	objectRepo building.ObjectRepository,
	treeRepo building.TreeRepository,
	versionRepo building.VersionRepository,
	logger domain.Logger,
) *RollbackService {
	return &RollbackService{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		floorRepo:     floorRepo,
		roomRepo:      roomRepo,
		snapshotRepo:  snapshotRepo,
		objectRepo:    objectRepo,
		treeRepo:      treeRepo,
		versionRepo:   versionRepo,
		logger:        logger,
	}
}

// RollbackOptions configures rollback behavior
type RollbackOptions struct {
	CreateVersion bool   // Create a new version for the rollback
	Message       string // Commit message for rollback version
	ValidateAfter bool   // Validate state after rollback
	DryRun        bool   // Preview changes without applying
}

// RollbackResult contains the results of a rollback operation
type RollbackResult struct {
	Success          bool              `json:"success"`
	TargetVersion    string            `json:"target_version"`
	PreviousVersion  string            `json:"previous_version"`
	NewVersion       *building.Version `json:"new_version,omitempty"`
	Changes          *RollbackChanges  `json:"changes"`
	ValidationResult *ValidationResult `json:"validation_result,omitempty"`
	Duration         time.Duration     `json:"duration"`
	Error            string            `json:"error,omitempty"`
}

// RollbackChanges describes what was restored
type RollbackChanges struct {
	BuildingRestored  bool                   `json:"building_restored"`
	FloorsRestored    int                    `json:"floors_restored"`
	RoomsRestored     int                    `json:"rooms_restored"`
	EquipmentRestored int                    `json:"equipment_restored"`
	FilesRestored     int                    `json:"files_restored"`
	Details           []RollbackChangeDetail `json:"details"`
}

// RollbackChangeDetail describes a specific restoration
type RollbackChangeDetail struct {
	Type        string `json:"type"`   // "building", "floor", "equipment", etc.
	Action      string `json:"action"` // "restored", "created", "deleted"
	EntityID    string `json:"entity_id"`
	EntityName  string `json:"entity_name"`
	Description string `json:"description"`
}

// ValidationResult contains validation results after rollback
type ValidationResult struct {
	Valid    bool     `json:"valid"`
	Checks   []string `json:"checks"`
	Warnings []string `json:"warnings"`
	Errors   []string `json:"errors"`
}

// Rollback rolls back to a specific version
func (s *RollbackService) Rollback(ctx context.Context, buildingID string, targetVersion *building.Version, opts *RollbackOptions) (*RollbackResult, error) {
	startTime := time.Now()

	s.logger.Info("Starting rollback",
		"building_id", buildingID,
		"target_version", targetVersion.Tag,
		"dry_run", opts.DryRun)

	result := &RollbackResult{
		TargetVersion: targetVersion.Tag,
		Changes:       &RollbackChanges{Details: []RollbackChangeDetail{}},
	}

	// Get current version for comparison
	currentVersion, err := s.versionRepo.GetLatest(ctx, buildingID)
	if err != nil {
		return s.failRollback(result, startTime, fmt.Errorf("failed to get current version: %w", err))
	}
	result.PreviousVersion = currentVersion.Tag

	// Load target snapshot
	targetSnapshot, err := s.snapshotRepo.GetByHash(ctx, targetVersion.Snapshot)
	if err != nil {
		return s.failRollback(result, startTime, fmt.Errorf("failed to load target snapshot: %w", err))
	}

	// Dry run - just preview changes
	if opts.DryRun {
		changes, err := s.previewRollback(ctx, buildingID, targetSnapshot)
		if err != nil {
			return s.failRollback(result, startTime, err)
		}
		result.Changes = changes
		result.Success = true
		result.Duration = time.Since(startTime)
		return result, nil
	}

	// Perform actual rollback
	changes, err := s.performRollback(ctx, buildingID, targetSnapshot)
	if err != nil {
		return s.failRollback(result, startTime, err)
	}
	result.Changes = changes

	// Validate after rollback if requested
	if opts.ValidateAfter {
		validation := s.validateRollback(ctx, buildingID, targetSnapshot)
		result.ValidationResult = validation
		if !validation.Valid {
			return s.failRollback(result, startTime, fmt.Errorf("validation failed after rollback"))
		}
	}

	// Create new version for rollback if requested
	if opts.CreateVersion {
		message := opts.Message
		if message == "" {
			message = fmt.Sprintf("Rollback to %s", targetVersion.Tag)
		}

		newVersion, err := s.createRollbackVersion(ctx, buildingID, targetVersion, message)
		if err != nil {
			s.logger.Warn("Failed to create rollback version", "error", err)
			// Don't fail the rollback, just log the warning
		} else {
			result.NewVersion = newVersion
		}
	}

	result.Success = true
	result.Duration = time.Since(startTime)

	s.logger.Info("Rollback completed successfully",
		"building_id", buildingID,
		"target_version", targetVersion.Tag,
		"duration", result.Duration)

	return result, nil
}

// previewRollback shows what would be changed without applying
func (s *RollbackService) previewRollback(ctx context.Context, buildingID string, targetSnapshot *building.Snapshot) (*RollbackChanges, error) {
	changes := &RollbackChanges{
		Details: []RollbackChangeDetail{},
	}

	// Count what would be restored
	buildingCount, err := s.countBuildingEntities(ctx, targetSnapshot.SpaceTree)
	if err != nil {
		return nil, fmt.Errorf("failed to count building entities: %w", err)
	}
	changes.BuildingRestored = true
	changes.FloorsRestored = buildingCount.Floors
	changes.RoomsRestored = buildingCount.Rooms

	equipmentCount, err := s.countEquipment(ctx, targetSnapshot.ItemTree)
	if err != nil {
		return nil, fmt.Errorf("failed to count equipment: %w", err)
	}
	changes.EquipmentRestored = equipmentCount

	// Add preview details
	changes.Details = append(changes.Details, RollbackChangeDetail{
		Type:   "preview",
		Action: "would_restore",
		Description: fmt.Sprintf("Would restore %d floors, %d rooms, %d equipment items",
			buildingCount.Floors, buildingCount.Rooms, equipmentCount),
	})

	return changes, nil
}

// performRollback actually applies the rollback
func (s *RollbackService) performRollback(ctx context.Context, buildingID string, targetSnapshot *building.Snapshot) (*RollbackChanges, error) {
	changes := &RollbackChanges{
		Details: []RollbackChangeDetail{},
	}

	// Step 1: Restore building metadata
	if err := s.restoreBuilding(ctx, buildingID, targetSnapshot.SpaceTree); err != nil {
		return nil, fmt.Errorf("failed to restore building: %w", err)
	}
	changes.BuildingRestored = true
	changes.Details = append(changes.Details, RollbackChangeDetail{
		Type:        "building",
		Action:      "restored",
		EntityID:    buildingID,
		Description: "Building metadata restored",
	})

	// Step 2: Restore floors
	floorsRestored, err := s.restoreFloors(ctx, buildingID, targetSnapshot.SpaceTree)
	if err != nil {
		return nil, fmt.Errorf("failed to restore floors: %w", err)
	}
	changes.FloorsRestored = floorsRestored
	if floorsRestored > 0 {
		changes.Details = append(changes.Details, RollbackChangeDetail{
			Type:        "floors",
			Action:      "restored",
			Description: fmt.Sprintf("Restored %d floors", floorsRestored),
		})
	}

	// Step 3: Restore equipment
	equipmentRestored, err := s.restoreEquipment(ctx, buildingID, targetSnapshot.ItemTree)
	if err != nil {
		return nil, fmt.Errorf("failed to restore equipment: %w", err)
	}
	changes.EquipmentRestored = equipmentRestored
	if equipmentRestored > 0 {
		changes.Details = append(changes.Details, RollbackChangeDetail{
			Type:        "equipment",
			Action:      "restored",
			Description: fmt.Sprintf("Restored %d equipment items", equipmentRestored),
		})
	}

	return changes, nil
}

// restoreBuilding restores building metadata from snapshot
func (s *RollbackService) restoreBuilding(ctx context.Context, buildingID string, buildingTreeHash string) error {
	// Load building tree
	tree, err := s.treeRepo.Load(ctx, buildingTreeHash)
	if err != nil {
		return fmt.Errorf("failed to load building tree: %w", err)
	}

	// Find building metadata entry
	for _, entry := range tree.Entries {
		if entry.Name == "building" && entry.Type == building.ObjectTypeBlob {
			// Load building object
			obj, err := s.objectRepo.Load(ctx, entry.Hash)
			if err != nil {
				return fmt.Errorf("failed to load building object: %w", err)
			}

			// Deserialize building
			var bldg domain.Building
			if err := json.Unmarshal(obj.Contents, &bldg); err != nil {
				return fmt.Errorf("failed to deserialize building: %w", err)
			}

			// Update building (preserve ID)
			bldg.ID = types.FromString(buildingID)
			bldg.UpdatedAt = time.Now()

			// Save to repository
			if err := s.buildingRepo.Update(ctx, &bldg); err != nil {
				return fmt.Errorf("failed to update building: %w", err)
			}

			return nil
		}
	}

	return fmt.Errorf("building metadata not found in tree")
}

// restoreFloors restores all floors from snapshot
func (s *RollbackService) restoreFloors(ctx context.Context, buildingID string, buildingTreeHash string) (int, error) {
	// Load building tree
	tree, err := s.treeRepo.Load(ctx, buildingTreeHash)
	if err != nil {
		return 0, fmt.Errorf("failed to load building tree: %w", err)
	}

	// Find floors subtree
	var floorsTreeHash string
	for _, entry := range tree.Entries {
		if entry.Name == "floors" && entry.Type == building.ObjectTypeTree {
			floorsTreeHash = entry.Hash
			break
		}
	}

	if floorsTreeHash == "" {
		// No floors in snapshot
		return 0, nil
	}

	// Load floors tree
	floorsTree, err := s.treeRepo.Load(ctx, floorsTreeHash)
	if err != nil {
		return 0, fmt.Errorf("failed to load floors tree: %w", err)
	}

	// Delete existing floors first (clean slate)
	if err := s.deleteExistingFloors(ctx, buildingID); err != nil {
		s.logger.Warn("Failed to delete existing floors", "error", err)
		// Continue anyway
	}

	// Restore each floor
	count := 0
	for _, entry := range floorsTree.Entries {
		// Load floor object
		obj, err := s.objectRepo.Load(ctx, entry.Hash)
		if err != nil {
			s.logger.Warn("Failed to load floor object", "hash", entry.Hash, "error", err)
			continue
		}

		// Deserialize floor
		var floor domain.Floor
		if err := json.Unmarshal(obj.Contents, &floor); err != nil {
			s.logger.Warn("Failed to deserialize floor", "error", err)
			continue
		}

		// Update timestamps
		floor.CreatedAt = time.Now()
		floor.UpdatedAt = time.Now()

		// Create floor
		if err := s.floorRepo.Create(ctx, &floor); err != nil {
			s.logger.Warn("Failed to create floor", "floor_id", floor.ID, "error", err)
			continue
		}

		count++
	}

	return count, nil
}

// restoreEquipment restores all equipment from snapshot
func (s *RollbackService) restoreEquipment(ctx context.Context, buildingID string, equipmentTreeHash string) (int, error) {
	// Load equipment tree
	tree, err := s.treeRepo.Load(ctx, equipmentTreeHash)
	if err != nil {
		return 0, fmt.Errorf("failed to load equipment tree: %w", err)
	}

	// Delete existing equipment first (clean slate)
	if err := s.deleteExistingEquipment(ctx, buildingID); err != nil {
		s.logger.Warn("Failed to delete existing equipment", "error", err)
		// Continue anyway
	}

	// Restore equipment from each type subtree
	totalCount := 0
	for _, typeEntry := range tree.Entries {
		if typeEntry.Type != building.ObjectTypeTree {
			continue
		}

		// Load equipment type subtree
		subtree, err := s.treeRepo.Load(ctx, typeEntry.Hash)
		if err != nil {
			s.logger.Warn("Failed to load equipment subtree", "type", typeEntry.Name, "error", err)
			continue
		}

		// Restore each equipment item
		for _, eqEntry := range subtree.Entries {
			// Load equipment object
			obj, err := s.objectRepo.Load(ctx, eqEntry.Hash)
			if err != nil {
				s.logger.Warn("Failed to load equipment object", "hash", eqEntry.Hash, "error", err)
				continue
			}

			// Deserialize equipment
			var eq domain.Equipment
			if err := json.Unmarshal(obj.Contents, &eq); err != nil {
				s.logger.Warn("Failed to deserialize equipment", "error", err)
				continue
			}

			// Update timestamps
			eq.CreatedAt = time.Now()
			eq.UpdatedAt = time.Now()

			// Create equipment
			if err := s.equipmentRepo.Create(ctx, &eq); err != nil {
				s.logger.Warn("Failed to create equipment", "equipment_id", eq.ID, "error", err)
				continue
			}

			totalCount++
		}
	}

	return totalCount, nil
}

// deleteExistingFloors removes all floors for a building
func (s *RollbackService) deleteExistingFloors(ctx context.Context, buildingID string) error {
	floors, err := s.floorRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return err
	}

	for _, floor := range floors {
		if err := s.floorRepo.Delete(ctx, floor.ID.String()); err != nil {
			s.logger.Warn("Failed to delete floor", "floor_id", floor.ID, "error", err)
		}
	}

	return nil
}

// deleteExistingEquipment removes all equipment for a building
func (s *RollbackService) deleteExistingEquipment(ctx context.Context, buildingID string) error {
	equipment, err := s.equipmentRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return err
	}

	for _, eq := range equipment {
		if err := s.equipmentRepo.Delete(ctx, eq.ID.String()); err != nil {
			s.logger.Warn("Failed to delete equipment", "equipment_id", eq.ID, "error", err)
		}
	}

	return nil
}

// validateRollback validates the restored state
func (s *RollbackService) validateRollback(ctx context.Context, buildingID string, targetSnapshot *building.Snapshot) *ValidationResult {
	result := &ValidationResult{
		Valid:    true,
		Checks:   []string{},
		Warnings: []string{},
		Errors:   []string{},
	}

	// Check building exists
	bldg, err := s.buildingRepo.GetByID(ctx, buildingID)
	if err != nil {
		result.Valid = false
		result.Errors = append(result.Errors, fmt.Sprintf("Building not found: %v", err))
		return result
	}
	result.Checks = append(result.Checks, "Building exists")

	// Check floors count matches snapshot metadata
	floors, err := s.floorRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		result.Warnings = append(result.Warnings, fmt.Sprintf("Could not verify floors: %v", err))
	} else {
		expectedFloors := targetSnapshot.Metadata.FloorCount
		if len(floors) != expectedFloors {
			result.Warnings = append(result.Warnings,
				fmt.Sprintf("Floor count mismatch: got %d, expected %d", len(floors), expectedFloors))
		} else {
			result.Checks = append(result.Checks, fmt.Sprintf("Floors restored correctly (%d)", len(floors)))
		}
	}

	// Check equipment count matches snapshot metadata
	equipment, err := s.equipmentRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		result.Warnings = append(result.Warnings, fmt.Sprintf("Could not verify equipment: %v", err))
	} else {
		expectedEquipment := targetSnapshot.Metadata.EquipmentCount
		if len(equipment) != expectedEquipment {
			result.Warnings = append(result.Warnings,
				fmt.Sprintf("Equipment count mismatch: got %d, expected %d", len(equipment), expectedEquipment))
		} else {
			result.Checks = append(result.Checks, fmt.Sprintf("Equipment restored correctly (%d)", len(equipment)))
		}
	}

	// Check referential integrity
	for _, eq := range equipment {
		if eq.BuildingID.String() != bldg.ID.String() {
			result.Valid = false
			result.Errors = append(result.Errors,
				fmt.Sprintf("Equipment %s has wrong building ID", eq.ID))
		}
	}
	result.Checks = append(result.Checks, "Referential integrity verified")

	return result
}

// createRollbackVersion creates a new version documenting the rollback
func (s *RollbackService) createRollbackVersion(ctx context.Context, buildingID string, targetVersion *building.Version, message string) (*building.Version, error) {
	// Get current version
	currentVersion, err := s.versionRepo.GetLatest(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get current version: %w", err)
	}

	// Create new version
	newVersion := &building.Version{
		ID:           fmt.Sprintf("ver-%d", time.Now().UnixNano()),
		RepositoryID: buildingID,
		Snapshot:     targetVersion.Snapshot, // Point to same snapshot as target
		Parent:       currentVersion.Hash,
		Tag:          s.generateRollbackTag(currentVersion.Tag),
		Message:      message,
		Author: building.Author{
			Name:  "system",
			Email: "system@arxos.local",
			ID:    "",
		},
		Hash:      fmt.Sprintf("rollback-%d", time.Now().UnixNano()),
		Timestamp: time.Now(),
		Metadata: building.VersionMetadata{
			ChangeCount:   0,
			ChangeSummary: building.Summary{},
			Source:        "rollback",
			SystemVersion: "1.0.0",
		},
	}

	// Save version
	if err := s.versionRepo.Create(ctx, newVersion); err != nil {
		return nil, fmt.Errorf("failed to create rollback version: %w", err)
	}

	return newVersion, nil
}

// Helper methods

// countBuildingEntities counts entities in a building tree
func (s *RollbackService) countBuildingEntities(ctx context.Context, buildingTreeHash string) (struct{ Floors, Rooms int }, error) {
	result := struct{ Floors, Rooms int }{}

	tree, err := s.treeRepo.Load(ctx, buildingTreeHash)
	if err != nil {
		return result, err
	}

	for _, entry := range tree.Entries {
		if entry.Name == "floors" && entry.Type == building.ObjectTypeTree {
			floorsTree, err := s.treeRepo.Load(ctx, entry.Hash)
			if err == nil {
				result.Floors = len(floorsTree.Entries)
			}
		}
	}

	return result, nil
}

// countEquipment counts equipment items in an equipment tree
func (s *RollbackService) countEquipment(ctx context.Context, equipmentTreeHash string) (int, error) {
	tree, err := s.treeRepo.Load(ctx, equipmentTreeHash)
	if err != nil {
		return 0, err
	}

	total := 0
	for _, typeEntry := range tree.Entries {
		if typeEntry.Type == building.ObjectTypeTree {
			subtree, err := s.treeRepo.Load(ctx, typeEntry.Hash)
			if err == nil {
				total += len(subtree.Entries)
			}
		}
	}

	return total, nil
}

// generateRollbackTag generates a tag for a rollback version
func (s *RollbackService) generateRollbackTag(currentTag string) string {
	// Simple incrementing strategy
	// v1.2.3 -> v1.2.3-rollback-{timestamp}
	// Semantic versioning: use prerelease tag for rollbacks
	return fmt.Sprintf("%s-rollback-%d", currentTag, time.Now().Unix())
}

// failRollback helper to create a failed result
func (s *RollbackService) failRollback(result *RollbackResult, startTime time.Time, err error) (*RollbackResult, error) {
	result.Success = false
	result.Error = err.Error()
	result.Duration = time.Since(startTime)
	s.logger.Error("Rollback failed", "error", err, "duration", result.Duration)
	return result, err
}
