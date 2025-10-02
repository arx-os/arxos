package sync

import (
	"context"
	"testing"
	"time"

	"github.com/arx-os/arxos/pkg/errors"
)

func TestVectorClock(t *testing.T) {
	// Test basic vector clock operations
	clock1 := NewVectorClock("node1")
	clock2 := NewVectorClock("node2")

	// Test increment
	clock1.Increment()
	if clock1.Clock["node1"] != 1 {
		t.Errorf("Expected clock1[node1] = 1, got %d", clock1.Clock["node1"])
	}

	// Test update
	clock2.Clock["node1"] = 1
	clock2.Clock["node2"] = 1
	clock1.Update(clock2)

	if clock1.Clock["node2"] != 1 {
		t.Errorf("Expected clock1[node2] = 1, got %d", clock1.Clock["node2"])
	}

	// Test happens before
	clock3 := NewVectorClock("node3")
	clock3.Clock["node1"] = 0
	clock3.Clock["node2"] = 0
	clock3.Clock["node3"] = 0

	if !clock3.HappensBefore(clock1) {
		t.Error("clock3 should happen before clock1")
	}

	if clock1.HappensBefore(clock3) {
		t.Error("clock1 should not happen before clock3")
	}

	// Test concurrent
	clock4 := NewVectorClock("node4")
	clock4.Clock["node1"] = 1
	clock4.Clock["node2"] = 0
	clock4.Clock["node4"] = 1

	if !clock1.Concurrent(clock4) {
		t.Error("clock1 and clock4 should be concurrent")
	}
}

func TestLastWriteWinsResolver(t *testing.T) {
	resolver := NewLastWriteWinsResolver()

	// Create test conflict
	now := time.Now()
	conflict := &Conflict{
		ID:       "test-conflict",
		Entity:   "building",
		EntityID: "building-001",
		LocalChange: &Change{
			ID:        "local-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Local Building"},
			Timestamp: now.Add(-time.Hour),
			UserID:    "user1",
			Version:   1,
		},
		RemoteChange: &Change{
			ID:        "remote-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Remote Building"},
			Timestamp: now,
			UserID:    "user2",
			Version:   2,
		},
		LocalData:  map[string]interface{}{"name": "Local Building"},
		RemoteData: map[string]interface{}{"name": "Remote Building"},
	}

	// Test resolution
	resolution, err := resolver.ResolveConflict(context.Background(), conflict)
	if err != nil {
		t.Fatalf("Failed to resolve conflict: %v", err)
	}

	if resolution.Resolution != StrategyLastWriteWins {
		t.Errorf("Expected resolution strategy %s, got %s", StrategyLastWriteWins, resolution.Resolution)
	}

	// Remote change should win (later timestamp)
	if resolution.AppliedChange.ID != "remote-change" {
		t.Errorf("Expected remote change to win, got %s", resolution.AppliedChange.ID)
	}

	// Test can auto resolve
	if !resolver.CanAutoResolve(conflict) {
		t.Error("Should be able to auto-resolve conflict")
	}
}

func TestFirstWriteWinsResolver(t *testing.T) {
	resolver := NewFirstWriteWinsResolver()

	// Create test conflict
	now := time.Now()
	conflict := &Conflict{
		ID:       "test-conflict",
		Entity:   "building",
		EntityID: "building-001",
		LocalChange: &Change{
			ID:        "local-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Local Building"},
			Timestamp: now.Add(-time.Hour),
			UserID:    "user1",
			Version:   1,
		},
		RemoteChange: &Change{
			ID:        "remote-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Remote Building"},
			Timestamp: now,
			UserID:    "user2",
			Version:   2,
		},
		LocalData:  map[string]interface{}{"name": "Local Building"},
		RemoteData: map[string]interface{}{"name": "Remote Building"},
	}

	// Test resolution
	resolution, err := resolver.ResolveConflict(context.Background(), conflict)
	if err != nil {
		t.Fatalf("Failed to resolve conflict: %v", err)
	}

	if resolution.Resolution != StrategyFirstWriteWins {
		t.Errorf("Expected resolution strategy %s, got %s", StrategyFirstWriteWins, resolution.Resolution)
	}

	// Local change should win (earlier timestamp)
	if resolution.AppliedChange.ID != "local-change" {
		t.Errorf("Expected local change to win, got %s", resolution.AppliedChange.ID)
	}
}

