package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/metrics"
	"github.com/arx-os/arxos/pkg/models"
)

// ExampleUserServiceWithMetrics demonstrates how to integrate comprehensive metrics
type ExampleUserServiceWithMetrics struct {
	instrumentation *metrics.Instrumentation
	metrics         *metrics.ServiceMetrics
	// ... other fields
}

// NewExampleUserServiceWithMetrics creates a new user service with comprehensive metrics
func NewExampleUserServiceWithMetrics() *ExampleUserServiceWithMetrics {
	serviceName := "user-service"

	return &ExampleUserServiceWithMetrics{
		instrumentation: metrics.GetInstrumentation(serviceName),
		metrics:         metrics.GetServiceMetrics(serviceName),
	}
}

// CreateUser demonstrates comprehensive metrics integration for user creation
func (s *ExampleUserServiceWithMetrics) CreateUser(ctx context.Context, req *models.UserCreateRequest) (*models.User, error) {
	// Start operation tracking with instrumentation
	labels := map[string]string{
		"operation": "create_user",
		"user_type": req.Role,
	}

	tracker := s.instrumentation.StartOperation(ctx, "create_user", labels)
	defer func() {
		if r := recover(); r != nil {
			s.instrumentation.CompleteOperationWithError(tracker, fmt.Errorf("panic: %v", r))
			panic(r)
		}
	}()

	// Validate input
	if err := s.validateUserRequest(req); err != nil {
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return nil, err
	}

	// Check if user already exists
	existingUser, err := s.getUserByEmail(ctx, req.Email)
	if err != nil {
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return nil, err
	}

	if existingUser != nil {
		conflictErr := fmt.Errorf("user with email %s already exists", req.Email)
		s.instrumentation.CompleteOperationWithError(tracker, conflictErr)
		return nil, conflictErr
	}

	// Create user with retry logic and metrics
	user, err := s.createUserWithRetryAndMetrics(ctx, req, tracker)
	if err != nil {
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return nil, err
	}

	// Complete operation successfully
	s.instrumentation.CompleteOperation(tracker)
	return user, nil
}

// GetUser demonstrates metrics integration for user retrieval
func (s *ExampleUserServiceWithMetrics) GetUser(ctx context.Context, userID string) (*models.User, error) {
	// Start operation tracking
	labels := map[string]string{
		"operation": "get_user",
		"user_id":   userID,
	}

	tracker := s.instrumentation.StartOperation(ctx, "get_user", labels)
	defer func() {
		if r := recover(); r != nil {
			s.instrumentation.CompleteOperationWithError(tracker, fmt.Errorf("panic: %v", r))
			panic(r)
		}
	}()

	// Validate input
	if userID == "" {
		err := fmt.Errorf("user ID cannot be empty")
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return nil, err
	}

	// Get user from database
	user, err := s.getUserFromDatabase(ctx, userID)
	if err != nil {
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return nil, err
	}

	if user == nil {
		err := fmt.Errorf("user with ID %s not found", userID)
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return nil, err
	}

	// Complete operation successfully
	s.instrumentation.CompleteOperation(tracker)
	return user, nil
}

// BatchCreateUsers demonstrates batch operation metrics
func (s *ExampleUserServiceWithMetrics) BatchCreateUsers(ctx context.Context, requests []*models.UserCreateRequest) ([]*models.User, []error) {
	// Start batch operation tracking
	labels := map[string]string{
		"operation":  "batch_create_users",
		"batch_size": fmt.Sprintf("%d", len(requests)),
	}

	tracker := s.instrumentation.StartOperation(ctx, "batch_create_users", labels)
	defer func() {
		if r := recover(); r != nil {
			s.instrumentation.CompleteOperationWithError(tracker, fmt.Errorf("panic: %v", r))
			panic(r)
		}
	}()

	// Record batch operation metrics
	s.metrics.RecordBatchOperation("batch_create_users", len(requests))

	var users []*models.User
	var userErrors []error

	// Process each user creation request
	for i, req := range requests {
		user, err := s.CreateUser(ctx, req)
		if err != nil {
			userErrors = append(userErrors, err)
			// Record individual error metrics
			s.metrics.StartOperation(fmt.Sprintf("batch_create_user_%d", i)).CompleteOperationWithError(err)
		} else {
			users = append(users, user)
			// Record individual success metrics
			s.metrics.StartOperation(fmt.Sprintf("batch_create_user_%d", i)).CompleteOperation()
		}
	}

	// Complete batch operation
	if len(userErrors) > 0 {
		s.instrumentation.CompleteOperationWithError(tracker, fmt.Errorf("batch operation completed with %d errors", len(userErrors)))
	} else {
		s.instrumentation.CompleteOperation(tracker)
	}

	return users, userErrors
}

