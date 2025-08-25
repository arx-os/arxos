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
	"github.com/arxos/core/internal/deployment/strategies"
)

// Deployment represents a configuration deployment to multiple buildings
type Deployment struct {
	ID          string    `db:"id" json:"id"`
	Name        string    `db:"name" json:"name"`
	Description string    `db:"description" json:"description,omitempty"`
	
	// Source
	SourceStateID string          `db:"source_state_id" json:"source_state_id,omitempty"`
	TemplateID    string          `db:"template_id" json:"template_id,omitempty"`
	Config        json.RawMessage `db:"config" json:"config"`
	
	// Targets
	TargetQuery     string   `db:"target_query" json:"target_query,omitempty"`
	TargetBuildings []string `db:"target_buildings" json:"target_buildings"`
	TargetCount     int      `db:"target_count" json:"target_count"`
	
	// Strategy
	Strategy       string          `db:"strategy" json:"strategy"`
	StrategyConfig json.RawMessage `db:"strategy_config" json:"strategy_config,omitempty"`
	
	// Scheduling
	ScheduledAt  *time.Time `db:"scheduled_at" json:"scheduled_at,omitempty"`
	StartedAt    *time.Time `db:"started_at" json:"started_at,omitempty"`
	CompletedAt  *time.Time `db:"completed_at" json:"completed_at,omitempty"`
	
	// Status
	Status             string `db:"status" json:"status"`
	ProgressPercentage int    `db:"progress_percentage" json:"progress_percentage"`
	SuccessfulCount    int    `db:"successful_count" json:"successful_count"`
	FailedCount        int    `db:"failed_count" json:"failed_count"`
	PendingCount       int    `db:"pending_count" json:"pending_count"`
	
	// Rollback
	RollbackEnabled  bool      `db:"rollback_enabled" json:"rollback_enabled"`
	RollbackStateID  string    `db:"rollback_state_id" json:"rollback_state_id,omitempty"`
	RolledBackAt     *time.Time `db:"rolled_back_at" json:"rolled_back_at,omitempty"`
	RollbackReason   string    `db:"rollback_reason" json:"rollback_reason,omitempty"`
	
	// Health checks
	HealthCheckEnabled bool            `db:"health_check_enabled" json:"health_check_enabled"`
	HealthCheckConfig  json.RawMessage `db:"health_check_config" json:"health_check_config,omitempty"`
	HealthStatus       string          `db:"health_status" json:"health_status,omitempty"`
	
	// Ownership
	CreatedBy       string    `db:"created_by" json:"created_by"`
	CreatedByName   string    `db:"created_by_name" json:"created_by_name"`
	ApprovedBy      string    `db:"approved_by" json:"approved_by,omitempty"`
	ApprovedByName  string    `db:"approved_by_name" json:"approved_by_name,omitempty"`
	ApprovedAt      *time.Time `db:"approved_at" json:"approved_at,omitempty"`
	
	// Metrics and logs
	Metrics  json.RawMessage `db:"metrics" json:"metrics,omitempty"`
	Logs     []string        `db:"logs" json:"logs,omitempty"`
	
	// Timestamps
	CreatedAt time.Time `db:"created_at" json:"created_at"`
	UpdatedAt time.Time `db:"updated_at" json:"updated_at"`
	
	// Metadata
	Tags     []string        `db:"tags" json:"tags,omitempty"`
	Metadata json.RawMessage `db:"metadata" json:"metadata,omitempty"`
}

