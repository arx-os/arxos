package cache

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// CacheMonitor provides real-time monitoring of cache health and performance
type CacheMonitor struct {
	cache     *UnifiedCache
	logger    domain.Logger
	analytics *CacheAnalytics

	// Monitoring configuration
	config *MonitoringConfig

	// Monitoring state
	isRunning   bool
	stopChan    chan struct{}
	metricsChan chan *MonitoringMetric
	alertsChan  chan *Alert

	// Alert thresholds
	thresholds *AlertThresholds

	// Monitoring data
	healthStatus HealthStatus
	mu           sync.RWMutex
}

// MonitoringConfig defines monitoring behavior
type MonitoringConfig struct {
	Enabled            bool          `json:"enabled"`
	CheckInterval      time.Duration `json:"check_interval"`
	MetricsRetention   time.Duration `json:"metrics_retention"`
	AlertCooldown      time.Duration `json:"alert_cooldown"`
	HealthCheckTimeout time.Duration `json:"health_check_timeout"`
}

// MonitoringMetric represents a monitoring data point
type MonitoringMetric struct {
	Timestamp  time.Time         `json:"timestamp"`
	MetricType string            `json:"metric_type"`
	Value      float64           `json:"value"`
	Unit       string            `json:"unit"`
	Tags       map[string]string `json:"tags"`
	Metadata   map[string]any    `json:"metadata"`
}

// Alert represents a monitoring alert
type Alert struct {
	ID         string         `json:"id"`
	Severity   AlertSeverity  `json:"severity"`
	Type       string         `json:"type"`
	Message    string         `json:"message"`
	Timestamp  time.Time      `json:"timestamp"`
	Resolved   bool           `json:"resolved"`
	ResolvedAt *time.Time     `json:"resolved_at,omitempty"`
	Metadata   map[string]any `json:"metadata"`
}

// AlertSeverity defines alert severity levels
type AlertSeverity int

const (
	SeverityInfo AlertSeverity = iota
	SeverityWarning
	SeverityCritical
	SeverityEmergency
)

// AlertThresholds defines alert thresholds
type AlertThresholds struct {
	HitRateLow           float64       `json:"hit_rate_low"`
	HitRateCritical      float64       `json:"hit_rate_critical"`
	ResponseTimeHigh     time.Duration `json:"response_time_high"`
	ResponseTimeCritical time.Duration `json:"response_time_critical"`
	MemoryUsageHigh      float64       `json:"memory_usage_high"`
	MemoryUsageCritical  float64       `json:"memory_usage_critical"`
	ErrorRateHigh        float64       `json:"error_rate_high"`
	ErrorRateCritical    float64       `json:"error_rate_critical"`
}

// HealthStatus represents cache health status
type HealthStatus struct {
	Status     string                     `json:"status"`
	LastCheck  time.Time                  `json:"last_check"`
	Uptime     time.Duration              `json:"uptime"`
	Components map[string]ComponentHealth `json:"components"`
	Metrics    map[string]float64         `json:"metrics"`
	Alerts     []Alert                    `json:"alerts"`
}

// ComponentHealth represents health of a cache component
type ComponentHealth struct {
	Status    string         `json:"status"`
	LastCheck time.Time      `json:"last_check"`
	Details   map[string]any `json:"details"`
}

// NewCacheMonitor creates a new cache monitor
func NewCacheMonitor(cache *UnifiedCache, logger domain.Logger, config *MonitoringConfig) *CacheMonitor {
	if config == nil {
		config = &MonitoringConfig{
			Enabled:            true,
			CheckInterval:      30 * time.Second,
			MetricsRetention:   24 * time.Hour,
			AlertCooldown:      5 * time.Minute,
			HealthCheckTimeout: 10 * time.Second,
		}
	}

	return &CacheMonitor{
		cache:       cache,
		logger:      logger,
		config:      config,
		stopChan:    make(chan struct{}),
		metricsChan: make(chan *MonitoringMetric, 1000),
		alertsChan:  make(chan *Alert, 100),
		thresholds: &AlertThresholds{
			HitRateLow:           0.7,
			HitRateCritical:      0.5,
			ResponseTimeHigh:     100 * time.Millisecond,
			ResponseTimeCritical: 500 * time.Millisecond,
			MemoryUsageHigh:      0.8,
			MemoryUsageCritical:  0.95,
			ErrorRateHigh:        0.05,
			ErrorRateCritical:    0.1,
		},
		healthStatus: HealthStatus{
			Status:     "unknown",
			LastCheck:  time.Now(),
			Components: make(map[string]ComponentHealth),
			Metrics:    make(map[string]float64),
			Alerts:     make([]Alert, 0),
		},
	}
}

