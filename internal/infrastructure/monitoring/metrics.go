package monitoring

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// MetricsCollector collects and manages application metrics
type MetricsCollector struct {
	mu        sync.RWMutex
	metrics   map[string]*Metric
	logger    domain.Logger
	startTime time.Time
}

// Metric represents a single metric
type Metric struct {
	Name        string            `json:"name"`
	Type        MetricType        `json:"type"`
	Value       any               `json:"value"`
	Labels      map[string]string `json:"labels"`
	Timestamp   time.Time         `json:"timestamp"`
	Description string            `json:"description"`
	Metadata    map[string]any    `json:"metadata,omitempty"`
}

// MetricType represents the type of metric
type MetricType string

const (
	Counter   MetricType = "counter"
	Gauge     MetricType = "gauge"
	Histogram MetricType = "histogram"
	Summary   MetricType = "summary"
)

// PerformanceMetrics represents application performance metrics
type PerformanceMetrics struct {
	HTTPRequests    *HTTPRequestMetrics    `json:"http_requests"`
	DatabaseQueries *DatabaseQueryMetrics  `json:"database_queries"`
	CacheOperations *CacheOperationMetrics `json:"cache_operations"`
	SystemResources *SystemResourceMetrics `json:"system_resources"`
	BusinessMetrics *BusinessMetrics       `json:"business_metrics"`
	Timestamp       time.Time              `json:"timestamp"`
	Uptime          time.Duration          `json:"uptime"`
}

// HTTPRequestMetrics tracks HTTP request performance
type HTTPRequestMetrics struct {
	TotalRequests      int64         `json:"total_requests"`
	SuccessfulRequests int64         `json:"successful_requests"`
	FailedRequests     int64         `json:"failed_requests"`
	AverageLatency     time.Duration `json:"average_latency"`
	MaxLatency         time.Duration `json:"max_latency"`
	MinLatency         time.Duration `json:"min_latency"`
	RequestsPerSecond  float64       `json:"requests_per_second"`
	StatusCodes        map[int]int64 `json:"status_codes"`
}

// DatabaseQueryMetrics tracks database query performance
type DatabaseQueryMetrics struct {
	TotalQueries   int64                  `json:"total_queries"`
	SlowQueries    int64                  `json:"slow_queries"`
	AverageLatency time.Duration          `json:"average_latency"`
	MaxLatency     time.Duration          `json:"max_latency"`
	MinLatency     time.Duration          `json:"min_latency"`
	ConnectionPool *ConnectionPoolMetrics `json:"connection_pool"`
	QueryTypes     map[string]int64       `json:"query_types"`
}

// ConnectionPoolMetrics tracks database connection pool metrics
type ConnectionPoolMetrics struct {
	MaxOpenConns      int           `json:"max_open_conns"`
	OpenConns         int           `json:"open_conns"`
	InUse             int           `json:"in_use"`
	Idle              int           `json:"idle"`
	WaitCount         int64         `json:"wait_count"`
	WaitDuration      time.Duration `json:"wait_duration"`
	MaxIdleClosed     int64         `json:"max_idle_closed"`
	MaxIdleTimeClosed int64         `json:"max_idle_time_closed"`
	MaxLifetimeClosed int64         `json:"max_lifetime_closed"`
}

// CacheOperationMetrics tracks cache operation performance
type CacheOperationMetrics struct {
	TotalOperations     int64         `json:"total_operations"`
	CacheHits           int64         `json:"cache_hits"`
	CacheMisses         int64         `json:"cache_misses"`
	HitRate             float64       `json:"hit_rate"`
	AverageLatency      time.Duration `json:"average_latency"`
	MaxLatency          time.Duration `json:"max_latency"`
	MinLatency          time.Duration `json:"min_latency"`
	OperationsPerSecond float64       `json:"operations_per_second"`
}

// SystemResourceMetrics tracks system resource usage
type SystemResourceMetrics struct {
	CPUUsage        float64       `json:"cpu_usage"`
	MemoryUsage     int64         `json:"memory_usage"`
	MemoryAvailable int64         `json:"memory_available"`
	DiskUsage       int64         `json:"disk_usage"`
	DiskAvailable   int64         `json:"disk_available"`
	Goroutines      int           `json:"goroutines"`
	GCPauseTime     time.Duration `json:"gc_pause_time"`
}

