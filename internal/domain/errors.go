package domain

import (
	"fmt"
	"time"
)

// Domain error types for better error categorization and handling
type ErrorType string

const (
	ErrorTypeValidation   ErrorType = "validation"
	ErrorTypeNotFound     ErrorType = "not_found"
	ErrorTypeConflict     ErrorType = "conflict"
	ErrorTypeUnauthorized ErrorType = "unauthorized"
	ErrorTypeForbidden    ErrorType = "forbidden"
	ErrorTypeRateLimited  ErrorType = "rate_limited"
	ErrorTypeInternal     ErrorType = "internal"
	ErrorTypeExternal     ErrorType = "external"
	ErrorTypeTimeout      ErrorType = "timeout"
	ErrorTypeSpatial      ErrorType = "spatial"
	ErrorTypeAR           ErrorType = "ar"
	ErrorTypeIFC          ErrorType = "ifc"
	ErrorTypeDatabase     ErrorType = "database"
	ErrorTypeCache        ErrorType = "cache"
	ErrorTypeNetwork      ErrorType = "network"
)

// DomainError represents a domain-specific error with type, message, and context
type DomainError struct {
	Type       ErrorType      `json:"type"`
	Code       string         `json:"code"`
	Message    string         `json:"message"`
	Context    map[string]any `json:"context,omitempty"`
	Cause      error          `json:"cause,omitempty"`
	Timestamp  time.Time      `json:"timestamp"`
	Retryable  bool           `json:"retryable"`
	UserAction string         `json:"user_action,omitempty"`
}

// Error implements the error interface
func (e *DomainError) Error() string {
	if e == nil {
		return "nil domain error"
	}

	if e.Cause != nil {
		return fmt.Sprintf("[%s] %s: %s (%v)", e.Type, e.Code, e.Message, e.Cause)
	}
	return fmt.Sprintf("[%s] %s: %s", e.Type, e.Code, e.Message)
}

// Unwrap returns the underlying cause error
func (e *DomainError) Unwrap() error {
	if e == nil {
		return nil
	}
	return e.Cause
}

// IsRetryable returns whether the error is retryable
func (e *DomainError) IsRetryable() bool {
	if e == nil {
		return false
	}
	return e.Retryable
}

// GetContext returns the error context
func (e *DomainError) GetContext() map[string]any {
	if e == nil {
		return nil
	}
	return e.Context
}

// DomainErrorBuilder provides a fluent interface for building domain errors
type DomainErrorBuilder struct {
	err *DomainError
}

// NewDomainError creates a new domain error builder
func NewDomainError(errorType ErrorType, code, message string) *DomainErrorBuilder {
	return &DomainErrorBuilder{
		err: &DomainError{
			Type:      errorType,
			Code:      code,
			Message:   message,
			Timestamp: time.Now(),
			Context:   make(map[string]any),
		},
	}
}

// WithContext adds context information to the error
func (b *DomainErrorBuilder) WithContext(key string, value any) *DomainErrorBuilder {
	if b.err != nil {
		b.err.Context[key] = value
	}
	return b
}

// WithCause sets the underlying cause error
func (b *DomainErrorBuilder) WithCause(cause error) *DomainErrorBuilder {
	if b.err != nil {
		b.err.Cause = cause
	}
	return b
}

// WithRetryable marks the error as retryable or not
func (b *DomainErrorBuilder) WithRetryable(retryable bool) *DomainErrorBuilder {
	if b.err != nil {
		b.err.Retryable = retryable
	}
	return b
}

// WithUserAction sets the recommended user action
func (b *DomainErrorBuilder) WithUserAction(action string) *DomainErrorBuilder {
	if b.err != nil {
		b.err.UserAction = action
	}
	return b
}

// Build returns the constructed domain error
func (b *DomainErrorBuilder) Build() *DomainError {
	if b.err == nil {
		return nil
	}
	return b.err
}

// Spatial-specific error constructors

// NewSpatialValidationError creates a spatial validation error
func NewSpatialValidationError(message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeSpatial, "SPATIAL_VALIDATION_ERROR", message).
		WithCause(cause).
		WithRetryable(false).
		WithUserAction("Check spatial data validity").
		Build()
}

// NewSpatialAnchorError creates a spatial anchor error
func NewSpatialAnchorError(operation, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeSpatial, "SPATIAL_ANCHOR_"+operation+"_ERROR", message).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Retry spatial anchor operation").
		Build()
}

// NewSpatialCalibrationError creates a spatial calibration error
func NewSpatialCalibrationError(message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeSpatial, "SPATIAL_CALIBRATION_ERROR", message).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Recalibrate spatial system").
		Build()
}

// NewSpatialOutOfBoundsError creates an out of bounds error
func NewSpatialOutOfBoundsError(location *SpatialLocation, bounds any) *DomainError {
	return NewDomainError(ErrorTypeSpatial, "SPATIAL_OUT_OF_BOUNDS", "Spatial location is out of bounds").
		WithContext("location", location).
		WithContext("bounds", bounds).
		WithRetryable(false).
		WithUserAction("Adjust location to be within bounds").
		Build()
}