// Start begins monitoring
func (cm *CacheMonitor) Start(ctx context.Context) error {
	if !cm.config.Enabled {
		cm.logger.Info("Cache monitoring is disabled")
		return nil
	}

	if cm.isRunning {
		return fmt.Errorf("monitor is already running")
	}

	cm.isRunning = true
	cm.healthStatus.Status = "starting"
	cm.healthStatus.Uptime = 0

	// Start monitoring goroutines
	go cm.monitoringLoop(ctx)
	go cm.alertProcessor(ctx)
	go cm.metricsProcessor(ctx)

	cm.logger.Info("Cache monitoring started",
		"check_interval", cm.config.CheckInterval)

	return nil
}

// Stop stops monitoring
func (cm *CacheMonitor) Stop() error {
	if !cm.isRunning {
		return fmt.Errorf("monitor is not running")
	}

	close(cm.stopChan)
	cm.isRunning = false
	cm.healthStatus.Status = "stopped"

	cm.logger.Info("Cache monitoring stopped")
	return nil
}

// GetHealthStatus returns current health status
func (cm *CacheMonitor) GetHealthStatus(ctx context.Context) (*HealthStatus, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	// Update uptime
	cm.healthStatus.Uptime = time.Since(cm.healthStatus.LastCheck)

	return &cm.healthStatus, nil
}

// GetAlerts returns current alerts
func (cm *CacheMonitor) GetAlerts(ctx context.Context) ([]Alert, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	return cm.healthStatus.Alerts, nil
}

// GetMetrics returns recent metrics
func (cm *CacheMonitor) GetMetrics(ctx context.Context, duration time.Duration) ([]MonitoringMetric, error) {
	// In a real implementation, this would query a time-series database
	// For now, return empty slice
	return []MonitoringMetric{}, nil
}

// monitoringLoop runs the main monitoring loop
func (cm *CacheMonitor) monitoringLoop(ctx context.Context) {
	ticker := time.NewTicker(cm.config.CheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-cm.stopChan:
			return
		case <-ticker.C:
			cm.performHealthCheck(ctx)
		}
	}
}

// performHealthCheck performs a comprehensive health check
func (cm *CacheMonitor) performHealthCheck(ctx context.Context) {
	start := time.Now()

	// Check L1 cache health
	l1Health := cm.checkL1Health(ctx)

	// Check L2 cache health
	l2Health := cm.checkL2Health(ctx)

	// Check L3 cache health
	l3Health := cm.checkL3Health(ctx)

	// Get overall cache stats
	stats, err := cm.cache.GetStats(ctx)
	if err != nil {
		cm.logger.Error("Failed to get cache stats", "error", err)
		cm.recordMetric("health_check_error", 1, "count", map[string]string{"error": "stats_failure"})
		return
	}

	// Update health status
	cm.mu.Lock()
	cm.healthStatus.LastCheck = time.Now()
	cm.healthStatus.Components["l1"] = l1Health
	cm.healthStatus.Components["l2"] = l2Health
	cm.healthStatus.Components["l3"] = l3Health

	// Calculate overall status
	overallStatus := cm.calculateOverallStatus(l1Health, l2Health, l3Health)
	cm.healthStatus.Status = overallStatus

	// Update metrics
	cm.healthStatus.Metrics["hit_rate"] = cm.calculateHitRate(stats)
	cm.healthStatus.Metrics["total_requests"] = float64(stats.TotalHits + stats.TotalMisses)
	cm.healthStatus.Metrics["l1_hit_rate"] = cm.calculateL1HitRate(stats)
	cm.healthStatus.Metrics["l2_hit_rate"] = cm.calculateL2HitRate(stats)
	cm.healthStatus.Metrics["l3_hit_rate"] = cm.calculateL3HitRate(stats)
	cm.mu.Unlock()

	// Record health check metric
	duration := time.Since(start)
	cm.recordMetric("health_check_duration", float64(duration.Nanoseconds()), "nanoseconds", nil)

	// Check for alerts
	cm.checkAlerts(stats)
}

