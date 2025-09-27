package workflow

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// N8NClient handles communication with n8n workflow automation platform
type N8NClient struct {
	baseURL    string
	apiKey     string
	httpClient *http.Client
}

// N8NWorkflow represents an n8n workflow
type N8NWorkflow struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Active      bool                   `json:"active"`
	Nodes       []*N8NNode             `json:"nodes"`
	Connections map[string]interface{} `json:"connections"`
	Settings    map[string]interface{} `json:"settings"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// N8NNode represents an n8n workflow node
type N8NNode struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	TypeVersion float64                `json:"typeVersion"`
	Position    []float64              `json:"position"`
	Parameters  map[string]interface{} `json:"parameters"`
	Credentials map[string]interface{} `json:"credentials"`
}

// N8NExecution represents an n8n workflow execution
type N8NExecution struct {
	ID         string                 `json:"id"`
	WorkflowID string                 `json:"workflowId"`
	Status     string                 `json:"status"`
	Data       map[string]interface{} `json:"data"`
	StartedAt  time.Time              `json:"startedAt"`
	StoppedAt  *time.Time             `json:"stoppedAt,omitempty"`
	Mode       string                 `json:"mode"`
}

// N8NWebhookRequest represents a webhook request to n8n
type N8NWebhookRequest struct {
	Headers map[string]string      `json:"headers"`
	Body    map[string]interface{} `json:"body"`
	Query   map[string]string      `json:"query"`
}

// N8NWebhookResponse represents a webhook response from n8n
type N8NWebhookResponse struct {
	Status  int                    `json:"status"`
	Headers map[string]string      `json:"headers"`
	Body    map[string]interface{} `json:"body"`
}

// NewN8NClient creates a new n8n client
func NewN8NClient() *N8NClient {
	return &N8NClient{
		baseURL: "http://localhost:5678", // Default n8n URL
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// SetCredentials sets the n8n API credentials
func (c *N8NClient) SetCredentials(baseURL, apiKey string) {
	c.baseURL = baseURL
	c.apiKey = apiKey
}

// CreateWorkflow creates a workflow in n8n
func (c *N8NClient) CreateWorkflow(ctx context.Context, workflow *N8NWorkflow) (*N8NWorkflow, error) {
	url := fmt.Sprintf("%s/api/v1/workflows", c.baseURL)

	jsonData, err := json.Marshal(workflow)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal workflow: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		return nil, fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	var createdWorkflow N8NWorkflow
	if err := json.NewDecoder(resp.Body).Decode(&createdWorkflow); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	logger.Info("Created n8n workflow: %s (%s)", createdWorkflow.ID, createdWorkflow.Name)
	return &createdWorkflow, nil
}

// GetWorkflow retrieves a workflow from n8n
func (c *N8NClient) GetWorkflow(ctx context.Context, workflowID string) (*N8NWorkflow, error) {
	url := fmt.Sprintf("%s/api/v1/workflows/%s", c.baseURL, workflowID)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("workflow %s not found", workflowID)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	var workflow N8NWorkflow
	if err := json.NewDecoder(resp.Body).Decode(&workflow); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &workflow, nil
}

// UpdateWorkflow updates a workflow in n8n
func (c *N8NClient) UpdateWorkflow(ctx context.Context, workflowID string, workflow *N8NWorkflow) (*N8NWorkflow, error) {
	url := fmt.Sprintf("%s/api/v1/workflows/%s", c.baseURL, workflowID)

	jsonData, err := json.Marshal(workflow)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal workflow: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "PUT", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	var updatedWorkflow N8NWorkflow
	if err := json.NewDecoder(resp.Body).Decode(&updatedWorkflow); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	logger.Info("Updated n8n workflow: %s (%s)", updatedWorkflow.ID, updatedWorkflow.Name)
	return &updatedWorkflow, nil
}

// DeleteWorkflow deletes a workflow from n8n
func (c *N8NClient) DeleteWorkflow(ctx context.Context, workflowID string) error {
	url := fmt.Sprintf("%s/api/v1/workflows/%s", c.baseURL, workflowID)

	req, err := http.NewRequestWithContext(ctx, "DELETE", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("workflow %s not found", workflowID)
	}

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	logger.Info("Deleted n8n workflow: %s", workflowID)
	return nil
}

// ActivateWorkflow activates a workflow in n8n
func (c *N8NClient) ActivateWorkflow(ctx context.Context, workflowID string) error {
	url := fmt.Sprintf("%s/api/v1/workflows/%s/activate", c.baseURL, workflowID)

	req, err := http.NewRequestWithContext(ctx, "POST", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	logger.Info("Activated n8n workflow: %s", workflowID)
	return nil
}

// DeactivateWorkflow deactivates a workflow in n8n
func (c *N8NClient) DeactivateWorkflow(ctx context.Context, workflowID string) error {
	url := fmt.Sprintf("%s/api/v1/workflows/%s/deactivate", c.baseURL, workflowID)

	req, err := http.NewRequestWithContext(ctx, "POST", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	logger.Info("Deactivated n8n workflow: %s", workflowID)
	return nil
}

// ExecuteWorkflow executes a workflow in n8n
func (c *N8NClient) ExecuteWorkflow(ctx context.Context, workflowID string, input map[string]interface{}) (*N8NExecution, error) {
	url := fmt.Sprintf("%s/api/v1/workflows/%s/execute", c.baseURL, workflowID)

	jsonData, err := json.Marshal(input)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal input: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	var execution N8NExecution
	if err := json.NewDecoder(resp.Body).Decode(&execution); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	logger.Info("Executed n8n workflow: %s (execution: %s)", workflowID, execution.ID)
	return &execution, nil
}

// GetExecution retrieves an execution from n8n
func (c *N8NClient) GetExecution(ctx context.Context, executionID string) (*N8NExecution, error) {
	url := fmt.Sprintf("%s/api/v1/executions/%s", c.baseURL, executionID)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("execution %s not found", executionID)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	var execution N8NExecution
	if err := json.NewDecoder(resp.Body).Decode(&execution); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &execution, nil
}

// SendWebhook sends a webhook to n8n
func (c *N8NClient) SendWebhook(ctx context.Context, webhookURL string, data map[string]interface{}) (*N8NWebhookResponse, error) {
	jsonData, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal data: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", webhookURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	response := &N8NWebhookResponse{
		Status:  resp.StatusCode,
		Headers: make(map[string]string),
		Body:    make(map[string]interface{}),
	}

	// Copy headers
	for key, values := range resp.Header {
		if len(values) > 0 {
			response.Headers[key] = values[0]
		}
	}

	// Parse response body
	if resp.Body != nil {
		var bodyData map[string]interface{}
		if err := json.NewDecoder(resp.Body).Decode(&bodyData); err == nil {
			response.Body = bodyData
		}
	}

	logger.Info("Sent webhook to n8n: %s (status: %d)", webhookURL, resp.StatusCode)
	return response, nil
}

// ListWorkflows lists all workflows in n8n
func (c *N8NClient) ListWorkflows(ctx context.Context) ([]*N8NWorkflow, error) {
	url := fmt.Sprintf("%s/api/v1/workflows", c.baseURL)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	var workflows []*N8NWorkflow
	if err := json.NewDecoder(resp.Body).Decode(&workflows); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return workflows, nil
}

// GetWorkflowExecutions retrieves executions for a workflow
func (c *N8NClient) GetWorkflowExecutions(ctx context.Context, workflowID string, limit int) ([]*N8NExecution, error) {
	url := fmt.Sprintf("%s/api/v1/executions?workflowId=%s&limit=%d", c.baseURL, workflowID, limit)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if c.apiKey != "" {
		req.Header.Set("X-N8N-API-KEY", c.apiKey)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("n8n API returned status %d", resp.StatusCode)
	}

	var executions []*N8NExecution
	if err := json.NewDecoder(resp.Body).Decode(&executions); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return executions, nil
}

// ConvertToN8NWorkflow converts an ArxOS workflow to n8n format
func (c *N8NClient) ConvertToN8NWorkflow(workflow *Workflow) *N8NWorkflow {
	n8nNodes := make([]*N8NNode, 0, len(workflow.Nodes))

	for _, node := range workflow.Nodes {
		n8nNode := &N8NNode{
			ID:          node.ID,
			Name:        node.Name,
			Type:        string(node.Type),
			TypeVersion: 1.0,
			Position:    []float64{node.Position.X, node.Position.Y},
			Parameters:  node.Parameters,
			Credentials: node.Credentials,
		}
		n8nNodes = append(n8nNodes, n8nNode)
	}

	// Convert connections to n8n format
	n8nConnections := make(map[string]interface{})
	for _, connection := range workflow.Connections {
		key := fmt.Sprintf("%s->%s", connection.FromNode, connection.ToNode)
		n8nConnections[key] = map[string]interface{}{
			"from": connection.FromNode,
			"to":   connection.ToNode,
		}
	}

	return &N8NWorkflow{
		ID:          workflow.ID,
		Name:        workflow.Name,
		Active:      workflow.Status == WorkflowStatusActive,
		Nodes:       n8nNodes,
		Connections: n8nConnections,
		Settings:    workflow.Config,
		CreatedAt:   workflow.CreatedAt,
		UpdatedAt:   workflow.UpdatedAt,
	}
}

// ConvertFromN8NWorkflow converts an n8n workflow to ArxOS format
func (c *N8NClient) ConvertFromN8NWorkflow(n8nWorkflow *N8NWorkflow) *Workflow {
	workflowNodes := make([]*WorkflowNode, 0, len(n8nWorkflow.Nodes))

	for _, n8nNode := range n8nWorkflow.Nodes {
		position := Position{X: 0, Y: 0}
		if len(n8nNode.Position) >= 2 {
			position.X = n8nNode.Position[0]
			position.Y = n8nNode.Position[1]
		}

		node := &WorkflowNode{
			ID:          n8nNode.ID,
			Type:        NodeType(n8nNode.Type),
			Name:        n8nNode.Name,
			Position:    position,
			Config:      make(map[string]interface{}),
			Parameters:  n8nNode.Parameters,
			Credentials: n8nNode.Credentials,
		}
		workflowNodes = append(workflowNodes, node)
	}

	// Convert n8n connections to ArxOS format
	workflowConnections := make([]*WorkflowConnection, 0)
	for key, connectionData := range n8nWorkflow.Connections {
		if connMap, ok := connectionData.(map[string]interface{}); ok {
			connection := &WorkflowConnection{
				ID:       key,
				FromNode: connMap["from"].(string),
				ToNode:   connMap["to"].(string),
				FromPort: "output",
				ToPort:   "input",
			}
			workflowConnections = append(workflowConnections, connection)
		}
	}

	status := WorkflowStatusInactive
	if n8nWorkflow.Active {
		status = WorkflowStatusActive
	}

	return &Workflow{
		ID:          n8nWorkflow.ID,
		Name:        n8nWorkflow.Name,
		Description: "",
		Version:     "1.0.0",
		Status:      status,
		Triggers:    make([]*Trigger, 0),
		Nodes:       workflowNodes,
		Connections: workflowConnections,
		Config:      n8nWorkflow.Settings,
		CreatedAt:   n8nWorkflow.CreatedAt,
		UpdatedAt:   n8nWorkflow.UpdatedAt,
		CreatedBy:   "n8n",
	}
}
