package api

import (
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/api/versioning"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// metricsWriter wraps http.ResponseWriter to capture status code and response size for metrics
type metricsWriter struct {
	http.ResponseWriter
	statusCode int
	bodySize   int64
}

func (mw *metricsWriter) WriteHeader(code int) {
	mw.statusCode = code
	mw.ResponseWriter.WriteHeader(code)
}

func (mw *metricsWriter) Write(b []byte) (int, error) {
	size, err := mw.ResponseWriter.Write(b)
	mw.bodySize += int64(size)
	return size, err
}

// createBaseMiddleware creates the base middleware chain with enhancements
func (s *Server) createBaseMiddleware() http.Handler {
	var handler http.Handler = s.router

	// Add metrics middleware (if enabled)
	if s.config.Metrics.Enabled && s.metricsCollector != nil {
		handler = s.metricsMiddleware(handler)
	}

	// Add versioning middleware
	if s.versionRegistry != nil {
		versionMW := versioning.NewMiddleware(s.versionRegistry)
		handler = versionMW.ExtractVersion(handler)
	}

	return handler
}

// metricsMiddleware wraps handlers with Prometheus metrics collection
func (s *Server) metricsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Track active requests
		s.metricsCollector.IncrementActiveRequests()
		defer s.metricsCollector.DecrementActiveRequests()

		// Wrap response writer to capture status and size
		wrapped := &metricsWriter{ResponseWriter: w, statusCode: http.StatusOK}

		next.ServeHTTP(wrapped, r)

		// Record metrics
		duration := time.Since(start)
		s.metricsCollector.RecordRequest(
			r.Method,
			r.URL.Path,
			wrapped.statusCode,
			duration,
			r.ContentLength,
			wrapped.bodySize,
		)
	})
}

// handleMetrics returns the Prometheus metrics handler
func (s *Server) handleMetrics() http.Handler {
	return promhttp.Handler()
}
