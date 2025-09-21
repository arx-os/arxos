package metrics

import (
	"context"
	"fmt"
	"net/http"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// MetricType represents the type of metric
type MetricType string

const (
	MetricTypeCounter   MetricType = "counter"
	MetricTypeGauge     MetricType = "gauge"
	MetricTypeHistogram MetricType = "histogram"
	MetricTypeSummary   MetricType = "summary"
)

// Metric represents a single metric
type Metric struct {
	Name      string
	Type      MetricType
	Help      string
	Labels    map[string]string
	value     atomic.Value
	histogram *Histogram
	mu        sync.RWMutex
}

// Histogram tracks distribution of values
type Histogram struct {
	buckets []float64
	counts  []uint64
	sum     float64
	count   uint64
	mu      sync.Mutex
}

// Collector manages all metrics
type Collector struct {
	metrics   map[string]*Metric
	mu        sync.RWMutex
	startTime time.Time

	// Pre-defined metrics
	httpRequests      *Metric
	httpDuration      *Metric
	httpErrors        *Metric
	dbQueries         *Metric
	dbErrors          *Metric
	dbDuration        *Metric
	cacheHits         *Metric
	cacheMisses       *Metric
	activeConnections *Metric
	goroutines        *Metric
	memoryUsage       *Metric
}

// Global collector instance
var (
	globalCollector *Collector
	once            sync.Once
)

// Initialize creates the global metrics collector
func Initialize() *Collector {
	once.Do(func() {
		globalCollector = NewCollector()
		globalCollector.RegisterDefaultMetrics()
	})
	return globalCollector
}

// GetCollector returns the global collector
func GetCollector() *Collector {
	if globalCollector == nil {
		return Initialize()
	}
	return globalCollector
}

// NewCollector creates a new metrics collector
func NewCollector() *Collector {
	return &Collector{
		metrics:   make(map[string]*Metric),
		startTime: time.Now(),
	}
}

// RegisterDefaultMetrics registers all default metrics
func (c *Collector) RegisterDefaultMetrics() {
	// HTTP metrics
	c.httpRequests = c.RegisterCounter(
		"arxos_http_requests_total",
		"Total number of HTTP requests",
		nil,
	)

	c.httpDuration = c.RegisterHistogram(
		"arxos_http_request_duration_seconds",
		"HTTP request latencies in seconds",
		[]float64{0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0},
	)

	c.httpErrors = c.RegisterCounter(
		"arxos_http_errors_total",
		"Total number of HTTP errors",
		nil,
	)

	// Database metrics
	c.dbQueries = c.RegisterCounter(
		"arxos_db_queries_total",
		"Total number of database queries",
		nil,
	)

	c.dbErrors = c.RegisterCounter(
		"arxos_db_errors_total",
		"Total number of database errors",
		nil,
	)

	c.dbDuration = c.RegisterHistogram(
		"arxos_db_query_duration_seconds",
		"Database query latencies in seconds",
		[]float64{0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0},
	)

	// Cache metrics
	c.cacheHits = c.RegisterCounter(
		"arxos_cache_hits_total",
		"Total number of cache hits",
		nil,
	)

	c.cacheMisses = c.RegisterCounter(
		"arxos_cache_misses_total",
		"Total number of cache misses",
		nil,
	)

	// System metrics
	c.activeConnections = c.RegisterGauge(
		"arxos_active_connections",
		"Number of active connections",
		nil,
	)

	c.goroutines = c.RegisterGauge(
		"arxos_goroutines",
		"Number of goroutines",
		nil,
	)

	c.memoryUsage = c.RegisterGauge(
		"arxos_memory_usage_bytes",
		"Current memory usage in bytes",
		nil,
	)
}

// RegisterCounter registers a new counter metric
func (c *Collector) RegisterCounter(name, help string, labels map[string]string) *Metric {
	c.mu.Lock()
	defer c.mu.Unlock()

	metric := &Metric{
		Name:   name,
		Type:   MetricTypeCounter,
		Help:   help,
		Labels: labels,
	}
	metric.value.Store(float64(0))
	c.metrics[name] = metric
	return metric
}

// RegisterGauge registers a new gauge metric
func (c *Collector) RegisterGauge(name, help string, labels map[string]string) *Metric {
	c.mu.Lock()
	defer c.mu.Unlock()

	metric := &Metric{
		Name:   name,
		Type:   MetricTypeGauge,
		Help:   help,
		Labels: labels,
	}
	metric.value.Store(float64(0))
	c.metrics[name] = metric
	return metric
}

// RegisterHistogram registers a new histogram metric
func (c *Collector) RegisterHistogram(name, help string, buckets []float64) *Metric {
	c.mu.Lock()
	defer c.mu.Unlock()

	metric := &Metric{
		Name: name,
		Type: MetricTypeHistogram,
		Help: help,
		histogram: &Histogram{
			buckets: buckets,
			counts:  make([]uint64, len(buckets)+1), // +1 for +Inf bucket
		},
	}
	c.metrics[name] = metric
	return metric
}

// Metric operations

// Inc increments a counter
func (m *Metric) Inc() {
	if m.Type != MetricTypeCounter {
		return
	}
	m.Add(1)
}

// Add adds a value to a counter
func (m *Metric) Add(v float64) {
	if m.Type != MetricTypeCounter {
		return
	}
	for {
		old := m.value.Load().(float64)
		if m.value.CompareAndSwap(old, old+v) {
			break
		}
	}
}

// Set sets a gauge value
func (m *Metric) Set(v float64) {
	if m.Type != MetricTypeGauge {
		return
	}
	m.value.Store(v)
}

// Observe adds an observation to a histogram
func (m *Metric) Observe(v float64) {
	if m.Type != MetricTypeHistogram && m.histogram != nil {
		m.histogram.Observe(v)
	}
}

// Observe adds a value to the histogram
func (h *Histogram) Observe(v float64) {
	h.mu.Lock()
	defer h.mu.Unlock()

	h.sum += v
	h.count++

	// Find the right bucket
	for i, upper := range h.buckets {
		if v <= upper {
			h.counts[i]++
			return
		}
	}
	// Falls into +Inf bucket
	h.counts[len(h.counts)-1]++
}

// HTTP Middleware for metrics collection

// HTTPMetricsMiddleware collects HTTP metrics
func HTTPMetricsMiddleware(next http.Handler) http.Handler {
	collector := GetCollector()

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Wrap response writer to capture status code
		wrapped := &responseWriter{
			ResponseWriter: w,
			statusCode:     http.StatusOK,
		}

		// Increment request counter
		collector.httpRequests.Inc()

		// Handle request
		next.ServeHTTP(wrapped, r)

		// Record duration
		duration := time.Since(start).Seconds()
		collector.httpDuration.Observe(duration)

		// Record errors
		if wrapped.statusCode >= 400 {
			collector.httpErrors.Inc()
		}

		// Log slow requests
		if duration > 1.0 {
			logger.Warn("Slow request: %s %s took %.2fs", r.Method, r.URL.Path, duration)
		}
	})
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Database metrics helpers

