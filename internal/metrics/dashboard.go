package metrics

import (
	"encoding/json"
	"fmt"
	"net/http"
	"runtime"
	"sync"
	"time"
)

// Dashboard provides a comprehensive metrics dashboard
type Dashboard struct {
	serviceName   string
	collector     *Collector
	systemMonitor *SystemMonitor
	mu            sync.RWMutex

	// Dashboard data
	lastUpdate    time.Time
	refreshRate   time.Duration
	alertRules    []AlertRule
	notifications []Notification
}

// AlertRule defines when to trigger alerts
type AlertRule struct {
	Name        string
	Metric      string
	Threshold   float64
	Operator    string // "gt", "lt", "eq", "gte", "lte"
	Duration    time.Duration
	Severity    string
	Description string
	Enabled     bool
}

// Notification represents a dashboard notification
type Notification struct {
	ID        string
	Type      string
	Title     string
	Message   string
	Severity  string
	Timestamp time.Time
	Read      bool
}

// DashboardData represents the complete dashboard data
type DashboardData struct {
	ServiceName string    `json:"service_name"`
	Environment string    `json:"environment"`
	Version     string    `json:"version"`
	Uptime      string    `json:"uptime"`
	Timestamp   time.Time `json:"timestamp"`

	// System metrics
	SystemInfo SystemInfo `json:"system_info"`

	// Service metrics
	ServiceMetrics map[string]interface{} `json:"service_metrics"`

	// Operation metrics
	OperationMetrics map[string]OperationMetrics `json:"operation_metrics"`

	// Error metrics
	ErrorMetrics ErrorMetrics `json:"error_metrics"`

	// Performance metrics
	PerformanceMetrics PerformanceMetrics `json:"performance_metrics"`

	// Alerts and notifications
	Alerts        []Alert        `json:"alerts"`
	Notifications []Notification `json:"notifications"`

	// Health status
	HealthStatus HealthStatus `json:"health_status"`
}

// SystemInfo provides system information
type SystemInfo struct {
	GoVersion    string  `json:"go_version"`
	NumCPU       int     `json:"num_cpu"`
	NumGoroutine int     `json:"num_goroutine"`
	MemoryMB     float64 `json:"memory_mb"`
	CPUPercent   float64 `json:"cpu_percent"`
	OpenFiles    int     `json:"open_files"`
	Uptime       string  `json:"uptime"`
}

// OperationMetrics provides metrics for a specific operation
type OperationMetrics struct {
	Operation       string  `json:"operation"`
	TotalCount      int64   `json:"total_count"`
	SuccessCount    int64   `json:"success_count"`
	ErrorCount      int64   `json:"error_count"`
	RetryCount      int64   `json:"retry_count"`
	AverageDuration float64 `json:"average_duration_ms"`
	MinDuration     float64 `json:"min_duration_ms"`
	MaxDuration     float64 `json:"max_duration_ms"`
	P95Duration     float64 `json:"p95_duration_ms"`
	P99Duration     float64 `json:"p99_duration_ms"`
	ErrorRate       float64 `json:"error_rate"`
	Throughput      float64 `json:"throughput_per_second"`
	IsActive        bool    `json:"is_active"`
}

// ErrorMetrics provides error-related metrics
type ErrorMetrics struct {
	TotalErrors     int64            `json:"total_errors"`
	ErrorRate       float64          `json:"error_rate"`
	ErrorTypes      map[string]int64 `json:"error_types"`
	ServiceErrors   map[string]int64 `json:"service_errors"`
	OperationErrors map[string]int64 `json:"operation_errors"`
	RecentErrors    []ErrorEvent     `json:"recent_errors"`
}

// ErrorEvent represents a recent error event
type ErrorEvent struct {
	Timestamp time.Time `json:"timestamp"`
	Service   string    `json:"service"`
	Operation string    `json:"operation"`
	Error     string    `json:"error"`
	Count     int64     `json:"count"`
}

