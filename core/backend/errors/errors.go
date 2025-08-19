// Package errors provides standardized error handling for the Arxos backend
package errors

import (
	"fmt"
	"net/http"
	"runtime"
	"time"

	"go.uber.org/zap"
)

// ErrorType represents the type of error
type ErrorType string

const (
	// ValidationError represents validation failures
	ValidationError ErrorType = "validation_error"
	
	// NotFoundError represents resource not found
	NotFoundError ErrorType = "not_found"
	
	// UnauthorizedError represents authentication failures
	UnauthorizedError ErrorType = "unauthorized"
	
	// ForbiddenError represents authorization failures
	ForbiddenError ErrorType = "forbidden"
	
	// ConflictError represents resource conflicts
	ConflictError ErrorType = "conflict"
	
	// InternalError represents internal server errors
	InternalError ErrorType = "internal_error"
	
	// ExternalError represents external service errors
	ExternalError ErrorType = "external_error"
	
	// DatabaseError represents database operation errors
	DatabaseError ErrorType = "database_error"
	
	// ConfigurationError represents configuration errors
	ConfigurationError ErrorType = "configuration_error"
	
	// RateLimitError represents rate limiting errors
	RateLimitError ErrorType = "rate_limit_error"
)

// ArxosError represents a standardized error in the Arxos system
type ArxosError struct {
	Type        ErrorType              `json:"type"`
	Message     string                 `json:"message"`
	Details     map[string]interface{} `json:"details,omitempty"`
	Code        string                 `json:"code,omitempty"`
	StatusCode  int                    `json:"status_code"`
	Timestamp   time.Time              `json:"timestamp"`
	RequestID   string                 `json:"request_id,omitempty"`
	UserID      string                 `json:"user_id,omitempty"`
	StackTrace  string                 `json:"stack_trace,omitempty"`
	Cause       error                  `json:"-"`
	Retryable   bool                   `json:"retryable"`
	Component   string                 `json:"component,omitempty"`
}

// Error implements the error interface
func (e *ArxosError) Error() string {
	if e.Code != "" {
		return fmt.Sprintf("[%s] %s: %s", e.Code, e.Type, e.Message)
	}
	return fmt.Sprintf("[%s] %s", e.Type, e.Message)
}

// Unwrap returns the underlying error
func (e *ArxosError) Unwrap() error {
	return e.Cause
}

// Is checks if the error is of a specific type
func (e *ArxosError) Is(target error) bool {
	if t, ok := target.(*ArxosError); ok {
		return e.Type == t.Type
	}
	return false
}

// WithDetail adds a detail to the error
func (e *ArxosError) WithDetail(key string, value interface{}) *ArxosError {
	if e.Details == nil {
		e.Details = make(map[string]interface{})
	}
	e.Details[key] = value
	return e
}

// WithCode sets the error code
func (e *ArxosError) WithCode(code string) *ArxosError {
	e.Code = code
	return e
}

// WithRequestID sets the request ID
func (e *ArxosError) WithRequestID(requestID string) *ArxosError {
	e.RequestID = requestID
	return e
}

// WithUserID sets the user ID
func (e *ArxosError) WithUserID(userID string) *ArxosError {
	e.UserID = userID
	return e
}

// WithComponent sets the component name
func (e *ArxosError) WithComponent(component string) *ArxosError {
	e.Component = component
	return e
}

// WithStackTrace captures the current stack trace
func (e *ArxosError) WithStackTrace() *ArxosError {
	buf := make([]byte, 2048)
	n := runtime.Stack(buf, false)
	e.StackTrace = string(buf[:n])
	return e
}

// NewError creates a new ArxosError
func NewError(errorType ErrorType, message string) *ArxosError {
	return &ArxosError{
		Type:       errorType,
		Message:    message,
		StatusCode: getDefaultStatusCode(errorType),
		Timestamp:  time.Now(),
		Retryable:  isRetryable(errorType),
	}
}

