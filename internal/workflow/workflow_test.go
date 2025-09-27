package workflow

import (
	"context"
	"testing"
	"time"
)

func TestWorkflowManager(t *testing.T) {
	manager := NewWorkflowManager()

	// Test creating a workflow
	workflow := &Workflow{
		Name:        "Test Workflow",
		Description: "Test workflow description",
		Version:     "1.0.0",
		Status:      WorkflowStatusDraft,
		Triggers:    []*Trigger{},
		Nodes: []*WorkflowNode{
			{
				ID:       "trigger_1",
				Type:     NodeTypeTrigger,
				Name:     "Start Trigger",
				Position: Position{X: 0, Y: 0},
			},
			{
				ID:       "action_1",
				Type:     NodeTypeAction,
				Name:     "Test Action",
				Position: Position{X: 100, Y: 0},
			},
		},
		Connections: []*WorkflowConnection{
			{
				ID:       "conn_1",
				FromNode: "trigger_1",
				ToNode:   "action_1",
				FromPort: "output",
				ToPort:   "input",
			},
		},
		Config:    make(map[string]interface{}),
		CreatedBy: "test",
	}

	err := manager.CreateWorkflow(workflow)
	if err != nil {
		t.Fatalf("Failed to create workflow: %v", err)
	}

	// Test getting workflow
	retrievedWorkflow, err := manager.GetWorkflow(workflow.ID)
	if err != nil {
		t.Fatalf("Failed to get workflow: %v", err)
	}

	if retrievedWorkflow.Name != workflow.Name {
		t.Errorf("Expected workflow name %s, got %s", workflow.Name, retrievedWorkflow.Name)
	}

	// Test updating workflow
	updates := map[string]interface{}{
		"name":   "Updated Workflow",
		"status": "active",
	}

	err = manager.UpdateWorkflow(workflow.ID, updates)
	if err != nil {
		t.Fatalf("Failed to update workflow: %v", err)
	}

	// Test executing workflow
	execution, err := manager.ExecuteWorkflow(context.Background(), workflow.ID, map[string]interface{}{
		"test_data": "hello world",
	})
	if err != nil {
		t.Fatalf("Failed to execute workflow: %v", err)
	}

	if execution.WorkflowID != workflow.ID {
		t.Errorf("Expected workflow ID %s, got %s", workflow.ID, execution.WorkflowID)
	}

	// Wait for execution to complete
	time.Sleep(100 * time.Millisecond)

	// Test getting execution
	retrievedExecution, err := manager.GetExecution(execution.ID)
	if err != nil {
		t.Fatalf("Failed to get execution: %v", err)
	}

	if retrievedExecution.ID != execution.ID {
		t.Errorf("Expected execution ID %s, got %s", execution.ID, retrievedExecution.ID)
	}

	// Test listing workflows
	workflows := manager.ListWorkflows()
	if len(workflows) == 0 {
		t.Error("Expected at least one workflow")
	}

	// Test metrics
	metrics := manager.GetMetrics()
	if metrics.TotalWorkflows == 0 {
		t.Error("Expected total workflows to be greater than 0")
	}
}

func TestTriggerManager(t *testing.T) {
	manager := NewTriggerManager()

	// Test creating a trigger
	trigger := &Trigger{
		Name:       "Test Trigger",
		Type:       TriggerTypeSchedule,
		WorkflowID: "test_workflow",
		Config: map[string]interface{}{
			"schedule": "0 */5 * * * *", // Every 5 minutes
		},
		Enabled: false,
	}

	err := manager.RegisterTrigger(trigger)
	if err != nil {
		t.Fatalf("Failed to register trigger: %v", err)
	}

	// Test getting trigger
	retrievedTrigger, err := manager.GetTrigger(trigger.ID)
	if err != nil {
		t.Fatalf("Failed to get trigger: %v", err)
	}

	if retrievedTrigger.Name != trigger.Name {
		t.Errorf("Expected trigger name %s, got %s", trigger.Name, retrievedTrigger.Name)
	}

	// Test starting trigger
	err = manager.StartTrigger(context.Background(), trigger.ID)
	if err != nil {
		t.Fatalf("Failed to start trigger: %v", err)
	}

	// Test stopping trigger
	err = manager.StopTrigger(context.Background(), trigger.ID)
	if err != nil {
		t.Fatalf("Failed to stop trigger: %v", err)
	}

	// Test listing triggers
	triggers := manager.ListTriggers()
	if len(triggers) == 0 {
		t.Error("Expected at least one trigger")
	}

	// Test metrics
	metrics := manager.GetMetrics()
	if metrics.TotalTriggers == 0 {
		t.Error("Expected total triggers to be greater than 0")
	}
}

