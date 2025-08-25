package monitoring

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
	"gorm.io/datatypes"
	"gorm.io/gorm"
)

// SecurityMonitor monitors security events and triggers alerts
type SecurityMonitor struct {
	db          *gorm.DB
	alerts      chan SecurityEvent
	thresholds  map[string]Threshold
	mu          sync.RWMutex
	ctx         context.Context
	cancel      context.CancelFunc
}

// SecurityEvent represents a security event to monitor
type SecurityEvent struct {
	Type      string
	Severity  string
	UserID    *uint
	IPAddress string
	Path      string
	Method    string
	Details   map[string]interface{}
	Timestamp time.Time
}

// Threshold defines alert thresholds
type Threshold struct {
	EventType    string
	MaxCount     int
	TimeWindow   time.Duration
	Severity     string
	AutoBlock    bool
	NotifyAdmins bool
}

// AlertNotification represents an alert to be sent
type AlertNotification struct {
	ID          uint      `json:"id"`
	AlertID     uint      `json:"alert_id"`
	Channel     string    `json:"channel"` // email, slack, webhook
	Recipient   string    `json:"recipient"`
	Status      string    `json:"status"` // pending, sent, failed
	SentAt      *time.Time `json:"sent_at,omitempty"`
	Error       string    `json:"error,omitempty"`
	CreatedAt   time.Time `json:"created_at"`
}

// NewSecurityMonitor creates a new security monitor
func NewSecurityMonitor() *SecurityMonitor {
	ctx, cancel := context.WithCancel(context.Background())
	
	sm := &SecurityMonitor{
		db:     db.GormDB,
		alerts: make(chan SecurityEvent, 1000),
		ctx:    ctx,
		cancel: cancel,
		thresholds: map[string]Threshold{
			"authentication_failure": {
				EventType:    "authentication_failure",
				MaxCount:     5,
				TimeWindow:   5 * time.Minute,
				Severity:     "high",
				AutoBlock:    true,
				NotifyAdmins: true,
			},
			"rate_limit_exceeded": {
				EventType:    "rate_limit_exceeded",
				MaxCount:     10,
				TimeWindow:   1 * time.Minute,
				Severity:     "medium",
				AutoBlock:    false,
				NotifyAdmins: false,
			},
			"suspicious_activity": {
				EventType:    "suspicious_activity",
				MaxCount:     3,
				TimeWindow:   10 * time.Minute,
				Severity:     "critical",
				AutoBlock:    true,
				NotifyAdmins: true,
			},
			"sql_injection_attempt": {
				EventType:    "sql_injection_attempt",
				MaxCount:     1,
				TimeWindow:   1 * time.Hour,
				Severity:     "critical",
				AutoBlock:    true,
				NotifyAdmins: true,
			},
			"xss_attempt": {
				EventType:    "xss_attempt",
				MaxCount:     1,
				TimeWindow:   1 * time.Hour,
				Severity:     "critical",
				AutoBlock:    true,
				NotifyAdmins: true,
			},
			"unauthorized_access": {
				EventType:    "unauthorized_access",
				MaxCount:     3,
				TimeWindow:   5 * time.Minute,
				Severity:     "high",
				AutoBlock:    false,
				NotifyAdmins: true,
			},
			"2fa_failure": {
				EventType:    "2fa_failure",
				MaxCount:     3,
				TimeWindow:   10 * time.Minute,
				Severity:     "high",
				AutoBlock:    true,
				NotifyAdmins: true,
			},
		},
	}

	// Start monitoring goroutines
	go sm.processEvents()
	go sm.checkThresholds()
	go sm.cleanupOldAlerts()

	return sm
}

// LogEvent logs a security event for monitoring
func (sm *SecurityMonitor) LogEvent(event SecurityEvent) {
	select {
	case sm.alerts <- event:
		// Event queued successfully
	default:
		// Queue full, log error
		fmt.Printf("Security event queue full, dropping event: %+v\n", event)
	}
}

