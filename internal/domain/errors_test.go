package domain

import (
	"errors"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestDomainError_Basic(t *testing.T) {
	tests := []struct {
		name      string
		errorType ErrorType
		code      string
		message   string
		expected  string
	}{
		{
			name:      "Simple validation error",
			errorType: ErrorTypeValidation,
			code:      "VALIDATION_ERROR",
			message:   "Invalid input",
			expected:  "[validation] VALIDATION_ERROR: Invalid input",
		},
		{
			name:      "Spatial error",
			errorType: ErrorTypeSpatial,
			code:      "SPATIAL_VALIDATION_ERROR",
			message:   "Invalid coordinates",
			expected:  "[spatial] SPATIAL_VALIDATION_ERROR: Invalid coordinates",
		},
		{
			name:      "AR error",
			errorType: ErrorTypeAR,
			code:      "AR_INITIALIZATION_ERROR",
			message:   "Failed to initialize AR session",
			expected:  "[ar] AR_INITIALIZATION_ERROR: Failed to initialize AR session",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := &DomainError{
				Type:      tt.errorType,
				Code:      tt.code,
				Message:   tt.message,
				Timestamp: time.Now(),
			}

			assert.Equal(t, tt.expected, err.Error())
			assert.Equal(t, tt.errorType, err.Type)
			assert.Equal(t, tt.code, err.Code)
			assert.Equal(t, tt.message, err.Message)
			assert.False(t, err.IsRetryable())
			assert.NotNil(t, err.Timestamp)
		})
	}
}

func TestDomainError_WithCause(t *testing.T) {
	originalErr := errors.New("original error")
	domainErr := &DomainError{
		Type:    ErrorTypeValidation,
		Code:    "VALIDATION_ERROR",
		Message: "Validation failed",
		Cause:   originalErr,
	}

	expected := "[validation] VALIDATION_ERROR: Validation failed (original error)"
	assert.Equal(t, expected, domainErr.Error())
	assert.Equal(t, originalErr, domainErr.Unwrap())
	assert.Equal(t, originalErr, domainErr.Cause)
}

func TestDomainErrorBuilder_Basic(t *testing.T) {
	err := NewDomainError(ErrorTypeValidation, "TEST_ERROR", "Test message").
		WithContext("user_id", "123").
		WithContext("operation", "create").
		WithRetryable(true).
		WithUserAction("Try again").
		Build()

	assert.NotNil(t, err)
	assert.Equal(t, ErrorTypeValidation, err.Type)
	assert.Equal(t, "TEST_ERROR", err.Code)
	assert.Equal(t, "Test message", err.Message)
	assert.True(t, err.IsRetryable())
	assert.Equal(t, "Try again", err.UserAction)
	assert.Equal(t, "123", err.Context["user_id"])
	assert.Equal(t, "create", err.Context["operation"])
}

func TestSpatialErrorConstructors(t *testing.T) {
	tests := []struct {
		name    string
		creator func() *DomainError
		wantErr bool
	}{
		{
			name: "Spatial validation error",
			creator: func() *DomainError {
				return NewSpatialValidationError("Invalid coordinates", nil)
			},
			wantErr: true,
		},
		{
			name: "Spatial anchor error",
			creator: func() *DomainError {
				return NewSpatialAnchorError("CREATE", "Failed to create anchor", nil)
			},
			wantErr: true,
		},
		{
			name: "Spatial out of bounds error",
			creator: func() *DomainError {
				return NewSpatialOutOfBoundsError(
					&SpatialLocation{X: 100, Y: 200, Z: 300},
					map[string]interface{}{"min": 0, "max": 50},
				)
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.creator()
			if tt.wantErr {
				assert.NotNil(t, err)
				assert.Equal(t, ErrorTypeSpatial, err.Type)
				assert.Contains(t, err.Error(), "spatial")
			}
		})
	}
}