// PerformanceMetrics provides performance-related metrics
type PerformanceMetrics struct {
	AverageResponseTime float64            `json:"average_response_time_ms"`
	P95ResponseTime     float64            `json:"p95_response_time_ms"`
	P99ResponseTime     float64            `json:"p99_response_time_ms"`
	Throughput          float64            `json:"throughput_per_second"`
	ConcurrentOps       int64              `json:"concurrent_operations"`
	CircuitBreakers     map[string]int     `json:"circuit_breakers"`
	FallbackUsage       map[string]int64   `json:"fallback_usage"`
	RetryRates          map[string]float64 `json:"retry_rates"`
}

// Alert represents an active alert
type Alert struct {
	ID           string    `json:"id"`
	Rule         string    `json:"rule"`
	Metric       string    `json:"metric"`
	Value        float64   `json:"value"`
	Threshold    float64   `json:"threshold"`
	Severity     string    `json:"severity"`
	Message      string    `json:"message"`
	Timestamp    time.Time `json:"timestamp"`
	Acknowledged bool      `json:"acknowledged"`
}

// HealthStatus represents the overall health status
type HealthStatus struct {
	Status      string            `json:"status"` // "healthy", "degraded", "unhealthy"
	Score       float64           `json:"score"`  // 0-100
	Checks      map[string]string `json:"checks"`
	LastCheck   time.Time         `json:"last_check"`
	Description string            `json:"description"`
}

// NewDashboard creates a new metrics dashboard
func NewDashboard(serviceName string) *Dashboard {
	return &Dashboard{
		serviceName:   serviceName,
		collector:     GetCollector(),
		refreshRate:   30 * time.Second,
		alertRules:    make([]AlertRule, 0),
		notifications: make([]Notification, 0),
	}
}

// AddAlertRule adds an alert rule to the dashboard
func (d *Dashboard) AddAlertRule(rule AlertRule) {
	d.mu.Lock()
	defer d.mu.Unlock()

	d.alertRules = append(d.alertRules, rule)
}

// AddNotification adds a notification to the dashboard
func (d *Dashboard) AddNotification(notification Notification) {
	d.mu.Lock()
	defer d.mu.Unlock()

	notification.ID = fmt.Sprintf("notif_%d", time.Now().UnixNano())
	notification.Timestamp = time.Now()

	d.notifications = append(d.notifications, notification)

	// Keep only last 100 notifications
	if len(d.notifications) > 100 {
		d.notifications = d.notifications[len(d.notifications)-100:]
	}
}

// GetDashboardData returns the complete dashboard data
func (d *Dashboard) GetDashboardData() *DashboardData {
	d.mu.Lock()
	defer d.mu.Unlock()

	now := time.Now()

	data := &DashboardData{
		ServiceName:        d.serviceName,
		Environment:        "production", // This would come from config
		Version:            "2.0.0",      // This would come from build info
		Uptime:             d.getRealUptime(),
		Timestamp:          now,
		SystemInfo:         d.getSystemInfo(),
		ServiceMetrics:     d.getServiceMetrics(),
		OperationMetrics:   d.getOperationMetrics(),
		ErrorMetrics:       d.getErrorMetrics(),
		PerformanceMetrics: d.getPerformanceMetrics(),
		Alerts:             d.getActiveAlerts(),
		Notifications:      d.getNotifications(),
		HealthStatus:       d.getHealthStatus(),
	}

	d.lastUpdate = now
	return data
}

