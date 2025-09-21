package errors

import (
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestSentinelErrors(t *testing.T) {
	tests := []struct {
		name string
		err  error
		is   func(error) bool
	}{
		{"NotFound", ErrNotFound, IsNotFound},
		{"AlreadyExists", ErrAlreadyExists, IsAlreadyExists},
		{"InvalidInput", ErrInvalidInput, IsInvalidInput},
		{"Unauthorized", ErrUnauthorized, IsUnauthorized},
		{"Forbidden", ErrForbidden, IsForbidden},
		{"Internal", ErrInternal, IsInternal},
		{"Timeout", ErrTimeout, IsTimeout},
		{"Canceled", ErrCanceled, IsCanceled},
		{"Database", ErrDatabase, IsDatabase},
		{"NotImplemented", ErrNotImplemented, IsNotImplemented},
		{"Unavailable", ErrUnavailable, IsUnavailable},
		{"RateLimited", ErrRateLimited, IsRateLimited},
		{"QuotaExceeded", ErrQuotaExceeded, IsQuotaExceeded},
		{"Conflict", ErrConflict, IsConflict},
		{"PreconditionFailed", ErrPreconditionFailed, IsPreconditionFailed},
		{"DataCorruption", ErrDataCorruption, IsDataCorruption},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.True(t, tt.is(tt.err))
			assert.False(t, tt.is(errors.New("other error")))
		})
	}
}

func TestFormattedErrors(t *testing.T) {
	tests := []struct {
		name     string
		fn       func(string, ...interface{}) error
		format   string
		args     []interface{}
		checkIs  func(error) bool
		contains string
	}{
		{
			name:     "NotFoundf",
			fn:       NotFoundf,
			format:   "user %s not found",
			args:     []interface{}{"123"},
			checkIs:  IsNotFound,
			contains: "user 123 not found",
		},
		{
			name:     "AlreadyExistsf",
			fn:       AlreadyExistsf,
			format:   "building %s already exists",
			args:     []interface{}{"B001"},
			checkIs:  IsAlreadyExists,
			contains: "building B001 already exists",
		},
		{
			name:     "InvalidInputf",
			fn:       InvalidInputf,
			format:   "invalid floor number: %d",
			args:     []interface{}{-5},
			checkIs:  IsInvalidInput,
			contains: "invalid floor number: -5",
		},
		{
			name:     "Unauthorizedf",
			fn:       Unauthorizedf,
			format:   "token expired for user %s",
			args:     []interface{}{"admin"},
			checkIs:  IsUnauthorized,
			contains: "token expired for user admin",
		},
		{
			name:     "Forbiddenf",
			fn:       Forbiddenf,
			format:   "user %s cannot access building %s",
			args:     []interface{}{"user1", "B002"},
			checkIs:  IsForbidden,
			contains: "user user1 cannot access building B002",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.fn(tt.format, tt.args...)
			assert.Error(t, err)
			assert.True(t, tt.checkIs(err))
			assert.Contains(t, err.Error(), tt.contains)
		})
	}
}

func TestAppError(t *testing.T) {
	t.Run("New", func(t *testing.T) {
		err := New(CodeNotFound, "resource not found")
		assert.NotNil(t, err)
		assert.Equal(t, CodeNotFound, err.Code)
		assert.Equal(t, "resource not found", err.Message)
		assert.NotEmpty(t, err.StackTrace)
	})

	t.Run("WithDetails", func(t *testing.T) {
		err := New(CodeInternal, "processing failed")
		err.WithDetails("database connection timeout")
		assert.Equal(t, "database connection timeout", err.Details)
	})

	t.Run("WithContext", func(t *testing.T) {
		err := New(CodeInvalidInput, "validation failed")
		err.WithContext("field", "email").WithContext("value", "invalid@")
		assert.Equal(t, "email", err.Context["field"])
		assert.Equal(t, "invalid@", err.Context["value"])
	})

	t.Run("Error", func(t *testing.T) {
		err := New(CodeNotFound, "building not found")
		assert.Equal(t, "NOT_FOUND: building not found", err.Error())

		wrapped := Wrap(errors.New("db error"), CodeDatabase, "query failed")
		assert.Contains(t, wrapped.Error(), "DATABASE")
		assert.Contains(t, wrapped.Error(), "query failed")
		assert.Contains(t, wrapped.Error(), "db error")
	})

	t.Run("Unwrap", func(t *testing.T) {
		origErr := errors.New("original error")
		wrapped := Wrap(origErr, CodeInternal, "wrapper message")
		assert.Equal(t, origErr, wrapped.Unwrap())
	})
}

func TestWrap(t *testing.T) {
	t.Run("WrapNil", func(t *testing.T) {
		err := Wrap(nil, CodeInternal, "should be nil")
		assert.Nil(t, err)
	})

	t.Run("WrapError", func(t *testing.T) {
		origErr := errors.New("original")
		wrapped := Wrap(origErr, CodeDatabase, "database operation failed")

		assert.NotNil(t, wrapped)
		assert.Equal(t, CodeDatabase, wrapped.Code)
		assert.Contains(t, wrapped.Message, "database operation failed")
		assert.NotEmpty(t, wrapped.StackTrace)
		assert.Equal(t, origErr, wrapped.Err)
	})

	t.Run("WrapAppError", func(t *testing.T) {
		appErr := New(CodeNotFound, "original message")
		wrapped := Wrap(appErr, CodeInternal, "wrapper message")

		// Should preserve original code and prepend message
		assert.Equal(t, CodeNotFound, wrapped.Code)
		assert.Contains(t, wrapped.Message, "wrapper message")
		assert.Contains(t, wrapped.Message, "original message")
	})
}

