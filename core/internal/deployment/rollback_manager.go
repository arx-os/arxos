package deployment

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/pkg/errors"
	
	"github.com/arxos/core/internal/state"
)

// RollbackManager handles deployment rollback operations
type RollbackManager struct {
	db           *sqlx.DB
	controller   *Controller
	stateManager *state.Manager
	mu           sync.RWMutex
	activeRollbacks map[string]*RollbackExecution
}

// RollbackExecution tracks an active rollback operation
type RollbackExecution struct {
	RollbackID   string
	DeploymentID string
	Deployment   *Deployment
	Targets      []*DeploymentTarget
	Scope        string // full, partial, single_building
	StartTime    time.Time
	Context      context.Context
	Cancel       context.CancelFunc
}

// RollbackResult represents the result of a rollback operation
type RollbackResult struct {
	Success         bool          `json:"success"`
	RollbackID      string        `json:"rollback_id"`
	DeploymentID    string        `json:"deployment_id"`
	SuccessfulCount int           `json:"successful_count"`
	FailedCount     int           `json:"failed_count"`
	Duration        time.Duration `json:"duration"`
	Errors          []string      `json:"errors,omitempty"`
}

// NewRollbackManager creates a new rollback manager
func NewRollbackManager(db *sqlx.DB, controller *Controller, stateManager *state.Manager) *RollbackManager {
	return &RollbackManager{
		db:              db,
		controller:      controller,
		stateManager:    stateManager,
		activeRollbacks: make(map[string]*RollbackExecution),
	}
}

// RollbackDeployment initiates a deployment rollback
func (rm *RollbackManager) RollbackDeployment(ctx context.Context, req *RollbackRequest) (*RollbackResult, error) {
	// Validate request
	if err := req.Validate(); err != nil {
		return nil, errors.Wrap(err, "invalid rollback request")
	}

	// Get deployment
	deployment, err := rm.controller.GetDeployment(ctx, req.DeploymentID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to get deployment")
	}

	// Check if deployment can be rolled back
	if !deployment.RollbackEnabled {
		return nil, fmt.Errorf("rollback is not enabled for this deployment")
	}

	if deployment.Status != string(StatusCompleted) && deployment.Status != string(StatusFailed) && !req.Force {
		return nil, fmt.Errorf("deployment must be completed or failed to rollback (status: %s)", deployment.Status)
	}

	// Get affected targets based on scope
	targets, err := rm.getAffectedTargets(ctx, deployment, req)
	if err != nil {
		return nil, errors.Wrap(err, "failed to determine rollback targets")
	}

	if len(targets) == 0 {
		return nil, fmt.Errorf("no targets to rollback")
	}

	// Create rollback record
	rollbackID := uuid.New().String()
	rollback := &DeploymentRollback{
		ID:               rollbackID,
		DeploymentID:     deployment.ID,
		TriggeredBy:      "manual",
		TriggeredByUser:  req.TriggeredBy,
		TriggeredByName:  req.TriggeredByName,
		TriggeredAt:      time.Now(),
		Scope:            req.Scope,
		AffectedBuildings: extractBuildingIDs(targets),
		Reason:           req.Reason,
		Status:           "in_progress",
	}

	// Insert rollback record
	if err := rm.insertRollbackRecord(ctx, rollback); err != nil {
		return nil, errors.Wrap(err, "failed to create rollback record")
	}

	// Create execution context
	execCtx, cancel := context.WithCancel(ctx)
	execution := &RollbackExecution{
		RollbackID:   rollbackID,
		DeploymentID: deployment.ID,
		Deployment:   deployment,
		Targets:      targets,
		Scope:        req.Scope,
		StartTime:    time.Now(),
		Context:      execCtx,
		Cancel:       cancel,
	}

	// Register active rollback
	rm.mu.Lock()
	rm.activeRollbacks[rollbackID] = execution
	rm.mu.Unlock()

	// Execute rollback asynchronously
	go rm.executeRollbackAsync(execution, rollback)

	// Return immediate response
	return &RollbackResult{
		Success:      true,
		RollbackID:   rollbackID,
		DeploymentID: deployment.ID,
	}, nil
}

