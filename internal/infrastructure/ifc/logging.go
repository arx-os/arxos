package ifc

import (
	"context"
	"fmt"
	"log/slog"
	"strings"
	"time"
)

// Logger interface for IFC operations
type Logger interface {
	Info(msg string, args ...any)
	Warn(msg string, args ...any)
	Error(msg string, args ...any)
	Debug(msg string, args ...any)
}

// DefaultLogger provides a default logger implementation
type DefaultLogger struct {
	logger *slog.Logger
}

// NewDefaultLogger creates a new default logger
func NewDefaultLogger() *DefaultLogger {
	return &DefaultLogger{
		logger: slog.Default(),
	}
}

// Info logs an info message
func (l *DefaultLogger) Info(msg string, args ...any) {
	l.logger.Info(msg, args...)
}

// Warn logs a warning message
func (l *DefaultLogger) Warn(msg string, args ...any) {
	l.logger.Warn(msg, args...)
}

// Error logs an error message
func (l *DefaultLogger) Error(msg string, args ...any) {
	l.logger.Error(msg, args...)
}

// Debug logs a debug message
func (l *DefaultLogger) Debug(msg string, args ...any) {
	l.logger.Debug(msg, args...)
}

// Enhanced IFCService with logging
type EnhancedIFCService struct {
	*IFCService
	logger Logger
}

// NewEnhancedIFCService creates a new enhanced IFC service with logging
func NewEnhancedIFCService(
	ifcOpenShellClient *IfcOpenShellClient,
	nativeParser *NativeParser,
	serviceEnabled bool,
	fallbackEnabled bool,
	failureThreshold int,
	recoveryTimeout time.Duration,
	logger Logger,
) *EnhancedIFCService {
	return &EnhancedIFCService{
		IFCService: NewIFCService(ifcOpenShellClient, nativeParser, serviceEnabled, fallbackEnabled, failureThreshold, recoveryTimeout),
		logger:     logger,
	}
}

// ParseIFC parses an IFC file with enhanced logging
func (s *EnhancedIFCService) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
	s.logger.Info("Starting IFC parsing", "data_size", len(data))

	startTime := time.Now()

	// Try IfcOpenShell service first if enabled
	if s.serviceEnabled && s.ifcOpenShellClient != nil {
		s.logger.Debug("Attempting to parse with IfcOpenShell service")

		result, err := s.tryIfcOpenShellService(ctx, data)
		if err == nil {
			duration := time.Since(startTime)
			s.logger.Info("Successfully parsed IFC with IfcOpenShell service",
				"duration", duration.String(),
				"buildings", result.Buildings,
				"spaces", result.Spaces,
				"equipment", result.Equipment)
			return result, nil
		}

		s.logger.Warn("IfcOpenShell service failed, using fallback", "error", err)
	}

	// Fallback to native parser
	if s.fallbackEnabled && s.nativeParser != nil {
		s.logger.Debug("Attempting to parse with native parser")

		result, err := s.nativeParser.ParseIFC(ctx, data)
		if err != nil {
			duration := time.Since(startTime)
			s.logger.Error("Native parser failed", "error", err, "duration", duration.String())
			return nil, fmt.Errorf("native parser failed: %w", err)
		}

		duration := time.Since(startTime)
		s.logger.Info("Successfully parsed IFC with native parser",
			"duration", duration.String(),
			"buildings", result.Buildings,
			"spaces", result.Spaces,
			"equipment", result.Equipment)
		return result, nil
	}

	s.logger.Error("No IFC parser available")
	return nil, fmt.Errorf("no IFC parser available")
}

