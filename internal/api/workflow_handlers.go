package api

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/arx-os/arxos/internal/common"
	"github.com/arx-os/arxos/internal/services"
	"github.com/go-chi/chi/v5"
)

// WorkflowHandlers handles Workflow tier API endpoints
type WorkflowHandlers struct {
	workflowService    *services.WorkflowService
	builderIntegration *services.WorkflowBuilderIntegration
}

// NewWorkflowHandlers creates a new WorkflowHandlers instance
func NewWorkflowHandlers(workflowService *services.WorkflowService, builderIntegration *services.WorkflowBuilderIntegration) *WorkflowHandlers {
	return &WorkflowHandlers{
		workflowService:    workflowService,
		builderIntegration: builderIntegration,
	}
}

// RegisterWorkflowRoutes registers Workflow tier API routes
func (wh *WorkflowHandlers) RegisterWorkflowRoutes(r chi.Router) {
	r.Route("/api/v1/workflow", func(r chi.Router) {
		// Workflow management
		r.Get("/workflows", wh.handleListWorkflows)
		r.Post("/workflows", wh.handleCreateWorkflow)
		r.Get("/workflows/{id}", wh.handleGetWorkflow)
		r.Put("/workflows/{id}", wh.handleUpdateWorkflow)
		r.Delete("/workflows/{id}", wh.handleDeleteWorkflow)
		r.Post("/workflows/{id}/activate", wh.handleActivateWorkflow)
		r.Post("/workflows/{id}/deactivate", wh.handleDeactivateWorkflow)

		// Workflow execution
		r.Post("/workflows/{id}/execute", wh.handleExecuteWorkflow)
		r.Get("/executions/{id}", wh.handleGetExecution)
		r.Get("/workflows/{id}/executions", wh.handleListExecutions)

		// Workflow builder integration
		r.Get("/templates", wh.handleGetTemplates)
		r.Post("/templates/{id}/create", wh.handleCreateFromTemplate)
		r.Post("/validate", wh.handleValidateWorkflow)

		// Maintenance automation
		r.Get("/maintenance/schedules", wh.handleGetMaintenanceSchedules)
		r.Post("/maintenance/work-orders", wh.handleCreateWorkOrders)
		r.Post("/maintenance/execute", wh.handleExecuteMaintenance)
	})
}

// Workflow management handlers

func (wh *WorkflowHandlers) handleListWorkflows(w http.ResponseWriter, r *http.Request) {
	userID := common.GetUserIDFromContextSafe(r.Context()) // Get from context/auth

	workflows, err := wh.workflowService.ListWorkflows(r.Context(), userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workflows)
}

