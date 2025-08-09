package services

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"arx/models"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"gorm.io/gorm"
)

// MonitoringService handles system monitoring and metrics collection
type MonitoringService struct {
	db *gorm.DB

	// Prometheus metrics
	apiRequestsTotal    *prometheus.CounterVec
	apiRequestDuration  *prometheus.HistogramVec
	apiErrorsTotal      *prometheus.CounterVec
	exportJobsTotal     *prometheus.CounterVec
	exportJobDuration   *prometheus.HistogramVec
	exportJobErrors     *prometheus.CounterVec
	activeUsers         *prometheus.GaugeVec
	databaseConnections *prometheus.GaugeVec
	rateLimitHits       *prometheus.CounterVec
	securityAlerts      *prometheus.CounterVec

	// Internal metrics
	metricsMutex sync.RWMutex
	metrics      map[string]interface{}

	// Health check data
	healthMutex sync.RWMutex
	healthData  map[string]interface{}
}

// NewMonitoringService creates a new monitoring service
func NewMonitoringService(db *gorm.DB) *MonitoringService {
	ms := &MonitoringService{
		db:         db,
		metrics:    make(map[string]interface{}),
		healthData: make(map[string]interface{}),
	}

	// Initialize Prometheus metrics
	ms.initializeMetrics()

	// Start background monitoring
	go ms.startBackgroundMonitoring()

	return ms
}

// initializeMetrics sets up Prometheus metrics
func (ms *MonitoringService) initializeMetrics() {
	// API metrics
	ms.apiRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "arxos_api_requests_total",
			Help: "Total number of API requests",
		},
		[]string{"method", "endpoint", "status", "user_role"},
	)

	ms.apiRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "arxos_api_request_duration_seconds",
			Help:    "API request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "endpoint"},
	)

	ms.apiErrorsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "arxos_api_errors_total",
			Help: "Total number of API errors",
		},
		[]string{"method", "endpoint", "error_type"},
	)

	// Export metrics
	ms.exportJobsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "arxos_export_jobs_total",
			Help: "Total number of export jobs",
		},
		[]string{"export_type", "format", "status"},
	)

	ms.exportJobDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "arxos_export_job_duration_seconds",
			Help:    "Export job duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"export_type", "format"},
	)

	ms.exportJobErrors = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "arxos_export_job_errors_total",
			Help: "Total number of export job errors",
		},
		[]string{"export_type", "error_type"},
	)

	// System metrics
	ms.activeUsers = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_active_users",
			Help: "Number of active users",
		},
		[]string{"role"},
	)

	ms.databaseConnections = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_database_connections",
			Help: "Number of database connections",
		},
		[]string{"status"},
	)

	ms.rateLimitHits = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "arxos_rate_limit_hits_total",
			Help: "Total number of rate limit hits",
		},
		[]string{"client_type", "endpoint"},
	)

	ms.securityAlerts = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "arxos_security_alerts_total",
			Help: "Total number of security alerts",
		},
		[]string{"alert_type", "severity"},
	)

	// Register metrics
	prometheus.MustRegister(
		ms.apiRequestsTotal,
		ms.apiRequestDuration,
		ms.apiErrorsTotal,
		ms.exportJobsTotal,
		ms.exportJobDuration,
		ms.exportJobErrors,
		ms.activeUsers,
		ms.databaseConnections,
		ms.rateLimitHits,
		ms.securityAlerts,
	)
}

// startBackgroundMonitoring runs background monitoring tasks
func (ms *MonitoringService) startBackgroundMonitoring() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			ms.collectSystemMetrics()
			ms.updateHealthData()
		}
	}
}

// collectSystemMetrics collects system-wide metrics
func (ms *MonitoringService) collectSystemMetrics() {
	ms.metricsMutex.Lock()
	defer ms.metricsMutex.Unlock()

	// Collect active users by role
	var activeUsers []struct {
		Role  string
		Count int64
	}
	ms.db.Raw(`
		SELECT role, COUNT(*) as count
		FROM users
		WHERE last_activity > NOW() - INTERVAL '1 hour'
		GROUP BY role
	`).Scan(&activeUsers)

	for _, user := range activeUsers {
		ms.activeUsers.WithLabelValues(user.Role).Set(float64(user.Count))
	}

	// Collect database connection stats
	var dbStats struct {
		Active  int64
		Idle    int64
		MaxOpen int64
		InUse   int64
	}
	sqlDB, _ := ms.db.DB()
	dbStats.MaxOpen = int64(sqlDB.Stats().MaxOpenConnections)
	dbStats.InUse = int64(sqlDB.Stats().InUse)
	dbStats.Idle = int64(sqlDB.Stats().Idle)
	dbStats.Active = dbStats.InUse + dbStats.Idle

	ms.databaseConnections.WithLabelValues("active").Set(float64(dbStats.Active))
	ms.databaseConnections.WithLabelValues("in_use").Set(float64(dbStats.InUse))
	ms.databaseConnections.WithLabelValues("idle").Set(float64(dbStats.Idle))

	// Update internal metrics
	ms.metrics["active_users"] = activeUsers
	ms.metrics["database_stats"] = dbStats
	ms.metrics["last_updated"] = time.Now()
}

