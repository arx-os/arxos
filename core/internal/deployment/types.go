package deployment

import (
	"encoding/json"
	"fmt"
	"time"
)

// CreateDeploymentRequest represents a request to create a deployment
type CreateDeploymentRequest struct {
	Name        string `json:"name" validate:"required,min=1,max=255"`
	Description string `json:"description"`
	
	// Source configuration
	SourceStateID string          `json:"source_state_id"`
	TemplateID    string          `json:"template_id"`
	Config        json.RawMessage `json:"config"`
	
	// Target selection
	TargetQuery     string   `json:"target_query"`     // AQL query
	TargetBuildings []string `json:"target_buildings"` // Explicit building IDs
	
	// Strategy
	Strategy       DeploymentStrategy `json:"strategy" validate:"required,oneof=immediate canary rolling blue_green"`
	StrategyConfig json.RawMessage    `json:"strategy_config"`
	
	// Options
	RollbackEnabled    bool            `json:"rollback_enabled"`
	HealthCheckEnabled bool            `json:"health_check_enabled"`
	HealthCheckConfig  json.RawMessage `json:"health_check_config"`
	
	// Scheduling
	ScheduledAt *time.Time `json:"scheduled_at"`
	
	// Ownership
	CreatedBy     string `json:"created_by" validate:"required"`
	CreatedByName string `json:"created_by_name" validate:"required"`
	
	// Metadata
	Tags     []string               `json:"tags"`
	Metadata map[string]interface{} `json:"metadata"`
}

// Validate validates the deployment request
func (r *CreateDeploymentRequest) Validate() error {
	if r.Name == "" {
		return fmt.Errorf("deployment name is required")
	}
	
	if r.SourceStateID == "" && r.TemplateID == "" && r.Config == nil {
		return fmt.Errorf("source state, template, or config must be specified")
	}
	
	if r.TargetQuery == "" && len(r.TargetBuildings) == 0 {
		return fmt.Errorf("target query or explicit target buildings must be specified")
	}
	
	if r.Strategy == "" {
		return fmt.Errorf("deployment strategy is required")
	}
	
	// Validate strategy
	switch r.Strategy {
	case StrategyImmediate, StrategyCanary, StrategyRolling, StrategyBlueGreen:
		// Valid strategies
	default:
		return fmt.Errorf("invalid deployment strategy: %s", r.Strategy)
	}
	
	if r.CreatedBy == "" || r.CreatedByName == "" {
		return fmt.Errorf("creator information is required")
	}
	
	return nil
}

// UpdateDeploymentRequest represents a request to update a deployment
type UpdateDeploymentRequest struct {
	Name        *string `json:"name"`
	Description *string `json:"description"`
	
	// Target updates
	TargetQuery     *string  `json:"target_query"`
	TargetBuildings []string `json:"target_buildings"`
	
	// Strategy updates
	StrategyConfig json.RawMessage `json:"strategy_config"`
	
	// Options updates
	RollbackEnabled    *bool           `json:"rollback_enabled"`
	HealthCheckEnabled *bool           `json:"health_check_enabled"`
	HealthCheckConfig  json.RawMessage `json:"health_check_config"`
	
	// Scheduling
	ScheduledAt *time.Time `json:"scheduled_at"`
	
	// Metadata
	Tags     []string               `json:"tags"`
	Metadata map[string]interface{} `json:"metadata"`
}

// ApprovalRequest represents a deployment approval request
type ApprovalRequest struct {
	DeploymentID      string   `json:"deployment_id" validate:"required"`
	RequiredApprovers []string `json:"required_approvers"`
	MinimumApprovals  int      `json:"minimum_approvals"`
	DeadlineHours     int      `json:"deadline_hours"`
	NotifyEmails      []string `json:"notify_emails"`
	Comments          string   `json:"comments"`
}

// ApprovalResponse represents an approval response
type ApprovalResponse struct {
	DeploymentID string    `json:"deployment_id"`
	ApproverID   string    `json:"approver_id"`
	ApproverName string    `json:"approver_name"`
	Approved     bool      `json:"approved"`
	Comments     string    `json:"comments"`
	ApprovedAt   time.Time `json:"approved_at"`
}