func TestGetCode(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected ErrorCode
	}{
		{"AppError", New(CodeNotFound, "test"), CodeNotFound},
		{"SentinelNotFound", ErrNotFound, CodeNotFound},
		{"SentinelUnauthorized", ErrUnauthorized, CodeUnauthorized},
		{"SentinelDatabase", ErrDatabase, CodeDatabase},
		{"UnknownError", errors.New("unknown"), CodeInternal},
		{"WrappedSentinel", NotFoundf("test %s", "123"), CodeNotFound},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			code := GetCode(tt.err)
			assert.Equal(t, tt.expected, code)
		})
	}
}

func TestHTTPStatus(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected int
	}{
		{"NotFound", ErrNotFound, 404},
		{"AlreadyExists", ErrAlreadyExists, 409},
		{"InvalidInput", ErrInvalidInput, 400},
		{"InvalidFormat", New(CodeInvalidFormat, "bad format"), 400},
		{"Unauthorized", ErrUnauthorized, 401},
		{"Forbidden", ErrForbidden, 403},
		{"Timeout", ErrTimeout, 408},
		{"Canceled", ErrCanceled, 499},
		{"RateLimited", ErrRateLimited, 429},
		{"QuotaExceeded", ErrQuotaExceeded, 429},
		{"Conflict", ErrConflict, 409},
		{"PreconditionFailed", ErrPreconditionFailed, 412},
		{"NotImplemented", ErrNotImplemented, 501},
		{"Unavailable", ErrUnavailable, 503},
		{"Database", ErrDatabase, 500},
		{"DataCorruption", ErrDataCorruption, 500},
		{"Internal", ErrInternal, 500},
		{"Unknown", errors.New("unknown"), 500},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			status := HTTPStatus(tt.err)
			assert.Equal(t, tt.expected, status)
		})
	}
}

func TestIsRetryable(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{"Timeout", ErrTimeout, true},
		{"Unavailable", ErrUnavailable, true},
		{"RateLimited", ErrRateLimited, true},
		{"Internal", ErrInternal, true}, // Not fatal, so retryable
		{"Database", ErrDatabase, true}, // Not fatal, so retryable
		{"DataCorruption", ErrDataCorruption, false}, // Fatal
		{"PreconditionFailed", ErrPreconditionFailed, false}, // Fatal
		{"NotFound", ErrNotFound, false},
		{"InvalidInput", ErrInvalidInput, false},
		{"Unauthorized", ErrUnauthorized, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsRetryable(tt.err)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestIsFatal(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{"DataCorruption", ErrDataCorruption, true},
		{"PreconditionFailed", ErrPreconditionFailed, true},
		{"Internal", ErrInternal, false},
		{"Database", ErrDatabase, false},
		{"NotFound", ErrNotFound, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsFatal(tt.err)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestErrorWrapping(t *testing.T) {
	t.Run("ErrorsIs", func(t *testing.T) {
		wrapped := NotFoundf("building %s", "B001")
		assert.True(t, errors.Is(wrapped, ErrNotFound))
		assert.False(t, errors.Is(wrapped, ErrInternal))
	})

	t.Run("ErrorsAs", func(t *testing.T) {
		appErr := New(CodeDatabase, "connection failed")
		wrapped := Wrap(appErr, CodeInternal, "operation failed")

		var target *AppError
		assert.True(t, errors.As(wrapped, &target))
		assert.NotNil(t, target)
	})

	t.Run("MultiLevelWrapping", func(t *testing.T) {
		err1 := errors.New("root cause")
		err2 := Wrap(err1, CodeDatabase, "db layer")
		err3 := Wrap(err2, CodeInternal, "service layer")

		// Should still find the root cause
		assert.Contains(t, err3.Error(), "root cause")
		assert.Contains(t, err3.Error(), "db layer")
		assert.Contains(t, err3.Error(), "service layer")
	})
}

// Benchmarks
func BenchmarkNew(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = New(CodeInternal, "test error")
	}
}

func BenchmarkWrap(b *testing.B) {
	err := errors.New("original")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = Wrap(err, CodeInternal, "wrapped")
	}
}

func BenchmarkGetCode(b *testing.B) {
	err := New(CodeNotFound, "test")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = GetCode(err)
	}
}

func BenchmarkHTTPStatus(b *testing.B) {
	err := New(CodeNotFound, "test")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = HTTPStatus(err)
	}
}

func BenchmarkIsRetryable(b *testing.B) {
	err := ErrTimeout
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = IsRetryable(err)
	}
}

func TestStackTrace(t *testing.T) {
	err := New(CodeInternal, "test error")
	require.NotEmpty(t, err.StackTrace)

	// Should contain this test function
	assert.Contains(t, err.StackTrace, "TestStackTrace")
}