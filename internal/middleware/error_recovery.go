package middleware

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"runtime"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/errors"
)

// ErrorRecoveryMiddleware provides comprehensive error recovery
type ErrorRecoveryMiddleware struct {
	includeStackTrace bool
	errorTracker      *errors.ServiceErrorTracker
}

// NewErrorRecoveryMiddleware creates a new error recovery middleware
func NewErrorRecoveryMiddleware(includeStackTrace bool) *ErrorRecoveryMiddleware {
	return &ErrorRecoveryMiddleware{
		includeStackTrace: includeStackTrace,
		errorTracker:      errors.NewServiceErrorTracker(),
	}
}

// Handler returns the middleware handler
func (m *ErrorRecoveryMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if recovered := recover(); recovered != nil {
				m.handlePanic(w, r, recovered)
			}
		}()

		// Create error-aware response writer
		writer := &errorAwareResponseWriter{
			ResponseWriter: w,
			middleware:     m,
			request:        r,
		}

		next.ServeHTTP(writer, r)
	})
}

// handlePanic handles panics and converts them to structured errors
func (m *ErrorRecoveryMiddleware) handlePanic(w http.ResponseWriter, r *http.Request, recovered interface{}) {
	// Create error from panic
	err := fmt.Errorf("panic recovered: %v", recovered)

	// Track error
	m.errorTracker.TrackError("middleware", "panic_recovery", err)

	// Log panic details
	logger.Error("Panic in request %s %s: %v", r.Method, r.URL.Path, recovered)

	// Get stack trace
	stackTrace := m.getStackTrace()

	// Create structured error response
	response := m.createErrorResponse(r, errors.New(errors.CodeInternal, "internal server error"), stackTrace)

	// Write response
	m.writeErrorResponse(w, response)
}

// errorAwareResponseWriter wraps http.ResponseWriter to handle errors
type errorAwareResponseWriter struct {
	http.ResponseWriter
	middleware *ErrorRecoveryMiddleware
	request    *http.Request
	statusCode int
	written    bool
}

// WriteHeader captures the status code
func (w *errorAwareResponseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
	w.written = true
}

// Write captures write operations
func (w *errorAwareResponseWriter) Write(data []byte) (int, error) {
	if !w.written {
		w.WriteHeader(http.StatusOK)
	}
	return w.ResponseWriter.Write(data)
}

// createErrorResponse creates a structured error response
func (m *ErrorRecoveryMiddleware) createErrorResponse(r *http.Request, err error, stackTrace string) *ErrorResponse {
	// Extract error information
	code := errors.GetCode(err)
	message := err.Error()
	details := ""
	context := make(map[string]interface{})

	// Handle different error types
	if appErr, ok := err.(*errors.AppError); ok {
		message = appErr.Message
		details = appErr.Details
		context = appErr.Context
	}

	if serviceErr := errors.GetServiceError(err); serviceErr != nil {
		context["service"] = serviceErr.Service
		context["operation"] = serviceErr.Operation
		if serviceErr.ResourceID != "" {
			context["resource_id"] = serviceErr.ResourceID
		}
	}

	// Add stack trace if enabled
	if m.includeStackTrace && stackTrace != "" {
		context["stack_trace"] = stackTrace
	}

	// Add request context
	context["method"] = r.Method
	context["path"] = r.URL.Path
	context["user_agent"] = r.UserAgent()
	context["remote_addr"] = r.RemoteAddr

	// Get HTTP status code
	statusCode := errors.HTTPStatus(err)

	return &ErrorResponse{
		Error: ErrorDetails{
			Code:    string(code),
			Message: message,
			Details: details,
			Context: context,
		},
		RequestID:  m.getRequestID(r),
		Timestamp:  time.Now().UTC(),
		Path:       r.URL.Path,
		StatusCode: statusCode,
	}
}

