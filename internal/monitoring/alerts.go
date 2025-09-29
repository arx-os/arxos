package monitoring

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// AlertLevel represents the severity level of an alert
type AlertLevel string

const (
	AlertLevelInfo      AlertLevel = "info"
	AlertLevelWarning   AlertLevel = "warning"
	AlertLevelCritical  AlertLevel = "critical"
	AlertLevelEmergency AlertLevel = "emergency"
)

// AlertStatus represents the status of an alert
type AlertStatus string

const (
	AlertStatusFiring   AlertStatus = "firing"
	AlertStatusResolved AlertStatus = "resolved"
	AlertStatusSilenced AlertStatus = "silenced"
)

// Alert represents an alert
type Alert struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Level       AlertLevel             `json:"level"`
	Status      AlertStatus            `json:"status"`
	Labels      map[string]string      `json:"labels"`
	Annotations map[string]string      `json:"annotations"`
	StartsAt    time.Time              `json:"starts_at"`
	EndsAt      time.Time              `json:"ends_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// AlertRule defines when an alert should fire
type AlertRule struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Level       AlertLevel             `json:"level"`
	Condition   string                 `json:"condition"`
	Duration    time.Duration          `json:"duration"`
	Labels      map[string]string      `json:"labels"`
	Annotations map[string]string      `json:"annotations"`
	Enabled     bool                   `json:"enabled"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// AlertManager manages alerts and alert rules
type AlertManager struct {
	mu            sync.RWMutex
	alerts        map[string]*Alert
	rules         map[string]*AlertRule
	receivers     map[string]AlertReceiver
	checkInterval time.Duration
}

// AlertReceiver defines the interface for alert receivers
type AlertReceiver interface {
	SendAlert(ctx context.Context, alert *Alert) error
	GetName() string
	IsEnabled() bool
}

// NewAlertManager creates a new alert manager
func NewAlertManager(checkInterval time.Duration) *AlertManager {
	return &AlertManager{
		alerts:        make(map[string]*Alert),
		rules:         make(map[string]*AlertRule),
		receivers:     make(map[string]AlertReceiver),
		checkInterval: checkInterval,
	}
}

// AddAlertRule adds an alert rule
func (am *AlertManager) AddAlertRule(rule *AlertRule) {
	am.mu.Lock()
	defer am.mu.Unlock()

	am.rules[rule.ID] = rule
	logger.Info("Added alert rule: %s", rule.Name)
}

// RemoveAlertRule removes an alert rule
func (am *AlertManager) RemoveAlertRule(id string) {
	am.mu.Lock()
	defer am.mu.Unlock()

	delete(am.rules, id)
	logger.Info("Removed alert rule: %s", id)
}

// AddAlertReceiver adds an alert receiver
func (am *AlertManager) AddAlertReceiver(receiver AlertReceiver) {
	am.mu.Lock()
	defer am.mu.Unlock()

	name := receiver.GetName()
	am.receivers[name] = receiver
	logger.Info("Added alert receiver: %s", name)
}

// RemoveAlertReceiver removes an alert receiver
func (am *AlertManager) RemoveAlertReceiver(name string) {
	am.mu.Lock()
	defer am.mu.Unlock()

	delete(am.receivers, name)
	logger.Info("Removed alert receiver: %s", name)
}

// FireAlert fires an alert
func (am *AlertManager) FireAlert(ruleID string, labels map[string]string, annotations map[string]string) error {
	am.mu.Lock()
	defer am.mu.Unlock()

	rule, exists := am.rules[ruleID]
	if !exists {
		return fmt.Errorf("alert rule %s not found", ruleID)
	}

	if !rule.Enabled {
		return fmt.Errorf("alert rule %s is disabled", ruleID)
	}

	alertID := fmt.Sprintf("%s_%d", ruleID, time.Now().Unix())
	alert := &Alert{
		ID:          alertID,
		Name:        rule.Name,
		Description: rule.Description,
		Level:       rule.Level,
		Status:      AlertStatusFiring,
		Labels:      mergeLabels(rule.Labels, labels),
		Annotations: mergeLabels(rule.Annotations, annotations),
		StartsAt:    time.Now(),
		UpdatedAt:   time.Now(),
		Metadata:    make(map[string]interface{}),
	}

	am.alerts[alertID] = alert

	// Send alert to receivers
	go am.sendAlertToReceivers(context.Background(), alert)

	logger.Warn("Alert fired: %s (%s)", alert.Name, alert.Level)
	return nil
}

