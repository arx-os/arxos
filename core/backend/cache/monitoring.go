// Package cache provides comprehensive monitoring for the caching system
package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// Monitor provides comprehensive monitoring for the cache system
type Monitor struct {
	cache           CacheInterface
	confidenceCache *ConfidenceCache
	clusterManager  *ClusterManager
	logger          *zap.Logger
	metrics         *SystemMetrics
	alerts          *AlertManager
	healthChecks    map[string]HealthCheck
	mutex           sync.RWMutex
	stopCh          chan struct{}
	running         bool
}

// SystemMetrics aggregates all cache system metrics
type SystemMetrics struct {
	// Performance metrics
	OverallHitRatio     float64           `json:"overall_hit_ratio"`
	AverageResponseTime time.Duration     `json:"average_response_time"`
	ThroughputPerSecond float64           `json:"throughput_per_second"`
	
	// Cache-specific metrics
	ConfidenceMetrics   ConfidenceCacheMetrics `json:"confidence_metrics"`
	ClusterMetrics      ClusterMetrics         `json:"cluster_metrics"`
	
	// System health
	SystemHealth        string                 `json:"system_health"`
	LastUpdated         time.Time              `json:"last_updated"`
	
	// Resource utilization
	MemoryUsage         MemoryUsageMetrics     `json:"memory_usage"`
	ConnectionMetrics   ConnectionMetrics      `json:"connection_metrics"`
	
	// Error tracking
	ErrorRates          ErrorRateMetrics       `json:"error_rates"`
	
	// Performance trends
	PerformanceTrends   map[string][]DataPoint `json:"performance_trends"`
}

// MemoryUsageMetrics tracks memory usage across the cache system
type MemoryUsageMetrics struct {
	TotalMemory      int64   `json:"total_memory"`
	UsedMemory       int64   `json:"used_memory"`
	FreeMemory       int64   `json:"free_memory"`
	UsagePercentage  float64 `json:"usage_percentage"`
	EvictionCount    int64   `json:"eviction_count"`
	MaxMemoryPolicy  string  `json:"max_memory_policy"`
}

// ConnectionMetrics tracks connection pool metrics
type ConnectionMetrics struct {
	ActiveConnections int `json:"active_connections"`
	IdleConnections   int `json:"idle_connections"`
	MaxConnections    int `json:"max_connections"`
	ConnectionErrors  int64 `json:"connection_errors"`
	PoolUtilization   float64 `json:"pool_utilization"`
}

// ErrorRateMetrics tracks error rates and types
type ErrorRateMetrics struct {
	TotalErrors       int64            `json:"total_errors"`
	ErrorsPerSecond   float64          `json:"errors_per_second"`
	ErrorsByType      map[string]int64 `json:"errors_by_type"`
	CriticalErrors    int64            `json:"critical_errors"`
	TimeoutErrors     int64            `json:"timeout_errors"`
	ConnectionErrors  int64            `json:"connection_errors"`
}

// DataPoint represents a time-series data point
type DataPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
}

// HealthCheck represents a health check function
type HealthCheck struct {
	Name        string                              `json:"name"`
	Description string                              `json:"description"`
	CheckFunc   func(context.Context) HealthResult `json:"-"`
	Interval    time.Duration                       `json:"interval"`
	Timeout     time.Duration                       `json:"timeout"`
	Critical    bool                                `json:"critical"`
	LastRun     time.Time                           `json:"last_run"`
	LastResult  HealthResult                        `json:"last_result"`
}

