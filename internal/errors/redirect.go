// Package errors redirects to the canonical pkg/errors package.
// This package is DEPRECATED. Use github.com/arx-os/arxos/pkg/errors instead.
//
// This file provides type aliases and function wrappers to maintain backward
// compatibility while encouraging migration to the new package.
package errors

import (
	"github.com/arx-os/arxos/pkg/errors"
)

// Type aliases for backward compatibility
type (
	ErrorCode = errors.ErrorCode
	AppError  = errors.AppError
)

// Sentinel error aliases
var (
	ErrNotFound           = errors.ErrNotFound
	ErrAlreadyExists      = errors.ErrAlreadyExists
	ErrInvalidInput       = errors.ErrInvalidInput
	ErrUnauthorized       = errors.ErrUnauthorized
	ErrForbidden          = errors.ErrForbidden
	ErrInternal           = errors.ErrInternal
	ErrNotImplemented     = errors.ErrNotImplemented
	ErrTimeout            = errors.ErrTimeout
	ErrCanceled           = errors.ErrCanceled
	ErrDatabase           = errors.ErrDatabase
	ErrInvalidFormat      = errors.ErrInvalidFormat
	ErrUnavailable        = errors.ErrUnavailable
	ErrRateLimited        = errors.ErrRateLimited
	ErrQuotaExceeded      = errors.ErrQuotaExceeded
	ErrConflict           = errors.ErrConflict
	ErrPreconditionFailed = errors.ErrPreconditionFailed
	ErrDataCorruption     = errors.ErrDataCorruption
	ErrDatabaseConnection = errors.ErrDatabaseConnection
	ErrTransaction        = errors.ErrTransaction
	ErrInvalidCoordinates = errors.ErrInvalidCoordinates
	ErrOutOfBounds        = errors.ErrOutOfBounds
)

// Error code constants
const (
	CodeNotFound           = errors.CodeNotFound
	CodeAlreadyExists      = errors.CodeAlreadyExists
	CodeInvalidInput       = errors.CodeInvalidInput
	CodeInvalidFormat      = errors.CodeInvalidFormat
	CodeConflict           = errors.CodeConflict
	CodePreconditionFailed = errors.CodePreconditionFailed
	CodeUnauthorized       = errors.CodeUnauthorized
	CodeForbidden          = errors.CodeForbidden
	CodeTokenExpired       = errors.CodeTokenExpired
	CodeInternal           = errors.CodeInternal
	CodeTimeout            = errors.CodeTimeout
	CodeCanceled           = errors.CodeCanceled
	CodeNotImplemented     = errors.CodeNotImplemented
	CodeUnavailable        = errors.CodeUnavailable
	CodeRateLimited        = errors.CodeRateLimited
	CodeQuotaExceeded      = errors.CodeQuotaExceeded
	CodeDataCorruption     = errors.CodeDataCorruption
	CodeDatabase           = errors.CodeDatabase
	CodeDBConnection       = errors.CodeDBConnection
	CodeDBQuery            = errors.CodeDBQuery
	CodeDBTransaction      = errors.CodeDBTransaction
	CodeInvalidCoordinates = errors.CodeInvalidCoordinates
	CodeOutOfBounds        = errors.CodeOutOfBounds
	CodeSpatialQuery       = errors.CodeSpatialQuery
)

// Function wrappers for backward compatibility
var (
	New                = errors.New
	Wrap               = errors.Wrap
	NotFoundf          = errors.NotFoundf
	AlreadyExistsf     = errors.AlreadyExistsf
	InvalidInputf      = errors.InvalidInputf
	Unauthorizedf      = errors.Unauthorizedf
	Forbiddenf         = errors.Forbiddenf
	Internalf          = errors.Internalf
	Databasef          = errors.Databasef
	IsNotFound         = errors.IsNotFound
	IsAlreadyExists    = errors.IsAlreadyExists
	IsInvalidInput     = errors.IsInvalidInput
	IsUnauthorized     = errors.IsUnauthorized
	IsForbidden        = errors.IsForbidden
	IsInternal         = errors.IsInternal
	IsTimeout          = errors.IsTimeout
	IsCanceled         = errors.IsCanceled
	IsDatabase         = errors.IsDatabase
	IsNotImplemented   = errors.IsNotImplemented
	IsUnavailable      = errors.IsUnavailable
	IsRateLimited      = errors.IsRateLimited
	IsQuotaExceeded    = errors.IsQuotaExceeded
	IsConflict         = errors.IsConflict
	IsPreconditionFailed = errors.IsPreconditionFailed
	IsDataCorruption   = errors.IsDataCorruption
	GetCode            = errors.GetCode
	HTTPStatus         = errors.HTTPStatus
	IsRetryable        = errors.IsRetryable
	IsFatal            = errors.IsFatal
)