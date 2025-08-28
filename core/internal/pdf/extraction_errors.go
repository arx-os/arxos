package pdf

import (
	"fmt"
	"time"
)

// ExtractionError represents a comprehensive error in the extraction pipeline
type ExtractionError struct {
	Operation   string    `json:"operation"`
	Message     string    `json:"message"`
	Cause       error     `json:"cause,omitempty"`
	Timestamp   time.Time `json:"timestamp"`
	Recoverable bool      `json:"recoverable"`
	Context     map[string]interface{} `json:"context,omitempty"`
}

// Error implements the error interface
func (e *ExtractionError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("extraction error in %s: %s (caused by: %v)", e.Operation, e.Message, e.Cause)
	}
	return fmt.Sprintf("extraction error in %s: %s", e.Operation, e.Message)
}

// Unwrap returns the underlying error for error unwrapping
func (e *ExtractionError) Unwrap() error {
	return e.Cause
}

// NewExtractionError creates a new extraction error
func NewExtractionError(operation, message string, cause error) *ExtractionError {
	return &ExtractionError{
		Operation:   operation,
		Message:     message,
		Cause:       cause,
		Timestamp:   time.Now(),
		Recoverable: true,
		Context:     make(map[string]interface{}),
	}
}

// NewFatalExtractionError creates a non-recoverable extraction error
func NewFatalExtractionError(operation, message string, cause error) *ExtractionError {
	return &ExtractionError{
		Operation:   operation,
		Message:     message,
		Cause:       cause,
		Timestamp:   time.Now(),
		Recoverable: false,
		Context:     make(map[string]interface{}),
	}
}

// WithContext adds context information to the error
func (e *ExtractionError) WithContext(key string, value interface{}) *ExtractionError {
	if e.Context == nil {
		e.Context = make(map[string]interface{})
	}
	e.Context[key] = value
	return e
}

// ValidationError represents input validation errors
type ValidationError struct {
	Field   string `json:"field"`
	Value   interface{} `json:"value"`
	Message string `json:"message"`
}

// Error implements the error interface
func (v *ValidationError) Error() string {
	return fmt.Sprintf("validation error for field '%s': %s (value: %v)", v.Field, v.Message, v.Value)
}

// NewValidationError creates a new validation error
func NewValidationError(field string, value interface{}, message string) *ValidationError {
	return &ValidationError{
		Field:   field,
		Value:   value,
		Message: message,
	}
}

// ProcessingError represents errors during object processing
type ProcessingError struct {
	ObjectID string `json:"object_id"`
	ObjectType string `json:"object_type"`
	Stage    string `json:"stage"`
	Message  string `json:"message"`
	Cause    error  `json:"cause,omitempty"`
}

// Error implements the error interface
func (p *ProcessingError) Error() string {
	if p.Cause != nil {
		return fmt.Sprintf("processing error for %s %s at stage %s: %s (caused by: %v)", 
			p.ObjectType, p.ObjectID, p.Stage, p.Message, p.Cause)
	}
	return fmt.Sprintf("processing error for %s %s at stage %s: %s", 
		p.ObjectType, p.ObjectID, p.Stage, p.Message)
}

// NewProcessingError creates a new processing error
func NewProcessingError(objectID, objectType, stage, message string, cause error) *ProcessingError {
	return &ProcessingError{
		ObjectID:   objectID,
		ObjectType: objectType,
		Stage:      stage,
		Message:    message,
		Cause:      cause,
	}
}

// ErrorRecovery provides error recovery strategies
type ErrorRecovery struct {
	MaxRetries      int
	RetryDelay      time.Duration
	FallbackEnabled bool
}

// DefaultErrorRecovery returns default error recovery settings
func DefaultErrorRecovery() *ErrorRecovery {
	return &ErrorRecovery{
		MaxRetries:      3,
		RetryDelay:      100 * time.Millisecond,
		FallbackEnabled: true,
	}
}

// SafeExecute executes a function with error recovery
func (r *ErrorRecovery) SafeExecute(operation string, fn func() error) error {
	var lastErr error
	
	for attempt := 0; attempt <= r.MaxRetries; attempt++ {
		if attempt > 0 && r.RetryDelay > 0 {
			time.Sleep(r.RetryDelay)
		}
		
		if err := fn(); err != nil {
			lastErr = err
			if !r.isRetryable(err) {
				break
			}
			continue
		}
		
		return nil // Success
	}
	
	return NewExtractionError(operation, fmt.Sprintf("failed after %d attempts", r.MaxRetries+1), lastErr)
}

// isRetryable determines if an error is retryable
func (r *ErrorRecovery) isRetryable(err error) bool {
	if extractionErr, ok := err.(*ExtractionError); ok {
		return extractionErr.Recoverable
	}
	return true // Default to retryable for unknown errors
}