package services

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"arxos/models"
	"gorm.io/gorm"
)

// MetricCounter represents a simple counter metric
type MetricCounter struct {
	value int64
	mu    sync.RWMutex
	labels map[string]map[string]int64 // label -> value -> count
}

func NewMetricCounter() *MetricCounter {
	return &MetricCounter{
		labels: make(map[string]map[string]int64),
	}
}

func (m *MetricCounter) Inc() {
	atomic.AddInt64(&m.value, 1)
}

func (m *MetricCounter) IncWithLabels(labels ...string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	key := ""
	for i := 0; i < len(labels); i += 2 {
		if i+1 < len(labels) {
			key += labels[i] + "=" + labels[i+1] + ","
		}
	}
	
	if m.labels[key] == nil {
		m.labels[key] = make(map[string]int64)
	}
	m.labels[key]["count"]++
}

func (m *MetricCounter) Value() int64 {
	return atomic.LoadInt64(&m.value)
}

// MetricHistogram represents a simple histogram metric
type MetricHistogram struct {
	mu     sync.RWMutex
	values []float64
	sum    float64
	count  int64
}

func NewMetricHistogram() *MetricHistogram {
	return &MetricHistogram{
		values: make([]float64, 0, 1000),
	}
}

func (m *MetricHistogram) Observe(value float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.values = append(m.values, value)
	m.sum += value
	m.count++
	
	// Keep only last 1000 values to prevent memory growth
	if len(m.values) > 1000 {
		m.values = m.values[len(m.values)-1000:]
	}
}

func (m *MetricHistogram) Summary() map[string]float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	if m.count == 0 {
		return map[string]float64{"count": 0, "sum": 0, "avg": 0}
	}
	
	return map[string]float64{
		"count": float64(m.count),
		"sum":   m.sum,
		"avg":   m.sum / float64(m.count),
	}
}

// MetricGauge represents a simple gauge metric
type MetricGauge struct {
	value float64
	mu    sync.RWMutex
}

func NewMetricGauge() *MetricGauge {
	return &MetricGauge{}
}

func (m *MetricGauge) Set(value float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.value = value
}

func (m *MetricGauge) Value() float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.value
}

// MonitoringService handles system monitoring and metrics collection
type MonitoringService struct {
	db *gorm.DB

	// Simple metrics
	apiRequestsTotal    *MetricCounter
	apiRequestDuration  *MetricHistogram
	apiErrorsTotal      *MetricCounter
	exportJobsTotal     *MetricCounter
	exportJobDuration   *MetricHistogram
	exportJobErrors     *MetricCounter
	activeUsers         *MetricGauge
	databaseConnections *MetricGauge
	rateLimitHits       *MetricCounter
	securityAlerts      *MetricCounter

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
		db:                  db,
		metrics:            make(map[string]interface{}),
		healthData:         make(map[string]interface{}),
		apiRequestsTotal:    NewMetricCounter(),
		apiRequestDuration:  NewMetricHistogram(),
		apiErrorsTotal:      NewMetricCounter(),
		exportJobsTotal:     NewMetricCounter(),
		exportJobDuration:   NewMetricHistogram(),
		exportJobErrors:     NewMetricCounter(),
		activeUsers:         NewMetricGauge(),
		databaseConnections: NewMetricGauge(),
		rateLimitHits:       NewMetricCounter(),
		securityAlerts:      NewMetricCounter(),
	}

	// Start background monitoring
	go ms.startBackgroundMonitoring()

	return ms
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

	totalActiveUsers := int64(0)
	for _, user := range activeUsers {
		totalActiveUsers += user.Count
	}
	ms.activeUsers.Set(float64(totalActiveUsers))

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

	ms.databaseConnections.Set(float64(dbStats.Active))

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
	ms.apiRequestsTotal.IncWithLabels("method", method, "endpoint", endpoint, "status", status, "user_role", userRole)
	ms.apiRequestDuration.Observe(duration.Seconds())
}

// RecordAPIError records an API error for monitoring
func (ms *MonitoringService) RecordAPIError(method, endpoint, errorType string) {
	ms.apiErrorsTotal.IncWithLabels("method", method, "endpoint", endpoint, "error_type", errorType)
}

// RecordExportJob records an export job for monitoring
func (ms *MonitoringService) RecordExportJob(exportType, format, status string, duration time.Duration) {
	ms.exportJobsTotal.IncWithLabels("export_type", exportType, "format", format, "status", status)
	if duration > 0 {
		ms.exportJobDuration.Observe(duration.Seconds())
	}
}

// RecordExportError records an export job error for monitoring
func (ms *MonitoringService) RecordExportError(exportType, errorType string) {
	ms.exportJobErrors.IncWithLabels("export_type", exportType, "error_type", errorType)
}

// RecordRateLimitHit records a rate limit hit for monitoring
func (ms *MonitoringService) RecordRateLimitHit(clientType, endpoint string) {
	ms.rateLimitHits.IncWithLabels("client_type", clientType, "endpoint", endpoint)
}

// RecordSecurityAlert records a security alert for monitoring
func (ms *MonitoringService) RecordSecurityAlert(alertType, severity string) {
	ms.securityAlerts.IncWithLabels("alert_type", alertType, "severity", severity)
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
	metrics["api_requests_total"] = ms.apiRequestsTotal.Value()
	metrics["api_request_duration"] = ms.apiRequestDuration.Summary()
	metrics["api_errors_total"] = ms.apiErrorsTotal.Value()
	metrics["export_jobs_total"] = ms.exportJobsTotal.Value()
	metrics["export_job_duration"] = ms.exportJobDuration.Summary()
	metrics["export_job_errors"] = ms.exportJobErrors.Value()
	metrics["active_users"] = ms.activeUsers.Value()
	metrics["database_connections"] = ms.databaseConnections.Value()
	metrics["rate_limit_hits"] = ms.rateLimitHits.Value()
	metrics["security_alerts"] = ms.securityAlerts.Value()

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

// StartMetricsServer starts the metrics server
func (ms *MonitoringService) StartMetricsServer(addr string) {
	http.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		metrics := ms.GetMetrics()
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(metrics)
	})
	
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