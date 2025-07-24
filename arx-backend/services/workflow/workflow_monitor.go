package workflow

import (
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// WorkflowMetrics represents workflow performance metrics
type WorkflowMetrics struct {
	TotalWorkflows       int       `json:"total_workflows"`
	SuccessfulWorkflows  int       `json:"successful_workflows"`
	FailedWorkflows      int       `json:"failed_workflows"`
	TotalExecutions      int       `json:"total_executions"`
	SuccessfulExecutions int       `json:"successful_executions"`
	FailedExecutions     int       `json:"failed_executions"`
	AverageExecutionTime float64   `json:"average_execution_time"`
	ActiveWorkflows      int       `json:"active_workflows"`
	QueueSize            int       `json:"queue_size"`
	LastUpdated          time.Time `json:"last_updated"`
}

// WorkflowAlert represents a workflow alert
type WorkflowAlert struct {
	AlertID        string                 `json:"alert_id" gorm:"primaryKey"`
	WorkflowID     string                 `json:"workflow_id"`
	ExecutionID    string                 `json:"execution_id"`
	AlertType      string                 `json:"alert_type"`
	Severity       string                 `json:"severity"`
	Message        string                 `json:"message"`
	Details        map[string]interface{} `json:"details" gorm:"type:json"`
	Acknowledged   bool                   `json:"acknowledged"`
	CreatedAt      time.Time              `json:"created_at"`
	AcknowledgedAt *time.Time             `json:"acknowledged_at"`
}

// WorkflowPerformance represents workflow performance data
type WorkflowPerformance struct {
	WorkflowID           string    `json:"workflow_id" gorm:"primaryKey"`
	TotalExecutions      int       `json:"total_executions"`
	SuccessfulExecutions int       `json:"successful_executions"`
	FailedExecutions     int       `json:"failed_executions"`
	AverageDuration      float64   `json:"average_duration"`
	MinDuration          float64   `json:"min_duration"`
	MaxDuration          float64   `json:"max_duration"`
	LastExecuted         time.Time `json:"last_executed"`
	SuccessRate          float64   `json:"success_rate"`
	UpdatedAt            time.Time `json:"updated_at"`
}

// WorkflowMonitor provides monitoring and analytics capabilities
type WorkflowMonitor struct {
	engine      *WorkflowEngine
	db          *gorm.DB
	metrics     *WorkflowMetrics
	alerts      map[string]*WorkflowAlert
	performance map[string]*WorkflowPerformance
	lock        sync.RWMutex
}

// NewWorkflowMonitor creates a new workflow monitor
func NewWorkflowMonitor(engine *WorkflowEngine) *WorkflowMonitor {
	monitor := &WorkflowMonitor{
		engine:      engine,
		db:          engine.db,
		metrics:     &WorkflowMetrics{},
		alerts:      make(map[string]*WorkflowAlert),
		performance: make(map[string]*WorkflowPerformance),
	}

	// Load existing alerts and performance data
	monitor.loadAlerts()
	monitor.loadPerformance()

	// Start monitoring worker
	go monitor.monitoringWorker()

	return monitor
}

// GetMetrics gets current workflow metrics
func (m *WorkflowMonitor) GetMetrics() *WorkflowMetrics {
	m.lock.RLock()
	defer m.lock.RUnlock()

	// Update metrics from engine
	engineMetrics := m.engine.GetMetrics()
	m.metrics.TotalWorkflows = engineMetrics["total_workflows"].(int)
	m.metrics.ActiveWorkflows = engineMetrics["active_executions"].(int)
	m.metrics.TotalExecutions = engineMetrics["total_executions"].(int)
	m.metrics.QueueSize = engineMetrics["queue_size"].(int)
	m.metrics.LastUpdated = time.Now()

	return m.metrics
}

// CreateAlert creates a new workflow alert
func (m *WorkflowMonitor) CreateAlert(workflowID string, executionID string, alertType string, severity string, message string, details map[string]interface{}) (*WorkflowAlert, error) {
	alert := &WorkflowAlert{
		AlertID:      fmt.Sprintf("alert_%d", time.Now().UnixNano()),
		WorkflowID:   workflowID,
		ExecutionID:  executionID,
		AlertType:    alertType,
		Severity:     severity,
		Message:      message,
		Details:      details,
		Acknowledged: false,
		CreatedAt:    time.Now(),
	}

	m.lock.Lock()
	m.alerts[alert.AlertID] = alert
	m.lock.Unlock()

	// Save to database
	if err := m.db.Create(alert).Error; err != nil {
		return nil, fmt.Errorf("failed to save alert: %w", err)
	}

	return alert, nil
}

// AcknowledgeAlert acknowledges a workflow alert
func (m *WorkflowMonitor) AcknowledgeAlert(alertID string) error {
	m.lock.Lock()
	defer m.lock.Unlock()

	alert, exists := m.alerts[alertID]
	if !exists {
		return fmt.Errorf("alert %s not found", alertID)
	}

	alert.Acknowledged = true
	now := time.Now()
	alert.AcknowledgedAt = &now

	// Update in database
	if err := m.db.Save(alert).Error; err != nil {
		return fmt.Errorf("failed to update alert: %w", err)
	}

	return nil
}

// ListAlerts lists all workflow alerts
func (m *WorkflowMonitor) ListAlerts(acknowledged *bool, severity string) ([]map[string]interface{}, error) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	var alerts []map[string]interface{}
	for _, alert := range m.alerts {
		// Apply filters
		if acknowledged != nil && alert.Acknowledged != *acknowledged {
			continue
		}
		if severity != "" && alert.Severity != severity {
			continue
		}

		alerts = append(alerts, map[string]interface{}{
			"alert_id":        alert.AlertID,
			"workflow_id":     alert.WorkflowID,
			"execution_id":    alert.ExecutionID,
			"alert_type":      alert.AlertType,
			"severity":        alert.Severity,
			"message":         alert.Message,
			"details":         alert.Details,
			"acknowledged":    alert.Acknowledged,
			"created_at":      alert.CreatedAt,
			"acknowledged_at": alert.AcknowledgedAt,
		})
	}

	return alerts, nil
}