// HealthResult represents the result of a health check
type HealthResult struct {
	Status      string                 `json:"status"` // healthy, degraded, unhealthy
	Message     string                 `json:"message"`
	Duration    time.Duration          `json:"duration"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// AlertManager handles cache system alerts
type AlertManager struct {
	logger      *zap.Logger
	thresholds  AlertThresholds
	subscribers []AlertSubscriber
	mutex       sync.RWMutex
}

// AlertThresholds defines alert thresholds
type AlertThresholds struct {
	HitRatioLow         float64       `json:"hit_ratio_low"`
	ResponseTimeHigh    time.Duration `json:"response_time_high"`
	ErrorRateHigh       float64       `json:"error_rate_high"`
	MemoryUsageHigh     float64       `json:"memory_usage_high"`
	NodeDownThreshold   int           `json:"node_down_threshold"`
	FailoverThreshold   int           `json:"failover_threshold"`
}

// AlertSubscriber receives cache alerts
type AlertSubscriber interface {
	OnAlert(alert Alert)
}

// Alert represents a cache system alert
type Alert struct {
	Level       string                 `json:"level"`       // info, warning, critical
	Type        string                 `json:"type"`        // performance, availability, error
	Title       string                 `json:"title"`
	Message     string                 `json:"message"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
	Resolved    bool                   `json:"resolved"`
	ResolvedAt  *time.Time             `json:"resolved_at,omitempty"`
}

// NewMonitor creates a new cache system monitor
func NewMonitor(
	cache CacheInterface,
	confidenceCache *ConfidenceCache,
	clusterManager *ClusterManager,
	logger *zap.Logger,
) *Monitor {
	monitor := &Monitor{
		cache:           cache,
		confidenceCache: confidenceCache,
		clusterManager:  clusterManager,
		logger:          logger,
		metrics:         &SystemMetrics{},
		alerts:          NewAlertManager(logger),
		healthChecks:    make(map[string]HealthCheck),
		stopCh:          make(chan struct{}),
	}

	// Register default health checks
	monitor.registerDefaultHealthChecks()

	return monitor
}

// Start begins monitoring
func (m *Monitor) Start(ctx context.Context) error {
	m.mutex.Lock()
	if m.running {
		m.mutex.Unlock()
		return nil
	}
	m.running = true
	m.mutex.Unlock()

	// Start metrics collection
	go m.collectMetrics(ctx)

	// Start health checks
	go m.runHealthChecks(ctx)

	// Start alert monitoring
	go m.monitorAlerts(ctx)

	m.logger.Info("Cache monitoring started")
	return nil
}

// Stop halts monitoring
func (m *Monitor) Stop() error {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	if !m.running {
		return nil
	}

	m.running = false
	close(m.stopCh)

	m.logger.Info("Cache monitoring stopped")
	return nil
}

// registerDefaultHealthChecks sets up standard health checks
func (m *Monitor) registerDefaultHealthChecks() {
	m.healthChecks["cache_connectivity"] = HealthCheck{
		Name:        "cache_connectivity",
		Description: "Checks if cache is reachable and responsive",
		CheckFunc:   m.checkCacheConnectivity,
		Interval:    30 * time.Second,
		Timeout:     5 * time.Second,
		Critical:    true,
	}

	m.healthChecks["confidence_cache"] = HealthCheck{
		Name:        "confidence_cache",
		Description: "Checks confidence cache functionality",
		CheckFunc:   m.checkConfidenceCache,
		Interval:    1 * time.Minute,
		Timeout:     10 * time.Second,
		Critical:    false,
	}

	m.healthChecks["cluster_health"] = HealthCheck{
		Name:        "cluster_health",
		Description: "Checks Redis cluster health",
		CheckFunc:   m.checkClusterHealth,
		Interval:    1 * time.Minute,
		Timeout:     10 * time.Second,
		Critical:    true,
	}

	m.healthChecks["memory_usage"] = HealthCheck{
		Name:        "memory_usage",
		Description: "Monitors cache memory usage",
		CheckFunc:   m.checkMemoryUsage,
		Interval:    2 * time.Minute,
		Timeout:     5 * time.Second,
		Critical:    false,
	}

	m.healthChecks["performance"] = HealthCheck{
		Name:        "performance",
		Description: "Monitors cache performance metrics",
		CheckFunc:   m.checkPerformance,
		Interval:    1 * time.Minute,
		Timeout:     5 * time.Second,
		Critical:    false,
	}
}

// collectMetrics periodically collects system metrics
func (m *Monitor) collectMetrics(ctx context.Context) {
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			m.updateMetrics(ctx)
		case <-m.stopCh:
			return
		case <-ctx.Done():
			return
		}
	}
}

