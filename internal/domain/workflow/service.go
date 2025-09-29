package workflow

import (
	"context"
	"time"

	"github.com/google/uuid"
)

// Service defines the interface for workflow business logic following Clean Architecture principles
type Service interface {
	// Workflow management
	CreateWorkflow(ctx context.Context, req CreateWorkflowRequest) (*Workflow, error)
	GetWorkflow(ctx context.Context, id uuid.UUID) (*Workflow, error)
	UpdateWorkflow(ctx context.Context, id uuid.UUID, req UpdateWorkflowRequest) (*Workflow, error)
	DeleteWorkflow(ctx context.Context, id uuid.UUID) error
	ListWorkflows(ctx context.Context, req ListWorkflowsRequest) ([]*Workflow, error)

	// Workflow execution
	ExecuteWorkflow(ctx context.Context, id uuid.UUID, req ExecuteWorkflowRequest) (*Execution, error)
	GetExecution(ctx context.Context, id uuid.UUID) (*Execution, error)
	GetExecutionHistory(ctx context.Context, workflowID uuid.UUID) ([]*Execution, error)

	// Workflow triggers
	CreateTrigger(ctx context.Context, req CreateTriggerRequest) (*Trigger, error)
	UpdateTrigger(ctx context.Context, id uuid.UUID, req UpdateTriggerRequest) (*Trigger, error)
	DeleteTrigger(ctx context.Context, id uuid.UUID) error
	ListTriggers(ctx context.Context, workflowID uuid.UUID) ([]*Trigger, error)
}

// Workflow represents a workflow entity
type Workflow struct {
	ID          uuid.UUID              `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Definition  map[string]interface{} `json:"definition"`
	Status      string                 `json:"status"` // active, inactive, draft
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	CreatedBy   string                 `json:"created_by"`
}

// Execution represents a workflow execution
type Execution struct {
	ID          uuid.UUID              `json:"id"`
	WorkflowID  uuid.UUID              `json:"workflow_id"`
	Status      string                 `json:"status"` // running, completed, failed, cancelled
	Input       map[string]interface{} `json:"input"`
	Output      map[string]interface{} `json:"output"`
	StartedAt   time.Time              `json:"started_at"`
	CompletedAt *time.Time             `json:"completed_at,omitempty"`
	Error       string                 `json:"error,omitempty"`
}

// Trigger represents a workflow trigger
type Trigger struct {
	ID         uuid.UUID              `json:"id"`
	WorkflowID uuid.UUID              `json:"workflow_id"`
	Type       string                 `json:"type"` // schedule, webhook, event, manual
	Config     map[string]interface{} `json:"config"`
	Status     string                 `json:"status"` // active, inactive
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
}

// Request types
type CreateWorkflowRequest struct {
	Name        string                 `json:"name" validate:"required"`
	Description string                 `json:"description"`
	Definition  map[string]interface{} `json:"definition" validate:"required"`
	Status      string                 `json:"status"`
}

type UpdateWorkflowRequest struct {
	Name        *string                `json:"name,omitempty"`
	Description *string                `json:"description,omitempty"`
	Definition  map[string]interface{} `json:"definition,omitempty"`
	Status      *string                `json:"status,omitempty"`
}

type ListWorkflowsRequest struct {
	Status string `json:"status"`
	Limit  int    `json:"limit" validate:"min=1,max=100"`
	Offset int    `json:"offset" validate:"min=0"`
}

type ExecuteWorkflowRequest struct {
	Input map[string]interface{} `json:"input"`
	Async bool                   `json:"async"`
}

type CreateTriggerRequest struct {
	WorkflowID uuid.UUID              `json:"workflow_id" validate:"required"`
	Type       string                 `json:"type" validate:"required"`
	Config     map[string]interface{} `json:"config" validate:"required"`
	Status     string                 `json:"status"`
}

type UpdateTriggerRequest struct {
	Type   *string                `json:"type,omitempty"`
	Config map[string]interface{} `json:"config,omitempty"`
	Status *string                `json:"status,omitempty"`
}
