package realtime

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// SyncStatus represents the status of a state synchronization
type SyncStatus string

const (
	SyncStatusPending    SyncStatus = "pending"
	SyncStatusInProgress SyncStatus = "in_progress"
	SyncStatusCompleted  SyncStatus = "completed"
	SyncStatusFailed     SyncStatus = "failed"
	SyncStatusConflict   SyncStatus = "conflict"
)

// SyncType represents the type of synchronization
type SyncType string

const (
	SyncTypeFull        SyncType = "full"
	SyncTypeDelta       SyncType = "delta"
	SyncTypeIncremental SyncType = "incremental"
	SyncTypeConflict    SyncType = "conflict"
)

// StateVersion represents a version of state
type StateVersion struct {
	ID        string          `json:"id" gorm:"primaryKey"`
	ElementID string          `json:"element_id"`
	Version   int64           `json:"version"`
	State     json.RawMessage `json:"state"`
	Delta     json.RawMessage `json:"delta"`
	ParentID  *string         `json:"parent_id"`
	UserID    string          `json:"user_id"`
	SessionID string          `json:"session_id"`
	CreatedAt time.Time       `json:"created_at"`
	UpdatedAt time.Time       `json:"updated_at"`
}

// StateSync represents a state synchronization operation
type StateSync struct {
	ID          string          `json:"id" gorm:"primaryKey"`
	ElementID   string          `json:"element_id"`
	FromVersion int64           `json:"from_version"`
	ToVersion   int64           `json:"to_version"`
	SyncType    SyncType        `json:"sync_type"`
	Status      SyncStatus      `json:"status"`
	Data        json.RawMessage `json:"data"`
	Conflicts   json.RawMessage `json:"conflicts"`
	Resolution  json.RawMessage `json:"resolution"`
	UserID      string          `json:"user_id"`
	SessionID   string          `json:"session_id"`
	StartedAt   time.Time       `json:"started_at"`
	CompletedAt *time.Time      `json:"completed_at"`
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
}

// StateDelta represents a state delta for incremental synchronization
type StateDelta struct {
	ID          string          `json:"id" gorm:"primaryKey"`
	ElementID   string          `json:"element_id"`
	FromVersion int64           `json:"from_version"`
	ToVersion   int64           `json:"to_version"`
	Changes     json.RawMessage `json:"changes"`
	Metadata    json.RawMessage `json:"metadata"`
	UserID      string          `json:"user_id"`
	SessionID   string          `json:"session_id"`
	CreatedAt   time.Time       `json:"created_at"`
}

// StateConflict represents a state conflict
type StateConflict struct {
	ID           string          `json:"id" gorm:"primaryKey"`
	ElementID    string          `json:"element_id"`
	Version1     int64           `json:"version_1"`
	Version2     int64           `json:"version_2"`
	State1       json.RawMessage `json:"state_1"`
	State2       json.RawMessage `json:"state_2"`
	ConflictType string          `json:"conflict_type"`
	Resolution   json.RawMessage `json:"resolution"`
	ResolvedBy   *string         `json:"resolved_by"`
	ResolvedAt   *time.Time      `json:"resolved_at"`
	CreatedAt    time.Time       `json:"created_at"`
	UpdatedAt    time.Time       `json:"updated_at"`
}

// StateSyncConfig represents state synchronization configuration
type StateSyncConfig struct {
	MaxVersionsPerElement    int           `json:"max_versions_per_element"`
	SyncTimeout              time.Duration `json:"sync_timeout"`
	ConflictDetectionEnabled bool          `json:"conflict_detection_enabled"`
	AutoResolveConflicts     bool          `json:"auto_resolve_conflicts"`
	DeltaCompressionEnabled  bool          `json:"delta_compression_enabled"`
	VersionRetentionPeriod   time.Duration `json:"version_retention_period"`
	CleanupInterval          time.Duration `json:"cleanup_interval"`
	MaxDeltaSize             int           `json:"max_delta_size"`
	EnableOptimisticLocking  bool          `json:"enable_optimistic_locking"`
}

