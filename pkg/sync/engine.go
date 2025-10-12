// Package sync provides the main synchronization engine for ArxOS.
// This engine orchestrates the synchronization process between local and remote data stores.
package sync

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/pkg/errors"
)

// SyncEngine orchestrates the synchronization process
type SyncEngine struct {
	resolver      ConflictResolver
	detector      *ConflictDetector
	changeStore   ChangeStore
	conflictStore ConflictStore
	metrics       SyncMetrics
	config        *SyncConfig
}

// SyncConfig holds configuration for the sync engine
type SyncConfig struct {
	// Maximum number of retries for failed operations
	MaxRetries int

	// Timeout for sync operations
	Timeout time.Duration

	// Batch size for processing changes
	BatchSize int

	// Whether to use vector clocks for conflict detection
	UseVectorClocks bool

	// Default conflict resolution strategy
	DefaultStrategy ConflictResolutionStrategy

	// Whether to enable automatic conflict resolution
	AutoResolveConflicts bool
}

// DefaultSyncConfig returns a default sync configuration
func DefaultSyncConfig() *SyncConfig {
	return &SyncConfig{
		MaxRetries:           3,
		Timeout:              30 * time.Second,
		BatchSize:            100,
		UseVectorClocks:      true,
		DefaultStrategy:      StrategyLastWriteWins,
		AutoResolveConflicts: true,
	}
}

// ChangeStore defines the interface for storing and retrieving changes
type ChangeStore interface {
	// StoreChange stores a change
	StoreChange(ctx context.Context, change *Change) error

	// GetChanges retrieves changes for a building since a timestamp
	GetChanges(ctx context.Context, buildingID string, since time.Time) ([]Change, error)

	// GetChange retrieves a specific change by ID
	GetChange(ctx context.Context, changeID string) (*Change, error)

	// DeleteChange deletes a change
	DeleteChange(ctx context.Context, changeID string) error

	// GetLastSyncTime gets the last sync time for a building
	GetLastSyncTime(ctx context.Context, buildingID string) (time.Time, error)

	// SetLastSyncTime sets the last sync time for a building
	SetLastSyncTime(ctx context.Context, buildingID string, timestamp time.Time) error
}

// ConflictStore defines the interface for storing and retrieving conflicts
type ConflictStore interface {
	// StoreConflict stores a conflict
	StoreConflict(ctx context.Context, conflict *Conflict) error

	// GetConflicts retrieves unresolved conflicts for a building
	GetConflicts(ctx context.Context, buildingID string) ([]Conflict, error)

	// GetConflict retrieves a specific conflict by ID
	GetConflict(ctx context.Context, conflictID string) (*Conflict, error)

	// ResolveConflict marks a conflict as resolved
	ResolveConflict(ctx context.Context, conflictID string, resolution *ConflictResolution) error

	// DeleteConflict deletes a conflict
	DeleteConflict(ctx context.Context, conflictID string) error
}

// SyncMetrics defines the interface for sync metrics
type SyncMetrics interface {
	// RecordSyncOperation records a sync operation
	RecordSyncOperation(ctx context.Context, operation string, duration time.Duration, success bool)

	// RecordConflictDetected records a conflict detection
	RecordConflictDetected(ctx context.Context, conflictType string)

	// RecordConflictResolved records a conflict resolution
	RecordConflictResolved(ctx context.Context, strategy ConflictResolutionStrategy, duration time.Duration)

	// RecordChangesApplied records applied changes
	RecordChangesApplied(ctx context.Context, count int)
}

// NewSyncEngine creates a new sync engine
func NewSyncEngine(
	resolver ConflictResolver,
	changeStore ChangeStore,
	conflictStore ConflictStore,
	metrics SyncMetrics,
	config *SyncConfig,
) *SyncEngine {
	if config == nil {
		config = DefaultSyncConfig()
	}

	detector := NewConflictDetector(config.UseVectorClocks)

	return &SyncEngine{
		resolver:      resolver,
		detector:      detector,
		changeStore:   changeStore,
		conflictStore: conflictStore,
		metrics:       metrics,
		config:        config,
	}
}

