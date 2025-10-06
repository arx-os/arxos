package ifc

import (
	"context"
	"fmt"
	"time"
)

// IfcOpenShellClientInterface defines the interface for IfcOpenShell clients
type IfcOpenShellClientInterface interface {
	ParseIFC(ctx context.Context, data []byte) (*IFCResult, error)
	ValidateIFC(ctx context.Context, data []byte) (*ValidationResult, error)
	Health(ctx context.Context) (*HealthResult, error)
	IsAvailable(ctx context.Context) bool
	SpatialQuery(ctx context.Context, ifcData []byte, queryReq SpatialQueryRequest) (*SpatialQueryResult, error)
	SpatialBounds(ctx context.Context, ifcData []byte) (*SpatialBoundsResult, error)
	Metrics(ctx context.Context) (*MetricsResult, error)
}

// IFCService orchestrates IFC parsing with fallback mechanism
type IFCService struct {
	ifcOpenShellClient IfcOpenShellClientInterface
	nativeParser       *NativeParser
	serviceEnabled     bool
	fallbackEnabled    bool
	circuitBreaker     *CircuitBreaker
}

// CircuitBreaker implements a simple circuit breaker pattern
type CircuitBreaker struct {
	failureThreshold int
	recoveryTimeout  time.Duration
	state            CircuitState
	failures         int
	lastFailureTime  time.Time
}

// CircuitState represents the state of the circuit breaker
type CircuitState int

const (
	Closed CircuitState = iota
	Open
	HalfOpen
)

// NewIFCService creates a new IFC service with fallback mechanism
func NewIFCService(
	ifcOpenShellClient IfcOpenShellClientInterface,
	nativeParser *NativeParser,
	serviceEnabled bool,
	fallbackEnabled bool,
	failureThreshold int,
	recoveryTimeout time.Duration,
) *IFCService {
	return &IFCService{
		ifcOpenShellClient: ifcOpenShellClient,
		nativeParser:       nativeParser,
		serviceEnabled:     serviceEnabled,
		fallbackEnabled:    fallbackEnabled,
		circuitBreaker: &CircuitBreaker{
			failureThreshold: failureThreshold,
			recoveryTimeout:  recoveryTimeout,
			state:            Closed,
			failures:         0,
		},
	}
}

// ParseIFC parses an IFC file with fallback mechanism
func (s *IFCService) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
	// Try IfcOpenShell service first if enabled
	if s.serviceEnabled && s.ifcOpenShellClient != nil {
		result, err := s.tryIfcOpenShellService(ctx, data)
		if err == nil {
			return result, nil
		}

		// Log the error but continue to fallback
		// In a real implementation, you'd use a proper logger
		fmt.Printf("IfcOpenShell service failed, using fallback: %v\n", err)
	}

	// Fallback to native parser
	if s.fallbackEnabled && s.nativeParser != nil {
		return s.nativeParser.ParseIFC(ctx, data)
	}

	return nil, fmt.Errorf("no IFC parser available")
}

// ValidateIFC validates an IFC file with fallback mechanism
func (s *IFCService) ValidateIFC(ctx context.Context, data []byte) (*ValidationResult, error) {
	// Try IfcOpenShell service first if enabled
	if s.serviceEnabled && s.ifcOpenShellClient != nil {
		result, err := s.tryIfcOpenShellValidation(ctx, data)
		if err == nil {
			return result, nil
		}

		// Log the error but continue to fallback
		fmt.Printf("IfcOpenShell validation failed, using fallback: %v\n", err)
	}

	// Fallback to native parser
	if s.fallbackEnabled && s.nativeParser != nil {
		return s.nativeParser.ValidateIFC(ctx, data)
	}

	return nil, fmt.Errorf("no IFC validator available")
}

// tryIfcOpenShellService attempts to use the IfcOpenShell service
func (s *IFCService) tryIfcOpenShellService(ctx context.Context, data []byte) (*IFCResult, error) {
	// Check circuit breaker
	if s.circuitBreaker.state == Open {
		if time.Since(s.circuitBreaker.lastFailureTime) > s.circuitBreaker.recoveryTimeout {
			s.circuitBreaker.state = HalfOpen
		} else {
			return nil, fmt.Errorf("circuit breaker is open")
		}
	}

	// Call the service
	result, err := s.ifcOpenShellClient.ParseIFC(ctx, data)
	if err != nil {
		s.circuitBreaker.recordFailure()
		return nil, err
	}

	s.circuitBreaker.recordSuccess()
	return result, nil
}

// tryIfcOpenShellValidation attempts to use the IfcOpenShell service for validation
func (s *IFCService) tryIfcOpenShellValidation(ctx context.Context, data []byte) (*ValidationResult, error) {
	// Check circuit breaker
	if s.circuitBreaker.state == Open {
		if time.Since(s.circuitBreaker.lastFailureTime) > s.circuitBreaker.recoveryTimeout {
			s.circuitBreaker.state = HalfOpen
		} else {
			return nil, fmt.Errorf("circuit breaker is open")
		}
	}

	// Call the service
	result, err := s.ifcOpenShellClient.ValidateIFC(ctx, data)
	if err != nil {
		s.circuitBreaker.recordFailure()
		return nil, err
	}

	s.circuitBreaker.recordSuccess()
	return result, nil
}

// IsServiceAvailable checks if the IfcOpenShell service is available
func (s *IFCService) IsServiceAvailable(ctx context.Context) bool {
	if !s.serviceEnabled || s.ifcOpenShellClient == nil {
		return false
	}

	return s.ifcOpenShellClient.IsAvailable(ctx)
}

// GetServiceStatus returns the current status of the service
func (s *IFCService) GetServiceStatus(ctx context.Context) map[string]any {
	status := map[string]any{
		"service_enabled":          s.serviceEnabled,
		"fallback_enabled":         s.fallbackEnabled,
		"circuit_breaker_state":    s.circuitBreaker.state.String(),
		"circuit_breaker_failures": s.circuitBreaker.failures,
	}

	if s.serviceEnabled && s.ifcOpenShellClient != nil {
		available := s.ifcOpenShellClient.IsAvailable(ctx)
		status["service_available"] = available

		if available {
			health, err := s.ifcOpenShellClient.Health(ctx)
			if err == nil {
				status["service_version"] = health.Version
				status["service_status"] = health.Status
			}
		}
	}

	return status
}

// recordFailure records a failure in the circuit breaker
func (cb *CircuitBreaker) recordFailure() {
	cb.failures++
	cb.lastFailureTime = time.Now()

	if cb.failures >= cb.failureThreshold {
		cb.state = Open
	}
}

// recordSuccess records a success in the circuit breaker
func (cb *CircuitBreaker) recordSuccess() {
	cb.failures = 0
	cb.state = Closed
}

// String returns the string representation of the circuit state
func (cs CircuitState) String() string {
	switch cs {
	case Closed:
		return "closed"
	case Open:
		return "open"
	case HalfOpen:
		return "half-open"
	default:
		return "unknown"
	}
}
