// Package sync provides utility functions for synchronization operations.
package sync

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"sort"
	"time"
)

// ChangeComparator compares two changes for ordering
type ChangeComparator func(a, b Change) bool

// ByTimestamp compares changes by timestamp
func ByTimestamp(a, b Change) bool {
	return a.Timestamp.Before(b.Timestamp)
}

// ByVersion compares changes by version
func ByVersion(a, b Change) bool {
	return a.Version < b.Version
}

// ByEntityID compares changes by entity ID
func ByEntityID(a, b Change) bool {
	return a.EntityID < b.EntityID
}

// SortChanges sorts changes using the provided comparator
func SortChanges(changes []Change, comparator ChangeComparator) {
	sort.Slice(changes, func(i, j int) bool {
		return comparator(changes[i], changes[j])
	})
}

// DeduplicateChanges removes duplicate changes based on ID
func DeduplicateChanges(changes []Change) []Change {
	seen := make(map[string]bool)
	var result []Change

	for _, change := range changes {
		if !seen[change.ID] {
			seen[change.ID] = true
			result = append(result, change)
		}
	}

	return result
}

// FilterChangesByType filters changes by type
func FilterChangesByType(changes []Change, changeType string) []Change {
	var result []Change
	for _, change := range changes {
		if change.Type == changeType {
			result = append(result, change)
		}
	}
	return result
}

// FilterChangesByEntity filters changes by entity
func FilterChangesByEntity(changes []Change, entity string) []Change {
	var result []Change
	for _, change := range changes {
		if change.Entity == entity {
			result = append(result, change)
		}
	}
	return result
}

// FilterChangesByEntityID filters changes by entity ID
func FilterChangesByEntityID(changes []Change, entityID string) []Change {
	var result []Change
	for _, change := range changes {
		if change.EntityID == entityID {
			result = append(result, change)
		}
	}
	return result
}

// FilterChangesByUser filters changes by user ID
func FilterChangesByUser(changes []Change, userID string) []Change {
	var result []Change
	for _, change := range changes {
		if change.UserID == userID {
			result = append(result, change)
		}
	}
	return result
}

// FilterChangesSince filters changes since a timestamp
func FilterChangesSince(changes []Change, since time.Time) []Change {
	var result []Change
	for _, change := range changes {
		if change.Timestamp.After(since) {
			result = append(result, change)
		}
	}
	return result
}

// GroupChangesByEntity groups changes by entity ID
func GroupChangesByEntity(changes []Change) map[string][]Change {
	groups := make(map[string][]Change)
	for _, change := range changes {
		groups[change.EntityID] = append(groups[change.EntityID], change)
	}
	return groups
}

// GroupChangesByType groups changes by type
func GroupChangesByType(changes []Change) map[string][]Change {
	groups := make(map[string][]Change)
	for _, change := range changes {
		groups[change.Type] = append(groups[change.Type], change)
	}
	return groups
}

// GroupChangesByUser groups changes by user ID
func GroupChangesByUser(changes []Change) map[string][]Change {
	groups := make(map[string][]Change)
	for _, change := range changes {
		groups[change.UserID] = append(groups[change.UserID], change)
	}
	return groups
}

// CalculateChangeHash calculates a hash for a change
func CalculateChangeHash(change Change) (string, error) {
	// Create a copy without timestamp for consistent hashing
	changeCopy := change
	changeCopy.Timestamp = time.Time{}

	data, err := json.Marshal(changeCopy)
	if err != nil {
		return "", err
	}

	hash := sha256.Sum256(data)
	return fmt.Sprintf("%x", hash), nil
}

// ValidateChange validates a change
func ValidateChange(change Change) error {
	if change.ID == "" {
		return fmt.Errorf("change ID is required")
	}
	if change.Type == "" {
		return fmt.Errorf("change type is required")
	}
	if change.Entity == "" {
		return fmt.Errorf("change entity is required")
	}
	if change.EntityID == "" {
		return fmt.Errorf("change entity ID is required")
	}
	if change.UserID == "" {
		return fmt.Errorf("change user ID is required")
	}
	if change.Timestamp.IsZero() {
		return fmt.Errorf("change timestamp is required")
	}

	// Validate change type
	validTypes := []string{"create", "update", "delete"}
	if !contains(validTypes, change.Type) {
		return fmt.Errorf("invalid change type: %s", change.Type)
	}

	return nil
}

// ValidateConflict validates a conflict
func ValidateConflict(conflict Conflict) error {
	if conflict.ID == "" {
		return fmt.Errorf("conflict ID is required")
	}
	if conflict.Entity == "" {
		return fmt.Errorf("conflict entity is required")
	}
	if conflict.EntityID == "" {
		return fmt.Errorf("conflict entity ID is required")
	}
	if conflict.ConflictType == "" {
		return fmt.Errorf("conflict type is required")
	}
	if conflict.CreatedAt.IsZero() {
		return fmt.Errorf("conflict created at is required")
	}

	return nil
}

// CreateChange creates a new change with generated ID
func CreateChange(changeType, entity, entityID, userID string, data map[string]any) Change {
	return Change{
		ID:        generateChangeID(),
		Type:      changeType,
		Entity:    entity,
		EntityID:  entityID,
		Data:      data,
		Timestamp: time.Now(),
		UserID:    userID,
		Version:   1,
	}
}