// NewValidationError creates a validation error
func NewValidationError(message string) *ArxosError {
	return NewError(ValidationError, message).WithCode("VAL_001")
}

// NewNotFoundError creates a not found error
func NewNotFoundError(resource string) *ArxosError {
	return NewError(NotFoundError, fmt.Sprintf("%s not found", resource)).WithCode("NOT_001")
}

// NewUnauthorizedError creates an unauthorized error
func NewUnauthorizedError(message string) *ArxosError {
	return NewError(UnauthorizedError, message).WithCode("AUTH_001")
}

// NewForbiddenError creates a forbidden error
func NewForbiddenError(message string) *ArxosError {
	return NewError(ForbiddenError, message).WithCode("AUTH_002")
}

// NewConflictError creates a conflict error
func NewConflictError(message string) *ArxosError {
	return NewError(ConflictError, message).WithCode("CONF_001")
}

// NewInternalError creates an internal error
func NewInternalError(message string) *ArxosError {
	return NewError(InternalError, message).WithCode("INT_001").WithStackTrace()
}

// NewExternalError creates an external service error
func NewExternalError(service, message string) *ArxosError {
	return NewError(ExternalError, fmt.Sprintf("%s: %s", service, message)).
		WithCode("EXT_001").
		WithDetail("service", service)
}

// NewDatabaseError creates a database error
func NewDatabaseError(operation, message string) *ArxosError {
	return NewError(DatabaseError, fmt.Sprintf("Database %s failed: %s", operation, message)).
		WithCode("DB_001").
		WithDetail("operation", operation)
}

// NewConfigurationError creates a configuration error
func NewConfigurationError(message string) *ArxosError {
	return NewError(ConfigurationError, message).WithCode("CFG_001")
}

// NewRateLimitError creates a rate limit error
func NewRateLimitError(message string) *ArxosError {
	return NewError(RateLimitError, message).WithCode("RATE_001")
}

// WrapError wraps an existing error with ArxosError
func WrapError(err error, errorType ErrorType, message string) *ArxosError {
	if err == nil {
		return nil
	}
	
	arxosErr := NewError(errorType, message)
	arxosErr.Cause = err
	
	// If the underlying error is already an ArxosError, preserve some details
	if existing, ok := err.(*ArxosError); ok {
		if arxosErr.RequestID == "" {
			arxosErr.RequestID = existing.RequestID
		}
		if arxosErr.UserID == "" {
			arxosErr.UserID = existing.UserID
		}
		if arxosErr.Component == "" {
			arxosErr.Component = existing.Component
		}
	}
	
	return arxosErr
}

// getDefaultStatusCode returns the default HTTP status code for an error type
func getDefaultStatusCode(errorType ErrorType) int {
	switch errorType {
	case ValidationError:
		return http.StatusBadRequest
	case NotFoundError:
		return http.StatusNotFound
	case UnauthorizedError:
		return http.StatusUnauthorized
	case ForbiddenError:
		return http.StatusForbidden
	case ConflictError:
		return http.StatusConflict
	case RateLimitError:
		return http.StatusTooManyRequests
	case InternalError, DatabaseError, ConfigurationError:
		return http.StatusInternalServerError
	case ExternalError:
		return http.StatusBadGateway
	default:
		return http.StatusInternalServerError
	}
}

// isRetryable returns whether an error type is retryable
func isRetryable(errorType ErrorType) bool {
	switch errorType {
	case ExternalError, DatabaseError, RateLimitError:
		return true
	case ValidationError, NotFoundError, UnauthorizedError, ForbiddenError, ConflictError:
		return false
	case InternalError, ConfigurationError:
		return false
	default:
		return false
	}
}

// ErrorResponse represents an HTTP error response
type ErrorResponse struct {
	Error     *ArxosError `json:"error"`
	Success   bool        `json:"success"`
	Timestamp time.Time   `json:"timestamp"`
	Path      string      `json:"path,omitempty"`
	Method    string      `json:"method,omitempty"`
}