// getSystemInfo returns current system information
func (d *Dashboard) getSystemInfo() SystemInfo {
	// Use system monitor if available, otherwise fallback to basic info
	if d.systemMonitor != nil {
		systemInfo := d.systemMonitor.GetSystemInfo()
		return SystemInfo{
			GoVersion:    runtime.Version(),
			NumCPU:       runtime.NumCPU(),
			NumGoroutine: systemInfo.GoroutineCount,
			MemoryMB:     systemInfo.MemoryUsage,
			CPUPercent:   systemInfo.CPUUsage,
			OpenFiles:    0, // Would need to be calculated
			Uptime:       systemInfo.Uptime,
		}
	}

	// Fallback to basic system information
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	return SystemInfo{
		GoVersion:    runtime.Version(),
		NumCPU:       runtime.NumCPU(),
		NumGoroutine: runtime.NumGoroutine(),
		MemoryMB:     float64(m.Alloc) / 1024 / 1024,
		CPUPercent:   0, // Would need to be calculated
		OpenFiles:    0, // Would need to be calculated
		Uptime:       d.getRealUptime(),
	}
}

// getRealUptime returns the actual service uptime
func (d *Dashboard) getRealUptime() string {
	if d.systemMonitor != nil {
		systemInfo := d.systemMonitor.GetSystemInfo()
		return systemInfo.Uptime
	}

	// Fallback to time since last update
	return time.Since(d.lastUpdate).String()
}

// getServiceMetrics returns service-level metrics
func (d *Dashboard) getServiceMetrics() map[string]interface{} {
	metrics := make(map[string]interface{})

	// Get service metrics summary
	serviceSummaries := GetServiceMetricsSummary()
	if summary, exists := serviceSummaries[d.serviceName]; exists {
		metrics["total_operations"] = summary.TotalOperations
		metrics["successful_operations"] = summary.SuccessfulOperations
		metrics["failed_operations"] = summary.FailedOperations
		metrics["error_rate"] = summary.ErrorRate
		metrics["average_duration"] = summary.AverageDuration
		metrics["concurrent_operations"] = summary.ConcurrentOps
	}

	return metrics
}

// getOperationMetrics returns operation-level metrics
func (d *Dashboard) getOperationMetrics() map[string]OperationMetrics {
	operationMetrics := make(map[string]OperationMetrics)

	// Get instrumentation for this service
	instrumentation := GetInstrumentation(d.serviceName)
	if instrumentation == nil {
		return operationMetrics
	}

	// Get operation stats
	stats := instrumentation.GetOperationStats()
	for operation, stat := range stats {
		operationMetrics[operation] = OperationMetrics{
			Operation:       operation,
			TotalCount:      stat.TotalCount,
			SuccessCount:    stat.TotalCount - stat.ErrorCount,
			ErrorCount:      stat.ErrorCount,
			RetryCount:      stat.RetryCount,
			AverageDuration: 0, // This would need to be calculated
			MinDuration:     0, // This would need to be calculated
			MaxDuration:     0, // This would need to be calculated
			P95Duration:     0, // This would need to be calculated
			P99Duration:     0, // This would need to be calculated
			ErrorRate:       float64(stat.ErrorCount) / float64(stat.TotalCount),
			Throughput:      0, // This would need to be calculated
			IsActive:        stat.IsActive,
		}
	}

	return operationMetrics
}

// getErrorMetrics returns error-related metrics
func (d *Dashboard) getErrorMetrics() ErrorMetrics {
	errorMetrics := ErrorMetrics{
		ErrorTypes:      make(map[string]int64),
		ServiceErrors:   make(map[string]int64),
		OperationErrors: make(map[string]int64),
		RecentErrors:    make([]ErrorEvent, 0),
	}

	// Get error metrics from all services
	allInstrumentation := GetAllInstrumentation()
	for serviceName, instrumentation := range allInstrumentation {
		stats := instrumentation.GetOperationStats()
		for operation, stat := range stats {
			errorMetrics.TotalErrors += stat.ErrorCount
			errorMetrics.ServiceErrors[serviceName] += stat.ErrorCount
			errorMetrics.OperationErrors[operation] += stat.ErrorCount
		}
	}

	// Calculate error rate
	totalOps := int64(0)
	for _, stat := range d.getOperationMetrics() {
		totalOps += stat.TotalCount
	}

	if totalOps > 0 {
		errorMetrics.ErrorRate = float64(errorMetrics.TotalErrors) / float64(totalOps)
	}

	return errorMetrics
}

