package middleware

import (
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// MetricsMiddleware provides request metrics collection
type MetricsMiddleware struct {
	requestCount    map[string]int64
	requestDuration map[string]time.Duration
	errorCount      map[string]int64
}

// NewMetricsMiddleware creates a new metrics middleware
func NewMetricsMiddleware() *MetricsMiddleware {
	return &MetricsMiddleware{
		requestCount:    make(map[string]int64),
		requestDuration: make(map[string]time.Duration),
		errorCount:      make(map[string]int64),
	}
}

// Metrics middleware that collects request metrics
func (m *MetricsMiddleware) Metrics(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create response writer wrapper
		responseWriter := &metricsResponseWriter{
			ResponseWriter: w,
			statusCode:     http.StatusOK,
		}

		// Process request
		next.ServeHTTP(responseWriter, r)

		// Calculate metrics
		duration := time.Since(start)
		path := r.URL.Path
		method := r.Method
		statusCode := responseWriter.statusCode

		// Update counters
		key := method + ":" + path
		m.requestCount[key]++
		m.requestDuration[key] += duration

		// Count errors
		if statusCode >= 400 {
			m.errorCount[key]++
		}

		// Log metrics
		logger.Info("Metrics: %s %s - Status: %d - Duration: %v - Count: %d",
			method, path, statusCode, duration, m.requestCount[key])
	})
}

// metricsResponseWriter wraps http.ResponseWriter to capture status code
type metricsResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

// WriteHeader captures the status code
func (mrw *metricsResponseWriter) WriteHeader(code int) {
	mrw.statusCode = code
	mrw.ResponseWriter.WriteHeader(code)
}

// GetMetrics returns current metrics
func (m *MetricsMiddleware) GetMetrics() map[string]interface{} {
	totalRequests := int64(0)
	totalErrors := int64(0)
	totalDuration := time.Duration(0)

	for _, count := range m.requestCount {
		totalRequests += count
	}

	for _, count := range m.errorCount {
		totalErrors += count
	}

	for _, duration := range m.requestDuration {
		totalDuration += duration
	}

	avgDuration := time.Duration(0)
	if totalRequests > 0 {
		avgDuration = totalDuration / time.Duration(totalRequests)
	}

	errorRate := float64(0)
	if totalRequests > 0 {
		errorRate = float64(totalErrors) / float64(totalRequests) * 100
	}

	return map[string]interface{}{
		"total_requests":  totalRequests,
		"total_errors":    totalErrors,
		"error_rate":      errorRate,
		"avg_duration":    avgDuration.String(),
		"endpoints":       m.requestCount,
		"error_endpoints": m.errorCount,
	}
}

// HealthCheckMiddleware provides health check functionality
type HealthCheckMiddleware struct {
	checks map[string]func() error
}

// NewHealthCheckMiddleware creates a new health check middleware
func NewHealthCheckMiddleware() *HealthCheckMiddleware {
	return &HealthCheckMiddleware{
		checks: make(map[string]func() error),
	}
}

// AddCheck adds a health check
func (hcm *HealthCheckMiddleware) AddCheck(name string, check func() error) {
	hcm.checks[name] = check
}

// HealthCheck middleware that performs health checks
func (hcm *HealthCheckMiddleware) HealthCheck(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Only perform health checks on health endpoints
		if r.URL.Path == "/health" || r.URL.Path == "/ready" {
			status := "healthy"
			details := make(map[string]string)

			for name, check := range hcm.checks {
				if err := check(); err != nil {
					status = "unhealthy"
					details[name] = err.Error()
				} else {
					details[name] = "ok"
				}
			}

			// Set response headers
			if status == "healthy" {
				w.WriteHeader(http.StatusOK)
			} else {
				w.WriteHeader(http.StatusServiceUnavailable)
			}

			// Write response
			w.Header().Set("Content-Type", "application/json")

			// Write JSON response
			w.Write([]byte(`{"status":"` + status + `","checks":{`))
			first := true
			for name, result := range details {
				if !first {
					w.Write([]byte(`,`))
				}
				w.Write([]byte(`"` + name + `":"` + result + `"`))
				first = false
			}
			w.Write([]byte(`},"time":"` + time.Now().UTC().Format(time.RFC3339) + `"}`))
			return
		}

		next.ServeHTTP(w, r)
	})
}

// DefaultHealthChecks creates default health checks
func DefaultHealthChecks() *HealthCheckMiddleware {
	hcm := NewHealthCheckMiddleware()

	// Add basic health checks
	hcm.AddCheck("database", func() error {
		// This would check database connectivity
		// For now, always return nil
		return nil
	})

	hcm.AddCheck("cache", func() error {
		// This would check cache connectivity
		// For now, always return nil
		return nil
	})

	hcm.AddCheck("auth_service", func() error {
		// This would check auth service connectivity
		// For now, always return nil
		return nil
	})

	return hcm
}
