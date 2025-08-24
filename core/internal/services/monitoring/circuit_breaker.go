package monitoring

import (
	"fmt"
	"sync"
	"time"
)

// CircuitState represents the current state of a circuit breaker
type CircuitState int

const (
	// StateClosed - circuit is closed, allowing requests through
	StateClosed CircuitState = iota
	// StateHalfOpen - circuit is testing if service has recovered
	StateHalfOpen
	// StateOpen - circuit is open, blocking requests
	StateOpen
)

// String returns the string representation of the circuit state
func (s CircuitState) String() string {
	switch s {
	case StateClosed:
		return "CLOSED"
	case StateHalfOpen:
		return "HALF_OPEN"
	case StateOpen:
		return "OPEN"
	default:
		return "UNKNOWN"
	}
}

// CircuitBreakerConfig contains configuration for a circuit breaker
type CircuitBreakerConfig struct {
	MaxFailures     int           `json:"max_failures"`      // Number of failures before opening
	Timeout         time.Duration `json:"timeout"`           // Time to wait before trying half-open
	MaxRequests     int           `json:"max_requests"`      // Max requests in half-open state
	SuccessThreshold int          `json:"success_threshold"` // Successes needed to close from half-open
	OnStateChange   func(name string, from CircuitState, to CircuitState) // Callback for state changes
}

// DefaultCircuitBreakerConfig returns default configuration
func DefaultCircuitBreakerConfig() *CircuitBreakerConfig {
	return &CircuitBreakerConfig{
		MaxFailures:      5,
		Timeout:          30 * time.Second,
		MaxRequests:      3,
		SuccessThreshold: 2,
		OnStateChange:    nil,
	}
}

// CircuitBreaker implements the circuit breaker pattern
type CircuitBreaker struct {
	name           string
	config         *CircuitBreakerConfig
	state          CircuitState
	failures       int
	successes      int
	requests       int
	lastFailureTime time.Time
	mutex          sync.RWMutex
}

// NewCircuitBreaker creates a new circuit breaker
func NewCircuitBreaker(name string, config *CircuitBreakerConfig) *CircuitBreaker {
	if config == nil {
		config = DefaultCircuitBreakerConfig()
	}

	return &CircuitBreaker{
		name:   name,
		config: config,
		state:  StateClosed,
	}
}

// CircuitBreakerError represents an error from a circuit breaker
type CircuitBreakerError struct {
	CircuitName string        `json:"circuit_name"`
	State       CircuitState  `json:"state"`
	Message     string        `json:"message"`
	RetryAfter  time.Duration `json:"retry_after,omitempty"`
}

// Error implements the error interface
func (e *CircuitBreakerError) Error() string {
	return fmt.Sprintf("circuit breaker '%s' is %s: %s", e.CircuitName, e.State.String(), e.Message)
}

// Execute runs a function through the circuit breaker
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mutex.Lock()
	defer cb.mutex.Unlock()

	// Check if circuit is open
	if cb.state == StateOpen {
		if time.Since(cb.lastFailureTime) < cb.config.Timeout {
			return &CircuitBreakerError{
				CircuitName: cb.name,
				State:       StateOpen,
				Message:     "circuit breaker is open",
				RetryAfter:  cb.config.Timeout - time.Since(cb.lastFailureTime),
			}
		}
		// Transition to half-open
		cb.transitionTo(StateHalfOpen)
		cb.requests = 0
		cb.successes = 0
	}

	// Check if we're in half-open and have exceeded max requests
	if cb.state == StateHalfOpen && cb.requests >= cb.config.MaxRequests {
		return &CircuitBreakerError{
			CircuitName: cb.name,
			State:       StateHalfOpen,
			Message:     "circuit breaker in half-open state has reached max requests",
		}
	}

	// Increment request counter for half-open state
	if cb.state == StateHalfOpen {
		cb.requests++
	}

	// Execute the function
	err := fn()

	if err != nil {
		cb.onFailure()
		return err
	}

	cb.onSuccess()
	return nil
}

// onSuccess handles successful execution
func (cb *CircuitBreaker) onSuccess() {
	switch cb.state {
	case StateClosed:
		cb.failures = 0
	case StateHalfOpen:
		cb.successes++
		if cb.successes >= cb.config.SuccessThreshold {
			cb.transitionTo(StateClosed)
			cb.failures = 0
			cb.successes = 0
			cb.requests = 0
		}
	}
}

// onFailure handles failed execution
func (cb *CircuitBreaker) onFailure() {
	cb.failures++
	cb.lastFailureTime = time.Now()

	switch cb.state {
	case StateClosed:
		if cb.failures >= cb.config.MaxFailures {
			cb.transitionTo(StateOpen)
		}
	case StateHalfOpen:
		cb.transitionTo(StateOpen)
		cb.requests = 0
		cb.successes = 0
	}
}

