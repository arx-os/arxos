package errors

import (
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestServiceError(t *testing.T) {
	t.Run("NewServiceError", func(t *testing.T) {
		err := NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed")

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "create_user", err.Operation)
		assert.Equal(t, CodeInvalidInput, err.Code)
		assert.Equal(t, "validation failed", err.Message)
		assert.NotNil(t, err.Metadata)
	})

	t.Run("WrapServiceError", func(t *testing.T) {
		originalErr := fmt.Errorf("database connection failed")
		err := WrapServiceError(originalErr, "user-service", "create_user", CodeDatabase, "failed to create user")

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "create_user", err.Operation)
		assert.Equal(t, CodeDatabase, err.Code)
		assert.Equal(t, originalErr, err.Unwrap())
	})

	t.Run("WithResourceID", func(t *testing.T) {
		err := NewServiceError("user-service", "get_user", CodeNotFound, "user not found").
			WithResourceID("user-123")

		assert.Equal(t, "user-123", err.ResourceID)
	})

	t.Run("WithRetryAfter", func(t *testing.T) {
		retryAfter := 5 * time.Second
		err := NewServiceError("user-service", "create_user", CodeRateLimited, "rate limited").
			WithRetryAfter(retryAfter)

		assert.Equal(t, &retryAfter, err.RetryAfter)
	})

	t.Run("WithMetadata", func(t *testing.T) {
		err := NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed").
			WithMetadata("field", "email").
			WithMetadata("reason", "invalid format")

		assert.Equal(t, "email", err.Metadata["field"])
		assert.Equal(t, "invalid format", err.Metadata["reason"])
	})

	t.Run("Error", func(t *testing.T) {
		err := NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed")
		errorMsg := err.Error()

		assert.Contains(t, errorMsg, "user-service")
		assert.Contains(t, errorMsg, "create_user")
		assert.Contains(t, errorMsg, "validation failed")
	})
}

func TestServiceErrorConstructors(t *testing.T) {
	t.Run("NotFoundServiceError", func(t *testing.T) {
		err := NotFoundServiceError("user-service", "get_user", "user", "user-123")

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "get_user", err.Operation)
		assert.Equal(t, CodeNotFound, err.Code)
		assert.Equal(t, "user-123", err.ResourceID)
		assert.Equal(t, "user", err.Metadata["resource_type"])
	})

	t.Run("ValidationServiceError", func(t *testing.T) {
		err := ValidationServiceError("user-service", "create_user", "email", "invalid format")

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "create_user", err.Operation)
		assert.Equal(t, CodeInvalidInput, err.Code)
		assert.Equal(t, "email", err.Metadata["field"])
		assert.Equal(t, "invalid format", err.Metadata["reason"])
	})

	t.Run("DatabaseServiceError", func(t *testing.T) {
		originalErr := fmt.Errorf("connection failed")
		err := DatabaseServiceError("user-service", "create_user", originalErr)

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "create_user", err.Operation)
		assert.Equal(t, CodeDatabase, err.Code)
		assert.Equal(t, originalErr, err.Unwrap())
		assert.Equal(t, "database", err.Metadata["operation_type"])
	})

	t.Run("TimeoutServiceError", func(t *testing.T) {
		timeout := 30 * time.Second
		err := TimeoutServiceError("user-service", "create_user", timeout)

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "create_user", err.Operation)
		assert.Equal(t, CodeTimeout, err.Code)
		assert.Equal(t, timeout.String(), err.Metadata["timeout_duration"])
	})

	t.Run("ConflictServiceError", func(t *testing.T) {
		err := ConflictServiceError("user-service", "update_user", "user", "user-123", "concurrent modification")

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "update_user", err.Operation)
		assert.Equal(t, CodeConflict, err.Code)
		assert.Equal(t, "user-123", err.ResourceID)
		assert.Equal(t, "user", err.Metadata["resource_type"])
		assert.Equal(t, "concurrent modification", err.Metadata["conflict_reason"])
	})

	t.Run("RateLimitServiceError", func(t *testing.T) {
		retryAfter := 60 * time.Second
		err := RateLimitServiceError("user-service", "create_user", retryAfter)

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "create_user", err.Operation)
		assert.Equal(t, CodeRateLimited, err.Code)
		assert.Equal(t, &retryAfter, err.RetryAfter)
		assert.Equal(t, "service", err.Metadata["rate_limit_type"])
	})
}

func TestRetryableServiceError(t *testing.T) {
	t.Run("NewRetryableServiceError", func(t *testing.T) {
		err := NewRetryableServiceError("user-service", "create_user", CodeTimeout, "operation timed out", 3, 1*time.Second)

		assert.Equal(t, "user-service", err.Service)
		assert.Equal(t, "create_user", err.Operation)
		assert.Equal(t, CodeTimeout, err.Code)
		assert.Equal(t, 3, err.MaxRetries)
		assert.Equal(t, 1*time.Second, err.RetryDelay)
	})

	t.Run("IsRetryableServiceError", func(t *testing.T) {
		err := NewRetryableServiceError("user-service", "create_user", CodeTimeout, "operation timed out", 3, 1*time.Second)

		assert.True(t, IsRetryableServiceError(err))

		regularErr := NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed")
		assert.False(t, IsRetryableServiceError(regularErr))
	})

	t.Run("GetRetryableServiceError", func(t *testing.T) {
		err := NewRetryableServiceError("user-service", "create_user", CodeTimeout, "operation timed out", 3, 1*time.Second)

		retryableErr := GetRetryableServiceError(err)
		require.NotNil(t, retryableErr)
		assert.Equal(t, 3, retryableErr.MaxRetries)
		assert.Equal(t, 1*time.Second, retryableErr.RetryDelay)
	})
}