// processEvents processes security events from the queue
func (sm *SecurityMonitor) processEvents() {
	for {
		select {
		case <-sm.ctx.Done():
			return
		case event := <-sm.alerts:
			// Store event in database
			detailsJSON, _ := json.Marshal(event.Details)
			alert := models.SecurityAlert{
				AlertType:  event.Type,
				Severity:   event.Severity,
				IPAddress:  event.IPAddress,
				Path:       event.Path,
				Method:     event.Method,
				UserID:     event.UserID,
				Details:    datatypes.JSON(detailsJSON),
				CreatedAt:  event.Timestamp,
			}
			
			if err := sm.db.Create(&alert).Error; err != nil {
				fmt.Printf("Failed to store security alert: %v\n", err)
				continue
			}

			// Check if threshold is exceeded
			sm.checkEventThreshold(event, alert.ID)
		}
	}
}

// checkEventThreshold checks if an event exceeds defined thresholds
func (sm *SecurityMonitor) checkEventThreshold(event SecurityEvent, alertID uint) {
	sm.mu.RLock()
	threshold, exists := sm.thresholds[event.Type]
	sm.mu.RUnlock()

	if !exists {
		return
	}

	// Count recent events of this type
	var count int64
	since := time.Now().Add(-threshold.TimeWindow)

	query := sm.db.Model(&models.SecurityAlert{}).
		Where("alert_type = ? AND created_at > ?", event.Type, since)

	if event.IPAddress != "" {
		query = query.Where("ip_address = ?", event.IPAddress)
	}

	if event.UserID != nil {
		query = query.Where("user_id = ?", *event.UserID)
	}

	query.Count(&count)

	if int(count) >= threshold.MaxCount {
		// Threshold exceeded, trigger actions
		sm.triggerAlert(event, threshold, alertID)
	}
}

// triggerAlert triggers alert actions when threshold is exceeded
func (sm *SecurityMonitor) triggerAlert(event SecurityEvent, threshold Threshold, alertID uint) {
	// Auto-block if configured
	if threshold.AutoBlock && event.IPAddress != "" {
		sm.blockIP(event.IPAddress)
	}

	// Notify admins if configured
	if threshold.NotifyAdmins {
		sm.notifyAdmins(event, threshold, alertID)
	}

	// Log critical event
	if threshold.Severity == "critical" {
		sm.logCriticalEvent(event, threshold)
	}
}

// blockIP blocks an IP address
func (sm *SecurityMonitor) blockIP(ip string) {
	// Create IP block record
	block := IPBlock{
		IPAddress: ip,
		Reason:    "Automated security threshold exceeded",
		BlockedAt: time.Now(),
		ExpiresAt: time.Now().Add(24 * time.Hour), // 24 hour block
		IsActive:  true,
	}

	sm.db.Create(&block)
}

// notifyAdmins sends notifications to administrators
func (sm *SecurityMonitor) notifyAdmins(event SecurityEvent, threshold Threshold, alertID uint) {
	// Get admin users
	var admins []models.User
	sm.db.Where("is_admin = ?", true).Find(&admins)

	for _, admin := range admins {
		// Create notification record
		notification := AlertNotification{
			AlertID:   alertID,
			Channel:   "email",
			Recipient: admin.Email,
			Status:    "pending",
			CreatedAt: time.Now(),
		}
		sm.db.Create(&notification)

		// Queue email sending (implementation depends on email service)
		go sm.sendAlertEmail(admin.Email, event, threshold)
	}
}

// sendAlertEmail sends alert email to administrator
func (sm *SecurityMonitor) sendAlertEmail(email string, event SecurityEvent, threshold Threshold) {
	// This would integrate with your email service
	// For now, just log
	fmt.Printf("Sending security alert to %s: %+v\n", email, event)
}

// logCriticalEvent logs critical security events
func (sm *SecurityMonitor) logCriticalEvent(event SecurityEvent, threshold Threshold) {
	// This could integrate with external SIEM systems
	fmt.Printf("CRITICAL SECURITY EVENT: %+v\n", event)
}

