package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/errors"
)

// ServiceErrorHandler provides error handling utilities for services
type ServiceErrorHandler struct {
	serviceName  string
	errorTracker *errors.ServiceErrorTracker
}

// NewServiceErrorHandler creates a new service error handler
func NewServiceErrorHandler(serviceName string) *ServiceErrorHandler {
	return &ServiceErrorHandler{
		serviceName:  serviceName,
		errorTracker: errors.NewServiceErrorTracker(),
	}
}

// HandleError handles an error with service context
func (h *ServiceErrorHandler) HandleError(operation string, err error) error {
	if err == nil {
		return nil
	}

	// Track error for metrics
	h.errorTracker.TrackError(h.serviceName, operation, err)

	// Add service context to error
	return errors.WithServiceContext(err, h.serviceName, operation)
}

// HandleDatabaseError handles database errors with proper context
func (h *ServiceErrorHandler) HandleDatabaseError(operation string, err error) error {
	if err == nil {
		return nil
	}

	// Create database service error
	serviceErr := errors.DatabaseServiceError(h.serviceName, operation, err)

	// Track error
	h.errorTracker.TrackError(h.serviceName, operation, serviceErr)

	return serviceErr
}

// HandleValidationError handles validation errors
func (h *ServiceErrorHandler) HandleValidationError(operation, field, reason string) error {
	serviceErr := errors.ValidationServiceError(h.serviceName, operation, field, reason)

	// Track error
	h.errorTracker.TrackError(h.serviceName, operation, serviceErr)

	return serviceErr
}

// HandleNotFoundError handles not found errors
func (h *ServiceErrorHandler) HandleNotFoundError(operation, resourceType, resourceID string) error {
	serviceErr := errors.NotFoundServiceError(h.serviceName, operation, resourceType, resourceID)

	// Track error
	h.errorTracker.TrackError(h.serviceName, operation, serviceErr)

	return serviceErr
}

// HandleConflictError handles conflict errors
func (h *ServiceErrorHandler) HandleConflictError(operation, resourceType, resourceID, reason string) error {
	serviceErr := errors.ConflictServiceError(h.serviceName, operation, resourceType, resourceID, reason)

	// Track error
	h.errorTracker.TrackError(h.serviceName, operation, serviceErr)

	return serviceErr
}

// HandleTimeoutError handles timeout errors
func (h *ServiceErrorHandler) HandleTimeoutError(operation string, timeout time.Duration) error {
	serviceErr := errors.TimeoutServiceError(h.serviceName, operation, timeout)

	// Track error
	h.errorTracker.TrackError(h.serviceName, operation, serviceErr)

	return serviceErr
}

// HandleRateLimitError handles rate limit errors
func (h *ServiceErrorHandler) HandleRateLimitError(operation string, retryAfter time.Duration) error {
	serviceErr := errors.RateLimitServiceError(h.serviceName, operation, retryAfter)

	// Track error
	h.errorTracker.TrackError(h.serviceName, operation, serviceErr)

	return serviceErr
}

// RetryableErrorHandler handles retryable errors with exponential backoff
type RetryableErrorHandler struct {
	*ServiceErrorHandler
	maxRetries int
	baseDelay  time.Duration
	maxDelay   time.Duration
}

// NewRetryableErrorHandler creates a new retryable error handler
func NewRetryableErrorHandler(serviceName string, maxRetries int, baseDelay, maxDelay time.Duration) *RetryableErrorHandler {
	return &RetryableErrorHandler{
		ServiceErrorHandler: NewServiceErrorHandler(serviceName),
		maxRetries:          maxRetries,
		baseDelay:           baseDelay,
		maxDelay:            maxDelay,
	}
}

