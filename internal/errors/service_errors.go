// Package errors provides enhanced error handling for service layer
package errors

import (
	"errors"
	"fmt"
	"time"
)

// ServiceError represents a service-specific error with additional context
type ServiceError struct {
	*AppError
	Service    string                 `json:"service"`
	Operation  string                 `json:"operation"`
	ResourceID string                 `json:"resource_id,omitempty"`
	RetryAfter *time.Duration         `json:"retry_after,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// Error implements the error interface
func (e *ServiceError) Error() string {
	if e.AppError != nil {
		return fmt.Sprintf("[%s:%s] %s", e.Service, e.Operation, e.AppError.Error())
	}
	return fmt.Sprintf("[%s:%s] %s", e.Service, e.Operation, e.Message)
}

// NewServiceError creates a new service error
func NewServiceError(service, operation string, code ErrorCode, message string) *ServiceError {
	return &ServiceError{
		AppError:  New(code, message),
		Service:   service,
		Operation: operation,
		Metadata:  make(map[string]interface{}),
	}
}

// WrapServiceError wraps an existing error as a service error
func WrapServiceError(err error, service, operation string, code ErrorCode, message string) *ServiceError {
	return &ServiceError{
		AppError:  Wrap(err, code, message),
		Service:   service,
		Operation: operation,
		Metadata:  make(map[string]interface{}),
	}
}

// WithResourceID adds a resource ID to the error
func (e *ServiceError) WithResourceID(resourceID string) *ServiceError {
	e.ResourceID = resourceID
	return e
}

// WithRetryAfter adds retry information to the error
func (e *ServiceError) WithRetryAfter(duration time.Duration) *ServiceError {
	e.RetryAfter = &duration
	return e
}

// WithMetadata adds metadata to the error
func (e *ServiceError) WithMetadata(key string, value interface{}) *ServiceError {
	if e.Metadata == nil {
		e.Metadata = make(map[string]interface{})
	}
	e.Metadata[key] = value
	return e
}

// IsServiceError checks if an error is a ServiceError
func IsServiceError(err error) bool {
	var serviceErr *ServiceError
	return errors.As(err, &serviceErr)
}

// GetServiceError extracts ServiceError from an error chain
func GetServiceError(err error) *ServiceError {
	var serviceErr *ServiceError
	if errors.As(err, &serviceErr) {
		return serviceErr
	}
	return nil
}

// Service error constructors for common patterns

// NotFoundServiceError creates a not found service error
func NotFoundServiceError(service, operation, resourceType, resourceID string) *ServiceError {
	return NewServiceError(service, operation, CodeNotFound, fmt.Sprintf("%s not found", resourceType)).
		WithResourceID(resourceID).
		WithMetadata("resource_type", resourceType)
}

// ValidationServiceError creates a validation service error
func ValidationServiceError(service, operation, field, reason string) *ServiceError {
	return NewServiceError(service, operation, CodeInvalidInput, fmt.Sprintf("validation failed for field '%s': %s", field, reason)).
		WithMetadata("field", field).
		WithMetadata("reason", reason)
}

// DatabaseServiceError creates a database service error
func DatabaseServiceError(service, operation string, err error) *ServiceError {
	return WrapServiceError(err, service, operation, CodeDatabase, "database operation failed").
		WithMetadata("operation_type", "database")
}

// TimeoutServiceError creates a timeout service error
func TimeoutServiceError(service, operation string, timeout time.Duration) *ServiceError {
	return NewServiceError(service, operation, CodeTimeout, fmt.Sprintf("operation timed out after %v", timeout)).
		WithMetadata("timeout_duration", timeout.String())
}

// ConflictServiceError creates a conflict service error
func ConflictServiceError(service, operation, resourceType, resourceID, reason string) *ServiceError {
	return NewServiceError(service, operation, CodeConflict, fmt.Sprintf("conflict in %s: %s", resourceType, reason)).
		WithResourceID(resourceID).
		WithMetadata("resource_type", resourceType).
		WithMetadata("conflict_reason", reason)
}

// RateLimitServiceError creates a rate limit service error
func RateLimitServiceError(service, operation string, retryAfter time.Duration) *ServiceError {
	return NewServiceError(service, operation, CodeRateLimited, "rate limit exceeded").
		WithRetryAfter(retryAfter).
		WithMetadata("rate_limit_type", "service")
}

// Service error recovery patterns

// RetryableServiceError represents an error that can be retried
type RetryableServiceError struct {
	*ServiceError
	MaxRetries int           `json:"max_retries"`
	RetryDelay time.Duration `json:"retry_delay"`
}

// NewRetryableServiceError creates a retryable service error
func NewRetryableServiceError(service, operation string, code ErrorCode, message string, maxRetries int, retryDelay time.Duration) *RetryableServiceError {
	return &RetryableServiceError{
		ServiceError: NewServiceError(service, operation, code, message),
		MaxRetries:   maxRetries,
		RetryDelay:   retryDelay,
	}
}

// IsRetryableServiceError checks if an error is retryable
func IsRetryableServiceError(err error) bool {
	var retryableErr *RetryableServiceError
	return errors.As(err, &retryableErr)
}

// GetRetryableServiceError extracts RetryableServiceError from an error chain
func GetRetryableServiceError(err error) *RetryableServiceError {
	var retryableErr *RetryableServiceError
	if errors.As(err, &retryableErr) {
		return retryableErr
	}
	return nil
}

// Service error aggregation

// ServiceErrorGroup represents multiple service errors
type ServiceErrorGroup struct {
	Service   string          `json:"service"`
	Operation string          `json:"operation"`
	Errors    []*ServiceError `json:"errors"`
	Summary   string          `json:"summary"`
}

// NewServiceErrorGroup creates a new service error group
func NewServiceErrorGroup(service, operation string, errors []*ServiceError) *ServiceErrorGroup {
	summary := fmt.Sprintf("%d errors occurred in %s:%s", len(errors), service, operation)
	return &ServiceErrorGroup{
		Service:   service,
		Operation: operation,
		Errors:    errors,
		Summary:   summary,
	}
}

// Error implements the error interface
func (g *ServiceErrorGroup) Error() string {
	return g.Summary
}

// AddError adds an error to the group
func (g *ServiceErrorGroup) AddError(err *ServiceError) {
	g.Errors = append(g.Errors, err)
	g.Summary = fmt.Sprintf("%d errors occurred in %s:%s", len(g.Errors), g.Service, g.Operation)
}

// HasErrors returns true if the group has errors
func (g *ServiceErrorGroup) HasErrors() bool {
	return len(g.Errors) > 0
}

// GetCriticalErrors returns only critical errors from the group
func (g *ServiceErrorGroup) GetCriticalErrors() []*ServiceError {
	var critical []*ServiceError
	for _, err := range g.Errors {
		if IsFatal(err) {
			critical = append(critical, err)
		}
	}
	return critical
}

// Service error context helpers

// WithServiceContext adds service context to an error
func WithServiceContext(err error, service, operation string) error {
	if err == nil {
		return nil
	}

	// If already a ServiceError, update context
	if serviceErr := GetServiceError(err); serviceErr != nil {
		serviceErr.Service = service
		serviceErr.Operation = operation
		return serviceErr
	}

	// Wrap as new ServiceError
	return WrapServiceError(err, service, operation, CodeInternal, "service operation failed")
}

// WithOperationContext adds operation context to an error
func WithOperationContext(err error, operation string) error {
	if err == nil {
		return nil
	}

	// If already a ServiceError, update operation
	if serviceErr := GetServiceError(err); serviceErr != nil {
		serviceErr.Operation = operation
		return serviceErr
	}

	// Wrap as new ServiceError with unknown service
	return WrapServiceError(err, "unknown", operation, CodeInternal, "service operation failed")
}

// Service error metrics and monitoring

// ServiceErrorMetrics tracks error metrics for a service
type ServiceErrorMetrics struct {
	Service     string
	Operation   string
	ErrorCount  int
	LastError   time.Time
	ErrorRate   float64
	RetryCount  int
	SuccessRate float64
}

// ServiceErrorTracker tracks errors across services
type ServiceErrorTracker struct {
	metrics map[string]*ServiceErrorMetrics
}

// NewServiceErrorTracker creates a new error tracker
func NewServiceErrorTracker() *ServiceErrorTracker {
	return &ServiceErrorTracker{
		metrics: make(map[string]*ServiceErrorMetrics),
	}
}

// TrackError records an error for metrics
func (t *ServiceErrorTracker) TrackError(service, operation string, err error) {
	key := fmt.Sprintf("%s:%s", service, operation)

	metrics, exists := t.metrics[key]
	if !exists {
		metrics = &ServiceErrorMetrics{
			Service:   service,
			Operation: operation,
		}
		t.metrics[key] = metrics
	}

	metrics.ErrorCount++
	metrics.LastError = time.Now()

	// Update error rate (simplified calculation)
	totalOps := metrics.ErrorCount + int(metrics.SuccessRate*float64(metrics.ErrorCount))
	if totalOps > 0 {
		metrics.ErrorRate = float64(metrics.ErrorCount) / float64(totalOps)
		metrics.SuccessRate = 1.0 - metrics.ErrorRate
	}
}

// GetMetrics returns error metrics for a service
func (t *ServiceErrorTracker) GetMetrics(service, operation string) *ServiceErrorMetrics {
	key := fmt.Sprintf("%s:%s", service, operation)
	return t.metrics[key]
}

// GetAllMetrics returns all error metrics
func (t *ServiceErrorTracker) GetAllMetrics() map[string]*ServiceErrorMetrics {
	return t.metrics
}
