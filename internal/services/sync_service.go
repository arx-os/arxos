package services

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	servicesync "github.com/arx-os/arxos/internal/services/sync"
	"github.com/arx-os/arxos/internal/storage"
	"github.com/arx-os/arxos/pkg/models"
)

// SyncService handles synchronization between local and cloud storage
type SyncService struct {
	db               database.DB
	storage          storage.Backend
	conflictMode     ConflictResolutionMode
	conflictResolver *servicesync.ConflictResolver
	changeTracker    *servicesync.ChangeTracker
	syncQueue        chan SyncTask
	workers          int
	mu               sync.RWMutex
	syncStatus       map[string]*SyncStatus
}

// ConflictResolutionMode defines how conflicts are resolved
type ConflictResolutionMode string

const (
	ConflictModeLocal  ConflictResolutionMode = "local"  // Local changes win
	ConflictModeRemote ConflictResolutionMode = "remote" // Remote changes win
	ConflictModeMerge  ConflictResolutionMode = "merge"  // Attempt to merge
	ConflictModeAsk    ConflictResolutionMode = "ask"    // Ask user
)

// SyncTask represents a synchronization task
type SyncTask struct {
	BuildingID string
	Type       SyncType
	Force      bool
	Callback   func(error)
}

// SyncType defines the type of sync operation
type SyncType string

const (
	SyncTypePush SyncType = "push"
	SyncTypePull SyncType = "pull"
	SyncTypeFull SyncType = "full"
)

// SyncStatus tracks the status of a sync operation
type SyncStatus struct {
	BuildingID  string
	LastSync    time.Time
	InProgress  bool
	PendingPush int
	PendingPull int
	Conflicts   []api.Conflict
	Error       error
}

// NewSyncService creates a new sync service
func NewSyncService(db database.DB, storage storage.Backend, workers int) *SyncService {
	if workers <= 0 {
		workers = 4
	}

	// Initialize conflict resolver with in-memory store
	conflictStore := servicesync.NewInMemoryConflictStore()
	conflictResolver := servicesync.NewConflictResolver(db, conflictStore)

	// Initialize change tracker
	changeTracker := servicesync.NewChangeTracker(db)

	s := &SyncService{
		db:               db,
		storage:          storage,
		conflictMode:     ConflictModeAsk,
		conflictResolver: conflictResolver,
		changeTracker:    changeTracker,
		syncQueue:        make(chan SyncTask, 100),
		workers:          workers,
		syncStatus:       make(map[string]*SyncStatus),
	}

	// Start workers
	for i := 0; i < workers; i++ {
		go s.worker()
	}

	return s
}

// PushBuilding pushes local changes to cloud
func (s *SyncService) PushBuilding(ctx context.Context, buildingID string) error {
	logger.Info("Starting push sync for building %s", buildingID)

	// Get local changes since last sync
	status := s.getStatus(buildingID)
	changes, err := s.getLocalChanges(ctx, buildingID, status.LastSync)
	if err != nil {
		return fmt.Errorf("failed to get local changes: %w", err)
	}

	if len(changes) == 0 {
		logger.Info("No changes to push for building %s", buildingID)
		return nil
	}

	// Create sync request
	syncReq := api.SyncRequest{
		BuildingID: buildingID,
		LastSync:   status.LastSync,
		Changes:    changes,
		Metadata: map[string]interface{}{
			"source": "cli",
			"mode":   "push",
		},
	}

	// Serialize and push to storage
	data, err := json.Marshal(syncReq)
	if err != nil {
		return fmt.Errorf("failed to marshal sync request: %w", err)
	}

	key := fmt.Sprintf("sync/%s/push/%d.json", buildingID, time.Now().Unix())
	if err := s.storage.Put(ctx, key, data); err != nil {
		return fmt.Errorf("failed to push to storage: %w", err)
	}

	// Update sync status
	s.updateStatus(buildingID, func(status *SyncStatus) {
		status.LastSync = time.Now()
		status.PendingPush = 0
	})

	logger.Info("Successfully pushed %d changes for building %s", len(changes), buildingID)
	return nil
}

