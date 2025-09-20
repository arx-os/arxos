// Package errors provides custom error types for ArxOS
package errors

import (
	"errors"
	"fmt"
)

// Common errors
var (
	// ErrNotFound is returned when a resource is not found
	ErrNotFound = errors.New("resource not found")

	// ErrAlreadyExists is returned when trying to create a duplicate resource
	ErrAlreadyExists = errors.New("resource already exists")

	// ErrInvalidInput is returned when input validation fails
	ErrInvalidInput = errors.New("invalid input")

	// ErrUnauthorized is returned when authentication fails
	ErrUnauthorized = errors.New("unauthorized")

	// ErrForbidden is returned when user lacks permission
	ErrForbidden = errors.New("forbidden")

	// ErrInternal is returned for internal server errors
	ErrInternal = errors.New("internal server error")

	// ErrNotImplemented is returned for unimplemented features
	ErrNotImplemented = errors.New("not implemented")

	// ErrDatabaseConnection is returned when database connection fails
	ErrDatabaseConnection = errors.New("database connection failed")

	// ErrTransaction is returned when a transaction fails
	ErrTransaction = errors.New("transaction failed")
)

// ErrorCode represents an error code
type ErrorCode string

const (
	// Database error codes
	CodeDBConnection ErrorCode = "DB_CONNECTION"
	CodeDBQuery      ErrorCode = "DB_QUERY"
	CodeDBTransaction ErrorCode = "DB_TRANSACTION"

	// Resource error codes
	CodeNotFound      ErrorCode = "NOT_FOUND"
	CodeAlreadyExists ErrorCode = "ALREADY_EXISTS"
	CodeInvalidInput  ErrorCode = "INVALID_INPUT"

	// Auth error codes
	CodeUnauthorized ErrorCode = "UNAUTHORIZED"
	CodeForbidden    ErrorCode = "FORBIDDEN"
	CodeTokenExpired ErrorCode = "TOKEN_EXPIRED"

	// Spatial error codes
	CodeInvalidCoordinates ErrorCode = "INVALID_COORDINATES"
	CodeOutOfBounds       ErrorCode = "OUT_OF_BOUNDS"
	CodeSpatialQuery      ErrorCode = "SPATIAL_QUERY"
)

// AppError represents an application error with code and context
type AppError struct {
	Code    ErrorCode              `json:"code"`
	Message string                 `json:"message"`
	Details map[string]interface{} `json:"details,omitempty"`
	Err     error                  `json:"-"`
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

// NewAppError creates a new application error
func NewAppError(code ErrorCode, message string, err error) *AppError {
	return &AppError{
		Code:    code,
		Message: message,
		Err:     err,
		Details: make(map[string]interface{}),
	}
}

// WithDetails adds details to the error
func (e *AppError) WithDetails(key string, value interface{}) *AppError {
	if e.Details == nil {
		e.Details = make(map[string]interface{})
	}
	e.Details[key] = value
	return e
}

// IsNotFound checks if an error is a not found error
func IsNotFound(err error) bool {
	if err == nil {
		return false
	}

	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code == CodeNotFound
	}

	return errors.Is(err, ErrNotFound)
}

// IsUnauthorized checks if an error is an unauthorized error
func IsUnauthorized(err error) bool {
	if err == nil {
		return false
	}

	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code == CodeUnauthorized
	}

	return errors.Is(err, ErrUnauthorized)
}

// WrapDatabaseError wraps a database error with context
func WrapDatabaseError(err error, operation string) error {
	if err == nil {
		return nil
	}

	return NewAppError(CodeDBQuery, fmt.Sprintf("database operation failed: %s", operation), err)
}

// WrapSpatialError wraps a spatial operation error
func WrapSpatialError(err error, operation string) error {
	if err == nil {
		return nil
	}

	return NewAppError(CodeSpatialQuery, fmt.Sprintf("spatial operation failed: %s", operation), err)
}