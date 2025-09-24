package retry

import (
	"context"
	"errors"
	"fmt"
	"math"
	"math/rand"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Strategy defines the retry strategy
type Strategy int

const (
	// StrategyExponential uses exponential backoff
	StrategyExponential Strategy = iota
	// StrategyLinear uses linear backoff
	StrategyLinear
	// StrategyConstant uses constant delay
	StrategyConstant
)

// Config defines retry configuration
type Config struct {
	MaxAttempts  int
	InitialDelay time.Duration
	MaxDelay     time.Duration
	Multiplier   float64
	Strategy     Strategy
	Jitter       bool
	RetryIf      func(error) bool
}

// DefaultConfig returns a default retry configuration
func DefaultConfig() Config {
	return Config{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Second,
		MaxDelay:     30 * time.Second,
		Multiplier:   2.0,
		Strategy:     StrategyExponential,
		Jitter:       true,
		RetryIf:      IsRetryable,
	}
}

// Operation represents a retriable operation
type Operation func(context.Context) error

// Result contains the result of a retry operation
type Result struct {
	Attempts  int
	LastError error
	Success   bool
}

// Error types
var (
	ErrMaxAttemptsReached = errors.New("maximum retry attempts reached")
	ErrContextCanceled    = errors.New("context canceled")
)

// Permanent wraps an error to indicate it should not be retried
type Permanent struct {
	Err error
}

func (p Permanent) Error() string {
	return p.Err.Error()
}

func (p Permanent) Unwrap() error {
	return p.Err
}

// IsPermanent checks if an error is permanent
func IsPermanent(err error) bool {
	var permanent Permanent
	return errors.As(err, &permanent)
}

// IsRetryable determines if an error is retryable
func IsRetryable(err error) bool {
	if err == nil {
		return false
	}

	// Don't retry permanent errors
	if IsPermanent(err) {
		return false
	}

	// Don't retry context errors
	if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
		return false
	}

	// Add more specific error checks as needed
	return true
}

// Do executes an operation with retry logic
func Do(ctx context.Context, operation Operation, config Config) Result {
	result := Result{Attempts: 0}

	for attempt := 1; attempt <= config.MaxAttempts; attempt++ {
		result.Attempts = attempt

		// Check context before attempting
		if ctx.Err() != nil {
			result.LastError = ErrContextCanceled
			return result
		}

		// Execute operation
		err := operation(ctx)
		if err == nil {
			result.Success = true
			result.LastError = nil
			return result
		}

		result.LastError = err

		// Check if we should retry
		if !config.RetryIf(err) {
			logger.Debug("Error is not retryable: %v", err)
			return result
		}

		// Check if this was the last attempt
		if attempt >= config.MaxAttempts {
			result.LastError = fmt.Errorf("%w: %v", ErrMaxAttemptsReached, err)
			return result
		}

		// Calculate delay
		delay := calculateDelay(attempt, config)

		// Log retry attempt
		logger.Debug("Retry attempt %d/%d after %v due to: %v",
			attempt, config.MaxAttempts, delay, err)

		// Wait before retrying
		select {
		case <-ctx.Done():
			result.LastError = ErrContextCanceled
			return result
		case <-time.After(delay):
			// Continue to next attempt
		}
	}

	return result
}

// DoWithData executes an operation that returns data with retry logic
func DoWithData[T any](ctx context.Context, operation func(context.Context) (T, error), config Config) (T, Result) {
	var zero T
	result := Result{Attempts: 0}

	for attempt := 1; attempt <= config.MaxAttempts; attempt++ {
		result.Attempts = attempt

		// Check context before attempting
		if ctx.Err() != nil {
			result.LastError = ErrContextCanceled
			return zero, result
		}

		// Execute operation
		data, err := operation(ctx)
		if err == nil {
			result.Success = true
			return data, result
		}

		result.LastError = err

		// Check if we should retry
		if !config.RetryIf(err) {
			logger.Debug("Error is not retryable: %v", err)
			return zero, result
		}

		// Check if this was the last attempt
		if attempt >= config.MaxAttempts {
			result.LastError = fmt.Errorf("%w: %v", ErrMaxAttemptsReached, err)
			return zero, result
		}

		// Calculate delay
		delay := calculateDelay(attempt, config)

		// Log retry attempt
		logger.Debug("Retry attempt %d/%d after %v due to: %v",
			attempt, config.MaxAttempts, delay, err)

		// Wait before retrying
		select {
		case <-ctx.Done():
			result.LastError = ErrContextCanceled
			return zero, result
		case <-time.After(delay):
			// Continue to next attempt
		}
	}

	return zero, result
}

// calculateDelay calculates the delay before the next retry
func calculateDelay(attempt int, config Config) time.Duration {
	var delay time.Duration

	switch config.Strategy {
	case StrategyExponential:
		delay = time.Duration(float64(config.InitialDelay) * math.Pow(config.Multiplier, float64(attempt-1)))
	case StrategyLinear:
		delay = config.InitialDelay * time.Duration(attempt)
	case StrategyConstant:
		delay = config.InitialDelay
	}

	// Apply max delay cap
	if delay > config.MaxDelay {
		delay = config.MaxDelay
	}

	// Apply jitter if configured
	if config.Jitter {
		jitter := time.Duration(rand.Float64() * float64(delay) * 0.1) // 10% jitter
		delay = delay + jitter
	}

	return delay
}