// ExecuteWithRetry executes an operation with retry logic
func (h *RetryableErrorHandler) ExecuteWithRetry(ctx context.Context, operation string, fn func() error) error {
	var lastErr error

	for attempt := 0; attempt <= h.maxRetries; attempt++ {
		// Check context cancellation
		select {
		case <-ctx.Done():
			return h.HandleError(operation, ctx.Err())
		default:
		}

		// Execute operation
		err := fn()
		if err == nil {
			return nil
		}

		lastErr = err

		// Check if error is retryable
		if !errors.IsRetryable(err) {
			return h.HandleError(operation, err)
		}

		// Don't retry on last attempt
		if attempt == h.maxRetries {
			break
		}

		// Calculate delay with exponential backoff
		delay := h.calculateDelay(attempt)

		logger.Warn("Operation %s failed (attempt %d/%d), retrying in %v: %v",
			operation, attempt+1, h.maxRetries+1, delay, err)

		// Wait before retry
		select {
		case <-ctx.Done():
			return h.HandleError(operation, ctx.Err())
		case <-time.After(delay):
		}
	}

	// All retries exhausted
	return h.HandleError(operation, lastErr)
}

// calculateDelay calculates the delay for the given attempt
func (h *RetryableErrorHandler) calculateDelay(attempt int) time.Duration {
	// Exponential backoff: baseDelay * 2^attempt
	delay := h.baseDelay * time.Duration(1<<uint(attempt))

	// Cap at maxDelay
	if delay > h.maxDelay {
		delay = h.maxDelay
	}

	return delay
}

// CircuitBreakerErrorHandler handles errors with circuit breaker pattern
type CircuitBreakerErrorHandler struct {
	*ServiceErrorHandler
	failureThreshold int
	resetTimeout     time.Duration
	state            CircuitBreakerState
	failureCount     int
	lastFailureTime  time.Time
}

// CircuitBreakerState represents the state of the circuit breaker
type CircuitBreakerState int

const (
	CircuitBreakerClosed CircuitBreakerState = iota
	CircuitBreakerOpen
	CircuitBreakerHalfOpen
)

// NewCircuitBreakerErrorHandler creates a new circuit breaker error handler
func NewCircuitBreakerErrorHandler(serviceName string, failureThreshold int, resetTimeout time.Duration) *CircuitBreakerErrorHandler {
	return &CircuitBreakerErrorHandler{
		ServiceErrorHandler: NewServiceErrorHandler(serviceName),
		failureThreshold:    failureThreshold,
		resetTimeout:        resetTimeout,
		state:               CircuitBreakerClosed,
	}
}

// ExecuteWithCircuitBreaker executes an operation with circuit breaker protection
func (h *CircuitBreakerErrorHandler) ExecuteWithCircuitBreaker(ctx context.Context, operation string, fn func() error) error {
	// Check circuit breaker state
	if h.state == CircuitBreakerOpen {
		if time.Since(h.lastFailureTime) < h.resetTimeout {
			return h.HandleError(operation, errors.NewServiceError(h.serviceName, operation, errors.CodeUnavailable, "circuit breaker is open"))
		}
		// Move to half-open state
		h.state = CircuitBreakerHalfOpen
	}

	// Execute operation
	err := fn()

	if err != nil {
		h.onFailure(operation, err)
		return h.HandleError(operation, err)
	}

	h.onSuccess(operation)
	return nil
}

// onFailure handles operation failure
func (h *CircuitBreakerErrorHandler) onFailure(operation string, err error) {
	h.failureCount++
	h.lastFailureTime = time.Now()

	// Check if we should open the circuit
	if h.failureCount >= h.failureThreshold {
		h.state = CircuitBreakerOpen
		logger.Warn("Circuit breaker opened for %s:%s after %d failures", h.serviceName, operation, h.failureCount)
	}
}

// onSuccess handles operation success
func (h *CircuitBreakerErrorHandler) onSuccess(operation string) {
	if h.state == CircuitBreakerHalfOpen {
		// Move back to closed state
		h.state = CircuitBreakerClosed
		h.failureCount = 0
		logger.Info("Circuit breaker closed for %s:%s", h.serviceName, operation)
	} else if h.state == CircuitBreakerClosed {
		// Reset failure count on success
		h.failureCount = 0
	}
}

