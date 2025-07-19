package repository

import (
	"context"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"

	"arxos/arx-backend/models"
)

// PipelineRepository handles database operations for pipeline entities
type PipelineRepository struct {
	db *sqlx.DB
}

// NewPipelineRepository creates a new pipeline repository
func NewPipelineRepository(db *sqlx.DB) *PipelineRepository {
	return &PipelineRepository{db: db}
}

// CreateExecution creates a new pipeline execution
func (r *PipelineRepository) CreateExecution(ctx context.Context, execution *models.PipelineExecution) error {
	query := `
		INSERT INTO pipeline_executions (id, system, object_type, status, created_by)
		VALUES ($1, $2, $3, $4, $5)
		RETURNING id, created_at, updated_at
	`

	execution.ID = uuid.New()
	execution.CreatedAt = time.Now()
	execution.Status = "pending"

	return r.db.QueryRowxContext(ctx, query,
		execution.ID,
		execution.System,
		execution.ObjectType,
		execution.Status,
		execution.CreatedBy,
	).StructScan(execution)
}

// GetExecution retrieves a pipeline execution by ID
func (r *PipelineRepository) GetExecution(ctx context.Context, id uuid.UUID) (*models.PipelineExecution, error) {
	query := `
		SELECT * FROM pipeline_executions WHERE id = $1
	`

	var execution models.PipelineExecution
	err := r.db.GetContext(ctx, &execution, query, id)
	if err != nil {
		return nil, err
	}

	// Load associated steps
	steps, err := r.GetStepsByExecutionID(ctx, id)
	if err != nil {
		return nil, err
	}
	execution.Steps = steps

	return &execution, nil
}

// UpdateExecution updates a pipeline execution
func (r *PipelineRepository) UpdateExecution(ctx context.Context, execution *models.PipelineExecution) error {
	query := `
		UPDATE pipeline_executions 
		SET status = $2, started_at = $3, completed_at = $4, error_message = $5, metadata = $6, updated_at = NOW()
		WHERE id = $1
	`

	_, err := r.db.ExecContext(ctx, query,
		execution.ID,
		execution.Status,
		execution.StartedAt,
		execution.CompletedAt,
		execution.ErrorMessage,
		execution.Metadata,
	)

	return err
}

// ListExecutions retrieves pipeline executions with optional filters
func (r *PipelineRepository) ListExecutions(ctx context.Context, system *string, status *string, limit, offset int) ([]models.PipelineExecutionSummary, error) {
	query := `
		SELECT * FROM pipeline_execution_summary
		WHERE ($1::text IS NULL OR system = $1)
		AND ($2::text IS NULL OR status = $2)
		ORDER BY created_at DESC
		LIMIT $3 OFFSET $4
	`

	var executions []models.PipelineExecutionSummary
	err := r.db.SelectContext(ctx, &executions, query, system, status, limit, offset)
	return executions, err
}

// CreateStep creates a new pipeline step
func (r *PipelineRepository) CreateStep(ctx context.Context, step *models.PipelineStep) error {
	query := `
		INSERT INTO pipeline_steps (id, execution_id, step_name, step_order, orchestrator, status)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, created_at, updated_at
	`

	step.ID = uuid.New()
	step.CreatedAt = time.Now()
	step.Status = "pending"

	return r.db.QueryRowxContext(ctx, query,
		step.ID,
		step.ExecutionID,
		step.StepName,
		step.StepOrder,
		step.Orchestrator,
		step.Status,
	).StructScan(step)
}

// UpdateStep updates a pipeline step
func (r *PipelineRepository) UpdateStep(ctx context.Context, step *models.PipelineStep) error {
	query := `
		UPDATE pipeline_steps 
		SET status = $2, started_at = $3, completed_at = $4, error_message = $5, metadata = $6, updated_at = NOW()
		WHERE id = $1
	`

	_, err := r.db.ExecContext(ctx, query,
		step.ID,
		step.Status,
		step.StartedAt,
		step.CompletedAt,
		step.ErrorMessage,
		step.Metadata,
	)

	return err
}

// GetStepsByExecutionID retrieves all steps for a pipeline execution
func (r *PipelineRepository) GetStepsByExecutionID(ctx context.Context, executionID uuid.UUID) ([]models.PipelineStep, error) {
	query := `
		SELECT * FROM pipeline_steps 
		WHERE execution_id = $1 
		ORDER BY step_order
	`

	var steps []models.PipelineStep
	err := r.db.SelectContext(ctx, &steps, query, executionID)
	return steps, err
}

