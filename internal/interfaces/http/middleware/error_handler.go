package middleware

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/arx-os/arxos/internal/domain"
)

// ErrorResponse represents a standardized error response
type ErrorResponse struct {
	Error     string                 `json:"error"`
	Message   string                 `json:"message"`
	Code      string                 `json:"code,omitempty"`
	RequestID string                 `json:"request_id,omitempty"`
	Details   map[string]interface{} `json:"details,omitempty"`
}

// ErrorHandlerMiddleware provides centralized error handling
func ErrorHandlerMiddleware(logger domain.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Create a custom response writer to capture panics
			wrapped := &panicResponseWriter{ResponseWriter: w, logger: logger}

			// Recover from panics
			defer func() {
				if err := recover(); err != nil {
					wrapped.handlePanic(err, r)
				}
			}()

			next.ServeHTTP(wrapped, r)
		})
	}
}

// panicResponseWriter wraps http.ResponseWriter to handle panics
type panicResponseWriter struct {
	http.ResponseWriter
	logger domain.Logger
}

func (prw *panicResponseWriter) handlePanic(err interface{}, r *http.Request) {
	// Log the panic
	prw.logger.Error("HTTP Handler Panic",
		"error", err,
		"method", r.Method,
		"path", r.URL.Path,
		"remote_addr", r.RemoteAddr,
		"request_id", r.Header.Get("X-Request-ID"),
	)

	// Send error response
	errorResp := ErrorResponse{
		Error:     "Internal Server Error",
		Message:   "An unexpected error occurred",
		Code:      "INTERNAL_ERROR",
		RequestID: r.Header.Get("X-Request-ID"),
	}

	prw.ResponseWriter.Header().Set("Content-Type", "application/json")
	prw.ResponseWriter.WriteHeader(http.StatusInternalServerError)
	json.NewEncoder(prw.ResponseWriter).Encode(errorResp)
}

// WriteErrorResponse writes a standardized error response
func WriteErrorResponse(w http.ResponseWriter, r *http.Request, statusCode int, error, message, code string, details map[string]interface{}) {
	errorResp := ErrorResponse{
		Error:     error,
		Message:   message,
		Code:      code,
		RequestID: r.Header.Get("X-Request-ID"),
		Details:   details,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(errorResp)
}

// ValidationErrorResponse writes a validation error response
func ValidationErrorResponse(w http.ResponseWriter, r *http.Request, validationErrors map[string]string) {
	WriteErrorResponse(w, r, http.StatusBadRequest,
		"Validation Error",
		"Request validation failed",
		"VALIDATION_ERROR",
		map[string]interface{}{"validation_errors": validationErrors})
}

// NotFoundErrorResponse writes a not found error response
func NotFoundErrorResponse(w http.ResponseWriter, r *http.Request, resource string) {
	WriteErrorResponse(w, r, http.StatusNotFound,
		"Not Found",
		fmt.Sprintf("%s not found", resource),
		"NOT_FOUND",
		nil)
}

// UnauthorizedErrorResponse writes an unauthorized error response
func UnauthorizedErrorResponse(w http.ResponseWriter, r *http.Request, message string) {
	if message == "" {
		message = "Authentication required"
	}
	WriteErrorResponse(w, r, http.StatusUnauthorized,
		"Unauthorized",
		message,
		"UNAUTHORIZED",
		nil)
}

// ForbiddenErrorResponse writes a forbidden error response
func ForbiddenErrorResponse(w http.ResponseWriter, r *http.Request, message string) {
	if message == "" {
		message = "Insufficient permissions"
	}
	WriteErrorResponse(w, r, http.StatusForbidden,
		"Forbidden",
		message,
		"FORBIDDEN",
		nil)
}

// ConflictErrorResponse writes a conflict error response
func ConflictErrorResponse(w http.ResponseWriter, r *http.Request, message string) {
	if message == "" {
		message = "Resource conflict"
	}
	WriteErrorResponse(w, r, http.StatusConflict,
		"Conflict",
		message,
		"CONFLICT",
		nil)
}

// TooManyRequestsErrorResponse writes a rate limit error response
func TooManyRequestsErrorResponse(w http.ResponseWriter, r *http.Request, message string) {
	if message == "" {
		message = "Rate limit exceeded"
	}
	WriteErrorResponse(w, r, http.StatusTooManyRequests,
		"Too Many Requests",
		message,
		"RATE_LIMIT_EXCEEDED",
		nil)
}
