package ar

import (
	"context"
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/merge"
	"github.com/arx-os/arxos/internal/spatial"
)

// SyncThresholds defines thresholds for triggering BIM sync
type SyncThresholds struct {
	PositionThreshold  float64       `json:"position_threshold"`  // meters
	RotationThreshold  float64       `json:"rotation_threshold"`  // degrees
	TimeThreshold      time.Duration `json:"time_threshold"`      // max time between syncs
	BatchSize          int           `json:"batch_size"`          // max changes per batch
	ConfidenceRequired float32       `json:"confidence_required"` // min confidence for sync
}

// DefaultSyncThresholds returns default sync thresholds
func DefaultSyncThresholds() SyncThresholds {
	return SyncThresholds{
		PositionThreshold:  0.3,             // 30cm movement
		RotationThreshold:  15.0,            // 15 degrees rotation
		TimeThreshold:      5 * time.Minute, // sync at least every 5 minutes
		BatchSize:          50,              // max 50 changes per batch
		ConfidenceRequired: 0.7,             // 70% confidence minimum
	}
}

// ChangeType represents the type of AR change
type ChangeType string

const (
	ChangeTypeMove   ChangeType = "move"
	ChangeTypeRotate ChangeType = "rotate"
	ChangeTypeAdd    ChangeType = "add"
	ChangeTypeRemove ChangeType = "remove"
	ChangeTypeModify ChangeType = "modify"
)

// ARChange represents a change made in AR
type ARChange struct {
	ID              string                 `json:"id"`
	SessionID       string                 `json:"session_id"`
	EquipmentID     string                 `json:"equipment_id"`
	Type            ChangeType             `json:"type"`
	OldPosition     spatial.Point3D        `json:"old_position,omitempty"`
	NewPosition     spatial.Point3D        `json:"new_position,omitempty"`
	OldRotation     ARRotation             `json:"old_rotation,omitempty"`
	NewRotation     ARRotation             `json:"new_rotation,omitempty"`
	Attributes      map[string]interface{} `json:"attributes,omitempty"`
	Timestamp       time.Time              `json:"timestamp"`
	Confidence      float32                `json:"confidence"`
	Applied         bool                   `json:"applied"`
	Rejected        bool                   `json:"rejected"`
	RejectionReason string                 `json:"rejection_reason,omitempty"`
}

// SyncEngine handles threshold-based BIM synchronization
type SyncEngine struct {
	thresholds       SyncThresholds
	changeQueue      *ChangeQueue
	changeDetector   *merge.ChangeDetector
	conflictResolver *merge.ConflictResolver
	bimUpdater       BIMUpdater
	sessions         map[string]*ARSession
	lastSync         map[string]time.Time
	mu               sync.RWMutex
	ctx              context.Context
	cancel           context.CancelFunc
}

// BIMUpdater interface for updating BIM data
type BIMUpdater interface {
	UpdateEquipment(equipmentID string, changes map[string]interface{}) error
	AddEquipment(equipment *EquipmentData) error
	RemoveEquipment(equipmentID string) error
	BatchUpdate(changes []*ARChange) error
}

// EquipmentData represents equipment data for BIM
type EquipmentData struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	Position   spatial.Point3D        `json:"position"`
	Rotation   ARRotation             `json:"rotation"`
	Dimensions spatial.BoundingBox    `json:"dimensions"`
	Attributes map[string]interface{} `json:"attributes"`
}

// NewSyncEngine creates a new sync engine
func NewSyncEngine(
	changeDetector *merge.ChangeDetector,
	conflictResolver *merge.ConflictResolver,
	bimUpdater BIMUpdater,
) *SyncEngine {
	ctx, cancel := context.WithCancel(context.Background())

	engine := &SyncEngine{
		thresholds:       DefaultSyncThresholds(),
		changeQueue:      NewChangeQueue(1000),
		changeDetector:   changeDetector,
		conflictResolver: conflictResolver,
		bimUpdater:       bimUpdater,
		sessions:         make(map[string]*ARSession),
		lastSync:         make(map[string]time.Time),
		ctx:              ctx,
		cancel:           cancel,
	}

	// Start sync routine
	go engine.syncRoutine()

	return engine
}

// SetThresholds sets custom sync thresholds
func (se *SyncEngine) SetThresholds(thresholds SyncThresholds) {
	se.mu.Lock()
	defer se.mu.Unlock()
	se.thresholds = thresholds
}