// executeRollbackAsync performs the rollback operation
func (rm *RollbackManager) executeRollbackAsync(execution *RollbackExecution, rollback *DeploymentRollback) {
	defer func() {
		// Clean up
		rm.mu.Lock()
		delete(rm.activeRollbacks, execution.RollbackID)
		rm.mu.Unlock()
		
		execution.Cancel()
	}()

	startTime := time.Now()
	var wg sync.WaitGroup
	successCount := 0
	failedCount := 0
	errorsChan := make(chan error, len(execution.Targets))
	successChan := make(chan string, len(execution.Targets))

	// Rollback each target
	for _, target := range execution.Targets {
		wg.Add(1)
		go func(t *DeploymentTarget) {
			defer wg.Done()
			
			if err := rm.rollbackTarget(execution.Context, t); err != nil {
				errorsChan <- fmt.Errorf("failed to rollback %s: %w", t.BuildingID, err)
			} else {
				successChan <- t.BuildingID
			}
		}(target)
	}

	// Wait for all rollbacks to complete
	wg.Wait()
	close(errorsChan)
	close(successChan)

	// Collect results
	var errors []string
	for err := range errorsChan {
		errors = append(errors, err.Error())
		failedCount++
	}
	
	for range successChan {
		successCount++
	}

	// Update rollback record
	duration := time.Since(startTime)
	rollback.CompletedAt = &startTime
	rollback.DurationMs = int(duration.Milliseconds())
	rollback.SuccessfulCount = successCount
	rollback.FailedCount = failedCount
	
	if failedCount > 0 {
		rollback.Status = "partial"
		rollback.ErrorLog = errors
	} else {
		rollback.Status = "completed"
	}

	// Update database
	rm.updateRollbackRecord(context.Background(), rollback)

	// Update deployment status
	if failedCount == 0 {
		rm.controller.updateDeploymentStatus(context.Background(), execution.DeploymentID, StatusRolledBack)
	}

	// Emit rollback event
	rm.controller.monitor.EmitEvent(DeploymentRolledBackEvent{
		DeploymentID:    execution.DeploymentID,
		Reason:          rollback.Reason,
		AffectedTargets: rollback.AffectedBuildings,
	})
}

// rollbackTarget rolls back a single target
func (rm *RollbackManager) rollbackTarget(ctx context.Context, target *DeploymentTarget) error {
	// Check if target has a previous state to rollback to
	if target.PreviousStateID == "" {
		return fmt.Errorf("no previous state available for rollback")
	}

	// Perform the state restoration
	err := rm.stateManager.RestoreState(ctx, target.BuildingID, target.PreviousStateID, state.CaptureOptions{
		Message:    fmt.Sprintf("Rollback from deployment %s", target.DeploymentID),
		AuthorID:   "system",
		AuthorName: "Rollback System",
	})
	
	if err != nil {
		// Update target status
		target.Status = "rollback_failed"
		target.ErrorMessage = fmt.Sprintf("Rollback failed: %v", err)
		rm.controller.updateTargetStatus(ctx, target)
		return err
	}

	// Update target status
	target.Status = "rolled_back"
	completedTime := time.Now()
	target.CompletedAt = &completedTime
	rm.controller.updateTargetStatus(ctx, target)

	return nil
}

// AutoRollback performs automatic rollback based on health checks
func (rm *RollbackManager) AutoRollback(ctx context.Context, deploymentID string, reason string) error {
	// Get deployment
	deployment, err := rm.controller.GetDeployment(ctx, deploymentID)
	if err != nil {
		return errors.Wrap(err, "failed to get deployment")
	}

	if !deployment.RollbackEnabled {
		return fmt.Errorf("automatic rollback is not enabled for this deployment")
	}

	// Get failed targets
	failedTargets, err := rm.getFailedTargets(ctx, deploymentID)
	if err != nil {
		return errors.Wrap(err, "failed to get failed targets")
	}

	if len(failedTargets) == 0 {
		return nil // Nothing to rollback
	}

	// Create automatic rollback request
	req := &RollbackRequest{
		DeploymentID: deploymentID,
		Scope:        "partial",
		Buildings:    extractBuildingIDs(failedTargets),
		Reason:       fmt.Sprintf("Automatic rollback: %s", reason),
		Force:        true,
	}

	// Execute rollback
	result, err := rm.RollbackDeployment(ctx, req)
	if err != nil {
		return errors.Wrap(err, "automatic rollback failed")
	}

	fmt.Printf("Automatic rollback initiated: %s\n", result.RollbackID)
	return nil
}

// GetRollbackStatus returns the status of a rollback operation
func (rm *RollbackManager) GetRollbackStatus(ctx context.Context, rollbackID string) (*DeploymentRollback, error) {
	var rollback DeploymentRollback
	err := rm.db.GetContext(ctx, &rollback, `
		SELECT * FROM deployment_rollbacks WHERE id = $1
	`, rollbackID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to get rollback status")
	}
	return &rollback, nil
}

// ListRollbacks lists rollback operations for a deployment
func (rm *RollbackManager) ListRollbacks(ctx context.Context, deploymentID string) ([]*DeploymentRollback, error) {
	var rollbacks []*DeploymentRollback
	err := rm.db.SelectContext(ctx, &rollbacks, `
		SELECT * FROM deployment_rollbacks 
		WHERE deployment_id = $1 
		ORDER BY triggered_at DESC
	`, deploymentID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to list rollbacks")
	}
	return rollbacks, nil
}

// Helper methods

