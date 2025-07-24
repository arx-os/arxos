package workflow

import (
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// WorkflowStatus represents the status of a workflow
type WorkflowStatus string

const (
	StatusPending   WorkflowStatus = "pending"
	StatusRunning   WorkflowStatus = "running"
	StatusCompleted WorkflowStatus = "completed"
	StatusFailed    WorkflowStatus = "failed"
	StatusCancelled WorkflowStatus = "cancelled"
	StatusPaused    WorkflowStatus = "paused"
)

// WorkflowType represents the type of workflow
type WorkflowType string

const (
	TypeValidation     WorkflowType = "validation"
	TypeExport         WorkflowType = "export"
	TypeReporting      WorkflowType = "reporting"
	TypeDataProcessing WorkflowType = "data_processing"
	TypeIntegration    WorkflowType = "integration"
	TypeCleanup        WorkflowType = "cleanup"
)

// StepType represents the type of workflow step
type StepType string

const (
	StepValidation    StepType = "validation"
	StepExport        StepType = "export"
	StepTransform     StepType = "transform"
	StepNotify        StepType = "notify"
	StepCondition     StepType = "condition"
	StepLoop          StepType = "loop"
	StepParallel      StepType = "parallel"
	StepDelay         StepType = "delay"
	StepAPICall       StepType = "api_call"
	StepFileOperation StepType = "file_operation"
)

// ConditionType represents the type of condition
type ConditionType string

const (
	ConditionEquals      ConditionType = "equals"
	ConditionNotEquals   ConditionType = "not_equals"
	ConditionGreaterThan ConditionType = "greater_than"
	ConditionLessThan    ConditionType = "less_than"
	ConditionContains    ConditionType = "contains"
	ConditionNotContains ConditionType = "not_contains"
	ConditionExists      ConditionType = "exists"
	ConditionNotExists   ConditionType = "not_exists"
)

// WorkflowStep represents a step in a workflow
type WorkflowStep struct {
	StepID     string                   `json:"step_id"`
	Name       string                   `json:"name"`
	StepType   StepType                 `json:"step_type"`
	Parameters map[string]interface{}   `json:"parameters"`
	Conditions []map[string]interface{} `json:"conditions"`
	Timeout    int                      `json:"timeout"`
	RetryCount int                      `json:"retry_count"`
	RetryDelay int                      `json:"retry_delay"`
	Parallel   bool                     `json:"parallel"`
	Required   bool                     `json:"required"`
}

// WorkflowDefinition represents a workflow definition
type WorkflowDefinition struct {
	WorkflowID    string                   `json:"workflow_id" gorm:"primaryKey"`
	Name          string                   `json:"name"`
	Description   string                   `json:"description"`
	WorkflowType  WorkflowType             `json:"workflow_type"`
	Steps         []WorkflowStep           `json:"steps" gorm:"type:json"`
	Triggers      []map[string]interface{} `json:"triggers" gorm:"type:json"`
	Schedule      *string                  `json:"schedule"`
	Timeout       int                      `json:"timeout"`
	MaxRetries    int                      `json:"max_retries"`
	ErrorHandling map[string]interface{}   `json:"error_handling" gorm:"type:json"`
	Metadata      map[string]interface{}   `json:"metadata" gorm:"type:json"`
	CreatedAt     time.Time                `json:"created_at"`
	UpdatedAt     time.Time                `json:"updated_at"`
}

// WorkflowExecution represents a workflow execution instance
type WorkflowExecution struct {
	ExecutionID string                 `json:"execution_id" gorm:"primaryKey"`
	WorkflowID  string                 `json:"workflow_id"`
	Status      WorkflowStatus         `json:"status"`
	StartTime   time.Time              `json:"start_time"`
	EndTime     *time.Time             `json:"end_time"`
	CurrentStep *string                `json:"current_step"`
	Progress    float64                `json:"progress"`
	Result      map[string]interface{} `json:"result" gorm:"type:json"`
	Error       *string                `json:"error"`
	Context     map[string]interface{} `json:"context" gorm:"type:json"`
	Metadata    map[string]interface{} `json:"metadata" gorm:"type:json"`
}

// StepExecution represents a step execution instance
type StepExecution struct {
	StepExecutionID     string                 `json:"step_execution_id" gorm:"primaryKey"`
	WorkflowExecutionID string                 `json:"workflow_execution_id"`
	StepID              string                 `json:"step_id"`
	Status              WorkflowStatus         `json:"status"`
	StartTime           time.Time              `json:"start_time"`
	EndTime             *time.Time             `json:"end_time"`
	Result              map[string]interface{} `json:"result" gorm:"type:json"`
	Error               *string                `json:"error"`
	RetryCount          int                    `json:"retry_count"`
	Duration            float64                `json:"duration"`
}

// WorkflowEngine provides workflow execution and orchestration
type WorkflowEngine struct {
	db             *gorm.DB
	workflows      map[string]*WorkflowDefinition
	executions     map[string]*WorkflowExecution
	executionQueue chan string
	lock           sync.RWMutex
	running        bool
	executor       *WorkflowExecutor
	monitor        *WorkflowMonitor
	manager        *WorkflowManager
}

// NewWorkflowEngine creates a new workflow engine
func NewWorkflowEngine(db *gorm.DB) *WorkflowEngine {
	engine := &WorkflowEngine{
		db:             db,
		workflows:      make(map[string]*WorkflowDefinition),
		executions:     make(map[string]*WorkflowExecution),
		executionQueue: make(chan string, 100),
		running:        true,
	}

	// Initialize components
	engine.executor = NewWorkflowExecutor(engine)
	engine.monitor = NewWorkflowMonitor(engine)
	engine.manager = NewWorkflowManager(engine)

	// Start execution worker
	go engine.executionWorker()

	// Load default workflows
	engine.loadDefaultWorkflows()

	return engine
}

// CreateWorkflow creates a new workflow definition
func (e *WorkflowEngine) CreateWorkflow(workflowData map[string]interface{}) (*WorkflowDefinition, error) {
	workflow, err := e.createWorkflowFromMap(workflowData)
	if err != nil {
		return nil, fmt.Errorf("failed to create workflow: %w", err)
	}

	e.lock.Lock()
	defer e.lock.Unlock()

	e.workflows[workflow.WorkflowID] = workflow

	// Save to database
	if err := e.db.Create(workflow).Error; err != nil {
		return nil, fmt.Errorf("failed to save workflow: %w", err)
	}

	return workflow, nil
}

// ExecuteWorkflow executes a workflow
func (e *WorkflowEngine) ExecuteWorkflow(workflowID string, context map[string]interface{}) (string, error) {
	e.lock.RLock()
	workflow, exists := e.workflows[workflowID]
	e.lock.RUnlock()

	if !exists {
		return "", fmt.Errorf("workflow %s not found", workflowID)
	}

	executionID := e.generateExecutionID()
	execution := &WorkflowExecution{
		ExecutionID: executionID,
		WorkflowID:  workflowID,
		Status:      StatusPending,
		StartTime:   time.Now(),
		Context:     context,
		Progress:    0.0,
	}

	e.lock.Lock()
	e.executions[executionID] = execution
	e.lock.Unlock()

	// Save to database
	if err := e.db.Create(execution).Error; err != nil {
		return "", fmt.Errorf("failed to save execution: %w", err)
	}

	// Queue for execution
	e.executionQueue <- executionID

	return executionID, nil
}

// GetWorkflowStatus gets the status of a workflow execution
func (e *WorkflowEngine) GetWorkflowStatus(executionID string) (map[string]interface{}, error) {
	e.lock.RLock()
	execution, exists := e.executions[executionID]
	e.lock.RUnlock()

	if !exists {
		return nil, fmt.Errorf("execution %s not found", executionID)
	}

	return map[string]interface{}{
		"execution_id": execution.ExecutionID,
		"workflow_id":  execution.WorkflowID,
		"status":       execution.Status,
		"progress":     execution.Progress,
		"current_step": execution.CurrentStep,
		"start_time":   execution.StartTime,
		"end_time":     execution.EndTime,
		"error":        execution.Error,
	}, nil
}

// CancelWorkflow cancels a workflow execution
func (e *WorkflowEngine) CancelWorkflow(executionID string) error {
	e.lock.Lock()
	defer e.lock.Unlock()

	execution, exists := e.executions[executionID]
	if !exists {
		return fmt.Errorf("execution %s not found", executionID)
	}

	if execution.Status == StatusPending || execution.Status == StatusRunning {
		execution.Status = StatusCancelled
		now := time.Now()
		execution.EndTime = &now

		// Update in database
		if err := e.db.Save(execution).Error; err != nil {
			return fmt.Errorf("failed to update execution: %w", err)
		}

		return nil
	}

	return fmt.Errorf("cannot cancel execution in status: %s", execution.Status)
}

// GetWorkflowHistory gets the execution history of a workflow
func (e *WorkflowEngine) GetWorkflowHistory(workflowID string, limit int) ([]map[string]interface{}, error) {
	var executions []WorkflowExecution
	if err := e.db.Where("workflow_id = ?", workflowID).
		Order("start_time DESC").
		Limit(limit).
		Find(&executions).Error; err != nil {
		return nil, fmt.Errorf("failed to get workflow history: %w", err)
	}

	var results []map[string]interface{}
	for _, execution := range executions {
		results = append(results, map[string]interface{}{
			"execution_id": execution.ExecutionID,
			"workflow_id":  execution.WorkflowID,
			"status":       execution.Status,
			"start_time":   execution.StartTime,
			"end_time":     execution.EndTime,
			"current_step": execution.CurrentStep,
			"progress":     execution.Progress,
			"result":       execution.Result,
			"error":        execution.Error,
		})
	}

	return results, nil
}

// ListWorkflows lists all workflows
func (e *WorkflowEngine) ListWorkflows() ([]map[string]interface{}, error) {
	e.lock.RLock()
	defer e.lock.RUnlock()

	var workflows []map[string]interface{}
	for _, workflow := range e.workflows {
		workflows = append(workflows, map[string]interface{}{
			"workflow_id":   workflow.WorkflowID,
			"name":          workflow.Name,
			"description":   workflow.Description,
			"workflow_type": workflow.WorkflowType,
			"steps_count":   len(workflow.Steps),
			"timeout":       workflow.Timeout,
			"max_retries":   workflow.MaxRetries,
		})
	}

	return workflows, nil
}

// GetMetrics gets workflow engine metrics
func (e *WorkflowEngine) GetMetrics() map[string]interface{} {
	e.lock.RLock()
	defer e.lock.RUnlock()

	activeExecutions := 0
	for _, execution := range e.executions {
		if execution.Status == StatusRunning {
			activeExecutions++
		}
	}

	return map[string]interface{}{
		"total_workflows":   len(e.workflows),
		"active_executions": activeExecutions,
		"total_executions":  len(e.executions),
		"queue_size":        len(e.executionQueue),
		"engine_running":    e.running,
	}
}

// Helper methods

func (e *WorkflowEngine) executionWorker() {
	for e.running {
		select {
		case executionID := <-e.executionQueue:
			e.executeWorkflow(executionID)
		case <-time.After(time.Second):
			// Continue loop
		}
	}
}

func (e *WorkflowEngine) executeWorkflow(executionID string) {
	e.lock.RLock()
	execution, exists := e.executions[executionID]
	e.lock.RUnlock()

	if !exists {
		return
	}

	e.lock.RLock()
	workflow, exists := e.workflows[execution.WorkflowID]
	e.lock.RUnlock()

	if !exists {
		return
	}

	// Update execution status
	execution.Status = StatusRunning
	execution.StartTime = time.Now()
	e.db.Save(execution)

	// Execute steps
	context := execution.Context
	if context == nil {
		context = make(map[string]interface{})
	}

	result := make(map[string]interface{})

	for i, step := range workflow.Steps {
		// Update current step
		execution.CurrentStep = &step.StepID
		execution.Progress = float64(i) / float64(len(workflow.Steps)) * 100
		e.db.Save(execution)

		// Check conditions
		if !e.evaluateConditions(step.Conditions, context) {
			continue
		}

		// Execute step
		stepResult, err := e.executor.ExecuteStep(step, context, executionID)
		if err != nil {
			stepResult = map[string]interface{}{
				"status": "failed",
				"error":  err.Error(),
			}
		}

		context[step.StepID] = stepResult
		result[step.StepID] = stepResult

		// Check for step failure
		if stepResult["status"] == "failed" && step.Required {
			execution.Status = StatusFailed
			errorMsg := fmt.Sprintf("Required step %s failed: %v", step.StepID, stepResult["error"])
			execution.Error = &errorMsg
			now := time.Now()
			execution.EndTime = &now
			e.db.Save(execution)
			return
		}
	}

	// Complete execution
	execution.Status = StatusCompleted
	now := time.Now()
	execution.EndTime = &now
	execution.Progress = 100.0
	execution.Result = result
	e.db.Save(execution)
}

func (e *WorkflowEngine) createWorkflowFromMap(workflowData map[string]interface{}) (*WorkflowDefinition, error) {
	workflowID, ok := workflowData["workflow_id"].(string)
	if !ok {
		return nil, fmt.Errorf("workflow_id is required")
	}

	name, ok := workflowData["name"].(string)
	if !ok {
		return nil, fmt.Errorf("name is required")
	}

	workflowTypeStr, ok := workflowData["workflow_type"].(string)
	if !ok {
		return nil, fmt.Errorf("workflow_type is required")
	}

	// Parse steps
	stepsData, ok := workflowData["steps"].([]interface{})
	if !ok {
		return nil, fmt.Errorf("steps is required")
	}

	var steps []WorkflowStep
	for _, stepData := range stepsData {
		stepMap, ok := stepData.(map[string]interface{})
		if !ok {
			continue
		}

		step, err := e.createStepFromMap(stepMap)
		if err != nil {
			return nil, fmt.Errorf("failed to create step: %w", err)
		}

		steps = append(steps, *step)
	}

	// Parse triggers
	var triggers []map[string]interface{}
	if triggersData, ok := workflowData["triggers"].([]interface{}); ok {
		for _, triggerData := range triggersData {
			if triggerMap, ok := triggerData.(map[string]interface{}); ok {
				triggers = append(triggers, triggerMap)
			}
		}
	}

	workflow := &WorkflowDefinition{
		WorkflowID:   workflowID,
		Name:         name,
		Description:  workflowData["description"].(string),
		WorkflowType: WorkflowType(workflowTypeStr),
		Steps:        steps,
		Triggers:     triggers,
		Timeout:      int(workflowData["timeout"].(float64)),
		MaxRetries:   int(workflowData["max_retries"].(float64)),
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	if schedule, ok := workflowData["schedule"].(string); ok {
		workflow.Schedule = &schedule
	}

	return workflow, nil
}

func (e *WorkflowEngine) createStepFromMap(stepData map[string]interface{}) (*WorkflowStep, error) {
	stepID, ok := stepData["step_id"].(string)
	if !ok {
		return nil, fmt.Errorf("step_id is required")
	}

	name, ok := stepData["name"].(string)
	if !ok {
		return nil, fmt.Errorf("name is required")
	}

	stepTypeStr, ok := stepData["step_type"].(string)
	if !ok {
		return nil, fmt.Errorf("step_type is required")
	}

	parameters, ok := stepData["parameters"].(map[string]interface{})
	if !ok {
		parameters = make(map[string]interface{})
	}

	conditions, ok := stepData["conditions"].([]interface{})
	if !ok {
		conditions = []interface{}{}
	}

	var conditionMaps []map[string]interface{}
	for _, condition := range conditions {
		if conditionMap, ok := condition.(map[string]interface{}); ok {
			conditionMaps = append(conditionMaps, conditionMap)
		}
	}

	step := &WorkflowStep{
		StepID:     stepID,
		Name:       name,
		StepType:   StepType(stepTypeStr),
		Parameters: parameters,
		Conditions: conditionMaps,
		Timeout:    int(stepData["timeout"].(float64)),
		RetryCount: int(stepData["retry_count"].(float64)),
		RetryDelay: int(stepData["retry_delay"].(float64)),
		Parallel:   stepData["parallel"].(bool),
		Required:   stepData["required"].(bool),
	}

	return step, nil
}

func (e *WorkflowEngine) evaluateConditions(conditions []map[string]interface{}, context map[string]interface{}) bool {
	if len(conditions) == 0 {
		return true
	}

	for _, condition := range conditions {
		if !e.evaluateCondition(condition, context) {
			return false
		}
	}

	return true
}

func (e *WorkflowEngine) evaluateCondition(condition map[string]interface{}, context map[string]interface{}) bool {
	conditionTypeStr, ok := condition["type"].(string)
	if !ok {
		return false
	}

	field, ok := condition["field"].(string)
	if !ok {
		return false
	}

	value := condition["value"]
	fieldValue := context[field]

	conditionType := ConditionType(conditionTypeStr)

	switch conditionType {
	case ConditionEquals:
		return fieldValue == value
	case ConditionNotEquals:
		return fieldValue != value
	case ConditionGreaterThan:
		if fieldFloat, ok := fieldValue.(float64); ok {
			if valueFloat, ok := value.(float64); ok {
				return fieldFloat > valueFloat
			}
		}
		return false
	case ConditionLessThan:
		if fieldFloat, ok := fieldValue.(float64); ok {
			if valueFloat, ok := value.(float64); ok {
				return fieldFloat < valueFloat
			}
		}
		return false
	case ConditionContains:
		if fieldStr, ok := fieldValue.(string); ok {
			if valueStr, ok := value.(string); ok {
				return fieldStr != "" && valueStr != ""
			}
		}
		return false
	case ConditionNotContains:
		if fieldStr, ok := fieldValue.(string); ok {
			if valueStr, ok := value.(string); ok {
				return fieldStr == "" || valueStr == ""
			}
		}
		return true
	case ConditionExists:
		return fieldValue != nil
	case ConditionNotExists:
		return fieldValue == nil
	default:
		return false
	}
}

func (e *WorkflowEngine) generateExecutionID() string {
	return fmt.Sprintf("exec_%d", time.Now().UnixNano())
}

func (e *WorkflowEngine) loadDefaultWorkflows() {
	defaultWorkflows := []map[string]interface{}{
		{
			"workflow_id":   "bim_validation_workflow",
			"name":          "BIM Validation Workflow",
			"description":   "Automated BIM validation with fix application",
			"workflow_type": "validation",
			"steps": []map[string]interface{}{
				{
					"step_id":   "validate_floorplan",
					"name":      "Validate Floorplan",
					"step_type": "validation",
					"parameters": map[string]interface{}{
						"service":          "bim_health_checker",
						"auto_apply_fixes": true,
					},
					"conditions":  []interface{}{},
					"timeout":     300.0,
					"retry_count": 2.0,
					"retry_delay": 60.0,
					"parallel":    false,
					"required":    true,
				},
				{
					"step_id":   "apply_fixes",
					"name":      "Apply Fixes",
					"step_type": "api_call",
					"parameters": map[string]interface{}{
						"endpoint": "/bim-health/apply-fixes",
						"method":   "POST",
					},
					"conditions": []interface{}{
						map[string]interface{}{
							"type":  "greater_than",
							"field": "issues_found",
							"value": 0.0,
						},
					},
					"timeout":     120.0,
					"retry_count": 1.0,
					"retry_delay": 60.0,
					"parallel":    false,
					"required":    true,
				},
				{
					"step_id":   "generate_report",
					"name":      "Generate Report",
					"step_type": "reporting",
					"parameters": map[string]interface{}{
						"report_type": "validation_summary",
						"format":      "pdf",
					},
					"conditions":  []interface{}{},
					"timeout":     180.0,
					"retry_count": 1.0,
					"retry_delay": 60.0,
					"parallel":    false,
					"required":    true,
				},
			},
			"triggers": []interface{}{
				map[string]interface{}{
					"type": "file_change",
					"path": "floorplans/*.json",
				},
			},
			"timeout":     900.0,
			"max_retries": 2.0,
		},
	}

	for _, workflowData := range defaultWorkflows {
		workflow, err := e.createWorkflowFromMap(workflowData)
		if err != nil {
			continue
		}

		e.lock.Lock()
		e.workflows[workflow.WorkflowID] = workflow
		e.lock.Unlock()

		// Save to database
		e.db.Create(workflow)
	}
}
