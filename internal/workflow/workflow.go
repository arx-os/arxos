package workflow

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// WorkflowManager manages workflow automation and n8n integration
type WorkflowManager struct {
	workflows  map[string]*Workflow
	executions map[string]*WorkflowExecution
	n8nClient  *N8NClient
	triggers   map[string]*Trigger
	actions    map[string]*Action
	metrics    *WorkflowMetrics
}

// Workflow represents a workflow definition
type Workflow struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Version     string                 `json:"version"`
	Status      WorkflowStatus         `json:"status"`
	Triggers    []*Trigger             `json:"triggers"`
	Nodes       []*WorkflowNode        `json:"nodes"`
	Connections []*WorkflowConnection  `json:"connections"`
	Config      map[string]interface{} `json:"config"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	CreatedBy   string                 `json:"created_by"`
}

// WorkflowStatus represents the status of a workflow
type WorkflowStatus string

const (
	WorkflowStatusDraft    = WorkflowStatus("draft")
	WorkflowStatusActive   = WorkflowStatus("active")
	WorkflowStatusInactive = WorkflowStatus("inactive")
	WorkflowStatusError    = WorkflowStatus("error")
	WorkflowStatusPaused   = WorkflowStatus("paused")
)

// WorkflowNode represents a node in a workflow
type WorkflowNode struct {
	ID          string                 `json:"id"`
	Type        NodeType               `json:"type"`
	Name        string                 `json:"name"`
	Position    Position               `json:"position"`
	Config      map[string]interface{} `json:"config"`
	Parameters  map[string]interface{} `json:"parameters"`
	Credentials map[string]interface{} `json:"credentials"`
}

// NodeType represents the type of workflow node
type NodeType string

const (
	NodeTypeTrigger   = NodeType("trigger")
	NodeTypeAction    = NodeType("action")
	NodeTypeCondition = NodeType("condition")
	NodeTypeTransform = NodeType("transform")
	NodeTypeDelay     = NodeType("delay")
	NodeTypeWebhook   = NodeType("webhook")
	NodeTypeEmail     = NodeType("email")
	NodeTypeSMS       = NodeType("sms")
	NodeTypeDatabase  = NodeType("database")
	NodeTypeAPI       = NodeType("api")
	NodeTypeCustom    = NodeType("custom")
)

// Position represents the position of a node in the workflow canvas
type Position struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// WorkflowConnection represents a connection between workflow nodes
type WorkflowConnection struct {
	ID       string `json:"id"`
	FromNode string `json:"from_node"`
	ToNode   string `json:"to_node"`
	FromPort string `json:"from_port"`
	ToPort   string `json:"to_port"`
}

// WorkflowExecution represents a workflow execution instance
type WorkflowExecution struct {
	ID          string                 `json:"id"`
	WorkflowID  string                 `json:"workflow_id"`
	Status      ExecutionStatus        `json:"status"`
	TriggerData map[string]interface{} `json:"trigger_data"`
	Context     map[string]interface{} `json:"context"`
	Results     []*NodeExecution       `json:"results"`
	StartTime   time.Time              `json:"start_time"`
	EndTime     *time.Time             `json:"end_time,omitempty"`
	Duration    time.Duration          `json:"duration"`
	Error       string                 `json:"error,omitempty"`
	RetryCount  int                    `json:"retry_count"`
	MaxRetries  int                    `json:"max_retries"`
}

// ExecutionStatus represents the status of a workflow execution
type ExecutionStatus string

const (
	ExecutionStatusPending   = ExecutionStatus("pending")
	ExecutionStatusRunning   = ExecutionStatus("running")
	ExecutionStatusCompleted = ExecutionStatus("completed")
	ExecutionStatusFailed    = ExecutionStatus("failed")
	ExecutionStatusCancelled = ExecutionStatus("cancelled")
	ExecutionStatusRetrying  = ExecutionStatus("retrying")
)

// NodeExecution represents the execution of a single node
type NodeExecution struct {
	NodeID     string                 `json:"node_id"`
	Status     ExecutionStatus        `json:"status"`
	Input      map[string]interface{} `json:"input"`
	Output     map[string]interface{} `json:"output"`
	Error      string                 `json:"error,omitempty"`
	StartTime  time.Time              `json:"start_time"`
	EndTime    *time.Time             `json:"end_time,omitempty"`
	Duration   time.Duration          `json:"duration"`
	RetryCount int                    `json:"retry_count"`
}

// Trigger represents a workflow trigger
type Trigger struct {
	ID          string                 `json:"id"`
	Type        TriggerType            `json:"type"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Config      map[string]interface{} `json:"config"`
	Enabled     bool                   `json:"enabled"`
	WorkflowID  string                 `json:"workflow_id"`
}