// AR-specific error constructors

// NewARInitializationError creates an AR initialization error
func NewARInitializationError(platform, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeAR, "AR_INITIALIZATION_ERROR", message).
		WithContext("platform", platform).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Restart AR session").
		Build()
}

// NewARSessionError creates an AR session error
func NewARSessionError(sessionID, operation, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeAR, "AR_SESSION_"+operation+"_ERROR", message).
		WithContext("session_id", sessionID).
		WithCause(cause).
		WithRetryable(true).
		Build()
}

// NewARVisualizationError creates an AR visualization error
func NewARVisualizationError(visualizationType, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeAR, "AR_VISUALIZATION_ERROR", message).
		WithContext("visualization_type", visualizationType).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Check visualization parameters").
		Build()
}

// NewARTrackingError creates an AR tracking error
func NewARTrackingError(message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeAR, "AR_TRACKING_ERROR", message).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Improve lighting conditions and retry").
		Build()
}

// Data validation error constructors

// NewValidationError creates a validation error
func NewValidationError(field, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeValidation, "VALIDATION_ERROR", message).
		WithContext("field", field).
		WithCause(cause).
		WithRetryable(false).
		WithUserAction("Correct the validation error and retry").
		Build()
}

// NewRequiredFieldError creates a required field error
func NewRequiredFieldError(field string) *DomainError {
	return NewDomainError(ErrorTypeValidation, "REQUIRED_FIELD_ERROR", fmt.Sprintf("Field '%s' is required", field)).
		WithContext("field", field).
		WithRetryable(false).
		WithUserAction("Provide the missing field").
		Build()
}

// NewInvalidFormatError creates an invalid format error
func NewInvalidFormatError(field, format string) *DomainError {
	return NewDomainError(ErrorTypeValidation, "INVALID_FORMAT_ERROR", fmt.Sprintf("Field '%s' has invalid format, expected: %s", field, format)).
		WithContext("field", field).
		WithContext("expected_format", format).
		WithRetryable(false).
		WithUserAction("Correct the format and retry").
		Build()
}

// Business logic error constructors

// NewNotFoundError creates a not found error
func NewNotFoundError(resourceType, resourceID string) *DomainError {
	return NewDomainError(ErrorTypeNotFound, "RESOURCE_NOT_FOUND", fmt.Sprintf("%s with ID '%s' not found", resourceType, resourceID)).
		WithContext("resource_type", resourceType).
		WithContext("resource_id", resourceID).
		WithRetryable(false).
		WithUserAction("Check if resource exists or verify ID").
		Build()
}

// NewConflictError creates a conflict error
func NewConflictError(resourceType, resourceID, reason string) *DomainError {
	return NewDomainError(ErrorTypeConflict, "RESOURCE_CONFLICT", fmt.Sprintf("Conflict with %s '%s': %s", resourceType, resourceID, reason)).
		WithContext("resource_type", resourceType).
		WithContext("resource_id", resourceID).
		WithContext("reason", reason).
		WithRetryable(false).
		WithUserAction("Resolve the conflict before retrying").
		Build()
}

// NewUnauthorizedError creates an unauthorized error
func NewUnauthorizedError(action string) *DomainError {
	return NewDomainError(ErrorTypeUnauthorized, "UNAUTHORIZED", fmt.Sprintf("Unauthorized to perform action: %s", action)).
		WithContext("action", action).
		WithRetryable(false).
		WithUserAction("Authenticate or check permissions").
		Build()
}

// NewForbiddenError creates a forbidden error
func NewForbiddenError(action, reason string) *DomainError {
	return NewDomainError(ErrorTypeForbidden, "FORBIDDEN", fmt.Sprintf("Action '%s' is forbidden: %s", action, reason)).
		WithContext("action", action).
		WithContext("reason", reason).
		WithRetryable(false).
		WithUserAction("Check permissions or contact administrator").
		Build()
}

// NewRateLimitError creates a rate limit error
func NewRateLimitError(limit, window string) *DomainError {
	return NewDomainError(ErrorTypeRateLimited, "RATE_LIMITED", fmt.Sprintf("Rate limit exceeded: %s requests per %s", limit, window)).
		WithContext("limit", limit).
		WithContext("window", window).
		WithRetryable(true).
		WithUserAction("Wait before retrying").
		WithUserAction("Reduce request frequency").
		Build()
}

// Infrastructure error constructors

// NewDatabaseError creates a database error
func NewDatabaseError(operation, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeDatabase, "DATABASE_"+operation+"_ERROR", message).
		WithContext("operation", operation).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Check database connection").
		Build()
}

// NewCacheError creates a cache error
func NewCacheError(operation, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeCache, "CACHE_"+operation+"_ERROR", message).
		WithContext("operation", operation).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Check cache service").
		Build()
}

// NewNetworkError creates a network error
func NewNetworkError(operation, endpoint, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeNetwork, "NETWORK_"+operation+"_ERROR", message).
		WithContext("operation", operation).
		WithContext("endpoint", endpoint).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Check network connectivity").
		Build()
}