// GetPerformance gets performance data for a workflow
func (m *WorkflowMonitor) GetPerformance(workflowID string) (*WorkflowPerformance, error) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	performance, exists := m.performance[workflowID]
	if !exists {
		return nil, fmt.Errorf("performance data for workflow %s not found", workflowID)
	}

	return performance, nil
}

// GetAllPerformance gets performance data for all workflows
func (m *WorkflowMonitor) GetAllPerformance() ([]map[string]interface{}, error) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	var performance []map[string]interface{}
	for _, perf := range m.performance {
		performance = append(performance, map[string]interface{}{
			"workflow_id":           perf.WorkflowID,
			"total_executions":      perf.TotalExecutions,
			"successful_executions": perf.SuccessfulExecutions,
			"failed_executions":     perf.FailedExecutions,
			"average_duration":      perf.AverageDuration,
			"min_duration":          perf.MinDuration,
			"max_duration":          perf.MaxDuration,
			"last_executed":         perf.LastExecuted,
			"success_rate":          perf.SuccessRate,
			"updated_at":            perf.UpdatedAt,
		})
	}

	return performance, nil
}

// GenerateReport generates a workflow analytics report
func (m *WorkflowMonitor) GenerateReport(startDate time.Time, endDate time.Time) (map[string]interface{}, error) {
	// Get executions in date range
	var executions []WorkflowExecution
	if err := m.db.Where("start_time BETWEEN ? AND ?", startDate, endDate).Find(&executions).Error; err != nil {
		return nil, fmt.Errorf("failed to get executions: %w", err)
	}

	// Calculate report metrics
	totalExecutions := len(executions)
	successfulExecutions := 0
	failedExecutions := 0
	totalDuration := 0.0
	workflowCounts := make(map[string]int)
	stepCounts := make(map[string]int)

	for _, execution := range executions {
		if execution.Status == StatusCompleted {
			successfulExecutions++
		} else if execution.Status == StatusFailed {
			failedExecutions++
		}

		if execution.EndTime != nil {
			duration := execution.EndTime.Sub(execution.StartTime).Seconds()
			totalDuration += duration
		}

		workflowCounts[execution.WorkflowID]++
	}

	// Get step executions
	var stepExecutions []StepExecution
	if err := m.db.Where("start_time BETWEEN ? AND ?", startDate, endDate).Find(&stepExecutions).Error; err != nil {
		return nil, fmt.Errorf("failed to get step executions: %w", err)
	}

	for _, stepExecution := range stepExecutions {
		stepCounts[stepExecution.StepID]++
	}

	// Calculate averages
	averageDuration := 0.0
	if totalExecutions > 0 {
		averageDuration = totalDuration / float64(totalExecutions)
	}

	successRate := 0.0
	if totalExecutions > 0 {
		successRate = float64(successfulExecutions) / float64(totalExecutions) * 100
	}

	// Generate report
	report := map[string]interface{}{
		"period": map[string]interface{}{
			"start_date": startDate,
			"end_date":   endDate,
		},
		"executions": map[string]interface{}{
			"total":        totalExecutions,
			"successful":   successfulExecutions,
			"failed":       failedExecutions,
			"success_rate": successRate,
		},
		"performance": map[string]interface{}{
			"average_duration": averageDuration,
			"total_duration":   totalDuration,
		},
		"workflows": workflowCounts,
		"steps":     stepCounts,
		"alerts": map[string]interface{}{
			"total": len(m.alerts),
		},
		"generated_at": time.Now(),
	}

	return report, nil
}

