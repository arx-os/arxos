package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/ecosystem"
)

// WorkflowService implements the workflow tier business logic (Layer 3 - PAID)
type WorkflowService struct {
	db              *database.PostGISDB
	n8nService      *N8NService
	cmmcService     *CMMCService
	executionEngine *WorkflowExecutionEngine
}

// NewWorkflowService creates a new workflow service
func NewWorkflowService(db *database.PostGISDB, n8nService *N8NService, cmmcService *CMMCService) *WorkflowService {
	executionEngine := NewWorkflowExecutionEngine(db, n8nService)

	return &WorkflowService{
		db:              db,
		n8nService:      n8nService,
		cmmcService:     cmmcService,
		executionEngine: executionEngine,
	}
}

// Workflow management

func (ws *WorkflowService) CreateWorkflow(ctx context.Context, req ecosystem.CreateWorkflowRequest) (*ecosystem.Workflow, error) {
	// Validate request
	if req.Name == "" {
		return nil, fmt.Errorf("workflow name is required")
	}

	// Create workflow in n8n
	n8nWorkflow, err := ws.n8nService.CreateWorkflow(ctx, CreateWorkflowRequest{
		Name:        req.Name,
		Description: req.Description,
		Definition:  req.Definition,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create n8n workflow: %w", err)
	}

	// Store workflow metadata in database
	query := `
		INSERT INTO workflows (id, name, description, definition, status, n8n_workflow_id, user_id, tier, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
		RETURNING id, name, description, definition, status, tier, created_at, updated_at
	`

	var workflow ecosystem.Workflow
	workflowID := generateWorkflowID()

	err = ws.db.QueryRow(ctx, query,
		workflowID,
		req.Name,
		req.Description,
		req.Definition,
		"created",
		n8nWorkflow.ID,
		common.GetUserIDFromContextSafe(ctx), // Get from context
		string(ecosystem.TierWorkflow),
	).Scan(
		&workflow.ID,
		&workflow.Name,
		&workflow.Description,
		&workflow.Definition,
		&workflow.Status,
		&workflow.Tier,
		&workflow.CreatedAt,
		&workflow.UpdatedAt,
	)

	if err != nil {
		// Cleanup n8n workflow if database insert fails
		ws.n8nService.DeleteWorkflow(ctx, n8nWorkflow.ID)
		return nil, fmt.Errorf("failed to store workflow: %w", err)
	}

	return &workflow, nil
}

func (ws *WorkflowService) GetWorkflow(ctx context.Context, workflowID string) (*ecosystem.Workflow, error) {
	query := `
		SELECT id, name, description, definition, status, n8n_workflow_id, tier, created_at, updated_at
		FROM workflows
		WHERE id = $1
	`

	var workflow ecosystem.Workflow
	var n8nWorkflowID string

	err := ws.db.QueryRow(ctx, query, workflowID).Scan(
		&workflow.ID,
		&workflow.Name,
		&workflow.Description,
		&workflow.Definition,
		&workflow.Status,
		&n8nWorkflowID,
		&workflow.Tier,
		&workflow.CreatedAt,
		&workflow.UpdatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("workflow not found")
		}
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Get current status from n8n
	n8nWorkflow, err := ws.n8nService.GetWorkflow(ctx, n8nWorkflowID)
	if err != nil {
		// Log error but don't fail the request
		fmt.Printf("Warning: failed to get n8n workflow status: %v\n", err)
	} else {
		workflow.Status = mapN8NStatus(n8nWorkflow.Active)
	}

	return &workflow, nil
}

func (ws *WorkflowService) ListWorkflows(ctx context.Context, userID string) ([]*ecosystem.Workflow, error) {
	query := `
		SELECT id, name, description, definition, status, tier, created_at, updated_at
		FROM workflows
		WHERE user_id = $1
		ORDER BY created_at DESC
	`

	rows, err := ws.db.Query(ctx, query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to list workflows: %w", err)
	}
	defer rows.Close()

	var workflows []*ecosystem.Workflow
	for rows.Next() {
		var workflow ecosystem.Workflow
		err := rows.Scan(
			&workflow.ID,
			&workflow.Name,
			&workflow.Description,
			&workflow.Definition,
			&workflow.Status,
			&workflow.Tier,
			&workflow.CreatedAt,
			&workflow.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan workflow: %w", err)
		}
		workflows = append(workflows, &workflow)
	}

	return workflows, nil
}

func (ws *WorkflowService) UpdateWorkflow(ctx context.Context, workflowID string, updates map[string]interface{}) (*ecosystem.Workflow, error) {
	// Get existing workflow
	workflow, err := ws.GetWorkflow(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get existing workflow: %w", err)
	}

	// Get n8n workflow ID
	var n8nWorkflowID string
	err = ws.db.QueryRow(ctx, "SELECT n8n_workflow_id FROM workflows WHERE id = $1", workflowID).Scan(&n8nWorkflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get n8n workflow ID: %w", err)
	}

	// Update in n8n
	n8nUpdates := make(map[string]interface{})
	if name, ok := updates["name"].(string); ok {
		n8nUpdates["name"] = name
	}
	if definition, ok := updates["definition"].(map[string]interface{}); ok {
		n8nUpdates["nodes"] = ws.n8nService.convertNodes(definition)
		n8nUpdates["connections"] = ws.n8nService.convertConnections(definition)
	}

	if len(n8nUpdates) > 0 {
		_, err = ws.n8nService.UpdateWorkflow(ctx, n8nWorkflowID, n8nUpdates)
		if err != nil {
			return nil, fmt.Errorf("failed to update n8n workflow: %w", err)
		}
	}

	// Update in database
	setParts := []string{}
	args := []interface{}{}
	argIndex := 1

	for key, value := range updates {
		setParts = append(setParts, fmt.Sprintf("%s = $%d", key, argIndex))
		args = append(args, value)
		argIndex++
	}

	if len(setParts) > 0 {
		setParts = append(setParts, "updated_at = NOW()")
		args = append(args, workflowID)
		argIndex++

		query := fmt.Sprintf(`
			UPDATE workflows 
			SET %s 
			WHERE id = $%d
			RETURNING id, name, description, definition, status, tier, created_at, updated_at
		`, joinStrings(setParts, ", "), argIndex)

		err = ws.db.QueryRow(ctx, query, args...).Scan(
			&workflow.ID,
			&workflow.Name,
			&workflow.Description,
			&workflow.Definition,
			&workflow.Status,
			&workflow.Tier,
			&workflow.CreatedAt,
			&workflow.UpdatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to update workflow in database: %w", err)
		}
	}

	return workflow, nil
}

// ActivateWorkflow activates a workflow
func (s *WorkflowService) ActivateWorkflow(ctx context.Context, workflowID string) error {
	// Get workflow to get n8n ID
	workflow, err := s.GetWorkflow(ctx, workflowID)
	if err != nil {
		return fmt.Errorf("failed to get workflow: %w", err)
	}

	// Activate in n8n
	if err := s.n8nService.ActivateWorkflow(ctx, workflow.N8nWorkflowID); err != nil {
		return fmt.Errorf("failed to activate workflow in n8n: %w", err)
	}

	// Update status in database
	_, err = s.db.Exec(ctx,
		"UPDATE workflows SET status = 'active', updated_at = NOW() WHERE id = $1",
		workflowID)
	if err != nil {
		return fmt.Errorf("failed to update workflow status: %w", err)
	}

	return nil
}

// DeactivateWorkflow deactivates a workflow
func (s *WorkflowService) DeactivateWorkflow(ctx context.Context, workflowID string) error {
	// Get workflow to get n8n ID
	workflow, err := s.GetWorkflow(ctx, workflowID)
	if err != nil {
		return fmt.Errorf("failed to get workflow: %w", err)
	}

	// Deactivate in n8n
	if err := s.n8nService.DeactivateWorkflow(ctx, workflow.N8nWorkflowID); err != nil {
		return fmt.Errorf("failed to deactivate workflow in n8n: %w", err)
	}

	// Update status in database
	_, err = s.db.Exec(ctx,
		"UPDATE workflows SET status = 'inactive', updated_at = NOW() WHERE id = $1",
		workflowID)
	if err != nil {
		return fmt.Errorf("failed to update workflow status: %w", err)
	}

	return nil
}

// ListWorkflowExecutions lists workflow executions
func (s *WorkflowService) ListWorkflowExecutions(ctx context.Context, workflowID string, limit int) ([]*WorkflowExecutionResult, error) {
	return s.executionEngine.ListExecutions(ctx, workflowID, limit)
}

// GetCMMCService returns the CMMS service for access to maintenance operations
func (s *WorkflowService) GetCMMCService() *CMMCService {
	return s.cmmcService
}

func (ws *WorkflowService) DeleteWorkflow(ctx context.Context, workflowID string) error {
	// Get n8n workflow ID
	var n8nWorkflowID string
	err := ws.db.QueryRow(ctx, "SELECT n8n_workflow_id FROM workflows WHERE id = $1", workflowID).Scan(&n8nWorkflowID)
	if err != nil {
		return fmt.Errorf("failed to get n8n workflow ID: %w", err)
	}

	// Delete from n8n
	err = ws.n8nService.DeleteWorkflow(ctx, n8nWorkflowID)
	if err != nil {
		return fmt.Errorf("failed to delete n8n workflow: %w", err)
	}

	// Delete from database
	_, err = ws.db.Exec(ctx, "DELETE FROM workflows WHERE id = $1", workflowID)
	if err != nil {
		return fmt.Errorf("failed to delete workflow from database: %w", err)
	}

	return nil
}

func (ws *WorkflowService) ExecuteWorkflow(ctx context.Context, workflowID string, input map[string]interface{}) (*ecosystem.WorkflowResult, error) {
	// Create execution request
	execReq := WorkflowExecutionRequest{
		WorkflowID: workflowID,
		Input:      input,
		MaxRetries: 3,
		Timeout:    30 * time.Minute,
		Metadata: map[string]interface{}{
			"triggered_by": "api",
			"timestamp":    time.Now().Unix(),
		},
	}

	// Execute using the execution engine
	result, err := ws.executionEngine.ExecuteWorkflow(ctx, execReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute workflow: %w", err)
	}

	// Convert to ecosystem format
	workflowResult := &ecosystem.WorkflowResult{
		ID:         result.ExecutionID,
		WorkflowID: workflowID,
		Status:     string(result.Status),
		Output:     result.Output,
		Error:      result.Error,
		Metadata:   result.Metadata,
	}

	return workflowResult, nil
}

func (ws *WorkflowService) GetWorkflowStatus(ctx context.Context, executionID string) (*ecosystem.WorkflowExecutionStatus, error) {
	// Get execution from database
	var n8nExecutionID string
	var status string
	var startedAt time.Time

	err := ws.db.QueryRow(ctx, `
		SELECT n8n_execution_id, status, started_at 
		FROM workflow_executions 
		WHERE id = $1
	`, executionID).Scan(&n8nExecutionID, &status, &startedAt)

	if err != nil {
		return nil, fmt.Errorf("failed to get execution: %w", err)
	}

	// Get current status from n8n
	n8nExecution, err := ws.n8nService.GetExecution(ctx, n8nExecutionID)
	if err != nil {
		return nil, fmt.Errorf("failed to get n8n execution status: %w", err)
	}

	// Convert to ArxOS format
	workflowStatus := &ecosystem.WorkflowExecutionStatus{
		ExecutionID: executionID,
		Status:      ecosystem.WorkflowStatus(n8nExecution.Status),
		Progress:    float64(calculateProgress(n8nExecution.Status)),
		CurrentStep: getCurrentStep(n8nExecution.Status),
		LastUpdated: time.Now(),
	}

	// Add metrics if available
	if n8nExecution.Data != nil {
		workflowStatus.Metrics = map[string]interface{}{
			"nodes_executed": len(n8nExecution.Data),
			"status":         n8nExecution.Status,
		}
	}

	return workflowStatus, nil
}

func (ws *WorkflowService) PauseWorkflow(ctx context.Context, workflowID string) error {
	// Get n8n workflow ID
	var n8nWorkflowID string
	err := ws.db.QueryRow(ctx, "SELECT n8n_workflow_id FROM workflows WHERE id = $1", workflowID).Scan(&n8nWorkflowID)
	if err != nil {
		return fmt.Errorf("failed to get n8n workflow ID: %w", err)
	}

	// Deactivate in n8n
	err = ws.n8nService.DeactivateWorkflow(ctx, n8nWorkflowID)
	if err != nil {
		return fmt.Errorf("failed to pause n8n workflow: %w", err)
	}

	// Update status in database
	_, err = ws.db.Exec(ctx, "UPDATE workflows SET status = 'paused', updated_at = NOW() WHERE id = $1", workflowID)
	if err != nil {
		return fmt.Errorf("failed to update workflow status: %w", err)
	}

	return nil
}

func (ws *WorkflowService) ResumeWorkflow(ctx context.Context, workflowID string) error {
	// Get n8n workflow ID
	var n8nWorkflowID string
	err := ws.db.QueryRow(ctx, "SELECT n8n_workflow_id FROM workflows WHERE id = $1", workflowID).Scan(&n8nWorkflowID)
	if err != nil {
		return fmt.Errorf("failed to get n8n workflow ID: %w", err)
	}

	// Activate in n8n
	err = ws.n8nService.ActivateWorkflow(ctx, n8nWorkflowID)
	if err != nil {
		return fmt.Errorf("failed to resume n8n workflow: %w", err)
	}

	// Update status in database
	_, err = ws.db.Exec(ctx, "UPDATE workflows SET status = 'active', updated_at = NOW() WHERE id = $1", workflowID)
	if err != nil {
		return fmt.Errorf("failed to update workflow status: %w", err)
	}

	return nil
}

// Helper functions

func mapN8NStatus(active bool) string {
	if active {
		return "active"
	}
	return "inactive"
}

func calculateProgress(status string) int {
	switch status {
	case "running":
		return 50
	case "success":
		return 100
	case "error":
		return 0
	case "waiting":
		return 25
	default:
		return 0
	}
}

func getCurrentStep(status string) string {
	switch status {
	case "running":
		return "executing_nodes"
	case "success":
		return "completed"
	case "error":
		return "failed"
	case "waiting":
		return "waiting_for_input"
	default:
		return "unknown"
	}
}

func generateWorkflowID() string {
	return fmt.Sprintf("workflow_%d", time.Now().UnixNano())
}

func generateExecutionID() string {
	return fmt.Sprintf("execution_%d", time.Now().UnixNano())
}

func joinStrings(strs []string, sep string) string {
	if len(strs) == 0 {
		return ""
	}
	if len(strs) == 1 {
		return strs[0]
	}

	result := strs[0]
	for i := 1; i < len(strs); i++ {
		result += sep + strs[i]
	}
	return result
}
