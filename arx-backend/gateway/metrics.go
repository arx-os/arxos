package gateway

import (
	"fmt"
	"net/http"
	"runtime"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.uber.org/zap"
)

// MetricsCollector handles metrics collection and Prometheus integration
type MetricsCollector struct {
	config MetricsConfig
	logger *zap.Logger

	// Core metrics
	requestCounter  *prometheus.CounterVec
	requestDuration *prometheus.HistogramVec
	responseSize    *prometheus.HistogramVec
	errorCounter    *prometheus.CounterVec
	activeRequests  *prometheus.GaugeVec

	// System metrics
	goroutines  prometheus.Gauge
	memoryUsage prometheus.Gauge
	cpuUsage    prometheus.Gauge
	uptime      prometheus.Gauge

	// Gateway-specific metrics
	gatewayRequestsTotal *prometheus.CounterVec
	gatewayLatency       *prometheus.HistogramVec
	gatewayErrors        *prometheus.CounterVec
	gatewayThroughput    *prometheus.GaugeVec

	// Service metrics
	serviceRequestsTotal *prometheus.CounterVec
	serviceLatency       *prometheus.HistogramVec
	serviceErrors        *prometheus.CounterVec
	serviceAvailability  *prometheus.GaugeVec

	// Authentication metrics
	authSuccessCounter *prometheus.CounterVec
	authFailureCounter *prometheus.CounterVec
	authLatency        *prometheus.HistogramVec

	// Rate limiting metrics
	rateLimitExceeded  *prometheus.CounterVec
	rateLimitRemaining *prometheus.GaugeVec

	// Custom metrics
	customMetrics map[string]prometheus.Collector
	mu            sync.RWMutex

	// Start time for uptime calculation
	startTime time.Time
}

