package deployment

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// Monitor tracks deployment metrics and events
type Monitor struct {
	mu          sync.RWMutex
	events      []DeploymentEvent
	metrics     map[string]*DeploymentMetrics
	subscribers []chan DeploymentEvent
	stopChan    chan bool
}

// NewMonitor creates a new deployment monitor
func NewMonitor() *Monitor {
	return &Monitor{
		events:      make([]DeploymentEvent, 0, 1000),
		metrics:     make(map[string]*DeploymentMetrics),
		subscribers: make([]chan DeploymentEvent, 0),
		stopChan:    make(chan bool),
	}
}

// Start begins monitoring
func (m *Monitor) Start(ctx context.Context) {
	go m.run(ctx)
}

// Stop stops monitoring
func (m *Monitor) Stop() {
	close(m.stopChan)
}

// Subscribe returns a channel for receiving deployment events
func (m *Monitor) Subscribe() <-chan DeploymentEvent {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	ch := make(chan DeploymentEvent, 100)
	m.subscribers = append(m.subscribers, ch)
	return ch
}

// EmitEvent emits a deployment event
func (m *Monitor) EmitEvent(event interface{}) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	// Create deployment event
	deploymentEvent := DeploymentEvent{
		Timestamp: time.Now(),
		Type:      fmt.Sprintf("%T", event),
		Level:     "info",
	}
	
	// Set event details based on type
	switch e := event.(type) {
	case DeploymentCreatedEvent:
		deploymentEvent.Message = fmt.Sprintf("Deployment '%s' created with %d targets", e.Name, e.TargetCount)
		deploymentEvent.Details = map[string]interface{}{
			"deployment_id": e.DeploymentID,
			"strategy":      e.Strategy,
		}
	
	case DeploymentStartedEvent:
		deploymentEvent.Message = fmt.Sprintf("Deployment started at %s", e.StartTime.Format("15:04:05"))
		deploymentEvent.Details = map[string]interface{}{
			"deployment_id": e.DeploymentID,
		}
	
	case DeploymentProgressEvent:
		deploymentEvent.Message = fmt.Sprintf("Progress: %d%% (%d successful, %d failed, %d pending)",
			e.Progress, e.Successful, e.Failed, e.Pending)
		deploymentEvent.Details = map[string]interface{}{
			"deployment_id": e.DeploymentID,
			"progress":      e.Progress,
		}
	
	case DeploymentCompletedEvent:
		deploymentEvent.Message = fmt.Sprintf("Deployment completed: %d successful, %d failed (duration: %v)",
			e.SuccessfulCount, e.FailedCount, e.Duration)
		deploymentEvent.Details = map[string]interface{}{
			"deployment_id": e.DeploymentID,
			"duration":      e.Duration.Seconds(),
		}
	
	case DeploymentFailedEvent:
		deploymentEvent.Level = "error"
		deploymentEvent.Message = fmt.Sprintf("Deployment failed: %s", e.Error)
		deploymentEvent.Details = map[string]interface{}{
			"deployment_id": e.DeploymentID,
			"failed_count":  e.FailedCount,
		}
	
	case DeploymentRolledBackEvent:
		deploymentEvent.Level = "warning"
		deploymentEvent.Message = fmt.Sprintf("Deployment rolled back: %s", e.Reason)
		deploymentEvent.Details = map[string]interface{}{
			"deployment_id": e.DeploymentID,
			"affected":      len(e.AffectedTargets),
		}
	
	case TargetDeploymentStartedEvent:
		deploymentEvent.Message = fmt.Sprintf("Target %s deployment started (wave %d)", e.BuildingID, e.Wave)
		deploymentEvent.BuildingID = e.BuildingID
		deploymentEvent.TargetID = e.TargetID
	
	case TargetDeploymentCompletedEvent:
		if e.Success {
			deploymentEvent.Message = fmt.Sprintf("Target %s deployment completed (duration: %v)",
				e.BuildingID, e.Duration)
		} else {
			deploymentEvent.Level = "error"
			deploymentEvent.Message = fmt.Sprintf("Target %s deployment failed", e.BuildingID)
		}
		deploymentEvent.BuildingID = e.BuildingID
		deploymentEvent.TargetID = e.TargetID
	
	case HealthCheckFailedEvent:
		deploymentEvent.Level = "warning"
		deploymentEvent.Message = fmt.Sprintf("Health check failed for %s: score %.1f",
			e.BuildingID, e.Score)
		deploymentEvent.BuildingID = e.BuildingID
		deploymentEvent.TargetID = e.TargetID
		deploymentEvent.Details = map[string]interface{}{
			"check_type": e.CheckType,
			"score":      e.Score,
			"issues":     e.Issues,
		}
	
	default:
		// Generic event
		eventJSON, _ := json.Marshal(event)
		deploymentEvent.Message = string(eventJSON)
	}
	
	// Store event
	m.events = append(m.events, deploymentEvent)
	
	// Limit event history
	if len(m.events) > 10000 {
		m.events = m.events[5000:]
	}
	
	// Notify subscribers
	for _, ch := range m.subscribers {
		select {
		case ch <- deploymentEvent:
		default:
			// Channel full, skip
		}
	}
}

