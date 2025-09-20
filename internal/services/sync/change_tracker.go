package sync

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	syncpkg "github.com/arx-os/arxos/pkg/sync"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
)

// ChangeTracker tracks changes to entities for synchronization
type ChangeTracker struct {
	db         database.DB
	changeLog  *ChangeLog
	mu         sync.RWMutex
	listeners  []ChangeListener
}

// ChangeListener is called when changes occur
type ChangeListener func(change *syncpkg.Change)

// ChangeLog stores change history
type ChangeLog struct {
	mu      sync.RWMutex
	changes map[string][]*syncpkg.Change // entityID -> changes
	byTime  []*syncpkg.Change            // ordered by timestamp
}

// NewChangeTracker creates a new change tracker
func NewChangeTracker(db database.DB) *ChangeTracker {
	return &ChangeTracker{
		db: db,
		changeLog: &ChangeLog{
			changes: make(map[string][]*syncpkg.Change),
			byTime:  make([]*syncpkg.Change, 0),
		},
		listeners: make([]ChangeListener, 0),
	}
}

// TrackCreate tracks creation of an entity
func (ct *ChangeTracker) TrackCreate(ctx context.Context, entityType, entityID string, data map[string]interface{}) error {
	change := &syncpkg.Change{
		ID:        uuid.New().String(),
		Type:      "create",
		Entity:    entityType,
		EntityID:  entityID,
		Timestamp: time.Now(),
		Data:      data,
		Version:   1,
	}

	return ct.recordChange(ctx, change)
}

// TrackUpdate tracks update of an entity
func (ct *ChangeTracker) TrackUpdate(ctx context.Context, entityType, entityID string, data map[string]interface{}, version int) error {
	change := &syncpkg.Change{
		ID:        uuid.New().String(),
		Type:      "update",
		Entity:    entityType,
		EntityID:  entityID,
		Timestamp: time.Now(),
		Data:      data,
		Version:   version + 1,
	}

	return ct.recordChange(ctx, change)
}

// TrackDelete tracks deletion of an entity
func (ct *ChangeTracker) TrackDelete(ctx context.Context, entityType, entityID string) error {
	change := &syncpkg.Change{
		ID:        uuid.New().String(),
		Type:      "delete",
		Entity:    entityType,
		EntityID:  entityID,
		Timestamp: time.Now(),
		Data:      nil,
	}

	return ct.recordChange(ctx, change)
}

// GetChanges retrieves changes since a given timestamp
func (ct *ChangeTracker) GetChanges(ctx context.Context, since time.Time, entityType string) ([]*syncpkg.Change, error) {
	ct.changeLog.mu.RLock()
	defer ct.changeLog.mu.RUnlock()

	var result []*syncpkg.Change
	for _, change := range ct.changeLog.byTime {
		if change.Timestamp.After(since) {
			if entityType == "" || change.Entity == entityType {
				result = append(result, change)
			}
		}
	}

	return result, nil
}

// GetEntityChanges retrieves all changes for a specific entity
func (ct *ChangeTracker) GetEntityChanges(ctx context.Context, entityID string) ([]*syncpkg.Change, error) {
	ct.changeLog.mu.RLock()
	defer ct.changeLog.mu.RUnlock()

	changes, exists := ct.changeLog.changes[entityID]
	if !exists {
		return []*syncpkg.Change{}, nil
	}

	return changes, nil
}

// GetLatestVersion gets the latest version number for an entity
func (ct *ChangeTracker) GetLatestVersion(ctx context.Context, entityID string) (int, error) {
	changes, err := ct.GetEntityChanges(ctx, entityID)
	if err != nil {
		return 0, err
	}

	maxVersion := 0
	for _, change := range changes {
		if change.Version > maxVersion {
			maxVersion = change.Version
		}
	}

	return maxVersion, nil
}

// Subscribe adds a listener for change events
func (ct *ChangeTracker) Subscribe(listener ChangeListener) {
	ct.mu.Lock()
	defer ct.mu.Unlock()
	ct.listeners = append(ct.listeners, listener)
}

