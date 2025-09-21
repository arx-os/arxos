package sync

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	syncpkg "github.com/arx-os/arxos/pkg/sync"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// ConflictResolver handles conflict detection and resolution
type ConflictResolver struct {
	db           database.DB
	resolutionDB ConflictResolutionStore
}

// NewConflictResolver creates a new conflict resolver
func NewConflictResolver(db database.DB, resolutionDB ConflictResolutionStore) *ConflictResolver {
	return &ConflictResolver{
		db:           db,
		resolutionDB: resolutionDB,
	}
}

// ConflictResolutionStore stores conflict resolutions
type ConflictResolutionStore interface {
	SaveConflict(ctx context.Context, conflict *syncpkg.Conflict) error
	GetConflict(ctx context.Context, id string) (*syncpkg.Conflict, error)
	ListConflicts(ctx context.Context, entityID string) ([]*syncpkg.Conflict, error)
	ResolveConflict(ctx context.Context, id string, resolution ConflictResolution) error
	DeleteConflict(ctx context.Context, id string) error
}

// ConflictResolution represents how a conflict was resolved
type ConflictResolution struct {
	ID           string                 `json:"id"`
	ConflictID   string                 `json:"conflict_id"`
	Resolution   ResolutionType         `json:"resolution"`
	ResolvedBy   string                 `json:"resolved_by"`
	ResolvedAt   time.Time              `json:"resolved_at"`
	MergedData   map[string]interface{} `json:"merged_data,omitempty"`
	Notes        string                 `json:"notes,omitempty"`
}

// ResolutionType defines types of conflict resolution
type ResolutionType string

const (
	ResolutionTypeLocal      ResolutionType = "local"      // Keep local version
	ResolutionTypeRemote     ResolutionType = "remote"     // Keep remote version
	ResolutionTypeMerge      ResolutionType = "merge"      // Merge both versions
	ResolutionTypeCustom     ResolutionType = "custom"     // Custom resolution
	ResolutionTypeDefer      ResolutionType = "defer"      // Defer resolution for later
)

// ConflictType represents types of conflicts
type ConflictType string

const (
	ConflictTypeUpdate    ConflictType = "update"     // Both sides updated
	ConflictTypeDeleteUpdate ConflictType = "delete_update" // One deleted, one updated
	ConflictTypeSchema    ConflictType = "schema"     // Schema mismatch
	ConflictTypeVersion   ConflictType = "version"    // Version conflict
)

// DetectConflicts detects conflicts between local and remote changes
func (cr *ConflictResolver) DetectConflicts(ctx context.Context, localChanges, remoteChanges []syncpkg.Change) ([]*syncpkg.Conflict, error) {
	conflicts := []*syncpkg.Conflict{}

	// Create maps for efficient lookup
	localMap := make(map[string]syncpkg.Change)
	for _, change := range localChanges {
		key := fmt.Sprintf("%s:%s", change.Entity, change.EntityID)
		localMap[key] = change
	}

	remoteMap := make(map[string]syncpkg.Change)
	for _, change := range remoteChanges {
		key := fmt.Sprintf("%s:%s", change.Entity, change.EntityID)
		remoteMap[key] = change
	}

	// Check for conflicts
	for key, localChange := range localMap {
		if remoteChange, exists := remoteMap[key]; exists {
			if conflict := cr.checkForConflict(localChange, remoteChange); conflict != nil {
				conflicts = append(conflicts, conflict)
			}
		}
	}

	return conflicts, nil
}

// checkForConflict checks if two changes conflict
func (cr *ConflictResolver) checkForConflict(local, remote syncpkg.Change) *syncpkg.Conflict {
	// If timestamps are the same, no conflict
	if local.Timestamp.Equal(remote.Timestamp) {
		return nil
	}

	// If versions are different, there's a conflict
	if local.Version != remote.Version && local.Version > 0 && remote.Version > 0 {
		return &syncpkg.Conflict{
			ID:            uuid.New().String(),
			Entity:        local.Entity,
			EntityID:      local.EntityID,
			LocalVersion:  local.Version,
			RemoteVersion: remote.Version,
			ConflictType:  string(ConflictTypeVersion),
			LocalData:     local.Data,
			RemoteData:    remote.Data,
			LocalChange:   &local,
			RemoteChange:  &remote,
		}
	}

	// Check for delete-update conflict
	if (local.Type == "delete" && remote.Type == "update") ||
	   (local.Type == "update" && remote.Type == "delete") {
		return &syncpkg.Conflict{
			ID:            uuid.New().String(),
			Entity:        local.Entity,
			EntityID:      local.EntityID,
			ConflictType:  string(ConflictTypeDeleteUpdate),
			LocalData:     local.Data,
			RemoteData:    remote.Data,
			LocalChange:   &local,
			RemoteChange:  &remote,
		}
	}

	// Check for concurrent updates
	if local.Type == "update" && remote.Type == "update" {
		// Check if the actual data differs
		if !cr.dataEquals(local.Data, remote.Data) {
			return &syncpkg.Conflict{
				ID:            uuid.New().String(),
				Entity:        local.Entity,
				EntityID:      local.EntityID,
				ConflictType:  string(ConflictTypeUpdate),
				LocalData:     local.Data,
				RemoteData:    remote.Data,
				LocalChange:   &local,
				RemoteChange:  &remote,
			}
		}
	}

	return nil
}

