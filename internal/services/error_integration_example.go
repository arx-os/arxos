package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/errors"
	"github.com/arx-os/arxos/pkg/models"
)

// ExampleUserServiceWithEnhancedErrorHandling demonstrates how to integrate enhanced error handling
type ExampleUserServiceWithEnhancedErrorHandling struct {
	errorHandler *ServiceErrorHandler
	// ... other fields
}

// NewExampleUserServiceWithEnhancedErrorHandling creates a new user service with enhanced error handling
func NewExampleUserServiceWithEnhancedErrorHandling() *ExampleUserServiceWithEnhancedErrorHandling {
	return &ExampleUserServiceWithEnhancedErrorHandling{
		errorHandler: NewServiceErrorHandler("user-service"),
	}
}

// CreateUser demonstrates enhanced error handling for user creation
func (s *ExampleUserServiceWithEnhancedErrorHandling) CreateUser(ctx context.Context, req *models.UserCreateRequest) (*models.User, error) {
	operation := "create_user"

	// Validate input with detailed error context
	if err := s.validateUserRequest(req); err != nil {
		return nil, s.errorHandler.HandleError(operation, err)
	}

	// Check if user already exists
	existingUser, err := s.getUserByEmail(ctx, req.Email)
	if err != nil {
		return nil, s.errorHandler.HandleDatabaseError(operation, err)
	}

	if existingUser != nil {
		return nil, s.errorHandler.HandleConflictError(operation, "user", req.Email, "email already exists")
	}

	// Create user with retry logic
	user, err := s.createUserWithRetry(ctx, req)
	if err != nil {
		return nil, s.errorHandler.HandleError(operation, err)
	}

	return user, nil
}

// GetUser demonstrates enhanced error handling for user retrieval
func (s *ExampleUserServiceWithEnhancedErrorHandling) GetUser(ctx context.Context, userID string) (*models.User, error) {
	operation := "get_user"

	if userID == "" {
		return nil, s.errorHandler.HandleValidationError(operation, "user_id", "cannot be empty")
	}

	user, err := s.getUserFromDatabase(ctx, userID)
	if err != nil {
		return nil, s.errorHandler.HandleDatabaseError(operation, err)
	}

	if user == nil {
		return nil, s.errorHandler.HandleNotFoundError(operation, "user", userID)
	}

	return user, nil
}

// UpdateUser demonstrates batch error handling
func (s *ExampleUserServiceWithEnhancedErrorHandling) UpdateUser(ctx context.Context, userID string, updates *models.UserUpdateRequest) (*models.User, error) {
	operation := "update_user"

	// Use batch error handler for multiple validations
	batchHandler := NewBatchErrorHandler("user-service")

	// Validate user ID
	if userID == "" {
		batchHandler.AddError(operation, s.errorHandler.HandleValidationError(operation, "user_id", "cannot be empty"))
	}

	// Validate updates
	if updates == nil {
		batchHandler.AddError(operation, s.errorHandler.HandleValidationError(operation, "updates", "cannot be nil"))
	}

	// Check for errors
	if batchHandler.HasErrors() {
		return nil, batchHandler.GetErrorGroup(operation)
	}

	// Get existing user
	user, err := s.GetUser(ctx, userID)
	if err != nil {
		return nil, s.errorHandler.HandleError(operation, err)
	}

	// Apply updates with conflict detection
	updatedUser, err := s.applyUserUpdates(ctx, user, updates)
	if err != nil {
		return nil, s.errorHandler.HandleError(operation, err)
	}

	return updatedUser, nil
}

// DeleteUser demonstrates circuit breaker pattern
func (s *ExampleUserServiceWithEnhancedErrorHandling) DeleteUser(ctx context.Context, userID string) error {
	operation := "delete_user"

	// Create circuit breaker for external service calls
	circuitBreaker := NewCircuitBreakerErrorHandler("user-service", 3, 30*time.Second)

	// Execute with circuit breaker protection
	err := circuitBreaker.ExecuteWithCircuitBreaker(ctx, operation, func() error {
		return s.performUserDeletion(ctx, userID)
	})

	if err != nil {
		return s.errorHandler.HandleError(operation, err)
	}

	return nil
}

