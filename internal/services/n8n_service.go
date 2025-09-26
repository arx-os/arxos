package services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/retry"
)

// N8NService handles integration with n8n workflow automation platform
type N8NService struct {
	baseURL     string
	apiKey      string
	httpClient  *http.Client
	retryConfig retry.Config
}

// NewN8NService creates a new n8n service
func NewN8NService(baseURL, apiKey string) *N8NService {
	return &N8NService{
		baseURL: baseURL,
		apiKey:  apiKey,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		retryConfig: retry.Config{
			MaxAttempts:  3,
			InitialDelay: 1 * time.Second,
			MaxDelay:     10 * time.Second,
			Multiplier:   2.0,
		},
	}
}

// N8N API types

type N8NWorkflow struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Active      bool                   `json:"active"`
	Nodes       []N8NNode              `json:"nodes"`
	Connections map[string]interface{} `json:"connections"`
	Settings    map[string]interface{} `json:"settings"`
	StaticData  map[string]interface{} `json:"staticData"`
	CreatedAt   time.Time              `json:"createdAt"`
	UpdatedAt   time.Time              `json:"updatedAt"`
}

type N8NNode struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	TypeVersion float64                `json:"typeVersion"`
	Position    []float64              `json:"position"`
	Parameters  map[string]interface{} `json:"parameters"`
	WebhookURL  string                 `json:"webhookUrl,omitempty"`
}

type N8NExecution struct {
	ID         string                 `json:"id"`
	WorkflowID string                 `json:"workflowId"`
	Status     string                 `json:"status"`
	StartedAt  time.Time              `json:"startedAt"`
	StoppedAt  *time.Time             `json:"stoppedAt,omitempty"`
	Data       map[string]interface{} `json:"data"`
	Error      string                 `json:"error,omitempty"`
}

type N8NExecutionRequest struct {
	WorkflowID string                 `json:"workflowId"`
	Input      map[string]interface{} `json:"input,omitempty"`
}

// Workflow management

func (ns *N8NService) CreateWorkflow(ctx context.Context, req CreateWorkflowRequest) (*N8NWorkflow, error) {
	// Convert ArxOS workflow to n8n format
	n8nWorkflow := &N8NWorkflow{
		Name:        req.Name,
		Active:      false, // Start inactive until validated
		Nodes:       ns.convertNodes(req.Definition),
		Connections: ns.convertConnections(req.Definition),
		Settings: map[string]interface{}{
			"executionOrder": "v1",
		},
	}

	// Create workflow in n8n
	payload, err := json.Marshal(n8nWorkflow)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal workflow: %w", err)
	}

	resp, err := ns.makeRequest(ctx, "POST", "/api/v1/workflows", payload)
	if err != nil {
		return nil, fmt.Errorf("failed to create workflow: %w", err)
	}

	var createdWorkflow N8NWorkflow
	if err := json.Unmarshal(resp, &createdWorkflow); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &createdWorkflow, nil
}

func (ns *N8NService) GetWorkflow(ctx context.Context, workflowID string) (*N8NWorkflow, error) {
	resp, err := ns.makeRequest(ctx, "GET", fmt.Sprintf("/api/v1/workflows/%s", workflowID), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	var workflow N8NWorkflow
	if err := json.Unmarshal(resp, &workflow); err != nil {
		return nil, fmt.Errorf("failed to unmarshal workflow: %w", err)
	}

	return &workflow, nil
}

func (ns *N8NService) UpdateWorkflow(ctx context.Context, workflowID string, updates map[string]interface{}) (*N8NWorkflow, error) {
	// Get existing workflow
	workflow, err := ns.GetWorkflow(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get existing workflow: %w", err)
	}

	// Apply updates
	if name, ok := updates["name"].(string); ok {
		workflow.Name = name
	}
	if nodes, ok := updates["nodes"].([]N8NNode); ok {
		workflow.Nodes = nodes
	}
	if connections, ok := updates["connections"].(map[string]interface{}); ok {
		workflow.Connections = connections
	}

	// Update in n8n
	payload, err := json.Marshal(workflow)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal workflow: %w", err)
	}

	resp, err := ns.makeRequest(ctx, "PUT", fmt.Sprintf("/api/v1/workflows/%s", workflowID), payload)
	if err != nil {
		return nil, fmt.Errorf("failed to update workflow: %w", err)
	}

	var updatedWorkflow N8NWorkflow
	if err := json.Unmarshal(resp, &updatedWorkflow); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &updatedWorkflow, nil
}