// dataEquals compares two data maps for equality
func (cr *ConflictResolver) dataEquals(a, b map[string]interface{}) bool {
	if len(a) != len(b) {
		return false
	}

	for key, aVal := range a {
		bVal, exists := b[key]
		if !exists {
			return false
		}

		// Simple comparison - could be enhanced for deep equality
		aJSON, _ := json.Marshal(aVal)
		bJSON, _ := json.Marshal(bVal)
		if string(aJSON) != string(bJSON) {
			return false
		}
	}

	return true
}

// ResolveConflict resolves a specific conflict
func (cr *ConflictResolver) ResolveConflict(ctx context.Context, conflictID string, resolution ResolutionType, userID string) error {
	// Get the conflict
	conflict, err := cr.resolutionDB.GetConflict(ctx, conflictID)
	if err != nil {
		return fmt.Errorf("failed to get conflict: %w", err)
	}

	// Apply resolution based on type
	switch resolution {
	case ResolutionTypeLocal:
		err = cr.applyLocalVersion(ctx, conflict)
	case ResolutionTypeRemote:
		err = cr.applyRemoteVersion(ctx, conflict)
	case ResolutionTypeMerge:
		err = cr.applyMergedVersion(ctx, conflict)
	case ResolutionTypeDefer:
		// Just mark as deferred, don't apply any changes
		logger.Info("Deferring conflict resolution for %s", conflictID)
	default:
		return fmt.Errorf("unknown resolution type: %s", resolution)
	}

	if err != nil {
		return fmt.Errorf("failed to apply resolution: %w", err)
	}

	// Save resolution record
	resolutionRecord := ConflictResolution{
		ID:         uuid.New().String(),
		ConflictID: conflictID,
		Resolution: resolution,
		ResolvedBy: userID,
		ResolvedAt: time.Now(),
	}

	if err := cr.resolutionDB.ResolveConflict(ctx, conflictID, resolutionRecord); err != nil {
		return fmt.Errorf("failed to save resolution: %w", err)
	}

	logger.Info("Resolved conflict %s with resolution %s", conflictID, resolution)
	return nil
}

// applyLocalVersion applies the local version to resolve a conflict
func (cr *ConflictResolver) applyLocalVersion(ctx context.Context, conflict *syncpkg.Conflict) error {
	if conflict.LocalChange == nil {
		return fmt.Errorf("no local change data available")
	}

	return cr.applyChange(ctx, *conflict.LocalChange)
}

// applyRemoteVersion applies the remote version to resolve a conflict
func (cr *ConflictResolver) applyRemoteVersion(ctx context.Context, conflict *syncpkg.Conflict) error {
	if conflict.RemoteChange == nil {
		return fmt.Errorf("no remote change data available")
	}

	return cr.applyChange(ctx, *conflict.RemoteChange)
}

// applyMergedVersion attempts to merge both versions
func (cr *ConflictResolver) applyMergedVersion(ctx context.Context, conflict *syncpkg.Conflict) error {
	// Merge strategy depends on the entity type
	switch conflict.Entity {
	case "equipment":
		return cr.mergeEquipment(ctx, conflict)
	case "room":
		return cr.mergeRoom(ctx, conflict)
	case "building":
		return cr.mergeBuilding(ctx, conflict)
	default:
		// Fallback to local version if merge not supported
		logger.Warn("Merge not supported for entity type %s, using local version", conflict.Entity)
		return cr.applyLocalVersion(ctx, conflict)
	}
}

// mergeEquipment merges equipment conflicts
func (cr *ConflictResolver) mergeEquipment(ctx context.Context, conflict *syncpkg.Conflict) error {
	// Get current equipment
	equipment, err := cr.db.GetEquipment(ctx, conflict.EntityID)
	if err != nil {
		return fmt.Errorf("failed to get equipment: %w", err)
	}

	// Apply non-conflicting fields from both versions
	if conflict.LocalData != nil {
		if name, ok := conflict.LocalData["name"].(string); ok && name != "" {
			equipment.Name = name
		}
		if status, ok := conflict.LocalData["status"].(string); ok && status != "" {
			equipment.Status = status
		}
	}

	if conflict.RemoteData != nil {
		if model, ok := conflict.RemoteData["model"].(string); ok && model != "" {
			equipment.Model = model
		}
		if serial, ok := conflict.RemoteData["serial"].(string); ok && serial != "" {
			equipment.Serial = serial
		}
	}

	// Save merged equipment
	return cr.db.UpdateEquipment(ctx, equipment)
}

