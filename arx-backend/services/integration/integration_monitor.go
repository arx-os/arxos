package integration

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// MonitorStatus represents the status of monitoring
type MonitorStatus string

const (
	MonitorStatusHealthy  MonitorStatus = "healthy"
	MonitorStatusWarning  MonitorStatus = "warning"
	MonitorStatusCritical MonitorStatus = "critical"
	MonitorStatusOffline  MonitorStatus = "offline"
)

// AlertLevel represents the level of an alert
type AlertLevel string

const (
	AlertLevelInfo     AlertLevel = "info"
	AlertLevelWarning  AlertLevel = "warning"
	AlertLevelCritical AlertLevel = "critical"
)

// HealthCheck represents a health check result
type HealthCheck struct {
	ID            string          `json:"id" gorm:"primaryKey"`
	IntegrationID string          `json:"integration_id"`
	Status        MonitorStatus   `json:"status"`
	ResponseTime  float64         `json:"response_time"`
	ErrorCount    int             `json:"error_count"`
	SuccessCount  int             `json:"success_count"`
	LastCheck     time.Time       `json:"last_check"`
	NextCheck     time.Time       `json:"next_check"`
	Details       json.RawMessage `json:"details"`
	CreatedAt     time.Time       `json:"created_at"`
	UpdatedAt     time.Time       `json:"updated_at"`
}

// IntegrationAlert represents an integration alert
type IntegrationAlert struct {
	ID             string          `json:"id" gorm:"primaryKey"`
	IntegrationID  string          `json:"integration_id"`
	AlertLevel     AlertLevel      `json:"alert_level"`
	Title          string          `json:"title"`
	Message        string          `json:"message"`
	Details        json.RawMessage `json:"details"`
	IsAcknowledged bool            `json:"is_acknowledged"`
	IsResolved     bool            `json:"is_resolved"`
	AcknowledgedAt *time.Time      `json:"acknowledged_at"`
	ResolvedAt     *time.Time      `json:"resolved_at"`
	CreatedAt      time.Time       `json:"created_at"`
	UpdatedAt      time.Time       `json:"updated_at"`
}

// MonitorConfig represents monitoring configuration
type MonitorConfig struct {
	HealthCheckInterval  time.Duration `json:"health_check_interval"`
	AlertThreshold       int           `json:"alert_threshold"`
	WarningThreshold     int           `json:"warning_threshold"`
	MaxResponseTime      float64       `json:"max_response_time"`
	EnableAutoRecovery   bool          `json:"enable_auto_recovery"`
	AutoRecoveryAttempts int           `json:"auto_recovery_attempts"`
	EnableNotifications  bool          `json:"enable_notifications"`
	NotificationChannels []string      `json:"notification_channels"`
	EnableMetrics        bool          `json:"enable_metrics"`
	MetricsRetentionDays int           `json:"metrics_retention_days"`
}

// IntegrationMonitor provides monitoring and alerting for integrations
type IntegrationMonitor struct {
	db           *gorm.DB
	mu           sync.RWMutex
	manager      *IntegrationManager
	healthChecks map[string]*HealthCheck
	alerts       map[string]*IntegrationAlert
	config       *MonitorConfig
	stopChan     chan struct{}
	isRunning    bool
}

// NewIntegrationMonitor creates a new integration monitor
func NewIntegrationMonitor(db *gorm.DB, manager *IntegrationManager, config *MonitorConfig) *IntegrationMonitor {
	if config == nil {
		config = &MonitorConfig{
			HealthCheckInterval:  2 * time.Minute,
			AlertThreshold:       5,
			WarningThreshold:     3,
			MaxResponseTime:      30.0,
			EnableAutoRecovery:   true,
			AutoRecoveryAttempts: 3,
			EnableNotifications:  true,
			NotificationChannels: []string{"email", "slack"},
			EnableMetrics:        true,
			MetricsRetentionDays: 30,
		}
	}

	return &IntegrationMonitor{
		db:           db,
		manager:      manager,
		healthChecks: make(map[string]*HealthCheck),
		alerts:       make(map[string]*IntegrationAlert),
		config:       config,
		stopChan:     make(chan struct{}),
	}
}

