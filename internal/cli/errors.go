package cli

import (
	"fmt"
	"os"
)

// ErrorHandler provides sophisticated error handling patterns for CLI commands
// following Go Blueprint standards
type ErrorHandler struct {
	verbose bool
	dryRun  bool
	cli     *CLI
}

// NewErrorHandler creates a new error handler with configuration
func NewErrorHandler(cli *CLI, verbose, dryRun bool) *ErrorHandler {
	return &ErrorHandler{
		verbose: verbose,
		dryRun:  dryRun,
		cli:     cli,
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
func (eh *ErrorHandler) HandleValidationError(err error, field, value string) {
	if err == nil {
		return
	}

	eh.cli.LogError("Validation error: field=%s value=%s error=%s", field, value, err.Error())

	fmt.Printf("❌ Validation Error: %s\n", err.Error())
	fmt.Printf("   Field: %s\n", field)
	fmt.Printf("   Value: %s\n", value)

	// Provide field-specific suggestions
	eh.provideValidationSuggestions(field)

	os.Exit(1)
}

// HandleServiceError handles service-level errors with context
func (eh *ErrorHandler) HandleServiceError(err error, service, operation string) {
	if err == nil {
		return
	}

	eh.cli.LogError("Service error: service=%s operation=%s error=%s", service, operation, err.Error())

	fmt.Printf("❌ Service Error: %s\n", err.Error())
	fmt.Printf("   Service: %s\n", service)
	fmt.Printf("   Operation: %s\n", operation)

	// Provide service-specific suggestions
	eh.provideServiceSuggestions(service, operation)

	os.Exit(1)
}

// ValidateAndHandle validates a value and handles errors if validation fails
func (eh *ErrorHandler) ValidateAndHandle(field string, value any, validator func(any) error) {
	if err := validator(value); err != nil {
		eh.HandleValidationError(err, field, fmt.Sprintf("%v", value))
	}
}

// logError logs the error with structured information
func (eh *ErrorHandler) logError(err error, context string) {
	if eh.verbose {
		eh.cli.LogError("Error occurred: context=%s error=%s", context, err.Error())
	}
}

// displayUserError displays a user-friendly error message
func (eh *ErrorHandler) displayUserError(err error, context string) {
	// Extract error code if available
	var errorCode string
	// Note: errors.Error type checking would be implemented when errors package is available

	if errorCode != "" {
		fmt.Printf("❌ Error (%s): %s\n", errorCode, err.Error())
	} else {
		fmt.Printf("❌ Error: %s\n", err.Error())
	}

	if context != "" {
		fmt.Printf("   Context: %s\n", context)
	}
}

// provideSuggestions provides helpful suggestions based on error type
func (eh *ErrorHandler) provideSuggestions(err error) {
	fmt.Println("\n💡 Suggestions:")

	// Note: Error code checking would be implemented when errors package is available
	fmt.Println("   • Use '--verbose' flag for detailed error information")
	fmt.Println("   • Check the documentation for more information")
}

// provideValidationSuggestions provides field-specific validation suggestions
func (eh *ErrorHandler) provideValidationSuggestions(field string) {
	fmt.Println("\n💡 Field-specific suggestions:")

	switch field {
	case "location":
		fmt.Println("   • Format: x,y,z (e.g., 1000,2000,2700)")
		fmt.Println("   • Coordinates in millimeters")
	case "bounds":
		fmt.Println("   • Format: minX,minY,maxX,maxY (e.g., 0,0,20,10)")
		fmt.Println("   • Coordinates in millimeters")
	case "type":
		fmt.Println("   • Equipment: Air Handler, Pump, etc.")
		fmt.Println("   • Room: office, conference, etc.")
	case "level":
		fmt.Println("   • Must be a positive integer")
		fmt.Println("   • Ground floor is typically 1")
	case "height":
		fmt.Println("   • Must be a positive number")
		fmt.Println("   • Height in millimeters")
	default:
		fmt.Println("   • Check the field format requirements")
	}
}

// provideServiceSuggestions provides service-specific suggestions
func (eh *ErrorHandler) provideServiceSuggestions(service, operation string) {
	fmt.Println("\n💡 Service-specific suggestions:")

	switch service {
	case "database":
		fmt.Println("   • Run 'arx health' to check database status")
		fmt.Println("   • Verify database configuration")
		fmt.Println("   • Check database connection string")
	case "building":
		if operation == "create" {
			fmt.Println("   • Check building name format")
			fmt.Println("   • Verify required fields are provided")
		} else if operation == "get" {
			fmt.Println("   • Verify building ID exists")
			fmt.Println("   • Use 'arx list buildings' to see available buildings")
		}
	case "equipment":
		if operation == "create" {
			fmt.Println("   • Check equipment type and location")
			fmt.Println("   • Verify all required fields")
		}
	default:
		fmt.Println("   • Check service configuration")
		fmt.Println("   • Verify service dependencies")
	}
}

// exitWithCode exits with appropriate error code
func (eh *ErrorHandler) exitWithCode(err error) {
	var exitCode int = 1

	// Note: Error code checking would be implemented when errors package is available
	os.Exit(exitCode)
}

// DryRunMode returns true if in dry run mode
func (eh *ErrorHandler) DryRunMode() bool {
	return eh.dryRun
}

// VerboseMode returns true if in verbose mode
func (eh *ErrorHandler) VerboseMode() bool {
	return eh.verbose
}