// DeploymentTarget represents a single building target in a deployment
type DeploymentTarget struct {
	ID             string `db:"id" json:"id"`
	DeploymentID   string `db:"deployment_id" json:"deployment_id"`
	BuildingID     string `db:"building_id" json:"building_id"`
	
	// Order
	DeploymentOrder int `db:"deployment_order" json:"deployment_order"`
	DeploymentWave  int `db:"deployment_wave" json:"deployment_wave"`
	
	// States
	PreviousStateID string `db:"previous_state_id" json:"previous_state_id,omitempty"`
	DeployedStateID string `db:"deployed_state_id" json:"deployed_state_id,omitempty"`
	
	// Status
	Status string `db:"status" json:"status"`
	
	// Timing
	QueuedAt    *time.Time `db:"queued_at" json:"queued_at,omitempty"`
	StartedAt   *time.Time `db:"started_at" json:"started_at,omitempty"`
	CompletedAt *time.Time `db:"completed_at" json:"completed_at,omitempty"`
	DurationMs  *int       `db:"duration_ms" json:"duration_ms,omitempty"`
	
	// Health checks
	PreDeploymentHealth  json.RawMessage `db:"pre_deployment_health" json:"pre_deployment_health,omitempty"`
	PostDeploymentHealth json.RawMessage `db:"post_deployment_health" json:"post_deployment_health,omitempty"`
	HealthCheckPassed    *bool           `db:"health_check_passed" json:"health_check_passed,omitempty"`
	
	// Validation
	ValidationResults json.RawMessage `db:"validation_results" json:"validation_results,omitempty"`
	ValidationPassed  *bool           `db:"validation_passed" json:"validation_passed,omitempty"`
	
	// Errors
	ErrorCode    string          `db:"error_code" json:"error_code,omitempty"`
	ErrorMessage string          `db:"error_message" json:"error_message,omitempty"`
	ErrorDetails json.RawMessage `db:"error_details" json:"error_details,omitempty"`
	RetryCount   int             `db:"retry_count" json:"retry_count"`
	
	// Metrics
	Metrics  json.RawMessage `db:"metrics" json:"metrics,omitempty"`
	Metadata json.RawMessage `db:"metadata" json:"metadata,omitempty"`
}

// DeploymentStatus represents the current status of a deployment
type DeploymentStatus string

const (
	StatusDraft           DeploymentStatus = "draft"
	StatusScheduled       DeploymentStatus = "scheduled"
	StatusPendingApproval DeploymentStatus = "pending_approval"
	StatusApproved        DeploymentStatus = "approved"
	StatusInProgress      DeploymentStatus = "in_progress"
	StatusPaused          DeploymentStatus = "paused"
	StatusCompleted       DeploymentStatus = "completed"
	StatusFailed          DeploymentStatus = "failed"
	StatusCancelled       DeploymentStatus = "cancelled"
	StatusRolledBack      DeploymentStatus = "rolled_back"
)

// DeploymentStrategy represents a deployment strategy type
type DeploymentStrategy string

const (
	StrategyImmediate DeploymentStrategy = "immediate"
	StrategyCanary    DeploymentStrategy = "canary"
	StrategyRolling   DeploymentStrategy = "rolling"
	StrategyBlueGreen DeploymentStrategy = "blue_green"
)

// Controller manages deployment operations
type Controller struct {
	db           *sqlx.DB
	stateManager *state.Manager
	strategies   map[DeploymentStrategy]Strategy
	healthChecker HealthChecker
	monitor      *Monitor
	mu           sync.RWMutex
	activeDeployments map[string]*DeploymentExecution
}

// DeploymentExecution tracks an active deployment
type DeploymentExecution struct {
	Deployment *Deployment
	Targets    []*DeploymentTarget
	Strategy   Strategy
	Context    context.Context
	Cancel     context.CancelFunc
	StartTime  time.Time
	Metrics    *DeploymentMetrics
}

// DeploymentMetrics tracks deployment performance
type DeploymentMetrics struct {
	StartTime         time.Time
	EndTime           time.Time
	TotalDuration     time.Duration
	AverageTargetTime time.Duration
	SuccessRate       float64
	HealthCheckRate   float64
	RollbackCount     int
}

// Strategy interface for deployment strategies
type Strategy interface {
	Name() string
	Validate(deployment *Deployment) error
	Plan(deployment *Deployment, targets []*DeploymentTarget) ([]*DeploymentWave, error)
	Execute(ctx context.Context, wave *DeploymentWave) error
	OnFailure(ctx context.Context, deployment *Deployment, target *DeploymentTarget, err error) error
	OnSuccess(ctx context.Context, deployment *Deployment, target *DeploymentTarget) error
}