func (ns *N8NService) DeleteWorkflow(ctx context.Context, workflowID string) error {
	_, err := ns.makeRequest(ctx, "DELETE", fmt.Sprintf("/api/v1/workflows/%s", workflowID), nil)
	if err != nil {
		return fmt.Errorf("failed to delete workflow: %w", err)
	}

	return nil
}

func (ns *N8NService) ActivateWorkflow(ctx context.Context, workflowID string) error {
	_, err := ns.makeRequest(ctx, "POST", fmt.Sprintf("/api/v1/workflows/%s/activate", workflowID), nil)
	if err != nil {
		return fmt.Errorf("failed to activate workflow: %w", err)
	}

	return nil
}

func (ns *N8NService) DeactivateWorkflow(ctx context.Context, workflowID string) error {
	_, err := ns.makeRequest(ctx, "POST", fmt.Sprintf("/api/v1/workflows/%s/deactivate", workflowID), nil)
	if err != nil {
		return fmt.Errorf("failed to deactivate workflow: %w", err)
	}

	return nil
}

// Workflow execution

func (ns *N8NService) ExecuteWorkflow(ctx context.Context, workflowID string, input map[string]interface{}) (*N8NExecution, error) {
	execReq := N8NExecutionRequest{
		WorkflowID: workflowID,
		Input:      input,
	}

	payload, err := json.Marshal(execReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal execution request: %w", err)
	}

	resp, err := ns.makeRequest(ctx, "POST", "/api/v1/executions", payload)
	if err != nil {
		return nil, fmt.Errorf("failed to execute workflow: %w", err)
	}

	var execution N8NExecution
	if err := json.Unmarshal(resp, &execution); err != nil {
		return nil, fmt.Errorf("failed to unmarshal execution: %w", err)
	}

	return &execution, nil
}

func (ns *N8NService) GetExecution(ctx context.Context, executionID string) (*N8NExecution, error) {
	resp, err := ns.makeRequest(ctx, "GET", fmt.Sprintf("/api/v1/executions/%s", executionID), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to get execution: %w", err)
	}

	var execution N8NExecution
	if err := json.Unmarshal(resp, &execution); err != nil {
		return nil, fmt.Errorf("failed to unmarshal execution: %w", err)
	}

	return &execution, nil
}

func (ns *N8NService) ListExecutions(ctx context.Context, workflowID string, limit int) ([]*N8NExecution, error) {
	url := fmt.Sprintf("/api/v1/executions?workflowId=%s&limit=%d", workflowID, limit)
	resp, err := ns.makeRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to list executions: %w", err)
	}

	var executions []*N8NExecution
	if err := json.Unmarshal(resp, &executions); err != nil {
		return nil, fmt.Errorf("failed to unmarshal executions: %w", err)
	}

	return executions, nil
}

// Building-specific n8n nodes

func (ns *N8NService) CreateBuildingNode(buildingID string) N8NNode {
	return N8NNode{
		ID:          generateNodeID(),
		Name:        "Building Input",
		Type:        "n8n-nodes-base.httpRequest",
		TypeVersion: 1,
		Position:    []float64{240, 300},
		Parameters: map[string]interface{}{
			"url": fmt.Sprintf("{{$node['Building'].json['building_id']}}"),
			"options": map[string]interface{}{
				"response": map[string]interface{}{
					"response": map[string]interface{}{
						"responseFormat": "json",
					},
				},
			},
		},
	}
}

func (ns *N8NService) CreateEquipmentNode(equipmentPath string) N8NNode {
	return N8NNode{
		ID:          generateNodeID(),
		Name:        "Equipment Control",
		Type:        "n8n-nodes-base.httpRequest",
		TypeVersion: 1,
		Position:    []float64{460, 300},
		Parameters: map[string]interface{}{
			"url":      fmt.Sprintf("/api/v1/core/equipment%s", equipmentPath),
			"method":   "PUT",
			"sendBody": true,
			"bodyParameters": map[string]interface{}{
				"parameters": []map[string]interface{}{
					{
						"name":  "state",
						"value": "{{$node['Trigger'].json['state']}}",
					},
				},
			},
		},
	}
}