// GetTrends gets workflow execution trends
func (m *WorkflowMonitor) GetTrends(days int) (map[string]interface{}, error) {
	endDate := time.Now()
	startDate := endDate.AddDate(0, 0, -days)

	// Get daily execution counts
	var dailyExecutions []struct {
		Date  string `json:"date"`
		Count int    `json:"count"`
	}

	if err := m.db.Raw(`
		SELECT DATE(start_time) as date, COUNT(*) as count 
		FROM workflow_executions 
		WHERE start_time BETWEEN ? AND ? 
		GROUP BY DATE(start_time) 
		ORDER BY date
	`, startDate, endDate).Scan(&dailyExecutions).Error; err != nil {
		return nil, fmt.Errorf("failed to get daily executions: %w", err)
	}

	// Get workflow type distribution
	var workflowTypeCounts []struct {
		WorkflowType string `json:"workflow_type"`
		Count        int    `json:"count"`
	}

	if err := m.db.Raw(`
		SELECT w.workflow_type, COUNT(e.execution_id) as count 
		FROM workflow_executions e 
		JOIN workflow_definitions w ON e.workflow_id = w.workflow_id 
		WHERE e.start_time BETWEEN ? AND ? 
		GROUP BY w.workflow_type
	`, startDate, endDate).Scan(&workflowTypeCounts).Error; err != nil {
		return nil, fmt.Errorf("failed to get workflow type counts: %w", err)
	}

	// Get step type distribution
	var stepTypeCounts []struct {
		StepType string `json:"step_type"`
		Count    int    `json:"count"`
	}

	if err := m.db.Raw(`
		SELECT s.step_type, COUNT(se.step_execution_id) as count 
		FROM step_executions se 
		JOIN workflow_executions e ON se.workflow_execution_id = e.execution_id 
		JOIN workflow_definitions w ON e.workflow_id = w.workflow_id 
		JOIN JSON_TABLE(w.steps, '$[*]' COLUMNS(step_type VARCHAR(50) PATH '$.step_type')) s 
		WHERE se.start_time BETWEEN ? AND ? 
		GROUP BY s.step_type
	`, startDate, endDate).Scan(&stepTypeCounts).Error; err != nil {
		return nil, fmt.Errorf("failed to get step type counts: %w", err)
	}

	trends := map[string]interface{}{
		"period": map[string]interface{}{
			"start_date": startDate,
			"end_date":   endDate,
			"days":       days,
		},
		"daily_executions": dailyExecutions,
		"workflow_types":   workflowTypeCounts,
		"step_types":       stepTypeCounts,
		"generated_at":     time.Now(),
	}

	return trends, nil
}