// checkL1Health checks L1 cache health
func (cm *CacheMonitor) checkL1Health(ctx context.Context) ComponentHealth {
	health := ComponentHealth{
		Status:    "healthy",
		LastCheck: time.Now(),
		Details:   make(map[string]any),
	}

	// Test L1 cache with a simple operation
	testKey := "health_check_l1"
	testValue := "test_value"
	testTTL := 1 * time.Minute

	// Set and get test value
	if err := cm.cache.Set(ctx, testKey, testValue, testTTL); err != nil {
		health.Status = "unhealthy"
		health.Details["error"] = err.Error()
		return health
	}

	retrieved, err := cm.cache.Get(ctx, testKey)
	if err != nil {
		health.Status = "unhealthy"
		health.Details["error"] = err.Error()
		return health
	}

	if retrieved != testValue {
		health.Status = "unhealthy"
		health.Details["error"] = "value_mismatch"
		return health
	}

	// Clean up test value
	cm.cache.Delete(ctx, testKey)

	health.Details["test_passed"] = true
	return health
}

// checkL2Health checks L2 cache health
func (cm *CacheMonitor) checkL2Health(ctx context.Context) ComponentHealth {
	health := ComponentHealth{
		Status:    "healthy",
		LastCheck: time.Now(),
		Details:   make(map[string]any),
	}

	// Test L2 cache with a longer TTL to ensure it goes to L2
	testKey := "health_check_l2"
	testValue := "test_value_l2"
	testTTL := 2 * time.Hour // This should go to L2

	// Set and get test value
	if err := cm.cache.Set(ctx, testKey, testValue, testTTL); err != nil {
		health.Status = "unhealthy"
		health.Details["error"] = err.Error()
		return health
	}

	retrieved, err := cm.cache.Get(ctx, testKey)
	if err != nil {
		health.Status = "unhealthy"
		health.Details["error"] = err.Error()
		return health
	}

	if retrieved != testValue {
		health.Status = "unhealthy"
		health.Details["error"] = "value_mismatch"
		return health
	}

	// Clean up test value
	cm.cache.Delete(ctx, testKey)

	health.Details["test_passed"] = true
	return health
}

// checkL3Health checks L3 cache health
func (cm *CacheMonitor) checkL3Health(ctx context.Context) ComponentHealth {
	health := ComponentHealth{
		Status:    "healthy",
		LastCheck: time.Now(),
		Details:   make(map[string]any),
	}

	// L3 cache might not be enabled
	if cm.cache.l3Cache == nil {
		health.Status = "disabled"
		health.Details["enabled"] = false
		return health
	}

	// Test L3 cache connection
	if err := cm.cache.l3Cache.Ping(ctx); err != nil {
		health.Status = "unhealthy"
		health.Details["error"] = err.Error()
		return health
	}

	health.Details["ping_successful"] = true
	return health
}

// calculateOverallStatus calculates overall cache health status
func (cm *CacheMonitor) calculateOverallStatus(l1, l2, l3 ComponentHealth) string {
	// If any critical component is unhealthy, overall is unhealthy
	if l1.Status == "unhealthy" || l2.Status == "unhealthy" {
		return "unhealthy"
	}

	// If L3 is unhealthy but L1 and L2 are healthy, status is degraded
	if l3.Status == "unhealthy" {
		return "degraded"
	}

	// If all components are healthy or disabled, status is healthy
	return "healthy"
}

