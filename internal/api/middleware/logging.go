package middleware

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// LoggingMiddleware provides request/response logging
type LoggingMiddleware struct {
	excludePaths []string
}

// NewLoggingMiddleware creates a new logging middleware
func NewLoggingMiddleware(excludePaths []string) *LoggingMiddleware {
	return &LoggingMiddleware{
		excludePaths: excludePaths,
	}
}

// DefaultLoggingMiddleware creates a logging middleware with default settings
func DefaultLoggingMiddleware() *LoggingMiddleware {
	return NewLoggingMiddleware([]string{
		"/health",
		"/ready",
		"/metrics",
	})
}

// Logging middleware that logs HTTP requests and responses
func (m *LoggingMiddleware) Logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip logging for excluded paths
		if m.shouldSkipLogging(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		start := time.Now()

		// Capture request details
		requestID := r.Header.Get("X-Request-ID")
		if requestID == "" {
			requestID = generateRequestID()
		}

		// Add request ID to context
		ctx := r.Context()
		ctx = context.WithValue(ctx, "request_id", requestID)
		r = r.WithContext(ctx)

		// Log request
		logger.Info("Request started: %s %s - ID: %s - User-Agent: %s - Remote: %s",
			r.Method, r.URL.Path, requestID, r.UserAgent(), r.RemoteAddr)

		// Capture response
		responseWriter := &responseWriter{
			ResponseWriter: w,
			statusCode:     http.StatusOK,
			body:           &bytes.Buffer{},
		}

		// Process request
		next.ServeHTTP(responseWriter, r)

		// Log response
		duration := time.Since(start)
		logger.Info("Request completed: %s %s - ID: %s - Status: %d - Duration: %v - Size: %d",
			r.Method, r.URL.Path, requestID, responseWriter.statusCode, duration, responseWriter.body.Len())

		// Log slow requests
		if duration > 5*time.Second {
			logger.Warn("Slow request: %s %s - ID: %s - Duration: %v",
				r.Method, r.URL.Path, requestID, duration)
		}
	})
}

// shouldSkipLogging checks if the path should be excluded from logging
func (m *LoggingMiddleware) shouldSkipLogging(path string) bool {
	for _, excludePath := range m.excludePaths {
		if path == excludePath {
			return true
		}
	}
	return false
}

// responseWriter wraps http.ResponseWriter to capture response details
type responseWriter struct {
	http.ResponseWriter
	statusCode int
	body       *bytes.Buffer
}

// WriteHeader captures the status code
func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Write captures the response body
func (rw *responseWriter) Write(b []byte) (int, error) {
	rw.body.Write(b)
	return rw.ResponseWriter.Write(b)
}

// generateRequestID generates a unique request ID
func generateRequestID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}