// RecordDBQuery records a database query metric
func RecordDBQuery(duration time.Duration, err error) {
	collector := GetCollector()
	collector.dbQueries.Inc()
	collector.dbDuration.Observe(duration.Seconds())
	if err != nil {
		collector.dbErrors.Inc()
	}
}

// RecordCacheAccess records cache access metrics
func RecordCacheAccess(hit bool) {
	collector := GetCollector()
	if hit {
		collector.cacheHits.Inc()
	} else {
		collector.cacheMisses.Inc()
	}
}

// UpdateSystemMetrics updates system-level metrics
func UpdateSystemMetrics(goroutines int, memoryBytes uint64, connections int) {
	collector := GetCollector()
	collector.goroutines.Set(float64(goroutines))
	collector.memoryUsage.Set(float64(memoryBytes))
	collector.activeConnections.Set(float64(connections))
}

// Export metrics in Prometheus format

// Handler returns an HTTP handler for Prometheus metrics
func (c *Collector) Handler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4")
		c.WritePrometheus(w)
	}
}

// WritePrometheus writes metrics in Prometheus format
func (c *Collector) WritePrometheus(w http.ResponseWriter) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	// Write uptime metric
	fmt.Fprintf(w, "# HELP arxos_uptime_seconds Time since service started in seconds.\n")
	fmt.Fprintf(w, "# TYPE arxos_uptime_seconds counter\n")
	fmt.Fprintf(w, "arxos_uptime_seconds %d\n\n", int(time.Since(c.startTime).Seconds()))

	// Write all registered metrics
	for _, metric := range c.metrics {
		c.writeMetric(w, metric)
	}
}

