// Package validation provides request validation using go-playground/validator
package validation

import (
	"fmt"
	"reflect"
	"strings"

	"github.com/go-playground/validator/v10"
)

// Validator wraps go-playground/validator with ArxOS-specific validation rules
type Validator struct {
	validate *validator.Validate
}

// ValidationError represents a single validation error
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
	Tag     string `json:"tag"`
	Value   string `json:"value,omitempty"`
}

// ValidationErrors is a collection of validation errors
type ValidationErrors []ValidationError

// Error implements the error interface
func (ve ValidationErrors) Error() string {
	if len(ve) == 0 {
		return ""
	}

	var messages []string
	for _, err := range ve {
		messages = append(messages, fmt.Sprintf("%s: %s", err.Field, err.Message))
	}
	return strings.Join(messages, "; ")
}

// New creates a new validator instance with custom ArxOS validation rules
func New() *Validator {
	validate := validator.New()

	v := &Validator{validate: validate}

	// Register custom tag name function (use JSON tags for field names)
	validate.RegisterTagNameFunc(func(fld reflect.StructField) string {
		name := strings.SplitN(fld.Tag.Get("json"), ",", 2)[0]
		if name == "-" {
			return ""
		}
		return name
	})

	// Register ArxOS-specific custom validations
	v.registerCustomValidations()

	return v
}

// Struct validates a struct
func (v *Validator) Struct(i interface{}) error {
	err := v.validate.Struct(i)
	if err == nil {
		return nil
	}

	// Convert validator errors to our ValidationError type
	var validationErrors ValidationErrors

	if validatorErrors, ok := err.(validator.ValidationErrors); ok {
		for _, e := range validatorErrors {
			validationErrors = append(validationErrors, ValidationError{
				Field:   e.Field(),
				Message: v.getErrorMessage(e),
				Tag:     e.Tag(),
				Value:   fmt.Sprintf("%v", e.Value()),
			})
		}
	}

	return validationErrors
}

// Var validates a single variable
func (v *Validator) Var(field interface{}, tag string) error {
	return v.validate.Var(field, tag)
}

// getErrorMessage returns a human-readable error message
func (v *Validator) getErrorMessage(e validator.FieldError) string {
	field := e.Field()

	switch e.Tag() {
	case "required":
		return fmt.Sprintf("%s is required", field)
	case "email":
		return fmt.Sprintf("%s must be a valid email address", field)
	case "min":
		return fmt.Sprintf("%s must be at least %s", field, e.Param())
	case "max":
		return fmt.Sprintf("%s must be at most %s", field, e.Param())
	case "len":
		return fmt.Sprintf("%s must be exactly %s characters", field, e.Param())
	case "eq":
		return fmt.Sprintf("%s must equal %s", field, e.Param())
	case "ne":
		return fmt.Sprintf("%s must not equal %s", field, e.Param())
	case "gt":
		return fmt.Sprintf("%s must be greater than %s", field, e.Param())
	case "gte":
		return fmt.Sprintf("%s must be greater than or equal to %s", field, e.Param())
	case "lt":
		return fmt.Sprintf("%s must be less than %s", field, e.Param())
	case "lte":
		return fmt.Sprintf("%s must be less than or equal to %s", field, e.Param())
	case "alpha":
		return fmt.Sprintf("%s must contain only alphabetic characters", field)
	case "alphanum":
		return fmt.Sprintf("%s must contain only alphanumeric characters", field)
	case "numeric":
		return fmt.Sprintf("%s must be a valid numeric value", field)
	case "url":
		return fmt.Sprintf("%s must be a valid URL", field)
	case "uuid":
		return fmt.Sprintf("%s must be a valid UUID", field)
	case "latitude":
		return fmt.Sprintf("%s must be a valid latitude (-90 to 90)", field)
	case "longitude":
		return fmt.Sprintf("%s must be a valid longitude (-180 to 180)", field)
	case "oneof":
		return fmt.Sprintf("%s must be one of: %s", field, e.Param())
	case "arxos_id":
		return fmt.Sprintf("%s must be a valid ArxOS ID (e.g., ARXOS-001)", field)
	case "building_path":
		return fmt.Sprintf("%s must be a valid building path (e.g., /B1/3/A/301)", field)
	case "coordinates":
		return fmt.Sprintf("%s must be valid 3D coordinates (x,y,z)", field)
	case "equipment_status":
		return fmt.Sprintf("%s must be a valid equipment status", field)
	default:
		return fmt.Sprintf("%s failed validation on '%s'", field, e.Tag())
	}
}

