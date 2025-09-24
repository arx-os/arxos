package api

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

// ErrorResponse represents a structured error response
type ErrorResponse struct {
	Error     ErrorDetails `json:"error"`
	RequestID string       `json:"request_id,omitempty"`
	Timestamp time.Time    `json:"timestamp"`
	Path      string       `json:"path,omitempty"`
}

// ErrorDetails contains detailed error information
type ErrorDetails struct {
	Code       string                 `json:"code"`
	Message    string                 `json:"message"`
	Details    string                 `json:"details,omitempty"`
	Context    map[string]interface{} `json:"context,omitempty"`
	RetryAfter *int                   `json:"retry_after,omitempty"`
	Help       string                 `json:"help,omitempty"`
}

// ErrorHandler handles errors and provides structured responses
type ErrorHandler struct {
	includeStackTrace bool
	includeHelp       bool
	errorTracker      *errors.ServiceErrorTracker
}

// NewErrorHandler creates a new error handler
func NewErrorHandler(includeStackTrace, includeHelp bool) *ErrorHandler {
	return &ErrorHandler{
		includeStackTrace: includeStackTrace,
		includeHelp:       includeHelp,
		errorTracker:      errors.NewServiceErrorTracker(),
	}
}

// HandleError handles an error and writes a structured response
func (h *ErrorHandler) HandleError(w http.ResponseWriter, r *http.Request, err error) {
	if err == nil {
		return
	}

	// Track error for metrics
	h.trackError(r, err)

	// Create error response
	response := h.createErrorResponse(r, err)

	// Write response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(errors.HTTPStatus(err))

	if err := json.NewEncoder(w).Encode(response); err != nil {
		logger.Error("Failed to encode error response: %v", err)
	}
}

// createErrorResponse creates a structured error response
func (h *ErrorHandler) createErrorResponse(r *http.Request, err error) *ErrorResponse {
	// Extract error information
	code := errors.GetCode(err)
	message := err.Error()
	details := ""
	context := make(map[string]interface{})
	var retryAfter *int

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
		if serviceErr.RetryAfter != nil {
			retryAfterInt := int(serviceErr.RetryAfter.Seconds())
			retryAfter = &retryAfterInt
		}
	}

	// Add stack trace if enabled
	if h.includeStackTrace {
		context["stack_trace"] = h.getStackTrace(err)
	}

	// Add help information if enabled
	help := ""
	if h.includeHelp {
		help = h.getHelpMessage(code)
	}

	// Get HTTP status code (used in WriteHeader call)

	return &ErrorResponse{
		Error: ErrorDetails{
			Code:       string(code),
			Message:    message,
			Details:    details,
			Context:    context,
			RetryAfter: retryAfter,
			Help:       help,
		},
		RequestID: h.getRequestID(r),
		Timestamp: time.Now().UTC(),
		Path:      r.URL.Path,
	}
}

// trackError tracks error for metrics
func (h *ErrorHandler) trackError(r *http.Request, err error) {
	// Extract service and operation from context or URL
	service := h.extractService(r)
	operation := h.extractOperation(r)

	h.errorTracker.TrackError(service, operation, err)
}

// extractService extracts service name from request
func (h *ErrorHandler) extractService(r *http.Request) string {
	// Try to get from context first
	if service := r.Context().Value("service"); service != nil {
		if s, ok := service.(string); ok {
			return s
		}
	}

	// Extract from URL path
	path := strings.TrimPrefix(r.URL.Path, "/api/")
	parts := strings.Split(path, "/")
	if len(parts) > 0 {
		return parts[0]
	}

	return "unknown"
}

// extractOperation extracts operation name from request
func (h *ErrorHandler) extractOperation(r *http.Request) string {
	// Try to get from context first
	if operation := r.Context().Value("operation"); operation != nil {
		if op, ok := operation.(string); ok {
			return op
		}
	}

	// Extract from HTTP method and path
	method := strings.ToLower(r.Method)
	path := strings.TrimPrefix(r.URL.Path, "/api/")

	// Map common patterns
	switch {
	case strings.Contains(path, "/auth/"):
		return fmt.Sprintf("auth_%s", method)
	case strings.Contains(path, "/users"):
		return fmt.Sprintf("users_%s", method)
	case strings.Contains(path, "/buildings"):
		return fmt.Sprintf("buildings_%s", method)
	case strings.Contains(path, "/equipment"):
		return fmt.Sprintf("equipment_%s", method)
	case strings.Contains(path, "/spatial"):
		return fmt.Sprintf("spatial_%s", method)
	default:
		return fmt.Sprintf("%s_%s", method, strings.ReplaceAll(path, "/", "_"))
	}
}

// getRequestID extracts request ID from context
func (h *ErrorHandler) getRequestID(r *http.Request) string {
	if requestID := r.Context().Value("request_id"); requestID != nil {
		if id, ok := requestID.(string); ok {
			return id
		}
	}
	return ""
}

// getStackTrace gets stack trace for an error
func (h *ErrorHandler) getStackTrace(err error) string {
	if appErr, ok := err.(*errors.AppError); ok && appErr.StackTrace != "" {
		return appErr.StackTrace
	}

	// Generate stack trace
	buf := make([]byte, 1024)
	n := runtime.Stack(buf, false)
	return string(buf[:n])
}