// writeMetric writes a single metric in Prometheus format
func (c *Collector) writeMetric(w http.ResponseWriter, m *Metric) {
	// Write HELP and TYPE
	fmt.Fprintf(w, "# HELP %s %s\n", m.Name, m.Help)
	fmt.Fprintf(w, "# TYPE %s %s\n", m.Name, m.Type)

	labels := c.formatLabels(m.Labels)

	switch m.Type {
	case MetricTypeCounter, MetricTypeGauge:
		value := m.value.Load().(float64)
		fmt.Fprintf(w, "%s%s %g\n", m.Name, labels, value)

	case MetricTypeHistogram:
		if m.histogram != nil {
			m.histogram.mu.Lock()
			defer m.histogram.mu.Unlock()

			// Write bucket counts
			cumulative := uint64(0)
			for i, upper := range m.histogram.buckets {
				cumulative += m.histogram.counts[i]
				fmt.Fprintf(w, "%s_bucket{le=\"%g\"%s} %d\n",
					m.Name, upper, labels, cumulative)
			}
			// +Inf bucket
			cumulative += m.histogram.counts[len(m.histogram.counts)-1]
			fmt.Fprintf(w, "%s_bucket{le=\"+Inf\"%s} %d\n",
				m.Name, labels, cumulative)

			// Write sum and count
			fmt.Fprintf(w, "%s_sum%s %g\n", m.Name, labels, m.histogram.sum)
			fmt.Fprintf(w, "%s_count%s %d\n", m.Name, labels, m.histogram.count)
		}
	}
	fmt.Fprintln(w)
}

// formatLabels formats labels for Prometheus
func (c *Collector) formatLabels(labels map[string]string) string {
	if len(labels) == 0 {
		return ""
	}

	result := "{"
	first := true
	for k, v := range labels {
		if !first {
			result += ","
		}
		result += fmt.Sprintf(`%s="%s"`, k, v)
		first = false
	}
	result += "}"
	return result
}

// BackgroundUpdater starts a goroutine to update system metrics
func (c *Collector) BackgroundUpdater(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			c.updateSystemMetrics()
		}
	}
}

// updateSystemMetrics updates system-level metrics
func (c *Collector) updateSystemMetrics() {
	// This would be called periodically to update system metrics
	// Implementation depends on actual system monitoring needs
}

// UpdateGoroutineCount updates the current goroutine count
func (c *Collector) UpdateGoroutineCount() {
	if c.goroutines != nil {
		count := runtime.NumGoroutine()
		c.goroutines.Set(float64(count))
		logger.Debug("Updated goroutine count: %d", count)
	}
}

// GetSnapshot returns a snapshot of current metrics
func (c *Collector) GetSnapshot() map[string]interface{} {
	c.mu.RLock()
	defer c.mu.RUnlock()

	snapshot := make(map[string]interface{})

	for name, metric := range c.metrics {
		switch metric.Type {
		case MetricTypeCounter, MetricTypeGauge:
			if val := metric.value.Load(); val != nil {
				snapshot[name] = val
			}
		case MetricTypeHistogram:
			if metric.histogram != nil {
				metric.histogram.mu.Lock()
				snapshot[name] = map[string]interface{}{
					"count": metric.histogram.count,
					"sum":   metric.histogram.sum,
					"avg":   metric.histogram.sum / float64(metric.histogram.count),
				}
				metric.histogram.mu.Unlock()
			}
		}
	}

	// Add system info
	snapshot["uptime_seconds"] = time.Since(c.startTime).Seconds()
	snapshot["timestamp"] = time.Now().Unix()

	return snapshot
}

// FormatPrometheus formats metrics in Prometheus exposition format
func (c *Collector) FormatPrometheus() string {
	var buf strings.Builder
	c.mu.RLock()
	defer c.mu.RUnlock()

	// Write header
	buf.WriteString("# ArxOS Metrics\n")
	buf.WriteString(fmt.Sprintf("# Generated at %s\n\n", time.Now().Format(time.RFC3339)))

	// Write each metric
	for name, metric := range c.metrics {
		// Write HELP and TYPE comments
		buf.WriteString(fmt.Sprintf("# HELP %s %s\n", name, metric.Help))
		buf.WriteString(fmt.Sprintf("# TYPE %s %s\n", name, strings.ToLower(string(metric.Type))))

		// Write metric value
		switch metric.Type {
		case MetricTypeCounter, MetricTypeGauge:
			if val := metric.value.Load(); val != nil {
				buf.WriteString(fmt.Sprintf("%s %g\n", name, val.(float64)))
			}
		case MetricTypeHistogram:
			if metric.histogram != nil {
				metric.histogram.mu.Lock()
				// Write histogram buckets
				cumulative := uint64(0)
				for i, upper := range metric.histogram.buckets {
					cumulative += metric.histogram.counts[i]
					buf.WriteString(fmt.Sprintf("%s_bucket{le=\"%g\"} %d\n", name, upper, cumulative))
				}
				// +Inf bucket
				cumulative += metric.histogram.counts[len(metric.histogram.counts)-1]
				buf.WriteString(fmt.Sprintf("%s_bucket{le=\"+Inf\"} %d\n", name, cumulative))
				// Sum and count
				buf.WriteString(fmt.Sprintf("%s_sum %g\n", name, metric.histogram.sum))
				buf.WriteString(fmt.Sprintf("%s_count %d\n", name, metric.histogram.count))
				metric.histogram.mu.Unlock()
			}
		}
		buf.WriteString("\n")
	}

	return buf.String()
}
