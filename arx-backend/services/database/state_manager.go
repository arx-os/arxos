package database

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// StateType represents different types of application state
type StateType string

const (
	StateTypeSession   StateType = "session"
	StateTypeUser      StateType = "user"
	StateTypeProject   StateType = "project"
	StateTypeWorkflow  StateType = "workflow"
	StateTypeCache     StateType = "cache"
	StateTypeSystem    StateType = "system"
	StateTypeTemporary StateType = "temporary"
)

// StatePriority represents state priority levels
type StatePriority int

const (
	PriorityLow      StatePriority = 1
	PriorityNormal   StatePriority = 2
	PriorityHigh     StatePriority = 3
	PriorityCritical StatePriority = 4
)

// StateEntry represents a state entry in the database
type StateEntry struct {
	ID         string                 `json:"id" db:"id"`
	Type       StateType              `json:"type" db:"type"`
	Key        string                 `json:"key" db:"key"`
	Value      json.RawMessage        `json:"value" db:"value"`
	Priority   StatePriority          `json:"priority" db:"priority"`
	ExpiresAt  *time.Time             `json:"expires_at" db:"expires_at"`
	CreatedBy  string                 `json:"created_by" db:"created_by"`
	CreatedAt  time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at" db:"updated_at"`
	AccessedAt time.Time              `json:"accessed_at" db:"accessed_at"`
	Properties map[string]interface{} `json:"properties" db:"properties"`
}

// SessionState represents a user session state
type SessionState struct {
	SessionID   string                 `json:"session_id"`
	UserID      string                 `json:"user_id"`
	Username    string                 `json:"username"`
	Role        string                 `json:"role"`
	Permissions []string               `json:"permissions"`
	Data        map[string]interface{} `json:"data"`
	CreatedAt   time.Time              `json:"created_at"`
	LastAccess  time.Time              `json:"last_access"`
	ExpiresAt   time.Time              `json:"expires_at"`
}