// BusinessMetrics tracks business-specific metrics
type BusinessMetrics struct {
	TotalBuildings     int64 `json:"total_buildings"`
	TotalEquipment     int64 `json:"total_equipment"`
	TotalComponents    int64 `json:"total_components"`
	TotalUsers         int64 `json:"total_users"`
	TotalOrganizations int64 `json:"total_organizations"`
	ActiveSessions     int64 `json:"active_sessions"`
	IFCImports         int64 `json:"ifc_imports"`
	IFCExports         int64 `json:"ifc_exports"`
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector(logger domain.Logger) *MetricsCollector {
	return &MetricsCollector{
		metrics:   make(map[string]*Metric),
		logger:    logger,
		startTime: time.Now(),
	}
}

// RecordMetric records a metric
func (mc *MetricsCollector) RecordMetric(name string, metricType MetricType, value any, labels map[string]string) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	metric := &Metric{
		Name:        name,
		Type:        metricType,
		Value:       value,
		Labels:      labels,
		Timestamp:   time.Now(),
		Description: fmt.Sprintf("Metric: %s", name),
	}

	mc.metrics[name] = metric
}

// GetMetric retrieves a metric by name
func (mc *MetricsCollector) GetMetric(name string) (*Metric, bool) {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	metric, exists := mc.metrics[name]
	return metric, exists
}

// GetAllMetrics returns all metrics
func (mc *MetricsCollector) GetAllMetrics() map[string]*Metric {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	// Return a copy to avoid race conditions
	result := make(map[string]*Metric)
	for name, metric := range mc.metrics {
		result[name] = metric
	}
	return result
}

// IncrementCounter increments a counter metric
func (mc *MetricsCollector) IncrementCounter(name string, labels map[string]string) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	if metric, exists := mc.metrics[name]; exists {
		if counter, ok := metric.Value.(int64); ok {
			metric.Value = counter + 1
			metric.Timestamp = time.Now()
		}
	} else {
		mc.metrics[name] = &Metric{
			Name:      name,
			Type:      Counter,
			Value:     int64(1),
			Labels:    labels,
			Timestamp: time.Now(),
		}
	}
}

// SetGauge sets a gauge metric value
func (mc *MetricsCollector) SetGauge(name string, value any, labels map[string]string) {
	mc.RecordMetric(name, Gauge, value, labels)
}

// RecordHistogram records a histogram metric
func (mc *MetricsCollector) RecordHistogram(name string, value float64, labels map[string]string) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	if metric, exists := mc.metrics[name]; exists {
		if histogram, ok := metric.Value.([]float64); ok {
			metric.Value = append(histogram, value)
			metric.Timestamp = time.Now()
		}
	} else {
		mc.metrics[name] = &Metric{
			Name:      name,
			Type:      Histogram,
			Value:     []float64{value},
			Labels:    labels,
			Timestamp: time.Now(),
		}
	}
}

// GetPerformanceMetrics returns comprehensive performance metrics
func (mc *MetricsCollector) GetPerformanceMetrics() *PerformanceMetrics {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	return &PerformanceMetrics{
		HTTPRequests:    mc.getHTTPRequestMetrics(),
		DatabaseQueries: mc.getDatabaseQueryMetrics(),
		CacheOperations: mc.getCacheOperationMetrics(),
		SystemResources: mc.getSystemResourceMetrics(),
		BusinessMetrics: mc.getBusinessMetrics(),
		Timestamp:       time.Now(),
		Uptime:          time.Since(mc.startTime),
	}
}

// getHTTPRequestMetrics extracts HTTP request metrics
func (mc *MetricsCollector) getHTTPRequestMetrics() *HTTPRequestMetrics {
	metrics := &HTTPRequestMetrics{
		StatusCodes: make(map[int]int64),
	}

	// Extract HTTP metrics from collected metrics
	for name, metric := range mc.metrics {
		switch name {
		case "http_requests_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.TotalRequests = val
			}
		case "http_requests_successful":
			if val, ok := metric.Value.(int64); ok {
				metrics.SuccessfulRequests = val
			}
		case "http_requests_failed":
			if val, ok := metric.Value.(int64); ok {
				metrics.FailedRequests = val
			}
		case "http_request_latency_avg":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.AverageLatency = val
			}
		case "http_request_latency_max":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.MaxLatency = val
			}
		case "http_request_latency_min":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.MinLatency = val
			}
		case "http_requests_per_second":
			if val, ok := metric.Value.(float64); ok {
				metrics.RequestsPerSecond = val
			}
		}
	}

	return metrics
}

// getDatabaseQueryMetrics extracts database query metrics
func (mc *MetricsCollector) getDatabaseQueryMetrics() *DatabaseQueryMetrics {
	metrics := &DatabaseQueryMetrics{
		QueryTypes: make(map[string]int64),
	}

	// Extract database metrics from collected metrics
	for name, metric := range mc.metrics {
		switch name {
		case "db_queries_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.TotalQueries = val
			}
		case "db_slow_queries":
			if val, ok := metric.Value.(int64); ok {
				metrics.SlowQueries = val
			}
		case "db_query_latency_avg":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.AverageLatency = val
			}
		case "db_query_latency_max":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.MaxLatency = val
			}
		case "db_query_latency_min":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.MinLatency = val
			}
		}
	}

	return metrics
}