// registerCustomValidations registers ArxOS-specific validation rules
func (v *Validator) registerCustomValidations() {
	// ArxOS ID validation (e.g., ARXOS-001 or ARXOS-NA-US-NY-NYC-0001)
	v.validate.RegisterValidation("arxos_id", func(fl validator.FieldLevel) bool {
		value := fl.Field().String()
		if value == "" {
			return true // Let required handle empty values
		}
		// ArxOS ID format: ARXOS- prefix followed by at least 3 characters
		return strings.HasPrefix(value, "ARXOS-") && len(value) >= 9
	})

	// Building path validation (e.g., /B1/3/A/301/HVAC/UNIT-01)
	v.validate.RegisterValidation("building_path", func(fl validator.FieldLevel) bool {
		value := fl.Field().String()
		if value == "" {
			return true
		}
		// Must start with / and contain at least one segment
		parts := strings.Split(value, "/")
		return strings.HasPrefix(value, "/") && len(parts) > 2
	})

	// 3D coordinates validation (x,y,z format or object with x,y,z fields)
	v.validate.RegisterValidation("coordinates", func(fl validator.FieldLevel) bool {
		field := fl.Field()

		// Handle string format: "x,y,z"
		if field.Kind() == reflect.String {
			value := field.String()
			if value == "" {
				return true
			}
			parts := strings.Split(value, ",")
			if len(parts) != 3 {
				return false
			}
			// Verify each part is numeric
			for _, part := range parts {
				var f float64
				_, err := fmt.Sscanf(strings.TrimSpace(part), "%f", &f)
				if err != nil {
					return false
				}
			}
			return true
		}

		// Handle struct with X, Y, Z fields
		if field.Kind() == reflect.Struct {
			xField := field.FieldByName("X")
			yField := field.FieldByName("Y")
			zField := field.FieldByName("Z")

			return xField.IsValid() && yField.IsValid() && zField.IsValid()
		}

		return false
	})

	// Equipment status validation
	v.validate.RegisterValidation("equipment_status", func(fl validator.FieldLevel) bool {
		value := strings.ToUpper(fl.Field().String())
		validStatuses := []string{"OPERATIONAL", "DEGRADED", "FAILED", "MAINTENANCE", "OFFLINE", "UNKNOWN"}
		for _, status := range validStatuses {
			if value == status {
				return true
			}
		}
		return false
	})

	// Building status validation
	v.validate.RegisterValidation("building_status", func(fl validator.FieldLevel) bool {
		value := fl.Field().String()
		validStatuses := []string{"active", "inactive", "maintenance", "construction", "renovation"}
		for _, status := range validStatuses {
			if value == status {
				return true
			}
		}
		return false
	})

	// GPS coordinate range validation
	v.validate.RegisterValidation("gps_latitude", func(fl validator.FieldLevel) bool {
		lat := fl.Field().Float()
		return lat >= -90.0 && lat <= 90.0
	})

	v.validate.RegisterValidation("gps_longitude", func(fl validator.FieldLevel) bool {
		lon := fl.Field().Float()
		return lon >= -180.0 && lon <= 180.0
	})
}

// Global validator instance
var defaultValidator *Validator

// init initializes the default validator
func init() {
	defaultValidator = New()
}

// ValidateStruct validates a struct using the default validator
func ValidateStruct(i interface{}) error {
	return defaultValidator.Struct(i)
}

// ValidateVar validates a variable using the default validator
func ValidateVar(field interface{}, tag string) error {
	return defaultValidator.Var(field, tag)
}