// MetricsConfig defines metrics configuration
type MetricsConfig struct {
	Enabled              bool      `yaml:"enabled"`
	Port                 int       `yaml:"port"`
	Path                 string    `yaml:"path"`
	CollectSystemMetrics bool      `yaml:"collect_system_metrics"`
	CollectCustomMetrics bool      `yaml:"collect_custom_metrics"`
	HistogramBuckets     []float64 `yaml:"histogram_buckets"`
	EnableGoMetrics      bool      `yaml:"enable_go_metrics"`
	EnableProcessMetrics bool      `yaml:"enable_process_metrics"`
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector(config MetricsConfig) (*MetricsCollector, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	collector := &MetricsCollector{
		config:        config,
		logger:        logger,
		customMetrics: make(map[string]prometheus.Collector),
		startTime:     time.Now(),
	}

	// Initialize metrics
	collector.initializeMetrics()

	// Start metrics server if enabled
	if config.Enabled {
		go collector.startMetricsServer()
	}

	return collector, nil
}

// initializeMetrics initializes all Prometheus metrics
func (mc *MetricsCollector) initializeMetrics() {
	// Core request metrics
	mc.requestCounter = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_requests_total",
			Help: "Total number of requests",
		},
		[]string{"method", "path", "status_code", "service"},
	)

	mc.requestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_request_duration_seconds",
			Help:    "Request duration in seconds",
			Buckets: mc.getHistogramBuckets(),
		},
		[]string{"method", "path", "service"},
	)

	mc.responseSize = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_response_size_bytes",
			Help:    "Response size in bytes",
			Buckets: prometheus.ExponentialBuckets(100, 10, 8),
		},
		[]string{"method", "path", "service"},
	)

	mc.errorCounter = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_errors_total",
			Help: "Total number of errors",
		},
		[]string{"method", "path", "error_type", "service"},
	)

	mc.activeRequests = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_active_requests",
			Help: "Number of active requests",
		},
		[]string{"method", "path", "service"},
	)

	// System metrics
	if mc.config.CollectSystemMetrics {
		mc.goroutines = promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "gateway_goroutines",
				Help: "Number of goroutines",
			},
		)

		mc.memoryUsage = promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "gateway_memory_bytes",
				Help: "Memory usage in bytes",
			},
		)

		mc.cpuUsage = promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "gateway_cpu_usage_percent",
				Help: "CPU usage percentage",
			},
		)

		mc.uptime = promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "gateway_uptime_seconds",
				Help: "Gateway uptime in seconds",
			},
		)
	}

	// Gateway-specific metrics
	mc.gatewayRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_total_requests",
			Help: "Total requests processed by gateway",
		},
		[]string{"gateway_instance"},
	)

	mc.gatewayLatency = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_latency_seconds",
			Help:    "Gateway processing latency",
			Buckets: mc.getHistogramBuckets(),
		},
		[]string{"gateway_instance"},
	)

	mc.gatewayErrors = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_errors",
			Help: "Gateway errors",
		},
		[]string{"gateway_instance", "error_type"},
	)

	mc.gatewayThroughput = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_throughput_requests_per_second",
			Help: "Gateway throughput in requests per second",
		},
		[]string{"gateway_instance"},
	)

	// Service metrics
	mc.serviceRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_service_requests_total",
			Help: "Total requests to each service",
		},
		[]string{"service", "method", "status_code"},
	)

	mc.serviceLatency = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_service_latency_seconds",
			Help:    "Service response latency",
			Buckets: mc.getHistogramBuckets(),
		},
		[]string{"service"},
	)

	mc.serviceErrors = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_service_errors_total",
			Help: "Total errors from each service",
		},
		[]string{"service", "error_type"},
	)

	mc.serviceAvailability = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_service_availability",
			Help: "Service availability (0=unavailable, 1=available)",
		},
		[]string{"service"},
	)

	// Authentication metrics
	mc.authSuccessCounter = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_auth_success_total",
			Help: "Total successful authentications",
		},
		[]string{"auth_method", "user_id"},
	)

	mc.authFailureCounter = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_auth_failure_total",
			Help: "Total authentication failures",
		},
		[]string{"auth_method", "error_type"},
	)

	mc.authLatency = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_auth_latency_seconds",
			Help:    "Authentication latency",
			Buckets: mc.getHistogramBuckets(),
		},
		[]string{"auth_method"},
	)

	// Rate limiting metrics
	mc.rateLimitExceeded = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_rate_limit_exceeded_total",
			Help: "Total rate limit violations",
		},
		[]string{"user_id", "service", "limit_type"},
	)

	mc.rateLimitRemaining = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_rate_limit_remaining",
			Help: "Remaining rate limit quota",
		},
		[]string{"user_id", "service", "limit_type"},
	)
}

// getHistogramBuckets returns histogram buckets for metrics
func (mc *MetricsCollector) getHistogramBuckets() []float64 {
	if len(mc.config.HistogramBuckets) > 0 {
		return mc.config.HistogramBuckets
	}
	return prometheus.DefBuckets
}

// startMetricsServer starts the Prometheus metrics server
func (mc *MetricsCollector) startMetricsServer() {
	http.Handle(mc.config.Path, promhttp.Handler())

	addr := fmt.Sprintf(":%d", mc.config.Port)
	mc.logger.Info("Starting metrics server",
		zap.String("address", addr),
		zap.String("path", mc.config.Path),
	)

	if err := http.ListenAndServe(addr, nil); err != nil {
		mc.logger.Error("Failed to start metrics server", zap.Error(err))
	}
}

// RecordRequest records a request metric
func (mc *MetricsCollector) RecordRequest(method, path, service string, statusCode int, duration time.Duration, responseSize int64) {
	labels := prometheus.Labels{
		"method":      method,
		"path":        path,
		"status_code": fmt.Sprintf("%d", statusCode),
		"service":     service,
	}

	// Record request counter
	mc.requestCounter.With(labels).Inc()

	// Record request duration
	mc.requestDuration.With(prometheus.Labels{
		"method":  method,
		"path":    path,
		"service": service,
	}).Observe(duration.Seconds())

	// Record response size
	mc.responseSize.With(prometheus.Labels{
		"method":  method,
		"path":    path,
		"service": service,
	}).Observe(float64(responseSize))

	// Record gateway metrics
	mc.gatewayRequestsTotal.WithLabelValues("gateway-1").Inc()
	mc.gatewayLatency.WithLabelValues("gateway-1").Observe(duration.Seconds())

	// Record service metrics
	mc.serviceRequestsTotal.WithLabelValues(service, method, fmt.Sprintf("%d", statusCode)).Inc()
	mc.serviceLatency.WithLabelValues(service).Observe(duration.Seconds())

	// Record error if status code indicates error
	if statusCode >= 400 {
		mc.errorCounter.With(prometheus.Labels{
			"method":     method,
			"path":       path,
			"error_type": fmt.Sprintf("http_%d", statusCode),
			"service":    service,
		}).Inc()

		mc.gatewayErrors.WithLabelValues("gateway-1", "http_error").Inc()
		mc.serviceErrors.WithLabelValues(service, "http_error").Inc()
	}
}