// DeploymentWave represents a group of targets to deploy together
type DeploymentWave struct {
	WaveNumber int
	Targets    []*DeploymentTarget
	Config     map[string]interface{}
}

// HealthChecker interface for health checks
type HealthChecker interface {
	CheckPreDeployment(ctx context.Context, buildingID string) (*HealthCheckResult, error)
	CheckPostDeployment(ctx context.Context, buildingID string) (*HealthCheckResult, error)
	ValidateDeployment(ctx context.Context, buildingID string, stateID string) (*ValidationResult, error)
}

// HealthCheckResult represents health check results
type HealthCheckResult struct {
	Passed  bool                   `json:"passed"`
	Score   float64                `json:"score"`
	Checks  map[string]CheckResult `json:"checks"`
	Issues  []string               `json:"issues,omitempty"`
	Metrics map[string]float64     `json:"metrics"`
}

// CheckResult represents individual check result
type CheckResult struct {
	Name   string  `json:"name"`
	Passed bool    `json:"passed"`
	Score  float64 `json:"score"`
	Details string `json:"details,omitempty"`
}

// ValidationResult represents deployment validation results
type ValidationResult struct {
	Valid    bool              `json:"valid"`
	Errors   []string          `json:"errors,omitempty"`
	Warnings []string          `json:"warnings,omitempty"`
	Details  map[string]interface{} `json:"details,omitempty"`
}

// NewController creates a new deployment controller
func NewController(db *sqlx.DB, stateManager *state.Manager) *Controller {
	c := &Controller{
		db:                db,
		stateManager:      stateManager,
		strategies:        make(map[DeploymentStrategy]Strategy),
		activeDeployments: make(map[string]*DeploymentExecution),
		monitor:          NewMonitor(),
	}
	
	// Register default strategies
	c.RegisterStrategy(StrategyImmediate, strategies.NewImmediateStrategy())
	c.RegisterStrategy(StrategyCanary, strategies.NewCanaryStrategy())
	c.RegisterStrategy(StrategyRolling, strategies.NewRollingStrategy())
	c.RegisterStrategy(StrategyBlueGreen, strategies.NewBlueGreenStrategy())
	
	// Initialize health checker
	c.healthChecker = NewDefaultHealthChecker(db)
	
	return c
}

// RegisterStrategy registers a deployment strategy
func (c *Controller) RegisterStrategy(name DeploymentStrategy, strategy Strategy) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.strategies[name] = strategy
}

