package telemetry

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sort"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// MetricsCollector collects and exposes metrics
type MetricsCollector struct {
	config   *ObservabilityConfig
	counters map[string]*CounterMetric
	gauges   map[string]*GaugeMetric
	histos   map[string]*HistogramMetric
	mu       sync.RWMutex
	server   *http.Server
}

// CounterMetric represents a counter metric
type CounterMetric struct {
	Name  string            `json:"name"`
	Value float64           `json:"value"`
	Tags  map[string]string `json:"tags"`
	mu    sync.RWMutex
}

// GaugeMetric represents a gauge metric
type GaugeMetric struct {
	Name      string            `json:"name"`
	Value     float64           `json:"value"`
	Tags      map[string]string `json:"tags"`
	Timestamp time.Time         `json:"timestamp"`
	mu        sync.RWMutex
}

// HistogramMetric represents a histogram metric
type HistogramMetric struct {
	Name    string            `json:"name"`
	Count   int64             `json:"count"`
	Sum     float64           `json:"sum"`
	Min     float64           `json:"min"`
	Max     float64           `json:"max"`
	Buckets map[float64]int64 `json:"buckets"`
	Tags    map[string]string `json:"tags"`
	mu      sync.RWMutex
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector(config *ObservabilityConfig) *MetricsCollector {
	mc := &MetricsCollector{
		config:   config,
		counters: make(map[string]*CounterMetric),
		gauges:   make(map[string]*GaugeMetric),
		histos:   make(map[string]*HistogramMetric),
	}

	// Start metrics HTTP server
	if config.Metrics.Enabled {
		mc.startMetricsServer()
	}

	return mc
}

// IncrementCounter increments a counter metric
func (mc *MetricsCollector) IncrementCounter(name string, tags map[string]string) {
	mc.incrementCounterBy(name, 1, tags)
}

// IncrementCounterBy increments a counter metric by a specific value
func (mc *MetricsCollector) incrementCounterBy(name string, value float64, tags map[string]string) {
	key := mc.getMetricKey(name, tags)

	mc.mu.Lock()
	counter, exists := mc.counters[key]
	if !exists {
		counter = &CounterMetric{
			Name: name,
			Tags: tags,
		}
		mc.counters[key] = counter
	}
	mc.mu.Unlock()

	counter.mu.Lock()
	counter.Value += value
	counter.mu.Unlock()
}

// RecordGauge records a gauge metric
func (mc *MetricsCollector) RecordGauge(name string, value float64, tags map[string]string) {
	key := mc.getMetricKey(name, tags)

	mc.mu.Lock()
	gauge, exists := mc.gauges[key]
	if !exists {
		gauge = &GaugeMetric{
			Name: name,
			Tags: tags,
		}
		mc.gauges[key] = gauge
	}
	mc.mu.Unlock()

	gauge.mu.Lock()
	gauge.Value = value
	gauge.Timestamp = time.Now()
	gauge.mu.Unlock()
}

// RecordHistogram records a histogram metric
func (mc *MetricsCollector) RecordHistogram(name string, value float64, tags map[string]string) {
	key := mc.getMetricKey(name, tags)

	mc.mu.Lock()
	histo, exists := mc.histos[key]
	if !exists {
		histo = &HistogramMetric{
			Name:    name,
			Tags:    tags,
			Min:     value,
			Max:     value,
			Buckets: make(map[float64]int64),
		}
		// Initialize standard buckets
		buckets := []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10}
		for _, bucket := range buckets {
			histo.Buckets[bucket] = 0
		}
		mc.histos[key] = histo
	}
	mc.mu.Unlock()

	histo.mu.Lock()
	histo.Count++
	histo.Sum += value
	if value < histo.Min {
		histo.Min = value
	}
	if value > histo.Max {
		histo.Max = value
	}

	// Update buckets
	for bucket := range histo.Buckets {
		if value <= bucket {
			histo.Buckets[bucket]++
		}
	}
	histo.mu.Unlock()
}

// GetCounters returns all counter metrics
func (mc *MetricsCollector) GetCounters() map[string]*CounterMetric {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	result := make(map[string]*CounterMetric)
	for k, v := range mc.counters {
		result[k] = v
	}
	return result
}

// GetGauges returns all gauge metrics
func (mc *MetricsCollector) GetGauges() map[string]*GaugeMetric {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	result := make(map[string]*GaugeMetric)
	for k, v := range mc.gauges {
		result[k] = v
	}
	return result
}