func TestActionManager(t *testing.T) {
	manager := NewActionManager()

	// Test creating an action
	action := &Action{
		Name:   "Test Action",
		Type:   ActionTypeEmail,
		Config: make(map[string]interface{}),
		Parameters: map[string]interface{}{
			"to":      "test@example.com",
			"subject": "Test Email",
			"body":    "This is a test email",
		},
		Enabled: true,
	}

	err := manager.RegisterAction(action)
	if err != nil {
		t.Fatalf("Failed to register action: %v", err)
	}

	// Test getting action
	retrievedAction, err := manager.GetAction(action.ID)
	if err != nil {
		t.Fatalf("Failed to get action: %v", err)
	}

	if retrievedAction.Name != action.Name {
		t.Errorf("Expected action name %s, got %s", action.Name, retrievedAction.Name)
	}

	// Test executing action
	input := map[string]interface{}{
		"test_data": "hello world",
	}

	output, err := manager.ExecuteAction(context.Background(), action.ID, input)
	if err != nil {
		t.Fatalf("Failed to execute action: %v", err)
	}

	if output == nil {
		t.Error("Expected output to be non-nil")
	}

	// Test listing actions
	actions := manager.ListActions()
	if len(actions) == 0 {
		t.Error("Expected at least one action")
	}

	// Test metrics
	metrics := manager.GetMetrics()
	if metrics.TotalActions == 0 {
		t.Error("Expected total actions to be greater than 0")
	}
}