// Sync performs synchronization between local and remote data
func (se *SyncEngine) Sync(ctx context.Context, request *SyncRequest) (*SyncResponse, error) {
	startTime := time.Now()
	defer func() {
		duration := time.Since(startTime)
		se.metrics.RecordSyncOperation(ctx, "sync", duration, true)
	}()

	// Create context with timeout
	ctx, cancel := context.WithTimeout(ctx, se.config.Timeout)
	defer cancel()

	// Get local changes since last sync
	localChanges, err := se.changeStore.GetChanges(ctx, request.BuildingID, request.LastSync)
	if err != nil {
		se.metrics.RecordSyncOperation(ctx, "sync", time.Since(startTime), false)
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to get local changes")
	}

	// Detect conflicts
	conflicts, err := se.detector.DetectConflicts(ctx, localChanges, request.Changes)
	if err != nil {
		se.metrics.RecordSyncOperation(ctx, "sync", time.Since(startTime), false)
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to detect conflicts")
	}

	// Record conflicts
	for i := range conflicts {
		se.metrics.RecordConflictDetected(ctx, conflicts[i].ConflictType)
		if err := se.conflictStore.StoreConflict(ctx, &conflicts[i]); err != nil {
			se.metrics.RecordSyncOperation(ctx, "sync", time.Since(startTime), false)
			return nil, errors.Wrap(err, errors.CodeInternal, "failed to store conflict")
		}
	}

	// Process changes in batches
	response := &SyncResponse{
		Success:         true,
		AppliedChanges:  []Change{},
		RejectedChanges: []RejectedChange{},
		Conflicts:       conflicts,
	}

	// Apply remote changes
	appliedChanges, rejectedChanges, err := se.applyRemoteChanges(ctx, request.Changes, conflicts)
	if err != nil {
		se.metrics.RecordSyncOperation(ctx, "sync", time.Since(startTime), false)
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to apply remote changes")
	}

	response.AppliedChanges = appliedChanges
	response.RejectedChanges = rejectedChanges

	// Update last sync time
	if err := se.changeStore.SetLastSyncTime(ctx, request.BuildingID, time.Now()); err != nil {
		se.metrics.RecordSyncOperation(ctx, "sync", time.Since(startTime), false)
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to update last sync time")
	}

	// Record metrics
	se.metrics.RecordChangesApplied(ctx, len(appliedChanges))

	return response, nil
}

// applyRemoteChanges applies remote changes, handling conflicts
func (se *SyncEngine) applyRemoteChanges(ctx context.Context, remoteChanges []Change, conflicts []Conflict) ([]Change, []RejectedChange, error) {
	var appliedChanges []Change
	var rejectedChanges []RejectedChange

	// Create conflict map for quick lookup
	conflictMap := make(map[string]*Conflict)
	for i := range conflicts {
		conflictMap[conflicts[i].EntityID] = &conflicts[i]
	}

	// Process changes in batches
	for i := 0; i < len(remoteChanges); i += se.config.BatchSize {
		end := i + se.config.BatchSize
		if end > len(remoteChanges) {
			end = len(remoteChanges)
		}

		batch := remoteChanges[i:end]
		batchApplied, batchRejected, err := se.processBatch(ctx, batch, conflictMap)
		if err != nil {
			return appliedChanges, rejectedChanges, err
		}

		appliedChanges = append(appliedChanges, batchApplied...)
		rejectedChanges = append(rejectedChanges, batchRejected...)
	}

	return appliedChanges, rejectedChanges, nil
}

// processBatch processes a batch of changes
func (se *SyncEngine) processBatch(ctx context.Context, changes []Change, conflictMap map[string]*Conflict) ([]Change, []RejectedChange, error) {
	var appliedChanges []Change
	var rejectedChanges []RejectedChange

	for _, change := range changes {
		// Check if there's a conflict for this entity
		if conflict, hasConflict := conflictMap[change.EntityID]; hasConflict {
			// Try to resolve conflict automatically if enabled
			if se.config.AutoResolveConflicts && se.resolver.CanAutoResolve(conflict) {
				resolution, err := se.resolver.ResolveConflict(ctx, conflict)
				if err != nil {
					rejectedChanges = append(rejectedChanges, RejectedChange{
						Change: change,
						Reason: fmt.Sprintf("failed to resolve conflict: %v", err),
					})
					continue
				}

				// Apply the resolved change
				resolvedChange := *resolution.AppliedChange
				if err := se.changeStore.StoreChange(ctx, &resolvedChange); err != nil {
					rejectedChanges = append(rejectedChanges, RejectedChange{
						Change: change,
						Reason: fmt.Sprintf("failed to store resolved change: %v", err),
					})
					continue
				}

				// Mark conflict as resolved
				if err := se.conflictStore.ResolveConflict(ctx, conflict.ID, resolution); err != nil {
					// Log error but don't fail the sync
					// NOTE: Logging handled by infrastructure logger when wired
				}

				appliedChanges = append(appliedChanges, resolvedChange)
				se.metrics.RecordConflictResolved(ctx, resolution.Resolution, time.Since(time.Now()))
			} else {
				// Conflict requires manual resolution
				rejectedChanges = append(rejectedChanges, RejectedChange{
					Change: change,
					Reason: "conflict requires manual resolution",
				})
			}
		} else {
			// No conflict, apply change directly
			if err := se.changeStore.StoreChange(ctx, &change); err != nil {
				rejectedChanges = append(rejectedChanges, RejectedChange{
					Change: change,
					Reason: fmt.Sprintf("failed to store change: %v", err),
				})
				continue
			}

			appliedChanges = append(appliedChanges, change)
		}
	}

	return appliedChanges, rejectedChanges, nil
}

