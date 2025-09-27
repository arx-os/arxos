package cache

import (
	"fmt"
	"runtime"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// PerformanceMetric represents a performance measurement
type PerformanceMetric struct {
	Name      string                 `json:"name"`
	Value     float64                `json:"value"`
	Unit      string                 `json:"unit"`
	Timestamp time.Time              `json:"timestamp"`
	Tags      map[string]string      `json:"tags"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// PerformanceAlert represents a performance alert
type PerformanceAlert struct {
	ID           string            `json:"id"`
	MetricName   string            `json:"metric_name"`
	Severity     AlertSeverity     `json:"severity"`
	Message      string            `json:"message"`
	Threshold    float64           `json:"threshold"`
	CurrentValue float64           `json:"current_value"`
	Timestamp    time.Time         `json:"timestamp"`
	Resolved     bool              `json:"resolved"`
	Tags         map[string]string `json:"tags"`
}

// AlertSeverity defines alert severity levels
type AlertSeverity string

const (
	SeverityInfo     AlertSeverity = "info"
	SeverityWarning  AlertSeverity = "warning"
	SeverityCritical AlertSeverity = "critical"
)

// PerformanceThreshold defines performance thresholds
type PerformanceThreshold struct {
	MetricName string            `json:"metric_name"`
	Warning    float64           `json:"warning"`
	Critical   float64           `json:"critical"`
	Unit       string            `json:"unit"`
	Tags       map[string]string `json:"tags"`
}

// PerformanceMonitor monitors system performance
type PerformanceMonitor struct {
	mu         sync.RWMutex
	metrics    map[string][]PerformanceMetric
	alerts     map[string]*PerformanceAlert
	thresholds map[string]PerformanceThreshold
	config     *MonitorConfig
	stopChan   chan struct{}
	alertChan  chan *PerformanceAlert
}

// MonitorConfig defines performance monitoring configuration
type MonitorConfig struct {
	CollectionInterval time.Duration          `json:"collection_interval"`
	RetentionPeriod    time.Duration          `json:"retention_period"`
	MaxMetrics         int                    `json:"max_metrics"`
	EnableAlerts       bool                   `json:"enable_alerts"`
	Thresholds         []PerformanceThreshold `json:"thresholds"`
}

// SystemMetrics represents current system metrics
type SystemMetrics struct {
	CPUUsage       float64       `json:"cpu_usage"`
	MemoryUsage    int64         `json:"memory_usage_mb"`
	GoroutineCount int           `json:"goroutine_count"`
	HeapSize       int64         `json:"heap_size_mb"`
	GCCount        uint32        `json:"gc_count"`
	LastGC         time.Time     `json:"last_gc"`
	Uptime         time.Duration `json:"uptime"`
}

// NewPerformanceMonitor creates a new performance monitor
func NewPerformanceMonitor(config *MonitorConfig) *PerformanceMonitor {
	if config == nil {
		config = &MonitorConfig{
			CollectionInterval: 30 * time.Second,
			RetentionPeriod:    24 * time.Hour,
			MaxMetrics:         10000,
			EnableAlerts:       true,
			Thresholds:         getDefaultThresholds(),
		}
	}

	monitor := &PerformanceMonitor{
		metrics:    make(map[string][]PerformanceMetric),
		alerts:     make(map[string]*PerformanceAlert),
		thresholds: make(map[string]PerformanceThreshold),
		config:     config,
		stopChan:   make(chan struct{}),
		alertChan:  make(chan *PerformanceAlert, 100),
	}

	// Initialize thresholds
	for _, threshold := range config.Thresholds {
		monitor.thresholds[threshold.MetricName] = threshold
	}

	// Start monitoring goroutines
	go monitor.collectionRoutine()
	go monitor.alertRoutine()
	go monitor.cleanupRoutine()

	return monitor
}

// RecordMetric records a performance metric
func (pm *PerformanceMonitor) RecordMetric(metric PerformanceMetric) {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	// Add metric to collection
	pm.metrics[metric.Name] = append(pm.metrics[metric.Name], metric)

	// Check thresholds and generate alerts
	if pm.config.EnableAlerts {
		pm.checkThresholds(metric)
	}

	// Limit metrics per name
	if len(pm.metrics[metric.Name]) > pm.config.MaxMetrics {
		pm.metrics[metric.Name] = pm.metrics[metric.Name][len(pm.metrics[metric.Name])-pm.config.MaxMetrics:]
	}
}

// GetMetrics retrieves metrics for a specific name
func (pm *PerformanceMonitor) GetMetrics(metricName string, limit int) []PerformanceMetric {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	metrics, exists := pm.metrics[metricName]
	if !exists {
		return []PerformanceMetric{}
	}

	if limit > 0 && len(metrics) > limit {
		return metrics[len(metrics)-limit:]
	}

	return metrics
}

// GetSystemMetrics returns current system metrics
func (pm *PerformanceMonitor) GetSystemMetrics() *SystemMetrics {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	return &SystemMetrics{
		CPUUsage:       pm.getCPUUsage(),
		MemoryUsage:    int64(m.Alloc / 1024 / 1024),
		GoroutineCount: runtime.NumGoroutine(),
		HeapSize:       int64(m.HeapAlloc / 1024 / 1024),
		GCCount:        m.NumGC,
		LastGC:         time.Unix(0, int64(m.LastGC)),
		Uptime:         time.Since(time.Now().Add(-time.Hour)), // Simplified
	}
}

// GetAlerts returns active alerts
func (pm *PerformanceMonitor) GetAlerts(resolved bool) []*PerformanceAlert {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	var alerts []*PerformanceAlert
	for _, alert := range pm.alerts {
		if alert.Resolved == resolved {
			alerts = append(alerts, alert)
		}
	}

	return alerts
}

// ResolveAlert resolves an alert
func (pm *PerformanceMonitor) ResolveAlert(alertID string) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	alert, exists := pm.alerts[alertID]
	if !exists {
		return fmt.Errorf("alert %s not found", alertID)
	}

	alert.Resolved = true
	alert.Timestamp = time.Now()

	logger.Info("Alert resolved: %s", alertID)
	return nil
}

// SetThreshold sets a performance threshold
func (pm *PerformanceMonitor) SetThreshold(threshold PerformanceThreshold) {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	pm.thresholds[threshold.MetricName] = threshold
	logger.Debug("Set threshold for metric %s: warning=%.2f, critical=%.2f",
		threshold.MetricName, threshold.Warning, threshold.Critical)
}

// Close gracefully shuts down the performance monitor
func (pm *PerformanceMonitor) Close() error {
	close(pm.stopChan)
	close(pm.alertChan)
	return nil
}

// Helper methods

func (pm *PerformanceMonitor) collectionRoutine() {
	interval := pm.config.CollectionInterval
	if interval <= 0 {
		interval = 30 * time.Second // Default collection interval
	}

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			pm.collectSystemMetrics()
		case <-pm.stopChan:
			return
		}
	}
}

func (pm *PerformanceMonitor) collectSystemMetrics() {
	systemMetrics := pm.GetSystemMetrics()

	// Record CPU usage
	pm.RecordMetric(PerformanceMetric{
		Name:      "cpu_usage",
		Value:     systemMetrics.CPUUsage,
		Unit:      "percent",
		Timestamp: time.Now(),
		Tags:      map[string]string{"type": "system"},
	})

	// Record memory usage
	pm.RecordMetric(PerformanceMetric{
		Name:      "memory_usage",
		Value:     float64(systemMetrics.MemoryUsage),
		Unit:      "MB",
		Timestamp: time.Now(),
		Tags:      map[string]string{"type": "system"},
	})

	// Record goroutine count
	pm.RecordMetric(PerformanceMetric{
		Name:      "goroutine_count",
		Value:     float64(systemMetrics.GoroutineCount),
		Unit:      "count",
		Timestamp: time.Now(),
		Tags:      map[string]string{"type": "system"},
	})

	// Record heap size
	pm.RecordMetric(PerformanceMetric{
		Name:      "heap_size",
		Value:     float64(systemMetrics.HeapSize),
		Unit:      "MB",
		Timestamp: time.Now(),
		Tags:      map[string]string{"type": "system"},
	})
}

func (pm *PerformanceMonitor) checkThresholds(metric PerformanceMetric) {
	threshold, exists := pm.thresholds[metric.Name]
	if !exists {
		return
	}

	var severity AlertSeverity
	var shouldAlert bool

	if metric.Value >= threshold.Critical {
		severity = SeverityCritical
		shouldAlert = true
	} else if metric.Value >= threshold.Warning {
		severity = SeverityWarning
		shouldAlert = true
	}

	if shouldAlert {
		alert := &PerformanceAlert{
			ID:         fmt.Sprintf("alert_%d", time.Now().UnixNano()),
			MetricName: metric.Name,
			Severity:   severity,
			Message: fmt.Sprintf("Metric %s exceeded threshold: %.2f %s (threshold: %.2f %s)",
				metric.Name, metric.Value, metric.Unit, threshold.Warning, threshold.Unit),
			Threshold:    threshold.Warning,
			CurrentValue: metric.Value,
			Timestamp:    time.Now(),
			Resolved:     false,
			Tags:         metric.Tags,
		}

		pm.alerts[alert.ID] = alert
		pm.alertChan <- alert

		logger.Warn("Performance alert: %s", alert.Message)
	}
}

func (pm *PerformanceMonitor) alertRoutine() {
	for {
		select {
		case alert := <-pm.alertChan:
			pm.handleAlert(alert)
		case <-pm.stopChan:
			return
		}
	}
}

func (pm *PerformanceMonitor) handleAlert(alert *PerformanceAlert) {
	if alert == nil {
		return
	}

	// In a real implementation, this would:
	// - Send notifications (email, Slack, etc.)
	// - Log to external monitoring systems
	// - Trigger automated responses

	logger.Error("PERFORMANCE ALERT [%s]: %s", alert.Severity, alert.Message)
}

func (pm *PerformanceMonitor) cleanupRoutine() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			pm.cleanupOldMetrics()
			pm.cleanupOldAlerts()
		case <-pm.stopChan:
			return
		}
	}
}

func (pm *PerformanceMonitor) cleanupOldMetrics() {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	cutoff := time.Now().Add(-pm.config.RetentionPeriod)

	for metricName, metrics := range pm.metrics {
		var filtered []PerformanceMetric
		for _, metric := range metrics {
			if metric.Timestamp.After(cutoff) {
				filtered = append(filtered, metric)
			}
		}
		pm.metrics[metricName] = filtered
	}
}

func (pm *PerformanceMonitor) cleanupOldAlerts() {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	cutoff := time.Now().Add(-pm.config.RetentionPeriod)

	for alertID, alert := range pm.alerts {
		if alert.Timestamp.Before(cutoff) && alert.Resolved {
			delete(pm.alerts, alertID)
		}
	}
}

func (pm *PerformanceMonitor) getCPUUsage() float64 {
	// Simplified CPU usage calculation
	// In a real implementation, this would use proper CPU monitoring
	return 0.0
}

func getDefaultThresholds() []PerformanceThreshold {
	return []PerformanceThreshold{
		{
			MetricName: "cpu_usage",
			Warning:    70.0,
			Critical:   90.0,
			Unit:       "percent",
			Tags:       map[string]string{"type": "system"},
		},
		{
			MetricName: "memory_usage",
			Warning:    512.0,
			Critical:   768.0,
			Unit:       "MB",
			Tags:       map[string]string{"type": "system"},
		},
		{
			MetricName: "goroutine_count",
			Warning:    1000.0,
			Critical:   2000.0,
			Unit:       "count",
			Tags:       map[string]string{"type": "system"},
		},
		{
			MetricName: "heap_size",
			Warning:    256.0,
			Critical:   512.0,
			Unit:       "MB",
			Tags:       map[string]string{"type": "system"},
		},
	}
}
