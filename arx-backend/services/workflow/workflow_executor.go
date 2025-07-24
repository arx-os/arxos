package workflow

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"gorm.io/gorm"
)

// WorkflowExecutor provides step execution capabilities
type WorkflowExecutor struct {
	engine *WorkflowEngine
	db     *gorm.DB
	client *http.Client
	lock   sync.RWMutex
}

// NewWorkflowExecutor creates a new workflow executor
func NewWorkflowExecutor(engine *WorkflowEngine) *WorkflowExecutor {
	return &WorkflowExecutor{
		engine: engine,
		db:     engine.db,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ExecuteStep executes a single workflow step
func (e *WorkflowExecutor) ExecuteStep(step WorkflowStep, context map[string]interface{}, executionID string) (map[string]interface{}, error) {
	stepExecutionID := e.generateStepExecutionID()
	stepExecution := &StepExecution{
		StepExecutionID:     stepExecutionID,
		WorkflowExecutionID: executionID,
		StepID:              step.StepID,
		Status:              StatusRunning,
		StartTime:           time.Now(),
		RetryCount:          0,
	}

	// Save step execution to database
	if err := e.db.Create(stepExecution).Error; err != nil {
		return nil, fmt.Errorf("failed to save step execution: %w", err)
	}

	var result map[string]interface{}
	var err error

	// Execute based on step type
	switch step.StepType {
	case StepValidation:
		result, err = e.executeValidationStep(step, context)
	case StepExport:
		result, err = e.executeExportStep(step, context)
	case StepTransform:
		result, err = e.executeTransformStep(step, context)
	case StepNotify:
		result, err = e.executeNotifyStep(step, context)
	case StepCondition:
		result, err = e.executeConditionStep(step, context)
	case StepLoop:
		result, err = e.executeLoopStep(step, context)
	case StepParallel:
		result, err = e.executeParallelStep(step, context)
	case StepDelay:
		result, err = e.executeDelayStep(step, context)
	case StepAPICall:
		result, err = e.executeAPICallStep(step, context)
	case StepFileOperation:
		result, err = e.executeFileOperationStep(step, context)
	default:
		err = fmt.Errorf("unknown step type: %s", step.StepType)
	}

	// Update step execution
	stepExecution.EndTime = timePtr(time.Now())
	stepExecution.Duration = stepExecution.EndTime.Sub(stepExecution.StartTime).Seconds()

	if err != nil {
		stepExecution.Status = StatusFailed
		errorMsg := err.Error()
		stepExecution.Error = &errorMsg
		result = map[string]interface{}{
			"status": "failed",
			"error":  err.Error(),
		}
	} else {
		stepExecution.Status = StatusCompleted
		stepExecution.Result = result
	}

	// Save step execution
	e.db.Save(stepExecution)

	// Retry logic
	if err != nil && stepExecution.RetryCount < step.RetryCount {
		stepExecution.RetryCount++
		time.Sleep(time.Duration(step.RetryDelay) * time.Second)
		return e.ExecuteStep(step, context, executionID)
	}

	return result, err
}

// executeValidationStep executes a validation step
func (e *WorkflowExecutor) executeValidationStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	service := step.Parameters["service"].(string)
	autoApplyFixes := step.Parameters["auto_apply_fixes"].(bool)

	// Mock validation execution
	// In real implementation, this would call the actual validation service
	validationResult := map[string]interface{}{
		"status":             "success",
		"issues_found":       2,
		"auto_fixes_applied": autoApplyFixes,
		"suggested_fixes":    1,
		"validation_time":    2.5,
		"service":            service,
	}

	return validationResult, nil
}

// executeExportStep executes an export step
func (e *WorkflowExecutor) executeExportStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	formatType := step.Parameters["format"].(string)
	destination := step.Parameters["destination"].(string)

	// Mock export execution
	exportResult := map[string]interface{}{
		"status":      "success",
		"file_path":   fmt.Sprintf("%sexport_%d.%s", destination, time.Now().Unix(), formatType),
		"file_size":   1024,
		"export_time": 1.2,
		"format":      formatType,
	}

	return exportResult, nil
}

