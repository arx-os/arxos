package services

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/database"
)

// WorkflowExecutionEngine manages workflow execution state and coordination
type WorkflowExecutionEngine struct {
	db           *database.PostGISDB
	n8nService   *N8NService
	executions   map[string]*WorkflowExecutionState
	executionsMu sync.RWMutex
	stopChan     chan struct{}
}

// WorkflowExecutionState tracks the state of a workflow execution
type WorkflowExecutionState struct {
	ID             string                  `json:"id"`
	WorkflowID     string                  `json:"workflow_id"`
	N8nExecutionID string                  `json:"n8n_execution_id"`
	Status         WorkflowExecutionStatus `json:"status"`
	Input          map[string]interface{}  `json:"input"`
	Output         map[string]interface{}  `json:"output"`
	Error          string                  `json:"error,omitempty"`
	StartedAt      time.Time               `json:"started_at"`
	CompletedAt    *time.Time              `json:"completed_at,omitempty"`
	LastUpdatedAt  time.Time               `json:"last_updated_at"`
	RetryCount     int                     `json:"retry_count"`
	MaxRetries     int                     `json:"max_retries"`
	Metadata       map[string]interface{}  `json:"metadata"`
}

// WorkflowExecutionStatus represents the status of a workflow execution
type WorkflowExecutionStatus string

const (
	WorkflowExecutionStatusPending   WorkflowExecutionStatus = "pending"
	WorkflowExecutionStatusRunning   WorkflowExecutionStatus = "running"
	WorkflowExecutionStatusCompleted WorkflowExecutionStatus = "completed"
	WorkflowExecutionStatusFailed    WorkflowExecutionStatus = "failed"
	WorkflowExecutionStatusCancelled WorkflowExecutionStatus = "cancelled"
	WorkflowExecutionStatusRetrying  WorkflowExecutionStatus = "retrying"
)