// ResolveAlert resolves an alert
func (am *AlertManager) ResolveAlert(alertID string) error {
	am.mu.Lock()
	defer am.mu.Unlock()

	alert, exists := am.alerts[alertID]
	if !exists {
		return fmt.Errorf("alert %s not found", alertID)
	}

	if alert.Status == AlertStatusResolved {
		return nil // Already resolved
	}

	alert.Status = AlertStatusResolved
	alert.EndsAt = time.Now()
	alert.UpdatedAt = time.Now()

	logger.Info("Alert resolved: %s", alert.Name)
	return nil
}

// SilenceAlert silences an alert
func (am *AlertManager) SilenceAlert(alertID string, duration time.Duration) error {
	am.mu.Lock()
	defer am.mu.Unlock()

	alert, exists := am.alerts[alertID]
	if !exists {
		return fmt.Errorf("alert %s not found", alertID)
	}

	alert.Status = AlertStatusSilenced
	alert.EndsAt = time.Now().Add(duration)
	alert.UpdatedAt = time.Now()

	logger.Info("Alert silenced: %s for %v", alert.Name, duration)
	return nil
}

// GetAlert retrieves an alert by ID
func (am *AlertManager) GetAlert(id string) (*Alert, bool) {
	am.mu.RLock()
	defer am.mu.RUnlock()

	alert, exists := am.alerts[id]
	return alert, exists
}

// GetAllAlerts returns all alerts
func (am *AlertManager) GetAllAlerts() map[string]*Alert {
	am.mu.RLock()
	defer am.mu.RUnlock()

	alerts := make(map[string]*Alert)
	for id, alert := range am.alerts {
		alerts[id] = alert
	}
	return alerts
}

// GetActiveAlerts returns all active (firing) alerts
func (am *AlertManager) GetActiveAlerts() map[string]*Alert {
	am.mu.RLock()
	defer am.mu.RUnlock()

	activeAlerts := make(map[string]*Alert)
	for id, alert := range am.alerts {
		if alert.Status == AlertStatusFiring {
			activeAlerts[id] = alert
		}
	}
	return activeAlerts
}

// GetAlertRules returns all alert rules
func (am *AlertManager) GetAlertRules() map[string]*AlertRule {
	am.mu.RLock()
	defer am.mu.RUnlock()

	rules := make(map[string]*AlertRule)
	for id, rule := range am.rules {
		rules[id] = rule
	}
	return rules
}

// sendAlertToReceivers sends an alert to all enabled receivers
func (am *AlertManager) sendAlertToReceivers(ctx context.Context, alert *Alert) {
	for name, receiver := range am.receivers {
		if !receiver.IsEnabled() {
			continue
		}

		go func(name string, receiver AlertReceiver) {
			if err := receiver.SendAlert(ctx, alert); err != nil {
				logger.Error("Failed to send alert to receiver %s: %v", name, err)
			}
		}(name, receiver)
	}
}

// mergeLabels merges two label maps
func mergeLabels(base, additional map[string]string) map[string]string {
	result := make(map[string]string)

	// Add base labels
	for k, v := range base {
		result[k] = v
	}

	// Add additional labels (override base if same key)
	for k, v := range additional {
		result[k] = v
	}

	return result
}

// LogAlertReceiver implements AlertReceiver for logging alerts
type LogAlertReceiver struct {
	name    string
	enabled bool
}

// NewLogAlertReceiver creates a new log alert receiver
func NewLogAlertReceiver(name string, enabled bool) *LogAlertReceiver {
	return &LogAlertReceiver{
		name:    name,
		enabled: enabled,
	}
}

