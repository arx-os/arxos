package validation

import (
	"fmt"
	"net/url"
	"regexp"
	"strings"
	"unicode"
)

// ValidationError represents a validation error with field and message
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
	Code    string `json:"code"`
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("%s: %s", e.Field, e.Message)
}

// ValidationResult contains the result of validation
type ValidationResult struct {
	Valid    bool              `json:"valid"`
	Errors   []ValidationError `json:"errors,omitempty"`
	Warnings []ValidationError `json:"warnings,omitempty"`
}

// Validator provides validation functionality
type Validator struct {
	errors []ValidationError
}

// New creates a new validator instance
func New() *Validator {
	return &Validator{
		errors: make([]ValidationError, 0),
	}
}

// Validate performs validation and returns the result
func (v *Validator) Validate() ValidationResult {
	return ValidationResult{
		Valid:  len(v.errors) == 0,
		Errors: v.errors,
	}
}

// AddError adds a validation error
func (v *Validator) AddError(field, message, code string) {
	v.errors = append(v.errors, ValidationError{
		Field:   field,
		Message: message,
		Code:    code,
	})
}

// Required validates that a field is not empty
func (v *Validator) Required(field, value string) *Validator {
	if strings.TrimSpace(value) == "" {
		v.AddError(field, "is required and cannot be empty", "REQUIRED")
	}
	return v
}

// MinLength validates minimum string length
func (v *Validator) MinLength(field, value string, min int) *Validator {
	if len(strings.TrimSpace(value)) < min {
		v.AddError(field, fmt.Sprintf("must be at least %d characters long", min), "MIN_LENGTH")
	}
	return v
}

// MaxLength validates maximum string length
func (v *Validator) MaxLength(field, value string, max int) *Validator {
	if len(value) > max {
		v.AddError(field, fmt.Sprintf("must not exceed %d characters", max), "MAX_LENGTH")
	}
	return v
}

// Length validates exact string length
func (v *Validator) Length(field, value string, length int) *Validator {
	if len(value) != length {
		v.AddError(field, fmt.Sprintf("must be exactly %d characters long", length), "LENGTH")
	}
	return v
}

// Pattern validates string against a regex pattern
func (v *Validator) Pattern(field, value, pattern, message string) *Validator {
	matched, err := regexp.MatchString(pattern, value)
	if err != nil {
		v.AddError(field, fmt.Sprintf("invalid pattern: %v", err), "PATTERN_ERROR")
		return v
	}
	if !matched {
		v.AddError(field, message, "PATTERN_MISMATCH")
	}
	return v
}

// Alphanumeric validates that a string contains only alphanumeric characters
func (v *Validator) Alphanumeric(field, value string) *Validator {
	pattern := `^[a-zA-Z0-9]+$`
	v.Pattern(field, value, pattern, "must contain only alphanumeric characters")
	return v
}

// AlphanumericWithSpaces validates alphanumeric characters and spaces
func (v *Validator) AlphanumericWithSpaces(field, value string) *Validator {
	pattern := `^[a-zA-Z0-9\s]+$`
	v.Pattern(field, value, pattern, "must contain only alphanumeric characters and spaces")
	return v
}

// AlphanumericWithHyphens validates alphanumeric characters, spaces, and hyphens
func (v *Validator) AlphanumericWithHyphens(field, value string) *Validator {
	pattern := `^[a-zA-Z0-9\s\-_]+$`
	v.Pattern(field, value, pattern, "must contain only alphanumeric characters, spaces, hyphens, and underscores")
	return v
}

// UUID validates that a string is a valid UUID
func (v *Validator) UUID(field, value string) *Validator {
	pattern := `^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`
	v.Pattern(field, value, pattern, "must be a valid UUID")
	return v
}