// getPerformanceMetrics returns performance-related metrics
func (d *Dashboard) getPerformanceMetrics() PerformanceMetrics {
	performanceMetrics := PerformanceMetrics{
		CircuitBreakers: make(map[string]int),
		FallbackUsage:   make(map[string]int64),
		RetryRates:      make(map[string]float64),
	}

	// Get performance metrics from service metrics
	serviceSummaries := GetServiceMetricsSummary()
	if summary, exists := serviceSummaries[d.serviceName]; exists {
		performanceMetrics.AverageResponseTime = summary.AverageDuration * 1000 // Convert to ms
		performanceMetrics.ConcurrentOps = summary.ConcurrentOps
		performanceMetrics.CircuitBreakers = summary.CircuitBreakerState
	}

	return performanceMetrics
}

// getActiveAlerts returns currently active alerts
func (d *Dashboard) getActiveAlerts() []Alert {
	alerts := make([]Alert, 0)

	// Check alert rules
	for _, rule := range d.alertRules {
		if !rule.Enabled {
			continue
		}

		// Get metric value (simplified)
		value := d.getMetricValue(rule.Metric)

		// Check if alert should trigger
		shouldAlert := false
		switch rule.Operator {
		case "gt":
			shouldAlert = value > rule.Threshold
		case "lt":
			shouldAlert = value < rule.Threshold
		case "eq":
			shouldAlert = value == rule.Threshold
		case "gte":
			shouldAlert = value >= rule.Threshold
		case "lte":
			shouldAlert = value <= rule.Threshold
		}

		if shouldAlert {
			alert := Alert{
				ID:        fmt.Sprintf("alert_%d", time.Now().UnixNano()),
				Rule:      rule.Name,
				Metric:    rule.Metric,
				Value:     value,
				Threshold: rule.Threshold,
				Severity:  rule.Severity,
				Message:   rule.Description,
				Timestamp: time.Now(),
			}
			alerts = append(alerts, alert)
		}
	}

	return alerts
}

// getNotifications returns dashboard notifications
func (d *Dashboard) getNotifications() []Notification {
	// Return last 20 notifications
	notifications := make([]Notification, 0, 20)
	start := len(d.notifications) - 20
	if start < 0 {
		start = 0
	}

	for i := start; i < len(d.notifications); i++ {
		notifications = append(notifications, d.notifications[i])
	}

	return notifications
}

// getHealthStatus returns the overall health status
func (d *Dashboard) getHealthStatus() HealthStatus {
	checks := make(map[string]string)
	score := 100.0

	// Check system health
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	// Memory usage check
	memoryUsageMB := float64(m.Alloc) / 1024 / 1024
	if memoryUsageMB > 1000 { // 1GB threshold
		checks["memory"] = "high"
		score -= 20
	} else {
		checks["memory"] = "ok"
	}

	// Goroutine count check
	goroutines := runtime.NumGoroutine()
	if goroutines > 1000 {
		checks["goroutines"] = "high"
		score -= 20
	} else {
		checks["goroutines"] = "ok"
	}

	// Error rate check
	errorMetrics := d.getErrorMetrics()
	if errorMetrics.ErrorRate > 0.1 { // 10% error rate threshold
		checks["error_rate"] = "high"
		score -= 30
	} else {
		checks["error_rate"] = "ok"
	}

	// Determine overall status
	status := "healthy"
	if score < 50 {
		status = "unhealthy"
	} else if score < 80 {
		status = "degraded"
	}

	return HealthStatus{
		Status:      status,
		Score:       score,
		Checks:      checks,
		LastCheck:   time.Now(),
		Description: fmt.Sprintf("Health score: %.1f/100", score),
	}
}