// executeTransformStep executes a transform step
func (e *WorkflowExecutor) executeTransformStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	transformations := step.Parameters["transformations"].([]interface{})

	// Mock transformation execution
	transformResult := map[string]interface{}{
		"status":                  "success",
		"records_processed":       100,
		"transformations_applied": len(transformations),
		"processing_time":         0.8,
	}

	return transformResult, nil
}

// executeNotifyStep executes a notification step
func (e *WorkflowExecutor) executeNotifyStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	method := step.Parameters["method"].(string)
	template := step.Parameters["template"].(string)
	recipients := step.Parameters["recipients"].([]interface{})

	// Mock notification execution
	notifyResult := map[string]interface{}{
		"status":     "success",
		"method":     method,
		"recipients": recipients,
		"template":   template,
		"sent_time":  time.Now().Format(time.RFC3339),
	}

	return notifyResult, nil
}

// executeConditionStep executes a condition step
func (e *WorkflowExecutor) executeConditionStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	conditions := step.Parameters["conditions"].([]interface{})

	// Evaluate conditions
	result := true
	for _, condition := range conditions {
		if conditionMap, ok := condition.(map[string]interface{}); ok {
			if !e.engine.evaluateCondition(conditionMap, context) {
				result = false
				break
			}
		}
	}

	return map[string]interface{}{
		"status":               "success",
		"result":               result,
		"conditions_evaluated": len(conditions),
	}, nil
}

// executeLoopStep executes a loop step
func (e *WorkflowExecutor) executeLoopStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	items := step.Parameters["items"].([]interface{})
	maxIterations := int(step.Parameters["max_iterations"].(float64))

	results := []map[string]interface{}{}
	for i, item := range items {
		if i >= maxIterations {
			break
		}

		// Execute loop body
		loopResult := map[string]interface{}{
			"iteration": i + 1,
			"item":      item,
			"result":    fmt.Sprintf("processed_%v", item),
		}
		results = append(results, loopResult)
	}

	return map[string]interface{}{
		"status":     "success",
		"iterations": len(results),
		"results":    results,
	}, nil
}

// executeParallelStep executes a parallel step
func (e *WorkflowExecutor) executeParallelStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	subSteps := step.Parameters["steps"].([]interface{})

	// Execute sub-steps in parallel
	var wg sync.WaitGroup
	results := make([]map[string]interface{}, len(subSteps))
	errors := make([]error, len(subSteps))

	for i, subStepData := range subSteps {
		wg.Add(1)
		go func(index int, subStep interface{}) {
			defer wg.Done()

			if subStepMap, ok := subStep.(map[string]interface{}); ok {
				// Create a temporary step for execution
				tempStep := WorkflowStep{
					StepID:     fmt.Sprintf("parallel_%d", index),
					Name:       subStepMap["name"].(string),
					StepType:   StepType(subStepMap["step_type"].(string)),
					Parameters: subStepMap["parameters"].(map[string]interface{}),
				}

				result, err := e.ExecuteStep(tempStep, context, "parallel")
				results[index] = result
				errors[index] = err
			}
		}(i, subStepData)
	}

	wg.Wait()

	// Check for errors
	for _, err := range errors {
		if err != nil {
			return map[string]interface{}{
				"status": "failed",
				"error":  err.Error(),
			}, err
		}
	}

	return map[string]interface{}{
		"status":              "success",
		"parallel_executions": len(results),
		"results":             results,
	}, nil
}

// executeDelayStep executes a delay step
func (e *WorkflowExecutor) executeDelayStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	delaySeconds := int(step.Parameters["delay_seconds"].(float64))

	time.Sleep(time.Duration(delaySeconds) * time.Second)

	return map[string]interface{}{
		"status":        "success",
		"delay_seconds": delaySeconds,
		"completed_at":  time.Now().Format(time.RFC3339),
	}, nil
}

// executeAPICallStep executes an API call step
func (e *WorkflowExecutor) executeAPICallStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	endpoint := step.Parameters["endpoint"].(string)
	method := step.Parameters["method"].(string)
	data := step.Parameters["data"].(map[string]interface{})

	// Mock API call
	apiResult := map[string]interface{}{
		"status":        "success",
		"endpoint":      endpoint,
		"method":        method,
		"response_code": 200,
		"response_time": 0.5,
		"data":          data,
	}

	return apiResult, nil
}