func TestMergeResolver(t *testing.T) {
	resolver := NewMergeResolver()

	// Create test conflict with mergeable data
	now := time.Now()
	conflict := &Conflict{
		ID:       "test-conflict",
		Entity:   "building",
		EntityID: "building-001",
		LocalChange: &Change{
			ID:        "local-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Local Building", "address": "123 Local St"},
			Timestamp: now.Add(-time.Hour),
			UserID:    "user1",
			Version:   1,
		},
		RemoteChange: &Change{
			ID:        "remote-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Remote Building", "description": "Remote description"},
			Timestamp: now,
			UserID:    "user2",
			Version:   2,
		},
		LocalData:  map[string]interface{}{"name": "Local Building", "address": "123 Local St"},
		RemoteData: map[string]interface{}{"name": "Remote Building", "description": "Remote description"},
	}

	// Test resolution
	resolution, err := resolver.ResolveConflict(context.Background(), conflict)
	if err != nil {
		t.Fatalf("Failed to resolve conflict: %v", err)
	}

	if resolution.Resolution != StrategyMerge {
		t.Errorf("Expected resolution strategy %s, got %s", StrategyMerge, resolution.Resolution)
	}

	// Check merged data
	mergedData := resolution.ResolvedData
	if mergedData["name"] != "Remote Building" { // Remote should win for conflicting field
		t.Errorf("Expected merged name to be 'Remote Building', got %v", mergedData["name"])
	}
	if mergedData["address"] != "123 Local St" {
		t.Errorf("Expected merged address to be '123 Local St', got %v", mergedData["address"])
	}
	if mergedData["description"] != "Remote description" {
		t.Errorf("Expected merged description to be 'Remote description', got %v", mergedData["description"])
	}
}

func TestManualResolver(t *testing.T) {
	resolver := NewManualResolver()

	// Create test conflict
	conflict := &Conflict{
		ID:       "test-conflict",
		Entity:   "building",
		EntityID: "building-001",
	}

	// Test resolution (should fail)
	_, err := resolver.ResolveConflict(context.Background(), conflict)
	if err == nil {
		t.Error("Expected manual resolution to fail")
	}

	// Test can auto resolve (should be false)
	if resolver.CanAutoResolve(conflict) {
		t.Error("Manual resolver should not be able to auto-resolve")
	}
}

func TestCustomResolver(t *testing.T) {
	// Create custom resolver that always chooses local
	customResolver := NewCustomResolver(func(ctx context.Context, conflict *Conflict) (*ConflictResolution, error) {
		return &ConflictResolution{
			ConflictID:    conflict.ID,
			Resolution:    StrategyCustom,
			ResolvedData:  conflict.LocalData,
			AppliedChange: conflict.LocalChange,
			Reason:        "custom logic: always choose local",
			ResolvedBy:    "custom",
			ResolvedAt:    time.Now(),
		}, nil
	})

	// Create test conflict
	now := time.Now()
	conflict := &Conflict{
		ID:       "test-conflict",
		Entity:   "building",
		EntityID: "building-001",
		LocalChange: &Change{
			ID:        "local-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Local Building"},
			Timestamp: now.Add(-time.Hour),
			UserID:    "user1",
			Version:   1,
		},
		RemoteChange: &Change{
			ID:        "remote-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Remote Building"},
			Timestamp: now,
			UserID:    "user2",
			Version:   2,
		},
		LocalData:  map[string]interface{}{"name": "Local Building"},
		RemoteData: map[string]interface{}{"name": "Remote Building"},
	}

	// Test resolution
	resolution, err := customResolver.ResolveConflict(context.Background(), conflict)
	if err != nil {
		t.Fatalf("Failed to resolve conflict: %v", err)
	}

	if resolution.Resolution != StrategyCustom {
		t.Errorf("Expected resolution strategy %s, got %s", StrategyCustom, resolution.Resolution)
	}

	// Local change should win (custom logic)
	if resolution.AppliedChange.ID != "local-change" {
		t.Errorf("Expected local change to win, got %s", resolution.AppliedChange.ID)
	}
}

func TestConflictDetector(t *testing.T) {
	detector := NewConflictDetector(false) // Don't use vector clocks for simplicity

	// Create test changes
	now := time.Now()
	localChanges := []Change{
		{
			ID:        "local-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Local Building"},
			Timestamp: now.Add(-time.Hour),
			UserID:    "user1",
			Version:   1,
		},
	}

	remoteChanges := []Change{
		{
			ID:        "remote-change",
			Type:      "update",
			Entity:    "building",
			EntityID:  "building-001",
			Data:      map[string]interface{}{"name": "Remote Building"},
			Timestamp: now,
			UserID:    "user2",
			Version:   2,
		},
	}

	// Test conflict detection
	conflicts, err := detector.DetectConflicts(context.Background(), localChanges, remoteChanges)
	if err != nil {
		t.Fatalf("Failed to detect conflicts: %v", err)
	}

	if len(conflicts) != 1 {
		t.Errorf("Expected 1 conflict, got %d", len(conflicts))
	}

	conflict := conflicts[0]
	if conflict.EntityID != "building-001" {
		t.Errorf("Expected conflict entity ID 'building-001', got %s", conflict.EntityID)
	}

	if conflict.ConflictType != "concurrent_modification" {
		t.Errorf("Expected conflict type 'concurrent_modification', got %s", conflict.ConflictType)
	}
}

