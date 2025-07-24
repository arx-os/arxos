package services

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"runtime"
	"sync"
	"time"

	"arx/models"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
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

	// Enhanced metrics
	systemMemoryUsage     *prometheus.GaugeVec
	systemCPUUsage        *prometheus.GaugeVec
	systemDiskUsage       *prometheus.GaugeVec
	goroutineCount        *prometheus.GaugeVec
	heapAllocBytes        *prometheus.GaugeVec
	heapSysBytes          *prometheus.GaugeVec
	gcDuration            *prometheus.HistogramVec
	svgxProcessingTime    *prometheus.HistogramVec
	svgxElementsProcessed *prometheus.CounterVec
	svgxValidationResults *prometheus.CounterVec
	cacheHitRate          *prometheus.GaugeVec
	cacheSize             *prometheus.GaugeVec
	exportFileSize        *prometheus.HistogramVec
	concurrentRequests    *prometheus.GaugeVec
	responseTimeP95       *prometheus.GaugeVec
	responseTimeP99       *prometheus.GaugeVec

	// Internal metrics
	metricsMutex sync.RWMutex
	metrics      map[string]interface{}

	// Health check data
	healthMutex sync.RWMutex
	healthData  map[string]interface{}

	// Real-time monitoring
	monitoringActive bool
	monitorCtx       context.Context
	monitorCancel    context.CancelFunc

	// Alerting
	alertHandlers []AlertHandler
	alertMutex    sync.RWMutex

	// Performance tracking
	performanceData map[string]*PerformanceTracker
	perfMutex       sync.RWMutex
}

// AlertHandler defines the interface for alert handlers
type AlertHandler interface {
	HandleAlert(alert *SecurityAlert) error
}

// SecurityAlert represents a security alert
type SecurityAlert struct {
	ID        string                 `json:"id"`
	Type      string                 `json:"type"`
	Severity  string                 `json:"severity"`
	Message   string                 `json:"message"`
	Timestamp time.Time              `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata"`
	Source    string                 `json:"source"`
	UserID    string                 `json:"user_id,omitempty"`
	IPAddress string                 `json:"ip_address,omitempty"`
	Resource  string                 `json:"resource,omitempty"`
}

// PerformanceTracker tracks performance metrics
type PerformanceTracker struct {
	Count       int64         `json:"count"`
	TotalTime   time.Duration `json:"total_time"`
	MinTime     time.Duration `json:"min_time"`
	MaxTime     time.Duration `json:"max_time"`
	LastUpdated time.Time     `json:"last_updated"`
	mutex       sync.RWMutex
}

// NewMonitoringService creates a new monitoring service
func NewMonitoringService(db *gorm.DB) *MonitoringService {
	ctx, cancel := context.WithCancel(context.Background())

	ms := &MonitoringService{
		db:               db,
		metrics:          make(map[string]interface{}),
		healthData:       make(map[string]interface{}),
		monitoringActive: true,
		monitorCtx:       ctx,
		monitorCancel:    cancel,
		performanceData:  make(map[string]*PerformanceTracker),
		alertHandlers:    make([]AlertHandler, 0),
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

	// Enhanced system metrics
	ms.systemMemoryUsage = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_system_memory_usage_bytes",
			Help: "System memory usage in bytes",
		},
		[]string{"type"},
	)

	ms.systemCPUUsage = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_system_cpu_usage_percent",
			Help: "System CPU usage percentage",
		},
		[]string{"core"},
	)

	ms.systemDiskUsage = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_system_disk_usage_bytes",
			Help: "System disk usage in bytes",
		},
		[]string{"mountpoint"},
	)

	ms.goroutineCount = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_goroutines_total",
			Help: "Number of goroutines",
		},
		[]string{},
	)

	ms.heapAllocBytes = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_heap_alloc_bytes",
			Help: "Heap memory allocated in bytes",
		},
		[]string{},
	)

	ms.heapSysBytes = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_heap_sys_bytes",
			Help: "Heap memory system bytes",
		},
		[]string{},
	)

	ms.gcDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "arxos_gc_duration_seconds",
			Help:    "Garbage collection duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{},
	)

	// SVGX-specific metrics
	ms.svgxProcessingTime = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "arxos_svgx_processing_duration_seconds",
			Help:    "SVGX processing duration in seconds",
			Buckets: []float64{0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0},
		},
		[]string{"operation", "element_type"},
	)

	ms.svgxElementsProcessed = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "arxos_svgx_elements_processed_total",
			Help: "Total number of SVGX elements processed",
		},
		[]string{"element_type", "operation", "status"},
	)

	ms.svgxValidationResults = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "arxos_svgx_validation_results_total",
			Help: "Total number of SVGX validation results",
		},
		[]string{"validation_type", "result"},
	)

	// Cache metrics
	ms.cacheHitRate = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_cache_hit_rate",
			Help: "Cache hit rate percentage",
		},
		[]string{"cache_type"},
	)

	ms.cacheSize = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_cache_size",
			Help: "Cache size in bytes",
		},
		[]string{"cache_type"},
	)

	// Export metrics
	ms.exportFileSize = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "arxos_export_file_size_bytes",
			Help:    "Export file size in bytes",
			Buckets: []float64{1024, 10240, 102400, 1048576, 10485760, 104857600},
		},
		[]string{"export_type", "format"},
	)

	// Performance metrics
	ms.concurrentRequests = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_concurrent_requests",
			Help: "Number of concurrent requests",
		},
		[]string{"endpoint"},
	)

	ms.responseTimeP95 = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_response_time_p95_seconds",
			Help: "95th percentile response time in seconds",
		},
		[]string{"endpoint"},
	)

	ms.responseTimeP99 = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "arxos_response_time_p99_seconds",
			Help: "99th percentile response time in seconds",
		},
		[]string{"endpoint"},
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
		ms.systemMemoryUsage,
		ms.systemCPUUsage,
		ms.systemDiskUsage,
		ms.goroutineCount,
		ms.heapAllocBytes,
		ms.heapSysBytes,
		ms.gcDuration,
		ms.svgxProcessingTime,
		ms.svgxElementsProcessed,
		ms.svgxValidationResults,
		ms.cacheHitRate,
		ms.cacheSize,
		ms.exportFileSize,
		ms.concurrentRequests,
		ms.responseTimeP95,
		ms.responseTimeP99,
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
			ms.collectPerformanceMetrics()
		case <-ms.monitorCtx.Done():
			return
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

	// Collect system metrics
	ms.collectSystemResources()

	// Update internal metrics
	ms.metrics["active_users"] = activeUsers
	ms.metrics["database_stats"] = dbStats
	ms.metrics["last_updated"] = time.Now()
}