// updateMetrics updates all system metrics
func (m *Monitor) updateMetrics(ctx context.Context) {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	// Update confidence cache metrics
	if m.confidenceCache != nil {
		m.metrics.ConfidenceMetrics = m.confidenceCache.GetMetrics()
	}

	// Update cluster metrics
	if m.clusterManager != nil {
		m.metrics.ClusterMetrics = m.clusterManager.GetMetrics()
	}

	// Calculate overall hit ratio
	totalHits := float64(m.metrics.ConfidenceMetrics.ConfidenceHits + 
						 m.metrics.ConfidenceMetrics.PatternHits +
						 m.metrics.ConfidenceMetrics.ValidationCacheHits)
	totalMisses := float64(m.metrics.ConfidenceMetrics.ConfidenceMisses + 
						   m.metrics.ConfidenceMetrics.PatternMisses +
						   m.metrics.ConfidenceMetrics.ValidationCacheMisses)
	
	if totalHits+totalMisses > 0 {
		m.metrics.OverallHitRatio = totalHits / (totalHits + totalMisses)
	}

	// Update system health
	m.metrics.SystemHealth = m.calculateSystemHealth()
	m.metrics.LastUpdated = time.Now()

	// Update performance trends
	m.updatePerformanceTrends()
}

// runHealthChecks executes health checks on schedule
func (m *Monitor) runHealthChecks(ctx context.Context) {
	for name, check := range m.healthChecks {
		go m.runIndividualHealthCheck(ctx, name, check)
	}
}

// runIndividualHealthCheck runs a specific health check
func (m *Monitor) runIndividualHealthCheck(ctx context.Context, name string, check HealthCheck) {
	ticker := time.NewTicker(check.Interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			checkCtx, cancel := context.WithTimeout(ctx, check.Timeout)
			
			start := time.Now()
			result := check.CheckFunc(checkCtx)
			result.Duration = time.Since(start)
			result.Timestamp = time.Now()
			
			m.mutex.Lock()
			check.LastRun = time.Now()
			check.LastResult = result
			m.healthChecks[name] = check
			m.mutex.Unlock()
			
			// Trigger alerts if necessary
			if result.Status != "healthy" && check.Critical {
				m.alerts.TriggerAlert(Alert{
					Level:     "critical",
					Type:      "availability",
					Title:     fmt.Sprintf("Critical health check failed: %s", name),
					Message:   result.Message,
					Timestamp: time.Now(),
					Metadata: map[string]interface{}{
						"check_name": name,
						"duration":   result.Duration,
					},
				})
			}
			
			cancel()
			
		case <-m.stopCh:
			return
		case <-ctx.Done():
			return
		}
	}
}

// Health check implementations

func (m *Monitor) checkCacheConnectivity(ctx context.Context) HealthResult {
	if err := m.cache.Health(ctx); err != nil {
		return HealthResult{
			Status:  "unhealthy",
			Message: fmt.Sprintf("Cache connectivity failed: %v", err),
		}
	}
	
	return HealthResult{
		Status:  "healthy",
		Message: "Cache is connected and responsive",
	}
}

func (m *Monitor) checkConfidenceCache(ctx context.Context) HealthResult {
	if m.confidenceCache == nil {
		return HealthResult{
			Status:  "unhealthy",
			Message: "Confidence cache not initialized",
		}
	}
	
	if err := m.confidenceCache.Health(ctx); err != nil {
		return HealthResult{
			Status:  "degraded",
			Message: fmt.Sprintf("Confidence cache issues: %v", err),
		}
	}
	
	metrics := m.confidenceCache.GetMetrics()
	hitRatio := float64(metrics.ConfidenceHits) / float64(metrics.ConfidenceHits + metrics.ConfidenceMisses)
	
	if hitRatio < 0.5 {
		return HealthResult{
			Status:  "degraded",
			Message: fmt.Sprintf("Low confidence cache hit ratio: %.2f", hitRatio),
			Metadata: map[string]interface{}{
				"hit_ratio": hitRatio,
			},
		}
	}
	
	return HealthResult{
		Status:  "healthy",
		Message: "Confidence cache is operating normally",
		Metadata: map[string]interface{}{
			"hit_ratio": hitRatio,
		},
	}
}