// CreateDeployment creates a new deployment
func (c *Controller) CreateDeployment(ctx context.Context, req *CreateDeploymentRequest) (*Deployment, error) {
	// Validate request
	if err := req.Validate(); err != nil {
		return nil, errors.Wrap(err, "invalid deployment request")
	}
	
	// Resolve target buildings
	targetBuildings, err := c.resolveTargets(ctx, req.TargetQuery, req.TargetBuildings)
	if err != nil {
		return nil, errors.Wrap(err, "failed to resolve targets")
	}
	
	if len(targetBuildings) == 0 {
		return nil, errors.New("no target buildings found")
	}
	
	// Create deployment record
	deployment := &Deployment{
		ID:               uuid.New().String(),
		Name:             req.Name,
		Description:      req.Description,
		SourceStateID:    req.SourceStateID,
		TemplateID:       req.TemplateID,
		Config:           req.Config,
		TargetQuery:      req.TargetQuery,
		TargetBuildings:  targetBuildings,
		TargetCount:      len(targetBuildings),
		Strategy:         string(req.Strategy),
		StrategyConfig:   req.StrategyConfig,
		Status:           string(StatusDraft),
		RollbackEnabled:  req.RollbackEnabled,
		HealthCheckEnabled: req.HealthCheckEnabled,
		HealthCheckConfig: req.HealthCheckConfig,
		CreatedBy:        req.CreatedBy,
		CreatedByName:    req.CreatedByName,
		CreatedAt:        time.Now(),
		UpdatedAt:        time.Now(),
		Tags:             req.Tags,
		PendingCount:     len(targetBuildings),
	}
	
	// Begin transaction
	tx, err := c.db.BeginTxx(ctx, nil)
	if err != nil {
		return nil, errors.Wrap(err, "failed to begin transaction")
	}
	defer tx.Rollback()
	
	// Insert deployment
	_, err = tx.NamedExecContext(ctx, `
		INSERT INTO deployments (
			id, name, description, source_state_id, template_id, config,
			target_query, target_buildings, target_count, strategy, strategy_config,
			status, rollback_enabled, health_check_enabled, health_check_config,
			created_by, created_by_name, created_at, updated_at, tags, pending_count
		) VALUES (
			:id, :name, :description, :source_state_id, :template_id, :config,
			:target_query, :target_buildings, :target_count, :strategy, :strategy_config,
			:status, :rollback_enabled, :health_check_enabled, :health_check_config,
			:created_by, :created_by_name, :created_at, :updated_at, :tags, :pending_count
		)
	`, deployment)
	if err != nil {
		return nil, errors.Wrap(err, "failed to insert deployment")
	}
	
	// Create deployment targets
	for i, buildingID := range targetBuildings {
		target := &DeploymentTarget{
			ID:              uuid.New().String(),
			DeploymentID:    deployment.ID,
			BuildingID:      buildingID,
			DeploymentOrder: i,
			Status:          "pending",
		}
		
		_, err = tx.NamedExecContext(ctx, `
			INSERT INTO deployment_targets (
				id, deployment_id, building_id, deployment_order, status
			) VALUES (
				:id, :deployment_id, :building_id, :deployment_order, :status
			)
		`, target)
		if err != nil {
			return nil, errors.Wrap(err, "failed to insert deployment target")
		}
	}
	
	// Commit transaction
	if err = tx.Commit(); err != nil {
		return nil, errors.Wrap(err, "failed to commit transaction")
	}
	
	// Emit creation event
	c.monitor.EmitEvent(DeploymentCreatedEvent{
		DeploymentID: deployment.ID,
		Name:         deployment.Name,
		TargetCount:  deployment.TargetCount,
		Strategy:     deployment.Strategy,
	})
	
	return deployment, nil
}

// ExecuteDeployment starts executing a deployment
func (c *Controller) ExecuteDeployment(ctx context.Context, deploymentID string) error {
	// Get deployment
	deployment, err := c.GetDeployment(ctx, deploymentID)
	if err != nil {
		return errors.Wrap(err, "failed to get deployment")
	}
	
	// Validate status
	if deployment.Status != string(StatusDraft) && deployment.Status != string(StatusApproved) {
		return fmt.Errorf("deployment cannot be executed in status: %s", deployment.Status)
	}
	
	// Get strategy
	strategy, exists := c.strategies[DeploymentStrategy(deployment.Strategy)]
	if !exists {
		return fmt.Errorf("unknown deployment strategy: %s", deployment.Strategy)
	}
	
	// Validate deployment with strategy
	if err := strategy.Validate(deployment); err != nil {
		return errors.Wrap(err, "deployment validation failed")
	}
	
	// Get deployment targets
	targets, err := c.GetDeploymentTargets(ctx, deploymentID)
	if err != nil {
		return errors.Wrap(err, "failed to get deployment targets")
	}
	
	// Create execution context
	execCtx, cancel := context.WithCancel(ctx)
	
	execution := &DeploymentExecution{
		Deployment: deployment,
		Targets:    targets,
		Strategy:   strategy,
		Context:    execCtx,
		Cancel:     cancel,
		StartTime:  time.Now(),
		Metrics:    &DeploymentMetrics{StartTime: time.Now()},
	}
	
	// Register active deployment
	c.mu.Lock()
	c.activeDeployments[deploymentID] = execution
	c.mu.Unlock()
	
	// Update deployment status
	if err := c.updateDeploymentStatus(ctx, deploymentID, StatusInProgress); err != nil {
		cancel()
		return errors.Wrap(err, "failed to update deployment status")
	}
	
	// Execute deployment asynchronously
	go c.executeDeploymentAsync(execution)
	
	return nil
}

