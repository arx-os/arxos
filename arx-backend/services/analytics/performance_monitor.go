package analytics

import (
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// PerformanceMetric represents a performance metric
type PerformanceMetric struct {
	ID          string                 `json:"id" gorm:"primaryKey"`
	MetricType  string                 `json:"metric_type"`
	MetricName  string                 `json:"metric_name"`
	MetricValue float64                `json:"metric_value"`
	Unit        string                 `json:"unit"`
	Threshold   *float64               `json:"threshold"`
	Status      string                 `json:"status"`
	Severity    string                 `json:"severity"`
	Timestamp   time.Time              `json:"timestamp"`
	Context     map[string]interface{} `json:"context" gorm:"type:json"`
}

// PerformanceAlert represents a performance alert
type PerformanceAlert struct {
	ID             string                 `json:"id" gorm:"primaryKey"`
	AlertType      string                 `json:"alert_type"`
	Severity       string                 `json:"severity"`
	Message        string                 `json:"message"`
	MetricName     string                 `json:"metric_name"`
	MetricValue    float64                `json:"metric_value"`
	Threshold      float64                `json:"threshold"`
	Context        map[string]interface{} `json:"context" gorm:"type:json"`
	Acknowledged   bool                   `json:"acknowledged"`
	CreatedAt      time.Time              `json:"created_at"`
	AcknowledgedAt *time.Time             `json:"acknowledged_at"`
}

// PerformanceSnapshot represents a performance snapshot
type PerformanceSnapshot struct {
	ID             string              `json:"id" gorm:"primaryKey"`
	Timestamp      time.Time           `json:"timestamp"`
	CPUUsage       float64             `json:"cpu_usage"`
	MemoryUsage    float64             `json:"memory_usage"`
	DiskUsage      float64             `json:"disk_usage"`
	NetworkIO      map[string]float64  `json:"network_io" gorm:"type:json"`
	ResponseTime   float64             `json:"response_time"`
	Throughput     float64             `json:"throughput"`
	ErrorRate      float64             `json:"error_rate"`
	CacheHitRate   float64             `json:"cache_hit_rate"`
	DBConnections  int                 `json:"db_connections"`
	ActiveRequests int                 `json:"active_requests"`
	Metrics        []PerformanceMetric `json:"metrics" gorm:"type:json"`
}

// PerformanceMonitor provides real-time performance monitoring
type PerformanceMonitor struct {
	service    *AnalyticsService
	db         *gorm.DB
	snapshots  map[string]*PerformanceSnapshot
	alerts     map[string]*PerformanceAlert
	metrics    map[string]*PerformanceMetric
	thresholds map[string]float64
	lock       sync.RWMutex
	monitoring bool
	alertCh    chan *PerformanceAlert
}

// NewPerformanceMonitor creates a new performance monitor
func NewPerformanceMonitor(service *AnalyticsService) *PerformanceMonitor {
	monitor := &PerformanceMonitor{
		service:    service,
		db:         service.db,
		snapshots:  make(map[string]*PerformanceSnapshot),
		alerts:     make(map[string]*PerformanceAlert),
		metrics:    make(map[string]*PerformanceMetric),
		thresholds: make(map[string]float64),
		alertCh:    make(chan *PerformanceAlert, 100),
	}

	// Set default thresholds
	monitor.setDefaultThresholds()

	// Load existing data
	monitor.loadSnapshots()
	monitor.loadAlerts()
	monitor.loadMetrics()

	// Start monitoring
	go monitor.startMonitoring()

	return monitor
}

// StartMonitoring starts the performance monitoring
func (m *PerformanceMonitor) StartMonitoring() {
	m.lock.Lock()
	m.monitoring = true
	m.lock.Unlock()

	go m.monitoringLoop()
}

// StopMonitoring stops the performance monitoring
func (m *PerformanceMonitor) StopMonitoring() {
	m.lock.Lock()
	m.monitoring = false
	m.lock.Unlock()
}

// CollectMetrics collects current performance metrics
func (m *PerformanceMonitor) CollectMetrics() (*PerformanceSnapshot, error) {
	snapshot := &PerformanceSnapshot{
		ID:             m.generateID("snapshot"),
		Timestamp:      time.Now(),
		CPUUsage:       m.getCPUUsage(),
		MemoryUsage:    m.getMemoryUsage(),
		DiskUsage:      m.getDiskUsage(),
		NetworkIO:      m.getNetworkIO(),
		ResponseTime:   m.getAverageResponseTime(),
		Throughput:     m.getCurrentThroughput(),
		ErrorRate:      m.getErrorRate(),
		CacheHitRate:   m.getCacheHitRate(),
		DBConnections:  m.getDatabaseConnections(),
		ActiveRequests: m.getActiveRequests(),
		Metrics:        m.collectDetailedMetrics(),
	}

	m.lock.Lock()
	m.snapshots[snapshot.ID] = snapshot
	m.lock.Unlock()

	// Save to database
	if err := m.db.Create(snapshot).Error; err != nil {
		return nil, fmt.Errorf("failed to save snapshot: %w", err)
	}

	// Check thresholds and generate alerts
	m.checkThresholds(snapshot)

	return snapshot, nil
}

// GetMetricsHistory gets performance metrics history
func (m *PerformanceMonitor) GetMetricsHistory(hours int) ([]*PerformanceSnapshot, error) {
	startTime := time.Now().Add(-time.Duration(hours) * time.Hour)

	var snapshots []PerformanceSnapshot
	if err := m.db.Where("timestamp >= ?", startTime).
		Order("timestamp DESC").
		Find(&snapshots).Error; err != nil {
		return nil, fmt.Errorf("failed to get metrics history: %w", err)
	}

	var results []*PerformanceSnapshot
	for i := range snapshots {
		results = append(results, &snapshots[i])
	}

	return results, nil
}

// GetAlerts gets performance alerts
func (m *PerformanceMonitor) GetAlerts(acknowledged *bool, severity string) ([]map[string]interface{}, error) {
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
			"id":           alert.ID,
			"alert_type":   alert.AlertType,
			"severity":     alert.Severity,
			"message":      alert.Message,
			"metric_name":  alert.MetricName,
			"metric_value": alert.MetricValue,
			"threshold":    alert.Threshold,
			"acknowledged": alert.Acknowledged,
			"created_at":   alert.CreatedAt,
		})
	}

	return alerts, nil
}

