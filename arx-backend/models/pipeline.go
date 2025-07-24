package models

import (
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

// PipelineExecution represents a pipeline execution record
type PipelineExecution struct {
	ID           uuid.UUID              `json:"id" db:"id"`
	System       string                 `json:"system" db:"system"`
	ObjectType   *string                `json:"object_type,omitempty" db:"object_type"`
	Status       string                 `json:"status" db:"status"`
	CreatedAt    time.Time              `json:"created_at" db:"created_at"`
	StartedAt    *time.Time             `json:"started_at,omitempty" db:"started_at"`
	CompletedAt  *time.Time             `json:"completed_at,omitempty" db:"completed_at"`
	ErrorMessage *string                `json:"error_message,omitempty" db:"error_message"`
	Metadata     map[string]interface{} `json:"metadata" db:"metadata"`
	CreatedBy    *string                `json:"created_by,omitempty" db:"created_by"`
	UpdatedAt    time.Time              `json:"updated_at" db:"updated_at"`
	Steps        []PipelineStep         `json:"steps,omitempty"`
}

// PipelineStep represents a step in a pipeline execution
type PipelineStep struct {
	ID           uuid.UUID              `json:"id" db:"id"`
	ExecutionID  uuid.UUID              `json:"execution_id" db:"execution_id"`
	StepName     string                 `json:"step_name" db:"step_name"`
	StepOrder    int                    `json:"step_order" db:"step_order"`
	Orchestrator string                 `json:"orchestrator" db:"orchestrator"`
	Status       string                 `json:"status" db:"status"`
	StartedAt    *time.Time             `json:"started_at,omitempty" db:"started_at"`
	CompletedAt  *time.Time             `json:"completed_at,omitempty" db:"completed_at"`
	ErrorMessage *string                `json:"error_message,omitempty" db:"error_message"`
	Metadata     map[string]interface{} `json:"metadata" db:"metadata"`
	CreatedAt    time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at" db:"updated_at"`
}

// PipelineConfiguration represents a pipeline configuration
type PipelineConfiguration struct {
	ID         uuid.UUID              `json:"id" db:"id"`
	System     string                 `json:"system" db:"system"`
	ConfigName string                 `json:"config_name" db:"config_name"`
	ConfigType string                 `json:"config_type" db:"config_type"`
	ConfigData map[string]interface{} `json:"config_data" db:"config_data"`
	IsActive   bool                   `json:"is_active" db:"is_active"`
	CreatedAt  time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at" db:"updated_at"`
	CreatedBy  *string                `json:"created_by,omitempty" db:"created_by"`
}

// PipelineQualityGate represents a quality gate for pipeline validation
type PipelineQualityGate struct {
	ID         uuid.UUID              `json:"id" db:"id"`
	GateName   string                 `json:"gate_name" db:"gate_name"`
	GateType   string                 `json:"gate_type" db:"gate_type"`
	GateConfig map[string]interface{} `json:"gate_config" db:"gate_config"`
	IsRequired bool                   `json:"is_required" db:"is_required"`
	IsActive   bool                   `json:"is_active" db:"is_active"`
	CreatedAt  time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at" db:"updated_at"`
}

// PipelineAuditLog represents an audit log entry for pipeline operations
type PipelineAuditLog struct {
	ID          uuid.UUID              `json:"id" db:"id"`
	ExecutionID *uuid.UUID             `json:"execution_id,omitempty" db:"execution_id"`
	StepID      *uuid.UUID             `json:"step_id,omitempty" db:"step_id"`
	Action      string                 `json:"action" db:"action"`
	ActionType  string                 `json:"action_type" db:"action_type"`
	Details     map[string]interface{} `json:"details" db:"details"`
	CreatedAt   time.Time              `json:"created_at" db:"created_at"`
	CreatedBy   *string                `json:"created_by,omitempty" db:"created_by"`
}

// PipelineExecutionSummary represents a summary view of pipeline executions
type PipelineExecutionSummary struct {
	ID              uuid.UUID  `json:"id" db:"id"`
	System          string     `json:"system" db:"system"`
	ObjectType      *string    `json:"object_type,omitempty" db:"object_type"`
	Status          string     `json:"status" db:"status"`
	CreatedAt       time.Time  `json:"created_at" db:"created_at"`
	CompletedAt     *time.Time `json:"completed_at,omitempty" db:"completed_at"`
	ErrorMessage    *string    `json:"error_message,omitempty" db:"error_message"`
	TotalSteps      int        `json:"total_steps" db:"total_steps"`
	CompletedSteps  int        `json:"completed_steps" db:"completed_steps"`
	FailedSteps     int        `json:"failed_steps" db:"failed_steps"`
	AvgStepDuration *float64   `json:"avg_step_duration,omitempty" db:"avg_step_duration"`
}

// PipelineQualityMetrics represents quality metrics for pipeline systems
type PipelineQualityMetrics struct {
	System               string     `json:"system" db:"system"`
	TotalExecutions      int        `json:"total_executions" db:"total_executions"`
	SuccessfulExecutions int        `json:"successful_executions" db:"successful_executions"`
	FailedExecutions     int        `json:"failed_executions" db:"failed_executions"`
	AvgExecutionTime     *float64   `json:"avg_execution_time,omitempty" db:"avg_execution_time"`
	LastExecution        *time.Time `json:"last_execution,omitempty" db:"last_execution"`
}

// PipelineRequest represents a request to execute a pipeline
type PipelineRequest struct {
	System     string   `json:"system" binding:"required"`
	ObjectType *string  `json:"object_type,omitempty"`
	Steps      []string `json:"steps,omitempty"`
	DryRun     bool     `json:"dry_run,omitempty"`
}

// PipelineResponse represents a response from pipeline operations
type PipelineResponse struct {
	Success     bool                   `json:"success"`
	ExecutionID *uuid.UUID             `json:"execution_id,omitempty"`
	Message     string                 `json:"message"`
	Error       *string                `json:"error,omitempty"`
	Status      string                 `json:"status,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
	Timestamp   time.Time              `json:"timestamp"`
}

// PipelineValidationRequest represents a validation request
type PipelineValidationRequest struct {
	System     string  `json:"system" binding:"required"`
	ObjectType *string `json:"object_type,omitempty"`
	Step       *string `json:"step,omitempty"`
}

// PipelineValidationResponse represents a validation response
type PipelineValidationResponse struct {
	Success   bool                   `json:"success"`
	Message   string                 `json:"message"`
	Error     *string                `json:"error,omitempty"`
	Details   map[string]interface{} `json:"details,omitempty"`
	Timestamp time.Time              `json:"timestamp"`
}

// Scan implements the sql.Scanner interface for PipelineExecution
func (pe *PipelineExecution) Scan(value interface{}) error {
	if value == nil {
		return nil
	}

	switch v := value.(type) {
	case []byte:
		return json.Unmarshal(v, pe)
	case string:
		return json.Unmarshal([]byte(v), pe)
	default:
		return nil
	}
}