// PullBuilding pulls remote changes from cloud
func (s *SyncService) PullBuilding(ctx context.Context, buildingID string) error {
	logger.Info("Starting pull sync for building %s", buildingID)

	// Get remote changes since last sync
	status := s.getStatus(buildingID)
	changes, err := s.getRemoteChanges(ctx, buildingID, status.LastSync)
	if err != nil {
		return fmt.Errorf("failed to get remote changes: %w", err)
	}

	if len(changes) == 0 {
		logger.Info("No changes to pull for building %s", buildingID)
		return nil
	}

	// Apply remote changes
	conflicts, err := s.applyRemoteChanges(ctx, buildingID, changes)
	if err != nil {
		return fmt.Errorf("failed to apply remote changes: %w", err)
	}

	// Update sync status
	s.updateStatus(buildingID, func(status *SyncStatus) {
		status.LastSync = time.Now()
		status.PendingPull = 0
		status.Conflicts = conflicts
	})

	if len(conflicts) > 0 {
		logger.Warn("Pull completed with %d conflicts for building %s", len(conflicts), buildingID)
	} else {
		logger.Info("Successfully pulled %d changes for building %s", len(changes), buildingID)
	}

	return nil
}

// SyncBuilding performs a full two-way sync
func (s *SyncService) SyncBuilding(ctx context.Context, buildingID string) error {
	logger.Info("Starting full sync for building %s", buildingID)

	// Pull first to get latest changes
	if err := s.PullBuilding(ctx, buildingID); err != nil {
		logger.Error("Pull failed during sync: %v", err)
		// Continue with push even if pull fails
	}

	// Then push local changes
	if err := s.PushBuilding(ctx, buildingID); err != nil {
		return fmt.Errorf("push failed during sync: %w", err)
	}

	logger.Info("Full sync completed for building %s", buildingID)
	return nil
}

// GetSyncStatus returns the sync status for a building
func (s *SyncService) GetSyncStatus(buildingID string) *SyncStatus {
	return s.getStatus(buildingID)
}

// ResolveConflict resolves a sync conflict
func (s *SyncService) ResolveConflict(ctx context.Context, conflictID string, resolution string, userID string) error {
	// Map resolution string to ResolutionType
	var resType servicesync.ResolutionType
	switch resolution {
	case "local":
		resType = servicesync.ResolutionTypeLocal
	case "remote":
		resType = servicesync.ResolutionTypeRemote
	case "merge":
		resType = servicesync.ResolutionTypeMerge
	case "defer":
		resType = servicesync.ResolutionTypeDefer
	default:
		return fmt.Errorf("invalid resolution type: %s", resolution)
	}

	// Use the conflict resolver
	return s.conflictResolver.ResolveConflict(ctx, conflictID, resType, userID)
}

// SetConflictMode sets the conflict resolution mode
func (s *SyncService) SetConflictMode(mode ConflictResolutionMode) {
	s.conflictMode = mode
	logger.Info("Conflict resolution mode set to: %s", mode)
}

// QueueSync queues a sync task
func (s *SyncService) QueueSync(task SyncTask) {
	select {
	case s.syncQueue <- task:
		logger.Debug("Queued sync task for building %s", task.BuildingID)
	default:
		logger.Warn("Sync queue full, dropping task for building %s", task.BuildingID)
	}
}

// worker processes sync tasks from the queue
func (s *SyncService) worker() {
	for task := range s.syncQueue {
		ctx := context.Background()
		var err error

		switch task.Type {
		case SyncTypePush:
			err = s.PushBuilding(ctx, task.BuildingID)
		case SyncTypePull:
			err = s.PullBuilding(ctx, task.BuildingID)
		case SyncTypeFull:
			err = s.SyncBuilding(ctx, task.BuildingID)
		}

		if task.Callback != nil {
			task.Callback(err)
		}
	}
}

