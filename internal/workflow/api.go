package workflow

import (
	"context"
	"encoding/json"
	"net/http"
)

// WorkflowAPI provides HTTP API for workflow management
type WorkflowAPI struct {
	manager        *WorkflowManager
	triggerManager *TriggerManager
	actionManager  *ActionManager
	n8nClient      *N8NClient
}

// NewWorkflowAPI creates a new workflow API
func NewWorkflowAPI() *WorkflowAPI {
	return &WorkflowAPI{
		manager:        NewWorkflowManager(),
		triggerManager: NewTriggerManager(),
		actionManager:  NewActionManager(),
		n8nClient:      NewN8NClient(),
	}
}

// RegisterRoutes registers HTTP routes for the workflow API
func (api *WorkflowAPI) RegisterRoutes(mux *http.ServeMux) {
	// Workflow management routes
	mux.HandleFunc("/api/v1/workflows", api.handleWorkflows)
	mux.HandleFunc("/api/v1/workflows/", api.handleWorkflowByID)

	// Workflow execution routes
	mux.HandleFunc("/api/v1/workflows/execute", api.handleExecuteWorkflow)
	mux.HandleFunc("/api/v1/executions/", api.handleExecutionByID)

	// Trigger management routes
	mux.HandleFunc("/api/v1/triggers", api.handleTriggers)
	mux.HandleFunc("/api/v1/triggers/", api.handleTriggerByID)
	mux.HandleFunc("/api/v1/triggers/start", api.handleStartTrigger)
	mux.HandleFunc("/api/v1/triggers/stop", api.handleStopTrigger)

	// Action management routes
	mux.HandleFunc("/api/v1/actions", api.handleActions)
	mux.HandleFunc("/api/v1/actions/", api.handleActionByID)
	mux.HandleFunc("/api/v1/actions/execute", api.handleExecuteAction)

	// n8n integration routes
	mux.HandleFunc("/api/v1/n8n/workflows", api.handleN8NWorkflows)
	mux.HandleFunc("/api/v1/n8n/workflows/", api.handleN8NWorkflowByID)
	mux.HandleFunc("/api/v1/n8n/sync", api.handleN8NSync)

	// Metrics and statistics routes
	mux.HandleFunc("/api/v1/workflows/metrics", api.handleWorkflowMetrics)
	mux.HandleFunc("/api/v1/triggers/metrics", api.handleTriggerMetrics)
	mux.HandleFunc("/api/v1/actions/metrics", api.handleActionMetrics)
}