// collectSystemResources collects system resource metrics
func (ms *MonitoringService) collectSystemResources() {
	// Memory metrics
	if memory, err := mem.VirtualMemory(); err == nil {
		ms.systemMemoryUsage.WithLabelValues("total").Set(float64(memory.Total))
		ms.systemMemoryUsage.WithLabelValues("used").Set(float64(memory.Used))
		ms.systemMemoryUsage.WithLabelValues("available").Set(float64(memory.Available))
		ms.systemMemoryUsage.WithLabelValues("cached").Set(float64(memory.Cached))
	}

	// CPU metrics
	if cpuPercentages, err := cpu.Percent(0, true); err == nil {
		for i, percentage := range cpuPercentages {
			ms.systemCPUUsage.WithLabelValues(fmt.Sprintf("core_%d", i)).Set(percentage)
		}
	}

	// Disk metrics
	if partitions, err := disk.Partitions(false); err == nil {
		for _, partition := range partitions {
			if usage, err := disk.Usage(partition.Mountpoint); err == nil {
				ms.systemDiskUsage.WithLabelValues(partition.Mountpoint).Set(float64(usage.Used))
			}
		}
	}

	// Go runtime metrics
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	ms.goroutineCount.WithLabelValues().Set(float64(runtime.NumGoroutine()))
	ms.heapAllocBytes.WithLabelValues().Set(float64(m.HeapAlloc))
	ms.heapSysBytes.WithLabelValues().Set(float64(m.HeapSys))
}