// updateHealthData updates health check data
func (ms *MonitoringService) updateHealthData() {
	ms.healthMutex.Lock()
	defer ms.healthMutex.Unlock()

	// Check database connectivity
	var dbStatus string
	var dbError error
	if err := ms.db.Raw("SELECT 1").Error; err != nil {
		dbStatus = "unhealthy"
		dbError = err
	} else {
		dbStatus = "healthy"
	}

	// Check system resources
	sqlDB, _ := ms.db.DB()
	dbStats := sqlDB.Stats()

	ms.healthData = map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now(),
		"services": map[string]interface{}{
			"database": map[string]interface{}{
				"status": dbStatus,
				"error":  dbError,
				"stats": map[string]interface{}{
					"max_open_connections": dbStats.MaxOpenConnections,
					"open_connections":     dbStats.OpenConnections,
					"in_use":               dbStats.InUse,
					"idle":                 dbStats.Idle,
				},
			},
		},
	}

	// Mark as unhealthy if any service is down
	if dbStatus == "unhealthy" {
		ms.healthData["status"] = "unhealthy"
	}
}

// RecordAPIRequest records an API request for monitoring
func (ms *MonitoringService) RecordAPIRequest(method, endpoint, status, userRole string, duration time.Duration) {
	ms.apiRequestsTotal.WithLabelValues(method, endpoint, status, userRole).Inc()
	ms.apiRequestDuration.WithLabelValues(method, endpoint).Observe(duration.Seconds())
}

// RecordAPIError records an API error for monitoring
func (ms *MonitoringService) RecordAPIError(method, endpoint, errorType string) {
	ms.apiErrorsTotal.WithLabelValues(method, endpoint, errorType).Inc()
}

// RecordExportJob records an export job for monitoring
func (ms *MonitoringService) RecordExportJob(exportType, format, status string, duration time.Duration) {
	ms.exportJobsTotal.WithLabelValues(exportType, format, status).Inc()
	if duration > 0 {
		ms.exportJobDuration.WithLabelValues(exportType, format).Observe(duration.Seconds())
	}
}

// RecordExportError records an export job error for monitoring
func (ms *MonitoringService) RecordExportError(exportType, errorType string) {
	ms.exportJobErrors.WithLabelValues(exportType, errorType).Inc()
}

// RecordRateLimitHit records a rate limit hit for monitoring
func (ms *MonitoringService) RecordRateLimitHit(clientType, endpoint string) {
	ms.rateLimitHits.WithLabelValues(clientType, endpoint).Inc()
}

// RecordSecurityAlert records a security alert for monitoring
func (ms *MonitoringService) RecordSecurityAlert(alertType, severity string) {
	ms.securityAlerts.WithLabelValues(alertType, severity).Inc()
}

// GetMetrics returns current system metrics
func (ms *MonitoringService) GetMetrics() map[string]interface{} {
	ms.metricsMutex.RLock()
	defer ms.metricsMutex.RUnlock()

	// Create a copy of metrics
	metrics := make(map[string]interface{})
	for k, v := range ms.metrics {
		metrics[k] = v
	}

	// Add real-time metrics
	metrics["timestamp"] = time.Now()
	metrics["uptime"] = time.Since(time.Now()).String()

	return metrics
}

// GetHealthStatus returns current health status
func (ms *MonitoringService) GetHealthStatus() map[string]interface{} {
	ms.healthMutex.RLock()
	defer ms.healthMutex.RUnlock()

	// Create a copy of health data
	health := make(map[string]interface{})
	for k, v := range ms.healthData {
		health[k] = v
	}

	return health
}

