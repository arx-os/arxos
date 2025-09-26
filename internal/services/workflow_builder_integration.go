package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/ecosystem"
)

// WorkflowBuilderIntegration provides integration between the visual workflow builder and n8n
type WorkflowBuilderIntegration struct {
	n8nService      *N8NService
	workflowService *WorkflowService
	executionEngine *WorkflowExecutionEngine
}

// NewWorkflowBuilderIntegration creates a new workflow builder integration
func NewWorkflowBuilderIntegration(n8nService *N8NService, workflowService *WorkflowService, executionEngine *WorkflowExecutionEngine) *WorkflowBuilderIntegration {
	return &WorkflowBuilderIntegration{
		n8nService:      n8nService,
		workflowService: workflowService,
		executionEngine: executionEngine,
	}
}

// WorkflowBuilderNode represents a node in the workflow builder
type WorkflowBuilderNode struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	Name       string                 `json:"name"`
	Position   Position               `json:"position"`
	Parameters map[string]interface{} `json:"parameters"`
	Data       map[string]interface{} `json:"data"`
}

// Position represents a 2D position
type Position struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// WorkflowBuilderConnection represents a connection between nodes
type WorkflowBuilderConnection struct {
	ID           string `json:"id"`
	Source       string `json:"source"`
	Target       string `json:"target"`
	SourceHandle string `json:"sourceHandle,omitempty"`
	TargetHandle string `json:"targetHandle,omitempty"`
}

// WorkflowBuilderDefinition represents the complete workflow definition from the builder
type WorkflowBuilderDefinition struct {
	Nodes       []WorkflowBuilderNode       `json:"nodes"`
	Connections []WorkflowBuilderConnection `json:"connections"`
	Settings    map[string]interface{}      `json:"settings,omitempty"`
}

// WorkflowTemplate represents a pre-built workflow template
type WorkflowTemplate struct {
	ID          string                    `json:"id"`
	Name        string                    `json:"name"`
	Description string                    `json:"description"`
	Category    string                    `json:"category"`
	Definition  WorkflowBuilderDefinition `json:"definition"`
	Tags        []string                  `json:"tags"`
	CreatedAt   time.Time                 `json:"created_at"`
	UpdatedAt   time.Time                 `json:"updated_at"`
}

// ValidateWorkflowDefinition validates a workflow definition from the builder
func (wbi *WorkflowBuilderIntegration) ValidateWorkflowDefinition(ctx context.Context, definition WorkflowBuilderDefinition) error {
	// Basic validation - check required fields
	if len(definition.Nodes) == 0 {
		return fmt.Errorf("workflow must have at least one node")
	}

	// Check for trigger nodes
	hasTrigger := false
	for _, node := range definition.Nodes {
		if node.Type == "schedule" || node.Type == "webhook" || node.Type == "manual" {
			hasTrigger = true
			break
		}
	}

	if !hasTrigger {
		return fmt.Errorf("workflow must have at least one trigger node")
	}

	return nil
}

// CreateWorkflowFromBuilder creates a workflow from the builder definition
func (wbi *WorkflowBuilderIntegration) CreateWorkflowFromBuilder(ctx context.Context, name, description string, definition WorkflowBuilderDefinition) (*ecosystem.Workflow, error) {
	// Validate definition
	if err := wbi.ValidateWorkflowDefinition(ctx, definition); err != nil {
		return nil, fmt.Errorf("workflow validation failed: %w", err)
	}

	// Convert to ecosystem format
	ecosystemDefinition := wbi.convertToEcosystemFormat(definition)

	// Create workflow request
	req := ecosystem.CreateWorkflowRequest{
		Name:        name,
		Description: description,
		Definition:  ecosystemDefinition,
	}

	// Create workflow using workflow service
	workflow, err := wbi.workflowService.CreateWorkflow(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to create workflow: %w", err)
	}

	return workflow, nil
}