// executeFileOperationStep executes a file operation step
func (e *WorkflowExecutor) executeFileOperationStep(step WorkflowStep, context map[string]interface{}) (map[string]interface{}, error) {
	operation := step.Parameters["operation"].(string)
	filePath := step.Parameters["file_path"].(string)

	var result map[string]interface{}
	var err error

	switch operation {
	case "read":
		result, err = e.executeFileRead(filePath)
	case "write":
		result, err = e.executeFileWrite(filePath, step.Parameters)
	case "delete":
		result, err = e.executeFileDelete(filePath)
	case "copy":
		result, err = e.executeFileCopy(filePath, step.Parameters)
	case "move":
		result, err = e.executeFileMove(filePath, step.Parameters)
	default:
		err = fmt.Errorf("unknown file operation: %s", operation)
	}

	if err != nil {
		return map[string]interface{}{
			"status": "failed",
			"error":  err.Error(),
		}, err
	}

	return result, nil
}

// executeFileRead executes a file read operation
func (e *WorkflowExecutor) executeFileRead(filePath string) (map[string]interface{}, error) {
	// Mock file read
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	return map[string]interface{}{
		"status":    "success",
		"operation": "read",
		"file_path": filePath,
		"file_size": fileInfo.Size(),
		"read_time": 0.1,
		"exists":    true,
	}, nil
}

// executeFileWrite executes a file write operation
func (e *WorkflowExecutor) executeFileWrite(filePath string, parameters map[string]interface{}) (map[string]interface{}, error) {
	// Mock file write
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create directory: %w", err)
	}

	// Create a mock file
	file, err := os.Create(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Write mock content
	content := parameters["content"].(string)
	if _, err := file.WriteString(content); err != nil {
		return nil, fmt.Errorf("failed to write file: %w", err)
	}

	return map[string]interface{}{
		"status":     "success",
		"operation":  "write",
		"file_path":  filePath,
		"file_size":  len(content),
		"write_time": 0.1,
		"created":    true,
	}, nil
}

// executeFileDelete executes a file delete operation
func (e *WorkflowExecutor) executeFileDelete(filePath string) (map[string]interface{}, error) {
	// Mock file delete
	if err := os.Remove(filePath); err != nil {
		return nil, fmt.Errorf("failed to delete file: %w", err)
	}

	return map[string]interface{}{
		"status":      "success",
		"operation":   "delete",
		"file_path":   filePath,
		"delete_time": 0.1,
		"deleted":     true,
	}, nil
}

// executeFileCopy executes a file copy operation
func (e *WorkflowExecutor) executeFileCopy(filePath string, parameters map[string]interface{}) (map[string]interface{}, error) {
	destination := parameters["destination"].(string)

	// Mock file copy
	if err := copyFile(filePath, destination); err != nil {
		return nil, fmt.Errorf("failed to copy file: %w", err)
	}

	return map[string]interface{}{
		"status":      "success",
		"operation":   "copy",
		"source_path": filePath,
		"destination": destination,
		"copy_time":   0.2,
		"copied":      true,
	}, nil
}

// executeFileMove executes a file move operation
func (e *WorkflowExecutor) executeFileMove(filePath string, parameters map[string]interface{}) (map[string]interface{}, error) {
	destination := parameters["destination"].(string)

	// Mock file move
	if err := os.Rename(filePath, destination); err != nil {
		return nil, fmt.Errorf("failed to move file: %w", err)
	}

	return map[string]interface{}{
		"status":      "success",
		"operation":   "move",
		"source_path": filePath,
		"destination": destination,
		"move_time":   0.1,
		"moved":       true,
	}, nil
}

// Helper methods

func (e *WorkflowExecutor) generateStepExecutionID() string {
	return fmt.Sprintf("step_%d", time.Now().UnixNano())
}

func timePtr(t time.Time) *time.Time {
	return &t
}

func copyFile(src, dst string) error {
	// Simplified file copy implementation
	// In practice, you'd use io.Copy for proper file copying
	return nil
}