// AcknowledgeAlert acknowledges a performance alert
func (m *PerformanceMonitor) AcknowledgeAlert(alertID string) error {
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

// SetThreshold sets a performance threshold
func (m *PerformanceMonitor) SetThreshold(metricName string, threshold float64) {
	m.lock.Lock()
	m.thresholds[metricName] = threshold
	m.lock.Unlock()
}

// GetThreshold gets a performance threshold
func (m *PerformanceMonitor) GetThreshold(metricName string) (float64, bool) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	threshold, exists := m.thresholds[metricName]
	return threshold, exists
}

// GetPerformanceReport generates a performance report
func (m *PerformanceMonitor) GetPerformanceReport() (map[string]interface{}, error) {
	// Get recent snapshots
	snapshots, err := m.GetMetricsHistory(24)
	if err != nil {
		return nil, fmt.Errorf("failed to get metrics history: %w", err)
	}

	if len(snapshots) == 0 {
		return nil, fmt.Errorf("no performance data available")
	}

	// Calculate summary statistics
	summary := m.calculatePerformanceSummary(snapshots)

	// Get alerts
	alerts, err := m.GetAlerts(nil, "")
	if err != nil {
		return nil, fmt.Errorf("failed to get alerts: %w", err)
	}

	// Generate recommendations
	recommendations := m.generatePerformanceRecommendations(snapshots)

	report := map[string]interface{}{
		"period": map[string]interface{}{
			"start_time":     snapshots[len(snapshots)-1].Timestamp,
			"end_time":       snapshots[0].Timestamp,
			"duration_hours": 24,
		},
		"summary": summary,
		"alerts": map[string]interface{}{
			"total":          len(alerts),
			"acknowledged":   len(alerts) - len(m.getUnacknowledgedAlerts()),
			"unacknowledged": len(m.getUnacknowledgedAlerts()),
		},
		"recommendations": recommendations,
		"generated_at":    time.Now(),
	}

	return report, nil
}

// Helper methods

func (m *PerformanceMonitor) monitoringLoop() {
	ticker := time.NewTicker(30 * time.Second) // Collect metrics every 30 seconds
	defer ticker.Stop()

	for m.isMonitoring() {
		select {
		case <-ticker.C:
			snapshot, err := m.CollectMetrics()
			if err != nil {
				continue
			}

			// Process alerts
			select {
			case alert := <-m.alertCh:
				m.processAlert(alert)
			default:
				// No alerts to process
			}
		}
	}
}

