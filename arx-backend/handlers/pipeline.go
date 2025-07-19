package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"arxos/arx-backend/models"
	"arxos/arx-backend/repository"
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
func (h *PipelineHandler) RegisterRoutes(r *gin.RouterGroup) {
	pipeline := r.Group("/pipeline")
	{
		pipeline.POST("/execute", h.ExecutePipeline)
		pipeline.GET("/status/:id", h.GetPipelineStatus)
		pipeline.POST("/validate-schema/:system", h.ValidateSchema)
		pipeline.POST("/validate-symbol/:symbol", h.ValidateSymbol)
		pipeline.POST("/validate-behavior/:system", h.ValidateBehavior)
		pipeline.GET("/executions", h.ListExecutions)
		pipeline.GET("/metrics", h.GetPipelineMetrics)
		pipeline.GET("/configurations/:system", h.GetConfigurations)
	}
}

// ExecutePipeline handles the main pipeline execution
func (h *PipelineHandler) ExecutePipeline(c *gin.Context) {
	var req models.PipelineRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.PipelineResponse{
			Success:   false,
			Message:   "Invalid request format",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	// Create pipeline execution in database
	execution := &models.PipelineExecution{
		System:     req.System,
		ObjectType: req.ObjectType,
		Status:     "pending",
		CreatedBy:  getCurrentUser(c),
	}

	if err := h.repo.CreateExecution(c.Request.Context(), execution); err != nil {
		c.JSON(http.StatusInternalServerError, models.PipelineResponse{
			Success:   false,
			Message:   "Failed to create pipeline execution",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	// Execute pipeline steps asynchronously
	go h.runPipelineExecution(execution.ID, req)

	c.JSON(http.StatusAccepted, models.PipelineResponse{
		Success:     true,
		ExecutionID: &execution.ID,
		Message:     "Pipeline execution started",
		Status:      "pending",
		Timestamp:   time.Now(),
	})
}

// GetPipelineStatus returns the status of a pipeline execution
func (h *PipelineHandler) GetPipelineStatus(c *gin.Context) {
	executionIDStr := c.Param("id")
	executionID, err := uuid.Parse(executionIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.PipelineResponse{
			Success:   false,
			Message:   "Invalid execution ID",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	execution, err := h.repo.GetExecution(c.Request.Context(), executionID)
	if err != nil {
		c.JSON(http.StatusNotFound, models.PipelineResponse{
			Success:   false,
			Message:   "Pipeline execution not found",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	c.JSON(http.StatusOK, models.PipelineResponse{
		Success:     true,
		ExecutionID: &execution.ID,
		Message:     "Pipeline status retrieved",
		Status:      execution.Status,
		Metadata: map[string]interface{}{
			"system":       execution.System,
			"object_type":  execution.ObjectType,
			"created_at":   execution.CreatedAt,
			"completed_at": execution.CompletedAt,
			"error":        execution.ErrorMessage,
			"steps":        execution.Steps,
		},
		Timestamp: time.Now(),
	})
}

// ListExecutions returns a list of pipeline executions
func (h *PipelineHandler) ListExecutions(c *gin.Context) {
	system := c.Query("system")
	status := c.Query("status")
	limit := 50 // Default limit
	offset := 0 // Default offset

	executions, err := h.repo.ListExecutions(c.Request.Context(), &system, &status, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.PipelineResponse{
			Success:   false,
			Message:   "Failed to retrieve pipeline executions",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success":    true,
		"executions": executions,
		"timestamp":  time.Now(),
	})
}

// GetPipelineMetrics returns pipeline metrics
func (h *PipelineHandler) GetPipelineMetrics(c *gin.Context) {
	stats, err := h.repo.GetExecutionStats(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.PipelineResponse{
			Success:   false,
			Message:   "Failed to retrieve pipeline metrics",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success":   true,
		"metrics":   stats,
		"timestamp": time.Now(),
	})
}

// GetConfigurations returns pipeline configurations for a system
func (h *PipelineHandler) GetConfigurations(c *gin.Context) {
	system := c.Param("system")

	configs, err := h.repo.ListConfigurations(c.Request.Context(), system)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.PipelineResponse{
			Success:   false,
			Message:   "Failed to retrieve pipeline configurations",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success":        true,
		"system":         system,
		"configurations": configs,
		"timestamp":      time.Now(),
	})
}

// ValidateSchema validates a system schema
func (h *PipelineHandler) ValidateSchema(c *gin.Context) {
	system := c.Param("system")

	result, err := h.executePythonBridge("validate-schema", map[string]string{
		"system": system,
	})

	if err != nil {
		c.JSON(http.StatusBadRequest, models.PipelineValidationResponse{
			Success:   false,
			Message:   "Schema validation failed",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	c.JSON(http.StatusOK, models.PipelineValidationResponse{
		Success:   true,
		Message:   "Schema validation completed",
		Details:   result,
		Timestamp: time.Now(),
	})
}

// ValidateSymbol validates a symbol
func (h *PipelineHandler) ValidateSymbol(c *gin.Context) {
	symbol := c.Param("symbol")

	result, err := h.executePythonBridge("validate-symbol", map[string]string{
		"symbol": symbol,
	})

	if err != nil {
		c.JSON(http.StatusBadRequest, models.PipelineValidationResponse{
			Success:   false,
			Message:   "Symbol validation failed",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	c.JSON(http.StatusOK, models.PipelineValidationResponse{
		Success:   true,
		Message:   "Symbol validation completed",
		Details:   result,
		Timestamp: time.Now(),
	})
}

// ValidateBehavior validates behavior profiles
func (h *PipelineHandler) ValidateBehavior(c *gin.Context) {
	system := c.Param("system")

	result, err := h.executePythonBridge("validate-behavior", map[string]string{
		"system": system,
	})

	if err != nil {
		c.JSON(http.StatusBadRequest, models.PipelineValidationResponse{
			Success:   false,
			Message:   "Behavior validation failed",
			Error:     &err.Error(),
			Timestamp: time.Now(),
		})
		return
	}

	c.JSON(http.StatusOK, models.PipelineValidationResponse{
		Success:   true,
		Message:   "Behavior validation completed",
		Details:   result,
		Timestamp: time.Now(),
	})
}

// executePythonBridge executes Python bridge operations
func (h *PipelineHandler) executePythonBridge(operation string, params map[string]string) (map[string]interface{}, error) {
	// Convert params to JSON
	paramsJSON, err := json.Marshal(params)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal params: %v", err)
	}

	// Execute Python bridge
	cmd := exec.Command("python", h.config.PythonBridgePath, "--operation", operation, "--params", string(paramsJSON))
	cmd.Dir = "svgx_engine"

	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("python bridge execution failed: %v, output: %s", err, string(output))
	}

	// Parse response
	var result map[string]interface{}
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("failed to parse python bridge response: %v", err)
	}

	return result, nil
}

// runPipelineExecution runs the complete pipeline execution
func (h *PipelineHandler) runPipelineExecution(executionID uuid.UUID, req models.PipelineRequest) {
	ctx := context.Background()

	// Update execution status to running
	execution, err := h.repo.GetExecution(ctx, executionID)
	if err != nil {
		return
	}

	now := time.Now()
	execution.Status = "running"
	execution.StartedAt = &now
	h.repo.UpdateExecution(ctx, execution)

	// Create pipeline steps
	steps := h.createDefaultSteps(req.System, req.ObjectType)

	for i, step := range steps {
		// Create step in database
		dbStep := &models.PipelineStep{
			ExecutionID:  executionID,
			StepName:     step.ID,
			StepOrder:    i + 1,
			Orchestrator: step.Orchestrator,
			Status:       "pending",
		}

		if err := h.repo.CreateStep(ctx, dbStep); err != nil {
			continue
		}

		// Update step status to running
		stepStarted := time.Now()
		dbStep.Status = "running"
		dbStep.StartedAt = &stepStarted
		h.repo.UpdateStep(ctx, dbStep)

		// Execute step based on orchestrator
		var stepErr error
		if step.Orchestrator == "go" {
			stepErr = h.executeGoStep(&step, execution)
		} else {
			stepErr = h.executePythonStep(&step, execution)
		}

		// Update step status
		stepCompleted := time.Now()
		if stepErr != nil {
			dbStep.Status = "failed"
			errorMsg := stepErr.Error()
			dbStep.ErrorMessage = &errorMsg
		} else {
			dbStep.Status = "completed"
		}
		dbStep.CompletedAt = &stepCompleted
		h.repo.UpdateStep(ctx, dbStep)

		if stepErr != nil {
			// Update execution status to failed
			execution.Status = "failed"
			errorMsg := stepErr.Error()
			execution.ErrorMessage = &errorMsg
			h.repo.UpdateExecution(ctx, execution)
			return
		}
	}

	// Update execution status to completed
	execution.Status = "completed"
	executionCompleted := time.Now()
	execution.CompletedAt = &executionCompleted
	h.repo.UpdateExecution(ctx, execution)
}

// executeGoStep executes a Go-orchestrated step
func (h *PipelineHandler) executeGoStep(step *PipelineStep, execution *models.PipelineExecution) error {
	switch step.ID {
	case "define-schema":
		return h.executeDefineSchema(execution)
	case "update-registry":
		return h.executeUpdateRegistry(execution)
	case "documentation":
		return h.executeDocumentation(execution)
	default:
		return fmt.Errorf("unknown Go step: %s", step.ID)
	}
}

// executePythonStep executes a Python-orchestrated step
func (h *PipelineHandler) executePythonStep(step *PipelineStep, execution *models.PipelineExecution) error {
	params := map[string]string{
		"system":      execution.System,
		"object_type": execution.ObjectType,
		"step":        step.ID,
	}

	_, err := h.executePythonBridge(step.ID, params)
	return err
}

// executeDefineSchema executes the schema definition step
func (h *PipelineHandler) executeDefineSchema(execution *models.PipelineExecution) error {
	// Create schema directory if it doesn't exist
	schemaDir := filepath.Join("schemas", execution.System)
	if err := os.MkdirAll(schemaDir, 0755); err != nil {
		return fmt.Errorf("failed to create schema directory: %v", err)
	}

	// Create basic schema file
	schemaFile := filepath.Join(schemaDir, "schema.json")
	schema := map[string]interface{}{
		"system": execution.System,
		"objects": map[string]interface{}{
			"default": map[string]interface{}{
				"properties":       map[string]interface{}{},
				"relationships":    map[string]interface{}{},
				"behavior_profile": "default",
			},
		},
		"created_at": time.Now().Format(time.RFC3339),
	}

	schemaData, err := json.MarshalIndent(schema, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal schema: %v", err)
	}

	if err := os.WriteFile(schemaFile, schemaData, 0644); err != nil {
		return fmt.Errorf("failed to write schema file: %v", err)
	}

	return nil
}

// executeUpdateRegistry executes the registry update step
func (h *PipelineHandler) executeUpdateRegistry(execution *models.PipelineExecution) error {
	// Update symbol index
	indexFile := "symbol_index.json"
	var index map[string]interface{}

	if data, err := os.ReadFile(indexFile); err == nil {
		if err := json.Unmarshal(data, &index); err != nil {
			return fmt.Errorf("failed to parse symbol index: %v", err)
		}
	} else {
		index = make(map[string]interface{})
	}

	// Add system to index
	index[execution.System] = map[string]interface{}{
		"added_at": time.Now().Format(time.RFC3339),
		"status":   "active",
	}

	indexData, err := json.MarshalIndent(index, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal index: %v", err)
	}

	if err := os.WriteFile(indexFile, indexData, 0644); err != nil {
		return fmt.Errorf("failed to write index file: %v", err)
	}

	return nil
}

// executeDocumentation executes the documentation step
func (h *PipelineHandler) executeDocumentation(execution *models.PipelineExecution) error {
	// Create documentation directory
	docsDir := filepath.Join("docs", "systems", execution.System)
	if err := os.MkdirAll(docsDir, 0755); err != nil {
		return fmt.Errorf("failed to create docs directory: %v", err)
	}

	// Create basic documentation
	docFile := filepath.Join(docsDir, "README.md")
	docContent := fmt.Sprintf(`# %s System

## Overview
This system was integrated via the Arxos pipeline.

## Objects
- Default object type

## Behavior Profiles
- Default behavior profile

## Integration Date
%s

## Status
Active
`, strings.Title(execution.System), time.Now().Format("2006-01-02"))

	if err := os.WriteFile(docFile, []byte(docContent), 0644); err != nil {
		return fmt.Errorf("failed to write documentation: %v", err)
	}

	return nil
}

// createDefaultSteps creates the default pipeline steps
func (h *PipelineHandler) createDefaultSteps(system, objectType string) []PipelineStep {
	return []PipelineStep{
		{
			ID:           "define-schema",
			Name:         "Define Schema",
			Description:  "Add or extend the BIM object schema",
			Orchestrator: "go",
			Status:       "pending",
		},
		{
			ID:           "add-symbols",
			Name:         "Add Symbols",
			Description:  "Create or update SVGX symbols",
			Orchestrator: "python",
			Status:       "pending",
		},
		{
			ID:           "implement-behavior",
			Name:         "Implement Behavior Profiles",
			Description:  "Add programmable behavior for objects",
			Orchestrator: "python",
			Status:       "pending",
		},
		{
			ID:           "update-registry",
			Name:         "Update Registry & Index",
			Description:  "Make system discoverable",
			Orchestrator: "go",
			Status:       "pending",
		},
		{
			ID:           "documentation",
			Name:         "Documentation & Test Coverage",
			Description:  "Add documentation and tests",
			Orchestrator: "go",
			Status:       "pending",
		},
		{
			ID:           "compliance",
			Name:         "Enterprise Compliance Validation",
			Description:  "Ensure enterprise-grade standards",
			Orchestrator: "python",
			Status:       "pending",
		},
	}
}

// getCurrentUser gets the current user from the context
func getCurrentUser(c *gin.Context) *string {
	// In a real implementation, this would extract the user from the JWT token
	// For now, return a default value
	user := "pipeline-system"
	return &user
}