// RecordAuthentication records authentication metrics
func (mc *MetricsCollector) RecordAuthentication(authMethod, userID string, success bool, duration time.Duration, errorType string) {
	if success {
		mc.authSuccessCounter.WithLabelValues(authMethod, userID).Inc()
	} else {
		mc.authFailureCounter.WithLabelValues(authMethod, errorType).Inc()
	}

	mc.authLatency.WithLabelValues(authMethod).Observe(duration.Seconds())
}

// RecordRateLimit records rate limiting metrics
func (mc *MetricsCollector) RecordRateLimit(userID, service, limitType string, exceeded bool, remaining int) {
	if exceeded {
		mc.rateLimitExceeded.WithLabelValues(userID, service, limitType).Inc()
	}

	mc.rateLimitRemaining.WithLabelValues(userID, service, limitType).Set(float64(remaining))
}

// UpdateSystemMetrics updates system-level metrics
func (mc *MetricsCollector) UpdateSystemMetrics() {
	if !mc.config.CollectSystemMetrics {
		return
	}

	// Update goroutine count
	mc.goroutines.Set(float64(runtime.NumGoroutine()))

	// Update memory usage
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	mc.memoryUsage.Set(float64(m.Alloc))

	// Update uptime
	mc.uptime.Set(time.Since(mc.startTime).Seconds())

	// CPU usage would require more complex implementation
	// For now, we'll set a placeholder value
	mc.cpuUsage.Set(0.0)
}

// SetServiceAvailability sets the availability status of a service
func (mc *MetricsCollector) SetServiceAvailability(service string, available bool) {
	var value float64
	if available {
		value = 1.0
	}
	mc.serviceAvailability.WithLabelValues(service).Set(value)
}

// AddCustomMetric adds a custom metric
func (mc *MetricsCollector) AddCustomMetric(name string, metric prometheus.Collector) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	if _, exists := mc.customMetrics[name]; exists {
		return fmt.Errorf("custom metric %s already exists", name)
	}

	mc.customMetrics[name] = metric
	prometheus.MustRegister(metric)

	mc.logger.Info("Custom metric added",
		zap.String("name", name),
	)

	return nil
}

// RemoveCustomMetric removes a custom metric
func (mc *MetricsCollector) RemoveCustomMetric(name string) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	metric, exists := mc.customMetrics[name]
	if !exists {
		return fmt.Errorf("custom metric %s does not exist", name)
	}

	prometheus.Unregister(metric)
	delete(mc.customMetrics, name)

	mc.logger.Info("Custom metric removed",
		zap.String("name", name),
	)

	return nil
}

// GetMetricsStats returns metrics statistics
func (mc *MetricsCollector) GetMetricsStats() map[string]interface{} {
	return map[string]interface{}{
		"enabled":                mc.config.Enabled,
		"port":                   mc.config.Port,
		"path":                   mc.config.Path,
		"collect_system_metrics": mc.config.CollectSystemMetrics,
		"collect_custom_metrics": mc.config.CollectCustomMetrics,
		"custom_metrics_count":   len(mc.customMetrics),
		"uptime_seconds":         time.Since(mc.startTime).Seconds(),
	}
}

// UpdateConfig updates the metrics configuration
func (mc *MetricsCollector) UpdateConfig(config MetricsConfig) error {
	mc.config = config
	mc.logger.Info("Metrics configuration updated")
	return nil
}
