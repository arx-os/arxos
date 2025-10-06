// Package sync provides synchronization algorithms and conflict resolution strategies.
// This package implements various conflict resolution algorithms for distributed
// building data synchronization in ArxOS.
package sync

import (
	"context"
	"fmt"
	"sort"
	"time"

	"github.com/arx-os/arxos/pkg/errors"
)

// ConflictResolutionStrategy defines the strategy for resolving conflicts
type ConflictResolutionStrategy string

const (
	// StrategyLastWriteWins uses the most recent timestamp to resolve conflicts
	StrategyLastWriteWins ConflictResolutionStrategy = "last_write_wins"

	// StrategyFirstWriteWins uses the earliest timestamp to resolve conflicts
	StrategyFirstWriteWins ConflictResolutionStrategy = "first_write_wins"

	// StrategyManual requires manual intervention to resolve conflicts
	StrategyManual ConflictResolutionStrategy = "manual"

	// StrategyMerge attempts to merge non-conflicting fields
	StrategyMerge ConflictResolutionStrategy = "merge"

	// StrategyCustom uses a custom resolution function
	StrategyCustom ConflictResolutionStrategy = "custom"
)

// ConflictResolver defines the interface for conflict resolution
type ConflictResolver interface {
	// ResolveConflict resolves a conflict using the configured strategy
	ResolveConflict(ctx context.Context, conflict *Conflict) (*ConflictResolution, error)

	// CanAutoResolve determines if a conflict can be automatically resolved
	CanAutoResolve(conflict *Conflict) bool

	// GetStrategy returns the resolution strategy
	GetStrategy() ConflictResolutionStrategy
}

// ConflictResolution represents the result of conflict resolution
type ConflictResolution struct {
	ConflictID    string                     `json:"conflict_id"`
	Resolution    ConflictResolutionStrategy `json:"resolution"`
	ResolvedData  map[string]any             `json:"resolved_data"`
	AppliedChange *Change                    `json:"applied_change,omitempty"`
	Reason        string                     `json:"reason"`
	ResolvedBy    string                     `json:"resolved_by"`
	ResolvedAt    time.Time                  `json:"resolved_at"`
}

// SyncAlgorithm defines the interface for synchronization algorithms
type SyncAlgorithm interface {
	// Sync performs synchronization between local and remote data
	Sync(ctx context.Context, request *SyncRequest) (*SyncResponse, error)

	// DetectConflicts identifies conflicts between local and remote changes
	DetectConflicts(ctx context.Context, localChanges, remoteChanges []Change) ([]Conflict, error)

	// ApplyChanges applies changes to the local data store
	ApplyChanges(ctx context.Context, changes []Change) error
}

// VectorClock represents a vector clock for distributed systems
type VectorClock struct {
	NodeID string         `json:"node_id"`
	Clock  map[string]int `json:"clock"`
}

// NewVectorClock creates a new vector clock
func NewVectorClock(nodeID string) *VectorClock {
	return &VectorClock{
		NodeID: nodeID,
		Clock:  make(map[string]int),
	}
}

// Increment increments the clock for the current node
func (vc *VectorClock) Increment() {
	vc.Clock[vc.NodeID]++
}

// Update updates the vector clock with another clock
func (vc *VectorClock) Update(other *VectorClock) {
	for nodeID, value := range other.Clock {
		if vc.Clock[nodeID] < value {
			vc.Clock[nodeID] = value
		}
	}
}

// HappensBefore determines if this clock happens before another
func (vc *VectorClock) HappensBefore(other *VectorClock) bool {
	allNodes := make(map[string]bool)
	for nodeID := range vc.Clock {
		allNodes[nodeID] = true
	}
	for nodeID := range other.Clock {
		allNodes[nodeID] = true
	}

	hasSmaller := false
	hasLarger := false

	for nodeID := range allNodes {
		localValue := vc.Clock[nodeID]
		otherValue := other.Clock[nodeID]

		if localValue < otherValue {
			hasSmaller = true
		} else if localValue > otherValue {
			hasLarger = true
		}
	}

	return hasSmaller && !hasLarger
}