func (m *Monitor) checkClusterHealth(ctx context.Context) HealthResult {
	if m.clusterManager == nil {
		return HealthResult{
			Status:  "healthy",
			Message: "Single node Redis configuration",
		}
	}
	
	metrics := m.clusterManager.GetMetrics()
	
	switch metrics.ClusterHealth {
	case "healthy":
		return HealthResult{
			Status:  "healthy",
			Message: fmt.Sprintf("All %d cluster nodes online", metrics.NodesOnline),
		}
	case "degraded":
		return HealthResult{
			Status:  "degraded",
			Message: fmt.Sprintf("%d of %d cluster nodes online", metrics.NodesOnline, metrics.NodesTotal),
		}
	case "critical":
		return HealthResult{
			Status:  "unhealthy",
			Message: fmt.Sprintf("Only %d of %d cluster nodes online", metrics.NodesOnline, metrics.NodesTotal),
		}
	default:
		return HealthResult{
			Status:  "unhealthy",
			Message: "Unknown cluster health status",
		}
	}
}

func (m *Monitor) checkMemoryUsage(ctx context.Context) HealthResult {
	// This would typically query Redis for memory statistics
	// Simplified implementation for example
	
	memoryUsage := 75.0 // Example percentage
	
	if memoryUsage > 90 {
		return HealthResult{
			Status:  "unhealthy",
			Message: fmt.Sprintf("Critical memory usage: %.1f%%", memoryUsage),
		}
	} else if memoryUsage > 80 {
		return HealthResult{
			Status:  "degraded",
			Message: fmt.Sprintf("High memory usage: %.1f%%", memoryUsage),
		}
	}
	
	return HealthResult{
		Status:  "healthy",
		Message: fmt.Sprintf("Memory usage normal: %.1f%%", memoryUsage),
	}
}

func (m *Monitor) checkPerformance(ctx context.Context) HealthResult {
	// Check average response time and throughput
	avgResponseTime := 50 * time.Millisecond // Example
	
	if avgResponseTime > 500*time.Millisecond {
		return HealthResult{
			Status:  "degraded",
			Message: fmt.Sprintf("High response time: %v", avgResponseTime),
		}
	}
	
	return HealthResult{
		Status:  "healthy",
		Message: fmt.Sprintf("Performance normal: %v response time", avgResponseTime),
	}
}

// calculateSystemHealth determines overall system health
func (m *Monitor) calculateSystemHealth() string {
	criticalFailures := 0
	degradedComponents := 0
	totalComponents := 0
	
	for _, check := range m.healthChecks {
		if check.LastResult.Timestamp.IsZero() {
			continue
		}
		
		totalComponents++
		
		switch check.LastResult.Status {
		case "unhealthy":
			if check.Critical {
				criticalFailures++
			} else {
				degradedComponents++
			}
		case "degraded":
			degradedComponents++
		}
	}
	
	if criticalFailures > 0 {
		return "critical"
	} else if degradedComponents > totalComponents/2 {
		return "degraded"
	} else if degradedComponents > 0 {
		return "warning"
	}
	
	return "healthy"
}

// updatePerformanceTrends updates performance trend data
func (m *Monitor) updatePerformanceTrends() {
	if m.metrics.PerformanceTrends == nil {
		m.metrics.PerformanceTrends = make(map[string][]DataPoint)
	}
	
	now := time.Now()
	
	// Add current hit ratio
	m.addDataPoint("hit_ratio", now, m.metrics.OverallHitRatio)
	
	// Add cluster health score
	healthScore := 0.0
	switch m.metrics.SystemHealth {
	case "healthy":
		healthScore = 1.0
	case "warning":
		healthScore = 0.7
	case "degraded":
		healthScore = 0.4
	case "critical":
		healthScore = 0.1
	}
	m.addDataPoint("health_score", now, healthScore)
	
	// Keep only last 100 data points
	for key, points := range m.metrics.PerformanceTrends {
		if len(points) > 100 {
			m.metrics.PerformanceTrends[key] = points[len(points)-100:]
		}
	}
}

