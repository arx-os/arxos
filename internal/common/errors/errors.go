package errors

import (
	"errors"
	"fmt"
	"runtime"
	"strings"
)

// Error types
var (
	// ErrNotFound indicates a resource was not found
	ErrNotFound = errors.New("resource not found")

	// ErrAlreadyExists indicates a resource already exists
	ErrAlreadyExists = errors.New("resource already exists")

	// ErrInvalidInput indicates invalid input was provided
	ErrInvalidInput = errors.New("invalid input")

	// ErrUnauthorized indicates authentication is required
	ErrUnauthorized = errors.New("unauthorized")

	// ErrForbidden indicates the operation is not allowed
	ErrForbidden = errors.New("forbidden")

	// ErrTimeout indicates an operation timed out
	ErrTimeout = errors.New("operation timed out")

	// ErrCanceled indicates an operation was canceled
	ErrCanceled = errors.New("operation canceled")

	// ErrInternal indicates an internal error occurred
	ErrInternal = errors.New("internal error")

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
)

// ErrorCode represents an error code
type ErrorCode string

const (
	CodeNotFound           ErrorCode = "NOT_FOUND"
	CodeAlreadyExists      ErrorCode = "ALREADY_EXISTS"
	CodeInvalidInput       ErrorCode = "INVALID_INPUT"
	CodeUnauthorized       ErrorCode = "UNAUTHORIZED"
	CodeForbidden          ErrorCode = "FORBIDDEN"
	CodeTimeout            ErrorCode = "TIMEOUT"
	CodeCanceled           ErrorCode = "CANCELED"
	CodeInternal           ErrorCode = "INTERNAL"
	CodeUnavailable        ErrorCode = "UNAVAILABLE"
	CodeRateLimited        ErrorCode = "RATE_LIMITED"
	CodeQuotaExceeded      ErrorCode = "QUOTA_EXCEEDED"
	CodeConflict           ErrorCode = "CONFLICT"
	CodePreconditionFailed ErrorCode = "PRECONDITION_FAILED"
	CodeDataCorruption     ErrorCode = "DATA_CORRUPTION"
)

// AppError represents an application error with context
type AppError struct {
	Code       ErrorCode
	Message    string
	Details    string
	Err        error
	StackTrace string
	Context    map[string]interface{}
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

// New creates a new application error
func New(code ErrorCode, message string) *AppError {
	return &AppError{
		Code:       code,
		Message:    message,
		StackTrace: getStackTrace(2),
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
	}
}

// WrapWithContext wraps an error with context
func WrapWithContext(err error, code ErrorCode, message string, context map[string]interface{}) *AppError {
	appErr := Wrap(err, code, message)
	if appErr != nil {
		appErr.Context = context
	}
	return appErr
}

// Is checks if an error matches a target error
func Is(err error, target error) bool {
	return errors.Is(err, target)
}

// As checks if an error can be cast to a target type
func As(err error, target interface{}) bool {
	return errors.As(err, target)
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
	default:
		return CodeInternal
	}
}

// HTTPStatus returns the HTTP status code for an error
func HTTPStatus(err error) int {
	code := GetCode(err)
	switch code {
	case CodeNotFound:
		return 404
	case CodeAlreadyExists:
		return 409
	case CodeInvalidInput:
		return 400
	case CodeUnauthorized:
		return 401
	case CodeForbidden:
		return 403
	case CodeTimeout:
		return 408
	case CodeCanceled:
		return 499
	case CodeRateLimited:
		return 429
	case CodeQuotaExceeded:
		return 429
	case CodeConflict:
		return 409
	case CodePreconditionFailed:
		return 412
	case CodeUnavailable:
		return 503
	case CodeDataCorruption:
		return 500
	default:
		return 500
	}
}