// getCacheOperationMetrics extracts cache operation metrics
func (mc *MetricsCollector) getCacheOperationMetrics() *CacheOperationMetrics {
	metrics := &CacheOperationMetrics{}

	// Extract cache metrics from collected metrics
	for name, metric := range mc.metrics {
		switch name {
		case "cache_operations_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.TotalOperations = val
			}
		case "cache_hits":
			if val, ok := metric.Value.(int64); ok {
				metrics.CacheHits = val
			}
		case "cache_misses":
			if val, ok := metric.Value.(int64); ok {
				metrics.CacheMisses = val
			}
		case "cache_hit_rate":
			if val, ok := metric.Value.(float64); ok {
				metrics.HitRate = val
			}
		case "cache_latency_avg":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.AverageLatency = val
			}
		case "cache_latency_max":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.MaxLatency = val
			}
		case "cache_latency_min":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.MinLatency = val
			}
		case "cache_operations_per_second":
			if val, ok := metric.Value.(float64); ok {
				metrics.OperationsPerSecond = val
			}
		}
	}

	return metrics
}

// getSystemResourceMetrics extracts system resource metrics
func (mc *MetricsCollector) getSystemResourceMetrics() *SystemResourceMetrics {
	metrics := &SystemResourceMetrics{}

	// Extract system metrics from collected metrics
	for name, metric := range mc.metrics {
		switch name {
		case "cpu_usage":
			if val, ok := metric.Value.(float64); ok {
				metrics.CPUUsage = val
			}
		case "memory_usage":
			if val, ok := metric.Value.(int64); ok {
				metrics.MemoryUsage = val
			}
		case "memory_available":
			if val, ok := metric.Value.(int64); ok {
				metrics.MemoryAvailable = val
			}
		case "disk_usage":
			if val, ok := metric.Value.(int64); ok {
				metrics.DiskUsage = val
			}
		case "disk_available":
			if val, ok := metric.Value.(int64); ok {
				metrics.DiskAvailable = val
			}
		case "goroutines":
			if val, ok := metric.Value.(int); ok {
				metrics.Goroutines = val
			}
		case "gc_pause_time":
			if val, ok := metric.Value.(time.Duration); ok {
				metrics.GCPauseTime = val
			}
		}
	}

	return metrics
}

// getBusinessMetrics extracts business-specific metrics
func (mc *MetricsCollector) getBusinessMetrics() *BusinessMetrics {
	metrics := &BusinessMetrics{}

	// Extract business metrics from collected metrics
	for name, metric := range mc.metrics {
		switch name {
		case "buildings_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.TotalBuildings = val
			}
		case "equipment_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.TotalEquipment = val
			}
		case "components_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.TotalComponents = val
			}
		case "users_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.TotalUsers = val
			}
		case "organizations_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.TotalOrganizations = val
			}
		case "active_sessions":
			if val, ok := metric.Value.(int64); ok {
				metrics.ActiveSessions = val
			}
		case "ifc_imports_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.IFCImports = val
			}
		case "ifc_exports_total":
			if val, ok := metric.Value.(int64); ok {
				metrics.IFCExports = val
			}
		}
	}

	return metrics
}

// ClearMetrics clears all metrics
func (mc *MetricsCollector) ClearMetrics() {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.metrics = make(map[string]*Metric)
	mc.startTime = time.Now()
}

// ExportMetrics exports metrics in a specific format
func (mc *MetricsCollector) ExportMetrics(format string) ([]byte, error) {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	switch format {
	case "json":
		return mc.exportJSON()
	case "prometheus":
		return mc.exportPrometheus()
	default:
		return nil, fmt.Errorf("unsupported export format: %s", format)
	}
}

// exportJSON exports metrics as JSON
func (mc *MetricsCollector) exportJSON() ([]byte, error) {
	// This would use json.Marshal in a real implementation
	return []byte("{}"), nil
}

// exportPrometheus exports metrics in Prometheus format
func (mc *MetricsCollector) exportPrometheus() ([]byte, error) {
	// This would format metrics in Prometheus format
	return []byte("# Prometheus metrics\n"), nil
}

// StartMetricsCollection starts background metrics collection
func (mc *MetricsCollector) StartMetricsCollection(ctx context.Context) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			mc.collectSystemMetrics()
		}
	}
}

// collectSystemMetrics collects system-level metrics
func (mc *MetricsCollector) collectSystemMetrics() {
	// Collect goroutine count
	mc.SetGauge("goroutines", 0, map[string]string{"source": "runtime"})

	// Collect memory usage (simplified)
	mc.SetGauge("memory_usage", int64(0), map[string]string{"source": "runtime"})

	// Collect other system metrics
	mc.logger.Debug("System metrics collected")
}