// checkThresholds periodically checks for patterns and anomalies
func (sm *SecurityMonitor) checkThresholds() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-sm.ctx.Done():
			return
		case <-ticker.C:
			sm.detectAnomalies()
			sm.checkBruteForce()
			sm.checkDDoS()
		}
	}
}

// detectAnomalies detects unusual patterns
func (sm *SecurityMonitor) detectAnomalies() {
	// Check for unusual activity patterns
	// Example: Multiple failed logins from different IPs for same user
	var results []struct {
		UserID uint
		Count  int
	}

	sm.db.Model(&models.SecurityAlert{}).
		Select("user_id, COUNT(DISTINCT ip_address) as count").
		Where("alert_type = ? AND created_at > ? AND user_id IS NOT NULL",
			"authentication_failure", time.Now().Add(-10*time.Minute)).
		Group("user_id").
		Having("COUNT(DISTINCT ip_address) > ?", 3).
		Scan(&results)

	for _, result := range results {
		event := SecurityEvent{
			Type:      "suspicious_activity",
			Severity:  "critical",
			UserID:    &result.UserID,
			Details: map[string]interface{}{
				"reason": "Multiple failed login attempts from different IPs",
				"count":  result.Count,
			},
			Timestamp: time.Now(),
		}
		sm.LogEvent(event)
	}
}

// checkBruteForce checks for brute force attacks
func (sm *SecurityMonitor) checkBruteForce() {
	// Check for rapid authentication failures
	var results []struct {
		IPAddress string
		Count     int
	}

	sm.db.Model(&models.SecurityAlert{}).
		Select("ip_address, COUNT(*) as count").
		Where("alert_type = ? AND created_at > ?",
			"authentication_failure", time.Now().Add(-5*time.Minute)).
		Group("ip_address").
		Having("COUNT(*) > ?", 10).
		Scan(&results)

	for _, result := range results {
		event := SecurityEvent{
			Type:      "brute_force_attempt",
			Severity:  "critical",
			IPAddress: result.IPAddress,
			Details: map[string]interface{}{
				"attempts": result.Count,
				"window":   "5 minutes",
			},
			Timestamp: time.Now(),
		}
		sm.LogEvent(event)
	}
}

// checkDDoS checks for potential DDoS attacks
func (sm *SecurityMonitor) checkDDoS() {
	// Check for high request rates
	var count int64
	sm.db.Model(&models.APIUsage{}).
		Where("timestamp > ?", time.Now().Add(-1*time.Minute)).
		Count(&count)

	if count > 10000 { // Threshold for 1 minute
		event := SecurityEvent{
			Type:     "ddos_suspected",
			Severity: "critical",
			Details: map[string]interface{}{
				"request_count": count,
				"time_window":   "1 minute",
			},
			Timestamp: time.Now(),
		}
		sm.LogEvent(event)
	}
}

// cleanupOldAlerts removes old security alerts
func (sm *SecurityMonitor) cleanupOldAlerts() {
	ticker := time.NewTicker(24 * time.Hour)
	defer ticker.Stop()

	for {
		select {
		case <-sm.ctx.Done():
			return
		case <-ticker.C:
			// Archive alerts older than 30 days
			archiveDate := time.Now().AddDate(0, 0, -30)
			sm.db.Where("created_at < ? AND is_resolved = ?", archiveDate, true).
				Delete(&models.SecurityAlert{})

			// Clean up old IP blocks
			sm.db.Where("expires_at < ? AND is_active = ?", time.Now(), true).
				Update("is_active", false)
		}
	}
}