// NewTimeoutError creates a timeout error
func NewTimeoutError(operation string, timeout time.Duration) *DomainError {
	return NewDomainError(ErrorTypeTimeout, "TIMEOUT_ERROR", fmt.Sprintf("Operation '%s' timed out after %v", operation, timeout)).
		WithContext("operation", operation).
		WithContext("timeout", timeout.String()).
		WithRetryable(true).
		WithUserAction("Increase timeout or reduce operation complexity").
		Build()
}

// IFC-specific error constructors

// NewIFCParsingError creates an IFC parsing error
func NewIFCParsingError(fileName, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeIFC, "IFC_PARSING_ERROR", message).
		WithContext("file_name", fileName).
		WithCause(cause).
		WithRetryable(false).
		WithUserAction("Check IFC file format and validity").
		Build()
}

// NewIFCValidationError creates an IFC validation error
func NewIFCValidationError(fileName, message string) *DomainError {
	return NewDomainError(ErrorTypeIFC, "IFC_VALIDATION_ERROR", message).
		WithContext("file_name", fileName).
		WithRetryable(false).
		WithUserAction("Fix IFC file structure").
		Build()
}

// NewIFCImportError creates an IFC import error
func NewIFCImportError(fileName, repositoryID, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeIFC, "IFC_IMPORT_ERROR", message).
		WithContext("file_name", fileName).
		WithContext("repository_id", repositoryID).
		WithCause(cause).
		WithRetryable(true).
		WithUserAction("Check repository accessibility and retry").
		Build()
}

// Business domain error constructors

// NewBuildingError creates a building-related error
func NewBuildingError(operation, buildingID, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeInternal, "BUILDING_"+operation+"_ERROR", message).
		WithContext("operation", operation).
		WithContext("building_id", buildingID).
		WithCause(cause).
		WithRetryable(true).
		Build()
}

// NewEquipmentError creates an equipment-related error
func NewEquipmentError(operation, equipmentID, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeInternal, "EQUIPMENT_"+operation+"_ERROR", message).
		WithContext("operation", operation).
		WithContext("equipment_id", equipmentID).
		WithCause(cause).
		WithRetryable(true).
		Build()
}

// NewUserError creates a user-related error
func NewUserError(operation, userID, message string, cause error) *DomainError {
	return NewDomainError(ErrorTypeInternal, "USER_"+operation+"_ERROR", message).
		WithContext("operation", operation).
		WithContext("user_id", userID).
		WithCause(cause).
		WithRetryable(true).
		Build()
}

// Error handling utilities

// IsDomainError checks if an error is a domain error
func IsDomainError(err error) bool {
	if err == nil {
		return false
	}
	_, ok := err.(*DomainError)
	return ok
}

// GetDomainError extracts a domain error from an error interface
func GetDomainError(err error) *DomainError {
	if err == nil {
		return nil
	}

	domainErr, ok := err.(*DomainError)
	if ok {
		return domainErr
	}

	// Try to unwrap the error
	if wrapErr, ok := err.(interface{ Unwrap() error }); ok {
		return GetDomainError(wrapErr.Unwrap())
	}

	return nil
}

// IsRetryableError checks if an error is retryable
func IsRetryableError(err error) bool {
	domainErr := GetDomainError(err)
	if domainErr != nil {
		return domainErr.IsRetryable()
	}

	// Default retryable for network/database errors
	return err != nil
}

// ErrorTypeOf returns the error type of an error
func ErrorTypeOf(err error) ErrorType {
	domainErr := GetDomainError(err)
	if domainErr != nil {
		return domainErr.Type
	}
	return ErrorTypeInternal
}

// WrapError wraps a regular error as a domain error with the specified type and message
func WrapError(err error, errorType ErrorType, code, message string) *DomainError {
	if err == nil {
		return nil
	}

	return NewDomainError(errorType, code, message).
		WithCause(err).
		WithRetryable(IsRetryableError(err)).
		Build()
}

// Error context utilities for common scenarios

// AddEntityContext adds entity information to error context
func AddEntityContext(e *DomainError, entityType, entityID string) {
	if e != nil && e.Context != nil {
		e.Context["entity_type"] = entityType
		e.Context["entity_id"] = entityID
	}
}

// AddOperationContext adds operation information to error context
func AddOperationContext(e *DomainError, operation string) {
	if e != nil && e.Context != nil {
		e.Context["operation"] = operation
	}
}

// AddTimingContext adds timing information to error context
func AddTimingContext(e *DomainError, startTime time.Time) {
	if e != nil && e.Context != nil {
		e.Context["duration"] = time.Since(startTime).String()
	}
}

// AddSpatialContext adds spatial information to error context
func AddSpatialContext(e *DomainError, location *SpatialLocation, bounds any) {
	if e != nil && e.Context != nil {
		e.Context["location"] = location
		e.Context["bounds"] = bounds
	}
}

// AddARContext adds AR information to error context
func AddARContext(e *DomainError, sessionID, platform string) {
	if e != nil && e.Context != nil {
		e.Context["ar_session_id"] = sessionID
		e.Context["ar_platform"] = platform
	}
}