// recordChange records a change and notifies listeners
func (ct *ChangeTracker) recordChange(ctx context.Context, change *syncpkg.Change) error {
	// Add to change log
	ct.changeLog.mu.Lock()
	key := fmt.Sprintf("%s:%s", change.Entity, change.EntityID)
	if _, exists := ct.changeLog.changes[key]; !exists {
		ct.changeLog.changes[key] = make([]*syncpkg.Change, 0)
	}
	ct.changeLog.changes[key] = append(ct.changeLog.changes[key], change)
	ct.changeLog.byTime = append(ct.changeLog.byTime, change)
	ct.changeLog.mu.Unlock()

	// Notify listeners
	ct.mu.RLock()
	listeners := make([]ChangeListener, len(ct.listeners))
	copy(listeners, ct.listeners)
	ct.mu.RUnlock()

	for _, listener := range listeners {
		go func(l ChangeListener) {
			defer func() {
				if r := recover(); r != nil {
					logger.Error("Change listener panic: %v", r)
				}
			}()
			l(change)
		}(listener)
	}

	logger.Debug("Tracked change: %s %s %s", change.Type, change.Entity, change.EntityID)
	return nil
}

// PruneOldChanges removes changes older than the specified duration
func (ct *ChangeTracker) PruneOldChanges(ctx context.Context, olderThan time.Duration) error {
	cutoff := time.Now().Add(-olderThan)

	ct.changeLog.mu.Lock()
	defer ct.changeLog.mu.Unlock()

	// Create new slices without old changes
	newByTime := make([]*syncpkg.Change, 0)
	newChanges := make(map[string][]*syncpkg.Change)

	for _, change := range ct.changeLog.byTime {
		if change.Timestamp.After(cutoff) {
			newByTime = append(newByTime, change)

			key := fmt.Sprintf("%s:%s", change.Entity, change.EntityID)
			if _, exists := newChanges[key]; !exists {
				newChanges[key] = make([]*syncpkg.Change, 0)
			}
			newChanges[key] = append(newChanges[key], change)
		}
	}

	pruned := len(ct.changeLog.byTime) - len(newByTime)
	ct.changeLog.byTime = newByTime
	ct.changeLog.changes = newChanges

	logger.Info("Pruned %d old changes", pruned)
	return nil
}

// Clear removes all tracked changes
func (ct *ChangeTracker) Clear(ctx context.Context) error {
	ct.changeLog.mu.Lock()
	defer ct.changeLog.mu.Unlock()

	ct.changeLog.changes = make(map[string][]*syncpkg.Change)
	ct.changeLog.byTime = make([]*syncpkg.Change, 0)

	logger.Info("Cleared all tracked changes")
	return nil
}

// MergeChanges merges multiple changes for the same entity into a single change
func (ct *ChangeTracker) MergeChanges(changes []*syncpkg.Change) *syncpkg.Change {
	if len(changes) == 0 {
		return nil
	}
	if len(changes) == 1 {
		return changes[0]
	}

	// Start with the first change
	merged := &syncpkg.Change{
		ID:        uuid.New().String(),
		Type:      changes[0].Type,
		Entity:    changes[0].Entity,
		EntityID:  changes[0].EntityID,
		Timestamp: changes[0].Timestamp,
		Data:      make(map[string]interface{}),
		Version:   changes[0].Version,
	}

	// Merge data from all changes
	for _, change := range changes {
		// Update type if we see different types
		if change.Type == "delete" {
			merged.Type = "delete"
		} else if change.Type == "create" && merged.Type != "delete" {
			merged.Type = "create"
		}

		// Use latest timestamp
		if change.Timestamp.After(merged.Timestamp) {
			merged.Timestamp = change.Timestamp
		}

		// Use highest version
		if change.Version > merged.Version {
			merged.Version = change.Version
		}

		// Merge data fields
		if change.Data != nil {
			for k, v := range change.Data {
				merged.Data[k] = v
			}
		}
	}

	return merged
}

// GetConflictingChanges finds changes that might conflict with a given change
func (ct *ChangeTracker) GetConflictingChanges(ctx context.Context, change *syncpkg.Change, window time.Duration) ([]*syncpkg.Change, error) {
	// Get all changes for the entity
	key := fmt.Sprintf("%s:%s", change.Entity, change.EntityID)

	ct.changeLog.mu.RLock()
	defer ct.changeLog.mu.RUnlock()

	entityChanges, exists := ct.changeLog.changes[key]
	if !exists {
		return []*syncpkg.Change{}, nil
	}

	// Find changes within the time window
	var conflicts []*syncpkg.Change
	startTime := change.Timestamp.Add(-window)
	endTime := change.Timestamp.Add(window)

	for _, c := range entityChanges {
		if c.ID != change.ID &&
		   c.Timestamp.After(startTime) &&
		   c.Timestamp.Before(endTime) {
			conflicts = append(conflicts, c)
		}
	}

	return conflicts, nil
}