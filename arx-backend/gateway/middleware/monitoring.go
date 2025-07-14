package middleware

import (
	"fmt"
	"net/http"
	"runtime"
	"strings"
	"sync"
	"time"

	"net/url"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.uber.org/zap"
)

// MonitoringMiddleware handles metrics collection and monitoring
type MonitoringMiddleware struct {
	config MonitoringConfig
	logger *zap.Logger

	// Prometheus metrics
	requestCounter  *prometheus.CounterVec
	requestDuration *prometheus.HistogramVec
	responseSize    *prometheus.HistogramVec
	errorCounter    *prometheus.CounterVec
	activeRequests  *prometheus.GaugeVec
	goroutines      prometheus.Gauge
	memoryUsage     prometheus.Gauge
	cpuUsage        prometheus.Gauge

	// Circuit breaker metrics
	circuitBreakerState    *prometheus.GaugeVec
	circuitBreakerFailures *prometheus.CounterVec

	// Health check metrics
	healthCheckDuration *prometheus.HistogramVec
	healthCheckStatus   *prometheus.GaugeVec

	// Custom metrics
	customMetrics map[string]prometheus.Collector
	mu            sync.RWMutex
}

// MonitoringConfig defines monitoring configuration
type MonitoringConfig struct {
	Enabled            bool                   `yaml:"enabled"`
	MetricsPort        int                    `yaml:"metrics_port"`
	MetricsPath        string                 `yaml:"metrics_path"`
	HealthCheckPath    string                 `yaml:"health_check_path"`
	LogLevel           string                 `yaml:"log_level"`
	LogFormat          string                 `yaml:"log_format"`
	RequestTracing     bool                   `yaml:"request_tracing"`
	PerformanceLogging bool                   `yaml:"performance_logging"`
	CircuitBreaker     CircuitBreakerConfig   `yaml:"circuit_breaker"`
	HealthMonitoring   HealthMonitoringConfig `yaml:"health_monitoring"`
	Alerting           AlertingConfig         `yaml:"alerting"`
}

// CircuitBreakerConfig defines circuit breaker configuration
type CircuitBreakerConfig struct {
	Enabled          bool          `yaml:"enabled"`
	FailureThreshold int           `yaml:"failure_threshold"`
	Timeout          time.Duration `yaml:"timeout"`
	ResetTimeout     time.Duration `yaml:"reset_timeout"`
	MonitorInterval  time.Duration `yaml:"monitor_interval"`
}

// HealthMonitoringConfig defines health monitoring configuration
type HealthMonitoringConfig struct {
	Enabled          bool          `yaml:"enabled"`
	CheckInterval    time.Duration `yaml:"check_interval"`
	Timeout          time.Duration `yaml:"timeout"`
	FailureThreshold int           `yaml:"failure_threshold"`
	SuccessThreshold int           `yaml:"success_threshold"`
	Services         []string      `yaml:"services"`
}

// AlertingConfig defines alerting configuration
type AlertingConfig struct {
	Enabled          bool          `yaml:"enabled"`
	AlertEndpoint    string        `yaml:"alert_endpoint"`
	AlertToken       string        `yaml:"alert_token"`
	ErrorThreshold   float64       `yaml:"error_threshold"`
	LatencyThreshold time.Duration `yaml:"latency_threshold"`
	AlertChannels    []string      `yaml:"alert_channels"`
}