func (rm *RollbackManager) getAffectedTargets(ctx context.Context, deployment *Deployment, req *RollbackRequest) ([]*DeploymentTarget, error) {
	switch req.Scope {
	case "full":
		// Get all deployment targets
		return rm.controller.GetDeploymentTargets(ctx, deployment.ID)
		
	case "partial":
		// Get specific building targets
		if len(req.Buildings) == 0 {
			return nil, fmt.Errorf("no buildings specified for partial rollback")
		}
		
		var targets []*DeploymentTarget
		query := `
			SELECT * FROM deployment_targets 
			WHERE deployment_id = $1 AND building_id = ANY($2)
		`
		err := rm.db.SelectContext(ctx, &targets, query, deployment.ID, req.Buildings)
		return targets, err
		
	case "single_building":
		// Get single building target
		if len(req.Buildings) != 1 {
			return nil, fmt.Errorf("exactly one building must be specified for single building rollback")
		}
		
		var target DeploymentTarget
		err := rm.db.GetContext(ctx, &target, `
			SELECT * FROM deployment_targets 
			WHERE deployment_id = $1 AND building_id = $2
		`, deployment.ID, req.Buildings[0])
		if err != nil {
			return nil, err
		}
		return []*DeploymentTarget{&target}, nil
		
	default:
		return nil, fmt.Errorf("invalid rollback scope: %s", req.Scope)
	}
}

func (rm *RollbackManager) getFailedTargets(ctx context.Context, deploymentID string) ([]*DeploymentTarget, error) {
	var targets []*DeploymentTarget
	err := rm.db.SelectContext(ctx, &targets, `
		SELECT * FROM deployment_targets 
		WHERE deployment_id = $1 AND status = 'failed'
	`, deploymentID)
	return targets, err
}

func (rm *RollbackManager) insertRollbackRecord(ctx context.Context, rollback *DeploymentRollback) error {
	_, err := rm.db.NamedExecContext(ctx, `
		INSERT INTO deployment_rollbacks (
			id, deployment_id, triggered_by, triggered_by_user, triggered_by_name,
			triggered_at, scope, affected_buildings, reason, status
		) VALUES (
			:id, :deployment_id, :triggered_by, :triggered_by_user, :triggered_by_name,
			:triggered_at, :scope, :affected_buildings, :reason, :status
		)
	`, rollback)
	return err
}

func (rm *RollbackManager) updateRollbackRecord(ctx context.Context, rollback *DeploymentRollback) error {
	_, err := rm.db.NamedExecContext(ctx, `
		UPDATE deployment_rollbacks SET
			completed_at = :completed_at,
			duration_ms = :duration_ms,
			status = :status,
			successful_count = :successful_count,
			failed_count = :failed_count,
			error_log = :error_log
		WHERE id = :id
	`, rollback)
	return err
}

func extractBuildingIDs(targets []*DeploymentTarget) []string {
	ids := make([]string, len(targets))
	for i, target := range targets {
		ids[i] = target.BuildingID
	}
	return ids
}

// DeploymentRollback represents a rollback operation
type DeploymentRollback struct {
	ID               string    `db:"id" json:"id"`
	DeploymentID     string    `db:"deployment_id" json:"deployment_id"`
	TriggeredBy      string    `db:"triggered_by" json:"triggered_by"`
	TriggeredByUser  string    `db:"triggered_by_user" json:"triggered_by_user,omitempty"`
	TriggeredByName  string    `db:"triggered_by_name" json:"triggered_by_name,omitempty"`
	TriggeredAt      time.Time `db:"triggered_at" json:"triggered_at"`
	
	Scope             string   `db:"scope" json:"scope"`
	AffectedBuildings []string `db:"affected_buildings" json:"affected_buildings"`
	
	StartedAt    *time.Time `db:"started_at" json:"started_at,omitempty"`
	CompletedAt  *time.Time `db:"completed_at" json:"completed_at,omitempty"`
	DurationMs   int        `db:"duration_ms" json:"duration_ms,omitempty"`
	
	Status          string   `db:"status" json:"status"`
	SuccessfulCount int      `db:"successful_count" json:"successful_count"`
	FailedCount     int      `db:"failed_count" json:"failed_count"`
	
	Reason   string          `db:"reason" json:"reason"`
	Details  json.RawMessage `db:"details" json:"details,omitempty"`
	ErrorLog []string        `db:"error_log" json:"error_log,omitempty"`
	
	Metadata json.RawMessage `db:"metadata" json:"metadata,omitempty"`
}

// Validate validates the rollback request
func (r *RollbackRequest) Validate() error {
	if r.DeploymentID == "" {
		return fmt.Errorf("deployment ID is required")
	}
	
	switch r.Scope {
	case "full", "partial", "single_building":
		// Valid scopes
	default:
		return fmt.Errorf("invalid scope: %s", r.Scope)
	}
	
	if r.Scope != "full" && len(r.Buildings) == 0 {
		return fmt.Errorf("buildings must be specified for %s rollback", r.Scope)
	}
	
	if r.Reason == "" {
		return fmt.Errorf("rollback reason is required")
	}
	
	return nil
}

// Additional fields for RollbackRequest
type RollbackRequest struct {
	DeploymentID    string   `json:"deployment_id" validate:"required"`
	Scope           string   `json:"scope" validate:"required,oneof=full partial single_building"`
	Buildings       []string `json:"buildings"`
	Reason          string   `json:"reason" validate:"required"`
	Force           bool     `json:"force"`
	TriggeredBy     string   `json:"triggered_by"`
	TriggeredByName string   `json:"triggered_by_name"`
}