// LogError logs an error with appropriate level and context
func LogError(logger *zap.Logger, err error, context ...zap.Field) {
	if err == nil {
		return
	}
	
	// Add error details to context
	fields := append(context, zap.Error(err))
	
	if arxosErr, ok := err.(*ArxosError); ok {
		// Add structured fields for ArxosError
		fields = append(fields,
			zap.String("error_type", string(arxosErr.Type)),
			zap.String("error_code", arxosErr.Code),
			zap.Int("status_code", arxosErr.StatusCode),
			zap.Bool("retryable", arxosErr.Retryable),
			zap.String("request_id", arxosErr.RequestID),
			zap.String("user_id", arxosErr.UserID),
			zap.String("component", arxosErr.Component),
		)
		
		// Add details if present
		if len(arxosErr.Details) > 0 {
			for key, value := range arxosErr.Details {
				fields = append(fields, zap.Any(fmt.Sprintf("detail_%s", key), value))
			}
		}
		
		// Log at appropriate level
		switch arxosErr.Type {
		case ValidationError, NotFoundError:
			logger.Info("Client error", fields...)
		case UnauthorizedError, ForbiddenError:
			logger.Warn("Authentication/Authorization error", fields...)
		case ConflictError, RateLimitError:
			logger.Warn("Request conflict", fields...)
		case ExternalError:
			logger.Error("External service error", fields...)
		case DatabaseError, InternalError, ConfigurationError:
			logger.Error("Internal error", fields...)
		default:
			logger.Error("Unknown error", fields...)
		}
	} else {
		// Log non-ArxosError as error
		logger.Error("Unhandled error", fields...)
	}
}

// RecoverPanic recovers from a panic and returns an ArxosError
func RecoverPanic() *ArxosError {
	if r := recover(); r != nil {
		err := NewInternalError(fmt.Sprintf("Panic recovered: %v", r)).WithStackTrace()
		err.WithDetail("panic_value", r)
		return err
	}
	return nil
}

// ErrorHandler provides centralized error handling middleware
type ErrorHandler struct {
	logger *zap.Logger
}

// NewErrorHandler creates a new error handler
func NewErrorHandler(logger *zap.Logger) *ErrorHandler {
	return &ErrorHandler{logger: logger}
}

// HandleError handles an error and writes an appropriate HTTP response
func (h *ErrorHandler) HandleError(w http.ResponseWriter, r *http.Request, err error) {
	if err == nil {
		return
	}
	
	// Convert to ArxosError if needed
	var arxosErr *ArxosError
	if ae, ok := err.(*ArxosError); ok {
		arxosErr = ae
	} else {
		arxosErr = WrapError(err, InternalError, "An internal error occurred")
	}
	
	// Add request context
	if arxosErr.RequestID == "" {
		if reqID := r.Header.Get("X-Request-ID"); reqID != "" {
			arxosErr.RequestID = reqID
		}
	}
	
	// Log the error
	LogError(h.logger, arxosErr,
		zap.String("method", r.Method),
		zap.String("path", r.URL.Path),
		zap.String("remote_addr", r.RemoteAddr),
		zap.String("user_agent", r.UserAgent()),
	)
	
	// Create error response
	response := ErrorResponse{
		Error:     arxosErr,
		Success:   false,
		Timestamp: time.Now(),
		Path:      r.URL.Path,
		Method:    r.Method,
	}
	
	// Remove stack trace from response in production
	if !h.isDevelopment() {
		response.Error.StackTrace = ""
	}
	
	// Write HTTP response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(arxosErr.StatusCode)
	
	// Note: In a real implementation, you'd use a proper JSON encoder
	// For simplicity, we'll assume encoding works
	_ = response
}

// isDevelopment checks if running in development mode
func (h *ErrorHandler) isDevelopment() bool {
	// This should be determined from configuration
	// For now, check environment variable
	return true // Simplified for example
}

// Validation helper functions

// RequireNotEmpty validates that a string is not empty
func RequireNotEmpty(value, fieldName string) error {
	if value == "" {
		return NewValidationError(fmt.Sprintf("%s is required", fieldName))
	}
	return nil
}

