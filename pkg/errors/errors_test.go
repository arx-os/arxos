package errors

import (
	"errors"
	"net/http"
	"testing"
)

func TestSentinelErrors(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want string
	}{
		{"NotFound", ErrNotFound, "not found"},
		{"AlreadyExists", ErrAlreadyExists, "already exists"},
		{"InvalidInput", ErrInvalidInput, "invalid input"},
		{"Unauthorized", ErrUnauthorized, "unauthorized"},
		{"Forbidden", ErrForbidden, "forbidden"},
		{"Internal", ErrInternal, "internal error"},
		{"Database", ErrDatabase, "database error"},
		{"Timeout", ErrTimeout, "operation timed out"},
		{"Canceled", ErrCanceled, "operation canceled"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.err.Error(); got != tt.want {
				t.Errorf("error message = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestFormattingFunctions(t *testing.T) {
	tests := []struct {
		name   string
		fn     func(string, ...interface{}) error
		format string
		args   []interface{}
		want   string
		check  func(error) bool
	}{
		{
			name:   "NotFoundf",
			fn:     NotFoundf,
			format: "user %s",
			args:   []interface{}{"123"},
			want:   "not found: user 123",
			check:  IsNotFound,
		},
		{
			name:   "AlreadyExistsf",
			fn:     AlreadyExistsf,
			format: "building %s",
			args:   []interface{}{"B1"},
			want:   "already exists: building B1",
			check:  IsAlreadyExists,
		},
		{
			name:   "InvalidInputf",
			fn:     InvalidInputf,
			format: "invalid ID %d",
			args:   []interface{}{-1},
			want:   "invalid input: invalid ID -1",
			check:  IsInvalidInput,
		},
		{
			name:   "Unauthorizedf",
			fn:     Unauthorizedf,
			format: "token expired for user %s",
			args:   []interface{}{"admin"},
			want:   "unauthorized: token expired for user admin",
			check:  IsUnauthorized,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.fn(tt.format, tt.args...)
			if got := err.Error(); got != tt.want {
				t.Errorf("error message = %v, want %v", got, tt.want)
			}
			if !tt.check(err) {
				t.Errorf("error check failed for %v", err)
			}
		})
	}
}

func TestAppError(t *testing.T) {
	// Test New
	appErr := New(CodeNotFound, "resource not found")
	if appErr.Code != CodeNotFound {
		t.Errorf("Code = %v, want %v", appErr.Code, CodeNotFound)
	}
	if appErr.Message != "resource not found" {
		t.Errorf("Message = %v, want resource not found", appErr.Message)
	}
	if appErr.StackTrace == "" {
		t.Error("StackTrace should not be empty")
	}

	// Test WithDetails
	appErr.WithDetails("additional info")
	if appErr.Details != "additional info" {
		t.Errorf("Details = %v, want additional info", appErr.Details)
	}

	// Test WithContext
	appErr.WithContext("id", "123").WithContext("type", "building")
	if appErr.Context["id"] != "123" {
		t.Errorf("Context[id] = %v, want 123", appErr.Context["id"])
	}
	if appErr.Context["type"] != "building" {
		t.Errorf("Context[type] = %v, want building", appErr.Context["type"])
	}

	// Test Error() method
	expected := "NOT_FOUND: resource not found"
	if got := appErr.Error(); got != expected {
		t.Errorf("Error() = %v, want %v", got, expected)
	}
}

func TestWrap(t *testing.T) {
	originalErr := errors.New("original error")

	// Test wrapping regular error
	wrapped := Wrap(originalErr, CodeDatabase, "database operation failed")
	if wrapped.Code != CodeDatabase {
		t.Errorf("Code = %v, want %v", wrapped.Code, CodeDatabase)
	}
	if !errors.Is(wrapped, originalErr) {
		t.Error("Should be able to unwrap to original error")
	}

	// Test wrapping nil error
	if Wrap(nil, CodeInternal, "message") != nil {
		t.Error("Wrapping nil should return nil")
	}

	// Test wrapping AppError preserves original
	appErr := New(CodeNotFound, "not found")
	rewrapped := Wrap(appErr, CodeInternal, "additional context")
	if rewrapped.Code != CodeNotFound {
		t.Error("Should preserve original error code")
	}
	if rewrapped.Message != "additional context: not found" {
		t.Errorf("Message = %v, want 'additional context: not found'", rewrapped.Message)
	}
}

func TestGetCode(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want ErrorCode
	}{
		{"AppError", New(CodeNotFound, "test"), CodeNotFound},
		{"ErrNotFound", ErrNotFound, CodeNotFound},
		{"ErrDatabase", ErrDatabase, CodeDatabase},
		{"ErrUnauthorized", ErrUnauthorized, CodeUnauthorized},
		{"ErrTimeout", ErrTimeout, CodeTimeout},
		{"ErrInvalidCoordinates", ErrInvalidCoordinates, CodeInvalidCoordinates},
		{"Unknown", errors.New("unknown"), CodeInternal},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := GetCode(tt.err); got != tt.want {
				t.Errorf("GetCode() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestHTTPStatus(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want int
	}{
		{"NotFound", ErrNotFound, http.StatusNotFound},
		{"AlreadyExists", ErrAlreadyExists, http.StatusConflict},
		{"InvalidInput", ErrInvalidInput, http.StatusBadRequest},
		{"Unauthorized", ErrUnauthorized, http.StatusUnauthorized},
		{"Forbidden", ErrForbidden, http.StatusForbidden},
		{"Timeout", ErrTimeout, http.StatusRequestTimeout},
		{"RateLimited", ErrRateLimited, http.StatusTooManyRequests},
		{"NotImplemented", ErrNotImplemented, http.StatusNotImplemented},
		{"Unavailable", ErrUnavailable, http.StatusServiceUnavailable},
		{"Database", ErrDatabase, http.StatusInternalServerError},
		{"Internal", ErrInternal, http.StatusInternalServerError},
		{"InvalidCoordinates", ErrInvalidCoordinates, http.StatusBadRequest},
		{"Unknown", errors.New("unknown"), http.StatusInternalServerError},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := HTTPStatus(tt.err); got != tt.want {
				t.Errorf("HTTPStatus() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestIsRetryable(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want bool
	}{
		{"Timeout", ErrTimeout, true},
		{"Unavailable", ErrUnavailable, true},
		{"RateLimited", ErrRateLimited, true},
		{"Database", ErrDatabase, true}, // Non-fatal database errors are retryable
		{"NotFound", ErrNotFound, false},
		{"InvalidInput", ErrInvalidInput, false},
		{"DataCorruption", ErrDataCorruption, false}, // Fatal errors are not retryable
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := IsRetryable(tt.err); got != tt.want {
				t.Errorf("IsRetryable() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestIsFatal(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want bool
	}{
		{"DataCorruption", ErrDataCorruption, true},
		{"PreconditionFailed", ErrPreconditionFailed, true},
		{"Database", ErrDatabase, false},
		{"NotFound", ErrNotFound, false},
		{"Internal", ErrInternal, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := IsFatal(tt.err); got != tt.want {
				t.Errorf("IsFatal() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestErrorCheckers(t *testing.T) {
	tests := []struct {
		name    string
		err     error
		checker func(error) bool
		want    bool
	}{
		{"IsNotFound true", ErrNotFound, IsNotFound, true},
		{"IsNotFound false", ErrDatabase, IsNotFound, false},
		{"IsAlreadyExists true", ErrAlreadyExists, IsAlreadyExists, true},
		{"IsInvalidInput true", ErrInvalidInput, IsInvalidInput, true},
		{"IsUnauthorized true", ErrUnauthorized, IsUnauthorized, true},
		{"IsForbidden true", ErrForbidden, IsForbidden, true},
		{"IsInternal true", ErrInternal, IsInternal, true},
		{"IsTimeout true", ErrTimeout, IsTimeout, true},
		{"IsCanceled true", ErrCanceled, IsCanceled, true},
		{"IsDatabase true", ErrDatabase, IsDatabase, true},
		{"IsDatabase connection", ErrDatabaseConnection, IsDatabase, true},
		{"IsDatabase transaction", ErrTransaction, IsDatabase, true},
		{"IsNotImplemented true", ErrNotImplemented, IsNotImplemented, true},
		{"IsUnavailable true", ErrUnavailable, IsUnavailable, true},
		{"IsRateLimited true", ErrRateLimited, IsRateLimited, true},
		{"IsQuotaExceeded true", ErrQuotaExceeded, IsQuotaExceeded, true},
		{"IsConflict true", ErrConflict, IsConflict, true},
		{"IsPreconditionFailed true", ErrPreconditionFailed, IsPreconditionFailed, true},
		{"IsDataCorruption true", ErrDataCorruption, IsDataCorruption, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.checker(tt.err); got != tt.want {
				t.Errorf("checker() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestErrorWrapping(t *testing.T) {
	// Test that wrapped errors still match with errors.Is
	base := ErrNotFound
	wrapped := NotFoundf("user %s", "123")

	if !errors.Is(wrapped, base) {
		t.Error("Wrapped error should match base error with errors.Is")
	}

	if !IsNotFound(wrapped) {
		t.Error("IsNotFound should work with wrapped error")
	}
}

func TestStackTrace(t *testing.T) {
	appErr := New(CodeInternal, "test error")

	// Stack trace should contain this test function
	if appErr.StackTrace == "" {
		t.Error("StackTrace should not be empty")
	}

	// Should not contain runtime functions
	if len(appErr.StackTrace) > 0 && appErr.StackTrace[0:7] == "runtime" {
		t.Error("StackTrace should skip runtime functions")
	}
}
