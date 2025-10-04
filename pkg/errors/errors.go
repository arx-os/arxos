// Package errors provides standardized error handling for ArxOS.
// This is the canonical error package for all ArxOS code.
package errors

import (
	"errors"
	"fmt"
	"net/http"
	"runtime"
	"strings"
)

// Standard sentinel errors for ArxOS following Go best practices
var (
	// ErrNotFound indicates a requested resource was not found
	ErrNotFound = errors.New("not found")

	// ErrAlreadyExists indicates a resource already exists
	ErrAlreadyExists = errors.New("already exists")

	// ErrInvalidInput indicates invalid input was provided
	ErrInvalidInput = errors.New("invalid input")

	// ErrUnauthorized indicates the request lacks valid authentication
	ErrUnauthorized = errors.New("unauthorized")

	// ErrForbidden indicates the request is not allowed for the authenticated user
	ErrForbidden = errors.New("forbidden")

	// ErrInternal indicates an internal server error
	ErrInternal = errors.New("internal error")

	// ErrNotImplemented indicates a feature is not yet implemented
	ErrNotImplemented = errors.New("not implemented")

	// ErrTimeout indicates an operation timed out
	ErrTimeout = errors.New("operation timed out")

	// ErrCanceled indicates an operation was canceled
	ErrCanceled = errors.New("operation canceled")

	// ErrDatabase indicates a database error
	ErrDatabase = errors.New("database error")

	// ErrInvalidFormat indicates invalid data format
	ErrInvalidFormat = errors.New("invalid format")

	// ErrUnavailable indicates a service is unavailable
	ErrUnavailable = errors.New("service unavailable")

	// ErrRateLimited indicates rate limiting is in effect
	ErrRateLimited = errors.New("rate limited")

	// ErrQuotaExceeded indicates a quota was exceeded
	ErrQuotaExceeded = errors.New("quota exceeded")

	// ErrConflict indicates a conflict occurred
	ErrConflict = errors.New("conflict")

	// ErrPreconditionFailed indicates a precondition was not met
	ErrPreconditionFailed = errors.New("precondition failed")

	// ErrDataCorruption indicates data corruption was detected
	ErrDataCorruption = errors.New("data corruption detected")

	// ErrDatabaseConnection is returned when database connection fails
	ErrDatabaseConnection = errors.New("database connection failed")

	// ErrTransaction is returned when a transaction fails
	ErrTransaction = errors.New("transaction failed")

	// ErrInvalidCoordinates indicates invalid spatial coordinates
	ErrInvalidCoordinates = errors.New("invalid coordinates")

	// ErrOutOfBounds indicates coordinates are out of bounds
	ErrOutOfBounds = errors.New("out of bounds")
)

// ErrorCode represents an error code for API responses
type ErrorCode string

const (
	// General error codes
	CodeNotFound           ErrorCode = "NOT_FOUND"
	CodeAlreadyExists      ErrorCode = "ALREADY_EXISTS"
	CodeInvalidInput       ErrorCode = "INVALID_INPUT"
	CodeInvalidFormat      ErrorCode = "INVALID_FORMAT"
	CodeConflict           ErrorCode = "CONFLICT"
	CodePreconditionFailed ErrorCode = "PRECONDITION_FAILED"

	// Auth error codes
	CodeUnauthorized ErrorCode = "UNAUTHORIZED"
	CodeForbidden    ErrorCode = "FORBIDDEN"
	CodeTokenExpired ErrorCode = "TOKEN_EXPIRED"

	// System error codes
	CodeInternal       ErrorCode = "INTERNAL"
	CodeTimeout        ErrorCode = "TIMEOUT"
	CodeCanceled       ErrorCode = "CANCELED"
	CodeNotImplemented ErrorCode = "NOT_IMPLEMENTED"
	CodeUnavailable    ErrorCode = "UNAVAILABLE"
	CodeRateLimited    ErrorCode = "RATE_LIMITED"
	CodeQuotaExceeded  ErrorCode = "QUOTA_EXCEEDED"
	CodeDataCorruption ErrorCode = "DATA_CORRUPTION"

	// Database error codes
	CodeDatabase      ErrorCode = "DATABASE"
	CodeDBConnection  ErrorCode = "DB_CONNECTION"
	CodeDBQuery       ErrorCode = "DB_QUERY"
	CodeDBTransaction ErrorCode = "DB_TRANSACTION"

	// Spatial error codes
	CodeInvalidCoordinates ErrorCode = "INVALID_COORDINATES"
	CodeOutOfBounds        ErrorCode = "OUT_OF_BOUNDS"
	CodeSpatialQuery       ErrorCode = "SPATIAL_QUERY"
)