// WorkflowState represents a workflow state
type WorkflowState struct {
	WorkflowID  string                 `json:"workflow_id"`
	Status      string                 `json:"status"`
	Step        string                 `json:"step"`
	Progress    int                    `json:"progress"`
	Data        map[string]interface{} `json:"data"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	CompletedAt *time.Time             `json:"completed_at"`
}

// StateManager provides state management functionality
type StateManager struct {
	dbService *DatabaseService
	logger    *zap.Logger
	mu        sync.RWMutex
	cache     map[string]*StateEntry
}

// NewStateManager creates a new state manager
func NewStateManager(logger *zap.Logger) *StateManager {
	return &StateManager{
		logger: logger,
		cache:  make(map[string]*StateEntry),
	}
}

// SetState sets a state entry
func (sm *StateManager) SetState(ctx context.Context, stateType StateType, key string, value interface{}, priority StatePriority, expiresAt *time.Time, createdBy string) error {
	stateID := fmt.Sprintf("%s:%s", stateType, key)

	valueJSON, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("failed to marshal state value: %w", err)
	}

	now := time.Now()
	state := &StateEntry{
		ID:         stateID,
		Type:       stateType,
		Key:        key,
		Value:      valueJSON,
		Priority:   priority,
		ExpiresAt:  expiresAt,
		CreatedBy:  createdBy,
		CreatedAt:  now,
		UpdatedAt:  now,
		AccessedAt: now,
		Properties: make(map[string]interface{}),
	}

	query := `
		INSERT INTO state_entries (
			id, type, key, value, priority, expires_at, created_by,
			created_at, updated_at, accessed_at, properties
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			value = EXCLUDED.value,
			priority = EXCLUDED.priority,
			expires_at = EXCLUDED.expires_at,
			updated_at = EXCLUDED.updated_at,
			accessed_at = EXCLUDED.accessed_at,
			properties = EXCLUDED.properties
	`

	propertiesJSON, _ := json.Marshal(state.Properties)

	_, err = sm.dbService.db.ExecContext(ctx, query,
		state.ID, state.Type, state.Key, state.Value, state.Priority, state.ExpiresAt, state.CreatedBy,
		state.CreatedAt, state.UpdatedAt, state.AccessedAt, propertiesJSON,
	)

	if err != nil {
		sm.logger.Error("Failed to set state", zap.String("state_id", stateID), zap.Error(err))
		return fmt.Errorf("failed to set state: %w", err)
	}

	// Update cache
	sm.mu.Lock()
	sm.cache[stateID] = state
	sm.mu.Unlock()

	sm.logger.Info("State set successfully", zap.String("state_id", stateID))
	return nil
}

// GetState retrieves a state entry
func (sm *StateManager) GetState(ctx context.Context, stateType StateType, key string) (*StateEntry, error) {
	stateID := fmt.Sprintf("%s:%s", stateType, key)

	// Check cache first
	sm.mu.RLock()
	if cached, exists := sm.cache[stateID]; exists {
		// Check if expired
		if cached.ExpiresAt != nil && time.Now().After(*cached.ExpiresAt) {
			sm.mu.RUnlock()
			sm.mu.Lock()
			delete(sm.cache, stateID)
			sm.mu.Unlock()
			return nil, fmt.Errorf("state expired: %s", stateID)
		}
		sm.mu.RUnlock()

		// Update access time
		cached.AccessedAt = time.Now()
		return cached, nil
	}
	sm.mu.RUnlock()

	// Load from database
	query := `
		SELECT id, type, key, value, priority, expires_at, created_by,
			   created_at, updated_at, accessed_at, properties
		FROM state_entries
		WHERE id = ?
	`

	var state StateEntry
	var propertiesJSON []byte

	err := sm.dbService.db.QueryRowContext(ctx, query, stateID).Scan(
		&state.ID, &state.Type, &state.Key, &state.Value, &state.Priority, &state.ExpiresAt, &state.CreatedBy,
		&state.CreatedAt, &state.UpdatedAt, &state.AccessedAt, &propertiesJSON,
	)

	if err != nil {
		return nil, fmt.Errorf("state not found: %s", stateID)
	}

	// Check if expired
	if state.ExpiresAt != nil && time.Now().After(*state.ExpiresAt) {
		sm.DeleteState(ctx, stateType, key)
		return nil, fmt.Errorf("state expired: %s", stateID)
	}

	// Parse JSON fields
	if len(propertiesJSON) > 0 {
		json.Unmarshal(propertiesJSON, &state.Properties)
	}

	// Update cache
	sm.mu.Lock()
	sm.cache[stateID] = &state
	sm.mu.Unlock()

	// Update access time
	state.AccessedAt = time.Now()
	sm.updateAccessTime(ctx, stateID)

	return &state, nil
}

// DeleteState deletes a state entry
func (sm *StateManager) DeleteState(ctx context.Context, stateType StateType, key string) error {
	stateID := fmt.Sprintf("%s:%s", stateType, key)

	query := `DELETE FROM state_entries WHERE id = ?`

	result, err := sm.dbService.db.ExecContext(ctx, query, stateID)
	if err != nil {
		sm.logger.Error("Failed to delete state", zap.String("state_id", stateID), zap.Error(err))
		return fmt.Errorf("failed to delete state: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("state not found: %s", stateID)
	}

	// Remove from cache
	sm.mu.Lock()
	delete(sm.cache, stateID)
	sm.mu.Unlock()

	sm.logger.Info("State deleted successfully", zap.String("state_id", stateID))
	return nil
}

// ListStates lists state entries with optional filtering
func (sm *StateManager) ListStates(ctx context.Context, stateType StateType, createdBy string) ([]*StateEntry, error) {
	query := `
		SELECT id, type, key, value, priority, expires_at, created_by,
			   created_at, updated_at, accessed_at, properties
		FROM state_entries
		WHERE 1=1
	`
	args := []interface{}{}

	if stateType != "" {
		query += " AND type = ?"
		args = append(args, stateType)
	}
	if createdBy != "" {
		query += " AND created_by = ?"
		args = append(args, createdBy)
	}
	query += " ORDER BY priority DESC, updated_at DESC"

	rows, err := sm.dbService.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list states: %w", err)
	}
	defer rows.Close()

	var states []*StateEntry
	for rows.Next() {
		var state StateEntry
		var propertiesJSON []byte

		err := rows.Scan(
			&state.ID, &state.Type, &state.Key, &state.Value, &state.Priority, &state.ExpiresAt, &state.CreatedBy,
			&state.CreatedAt, &state.UpdatedAt, &state.AccessedAt, &propertiesJSON,
		)
		if err != nil {
			sm.logger.Error("Failed to scan state row", zap.Error(err))
			continue
		}

		// Check if expired
		if state.ExpiresAt != nil && time.Now().After(*state.ExpiresAt) {
			continue
		}

		// Parse JSON fields
		if len(propertiesJSON) > 0 {
			json.Unmarshal(propertiesJSON, &state.Properties)
		}

		states = append(states, &state)
	}

	return states, nil
}

// CleanupExpiredStates removes expired state entries
func (sm *StateManager) CleanupExpiredStates(ctx context.Context) error {
	query := `DELETE FROM state_entries WHERE expires_at IS NOT NULL AND expires_at < ?`

	result, err := sm.dbService.db.ExecContext(ctx, query, time.Now())
	if err != nil {
		sm.logger.Error("Failed to cleanup expired states", zap.Error(err))
		return fmt.Errorf("failed to cleanup expired states: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	sm.logger.Info("Expired states cleaned up", zap.Int64("count", rowsAffected))

	// Clean up cache
	sm.mu.Lock()
	now := time.Now()
	for stateID, state := range sm.cache {
		if state.ExpiresAt != nil && now.After(*state.ExpiresAt) {
			delete(sm.cache, stateID)
		}
	}
	sm.mu.Unlock()

	return nil
}

// SaveSessionState saves a session state
func (sm *StateManager) SaveSessionState(ctx context.Context, session *SessionState) error {
	return sm.SetState(ctx, StateTypeSession, session.SessionID, session, PriorityHigh, &session.ExpiresAt, session.UserID)
}

// LoadSessionState loads a session state
func (sm *StateManager) LoadSessionState(ctx context.Context, sessionID string) (*SessionState, error) {
	state, err := sm.GetState(ctx, StateTypeSession, sessionID)
	if err != nil {
		return nil, err
	}

	var session SessionState
	if err := json.Unmarshal(state.Value, &session); err != nil {
		return nil, fmt.Errorf("failed to unmarshal session state: %w", err)
	}

	return &session, nil
}

// DeleteSessionState deletes a session state
func (sm *StateManager) DeleteSessionState(ctx context.Context, sessionID string) error {
	return sm.DeleteState(ctx, StateTypeSession, sessionID)
}

// SaveWorkflowState saves a workflow state
func (sm *StateManager) SaveWorkflowState(ctx context.Context, workflow *WorkflowState) error {
	return sm.SetState(ctx, StateTypeWorkflow, workflow.WorkflowID, workflow, PriorityNormal, nil, "")
}

// LoadWorkflowState loads a workflow state
func (sm *StateManager) LoadWorkflowState(ctx context.Context, workflowID string) (*WorkflowState, error) {
	state, err := sm.GetState(ctx, StateTypeWorkflow, workflowID)
	if err != nil {
		return nil, err
	}

	var workflow WorkflowState
	if err := json.Unmarshal(state.Value, &workflow); err != nil {
		return nil, fmt.Errorf("failed to unmarshal workflow state: %w", err)
	}

	return &workflow, nil
}

// DeleteWorkflowState deletes a workflow state
func (sm *StateManager) DeleteWorkflowState(ctx context.Context, workflowID string) error {
	return sm.DeleteState(ctx, StateTypeWorkflow, workflowID)
}

// GetStateStats returns state statistics
func (sm *StateManager) GetStateStats(ctx context.Context) map[string]interface{} {
	query := `
		SELECT 
			type,
			COUNT(*) as count,
			COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < ? THEN 1 END) as expired_count
		FROM state_entries
		GROUP BY type
	`

	rows, err := sm.dbService.db.QueryContext(ctx, query, time.Now())
	if err != nil {
		sm.logger.Error("Failed to get state stats", zap.Error(err))
		return map[string]interface{}{}
	}
	defer rows.Close()

	stats := make(map[string]interface{})
	for rows.Next() {
		var stateType string
		var count, expiredCount int

		if err := rows.Scan(&stateType, &count, &expiredCount); err != nil {
			continue
		}

		stats[stateType] = map[string]interface{}{
			"total_count":   count,
			"expired_count": expiredCount,
			"active_count":  count - expiredCount,
		}
	}

	// Add cache stats
	sm.mu.RLock()
	cacheStats := map[string]interface{}{
		"cache_size": len(sm.cache),
	}
	sm.mu.RUnlock()

	stats["cache"] = cacheStats

	return stats
}

// updateAccessTime updates the access time for a state entry
func (sm *StateManager) updateAccessTime(ctx context.Context, stateID string) {
	query := `UPDATE state_entries SET accessed_at = ? WHERE id = ?`

	_, err := sm.dbService.db.ExecContext(ctx, query, time.Now(), stateID)
	if err != nil {
		sm.logger.Error("Failed to update state access time", zap.String("state_id", stateID), zap.Error(err))
	}
}

// initializeStateSchema creates the state_entries table
func (sm *StateManager) initializeStateSchema() error {
	schema := `
	CREATE TABLE IF NOT EXISTS state_entries (
		id TEXT PRIMARY KEY,
		type TEXT NOT NULL,
		key TEXT NOT NULL,
		value TEXT NOT NULL,
		priority INTEGER DEFAULT 2,
		expires_at DATETIME,
		created_by TEXT,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		properties TEXT
	);

	CREATE INDEX IF NOT EXISTS idx_state_entries_type ON state_entries(type);
	CREATE INDEX IF NOT EXISTS idx_state_entries_created_by ON state_entries(created_by);
	CREATE INDEX IF NOT EXISTS idx_state_entries_expires_at ON state_entries(expires_at);
	CREATE INDEX IF NOT EXISTS idx_state_entries_priority ON state_entries(priority);
	`

	_, err := sm.dbService.db.Exec(schema)
	if err != nil {
		return fmt.Errorf("failed to initialize state schema: %w", err)
	}

	return nil
}