func TestARErrorConstructors(t *testing.T) {
	tests := []struct {
		name    string
		creator func() *DomainError
		wantErr bool
	}{
		{
			name: "AR initialization error",
			creator: func() *DomainError {
				return NewARInitializationError("ARKit", "Failed to initialize", nil)
			},
			wantErr: true,
		},
		{
			name: "AR session error",
			creator: func() *DomainError {
				return NewARSessionError("session-123", "CREATE", "Session creation failed", nil)
			},
			wantErr: true,
		},
		{
			name: "AR tracking error",
			creator: func() *DomainError {
				return NewARTrackingError("Poor lighting conditions", nil)
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.creator()
			if tt.wantErr {
				assert.NotNil(t, err)
				assert.Equal(t, ErrorTypeAR, err.Type)
				assert.Contains(t, err.Error(), "ar")
			}
		})
	}
}

func TestValidationErrorConstructors(t *testing.T) {
	tests := []struct {
		name    string
		creator func() *DomainError
		wantErr bool
	}{
		{
			name: "Validation error",
			creator: func() *DomainError {
				return NewValidationError("email", "Invalid email format", nil)
			},
			wantErr: true,
		},
		{
			name: "Required field error",
			creator: func() *DomainError {
				return NewRequiredFieldError("name")
			},
			wantErr: true,
		},
		{
			name: "Invalid format error",
			creator: func() *DomainError {
				return NewInvalidFormatError("date", "YYYY-MM-DD")
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.creator()
			if tt.wantErr {
				assert.NotNil(t, err)
				assert.Equal(t, ErrorTypeValidation, err.Type)
				assert.False(t, err.IsRetryable())
			}
		})
	}
}

func TestBusinessLogicErrorConstructors(t *testing.T) {
	tests := []struct {
		name    string
		creator func() *DomainError
		wantErr bool
	}{
		{
			name: "Not found error",
			creator: func() *DomainError {
				return NewNotFoundError("Building", "building-123")
			},
			wantErr: true,
		},
		{
			name: "Conflict error",
			creator: func() *DomainError {
				return NewConflictError("User", "user-123", "Email already exists")
			},
			wantErr: true,
		},
		{
			name: "Unauthorized error",
			creator: func() *DomainError {
				return NewUnauthorizedError("delete_building")
			},
			wantErr: true,
		},
		{
			name: "Forbidden error",
			creator: func() *DomainError {
				return NewForbiddenError("access_admin", "Insufficient permissions")
			},
			wantErr: true,
		},
		{
			name: "Rate limit error",
			creator: func() *DomainError {
				return NewRateLimitError("100", "minute")
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.creator()
			if tt.wantErr {
				assert.NotNil(t, err)
				assert.NotEmpty(t, err.Code)
			}
		})
	}
}

func TestInfrastructureErrorConstructors(t *testing.T) {
	tests := []struct {
		name    string
		creator func() *DomainError
		wantErr bool
	}{
		{
			name: "Database error",
			creator: func() *DomainError {
				return NewDatabaseError("CONNECT", "Connection failed", nil)
			},
			wantErr: true,
		},
		{
			name: "Cache error",
			creator: func() *DomainError {
				return NewCacheError("SET", "Failed to set value", nil)
			},
			wantErr: true,
		},
		{
			name: "Network error",
			creator: func() *DomainError {
				return NewNetworkError("REQUEST", "https://api.example.com", "Timeout", nil)
			},
			wantErr: true,
		},
		{
			name: "Timeout error",
			creator: func() *DomainError {
				return NewTimeoutError("database_query", 30*time.Second)
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.creator()
			if tt.wantErr {
				assert.NotNil(t, err)
				assert.True(t, err.IsRetryable())
			}
		})
	}
}

func TestIFCErrorConstructors(t *testing.T) {
	tests := []struct {
		name    string
		creator func() *DomainError
		wantErr bool
	}{
		{
			name: "IFC parsing error",
			creator: func() *DomainError {
				return NewIFCParsingError("building.ifc", "Invalid IFC format", nil)
			},
			wantErr: true,
		},
		{
			name: "IFC validation error",
			creator: func() *DomainError {
				return NewIFCValidationError("building.ifc", "Missing required entities")
			},
			wantErr: true,
		},
		{
			name: "IFC import error",
			creator: func() *DomainError {
				return NewIFCImportError("building.ifc", "repo-123", "Import failed", nil)
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.creator()
			if tt.wantErr {
				assert.NotNil(t, err)
				assert.Equal(t, ErrorTypeIFC, err.Type)
			}
		})
	}
}