// AppError represents an application error with additional context
type AppError struct {
	Code       ErrorCode              `json:"code"`
	Message    string                 `json:"message"`
	Details    string                 `json:"details,omitempty"`
	Err        error                  `json:"-"`
	StackTrace string                 `json:"-"`
	Context    map[string]interface{} `json:"context,omitempty"`
}

// Error implements the error interface
func (e *AppError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("%s: %s: %v", e.Code, e.Message, e.Err)
	}
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

// Unwrap returns the wrapped error
func (e *AppError) Unwrap() error {
	return e.Err
}

// WithDetails adds details to the error
func (e *AppError) WithDetails(details string) *AppError {
	e.Details = details
	return e
}

// WithContext adds context to the error
func (e *AppError) WithContext(key string, value interface{}) *AppError {
	if e.Context == nil {
		e.Context = make(map[string]interface{})
	}
	e.Context[key] = value
	return e
}

// New creates a new application error with stack trace
func New(code ErrorCode, message string) *AppError {
	return &AppError{
		Code:       code,
		Message:    message,
		StackTrace: getStackTrace(2),
		Context:    make(map[string]interface{}),
	}
}

// Wrap wraps an error with additional context
func Wrap(err error, code ErrorCode, message string) *AppError {
	if err == nil {
		return nil
	}

	// If already an AppError, preserve the original
	var appErr *AppError
	if errors.As(err, &appErr) {
		appErr.Message = message + ": " + appErr.Message
		return appErr
	}

	return &AppError{
		Code:       code,
		Message:    message,
		Err:        err,
		StackTrace: getStackTrace(2),
		Context:    make(map[string]interface{}),
	}
}

// Formatting functions for common errors

// NotFoundf creates a formatted not found error
func NotFoundf(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrNotFound, fmt.Sprintf(format, args...))
}

// AlreadyExistsf creates a formatted already exists error
func AlreadyExistsf(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrAlreadyExists, fmt.Sprintf(format, args...))
}

// InvalidInputf creates a formatted invalid input error
func InvalidInputf(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrInvalidInput, fmt.Sprintf(format, args...))
}

// Unauthorizedf creates a formatted unauthorized error
func Unauthorizedf(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrUnauthorized, fmt.Sprintf(format, args...))
}

// Forbiddenf creates a formatted forbidden error
func Forbiddenf(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrForbidden, fmt.Sprintf(format, args...))
}

// Internalf creates a formatted internal error
func Internalf(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrInternal, fmt.Sprintf(format, args...))
}

// Databasef creates a formatted database error
func Databasef(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrDatabase, fmt.Sprintf(format, args...))
}

// Error checking functions

// IsNotFound checks if an error is a not found error
func IsNotFound(err error) bool {
	return errors.Is(err, ErrNotFound)
}

// IsAlreadyExists checks if an error is an already exists error
func IsAlreadyExists(err error) bool {
	return errors.Is(err, ErrAlreadyExists)
}

// IsInvalidInput checks if an error is an invalid input error
func IsInvalidInput(err error) bool {
	return errors.Is(err, ErrInvalidInput)
}

// IsUnauthorized checks if an error is an unauthorized error
func IsUnauthorized(err error) bool {
	return errors.Is(err, ErrUnauthorized)
}

// IsForbidden checks if an error is a forbidden error
func IsForbidden(err error) bool {
	return errors.Is(err, ErrForbidden)
}

// IsInternal checks if an error is an internal error
func IsInternal(err error) bool {
	return errors.Is(err, ErrInternal)
}

// IsTimeout checks if an error is a timeout error
func IsTimeout(err error) bool {
	return errors.Is(err, ErrTimeout)
}

// IsCanceled checks if an error is a canceled error
func IsCanceled(err error) bool {
	return errors.Is(err, ErrCanceled)
}

// IsDatabase checks if an error is a database error
func IsDatabase(err error) bool {
	return errors.Is(err, ErrDatabase) || errors.Is(err, ErrDatabaseConnection) || errors.Is(err, ErrTransaction)
}

// IsNotImplemented checks if an error is a not implemented error
func IsNotImplemented(err error) bool {
	return errors.Is(err, ErrNotImplemented)
}

// IsUnavailable checks if an error is a service unavailable error
func IsUnavailable(err error) bool {
	return errors.Is(err, ErrUnavailable)
}

// IsRateLimited checks if an error is a rate limited error
func IsRateLimited(err error) bool {
	return errors.Is(err, ErrRateLimited)
}

// IsQuotaExceeded checks if an error is a quota exceeded error
func IsQuotaExceeded(err error) bool {
	return errors.Is(err, ErrQuotaExceeded)
}

// IsConflict checks if an error is a conflict error
func IsConflict(err error) bool {
	return errors.Is(err, ErrConflict)
}