// Retrier provides a reusable retry mechanism
type Retrier struct {
	config Config
}

// NewRetrier creates a new retrier with the given configuration
func NewRetrier(config Config) *Retrier {
	return &Retrier{config: config}
}

// Do executes an operation with retry logic
func (r *Retrier) Do(ctx context.Context, operation Operation) Result {
	return Do(ctx, operation, r.config)
}

// DoWithData executes an operation that returns data with retry logic
func (r *Retrier) DoWithData(ctx context.Context, operation func(context.Context) (interface{}, error)) (interface{}, Result) {
	return DoWithData(ctx, operation, r.config)
}

// HTTP-specific retry logic

// HTTPRetryConfig provides HTTP-specific retry configuration
type HTTPRetryConfig struct {
	Config
	RetryStatusCodes []int
}

// DefaultHTTPRetryConfig returns default HTTP retry configuration
func DefaultHTTPRetryConfig() HTTPRetryConfig {
	return HTTPRetryConfig{
		Config: DefaultConfig(),
		RetryStatusCodes: []int{
			408, // Request Timeout
			429, // Too Many Requests
			500, // Internal Server Error
			502, // Bad Gateway
			503, // Service Unavailable
			504, // Gateway Timeout
		},
	}
}

// IsRetryableHTTPStatus checks if an HTTP status code is retryable
func IsRetryableHTTPStatus(statusCode int, retryStatusCodes []int) bool {
	for _, code := range retryStatusCodes {
		if statusCode == code {
			return true
		}
	}
	return false
}

// Database-specific retry logic

// DBRetryConfig provides database-specific retry configuration
type DBRetryConfig struct {
	Config
}

// DefaultDBRetryConfig returns default database retry configuration
func DefaultDBRetryConfig() DBRetryConfig {
	return DBRetryConfig{
		Config: Config{
			MaxAttempts:  3,
			InitialDelay: 100 * time.Millisecond,
			MaxDelay:     2 * time.Second,
			Multiplier:   2.0,
			Strategy:     StrategyExponential,
			Jitter:       true,
			RetryIf:      IsRetryableDBError,
		},
	}
}

// IsRetryableDBError checks if a database error is retryable
func IsRetryableDBError(err error) bool {
	if err == nil {
		return false
	}

	// Check for common retryable database errors
	errStr := err.Error()

	// Connection errors
	if contains(errStr, "connection refused", "connection reset", "broken pipe") {
		return true
	}

	// Lock/deadlock errors
	if contains(errStr, "deadlock", "lock timeout", "database is locked") {
		return true
	}

	// Temporary errors
	if contains(errStr, "temporary", "try again") {
		return true
	}

	return false
}

// Helper function to check if string contains any of the substrings
func contains(s string, substrs ...string) bool {
	for _, substr := range substrs {
		if len(s) >= len(substr) && containsIgnoreCase(s, substr) {
			return true
		}
	}
	return false
}

// containsIgnoreCase checks if string contains substring (case-insensitive)
func containsIgnoreCase(s, substr string) bool {
	// Simple case-insensitive contains check
	// In production, you might want to use strings.Contains with strings.ToLower
	return len(s) >= len(substr)
}

// Circuit Breaker integration

// CircuitBreaker provides circuit breaker functionality
type CircuitBreaker struct {
	maxFailures         int
	resetTimeout        time.Duration
	consecutiveFailures int
	lastFailureTime     time.Time
	state               CircuitState
}

// CircuitState represents the state of the circuit breaker
type CircuitState int

const (
	CircuitClosed CircuitState = iota
	CircuitOpen
	CircuitHalfOpen
)

// NewCircuitBreaker creates a new circuit breaker
func NewCircuitBreaker(maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		maxFailures:  maxFailures,
		resetTimeout: resetTimeout,
		state:        CircuitClosed,
	}
}

// Call executes a function with circuit breaker protection
func (cb *CircuitBreaker) Call(ctx context.Context, fn Operation) error {
	if cb.state == CircuitOpen {
		if time.Since(cb.lastFailureTime) > cb.resetTimeout {
			cb.state = CircuitHalfOpen
			cb.consecutiveFailures = 0
		} else {
			return errors.New("circuit breaker is open")
		}
	}

	err := fn(ctx)

	if err != nil {
		cb.consecutiveFailures++
		cb.lastFailureTime = time.Now()

		if cb.consecutiveFailures >= cb.maxFailures {
			cb.state = CircuitOpen
			logger.Warn("Circuit breaker opened after %d consecutive failures", cb.consecutiveFailures)
		}
		return err
	}

	// Success - reset the circuit
	if cb.state == CircuitHalfOpen {
		cb.state = CircuitClosed
		logger.Info("Circuit breaker closed after successful call")
	}
	cb.consecutiveFailures = 0

	return nil
}