// ValidateIFC validates an IFC file with enhanced logging
func (s *EnhancedIFCService) ValidateIFC(ctx context.Context, data []byte) (*ValidationResult, error) {
	s.logger.Info("Starting IFC validation", "data_size", len(data))

	startTime := time.Now()

	// Try IfcOpenShell service first if enabled
	if s.serviceEnabled && s.ifcOpenShellClient != nil {
		s.logger.Debug("Attempting to validate with IfcOpenShell service")

		result, err := s.tryIfcOpenShellValidation(ctx, data)
		if err == nil {
			duration := time.Since(startTime)
			s.logger.Info("Successfully validated IFC with IfcOpenShell service",
				"duration", duration.String(),
				"valid", result.Valid,
				"warnings", len(result.Warnings),
				"errors", len(result.Errors))
			return result, nil
		}

		s.logger.Warn("IfcOpenShell validation failed, using fallback", "error", err)
	}

	// Fallback to native parser
	if s.fallbackEnabled && s.nativeParser != nil {
		s.logger.Debug("Attempting to validate with native parser")

		result, err := s.nativeParser.ValidateIFC(ctx, data)
		if err != nil {
			duration := time.Since(startTime)
			s.logger.Error("Native validator failed", "error", err, "duration", duration.String())
			return nil, fmt.Errorf("native validator failed: %w", err)
		}

		duration := time.Since(startTime)
		s.logger.Info("Successfully validated IFC with native parser",
			"duration", duration.String(),
			"valid", result.Valid,
			"warnings", len(result.Warnings),
			"errors", len(result.Errors))
		return result, nil
	}

	s.logger.Error("No IFC validator available")
	return nil, fmt.Errorf("no IFC validator available")
}

// tryIfcOpenShellService attempts to use the IfcOpenShell service with logging
func (s *EnhancedIFCService) tryIfcOpenShellService(ctx context.Context, data []byte) (*IFCResult, error) {
	// Check circuit breaker
	if s.circuitBreaker.state == Open {
		if time.Since(s.circuitBreaker.lastFailureTime) > s.circuitBreaker.recoveryTimeout {
			s.circuitBreaker.state = HalfOpen
			s.logger.Info("Circuit breaker transitioning to half-open state")
		} else {
			s.logger.Warn("Circuit breaker is open, skipping IfcOpenShell service")
			return nil, fmt.Errorf("circuit breaker is open")
		}
	}

	// Call the service
	s.logger.Debug("Calling IfcOpenShell service")
	result, err := s.ifcOpenShellClient.ParseIFC(ctx, data)
	if err != nil {
		s.circuitBreaker.recordFailure()
		s.logger.Error("IfcOpenShell service call failed", "error", err, "failures", s.circuitBreaker.failures)
		return nil, err
	}

	s.circuitBreaker.recordSuccess()
	s.logger.Debug("IfcOpenShell service call successful")
	return result, nil
}

// tryIfcOpenShellValidation attempts to use the IfcOpenShell service for validation with logging
func (s *EnhancedIFCService) tryIfcOpenShellValidation(ctx context.Context, data []byte) (*ValidationResult, error) {
	// Check circuit breaker
	if s.circuitBreaker.state == Open {
		if time.Since(s.circuitBreaker.lastFailureTime) > s.circuitBreaker.recoveryTimeout {
			s.circuitBreaker.state = HalfOpen
			s.logger.Info("Circuit breaker transitioning to half-open state")
		} else {
			s.logger.Warn("Circuit breaker is open, skipping IfcOpenShell validation")
			return nil, fmt.Errorf("circuit breaker is open")
		}
	}

	// Call the service
	s.logger.Debug("Calling IfcOpenShell validation service")
	result, err := s.ifcOpenShellClient.ValidateIFC(ctx, data)
	if err != nil {
		s.circuitBreaker.recordFailure()
		s.logger.Error("IfcOpenShell validation service call failed", "error", err, "failures", s.circuitBreaker.failures)
		return nil, err
	}

	s.circuitBreaker.recordSuccess()
	s.logger.Debug("IfcOpenShell validation service call successful")
	return result, nil
}

// GetServiceStatus returns the current status of the service with logging
func (s *EnhancedIFCService) GetServiceStatus(ctx context.Context) map[string]interface{} {
	s.logger.Debug("Getting service status")

	status := s.IFCService.GetServiceStatus(ctx)

	// Add logging-specific information
	status["logger_enabled"] = s.logger != nil
	status["circuit_breaker_failures"] = s.circuitBreaker.failures
	status["circuit_breaker_last_failure"] = s.circuitBreaker.lastFailureTime.Format(time.RFC3339)

	s.logger.Debug("Service status retrieved", "status", status)
	return status
}

// GetIFCErrorCode returns the error code if it's an IFC error
func GetIFCErrorCode(err error) string {
	// Check if it's an IFCError by checking the error message format
	if err != nil && strings.Contains(err.Error(), ":") {
		parts := strings.Split(err.Error(), ":")
		if len(parts) >= 2 {
			return strings.TrimSpace(parts[0])
		}
	}
	return "INTERNAL_ERROR"
}