// ErrorResponse represents a structured error response
type ErrorResponse struct {
	Error      ErrorDetails `json:"error"`
	RequestID  string       `json:"request_id,omitempty"`
	Timestamp  time.Time    `json:"timestamp"`
	Path       string       `json:"path,omitempty"`
	StatusCode int          `json:"-"`
}

// ErrorDetails contains detailed error information
type ErrorDetails struct {
	Code    string                 `json:"code"`
	Message string                 `json:"message"`
	Details string                 `json:"details,omitempty"`
	Context map[string]interface{} `json:"context,omitempty"`
}

// writeErrorResponse writes an error response
func (m *ErrorRecoveryMiddleware) writeErrorResponse(w http.ResponseWriter, response *ErrorResponse) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(response.StatusCode)

	// Write JSON response
	if err := json.NewEncoder(w).Encode(response); err != nil {
		logger.Error("Failed to encode error response: %v", err)
	}
}

// getStackTrace gets stack trace
func (m *ErrorRecoveryMiddleware) getStackTrace() string {
	buf := make([]byte, 1024)
	n := runtime.Stack(buf, false)
	return string(buf[:n])
}

// getRequestID extracts request ID from context
func (m *ErrorRecoveryMiddleware) getRequestID(r *http.Request) string {
	if requestID := r.Context().Value("request_id"); requestID != nil {
		if id, ok := requestID.(string); ok {
			return id
		}
	}
	return ""
}

// Error context middleware

// ErrorContextMiddleware adds error context to requests
func ErrorContextMiddleware(service, operation string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Add service and operation context
			ctx := r.Context()
			ctx = context.WithValue(ctx, "service", service)
			ctx = context.WithValue(ctx, "operation", operation)

			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// Error logging middleware

// ErrorLoggingMiddleware logs errors for monitoring
type ErrorLoggingMiddleware struct {
	errorTracker *errors.ServiceErrorTracker
}

// NewErrorLoggingMiddleware creates a new error logging middleware
func NewErrorLoggingMiddleware() *ErrorLoggingMiddleware {
	return &ErrorLoggingMiddleware{
		errorTracker: errors.NewServiceErrorTracker(),
	}
}

// Handler returns the middleware handler
func (m *ErrorLoggingMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Create response writer that captures errors
		writer := &errorLoggingResponseWriter{
			ResponseWriter: w,
			middleware:     m,
			request:        r,
		}

		next.ServeHTTP(writer, r)
	})
}

// errorLoggingResponseWriter logs errors
type errorLoggingResponseWriter struct {
	http.ResponseWriter
	middleware *ErrorLoggingMiddleware
	request    *http.Request
	statusCode int
}

// WriteHeader captures the status code
func (w *errorLoggingResponseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
}

// Write captures write operations
func (w *errorLoggingResponseWriter) Write(data []byte) (int, error) {
	if w.statusCode == 0 {
		w.WriteHeader(http.StatusOK)
	}
	return w.ResponseWriter.Write(data)
}

// Error rate limiting middleware

// ErrorRateLimitMiddleware limits error responses to prevent abuse
type ErrorRateLimitMiddleware struct {
	errorTracker *errors.ServiceErrorTracker
	maxErrors    int
	windowSize   time.Duration
	errorCounts  map[string]int
	lastReset    time.Time
}

// NewErrorRateLimitMiddleware creates a new error rate limit middleware
func NewErrorRateLimitMiddleware(maxErrors int, windowSize time.Duration) *ErrorRateLimitMiddleware {
	return &ErrorRateLimitMiddleware{
		errorTracker: errors.NewServiceErrorTracker(),
		maxErrors:    maxErrors,
		windowSize:   windowSize,
		errorCounts:  make(map[string]int),
		lastReset:    time.Now(),
	}
}

// Handler returns the middleware handler
func (m *ErrorRateLimitMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if we should rate limit error responses
		if m.shouldRateLimit(r) {
			m.writeRateLimitResponse(w, r)
			return
		}

		// Create response writer that tracks errors
		writer := &errorRateLimitResponseWriter{
			ResponseWriter: w,
			middleware:     m,
			request:        r,
		}

		next.ServeHTTP(writer, r)
	})
}