// StateSyncService handles state synchronization between clients and servers
type StateSyncService struct {
	db        *gorm.DB
	mu        sync.RWMutex
	versions  map[string]map[int64]*StateVersion // element_id -> version -> StateVersion
	syncs     map[string]*StateSync              // sync_id -> StateSync
	deltas    map[string]*StateDelta             // delta_id -> StateDelta
	conflicts map[string]*StateConflict          // conflict_id -> StateConflict
	config    *StateSyncConfig
	eventChan chan *StateSyncEvent
	stopChan  chan struct{}
	isRunning bool
}

// StateSyncEvent represents a state synchronization event
type StateSyncEvent struct {
	Type      string                 `json:"type"`
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
	UserID    string                 `json:"user_id"`
	SessionID string                 `json:"session_id"`
	ElementID string                 `json:"element_id"`
}

// NewStateSyncService creates a new state synchronization service
func NewStateSyncService(db *gorm.DB, config *StateSyncConfig) *StateSyncService {
	if config == nil {
		config = &StateSyncConfig{
			MaxVersionsPerElement:    100,
			SyncTimeout:              30 * time.Second,
			ConflictDetectionEnabled: true,
			AutoResolveConflicts:     false,
			DeltaCompressionEnabled:  true,
			VersionRetentionPeriod:   24 * time.Hour,
			CleanupInterval:          1 * time.Hour,
			MaxDeltaSize:             1024 * 1024, // 1MB
			EnableOptimisticLocking:  true,
		}
	}

	return &StateSyncService{
		db:        db,
		versions:  make(map[string]map[int64]*StateVersion),
		syncs:     make(map[string]*StateSync),
		deltas:    make(map[string]*StateDelta),
		conflicts: make(map[string]*StateConflict),
		config:    config,
		eventChan: make(chan *StateSyncEvent, 1000),
		stopChan:  make(chan struct{}),
	}
}

// Start starts the state synchronization service
func (ss *StateSyncService) Start(ctx context.Context) error {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	if ss.isRunning {
		return fmt.Errorf("state sync service is already running")
	}

	// Auto-migrate database tables
	if err := ss.db.AutoMigrate(&StateVersion{}, &StateSync{}, &StateDelta{}, &StateConflict{}); err != nil {
		return fmt.Errorf("failed to migrate state sync tables: %w", err)
	}

	// Load existing data from database
	if err := ss.loadExistingData(ctx); err != nil {
		return fmt.Errorf("failed to load existing data: %w", err)
	}

	ss.isRunning = true

	// Start background goroutines
	go ss.eventProcessingLoop(ctx)
	go ss.cleanupLoop(ctx)

	return nil
}

// Stop stops the state synchronization service
func (ss *StateSyncService) Stop() {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	if !ss.isRunning {
		return
	}

	close(ss.stopChan)
	ss.isRunning = false
}