// getLocalChanges retrieves local changes since last sync
func (s *SyncService) getLocalChanges(ctx context.Context, buildingID string, since time.Time) ([]api.Change, error) {
	// Use change tracker to get changes
	trackedChanges, err := s.changeTracker.GetChanges(ctx, since, "")
	if err != nil {
		logger.Warn("Failed to get tracked changes: %v", err)
		// Fall back to database query
		return s.getLocalChangesFromDB(ctx, buildingID, since)
	}

	// Filter changes for this building
	var changes []api.Change
	for _, change := range trackedChanges {
		// Include building changes and related entities
		if change.Entity == "building" && change.EntityID == buildingID {
			changes = append(changes, *change)
		} else if change.Entity == "equipment" || change.Entity == "room" {
			// Check if equipment/room belongs to this building
			// This would require additional context in the change data
			if buildingRef, ok := change.Data["building_id"].(string); ok && buildingRef == buildingID {
				changes = append(changes, *change)
			}
		}
	}

	return changes, nil
}

// getLocalChangesFromDB fallback method to get changes from database
func (s *SyncService) getLocalChangesFromDB(ctx context.Context, buildingID string, since time.Time) ([]api.Change, error) {
	changes := []api.Change{}

	// Query database for changes
	building, err := s.db.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return nil, err
	}

	if building != nil && building.UpdatedAt != nil && building.UpdatedAt.After(since) {
		change := api.Change{
			ID:        fmt.Sprintf("%s-%d", buildingID, time.Now().Unix()),
			Type:      "update",
			Entity:    "building",
			EntityID:  buildingID,
			Timestamp: *building.UpdatedAt,
			Data: map[string]interface{}{
				"name":      building.Name,
				"rooms":     len(building.Rooms),
				"equipment": len(building.Equipment),
				"level":     building.Level,
			},
		}
		changes = append(changes, change)
	}

	return changes, nil
}

// getRemoteChanges retrieves remote changes since last sync
func (s *SyncService) getRemoteChanges(ctx context.Context, buildingID string, since time.Time) ([]api.Change, error) {
	changes := []api.Change{}

	// List sync files from storage
	prefix := fmt.Sprintf("sync/%s/", buildingID)
	keys, err := s.storage.List(ctx, prefix)
	if err != nil {
		return nil, err
	}

	for _, key := range keys {
		// Get sync data
		data, err := s.storage.Get(ctx, key)
		if err != nil {
			logger.Warn("Failed to get sync data from %s: %v", key, err)
			continue
		}

		var syncReq api.SyncRequest
		if err := json.Unmarshal(data, &syncReq); err != nil {
			logger.Warn("Failed to unmarshal sync data from %s: %v", key, err)
			continue
		}

		// Add changes if they're newer than last sync
		for _, change := range syncReq.Changes {
			if change.Timestamp.After(since) {
				changes = append(changes, change)
			}
		}
	}

	return changes, nil
}

// applyRemoteChanges applies remote changes to local database
func (s *SyncService) applyRemoteChanges(ctx context.Context, buildingID string, remoteChanges []api.Change) ([]api.Conflict, error) {
	// Get local changes to check for conflicts
	status := s.getStatus(buildingID)
	localChanges, err := s.getLocalChanges(ctx, buildingID, status.LastSync)
	if err != nil {
		logger.Warn("Failed to get local changes for conflict detection: %v", err)
		// Continue without conflict detection
		localChanges = []api.Change{}
	}

	// Detect conflicts using the conflict resolver
	detectedConflicts, err := s.conflictResolver.DetectConflicts(ctx, localChanges, remoteChanges)
	if err != nil {
		logger.Warn("Failed to detect conflicts: %v", err)
	}

	// Convert detected conflicts to API conflicts
	conflicts := []api.Conflict{}
	for _, conflict := range detectedConflicts {
		conflicts = append(conflicts, *conflict)
	}

	// Apply non-conflicting changes
	for _, change := range remoteChanges {
		switch change.Entity {
		case "building":
			if err := s.applyBuildingChange(ctx, change); err != nil {
				logger.Warn("Failed to apply building change: %v", err)
				// Create conflict record
				conflict := api.Conflict{
					ID:         fmt.Sprintf("conflict-%d", time.Now().UnixNano()),
					Entity:     change.Entity,
					EntityID:   change.EntityID,
					RemoteData: change.Data,
					Resolution: string(s.conflictMode),
				}
				conflicts = append(conflicts, conflict)
			}
		case "equipment":
			if !s.isConflicting(change, detectedConflicts) {
				if err := s.applyEquipmentChange(ctx, change); err != nil {
					logger.Warn("Failed to apply equipment change: %v", err)
				}
			}
		case "room":
			if !s.isConflicting(change, detectedConflicts) {
				if err := s.applyRoomChange(ctx, change); err != nil {
					logger.Warn("Failed to apply room change: %v", err)
				}
			}
		}
	}

	return conflicts, nil
}

