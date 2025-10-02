// Package validation provides comprehensive validation utilities for ArxOS.
// This package implements business rule validation, data validation,
// and constraint checking for building data and operations.
package validation

import (
	"fmt"
	"reflect"
	"regexp"
	"strings"
	"time"
)

// ValidationError represents a validation error
type ValidationError struct {
	Field   string      `json:"field"`
	Message string      `json:"message"`
	Code    string      `json:"code"`
	Value   interface{} `json:"value,omitempty"`
}

// Error implements the error interface
func (ve *ValidationError) Error() string {
	return fmt.Sprintf("validation failed for field '%s': %s", ve.Field, ve.Message)
}

// ValidationResult represents the result of validation
type ValidationResult struct {
	Valid    bool              `json:"valid"`
	Errors   []ValidationError `json:"errors,omitempty"`
	Warnings []ValidationError `json:"warnings,omitempty"`
}

// IsValid returns true if validation passed
func (vr *ValidationResult) IsValid() bool {
	return vr.Valid && len(vr.Errors) == 0
}

// AddError adds a validation error
func (vr *ValidationResult) AddError(field, message, code string, value interface{}) {
	vr.Errors = append(vr.Errors, ValidationError{
		Field:   field,
		Message: message,
		Code:    code,
		Value:   value,
	})
	vr.Valid = false
}

// AddWarning adds a validation warning
func (vr *ValidationResult) AddWarning(field, message, code string, value interface{}) {
	vr.Warnings = append(vr.Warnings, ValidationError{
		Field:   field,
		Message: message,
		Code:    code,
		Value:   value,
	})
}

// Validator defines the interface for validators
type Validator interface {
	Validate(value interface{}) *ValidationResult
	GetRules() []ValidationRule
}

// ValidationRule represents a single validation rule
type ValidationRule struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Required    bool                   `json:"required"`
	Type        string                 `json:"type"`
	Min         interface{}            `json:"min,omitempty"`
	Max         interface{}            `json:"max,omitempty"`
	Pattern     string                 `json:"pattern,omitempty"`
	Options     []interface{}          `json:"options,omitempty"`
	Custom      func(interface{}) bool `json:"-"`
}

// BaseValidator provides common validation functionality
type BaseValidator struct {
	rules map[string][]ValidationRule
}

// NewBaseValidator creates a new base validator
func NewBaseValidator() *BaseValidator {
	return &BaseValidator{
		rules: make(map[string][]ValidationRule),
	}
}

// AddRule adds a validation rule for a field
func (bv *BaseValidator) AddRule(field string, rule ValidationRule) {
	bv.rules[field] = append(bv.rules[field], rule)
}

// Validate validates a struct against its rules
func (bv *BaseValidator) Validate(value interface{}) *ValidationResult {
	result := &ValidationResult{Valid: true}

	v := reflect.ValueOf(value)
	if v.Kind() == reflect.Ptr {
		v = v.Elem()
	}

	if v.Kind() != reflect.Struct {
		result.AddError("", "value must be a struct", "INVALID_TYPE", value)
		return result
	}

	t := v.Type()

	for i := 0; i < v.NumField(); i++ {
		field := t.Field(i)
		fieldValue := v.Field(i)

		// Skip unexported fields
		if !fieldValue.CanInterface() {
			continue
		}

		fieldName := getFieldName(field)
		rules := bv.rules[fieldName]

		// Validate field
		fieldResult := bv.validateField(fieldName, fieldValue.Interface(), rules)
		if !fieldResult.IsValid() {
			result.Errors = append(result.Errors, fieldResult.Errors...)
			result.Valid = false
		}
		result.Warnings = append(result.Warnings, fieldResult.Warnings...)
	}

	return result
}

// validateField validates a single field against its rules
func (bv *BaseValidator) validateField(fieldName string, value interface{}, rules []ValidationRule) *ValidationResult {
	result := &ValidationResult{Valid: true}

	for _, rule := range rules {
		ruleResult := bv.validateRule(fieldName, value, rule)
		if !ruleResult.IsValid() {
			result.Errors = append(result.Errors, ruleResult.Errors...)
			result.Valid = false
		}
		result.Warnings = append(result.Warnings, ruleResult.Warnings...)
	}

	return result
}

// validateRule validates a field against a single rule
func (bv *BaseValidator) validateRule(fieldName string, value interface{}, rule ValidationRule) *ValidationResult {
	result := &ValidationResult{Valid: true}

	// Check required
	if rule.Required && isEmpty(value) {
		result.AddError(fieldName, "field is required", "REQUIRED", value)
		return result
	}

	// Skip other validations if field is empty and not required
	if isEmpty(value) {
		return result
	}

	// Type validation
	if rule.Type != "" && !bv.validateType(value, rule.Type) {
		result.AddError(fieldName, fmt.Sprintf("field must be of type %s", rule.Type), "INVALID_TYPE", value)
		return result
	}

	// Min/Max validation
	if rule.Min != nil || rule.Max != nil {
		if err := bv.validateRange(value, rule.Min, rule.Max); err != nil {
			result.AddError(fieldName, err.Error(), "INVALID_RANGE", value)
			return result
		}
	}

	// Pattern validation
	if rule.Pattern != "" {
		if err := bv.validatePattern(value, rule.Pattern); err != nil {
			result.AddError(fieldName, err.Error(), "INVALID_PATTERN", value)
			return result
		}
	}

	// Options validation
	if len(rule.Options) > 0 {
		if err := bv.validateOptions(value, rule.Options); err != nil {
			result.AddError(fieldName, err.Error(), "INVALID_OPTION", value)
			return result
		}
	}

	// Custom validation
	if rule.Custom != nil {
		if !rule.Custom(value) {
			result.AddError(fieldName, "custom validation failed", "CUSTOM_VALIDATION", value)
			return result
		}
	}

	return result
}