func (wh *WorkflowHandlers) handleCreateWorkflow(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name        string                 `json:"name"`
		Description string                 `json:"description"`
		Definition  map[string]interface{} `json:"definition"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	ecosystemReq := struct {
		Name        string                 `json:"name"`
		Description string                 `json:"description"`
		Definition  map[string]interface{} `json:"definition"`
	}{
		Name:        req.Name,
		Description: req.Description,
		Definition:  req.Definition,
	}

	workflow, err := wh.workflowService.CreateWorkflow(r.Context(), ecosystemReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(workflow)
}

func (wh *WorkflowHandlers) handleGetWorkflow(w http.ResponseWriter, r *http.Request) {
	workflowID := chi.URLParam(r, "id")

	workflow, err := wh.workflowService.GetWorkflow(r.Context(), workflowID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workflow)
}

func (wh *WorkflowHandlers) handleUpdateWorkflow(w http.ResponseWriter, r *http.Request) {
	workflowID := chi.URLParam(r, "id")

	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	workflow, err := wh.workflowService.UpdateWorkflow(r.Context(), workflowID, updates)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(workflow)
}

func (wh *WorkflowHandlers) handleDeleteWorkflow(w http.ResponseWriter, r *http.Request) {
	workflowID := chi.URLParam(r, "id")

	if err := wh.workflowService.DeleteWorkflow(r.Context(), workflowID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

func (wh *WorkflowHandlers) handleActivateWorkflow(w http.ResponseWriter, r *http.Request) {
	workflowID := chi.URLParam(r, "id")

	if err := wh.workflowService.ActivateWorkflow(r.Context(), workflowID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func (wh *WorkflowHandlers) handleDeactivateWorkflow(w http.ResponseWriter, r *http.Request) {
	workflowID := chi.URLParam(r, "id")

	if err := wh.workflowService.DeactivateWorkflow(r.Context(), workflowID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

// Workflow execution handlers

func (wh *WorkflowHandlers) handleExecuteWorkflow(w http.ResponseWriter, r *http.Request) {
	workflowID := chi.URLParam(r, "id")

	var input map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	result, err := wh.workflowService.ExecuteWorkflow(r.Context(), workflowID, input)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (wh *WorkflowHandlers) handleGetExecution(w http.ResponseWriter, r *http.Request) {
	executionID := chi.URLParam(r, "id")

	status, err := wh.workflowService.GetWorkflowStatus(r.Context(), executionID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

func (wh *WorkflowHandlers) handleListExecutions(w http.ResponseWriter, r *http.Request) {
	workflowID := chi.URLParam(r, "id")
	limitStr := r.URL.Query().Get("limit")

	limit := 20
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		}
	}

	executions, err := wh.workflowService.ListWorkflowExecutions(r.Context(), workflowID, limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(executions)
}

// Workflow builder integration handlers

func (wh *WorkflowHandlers) handleGetTemplates(w http.ResponseWriter, r *http.Request) {
	templates, err := wh.builderIntegration.GetWorkflowTemplates(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(templates)
}

func (wh *WorkflowHandlers) handleCreateFromTemplate(w http.ResponseWriter, r *http.Request) {
	templateID := chi.URLParam(r, "id")

	var req struct {
		Name        string `json:"name"`
		Description string `json:"description"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	result, err := wh.builderIntegration.CreateWorkflowFromTemplate(r.Context(), templateID, req.Name, req.Description)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(result)
}

func (wh *WorkflowHandlers) handleValidateWorkflow(w http.ResponseWriter, r *http.Request) {
	var definition services.WorkflowBuilderDefinition
	if err := json.NewDecoder(r.Body).Decode(&definition); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := wh.builderIntegration.ValidateWorkflowDefinition(r.Context(), definition)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "valid"})
}

// Maintenance automation handlers

func (wh *WorkflowHandlers) handleGetMaintenanceSchedules(w http.ResponseWriter, r *http.Request) {
	userID := common.GetUserIDFromContextSafe(r.Context()) // Get from context/auth

	schedules, err := wh.workflowService.GetCMMCService().ListMaintenanceSchedules(r.Context(), userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(schedules)
}

func (wh *WorkflowHandlers) handleCreateWorkOrders(w http.ResponseWriter, r *http.Request) {
	var schedules []map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&schedules); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Create work orders for each schedule
	var workOrders []map[string]interface{}
	for _, schedule := range schedules {
		// TODO: Implement work order creation logic
		workOrder := map[string]interface{}{
			"schedule_id": schedule["id"],
			"status":      "created",
			"created_at":  "now",
		}
		workOrders = append(workOrders, workOrder)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"count":       len(workOrders),
		"work_orders": workOrders,
	})
}

func (wh *WorkflowHandlers) handleExecuteMaintenance(w http.ResponseWriter, r *http.Request) {
	var req struct {
		ScheduleID string                   `json:"schedule_id"`
		Tasks      []map[string]interface{} `json:"tasks"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Execute maintenance using CMMS service
	execution, err := wh.workflowService.GetCMMCService().ExecuteMaintenanceSchedule(r.Context(), req.ScheduleID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(execution)
}