// executeDeploymentAsync executes deployment in background
func (c *Controller) executeDeploymentAsync(execution *DeploymentExecution) {
	defer func() {
		// Clean up active deployment
		c.mu.Lock()
		delete(c.activeDeployments, execution.Deployment.ID)
		c.mu.Unlock()
		
		// Cancel context
		execution.Cancel()
		
		// Record metrics
		execution.Metrics.EndTime = time.Now()
		execution.Metrics.TotalDuration = execution.Metrics.EndTime.Sub(execution.Metrics.StartTime)
		c.recordDeploymentMetrics(execution)
	}()
	
	// Plan deployment waves
	waves, err := execution.Strategy.Plan(execution.Deployment, execution.Targets)
	if err != nil {
		c.handleDeploymentError(execution, errors.Wrap(err, "failed to plan deployment"))
		return
	}
	
	// Execute waves
	for _, wave := range waves {
		select {
		case <-execution.Context.Done():
			// Deployment cancelled
			c.updateDeploymentStatus(context.Background(), execution.Deployment.ID, StatusCancelled)
			return
		default:
			// Execute wave
			if err := c.executeWave(execution, wave); err != nil {
				c.handleDeploymentError(execution, errors.Wrap(err, "wave execution failed"))
				return
			}
		}
	}
	
	// Mark deployment as completed
	c.updateDeploymentStatus(context.Background(), execution.Deployment.ID, StatusCompleted)
	
	// Emit completion event
	c.monitor.EmitEvent(DeploymentCompletedEvent{
		DeploymentID:    execution.Deployment.ID,
		SuccessfulCount: execution.Deployment.SuccessfulCount,
		FailedCount:     execution.Deployment.FailedCount,
		Duration:        execution.Metrics.TotalDuration,
	})
}

// executeWave executes a deployment wave
func (c *Controller) executeWave(execution *DeploymentExecution, wave *DeploymentWave) error {
	var wg sync.WaitGroup
	errors := make(chan error, len(wave.Targets))
	
	for _, target := range wave.Targets {
		wg.Add(1)
		go func(t *DeploymentTarget) {
			defer wg.Done()
			if err := c.deployToTarget(execution, t); err != nil {
				errors <- err
			}
		}(target)
	}
	
	wg.Wait()
	close(errors)
	
	// Check for errors
	var deploymentErrors []error
	for err := range errors {
		deploymentErrors = append(deploymentErrors, err)
	}
	
	if len(deploymentErrors) > 0 {
		// Handle based on strategy
		return execution.Strategy.OnFailure(execution.Context, execution.Deployment, nil, deploymentErrors[0])
	}
	
	return nil
}

