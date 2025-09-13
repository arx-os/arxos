package services

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/api"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/storage"
	"github.com/joelpate/arxos/pkg/models"
)

// SyncService handles synchronization between local and cloud storage
type SyncService struct {
	db           database.DB
	storage      storage.Backend
	conflictMode ConflictResolutionMode
	syncQueue    chan SyncTask
	workers      int
	mu           sync.RWMutex
	syncStatus   map[string]*SyncStatus
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
	BuildingID   string
	LastSync     time.Time
	InProgress   bool
	PendingPush  int
	PendingPull  int
	Conflicts    []api.Conflict
	Error        error
}

// NewSyncService creates a new sync service
func NewSyncService(db database.DB, storage storage.Backend, workers int) *SyncService {
	if workers <= 0 {
		workers = 4
	}
	
	s := &SyncService{
		db:           db,
		storage:      storage,
		conflictMode: ConflictModeAsk,
		syncQueue:    make(chan SyncTask, 100),
		workers:      workers,
		syncStatus:   make(map[string]*SyncStatus),
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
func (s *SyncService) ResolveConflict(ctx context.Context, conflictID string, resolution string) error {
	// TODO: Implement conflict resolution
	logger.Info("Resolving conflict %s with resolution: %s", conflictID, resolution)
	return nil
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
	changes := []api.Change{}
	
	// Query database for changes
	// This is a simplified implementation - real version would track changes in audit table
	building, err := s.db.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return nil, err
	}
	
	if building != nil && building.UpdatedAt.After(since) {
		change := api.Change{
			ID:        fmt.Sprintf("%s-%d", buildingID, time.Now().Unix()),
			Type:      "update",
			Entity:    "building",
			EntityID:  buildingID,
			Timestamp: building.UpdatedAt,
			Data: map[string]interface{}{
				"name":        building.Name,
				"rooms":       len(building.Rooms),
				"equipment":   len(building.Equipment),
				"level": building.Level,
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
func (s *SyncService) applyRemoteChanges(ctx context.Context, buildingID string, changes []api.Change) ([]api.Conflict, error) {
	conflicts := []api.Conflict{}
	
	for _, change := range changes {
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
			if err := s.applyEquipmentChange(ctx, change); err != nil {
				logger.Warn("Failed to apply equipment change: %v", err)
			}
		case "room":
			if err := s.applyRoomChange(ctx, change); err != nil {
				logger.Warn("Failed to apply room change: %v", err)
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
		building.UpdatedAt = time.Now()
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
	// TODO: Implement equipment change application
	logger.Debug("Applying equipment change: %+v", change)
	return nil
}

// applyRoomChange applies a room change
func (s *SyncService) applyRoomChange(ctx context.Context, change api.Change) error {
	// TODO: Implement room change application
	logger.Debug("Applying room change: %+v", change)
	return nil
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