// Concurrent determines if this clock is concurrent with another
func (vc *VectorClock) Concurrent(other *VectorClock) bool {
	return !vc.HappensBefore(other) && !other.HappensBefore(vc)
}

// LastWriteWinsResolver implements the last-write-wins conflict resolution strategy
type LastWriteWinsResolver struct {
	strategy ConflictResolutionStrategy
}

// NewLastWriteWinsResolver creates a new last-write-wins resolver
func NewLastWriteWinsResolver() *LastWriteWinsResolver {
	return &LastWriteWinsResolver{
		strategy: StrategyLastWriteWins,
	}
}

// ResolveConflict resolves conflicts using last-write-wins strategy
func (r *LastWriteWinsResolver) ResolveConflict(ctx context.Context, conflict *Conflict) (*ConflictResolution, error) {
	if !r.CanAutoResolve(conflict) {
		return nil, errors.New(errors.CodeConflict, "conflict cannot be auto-resolved")
	}

	var resolvedData map[string]any
	var appliedChange *Change
	var reason string

	// Compare timestamps
	if conflict.LocalChange.Timestamp.After(conflict.RemoteChange.Timestamp) {
		resolvedData = conflict.LocalData
		appliedChange = conflict.LocalChange
		reason = "local change has later timestamp"
	} else {
		resolvedData = conflict.RemoteData
		appliedChange = conflict.RemoteChange
		reason = "remote change has later timestamp"
	}

	return &ConflictResolution{
		ConflictID:    conflict.ID,
		Resolution:    r.strategy,
		ResolvedData:  resolvedData,
		AppliedChange: appliedChange,
		Reason:        reason,
		ResolvedBy:    "system",
		ResolvedAt:    time.Now(),
	}, nil
}

// CanAutoResolve determines if the conflict can be auto-resolved
func (r *LastWriteWinsResolver) CanAutoResolve(conflict *Conflict) bool {
	return conflict.LocalChange != nil && conflict.RemoteChange != nil
}

// GetStrategy returns the resolution strategy
func (r *LastWriteWinsResolver) GetStrategy() ConflictResolutionStrategy {
	return r.strategy
}

// FirstWriteWinsResolver implements the first-write-wins conflict resolution strategy
type FirstWriteWinsResolver struct {
	strategy ConflictResolutionStrategy
}

// NewFirstWriteWinsResolver creates a new first-write-wins resolver
func NewFirstWriteWinsResolver() *FirstWriteWinsResolver {
	return &FirstWriteWinsResolver{
		strategy: StrategyFirstWriteWins,
	}
}

// ResolveConflict resolves conflicts using first-write-wins strategy
func (r *FirstWriteWinsResolver) ResolveConflict(ctx context.Context, conflict *Conflict) (*ConflictResolution, error) {
	if !r.CanAutoResolve(conflict) {
		return nil, errors.New(errors.CodeConflict, "conflict cannot be auto-resolved")
	}

	var resolvedData map[string]any
	var appliedChange *Change
	var reason string

	// Compare timestamps (earlier wins)
	if conflict.LocalChange.Timestamp.Before(conflict.RemoteChange.Timestamp) {
		resolvedData = conflict.LocalData
		appliedChange = conflict.LocalChange
		reason = "local change has earlier timestamp"
	} else {
		resolvedData = conflict.RemoteData
		appliedChange = conflict.RemoteChange
		reason = "remote change has earlier timestamp"
	}

	return &ConflictResolution{
		ConflictID:    conflict.ID,
		Resolution:    r.strategy,
		ResolvedData:  resolvedData,
		AppliedChange: appliedChange,
		Reason:        reason,
		ResolvedBy:    "system",
		ResolvedAt:    time.Now(),
	}, nil
}

// CanAutoResolve determines if the conflict can be auto-resolved
func (r *FirstWriteWinsResolver) CanAutoResolve(conflict *Conflict) bool {
	return conflict.LocalChange != nil && conflict.RemoteChange != nil
}

// GetStrategy returns the resolution strategy
func (r *FirstWriteWinsResolver) GetStrategy() ConflictResolutionStrategy {
	return r.strategy
}