// collectPerformanceMetrics collects performance metrics
func (ms *MonitoringService) collectPerformanceMetrics() {
	ms.perfMutex.Lock()
	defer ms.perfMutex.Unlock()

	for operation, tracker := range ms.performanceData {
		tracker.mutex.RLock()
		if tracker.Count > 0 {
			avgTime := tracker.TotalTime.Seconds() / float64(tracker.Count)
			ms.svgxProcessingTime.WithLabelValues(operation, "unknown").Observe(avgTime)
		}
		tracker.mutex.RUnlock()
	}
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

	// Check memory health
	memoryHealth := "healthy"
	if memory, err := mem.VirtualMemory(); err == nil {
		if memory.UsedPercent > 90 {
			memoryHealth = "critical"
		} else if memory.UsedPercent > 80 {
			memoryHealth = "warning"
		}
	}

	// Check disk health
	diskHealth := "healthy"
	if partitions, err := disk.Partitions(false); err == nil {
		for _, partition := range partitions {
			if usage, err := disk.Usage(partition.Mountpoint); err == nil {
				if usage.UsedPercent > 90 {
					diskHealth = "critical"
					break
				} else if usage.UsedPercent > 80 {
					diskHealth = "warning"
				}
			}
		}
	}

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
			"memory": map[string]interface{}{
				"status": memoryHealth,
			},
			"disk": map[string]interface{}{
				"status": diskHealth,
			},
		},
	}

	// Mark as unhealthy if any service is down
	if dbStatus == "unhealthy" || memoryHealth == "critical" || diskHealth == "critical" {
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

// RecordSVGXProcessing records SVGX processing metrics
func (ms *MonitoringService) RecordSVGXProcessing(operation, elementType string, duration time.Duration) {
	ms.svgxProcessingTime.WithLabelValues(operation, elementType).Observe(duration.Seconds())
}

// RecordSVGXElement records SVGX element processing
func (ms *MonitoringService) RecordSVGXElement(elementType, operation, status string) {
	ms.svgxElementsProcessed.WithLabelValues(elementType, operation, status).Inc()
}

// RecordValidationResult records validation results
func (ms *MonitoringService) RecordValidationResult(validationType, result string) {
	ms.svgxValidationResults.WithLabelValues(validationType, result).Inc()
}

// UpdateCacheMetrics updates cache metrics
func (ms *MonitoringService) UpdateCacheMetrics(cacheType string, hitRate float64, sizeBytes int64) {
	ms.cacheHitRate.WithLabelValues(cacheType).Set(hitRate)
	ms.cacheSize.WithLabelValues(cacheType).Set(float64(sizeBytes))
}

// RecordExportFileSize records export file size
func (ms *MonitoringService) RecordExportFileSize(exportType, format string, sizeBytes int64) {
	ms.exportFileSize.WithLabelValues(exportType, format).Observe(float64(sizeBytes))
}

// UpdateConcurrentRequests updates concurrent requests metric
func (ms *MonitoringService) UpdateConcurrentRequests(endpoint string, count int) {
	ms.concurrentRequests.WithLabelValues(endpoint).Set(float64(count))
}

// UpdateResponseTimePercentiles updates response time percentiles
func (ms *MonitoringService) UpdateResponseTimePercentiles(endpoint string, p95, p99 float64) {
	ms.responseTimeP95.WithLabelValues(endpoint).Set(p95)
	ms.responseTimeP99.WithLabelValues(endpoint).Set(p99)
}

// TrackPerformance tracks performance for an operation
func (ms *MonitoringService) TrackPerformance(operation string, duration time.Duration) {
	ms.perfMutex.Lock()
	defer ms.perfMutex.Unlock()

	tracker, exists := ms.performanceData[operation]
	if !exists {
		tracker = &PerformanceTracker{
			MinTime:     duration,
			MaxTime:     duration,
			LastUpdated: time.Now(),
		}
		ms.performanceData[operation] = tracker
	}

	tracker.mutex.Lock()
	tracker.Count++
	tracker.TotalTime += duration
	if duration < tracker.MinTime {
		tracker.MinTime = duration
	}
	if duration > tracker.MaxTime {
		tracker.MaxTime = duration
	}
	tracker.LastUpdated = time.Now()
	tracker.mutex.Unlock()
}

// AddAlertHandler adds an alert handler
func (ms *MonitoringService) AddAlertHandler(handler AlertHandler) {
	ms.alertMutex.Lock()
	defer ms.alertMutex.Unlock()
	ms.alertHandlers = append(ms.alertHandlers, handler)
}

// TriggerAlert triggers a security alert
func (ms *MonitoringService) TriggerAlert(alert *SecurityAlert) {
	ms.alertMutex.RLock()
	defer ms.alertMutex.RUnlock()

	// Record in metrics
	ms.securityAlerts.WithLabelValues(alert.Type, alert.Severity).Inc()

	// Trigger handlers
	for _, handler := range ms.alertHandlers {
		go func(h AlertHandler) {
			if err := h.HandleAlert(alert); err != nil {
				log.Printf("Alert handler error: %v", err)
			}
		}(handler)
	}
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

// GetPerformanceData returns performance tracking data
func (ms *MonitoringService) GetPerformanceData() map[string]*PerformanceTracker {
	ms.perfMutex.RLock()
	defer ms.perfMutex.RUnlock()

	// Create a copy of performance data
	perfData := make(map[string]*PerformanceTracker)
	for k, v := range ms.performanceData {
		perfData[k] = &PerformanceTracker{
			Count:       v.Count,
			TotalTime:   v.TotalTime,
			MinTime:     v.MinTime,
			MaxTime:     v.MaxTime,
			LastUpdated: v.LastUpdated,
		}
	}

	return perfData
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

// Stop stops the monitoring service
func (ms *MonitoringService) Stop() {
	ms.monitoringActive = false
	ms.monitorCancel()
}