// CreateVersion creates a new state version
func (ss *StateSyncService) CreateVersion(ctx context.Context, elementID, userID, sessionID string, state map[string]interface{}, parentID *string) (*StateVersion, error) {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	// Get current version number
	var currentVersion int64
	if versions, exists := ss.versions[elementID]; exists && len(versions) > 0 {
		for version := range versions {
			if version > currentVersion {
				currentVersion = version
			}
		}
	}
	newVersion := currentVersion + 1

	// Check if we need to clean up old versions
	if len(ss.versions[elementID]) >= ss.config.MaxVersionsPerElement {
		ss.cleanupOldVersions(elementID)
	}

	// Create new version
	version := &StateVersion{
		ID:        generateVersionID(),
		ElementID: elementID,
		Version:   newVersion,
		State:     mustMarshalJSON(state),
		ParentID:  parentID,
		UserID:    userID,
		SessionID: sessionID,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Store in memory
	if ss.versions[elementID] == nil {
		ss.versions[elementID] = make(map[int64]*StateVersion)
	}
	ss.versions[elementID][newVersion] = version

	// Save to database
	if err := ss.db.Create(version).Error; err != nil {
		return nil, fmt.Errorf("failed to create state version: %w", err)
	}

	// Emit event
	ss.eventChan <- &StateSyncEvent{
		Type:      "version_created",
		Data:      map[string]interface{}{"version": newVersion, "element_id": elementID},
		Timestamp: time.Now(),
		UserID:    userID,
		SessionID: sessionID,
		ElementID: elementID,
	}

	return version, nil
}

// GetVersion retrieves a specific state version
func (ss *StateSyncService) GetVersion(ctx context.Context, elementID string, version int64) (*StateVersion, error) {
	ss.mu.RLock()
	defer ss.mu.RUnlock()

	if versions, exists := ss.versions[elementID]; exists {
		if version, exists := versions[version]; exists {
			return version, nil
		}
	}

	// Try to load from database
	var dbVersion StateVersion
	if err := ss.db.Where("element_id = ? AND version = ?", elementID, version).First(&dbVersion).Error; err != nil {
		return nil, fmt.Errorf("version not found: %w", err)
	}

	return &dbVersion, nil
}

// GetLatestVersion retrieves the latest state version for an element
func (ss *StateSyncService) GetLatestVersion(ctx context.Context, elementID string) (*StateVersion, error) {
	ss.mu.RLock()
	defer ss.mu.RUnlock()

	if versions, exists := ss.versions[elementID]; exists && len(versions) > 0 {
		var latestVersion *StateVersion
		var maxVersion int64

		for version, stateVersion := range versions {
			if version > maxVersion {
				maxVersion = version
				latestVersion = stateVersion
			}
		}

		if latestVersion != nil {
			return latestVersion, nil
		}
	}

	// Try to load from database
	var dbVersion StateVersion
	if err := ss.db.Where("element_id = ?", elementID).Order("version DESC").First(&dbVersion).Error; err != nil {
		return nil, fmt.Errorf("no versions found for element: %w", err)
	}

	return &dbVersion, nil
}

// SyncState synchronizes state between client and server
func (ss *StateSyncService) SyncState(ctx context.Context, elementID, userID, sessionID string, clientVersion int64, clientState map[string]interface{}) (*StateSync, error) {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	// Get latest server version
	latestVersion, err := ss.GetLatestVersion(ctx, elementID)
	if err != nil {
		return nil, fmt.Errorf("failed to get latest version: %w", err)
	}

	// Check if client is up to date
	if clientVersion >= latestVersion.Version {
		return &StateSync{
			ID:          generateSyncID(),
			ElementID:   elementID,
			FromVersion: clientVersion,
			ToVersion:   latestVersion.Version,
			SyncType:    SyncTypeDelta,
			Status:      SyncStatusCompleted,
			UserID:      userID,
			SessionID:   sessionID,
			StartedAt:   time.Now(),
			CompletedAt: &time.Time{},
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}, nil
	}

	// Create sync operation
	sync := &StateSync{
		ID:          generateSyncID(),
		ElementID:   elementID,
		FromVersion: clientVersion,
		ToVersion:   latestVersion.Version,
		SyncType:    SyncTypeDelta,
		Status:      SyncStatusInProgress,
		UserID:      userID,
		SessionID:   sessionID,
		StartedAt:   time.Now(),
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Check for conflicts
	if ss.config.ConflictDetectionEnabled {
		if conflict := ss.detectConflict(elementID, clientVersion, clientState, latestVersion); conflict != nil {
			sync.Status = SyncStatusConflict
			sync.Conflicts = mustMarshalJSON(conflict)

			// Store conflict
			ss.conflicts[conflict.ID] = conflict
			if err := ss.db.Create(conflict).Error; err != nil {
				return nil, fmt.Errorf("failed to store conflict: %w", err)
			}

			// Auto-resolve if enabled
			if ss.config.AutoResolveConflicts {
				if resolution := ss.autoResolveConflict(conflict); resolution != nil {
					sync.Resolution = mustMarshalJSON(resolution)
					sync.Status = SyncStatusCompleted
					now := time.Now()
					sync.CompletedAt = &now
				}
			}
		} else {
			// No conflict, complete sync
			sync.Status = SyncStatusCompleted
			now := time.Now()
			sync.CompletedAt = &now
		}
	} else {
		// No conflict detection, complete sync
		sync.Status = SyncStatusCompleted
		now := time.Now()
		sync.CompletedAt = &now
	}

	// Store sync
	ss.syncs[sync.ID] = sync
	if err := ss.db.Create(sync).Error; err != nil {
		return nil, fmt.Errorf("failed to store sync: %w", err)
	}

	return sync, nil
}

// CreateDelta creates a state delta for incremental synchronization
func (ss *StateSyncService) CreateDelta(ctx context.Context, elementID, userID, sessionID string, fromVersion, toVersion int64, changes map[string]interface{}) (*StateDelta, error) {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	delta := &StateDelta{
		ID:          generateDeltaID(),
		ElementID:   elementID,
		FromVersion: fromVersion,
		ToVersion:   toVersion,
		Changes:     mustMarshalJSON(changes),
		UserID:      userID,
		SessionID:   sessionID,
		CreatedAt:   time.Now(),
	}

	// Store in memory
	ss.deltas[delta.ID] = delta

	// Save to database
	if err := ss.db.Create(delta).Error; err != nil {
		return nil, fmt.Errorf("failed to create state delta: %w", err)
	}

	return delta, nil
}

// GetDelta retrieves a state delta
func (ss *StateSyncService) GetDelta(ctx context.Context, elementID string, fromVersion, toVersion int64) (*StateDelta, error) {
	ss.mu.RLock()
	defer ss.mu.RUnlock()

	// Try to find in memory
	for _, delta := range ss.deltas {
		if delta.ElementID == elementID && delta.FromVersion == fromVersion && delta.ToVersion == toVersion {
			return delta, nil
		}
	}

	// Try to load from database
	var dbDelta StateDelta
	if err := ss.db.Where("element_id = ? AND from_version = ? AND to_version = ?", elementID, fromVersion, toVersion).First(&dbDelta).Error; err != nil {
		return nil, fmt.Errorf("delta not found: %w", err)
	}

	return &dbDelta, nil
}

// ResolveConflict resolves a state conflict
func (ss *StateSyncService) ResolveConflict(ctx context.Context, conflictID string, resolution map[string]interface{}, resolvedBy string) error {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	conflict, exists := ss.conflicts[conflictID]
	if !exists {
		return fmt.Errorf("conflict not found")
	}

	now := time.Now()
	conflict.Resolution = mustMarshalJSON(resolution)
	conflict.ResolvedBy = &resolvedBy
	conflict.ResolvedAt = &now
	conflict.UpdatedAt = now

	// Update in database
	if err := ss.db.Save(conflict).Error; err != nil {
		return fmt.Errorf("failed to update conflict: %w", err)
	}

	// Emit event
	ss.eventChan <- &StateSyncEvent{
		Type:      "conflict_resolved",
		Data:      map[string]interface{}{"conflict_id": conflictID, "resolution": resolution},
		Timestamp: time.Now(),
		UserID:    resolvedBy,
		ElementID: conflict.ElementID,
	}

	return nil
}

// GetElementVersions retrieves all versions for an element
func (ss *StateSyncService) GetElementVersions(ctx context.Context, elementID string, limit int) ([]StateVersion, error) {
	ss.mu.RLock()
	defer ss.mu.RUnlock()

	if limit <= 0 {
		limit = 50
	}

	var versions []StateVersion
	if err := ss.db.Where("element_id = ?", elementID).Order("version DESC").Limit(limit).Find(&versions).Error; err != nil {
		return nil, fmt.Errorf("failed to get element versions: %w", err)
	}

	return versions, nil
}

// GetSyncHistory retrieves sync history for an element
func (ss *StateSyncService) GetSyncHistory(ctx context.Context, elementID string, limit int) ([]StateSync, error) {
	ss.mu.RLock()
	defer ss.mu.RUnlock()

	if limit <= 0 {
		limit = 50
	}

	var syncs []StateSync
	if err := ss.db.Where("element_id = ?", elementID).Order("created_at DESC").Limit(limit).Find(&syncs).Error; err != nil {
		return nil, fmt.Errorf("failed to get sync history: %w", err)
	}

	return syncs, nil
}

// loadExistingData loads existing data from database
func (ss *StateSyncService) loadExistingData(ctx context.Context) error {
	// Load recent versions (last 1000)
	var versions []StateVersion
	if err := ss.db.Order("created_at DESC").Limit(1000).Find(&versions).Error; err != nil {
		return fmt.Errorf("failed to load versions: %w", err)
	}

	for _, version := range versions {
		if ss.versions[version.ElementID] == nil {
			ss.versions[version.ElementID] = make(map[int64]*StateVersion)
		}
		ss.versions[version.ElementID][version.Version] = &version
	}

	// Load recent syncs (last 1000)
	var syncs []StateSync
	if err := ss.db.Order("created_at DESC").Limit(1000).Find(&syncs).Error; err != nil {
		return fmt.Errorf("failed to load syncs: %w", err)
	}

	for _, sync := range syncs {
		ss.syncs[sync.ID] = &sync
	}

	// Load recent deltas (last 1000)
	var deltas []StateDelta
	if err := ss.db.Order("created_at DESC").Limit(1000).Find(&deltas).Error; err != nil {
		return fmt.Errorf("failed to load deltas: %w", err)
	}

	for _, delta := range deltas {
		ss.deltas[delta.ID] = &delta
	}

	// Load recent conflicts (last 1000)
	var conflicts []StateConflict
	if err := ss.db.Order("created_at DESC").Limit(1000).Find(&conflicts).Error; err != nil {
		return fmt.Errorf("failed to load conflicts: %w", err)
	}

	for _, conflict := range conflicts {
		ss.conflicts[conflict.ID] = &conflict
	}

	return nil
}

// detectConflict detects conflicts between client and server state
func (ss *StateSyncService) detectConflict(elementID string, clientVersion int64, clientState map[string]interface{}, serverVersion *StateVersion) *StateConflict {
	// Simple conflict detection - can be enhanced with more sophisticated algorithms
	if clientVersion < serverVersion.Version {
		// Check if client state conflicts with server state
		// This is a simplified implementation
		return &StateConflict{
			ID:           generateConflictID(),
			ElementID:    elementID,
			Version1:     clientVersion,
			Version2:     serverVersion.Version,
			State1:       mustMarshalJSON(clientState),
			State2:       serverVersion.State,
			ConflictType: "version_mismatch",
			CreatedAt:    time.Now(),
			UpdatedAt:    time.Now(),
		}
	}

	return nil
}

// autoResolveConflict automatically resolves conflicts
func (ss *StateSyncService) autoResolveConflict(conflict *StateConflict) map[string]interface{} {
	// Simple auto-resolution - can be enhanced with more sophisticated algorithms
	return map[string]interface{}{
		"resolution_type": "server_wins",
		"reason":          "automatic resolution",
		"timestamp":       time.Now(),
	}
}

// cleanupOldVersions cleans up old versions for an element
func (ss *StateSyncService) cleanupOldVersions(elementID string) {
	versions := ss.versions[elementID]
	if len(versions) <= ss.config.MaxVersionsPerElement {
		return
	}

	// Find oldest versions to remove
	var versionNumbers []int64
	for version := range versions {
		versionNumbers = append(versionNumbers, version)
	}

	// Sort and remove oldest
	// Implementation would sort versionNumbers and remove oldest ones
	// This is a simplified version
}

// eventProcessingLoop processes state sync events
func (ss *StateSyncService) eventProcessingLoop(ctx context.Context) {
	for {
		select {
		case event := <-ss.eventChan:
			ss.processEvent(event)
		case <-ss.stopChan:
			return
		case <-ctx.Done():
			return
		}
	}
}

// processEvent processes a state sync event
func (ss *StateSyncService) processEvent(event *StateSyncEvent) {
	// Process event based on type
	switch event.Type {
	case "version_created":
		// Handle version creation event
	case "conflict_resolved":
		// Handle conflict resolution event
	case "sync_completed":
		// Handle sync completion event
	}
}

// cleanupLoop runs periodic cleanup tasks
func (ss *StateSyncService) cleanupLoop(ctx context.Context) {
	ticker := time.NewTicker(ss.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			ss.cleanupExpiredData(ctx)
		case <-ss.stopChan:
			return
		case <-ctx.Done():
			return
		}
	}
}

// cleanupExpiredData cleans up expired data
func (ss *StateSyncService) cleanupExpiredData(ctx context.Context) {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	cutoff := time.Now().Add(-ss.config.VersionRetentionPeriod)

	// Clean up old versions from database
	if err := ss.db.Where("created_at < ?", cutoff).Delete(&StateVersion{}).Error; err != nil {
		// Log error but continue
	}

	// Clean up old syncs from database
	if err := ss.db.Where("created_at < ?", cutoff).Delete(&StateSync{}).Error; err != nil {
		// Log error but continue
	}

	// Clean up old deltas from database
	if err := ss.db.Where("created_at < ?", cutoff).Delete(&StateDelta{}).Error; err != nil {
		// Log error but continue
	}

	// Clean up old conflicts from database
	if err := ss.db.Where("created_at < ?", cutoff).Delete(&StateConflict{}).Error; err != nil {
		// Log error but continue
	}
}

// GetStateSyncStats returns statistics about state synchronization
func (ss *StateSyncService) GetStateSyncStats() map[string]interface{} {
	ss.mu.RLock()
	defer ss.mu.RUnlock()

	var totalVersions, totalSyncs, totalDeltas, totalConflicts int64

	// Count versions
	ss.db.Model(&StateVersion{}).Count(&totalVersions)

	// Count syncs
	ss.db.Model(&StateSync{}).Count(&totalSyncs)

	// Count deltas
	ss.db.Model(&StateDelta{}).Count(&totalDeltas)

	// Count conflicts
	ss.db.Model(&StateConflict{}).Count(&totalConflicts)

	return map[string]interface{}{
		"total_versions":   totalVersions,
		"total_syncs":      totalSyncs,
		"total_deltas":     totalDeltas,
		"total_conflicts":  totalConflicts,
		"memory_versions":  len(ss.versions),
		"memory_syncs":     len(ss.syncs),
		"memory_deltas":    len(ss.deltas),
		"memory_conflicts": len(ss.conflicts),
		"is_running":       ss.isRunning,
		"config":           ss.config,
	}
}

// Helper functions
func generateVersionID() string {
	return fmt.Sprintf("ver_%d", time.Now().UnixNano())
}

func generateSyncID() string {
	return fmt.Sprintf("sync_%d", time.Now().UnixNano())
}

func generateDeltaID() string {
	return fmt.Sprintf("delta_%d", time.Now().UnixNano())
}

func generateConflictID() string {
	return fmt.Sprintf("conflict_%d", time.Now().UnixNano())
}

func mustMarshalJSON(v interface{}) json.RawMessage {
	data, err := json.Marshal(v)
	if err != nil {
		panic(fmt.Sprintf("failed to marshal JSON: %v", err))
	}
	return data
}