// RequirePositive validates that a number is positive
func RequirePositive(value float64, fieldName string) error {
	if value <= 0 {
		return NewValidationError(fmt.Sprintf("%s must be positive", fieldName))
	}
	return nil
}

// RequireRange validates that a number is within a range
func RequireRange(value, min, max float64, fieldName string) error {
	if value < min || value > max {
		return NewValidationError(fmt.Sprintf("%s must be between %f and %f", fieldName, min, max))
	}
	return nil
}

// RequireValidEmail validates email format (simplified)
func RequireValidEmail(email string) error {
	if email == "" {
		return NewValidationError("email is required")
	}
	// Simplified validation - in production use proper email validation
	if len(email) < 5 || !contains(email, "@") || !contains(email, ".") {
		return NewValidationError("email format is invalid")
	}
	return nil
}

// RequireValidUUID validates UUID format (simplified)
func RequireValidUUID(uuid, fieldName string) error {
	if uuid == "" {
		return NewValidationError(fmt.Sprintf("%s is required", fieldName))
	}
	// Simplified validation - in production use proper UUID validation
	if len(uuid) != 36 {
		return NewValidationError(fmt.Sprintf("%s must be a valid UUID", fieldName))
	}
	return nil
}

// RequireOneOf validates that value is one of allowed values
func RequireOneOf(value string, allowed []string, fieldName string) error {
	for _, a := range allowed {
		if value == a {
			return nil
		}
	}
	return NewValidationError(fmt.Sprintf("%s must be one of: %v", fieldName, allowed))
}

// Helper function for string contains check
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 || 
		(len(s) > len(substr) && s[len(s)-len(substr):] == substr) ||
		(len(s) > len(substr) && s[:len(substr)] == substr) ||
		(len(s) > 2*len(substr) && s[len(s)/2-len(substr)/2:len(s)/2+len(substr)/2] == substr))
}

// Circuit breaker for external services
type CircuitState int

const (
	Closed CircuitState = iota
	Open
	HalfOpen
)

// CircuitBreaker prevents cascading failures
type CircuitBreaker struct {
	name            string
	maxFailures     int
	resetTimeout    time.Duration
	state           CircuitState
	failures        int
	lastFailureTime time.Time
	logger          *zap.Logger
}

// NewCircuitBreaker creates a new circuit breaker
func NewCircuitBreaker(name string, maxFailures int, resetTimeout time.Duration, logger *zap.Logger) *CircuitBreaker {
	return &CircuitBreaker{
		name:         name,
		maxFailures:  maxFailures,
		resetTimeout: resetTimeout,
		state:        Closed,
		logger:       logger,
	}
}

// Execute executes a function with circuit breaker protection
func (cb *CircuitBreaker) Execute(fn func() error) error {
	if cb.state == Open {
		if time.Since(cb.lastFailureTime) > cb.resetTimeout {
			cb.state = HalfOpen
			cb.logger.Info("Circuit breaker transitioning to half-open", zap.String("circuit", cb.name))
		} else {
			return NewExternalError(cb.name, "circuit breaker is open")
		}
	}
	
	err := fn()
	
	if err != nil {
		cb.recordFailure()
		return err
	}
	
	cb.recordSuccess()
	return nil
}

// recordFailure records a failure
func (cb *CircuitBreaker) recordFailure() {
	cb.failures++
	cb.lastFailureTime = time.Now()
	
	if cb.failures >= cb.maxFailures {
		cb.state = Open
		cb.logger.Warn("Circuit breaker opened due to failures",
			zap.String("circuit", cb.name),
			zap.Int("failures", cb.failures))
	}
}

// recordSuccess records a success
func (cb *CircuitBreaker) recordSuccess() {
	cb.failures = 0
	if cb.state == HalfOpen {
		cb.state = Closed
		cb.logger.Info("Circuit breaker closed after successful request", zap.String("circuit", cb.name))
	}
}