// IsRetryable checks if an error is retryable
func IsRetryable(err error) bool {
	code := GetCode(err)
	switch code {
	case CodeTimeout, CodeUnavailable, CodeRateLimited:
		return true
	case CodeInternal:
		// Some internal errors might be retryable
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

// ErrorHandler provides centralized error handling
type ErrorHandler struct {
	logFunc    func(string, ...interface{})
	metricFunc func(error)
	alertFunc  func(error)
}

// NewErrorHandler creates a new error handler
func NewErrorHandler() *ErrorHandler {
	return &ErrorHandler{
		logFunc: func(format string, args ...interface{}) {
			// Default to fmt.Printf, should be replaced with logger
			fmt.Printf(format+"\n", args...)
		},
	}
}

// SetLogFunc sets the logging function
func (h *ErrorHandler) SetLogFunc(fn func(string, ...interface{})) {
	h.logFunc = fn
}

// SetMetricFunc sets the metrics function
func (h *ErrorHandler) SetMetricFunc(fn func(error)) {
	h.metricFunc = fn
}

// SetAlertFunc sets the alerting function
func (h *ErrorHandler) SetAlertFunc(fn func(error)) {
	h.alertFunc = fn
}

// Handle handles an error appropriately
func (h *ErrorHandler) Handle(err error) {
	if err == nil {
		return
	}

	// Log the error
	if h.logFunc != nil {
		var appErr *AppError
		if errors.As(err, &appErr) {
			h.logFunc("Error [%s]: %s", appErr.Code, appErr.Error())
			if appErr.StackTrace != "" {
				h.logFunc("Stack trace:\n%s", appErr.StackTrace)
			}
		} else {
			h.logFunc("Error: %v", err)
		}
	}

	// Record metrics
	if h.metricFunc != nil {
		h.metricFunc(err)
	}

	// Send alerts for critical errors
	if h.alertFunc != nil && IsFatal(err) {
		h.alertFunc(err)
	}
}

// ErrorGroup collects multiple errors
type ErrorGroup struct {
	errors []error
}

// NewErrorGroup creates a new error group
func NewErrorGroup() *ErrorGroup {
	return &ErrorGroup{
		errors: make([]error, 0),
	}
}

// Add adds an error to the group
func (eg *ErrorGroup) Add(err error) {
	if err != nil {
		eg.errors = append(eg.errors, err)
	}
}

// Error returns the combined error message
func (eg *ErrorGroup) Error() string {
	if len(eg.errors) == 0 {
		return ""
	}

	var messages []string
	for _, err := range eg.errors {
		messages = append(messages, err.Error())
	}

	return fmt.Sprintf("multiple errors occurred: %s", strings.Join(messages, "; "))
}

// Err returns an error if any errors were added
func (eg *ErrorGroup) Err() error {
	if len(eg.errors) == 0 {
		return nil
	}
	return eg
}

// Count returns the number of errors
func (eg *ErrorGroup) Count() int {
	return len(eg.errors)
}

// Errors returns all errors
func (eg *ErrorGroup) Errors() []error {
	return eg.errors
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

// Sentinel errors for common scenarios

// NotFoundf creates a formatted not found error
func NotFoundf(format string, args ...interface{}) error {
	return Wrap(ErrNotFound, CodeNotFound, fmt.Sprintf(format, args...))
}

// AlreadyExistsf creates a formatted already exists error
func AlreadyExistsf(format string, args ...interface{}) error {
	return Wrap(ErrAlreadyExists, CodeAlreadyExists, fmt.Sprintf(format, args...))
}

// InvalidInputf creates a formatted invalid input error
func InvalidInputf(format string, args ...interface{}) error {
	return Wrap(ErrInvalidInput, CodeInvalidInput, fmt.Sprintf(format, args...))
}

// Internalf creates a formatted internal error
func Internalf(format string, args ...interface{}) error {
	return Wrap(ErrInternal, CodeInternal, fmt.Sprintf(format, args...))
}

// Unauthorizedf creates a formatted unauthorized error
func Unauthorizedf(format string, args ...interface{}) error {
	return Wrap(ErrUnauthorized, CodeUnauthorized, fmt.Sprintf(format, args...))
}

// Forbiddenf creates a formatted forbidden error
func Forbiddenf(format string, args ...interface{}) error {
	return Wrap(ErrForbidden, CodeForbidden, fmt.Sprintf(format, args...))
}