func TestSyncEngine(t *testing.T) {
	// Create mock stores
	changeStore := &mockChangeStore{
		changes:  make(map[string]*Change),
		lastSync: make(map[string]time.Time),
	}
	conflictStore := &mockConflictStore{
		conflicts: make(map[string]*Conflict),
	}
	metrics := &mockSyncMetrics{}

	// Create sync engine
	resolver := NewLastWriteWinsResolver()
	engine := NewSyncEngine(resolver, changeStore, conflictStore, metrics, nil)

	// Create sync request
	now := time.Now()
	request := &SyncRequest{
		BuildingID: "building-001",
		Changes: []Change{
			{
				ID:        "remote-change",
				Type:      "update",
				Entity:    "building",
				EntityID:  "building-001",
				Data:      map[string]interface{}{"name": "Remote Building"},
				Timestamp: now,
				UserID:    "user2",
				Version:   2,
			},
		},
		LastSync: now.Add(-time.Hour),
		Metadata: map[string]interface{}{},
	}

	// Test sync
	response, err := engine.Sync(context.Background(), request)
	if err != nil {
		t.Fatalf("Failed to sync: %v", err)
	}

	if !response.Success {
		t.Error("Expected sync to be successful")
	}

	if len(response.AppliedChanges) != 1 {
		t.Errorf("Expected 1 applied change, got %d", len(response.AppliedChanges))
	}

	// Test sync status
	status, err := engine.GetSyncStatus(context.Background(), "building-001")
	if err != nil {
		t.Fatalf("Failed to get sync status: %v", err)
	}

	if status.BuildingID != "building-001" {
		t.Errorf("Expected building ID 'building-001', got %s", status.BuildingID)
	}

	if !status.IsInSync {
		t.Error("Expected building to be in sync")
	}
}

// Mock implementations for testing

type mockChangeStore struct {
	changes  map[string]*Change
	lastSync map[string]time.Time
}

func (m *mockChangeStore) StoreChange(ctx context.Context, change *Change) error {
	m.changes[change.ID] = change
	return nil
}

func (m *mockChangeStore) GetChanges(ctx context.Context, buildingID string, since time.Time) ([]Change, error) {
	var changes []Change
	for _, change := range m.changes {
		if change.Timestamp.After(since) {
			changes = append(changes, *change)
		}
	}
	return changes, nil
}

func (m *mockChangeStore) GetChange(ctx context.Context, changeID string) (*Change, error) {
	if change, exists := m.changes[changeID]; exists {
		return change, nil
	}
	return nil, errors.New(errors.CodeNotFound, "change not found")
}

func (m *mockChangeStore) DeleteChange(ctx context.Context, changeID string) error {
	delete(m.changes, changeID)
	return nil
}

func (m *mockChangeStore) GetLastSyncTime(ctx context.Context, buildingID string) (time.Time, error) {
	if lastSync, exists := m.lastSync[buildingID]; exists {
		return lastSync, nil
	}
	return time.Time{}, nil
}

func (m *mockChangeStore) SetLastSyncTime(ctx context.Context, buildingID string, timestamp time.Time) error {
	m.lastSync[buildingID] = timestamp
	return nil
}

type mockConflictStore struct {
	conflicts map[string]*Conflict
}

func (m *mockConflictStore) StoreConflict(ctx context.Context, conflict *Conflict) error {
	m.conflicts[conflict.ID] = conflict
	return nil
}

func (m *mockConflictStore) GetConflicts(ctx context.Context, buildingID string) ([]Conflict, error) {
	var conflicts []Conflict
	for _, conflict := range m.conflicts {
		if conflict.Resolution == "" { // Unresolved
			conflicts = append(conflicts, *conflict)
		}
	}
	return conflicts, nil
}

func (m *mockConflictStore) GetConflict(ctx context.Context, conflictID string) (*Conflict, error) {
	if conflict, exists := m.conflicts[conflictID]; exists {
		return conflict, nil
	}
	return nil, errors.New(errors.CodeNotFound, "conflict not found")
}

func (m *mockConflictStore) ResolveConflict(ctx context.Context, conflictID string, resolution *ConflictResolution) error {
	if conflict, exists := m.conflicts[conflictID]; exists {
		conflict.Resolution = string(resolution.Resolution)
		now := time.Now()
		conflict.ResolvedAt = &now
		conflict.ResolvedBy = resolution.ResolvedBy
		return nil
	}
	return errors.New(errors.CodeNotFound, "conflict not found")
}

func (m *mockConflictStore) DeleteConflict(ctx context.Context, conflictID string) error {
	delete(m.conflicts, conflictID)
	return nil
}

type mockSyncMetrics struct{}

func (m *mockSyncMetrics) RecordSyncOperation(ctx context.Context, operation string, duration time.Duration, success bool) {
}
func (m *mockSyncMetrics) RecordConflictDetected(ctx context.Context, conflictType string) {}
func (m *mockSyncMetrics) RecordConflictResolved(ctx context.Context, strategy ConflictResolutionStrategy, duration time.Duration) {
}
func (m *mockSyncMetrics) RecordChangesApplied(ctx context.Context, count int) {}