// GetRecommendations gets workflow optimization recommendations
func (m *WorkflowMonitor) GetRecommendations() ([]map[string]interface{}, error) {
	var recommendations []map[string]interface{}

	// Get slow workflows
	var slowWorkflows []WorkflowPerformance
	if err := m.db.Where("average_duration > ?", 300.0).Find(&slowWorkflows).Error; err != nil {
		return nil, fmt.Errorf("failed to get slow workflows: %w", err)
	}

	for _, workflow := range slowWorkflows {
		recommendations = append(recommendations, map[string]interface{}{
			"type":        "performance",
			"severity":    "medium",
			"workflow_id": workflow.WorkflowID,
			"message":     "Workflow has high average execution time",
			"details": map[string]interface{}{
				"average_duration": workflow.AverageDuration,
				"suggestion":       "Consider optimizing steps or adding parallel execution",
			},
		})
	}

	// Get workflows with low success rate
	var lowSuccessWorkflows []WorkflowPerformance
	if err := m.db.Where("success_rate < ?", 80.0).Find(&lowSuccessWorkflows).Error; err != nil {
		return nil, fmt.Errorf("failed to get low success workflows: %w", err)
	}

	for _, workflow := range lowSuccessWorkflows {
		recommendations = append(recommendations, map[string]interface{}{
			"type":        "reliability",
			"severity":    "high",
			"workflow_id": workflow.WorkflowID,
			"message":     "Workflow has low success rate",
			"details": map[string]interface{}{
				"success_rate": workflow.SuccessRate,
				"suggestion":   "Review error handling and retry logic",
			},
		})
	}

	// Get unacknowledged alerts
	var unacknowledgedAlerts []WorkflowAlert
	if err := m.db.Where("acknowledged = ?", false).Find(&unacknowledgedAlerts).Error; err != nil {
		return nil, fmt.Errorf("failed to get unacknowledged alerts: %w", err)
	}

	for _, alert := range unacknowledgedAlerts {
		recommendations = append(recommendations, map[string]interface{}{
			"type":        "alert",
			"severity":    alert.Severity,
			"workflow_id": alert.WorkflowID,
			"message":     "Unacknowledged alert",
			"details": map[string]interface{}{
				"alert_type": alert.AlertType,
				"message":    alert.Message,
				"suggestion": "Review and acknowledge the alert",
			},
		})
	}

	return recommendations, nil
}

// Helper methods

func (m *WorkflowMonitor) monitoringWorker() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		m.updateMetrics()
		m.checkAlerts()
		m.updatePerformance()
	}
}

func (m *WorkflowMonitor) updateMetrics() {
	m.lock.Lock()
	defer m.lock.Unlock()

	// Update metrics from database
	var totalExecutions, successfulExecutions, failedExecutions int64
	m.db.Model(&WorkflowExecution{}).Count(&totalExecutions)
	m.db.Model(&WorkflowExecution{}).Where("status = ?", StatusCompleted).Count(&successfulExecutions)
	m.db.Model(&WorkflowExecution{}).Where("status = ?", StatusFailed).Count(&failedExecutions)

	m.metrics.TotalExecutions = int(totalExecutions)
	m.metrics.SuccessfulExecutions = int(successfulExecutions)
	m.metrics.FailedExecutions = int(failedExecutions)
	m.metrics.LastUpdated = time.Now()
}