// ResolveConflict manually resolves a conflict
func (se *SyncEngine) ResolveConflict(ctx context.Context, conflictID string, resolution *ConflictResolution) error {
	startTime := time.Now()
	defer func() {
		duration := time.Since(startTime)
		se.metrics.RecordConflictResolved(ctx, resolution.Resolution, duration)
	}()

	// Get the conflict
	_, err := se.conflictStore.GetConflict(ctx, conflictID)
	if err != nil {
		return errors.Wrap(err, errors.CodeNotFound, "conflict not found")
	}

	// Apply the resolved change
	if resolution.AppliedChange != nil {
		if err := se.changeStore.StoreChange(ctx, resolution.AppliedChange); err != nil {
			return errors.Wrap(err, errors.CodeInternal, "failed to store resolved change")
		}
	}

	// Mark conflict as resolved
	if err := se.conflictStore.ResolveConflict(ctx, conflictID, resolution); err != nil {
		return errors.Wrap(err, errors.CodeInternal, "failed to mark conflict as resolved")
	}

	return nil
}

// GetUnresolvedConflicts retrieves unresolved conflicts for a building
func (se *SyncEngine) GetUnresolvedConflicts(ctx context.Context, buildingID string) ([]Conflict, error) {
	return se.conflictStore.GetConflicts(ctx, buildingID)
}

// GetSyncStatus returns the sync status for a building
func (se *SyncEngine) GetSyncStatus(ctx context.Context, buildingID string) (*SyncStatus, error) {
	lastSync, err := se.changeStore.GetLastSyncTime(ctx, buildingID)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to get last sync time")
	}

	conflicts, err := se.conflictStore.GetConflicts(ctx, buildingID)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to get conflicts")
	}

	return &SyncStatus{
		BuildingID:          buildingID,
		LastSyncTime:        lastSync,
		UnresolvedConflicts: len(conflicts),
		IsInSync:            len(conflicts) == 0,
		LastUpdated:         time.Now(),
	}, nil
}

// SyncStatus represents the synchronization status of a building
type SyncStatus struct {
	BuildingID          string    `json:"building_id"`
	LastSyncTime        time.Time `json:"last_sync_time"`
	UnresolvedConflicts int       `json:"unresolved_conflicts"`
	IsInSync            bool      `json:"is_in_sync"`
	LastUpdated         time.Time `json:"last_updated"`
}

// RetryableError represents an error that can be retried
type RetryableError struct {
	Err        error
	RetryAfter time.Duration
}

func (re *RetryableError) Error() string {
	return re.Err.Error()
}

// IsRetryable determines if an error is retryable
func IsRetryable(err error) bool {
	_, ok := err.(*RetryableError)
	return ok
}

// WithRetry executes a function with retry logic
func (se *SyncEngine) WithRetry(ctx context.Context, operation string, fn func() error) error {
	var lastErr error

	for attempt := 0; attempt <= se.config.MaxRetries; attempt++ {
		if attempt > 0 {
			// Wait before retry
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(time.Duration(attempt) * time.Second):
			}
		}

		err := fn()
		if err == nil {
			return nil
		}

		lastErr = err
		if !IsRetryable(err) {
			break
		}
	}

	return errors.Wrap(lastErr, errors.CodeInternal, fmt.Sprintf("operation %s failed after %d retries", operation, se.config.MaxRetries))
}