// RollbackRequest represents a deployment rollback request
type RollbackRequest struct {
	DeploymentID string   `json:"deployment_id" validate:"required"`
	Scope        string   `json:"scope" validate:"required,oneof=full partial single_building"`
	Buildings    []string `json:"buildings"` // For partial or single_building scope
	Reason       string   `json:"reason" validate:"required"`
	Force        bool     `json:"force"`      // Skip validation checks
}

// DeploymentListRequest represents a request to list deployments
type DeploymentListRequest struct {
	// Filters
	Status       []string  `json:"status"`
	Strategy     []string  `json:"strategy"`
	CreatedBy    string    `json:"created_by"`
	BuildingID   string    `json:"building_id"`
	Tags         []string  `json:"tags"`
	CreatedAfter time.Time `json:"created_after"`
	CreatedBefore time.Time `json:"created_before"`
	
	// Pagination
	Limit  int `json:"limit"`
	Offset int `json:"offset"`
	
	// Sorting
	SortBy    string `json:"sort_by"`    // created_at, updated_at, name, status
	SortOrder string `json:"sort_order"` // asc, desc
}

// DeploymentSummary provides a summary of a deployment
type DeploymentSummary struct {
	ID               string             `json:"id"`
	Name             string             `json:"name"`
	Status           DeploymentStatus   `json:"status"`
	Strategy         DeploymentStrategy `json:"strategy"`
	TargetCount      int                `json:"target_count"`
	SuccessfulCount  int                `json:"successful_count"`
	FailedCount      int                `json:"failed_count"`
	Progress         int                `json:"progress_percentage"`
	CreatedAt        time.Time          `json:"created_at"`
	StartedAt        *time.Time         `json:"started_at"`
	CompletedAt      *time.Time         `json:"completed_at"`
	Duration         *time.Duration     `json:"duration,omitempty"`
}

// DeploymentDetails provides detailed information about a deployment
type DeploymentDetails struct {
	Deployment *Deployment         `json:"deployment"`
	Targets    []*DeploymentTarget `json:"targets"`
	Approvals  []*ApprovalResponse `json:"approvals,omitempty"`
	Metrics    *DeploymentMetrics  `json:"metrics,omitempty"`
	Events     []DeploymentEvent   `json:"events,omitempty"`
}

// DeploymentEvent represents an event during deployment
type DeploymentEvent struct {
	Timestamp   time.Time              `json:"timestamp"`
	Type        string                 `json:"type"`
	Level       string                 `json:"level"` // info, warning, error
	Message     string                 `json:"message"`
	Details     map[string]interface{} `json:"details,omitempty"`
	BuildingID  string                 `json:"building_id,omitempty"`
	TargetID    string                 `json:"target_id,omitempty"`
}

// Monitor events
type DeploymentCreatedEvent struct {
	DeploymentID string `json:"deployment_id"`
	Name         string `json:"name"`
	TargetCount  int    `json:"target_count"`
	Strategy     string `json:"strategy"`
}

type DeploymentStartedEvent struct {
	DeploymentID string    `json:"deployment_id"`
	StartTime    time.Time `json:"start_time"`
}

type DeploymentProgressEvent struct {
	DeploymentID string  `json:"deployment_id"`
	Progress     int     `json:"progress"`
	Successful   int     `json:"successful"`
	Failed       int     `json:"failed"`
	Pending      int     `json:"pending"`
}

type DeploymentCompletedEvent struct {
	DeploymentID    string        `json:"deployment_id"`
	SuccessfulCount int           `json:"successful_count"`
	FailedCount     int           `json:"failed_count"`
	Duration        time.Duration `json:"duration"`
}

type DeploymentFailedEvent struct {
	DeploymentID string `json:"deployment_id"`
	Error        string `json:"error"`
	FailedCount  int    `json:"failed_count"`
}

type DeploymentRolledBackEvent struct {
	DeploymentID    string   `json:"deployment_id"`
	Reason          string   `json:"reason"`
	AffectedTargets []string `json:"affected_targets"`
}

type TargetDeploymentStartedEvent struct {
	DeploymentID string `json:"deployment_id"`
	TargetID     string `json:"target_id"`
	BuildingID   string `json:"building_id"`
	Wave         int    `json:"wave"`
}