// shouldRateLimit checks if error responses should be rate limited
func (m *ErrorRateLimitMiddleware) shouldRateLimit(r *http.Request) bool {
	// Reset counters if window has passed
	if time.Since(m.lastReset) > m.windowSize {
		m.errorCounts = make(map[string]int)
		m.lastReset = time.Now()
	}

	// Get client identifier
	clientID := m.getClientID(r)

	// Check error count for this client
	if m.errorCounts[clientID] >= m.maxErrors {
		return true
	}

	return false
}

// getClientID gets a client identifier for rate limiting
func (m *ErrorRateLimitMiddleware) getClientID(r *http.Request) string {
	// Try to get from X-Forwarded-For header first
	if forwardedFor := r.Header.Get("X-Forwarded-For"); forwardedFor != "" {
		// Take the first IP
		ips := strings.Split(forwardedFor, ",")
		return strings.TrimSpace(ips[0])
	}

	// Fall back to RemoteAddr
	return r.RemoteAddr
}

// writeRateLimitResponse writes a rate limit response
func (m *ErrorRateLimitMiddleware) writeRateLimitResponse(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusTooManyRequests)

	response := map[string]interface{}{
		"error": map[string]interface{}{
			"code":    "RATE_LIMITED",
			"message": "Too many error responses, please try again later",
		},
		"timestamp": time.Now().UTC(),
		"path":      r.URL.Path,
	}

	json.NewEncoder(w).Encode(response)
}

// errorRateLimitResponseWriter tracks errors for rate limiting
type errorRateLimitResponseWriter struct {
	http.ResponseWriter
	middleware *ErrorRateLimitMiddleware
	request    *http.Request
	statusCode int
}

// WriteHeader captures the status code
func (w *errorRateLimitResponseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
	w.ResponseWriter.WriteHeader(statusCode)

	// Track error responses
	if statusCode >= 400 {
		clientID := w.middleware.getClientID(w.request)
		w.middleware.errorCounts[clientID]++
	}
}

// Write captures write operations
func (w *errorRateLimitResponseWriter) Write(data []byte) (int, error) {
	if w.statusCode == 0 {
		w.WriteHeader(http.StatusOK)
	}
	return w.ResponseWriter.Write(data)
}

// Error metrics middleware

// ErrorMetricsMiddleware provides error metrics
type ErrorMetricsMiddleware struct {
	errorTracker *errors.ServiceErrorTracker
}

// NewErrorMetricsMiddleware creates a new error metrics middleware
func NewErrorMetricsMiddleware() *ErrorMetricsMiddleware {
	return &ErrorMetricsMiddleware{
		errorTracker: errors.NewServiceErrorTracker(),
	}
}

// Handler returns the middleware handler
func (m *ErrorMetricsMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create response writer that tracks metrics
		writer := &errorMetricsResponseWriter{
			ResponseWriter: w,
			middleware:     m,
			request:        r,
			startTime:      start,
		}

		next.ServeHTTP(writer, r)
	})
}

// errorMetricsResponseWriter tracks error metrics
type errorMetricsResponseWriter struct {
	http.ResponseWriter
	middleware *ErrorMetricsMiddleware
	request    *http.Request
	startTime  time.Time
	statusCode int
}

// WriteHeader captures the status code
func (w *errorMetricsResponseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
}

// Write captures write operations
func (w *errorMetricsResponseWriter) Write(data []byte) (int, error) {
	if w.statusCode == 0 {
		w.WriteHeader(http.StatusOK)
	}
	return w.ResponseWriter.Write(data)
}

// GetErrorMetrics returns error metrics
func (m *ErrorMetricsMiddleware) GetErrorMetrics() map[string]*errors.ServiceErrorMetrics {
	return m.errorTracker.GetAllMetrics()
}
