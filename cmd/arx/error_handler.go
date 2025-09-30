package main

import (
	"context"
	"fmt"
	"os"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/errors"
)

// ErrorHandler provides sophisticated error handling patterns for CLI commands
type ErrorHandler struct {
	verbose bool
	dryRun  bool
}

// NewErrorHandler creates a new error handler with configuration
func NewErrorHandler(verbose, dryRun bool) *ErrorHandler {
	return &ErrorHandler{
		verbose: verbose,
		dryRun:  dryRun,
	}
}

// HandleError processes errors with sophisticated patterns including:
// - Structured error logging
// - User-friendly error messages
// - Context-aware error handling
// - Retry suggestions
// - Exit code management
func (eh *ErrorHandler) HandleError(err error, context string) {
	if err == nil {
		return
	}

	// Log the error with full context
	eh.logError(err, context)

	// Display user-friendly error message
	eh.displayUserError(err, context)

	// Provide helpful suggestions
	eh.provideSuggestions(err)

	// Exit with appropriate code
	eh.exitWithCode(err)
}

// HandleValidationError handles input validation errors with specific guidance
func (eh *ErrorHandler) HandleValidationError(err error, field string, value interface{}) {
	if err == nil {
		return
	}

	logger.Error("Validation failed for field '%s' with value '%v': %v", field, value, err)

	fmt.Printf("❌ Validation Error\n")
	fmt.Printf("   Field: %s\n", field)
	fmt.Printf("   Value: %v\n", value)
	fmt.Printf("   Error: %v\n", err)

	// Provide field-specific suggestions
	eh.provideValidationSuggestions(field)

	os.Exit(1)
}

// HandleServiceError handles service-level errors with retry logic
func (eh *ErrorHandler) HandleServiceError(err error, service string, operation string) {
	if err == nil {
		return
	}

	logger.Error("Service error in %s during %s: %v", service, operation, err)

	fmt.Printf("❌ Service Error\n")
	fmt.Printf("   Service: %s\n", service)
	fmt.Printf("   Operation: %s\n", operation)
	fmt.Printf("   Error: %v\n", err)

	// Check if error is retryable
	if errors.IsRetryable(err) {
		fmt.Printf("   💡 This error may be temporary. You can try again.\n")
	}

	// Provide service-specific suggestions
	eh.provideServiceSuggestions(service, operation, err)

	os.Exit(1)
}

// HandleDatabaseError handles database errors with connection status
func (eh *ErrorHandler) HandleDatabaseError(err error, operation string) {
	if err == nil {
		return
	}

	logger.Error("Database error during %s: %v", operation, err)

	fmt.Printf("❌ Database Error\n")
	fmt.Printf("   Operation: %s\n", operation)
	fmt.Printf("   Error: %v\n", err)

	// Check database connection issues
	if errors.IsDatabase(err) {
		fmt.Printf("   💡 Check database connection and try again.\n")
		fmt.Printf("   💡 Ensure database is running and accessible.\n")
	}

	os.Exit(1)
}

// HandleNotFoundError handles not found errors with search suggestions
func (eh *ErrorHandler) HandleNotFoundError(err error, resourceType string, identifier string) {
	if err == nil {
		return
	}

	logger.Error("Resource not found: %s '%s': %v", resourceType, identifier, err)

	fmt.Printf("❌ Not Found\n")
	fmt.Printf("   Resource: %s\n", resourceType)
	fmt.Printf("   Identifier: %s\n", identifier)
	fmt.Printf("   Error: %v\n", err)

	// Provide search suggestions
	fmt.Printf("   💡 Try listing available %ss: arx list %s\n", resourceType, resourceType)
	fmt.Printf("   💡 Check spelling and case sensitivity.\n")

	os.Exit(1)
}