// TriggerType represents the type of trigger
type TriggerType string

const (
	TriggerTypeSchedule = TriggerType("schedule")
	TriggerTypeWebhook  = TriggerType("webhook")
	TriggerTypeEvent    = TriggerType("event")
	TriggerTypeManual   = TriggerType("manual")
	TriggerTypeFile     = TriggerType("file")
	TriggerTypeEmail    = TriggerType("email")
	TriggerTypeDatabase = TriggerType("database")
	TriggerTypeMQTT     = TriggerType("mqtt")
	TriggerTypeModbus   = TriggerType("modbus")
	TriggerTypeCustom   = TriggerType("custom")
)

// Action represents a workflow action
type Action struct {
	ID          string                 `json:"id"`
	Type        ActionType             `json:"type"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Config      map[string]interface{} `json:"config"`
	Parameters  map[string]interface{} `json:"parameters"`
	Enabled     bool                   `json:"enabled"`
}

// ActionType represents the type of action
type ActionType string

const (
	ActionTypeEmail     = ActionType("email")
	ActionTypeSMS       = ActionType("sms")
	ActionTypeWebhook   = ActionType("webhook")
	ActionTypeDatabase  = ActionType("database")
	ActionTypeAPI       = ActionType("api")
	ActionTypeFile      = ActionType("file")
	ActionTypeTransform = ActionType("transform")
	ActionTypeCondition = ActionType("condition")
	ActionTypeDelay     = ActionType("delay")
	ActionTypeMQTT      = ActionType("mqtt")
	ActionTypeModbus    = ActionType("modbus")
	ActionTypeCustom    = ActionType("custom")
)

// WorkflowMetrics tracks workflow performance metrics
type WorkflowMetrics struct {
	TotalWorkflows       int64         `json:"total_workflows"`
	ActiveWorkflows      int64         `json:"active_workflows"`
	TotalExecutions      int64         `json:"total_executions"`
	SuccessfulExecutions int64         `json:"successful_executions"`
	FailedExecutions     int64         `json:"failed_executions"`
	AverageDuration      time.Duration `json:"average_duration"`
	TotalTriggers        int64         `json:"total_triggers"`
	ActiveTriggers       int64         `json:"active_triggers"`
}

// NewWorkflowManager creates a new workflow manager
func NewWorkflowManager() *WorkflowManager {
	return &WorkflowManager{
		workflows:  make(map[string]*Workflow),
		executions: make(map[string]*WorkflowExecution),
		n8nClient:  NewN8NClient(),
		triggers:   make(map[string]*Trigger),
		actions:    make(map[string]*Action),
		metrics:    &WorkflowMetrics{},
	}
}

// CreateWorkflow creates a new workflow
func (wm *WorkflowManager) CreateWorkflow(workflow *Workflow) error {
	if workflow == nil {
		return fmt.Errorf("workflow cannot be nil")
	}

	if workflow.ID == "" {
		workflow.ID = fmt.Sprintf("wf_%d", time.Now().UnixNano())
	}

	if workflow.Name == "" {
		return fmt.Errorf("workflow name cannot be empty")
	}

	// Set timestamps
	now := time.Now()
	workflow.CreatedAt = now
	workflow.UpdatedAt = now

	// Set default status
	if workflow.Status == "" {
		workflow.Status = WorkflowStatusDraft
	}

	// Validate workflow
	if err := wm.validateWorkflow(workflow); err != nil {
		return fmt.Errorf("workflow validation failed: %w", err)
	}

	// Store workflow
	wm.workflows[workflow.ID] = workflow
	wm.metrics.TotalWorkflows++

	logger.Info("Workflow created: %s (%s)", workflow.ID, workflow.Name)
	return nil
}

// GetWorkflow retrieves a workflow by ID
func (wm *WorkflowManager) GetWorkflow(workflowID string) (*Workflow, error) {
	workflow, exists := wm.workflows[workflowID]
	if !exists {
		return nil, fmt.Errorf("workflow %s not found", workflowID)
	}
	return workflow, nil
}

// UpdateWorkflow updates an existing workflow
func (wm *WorkflowManager) UpdateWorkflow(workflowID string, updates map[string]interface{}) error {
	workflow, exists := wm.workflows[workflowID]
	if !exists {
		return fmt.Errorf("workflow %s not found", workflowID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "name":
			if name, ok := value.(string); ok {
				workflow.Name = name
			}
		case "description":
			if desc, ok := value.(string); ok {
				workflow.Description = desc
			}
		case "status":
			if status, ok := value.(string); ok {
				workflow.Status = WorkflowStatus(status)
			}
		case "config":
			if config, ok := value.(map[string]interface{}); ok {
				workflow.Config = config
			}
		case "nodes":
			if nodes, ok := value.([]*WorkflowNode); ok {
				workflow.Nodes = nodes
			}
		case "connections":
			if connections, ok := value.([]*WorkflowConnection); ok {
				workflow.Connections = connections
			}
		}
	}

	workflow.UpdatedAt = time.Now()

	// Validate updated workflow
	if err := wm.validateWorkflow(workflow); err != nil {
		return fmt.Errorf("workflow validation failed: %w", err)
	}

	logger.Info("Workflow updated: %s", workflowID)
	return nil
}

// DeleteWorkflow deletes a workflow
func (wm *WorkflowManager) DeleteWorkflow(workflowID string) error {
	workflow, exists := wm.workflows[workflowID]
	if !exists {
		return fmt.Errorf("workflow %s not found", workflowID)
	}

	// Deactivate triggers
	for _, trigger := range workflow.Triggers {
		trigger.Enabled = false
	}

	// Delete workflow
	delete(wm.workflows, workflowID)
	wm.metrics.TotalWorkflows--

	logger.Info("Workflow deleted: %s (%s)", workflowID, workflow.Name)
	return nil
}

// ListWorkflows returns all workflows
func (wm *WorkflowManager) ListWorkflows() []*Workflow {
	workflows := make([]*Workflow, 0, len(wm.workflows))
	for _, workflow := range wm.workflows {
		workflows = append(workflows, workflow)
	}
	return workflows
}

// ExecuteWorkflow executes a workflow
func (wm *WorkflowManager) ExecuteWorkflow(ctx context.Context, workflowID string, triggerData map[string]interface{}) (*WorkflowExecution, error) {
	workflow, exists := wm.workflows[workflowID]
	if !exists {
		return nil, fmt.Errorf("workflow %s not found", workflowID)
	}

	if workflow.Status != WorkflowStatusActive {
		return nil, fmt.Errorf("workflow %s is not active", workflowID)
	}

	// Create execution
	execution := &WorkflowExecution{
		ID:          fmt.Sprintf("exec_%d", time.Now().UnixNano()),
		WorkflowID:  workflowID,
		Status:      ExecutionStatusPending,
		TriggerData: triggerData,
		Context:     make(map[string]interface{}),
		Results:     make([]*NodeExecution, 0),
		StartTime:   time.Now(),
		MaxRetries:  3,
	}

	// Store execution
	wm.executions[execution.ID] = execution

	// Execute workflow asynchronously
	go wm.executeWorkflowAsync(ctx, execution, workflow)

	wm.metrics.TotalExecutions++
	logger.Info("Workflow execution started: %s (workflow: %s)", execution.ID, workflowID)
	return execution, nil
}

// GetExecution retrieves a workflow execution by ID
func (wm *WorkflowManager) GetExecution(executionID string) (*WorkflowExecution, error) {
	execution, exists := wm.executions[executionID]
	if !exists {
		return nil, fmt.Errorf("execution %s not found", executionID)
	}
	return execution, nil
}

// CancelExecution cancels a running workflow execution
func (wm *WorkflowManager) CancelExecution(executionID string) error {
	execution, exists := wm.executions[executionID]
	if !exists {
		return fmt.Errorf("execution %s not found", executionID)
	}

	if execution.Status == ExecutionStatusRunning {
		execution.Status = ExecutionStatusCancelled
		now := time.Now()
		execution.EndTime = &now
		execution.Duration = now.Sub(execution.StartTime)
		logger.Info("Workflow execution cancelled: %s", executionID)
	}

	return nil
}

// GetMetrics returns workflow metrics
func (wm *WorkflowManager) GetMetrics() *WorkflowMetrics {
	// Update active counts
	wm.metrics.ActiveWorkflows = 0
	wm.metrics.ActiveTriggers = 0

	for _, workflow := range wm.workflows {
		if workflow.Status == WorkflowStatusActive {
			wm.metrics.ActiveWorkflows++
		}
		for _, trigger := range workflow.Triggers {
			if trigger.Enabled {
				wm.metrics.ActiveTriggers++
			}
		}
	}

	return wm.metrics
}

// validateWorkflow validates a workflow definition
func (wm *WorkflowManager) validateWorkflow(workflow *Workflow) error {
	// Check for at least one trigger
	if len(workflow.Triggers) == 0 {
		return fmt.Errorf("workflow must have at least one trigger")
	}

	// Check for at least one node
	if len(workflow.Nodes) == 0 {
		return fmt.Errorf("workflow must have at least one node")
	}

	// Validate nodes
	for _, node := range workflow.Nodes {
		if err := wm.validateNode(node); err != nil {
			return fmt.Errorf("invalid node %s: %w", node.ID, err)
		}
	}

	// Validate connections
	for _, connection := range workflow.Connections {
		if err := wm.validateConnection(connection, workflow.Nodes); err != nil {
			return fmt.Errorf("invalid connection %s: %w", connection.ID, err)
		}
	}

	return nil
}

// validateNode validates a workflow node
func (wm *WorkflowManager) validateNode(node *WorkflowNode) error {
	if node.ID == "" {
		return fmt.Errorf("node ID cannot be empty")
	}

	if node.Name == "" {
		return fmt.Errorf("node name cannot be empty")
	}

	if node.Type == "" {
		return fmt.Errorf("node type cannot be empty")
	}

	return nil
}

// validateConnection validates a workflow connection
func (wm *WorkflowManager) validateConnection(connection *WorkflowConnection, nodes []*WorkflowNode) error {
	if connection.ID == "" {
		return fmt.Errorf("connection ID cannot be empty")
	}

	// Check if from node exists
	fromNodeExists := false
	for _, node := range nodes {
		if node.ID == connection.FromNode {
			fromNodeExists = true
			break
		}
	}
	if !fromNodeExists {
		return fmt.Errorf("from node %s not found", connection.FromNode)
	}

	// Check if to node exists
	toNodeExists := false
	for _, node := range nodes {
		if node.ID == connection.ToNode {
			toNodeExists = true
			break
		}
	}
	if !toNodeExists {
		return fmt.Errorf("to node %s not found", connection.ToNode)
	}

	return nil
}

// executeWorkflowAsync executes a workflow asynchronously
func (wm *WorkflowManager) executeWorkflowAsync(ctx context.Context, execution *WorkflowExecution, workflow *Workflow) {
	execution.Status = ExecutionStatusRunning

	// Find trigger node
	var triggerNode *WorkflowNode
	for _, node := range workflow.Nodes {
		if node.Type == NodeTypeTrigger {
			triggerNode = node
			break
		}
	}

	if triggerNode == nil {
		execution.Status = ExecutionStatusFailed
		execution.Error = "no trigger node found"
		now := time.Now()
		execution.EndTime = &now
		execution.Duration = now.Sub(execution.StartTime)
		wm.metrics.FailedExecutions++
		return
	}

	// Execute trigger node
	triggerResult := wm.executeNode(ctx, triggerNode, execution.TriggerData, execution)
	execution.Results = append(execution.Results, triggerResult)

	// Execute subsequent nodes
	if triggerResult.Status == ExecutionStatusCompleted {
		wm.executeSubsequentNodes(ctx, workflow, execution, triggerNode.ID)
	}

	// Complete execution
	now := time.Now()
	execution.EndTime = &now
	execution.Duration = now.Sub(execution.StartTime)

	if execution.Status == ExecutionStatusRunning {
		execution.Status = ExecutionStatusCompleted
		wm.metrics.SuccessfulExecutions++
	} else {
		wm.metrics.FailedExecutions++
	}

	logger.Info("Workflow execution completed: %s (status: %s, duration: %s)",
		execution.ID, execution.Status, execution.Duration)
}

// executeSubsequentNodes executes nodes connected to the given node
func (wm *WorkflowManager) executeSubsequentNodes(ctx context.Context, workflow *Workflow, execution *WorkflowExecution, nodeID string) {
	// Find connections from this node
	for _, connection := range workflow.Connections {
		if connection.FromNode == nodeID {
			// Find target node
			var targetNode *WorkflowNode
			for _, node := range workflow.Nodes {
				if node.ID == connection.ToNode {
					targetNode = node
					break
				}
			}

			if targetNode != nil {
				// Execute target node
				result := wm.executeNode(ctx, targetNode, execution.Context, execution)
				execution.Results = append(execution.Results, result)

				// Continue with subsequent nodes if successful
				if result.Status == ExecutionStatusCompleted {
					wm.executeSubsequentNodes(ctx, workflow, execution, targetNode.ID)
				}
			}
		}
	}
}

// executeNode executes a single workflow node
func (wm *WorkflowManager) executeNode(ctx context.Context, node *WorkflowNode, input map[string]interface{}, execution *WorkflowExecution) *NodeExecution {
	nodeExecution := &NodeExecution{
		NodeID:     node.ID,
		Status:     ExecutionStatusRunning,
		Input:      input,
		StartTime:  time.Now(),
		RetryCount: 0,
	}

	// Execute node based on type
	switch node.Type {
	case NodeTypeTrigger:
		wm.executeTriggerNode(ctx, node, nodeExecution)
	case NodeTypeAction:
		wm.executeActionNode(ctx, node, nodeExecution)
	case NodeTypeCondition:
		wm.executeConditionNode(ctx, node, nodeExecution)
	case NodeTypeTransform:
		wm.executeTransformNode(ctx, node, nodeExecution)
	case NodeTypeDelay:
		wm.executeDelayNode(ctx, node, nodeExecution)
	case NodeTypeWebhook:
		wm.executeWebhookNode(ctx, node, nodeExecution)
	case NodeTypeEmail:
		wm.executeEmailNode(ctx, node, nodeExecution)
	case NodeTypeDatabase:
		wm.executeDatabaseNode(ctx, node, nodeExecution)
	case NodeTypeAPI:
		wm.executeAPINode(ctx, node, nodeExecution)
	case NodeTypeCustom:
		wm.executeCustomNode(ctx, node, nodeExecution)
	default:
		nodeExecution.Status = ExecutionStatusFailed
		nodeExecution.Error = fmt.Sprintf("unknown node type: %s", node.Type)
	}

	// Complete node execution
	now := time.Now()
	nodeExecution.EndTime = &now
	nodeExecution.Duration = now.Sub(nodeExecution.StartTime)

	// Update execution context
	if nodeExecution.Status == ExecutionStatusCompleted {
		for key, value := range nodeExecution.Output {
			execution.Context[key] = value
		}
	} else {
		execution.Status = ExecutionStatusFailed
		execution.Error = nodeExecution.Error
	}

	return nodeExecution
}

// Node execution methods (simplified implementations)
func (wm *WorkflowManager) executeTriggerNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	execution.Status = ExecutionStatusCompleted
	execution.Output = execution.Input
}

func (wm *WorkflowManager) executeActionNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Simulate action execution
	time.Sleep(100 * time.Millisecond)
	execution.Status = ExecutionStatusCompleted
	execution.Output = map[string]interface{}{
		"action": "completed",
		"node":   node.Name,
	}
}

func (wm *WorkflowManager) executeConditionNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Simulate condition evaluation
	execution.Status = ExecutionStatusCompleted
	execution.Output = map[string]interface{}{
		"condition": "true",
		"result":    true,
	}
}

func (wm *WorkflowManager) executeTransformNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Simulate data transformation
	execution.Status = ExecutionStatusCompleted
	execution.Output = map[string]interface{}{
		"transformed": true,
		"data":        execution.Input,
	}
}

func (wm *WorkflowManager) executeDelayNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Get delay duration from node config
	delay := 1 * time.Second
	if delayConfig, ok := node.Config["delay"].(float64); ok {
		delay = time.Duration(delayConfig) * time.Second
	}

	time.Sleep(delay)
	execution.Status = ExecutionStatusCompleted
	execution.Output = execution.Input
}

func (wm *WorkflowManager) executeWebhookNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Simulate webhook execution
	execution.Status = ExecutionStatusCompleted
	execution.Output = map[string]interface{}{
		"webhook": "sent",
		"url":     node.Config["url"],
	}
}

func (wm *WorkflowManager) executeEmailNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Simulate email sending
	execution.Status = ExecutionStatusCompleted
	execution.Output = map[string]interface{}{
		"email": "sent",
		"to":    node.Config["to"],
	}
}

func (wm *WorkflowManager) executeDatabaseNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Simulate database operation
	execution.Status = ExecutionStatusCompleted
	execution.Output = map[string]interface{}{
		"database": "operation_completed",
		"query":    node.Config["query"],
	}
}

func (wm *WorkflowManager) executeAPINode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Simulate API call
	execution.Status = ExecutionStatusCompleted
	execution.Output = map[string]interface{}{
		"api": "call_completed",
		"url": node.Config["url"],
	}
}

func (wm *WorkflowManager) executeCustomNode(ctx context.Context, node *WorkflowNode, execution *NodeExecution) {
	// Simulate custom node execution
	execution.Status = ExecutionStatusCompleted
	execution.Output = map[string]interface{}{
		"custom": "executed",
		"node":   node.Name,
	}
}