// BatchCreateUsers demonstrates batch operations with error aggregation
func (s *ExampleUserServiceWithEnhancedErrorHandling) BatchCreateUsers(ctx context.Context, requests []*models.UserCreateRequest) ([]*models.User, []error) {
	operation := "batch_create_users"
	batchHandler := NewBatchErrorHandler("user-service")

	var users []*models.User
	var userErrors []error

	for i, req := range requests {
		user, err := s.CreateUser(ctx, req)
		if err != nil {
			batchHandler.AddError(fmt.Sprintf("%s_user_%d", operation, i), err)
			userErrors = append(userErrors, err)
		} else {
			users = append(users, user)
		}
	}

	// Log batch results
	if batchHandler.HasErrors() {
		errorGroup := batchHandler.GetErrorGroup(operation)
		// Log error group for monitoring
		_ = errorGroup
	}

	return users, userErrors
}

// Helper methods (these would be implemented in the actual service)

func (s *ExampleUserServiceWithEnhancedErrorHandling) validateUserRequest(req *models.UserCreateRequest) error {
	if req == nil {
		return s.errorHandler.HandleValidationError("validate_user_request", "request", "cannot be nil")
	}

	if req.Email == "" {
		return s.errorHandler.HandleValidationError("validate_user_request", "email", "cannot be empty")
	}

	if req.Username == "" {
		return s.errorHandler.HandleValidationError("validate_user_request", "username", "cannot be empty")
	}

	if req.Password == "" {
		return s.errorHandler.HandleValidationError("validate_user_request", "password", "cannot be empty")
	}

	return nil
}

func (s *ExampleUserServiceWithEnhancedErrorHandling) getUserByEmail(ctx context.Context, email string) (*models.User, error) {
	// Simulate database call
	// In real implementation, this would call the actual database
	return nil, nil
}

func (s *ExampleUserServiceWithEnhancedErrorHandling) createUserWithRetry(ctx context.Context, req *models.UserCreateRequest) (*models.User, error) {
	// Create retryable error handler
	retryHandler := NewRetryableErrorHandler("user-service", 3, 1*time.Second, 10*time.Second)

	// Execute with retry logic
	var user *models.User
	err := retryHandler.ExecuteWithRetry(ctx, "create_user_with_retry", func() error {
		var err error
		user, err = s.performUserCreation(ctx, req)
		return err
	})

	return user, err
}

func (s *ExampleUserServiceWithEnhancedErrorHandling) performUserCreation(ctx context.Context, req *models.UserCreateRequest) (*models.User, error) {
	// Simulate user creation
	// In real implementation, this would create the user in the database
	return &models.User{
		ID:       "user-123",
		Email:    req.Email,
		Username: req.Username,
		FullName: req.FullName,
		Role:     req.Role,
		IsActive: true,
	}, nil
}

func (s *ExampleUserServiceWithEnhancedErrorHandling) getUserFromDatabase(ctx context.Context, userID string) (*models.User, error) {
	// Simulate database call
	// In real implementation, this would query the database
	return nil, nil
}

func (s *ExampleUserServiceWithEnhancedErrorHandling) applyUserUpdates(ctx context.Context, user *models.User, updates *models.UserUpdateRequest) (*models.User, error) {
	// Simulate user update
	// In real implementation, this would update the user in the database
	return user, nil
}

func (s *ExampleUserServiceWithEnhancedErrorHandling) performUserDeletion(ctx context.Context, userID string) error {
	// Simulate user deletion
	// In real implementation, this would delete the user from the database
	return nil
}

// Example of using fallback error handling
type ExampleServiceWithFallback struct {
	errorHandler *ServiceErrorHandler
	fallbackFunc func() error
}

func NewExampleServiceWithFallback() *ExampleServiceWithFallback {
	return &ExampleServiceWithFallback{
		errorHandler: NewServiceErrorHandler("example-service"),
		fallbackFunc: func() error {
			// Implement fallback logic
			return nil
		},
	}
}

func (s *ExampleServiceWithFallback) ProcessWithFallback(ctx context.Context, operation string, fn func() error) error {
	fallbackHandler := NewFallbackErrorHandler("example-service", s.fallbackFunc)
	return fallbackHandler.ExecuteWithFallback(ctx, operation, fn)
}

// Example of error metrics and monitoring
func (s *ExampleUserServiceWithEnhancedErrorHandling) GetErrorMetrics() map[string]*errors.ServiceErrorMetrics {
	return s.errorHandler.GetErrorMetrics()
}

func (s *ExampleUserServiceWithEnhancedErrorHandling) GetServiceMetrics() map[string]*errors.ServiceErrorMetrics {
	return s.errorHandler.GetServiceMetrics()
}