// RequestTrace represents a request trace
type RequestTrace struct {
	TraceID      string                 `json:"trace_id"`
	SpanID       string                 `json:"span_id"`
	ParentSpanID string                 `json:"parent_span_id,omitempty"`
	StartTime    time.Time              `json:"start_time"`
	EndTime      time.Time              `json:"end_time"`
	Duration     time.Duration          `json:"duration"`
	Method       string                 `json:"method"`
	Path         string                 `json:"path"`
	StatusCode   int                    `json:"status_code"`
	UserID       string                 `json:"user_id,omitempty"`
	Service      string                 `json:"service,omitempty"`
	Headers      map[string]string      `json:"headers,omitempty"`
	QueryParams  map[string]string      `json:"query_params,omitempty"`
	RequestBody  string                 `json:"request_body,omitempty"`
	ResponseBody string                 `json:"response_body,omitempty"`
	Error        string                 `json:"error,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// HealthStatus represents service health status
type HealthStatus struct {
	Service      string                 `json:"service"`
	Status       string                 `json:"status"`
	LastCheck    time.Time              `json:"last_check"`
	ResponseTime time.Duration          `json:"response_time"`
	Error        string                 `json:"error,omitempty"`
	Details      map[string]interface{} `json:"details,omitempty"`
}

// NewMonitoringMiddleware creates a new monitoring middleware
func NewMonitoringMiddleware(config MonitoringConfig) (*MonitoringMiddleware, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	middleware := &MonitoringMiddleware{
		config:        config,
		logger:        logger,
		customMetrics: make(map[string]prometheus.Collector),
	}

	// Initialize Prometheus metrics
	middleware.initializeMetrics()

	return middleware, nil
}

// initializeMetrics initializes Prometheus metrics
func (mm *MonitoringMiddleware) initializeMetrics() {
	// Request metrics
	mm.requestCounter = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_requests_total",
			Help: "Total number of requests",
		},
		[]string{"method", "path", "status_code", "service"},
	)

	mm.requestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_request_duration_seconds",
			Help:    "Request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "path", "service"},
	)

	mm.responseSize = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_response_size_bytes",
			Help:    "Response size in bytes",
			Buckets: prometheus.ExponentialBuckets(100, 10, 8),
		},
		[]string{"method", "path", "service"},
	)

	mm.errorCounter = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_errors_total",
			Help: "Total number of errors",
		},
		[]string{"method", "path", "error_type", "service"},
	)

	mm.activeRequests = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_active_requests",
			Help: "Number of active requests",
		},
		[]string{"method", "path", "service"},
	)

	// System metrics
	mm.goroutines = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "gateway_goroutines",
			Help: "Number of goroutines",
		},
	)

	mm.memoryUsage = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "gateway_memory_bytes",
			Help: "Memory usage in bytes",
		},
	)

	mm.cpuUsage = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "gateway_cpu_usage_percent",
			Help: "CPU usage percentage",
		},
	)

	// Circuit breaker metrics
	mm.circuitBreakerState = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_circuit_breaker_state",
			Help: "Circuit breaker state (0=closed, 1=half-open, 2=open)",
		},
		[]string{"service"},
	)

	mm.circuitBreakerFailures = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_circuit_breaker_failures_total",
			Help: "Total circuit breaker failures",
		},
		[]string{"service"},
	)

	// Health check metrics
	mm.healthCheckDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_health_check_duration_seconds",
			Help:    "Health check duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"service"},
	)

	mm.healthCheckStatus = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_health_check_status",
			Help: "Health check status (0=unhealthy, 1=healthy)",
		},
		[]string{"service"},
	)
}

// Middleware returns the monitoring middleware function
func (mm *MonitoringMiddleware) Middleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if !mm.config.Enabled {
				next.ServeHTTP(w, r)
				return
			}

			start := time.Now()

			// Create request trace
			trace := mm.createRequestTrace(r)

			// Increment active requests
			mm.activeRequests.WithLabelValues(r.Method, r.URL.Path, mm.getServiceName(r)).Inc()
			defer mm.activeRequests.WithLabelValues(r.Method, r.URL.Path, mm.getServiceName(r)).Dec()

			// Create response writer wrapper
			responseWriter := &monitoringResponseWriter{
				ResponseWriter: w,
				statusCode:     http.StatusOK,
				body:           make([]byte, 0),
			}

			// Process request
			next.ServeHTTP(responseWriter, r)

			// Complete trace
			mm.completeRequestTrace(trace, responseWriter, time.Since(start))

			// Update metrics
			mm.updateMetrics(trace)

			// Log performance if enabled
			if mm.config.PerformanceLogging {
				mm.logPerformance(trace)
			}

			// Check for alerts
			mm.checkAlerts(trace)
		})
	}
}

// createRequestTrace creates a request trace
func (mm *MonitoringMiddleware) createRequestTrace(r *http.Request) *RequestTrace {
	trace := &RequestTrace{
		TraceID:     mm.generateTraceID(),
		SpanID:      mm.generateSpanID(),
		StartTime:   time.Now(),
		Method:      r.Method,
		Path:        r.URL.Path,
		Headers:     mm.sanitizeHeaders(r.Header),
		QueryParams: mm.extractQueryParams(r.URL.RawQuery),
		Service:     mm.getServiceName(r),
	}

	// Add user information if available
	if user, ok := GetUserFromContext(r.Context()); ok {
		trace.UserID = user.UserID
	}

	// Add request body if tracing is enabled
	if mm.config.RequestTracing {
		trace.RequestBody = mm.extractRequestBody(r)
	}

	return trace
}

// completeRequestTrace completes the request trace
func (mm *MonitoringMiddleware) completeRequestTrace(trace *RequestTrace, w *monitoringResponseWriter, duration time.Duration) {
	trace.EndTime = time.Now()
	trace.Duration = duration
	trace.StatusCode = w.statusCode

	if mm.config.RequestTracing {
		trace.ResponseBody = string(w.body)
	}

	if trace.StatusCode >= 400 {
		trace.Error = http.StatusText(trace.StatusCode)
	}
}

// updateMetrics updates Prometheus metrics
func (mm *MonitoringMiddleware) updateMetrics(trace *RequestTrace) {
	labels := prometheus.Labels{
		"method":      trace.Method,
		"path":        trace.Path,
		"status_code": fmt.Sprintf("%d", trace.StatusCode),
		"service":     trace.Service,
	}

	// Update request counter
	mm.requestCounter.With(labels).Inc()

	// Update request duration
	mm.requestDuration.With(prometheus.Labels{
		"method":  trace.Method,
		"path":    trace.Path,
		"service": trace.Service,
	}).Observe(trace.Duration.Seconds())

	// Update response size
	mm.responseSize.With(prometheus.Labels{
		"method":  trace.Method,
		"path":    trace.Path,
		"service": trace.Service,
	}).Observe(float64(len(trace.ResponseBody)))

	// Update error counter if there's an error
	if trace.Error != "" {
		mm.errorCounter.With(prometheus.Labels{
			"method":     trace.Method,
			"path":       trace.Path,
			"error_type": trace.Error,
			"service":    trace.Service,
		}).Inc()
	}

	// Update system metrics
	mm.updateSystemMetrics()
}

// updateSystemMetrics updates system-level metrics
func (mm *MonitoringMiddleware) updateSystemMetrics() {
	// Update goroutine count
	mm.goroutines.Set(float64(runtime.NumGoroutine()))

	// Update memory usage
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	mm.memoryUsage.Set(float64(m.Alloc))

	// CPU usage would require more complex implementation
	// For now, we'll set a placeholder value
	mm.cpuUsage.Set(0.0)
}

// logPerformance logs performance information
func (mm *MonitoringMiddleware) logPerformance(trace *RequestTrace) {
	mm.logger.Info("Request performance",
		zap.String("trace_id", trace.TraceID),
		zap.String("method", trace.Method),
		zap.String("path", trace.Path),
		zap.Int("status_code", trace.StatusCode),
		zap.Duration("duration", trace.Duration),
		zap.String("service", trace.Service),
		zap.String("user_id", trace.UserID),
		zap.String("error", trace.Error),
	)
}

// checkAlerts checks for alert conditions
func (mm *MonitoringMiddleware) checkAlerts(trace *RequestTrace) {
	if !mm.config.Alerting.Enabled {
		return
	}

	// Check error rate
	if trace.StatusCode >= 500 {
		mm.sendAlert("high_error_rate", fmt.Sprintf("High error rate for %s: %d", trace.Path, trace.StatusCode))
	}

	// Check latency threshold
	if trace.Duration > mm.config.Alerting.LatencyThreshold {
		mm.sendAlert("high_latency", fmt.Sprintf("High latency for %s: %v", trace.Path, trace.Duration))
	}
}

// sendAlert sends an alert
func (mm *MonitoringMiddleware) sendAlert(alertType, message string) {
	mm.logger.Warn("Alert triggered",
		zap.String("alert_type", alertType),
		zap.String("message", message),
	)

	// In a real implementation, you would send this to your alerting system
	// For now, we'll just log it
}

// generateTraceID generates a unique trace ID
func (mm *MonitoringMiddleware) generateTraceID() string {
	return fmt.Sprintf("trace_%d_%s", time.Now().UnixNano(), mm.generateRandomString(8))
}

// generateSpanID generates a unique span ID
func (mm *MonitoringMiddleware) generateSpanID() string {
	return fmt.Sprintf("span_%d_%s", time.Now().UnixNano(), mm.generateRandomString(8))
}

// generateRandomString generates a random string
func (mm *MonitoringMiddleware) generateRandomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// sanitizeHeaders sanitizes headers for logging
func (mm *MonitoringMiddleware) sanitizeHeaders(headers http.Header) map[string]string {
	sanitized := make(map[string]string)

	for key, values := range headers {
		// Skip sensitive headers
		if mm.isSensitiveHeader(key) {
			sanitized[key] = "[REDACTED]"
			continue
		}

		if len(values) > 0 {
			sanitized[key] = values[0]
		}
	}

	return sanitized
}

// isSensitiveHeader checks if a header is sensitive
func (mm *MonitoringMiddleware) isSensitiveHeader(header string) bool {
	sensitiveHeaders := []string{"authorization", "cookie", "x-api-key", "x-oauth2-token"}
	for _, sensitiveHeader := range sensitiveHeaders {
		if strings.EqualFold(header, sensitiveHeader) {
			return true
		}
	}
	return false
}

// extractQueryParams extracts query parameters
func (mm *MonitoringMiddleware) extractQueryParams(rawQuery string) map[string]string {
	params := make(map[string]string)
	if rawQuery == "" {
		return params
	}

	values, err := url.ParseQuery(rawQuery)
	if err != nil {
		return params
	}

	for key, values := range values {
		if len(values) > 0 {
			params[key] = values[0]
		}
	}

	return params
}

// extractRequestBody extracts request body
func (mm *MonitoringMiddleware) extractRequestBody(r *http.Request) string {
	if r.Body == nil {
		return ""
	}

	// Limit body size for logging
	maxSize := int64(1024) // 1KB
	if r.ContentLength > maxSize {
		return "[BODY TOO LARGE]"
	}

	// Read body (simplified implementation)
	return "[BODY CONTENT]"
}

// getServiceName gets the service name from the request
func (mm *MonitoringMiddleware) getServiceName(r *http.Request) string {
	// Extract service name from path
	// This is a simplified implementation
	path := r.URL.Path
	if strings.HasPrefix(path, "/api/v1/svg") {
		return "svg-parser"
	} else if strings.HasPrefix(path, "/api/v1/cmms") {
		return "cmms-service"
	} else if strings.HasPrefix(path, "/api/v1/database") {
		return "database-infra"
	} else if strings.HasPrefix(path, "/api/v1/auth") {
		return "arx-backend"
	}
	return "unknown"
}

// monitoringResponseWriter wraps http.ResponseWriter to capture response details
type monitoringResponseWriter struct {
	http.ResponseWriter
	statusCode int
	body       []byte
}

func (mw *monitoringResponseWriter) WriteHeader(code int) {
	mw.statusCode = code
	mw.ResponseWriter.WriteHeader(code)
}

func (mw *monitoringResponseWriter) Write(data []byte) (int, error) {
	mw.body = append(mw.body, data...)
	return mw.ResponseWriter.Write(data)
}

// UpdateConfig updates the monitoring configuration
func (mm *MonitoringMiddleware) UpdateConfig(config MonitoringConfig) error {
	mm.config = config
	mm.logger.Info("Monitoring configuration updated")
	return nil
}

// GetMonitoringStats returns monitoring statistics
func (mm *MonitoringMiddleware) GetMonitoringStats() map[string]interface{} {
	return map[string]interface{}{
		"enabled":             mm.config.Enabled,
		"metrics_port":        mm.config.MetricsPort,
		"request_tracing":     mm.config.RequestTracing,
		"performance_logging": mm.config.PerformanceLogging,
		"circuit_breaker":     mm.config.CircuitBreaker.Enabled,
		"health_monitoring":   mm.config.HealthMonitoring.Enabled,
		"alerting":            mm.config.Alerting.Enabled,
	}
}
