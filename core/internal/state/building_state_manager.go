package state

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/pkg/errors"
)

// BuildingState represents a complete snapshot of a building at a point in time
type BuildingState struct {
	ID           string    `db:"id" json:"id"`
	BuildingID   string    `db:"building_id" json:"building_id"`
	Version      string    `db:"version" json:"version"`
	StateHash    string    `db:"state_hash" json:"state_hash"`
	MerkleRoot   string    `db:"merkle_root" json:"merkle_root,omitempty"`
	ParentStateID *string  `db:"parent_state_id" json:"parent_state_id,omitempty"`
	BranchName   string    `db:"branch_name" json:"branch_name"`
	
	// State data
	ArxObjectSnapshot json.RawMessage `db:"arxobject_snapshot" json:"arxobject_snapshot"`
	SystemsState      json.RawMessage `db:"systems_state" json:"systems_state"`
	PerformanceMetrics json.RawMessage `db:"performance_metrics" json:"performance_metrics,omitempty"`
	ComplianceStatus  json.RawMessage `db:"compliance_status" json:"compliance_status,omitempty"`
	
	// Metadata
	AuthorID      string    `db:"author_id" json:"author_id"`
	AuthorName    string    `db:"author_name" json:"author_name"`
	Message       string    `db:"message" json:"message"`
	Tags          []string  `db:"tags" json:"tags,omitempty"`
	ArxObjectCount int      `db:"arxobject_count" json:"arxobject_count"`
	TotalSizeBytes int64    `db:"total_size_bytes" json:"total_size_bytes,omitempty"`
	
	// Timestamps
	CreatedAt   time.Time `db:"created_at" json:"created_at"`
	CapturedAt  time.Time `db:"captured_at" json:"captured_at"`
	
	// Additional metadata
	Metadata    json.RawMessage `db:"metadata" json:"metadata,omitempty"`
}

// StateTransition represents a change from one state to another
type StateTransition struct {
	ID          string    `db:"id" json:"id"`
	BuildingID  string    `db:"building_id" json:"building_id"`
	FromStateID *string   `db:"from_state_id" json:"from_state_id,omitempty"`
	ToStateID   string    `db:"to_state_id" json:"to_state_id"`
	TransitionType string `db:"transition_type" json:"transition_type"`
	InitiatedBy string    `db:"initiated_by" json:"initiated_by"`
	InitiatedByName string `db:"initiated_by_name" json:"initiated_by_name"`
	Reason      string    `db:"reason" json:"reason,omitempty"`
	
	// Details
	ChangesSummary    json.RawMessage `db:"changes_summary" json:"changes_summary,omitempty"`
	AffectedSystems   []string        `db:"affected_systems" json:"affected_systems,omitempty"`
	ValidationResults json.RawMessage `db:"validation_results" json:"validation_results,omitempty"`
	
	// Timing
	InitiatedAt  time.Time  `db:"initiated_at" json:"initiated_at"`
	CompletedAt  *time.Time `db:"completed_at" json:"completed_at,omitempty"`
	DurationMs   *int       `db:"duration_ms" json:"duration_ms,omitempty"`
	
	// Status
	Status       string `db:"status" json:"status"`
	ErrorDetails string `db:"error_details" json:"error_details,omitempty"`
	
	Metadata     json.RawMessage `db:"metadata" json:"metadata,omitempty"`
}

// StateBranch represents a branch in the building's version history
type StateBranch struct {
	ID          string    `db:"id" json:"id"`
	BuildingID  string    `db:"building_id" json:"building_id"`
	BranchName  string    `db:"branch_name" json:"branch_name"`
	BaseStateID *string   `db:"base_state_id" json:"base_state_id,omitempty"`
	HeadStateID *string   `db:"head_state_id" json:"head_state_id,omitempty"`
	
	// Metadata
	Description      string          `db:"description" json:"description,omitempty"`
	IsProtected      bool            `db:"is_protected" json:"is_protected"`
	IsDefault        bool            `db:"is_default" json:"is_default"`
	MergeRequirements json.RawMessage `db:"merge_requirements" json:"merge_requirements,omitempty"`
	
	// Ownership
	CreatedBy     string    `db:"created_by" json:"created_by"`
	CreatedByName string    `db:"created_by_name" json:"created_by_name"`
	CreatedAt     time.Time `db:"created_at" json:"created_at"`
	UpdatedAt     time.Time `db:"updated_at" json:"updated_at"`
	
	// Statistics
	CommitsAhead  int        `db:"commits_ahead" json:"commits_ahead"`
	CommitsBehind int        `db:"commits_behind" json:"commits_behind"`
	LastActivityAt *time.Time `db:"last_activity_at" json:"last_activity_at,omitempty"`
	
	Metadata      json.RawMessage `db:"metadata" json:"metadata,omitempty"`
}