// deployToTarget deploys to a single target building
func (c *Controller) deployToTarget(execution *DeploymentExecution, target *DeploymentTarget) error {
	startTime := time.Now()
	
	// Update target status
	target.Status = "in_progress"
	target.StartedAt = &startTime
	c.updateTargetStatus(execution.Context, target)
	
	// Pre-deployment health check
	if execution.Deployment.HealthCheckEnabled {
		health, err := c.healthChecker.CheckPreDeployment(execution.Context, target.BuildingID)
		if err != nil {
			return c.handleTargetError(execution, target, errors.Wrap(err, "pre-deployment health check failed"))
		}
		
		healthJSON, _ := json.Marshal(health)
		target.PreDeploymentHealth = healthJSON
		
		if !health.Passed {
			return c.handleTargetError(execution, target, errors.New("pre-deployment health check failed"))
		}
	}
	
	// Apply state to building
	if execution.Deployment.SourceStateID != "" {
		// Capture current state for rollback
		currentState, err := c.stateManager.CaptureState(execution.Context, target.BuildingID, "main", state.CaptureOptions{
			Message:    fmt.Sprintf("Pre-deployment state for deployment %s", execution.Deployment.Name),
			AuthorID:   "system",
			AuthorName: "Deployment System",
		})
		if err != nil {
			return c.handleTargetError(execution, target, errors.Wrap(err, "failed to capture current state"))
		}
		target.PreviousStateID = currentState.ID
		
		// Apply new state
		err = c.stateManager.RestoreState(execution.Context, target.BuildingID, execution.Deployment.SourceStateID, state.CaptureOptions{
			Message:    fmt.Sprintf("Deployment %s", execution.Deployment.Name),
			AuthorID:   execution.Deployment.CreatedBy,
			AuthorName: execution.Deployment.CreatedByName,
		})
		if err != nil {
			return c.handleTargetError(execution, target, errors.Wrap(err, "failed to apply state"))
		}
		
		target.DeployedStateID = execution.Deployment.SourceStateID
	}
	
	// Post-deployment validation
	if execution.Deployment.HealthCheckEnabled {
		validation, err := c.healthChecker.ValidateDeployment(execution.Context, target.BuildingID, target.DeployedStateID)
		if err != nil {
			return c.handleTargetError(execution, target, errors.Wrap(err, "post-deployment validation failed"))
		}
		
		validationJSON, _ := json.Marshal(validation)
		target.ValidationResults = validationJSON
		target.ValidationPassed = &validation.Valid
		
		if !validation.Valid {
			// Rollback if validation fails
			if execution.Deployment.RollbackEnabled && target.PreviousStateID != "" {
				c.rollbackTarget(execution.Context, target)
			}
			return c.handleTargetError(execution, target, errors.New("post-deployment validation failed"))
		}
	}
	
	// Post-deployment health check
	if execution.Deployment.HealthCheckEnabled {
		health, err := c.healthChecker.CheckPostDeployment(execution.Context, target.BuildingID)
		if err != nil {
			return c.handleTargetError(execution, target, errors.Wrap(err, "post-deployment health check failed"))
		}
		
		healthJSON, _ := json.Marshal(health)
		target.PostDeploymentHealth = healthJSON
		target.HealthCheckPassed = &health.Passed
		
		if !health.Passed {
			// Rollback if health check fails
			if execution.Deployment.RollbackEnabled && target.PreviousStateID != "" {
				c.rollbackTarget(execution.Context, target)
			}
			return c.handleTargetError(execution, target, errors.New("post-deployment health check failed"))
		}
	}
	
	// Mark target as completed
	completedTime := time.Now()
	duration := int(completedTime.Sub(startTime).Milliseconds())
	target.Status = "completed"
	target.CompletedAt = &completedTime
	target.DurationMs = &duration
	
	c.updateTargetStatus(execution.Context, target)
	
	// Update deployment progress
	c.updateDeploymentProgress(execution.Context, execution.Deployment.ID)
	
	// Call strategy success handler
	return execution.Strategy.OnSuccess(execution.Context, execution.Deployment, target)
}

// Helper methods

func (c *Controller) resolveTargets(ctx context.Context, query string, explicit []string) ([]string, error) {
	if len(explicit) > 0 {
		return explicit, nil
	}
	
	if query != "" {
		// TODO: Execute AQL query to resolve targets
		// For now, return empty
		return []string{}, nil
	}
	
	return []string{}, errors.New("no targets specified")
}

func (c *Controller) GetDeployment(ctx context.Context, deploymentID string) (*Deployment, error) {
	var deployment Deployment
	err := c.db.GetContext(ctx, &deployment, `
		SELECT * FROM deployments WHERE id = $1
	`, deploymentID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to get deployment")
	}
	return &deployment, nil
}

func (c *Controller) GetDeploymentTargets(ctx context.Context, deploymentID string) ([]*DeploymentTarget, error) {
	var targets []*DeploymentTarget
	err := c.db.SelectContext(ctx, &targets, `
		SELECT * FROM deployment_targets 
		WHERE deployment_id = $1 
		ORDER BY deployment_order
	`, deploymentID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to get deployment targets")
	}
	return targets, nil
}

func (c *Controller) updateDeploymentStatus(ctx context.Context, deploymentID string, status DeploymentStatus) error {
	_, err := c.db.ExecContext(ctx, `
		UPDATE deployments 
		SET status = $2, updated_at = $3
		WHERE id = $1
	`, deploymentID, string(status), time.Now())
	return err
}