// StartMonitoring starts the monitoring service
func (im *IntegrationMonitor) StartMonitoring(ctx context.Context) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if im.isRunning {
		return fmt.Errorf("monitoring is already running")
	}

	im.isRunning = true
	go im.monitoringLoop(ctx)

	return nil
}

// StopMonitoring stops the monitoring service
func (im *IntegrationMonitor) StopMonitoring() {
	im.mu.Lock()
	defer im.mu.Unlock()

	if !im.isRunning {
		return
	}

	im.isRunning = false
	close(im.stopChan)
}

// GetHealthStatus gets the health status of an integration
func (im *IntegrationMonitor) GetHealthStatus(ctx context.Context, integrationID string) (*HealthCheck, error) {
	var healthCheck HealthCheck
	if err := im.db.WithContext(ctx).Where("integration_id = ?", integrationID).First(&healthCheck).Error; err != nil {
		return nil, fmt.Errorf("health check not found: %w", err)
	}
	return &healthCheck, nil
}

// GetAllHealthStatuses gets health statuses for all integrations
func (im *IntegrationMonitor) GetAllHealthStatuses(ctx context.Context) ([]HealthCheck, error) {
	var healthChecks []HealthCheck
	if err := im.db.WithContext(ctx).Find(&healthChecks).Error; err != nil {
		return nil, fmt.Errorf("failed to get health checks: %w", err)
	}
	return healthChecks, nil
}

// GetActiveAlerts gets active alerts for an integration
func (im *IntegrationMonitor) GetActiveAlerts(ctx context.Context, integrationID string) ([]IntegrationAlert, error) {
	var alerts []IntegrationAlert
	if err := im.db.WithContext(ctx).Where("integration_id = ? AND is_resolved = ?", integrationID, false).Find(&alerts).Error; err != nil {
		return nil, fmt.Errorf("failed to get alerts: %w", err)
	}
	return alerts, nil
}

// GetAllActiveAlerts gets all active alerts
func (im *IntegrationMonitor) GetAllActiveAlerts(ctx context.Context) ([]IntegrationAlert, error) {
	var alerts []IntegrationAlert
	if err := im.db.WithContext(ctx).Where("is_resolved = ?", false).Find(&alerts).Error; err != nil {
		return nil, fmt.Errorf("failed to get alerts: %w", err)
	}
	return alerts, nil
}

// AcknowledgeAlert acknowledges an alert
func (im *IntegrationMonitor) AcknowledgeAlert(ctx context.Context, alertID string) error {
	now := time.Now()
	updates := map[string]interface{}{
		"is_acknowledged": true,
		"acknowledged_at": &now,
		"updated_at":      now,
	}

	if err := im.db.WithContext(ctx).Model(&IntegrationAlert{}).Where("id = ?", alertID).Updates(updates).Error; err != nil {
		return fmt.Errorf("failed to acknowledge alert: %w", err)
	}

	return nil
}

// ResolveAlert resolves an alert
func (im *IntegrationMonitor) ResolveAlert(ctx context.Context, alertID string) error {
	now := time.Now()
	updates := map[string]interface{}{
		"is_resolved": true,
		"resolved_at": &now,
		"updated_at":  now,
	}

	if err := im.db.WithContext(ctx).Model(&IntegrationAlert{}).Where("id = ?", alertID).Updates(updates).Error; err != nil {
		return fmt.Errorf("failed to resolve alert: %w", err)
	}

	return nil
}

