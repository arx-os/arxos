// Package errors provides comprehensive error handling for ArxOS
package errors

import (
	"fmt"
	"runtime"
	"strings"
)

// ErrorType represents different categories of errors
type ErrorType string

const (
	// Database errors
	ErrorTypeDatabase    ErrorType = "database"
	ErrorTypeConnection  ErrorType = "connection"
	ErrorTypeMigration   ErrorType = "migration"
	ErrorTypeQuery       ErrorType = "query"

	// File/IO errors
	ErrorTypeFileIO      ErrorType = "file_io"
	ErrorTypeImport      ErrorType = "import"
	ErrorTypeExport      ErrorType = "export"
	ErrorTypePermission  ErrorType = "permission"

	// Configuration errors
	ErrorTypeConfig      ErrorType = "config"
	ErrorTypeValidation  ErrorType = "validation"
	ErrorTypeAuth        ErrorType = "auth"

	// Network errors
	ErrorTypeNetwork     ErrorType = "network"
	ErrorTypeTimeout     ErrorType = "timeout"
	ErrorTypeAPI         ErrorType = "api"

	// Processing errors
	ErrorTypeProcessing  ErrorType = "processing"
	ErrorTypeConversion  ErrorType = "conversion"
	ErrorTypeParsing     ErrorType = "parsing"

	// System errors
	ErrorTypeSystem      ErrorType = "system"
	ErrorTypeMemory      ErrorType = "memory"
	ErrorTypeDisk        ErrorType = "disk"

	// Business logic errors
	ErrorTypeBusiness    ErrorType = "business"
	ErrorTypeNotFound    ErrorType = "not_found"
	ErrorTypeExists      ErrorType = "exists"
	ErrorTypeConstraint  ErrorType = "constraint"
)

// ArxError represents a comprehensive error in the ArxOS system
type ArxError struct {
	Type        ErrorType              `json:"type"`
	Code        string                 `json:"code"`
	Message     string                 `json:"message"`
	Details     string                 `json:"details,omitempty"`
	Component   string                 `json:"component"`
	Operation   string                 `json:"operation"`
	Cause       error                  `json:"-"`
	Context     map[string]interface{} `json:"context,omitempty"`
	StackTrace  []string              `json:"stack_trace,omitempty"`
	Recoverable bool                  `json:"recoverable"`
}

// Error implements the error interface
func (e *ArxError) Error() string {
	if e.Details != "" {
		return fmt.Sprintf("%s: %s (%s)", e.Message, e.Details, e.Code)
	}
	return fmt.Sprintf("%s (%s)", e.Message, e.Code)
}

// Unwrap returns the underlying cause
func (e *ArxError) Unwrap() error {
	return e.Cause
}

// Is checks if the error matches a target
func (e *ArxError) Is(target error) bool {
	if t, ok := target.(*ArxError); ok {
		return e.Type == t.Type && e.Code == t.Code
	}
	return false
}

// WithContext adds context to the error
func (e *ArxError) WithContext(key string, value interface{}) *ArxError {
	if e.Context == nil {
		e.Context = make(map[string]interface{})
	}
	e.Context[key] = value
	return e
}

// WithStackTrace captures the current stack trace
func (e *ArxError) WithStackTrace() *ArxError {
	e.StackTrace = captureStackTrace()
	return e
}

// New creates a new ArxError
func New(errType ErrorType, code, message string) *ArxError {
	return &ArxError{
		Type:        errType,
		Code:        code,
		Message:     message,
		Component:   getCallerComponent(),
		Recoverable: true,
	}
}

// Wrap wraps an existing error with ArxOS error information
func Wrap(err error, errType ErrorType, code, message string) *ArxError {
	if err == nil {
		return nil
	}

	return &ArxError{
		Type:        errType,
		Code:        code,
		Message:     message,
		Cause:       err,
		Component:   getCallerComponent(),
		Recoverable: true,
	}
}