func (m *WorkflowMonitor) checkAlerts() {
	// Check for failed executions and create alerts
	var failedExecutions []WorkflowExecution
	if err := m.db.Where("status = ? AND end_time > ?", StatusFailed, time.Now().Add(-time.Hour)).Find(&failedExecutions).Error; err != nil {
		return
	}

	for _, execution := range failedExecutions {
		// Check if alert already exists
		var existingAlert WorkflowAlert
		if err := m.db.Where("execution_id = ? AND alert_type = ?", execution.ExecutionID, "execution_failed").First(&existingAlert).Error; err == nil {
			continue // Alert already exists
		}

		// Create alert
		alert := &WorkflowAlert{
			AlertID:     fmt.Sprintf("alert_%d", time.Now().UnixNano()),
			WorkflowID:  execution.WorkflowID,
			ExecutionID: execution.ExecutionID,
			AlertType:   "execution_failed",
			Severity:    "high",
			Message:     fmt.Sprintf("Workflow execution %s failed", execution.ExecutionID),
			Details: map[string]interface{}{
				"error": execution.Error,
			},
			Acknowledged: false,
			CreatedAt:    time.Now(),
		}

		m.lock.Lock()
		m.alerts[alert.AlertID] = alert
		m.lock.Unlock()

		m.db.Create(alert)
	}
}

func (m *WorkflowMonitor) updatePerformance() {
	// Update performance data for all workflows
	var workflows []WorkflowDefinition
	if err := m.db.Find(&workflows).Error; err != nil {
		return
	}

	for _, workflow := range workflows {
		var executions []WorkflowExecution
		if err := m.db.Where("workflow_id = ?", workflow.WorkflowID).Find(&executions).Error; err != nil {
			continue
		}

		totalExecutions := len(executions)
		successfulExecutions := 0
		failedExecutions := 0
		totalDuration := 0.0
		minDuration := 0.0
		maxDuration := 0.0
		var lastExecuted time.Time

		for i, execution := range executions {
			if execution.Status == StatusCompleted {
				successfulExecutions++
			} else if execution.Status == StatusFailed {
				failedExecutions++
			}

			if execution.EndTime != nil {
				duration := execution.EndTime.Sub(execution.StartTime).Seconds()
				totalDuration += duration

				if i == 0 || duration < minDuration {
					minDuration = duration
				}
				if duration > maxDuration {
					maxDuration = duration
				}
			}

			if execution.StartTime.After(lastExecuted) {
				lastExecuted = execution.StartTime
			}
		}

		averageDuration := 0.0
		if totalExecutions > 0 {
			averageDuration = totalDuration / float64(totalExecutions)
		}

		successRate := 0.0
		if totalExecutions > 0 {
			successRate = float64(successfulExecutions) / float64(totalExecutions) * 100
		}

		performance := &WorkflowPerformance{
			WorkflowID:           workflow.WorkflowID,
			TotalExecutions:      totalExecutions,
			SuccessfulExecutions: successfulExecutions,
			FailedExecutions:     failedExecutions,
			AverageDuration:      averageDuration,
			MinDuration:          minDuration,
			MaxDuration:          maxDuration,
			LastExecuted:         lastExecuted,
			SuccessRate:          successRate,
			UpdatedAt:            time.Now(),
		}

		m.lock.Lock()
		m.performance[workflow.WorkflowID] = performance
		m.lock.Unlock()

		// Save to database
		m.db.Save(performance)
	}
}

func (m *WorkflowMonitor) loadAlerts() {
	var alerts []WorkflowAlert
	if err := m.db.Find(&alerts).Error; err != nil {
		return
	}

	for i := range alerts {
		m.alerts[alerts[i].AlertID] = &alerts[i]
	}
}

func (m *WorkflowMonitor) loadPerformance() {
	var performance []WorkflowPerformance
	if err := m.db.Find(&performance).Error; err != nil {
		return
	}

	for i := range performance {
		m.performance[performance[i].WorkflowID] = &performance[i]
	}
}