// CreateConflict creates a new conflict
func CreateConflict(entity, entityID, conflictType string, localChange, remoteChange *Change) Conflict {
	return Conflict{
		ID:            generateConflictID(),
		Entity:        entity,
		EntityID:      entityID,
		ConflictType:  conflictType,
		LocalVersion:  localChange.Version,
		RemoteVersion: remoteChange.Version,
		LocalData:     localChange.Data,
		RemoteData:    remoteChange.Data,
		LocalChange:   localChange,
		RemoteChange:  remoteChange,
		CreatedAt:     time.Now(),
	}
}

// MergeChangeData merges data from two changes
func MergeChangeData(change1, change2 Change) map[string]any {
	merged := make(map[string]any)

	// Start with first change data
	for key, value := range change1.Data {
		merged[key] = value
	}

	// Add second change data, preferring newer values
	for key, value := range change2.Data {
		if change2.Timestamp.After(change1.Timestamp) {
			merged[key] = value
		} else if _, exists := merged[key]; !exists {
			merged[key] = value
		}
	}

	return merged
}

// CalculateConflictSeverity calculates the severity of a conflict
func CalculateConflictSeverity(conflict Conflict) ConflictSeverity {
	// Simple severity calculation based on conflict type
	switch conflict.ConflictType {
	case "concurrent_modification":
		return SeverityHigh
	case "data_inconsistency":
		return SeverityMedium
	case "version_mismatch":
		return SeverityLow
	default:
		return SeverityUnknown
	}
}

// ConflictSeverity represents the severity of a conflict
type ConflictSeverity string

const (
	SeverityUnknown  ConflictSeverity = "unknown"
	SeverityLow      ConflictSeverity = "low"
	SeverityMedium   ConflictSeverity = "medium"
	SeverityHigh     ConflictSeverity = "high"
	SeverityCritical ConflictSeverity = "critical"
)

// SyncMetricsData represents sync metrics data
type SyncMetricsData struct {
	TotalSyncs           int64            `json:"total_syncs"`
	SuccessfulSyncs      int64            `json:"successful_syncs"`
	FailedSyncs          int64            `json:"failed_syncs"`
	TotalConflicts       int64            `json:"total_conflicts"`
	ResolvedConflicts    int64            `json:"resolved_conflicts"`
	UnresolvedConflicts  int64            `json:"unresolved_conflicts"`
	AverageSyncTime      time.Duration    `json:"average_sync_time"`
	LastSyncTime         time.Time        `json:"last_sync_time"`
	ConflictTypes        map[string]int64 `json:"conflict_types"`
	ResolutionStrategies map[string]int64 `json:"resolution_strategies"`
}

// CalculateSyncMetrics calculates sync metrics from sync operations
func CalculateSyncMetrics(syncs []SyncResponse, conflicts []Conflict, resolutions []ConflictResolution) SyncMetricsData {
	metrics := SyncMetricsData{
		ConflictTypes:        make(map[string]int64),
		ResolutionStrategies: make(map[string]int64),
	}

	// Calculate sync metrics
	metrics.TotalSyncs = int64(len(syncs))
	for _, sync := range syncs {
		if sync.Success {
			metrics.SuccessfulSyncs++
		} else {
			metrics.FailedSyncs++
		}
	}

	// Calculate conflict metrics
	metrics.TotalConflicts = int64(len(conflicts))
	for _, conflict := range conflicts {
		if conflict.Resolution != "" {
			metrics.ResolvedConflicts++
		} else {
			metrics.UnresolvedConflicts++
		}
		metrics.ConflictTypes[conflict.ConflictType]++
	}

	// Calculate resolution strategy metrics
	for _, resolution := range resolutions {
		metrics.ResolutionStrategies[string(resolution.Resolution)]++
	}

	return metrics
}

// Helper functions

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func generateChangeID() string {
	return fmt.Sprintf("change_%d", time.Now().UnixNano())
}

func generateConflictID() string {
	return fmt.Sprintf("conflict_%d", time.Now().UnixNano())
}

// SyncBatch represents a batch of sync operations
type SyncBatch struct {
	ID         string    `json:"id"`
	BuildingID string    `json:"building_id"`
	Changes    []Change  `json:"changes"`
	CreatedAt  time.Time `json:"created_at"`
	Status     string    `json:"status"` // pending, processing, completed, failed
}

// CreateSyncBatch creates a new sync batch
func CreateSyncBatch(buildingID string, changes []Change) SyncBatch {
	return SyncBatch{
		ID:         generateBatchID(),
		BuildingID: buildingID,
		Changes:    changes,
		CreatedAt:  time.Now(),
		Status:     "pending",
	}
}

func generateBatchID() string {
	return fmt.Sprintf("batch_%d", time.Now().UnixNano())
}

// BatchChanges batches changes into groups of specified size
func BatchChanges(changes []Change, batchSize int) []SyncBatch {
	var batches []SyncBatch
	var currentBatch []Change

	for _, change := range changes {
		currentBatch = append(currentBatch, change)

		if len(currentBatch) >= batchSize {
			batches = append(batches, CreateSyncBatch("", currentBatch))
			currentBatch = []Change{}
		}
	}

	// Add remaining changes as final batch
	if len(currentBatch) > 0 {
		batches = append(batches, CreateSyncBatch("", currentBatch))
	}

	return batches
}