// validateType validates the type of a value
func (bv *BaseValidator) validateType(value interface{}, expectedType string) bool {
	switch expectedType {
	case "string":
		_, ok := value.(string)
		return ok
	case "int":
		_, ok := value.(int)
		return ok
	case "int64":
		_, ok := value.(int64)
		return ok
	case "float64":
		_, ok := value.(float64)
		return ok
	case "bool":
		_, ok := value.(bool)
		return ok
	case "time":
		_, ok := value.(time.Time)
		return ok
	case "email":
		if str, ok := value.(string); ok {
			return isValidEmail(str)
		}
		return false
	case "uuid":
		if str, ok := value.(string); ok {
			return isValidUUID(str)
		}
		return false
	default:
		return true
	}
}

// validateRange validates the range of a value
func (bv *BaseValidator) validateRange(value interface{}, min, max interface{}) error {
	switch v := value.(type) {
	case int:
		if min != nil {
			if minVal, ok := min.(int); ok && v < minVal {
				return fmt.Errorf("value %d is less than minimum %d", v, minVal)
			}
		}
		if max != nil {
			if maxVal, ok := max.(int); ok && v > maxVal {
				return fmt.Errorf("value %d is greater than maximum %d", v, maxVal)
			}
		}
	case int64:
		if min != nil {
			if minVal, ok := min.(int64); ok && v < minVal {
				return fmt.Errorf("value %d is less than minimum %d", v, minVal)
			}
		}
		if max != nil {
			if maxVal, ok := max.(int64); ok && v > maxVal {
				return fmt.Errorf("value %d is greater than maximum %d", v, maxVal)
			}
		}
	case float64:
		if min != nil {
			if minVal, ok := min.(float64); ok && v < minVal {
				return fmt.Errorf("value %f is less than minimum %f", v, minVal)
			}
		}
		if max != nil {
			if maxVal, ok := max.(float64); ok && v > maxVal {
				return fmt.Errorf("value %f is greater than maximum %f", v, maxVal)
			}
		}
	case string:
		if min != nil {
			if minVal, ok := min.(int); ok && len(v) < minVal {
				return fmt.Errorf("string length %d is less than minimum %d", len(v), minVal)
			}
		}
		if max != nil {
			if maxVal, ok := max.(int); ok && len(v) > maxVal {
				return fmt.Errorf("string length %d is greater than maximum %d", len(v), maxVal)
			}
		}
	}
	return nil
}

// validatePattern validates a value against a regex pattern
func (bv *BaseValidator) validatePattern(value interface{}, pattern string) error {
	str, ok := value.(string)
	if !ok {
		return fmt.Errorf("pattern validation only applies to strings")
	}

	matched, err := regexp.MatchString(pattern, str)
	if err != nil {
		return fmt.Errorf("invalid pattern: %v", err)
	}

	if !matched {
		return fmt.Errorf("value does not match pattern %s", pattern)
	}

	return nil
}

// validateOptions validates that a value is one of the allowed options
func (bv *BaseValidator) validateOptions(value interface{}, options []interface{}) error {
	for _, option := range options {
		if reflect.DeepEqual(value, option) {
			return nil
		}
	}
	return fmt.Errorf("value is not one of the allowed options")
}

// Helper functions

func isEmpty(value interface{}) bool {
	if value == nil {
		return true
	}

	v := reflect.ValueOf(value)
	switch v.Kind() {
	case reflect.String:
		return v.String() == ""
	case reflect.Slice, reflect.Map, reflect.Array:
		return v.Len() == 0
	case reflect.Ptr, reflect.Interface:
		return v.IsNil()
	case reflect.Bool:
		return !v.Bool()
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return v.Int() == 0
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		return v.Uint() == 0
	case reflect.Float32, reflect.Float64:
		return v.Float() == 0
	default:
		return false
	}
}

func getFieldName(field reflect.StructField) string {
	if tag := field.Tag.Get("json"); tag != "" {
		if parts := strings.Split(tag, ","); len(parts) > 0 {
			if parts[0] != "" {
				return parts[0]
			}
		}
	}
	return field.Name
}

func isValidEmail(email string) bool {
	pattern := `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
	matched, _ := regexp.MatchString(pattern, email)
	return matched
}

func isValidUUID(uuid string) bool {
	pattern := `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`
	matched, _ := regexp.MatchString(pattern, strings.ToLower(uuid))
	return matched
}

// GetRules returns all validation rules
func (bv *BaseValidator) GetRules() []ValidationRule {
	var allRules []ValidationRule
	for _, rules := range bv.rules {
		allRules = append(allRules, rules...)
	}
	return allRules
}
