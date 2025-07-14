package gateway

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.uber.org/zap"
)

// CircuitBreaker implements the circuit breaker pattern
type CircuitBreaker struct {
	name             string
	failureThreshold int
	timeout          time.Duration
	resetTimeout     time.Duration
	monitorInterval  time.Duration
	state            CircuitState
	failures         int
	lastFailure      time.Time
	lastSuccess      time.Time
	mu               sync.RWMutex
	logger           *zap.Logger
	metrics          *CircuitBreakerMetrics
}

// CircuitState represents the circuit breaker state
type CircuitState string

const (
	CircuitStateClosed   CircuitState = "closed"
	CircuitStateOpen     CircuitState = "open"
	CircuitStateHalfOpen CircuitState = "half-open"
)

// CircuitBreakerMetrics holds circuit breaker metrics
type CircuitBreakerMetrics struct {
	stateGauge      *prometheus.GaugeVec
	failuresCounter *prometheus.CounterVec
	successCounter  *prometheus.CounterVec
	timeoutCounter  *prometheus.CounterVec
}

// CircuitBreakerConfig defines circuit breaker configuration
type CircuitBreakerConfig struct {
	Name             string        `yaml:"name"`
	FailureThreshold int           `yaml:"failure_threshold"`
	Timeout          time.Duration `yaml:"timeout"`
	ResetTimeout     time.Duration `yaml:"reset_timeout"`
	MonitorInterval  time.Duration `yaml:"monitor_interval"`
	Enabled          bool          `yaml:"enabled"`
}

// CircuitBreakerResult represents the result of a circuit breaker operation
type CircuitBreakerResult struct {
	Success  bool
	Error    error
	State    CircuitState
	Duration time.Duration
}

// NewCircuitBreaker creates a new circuit breaker
func NewCircuitBreaker(config CircuitBreakerConfig) (*CircuitBreaker, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	cb := &CircuitBreaker{
		name:             config.Name,
		failureThreshold: config.FailureThreshold,
		timeout:          config.Timeout,
		resetTimeout:     config.ResetTimeout,
		monitorInterval:  config.MonitorInterval,
		state:            CircuitStateClosed,
		failures:         0,
		logger:           logger,
	}

	// Initialize metrics
	cb.initializeMetrics()

	// Start monitoring goroutine
	if config.Enabled {
		go cb.monitor()
	}

	return cb, nil
}

// initializeMetrics initializes circuit breaker metrics
func (cb *CircuitBreaker) initializeMetrics() {
	cb.metrics = &CircuitBreakerMetrics{
		stateGauge: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_circuit_breaker_state",
				Help: "Circuit breaker state (0=closed, 1=half-open, 2=open)",
			},
			[]string{"service"},
		),
		failuresCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_circuit_breaker_failures_total",
				Help: "Total circuit breaker failures",
			},
			[]string{"service"},
		),
		successCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_circuit_breaker_success_total",
				Help: "Total circuit breaker successes",
			},
			[]string{"service"},
		),
		timeoutCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_circuit_breaker_timeouts_total",
				Help: "Total circuit breaker timeouts",
			},
			[]string{"service"},
		),
	}
}

// Execute executes a function with circuit breaker protection
func (cb *CircuitBreaker) Execute(ctx context.Context, fn func() error) error {
	start := time.Now()

	// Check circuit breaker state
	state := cb.getState()
	switch state {
	case CircuitStateOpen:
		return fmt.Errorf("circuit breaker is open for service %s", cb.name)
	case CircuitStateHalfOpen:
		// Allow limited requests in half-open state
		if cb.shouldAllowRequest() {
			return cb.executeWithTimeout(ctx, fn)
		}
		return fmt.Errorf("circuit breaker is half-open, request rejected for service %s", cb.name)
	case CircuitStateClosed:
		return cb.executeWithTimeout(ctx, fn)
	default:
		return fmt.Errorf("unknown circuit breaker state: %s", state)
	}
}

// executeWithTimeout executes a function with timeout and circuit breaker logic
func (cb *CircuitBreaker) executeWithTimeout(ctx context.Context, fn func() error) error {
	start := time.Now()

	// Create timeout context
	timeoutCtx, cancel := context.WithTimeout(ctx, cb.timeout)
	defer cancel()

	// Execute function
	err := fn()
	duration := time.Since(start)

	// Record result
	cb.recordResult(err, duration)

	return err
}

// recordResult records the result of an operation
func (cb *CircuitBreaker) recordResult(err error, duration time.Duration) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		// Record failure
		cb.failures++
		cb.lastFailure = time.Now()
		cb.metrics.failuresCounter.WithLabelValues(cb.name).Inc()

		cb.logger.Warn("Circuit breaker failure",
			zap.String("service", cb.name),
			zap.Error(err),
			zap.Int("failures", cb.failures),
			zap.Duration("duration", duration),
		)

		// Check if we should open the circuit
		if cb.failures >= cb.failureThreshold {
			cb.openCircuit()
		}
	} else {
		// Record success
		cb.failures = 0
		cb.lastSuccess = time.Now()
		cb.metrics.successCounter.WithLabelValues(cb.name).Inc()

		cb.logger.Info("Circuit breaker success",
			zap.String("service", cb.name),
			zap.Duration("duration", duration),
		)

		// If we're in half-open state, close the circuit
		if cb.state == CircuitStateHalfOpen {
			cb.closeCircuit()
		}
	}
}