// MergeResolver implements the merge conflict resolution strategy
type MergeResolver struct {
	strategy ConflictResolutionStrategy
}

// NewMergeResolver creates a new merge resolver
func NewMergeResolver() *MergeResolver {
	return &MergeResolver{
		strategy: StrategyMerge,
	}
}

// ResolveConflict resolves conflicts using merge strategy
func (r *MergeResolver) ResolveConflict(ctx context.Context, conflict *Conflict) (*ConflictResolution, error) {
	if !r.CanAutoResolve(conflict) {
		return nil, errors.New(errors.CodeConflict, "conflict cannot be auto-resolved")
	}

	// Merge non-conflicting fields
	resolvedData := make(map[string]any)

	// Start with local data
	for key, value := range conflict.LocalData {
		resolvedData[key] = value
	}

	// Add remote data for fields that don't conflict
	for key, remoteValue := range conflict.RemoteData {
		if localValue, exists := resolvedData[key]; !exists {
			// Field doesn't exist in local data, add it
			resolvedData[key] = remoteValue
		} else if localValue == remoteValue {
			// Values are the same, keep local value
			continue
		} else {
			// Values conflict, use the more recent one
			if conflict.RemoteChange.Timestamp.After(conflict.LocalChange.Timestamp) {
				resolvedData[key] = remoteValue
			}
		}
	}

	// Create a merged change
	mergedChange := &Change{
		ID:        fmt.Sprintf("merged_%s_%d", conflict.EntityID, time.Now().UnixNano()),
		Type:      "update",
		Entity:    conflict.Entity,
		EntityID:  conflict.EntityID,
		Data:      resolvedData,
		Timestamp: time.Now(),
		UserID:    "system",
		Version:   max(conflict.LocalVersion, conflict.RemoteVersion) + 1,
	}

	return &ConflictResolution{
		ConflictID:    conflict.ID,
		Resolution:    r.strategy,
		ResolvedData:  resolvedData,
		AppliedChange: mergedChange,
		Reason:        "merged non-conflicting fields",
		ResolvedBy:    "system",
		ResolvedAt:    time.Now(),
	}, nil
}

// CanAutoResolve determines if the conflict can be auto-resolved
func (r *MergeResolver) CanAutoResolve(conflict *Conflict) bool {
	return conflict.LocalChange != nil && conflict.RemoteChange != nil
}

// GetStrategy returns the resolution strategy
func (r *MergeResolver) GetStrategy() ConflictResolutionStrategy {
	return r.strategy
}

// ManualResolver implements the manual conflict resolution strategy
type ManualResolver struct {
	strategy ConflictResolutionStrategy
}

// NewManualResolver creates a new manual resolver
func NewManualResolver() *ManualResolver {
	return &ManualResolver{
		strategy: StrategyManual,
	}
}

// ResolveConflict requires manual intervention
func (r *ManualResolver) ResolveConflict(ctx context.Context, conflict *Conflict) (*ConflictResolution, error) {
	return nil, errors.New(errors.CodeConflict, "manual resolution required")
}

// CanAutoResolve always returns false for manual resolution
func (r *ManualResolver) CanAutoResolve(conflict *Conflict) bool {
	return false
}

// GetStrategy returns the resolution strategy
func (r *ManualResolver) GetStrategy() ConflictResolutionStrategy {
	return r.strategy
}

// CustomResolver implements custom conflict resolution using a provided function
type CustomResolver struct {
	strategy    ConflictResolutionStrategy
	resolveFunc func(ctx context.Context, conflict *Conflict) (*ConflictResolution, error)
}

// NewCustomResolver creates a new custom resolver
func NewCustomResolver(resolveFunc func(ctx context.Context, conflict *Conflict) (*ConflictResolution, error)) *CustomResolver {
	return &CustomResolver{
		strategy:    StrategyCustom,
		resolveFunc: resolveFunc,
	}
}