func (c *Controller) updateTargetStatus(ctx context.Context, target *DeploymentTarget) error {
	_, err := c.db.NamedExecContext(ctx, `
		UPDATE deployment_targets 
		SET status = :status, started_at = :started_at, completed_at = :completed_at,
		    duration_ms = :duration_ms, error_code = :error_code, error_message = :error_message,
		    pre_deployment_health = :pre_deployment_health, post_deployment_health = :post_deployment_health,
		    health_check_passed = :health_check_passed, validation_results = :validation_results,
		    validation_passed = :validation_passed, previous_state_id = :previous_state_id,
		    deployed_state_id = :deployed_state_id
		WHERE id = :id
	`, target)
	return err
}

func (c *Controller) updateDeploymentProgress(ctx context.Context, deploymentID string) error {
	// Count target statuses
	var stats struct {
		Successful int `db:"successful"`
		Failed     int `db:"failed"`
		Pending    int `db:"pending"`
		Total      int `db:"total"`
	}
	
	err := c.db.GetContext(ctx, &stats, `
		SELECT 
			COUNT(*) FILTER (WHERE status = 'completed') as successful,
			COUNT(*) FILTER (WHERE status = 'failed') as failed,
			COUNT(*) FILTER (WHERE status = 'pending') as pending,
			COUNT(*) as total
		FROM deployment_targets
		WHERE deployment_id = $1
	`, deploymentID)
	if err != nil {
		return err
	}
	
	progress := 0
	if stats.Total > 0 {
		progress = ((stats.Successful + stats.Failed) * 100) / stats.Total
	}
	
	_, err = c.db.ExecContext(ctx, `
		UPDATE deployments 
		SET successful_count = $2, failed_count = $3, pending_count = $4,
		    progress_percentage = $5, updated_at = $6
		WHERE id = $1
	`, deploymentID, stats.Successful, stats.Failed, stats.Pending, progress, time.Now())
	
	return err
}

func (c *Controller) handleDeploymentError(execution *DeploymentExecution, err error) {
	// Log error
	execution.Deployment.Logs = append(execution.Deployment.Logs, fmt.Sprintf("ERROR: %v", err))
	
	// Update status
	c.updateDeploymentStatus(context.Background(), execution.Deployment.ID, StatusFailed)
	
	// Emit failure event
	c.monitor.EmitEvent(DeploymentFailedEvent{
		DeploymentID: execution.Deployment.ID,
		Error:        err.Error(),
	})
}

func (c *Controller) handleTargetError(execution *DeploymentExecution, target *DeploymentTarget, err error) error {
	target.Status = "failed"
	target.ErrorMessage = err.Error()
	c.updateTargetStatus(execution.Context, target)
	return err
}

func (c *Controller) rollbackTarget(ctx context.Context, target *DeploymentTarget) error {
	if target.PreviousStateID == "" {
		return nil
	}
	
	return c.stateManager.RestoreState(ctx, target.BuildingID, target.PreviousStateID, state.CaptureOptions{
		Message:    "Automatic rollback due to deployment failure",
		AuthorID:   "system",
		AuthorName: "Deployment System",
	})
}

func (c *Controller) recordDeploymentMetrics(execution *DeploymentExecution) {
	metrics := map[string]interface{}{
		"duration_seconds":     execution.Metrics.TotalDuration.Seconds(),
		"success_rate":         execution.Metrics.SuccessRate,
		"health_check_rate":    execution.Metrics.HealthCheckRate,
		"rollback_count":       execution.Metrics.RollbackCount,
		"targets_total":        len(execution.Targets),
		"targets_successful":   execution.Deployment.SuccessfulCount,
		"targets_failed":       execution.Deployment.FailedCount,
	}
	
	metricsJSON, _ := json.Marshal(metrics)
	c.db.Exec(`
		UPDATE deployments 
		SET metrics = $2, completed_at = $3
		WHERE id = $1
	`, execution.Deployment.ID, metricsJSON, execution.Metrics.EndTime)
}