package monitoring

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Dashboard provides a monitoring dashboard API
type Dashboard struct {
	metricsCollector *MetricsCollector
	healthMonitor    *HealthMonitor
	alertManager     *AlertManager
	tracer           *Tracer
}

// NewDashboard creates a new monitoring dashboard
func NewDashboard(metricsCollector *MetricsCollector, healthMonitor *HealthMonitor, alertManager *AlertManager, tracer *Tracer) *Dashboard {
	return &Dashboard{
		metricsCollector: metricsCollector,
		healthMonitor:    healthMonitor,
		alertManager:     alertManager,
		tracer:           tracer,
	}
}

// DashboardData represents the complete dashboard data
type DashboardData struct {
	Timestamp  time.Time              `json:"timestamp"`
	Health     HealthStatus           `json:"health"`
	Metrics    map[string]interface{} `json:"metrics"`
	Alerts     map[string]*Alert      `json:"alerts"`
	Traces     map[string]*Trace      `json:"traces"`
	SystemInfo map[string]interface{} `json:"system_info"`
}

// ServeHTTP implements http.Handler for the dashboard
func (d *Dashboard) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch r.URL.Path {
	case "/health":
		d.handleHealth(w, r)
	case "/metrics":
		d.handleMetrics(w, r)
	case "/alerts":
		d.handleAlerts(w, r)
	case "/traces":
		d.handleTraces(w, r)
	case "/dashboard":
		d.handleDashboard(w, r)
	case "/prometheus":
		d.handlePrometheus(w, r)
	default:
		http.NotFound(w, r)
	}
}