// checkAlerts checks for alert conditions
func (cm *CacheMonitor) checkAlerts(stats *CacheStats) {
	hitRate := cm.calculateHitRate(stats)

	// Check hit rate alerts
	if hitRate < cm.thresholds.HitRateCritical {
		cm.triggerAlert("hit_rate_critical", SeverityCritical,
			fmt.Sprintf("Hit rate is critically low: %.2f%%", hitRate*100))
	} else if hitRate < cm.thresholds.HitRateLow {
		cm.triggerAlert("hit_rate_low", SeverityWarning,
			fmt.Sprintf("Hit rate is low: %.2f%%", hitRate*100))
	}

	// Check L1 hit rate
	l1HitRate := cm.calculateL1HitRate(stats)
	if l1HitRate < 0.5 {
		cm.triggerAlert("l1_hit_rate_low", SeverityWarning,
			fmt.Sprintf("L1 hit rate is low: %.2f%%", l1HitRate*100))
	}
}

// triggerAlert triggers an alert
func (cm *CacheMonitor) triggerAlert(alertType string, severity AlertSeverity, message string) {
	alert := Alert{
		ID:        fmt.Sprintf("%s_%d", alertType, time.Now().Unix()),
		Severity:  severity,
		Type:      alertType,
		Message:   message,
		Timestamp: time.Now(),
		Resolved:  false,
		Metadata:  make(map[string]any),
	}

	// Check if we already have this alert active
	cm.mu.Lock()
	defer cm.mu.Unlock()

	for _, existingAlert := range cm.healthStatus.Alerts {
		if existingAlert.Type == alertType && !existingAlert.Resolved {
			return // Alert already active
		}
	}

	cm.healthStatus.Alerts = append(cm.healthStatus.Alerts, alert)

	// Send alert to channel
	select {
	case cm.alertsChan <- &alert:
	default:
		cm.logger.Warn("Alert channel full, dropping alert", "type", alertType)
	}
}

// recordMetric records a monitoring metric
func (cm *CacheMonitor) recordMetric(metricType string, value float64, unit string, tags map[string]string) {
	metric := &MonitoringMetric{
		Timestamp:  time.Now(),
		MetricType: metricType,
		Value:      value,
		Unit:       unit,
		Tags:       tags,
		Metadata:   make(map[string]any),
	}

	select {
	case cm.metricsChan <- metric:
	default:
		cm.logger.Warn("Metrics channel full, dropping metric", "type", metricType)
	}
}

// alertProcessor processes alerts
func (cm *CacheMonitor) alertProcessor(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-cm.stopChan:
			return
		case alert := <-cm.alertsChan:
			cm.processAlert(alert)
		}
	}
}

// metricsProcessor processes metrics
func (cm *CacheMonitor) metricsProcessor(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-cm.stopChan:
			return
		case metric := <-cm.metricsChan:
			cm.processMetric(metric)
		}
	}
}

// processAlert processes an alert
func (cm *CacheMonitor) processAlert(alert *Alert) {
	cm.logger.Warn("Cache alert triggered",
		"type", alert.Type,
		"severity", alert.Severity,
		"message", alert.Message)

	// In production, this would send alerts to external systems
	// (email, Slack, PagerDuty, etc.)
}

// processMetric processes a metric
func (cm *CacheMonitor) processMetric(metric *MonitoringMetric) {
	// In production, this would send metrics to external systems
	// (Prometheus, InfluxDB, etc.)
	cm.logger.Debug("Cache metric recorded",
		"type", metric.MetricType,
		"value", metric.Value,
		"unit", metric.Unit)
}

// Helper methods for calculating metrics

func (cm *CacheMonitor) calculateHitRate(stats *CacheStats) float64 {
	total := stats.TotalHits + stats.TotalMisses
	if total == 0 {
		return 0
	}
	return float64(stats.TotalHits) / float64(total)
}

func (cm *CacheMonitor) calculateL1HitRate(stats *CacheStats) float64 {
	total := stats.L1Hits + stats.L1Misses
	if total == 0 {
		return 0
	}
	return float64(stats.L1Hits) / float64(total)
}

func (cm *CacheMonitor) calculateL2HitRate(stats *CacheStats) float64 {
	total := stats.L2Hits + stats.L2Misses
	if total == 0 {
		return 0
	}
	return float64(stats.L2Hits) / float64(total)
}

func (cm *CacheMonitor) calculateL3HitRate(stats *CacheStats) float64 {
	total := stats.L3Hits + stats.L3Misses
	if total == 0 {
		return 0
	}
	return float64(stats.L3Hits) / float64(total)
}