// RegisterSession registers an AR session for sync
func (se *SyncEngine) RegisterSession(session *ARSession) {
	se.mu.Lock()
	defer se.mu.Unlock()

	se.sessions[session.ID] = session
	se.lastSync[session.ID] = time.Now()
}

// UnregisterSession unregisters an AR session
func (se *SyncEngine) UnregisterSession(sessionID string) {
	se.mu.Lock()
	defer se.mu.Unlock()

	delete(se.sessions, sessionID)
	delete(se.lastSync, sessionID)
}

// RecordChange records an AR change
func (se *SyncEngine) RecordChange(change *ARChange) error {
	// Validate confidence
	if change.Confidence < se.thresholds.ConfidenceRequired {
		change.Rejected = true
		change.RejectionReason = fmt.Sprintf("confidence too low: %.2f < %.2f",
			change.Confidence, se.thresholds.ConfidenceRequired)
		return fmt.Errorf("%s", change.RejectionReason)
	}

	// Check if change exceeds thresholds
	if se.exceedsThreshold(change) {
		// Add to high priority queue
		se.changeQueue.AddHighPriority(change)

		// Trigger immediate sync if critical
		if se.isCriticalChange(change) {
			go se.syncImmediate(change.SessionID)
		}
	} else {
		// Add to normal queue
		se.changeQueue.Add(change)
	}

	return nil
}

// exceedsThreshold checks if a change exceeds sync thresholds
func (se *SyncEngine) exceedsThreshold(change *ARChange) bool {
	switch change.Type {
	case ChangeTypeMove:
		distance := change.OldPosition.DistanceTo(change.NewPosition)
		return distance >= se.thresholds.PositionThreshold

	case ChangeTypeRotate:
		// Calculate rotation angle difference
		angle := calculateRotationAngle(change.OldRotation, change.NewRotation)
		return angle >= se.thresholds.RotationThreshold

	case ChangeTypeAdd, ChangeTypeRemove:
		return true // Always sync adds/removes immediately

	case ChangeTypeModify:
		return true // Always sync modifications

	default:
		return false
	}
}

// isCriticalChange determines if a change is critical
func (se *SyncEngine) isCriticalChange(change *ARChange) bool {
	// Additions and removals are always critical
	if change.Type == ChangeTypeAdd || change.Type == ChangeTypeRemove {
		return true
	}

	// Large movements are critical
	if change.Type == ChangeTypeMove {
		distance := change.OldPosition.DistanceTo(change.NewPosition)
		return distance > 1.0 // More than 1 meter
	}

	return false
}

// syncRoutine periodically syncs changes
func (se *SyncEngine) syncRoutine() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-se.ctx.Done():
			return
		case <-ticker.C:
			se.syncPending()
		}
	}
}

// syncPending syncs all pending changes
func (se *SyncEngine) syncPending() {
	se.mu.Lock()
	sessions := make([]string, 0, len(se.sessions))
	for sessionID := range se.sessions {
		sessions = append(sessions, sessionID)
	}
	se.mu.Unlock()

	for _, sessionID := range sessions {
		// Check if sync is needed
		if se.shouldSync(sessionID) {
			se.syncSession(sessionID)
		}
	}
}

// shouldSync determines if a session should sync
func (se *SyncEngine) shouldSync(sessionID string) bool {
	se.mu.RLock()
	lastSync, exists := se.lastSync[sessionID]
	se.mu.RUnlock()

	if !exists {
		return false
	}

	// Check time threshold
	if time.Since(lastSync) >= se.thresholds.TimeThreshold {
		return true
	}

	// Check queue size
	changes := se.changeQueue.GetSessionChanges(sessionID)
	return len(changes) >= se.thresholds.BatchSize
}

// syncSession syncs changes for a session
func (se *SyncEngine) syncSession(sessionID string) error {
	se.mu.Lock()
	session, exists := se.sessions[sessionID]
	if !exists {
		se.mu.Unlock()
		return fmt.Errorf("session %s not found", sessionID)
	}
	se.mu.Unlock()

	// Get pending changes
	changes := se.changeQueue.GetSessionChanges(sessionID)
	if len(changes) == 0 {
		return nil
	}

	// Batch changes
	batches := se.batchChanges(changes)

	// Apply each batch
	for _, batch := range batches {
		if err := se.applyBatch(session, batch); err != nil {
			// Mark failed changes
			for _, change := range batch {
				change.Rejected = true
				change.RejectionReason = err.Error()
			}
			continue
		}

		// Mark successful changes
		for _, change := range batch {
			change.Applied = true
		}
	}

	// Update last sync time
	se.mu.Lock()
	se.lastSync[sessionID] = time.Now()
	se.mu.Unlock()

	// Clear processed changes
	se.changeQueue.ClearSessionChanges(sessionID)

	return nil
}

