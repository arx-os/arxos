package monitoring

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// MetricsCollector provides a centralized metrics collection system
type MetricsCollector struct {
	mu         sync.RWMutex
	metrics    map[string]*Metric
	counters   map[string]*Counter
	gauges     map[string]*Gauge
	timers     map[string]*Timer
	histograms map[string]*Histogram
}

// Metric represents a generic metric
type Metric struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Value       interface{}            `json:"value"`
	Labels      map[string]string      `json:"labels"`
	Timestamp   time.Time              `json:"timestamp"`
	Description string                 `json:"description"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Counter represents a monotonically increasing metric
type Counter struct {
	Name        string            `json:"name"`
	Value       int64             `json:"value"`
	Labels      map[string]string `json:"labels"`
	LastUpdated time.Time         `json:"last_updated"`
	Description string            `json:"description"`
}

// Gauge represents a metric that can go up or down
type Gauge struct {
	Name        string            `json:"name"`
	Value       float64           `json:"value"`
	Labels      map[string]string `json:"labels"`
	LastUpdated time.Time         `json:"last_updated"`
	Description string            `json:"description"`
}

// Timer represents a metric for measuring duration
type Timer struct {
	Name        string            `json:"name"`
	Duration    time.Duration     `json:"duration"`
	Labels      map[string]string `json:"labels"`
	LastUpdated time.Time         `json:"last_updated"`
	Description string            `json:"description"`
}

// Histogram represents a distribution of values
type Histogram struct {
	Name        string            `json:"name"`
	Buckets     map[string]int64  `json:"buckets"`
	Count       int64             `json:"count"`
	Sum         float64           `json:"sum"`
	Labels      map[string]string `json:"labels"`
	LastUpdated time.Time         `json:"last_updated"`
	Description string            `json:"description"`
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector() *MetricsCollector {
	return &MetricsCollector{
		metrics:    make(map[string]*Metric),
		counters:   make(map[string]*Counter),
		gauges:     make(map[string]*Gauge),
		timers:     make(map[string]*Timer),
		histograms: make(map[string]*Histogram),
	}
}

// IncrementCounter increments a counter metric
func (mc *MetricsCollector) IncrementCounter(name string, labels map[string]string) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	key := mc.buildKey(name, labels)
	if counter, exists := mc.counters[key]; exists {
		counter.Value++
		counter.LastUpdated = time.Now()
	} else {
		mc.counters[key] = &Counter{
			Name:        name,
			Value:       1,
			Labels:      labels,
			LastUpdated: time.Now(),
			Description: fmt.Sprintf("Counter metric: %s", name),
		}
	}
}

// SetGauge sets a gauge metric value
func (mc *MetricsCollector) SetGauge(name string, value float64, labels map[string]string) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	key := mc.buildKey(name, labels)
	mc.gauges[key] = &Gauge{
		Name:        name,
		Value:       value,
		Labels:      labels,
		LastUpdated: time.Now(),
		Description: fmt.Sprintf("Gauge metric: %s", name),
	}
}

// RecordTimer records a timer metric
func (mc *MetricsCollector) RecordTimer(name string, duration time.Duration, labels map[string]string) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	key := mc.buildKey(name, labels)
	mc.timers[key] = &Timer{
		Name:        name,
		Duration:    duration,
		Labels:      labels,
		LastUpdated: time.Now(),
		Description: fmt.Sprintf("Timer metric: %s", name),
	}
}

// RecordHistogram records a histogram metric
func (mc *MetricsCollector) RecordHistogram(name string, value float64, labels map[string]string) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	key := mc.buildKey(name, labels)
	if histogram, exists := mc.histograms[key]; exists {
		histogram.Count++
		histogram.Sum += value
		histogram.LastUpdated = time.Now()

		// Update buckets (simplified implementation)
		bucket := mc.getBucket(value)
		histogram.Buckets[bucket]++
	} else {
		mc.histograms[key] = &Histogram{
			Name:        name,
			Buckets:     make(map[string]int64),
			Count:       1,
			Sum:         value,
			Labels:      labels,
			LastUpdated: time.Now(),
			Description: fmt.Sprintf("Histogram metric: %s", name),
		}

		bucket := mc.getBucket(value)
		mc.histograms[key].Buckets[bucket] = 1
	}
}

// GetCounter retrieves a counter metric
func (mc *MetricsCollector) GetCounter(name string, labels map[string]string) *Counter {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	key := mc.buildKey(name, labels)
	return mc.counters[key]
}

// GetGauge retrieves a gauge metric
func (mc *MetricsCollector) GetGauge(name string, labels map[string]string) *Gauge {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	key := mc.buildKey(name, labels)
	return mc.gauges[key]
}

// GetTimer retrieves a timer metric
func (mc *MetricsCollector) GetTimer(name string, labels map[string]string) *Timer {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	key := mc.buildKey(name, labels)
	return mc.timers[key]
}

// GetHistogram retrieves a histogram metric
func (mc *MetricsCollector) GetHistogram(name string, labels map[string]string) *Histogram {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	key := mc.buildKey(name, labels)
	return mc.histograms[key]
}

// GetAllMetrics returns all collected metrics
func (mc *MetricsCollector) GetAllMetrics() map[string]interface{} {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	return map[string]interface{}{
		"counters":   mc.counters,
		"gauges":     mc.gauges,
		"timers":     mc.timers,
		"histograms": mc.histograms,
		"timestamp":  time.Now(),
	}
}

// GetMetricsSummary returns a summary of all metrics
func (mc *MetricsCollector) GetMetricsSummary() map[string]interface{} {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	return map[string]interface{}{
		"total_counters":   len(mc.counters),
		"total_gauges":     len(mc.gauges),
		"total_timers":     len(mc.timers),
		"total_histograms": len(mc.histograms),
		"timestamp":        time.Now(),
	}
}

// Reset clears all metrics
func (mc *MetricsCollector) Reset() {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.counters = make(map[string]*Counter)
	mc.gauges = make(map[string]*Gauge)
	mc.timers = make(map[string]*Timer)
	mc.histograms = make(map[string]*Histogram)
}

// buildKey creates a unique key for a metric with labels
func (mc *MetricsCollector) buildKey(name string, labels map[string]string) string {
	if len(labels) == 0 {
		return name
	}

	key := name
	for k, v := range labels {
		key += fmt.Sprintf("_%s_%s", k, v)
	}
	return key
}

// getBucket determines which bucket a value belongs to
func (mc *MetricsCollector) getBucket(value float64) string {
	buckets := []float64{0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0}

	for _, bucket := range buckets {
		if value <= bucket {
			return fmt.Sprintf("le_%.1f", bucket)
		}
	}
	return "le_inf"
}

// ExportMetrics exports metrics in Prometheus format
func (mc *MetricsCollector) ExportMetrics() string {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	var output string

	// Export counters
	for _, counter := range mc.counters {
		output += fmt.Sprintf("# HELP %s %s\n", counter.Name, counter.Description)
		output += fmt.Sprintf("# TYPE %s counter\n", counter.Name)
		labels := mc.formatLabels(counter.Labels)
		output += fmt.Sprintf("%s%s %d\n", counter.Name, labels, counter.Value)
	}

	// Export gauges
	for _, gauge := range mc.gauges {
		output += fmt.Sprintf("# HELP %s %s\n", gauge.Name, gauge.Description)
		output += fmt.Sprintf("# TYPE %s gauge\n", gauge.Name)
		labels := mc.formatLabels(gauge.Labels)
		output += fmt.Sprintf("%s%s %.2f\n", gauge.Name, labels, gauge.Value)
	}

	// Export histograms
	for _, histogram := range mc.histograms {
		output += fmt.Sprintf("# HELP %s %s\n", histogram.Name, histogram.Description)
		output += fmt.Sprintf("# TYPE %s histogram\n", histogram.Name)
		labels := mc.formatLabels(histogram.Labels)

		// Export buckets
		for bucket, count := range histogram.Buckets {
			bucketLabels := labels + fmt.Sprintf(",le=\"%s\"", bucket)
			output += fmt.Sprintf("%s_bucket%s %d\n", histogram.Name, bucketLabels, count)
		}

		// Export sum and count
		output += fmt.Sprintf("%s_sum%s %.2f\n", histogram.Name, labels, histogram.Sum)
		output += fmt.Sprintf("%s_count%s %d\n", histogram.Name, labels, histogram.Count)
	}

	return output
}

// formatLabels formats labels for Prometheus export
func (mc *MetricsCollector) formatLabels(labels map[string]string) string {
	if len(labels) == 0 {
		return ""
	}

	var formatted string
	for k, v := range labels {
		if formatted == "" {
			formatted = fmt.Sprintf("{%s=\"%s\"", k, v)
		} else {
			formatted += fmt.Sprintf(",%s=\"%s\"", k, v)
		}
	}
	formatted += "}"
	return formatted
}

// StartMetricsCollection starts background metrics collection
func (mc *MetricsCollector) StartMetricsCollection(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	logger.Info("Started metrics collection with interval %v", interval)

	for {
		select {
		case <-ctx.Done():
			logger.Info("Stopped metrics collection")
			return
		case <-ticker.C:
			mc.collectSystemMetrics()
		}
	}
}

// collectSystemMetrics collects system-level metrics
func (mc *MetricsCollector) collectSystemMetrics() {
	// Collect memory usage (placeholder implementation)
	mc.SetGauge("system_memory_usage", 1024.0, map[string]string{
		"type": "bytes",
	})

	// Collect CPU usage (placeholder implementation)
	mc.SetGauge("system_cpu_usage", 25.0, map[string]string{
		"type": "percent",
	})

	// Collect goroutine count (placeholder implementation)
	mc.SetGauge("system_goroutines", 10.0, map[string]string{
		"type": "count",
	})
}

// Global metrics collector instance
var globalMetricsCollector *MetricsCollector
var metricsOnce sync.Once

// GetGlobalMetricsCollector returns the global metrics collector instance
func GetGlobalMetricsCollector() *MetricsCollector {
	metricsOnce.Do(func() {
		globalMetricsCollector = NewMetricsCollector()
	})
	return globalMetricsCollector
}

// Convenience functions for global metrics collection
func IncrementCounter(name string, labels map[string]string) {
	GetGlobalMetricsCollector().IncrementCounter(name, labels)
}

func SetGauge(name string, value float64, labels map[string]string) {
	GetGlobalMetricsCollector().SetGauge(name, value, labels)
}

func RecordTimer(name string, duration time.Duration, labels map[string]string) {
	GetGlobalMetricsCollector().RecordTimer(name, duration, labels)
}

func RecordHistogram(name string, value float64, labels map[string]string) {
	GetGlobalMetricsCollector().RecordHistogram(name, value, labels)
}