// IsPreconditionFailed checks if an error is a precondition failed error
func IsPreconditionFailed(err error) bool {
	return errors.Is(err, ErrPreconditionFailed)
}

// IsDataCorruption checks if an error is a data corruption error
func IsDataCorruption(err error) bool {
	return errors.Is(err, ErrDataCorruption)
}

// GetCode returns the error code from an error
func GetCode(err error) ErrorCode {
	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code
	}

	// Map standard errors to codes
	switch {
	case errors.Is(err, ErrNotFound):
		return CodeNotFound
	case errors.Is(err, ErrAlreadyExists):
		return CodeAlreadyExists
	case errors.Is(err, ErrInvalidInput):
		return CodeInvalidInput
	case errors.Is(err, ErrUnauthorized):
		return CodeUnauthorized
	case errors.Is(err, ErrForbidden):
		return CodeForbidden
	case errors.Is(err, ErrTimeout):
		return CodeTimeout
	case errors.Is(err, ErrCanceled):
		return CodeCanceled
	case errors.Is(err, ErrDatabase):
		return CodeDatabase
	case errors.Is(err, ErrDatabaseConnection):
		return CodeDBConnection
	case errors.Is(err, ErrTransaction):
		return CodeDBTransaction
	case errors.Is(err, ErrNotImplemented):
		return CodeNotImplemented
	case errors.Is(err, ErrUnavailable):
		return CodeUnavailable
	case errors.Is(err, ErrRateLimited):
		return CodeRateLimited
	case errors.Is(err, ErrQuotaExceeded):
		return CodeQuotaExceeded
	case errors.Is(err, ErrConflict):
		return CodeConflict
	case errors.Is(err, ErrPreconditionFailed):
		return CodePreconditionFailed
	case errors.Is(err, ErrDataCorruption):
		return CodeDataCorruption
	case errors.Is(err, ErrInvalidFormat):
		return CodeInvalidFormat
	case errors.Is(err, ErrInvalidCoordinates):
		return CodeInvalidCoordinates
	case errors.Is(err, ErrOutOfBounds):
		return CodeOutOfBounds
	default:
		return CodeInternal
	}
}

// HTTPStatus returns the HTTP status code for an error
func HTTPStatus(err error) int {
	code := GetCode(err)
	switch code {
	case CodeNotFound:
		return http.StatusNotFound
	case CodeAlreadyExists:
		return http.StatusConflict
	case CodeInvalidInput, CodeInvalidFormat, CodeInvalidCoordinates, CodeOutOfBounds:
		return http.StatusBadRequest
	case CodeUnauthorized, CodeTokenExpired:
		return http.StatusUnauthorized
	case CodeForbidden:
		return http.StatusForbidden
	case CodeTimeout:
		return http.StatusRequestTimeout
	case CodeCanceled:
		return 499 // Client Closed Request
	case CodeRateLimited, CodeQuotaExceeded:
		return http.StatusTooManyRequests
	case CodeConflict:
		return http.StatusConflict
	case CodePreconditionFailed:
		return http.StatusPreconditionFailed
	case CodeNotImplemented:
		return http.StatusNotImplemented
	case CodeUnavailable:
		return http.StatusServiceUnavailable
	case CodeDatabase, CodeDBConnection, CodeDBQuery, CodeDBTransaction,
		CodeDataCorruption, CodeInternal, CodeSpatialQuery:
		return http.StatusInternalServerError
	default:
		return http.StatusInternalServerError
	}
}

// IsRetryable checks if an error is retryable
func IsRetryable(err error) bool {
	code := GetCode(err)
	switch code {
	case CodeTimeout, CodeUnavailable, CodeRateLimited:
		return true
	case CodeInternal, CodeDatabase, CodeDBConnection:
		// Some internal/database errors might be retryable
		return !IsFatal(err)
	default:
		return false
	}
}

// IsFatal checks if an error is fatal (non-recoverable)
func IsFatal(err error) bool {
	code := GetCode(err)
	switch code {
	case CodeDataCorruption, CodePreconditionFailed:
		return true
	default:
		return false
	}
}

// getStackTrace captures the current stack trace
func getStackTrace(skip int) string {
	var buf strings.Builder
	for i := skip; i < skip+10; i++ {
		pc, file, line, ok := runtime.Caller(i)
		if !ok {
			break
		}

		fn := runtime.FuncForPC(pc)
		if fn == nil {
			continue
		}

		// Skip runtime functions
		fnName := fn.Name()
		if strings.HasPrefix(fnName, "runtime.") {
			continue
		}

		// Format: function_name (file:line)
		buf.WriteString(fmt.Sprintf("  %s\n    %s:%d\n", fnName, file, line))
	}
	return buf.String()
}