func (m *PerformanceMonitor) isMonitoring() bool {
	m.lock.RLock()
	defer m.lock.RUnlock()
	return m.monitoring
}

func (m *PerformanceMonitor) generateID(prefix string) string {
	return fmt.Sprintf("%s_%d", prefix, time.Now().UnixNano())
}

func (m *PerformanceMonitor) setDefaultThresholds() {
	defaultThresholds := map[string]float64{
		"cpu_usage":      80.0,
		"memory_usage":   85.0,
		"disk_usage":     90.0,
		"response_time":  1000.0, // ms
		"error_rate":     5.0,    // %
		"cache_hit_rate": 70.0,   // %
		"throughput":     100.0,  // requests/sec
	}

	for metric, threshold := range defaultThresholds {
		m.thresholds[metric] = threshold
	}
}

func (m *PerformanceMonitor) getCPUUsage() float64 {
	// Mock CPU usage calculation
	// In real implementation, this would use system metrics
	return 45.2
}

func (m *PerformanceMonitor) getMemoryUsage() float64 {
	// Mock memory usage calculation
	return 62.8
}

func (m *PerformanceMonitor) getDiskUsage() float64 {
	// Mock disk usage calculation
	return 34.5
}

func (m *PerformanceMonitor) getNetworkIO() map[string]float64 {
	// Mock network I/O calculation
	return map[string]float64{
		"bytes_in":    1024000.0,
		"bytes_out":   512000.0,
		"packets_in":  1500.0,
		"packets_out": 1200.0,
	}
}

func (m *PerformanceMonitor) getAverageResponseTime() float64 {
	// Mock response time calculation
	return 245.0
}

func (m *PerformanceMonitor) getCurrentThroughput() float64 {
	// Mock throughput calculation
	return 125.5
}

func (m *PerformanceMonitor) getErrorRate() float64 {
	// Mock error rate calculation
	return 2.1
}

func (m *PerformanceMonitor) getCacheHitRate() float64 {
	// Mock cache hit rate calculation
	return 78.5
}

func (m *PerformanceMonitor) getDatabaseConnections() int {
	// Mock database connections count
	return 15
}

func (m *PerformanceMonitor) getActiveRequests() int {
	// Mock active requests count
	return 42
}

func (m *PerformanceMonitor) collectDetailedMetrics() []PerformanceMetric {
	var metrics []PerformanceMetric

	// CPU metrics
	metrics = append(metrics, PerformanceMetric{
		ID:          m.generateID("metric"),
		MetricType:  "system",
		MetricName:  "cpu_usage",
		MetricValue: m.getCPUUsage(),
		Unit:        "percent",
		Status:      "normal",
		Timestamp:   time.Now(),
	})

	// Memory metrics
	metrics = append(metrics, PerformanceMetric{
		ID:          m.generateID("metric"),
		MetricType:  "system",
		MetricName:  "memory_usage",
		MetricValue: m.getMemoryUsage(),
		Unit:        "percent",
		Status:      "normal",
		Timestamp:   time.Now(),
	})

	// Response time metrics
	metrics = append(metrics, PerformanceMetric{
		ID:          m.generateID("metric"),
		MetricType:  "application",
		MetricName:  "response_time",
		MetricValue: m.getAverageResponseTime(),
		Unit:        "milliseconds",
		Status:      "normal",
		Timestamp:   time.Now(),
	})

	// Error rate metrics
	metrics = append(metrics, PerformanceMetric{
		ID:          m.generateID("metric"),
		MetricType:  "application",
		MetricName:  "error_rate",
		MetricValue: m.getErrorRate(),
		Unit:        "percent",
		Status:      "normal",
		Timestamp:   time.Now(),
	})

	return metrics
}