// openCircuit opens the circuit breaker
func (cb *CircuitBreaker) openCircuit() {
	if cb.state != CircuitStateOpen {
		cb.state = CircuitStateOpen
		cb.metrics.stateGauge.WithLabelValues(cb.name).Set(2.0) // Open state

		cb.logger.Warn("Circuit breaker opened",
			zap.String("service", cb.name),
			zap.Int("failures", cb.failures),
		)

		// Schedule transition to half-open state
		time.AfterFunc(cb.resetTimeout, func() {
			cb.transitionToHalfOpen()
		})
	}
}

// closeCircuit closes the circuit breaker
func (cb *CircuitBreaker) closeCircuit() {
	if cb.state != CircuitStateClosed {
		cb.state = CircuitStateClosed
		cb.metrics.stateGauge.WithLabelValues(cb.name).Set(0.0) // Closed state

		cb.logger.Info("Circuit breaker closed",
			zap.String("service", cb.name),
		)
	}
}

// transitionToHalfOpen transitions the circuit breaker to half-open state
func (cb *CircuitBreaker) transitionToHalfOpen() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if cb.state == CircuitStateOpen {
		cb.state = CircuitStateHalfOpen
		cb.metrics.stateGauge.WithLabelValues(cb.name).Set(1.0) // Half-open state

		cb.logger.Info("Circuit breaker transitioned to half-open",
			zap.String("service", cb.name),
		)
	}
}

// shouldAllowRequest determines if a request should be allowed in half-open state
func (cb *CircuitBreaker) shouldAllowRequest() bool {
	// In half-open state, allow only a small percentage of requests
	// This is a simplified implementation - in production, you might use a more sophisticated algorithm
	return time.Since(cb.lastFailure) > cb.resetTimeout/2
}

// getState gets the current circuit breaker state
func (cb *CircuitBreaker) getState() CircuitState {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state
}

// GetStatus returns the circuit breaker status
func (cb *CircuitBreaker) GetStatus() map[string]interface{} {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	return map[string]interface{}{
		"name":              cb.name,
		"state":             cb.state,
		"failures":          cb.failures,
		"failure_threshold": cb.failureThreshold,
		"last_failure":      cb.lastFailure,
		"last_success":      cb.lastSuccess,
		"timeout":           cb.timeout,
		"reset_timeout":     cb.resetTimeout,
	}
}

// ForceOpen forces the circuit breaker to open state
func (cb *CircuitBreaker) ForceOpen() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.state = CircuitStateOpen
	cb.metrics.stateGauge.WithLabelValues(cb.name).Set(2.0)

	cb.logger.Warn("Circuit breaker forced open",
		zap.String("service", cb.name),
	)
}

// ForceClose forces the circuit breaker to closed state
func (cb *CircuitBreaker) ForceClose() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.state = CircuitStateClosed
	cb.failures = 0
	cb.metrics.stateGauge.WithLabelValues(cb.name).Set(0.0)

	cb.logger.Info("Circuit breaker forced closed",
		zap.String("service", cb.name),
	)
}

// Reset resets the circuit breaker to initial state
func (cb *CircuitBreaker) Reset() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.state = CircuitStateClosed
	cb.failures = 0
	cb.lastFailure = time.Time{}
	cb.lastSuccess = time.Time{}
	cb.metrics.stateGauge.WithLabelValues(cb.name).Set(0.0)

	cb.logger.Info("Circuit breaker reset",
		zap.String("service", cb.name),
	)
}

// monitor monitors the circuit breaker state
func (cb *CircuitBreaker) monitor() {
	ticker := time.NewTicker(cb.monitorInterval)
	defer ticker.Stop()

	for range ticker.C {
		cb.checkHealth()
	}
}

// checkHealth checks the health of the circuit breaker
func (cb *CircuitBreaker) checkHealth() {
	status := cb.GetStatus()

	cb.logger.Debug("Circuit breaker health check",
		zap.String("service", cb.name),
		zap.String("state", string(status["state"].(CircuitState))),
		zap.Int("failures", status["failures"].(int)),
	)
}

// CircuitBreakerManager manages multiple circuit breakers
type CircuitBreakerManager struct {
	breakers map[string]*CircuitBreaker
	mu       sync.RWMutex
	logger   *zap.Logger
}

// NewCircuitBreakerManager creates a new circuit breaker manager
func NewCircuitBreakerManager() (*CircuitBreakerManager, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	manager := &CircuitBreakerManager{
		breakers: make(map[string]*CircuitBreaker),
		logger:   logger,
	}

	return manager, nil
}

// GetCircuitBreaker gets or creates a circuit breaker for a service
func (cbm *CircuitBreakerManager) GetCircuitBreaker(serviceName string, config CircuitBreakerConfig) (*CircuitBreaker, error) {
	cbm.mu.Lock()
	defer cbm.mu.Unlock()

	if breaker, exists := cbm.breakers[serviceName]; exists {
		return breaker, nil
	}

	config.Name = serviceName
	breaker, err := NewCircuitBreaker(config)
	if err != nil {
		return nil, err
	}

	cbm.breakers[serviceName] = breaker
	return breaker, nil
}

// GetStatus returns the status of all circuit breakers
func (cbm *CircuitBreakerManager) GetStatus() map[string]interface{} {
	cbm.mu.RLock()
	defer cbm.mu.RUnlock()

	status := make(map[string]interface{})
	for name, breaker := range cbm.breakers {
		status[name] = breaker.GetStatus()
	}

	return status
}

// ResetAll resets all circuit breakers
func (cbm *CircuitBreakerManager) ResetAll() {
	cbm.mu.Lock()
	defer cbm.mu.Unlock()

	for _, breaker := range cbm.breakers {
		breaker.Reset()
	}

	cbm.logger.Info("All circuit breakers reset")
}