func TestServiceErrorGroup(t *testing.T) {
	t.Run("NewServiceErrorGroup", func(t *testing.T) {
		errors := []*ServiceError{
			NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed"),
			NewServiceError("user-service", "create_user", CodeDatabase, "database error"),
		}

		group := NewServiceErrorGroup("user-service", "batch_create", errors)

		assert.Equal(t, "user-service", group.Service)
		assert.Equal(t, "batch_create", group.Operation)
		assert.Equal(t, 2, len(group.Errors))
		assert.Contains(t, group.Summary, "2 errors occurred")
	})

	t.Run("AddError", func(t *testing.T) {
		group := NewServiceErrorGroup("user-service", "batch_create", []*ServiceError{})

		err := NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed")
		group.AddError(err)

		assert.Equal(t, 1, len(group.Errors))
		assert.Contains(t, group.Summary, "1 errors occurred")
	})

	t.Run("HasErrors", func(t *testing.T) {
		emptyGroup := NewServiceErrorGroup("user-service", "batch_create", []*ServiceError{})
		assert.False(t, emptyGroup.HasErrors())

		groupWithErrors := NewServiceErrorGroup("user-service", "batch_create", []*ServiceError{
			NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed"),
		})
		assert.True(t, groupWithErrors.HasErrors())
	})

	t.Run("GetCriticalErrors", func(t *testing.T) {
		group := NewServiceErrorGroup("user-service", "batch_create", []*ServiceError{
			NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed"),
			NewServiceError("user-service", "create_user", CodeDataCorruption, "data corruption"),
		})

		criticalErrors := group.GetCriticalErrors()
		assert.Equal(t, 1, len(criticalErrors))
		assert.Equal(t, CodeDataCorruption, criticalErrors[0].Code)
	})
}

func TestServiceErrorContext(t *testing.T) {
	t.Run("WithServiceContext", func(t *testing.T) {
		originalErr := fmt.Errorf("operation failed")
		err := WithServiceContext(originalErr, "user-service", "create_user")

		serviceErr := GetServiceError(err)
		require.NotNil(t, serviceErr)
		assert.Equal(t, "user-service", serviceErr.Service)
		assert.Equal(t, "create_user", serviceErr.Operation)
	})

	t.Run("WithOperationContext", func(t *testing.T) {
		originalErr := fmt.Errorf("operation failed")
		err := WithOperationContext(originalErr, "create_user")

		serviceErr := GetServiceError(err)
		require.NotNil(t, serviceErr)
		assert.Equal(t, "unknown", serviceErr.Service)
		assert.Equal(t, "create_user", serviceErr.Operation)
	})
}

func TestServiceErrorTracker(t *testing.T) {
	t.Run("NewServiceErrorTracker", func(t *testing.T) {
		tracker := NewServiceErrorTracker()
		assert.NotNil(t, tracker)
		assert.NotNil(t, tracker.metrics)
	})

	t.Run("TrackError", func(t *testing.T) {
		tracker := NewServiceErrorTracker()

		err := NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed")
		tracker.TrackError("user-service", "create_user", err)

		metrics := tracker.GetMetrics("user-service", "create_user")
		require.NotNil(t, metrics)
		assert.Equal(t, "user-service", metrics.Service)
		assert.Equal(t, "create_user", metrics.Operation)
		assert.Equal(t, 1, metrics.ErrorCount)
	})

	t.Run("GetAllMetrics", func(t *testing.T) {
		tracker := NewServiceErrorTracker()

		err1 := NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed")
		err2 := NewServiceError("user-service", "get_user", CodeNotFound, "user not found")

		tracker.TrackError("user-service", "create_user", err1)
		tracker.TrackError("user-service", "get_user", err2)

		allMetrics := tracker.GetAllMetrics()
		assert.Equal(t, 2, len(allMetrics))
	})
}

func TestServiceErrorIntegration(t *testing.T) {
	t.Run("ErrorChaining", func(t *testing.T) {
		// Create a chain of errors
		originalErr := fmt.Errorf("database connection failed")
		serviceErr := WrapServiceError(originalErr, "user-service", "create_user", CodeDatabase, "failed to create user")
		serviceErr = serviceErr.WithResourceID("user-123").WithMetadata("attempt", 1)

		// Verify error chain
		assert.Equal(t, originalErr, serviceErr.Unwrap())
		assert.Equal(t, "user-123", serviceErr.ResourceID)
		assert.Equal(t, 1, serviceErr.Metadata["attempt"])
	})

	t.Run("ErrorRecovery", func(t *testing.T) {
		// Test error recovery patterns
		tracker := NewServiceErrorTracker()

		// Simulate multiple errors
		for i := 0; i < 5; i++ {
			err := NewServiceError("user-service", "create_user", CodeTimeout, "operation timed out")
			tracker.TrackError("user-service", "create_user", err)
		}

		metrics := tracker.GetMetrics("user-service", "create_user")
		assert.Equal(t, 5, metrics.ErrorCount)
		assert.True(t, metrics.ErrorRate > 0)
	})

	t.Run("ContextPropagation", func(t *testing.T) {
		// Test context propagation through error chain
		// Create error with context
		err := NewServiceError("user-service", "create_user", CodeInvalidInput, "validation failed")
		err.AppError = err.AppError.WithContext("user_id", "user-123").WithContext("request_id", "req-456")

		// Verify context is preserved
		assert.Equal(t, "user-123", err.AppError.Context["user_id"])
		assert.Equal(t, "req-456", err.AppError.Context["request_id"])
	})
}