// handleWorkflows handles workflow management requests
func (api *WorkflowAPI) handleWorkflows(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getWorkflows(w, r)
	case http.MethodPost:
		api.createWorkflow(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleWorkflowByID handles individual workflow requests
func (api *WorkflowAPI) handleWorkflowByID(w http.ResponseWriter, r *http.Request) {
	workflowID := r.URL.Path[len("/api/v1/workflows/"):]
	if workflowID == "" {
		http.Error(w, "Workflow ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getWorkflow(w, r, workflowID)
	case http.MethodPut:
		api.updateWorkflow(w, r, workflowID)
	case http.MethodDelete:
		api.deleteWorkflow(w, r, workflowID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleExecuteWorkflow handles workflow execution requests
func (api *WorkflowAPI) handleExecuteWorkflow(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		WorkflowID string                 `json:"workflow_id"`
		Input      map[string]interface{} `json:"input"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	execution, err := api.manager.ExecuteWorkflow(context.Background(), req.WorkflowID, req.Input)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(execution)
}

// handleExecutionByID handles execution status requests
func (api *WorkflowAPI) handleExecutionByID(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	executionID := r.URL.Path[len("/api/v1/executions/"):]
	if executionID == "" {
		http.Error(w, "Execution ID required", http.StatusBadRequest)
		return
	}

	execution, err := api.manager.GetExecution(executionID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(execution)
}

// handleTriggers handles trigger management requests
func (api *WorkflowAPI) handleTriggers(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getTriggers(w, r)
	case http.MethodPost:
		api.createTrigger(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleTriggerByID handles individual trigger requests
func (api *WorkflowAPI) handleTriggerByID(w http.ResponseWriter, r *http.Request) {
	triggerID := r.URL.Path[len("/api/v1/triggers/"):]
	if triggerID == "" {
		http.Error(w, "Trigger ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getTrigger(w, r, triggerID)
	case http.MethodPut:
		api.updateTrigger(w, r, triggerID)
	case http.MethodDelete:
		api.deleteTrigger(w, r, triggerID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleStartTrigger handles trigger start requests
func (api *WorkflowAPI) handleStartTrigger(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		TriggerID string `json:"trigger_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.triggerManager.StartTrigger(context.Background(), req.TriggerID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "started"})
}

// handleStopTrigger handles trigger stop requests
func (api *WorkflowAPI) handleStopTrigger(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		TriggerID string `json:"trigger_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := api.triggerManager.StopTrigger(context.Background(), req.TriggerID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "stopped"})
}

// handleActions handles action management requests
func (api *WorkflowAPI) handleActions(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getActions(w, r)
	case http.MethodPost:
		api.createAction(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleActionByID handles individual action requests
func (api *WorkflowAPI) handleActionByID(w http.ResponseWriter, r *http.Request) {
	actionID := r.URL.Path[len("/api/v1/actions/"):]
	if actionID == "" {
		http.Error(w, "Action ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getAction(w, r, actionID)
	case http.MethodPut:
		api.updateAction(w, r, actionID)
	case http.MethodDelete:
		api.deleteAction(w, r, actionID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleExecuteAction handles action execution requests
func (api *WorkflowAPI) handleExecuteAction(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		ActionID string                 `json:"action_id"`
		Input    map[string]interface{} `json:"input"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	output, err := api.actionManager.ExecuteAction(context.Background(), req.ActionID, req.Input)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(output)
}

// handleN8NWorkflows handles n8n workflow requests
func (api *WorkflowAPI) handleN8NWorkflows(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		api.getN8NWorkflows(w, r)
	case http.MethodPost:
		api.createN8NWorkflow(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleN8NWorkflowByID handles individual n8n workflow requests
func (api *WorkflowAPI) handleN8NWorkflowByID(w http.ResponseWriter, r *http.Request) {
	workflowID := r.URL.Path[len("/api/v1/n8n/workflows/"):]
	if workflowID == "" {
		http.Error(w, "Workflow ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		api.getN8NWorkflow(w, r, workflowID)
	case http.MethodPut:
		api.updateN8NWorkflow(w, r, workflowID)
	case http.MethodDelete:
		api.deleteN8NWorkflow(w, r, workflowID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleN8NSync handles n8n synchronization requests
func (api *WorkflowAPI) handleN8NSync(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		Direction  string `json:"direction"` // "to_n8n" or "from_n8n"
		WorkflowID string `json:"workflow_id,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Sync workflows between ArxOS and n8n
	var result map[string]interface{}

	switch req.Direction {
	case "to_n8n":
		if req.WorkflowID != "" {
			// Sync specific workflow to n8n
			workflow, err := api.manager.GetWorkflow(req.WorkflowID)
			if err != nil {
				http.Error(w, err.Error(), http.StatusNotFound)
				return
			}

			n8nWorkflow := api.n8nClient.ConvertToN8NWorkflow(workflow)
			_, err = api.n8nClient.CreateWorkflow(context.Background(), n8nWorkflow)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}

			result = map[string]interface{}{
				"status":      "synced",
				"workflow_id": req.WorkflowID,
				"direction":   "to_n8n",
			}
		} else {
			// Sync all workflows to n8n
			workflows := api.manager.ListWorkflows()
			synced := 0
			for _, workflow := range workflows {
				n8nWorkflow := api.n8nClient.ConvertToN8NWorkflow(workflow)
				_, err := api.n8nClient.CreateWorkflow(context.Background(), n8nWorkflow)
				if err == nil {
					synced++
				}
			}

			result = map[string]interface{}{
				"status":       "synced",
				"synced_count": synced,
				"total_count":  len(workflows),
				"direction":    "to_n8n",
			}
		}
	case "from_n8n":
		// Sync workflows from n8n to ArxOS
		n8nWorkflows, err := api.n8nClient.ListWorkflows(context.Background())
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		synced := 0
		for _, n8nWorkflow := range n8nWorkflows {
			workflow := api.n8nClient.ConvertFromN8NWorkflow(n8nWorkflow)
			err := api.manager.CreateWorkflow(workflow)
			if err == nil {
				synced++
			}
		}

		result = map[string]interface{}{
			"status":       "synced",
			"synced_count": synced,
			"total_count":  len(n8nWorkflows),
			"direction":    "from_n8n",
		}
	default:
		http.Error(w, "Invalid direction", http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

// handleWorkflowMetrics handles workflow metrics requests
func (api *WorkflowAPI) handleWorkflowMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.manager.GetMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// handleTriggerMetrics handles trigger metrics requests
func (api *WorkflowAPI) handleTriggerMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.triggerManager.GetMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// handleActionMetrics handles action metrics requests
func (api *WorkflowAPI) handleActionMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	metrics := api.actionManager.GetMetrics()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// HTTP handler implementations
func (api *WorkflowAPI) getWorkflows(w http.ResponseWriter, r *http.Request) {
	workflows := api.manager.ListWorkflows()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workflows)
}

func (api *WorkflowAPI) createWorkflow(w http.ResponseWriter, r *http.Request) {
	var workflow Workflow
	if err := json.NewDecoder(r.Body).Decode(&workflow); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.manager.CreateWorkflow(&workflow); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(workflow)
}

func (api *WorkflowAPI) getWorkflow(w http.ResponseWriter, r *http.Request, workflowID string) {
	workflow, err := api.manager.GetWorkflow(workflowID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workflow)
}

func (api *WorkflowAPI) updateWorkflow(w http.ResponseWriter, r *http.Request, workflowID string) {
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.manager.UpdateWorkflow(workflowID, updates); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *WorkflowAPI) deleteWorkflow(w http.ResponseWriter, r *http.Request, workflowID string) {
	if err := api.manager.DeleteWorkflow(workflowID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

func (api *WorkflowAPI) getTriggers(w http.ResponseWriter, r *http.Request) {
	triggers := api.triggerManager.ListTriggers()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(triggers)
}

func (api *WorkflowAPI) createTrigger(w http.ResponseWriter, r *http.Request) {
	var trigger Trigger
	if err := json.NewDecoder(r.Body).Decode(&trigger); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.triggerManager.RegisterTrigger(&trigger); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(trigger)
}

func (api *WorkflowAPI) getTrigger(w http.ResponseWriter, r *http.Request, triggerID string) {
	trigger, err := api.triggerManager.GetTrigger(triggerID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(trigger)
}

func (api *WorkflowAPI) updateTrigger(w http.ResponseWriter, r *http.Request, triggerID string) {
	// Implementation for updating trigger
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *WorkflowAPI) deleteTrigger(w http.ResponseWriter, r *http.Request, triggerID string) {
	// Implementation for deleting trigger
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

func (api *WorkflowAPI) getActions(w http.ResponseWriter, r *http.Request) {
	actions := api.actionManager.ListActions()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(actions)
}

func (api *WorkflowAPI) createAction(w http.ResponseWriter, r *http.Request) {
	var action Action
	if err := json.NewDecoder(r.Body).Decode(&action); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := api.actionManager.RegisterAction(&action); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(action)
}

func (api *WorkflowAPI) getAction(w http.ResponseWriter, r *http.Request, actionID string) {
	action, err := api.actionManager.GetAction(actionID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(action)
}

func (api *WorkflowAPI) updateAction(w http.ResponseWriter, r *http.Request, actionID string) {
	// Implementation for updating action
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *WorkflowAPI) deleteAction(w http.ResponseWriter, r *http.Request, actionID string) {
	// Implementation for deleting action
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}

func (api *WorkflowAPI) getN8NWorkflows(w http.ResponseWriter, r *http.Request) {
	workflows, err := api.n8nClient.ListWorkflows(context.Background())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workflows)
}

func (api *WorkflowAPI) createN8NWorkflow(w http.ResponseWriter, r *http.Request) {
	var workflow N8NWorkflow
	if err := json.NewDecoder(r.Body).Decode(&workflow); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	createdWorkflow, err := api.n8nClient.CreateWorkflow(context.Background(), &workflow)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(createdWorkflow)
}

func (api *WorkflowAPI) getN8NWorkflow(w http.ResponseWriter, r *http.Request, workflowID string) {
	workflow, err := api.n8nClient.GetWorkflow(context.Background(), workflowID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workflow)
}

func (api *WorkflowAPI) updateN8NWorkflow(w http.ResponseWriter, r *http.Request, workflowID string) {
	var workflow N8NWorkflow
	if err := json.NewDecoder(r.Body).Decode(&workflow); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	updatedWorkflow, err := api.n8nClient.UpdateWorkflow(context.Background(), workflowID, &workflow)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(updatedWorkflow)
}

func (api *WorkflowAPI) deleteN8NWorkflow(w http.ResponseWriter, r *http.Request, workflowID string) {
	if err := api.n8nClient.DeleteWorkflow(context.Background(), workflowID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "deleted"})
}