// GetEvents returns recent deployment events
func (m *Monitor) GetEvents(deploymentID string, limit int) []DeploymentEvent {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	filtered := make([]DeploymentEvent, 0)
	
	// Start from end for most recent first
	for i := len(m.events) - 1; i >= 0 && len(filtered) < limit; i-- {
		event := m.events[i]
		
		// Filter by deployment ID if specified
		if deploymentID != "" {
			if details, ok := event.Details["deployment_id"]; ok {
				if id, ok := details.(string); ok && id != deploymentID {
					continue
				}
			}
		}
		
		filtered = append(filtered, event)
	}
	
	return filtered
}

// RecordMetrics records deployment metrics
func (m *Monitor) RecordMetrics(deploymentID string, metrics *DeploymentMetrics) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.metrics[deploymentID] = metrics
}

// GetMetrics returns deployment metrics
func (m *Monitor) GetMetrics(deploymentID string) *DeploymentMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	return m.metrics[deploymentID]
}

// GetAllMetrics returns metrics for all deployments
func (m *Monitor) GetAllMetrics() map[string]*DeploymentMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	// Create copy
	result := make(map[string]*DeploymentMetrics)
	for k, v := range m.metrics {
		result[k] = v
	}
	
	return result
}

// run is the main monitoring loop
func (m *Monitor) run(ctx context.Context) {
	metricsTicker := time.NewTicker(30 * time.Second)
	cleanupTicker := time.NewTicker(5 * time.Minute)
	
	defer metricsTicker.Stop()
	defer cleanupTicker.Stop()
	
	for {
		select {
		case <-ctx.Done():
			return
		case <-m.stopChan:
			return
		case <-metricsTicker.C:
			m.collectMetrics()
		case <-cleanupTicker.C:
			m.cleanup()
		}
	}
}

// collectMetrics collects system metrics
func (m *Monitor) collectMetrics() {
	// In production, would collect:
	// - Active deployment count
	// - Success/failure rates
	// - Average deployment duration
	// - Resource utilization
	// - Queue depths
}

// cleanup removes old events and metrics
func (m *Monitor) cleanup() {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	// Remove events older than 24 hours
	cutoff := time.Now().Add(-24 * time.Hour)
	newEvents := make([]DeploymentEvent, 0)
	
	for _, event := range m.events {
		if event.Timestamp.After(cutoff) {
			newEvents = append(newEvents, event)
		}
	}
	
	m.events = newEvents
	
	// Remove metrics for completed deployments older than 1 hour
	// (In production, would check deployment status from database)
}

// DeploymentDashboard provides a real-time view of deployments
type DeploymentDashboard struct {
	monitor *Monitor
	mu      sync.RWMutex
	stats   DashboardStats
}

// DashboardStats contains dashboard statistics
type DashboardStats struct {
	ActiveDeployments   int                    `json:"active_deployments"`
	TotalDeployments    int                    `json:"total_deployments"`
	SuccessRate         float64                `json:"success_rate"`
	AverageD uration    time.Duration          `json:"average_duration"`
	RecentEvents        []DeploymentEvent      `json:"recent_events"`
	StrategyBreakdown   map[string]int         `json:"strategy_breakdown"`
	HealthScoreAverage  float64                `json:"health_score_average"`
	LastUpdated         time.Time              `json:"last_updated"`
}

// NewDashboard creates a new deployment dashboard
func NewDashboard(monitor *Monitor) *DeploymentDashboard {
	return &DeploymentDashboard{
		monitor: monitor,
	}
}

// GetStats returns current dashboard statistics
func (d *DeploymentDashboard) GetStats() DashboardStats {
	d.mu.RLock()
	defer d.mu.RUnlock()
	
	return d.stats
}

