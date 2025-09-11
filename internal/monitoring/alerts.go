package monitoring

import (
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/logger"
)

// AlertManager handles system alerts and notifications
type AlertManager struct {
	alerts    map[string]Alert
	mu        sync.RWMutex
	maxAlerts int
}

// Alert represents a system alert
type Alert struct {
	ID          string        `json:"id"`
	Type        AlertType     `json:"type"`
	Severity    AlertSeverity `json:"severity"`
	Message     string        `json:"message"`
	EquipmentID *string       `json:"equipment_id,omitempty"`
	Timestamp   time.Time     `json:"timestamp"`
	Acknowledged bool         `json:"acknowledged"`
	ResolvedAt  *time.Time    `json:"resolved_at,omitempty"`
	Details     map[string]interface{} `json:"details,omitempty"`
}

// AlertType categorizes different alert types
type AlertType string

const (
	AlertEquipmentFailure   AlertType = "equipment_failure"
	AlertEquipmentCritical  AlertType = "equipment_critical"
	AlertEnergyEfficiency   AlertType = "energy_efficiency"
	AlertConnectionLoss     AlertType = "connection_loss"
	AlertMaintenanceOverdue AlertType = "maintenance_overdue"
	AlertPerformance        AlertType = "performance"
	AlertSecurity          AlertType = "security"
	AlertFailure           AlertType = "system_failure"
)

// AlertSeverity indicates alert importance
type AlertSeverity string

const (
	AlertInfo     AlertSeverity = "info"
	AlertWarning  AlertSeverity = "warning"
	AlertError    AlertSeverity = "error"
	AlertCritical AlertSeverity = "critical"
)

// NewAlertManager creates a new alert manager
func NewAlertManager() *AlertManager {
	return &AlertManager{
		alerts:    make(map[string]Alert),
		maxAlerts: 1000, // Limit to prevent memory issues
	}
}

// AddAlert adds a new alert to the system
func (am *AlertManager) AddAlert(alert Alert) {
	am.mu.Lock()
	defer am.mu.Unlock()
	
	// Check if alert already exists (avoid duplicates)
	if existing, exists := am.alerts[alert.ID]; exists {
		if !existing.Acknowledged && existing.ResolvedAt == nil {
			// Update existing unresolved alert
			existing.Timestamp = alert.Timestamp
			existing.Message = alert.Message
			am.alerts[alert.ID] = existing
			return
		}
	}
	
	// Add new alert
	am.alerts[alert.ID] = alert
	
	// Enforce max alerts limit
	if len(am.alerts) > am.maxAlerts {
		am.cleanupOldestAlerts(am.maxAlerts / 2)
	}
	
	logger.Info("Alert added: %s - %s (%s)", alert.Type, alert.Message, alert.Severity)
}

// GetActiveAlerts returns all unresolved alerts
func (am *AlertManager) GetActiveAlerts() []Alert {
	am.mu.RLock()
	defer am.mu.RUnlock()
	
	var active []Alert
	for _, alert := range am.alerts {
		if alert.ResolvedAt == nil {
			active = append(active, alert)
		}
	}
	
	return active
}

// GetAlertsByType returns alerts of a specific type
func (am *AlertManager) GetAlertsByType(alertType AlertType) []Alert {
	am.mu.RLock()
	defer am.mu.RUnlock()
	
	var filtered []Alert
	for _, alert := range am.alerts {
		if alert.Type == alertType {
			filtered = append(filtered, alert)
		}
	}
	
	return filtered
}

// GetAlertsBySeverity returns alerts of a specific severity
func (am *AlertManager) GetAlertsBySeverity(severity AlertSeverity) []Alert {
	am.mu.RLock()
	defer am.mu.RUnlock()
	
	var filtered []Alert
	for _, alert := range am.alerts {
		if alert.Severity == severity {
			filtered = append(filtered, alert)
		}
	}
	
	return filtered
}

// AcknowledgeAlert marks an alert as acknowledged
func (am *AlertManager) AcknowledgeAlert(alertID string) error {
	am.mu.Lock()
	defer am.mu.Unlock()
	
	alert, exists := am.alerts[alertID]
	if !exists {
		return ErrAlertNotFound
	}
	
	alert.Acknowledged = true
	am.alerts[alertID] = alert
	
	logger.Info("Alert acknowledged: %s", alertID)
	return nil
}

// ResolveAlert marks an alert as resolved
func (am *AlertManager) ResolveAlert(alertID string) error {
	am.mu.Lock()
	defer am.mu.Unlock()
	
	alert, exists := am.alerts[alertID]
	if !exists {
		return ErrAlertNotFound
	}
	
	now := time.Now()
	alert.ResolvedAt = &now
	am.alerts[alertID] = alert
	
	logger.Info("Alert resolved: %s", alertID)
	return nil
}