// GetAPIUsageStats returns API usage statistics
func (ms *MonitoringService) GetAPIUsageStats(period string) (map[string]interface{}, error) {
	var stats []struct {
		Endpoint    string  `json:"endpoint"`
		Method      string  `json:"method"`
		Count       int64   `json:"count"`
		AvgDuration float64 `json:"avg_duration"`
		ErrorCount  int64   `json:"error_count"`
	}

	timeFilter := "1 hour"
	switch period {
	case "1h":
		timeFilter = "1 hour"
	case "24h":
		timeFilter = "24 hours"
	case "7d":
		timeFilter = "7 days"
	case "30d":
		timeFilter = "30 days"
	}

	err := ms.db.Raw(`
		SELECT
			endpoint,
			method,
			COUNT(*) as count,
			AVG(response_time) as avg_duration,
			COUNT(CASE WHEN status >= 400 THEN 1 END) as error_count
		FROM api_key_usage
		WHERE created_at > NOW() - INTERVAL '` + timeFilter + `'
		GROUP BY endpoint, method
		ORDER BY count DESC
	`).Scan(&stats).Error

	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"period": period,
		"stats":  stats,
	}, nil
}

// GetExportJobStats returns export job statistics
func (ms *MonitoringService) GetExportJobStats(period string) (map[string]interface{}, error) {
	var stats []struct {
		ExportType    string  `json:"export_type"`
		Format        string  `json:"format"`
		Count         int64   `json:"count"`
		AvgDuration   float64 `json:"avg_duration"`
		TotalFileSize int64   `json:"total_file_size"`
		ErrorCount    int64   `json:"error_count"`
		SuccessRate   float64 `json:"success_rate"`
	}

	timeFilter := "1 hour"
	switch period {
	case "1h":
		timeFilter = "1 hour"
	case "24h":
		timeFilter = "24 hours"
	case "7d":
		timeFilter = "7 days"
	case "30d":
		timeFilter = "30 days"
	}

	err := ms.db.Raw(`
		SELECT
			export_type,
			format,
			COUNT(*) as count,
			AVG(processing_time) as avg_duration,
			SUM(file_size) as total_file_size,
			COUNT(CASE WHEN status = 'failed' THEN 1 END) as error_count,
			(COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*)) as success_rate
		FROM export_activities
		WHERE created_at > NOW() - INTERVAL '` + timeFilter + `'
		GROUP BY export_type, format
		ORDER BY count DESC
	`).Scan(&stats).Error

	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"period": period,
		"stats":  stats,
	}, nil
}

// GetErrorRateStats returns error rate statistics
func (ms *MonitoringService) GetErrorRateStats(period string) (map[string]interface{}, error) {
	var stats []struct {
		ErrorType  string  `json:"error_type"`
		Count      int64   `json:"count"`
		Percentage float64 `json:"percentage"`
	}

	timeFilter := "1 hour"
	switch period {
	case "1h":
		timeFilter = "1 hour"
	case "24h":
		timeFilter = "24 hours"
	case "7d":
		timeFilter = "7 days"
	case "30d":
		timeFilter = "30 days"
	}

	err := ms.db.Raw(`
		SELECT
			alert_type as error_type,
			COUNT(*) as count,
			(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM security_alerts WHERE created_at > NOW() - INTERVAL '` + timeFilter + `')) as percentage
		FROM security_alerts
		WHERE created_at > NOW() - INTERVAL '` + timeFilter + `'
		GROUP BY alert_type
		ORDER BY count DESC
	`).Scan(&stats).Error

	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"period": period,
		"stats":  stats,
	}, nil
}

// GetSystemAlerts returns recent system alerts
func (ms *MonitoringService) GetSystemAlerts(limit int) ([]models.SecurityAlert, error) {
	var alerts []models.SecurityAlert
	err := ms.db.Where("created_at > NOW() - INTERVAL '24 hours'").
		Order("created_at DESC").
		Limit(limit).
		Find(&alerts).Error

	return alerts, err
}

// StartMetricsServer starts the Prometheus metrics server
func (ms *MonitoringService) StartMetricsServer(addr string) {
	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		health := ms.GetHealthStatus()
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(health)
	})

	log.Printf("Starting metrics server on %s", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Printf("Metrics server error: %v", err)
	}
}

// LogSystemEvent logs a system event for monitoring
func (ms *MonitoringService) LogSystemEvent(eventType, message string, metadata map[string]interface{}) {
	log.Printf("[SYSTEM] %s: %s - %+v", eventType, message, metadata)

	// Store in database for historical tracking
	detailsJSON, _ := json.Marshal(metadata)

	alert := models.SecurityAlert{
		AlertType: eventType,
		Severity:  "info",
		Details:   detailsJSON,
		CreatedAt: time.Now(),
	}

	ms.db.Create(&alert)
}