type TargetDeploymentCompletedEvent struct {
	DeploymentID string        `json:"deployment_id"`
	TargetID     string        `json:"target_id"`
	BuildingID   string        `json:"building_id"`
	Success      bool          `json:"success"`
	Duration     time.Duration `json:"duration"`
}

type HealthCheckFailedEvent struct {
	DeploymentID string  `json:"deployment_id"`
	TargetID     string  `json:"target_id"`
	BuildingID   string  `json:"building_id"`
	CheckType    string  `json:"check_type"` // pre, post
	Score        float64 `json:"score"`
	Issues       []string `json:"issues"`
}

// StrategyConfig types for different strategies

// ImmediateStrategyConfig configures immediate deployment
type ImmediateStrategyConfig struct {
	ParallelExecution bool `json:"parallel_execution"`
	MaxParallel       int  `json:"max_parallel"`
	TimeoutMinutes    int  `json:"timeout_minutes"`
	StopOnFirstError  bool `json:"stop_on_first_error"`
}

// CanaryStrategyConfig configures canary deployment
type CanaryStrategyConfig struct {
	CanaryPercentage       int  `json:"canary_percentage"`
	ValidationPeriodMinutes int  `json:"validation_period_minutes"`
	AutoPromote            bool `json:"auto_promote"`
	SuccessThreshold       float64 `json:"success_threshold"`
	MetricsToMonitor       []string `json:"metrics_to_monitor"`
}

// RollingStrategyConfig configures rolling deployment
type RollingStrategyConfig struct {
	WaveSizePercentage int  `json:"wave_size_percentage"`
	WaveSizeFixed      int  `json:"wave_size_fixed"`
	WaveDelayMinutes   int  `json:"wave_delay_minutes"`
	StopOnFailure      bool `json:"stop_on_failure"`
	MaxFailureRate     float64 `json:"max_failure_rate"`
}

// BlueGreenStrategyConfig configures blue-green deployment
type BlueGreenStrategyConfig struct {
	ValidationPeriodMinutes int   `json:"validation_period_minutes"`
	TrafficShiftPercentage  []int `json:"traffic_shift_percentage"` // e.g., [0, 50, 100]
	TrafficShiftDelayMinutes int   `json:"traffic_shift_delay_minutes"`
	RollbackWindowHours     int   `json:"rollback_window_hours"`
	AutoSwitch              bool  `json:"auto_switch"`
}

// HealthCheckConfig configures health checks
type HealthCheckConfig struct {
	Enabled           bool              `json:"enabled"`
	PreDeploymentChecks  []HealthCheck `json:"pre_deployment_checks"`
	PostDeploymentChecks []HealthCheck `json:"post_deployment_checks"`
	ContinuousMonitoring bool          `json:"continuous_monitoring"`
	MonitoringInterval   int           `json:"monitoring_interval_minutes"`
	FailureThreshold     float64       `json:"failure_threshold"`
}

// HealthCheck defines a single health check
type HealthCheck struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"` // system, performance, compliance, custom
	Enabled     bool                   `json:"enabled"`
	Critical    bool                   `json:"critical"`
	Timeout     int                    `json:"timeout_seconds"`
	Parameters  map[string]interface{} `json:"parameters"`
	Thresholds  HealthCheckThresholds  `json:"thresholds"`
}

// HealthCheckThresholds defines thresholds for health checks
type HealthCheckThresholds struct {
	MinScore        float64                `json:"min_score"`
	MaxResponseTime int                    `json:"max_response_time_ms"`
	MaxErrorRate    float64                `json:"max_error_rate"`
	CustomMetrics   map[string]interface{} `json:"custom_metrics"`
}

// RollbackPolicy defines rollback behavior
type RollbackPolicy struct {
	Enabled              bool    `json:"enabled"`
	AutoRollback         bool    `json:"auto_rollback"`
	RollbackOnHealthFail bool    `json:"rollback_on_health_fail"`
	RollbackOnValidationFail bool `json:"rollback_on_validation_fail"`
	MaxRollbackTime      int     `json:"max_rollback_time_minutes"`
	PreserveData         bool    `json:"preserve_data"`
}