// getHelpMessage returns help message for error codes
func (h *ErrorHandler) getHelpMessage(code errors.ErrorCode) string {
	switch code {
	case errors.CodeNotFound:
		return "The requested resource was not found. Please check the resource ID and try again."
	case errors.CodeUnauthorized:
		return "Authentication is required. Please provide a valid token."
	case errors.CodeForbidden:
		return "You don't have permission to access this resource. Please contact your administrator."
	case errors.CodeInvalidInput:
		return "The request contains invalid data. Please check your input and try again."
	case errors.CodeConflict:
		return "A conflict occurred. The resource may have been modified by another user."
	case errors.CodeRateLimited:
		return "Too many requests. Please wait before making another request."
	case errors.CodeTimeout:
		return "The request timed out. Please try again."
	case errors.CodeDatabase:
		return "A database error occurred. Please try again later."
	case errors.CodeInternal:
		return "An internal error occurred. Please contact support if the problem persists."
	default:
		return "An error occurred. Please try again or contact support if the problem persists."
	}
}

// ErrorHandler middleware
func (s *Server) errorHandlerMiddleware(next http.Handler) http.Handler {
	errorHandler := NewErrorHandler(
		true, // Include stack trace in dev
		true, // Always include help
	)

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Create a custom response writer to capture errors
		writer := &errorResponseWriter{
			ResponseWriter: w,
			errorHandler:   errorHandler,
			request:        r,
		}

		next.ServeHTTP(writer, r)
	})
}

// errorResponseWriter wraps http.ResponseWriter to capture errors
type errorResponseWriter struct {
	http.ResponseWriter
	errorHandler *ErrorHandler
	request      *http.Request
	statusCode   int
	written      bool
}

// WriteHeader captures the status code
func (w *errorResponseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
	w.written = true
}

// Write captures write operations
func (w *errorResponseWriter) Write(data []byte) (int, error) {
	if !w.written {
		w.WriteHeader(http.StatusOK)
	}
	return w.ResponseWriter.Write(data)
}

// HandleError handles errors in the response writer
func (w *errorResponseWriter) HandleError(err error) {
	if err != nil && !w.written {
		w.errorHandler.HandleError(w.ResponseWriter, w.request, err)
		w.written = true
	}
}

// Enhanced error response helpers

// respondStructuredError sends a structured error response
func (s *Server) respondStructuredError(w http.ResponseWriter, r *http.Request, err error) {
	errorHandler := NewErrorHandler(
		true,
		true,
	)
	errorHandler.HandleError(w, r, err)
}

// respondValidationError sends a validation error response
func (s *Server) respondValidationError(w http.ResponseWriter, r *http.Request, field, reason string) {
	err := errors.ValidationServiceError("api", "validation", field, reason)
	s.respondStructuredError(w, r, err)
}

// respondNotFoundError sends a not found error response
func (s *Server) respondNotFoundError(w http.ResponseWriter, r *http.Request, resourceType, resourceID string) {
	err := errors.NotFoundServiceError("api", "get", resourceType, resourceID)
	s.respondStructuredError(w, r, err)
}

// respondConflictError sends a conflict error response
func (s *Server) respondConflictError(w http.ResponseWriter, r *http.Request, resourceType, resourceID, reason string) {
	err := errors.ConflictServiceError("api", "update", resourceType, resourceID, reason)
	s.respondStructuredError(w, r, err)
}

// respondRateLimitError sends a rate limit error response
func (s *Server) respondRateLimitError(w http.ResponseWriter, r *http.Request, retryAfter time.Duration) {
	err := errors.RateLimitServiceError("api", "request", retryAfter)
	s.respondStructuredError(w, r, err)
}

// Error recovery patterns

// RecoverFromPanic recovers from panics and converts to errors
func (s *Server) RecoverFromPanic(r *http.Request) {
	if recovered := recover(); recovered != nil {
		err := fmt.Errorf("panic recovered: %v", recovered)
		logger.Error("Panic in request %s: %v", r.URL.Path, err)

		// Convert panic to structured error
		appErr := errors.New(errors.CodeInternal, "internal server error")
		appErr = appErr.WithContext("panic", true)
		appErr = appErr.WithContext("recovered_value", recovered)

		// This would need to be handled by the calling code
		// as we can't write to response here
		_ = appErr
	}
}

// Error context helpers

// WithErrorContext adds error context to a request
func WithErrorContext(r *http.Request, service, operation string) *http.Request {
	ctx := r.Context()
	ctx = context.WithValue(ctx, "service", service)
	ctx = context.WithValue(ctx, "operation", operation)
	return r.WithContext(ctx)
}

// Error metrics and monitoring

// GetErrorMetrics returns error metrics for monitoring
func (s *Server) GetErrorMetrics() map[string]*errors.ServiceErrorMetrics {
	// This would be implemented with the actual error tracker
	// For now, return empty map
	return make(map[string]*errors.ServiceErrorMetrics)
}