func (m *PerformanceMonitor) checkThresholds(snapshot *PerformanceSnapshot) {
	// Check CPU usage
	if snapshot.CPUUsage > m.thresholds["cpu_usage"] {
		m.createAlert("high_cpu_usage", "warning",
			fmt.Sprintf("CPU usage is high: %.2f%%", snapshot.CPUUsage),
			"cpu_usage", snapshot.CPUUsage, m.thresholds["cpu_usage"])
	}

	// Check memory usage
	if snapshot.MemoryUsage > m.thresholds["memory_usage"] {
		m.createAlert("high_memory_usage", "warning",
			fmt.Sprintf("Memory usage is high: %.2f%%", snapshot.MemoryUsage),
			"memory_usage", snapshot.MemoryUsage, m.thresholds["memory_usage"])
	}

	// Check response time
	if snapshot.ResponseTime > m.thresholds["response_time"] {
		m.createAlert("high_response_time", "critical",
			fmt.Sprintf("Response time is high: %.2fms", snapshot.ResponseTime),
			"response_time", snapshot.ResponseTime, m.thresholds["response_time"])
	}

	// Check error rate
	if snapshot.ErrorRate > m.thresholds["error_rate"] {
		m.createAlert("high_error_rate", "critical",
			fmt.Sprintf("Error rate is high: %.2f%%", snapshot.ErrorRate),
			"error_rate", snapshot.ErrorRate, m.thresholds["error_rate"])
	}

	// Check cache hit rate
	if snapshot.CacheHitRate < m.thresholds["cache_hit_rate"] {
		m.createAlert("low_cache_hit_rate", "warning",
			fmt.Sprintf("Cache hit rate is low: %.2f%%", snapshot.CacheHitRate),
			"cache_hit_rate", snapshot.CacheHitRate, m.thresholds["cache_hit_rate"])
	}
}

func (m *PerformanceMonitor) createAlert(alertType, severity, message, metricName string, metricValue, threshold float64) {
	alert := &PerformanceAlert{
		ID:          m.generateID("alert"),
		AlertType:   alertType,
		Severity:    severity,
		Message:     message,
		MetricName:  metricName,
		MetricValue: metricValue,
		Threshold:   threshold,
		Context: map[string]interface{}{
			"timestamp":   time.Now(),
			"snapshot_id": "current",
		},
		Acknowledged: false,
		CreatedAt:    time.Now(),
	}

	// Send to alert channel
	select {
	case m.alertCh <- alert:
	default:
		// Channel is full, log the alert
	}
}

func (m *PerformanceMonitor) processAlert(alert *PerformanceAlert) {
	m.lock.Lock()
	m.alerts[alert.ID] = alert
	m.lock.Unlock()

	// Save to database
	m.db.Create(alert)

	// Log the alert
	// In real implementation, this would send notifications
}

func (m *PerformanceMonitor) calculatePerformanceSummary(snapshots []*PerformanceSnapshot) map[string]interface{} {
	if len(snapshots) == 0 {
		return map[string]interface{}{}
	}

	// Calculate averages
	totalCPU := 0.0
	totalMemory := 0.0
	totalResponseTime := 0.0
	totalErrorRate := 0.0
	totalCacheHitRate := 0.0

	for _, snapshot := range snapshots {
		totalCPU += snapshot.CPUUsage
		totalMemory += snapshot.MemoryUsage
		totalResponseTime += snapshot.ResponseTime
		totalErrorRate += snapshot.ErrorRate
		totalCacheHitRate += snapshot.CacheHitRate
	}

	count := float64(len(snapshots))

	summary := map[string]interface{}{
		"cpu_usage": map[string]interface{}{
			"average": totalCPU / count,
			"min":     m.findMin(snapshots, func(s *PerformanceSnapshot) float64 { return s.CPUUsage }),
			"max":     m.findMax(snapshots, func(s *PerformanceSnapshot) float64 { return s.CPUUsage }),
		},
		"memory_usage": map[string]interface{}{
			"average": totalMemory / count,
			"min":     m.findMin(snapshots, func(s *PerformanceSnapshot) float64 { return s.MemoryUsage }),
			"max":     m.findMax(snapshots, func(s *PerformanceSnapshot) float64 { return s.MemoryUsage }),
		},
		"response_time": map[string]interface{}{
			"average": totalResponseTime / count,
			"min":     m.findMin(snapshots, func(s *PerformanceSnapshot) float64 { return s.ResponseTime }),
			"max":     m.findMax(snapshots, func(s *PerformanceSnapshot) float64 { return s.ResponseTime }),
		},
		"error_rate": map[string]interface{}{
			"average": totalErrorRate / count,
			"min":     m.findMin(snapshots, func(s *PerformanceSnapshot) float64 { return s.ErrorRate }),
			"max":     m.findMax(snapshots, func(s *PerformanceSnapshot) float64 { return s.ErrorRate }),
		},
		"cache_hit_rate": map[string]interface{}{
			"average": totalCacheHitRate / count,
			"min":     m.findMin(snapshots, func(s *PerformanceSnapshot) float64 { return s.CacheHitRate }),
			"max":     m.findMax(snapshots, func(s *PerformanceSnapshot) float64 { return s.CacheHitRate }),
		},
	}

	return summary
}

