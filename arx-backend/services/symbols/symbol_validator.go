package symbols

import (
	"fmt"
	"regexp"
	"strings"
)

// ValidationError represents a validation error
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("%s: %s", e.Field, e.Message)
}

// ValidationResult represents the result of validation
type ValidationResult struct {
	IsValid bool              `json:"is_valid"`
	Errors  []ValidationError `json:"errors"`
}

// SymbolValidator provides validation for symbol data
type SymbolValidator struct {
	requiredFields []string
	validSystems   []string
}

// NewSymbolValidator creates a new symbol validator
func NewSymbolValidator() *SymbolValidator {
	return &SymbolValidator{
		requiredFields: []string{"name", "system", "svg"},
		validSystems: []string{
			"electrical", "mechanical", "plumbing", "hvac", "fire", "security",
			"audiovisual", "telecommunications", "lighting", "structural",
		},
	}
}

// ValidateSymbol validates symbol data and returns detailed validation results
func (v *SymbolValidator) ValidateSymbol(symbolData map[string]interface{}) error {
	var errors []ValidationError

	// Check required fields
	for _, field := range v.requiredFields {
		if value, exists := symbolData[field]; !exists || value == "" {
			errors = append(errors, ValidationError{
				Field:   field,
				Message: "field is required",
			})
		}
	}

	// Validate name
	if name, exists := symbolData["name"]; exists {
		if err := v.validateName(name); err != nil {
			errors = append(errors, ValidationError{
				Field:   "name",
				Message: err.Error(),
			})
		}
	}

	// Validate system
	if system, exists := symbolData["system"]; exists {
		if err := v.validateSystem(system); err != nil {
			errors = append(errors, ValidationError{
				Field:   "system",
				Message: err.Error(),
			})
		}
	}

	// Validate SVG content
	if svg, exists := symbolData["svg"]; exists {
		if err := v.validateSVG(svg); err != nil {
			errors = append(errors, ValidationError{
				Field:   "svg",
				Message: err.Error(),
			})
		}
	}

	// Validate ID if present
	if id, exists := symbolData["id"]; exists {
		if err := v.validateID(id); err != nil {
			errors = append(errors, ValidationError{
				Field:   "id",
				Message: err.Error(),
			})
		}
	}

	// Validate properties if present
	if properties, exists := symbolData["properties"]; exists {
		if err := v.validateProperties(properties); err != nil {
			errors = append(errors, ValidationError{
				Field:   "properties",
				Message: err.Error(),
			})
		}
	}

	// Validate connections if present
	if connections, exists := symbolData["connections"]; exists {
		if err := v.validateConnections(connections); err != nil {
			errors = append(errors, ValidationError{
				Field:   "connections",
				Message: err.Error(),
			})
		}
	}

	// Validate tags if present
	if tags, exists := symbolData["tags"]; exists {
		if err := v.validateTags(tags); err != nil {
			errors = append(errors, ValidationError{
				Field:   "tags",
				Message: err.Error(),
			})
		}
	}

	// Validate metadata if present
	if metadata, exists := symbolData["metadata"]; exists {
		if err := v.validateMetadata(metadata); err != nil {
			errors = append(errors, ValidationError{
				Field:   "metadata",
				Message: err.Error(),
			})
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("validation failed: %v", errors)
	}

	return nil
}

// ValidateSymbolWithDetails validates symbol data and returns detailed validation results
func (v *SymbolValidator) ValidateSymbolWithDetails(symbolData map[string]interface{}) ValidationResult {
	err := v.ValidateSymbol(symbolData)

	if err != nil {
		// Extract validation errors from error message
		errorStr := err.Error()
		if strings.Contains(errorStr, "validation failed:") {
			// Parse the validation errors from the error message
			// This is a simplified approach - in a real implementation,
			// you might want to return the errors directly
			return ValidationResult{
				IsValid: false,
				Errors: []ValidationError{
					{
						Field:   "validation",
						Message: errorStr,
					},
				},
			}
		}

		return ValidationResult{
			IsValid: false,
			Errors: []ValidationError{
				{
					Field:   "validation",
					Message: err.Error(),
				},
			},
		}
	}

	return ValidationResult{
		IsValid: true,
		Errors:  []ValidationError{},
	}
}

// ValidateBatch validates a batch of symbols and returns detailed validation results
func (v *SymbolValidator) ValidateBatch(symbols []map[string]interface{}) map[string]interface{} {
	results := map[string]interface{}{
		"total_symbols":      len(symbols),
		"valid_symbols":      0,
		"invalid_symbols":    0,
		"validation_details": []map[string]interface{}{},
	}

	for i, symbol := range symbols {
		validationResult := v.ValidateSymbolWithDetails(symbol)

		detail := map[string]interface{}{
			"index":       i,
			"symbol_name": symbol["name"],
			"symbol_id":   symbol["id"],
			"is_valid":    validationResult.IsValid,
			"errors":      validationResult.Errors,
		}

		if validationResult.IsValid {
			results["valid_symbols"] = results["valid_symbols"].(int) + 1
		} else {
			results["invalid_symbols"] = results["invalid_symbols"].(int) + 1
		}

		results["validation_details"] = append(results["validation_details"].([]map[string]interface{}), detail)
	}

	return results
}

// Helper validation methods

func (v *SymbolValidator) validateName(name interface{}) error {
	nameStr, ok := name.(string)
	if !ok {
		return fmt.Errorf("name must be a string")
	}

	if strings.TrimSpace(nameStr) == "" {
		return fmt.Errorf("name cannot be empty")
	}

	if len(nameStr) > 100 {
		return fmt.Errorf("name cannot exceed 100 characters")
	}

	// Check for valid characters
	validNameRegex := regexp.MustCompile(`^[a-zA-Z0-9\s\-_\.]+$`)
	if !validNameRegex.MatchString(nameStr) {
		return fmt.Errorf("name contains invalid characters")
	}

	return nil
}

func (v *SymbolValidator) validateSystem(system interface{}) error {
	systemStr, ok := system.(string)
	if !ok {
		return fmt.Errorf("system must be a string")
	}

	if strings.TrimSpace(systemStr) == "" {
		return fmt.Errorf("system cannot be empty")
	}

	// Check if system is in valid systems list
	systemLower := strings.ToLower(systemStr)
	for _, validSystem := range v.validSystems {
		if systemLower == validSystem {
			return nil
		}
	}

	return fmt.Errorf("system '%s' is not valid. Valid systems: %v", systemStr, v.validSystems)
}

func (v *SymbolValidator) validateSVG(svg interface{}) error {
	svgMap, ok := svg.(map[string]interface{})
	if !ok {
		return fmt.Errorf("svg must be an object")
	}

	// Check for required SVG content
	content, exists := svgMap["content"]
	if !exists || content == "" {
		return fmt.Errorf("svg content is required")
	}

	contentStr, ok := content.(string)
	if !ok {
		return fmt.Errorf("svg content must be a string")
	}

	if strings.TrimSpace(contentStr) == "" {
		return fmt.Errorf("svg content cannot be empty")
	}

	// Basic SVG validation
	if !strings.Contains(contentStr, "<svg") {
		return fmt.Errorf("svg content must contain valid SVG markup")
	}

	// Validate optional SVG properties
	if width, exists := svgMap["width"]; exists {
		if _, ok := width.(float64); !ok {
			return fmt.Errorf("svg width must be a number")
		}
	}

	if height, exists := svgMap["height"]; exists {
		if _, ok := height.(float64); !ok {
			return fmt.Errorf("svg height must be a number")
		}
	}

	if scale, exists := svgMap["scale"]; exists {
		if scaleFloat, ok := scale.(float64); !ok || scaleFloat <= 0 {
			return fmt.Errorf("svg scale must be a positive number")
		}
	}

	return nil
}

func (v *SymbolValidator) validateID(id interface{}) error {
	idStr, ok := id.(string)
	if !ok {
		return fmt.Errorf("id must be a string")
	}

	if strings.TrimSpace(idStr) == "" {
		return fmt.Errorf("id cannot be empty")
	}

	// Check for valid ID format
	validIDRegex := regexp.MustCompile(`^[a-z][a-z0-9_]*$`)
	if !validIDRegex.MatchString(idStr) {
		return fmt.Errorf("id must start with a letter and contain only lowercase letters, numbers, and underscores")
	}

	if len(idStr) > 50 {
		return fmt.Errorf("id cannot exceed 50 characters")
	}

	return nil
}

func (v *SymbolValidator) validateProperties(properties interface{}) error {
	propsMap, ok := properties.(map[string]interface{})
	if !ok {
		return fmt.Errorf("properties must be an object")
	}

	// Validate each property
	for key, value := range propsMap {
		if strings.TrimSpace(key) == "" {
			return fmt.Errorf("property key cannot be empty")
		}

		// Validate property value types
		switch value.(type) {
		case string, float64, bool, nil:
			// Valid types
		case []interface{}:
			// Array is valid
		case map[string]interface{}:
			// Object is valid
		default:
			return fmt.Errorf("property '%s' has invalid value type", key)
		}
	}

	return nil
}

func (v *SymbolValidator) validateConnections(connections interface{}) error {
	connsSlice, ok := connections.([]interface{})
	if !ok {
		return fmt.Errorf("connections must be an array")
	}

	for i, conn := range connsSlice {
		connMap, ok := conn.(map[string]interface{})
		if !ok {
			return fmt.Errorf("connection %d must be an object", i)
		}

		// Validate connection ID
		if id, exists := connMap["id"]; !exists || id == "" {
			return fmt.Errorf("connection %d: id is required", i)
		}

		// Validate connection type
		if connType, exists := connMap["type"]; !exists || connType == "" {
			return fmt.Errorf("connection %d: type is required", i)
		}

		// Validate position
		if position, exists := connMap["position"]; exists {
			if err := v.validatePosition(position); err != nil {
				return fmt.Errorf("connection %d position: %w", i, err)
			}
		}
	}

	return nil
}

func (v *SymbolValidator) validatePosition(position interface{}) error {
	posMap, ok := position.(map[string]interface{})
	if !ok {
		return fmt.Errorf("position must be an object")
	}

	// Validate X coordinate
	if x, exists := posMap["x"]; !exists {
		return fmt.Errorf("position x coordinate is required")
	} else if _, ok := x.(float64); !ok {
		return fmt.Errorf("position x coordinate must be a number")
	}

	// Validate Y coordinate
	if y, exists := posMap["y"]; !exists {
		return fmt.Errorf("position y coordinate is required")
	} else if _, ok := y.(float64); !ok {
		return fmt.Errorf("position y coordinate must be a number")
	}

	return nil
}

func (v *SymbolValidator) validateTags(tags interface{}) error {
	tagsSlice, ok := tags.([]interface{})
	if !ok {
		return fmt.Errorf("tags must be an array")
	}

	for i, tag := range tagsSlice {
		tagStr, ok := tag.(string)
		if !ok {
			return fmt.Errorf("tag %d must be a string", i)
		}

		if strings.TrimSpace(tagStr) == "" {
			return fmt.Errorf("tag %d cannot be empty", i)
		}

		if len(tagStr) > 50 {
			return fmt.Errorf("tag %d cannot exceed 50 characters", i)
		}
	}

	return nil
}

func (v *SymbolValidator) validateMetadata(metadata interface{}) error {
	metadataMap, ok := metadata.(map[string]interface{})
	if !ok {
		return fmt.Errorf("metadata must be an object")
	}

	// Validate metadata values
	for key, value := range metadataMap {
		if strings.TrimSpace(key) == "" {
			return fmt.Errorf("metadata key cannot be empty")
		}

		// Validate metadata value types
		switch value.(type) {
		case string, float64, bool, nil:
			// Valid types
		case []interface{}:
			// Array is valid
		case map[string]interface{}:
			// Object is valid
		default:
			return fmt.Errorf("metadata '%s' has invalid value type", key)
		}
	}

	return nil
}

// SetValidSystems sets the list of valid systems for validation
func (v *SymbolValidator) SetValidSystems(systems []string) {
	v.validSystems = systems
}

// GetValidSystems returns the list of valid systems
func (v *SymbolValidator) GetValidSystems() []string {
	return v.validSystems
}