// GetHistograms returns all histogram metrics
func (mc *MetricsCollector) GetHistograms() map[string]*HistogramMetric {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	result := make(map[string]*HistogramMetric)
	for k, v := range mc.histos {
		result[k] = v
	}
	return result
}

// Stop stops the metrics collector
func (mc *MetricsCollector) Stop() {
	if mc.server != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		mc.server.Shutdown(ctx)
	}
}

// startMetricsServer starts the HTTP server for metrics endpoint
func (mc *MetricsCollector) startMetricsServer() {
	mux := http.NewServeMux()
	mux.HandleFunc(mc.config.Metrics.Endpoint, mc.handleMetrics)
	mux.HandleFunc("/health", mc.handleHealth)

	mc.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", mc.config.Metrics.Port),
		Handler: mux,
	}

	go func() {
		logger.Info("Metrics server listening on :%d%s", mc.config.Metrics.Port, mc.config.Metrics.Endpoint)
		if err := mc.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("Metrics server error: %v", err)
		}
	}()
}

// handleMetrics handles the metrics endpoint
func (mc *MetricsCollector) handleMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	format := r.URL.Query().Get("format")

	switch format {
	case "prometheus":
		mc.handlePrometheusMetrics(w, r)
	default:
		mc.handleJSONMetrics(w, r)
	}
}

// handleJSONMetrics returns metrics in JSON format
func (mc *MetricsCollector) handleJSONMetrics(w http.ResponseWriter, r *http.Request) {
	metrics := map[string]interface{}{
		"timestamp":  time.Now().Unix(),
		"counters":   mc.GetCounters(),
		"gauges":     mc.GetGauges(),
		"histograms": mc.GetHistograms(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// handlePrometheusMetrics returns metrics in Prometheus format
func (mc *MetricsCollector) handlePrometheusMetrics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")

	// Write counters
	for _, counter := range mc.GetCounters() {
		counter.mu.RLock()
		fmt.Fprintf(w, "# TYPE %s counter\n", counter.Name)
		fmt.Fprintf(w, "%s%s %.6f\n", counter.Name, mc.formatTags(counter.Tags), counter.Value)
		counter.mu.RUnlock()
	}

	// Write gauges
	for _, gauge := range mc.GetGauges() {
		gauge.mu.RLock()
		fmt.Fprintf(w, "# TYPE %s gauge\n", gauge.Name)
		fmt.Fprintf(w, "%s%s %.6f\n", gauge.Name, mc.formatTags(gauge.Tags), gauge.Value)
		gauge.mu.RUnlock()
	}

	// Write histograms
	for _, histo := range mc.GetHistograms() {
		histo.mu.RLock()
		fmt.Fprintf(w, "# TYPE %s histogram\n", histo.Name)

		// Write buckets
		var buckets []float64
		for bucket := range histo.Buckets {
			buckets = append(buckets, bucket)
		}
		sort.Float64s(buckets)

		for _, bucket := range buckets {
			tags := make(map[string]string)
			for k, v := range histo.Tags {
				tags[k] = v
			}
			tags["le"] = fmt.Sprintf("%.3f", bucket)
			fmt.Fprintf(w, "%s_bucket%s %d\n", histo.Name, mc.formatTags(tags), histo.Buckets[bucket])
		}

		// Write count and sum
		fmt.Fprintf(w, "%s_count%s %d\n", histo.Name, mc.formatTags(histo.Tags), histo.Count)
		fmt.Fprintf(w, "%s_sum%s %.6f\n", histo.Name, mc.formatTags(histo.Tags), histo.Sum)
		histo.mu.RUnlock()
	}
}

// handleHealth handles the health endpoint
func (mc *MetricsCollector) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().Unix(),
		"metrics": map[string]int{
			"counters":   len(mc.counters),
			"gauges":     len(mc.gauges),
			"histograms": len(mc.histos),
		},
	})
}

// getMetricKey generates a unique key for a metric with tags
func (mc *MetricsCollector) getMetricKey(name string, tags map[string]string) string {
	if len(tags) == 0 {
		return name
	}

	// Sort tags for consistent keys
	var keys []string
	for k := range tags {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	key := name
	for _, k := range keys {
		key += fmt.Sprintf(",%s=%s", k, tags[k])
	}
	return key
}

// formatTags formats tags for Prometheus output
func (mc *MetricsCollector) formatTags(tags map[string]string) string {
	if len(tags) == 0 {
		return ""
	}

	result := "{"
	first := true
	for k, v := range tags {
		if !first {
			result += ","
		}
		result += fmt.Sprintf(`%s="%s"`, k, v)
		first = false
	}
	result += "}"
	return result
}