// syncImmediate performs immediate sync for critical changes
func (se *SyncEngine) syncImmediate(sessionID string) error {
	return se.syncSession(sessionID)
}

// batchChanges groups changes into batches
func (se *SyncEngine) batchChanges(changes []*ARChange) [][]*ARChange {
	if len(changes) <= se.thresholds.BatchSize {
		return [][]*ARChange{changes}
	}

	batches := make([][]*ARChange, 0)
	for i := 0; i < len(changes); i += se.thresholds.BatchSize {
		end := i + se.thresholds.BatchSize
		if end > len(changes) {
			end = len(changes)
		}
		batches = append(batches, changes[i:end])
	}

	return batches
}

// applyBatch applies a batch of changes to BIM
func (se *SyncEngine) applyBatch(session *ARSession, batch []*ARChange) error {
	// Check for conflicts
	conflicts := se.detectConflicts(batch)
	if len(conflicts) > 0 {
		// Resolve conflicts
		resolved, err := se.resolveConflicts(conflicts)
		if err != nil {
			return fmt.Errorf("failed to resolve conflicts: %w", err)
		}
		batch = resolved
	}

	// Apply batch update
	return se.bimUpdater.BatchUpdate(batch)
}

// detectConflicts detects conflicts in a batch of changes
func (se *SyncEngine) detectConflicts(batch []*ARChange) []ChangeConflict {
	conflicts := make([]ChangeConflict, 0)

	// Check for duplicate equipment IDs
	equipmentChanges := make(map[string][]*ARChange)
	for _, change := range batch {
		equipmentChanges[change.EquipmentID] = append(
			equipmentChanges[change.EquipmentID], change)
	}

	// Find conflicts
	for equipmentID, changes := range equipmentChanges {
		if len(changes) > 1 {
			conflicts = append(conflicts, ChangeConflict{
				EquipmentID: equipmentID,
				Changes:     changes,
			})
		}
	}

	return conflicts
}

// ChangeConflict represents conflicting changes
type ChangeConflict struct {
	EquipmentID string
	Changes     []*ARChange
}

// resolveConflicts resolves change conflicts
func (se *SyncEngine) resolveConflicts(conflicts []ChangeConflict) ([]*ARChange, error) {
	resolved := make([]*ARChange, 0)

	for _, conflict := range conflicts {
		// Use most recent change with highest confidence
		best := conflict.Changes[0]
		for _, change := range conflict.Changes[1:] {
			if change.Timestamp.After(best.Timestamp) &&
				change.Confidence >= best.Confidence {
				best = change
			}
		}
		resolved = append(resolved, best)
	}

	return resolved, nil
}

// ChangeQueue manages the queue of AR changes
type ChangeQueue struct {
	changes      []*ARChange
	highPriority []*ARChange
	maxSize      int
	mu           sync.Mutex
}

// NewChangeQueue creates a new change queue
func NewChangeQueue(maxSize int) *ChangeQueue {
	return &ChangeQueue{
		changes:      make([]*ARChange, 0),
		highPriority: make([]*ARChange, 0),
		maxSize:      maxSize,
	}
}

// Add adds a change to the queue
func (cq *ChangeQueue) Add(change *ARChange) {
	cq.mu.Lock()
	defer cq.mu.Unlock()

	cq.changes = append(cq.changes, change)

	// Trim if exceeds max size
	if len(cq.changes) > cq.maxSize {
		cq.changes = cq.changes[len(cq.changes)-cq.maxSize:]
	}
}

// AddHighPriority adds a high priority change
func (cq *ChangeQueue) AddHighPriority(change *ARChange) {
	cq.mu.Lock()
	defer cq.mu.Unlock()

	cq.highPriority = append(cq.highPriority, change)
}

// GetSessionChanges gets all changes for a session
func (cq *ChangeQueue) GetSessionChanges(sessionID string) []*ARChange {
	cq.mu.Lock()
	defer cq.mu.Unlock()

	result := make([]*ARChange, 0)

	// Add high priority changes first
	for _, change := range cq.highPriority {
		if change.SessionID == sessionID && !change.Applied {
			result = append(result, change)
		}
	}

	// Add normal priority changes
	for _, change := range cq.changes {
		if change.SessionID == sessionID && !change.Applied {
			result = append(result, change)
		}
	}

	return result
}