// UpdateUser demonstrates circuit breaker and fallback metrics
func (s *ExampleUserServiceWithMetrics) UpdateUser(ctx context.Context, userID string, updates *models.UserUpdateRequest) (*models.User, error) {
	// Start operation tracking
	labels := map[string]string{
		"operation": "update_user",
		"user_id":   userID,
	}

	tracker := s.instrumentation.StartOperation(ctx, "update_user", labels)
	defer func() {
		if r := recover(); r != nil {
			s.instrumentation.CompleteOperationWithError(tracker, fmt.Errorf("panic: %v", r))
			panic(r)
		}
	}()

	// Get existing user
	user, err := s.GetUser(ctx, userID)
	if err != nil {
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return nil, err
	}

	// Apply updates with circuit breaker protection
	updatedUser, err := s.applyUserUpdatesWithCircuitBreaker(ctx, user, updates, tracker)
	if err != nil {
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return nil, err
	}

	// Complete operation successfully
	s.instrumentation.CompleteOperation(tracker)
	return updatedUser, nil
}

// DeleteUser demonstrates retry and fallback metrics
func (s *ExampleUserServiceWithMetrics) DeleteUser(ctx context.Context, userID string) error {
	// Start operation tracking
	labels := map[string]string{
		"operation": "delete_user",
		"user_id":   userID,
	}

	tracker := s.instrumentation.StartOperation(ctx, "delete_user", labels)
	defer func() {
		if r := recover(); r != nil {
			s.instrumentation.CompleteOperationWithError(tracker, fmt.Errorf("panic: %v", r))
			panic(r)
		}
	}()

	// Delete user with retry logic
	err := s.deleteUserWithRetryAndMetrics(ctx, userID, tracker)
	if err != nil {
		s.instrumentation.CompleteOperationWithError(tracker, err)
		return err
	}

	// Complete operation successfully
	s.instrumentation.CompleteOperation(tracker)
	return nil
}

// Helper methods with metrics integration

func (s *ExampleUserServiceWithMetrics) validateUserRequest(req *models.UserCreateRequest) error {
	// This would contain validation logic
	if req == nil {
		return fmt.Errorf("request cannot be nil")
	}
	if req.Email == "" {
		return fmt.Errorf("email is required")
	}
	if req.Username == "" {
		return fmt.Errorf("username is required")
	}
	return nil
}

func (s *ExampleUserServiceWithMetrics) getUserByEmail(ctx context.Context, email string) (*models.User, error) {
	// Simulate database call
	// In real implementation, this would query the database
	return nil, nil
}

func (s *ExampleUserServiceWithMetrics) createUserWithRetryAndMetrics(ctx context.Context, req *models.UserCreateRequest, tracker *metrics.OperationTracker) (*models.User, error) {
	maxRetries := 3
	var lastErr error

	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			// Record retry
			s.instrumentation.RecordRetry(tracker)
			s.metrics.RecordRetry("create_user")

			// Wait before retry
			time.Sleep(time.Duration(attempt) * 100 * time.Millisecond)
		}

		user, err := s.performUserCreation(ctx, req)
		if err == nil {
			return user, nil
		}

		lastErr = err

		// Don't retry on last attempt
		if attempt == maxRetries {
			break
		}

		// Check if error is retryable
		if !s.isRetryableError(err) {
			break
		}
	}

	return nil, lastErr
}

func (s *ExampleUserServiceWithMetrics) performUserCreation(ctx context.Context, req *models.UserCreateRequest) (*models.User, error) {
	// Simulate user creation
	// In real implementation, this would create the user in the database
	return &models.User{
		ID:       fmt.Sprintf("user-%d", time.Now().UnixNano()),
		Email:    req.Email,
		Username: req.Username,
		FullName: req.FullName,
		Role:     req.Role,
		IsActive: true,
	}, nil
}

func (s *ExampleUserServiceWithMetrics) getUserFromDatabase(ctx context.Context, userID string) (*models.User, error) {
	// Simulate database call
	// In real implementation, this would query the database
	return nil, nil
}