// Wrapf wraps an error with formatted message
func Wrapf(err error, errType ErrorType, code, format string, args ...interface{}) *ArxError {
	return Wrap(err, errType, code, fmt.Sprintf(format, args...))
}

// Database error constructors

func NewDatabaseError(code, message string) *ArxError {
	return New(ErrorTypeDatabase, code, message).WithStackTrace()
}

func NewConnectionError(message string) *ArxError {
	return New(ErrorTypeConnection, "CONNECTION_FAILED", message).WithStackTrace()
}

func NewQueryError(query, message string) *ArxError {
	return New(ErrorTypeQuery, "QUERY_FAILED", message).
		WithContext("query", query).
		WithStackTrace()
}

func NewMigrationError(version, message string) *ArxError {
	return New(ErrorTypeMigration, "MIGRATION_FAILED", message).
		WithContext("version", version).
		WithStackTrace()
}

// File/IO error constructors

func NewFileIOError(path, operation, message string) *ArxError {
	return New(ErrorTypeFileIO, "FILE_IO_ERROR", message).
		WithContext("path", path).
		WithContext("operation", operation).
		WithStackTrace()
}

func NewImportError(file, message string) *ArxError {
	return New(ErrorTypeImport, "IMPORT_FAILED", message).
		WithContext("file", file).
		WithStackTrace()
}

func NewExportError(format, message string) *ArxError {
	return New(ErrorTypeExport, "EXPORT_FAILED", message).
		WithContext("format", format).
		WithStackTrace()
}

func NewPermissionError(resource, operation string) *ArxError {
	return New(ErrorTypePermission, "PERMISSION_DENIED",
		fmt.Sprintf("Permission denied: %s %s", operation, resource)).
		WithContext("resource", resource).
		WithContext("operation", operation).
		WithStackTrace()
}

// Configuration error constructors

func NewConfigError(key, message string) *ArxError {
	return New(ErrorTypeConfig, "CONFIG_ERROR", message).
		WithContext("key", key).
		WithStackTrace()
}

func NewValidationError(field, message string) *ArxError {
	return New(ErrorTypeValidation, "VALIDATION_FAILED", message).
		WithContext("field", field).
		WithStackTrace()
}

func NewAuthError(message string) *ArxError {
	return New(ErrorTypeAuth, "AUTH_FAILED", message).WithStackTrace()
}

// Network error constructors

func NewNetworkError(endpoint, message string) *ArxError {
	return New(ErrorTypeNetwork, "NETWORK_ERROR", message).
		WithContext("endpoint", endpoint).
		WithStackTrace()
}

func NewTimeoutError(operation, duration string) *ArxError {
	return New(ErrorTypeTimeout, "TIMEOUT", fmt.Sprintf("Operation %s timed out after %s", operation, duration)).
		WithContext("operation", operation).
		WithContext("duration", duration).
		WithStackTrace()
}

func NewAPIError(endpoint, method, message string, statusCode int) *ArxError {
	return New(ErrorTypeAPI, "API_ERROR", message).
		WithContext("endpoint", endpoint).
		WithContext("method", method).
		WithContext("status_code", statusCode).
		WithStackTrace()
}

// Processing error constructors

func NewProcessingError(stage, message string) *ArxError {
	return New(ErrorTypeProcessing, "PROCESSING_FAILED", message).
		WithContext("stage", stage).
		WithStackTrace()
}

func NewConversionError(from, to, message string) *ArxError {
	return New(ErrorTypeConversion, "CONVERSION_FAILED", message).
		WithContext("from", from).
		WithContext("to", to).
		WithStackTrace()
}

func NewParsingError(format, message string) *ArxError {
	return New(ErrorTypeParsing, "PARSING_FAILED", message).
		WithContext("format", format).
		WithStackTrace()
}

// System error constructors

func NewSystemError(message string) *ArxError {
	return New(ErrorTypeSystem, "SYSTEM_ERROR", message).WithStackTrace()
}

func NewMemoryError(message string) *ArxError {
	return New(ErrorTypeMemory, "MEMORY_ERROR", message).WithStackTrace()
}