// ClearSessionChanges clears processed changes for a session
func (cq *ChangeQueue) ClearSessionChanges(sessionID string) {
	cq.mu.Lock()
	defer cq.mu.Unlock()

	// Filter out applied changes
	filtered := make([]*ARChange, 0)
	for _, change := range cq.changes {
		if change.SessionID != sessionID || !change.Applied {
			filtered = append(filtered, change)
		}
	}
	cq.changes = filtered

	// Filter high priority
	filteredHP := make([]*ARChange, 0)
	for _, change := range cq.highPriority {
		if change.SessionID != sessionID || !change.Applied {
			filteredHP = append(filteredHP, change)
		}
	}
	cq.highPriority = filteredHP
}

// calculateRotationAngle calculates the angle between two rotations
func calculateRotationAngle(r1, r2 ARRotation) float64 {
	// Quaternion dot product
	dot := r1.X*r2.X + r1.Y*r2.Y + r1.Z*r2.Z + r1.W*r2.W

	// Clamp to avoid numerical errors
	if dot > 1.0 {
		dot = 1.0
	} else if dot < -1.0 {
		dot = -1.0
	}

	// Convert to degrees
	angle := 2.0 * math.Acos(math.Abs(dot)) * 180.0 / math.Pi
	return angle
}

// MockBIMUpdater is a mock implementation of BIMUpdater for testing
type MockBIMUpdater struct {
	updates []map[string]interface{}
	mu      sync.Mutex
}

// NewMockBIMUpdater creates a new mock BIM updater
func NewMockBIMUpdater() *MockBIMUpdater {
	return &MockBIMUpdater{
		updates: make([]map[string]interface{}, 0),
	}
}

// UpdateEquipment updates equipment in mock
func (m *MockBIMUpdater) UpdateEquipment(equipmentID string, changes map[string]interface{}) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	update := map[string]interface{}{
		"equipment_id": equipmentID,
		"changes":      changes,
		"timestamp":    time.Now(),
	}
	m.updates = append(m.updates, update)
	return nil
}

// AddEquipment adds equipment in mock
func (m *MockBIMUpdater) AddEquipment(equipment *EquipmentData) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	update := map[string]interface{}{
		"action":    "add",
		"equipment": equipment,
		"timestamp": time.Now(),
	}
	m.updates = append(m.updates, update)
	return nil
}

// RemoveEquipment removes equipment in mock
func (m *MockBIMUpdater) RemoveEquipment(equipmentID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	update := map[string]interface{}{
		"action":       "remove",
		"equipment_id": equipmentID,
		"timestamp":    time.Now(),
	}
	m.updates = append(m.updates, update)
	return nil
}

// BatchUpdate applies batch update in mock
func (m *MockBIMUpdater) BatchUpdate(changes []*ARChange) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	for _, change := range changes {
		update := map[string]interface{}{
			"change":    change,
			"timestamp": time.Now(),
		}
		m.updates = append(m.updates, update)
	}
	return nil
}

// GetUpdates returns all recorded updates
func (m *MockBIMUpdater) GetUpdates() []map[string]interface{} {
	m.mu.Lock()
	defer m.mu.Unlock()

	result := make([]map[string]interface{}, len(m.updates))
	copy(result, m.updates)
	return result
}

// SyncStatus represents the status of sync operations
type SyncStatus struct {
	SessionID       string    `json:"session_id"`
	LastSync        time.Time `json:"last_sync"`
	PendingChanges  int       `json:"pending_changes"`
	AppliedChanges  int       `json:"applied_changes"`
	RejectedChanges int       `json:"rejected_changes"`
	NextSync        time.Time `json:"next_sync"`
}

// GetSyncStatus returns sync status for a session
func (se *SyncEngine) GetSyncStatus(sessionID string) (*SyncStatus, error) {
	se.mu.RLock()
	lastSync, exists := se.lastSync[sessionID]
	se.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("session %s not found", sessionID)
	}

	changes := se.changeQueue.GetSessionChanges(sessionID)

	var applied, rejected int
	for _, change := range changes {
		if change.Applied {
			applied++
		} else if change.Rejected {
			rejected++
		}
	}

	return &SyncStatus{
		SessionID:       sessionID,
		LastSync:        lastSync,
		PendingChanges:  len(changes) - applied - rejected,
		AppliedChanges:  applied,
		RejectedChanges: rejected,
		NextSync:        lastSync.Add(se.thresholds.TimeThreshold),
	}, nil
}

// Close closes the sync engine
func (se *SyncEngine) Close() {
	se.cancel()
}