// CaptureOptions defines options for capturing building state
type CaptureOptions struct {
	Message       string
	AuthorID      string
	AuthorName    string
	Tags          []string
	IncludeMetrics bool
	IncludeCompliance bool
}

// Manager handles building state management operations
type Manager struct {
	db *sqlx.DB
}

// NewManager creates a new BuildingStateManager
func NewManager(db *sqlx.DB) *Manager {
	return &Manager{
		db: db,
	}
}

// CaptureState captures the current state of a building
func (m *Manager) CaptureState(ctx context.Context, buildingID string, branch string, opts CaptureOptions) (*BuildingState, error) {
	// Begin transaction
	tx, err := m.db.BeginTxx(ctx, nil)
	if err != nil {
		return nil, errors.Wrap(err, "failed to begin transaction")
	}
	defer tx.Rollback()

	// Get current branch info
	var currentBranch StateBranch
	err = tx.GetContext(ctx, &currentBranch, `
		SELECT * FROM state_branches 
		WHERE building_id = $1 AND branch_name = $2
	`, buildingID, branch)
	if err != nil {
		// Create branch if it doesn't exist
		if branch != "main" {
			return nil, errors.Wrap(err, "branch not found")
		}
		// Create main branch
		currentBranch = StateBranch{
			ID:         uuid.New().String(),
			BuildingID: buildingID,
			BranchName: "main",
			IsDefault:  true,
			CreatedBy:  opts.AuthorID,
			CreatedByName: opts.AuthorName,
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		_, err = tx.NamedExecContext(ctx, `
			INSERT INTO state_branches (
				id, building_id, branch_name, is_default, 
				created_by, created_by_name, created_at, updated_at
			) VALUES (
				:id, :building_id, :branch_name, :is_default,
				:created_by, :created_by_name, :created_at, :updated_at
			)
		`, currentBranch)
		if err != nil {
			return nil, errors.Wrap(err, "failed to create main branch")
		}
	}

	// Fetch current ArxObjects
	arxObjectSnapshot, err := m.fetchArxObjectSnapshot(ctx, tx, buildingID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to fetch ArxObject snapshot")
	}

	// Fetch systems state
	systemsState, err := m.fetchSystemsState(ctx, tx, buildingID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to fetch systems state")
	}

	// Calculate state hash
	stateHash := m.calculateStateHash(arxObjectSnapshot, systemsState)

	// Check if this exact state already exists
	var existingState BuildingState
	err = tx.GetContext(ctx, &existingState, `
		SELECT * FROM building_states 
		WHERE building_id = $1 AND state_hash = $2 AND branch_name = $3
		LIMIT 1
	`, buildingID, stateHash, branch)
	if err == nil {
		// State hasn't changed
		return &existingState, nil
	}

	// Generate new version
	newVersion, err := m.generateNextVersion(ctx, tx, buildingID, branch)
	if err != nil {
		return nil, errors.Wrap(err, "failed to generate version")
	}

	// Create new state
	newState := BuildingState{
		ID:                uuid.New().String(),
		BuildingID:        buildingID,
		Version:           newVersion,
		StateHash:         stateHash,
		ParentStateID:     currentBranch.HeadStateID,
		BranchName:        branch,
		ArxObjectSnapshot: arxObjectSnapshot,
		SystemsState:      systemsState,
		AuthorID:          opts.AuthorID,
		AuthorName:        opts.AuthorName,
		Message:           opts.Message,
		Tags:              opts.Tags,
		ArxObjectCount:    m.countArxObjects(arxObjectSnapshot),
		TotalSizeBytes:    int64(len(arxObjectSnapshot) + len(systemsState)),
		CreatedAt:         time.Now(),
		CapturedAt:        time.Now(),
	}

	// Optional: Include performance metrics
	if opts.IncludeMetrics {
		metrics, _ := m.fetchPerformanceMetrics(ctx, tx, buildingID)
		newState.PerformanceMetrics = metrics
	}

	// Optional: Include compliance status
	if opts.IncludeCompliance {
		compliance, _ := m.fetchComplianceStatus(ctx, tx, buildingID)
		newState.ComplianceStatus = compliance
	}

	// Insert new state
	_, err = tx.NamedExecContext(ctx, `
		INSERT INTO building_states (
			id, building_id, version, state_hash, merkle_root, parent_state_id,
			branch_name, arxobject_snapshot, systems_state, performance_metrics,
			compliance_status, author_id, author_name, message, tags,
			arxobject_count, total_size_bytes, created_at, captured_at, metadata
		) VALUES (
			:id, :building_id, :version, :state_hash, :merkle_root, :parent_state_id,
			:branch_name, :arxobject_snapshot, :systems_state, :performance_metrics,
			:compliance_status, :author_id, :author_name, :message, :tags,
			:arxobject_count, :total_size_bytes, :created_at, :captured_at, :metadata
		)
	`, newState)
	if err != nil {
		return nil, errors.Wrap(err, "failed to insert state")
	}

	// Update branch HEAD
	_, err = tx.ExecContext(ctx, `
		UPDATE state_branches 
		SET head_state_id = $1, updated_at = $2, last_activity_at = $3
		WHERE id = $4
	`, newState.ID, time.Now(), time.Now(), currentBranch.ID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to update branch HEAD")
	}

	// Record transition
	transition := StateTransition{
		ID:              uuid.New().String(),
		BuildingID:      buildingID,
		FromStateID:     currentBranch.HeadStateID,
		ToStateID:       newState.ID,
		TransitionType:  "capture",
		InitiatedBy:     opts.AuthorID,
		InitiatedByName: opts.AuthorName,
		Reason:          opts.Message,
		InitiatedAt:     time.Now(),
		Status:          "completed",
	}

	_, err = tx.NamedExecContext(ctx, `
		INSERT INTO state_transitions (
			id, building_id, from_state_id, to_state_id, transition_type,
			initiated_by, initiated_by_name, reason, initiated_at, status
		) VALUES (
			:id, :building_id, :from_state_id, :to_state_id, :transition_type,
			:initiated_by, :initiated_by_name, :reason, :initiated_at, :status
		)
	`, transition)
	if err != nil {
		return nil, errors.Wrap(err, "failed to record transition")
	}

	// Commit transaction
	if err = tx.Commit(); err != nil {
		return nil, errors.Wrap(err, "failed to commit transaction")
	}

	return &newState, nil
}

// GetState retrieves a specific state by ID
func (m *Manager) GetState(ctx context.Context, stateID string) (*BuildingState, error) {
	var state BuildingState
	err := m.db.GetContext(ctx, &state, `
		SELECT * FROM building_states WHERE id = $1
	`, stateID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to get state")
	}
	return &state, nil
}

// GetStateByVersion retrieves a state by building ID, version, and branch
func (m *Manager) GetStateByVersion(ctx context.Context, buildingID, version, branch string) (*BuildingState, error) {
	var state BuildingState
	err := m.db.GetContext(ctx, &state, `
		SELECT * FROM building_states 
		WHERE building_id = $1 AND version = $2 AND branch_name = $3
	`, buildingID, version, branch)
	if err != nil {
		return nil, errors.Wrap(err, "failed to get state by version")
	}
	return &state, nil
}

// ListStates lists all states for a building with pagination
func (m *Manager) ListStates(ctx context.Context, buildingID string, branch string, limit, offset int) ([]*BuildingState, error) {
	var states []*BuildingState
	query := `
		SELECT * FROM building_states 
		WHERE building_id = $1 AND branch_name = $2
		ORDER BY created_at DESC
		LIMIT $3 OFFSET $4
	`
	err := m.db.SelectContext(ctx, &states, query, buildingID, branch, limit, offset)
	if err != nil {
		return nil, errors.Wrap(err, "failed to list states")
	}
	return states, nil
}

// RestoreState restores a building to a previous state
func (m *Manager) RestoreState(ctx context.Context, buildingID, targetStateID string, opts CaptureOptions) error {
	// Begin transaction
	tx, err := m.db.BeginTxx(ctx, nil)
	if err != nil {
		return errors.Wrap(err, "failed to begin transaction")
	}
	defer tx.Rollback()

	// Get target state
	var targetState BuildingState
	err = tx.GetContext(ctx, &targetState, `
		SELECT * FROM building_states WHERE id = $1 AND building_id = $2
	`, targetStateID, buildingID)
	if err != nil {
		return errors.Wrap(err, "target state not found")
	}

	// Apply the state to the building
	err = m.applyStateToBuilding(ctx, tx, &targetState)
	if err != nil {
		return errors.Wrap(err, "failed to apply state")
	}

	// Create a new state record for the restoration
	restoredState, err := m.CaptureState(ctx, buildingID, targetState.BranchName, CaptureOptions{
		Message:    fmt.Sprintf("Restored to version %s: %s", targetState.Version, opts.Message),
		AuthorID:   opts.AuthorID,
		AuthorName: opts.AuthorName,
	})
	if err != nil {
		return errors.Wrap(err, "failed to capture restored state")
	}

	// Record the restoration transition
	transition := StateTransition{
		ID:              uuid.New().String(),
		BuildingID:      buildingID,
		FromStateID:     &targetState.ID,
		ToStateID:       restoredState.ID,
		TransitionType:  "restore",
		InitiatedBy:     opts.AuthorID,
		InitiatedByName: opts.AuthorName,
		Reason:          opts.Message,
		InitiatedAt:     time.Now(),
		Status:          "completed",
	}

	_, err = tx.NamedExecContext(ctx, `
		INSERT INTO state_transitions (
			id, building_id, from_state_id, to_state_id, transition_type,
			initiated_by, initiated_by_name, reason, initiated_at, status
		) VALUES (
			:id, :building_id, :from_state_id, :to_state_id, :transition_type,
			:initiated_by, :initiated_by_name, :reason, :initiated_at, :status
		)
	`, transition)
	if err != nil {
		return errors.Wrap(err, "failed to record restoration transition")
	}

	// Commit transaction
	if err = tx.Commit(); err != nil {
		return errors.Wrap(err, "failed to commit transaction")
	}

	return nil
}

// Helper methods

func (m *Manager) fetchArxObjectSnapshot(ctx context.Context, tx *sqlx.Tx, buildingID string) (json.RawMessage, error) {
	var objects []json.RawMessage
	err := tx.SelectContext(ctx, &objects, `
		SELECT row_to_json(a.*) 
		FROM arx_objects a 
		WHERE building_id = $1
		ORDER BY id
	`, buildingID)
	if err != nil {
		return nil, err
	}
	
	snapshot, err := json.Marshal(objects)
	if err != nil {
		return nil, err
	}
	
	return snapshot, nil
}

func (m *Manager) fetchSystemsState(ctx context.Context, tx *sqlx.Tx, buildingID string) (json.RawMessage, error) {
	// Placeholder for systems state fetching
	// This would aggregate HVAC, electrical, plumbing, etc.
	systemsState := map[string]interface{}{
		"hvac": map[string]interface{}{
			"status": "operational",
			"setpoints": map[string]float64{
				"temperature": 72.0,
				"humidity": 45.0,
			},
		},
		"electrical": map[string]interface{}{
			"status": "operational",
			"load_percentage": 65.0,
		},
		"timestamp": time.Now(),
	}
	
	return json.Marshal(systemsState)
}

func (m *Manager) fetchPerformanceMetrics(ctx context.Context, tx *sqlx.Tx, buildingID string) (json.RawMessage, error) {
	// Placeholder for performance metrics
	metrics := map[string]interface{}{
		"energy_usage_kwh": 1250.5,
		"occupancy_rate": 0.85,
		"response_time_ms": 125,
		"timestamp": time.Now(),
	}
	return json.Marshal(metrics)
}

func (m *Manager) fetchComplianceStatus(ctx context.Context, tx *sqlx.Tx, buildingID string) (json.RawMessage, error) {
	// Placeholder for compliance status
	compliance := map[string]interface{}{
		"fire_safety": "compliant",
		"ada": "compliant",
		"energy_star": "pending",
		"last_inspection": time.Now().AddDate(0, -3, 0),
	}
	return json.Marshal(compliance)
}

func (m *Manager) calculateStateHash(arxObjects, systemsState json.RawMessage) string {
	h := sha256.New()
	h.Write(arxObjects)
	h.Write(systemsState)
	return hex.EncodeToString(h.Sum(nil))
}

func (m *Manager) countArxObjects(snapshot json.RawMessage) int {
	var objects []interface{}
	if err := json.Unmarshal(snapshot, &objects); err != nil {
		return 0
	}
	return len(objects)
}

func (m *Manager) generateNextVersion(ctx context.Context, tx *sqlx.Tx, buildingID, branch string) (string, error) {
	var lastVersion string
	err := tx.GetContext(ctx, &lastVersion, `
		SELECT version FROM building_states 
		WHERE building_id = $1 AND branch_name = $2
		ORDER BY created_at DESC
		LIMIT 1
	`, buildingID, branch)
	
	if err != nil {
		// First version
		return "1.0.0", nil
	}
	
	// Simple version increment (patch level)
	// In production, would parse semantic version properly
	return incrementVersion(lastVersion), nil
}

func incrementVersion(version string) string {
	// Simple implementation - in production use proper semver library
	// For now, just increment patch version
	var major, minor, patch int
	fmt.Sscanf(version, "%d.%d.%d", &major, &minor, &patch)
	return fmt.Sprintf("%d.%d.%d", major, minor, patch+1)
}

func (m *Manager) applyStateToBuilding(ctx context.Context, tx *sqlx.Tx, state *BuildingState) error {
	// This would restore ArxObjects and system configurations
	// For now, this is a placeholder
	// In production, would:
	// 1. Clear current ArxObjects
	// 2. Insert ArxObjects from snapshot
	// 3. Update system configurations
	// 4. Trigger any necessary hardware updates
	return nil
}