// Update updates dashboard statistics
func (d *DeploymentDashboard) Update() {
	d.mu.Lock()
	defer d.mu.Unlock()
	
	// Get recent events
	d.stats.RecentEvents = d.monitor.GetEvents("", 10)
	
	// Calculate statistics from metrics
	metrics := d.monitor.GetAllMetrics()
	
	if len(metrics) > 0 {
		var totalDuration time.Duration
		var successCount, totalCount int
		
		for _, m := range metrics {
			if m.TotalDuration > 0 {
				totalDuration += m.TotalDuration
				totalCount++
			}
			if m.SuccessRate > 0 {
				successCount++
			}
		}
		
		if totalCount > 0 {
			d.stats.AverageDuration = totalDuration / time.Duration(totalCount)
			d.stats.SuccessRate = float64(successCount) / float64(totalCount)
		}
	}
	
	d.stats.TotalDeployments = len(metrics)
	d.stats.LastUpdated = time.Now()
}

// StartAutoUpdate starts automatic dashboard updates
func (d *DeploymentDashboard) StartAutoUpdate(ctx context.Context, interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				d.Update()
			}
		}
	}()
}

// AlertManager handles deployment alerts
type AlertManager struct {
	mu        sync.RWMutex
	rules     []AlertRule
	alerts    []Alert
	handlers  []AlertHandler
}

// AlertRule defines when to trigger an alert
type AlertRule struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Condition   string                 `json:"condition"`
	Threshold   float64                `json:"threshold"`
	Duration    time.Duration          `json:"duration"`
	Severity    string                 `json:"severity"`
	Actions     []string               `json:"actions"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Alert represents an active alert
type Alert struct {
	ID           string                 `json:"id"`
	RuleID       string                 `json:"rule_id"`
	DeploymentID string                 `json:"deployment_id"`
	BuildingID   string                 `json:"building_id,omitempty"`
	Severity     string                 `json:"severity"`
	Message      string                 `json:"message"`
	Details      map[string]interface{} `json:"details"`
	TriggeredAt  time.Time              `json:"triggered_at"`
	ResolvedAt   *time.Time             `json:"resolved_at,omitempty"`
}

// AlertHandler handles alert actions
type AlertHandler interface {
	Handle(alert Alert) error
}

// NewAlertManager creates a new alert manager
func NewAlertManager() *AlertManager {
	return &AlertManager{
		rules:    make([]AlertRule, 0),
		alerts:   make([]Alert, 0),
		handlers: make([]AlertHandler, 0),
	}
}

// AddRule adds an alert rule
func (am *AlertManager) AddRule(rule AlertRule) {
	am.mu.Lock()
	defer am.mu.Unlock()
	
	am.rules = append(am.rules, rule)
}

// AddHandler adds an alert handler
func (am *AlertManager) AddHandler(handler AlertHandler) {
	am.mu.Lock()
	defer am.mu.Unlock()
	
	am.handlers = append(am.handlers, handler)
}

// TriggerAlert triggers a new alert
func (am *AlertManager) TriggerAlert(ruleID, deploymentID, message string, details map[string]interface{}) {
	am.mu.Lock()
	defer am.mu.Unlock()
	
	// Find rule
	var rule *AlertRule
	for _, r := range am.rules {
		if r.ID == ruleID {
			rule = &r
			break
		}
	}
	
	if rule == nil {
		return
	}
	
	// Create alert
	alert := Alert{
		ID:           fmt.Sprintf("alert-%d", time.Now().UnixNano()),
		RuleID:       ruleID,
		DeploymentID: deploymentID,
		Severity:     rule.Severity,
		Message:      message,
		Details:      details,
		TriggeredAt:  time.Now(),
	}
	
	am.alerts = append(am.alerts, alert)
	
	// Trigger handlers
	for _, handler := range am.handlers {
		go handler.Handle(alert)
	}
}

// GetActiveAlerts returns active alerts
func (am *AlertManager) GetActiveAlerts() []Alert {
	am.mu.RLock()
	defer am.mu.RUnlock()
	
	active := make([]Alert, 0)
	for _, alert := range am.alerts {
		if alert.ResolvedAt == nil {
			active = append(active, alert)
		}
	}
	
	return active
}

// ResolveAlert resolves an alert
func (am *AlertManager) ResolveAlert(alertID string) {
	am.mu.Lock()
	defer am.mu.Unlock()
	
	for i := range am.alerts {
		if am.alerts[i].ID == alertID && am.alerts[i].ResolvedAt == nil {
			now := time.Now()
			am.alerts[i].ResolvedAt = &now
			break
		}
	}
}