func (ns *N8NService) CreateNotificationNode(notificationType string) N8NNode {
	return N8NNode{
		ID:          generateNodeID(),
		Name:        "Send Notification",
		Type:        "n8n-nodes-base.httpRequest",
		TypeVersion: 1,
		Position:    []float64{680, 300},
		Parameters: map[string]interface{}{
			"url":      "/api/v1/notifications/send",
			"method":   "POST",
			"sendBody": true,
			"bodyParameters": map[string]interface{}{
				"parameters": []map[string]interface{}{
					{
						"name":  "type",
						"value": notificationType,
					},
					{
						"name":  "message",
						"value": "{{$node['Equipment Control'].json['message']}}",
					},
				},
			},
		},
	}
}

// Helper functions

func (ns *N8NService) convertNodes(definition map[string]interface{}) []N8NNode {
	nodes := []N8NNode{}

	if nodesData, ok := definition["nodes"].([]interface{}); ok {
		for _, nodeData := range nodesData {
			if nodeMap, ok := nodeData.(map[string]interface{}); ok {
				node := N8NNode{
					ID:          generateNodeID(),
					Name:        getString(nodeMap, "name"),
					Type:        getString(nodeMap, "type"),
					TypeVersion: 1,
					Position:    []float64{240, 300}, // Default position
					Parameters:  getMap(nodeMap, "config"),
				}

				// Set specific position if provided
				if pos, ok := nodeMap["position"].([]interface{}); ok && len(pos) >= 2 {
					node.Position = []float64{
						getFloat(pos[0]),
						getFloat(pos[1]),
					}
				}

				nodes = append(nodes, node)
			}
		}
	}

	return nodes
}

func (ns *N8NService) convertConnections(definition map[string]interface{}) map[string]interface{} {
	connections := make(map[string]interface{})

	if connectionsData, ok := definition["connections"].([]interface{}); ok {
		for _, connData := range connectionsData {
			if connMap, ok := connData.(map[string]interface{}); ok {
				from := getString(connMap, "from")
				to := getString(connMap, "to")

				if from != "" && to != "" {
					connections[from] = map[string]interface{}{
						"main": [][]map[string]interface{}{
							{
								{
									"node":  to,
									"type":  "main",
									"index": 0,
								},
							},
						},
					}
				}
			}
		}
	}

	return connections
}

func (ns *N8NService) makeRequest(ctx context.Context, method, path string, body []byte) ([]byte, error) {
	var responseBody []byte

	result := retry.Do(ctx, func(ctx context.Context) error {
		url := ns.baseURL + path

		var reqBody *bytes.Reader
		if body != nil {
			reqBody = bytes.NewReader(body)
		}

		req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}

		// Set headers
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-N8N-API-KEY", ns.apiKey)
		req.Header.Set("User-Agent", "ArxOS-Workflow-Service/1.0")

		// Make request
		resp, err := ns.httpClient.Do(req)
		if err != nil {
			return fmt.Errorf("failed to make request: %w", err)
		}
		defer resp.Body.Close()

		// Check status code
		if resp.StatusCode < 200 || resp.StatusCode >= 300 {
			// Try to read error response
			var errorBody bytes.Buffer
			errorBody.ReadFrom(resp.Body)
			return fmt.Errorf("request failed with status %d: %s", resp.StatusCode, errorBody.String())
		}

		// Read response
		var bodyBuffer bytes.Buffer
		_, err = bodyBuffer.ReadFrom(resp.Body)
		if err != nil {
			return fmt.Errorf("failed to read response: %w", err)
		}

		responseBody = bodyBuffer.Bytes()
		return nil
	}, ns.retryConfig)

	if !result.Success {
		return nil, fmt.Errorf("request failed after %d attempts: %w", result.Attempts, result.LastError)
	}
	return responseBody, nil
}

// Utility functions

func generateNodeID() string {
	return fmt.Sprintf("node_%d", time.Now().UnixNano())
}

func getString(m map[string]interface{}, key string) string {
	if val, ok := m[key].(string); ok {
		return val
	}
	return ""
}

func getFloat(val interface{}) float64 {
	if f, ok := val.(float64); ok {
		return f
	}
	if i, ok := val.(int); ok {
		return float64(i)
	}
	return 0
}

func getMap(m map[string]interface{}, key string) map[string]interface{} {
	if val, ok := m[key].(map[string]interface{}); ok {
		return val
	}
	return make(map[string]interface{})
}

// Request types (from ecosystem package)

type CreateWorkflowRequest struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Definition  map[string]interface{} `json:"definition"`
}