// applyBuildingChange applies a building change
func (s *SyncService) applyBuildingChange(ctx context.Context, change api.Change) error {
	// Get current building
	building, err := s.db.GetFloorPlan(ctx, change.EntityID)
	if err != nil {
		return err
	}

	if building == nil && change.Type != "create" {
		return fmt.Errorf("building not found: %s", change.EntityID)
	}

	switch change.Type {
	case "create":
		// Create new building
		newBuilding := &models.FloorPlan{
			Name: change.EntityID,
		}
		return s.db.SaveFloorPlan(ctx, newBuilding)

	case "update":
		// Update existing building
		if name, ok := change.Data["name"].(string); ok {
			building.Name = name
		}
		if level, ok := change.Data["level"].(float64); ok {
			building.Level = int(level)
		}
		now := time.Now()
		building.UpdatedAt = &now
		return s.db.SaveFloorPlan(ctx, building)

	case "delete":
		// Delete building
		return s.db.DeleteFloorPlan(ctx, change.EntityID)

	default:
		return fmt.Errorf("unknown change type: %s", change.Type)
	}
}

// applyEquipmentChange applies an equipment change
func (s *SyncService) applyEquipmentChange(ctx context.Context, change api.Change) error {
	switch change.Type {
	case "create":
		equipment := &models.Equipment{
			ID: change.EntityID,
		}
		// Apply data fields
		if name, ok := change.Data["name"].(string); ok {
			equipment.Name = name
		}
		if eType, ok := change.Data["type"].(string); ok {
			equipment.Type = eType
		}
		if roomID, ok := change.Data["room_id"].(string); ok {
			equipment.RoomID = roomID
		}
		if status, ok := change.Data["status"].(string); ok {
			equipment.Status = status
		}
		if model, ok := change.Data["model"].(string); ok {
			equipment.Model = model
		}
		if serial, ok := change.Data["serial"].(string); ok {
			equipment.Serial = serial
		}
		return s.db.SaveEquipment(ctx, equipment)

	case "update":
		equipment, err := s.db.GetEquipment(ctx, change.EntityID)
		if err != nil {
			return fmt.Errorf("failed to get equipment: %w", err)
		}
		// Apply updates
		if name, ok := change.Data["name"].(string); ok {
			equipment.Name = name
		}
		if eType, ok := change.Data["type"].(string); ok {
			equipment.Type = eType
		}
		if roomID, ok := change.Data["room_id"].(string); ok {
			equipment.RoomID = roomID
		}
		if status, ok := change.Data["status"].(string); ok {
			equipment.Status = status
		}
		if model, ok := change.Data["model"].(string); ok {
			equipment.Model = model
		}
		if serial, ok := change.Data["serial"].(string); ok {
			equipment.Serial = serial
		}
		return s.db.UpdateEquipment(ctx, equipment)

	case "delete":
		return s.db.DeleteEquipment(ctx, change.EntityID)

	default:
		return fmt.Errorf("unknown change type: %s", change.Type)
	}
}