func TestBusinessDomainErrorConstructors(t *testing.T) {
	tests := []struct {
		name    string
		creator func() *DomainError
		wantErr bool
	}{
		{
			name: "Building error",
			creator: func() *DomainError {
				return NewBuildingError("CREATE", "building-123", "Creation failed", nil)
			},
			wantErr: true,
		},
		{
			name: "Equipment error",
			creator: func() *DomainError {
				return NewEquipmentError("UPDATE", "equipment-123", "Update failed", nil)
			},
			wantErr: true,
		},
		{
			name: "User error",
			creator: func() *DomainError {
				return NewUserError("DELETE", "user-123", "Deletion failed", nil)
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.creator()
			if tt.wantErr {
				assert.NotNil(t, err)
				assert.Equal(t, ErrorTypeInternal, err.Type)
				assert.True(t, err.IsRetryable())
			}
		})
	}
}

func TestErrorHandlingUtilities(t *testing.T) {
	tests := []struct {
		name      string
		inputErr  error
		isDomain  bool
		retryable bool
		errorType ErrorType
	}{
		{
			name:      "Domain error",
			inputErr:  NewValidationError("email", "Invalid format", nil),
			isDomain:  true,
			retryable: false,
			errorType: ErrorTypeValidation,
		},
		{
			name:      "Wrapped domain error",
			inputErr:  fmt.Errorf("wrapped: %w", NewValidationError("email", "Invalid format", nil)),
			isDomain:  false, // fmt.Errorf wraps the error, so IsDomainError returns false
			retryable: false,
			errorType: ErrorTypeValidation, // GetDomainError extracts the wrapped domain error
		},
		{
			name:      "Regular error",
			inputErr:  errors.New("regular error"),
			isDomain:  false,
			retryable: true, // Default behavior
			errorType: ErrorTypeInternal,
		},
		{
			name:      "Nil error",
			inputErr:  nil,
			isDomain:  false,
			retryable: false,
			errorType: ErrorTypeInternal,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.isDomain, IsDomainError(tt.inputErr))
			assert.Equal(t, tt.retryable, IsRetryableError(tt.inputErr))
			assert.Equal(t, tt.errorType, ErrorTypeOf(tt.inputErr))

			domainErr := GetDomainError(tt.inputErr)
			if tt.isDomain || tt.name == "Wrapped domain error" {
				assert.NotNil(t, domainErr)
			} else {
				assert.Nil(t, domainErr)
			}
		})
	}
}

func TestWrapError(t *testing.T) {
	originalErr := errors.New("original error")
	wrappedErr := WrapError(originalErr, ErrorTypeDatabase, "DB_ERROR", "Database operation failed")

	assert.NotNil(t, wrappedErr)
	assert.Equal(t, ErrorTypeDatabase, wrappedErr.Type)
	assert.Equal(t, "DB_ERROR", wrappedErr.Code)
	assert.Equal(t, "Database operation failed", wrappedErr.Message)
	assert.Equal(t, originalErr, wrappedErr.Cause)
	assert.True(t, wrappedErr.IsRetryable())

	// Test wrapping nil error
	nilErr := WrapError(nil, ErrorTypeDatabase, "DB_ERROR", "Database operation failed")
	assert.Nil(t, nilErr)
}

func TestDomainErrorContextUtilities(t *testing.T) {
	err := NewDomainError(ErrorTypeInternal, "TEST_ERROR", "Test message").Build()

	t.Run("AddEntityContext", func(t *testing.T) {
		AddEntityContext(err, "Building", "building-123")
		assert.Equal(t, "Building", err.Context["entity_type"])
		assert.Equal(t, "building-123", err.Context["entity_id"])
	})

	t.Run("AddOperationContext", func(t *testing.T) {
		AddOperationContext(err, "create")
		assert.Equal(t, "create", err.Context["operation"])
	})

	t.Run("AddTimingContext", func(t *testing.T) {
		startTime := time.Now().Add(-time.Second)
		AddTimingContext(err, startTime)
		duration, exists := err.Context["duration"]
		assert.True(t, exists)
		assert.IsType(t, "", duration)
	})

	t.Run("AddSpatialContext", func(t *testing.T) {
		location := &SpatialLocation{X: 100, Y: 200, Z: 300}
		bounds := map[string]interface{}{"min": 0, "max": 1000}
		AddSpatialContext(err, location, bounds)
		assert.Equal(t, location, err.Context["location"])
		assert.Equal(t, bounds, err.Context["bounds"])
	})

	t.Run("AddARContext", func(t *testing.T) {
		AddARContext(err, "session-123", "ARKit")
		assert.Equal(t, "session-123", err.Context["ar_session_id"])
		assert.Equal(t, "ARKit", err.Context["ar_platform"])
	})
}