// ResolveConflict uses the custom resolution function
func (r *CustomResolver) ResolveConflict(ctx context.Context, conflict *Conflict) (*ConflictResolution, error) {
	if r.resolveFunc == nil {
		return nil, errors.New(errors.CodeInternal, "custom resolve function not provided")
	}
	return r.resolveFunc(ctx, conflict)
}

// CanAutoResolve determines if the conflict can be auto-resolved
func (r *CustomResolver) CanAutoResolve(conflict *Conflict) bool {
	return r.resolveFunc != nil
}

// GetStrategy returns the resolution strategy
func (r *CustomResolver) GetStrategy() ConflictResolutionStrategy {
	return r.strategy
}

// ConflictDetector detects conflicts between changes
type ConflictDetector struct {
	useVectorClocks bool
}

// NewConflictDetector creates a new conflict detector
func NewConflictDetector(useVectorClocks bool) *ConflictDetector {
	return &ConflictDetector{
		useVectorClocks: useVectorClocks,
	}
}

// DetectConflicts identifies conflicts between local and remote changes
func (cd *ConflictDetector) DetectConflicts(ctx context.Context, localChanges, remoteChanges []Change) ([]Conflict, error) {
	var conflicts []Conflict

	// Group changes by entity ID
	localChangesByEntity := make(map[string][]Change)
	remoteChangesByEntity := make(map[string][]Change)

	for _, change := range localChanges {
		localChangesByEntity[change.EntityID] = append(localChangesByEntity[change.EntityID], change)
	}

	for _, change := range remoteChanges {
		remoteChangesByEntity[change.EntityID] = append(remoteChangesByEntity[change.EntityID], change)
	}

	// Check for conflicts
	for entityID, localChanges := range localChangesByEntity {
		if remoteChanges, exists := remoteChangesByEntity[entityID]; exists {
			conflict := cd.detectEntityConflicts(entityID, localChanges, remoteChanges)
			if conflict != nil {
				conflicts = append(conflicts, *conflict)
			}
		}
	}

	return conflicts, nil
}

// detectEntityConflicts detects conflicts for a specific entity
func (cd *ConflictDetector) detectEntityConflicts(entityID string, localChanges, remoteChanges []Change) *Conflict {
	if len(localChanges) == 0 || len(remoteChanges) == 0 {
		return nil
	}

	// Sort changes by timestamp
	sort.Slice(localChanges, func(i, j int) bool {
		return localChanges[i].Timestamp.Before(localChanges[j].Timestamp)
	})
	sort.Slice(remoteChanges, func(i, j int) bool {
		return remoteChanges[i].Timestamp.Before(remoteChanges[j].Timestamp)
	})

	// Get the latest changes
	localLatest := localChanges[len(localChanges)-1]
	remoteLatest := remoteChanges[len(remoteChanges)-1]

	// Check if there's a conflict
	if cd.hasConflict(localLatest, remoteLatest) {
		return &Conflict{
			ID:            fmt.Sprintf("conflict_%s_%d", entityID, time.Now().UnixNano()),
			Entity:        localLatest.Entity,
			EntityID:      entityID,
			ConflictType:  "concurrent_modification",
			LocalVersion:  localLatest.Version,
			RemoteVersion: remoteLatest.Version,
			LocalData:     localLatest.Data,
			RemoteData:    remoteLatest.Data,
			LocalChange:   &localLatest,
			RemoteChange:  &remoteLatest,
			Resolution:    "",
			CreatedAt:     time.Now(),
		}
	}

	return nil
}

// hasConflict determines if two changes conflict
func (cd *ConflictDetector) hasConflict(local, remote Change) bool {
	// Same entity and type
	if local.EntityID != remote.EntityID || local.Entity != remote.Entity {
		return false
	}

	// Different users or different timestamps
	if local.UserID != remote.UserID {
		return true
	}

	// Check for concurrent modifications
	if cd.useVectorClocks {
		// This would require vector clock implementation
		// For now, use timestamp-based detection
		return !local.Timestamp.Equal(remote.Timestamp)
	}

	// Simple timestamp-based conflict detection
	return !local.Timestamp.Equal(remote.Timestamp)
}

// Helper function
func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