// HandlePermissionError handles permission errors with access suggestions
func (eh *ErrorHandler) HandlePermissionError(err error, resource string, action string) {
	if err == nil {
		return
	}

	logger.Error("Permission denied for %s on %s: %v", action, resource, err)

	fmt.Printf("❌ Permission Denied\n")
	fmt.Printf("   Resource: %s\n", resource)
	fmt.Printf("   Action: %s\n", action)
	fmt.Printf("   Error: %v\n", err)

	fmt.Printf("   💡 Check your authentication and permissions.\n")
	fmt.Printf("   💡 Contact administrator if you need access.\n")

	os.Exit(1)
}

// HandleTimeoutError handles timeout errors with performance suggestions
func (eh *ErrorHandler) HandleTimeoutError(err error, operation string, timeout string) {
	if err == nil {
		return
	}

	logger.Error("Timeout during %s (timeout: %s): %v", operation, timeout, err)

	fmt.Printf("❌ Timeout Error\n")
	fmt.Printf("   Operation: %s\n", operation)
	fmt.Printf("   Timeout: %s\n", timeout)
	fmt.Printf("   Error: %v\n", err)

	fmt.Printf("   💡 Try increasing timeout or reducing data size.\n")
	fmt.Printf("   💡 Check network connectivity and server performance.\n")

	os.Exit(1)
}

// HandleConfigurationError handles configuration errors with setup guidance
func (eh *ErrorHandler) HandleConfigurationError(err error, configFile string) {
	if err == nil {
		return
	}

	logger.Error("Configuration error in %s: %v", configFile, err)

	fmt.Printf("❌ Configuration Error\n")
	fmt.Printf("   File: %s\n", configFile)
	fmt.Printf("   Error: %v\n", err)

	fmt.Printf("   💡 Check configuration file syntax and values.\n")
	fmt.Printf("   💡 Run 'arx config validate' to check configuration.\n")

	os.Exit(1)
}

// Private helper methods

func (eh *ErrorHandler) logError(err error, context string) {
	if eh.verbose {
		logger.Error("Error in %s: %v", context, err)

		// Log stack trace if available
		if appErr, ok := err.(*errors.AppError); ok && appErr.StackTrace != "" {
			logger.Debug("Stack trace: %s", appErr.StackTrace)
		}
	} else {
		logger.Error("Error in %s: %v", context, err)
	}
}

func (eh *ErrorHandler) displayUserError(err error, context string) {
	// Get error code for structured display
	code := errors.GetCode(err)

	fmt.Printf("❌ Error in %s\n", context)
	fmt.Printf("   Code: %s\n", code)
	fmt.Printf("   Message: %v\n", err)

	// Add dry run indicator if applicable
	if eh.dryRun {
		fmt.Printf("   Mode: Dry Run (no changes made)\n")
	}
}

func (eh *ErrorHandler) provideSuggestions(err error) {
	code := errors.GetCode(err)

	switch code {
	case errors.CodeNotFound:
		fmt.Printf("   💡 The requested resource was not found.\n")
		fmt.Printf("   💡 Check spelling and try listing available resources.\n")
	case errors.CodeInvalidInput:
		fmt.Printf("   💡 Check your input parameters and try again.\n")
		fmt.Printf("   💡 Use 'arx help <command>' for usage information.\n")
	case errors.CodeDatabase:
		fmt.Printf("   💡 Database operation failed. Check connection and try again.\n")
	case errors.CodeTimeout:
		fmt.Printf("   💡 Operation timed out. Try again or increase timeout.\n")
	case errors.CodeUnauthorized:
		fmt.Printf("   💡 Authentication required. Check your credentials.\n")
	case errors.CodeForbidden:
		fmt.Printf("   💡 Permission denied. Check your access rights.\n")
	default:
		fmt.Printf("   💡 An unexpected error occurred. Check logs for details.\n")
	}
}