// GetMonitoringMetrics gets monitoring metrics
func (im *IntegrationMonitor) GetMonitoringMetrics(ctx context.Context) (*map[string]interface{}, error) {
	var totalIntegrations, healthyIntegrations, warningIntegrations, criticalIntegrations, offlineIntegrations int64
	var totalAlerts, activeAlerts, acknowledgedAlerts int64

	// Count integrations by status
	im.db.WithContext(ctx).Model(&HealthCheck{}).Count(&totalIntegrations)
	im.db.WithContext(ctx).Model(&HealthCheck{}).Where("status = ?", MonitorStatusHealthy).Count(&healthyIntegrations)
	im.db.WithContext(ctx).Model(&HealthCheck{}).Where("status = ?", MonitorStatusWarning).Count(&warningIntegrations)
	im.db.WithContext(ctx).Model(&HealthCheck{}).Where("status = ?", MonitorStatusCritical).Count(&criticalIntegrations)
	im.db.WithContext(ctx).Model(&HealthCheck{}).Where("status = ?", MonitorStatusOffline).Count(&offlineIntegrations)

	// Count alerts
	im.db.WithContext(ctx).Model(&IntegrationAlert{}).Count(&totalAlerts)
	im.db.WithContext(ctx).Model(&IntegrationAlert{}).Where("is_resolved = ?", false).Count(&activeAlerts)
	im.db.WithContext(ctx).Model(&IntegrationAlert{}).Where("is_acknowledged = ?", true).Count(&acknowledgedAlerts)

	metrics := map[string]interface{}{
		"total_integrations":    totalIntegrations,
		"healthy_integrations":  healthyIntegrations,
		"warning_integrations":  warningIntegrations,
		"critical_integrations": criticalIntegrations,
		"offline_integrations":  offlineIntegrations,
		"total_alerts":          totalAlerts,
		"active_alerts":         activeAlerts,
		"acknowledged_alerts":   acknowledgedAlerts,
		"health_percentage":     calculateHealthPercentage(healthyIntegrations, totalIntegrations),
		"monitoring_status":     im.isRunning,
		"last_updated":          time.Now(),
	}

	return &metrics, nil
}

// monitoringLoop runs the main monitoring loop
func (im *IntegrationMonitor) monitoringLoop(ctx context.Context) {
	ticker := time.NewTicker(im.config.HealthCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-im.stopChan:
			return
		case <-ticker.C:
			im.performHealthChecks(ctx)
		}
	}
}

// performHealthChecks performs health checks for all integrations
func (im *IntegrationMonitor) performHealthChecks(ctx context.Context) {
	configs, err := im.manager.ListIntegrationConfigs(ctx, nil)
	if err != nil {
		im.logMonitoringError("Failed to get integration configs", err)
		return
	}

	for _, config := range configs {
		if config.Status == "active" {
			im.performHealthCheck(ctx, config.ID)
		}
	}
}

// performHealthCheck performs a health check for a specific integration
func (im *IntegrationMonitor) performHealthCheck(ctx context.Context, integrationID string) {
	startTime := time.Now()

	// Get integration status
	status, err := im.manager.GetIntegrationStatus(ctx, integrationID)
	if err != nil {
		im.updateHealthCheck(ctx, integrationID, MonitorStatusOffline, time.Since(startTime).Seconds(), 1, 0, map[string]interface{}{
			"error": err.Error(),
		})
		im.createAlert(ctx, integrationID, AlertLevelCritical, "Integration Offline", fmt.Sprintf("Integration %s is offline: %v", integrationID, err))
		return
	}

	// Check response time
	responseTime := time.Since(startTime).Seconds()
	if responseTime > im.config.MaxResponseTime {
		im.updateHealthCheck(ctx, integrationID, MonitorStatusWarning, responseTime, 0, 1, map[string]interface{}{
			"response_time": responseTime,
			"threshold":     im.config.MaxResponseTime,
		})
		im.createAlert(ctx, integrationID, AlertLevelWarning, "High Response Time", fmt.Sprintf("Integration %s has high response time: %.2fs", integrationID, responseTime))
		return
	}

	// Check if integration is healthy
	if statusMap, ok := (*status)["status"].(string); ok && statusMap == "connected" {
		im.updateHealthCheck(ctx, integrationID, MonitorStatusHealthy, responseTime, 0, 1, map[string]interface{}{
			"response_time": responseTime,
			"status":        "connected",
		})
	} else {
		im.updateHealthCheck(ctx, integrationID, MonitorStatusCritical, responseTime, 1, 0, map[string]interface{}{
			"response_time": responseTime,
			"status":        statusMap,
		})
		im.createAlert(ctx, integrationID, AlertLevelCritical, "Integration Error", fmt.Sprintf("Integration %s has errors", integrationID))
	}
}