// CreateConfiguration creates a new pipeline configuration
func (r *PipelineRepository) CreateConfiguration(ctx context.Context, config *models.PipelineConfiguration) error {
	query := `
		INSERT INTO pipeline_configurations (id, system, config_name, config_type, config_data, created_by)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, created_at, updated_at
	`

	config.ID = uuid.New()
	config.CreatedAt = time.Now()
	config.IsActive = true

	return r.db.QueryRowxContext(ctx, query,
		config.ID,
		config.System,
		config.ConfigName,
		config.ConfigType,
		config.ConfigData,
		config.CreatedBy,
	).StructScan(config)
}

// GetConfiguration retrieves a pipeline configuration
func (r *PipelineRepository) GetConfiguration(ctx context.Context, system, configName, configType string) (*models.PipelineConfiguration, error) {
	query := `
		SELECT * FROM pipeline_configurations 
		WHERE system = $1 AND config_name = $2 AND config_type = $3 AND is_active = true
	`

	var config models.PipelineConfiguration
	err := r.db.GetContext(ctx, &config, query, system, configName, configType)
	if err != nil {
		return nil, err
	}

	return &config, nil
}

// ListConfigurations retrieves pipeline configurations for a system
func (r *PipelineRepository) ListConfigurations(ctx context.Context, system string) ([]models.PipelineConfiguration, error) {
	query := `
		SELECT * FROM pipeline_configurations 
		WHERE system = $1 AND is_active = true
		ORDER BY config_type, config_name
	`

	var configs []models.PipelineConfiguration
	err := r.db.SelectContext(ctx, &configs, query, system)
	return configs, err
}

// GetQualityGates retrieves all active quality gates
func (r *PipelineRepository) GetQualityGates(ctx context.Context) ([]models.PipelineQualityGate, error) {
	query := `
		SELECT * FROM pipeline_quality_gates 
		WHERE is_active = true
		ORDER BY gate_type, gate_name
	`

	var gates []models.PipelineQualityGate
	err := r.db.SelectContext(ctx, &gates, query)
	return gates, err
}

// CreateAuditLog creates a new audit log entry
func (r *PipelineRepository) CreateAuditLog(ctx context.Context, log *models.PipelineAuditLog) error {
	query := `
		INSERT INTO pipeline_audit_log (id, execution_id, step_id, action, action_type, details, created_by)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`

	log.ID = uuid.New()
	log.CreatedAt = time.Now()

	_, err := r.db.ExecContext(ctx, query,
		log.ID,
		log.ExecutionID,
		log.StepID,
		log.Action,
		log.ActionType,
		log.Details,
		log.CreatedBy,
	)

	return err
}

// GetQualityMetrics retrieves quality metrics for pipeline systems
func (r *PipelineRepository) GetQualityMetrics(ctx context.Context, system *string) ([]models.PipelineQualityMetrics, error) {
	query := `
		SELECT * FROM pipeline_quality_metrics
		WHERE ($1::text IS NULL OR system = $1)
		ORDER BY total_executions DESC
	`

	var metrics []models.PipelineQualityMetrics
	err := r.db.SelectContext(ctx, &metrics, query, system)
	return metrics, err
}

// GetExecutionStats retrieves execution statistics
func (r *PipelineRepository) GetExecutionStats(ctx context.Context) (map[string]interface{}, error) {
	query := `
		SELECT 
			COUNT(*) as total_executions,
			COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
			COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
			COUNT(CASE WHEN status = 'running' THEN 1 END) as running_executions,
			AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_execution_time
		FROM pipeline_executions
		WHERE created_at >= NOW() - INTERVAL '30 days'
	`

	var stats struct {
		TotalExecutions      int      `db:"total_executions"`
		SuccessfulExecutions int      `db:"successful_executions"`
		FailedExecutions     int      `db:"failed_executions"`
		RunningExecutions    int      `db:"running_executions"`
		AvgExecutionTime     *float64 `db:"avg_execution_time"`
	}

	err := r.db.GetContext(ctx, &stats, query)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"total_executions":      stats.TotalExecutions,
		"successful_executions": stats.SuccessfulExecutions,
		"failed_executions":     stats.FailedExecutions,
		"running_executions":    stats.RunningExecutions,
		"avg_execution_time":    stats.AvgExecutionTime,
		"success_rate":          float64(stats.SuccessfulExecutions) / float64(stats.TotalExecutions) * 100,
	}, nil
}

// DeleteExecution deletes a pipeline execution and all associated data
func (r *PipelineRepository) DeleteExecution(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM pipeline_executions WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}

// CleanupOldExecutions removes old pipeline executions (older than 90 days)
func (r *PipelineRepository) CleanupOldExecutions(ctx context.Context) error {
	query := `
		DELETE FROM pipeline_executions 
		WHERE created_at < NOW() - INTERVAL '90 days'
		AND status IN ('completed', 'failed')
	`

	_, err := r.db.ExecContext(ctx, query)
	return err
}