// mergeRoom merges room conflicts
func (cr *ConflictResolver) mergeRoom(ctx context.Context, conflict *syncpkg.Conflict) error {
	// Get current room
	room, err := cr.db.GetRoom(ctx, conflict.EntityID)
	if err != nil {
		return fmt.Errorf("failed to get room: %w", err)
	}

	// Apply non-conflicting fields
	if conflict.LocalData != nil {
		if name, ok := conflict.LocalData["name"].(string); ok && name != "" {
			room.Name = name
		}
	}

	if conflict.RemoteData != nil {
		// Remote data might have different fields
		// Merge based on your business logic
	}

	// Save merged room
	return cr.db.UpdateRoom(ctx, room)
}

// mergeBuilding merges building conflicts
func (cr *ConflictResolver) mergeBuilding(ctx context.Context, conflict *syncpkg.Conflict) error {
	// Get current building
	building, err := cr.db.GetFloorPlan(ctx, conflict.EntityID)
	if err != nil {
		return fmt.Errorf("failed to get building: %w", err)
	}

	// Merge building fields
	if conflict.LocalData != nil {
		if name, ok := conflict.LocalData["name"].(string); ok && name != "" {
			building.Name = name
		}
		if level, ok := conflict.LocalData["level"].(float64); ok {
			building.Level = int(level)
		}
	}

	// Save merged building
	return cr.db.UpdateFloorPlan(ctx, building)
}

// applyChange applies a change to the database
func (cr *ConflictResolver) applyChange(ctx context.Context, change syncpkg.Change) error {
	switch change.Entity {
	case "equipment":
		return cr.applyEquipmentChange(ctx, change)
	case "room":
		return cr.applyRoomChange(ctx, change)
	case "building":
		return cr.applyBuildingChange(ctx, change)
	default:
		return fmt.Errorf("unknown entity type: %s", change.Entity)
	}
}

// applyEquipmentChange applies an equipment change
func (cr *ConflictResolver) applyEquipmentChange(ctx context.Context, change syncpkg.Change) error {
	switch change.Type {
	case "create":
		equipment := &models.Equipment{
			ID: change.EntityID,
		}
		cr.populateEquipmentFromData(equipment, change.Data)
		return cr.db.SaveEquipment(ctx, equipment)

	case "update":
		equipment, err := cr.db.GetEquipment(ctx, change.EntityID)
		if err != nil {
			return err
		}
		cr.populateEquipmentFromData(equipment, change.Data)
		return cr.db.UpdateEquipment(ctx, equipment)

	case "delete":
		return cr.db.DeleteEquipment(ctx, change.EntityID)

	default:
		return fmt.Errorf("unknown change type: %s", change.Type)
	}
}

// applyRoomChange applies a room change
func (cr *ConflictResolver) applyRoomChange(ctx context.Context, change syncpkg.Change) error {
	switch change.Type {
	case "create":
		room := &models.Room{
			ID: change.EntityID,
		}
		cr.populateRoomFromData(room, change.Data)
		return cr.db.SaveRoom(ctx, room)

	case "update":
		room, err := cr.db.GetRoom(ctx, change.EntityID)
		if err != nil {
			return err
		}
		cr.populateRoomFromData(room, change.Data)
		return cr.db.UpdateRoom(ctx, room)

	case "delete":
		return cr.db.DeleteRoom(ctx, change.EntityID)

	default:
		return fmt.Errorf("unknown change type: %s", change.Type)
	}
}

// applyBuildingChange applies a building change
func (cr *ConflictResolver) applyBuildingChange(ctx context.Context, change syncpkg.Change) error {
	switch change.Type {
	case "update":
		building, err := cr.db.GetFloorPlan(ctx, change.EntityID)
		if err != nil {
			return err
		}
		cr.populateBuildingFromData(building, change.Data)
		return cr.db.UpdateFloorPlan(ctx, building)

	case "delete":
		return cr.db.DeleteFloorPlan(ctx, change.EntityID)

	default:
		return fmt.Errorf("unknown change type: %s", change.Type)
	}
}

// Helper functions to populate models from data
func (cr *ConflictResolver) populateEquipmentFromData(equipment *models.Equipment, data map[string]interface{}) {
	if name, ok := data["name"].(string); ok {
		equipment.Name = name
	}
	if eType, ok := data["type"].(string); ok {
		equipment.Type = eType
	}
	if status, ok := data["status"].(string); ok {
		equipment.Status = status
	}
	if model, ok := data["model"].(string); ok {
		equipment.Model = model
	}
	if serial, ok := data["serial"].(string); ok {
		equipment.Serial = serial
	}
}

func (cr *ConflictResolver) populateRoomFromData(room *models.Room, data map[string]interface{}) {
	if name, ok := data["name"].(string); ok {
		room.Name = name
	}
	// Add more field mappings as needed
}

func (cr *ConflictResolver) populateBuildingFromData(building *models.FloorPlan, data map[string]interface{}) {
	if name, ok := data["name"].(string); ok {
		building.Name = name
	}
	if level, ok := data["level"].(float64); ok {
		building.Level = int(level)
	}
	// Add more field mappings as needed
}