// addDataPoint adds a data point to performance trends
func (m *Monitor) addDataPoint(metric string, timestamp time.Time, value float64) {
	if m.metrics.PerformanceTrends[metric] == nil {
		m.metrics.PerformanceTrends[metric] = make([]DataPoint, 0)
	}
	
	m.metrics.PerformanceTrends[metric] = append(
		m.metrics.PerformanceTrends[metric],
		DataPoint{Timestamp: timestamp, Value: value},
	)
}

// monitorAlerts watches for alert conditions
func (m *Monitor) monitorAlerts(ctx context.Context) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			m.checkAlertConditions()
		case <-m.stopCh:
			return
		case <-ctx.Done():
			return
		}
	}
}

// checkAlertConditions checks for conditions that should trigger alerts
func (m *Monitor) checkAlertConditions() {
	// Check hit ratio
	if m.metrics.OverallHitRatio < m.alerts.thresholds.HitRatioLow {
		m.alerts.TriggerAlert(Alert{
			Level:     "warning",
			Type:      "performance",
			Title:     "Low cache hit ratio",
			Message:   fmt.Sprintf("Hit ratio %.2f below threshold %.2f", m.metrics.OverallHitRatio, m.alerts.thresholds.HitRatioLow),
			Timestamp: time.Now(),
		})
	}

	// Check error rates
	if m.metrics.ErrorRates.ErrorsPerSecond > m.alerts.thresholds.ErrorRateHigh {
		m.alerts.TriggerAlert(Alert{
			Level:     "critical",
			Type:      "error",
			Title:     "High error rate",
			Message:   fmt.Sprintf("Error rate %.2f/sec exceeds threshold %.2f/sec", m.metrics.ErrorRates.ErrorsPerSecond, m.alerts.thresholds.ErrorRateHigh),
			Timestamp: time.Now(),
		})
	}
}

// GetMetrics returns current system metrics
func (m *Monitor) GetMetrics() SystemMetrics {
	m.mutex.RLock()
	defer m.mutex.RUnlock()
	
	// Deep copy metrics
	metrics := *m.metrics
	return metrics
}

// GetHealthStatus returns current health status
func (m *Monitor) GetHealthStatus() map[string]HealthResult {
	m.mutex.RLock()
	defer m.mutex.RUnlock()
	
	status := make(map[string]HealthResult)
	for name, check := range m.healthChecks {
		status[name] = check.LastResult
	}
	
	return status
}

// GetMetricsJSON returns metrics as JSON
func (m *Monitor) GetMetricsJSON() ([]byte, error) {
	metrics := m.GetMetrics()
	return json.MarshalIndent(metrics, "", "  ")
}

// Alert Manager implementation

// NewAlertManager creates a new alert manager
func NewAlertManager(logger *zap.Logger) *AlertManager {
	return &AlertManager{
		logger: logger,
		thresholds: AlertThresholds{
			HitRatioLow:       0.6,
			ResponseTimeHigh:  1 * time.Second,
			ErrorRateHigh:     10.0,
			MemoryUsageHigh:   85.0,
			NodeDownThreshold: 1,
			FailoverThreshold: 2,
		},
		subscribers: make([]AlertSubscriber, 0),
	}
}

// TriggerAlert sends an alert to all subscribers
func (am *AlertManager) TriggerAlert(alert Alert) {
	am.mutex.RLock()
	subscribers := am.subscribers
	am.mutex.RUnlock()

	// Log the alert
	am.logger.Warn("Cache system alert triggered",
		zap.String("level", alert.Level),
		zap.String("type", alert.Type),
		zap.String("title", alert.Title),
		zap.String("message", alert.Message))

	// Notify subscribers
	for _, subscriber := range subscribers {
		go subscriber.OnAlert(alert)
	}
}

// Subscribe adds an alert subscriber
func (am *AlertManager) Subscribe(subscriber AlertSubscriber) {
	am.mutex.Lock()
	defer am.mutex.Unlock()
	
	am.subscribers = append(am.subscribers, subscriber)
}