// getMetricValue gets the value of a metric (simplified)
func (d *Dashboard) getMetricValue(metricName string) float64 {
	// This is a simplified implementation
	// In a real system, you would query the actual metric values
	switch metricName {
	case "error_rate":
		errorMetrics := d.getErrorMetrics()
		return errorMetrics.ErrorRate
	case "memory_usage":
		var m runtime.MemStats
		runtime.ReadMemStats(&m)
		return float64(m.Alloc) / 1024 / 1024
	case "goroutine_count":
		return float64(runtime.NumGoroutine())
	default:
		return 0
	}
}

// HTTP handlers for dashboard

// HandleDashboard returns the dashboard data as JSON
func (d *Dashboard) HandleDashboard(w http.ResponseWriter, r *http.Request) {
	data := d.GetDashboardData()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// HandleDashboardHTML returns the dashboard as HTML
func (d *Dashboard) HandleDashboardHTML(w http.ResponseWriter, r *http.Request) {
	data := d.GetDashboardData()

	html := d.generateDashboardHTML(data)

	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

// generateDashboardHTML generates HTML for the dashboard
func (d *Dashboard) generateDashboardHTML(data *DashboardData) string {
	// This is a simplified HTML template
	// In a real system, you would use a proper template engine
	return fmt.Sprintf(`
<!DOCTYPE html>
<html>
<head>
    <title>ArxOS Metrics Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .metric { background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .metric h3 { margin: 0 0 10px 0; color: #333; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .status-healthy { color: #28a745; }
        .status-degraded { color: #ffc107; }
        .status-unhealthy { color: #dc3545; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ArxOS Metrics Dashboard</h1>
        <p>Service: %s | Environment: %s | Version: %s</p>
        <p>Uptime: %s | Last Updated: %s</p>
    </div>
    
    <div class="grid">
        <div class="metric">
            <h3>System Health</h3>
            <div class="metric-value status-%s">%s</div>
            <p>Score: %.1f/100</p>
        </div>
        
        <div class="metric">
            <h3>Total Operations</h3>
            <div class="metric-value">%d</div>
        </div>
        
        <div class="metric">
            <h3>Error Rate</h3>
            <div class="metric-value">%.2f%%</div>
        </div>
        
        <div class="metric">
            <h3>Memory Usage</h3>
            <div class="metric-value">%.1f MB</div>
        </div>
        
        <div class="metric">
            <h3>Goroutines</h3>
            <div class="metric-value">%d</div>
        </div>
        
        <div class="metric">
            <h3>Concurrent Operations</h3>
            <div class="metric-value">%d</div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
`, data.ServiceName, data.Environment, data.Version, data.Uptime, data.Timestamp.Format(time.RFC3339),
		data.HealthStatus.Status, data.HealthStatus.Status, data.HealthStatus.Score,
		data.ServiceMetrics["total_operations"],
		data.ErrorMetrics.ErrorRate*100,
		data.SystemInfo.MemoryMB,
		data.SystemInfo.NumGoroutine,
		data.ServiceMetrics["concurrent_operations"])
}

// StartAutoRefresh starts automatic dashboard refresh
func (d *Dashboard) StartAutoRefresh() {
	ticker := time.NewTicker(d.refreshRate)
	go func() {
		for range ticker.C {
			// Dashboard data is generated on-demand, so no need to refresh here
			// But we could add caching or other refresh logic here
		}
	}()
}

// Global dashboard instance
var (
	globalDashboard *Dashboard
	dashboardOnce   sync.Once
)

// GetDashboard returns the global dashboard instance
func GetDashboard(serviceName string) *Dashboard {
	dashboardOnce.Do(func() {
		globalDashboard = NewDashboard(serviceName)
		globalDashboard.StartAutoRefresh()
	})
	return globalDashboard
}