// updateHealthCheck updates a health check record
func (im *IntegrationMonitor) updateHealthCheck(ctx context.Context, integrationID string, status MonitorStatus, responseTime float64, errorCount, successCount int, details map[string]interface{}) {
	var healthCheck HealthCheck
	err := im.db.WithContext(ctx).Where("integration_id = ?", integrationID).First(&healthCheck).Error

	detailsJSON, _ := json.Marshal(details)
	now := time.Now()
	nextCheck := now.Add(im.config.HealthCheckInterval)

	if err != nil {
		// Create new health check
		healthCheck = HealthCheck{
			ID:            generateMonitorID(),
			IntegrationID: integrationID,
			Status:        status,
			ResponseTime:  responseTime,
			ErrorCount:    errorCount,
			SuccessCount:  successCount,
			LastCheck:     now,
			NextCheck:     nextCheck,
			Details:       detailsJSON,
			CreatedAt:     now,
			UpdatedAt:     now,
		}
		im.db.WithContext(ctx).Create(&healthCheck)
	} else {
		// Update existing health check
		healthCheck.Status = status
		healthCheck.ResponseTime = responseTime
		healthCheck.ErrorCount += errorCount
		healthCheck.SuccessCount += successCount
		healthCheck.LastCheck = now
		healthCheck.NextCheck = nextCheck
		healthCheck.Details = detailsJSON
		healthCheck.UpdatedAt = now
		im.db.WithContext(ctx).Save(&healthCheck)
	}

	im.mu.Lock()
	im.healthChecks[integrationID] = &healthCheck
	im.mu.Unlock()
}

// createAlert creates a new alert
func (im *IntegrationMonitor) createAlert(ctx context.Context, integrationID string, level AlertLevel, title string, message string) {
	alert := &IntegrationAlert{
		ID:             generateMonitorID(),
		IntegrationID:  integrationID,
		AlertLevel:     level,
		Title:          title,
		Message:        message,
		IsAcknowledged: false,
		IsResolved:     false,
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}

	if err := im.db.WithContext(ctx).Create(alert).Error; err != nil {
		im.logMonitoringError("Failed to create alert", err)
		return
	}

	im.mu.Lock()
	im.alerts[alert.ID] = alert
	im.mu.Unlock()

	// Send notification if enabled
	if im.config.EnableNotifications {
		im.sendNotification(alert)
	}
}

// sendNotification sends a notification for an alert
func (im *IntegrationMonitor) sendNotification(alert *IntegrationAlert) {
	// Mock implementation - in real implementation, this would send notifications
	// to configured channels (email, slack, etc.)
}

// logMonitoringError logs a monitoring error
func (im *IntegrationMonitor) logMonitoringError(message string, err error) {
	// Mock implementation - in real implementation, this would log errors
	// to a proper logging system
}

// calculateHealthPercentage calculates the health percentage
func calculateHealthPercentage(healthy, total int64) float64 {
	if total == 0 {
		return 0.0
	}
	return float64(healthy) / float64(total) * 100.0
}

// generateMonitorID generates a unique ID for monitor entities
func generateMonitorID() string {
	return fmt.Sprintf("mon_%d", time.Now().UnixNano())
}