// Error chains testing

type testErrorChain struct {
	wrapped error
	message string
}

func (e *testErrorChain) Error() string {
	if e.wrapped != nil {
		return fmt.Sprintf("%s: %v", e.message, e.wrapped)
	}
	return e.message
}

func (e *testErrorChain) Unwrap() error {
	return e.wrapped
}

func TestErrorChains(t *testing.T) {
	originalDomainErr := NewValidationError("email", "Invalid format", nil)
	chainErr := &testErrorChain{
		wrapped: originalDomainErr,
		message: "Additional context",
	}
	topErr := &testErrorChain{
		wrapped: chainErr,
		message: "Top level error",
	}

	// Test that we can extract the original domain error from the chain
	extractedErr := GetDomainError(topErr)
	assert.NotNil(t, extractedErr)
	assert.Equal(t, originalDomainErr.Type, extractedErr.Type)
	assert.Equal(t, originalDomainErr.Code, extractedErr.Code)

	// Test that it preserves retryable status
	assert.False(t, IsRetryableError(topErr))
}

func TestErrorTypeConstants(t *testing.T) {
	expectedTypes := []ErrorType{
		ErrorTypeValidation,
		ErrorTypeNotFound,
		ErrorTypeConflict,
		ErrorTypeUnauthorized,
		ErrorTypeForbidden,
		ErrorTypeRateLimited,
		ErrorTypeInternal,
		ErrorTypeExternal,
		ErrorTypeTimeout,
		ErrorTypeSpatial,
		ErrorTypeAR,
		ErrorTypeIFC,
		ErrorTypeDatabase,
		ErrorTypeCache,
		ErrorTypeNetwork,
	}

	for _, expectedType := range expectedTypes {
		assert.NotEmpty(t, string(expectedType))
		assert.Contains(t, []string{
			"validation", "not_found", "conflict", "unauthorized", "forbidden",
			"rate_limited", "internal", "external", "timeout", "spatial",
			"ar", "ifc", "database", "cache", "network",
		}, string(expectedType))
	}
}

func TestDomainErrorNilHandling(t *testing.T) {
	var nilErr *DomainError

	// All methods should handle nil gracefully
	assert.Equal(t, "nil domain error", nilErr.Error())
	assert.Nil(t, nilErr.Unwrap())
	assert.False(t, nilErr.IsRetryable())
	assert.Nil(t, nilErr.GetContext())

	// Context methods should handle nil gracefully
	AddEntityContext(nilErr, "Building", "building-123")
	AddOperationContext(nilErr, "create")
	AddTimingContext(nilErr, time.Now())
	AddSpatialContext(nilErr, &SpatialLocation{}, nil)
	AddARContext(nilErr, "session", "ARKit")
	// These should not panic
}

// Benchmark tests for error creation performance

func BenchmarkDomainErrorCreation(b *testing.B) {
	b.ReportAllocs()

	for i := 0; i < b.N; i++ {
		err := NewDomainError(ErrorTypeValidation, "TEST_ERROR", "Test message").
			WithContext("user_id", "123").
			WithContext("operation", "create").
			WithRetryable(true).
			Build()
		_ = err.Error()
	}
}

func BenchmarkDomainErrorString(b *testing.B) {
	err := NewDomainError(ErrorTypeValidation, "TEST_ERROR", "Test message").
		WithCause(errors.New("cause")).
		WithContext("user_id", "123").
		Build()

	b.ReportAllocs()
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_ = err.Error()
	}
}

func BenchmarkErrorTypeCheck(b *testing.B) {
	err := NewValidationError("email", "Invalid format", nil)

	b.ReportAllocs()
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_ = ErrorTypeOf(err)
	}
}