// applyRoomChange applies a room change
func (s *SyncService) applyRoomChange(ctx context.Context, change api.Change) error {
	switch change.Type {
	case "create":
		room := &models.Room{
			ID: change.EntityID,
		}
		// Apply data fields
		if name, ok := change.Data["name"].(string); ok {
			room.Name = name
		}
		if floorPlanID, ok := change.Data["floor_plan_id"].(string); ok {
			room.FloorPlanID = floorPlanID
		}
		return s.db.SaveRoom(ctx, room)

	case "update":
		room, err := s.db.GetRoom(ctx, change.EntityID)
		if err != nil {
			return fmt.Errorf("failed to get room: %w", err)
		}
		// Apply updates
		if name, ok := change.Data["name"].(string); ok {
			room.Name = name
		}
		if floorPlanID, ok := change.Data["floor_plan_id"].(string); ok {
			room.FloorPlanID = floorPlanID
		}
		return s.db.UpdateRoom(ctx, room)

	case "delete":
		return s.db.DeleteRoom(ctx, change.EntityID)

	default:
		return fmt.Errorf("unknown change type: %s", change.Type)
	}
}

// getStatus returns the sync status for a building
func (s *SyncService) getStatus(buildingID string) *SyncStatus {
	s.mu.RLock()
	status, exists := s.syncStatus[buildingID]
	s.mu.RUnlock()

	if !exists {
		status = &SyncStatus{
			BuildingID: buildingID,
			LastSync:   time.Time{},
		}
		s.mu.Lock()
		s.syncStatus[buildingID] = status
		s.mu.Unlock()
	}

	return status
}

// updateStatus updates the sync status for a building
func (s *SyncService) updateStatus(buildingID string, update func(*SyncStatus)) {
	s.mu.Lock()
	defer s.mu.Unlock()

	status, exists := s.syncStatus[buildingID]
	if !exists {
		status = &SyncStatus{
			BuildingID: buildingID,
		}
		s.syncStatus[buildingID] = status
	}

	update(status)
}

// isConflicting checks if a change is part of a conflict
func (s *SyncService) isConflicting(change api.Change, conflicts []*api.Conflict) bool {
	for _, conflict := range conflicts {
		if conflict.Entity == change.Entity && conflict.EntityID == change.EntityID {
			return true
		}
	}
	return false
}

// TrackBuildingChange tracks a building modification for sync
func (s *SyncService) TrackBuildingChange(ctx context.Context, building *models.FloorPlan, changeType string) {
	data := map[string]interface{}{
		"name":        building.Name,
		"building_id": building.Building,
		"level":       building.Level,
	}

	switch changeType {
	case "create":
		s.changeTracker.TrackCreate(ctx, "building", building.ID, data)
	case "update":
		version, _ := s.changeTracker.GetLatestVersion(ctx, building.ID)
		s.changeTracker.TrackUpdate(ctx, "building", building.ID, data, version)
	case "delete":
		s.changeTracker.TrackDelete(ctx, "building", building.ID)
	}
}

// TrackEquipmentChange tracks an equipment modification for sync
func (s *SyncService) TrackEquipmentChange(ctx context.Context, equipment *models.Equipment, buildingID, changeType string) {
	data := map[string]interface{}{
		"name":        equipment.Name,
		"type":        equipment.Type,
		"room_id":     equipment.RoomID,
		"building_id": buildingID,
		"status":      equipment.Status,
		"model":       equipment.Model,
		"serial":      equipment.Serial,
	}

	switch changeType {
	case "create":
		s.changeTracker.TrackCreate(ctx, "equipment", equipment.ID, data)
	case "update":
		version, _ := s.changeTracker.GetLatestVersion(ctx, equipment.ID)
		s.changeTracker.TrackUpdate(ctx, "equipment", equipment.ID, data, version)
	case "delete":
		s.changeTracker.TrackDelete(ctx, "equipment", equipment.ID)
	}
}

// TrackRoomChange tracks a room modification for sync
func (s *SyncService) TrackRoomChange(ctx context.Context, room *models.Room, buildingID, changeType string) {
	data := map[string]interface{}{
		"name":          room.Name,
		"floor_plan_id": room.FloorPlanID,
		"building_id":   buildingID,
	}

	switch changeType {
	case "create":
		s.changeTracker.TrackCreate(ctx, "room", room.ID, data)
	case "update":
		version, _ := s.changeTracker.GetLatestVersion(ctx, room.ID)
		s.changeTracker.TrackUpdate(ctx, "room", room.ID, data, version)
	case "delete":
		s.changeTracker.TrackDelete(ctx, "room", room.ID)
	}
}