// UpdateWorkflowFromBuilder updates a workflow from the builder definition
func (wbi *WorkflowBuilderIntegration) UpdateWorkflowFromBuilder(ctx context.Context, workflowID string, definition WorkflowBuilderDefinition) (*ecosystem.Workflow, error) {
	// Validate definition
	if err := wbi.ValidateWorkflowDefinition(ctx, definition); err != nil {
		return nil, fmt.Errorf("workflow validation failed: %w", err)
	}

	// Convert to ecosystem format
	ecosystemDefinition := wbi.convertToEcosystemFormat(definition)

	// Update workflow
	updates := map[string]interface{}{
		"definition": ecosystemDefinition,
	}

	workflow, err := wbi.workflowService.UpdateWorkflow(ctx, workflowID, updates)
	if err != nil {
		return nil, fmt.Errorf("failed to update workflow: %w", err)
	}

	return workflow, nil
}

// ExecuteWorkflowFromBuilder executes a workflow with input from the builder
func (wbi *WorkflowBuilderIntegration) ExecuteWorkflowFromBuilder(ctx context.Context, workflowID string, input map[string]interface{}) (*WorkflowExecutionResult, error) {
	// Execute using the execution engine
	execReq := WorkflowExecutionRequest{
		WorkflowID: workflowID,
		Input:      input,
		MaxRetries: 3,
		Timeout:    30 * time.Minute,
		Metadata: map[string]interface{}{
			"triggered_by": "workflow_builder",
			"timestamp":    time.Now().Unix(),
		},
	}

	return wbi.executionEngine.ExecuteWorkflow(ctx, execReq)
}