// GetSecurityDashboard returns security monitoring dashboard data
func (sm *SecurityMonitor) GetSecurityDashboard() map[string]interface{} {
	dashboard := make(map[string]interface{})

	// Recent alerts
	var recentAlerts []models.SecurityAlert
	sm.db.Order("created_at DESC").Limit(10).Find(&recentAlerts)
	dashboard["recent_alerts"] = recentAlerts

	// Alert statistics
	var stats struct {
		TotalToday     int64
		CriticalToday  int64
		Unresolved     int64
		BlockedIPs     int64
	}

	today := time.Now().Truncate(24 * time.Hour)
	sm.db.Model(&models.SecurityAlert{}).Where("created_at >= ?", today).Count(&stats.TotalToday)
	sm.db.Model(&models.SecurityAlert{}).Where("created_at >= ? AND severity = ?", today, "critical").Count(&stats.CriticalToday)
	sm.db.Model(&models.SecurityAlert{}).Where("is_resolved = ?", false).Count(&stats.Unresolved)
	sm.db.Model(&IPBlock{}).Where("is_active = ?", true).Count(&stats.BlockedIPs)

	dashboard["statistics"] = stats

	// Top threat types
	var threatTypes []struct {
		AlertType string
		Count     int
	}
	sm.db.Model(&models.SecurityAlert{}).
		Select("alert_type, COUNT(*) as count").
		Where("created_at >= ?", today).
		Group("alert_type").
		Order("count DESC").
		Limit(5).
		Scan(&threatTypes)

	dashboard["top_threats"] = threatTypes

	// Active monitoring status
	dashboard["monitoring_active"] = true
	dashboard["thresholds_configured"] = len(sm.thresholds)

	return dashboard
}

// IPBlock represents a blocked IP address
type IPBlock struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	IPAddress string    `gorm:"uniqueIndex" json:"ip_address"`
	Reason    string    `json:"reason"`
	BlockedAt time.Time `json:"blocked_at"`
	ExpiresAt time.Time `json:"expires_at"`
	IsActive  bool      `gorm:"default:true" json:"is_active"`
	CreatedBy uint      `json:"created_by,omitempty"`
}

// IsIPBlocked checks if an IP is blocked
func IsIPBlocked(ip string) bool {
	var block IPBlock
	err := db.GormDB.Where("ip_address = ? AND is_active = ? AND expires_at > ?",
		ip, true, time.Now()).First(&block).Error
	return err == nil
}

// HTTP Handlers

// SecurityDashboardHandler returns security monitoring dashboard
func SecurityDashboardHandler(w http.ResponseWriter, r *http.Request) {
	// Check if user is admin
	userID := getUserIDFromContext(r.Context())
	var user models.User
	if err := db.GormDB.Where("id = ?", userID).First(&user).Error; err != nil || !user.IsAdmin {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	monitor := NewSecurityMonitor()
	dashboard := monitor.GetSecurityDashboard()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(dashboard)
}

// SecurityAlertsHandler manages security alerts
func SecurityAlertsHandler(w http.ResponseWriter, r *http.Request) {
	// Check if user is admin
	userID := getUserIDFromContext(r.Context())
	var user models.User
	if err := db.GormDB.Where("id = ?", userID).First(&user).Error; err != nil || !user.IsAdmin {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	switch r.Method {
	case "GET":
		// Get alerts with pagination
		var alerts []models.SecurityAlert
		db.GormDB.Order("created_at DESC").Limit(100).Find(&alerts)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(alerts)

	case "PATCH":
		// Update alert (mark as resolved)
		var req struct {
			AlertID    uint   `json:"alert_id"`
			IsResolved bool   `json:"is_resolved"`
			Notes      string `json:"notes"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Invalid request", http.StatusBadRequest)
			return
		}

		now := time.Now()
		db.GormDB.Model(&models.SecurityAlert{}).
			Where("id = ?", req.AlertID).
			Updates(map[string]interface{}{
				"is_resolved": req.IsResolved,
				"resolved_by": userID,
				"resolved_at": now,
				"notes":       req.Notes,
			})

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{
			"message": "Alert updated successfully",
		})

	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getUserIDFromContext gets user ID from request context
func getUserIDFromContext(ctx context.Context) uint {
	if userID := ctx.Value("user_id"); userID != nil {
		if id, ok := userID.(uint); ok {
			return id
		}
	}
	return 0
}

// Stop gracefully stops the security monitor
func (sm *SecurityMonitor) Stop() {
	sm.cancel()
	close(sm.alerts)
}