func (s *ExampleUserServiceWithMetrics) applyUserUpdatesWithCircuitBreaker(ctx context.Context, user *models.User, updates *models.UserUpdateRequest, tracker *metrics.OperationTracker) (*models.User, error) {
	// Simulate circuit breaker state
	circuitBreakerState := 0 // Closed
	s.metrics.RecordCircuitBreakerState("update_user", circuitBreakerState)
	s.instrumentation.RecordCircuitBreakerState("update_user", circuitBreakerState)

	// Simulate user update
	// In real implementation, this would update the user in the database
	return user, nil
}

func (s *ExampleUserServiceWithMetrics) deleteUserWithRetryAndMetrics(ctx context.Context, userID string, tracker *metrics.OperationTracker) error {
	maxRetries := 2
	var lastErr error

	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			// Record retry
			s.instrumentation.RecordRetry(tracker)
			s.metrics.RecordRetry("delete_user")
		}

		err := s.performUserDeletion(ctx, userID)
		if err == nil {
			return nil
		}

		lastErr = err

		// Don't retry on last attempt
		if attempt == maxRetries {
			break
		}

		// Check if error is retryable
		if !s.isRetryableError(err) {
			break
		}

		// Wait before retry
		time.Sleep(time.Duration(attempt+1) * 100 * time.Millisecond)
	}

	return lastErr
}

func (s *ExampleUserServiceWithMetrics) performUserDeletion(ctx context.Context, userID string) error {
	// Simulate user deletion
	// In real implementation, this would delete the user from the database
	return nil
}

func (s *ExampleUserServiceWithMetrics) isRetryableError(err error) bool {
	// This would typically check error types to determine if retryable
	// For now, return true for all errors
	return true
}

// Metrics and monitoring methods

// GetServiceMetrics returns the service metrics
func (s *ExampleUserServiceWithMetrics) GetServiceMetrics() *metrics.ServiceMetrics {
	return s.metrics
}

// GetInstrumentation returns the instrumentation
func (s *ExampleUserServiceWithMetrics) GetInstrumentation() *metrics.Instrumentation {
	return s.instrumentation
}

// GetOperationStats returns operation statistics
func (s *ExampleUserServiceWithMetrics) GetOperationStats() map[string]metrics.OperationStats {
	return s.instrumentation.GetOperationStats()
}

// GetActiveOperations returns currently active operations
func (s *ExampleUserServiceWithMetrics) GetActiveOperations() map[string]*metrics.OperationTracker {
	return s.instrumentation.GetActiveOperations()
}

// GetServiceSummary returns a summary of service metrics
func (s *ExampleUserServiceWithMetrics) GetServiceSummary() *metrics.ServiceMetricsSummary {
	return s.metrics.GetServiceSummary()
}

// Example of using the metrics middleware

// ExampleServiceWithMiddleware demonstrates using the metrics middleware
type ExampleServiceWithMiddleware struct {
	instrumentationMiddleware *metrics.InstrumentationMiddleware
	metricsMiddleware         *metrics.ServiceMetricsMiddleware
}

// NewExampleServiceWithMiddleware creates a new service with middleware
func NewExampleServiceWithMiddleware() *ExampleServiceWithMiddleware {
	serviceName := "example-service"

	return &ExampleServiceWithMiddleware{
		instrumentationMiddleware: metrics.NewInstrumentationMiddleware(serviceName),
		metricsMiddleware:         metrics.NewServiceMetricsMiddleware(serviceName),
	}
}

// ProcessData demonstrates using both middlewares
func (s *ExampleServiceWithMiddleware) ProcessData(ctx context.Context, data string) (string, error) {
	// Use instrumentation middleware
	var result string
	err := s.instrumentationMiddleware.WrapOperation(ctx, "process_data", map[string]string{"data_length": fmt.Sprintf("%d", len(data))}, func(ctx context.Context) error {
		// Use metrics middleware
		return s.metricsMiddleware.WrapOperationWithContext(ctx, "process_data", func(ctx context.Context) error {
			// Actual processing logic
			result = fmt.Sprintf("processed: %s", data)
			return nil
		})
	})

	return result, err
}

// GetMetrics returns the metrics middleware
func (s *ExampleServiceWithMiddleware) GetMetrics() *metrics.ServiceMetrics {
	return s.metricsMiddleware.GetMetrics()
}

// GetInstrumentation returns the instrumentation middleware
func (s *ExampleServiceWithMiddleware) GetInstrumentation() *metrics.Instrumentation {
	return s.instrumentationMiddleware.GetInstrumentation()
}