// GetWorkflowTemplates returns available workflow templates
func (wbi *WorkflowBuilderIntegration) GetWorkflowTemplates(ctx context.Context) ([]WorkflowTemplate, error) {
	// Pre-defined templates for building automation
	templates := []WorkflowTemplate{
		{
			ID:          "equipment_monitoring",
			Name:        "Equipment Monitoring",
			Description: "Monitor equipment status and send alerts",
			Category:    "monitoring",
			Tags:        []string{"equipment", "monitoring", "alerts"},
			Definition: WorkflowBuilderDefinition{
				Nodes: []WorkflowBuilderNode{
					{
						ID:       "schedule_trigger",
						Type:     "schedule",
						Name:     "Schedule Check",
						Position: Position{X: 100, Y: 100},
						Parameters: map[string]interface{}{
							"interval": "*/5 * * * *", // Every 5 minutes
						},
					},
					{
						ID:       "equipment_check",
						Type:     "http_request",
						Name:     "Check Equipment Status",
						Position: Position{X: 300, Y: 100},
						Parameters: map[string]interface{}{
							"url":    "/api/v1/core/equipment/status",
							"method": "GET",
						},
					},
					{
						ID:       "condition_check",
						Type:     "condition",
						Name:     "Status Check",
						Position: Position{X: 500, Y: 100},
						Parameters: map[string]interface{}{
							"condition": "{{$json.status}} !== 'operational'",
						},
					},
					{
						ID:       "send_alert",
						Type:     "notification",
						Name:     "Send Alert",
						Position: Position{X: 700, Y: 100},
						Parameters: map[string]interface{}{
							"type":    "email",
							"subject": "Equipment Alert",
							"message": "Equipment {{$json.name}} is {{$json.status}}",
						},
					},
				},
				Connections: []WorkflowBuilderConnection{
					{ID: "conn1", Source: "schedule_trigger", Target: "equipment_check"},
					{ID: "conn2", Source: "equipment_check", Target: "condition_check"},
					{ID: "conn3", Source: "condition_check", Target: "send_alert"},
				},
			},
		},
		{
			ID:          "maintenance_scheduler",
			Name:        "Maintenance Scheduler",
			Description: "Automated maintenance scheduling and execution",
			Category:    "maintenance",
			Tags:        []string{"maintenance", "scheduling", "automation"},
			Definition: WorkflowBuilderDefinition{
				Nodes: []WorkflowBuilderNode{
					{
						ID:       "cron_trigger",
						Type:     "schedule",
						Name:     "Daily Check",
						Position: Position{X: 100, Y: 100},
						Parameters: map[string]interface{}{
							"interval": "0 8 * * *", // Daily at 8 AM
						},
					},
					{
						ID:       "get_schedules",
						Type:     "http_request",
						Name:     "Get Maintenance Schedules",
						Position: Position{X: 300, Y: 100},
						Parameters: map[string]interface{}{
							"url":    "/api/v1/workflow/maintenance/schedules",
							"method": "GET",
						},
					},
					{
						ID:       "create_work_orders",
						Type:     "http_request",
						Name:     "Create Work Orders",
						Position: Position{X: 500, Y: 100},
						Parameters: map[string]interface{}{
							"url":    "/api/v1/workflow/maintenance/work-orders",
							"method": "POST",
							"body":   "{{$json.schedules}}",
						},
					},
					{
						ID:       "notify_team",
						Type:     "notification",
						Name:     "Notify Team",
						Position: Position{X: 700, Y: 100},
						Parameters: map[string]interface{}{
							"type":    "slack",
							"message": "Created {{$json.count}} work orders for today",
						},
					},
				},
				Connections: []WorkflowBuilderConnection{
					{ID: "conn1", Source: "cron_trigger", Target: "get_schedules"},
					{ID: "conn2", Source: "get_schedules", Target: "create_work_orders"},
					{ID: "conn3", Source: "create_work_orders", Target: "notify_team"},
				},
			},
		},
		{
			ID:          "energy_optimization",
			Name:        "Energy Optimization",
			Description: "Optimize energy usage based on occupancy and time",
			Category:    "optimization",
			Tags:        []string{"energy", "optimization", "automation"},
			Definition: WorkflowBuilderDefinition{
				Nodes: []WorkflowBuilderNode{
					{
						ID:       "time_trigger",
						Type:     "schedule",
						Name:     "Hourly Check",
						Position: Position{X: 100, Y: 100},
						Parameters: map[string]interface{}{
							"interval": "0 * * * *", // Every hour
						},
					},
					{
						ID:       "get_occupancy",
						Type:     "http_request",
						Name:     "Get Occupancy Data",
						Position: Position{X: 300, Y: 100},
						Parameters: map[string]interface{}{
							"url":    "/api/v1/core/spatial/occupancy",
							"method": "GET",
						},
					},
					{
						ID:       "optimize_settings",
						Type:     "function",
						Name:     "Optimize Settings",
						Position: Position{X: 500, Y: 100},
						Parameters: map[string]interface{}{
							"function": `
								const occupancy = $input.all().map(item => item.json.occupancy);
								const avgOccupancy = occupancy.reduce((a, b) => a + b, 0) / occupancy.length;
								
								const settings = {
									lighting: avgOccupancy > 0.3 ? 100 : 30,
									hvac: avgOccupancy > 0.5 ? 22 : 18,
									ventilation: avgOccupancy > 0.7 ? 100 : 50
								};
								
								return { settings };
							`,
						},
					},
					{
						ID:       "apply_settings",
						Type:     "http_request",
						Name:     "Apply Settings",
						Position: Position{X: 700, Y: 100},
						Parameters: map[string]interface{}{
							"url":    "/api/v1/core/equipment/bulk-update",
							"method": "PUT",
							"body":   "{{$json.settings}}",
						},
					},
				},
				Connections: []WorkflowBuilderConnection{
					{ID: "conn1", Source: "time_trigger", Target: "get_occupancy"},
					{ID: "conn2", Source: "get_occupancy", Target: "optimize_settings"},
					{ID: "conn3", Source: "optimize_settings", Target: "apply_settings"},
				},
			},
		},
	}

	return templates, nil
}