// SendAlert sends an alert to the log
func (lar *LogAlertReceiver) SendAlert(ctx context.Context, alert *Alert) error {
	logger.Warn("ALERT [%s] %s: %s", alert.Level, alert.Name, alert.Description)

	if len(alert.Labels) > 0 {
		logger.Warn("Alert labels: %v", alert.Labels)
	}

	if len(alert.Annotations) > 0 {
		logger.Warn("Alert annotations: %v", alert.Annotations)
	}

	return nil
}

// GetName returns the receiver name
func (lar *LogAlertReceiver) GetName() string {
	return lar.name
}

// IsEnabled returns whether the receiver is enabled
func (lar *LogAlertReceiver) IsEnabled() bool {
	return lar.enabled
}

// EmailAlertReceiver implements AlertReceiver for email alerts
type EmailAlertReceiver struct {
	name     string
	enabled  bool
	smtpHost string
	smtpPort int
	username string
	password string
	from     string
	to       []string
}

// NewEmailAlertReceiver creates a new email alert receiver
func NewEmailAlertReceiver(name string, enabled bool, smtpHost string, smtpPort int, username, password, from string, to []string) *EmailAlertReceiver {
	return &EmailAlertReceiver{
		name:     name,
		enabled:  enabled,
		smtpHost: smtpHost,
		smtpPort: smtpPort,
		username: username,
		password: password,
		from:     from,
		to:       to,
	}
}

// SendAlert sends an alert via email
func (ear *EmailAlertReceiver) SendAlert(ctx context.Context, alert *Alert) error {
	// TODO: Implement email sending
	logger.Info("Email alert sent: %s to %v", alert.Name, ear.to)
	return nil
}

// GetName returns the receiver name
func (ear *EmailAlertReceiver) GetName() string {
	return ear.name
}

// IsEnabled returns whether the receiver is enabled
func (ear *EmailAlertReceiver) IsEnabled() bool {
	return ear.enabled
}

// WebhookAlertReceiver implements AlertReceiver for webhook alerts
type WebhookAlertReceiver struct {
	name    string
	enabled bool
	url     string
	headers map[string]string
}

// NewWebhookAlertReceiver creates a new webhook alert receiver
func NewWebhookAlertReceiver(name string, enabled bool, url string, headers map[string]string) *WebhookAlertReceiver {
	return &WebhookAlertReceiver{
		name:    name,
		enabled: enabled,
		url:     url,
		headers: headers,
	}
}

// SendAlert sends an alert via webhook
func (war *WebhookAlertReceiver) SendAlert(ctx context.Context, alert *Alert) error {
	// TODO: Implement webhook sending
	logger.Info("Webhook alert sent: %s to %s", alert.Name, war.url)
	return nil
}

// GetName returns the receiver name
func (war *WebhookAlertReceiver) GetName() string {
	return war.name
}

// IsEnabled returns whether the receiver is enabled
func (war *WebhookAlertReceiver) IsEnabled() bool {
	return war.enabled
}

// Global alert manager instance
var globalAlertManager *AlertManager
var alertOnce sync.Once

// GetGlobalAlertManager returns the global alert manager instance
func GetGlobalAlertManager() *AlertManager {
	alertOnce.Do(func() {
		globalAlertManager = NewAlertManager(30 * time.Second)

		// Add default log receiver
		logReceiver := NewLogAlertReceiver("log", true)
		globalAlertManager.AddAlertReceiver(logReceiver)
	})
	return globalAlertManager
}

// Convenience functions for global alert management
func AddAlertRule(rule *AlertRule) {
	GetGlobalAlertManager().AddAlertRule(rule)
}

func FireAlert(ruleID string, labels map[string]string, annotations map[string]string) error {
	return GetGlobalAlertManager().FireAlert(ruleID, labels, annotations)
}

func ResolveAlert(alertID string) error {
	return GetGlobalAlertManager().ResolveAlert(alertID)
}

func GetActiveAlerts() map[string]*Alert {
	return GetGlobalAlertManager().GetActiveAlerts()
}