// handleHealth handles health check requests
func (d *Dashboard) handleHealth(w http.ResponseWriter, r *http.Request) {
	// Perform health checks
	statuses := d.healthMonitor.CheckHealth(r.Context())
	overallHealth := d.healthMonitor.GetOverallHealth()

	response := map[string]interface{}{
		"overall":    overallHealth,
		"components": statuses,
		"timestamp":  time.Now(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handleMetrics handles metrics requests
func (d *Dashboard) handleMetrics(w http.ResponseWriter, r *http.Request) {
	metrics := d.metricsCollector.GetAllMetrics()
	summary := d.metricsCollector.GetMetricsSummary()

	response := map[string]interface{}{
		"metrics":   metrics,
		"summary":   summary,
		"timestamp": time.Now(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handleAlerts handles alerts requests
func (d *Dashboard) handleAlerts(w http.ResponseWriter, r *http.Request) {
	alerts := d.alertManager.GetAllAlerts()
	activeAlerts := d.alertManager.GetActiveAlerts()
	rules := d.alertManager.GetAlertRules()

	response := map[string]interface{}{
		"alerts":        alerts,
		"active_alerts": activeAlerts,
		"rules":         rules,
		"timestamp":     time.Now(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handleTraces handles traces requests
func (d *Dashboard) handleTraces(w http.ResponseWriter, r *http.Request) {
	traces := d.tracer.GetAllTraces()

	response := map[string]interface{}{
		"traces":    traces,
		"timestamp": time.Now(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handleDashboard handles dashboard requests
func (d *Dashboard) handleDashboard(w http.ResponseWriter, r *http.Request) {
	// Gather all dashboard data
	dashboardData := DashboardData{
		Timestamp: time.Now(),
		Health:    d.healthMonitor.GetOverallHealth(),
		Metrics:   d.metricsCollector.GetAllMetrics(),
		Alerts:    d.alertManager.GetActiveAlerts(),
		Traces:    d.tracer.GetAllTraces(),
		SystemInfo: map[string]interface{}{
			"uptime":      "1h30m",
			"version":     "1.0.0",
			"environment": "development",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(dashboardData)
}

// handlePrometheus handles Prometheus metrics export
func (d *Dashboard) handlePrometheus(w http.ResponseWriter, r *http.Request) {
	metrics := d.metricsCollector.ExportMetrics()

	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(metrics))
}

// StartDashboard starts the monitoring dashboard server
func (d *Dashboard) StartDashboard(ctx context.Context, addr string) error {
	mux := http.NewServeMux()
	mux.Handle("/", d)

	server := &http.Server{
		Addr:    addr,
		Handler: mux,
	}

	logger.Info("Starting monitoring dashboard on %s", addr)

	go func() {
		<-ctx.Done()
		logger.Info("Shutting down monitoring dashboard")
		server.Shutdown(context.Background())
	}()

	return server.ListenAndServe()
}

// MonitoringMiddleware provides middleware for request monitoring
type MonitoringMiddleware struct {
	metricsCollector *MetricsCollector
	tracer           *Tracer
}

// NewMonitoringMiddleware creates a new monitoring middleware
func NewMonitoringMiddleware(metricsCollector *MetricsCollector, tracer *Tracer) *MonitoringMiddleware {
	return &MonitoringMiddleware{
		metricsCollector: metricsCollector,
		tracer:           tracer,
	}
}

// Middleware returns the middleware function
func (mm *MonitoringMiddleware) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create trace context
		traceID := fmt.Sprintf("trace_%d", time.Now().UnixNano())
		spanID := fmt.Sprintf("span_%d", time.Now().UnixNano())

		ctx := WithTraceContext(r.Context(), traceID, spanID)
		r = r.WithContext(ctx)

		// Start span
		mm.tracer.StartSpan(traceID, spanID, fmt.Sprintf("%s %s", r.Method, r.URL.Path), "", map[string]string{
			"method":      r.Method,
			"path":        r.URL.Path,
			"remote_addr": r.RemoteAddr,
		})

		// Wrap response writer to capture status code
		wrapped := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		// Call next handler
		next.ServeHTTP(wrapped, r)

		// Record metrics
		duration := time.Since(start)
		mm.metricsCollector.RecordTimer("http_request_duration", duration, map[string]string{
			"method": r.Method,
			"path":   r.URL.Path,
			"status": fmt.Sprintf("%d", wrapped.statusCode),
		})

		mm.metricsCollector.IncrementCounter("http_requests_total", map[string]string{
			"method": r.Method,
			"path":   r.URL.Path,
			"status": fmt.Sprintf("%d", wrapped.statusCode),
		})

		// End span
		var err error
		if wrapped.statusCode >= 400 {
			err = fmt.Errorf("HTTP %d", wrapped.statusCode)
		}
		mm.tracer.EndSpan(spanID, err)
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

// SetupDefaultMonitoring sets up default monitoring configuration
func SetupDefaultMonitoring() (*MetricsCollector, *HealthMonitor, *AlertManager, *Tracer) {
	// Create monitoring components
	metricsCollector := NewMetricsCollector()
	healthMonitor := NewHealthMonitor(30*time.Second, 5*time.Second)
	alertManager := NewAlertManager(30 * time.Second)
	tracer := NewTracer()

	// Add default alert rules
	alertManager.AddAlertRule(&AlertRule{
		ID:          "high_error_rate",
		Name:        "High Error Rate",
		Description: "Error rate is above 5%",
		Level:       AlertLevelWarning,
		Condition:   "error_rate > 0.05",
		Duration:    5 * time.Minute,
		Labels:      map[string]string{"service": "api"},
		Annotations: map[string]string{"summary": "High error rate detected"},
		Enabled:     true,
	})

	alertManager.AddAlertRule(&AlertRule{
		ID:          "high_response_time",
		Name:        "High Response Time",
		Description: "Response time is above 1 second",
		Level:       AlertLevelWarning,
		Condition:   "response_time > 1.0",
		Duration:    2 * time.Minute,
		Labels:      map[string]string{"service": "api"},
		Annotations: map[string]string{"summary": "High response time detected"},
		Enabled:     true,
	})

	alertManager.AddAlertRule(&AlertRule{
		ID:          "service_down",
		Name:        "Service Down",
		Description: "Service is not responding",
		Level:       AlertLevelCritical,
		Condition:   "health_status == 'unhealthy'",
		Duration:    1 * time.Minute,
		Labels:      map[string]string{"service": "all"},
		Annotations: map[string]string{"summary": "Service is down"},
		Enabled:     true,
	})

	logger.Info("Default monitoring setup completed")
	return metricsCollector, healthMonitor, alertManager, tracer
}