// CreateWorkflowFromTemplate creates a workflow from a template
func (wbi *WorkflowBuilderIntegration) CreateWorkflowFromTemplate(ctx context.Context, templateID, name, description string) (*ecosystem.Workflow, error) {
	// Get templates
	templates, err := wbi.GetWorkflowTemplates(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get templates: %w", err)
	}

	// Find template
	var template *WorkflowTemplate
	for _, t := range templates {
		if t.ID == templateID {
			template = &t
			break
		}
	}

	if template == nil {
		return nil, fmt.Errorf("template not found: %s", templateID)
	}

	// Use template name if name not provided
	if name == "" {
		name = template.Name
	}
	if description == "" {
		description = template.Description
	}

	// Create workflow from template
	return wbi.CreateWorkflowFromBuilder(ctx, name, description, template.Definition)
}

// convertToN8nFormat converts builder definition to n8n format
func (wbi *WorkflowBuilderIntegration) convertToN8nFormat(definition WorkflowBuilderDefinition) map[string]interface{} {
	n8nNodes := make([]map[string]interface{}, len(definition.Nodes))
	for i, node := range definition.Nodes {
		n8nNodes[i] = map[string]interface{}{
			"id":         node.ID,
			"name":       node.Name,
			"type":       wbi.mapNodeType(node.Type),
			"position":   []float64{node.Position.X, node.Position.Y},
			"parameters": node.Parameters,
		}
	}

	n8nConnections := make(map[string]interface{})
	for _, conn := range definition.Connections {
		if n8nConnections[conn.Source] == nil {
			n8nConnections[conn.Source] = make(map[string]interface{})
		}
		// Convert to n8n connection format
		n8nConnections[conn.Source].(map[string]interface{})["main"] = [][]map[string]interface{}{
			{
				{
					"node":  conn.Target,
					"type":  "main",
					"index": 0,
				},
			},
		}
	}

	return map[string]interface{}{
		"nodes":       n8nNodes,
		"connections": n8nConnections,
		"settings":    definition.Settings,
	}
}

// convertToEcosystemFormat converts builder definition to ecosystem format
func (wbi *WorkflowBuilderIntegration) convertToEcosystemFormat(definition WorkflowBuilderDefinition) map[string]interface{} {
	nodes := make([]map[string]interface{}, len(definition.Nodes))
	for i, node := range definition.Nodes {
		nodes[i] = map[string]interface{}{
			"id":         node.ID,
			"type":       node.Type,
			"name":       node.Name,
			"position":   []float64{node.Position.X, node.Position.Y},
			"parameters": node.Parameters,
			"data":       node.Data,
		}
	}

	connections := make([]map[string]interface{}, len(definition.Connections))
	for i, conn := range definition.Connections {
		connections[i] = map[string]interface{}{
			"id":           conn.ID,
			"source":       conn.Source,
			"target":       conn.Target,
			"sourceHandle": conn.SourceHandle,
			"targetHandle": conn.TargetHandle,
		}
	}

	return map[string]interface{}{
		"nodes":       nodes,
		"connections": connections,
		"settings":    definition.Settings,
	}
}

// mapNodeType maps builder node types to n8n node types
func (wbi *WorkflowBuilderIntegration) mapNodeType(builderType string) string {
	typeMap := map[string]string{
		"schedule":     "n8n-nodes-base.scheduleTrigger",
		"http_request": "n8n-nodes-base.httpRequest",
		"condition":    "n8n-nodes-base.if",
		"notification": "n8n-nodes-base.email",
		"function":     "n8n-nodes-base.function",
		"webhook":      "n8n-nodes-base.webhook",
		"database":     "n8n-nodes-base.postgres",
		"file":         "n8n-nodes-base.readFile",
		"transform":    "n8n-nodes-base.itemLists",
		"merge":        "n8n-nodes-base.merge",
		"split":        "n8n-nodes-base.splitInBatches",
		"loop":         "n8n-nodes-base.loopOverItems",
	}

	if n8nType, exists := typeMap[builderType]; exists {
		return n8nType
	}
	return "n8n-nodes-base.noOp" // Default fallback
}