// GetState returns the current circuit breaker state
func (h *CircuitBreakerErrorHandler) GetState() CircuitBreakerState {
	return h.state
}

// Error aggregation and batching

// BatchErrorHandler handles multiple errors in batch operations
type BatchErrorHandler struct {
	*ServiceErrorHandler
	errors []*errors.ServiceError
}

// NewBatchErrorHandler creates a new batch error handler
func NewBatchErrorHandler(serviceName string) *BatchErrorHandler {
	return &BatchErrorHandler{
		ServiceErrorHandler: NewServiceErrorHandler(serviceName),
		errors:              make([]*errors.ServiceError, 0),
	}
}

// AddError adds an error to the batch
func (h *BatchErrorHandler) AddError(operation string, err error) {
	if err == nil {
		return
	}

	serviceErr := errors.GetServiceError(err)
	if serviceErr == nil {
		serviceErr = errors.WrapServiceError(err, h.serviceName, operation, errors.CodeInternal, "batch operation failed")
	}

	h.errors = append(h.errors, serviceErr)
}

// HasErrors returns true if there are any errors
func (h *BatchErrorHandler) HasErrors() bool {
	return len(h.errors) > 0
}

// GetErrors returns all errors
func (h *BatchErrorHandler) GetErrors() []*errors.ServiceError {
	return h.errors
}

// GetErrorGroup returns an error group
func (h *BatchErrorHandler) GetErrorGroup(operation string) *errors.ServiceErrorGroup {
	return errors.NewServiceErrorGroup(h.serviceName, operation, h.errors)
}

// Clear clears all errors
func (h *BatchErrorHandler) Clear() {
	h.errors = h.errors[:0]
}

// Error recovery and fallback

// FallbackErrorHandler provides fallback mechanisms for errors
type FallbackErrorHandler struct {
	*ServiceErrorHandler
	fallbackFunc func() error
}

// NewFallbackErrorHandler creates a new fallback error handler
func NewFallbackErrorHandler(serviceName string, fallbackFunc func() error) *FallbackErrorHandler {
	return &FallbackErrorHandler{
		ServiceErrorHandler: NewServiceErrorHandler(serviceName),
		fallbackFunc:        fallbackFunc,
	}
}

// ExecuteWithFallback executes an operation with fallback
func (h *FallbackErrorHandler) ExecuteWithFallback(ctx context.Context, operation string, fn func() error) error {
	// Try primary operation
	err := fn()
	if err == nil {
		return nil
	}

	// Log primary operation failure
	logger.Warn("Primary operation %s:%s failed, attempting fallback: %v", h.serviceName, operation, err)

	// Try fallback
	if h.fallbackFunc != nil {
		fallbackErr := h.fallbackFunc()
		if fallbackErr != nil {
			// Both primary and fallback failed
			return h.HandleError(operation, fmt.Errorf("primary operation failed: %w, fallback also failed: %w", err, fallbackErr))
		}

		// Fallback succeeded
		logger.Info("Fallback operation succeeded for %s:%s", h.serviceName, operation)
		return nil
	}

	// No fallback available
	return h.HandleError(operation, err)
}

// Error metrics and monitoring

// GetErrorMetrics returns error metrics for the service
func (h *ServiceErrorHandler) GetErrorMetrics() map[string]*errors.ServiceErrorMetrics {
	return h.errorTracker.GetAllMetrics()
}

// GetServiceMetrics returns metrics for this specific service
func (h *ServiceErrorHandler) GetServiceMetrics() map[string]*errors.ServiceErrorMetrics {
	metrics := make(map[string]*errors.ServiceErrorMetrics)
	allMetrics := h.errorTracker.GetAllMetrics()

	for key, metric := range allMetrics {
		if metric.Service == h.serviceName {
			metrics[key] = metric
		}
	}

	return metrics
}
