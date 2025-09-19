// Package errors provides standardized error handling for ArxOS
package errors

import (
	"errors"
	"fmt"
)

// Standard errors for ArxOS following Go best practices

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
)

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

// Internalf creates a formatted internal error
func Internalf(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrInternal, fmt.Sprintf(format, args...))
}

// Databasef creates a formatted database error
func Databasef(format string, args ...interface{}) error {
	return fmt.Errorf("%w: %s", ErrDatabase, fmt.Sprintf(format, args...))
}

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
	return errors.Is(err, ErrDatabase)
}