// WorkflowExecutionRequest represents a request to execute a workflow
type WorkflowExecutionRequest struct {
	WorkflowID string                 `json:"workflow_id"`
	Input      map[string]interface{} `json:"input"`
	Priority   int                    `json:"priority,omitempty"`
	MaxRetries int                    `json:"max_retries,omitempty"`
	Timeout    time.Duration          `json:"timeout,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// WorkflowExecutionResult represents the result of a workflow execution
type WorkflowExecutionResult struct {
	ExecutionID string                  `json:"execution_id"`
	Status      WorkflowExecutionStatus `json:"status"`
	Output      map[string]interface{}  `json:"output"`
	Error       string                  `json:"error,omitempty"`
	Duration    time.Duration           `json:"duration"`
	Metadata    map[string]interface{}  `json:"metadata"`
}

// NewWorkflowExecutionEngine creates a new workflow execution engine
func NewWorkflowExecutionEngine(db *database.PostGISDB, n8nService *N8NService) *WorkflowExecutionEngine {
	engine := &WorkflowExecutionEngine{
		db:         db,
		n8nService: n8nService,
		executions: make(map[string]*WorkflowExecutionState),
		stopChan:   make(chan struct{}),
	}

	// Start background monitoring
	go engine.monitorExecutions()

	return engine
}

// ExecuteWorkflow executes a workflow with the given input
func (wee *WorkflowExecutionEngine) ExecuteWorkflow(ctx context.Context, req WorkflowExecutionRequest) (*WorkflowExecutionResult, error) {
	// Generate execution ID
	executionID := generateWorkflowExecutionID()

	// Set defaults
	if req.MaxRetries == 0 {
		req.MaxRetries = 3
	}
	if req.Timeout == 0 {
		req.Timeout = 30 * time.Minute
	}

	// Create execution state
	executionState := &WorkflowExecutionState{
		ID:            executionID,
		WorkflowID:    req.WorkflowID,
		Status:        WorkflowExecutionStatusPending,
		Input:         req.Input,
		StartedAt:     time.Now(),
		LastUpdatedAt: time.Now(),
		MaxRetries:    req.MaxRetries,
		Metadata:      req.Metadata,
	}

	// Store execution state
	wee.executionsMu.Lock()
	wee.executions[executionID] = executionState
	wee.executionsMu.Unlock()

	// Store in database
	if err := wee.storeExecutionState(ctx, executionState); err != nil {
		return nil, fmt.Errorf("failed to store execution state: %w", err)
	}

	// Start execution in background
	go wee.executeWorkflowAsync(ctx, executionState, req.Timeout)

	// Return immediate result
	return &WorkflowExecutionResult{
		ExecutionID: executionID,
		Status:      WorkflowExecutionStatusPending,
		Metadata:    req.Metadata,
	}, nil
}

// GetExecutionStatus retrieves the status of a workflow execution
func (wee *WorkflowExecutionEngine) GetExecutionStatus(ctx context.Context, executionID string) (*WorkflowExecutionResult, error) {
	wee.executionsMu.RLock()
	executionState, exists := wee.executions[executionID]
	wee.executionsMu.RUnlock()

	if !exists {
		// Try to load from database
		var err error
		executionState, err = wee.loadExecutionState(ctx, executionID)
		if err != nil {
			return nil, fmt.Errorf("execution not found: %w", err)
		}
	}

	var duration time.Duration
	if executionState.CompletedAt != nil {
		duration = executionState.CompletedAt.Sub(executionState.StartedAt)
	} else {
		duration = time.Since(executionState.StartedAt)
	}

	return &WorkflowExecutionResult{
		ExecutionID: executionID,
		Status:      executionState.Status,
		Output:      executionState.Output,
		Error:       executionState.Error,
		Duration:    duration,
		Metadata:    executionState.Metadata,
	}, nil
}

// CancelExecution cancels a running workflow execution
func (wee *WorkflowExecutionEngine) CancelExecution(ctx context.Context, executionID string) error {
	wee.executionsMu.Lock()
	executionState, exists := wee.executions[executionID]
	wee.executionsMu.Unlock()

	if !exists {
		// Try to load from database
		var err error
		executionState, err = wee.loadExecutionState(ctx, executionID)
		if err != nil {
			return fmt.Errorf("execution not found: %w", err)
		}
	}

	if executionState.Status != WorkflowExecutionStatusRunning && executionState.Status != WorkflowExecutionStatusPending {
		return fmt.Errorf("cannot cancel execution in status: %s", executionState.Status)
	}

	// Update status
	executionState.Status = WorkflowExecutionStatusCancelled
	executionState.LastUpdatedAt = time.Now()
	now := time.Now()
	executionState.CompletedAt = &now

	// Update in memory
	wee.executionsMu.Lock()
	wee.executions[executionID] = executionState
	wee.executionsMu.Unlock()

	// Update in database
	if err := wee.updateExecutionState(ctx, executionState); err != nil {
		return fmt.Errorf("failed to update execution state: %w", err)
	}

	return nil
}

// ListExecutions lists workflow executions with optional filtering
func (wee *WorkflowExecutionEngine) ListExecutions(ctx context.Context, workflowID string, limit int) ([]*WorkflowExecutionResult, error) {
	query := `
		SELECT id, workflow_id, n8n_execution_id, status, input, output, error, 
		       started_at, completed_at, last_updated_at, retry_count, max_retries, metadata
		FROM workflow_executions
		WHERE tier = 'workflow'
	`

	args := []interface{}{}
	if workflowID != "" {
		query += " AND workflow_id = $1"
		args = append(args, workflowID)
	}

	query += " ORDER BY started_at DESC"
	if limit > 0 {
		query += fmt.Sprintf(" LIMIT %d", limit)
	}

	rows, err := wee.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query executions: %w", err)
	}
	defer rows.Close()

	var results []*WorkflowExecutionResult
	for rows.Next() {
		var execution WorkflowExecutionState
		var inputJSON, outputJSON, metadataJSON []byte

		err := rows.Scan(
			&execution.ID,
			&execution.WorkflowID,
			&execution.N8nExecutionID,
			&execution.Status,
			&inputJSON,
			&outputJSON,
			&execution.Error,
			&execution.StartedAt,
			&execution.CompletedAt,
			&execution.LastUpdatedAt,
			&execution.RetryCount,
			&execution.MaxRetries,
			&metadataJSON,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan execution: %w", err)
		}

		// Parse JSON fields
		if len(inputJSON) > 0 {
			json.Unmarshal(inputJSON, &execution.Input)
		}
		if len(outputJSON) > 0 {
			json.Unmarshal(outputJSON, &execution.Output)
		}
		if len(metadataJSON) > 0 {
			json.Unmarshal(metadataJSON, &execution.Metadata)
		}

		// Calculate duration
		var duration time.Duration
		if execution.CompletedAt != nil {
			duration = execution.CompletedAt.Sub(execution.StartedAt)
		} else {
			duration = time.Since(execution.StartedAt)
		}

		results = append(results, &WorkflowExecutionResult{
			ExecutionID: execution.ID,
			Status:      execution.Status,
			Output:      execution.Output,
			Error:       execution.Error,
			Duration:    duration,
			Metadata:    execution.Metadata,
		})
	}

	return results, nil
}

// executeWorkflowAsync executes a workflow asynchronously
func (wee *WorkflowExecutionEngine) executeWorkflowAsync(ctx context.Context, executionState *WorkflowExecutionState, timeout time.Duration) {
	// Create context with timeout
	execCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	// Update status to running
	executionState.Status = WorkflowExecutionStatusRunning
	executionState.LastUpdatedAt = time.Now()
	wee.updateExecutionState(execCtx, executionState)

	// Execute workflow in n8n
	n8nExecution, err := wee.n8nService.ExecuteWorkflow(execCtx, executionState.WorkflowID, executionState.Input)
	if err != nil {
		wee.handleExecutionError(execCtx, executionState, fmt.Errorf("failed to execute workflow in n8n: %w", err))
		return
	}

	// Store n8n execution ID
	executionState.N8nExecutionID = n8nExecution.ID
	wee.updateExecutionState(execCtx, executionState)

	// Monitor execution until completion
	wee.monitorN8nExecution(execCtx, executionState, n8nExecution.ID)
}

// monitorN8nExecution monitors an n8n execution until completion
func (wee *WorkflowExecutionEngine) monitorN8nExecution(ctx context.Context, executionState *WorkflowExecutionState, n8nExecutionID string) {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			// Context cancelled or timeout
			executionState.Status = WorkflowExecutionStatusCancelled
			executionState.Error = "execution cancelled or timed out"
			executionState.LastUpdatedAt = time.Now()
			now := time.Now()
			executionState.CompletedAt = &now
			wee.updateExecutionState(ctx, executionState)
			return

		case <-ticker.C:
			// Check execution status
			n8nExecution, err := wee.n8nService.GetExecution(ctx, n8nExecutionID)
			if err != nil {
				wee.handleExecutionError(ctx, executionState, fmt.Errorf("failed to get n8n execution status: %w", err))
				return
			}

			// Update execution state
			executionState.LastUpdatedAt = time.Now()

			switch n8nExecution.Status {
			case "success":
				executionState.Status = WorkflowExecutionStatusCompleted
				executionState.Output = n8nExecution.Data
				executionState.LastUpdatedAt = time.Now()
				now := time.Now()
				executionState.CompletedAt = &now
				wee.updateExecutionState(ctx, executionState)
				return

			case "error":
				executionState.Status = WorkflowExecutionStatusFailed
				executionState.Error = n8nExecution.Error
				executionState.LastUpdatedAt = time.Now()
				now := time.Now()
				executionState.CompletedAt = &now
				wee.updateExecutionState(ctx, executionState)
				return

			case "running":
				// Continue monitoring
				wee.updateExecutionState(ctx, executionState)
				continue

			default:
				// Unknown status, continue monitoring
				wee.updateExecutionState(ctx, executionState)
				continue
			}
		}
	}
}

// handleExecutionError handles execution errors with retry logic
func (wee *WorkflowExecutionEngine) handleExecutionError(ctx context.Context, executionState *WorkflowExecutionState, err error) {
	executionState.Error = err.Error()
	executionState.RetryCount++

	if executionState.RetryCount < executionState.MaxRetries {
		// Retry execution
		executionState.Status = WorkflowExecutionStatusRetrying
		executionState.LastUpdatedAt = time.Now()
		wee.updateExecutionState(ctx, executionState)

		// Wait before retry (exponential backoff)
		retryDelay := time.Duration(executionState.RetryCount) * time.Second
		time.Sleep(retryDelay)

		// Retry execution
		go wee.executeWorkflowAsync(ctx, executionState, 30*time.Minute)
	} else {
		// Max retries exceeded
		executionState.Status = WorkflowExecutionStatusFailed
		executionState.LastUpdatedAt = time.Now()
		now := time.Now()
		executionState.CompletedAt = &now
		wee.updateExecutionState(ctx, executionState)
	}
}

// monitorExecutions monitors all running executions and cleans up completed ones
func (wee *WorkflowExecutionEngine) monitorExecutions() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			wee.cleanupCompletedExecutions()
		case <-wee.stopChan:
			return
		}
	}
}

// cleanupCompletedExecutions removes completed executions from memory after a period
func (wee *WorkflowExecutionEngine) cleanupCompletedExecutions() {
	wee.executionsMu.Lock()
	defer wee.executionsMu.Unlock()

	cutoff := time.Now().Add(-24 * time.Hour) // Keep for 24 hours

	for id, execution := range wee.executions {
		if (execution.Status == WorkflowExecutionStatusCompleted ||
			execution.Status == WorkflowExecutionStatusFailed ||
			execution.Status == WorkflowExecutionStatusCancelled) &&
			execution.CompletedAt != nil &&
			execution.CompletedAt.Before(cutoff) {
			delete(wee.executions, id)
		}
	}
}

// Stop stops the execution engine
func (wee *WorkflowExecutionEngine) Stop() {
	close(wee.stopChan)
}

// Database operations

func (wee *WorkflowExecutionEngine) storeExecutionState(ctx context.Context, state *WorkflowExecutionState) error {
	query := `
		INSERT INTO workflow_executions (id, workflow_id, n8n_execution_id, status, input, output, error, 
		                                started_at, completed_at, last_updated_at, retry_count, max_retries, 
		                                metadata, tier)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'workflow')
		ON CONFLICT (id) DO UPDATE SET
			status = EXCLUDED.status,
			output = EXCLUDED.output,
			error = EXCLUDED.error,
			completed_at = EXCLUDED.completed_at,
			last_updated_at = EXCLUDED.last_updated_at,
			retry_count = EXCLUDED.retry_count,
			metadata = EXCLUDED.metadata
	`

	inputJSON, _ := json.Marshal(state.Input)
	outputJSON, _ := json.Marshal(state.Output)
	metadataJSON, _ := json.Marshal(state.Metadata)

	_, err := wee.db.Exec(ctx, query,
		state.ID,
		state.WorkflowID,
		state.N8nExecutionID,
		string(state.Status),
		inputJSON,
		outputJSON,
		state.Error,
		state.StartedAt,
		state.CompletedAt,
		state.LastUpdatedAt,
		state.RetryCount,
		state.MaxRetries,
		metadataJSON,
	)

	return err
}

func (wee *WorkflowExecutionEngine) updateExecutionState(ctx context.Context, state *WorkflowExecutionState) error {
	return wee.storeExecutionState(ctx, state)
}

func (wee *WorkflowExecutionEngine) loadExecutionState(ctx context.Context, executionID string) (*WorkflowExecutionState, error) {
	query := `
		SELECT id, workflow_id, n8n_execution_id, status, input, output, error, 
		       started_at, completed_at, last_updated_at, retry_count, max_retries, metadata
		FROM workflow_executions
		WHERE id = $1 AND tier = 'workflow'
	`

	var state WorkflowExecutionState
	var inputJSON, outputJSON, metadataJSON []byte
	var statusStr string

	err := wee.db.QueryRow(ctx, query, executionID).Scan(
		&state.ID,
		&state.WorkflowID,
		&state.N8nExecutionID,
		&statusStr,
		&inputJSON,
		&outputJSON,
		&state.Error,
		&state.StartedAt,
		&state.CompletedAt,
		&state.LastUpdatedAt,
		&state.RetryCount,
		&state.MaxRetries,
		&metadataJSON,
	)
	if err != nil {
		return nil, err
	}

	state.Status = WorkflowExecutionStatus(statusStr)

	// Parse JSON fields
	if len(inputJSON) > 0 {
		json.Unmarshal(inputJSON, &state.Input)
	}
	if len(outputJSON) > 0 {
		json.Unmarshal(outputJSON, &state.Output)
	}
	if len(metadataJSON) > 0 {
		json.Unmarshal(metadataJSON, &state.Metadata)
	}

	return &state, nil
}

// Helper function
func generateWorkflowExecutionID() string {
	return fmt.Sprintf("exec_%d", time.Now().UnixNano())
}