func NewDiskError(path, message string) *ArxError {
	return New(ErrorTypeDisk, "DISK_ERROR", message).
		WithContext("path", path).
		WithStackTrace()
}

// Business logic error constructors

func NewBusinessError(code, message string) *ArxError {
	return New(ErrorTypeBusiness, code, message).WithStackTrace()
}

func NewNotFoundError(resource, identifier string) *ArxError {
	return New(ErrorTypeNotFound, "NOT_FOUND",
		fmt.Sprintf("%s not found: %s", resource, identifier)).
		WithContext("resource", resource).
		WithContext("identifier", identifier).
		WithStackTrace()
}

func NewExistsError(resource, identifier string) *ArxError {
	return New(ErrorTypeExists, "ALREADY_EXISTS",
		fmt.Sprintf("%s already exists: %s", resource, identifier)).
		WithContext("resource", resource).
		WithContext("identifier", identifier).
		WithStackTrace()
}

func NewConstraintError(constraint, message string) *ArxError {
	return New(ErrorTypeConstraint, "CONSTRAINT_VIOLATION", message).
		WithContext("constraint", constraint).
		WithStackTrace()
}

// Utility functions

// IsRecoverable checks if an error is recoverable
func IsRecoverable(err error) bool {
	if arxErr, ok := err.(*ArxError); ok {
		return arxErr.Recoverable
	}
	return true // Unknown errors are considered recoverable by default
}

// GetErrorType extracts the error type from an error
func GetErrorType(err error) ErrorType {
	if arxErr, ok := err.(*ArxError); ok {
		return arxErr.Type
	}
	return ErrorTypeSystem
}

// GetErrorCode extracts the error code from an error
func GetErrorCode(err error) string {
	if arxErr, ok := err.(*ArxError); ok {
		return arxErr.Code
	}
	return "UNKNOWN_ERROR"
}

// Helper functions

func getCallerComponent() string {
	pc, _, _, ok := runtime.Caller(3)
	if !ok {
		return "unknown"
	}

	funcName := runtime.FuncForPC(pc).Name()
	parts := strings.Split(funcName, "/")
	if len(parts) > 0 {
		lastPart := parts[len(parts)-1]
		if dotIndex := strings.LastIndex(lastPart, "."); dotIndex != -1 {
			return lastPart[:dotIndex]
		}
	}
	return "unknown"
}

func captureStackTrace() []string {
	var trace []string
	for i := 2; i < 10; i++ { // Skip captureStackTrace and WithStackTrace
		pc, file, line, ok := runtime.Caller(i)
		if !ok {
			break
		}

		funcName := runtime.FuncForPC(pc).Name()
		// Simplify file path
		if idx := strings.LastIndex(file, "/"); idx != -1 {
			file = file[idx+1:]
		}

		trace = append(trace, fmt.Sprintf("%s (%s:%d)", funcName, file, line))
	}
	return trace
}

// Error aggregation

// MultiError represents multiple errors
type MultiError struct {
	Errors []error
}

func (m *MultiError) Error() string {
	if len(m.Errors) == 0 {
		return "no errors"
	}
	if len(m.Errors) == 1 {
		return m.Errors[0].Error()
	}

	var messages []string
	for _, err := range m.Errors {
		messages = append(messages, err.Error())
	}
	return fmt.Sprintf("multiple errors: %s", strings.Join(messages, "; "))
}

// Add adds an error to the collection
func (m *MultiError) Add(err error) {
	if err != nil {
		m.Errors = append(m.Errors, err)
	}
}

// HasErrors returns true if there are any errors
func (m *MultiError) HasErrors() bool {
	return len(m.Errors) > 0
}

// ToError returns nil if no errors, otherwise returns the MultiError
func (m *MultiError) ToError() error {
	if !m.HasErrors() {
		return nil
	}
	return m
}

// NewMultiError creates a new MultiError
func NewMultiError() *MultiError {
	return &MultiError{}
}