func TestN8NClient(t *testing.T) {
	client := NewN8NClient()

	// Test setting credentials
	client.SetCredentials("http://localhost:5678", "test-api-key")

	// Test converting workflow to n8n format
	workflow := &Workflow{
		ID:     "test_workflow",
		Name:   "Test Workflow",
		Status: WorkflowStatusActive,
		Nodes: []*WorkflowNode{
			{
				ID:       "trigger_1",
				Type:     NodeTypeTrigger,
				Name:     "Start Trigger",
				Position: Position{X: 0, Y: 0},
			},
		},
		Connections: []*WorkflowConnection{},
		Config:      make(map[string]interface{}),
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	n8nWorkflow := client.ConvertToN8NWorkflow(workflow)
	if n8nWorkflow.ID != workflow.ID {
		t.Errorf("Expected n8n workflow ID %s, got %s", workflow.ID, n8nWorkflow.ID)
	}

	if n8nWorkflow.Name != workflow.Name {
		t.Errorf("Expected n8n workflow name %s, got %s", workflow.Name, n8nWorkflow.Name)
	}

	// Test converting n8n workflow to ArxOS format
	convertedWorkflow := client.ConvertFromN8NWorkflow(n8nWorkflow)
	if convertedWorkflow.ID != workflow.ID {
		t.Errorf("Expected converted workflow ID %s, got %s", workflow.ID, convertedWorkflow.ID)
	}

	if convertedWorkflow.Name != workflow.Name {
		t.Errorf("Expected converted workflow name %s, got %s", workflow.Name, convertedWorkflow.Name)
	}
}

func TestWorkflowNodeExecution(t *testing.T) {
	manager := NewWorkflowManager()

	// Test different node types
	nodeTypes := []NodeType{
		NodeTypeTrigger,
		NodeTypeAction,
		NodeTypeCondition,
		NodeTypeTransform,
		NodeTypeDelay,
		NodeTypeWebhook,
		NodeTypeEmail,
		NodeTypeDatabase,
		NodeTypeAPI,
		NodeTypeCustom,
	}

	for _, nodeType := range nodeTypes {
		node := &WorkflowNode{
			ID:          "test_node",
			Type:        nodeType,
			Name:        "Test Node",
			Position:    Position{X: 0, Y: 0},
			Config:      make(map[string]interface{}),
			Parameters:  make(map[string]interface{}),
			Credentials: make(map[string]interface{}),
		}

		// Test node execution
		execution := &WorkflowExecution{
			ID:          "test_execution",
			WorkflowID:  "test_workflow",
			Status:      ExecutionStatusRunning,
			TriggerData: make(map[string]interface{}),
			Context:     make(map[string]interface{}),
			Results:     make([]*NodeExecution, 0),
			StartTime:   time.Now(),
		}

		result := manager.executeNode(context.Background(), node, map[string]interface{}{}, execution)
		if result == nil {
			t.Errorf("Expected node execution result for type %s", nodeType)
		}

		if result.NodeID != node.ID {
			t.Errorf("Expected node ID %s, got %s", node.ID, result.NodeID)
		}
	}
}

func TestWorkflowStatus(t *testing.T) {
	// Test workflow status values
	statuses := []WorkflowStatus{
		WorkflowStatusDraft,
		WorkflowStatusActive,
		WorkflowStatusInactive,
		WorkflowStatusError,
		WorkflowStatusPaused,
	}

	for _, status := range statuses {
		if status == "" {
			t.Error("Expected status to be non-empty")
		}
	}
}

func TestExecutionStatus(t *testing.T) {
	// Test execution status values
	statuses := []ExecutionStatus{
		ExecutionStatusPending,
		ExecutionStatusRunning,
		ExecutionStatusCompleted,
		ExecutionStatusFailed,
		ExecutionStatusCancelled,
		ExecutionStatusRetrying,
	}

	for _, status := range statuses {
		if status == "" {
			t.Error("Expected status to be non-empty")
		}
	}
}

func TestTriggerType(t *testing.T) {
	// Test trigger type values
	types := []TriggerType{
		TriggerTypeSchedule,
		TriggerTypeWebhook,
		TriggerTypeEvent,
		TriggerTypeManual,
		TriggerTypeFile,
		TriggerTypeEmail,
		TriggerTypeDatabase,
		TriggerTypeMQTT,
		TriggerTypeModbus,
		TriggerTypeCustom,
	}

	for _, triggerType := range types {
		if triggerType == "" {
			t.Error("Expected trigger type to be non-empty")
		}
	}
}

func TestActionType(t *testing.T) {
	// Test action type values
	types := []ActionType{
		ActionTypeEmail,
		ActionTypeSMS,
		ActionTypeWebhook,
		ActionTypeDatabase,
		ActionTypeAPI,
		ActionTypeFile,
		ActionTypeTransform,
		ActionTypeCondition,
		ActionTypeDelay,
		ActionTypeMQTT,
		ActionTypeModbus,
		ActionTypeCustom,
	}

	for _, actionType := range types {
		if actionType == "" {
			t.Error("Expected action type to be non-empty")
		}
	}
}

func TestNodeType(t *testing.T) {
	// Test node type values
	types := []NodeType{
		NodeTypeTrigger,
		NodeTypeAction,
		NodeTypeCondition,
		NodeTypeTransform,
		NodeTypeDelay,
		NodeTypeWebhook,
		NodeTypeEmail,
		NodeTypeSMS,
		NodeTypeDatabase,
		NodeTypeAPI,
		NodeTypeCustom,
	}

	for _, nodeType := range types {
		if nodeType == "" {
			t.Error("Expected node type to be non-empty")
		}
	}
}

func TestWorkflowValidation(t *testing.T) {
	manager := NewWorkflowManager()

	// Test invalid workflow (no triggers)
	invalidWorkflow := &Workflow{
		Name:        "Invalid Workflow",
		Description: "Workflow without triggers",
		Version:     "1.0.0",
		Status:      WorkflowStatusDraft,
		Triggers:    []*Trigger{}, // Empty triggers
		Nodes: []*WorkflowNode{
			{
				ID:       "action_1",
				Type:     NodeTypeAction,
				Name:     "Test Action",
				Position: Position{X: 0, Y: 0},
			},
		},
		Connections: []*WorkflowConnection{},
		Config:      make(map[string]interface{}),
		CreatedBy:   "test",
	}

	err := manager.CreateWorkflow(invalidWorkflow)
	if err == nil {
		t.Error("Expected error for workflow without triggers")
	}

	// Test invalid workflow (no nodes)
	invalidWorkflow2 := &Workflow{
		Name:        "Invalid Workflow 2",
		Description: "Workflow without nodes",
		Version:     "1.0.0",
		Status:      WorkflowStatusDraft,
		Triggers: []*Trigger{
			{
				ID:         "trigger_1",
				Type:       TriggerTypeManual,
				Name:       "Test Trigger",
				WorkflowID: "test_workflow",
				Config:     make(map[string]interface{}),
				Enabled:    false,
			},
		},
		Nodes:       []*WorkflowNode{}, // Empty nodes
		Connections: []*WorkflowConnection{},
		Config:      make(map[string]interface{}),
		CreatedBy:   "test",
	}

	err = manager.CreateWorkflow(invalidWorkflow2)
	if err == nil {
		t.Error("Expected error for workflow without nodes")
	}
}

func TestActionHandlers(t *testing.T) {
	// Test email action handler
	emailHandler := NewEmailActionHandler()
	if emailHandler.GetName() == "" {
		t.Error("Expected email handler name to be non-empty")
	}

	capabilities := emailHandler.GetCapabilities()
	if len(capabilities) == 0 {
		t.Error("Expected email handler capabilities to be non-empty")
	}

	// Test SMS action handler
	smsHandler := NewSMSActionHandler()
	if smsHandler.GetName() == "" {
		t.Error("Expected SMS handler name to be non-empty")
	}

	// Test webhook action handler
	webhookHandler := NewWebhookActionHandler()
	if webhookHandler.GetName() == "" {
		t.Error("Expected webhook handler name to be non-empty")
	}

	// Test database action handler
	dbHandler := NewDatabaseActionHandler()
	if dbHandler.GetName() == "" {
		t.Error("Expected database handler name to be non-empty")
	}

	// Test API action handler
	apiHandler := NewAPIActionHandler()
	if apiHandler.GetName() == "" {
		t.Error("Expected API handler name to be non-empty")
	}

	// Test file action handler
	fileHandler := NewFileActionHandler()
	if fileHandler.GetName() == "" {
		t.Error("Expected file handler name to be non-empty")
	}

	// Test transform action handler
	transformHandler := NewTransformActionHandler()
	if transformHandler.GetName() == "" {
		t.Error("Expected transform handler name to be non-empty")
	}

	// Test condition action handler
	conditionHandler := NewConditionActionHandler()
	if conditionHandler.GetName() == "" {
		t.Error("Expected condition handler name to be non-empty")
	}

	// Test delay action handler
	delayHandler := NewDelayActionHandler()
	if delayHandler.GetName() == "" {
		t.Error("Expected delay handler name to be non-empty")
	}

	// Test MQTT action handler
	mqttHandler := NewMQTTActionHandler()
	if mqttHandler.GetName() == "" {
		t.Error("Expected MQTT handler name to be non-empty")
	}

	// Test Modbus action handler
	modbusHandler := NewModbusActionHandler()
	if modbusHandler.GetName() == "" {
		t.Error("Expected Modbus handler name to be non-empty")
	}
}

func TestTriggerHandlers(t *testing.T) {
	// Test schedule trigger handler
	scheduleHandler := NewScheduleTriggerHandler()
	if scheduleHandler.GetName() == "" {
		t.Error("Expected schedule handler name to be non-empty")
	}

	// Test webhook trigger handler
	webhookHandler := NewWebhookTriggerHandler()
	if webhookHandler.GetName() == "" {
		t.Error("Expected webhook handler name to be non-empty")
	}

	// Test event trigger handler
	eventHandler := NewEventTriggerHandler()
	if eventHandler.GetName() == "" {
		t.Error("Expected event handler name to be non-empty")
	}

	// Test manual trigger handler
	manualHandler := NewManualTriggerHandler()
	if manualHandler.GetName() == "" {
		t.Error("Expected manual handler name to be non-empty")
	}

	// Test file trigger handler
	fileHandler := NewFileTriggerHandler()
	if fileHandler.GetName() == "" {
		t.Error("Expected file handler name to be non-empty")
	}

	// Test email trigger handler
	emailHandler := NewEmailTriggerHandler()
	if emailHandler.GetName() == "" {
		t.Error("Expected email handler name to be non-empty")
	}

	// Test database trigger handler
	dbHandler := NewDatabaseTriggerHandler()
	if dbHandler.GetName() == "" {
		t.Error("Expected database handler name to be non-empty")
	}

	// Test MQTT trigger handler
	mqttHandler := NewMQTTTriggerHandler()
	if mqttHandler.GetName() == "" {
		t.Error("Expected MQTT handler name to be non-empty")
	}

	// Test Modbus trigger handler
	modbusHandler := NewModbusTriggerHandler()
	if modbusHandler.GetName() == "" {
		t.Error("Expected Modbus handler name to be non-empty")
	}
}

func TestWorkflowExecution(t *testing.T) {
	manager := NewWorkflowManager()

	// Create a simple workflow
	workflow := &Workflow{
		Name:        "Test Execution Workflow",
		Description: "Workflow for testing execution",
		Version:     "1.0.0",
		Status:      WorkflowStatusActive,
		Triggers: []*Trigger{
			{
				ID:         "trigger_1",
				Type:       TriggerTypeManual,
				Name:       "Manual Trigger",
				WorkflowID: "test_workflow",
				Config:     make(map[string]interface{}),
				Enabled:    true,
			},
		},
		Nodes: []*WorkflowNode{
			{
				ID:       "trigger_1",
				Type:     NodeTypeTrigger,
				Name:     "Start Trigger",
				Position: Position{X: 0, Y: 0},
			},
			{
				ID:       "action_1",
				Type:     NodeTypeAction,
				Name:     "Test Action",
				Position: Position{X: 100, Y: 0},
			},
		},
		Connections: []*WorkflowConnection{
			{
				ID:       "conn_1",
				FromNode: "trigger_1",
				ToNode:   "action_1",
				FromPort: "output",
				ToPort:   "input",
			},
		},
		Config:    make(map[string]interface{}),
		CreatedBy: "test",
	}

	err := manager.CreateWorkflow(workflow)
	if err != nil {
		t.Fatalf("Failed to create workflow: %v", err)
	}

	// Execute workflow
	execution, err := manager.ExecuteWorkflow(context.Background(), workflow.ID, map[string]interface{}{
		"test_input": "hello world",
	})
	if err != nil {
		t.Fatalf("Failed to execute workflow: %v", err)
	}

	// Wait for execution to complete
	time.Sleep(200 * time.Millisecond)

	// Get execution status
	finalExecution, err := manager.GetExecution(execution.ID)
	if err != nil {
		t.Fatalf("Failed to get execution: %v", err)
	}

	// Check execution status
	if finalExecution.Status != ExecutionStatusCompleted && finalExecution.Status != ExecutionStatusFailed {
		t.Errorf("Expected execution to be completed or failed, got %s", finalExecution.Status)
	}

	// Check that we have results
	if len(finalExecution.Results) == 0 {
		t.Error("Expected execution to have results")
	}
}

func TestWorkflowMetrics(t *testing.T) {
	manager := NewWorkflowManager()

	// Create and execute a workflow to generate metrics
	workflow := &Workflow{
		Name:        "Metrics Test Workflow",
		Description: "Workflow for testing metrics",
		Version:     "1.0.0",
		Status:      WorkflowStatusActive,
		Triggers:    []*Trigger{},
		Nodes: []*WorkflowNode{
			{
				ID:       "trigger_1",
				Type:     NodeTypeTrigger,
				Name:     "Start Trigger",
				Position: Position{X: 0, Y: 0},
			},
		},
		Connections: []*WorkflowConnection{},
		Config:      make(map[string]interface{}),
		CreatedBy:   "test",
	}

	err := manager.CreateWorkflow(workflow)
	if err != nil {
		t.Fatalf("Failed to create workflow: %v", err)
	}

	// Execute workflow
	_, err = manager.ExecuteWorkflow(context.Background(), workflow.ID, map[string]interface{}{})
	if err != nil {
		t.Fatalf("Failed to execute workflow: %v", err)
	}

	// Wait for execution to complete
	time.Sleep(100 * time.Millisecond)

	// Check metrics
	metrics := manager.GetMetrics()
	if metrics.TotalWorkflows == 0 {
		t.Error("Expected total workflows to be greater than 0")
	}

	if metrics.TotalExecutions == 0 {
		t.Error("Expected total executions to be greater than 0")
	}
}