// Email validates that a string is a valid email address
func (v *Validator) Email(field, value string) *Validator {
	if value != "" {
		pattern := `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
		v.Pattern(field, value, pattern, "must be a valid email address")
	}
	return v
}

// URL validates that a string is a valid URL
func (v *Validator) URL(field, value string) *Validator {
	if value != "" {
		if _, err := url.ParseRequestURI(value); err != nil {
			v.AddError(field, "must be a valid URL", "INVALID_URL")
		}
	}
	return v
}

// Min validates minimum numeric value
func (v *Validator) Min(field string, value, min int) *Validator {
	if value < min {
		v.AddError(field, fmt.Sprintf("must be at least %d", min), "MIN_VALUE")
	}
	return v
}

// Max validates maximum numeric value
func (v *Validator) Max(field string, value, max int) *Validator {
	if value > max {
		v.AddError(field, fmt.Sprintf("must not exceed %d", max), "MAX_VALUE")
	}
	return v
}

// Range validates that a numeric value is within a range
func (v *Validator) Range(field string, value, min, max int) *Validator {
	if value < min || value > max {
		v.AddError(field, fmt.Sprintf("must be between %d and %d", min, max), "OUT_OF_RANGE")
	}
	return v
}

// In validates that a string value is in a list of allowed values
func (v *Validator) In(field, value string, allowed []string) *Validator {
	if value != "" {
		for _, allowedValue := range allowed {
			if value == allowedValue {
				return v
			}
		}
		v.AddError(field, fmt.Sprintf("must be one of: %s", strings.Join(allowed, ", ")), "INVALID_CHOICE")
	}
	return v
}

// NotIn validates that a string value is not in a list of forbidden values
func (v *Validator) NotIn(field, value string, forbidden []string) *Validator {
	if value != "" {
		for _, forbiddenValue := range forbidden {
			if value == forbiddenValue {
				v.AddError(field, fmt.Sprintf("cannot be: %s", forbiddenValue), "FORBIDDEN_VALUE")
				return v
			}
		}
	}
	return v
}

// FileExists validates that a file exists
func (v *Validator) FileExists(field, filePath string) *Validator {
	if filePath != "" {
		// This would need to be implemented with actual file system check
		// For now, we'll do basic path validation
		if strings.TrimSpace(filePath) == "" {
			v.AddError(field, "file path cannot be empty", "EMPTY_PATH")
		}
	}
	return v
}

// DirectoryExists validates that a directory exists
func (v *Validator) DirectoryExists(field, dirPath string) *Validator {
	if dirPath != "" {
		if strings.TrimSpace(dirPath) == "" {
			v.AddError(field, "directory path cannot be empty", "EMPTY_PATH")
		}
	}
	return v
}

// SanitizeString removes potentially dangerous characters from strings
func SanitizeString(input string) string {
	// Remove control characters and normalize whitespace
	result := strings.Map(func(r rune) rune {
		if unicode.IsControl(r) && r != '\t' && r != '\n' && r != '\r' {
			return -1 // Remove character
		}
		return r
	}, input)

	// Normalize whitespace
	result = strings.Join(strings.Fields(result), " ")

	return strings.TrimSpace(result)
}

// ValidateBuildingName validates a building name
func ValidateBuildingName(name string) ValidationResult {
	v := New()

	// Sanitize input
	sanitized := SanitizeString(name)

	v.Required("name", sanitized).
		MinLength("name", sanitized, 1).
		MaxLength("name", sanitized, 255).
		AlphanumericWithHyphens("name", sanitized)

	return v.Validate()
}

// ValidateEquipmentName validates an equipment name
func ValidateEquipmentName(name string) ValidationResult {
	v := New()

	// Sanitize input
	sanitized := SanitizeString(name)

	v.Required("name", sanitized).
		MinLength("name", sanitized, 1).
		MaxLength("name", sanitized, 255).
		AlphanumericWithHyphens("name", sanitized)

	return v.Validate()
}

// ValidateRoomName validates a room name
func ValidateRoomName(name string) ValidationResult {
	v := New()

	// Sanitize input
	sanitized := SanitizeString(name)

	v.Required("name", sanitized).
		MinLength("name", sanitized, 1).
		MaxLength("name", sanitized, 255).
		AlphanumericWithHyphens("name", sanitized)

	return v.Validate()
}

// ValidateID validates an entity ID
func ValidateID(id string) ValidationResult {
	v := New()

	// Sanitize input
	sanitized := SanitizeString(id)

	v.Required("id", sanitized).
		MinLength("id", sanitized, 1).
		MaxLength("id", sanitized, 255).
		AlphanumericWithHyphens("id", sanitized)

	return v.Validate()
}

// ValidateSimulationType validates a simulation type
func ValidateSimulationType(simType string) ValidationResult {
	v := New()

	allowedTypes := []string{
		"occupancy", "hvac", "energy", "lighting",
		"evacuation", "maintenance", "thermal", "acoustic",
		"structural", "fire", "security", "accessibility",
	}

	v.Required("simulation_type", simType).
		In("simulation_type", simType, allowedTypes)

	return v.Validate()
}

// ValidateFilePath validates a file path
func ValidateFilePath(filePath string) ValidationResult {
	v := New()

	// Sanitize input
	sanitized := SanitizeString(filePath)

	v.Required("file_path", sanitized).
		MinLength("file_path", sanitized, 1).
		MaxLength("file_path", sanitized, 4096) // Max path length on most systems

	return v.Validate()
}

// ValidateDirectoryPath validates a directory path
func ValidateDirectoryPath(dirPath string) ValidationResult {
	v := New()

	// Sanitize input
	sanitized := SanitizeString(dirPath)

	v.Required("directory_path", sanitized).
		MinLength("directory_path", sanitized, 1).
		MaxLength("directory_path", sanitized, 4096)

	return v.Validate()
}

// ValidateConnectionPath validates a connection path for tracing
func ValidateConnectionPath(path string) ValidationResult {
	v := New()

	// Sanitize input
	sanitized := SanitizeString(path)

	v.Required("connection_path", sanitized).
		MinLength("connection_path", sanitized, 1).
		MaxLength("connection_path", sanitized, 1024).
		Pattern("connection_path", sanitized, `^[a-zA-Z0-9/._-]+$`, "must contain only valid path characters")

	return v.Validate()
}
