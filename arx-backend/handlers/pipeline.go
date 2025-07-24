package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os/exec"
	"time"

	"arx/models"
	"arx/repository"
	"arx/utils"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
)

// PipelineStep represents a step in the integration pipeline
type PipelineStep struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Orchestrator string                 `json:"orchestrator"` // "go" or "python"
	Status       string                 `json:"status"`       // "pending", "running", "completed", "failed"
	StartedAt    *time.Time             `json:"started_at,omitempty"`
	CompletedAt  *time.Time             `json:"completed_at,omitempty"`
	Error        string                 `json:"error,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// PipelineExecution represents a complete pipeline execution
type PipelineExecution struct {
	ID          string         `json:"id"`
	System      string         `json:"system"`
	ObjectType  string         `json:"object_type,omitempty"`
	Status      string         `json:"status"` // "running", "completed", "failed"
	Steps       []PipelineStep `json:"steps"`
	CreatedAt   time.Time      `json:"created_at"`
	CompletedAt *time.Time     `json:"completed_at,omitempty"`
	Error       string         `json:"error,omitempty"`
}

// PipelineConfig holds configuration for pipeline execution
type PipelineConfig struct {
	PythonBridgePath string            `json:"python_bridge_path"`
	SVGXEnginePath   string            `json:"svgx_engine_path"`
	ValidationRules  map[string]string `json:"validation_rules"`
}

// PipelineHandler handles pipeline orchestration
type PipelineHandler struct {
	config PipelineConfig
	repo   *repository.PipelineRepository
}

// NewPipelineHandler creates a new pipeline handler
func NewPipelineHandler(repo *repository.PipelineRepository) *PipelineHandler {
	return &PipelineHandler{
		config: PipelineConfig{
			PythonBridgePath: "svgx_engine/services/pipeline_integration.py",
			SVGXEnginePath:   "svgx_engine",
			ValidationRules: map[string]string{
				"schema":     "validate-schema",
				"symbol":     "validate-symbol",
				"behavior":   "validate-behavior",
				"registry":   "validate-registry",
				"compliance": "validate-compliance",
			},
		},
		repo: repo,
	}
}

// RegisterRoutes registers pipeline routes with the router
func (h *PipelineHandler) RegisterRoutes(r chi.Router) {
	r.Route("/api/pipeline", func(r chi.Router) {
		r.Post("/execute", utils.ToChiHandler(h.ExecutePipeline))
		r.Get("/status/{id}", utils.ToChiHandler(h.GetPipelineStatus))
		r.Post("/validate-schema/{system}", utils.ToChiHandler(h.ValidateSchema))
		r.Post("/validate-symbol/{symbol}", utils.ToChiHandler(h.ValidateSymbol))
		r.Post("/validate-behavior/{system}", utils.ToChiHandler(h.ValidateBehavior))
		r.Get("/executions", utils.ToChiHandler(h.ListExecutions))
		r.Get("/metrics", utils.ToChiHandler(h.GetPipelineMetrics))
		r.Get("/configurations/{system}", utils.ToChiHandler(h.GetConfigurations))
	})
}

// ExecutePipeline handles the main pipeline execution
func (h *PipelineHandler) ExecutePipeline(c *utils.ChiContext) {
	var req models.PipelineRequest

	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	// Validate request
	if req.System == "" {
		c.Writer.Error(http.StatusBadRequest, "System is required")
		return
	}

	// Create execution record
	executionID := uuid.New()
	execution := &models.PipelineExecution{
		ID:         executionID.String(),
		System:     req.System,
		ObjectType: req.ObjectType,
		Status:     "running",
		CreatedAt:  time.Now(),
	}

	// Save to database
	if err := h.repo.CreateExecution(execution); err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create execution record", err.Error())
		return
	}

	// Start pipeline execution in background
	go h.runPipelineExecution(executionID, req)

	response := models.PipelineResponse{
		Success:     true,
		Message:     "Pipeline execution started",
		ExecutionID: executionID.String(),
	}

	c.Writer.JSON(http.StatusAccepted, response)
}

// GetPipelineStatus handles GET /api/pipeline/status/{id}
func (h *PipelineHandler) GetPipelineStatus(c *utils.ChiContext) {
	executionID := c.Reader.Param("id")
	if executionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Execution ID is required")
		return
	}

	execution, err := h.repo.GetExecution(executionID)
	if err != nil {
		c.Writer.Error(http.StatusNotFound, "Execution not found", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, execution)
}

// ListExecutions handles GET /api/pipeline/executions
func (h *PipelineHandler) ListExecutions(c *utils.ChiContext) {
	executions, err := h.repo.ListExecutions()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to list executions", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, executions)
}

// GetPipelineMetrics handles GET /api/pipeline/metrics
func (h *PipelineHandler) GetPipelineMetrics(c *utils.ChiContext) {
	metrics, err := h.repo.GetMetrics()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get metrics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, metrics)
}

// GetConfigurations handles GET /api/pipeline/configurations/{system}
func (h *PipelineHandler) GetConfigurations(c *utils.ChiContext) {
	system := c.Reader.Param("system")
	if system == "" {
		c.Writer.Error(http.StatusBadRequest, "System is required")
		return
	}

	configs, err := h.repo.GetConfigurations(system)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get configurations", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, configs)
}

// ValidateSchema handles POST /api/pipeline/validate-schema/{system}
func (h *PipelineHandler) ValidateSchema(c *utils.ChiContext) {
	system := c.Reader.Param("system")
	if system == "" {
		c.Writer.Error(http.StatusBadRequest, "System is required")
		return
	}

	var req models.ValidationRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := h.executePythonBridge("validate-schema", map[string]string{
		"system": system,
		"schema": req.Data,
	})
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Schema validation failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// ValidateSymbol handles POST /api/pipeline/validate-symbol/{symbol}
func (h *PipelineHandler) ValidateSymbol(c *utils.ChiContext) {
	symbol := c.Reader.Param("symbol")
	if symbol == "" {
		c.Writer.Error(http.StatusBadRequest, "Symbol is required")
		return
	}

	var req models.ValidationRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := h.executePythonBridge("validate-symbol", map[string]string{
		"symbol": symbol,
		"data":   req.Data,
	})
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Symbol validation failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// ValidateBehavior handles POST /api/pipeline/validate-behavior/{system}
func (h *PipelineHandler) ValidateBehavior(c *utils.ChiContext) {
	system := c.Reader.Param("system")
	if system == "" {
		c.Writer.Error(http.StatusBadRequest, "System is required")
		return
	}

	var req models.ValidationRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := h.executePythonBridge("validate-behavior", map[string]string{
		"system": system,
		"data":   req.Data,
	})
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Behavior validation failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// executePythonBridge executes Python bridge operations
func (h *PipelineHandler) executePythonBridge(operation string, params map[string]string) (map[string]interface{}, error) {
	// Convert params to JSON
	paramsJSON, err := json.Marshal(params)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal params: %v", err)
	}

	// Execute Python script
	cmd := exec.Command("python", h.config.PythonBridgePath, operation, string(paramsJSON))
	cmd.Dir = h.config.SVGXEnginePath

	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("python bridge execution failed: %v, output: %s", err, string(output))
	}

	// Parse output
	var result map[string]interface{}
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("failed to parse python output: %v", err)
	}

	return result, nil
}

// runPipelineExecution runs the pipeline execution in background
func (h *PipelineHandler) runPipelineExecution(executionID uuid.UUID, req models.PipelineRequest) {
	// Create default steps
	steps := h.createDefaultSteps(req.System, req.ObjectType)

	// Update execution with steps
	execution := &models.PipelineExecution{
		ID:    executionID.String(),
		Steps: steps,
	}

	if err := h.repo.UpdateExecution(execution); err != nil {
		// Log error but continue execution
		fmt.Printf("Failed to update execution: %v\n", err)
	}

	// Execute each step
	for i := range steps {
		steps[i].Status = "running"
		now := time.Now()
		steps[i].StartedAt = &now

		// Update step status
		if err := h.repo.UpdateExecution(execution); err != nil {
			fmt.Printf("Failed to update step status: %v\n", err)
		}

		// Execute step
		var err error
		switch steps[i].Orchestrator {
		case "go":
			err = h.executeGoStep(&steps[i], execution)
		case "python":
			err = h.executePythonStep(&steps[i], execution)
		default:
			err = fmt.Errorf("unknown orchestrator: %s", steps[i].Orchestrator)
		}

		// Update step completion
		completedAt := time.Now()
		steps[i].CompletedAt = &completedAt
		if err != nil {
			steps[i].Status = "failed"
			steps[i].Error = err.Error()
			execution.Status = "failed"
			execution.Error = err.Error()
		} else {
			steps[i].Status = "completed"
		}

		// Update execution
		if err := h.repo.UpdateExecution(execution); err != nil {
			fmt.Printf("Failed to update execution: %v\n", err)
		}

		// Stop if step failed
		if err != nil {
			return
		}
	}

	// Mark execution as completed
	execution.Status = "completed"
	completedAt := time.Now()
	execution.CompletedAt = &completedAt

	if err := h.repo.UpdateExecution(execution); err != nil {
		fmt.Printf("Failed to mark execution as completed: %v\n", err)
	}
}

// executeGoStep executes a Go step
func (h *PipelineHandler) executeGoStep(step *PipelineStep, execution *models.PipelineExecution) error {
	// Implement Go step execution logic
	// This would typically call Go functions or services
	return nil
}

// executePythonStep executes a Python step
func (h *PipelineHandler) executePythonStep(step *PipelineStep, execution *models.PipelineExecution) error {
	// Execute Python script for the step
	cmd := exec.Command("python", h.config.PythonBridgePath, step.Name)
	cmd.Dir = h.config.SVGXEnginePath

	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("python step execution failed: %v, output: %s", err, string(output))
	}

	return nil
}

// executeDefineSchema executes schema definition step
func (h *PipelineHandler) executeDefineSchema(execution *models.PipelineExecution) error {
	// Execute schema definition
	result, err := h.executePythonBridge("define-schema", map[string]string{
		"system":      execution.System,
		"object_type": execution.ObjectType,
	})
	if err != nil {
		return fmt.Errorf("schema definition failed: %v", err)
	}

	// Update execution metadata
	if execution.Metadata == nil {
		execution.Metadata = make(map[string]interface{})
	}
	execution.Metadata["schema_result"] = result

	return nil
}

// executeUpdateRegistry executes registry update step
func (h *PipelineHandler) executeUpdateRegistry(execution *models.PipelineExecution) error {
	// Execute registry update
	result, err := h.executePythonBridge("update-registry", map[string]string{
		"system":      execution.System,
		"object_type": execution.ObjectType,
	})
	if err != nil {
		return fmt.Errorf("registry update failed: %v", err)
	}

	// Update execution metadata
	if execution.Metadata == nil {
		execution.Metadata = make(map[string]interface{})
	}
	execution.Metadata["registry_result"] = result

	return nil
}

// executeDocumentation executes documentation generation step
func (h *PipelineHandler) executeDocumentation(execution *models.PipelineExecution) error {
	// Execute documentation generation
	result, err := h.executePythonBridge("generate-docs", map[string]string{
		"system":      execution.System,
		"object_type": execution.ObjectType,
	})
	if err != nil {
		return fmt.Errorf("documentation generation failed: %v", err)
	}

	// Update execution metadata
	if execution.Metadata == nil {
		execution.Metadata = make(map[string]interface{})
	}
	execution.Metadata["docs_result"] = result

	return nil
}

// createDefaultSteps creates default pipeline steps
func (h *PipelineHandler) createDefaultSteps(system, objectType string) []PipelineStep {
	steps := []PipelineStep{
		{
			ID:           "1",
			Name:         "validate-schema",
			Description:  "Validate system schema",
			Orchestrator: "python",
			Status:       "pending",
		},
		{
			ID:           "2",
			Name:         "define-schema",
			Description:  "Define system schema",
			Orchestrator: "python",
			Status:       "pending",
		},
		{
			ID:           "3",
			Name:         "update-registry",
			Description:  "Update symbol registry",
			Orchestrator: "python",
			Status:       "pending",
		},
		{
			ID:           "4",
			Name:         "generate-docs",
			Description:  "Generate documentation",
			Orchestrator: "python",
			Status:       "pending",
		},
	}

	return steps
}

// getCurrentUser gets the current user from context
func getCurrentUser(c *utils.ChiContext) *string {
	// Extract user from context
	// This would typically get user from JWT token or session
	user := c.Reader.GetHeader("X-User-ID")
	if user == "" {
		return nil
	}
	return &user
}
