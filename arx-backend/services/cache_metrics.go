package services

import (
	"context"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// MetricType represents different types of cache metrics
type MetricType string

const (
	MetricHitRate     MetricType = "hit_rate"
	MetricMissRate    MetricType = "miss_rate"
	MetricLatency     MetricType = "latency"
	MetricThroughput  MetricType = "throughput"
	MetricMemoryUsage MetricType = "memory_usage"
	MetricDiskUsage   MetricType = "disk_usage"
	MetricCompression MetricType = "compression"
	MetricEviction    MetricType = "eviction"
	MetricWarmup      MetricType = "warmup"
	MetricError       MetricType = "error"
)

// MetricLevel represents the cache level for metrics
type MetricLevel string

const (
	LevelMemory   MetricLevel = "memory"
	LevelRedis    MetricLevel = "redis"
	LevelDisk     MetricLevel = "disk"
	LevelDatabase MetricLevel = "database"
	LevelOverall  MetricLevel = "overall"
)

// CacheMetric represents a single metric measurement
type CacheMetric struct {
	Type      MetricType        `json:"type"`
	Level     MetricLevel       `json:"level"`
	Value     float64           `json:"value"`
	Unit      string            `json:"unit"`
	Timestamp time.Time         `json:"timestamp"`
	Tags      map[string]string `json:"tags,omitempty"`
}

// PerformanceSnapshot represents a snapshot of cache performance
type PerformanceSnapshot struct {
	Timestamp        time.Time               `json:"timestamp"`
	HitRate          float64                 `json:"hit_rate"`
	MissRate         float64                 `json:"miss_rate"`
	AverageLatency   time.Duration           `json:"average_latency"`
	Throughput       float64                 `json:"throughput"`
	MemoryUsage      map[string]float64      `json:"memory_usage"`
	DiskUsage        map[string]float64      `json:"disk_usage"`
	CompressionRatio float64                 `json:"compression_ratio"`
	EvictionCount    int64                   `json:"eviction_count"`
	ErrorCount       int64                   `json:"error_count"`
	LevelMetrics     map[MetricLevel]float64 `json:"level_metrics"`
}

// AlertThreshold represents alerting thresholds for metrics
type AlertThreshold struct {
	MetricType MetricType  `json:"metric_type"`
	Level      MetricLevel `json:"level"`
	Operator   string      `json:"operator"` // >, <, >=, <=, ==
	Value      float64     `json:"value"`
	Severity   string      `json:"severity"` // info, warning, critical
	Message    string      `json:"message"`
}

// CacheMetrics provides comprehensive monitoring and analytics
type CacheMetrics struct {
	cacheService *CacheService
	logger       *zap.Logger
	mu           sync.RWMutex

	// Metric storage
	metrics    []*CacheMetric
	maxMetrics int
	metricsTTL time.Duration

	// Performance tracking
	snapshots    []*PerformanceSnapshot
	maxSnapshots int

	// Alerting
	thresholds []*AlertThreshold
	alerts     []*CacheAlert
	maxAlerts  int

	// Aggregation
	aggregationInterval time.Duration
	lastAggregation     time.Time

	// Background processing
	ctx    context.Context
	cancel context.CancelFunc
}

// CacheAlert represents a cache performance alert
type CacheAlert struct {
	ID        string                 `json:"id"`
	Type      MetricType             `json:"type"`
	Level     MetricLevel            `json:"level"`
	Severity  string                 `json:"severity"`
	Message   string                 `json:"message"`
	Value     float64                `json:"value"`
	Threshold float64                `json:"threshold"`
	Timestamp time.Time              `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// NewCacheMetrics creates a new cache metrics service
func NewCacheMetrics(cacheService *CacheService, logger *zap.Logger) *CacheMetrics {
	ctx, cancel := context.WithCancel(context.Background())

	cm := &CacheMetrics{
		cacheService:        cacheService,
		logger:              logger,
		metrics:             make([]*CacheMetric, 0),
		maxMetrics:          10000,
		metricsTTL:          24 * time.Hour,
		snapshots:           make([]*PerformanceSnapshot, 0),
		maxSnapshots:        1000,
		thresholds:          make([]*AlertThreshold, 0),
		alerts:              make([]*CacheAlert, 0),
		maxAlerts:           1000,
		aggregationInterval: 5 * time.Minute,
		ctx:                 ctx,
		cancel:              cancel,
	}

	// Initialize default thresholds
	cm.initializeDefaultThresholds()

	// Start background processing
	go cm.backgroundProcessor()

	logger.Info("Cache metrics service initialized")
	return cm
}

// RecordMetric records a new metric
func (cm *CacheMetrics) RecordMetric(metricType MetricType, level MetricLevel, value float64, unit string, tags map[string]string) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	metric := &CacheMetric{
		Type:      metricType,
		Level:     level,
		Value:     value,
		Unit:      unit,
		Timestamp: time.Now(),
		Tags:      tags,
	}

	cm.metrics = append(cm.metrics, metric)

	// Maintain metrics size limit
	if len(cm.metrics) > cm.maxMetrics {
		cm.metrics = cm.metrics[1:]
	}

	// Check thresholds
	cm.checkThresholds(metric)
}

// RecordHit records a cache hit
func (cm *CacheMetrics) RecordHit(level MetricLevel, latency time.Duration) {
	cm.RecordMetric(MetricHitRate, level, 1.0, "count", map[string]string{
		"operation":  "hit",
		"latency_ms": fmt.Sprintf("%.2f", float64(latency.Microseconds())/1000.0),
	})
}

// RecordMiss records a cache miss
func (cm *CacheMetrics) RecordMiss(level MetricLevel, latency time.Duration) {
	cm.RecordMetric(MetricMissRate, level, 1.0, "count", map[string]string{
		"operation":  "miss",
		"latency_ms": fmt.Sprintf("%.2f", float64(latency.Microseconds())/1000.0),
	})
}

// RecordLatency records operation latency
func (cm *CacheMetrics) RecordLatency(level MetricLevel, operation string, latency time.Duration) {
	cm.RecordMetric(MetricLatency, level, float64(latency.Microseconds())/1000.0, "ms", map[string]string{
		"operation": operation,
	})
}

// RecordThroughput records throughput metrics
func (cm *CacheMetrics) RecordThroughput(level MetricLevel, operations int64, duration time.Duration) {
	throughput := float64(operations) / duration.Seconds()
	cm.RecordMetric(MetricThroughput, level, throughput, "ops/sec", map[string]string{
		"operations":   fmt.Sprintf("%d", operations),
		"duration_sec": fmt.Sprintf("%.2f", duration.Seconds()),
	})
}

// RecordMemoryUsage records memory usage metrics
func (cm *CacheMetrics) RecordMemoryUsage(level MetricLevel, usedBytes, totalBytes int64) {
	usagePercent := float64(usedBytes) / float64(totalBytes) * 100.0
	cm.RecordMetric(MetricMemoryUsage, level, usagePercent, "percent", map[string]string{
		"used_bytes":  fmt.Sprintf("%d", usedBytes),
		"total_bytes": fmt.Sprintf("%d", totalBytes),
	})
}

// RecordDiskUsage records disk usage metrics
func (cm *CacheMetrics) RecordDiskUsage(level MetricLevel, usedBytes, totalBytes int64) {
	usagePercent := float64(usedBytes) / float64(totalBytes) * 100.0
	cm.RecordMetric(MetricDiskUsage, level, usagePercent, "percent", map[string]string{
		"used_bytes":  fmt.Sprintf("%d", usedBytes),
		"total_bytes": fmt.Sprintf("%d", totalBytes),
	})
}

// RecordCompression records compression metrics
func (cm *CacheMetrics) RecordCompression(level MetricLevel, originalSize, compressedSize int64) {
	ratio := float64(compressedSize) / float64(originalSize) * 100.0
	cm.RecordMetric(MetricCompression, level, ratio, "percent", map[string]string{
		"original_size":   fmt.Sprintf("%d", originalSize),
		"compressed_size": fmt.Sprintf("%d", compressedSize),
	})
}

// RecordEviction records cache eviction metrics
func (cm *CacheMetrics) RecordEviction(level MetricLevel, reason string) {
	cm.RecordMetric(MetricEviction, level, 1.0, "count", map[string]string{
		"reason": reason,
	})
}

// RecordWarmup records cache warmup metrics
func (cm *CacheMetrics) RecordWarmup(level MetricLevel, keysWarmed int64, duration time.Duration) {
	cm.RecordMetric(MetricWarmup, level, float64(keysWarmed), "keys", map[string]string{
		"duration_ms": fmt.Sprintf("%.2f", float64(duration.Microseconds())/1000.0),
	})
}

// RecordError records error metrics
func (cm *CacheMetrics) RecordError(level MetricLevel, errorType string, errorMessage string) {
	cm.RecordMetric(MetricError, level, 1.0, "count", map[string]string{
		"error_type":    errorType,
		"error_message": errorMessage,
	})
}

// GetMetrics retrieves metrics with optional filtering
func (cm *CacheMetrics) GetMetrics(metricType MetricType, level MetricLevel, since time.Time) []*CacheMetric {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var filtered []*CacheMetric
	for _, metric := range cm.metrics {
		if metric.Timestamp.Before(since) {
			continue
		}
		if metricType != "" && metric.Type != metricType {
			continue
		}
		if level != "" && metric.Level != level {
			continue
		}
		filtered = append(filtered, metric)
	}

	return filtered
}

// GetPerformanceSnapshot creates a performance snapshot
func (cm *CacheMetrics) GetPerformanceSnapshot() *PerformanceSnapshot {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	snapshot := &PerformanceSnapshot{
		Timestamp:    time.Now(),
		LevelMetrics: make(map[MetricLevel]float64),
		MemoryUsage:  make(map[string]float64),
		DiskUsage:    make(map[string]float64),
	}

	// Calculate aggregated metrics
	metrics := cm.getRecentMetrics(10 * time.Minute)

	// Calculate hit/miss rates
	hits := cm.countMetrics(metrics, MetricHitRate)
	misses := cm.countMetrics(metrics, MetricMissRate)
	total := hits + misses
	if total > 0 {
		snapshot.HitRate = float64(hits) / float64(total) * 100.0
		snapshot.MissRate = float64(misses) / float64(total) * 100.0
	}

	// Calculate average latency
	snapshot.AverageLatency = cm.calculateAverageLatency(metrics)

	// Calculate throughput
	snapshot.Throughput = cm.calculateThroughput(metrics)

	// Calculate compression ratio
	snapshot.CompressionRatio = cm.calculateCompressionRatio(metrics)

	// Calculate eviction and error counts
	snapshot.EvictionCount = cm.countMetrics(metrics, MetricEviction)
	snapshot.ErrorCount = cm.countMetrics(metrics, MetricError)

	// Calculate level-specific metrics
	cm.calculateLevelMetrics(snapshot, metrics)

	return snapshot
}

// AddAlertThreshold adds a new alert threshold
func (cm *CacheMetrics) AddAlertThreshold(threshold *AlertThreshold) {
	cm.mu.Lock()
	defer cm.mu.Unlock()
	cm.thresholds = append(cm.thresholds, threshold)
}

// GetAlerts retrieves alerts with optional filtering
func (cm *CacheMetrics) GetAlerts(severity string, since time.Time) []*CacheAlert {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var filtered []*CacheAlert
	for _, alert := range cm.alerts {
		if alert.Timestamp.Before(since) {
			continue
		}
		if severity != "" && alert.Severity != severity {
			continue
		}
		filtered = append(filtered, alert)
	}

	return filtered
}

// ClearAlerts clears old alerts
func (cm *CacheMetrics) ClearAlerts() {
	cm.mu.Lock()
	defer cm.mu.Unlock()
	cm.alerts = make([]*CacheAlert, 0)
}

// GetMetricsSummary returns a summary of current metrics
func (cm *CacheMetrics) GetMetricsSummary() map[string]interface{} {
	snapshot := cm.GetPerformanceSnapshot()

	return map[string]interface{}{
		"hit_rate":          snapshot.HitRate,
		"miss_rate":         snapshot.MissRate,
		"average_latency":   snapshot.AverageLatency.String(),
		"throughput":        snapshot.Throughput,
		"compression_ratio": snapshot.CompressionRatio,
		"eviction_count":    snapshot.EvictionCount,
		"error_count":       snapshot.ErrorCount,
		"level_metrics":     snapshot.LevelMetrics,
		"memory_usage":      snapshot.MemoryUsage,
		"disk_usage":        snapshot.DiskUsage,
		"alerts_count":      len(cm.GetAlerts("", time.Now().Add(-24*time.Hour))),
	}
}

// ExportMetrics exports metrics in various formats
func (cm *CacheMetrics) ExportMetrics(format string) ([]byte, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	switch format {
	case "json":
		return cm.exportJSON()
	case "prometheus":
		return cm.exportPrometheus()
	case "csv":
		return cm.exportCSV()
	default:
		return nil, fmt.Errorf("unsupported export format: %s", format)
	}
}

// Close cleans up the metrics service
func (cm *CacheMetrics) Close() {
	cm.cancel()
	cm.logger.Info("Cache metrics service closed")
}

// Helper methods

func (cm *CacheMetrics) initializeDefaultThresholds() {
	defaultThresholds := []*AlertThreshold{
		{
			MetricType: MetricHitRate,
			Level:      LevelOverall,
			Operator:   "<",
			Value:      80.0,
			Severity:   "warning",
			Message:    "Cache hit rate below 80%",
		},
		{
			MetricType: MetricLatency,
			Level:      LevelOverall,
			Operator:   ">",
			Value:      100.0, // 100ms
			Severity:   "warning",
			Message:    "Cache latency above 100ms",
		},
		{
			MetricType: MetricMemoryUsage,
			Level:      LevelMemory,
			Operator:   ">",
			Value:      90.0,
			Severity:   "critical",
			Message:    "Memory cache usage above 90%",
		},
		{
			MetricType: MetricError,
			Level:      LevelOverall,
			Operator:   ">",
			Value:      10.0,
			Severity:   "critical",
			Message:    "Cache error count above 10",
		},
	}

	cm.thresholds = defaultThresholds
}

func (cm *CacheMetrics) checkThresholds(metric *CacheMetric) {
	for _, threshold := range cm.thresholds {
		if threshold.MetricType != metric.Type || threshold.Level != metric.Level {
			continue
		}

		var triggered bool
		switch threshold.Operator {
		case ">":
			triggered = metric.Value > threshold.Value
		case ">=":
			triggered = metric.Value >= threshold.Value
		case "<":
			triggered = metric.Value < threshold.Value
		case "<=":
			triggered = metric.Value <= threshold.Value
		case "==":
			triggered = metric.Value == threshold.Value
		}

		if triggered {
			alert := &CacheAlert{
				ID:        fmt.Sprintf("alert_%d", time.Now().UnixNano()),
				Type:      metric.Type,
				Level:     metric.Level,
				Severity:  threshold.Severity,
				Message:   threshold.Message,
				Value:     metric.Value,
				Threshold: threshold.Value,
				Timestamp: time.Now(),
				Metadata: map[string]interface{}{
					"unit": metric.Unit,
					"tags": metric.Tags,
				},
			}

			cm.alerts = append(cm.alerts, alert)
			if len(cm.alerts) > cm.maxAlerts {
				cm.alerts = cm.alerts[1:]
			}

			cm.logger.Warn("Cache alert triggered",
				zap.String("alert_id", alert.ID),
				zap.String("severity", alert.Severity),
				zap.String("message", alert.Message),
				zap.Float64("value", alert.Value),
				zap.Float64("threshold", alert.Threshold),
			)
		}
	}
}

func (cm *CacheMetrics) backgroundProcessor() {
	ticker := time.NewTicker(cm.aggregationInterval)
	defer ticker.Stop()

	for {
		select {
		case <-cm.ctx.Done():
			return
		case <-ticker.C:
			cm.aggregateMetrics()
			cm.cleanupOldMetrics()
		}
	}
}

func (cm *CacheMetrics) aggregateMetrics() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Create performance snapshot
	snapshot := cm.GetPerformanceSnapshot()
	cm.snapshots = append(cm.snapshots, snapshot)

	// Maintain snapshots size limit
	if len(cm.snapshots) > cm.maxSnapshots {
		cm.snapshots = cm.snapshots[1:]
	}

	cm.lastAggregation = time.Now()
}

func (cm *CacheMetrics) cleanupOldMetrics() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	cutoff := time.Now().Add(-cm.metricsTTL)
	var filtered []*CacheMetric
	for _, metric := range cm.metrics {
		if metric.Timestamp.After(cutoff) {
			filtered = append(filtered, metric)
		}
	}
	cm.metrics = filtered
}

func (cm *CacheMetrics) getRecentMetrics(duration time.Duration) []*CacheMetric {
	since := time.Now().Add(-duration)
	return cm.GetMetrics("", "", since)
}

func (cm *CacheMetrics) countMetrics(metrics []*CacheMetric, metricType MetricType) int64 {
	var count int64
	for _, metric := range metrics {
		if metric.Type == metricType {
			count++
		}
	}
	return count
}

func (cm *CacheMetrics) calculateAverageLatency(metrics []*CacheMetric) time.Duration {
	var total time.Duration
	var count int64

	for _, metric := range metrics {
		if metric.Type == MetricLatency {
			total += time.Duration(metric.Value * float64(time.Millisecond))
			count++
		}
	}

	if count == 0 {
		return 0
	}
	return total / time.Duration(count)
}

func (cm *CacheMetrics) calculateThroughput(metrics []*CacheMetric) float64 {
	var total float64
	var count int64

	for _, metric := range metrics {
		if metric.Type == MetricThroughput {
			total += metric.Value
			count++
		}
	}

	if count == 0 {
		return 0
	}
	return total / float64(count)
}

func (cm *CacheMetrics) calculateCompressionRatio(metrics []*CacheMetric) float64 {
	var total float64
	var count int64

	for _, metric := range metrics {
		if metric.Type == MetricCompression {
			total += metric.Value
			count++
		}
	}

	if count == 0 {
		return 0
	}
	return total / float64(count)
}

func (cm *CacheMetrics) calculateLevelMetrics(snapshot *PerformanceSnapshot, metrics []*CacheMetric) {
	levelCounts := make(map[MetricLevel]int64)
	levelLatencies := make(map[MetricLevel]time.Duration)

	for _, metric := range metrics {
		if metric.Type == MetricLatency {
			levelCounts[metric.Level]++
			levelLatencies[metric.Level] += time.Duration(metric.Value * float64(time.Millisecond))
		}
	}

	for level, count := range levelCounts {
		if count > 0 {
			snapshot.LevelMetrics[level] = float64(levelLatencies[level]) / float64(count) / float64(time.Millisecond)
		}
	}
}

func (cm *CacheMetrics) exportJSON() ([]byte, error) {
	// Implementation for JSON export
	return nil, fmt.Errorf("JSON export not implemented")
}

func (cm *CacheMetrics) exportPrometheus() ([]byte, error) {
	// Implementation for Prometheus export
	return nil, fmt.Errorf("Prometheus export not implemented")
}

func (cm *CacheMetrics) exportCSV() ([]byte, error) {
	// Implementation for CSV export
	return nil, fmt.Errorf("CSV export not implemented")
}