// transitionTo changes the circuit breaker state
func (cb *CircuitBreaker) transitionTo(newState CircuitState) {
	if cb.state == newState {
		return
	}

	oldState := cb.state
	cb.state = newState

	// Call state change callback if configured
	if cb.config.OnStateChange != nil {
		cb.config.OnStateChange(cb.name, oldState, newState)
	}
}

// GetState returns the current state of the circuit breaker
func (cb *CircuitBreaker) GetState() CircuitState {
	cb.mutex.RLock()
	defer cb.mutex.RUnlock()
	return cb.state
}

// GetStats returns statistics about the circuit breaker
func (cb *CircuitBreaker) GetStats() CircuitBreakerStats {
	cb.mutex.RLock()
	defer cb.mutex.RUnlock()

	return CircuitBreakerStats{
		Name:            cb.name,
		State:           cb.state,
		Failures:        cb.failures,
		Successes:       cb.successes,
		Requests:        cb.requests,
		LastFailureTime: cb.lastFailureTime,
	}
}

// CircuitBreakerStats contains statistics about a circuit breaker
type CircuitBreakerStats struct {
	Name            string        `json:"name"`
	State           CircuitState  `json:"state"`
	Failures        int           `json:"failures"`
	Successes       int           `json:"successes"`
	Requests        int           `json:"requests"`
	LastFailureTime time.Time     `json:"last_failure_time"`
}

// Reset manually resets the circuit breaker to closed state
func (cb *CircuitBreaker) Reset() {
	cb.mutex.Lock()
	defer cb.mutex.Unlock()

	cb.transitionTo(StateClosed)
	cb.failures = 0
	cb.successes = 0
	cb.requests = 0
	cb.lastFailureTime = time.Time{}
}

// CircuitBreakerManager manages multiple circuit breakers
type CircuitBreakerManager struct {
	breakers map[string]*CircuitBreaker
	mutex    sync.RWMutex
}

// NewCircuitBreakerManager creates a new circuit breaker manager
func NewCircuitBreakerManager() *CircuitBreakerManager {
	return &CircuitBreakerManager{
		breakers: make(map[string]*CircuitBreaker),
	}
}

// GetOrCreate gets an existing circuit breaker or creates a new one
func (cbm *CircuitBreakerManager) GetOrCreate(name string, config *CircuitBreakerConfig) *CircuitBreaker {
	cbm.mutex.Lock()
	defer cbm.mutex.Unlock()

	if breaker, exists := cbm.breakers[name]; exists {
		return breaker
	}

	breaker := NewCircuitBreaker(name, config)
	cbm.breakers[name] = breaker
	return breaker
}

// Get retrieves a circuit breaker by name
func (cbm *CircuitBreakerManager) Get(name string) (*CircuitBreaker, bool) {
	cbm.mutex.RLock()
	defer cbm.mutex.RUnlock()

	breaker, exists := cbm.breakers[name]
	return breaker, exists
}

// GetAll returns all circuit breaker statistics
func (cbm *CircuitBreakerManager) GetAll() map[string]CircuitBreakerStats {
	cbm.mutex.RLock()
	defer cbm.mutex.RUnlock()

	stats := make(map[string]CircuitBreakerStats)
	for name, breaker := range cbm.breakers {
		stats[name] = breaker.GetStats()
	}
	return stats
}

// Reset resets a specific circuit breaker
func (cbm *CircuitBreakerManager) Reset(name string) error {
	cbm.mutex.RLock()
	breaker, exists := cbm.breakers[name]
	cbm.mutex.RUnlock()

	if !exists {
		return fmt.Errorf("circuit breaker '%s' not found", name)
	}

	breaker.Reset()
	return nil
}

// ResetAll resets all circuit breakers
func (cbm *CircuitBreakerManager) ResetAll() {
	cbm.mutex.RLock()
	defer cbm.mutex.RUnlock()

	for _, breaker := range cbm.breakers {
		breaker.Reset()
	}
}

// Global circuit breaker manager instance
var globalCircuitBreakerManager = NewCircuitBreakerManager()

// GetCircuitBreaker is a convenience function to get a circuit breaker from the global manager
func GetCircuitBreaker(name string, config *CircuitBreakerConfig) *CircuitBreaker {
	return globalCircuitBreakerManager.GetOrCreate(name, config)
}

// GetAllCircuitBreakers returns all circuit breaker statistics from the global manager
func GetAllCircuitBreakers() map[string]CircuitBreakerStats {
	return globalCircuitBreakerManager.GetAll()
}

// ResetCircuitBreaker resets a specific circuit breaker in the global manager
func ResetCircuitBreaker(name string) error {
	return globalCircuitBreakerManager.Reset(name)
}