func (eh *ErrorHandler) provideValidationSuggestions(field string) {
	switch field {
	case "name":
		fmt.Printf("   💡 Names should be non-empty and contain valid characters.\n")
	case "id":
		fmt.Printf("   💡 IDs should be valid UUIDs or alphanumeric strings.\n")
	case "location":
		fmt.Printf("   💡 Locations should be in format 'x,y,z' (millimeters).\n")
	case "bounds":
		fmt.Printf("   💡 Bounds should be in format 'minX,minY,maxX,maxY' (millimeters).\n")
	case "email":
		fmt.Printf("   💡 Email should be a valid email address.\n")
	default:
		fmt.Printf("   💡 Check the field format and try again.\n")
	}
}

func (eh *ErrorHandler) provideServiceSuggestions(service string, operation string, err error) {
	switch service {
	case "building":
		fmt.Printf("   💡 Check building service status: arx health\n")
		fmt.Printf("   💡 Verify building exists: arx get building <id>\n")
	case "equipment":
		fmt.Printf("   💡 Check equipment service status: arx health\n")
		fmt.Printf("   💡 List available equipment: arx list equipment\n")
	case "database":
		fmt.Printf("   💡 Check database connection: arx health\n")
		fmt.Printf("   💡 Verify database is running and accessible.\n")
	default:
		fmt.Printf("   💡 Check service status: arx health\n")
	}
}

func (eh *ErrorHandler) exitWithCode(err error) {
	code := errors.GetCode(err)

	switch code {
	case errors.CodeNotFound:
		os.Exit(2) // Not found
	case errors.CodeInvalidInput:
		os.Exit(3) // Invalid input
	case errors.CodeUnauthorized:
		os.Exit(4) // Unauthorized
	case errors.CodeForbidden:
		os.Exit(5) // Forbidden
	case errors.CodeTimeout:
		os.Exit(6) // Timeout
	case errors.CodeDatabase:
		os.Exit(7) // Database error
	default:
		os.Exit(1) // General error
	}
}

// Context-aware error handling functions

// WithContext adds context to error handling
func (eh *ErrorHandler) WithContext(ctx context.Context) *ContextualErrorHandler {
	return &ContextualErrorHandler{
		ErrorHandler: eh,
		ctx:          ctx,
	}
}

// ContextualErrorHandler provides context-aware error handling
type ContextualErrorHandler struct {
	*ErrorHandler
	ctx context.Context
}

// HandleErrorWithContext handles errors with context information
func (ceh *ContextualErrorHandler) HandleErrorWithContext(err error, context string) {
	if err == nil {
		return
	}

	// Add context information to error
	if appErr, ok := err.(*errors.AppError); ok {
		appErr.WithContext("operation_context", context)
		appErr.WithContext("request_id", ceh.getRequestID())
	}

	ceh.HandleError(err, context)
}

func (ceh *ContextualErrorHandler) getRequestID() string {
	// Extract request ID from context if available
	if requestID := ceh.ctx.Value("request_id"); requestID != nil {
		if id, ok := requestID.(string); ok {
			return id
		}
	}
	return "unknown"
}

// Validation helpers

// ValidateAndHandle validates input and handles errors
func (eh *ErrorHandler) ValidateAndHandle(field string, value interface{}, validator func(interface{}) error) {
	if err := validator(value); err != nil {
		eh.HandleValidationError(err, field, value)
	}
}

// Common validators
func ValidateNonEmpty(value interface{}) error {
	if str, ok := value.(string); ok {
		if str == "" {
			return errors.New(errors.CodeInvalidInput, "value cannot be empty")
		}
	}
	return nil
}

func ValidatePositiveNumber(value interface{}) error {
	switch v := value.(type) {
	case int:
		if v <= 0 {
			return errors.New(errors.CodeInvalidInput, "value must be positive")
		}
	case float64:
		if v <= 0 {
			return errors.New(errors.CodeInvalidInput, "value must be positive")
		}
	}
	return nil
}

func ValidateUUID(value interface{}) error {
	if str, ok := value.(string); ok {
		if len(str) != 36 {
			return errors.New(errors.CodeInvalidInput, "invalid UUID format")
		}
	}
	return nil
}