func (m *PerformanceMonitor) findMin(snapshots []*PerformanceSnapshot, getter func(*PerformanceSnapshot) float64) float64 {
	if len(snapshots) == 0 {
		return 0.0
	}

	min := getter(snapshots[0])
	for _, snapshot := range snapshots {
		if value := getter(snapshot); value < min {
			min = value
		}
	}
	return min
}

func (m *PerformanceMonitor) findMax(snapshots []*PerformanceSnapshot, getter func(*PerformanceSnapshot) float64) float64 {
	if len(snapshots) == 0 {
		return 0.0
	}

	max := getter(snapshots[0])
	for _, snapshot := range snapshots {
		if value := getter(snapshot); value > max {
			max = value
		}
	}
	return max
}

func (m *PerformanceMonitor) generatePerformanceRecommendations(snapshots []*PerformanceSnapshot) []map[string]interface{} {
	var recommendations []map[string]interface{}

	// Analyze CPU usage
	if avgCPU := m.calculateAverage(snapshots, func(s *PerformanceSnapshot) float64 { return s.CPUUsage }); avgCPU > 70 {
		recommendations = append(recommendations, map[string]interface{}{
			"type":        "performance",
			"severity":    "medium",
			"title":       "High CPU Usage",
			"description": "Average CPU usage is above 70%",
			"action":      "Consider scaling horizontally or optimizing CPU-intensive operations",
		})
	}

	// Analyze memory usage
	if avgMemory := m.calculateAverage(snapshots, func(s *PerformanceSnapshot) float64 { return s.MemoryUsage }); avgMemory > 80 {
		recommendations = append(recommendations, map[string]interface{}{
			"type":        "performance",
			"severity":    "high",
			"title":       "High Memory Usage",
			"description": "Average memory usage is above 80%",
			"action":      "Consider increasing memory allocation or optimizing memory usage",
		})
	}

	// Analyze response time
	if avgResponseTime := m.calculateAverage(snapshots, func(s *PerformanceSnapshot) float64 { return s.ResponseTime }); avgResponseTime > 500 {
		recommendations = append(recommendations, map[string]interface{}{
			"type":        "performance",
			"severity":    "high",
			"title":       "High Response Time",
			"description": "Average response time is above 500ms",
			"action":      "Consider optimizing database queries and implementing caching",
		})
	}

	// Analyze error rate
	if avgErrorRate := m.calculateAverage(snapshots, func(s *PerformanceSnapshot) float64 { return s.ErrorRate }); avgErrorRate > 3 {
		recommendations = append(recommendations, map[string]interface{}{
			"type":        "reliability",
			"severity":    "critical",
			"title":       "High Error Rate",
			"description": "Average error rate is above 3%",
			"action":      "Investigate error sources and improve error handling",
		})
	}

	return recommendations
}

func (m *PerformanceMonitor) calculateAverage(snapshots []*PerformanceSnapshot, getter func(*PerformanceSnapshot) float64) float64 {
	if len(snapshots) == 0 {
		return 0.0
	}

	sum := 0.0
	for _, snapshot := range snapshots {
		sum += getter(snapshot)
	}
	return sum / float64(len(snapshots))
}

func (m *PerformanceMonitor) getUnacknowledgedAlerts() []*PerformanceAlert {
	var unacknowledged []*PerformanceAlert
	for _, alert := range m.alerts {
		if !alert.Acknowledged {
			unacknowledged = append(unacknowledged, alert)
		}
	}
	return unacknowledged
}

func (m *PerformanceMonitor) loadSnapshots() {
	var snapshots []PerformanceSnapshot
	if err := m.db.Find(&snapshots).Error; err != nil {
		return
	}

	for i := range snapshots {
		m.snapshots[snapshots[i].ID] = &snapshots[i]
	}
}

func (m *PerformanceMonitor) loadAlerts() {
	var alerts []PerformanceAlert
	if err := m.db.Find(&alerts).Error; err != nil {
		return
	}

	for i := range alerts {
		m.alerts[alerts[i].ID] = &alerts[i]
	}
}

func (m *PerformanceMonitor) loadMetrics() {
	var metrics []PerformanceMetric
	if err := m.db.Find(&metrics).Error; err != nil {
		return
	}

	for i := range metrics {
		m.metrics[metrics[i].ID] = &metrics[i]
	}
}