// GetAlertStats returns alert statistics
func (am *AlertManager) GetAlertStats() AlertStats {
	am.mu.RLock()
	defer am.mu.RUnlock()
	
	stats := AlertStats{
		TotalAlerts: len(am.alerts),
		BySeverity:  make(map[AlertSeverity]int),
		ByType:      make(map[AlertType]int),
	}
	
	for _, alert := range am.alerts {
		// Count by severity
		stats.BySeverity[alert.Severity]++
		
		// Count by type
		stats.ByType[alert.Type]++
		
		// Count active alerts
		if alert.ResolvedAt == nil {
			stats.ActiveAlerts++
			
			if !alert.Acknowledged {
				stats.UnacknowledgedAlerts++
			}
		} else {
			stats.ResolvedAlerts++
		}
	}
	
	return stats
}

// CleanupExpiredAlerts removes old resolved alerts
func (am *AlertManager) CleanupExpiredAlerts(maxAge time.Duration) {
	am.mu.Lock()
	defer am.mu.Unlock()
	
	cutoff := time.Now().Add(-maxAge)
	removed := 0
	
	for id, alert := range am.alerts {
		if alert.ResolvedAt != nil && alert.ResolvedAt.Before(cutoff) {
			delete(am.alerts, id)
			removed++
		}
	}
	
	if removed > 0 {
		logger.Debug("Cleaned up %d expired alerts", removed)
	}
}

// cleanupOldestAlerts removes the oldest alerts to enforce limits
func (am *AlertManager) cleanupOldestAlerts(keepCount int) {
	if len(am.alerts) <= keepCount {
		return
	}
	
	// Convert to slice for sorting
	type alertWithID struct {
		id    string
		alert Alert
	}
	
	var alertList []alertWithID
	for id, alert := range am.alerts {
		alertList = append(alertList, alertWithID{id, alert})
	}
	
	// Sort by timestamp (oldest first)
	for i := 0; i < len(alertList)-1; i++ {
		for j := i + 1; j < len(alertList); j++ {
			if alertList[i].alert.Timestamp.After(alertList[j].alert.Timestamp) {
				alertList[i], alertList[j] = alertList[j], alertList[i]
			}
		}
	}
	
	// Remove oldest alerts
	removeCount := len(alertList) - keepCount
	for i := 0; i < removeCount; i++ {
		delete(am.alerts, alertList[i].id)
	}
	
	logger.Debug("Cleaned up %d oldest alerts", removeCount)
}

// AlertStats provides statistical information about alerts
type AlertStats struct {
	TotalAlerts           int                        `json:"total_alerts"`
	ActiveAlerts          int                        `json:"active_alerts"`
	ResolvedAlerts        int                        `json:"resolved_alerts"`
	UnacknowledgedAlerts  int                        `json:"unacknowledged_alerts"`
	BySeverity           map[AlertSeverity]int       `json:"by_severity"`
	ByType               map[AlertType]int           `json:"by_type"`
}

// Custom errors
type AlertManagerError string

func (e AlertManagerError) Error() string {
	return string(e)
}

const (
	ErrAlertNotFound AlertManagerError = "alert not found"
)

// GetCriticalAlerts returns only critical severity alerts
func (am *AlertManager) GetCriticalAlerts() []Alert {
	return am.GetAlertsBySeverity(AlertCritical)
}

// GetEquipmentAlerts returns alerts for specific equipment
func (am *AlertManager) GetEquipmentAlerts(equipmentID string) []Alert {
	am.mu.RLock()
	defer am.mu.RUnlock()
	
	var filtered []Alert
	for _, alert := range am.alerts {
		if alert.EquipmentID != nil && *alert.EquipmentID == equipmentID {
			filtered = append(filtered, alert)
		}
	}
	
	return filtered
}

// HasCriticalAlerts checks if there are any unresolved critical alerts
func (am *AlertManager) HasCriticalAlerts() bool {
	am.mu.RLock()
	defer am.mu.RUnlock()
	
	for _, alert := range am.alerts {
		if alert.Severity == AlertCritical && alert.ResolvedAt == nil {
			return true
		}
	}
	
	return false
}

// GetAlertSummary provides a quick overview of alert status
func (am *AlertManager) GetAlertSummary() AlertSummary {
	stats := am.GetAlertStats()
	
	return AlertSummary{
		Critical:        stats.BySeverity[AlertCritical],
		Warning:         stats.BySeverity[AlertWarning],
		Info:           stats.BySeverity[AlertInfo],
		Error:          stats.BySeverity[AlertError],
		Active:         stats.ActiveAlerts,
		Unacknowledged: stats.UnacknowledgedAlerts,
		HasCritical:    am.HasCriticalAlerts(),
	}
}

// AlertSummary provides a condensed view of alert status
type AlertSummary struct {
	Critical        int  `json:"critical"`
	Warning         int  `json:"warning"`
	Info           int  `json:"info"`
	Error          int  `json:"error"`
	Active         int  `json:"active"`
	Unacknowledged int  `json:"unacknowledged"`
	HasCritical    bool `json:"has_critical"`
}