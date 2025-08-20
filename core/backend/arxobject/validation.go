package arxobject

import (
	"encoding/json"
	"fmt"
	"math"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"
)

// ValidationConfig contains validation parameters
type ValidationConfig struct {
	MaxIDLength         int     `json:"max_id_length"`
	MaxStringLength     int     `json:"max_string_length"`
	MaxPropertiesSize   int     `json:"max_properties_size"`
	MinConfidence       float32 `json:"min_confidence"`
	MaxConfidence       float32 `json:"max_confidence"`
	MaxCoordinate       int64   `json:"max_coordinate"`       // In nanometers
	MinDimension        int64   `json:"min_dimension"`        // In nanometers
	MaxDimension        int64   `json:"max_dimension"`        // In nanometers
	AllowedTypes        []string `json:"allowed_types"`
	AllowedSystems      []string `json:"allowed_systems"`
	RequiredFields      []string `json:"required_fields"`
}

// DefaultValidationConfig returns default validation settings
func DefaultValidationConfig() *ValidationConfig {
	return &ValidationConfig{
		MaxIDLength:       100,
		MaxStringLength:   500,
		MaxPropertiesSize: 10240, // 10KB
		MinConfidence:     0.0,
		MaxConfidence:     1.0,
		MaxCoordinate:     int64(1000 * 1e9), // 1000 meters in nanometers
		MinDimension:      int64(1 * 1e6),    // 1mm in nanometers  
		MaxDimension:      int64(1000 * 1e9), // 1000 meters in nanometers
		AllowedTypes: []string{
			"wall", "door", "window", "column", "beam", "foundation",
			"hvac_unit", "hvac_duct", "hvac_diffuser", "hvac_return",
			"electrical_panel", "electrical_outlet", "electrical_switch", 
			"electrical_light", "electrical_conduit",
			"plumbing_fixture", "plumbing_pipe", "plumbing_valve",
			"fire_sprinkler", "fire_extinguisher", "fire_alarm", "smoke_detector",
			"room", "space", "dimension", "annotation", "grid", "reference",
		},
		AllowedSystems: []string{
			"structural", "architectural", "hvac", "electrical", 
			"plumbing", "fire_safety", "spatial", "annotation", "reference",
		},
		RequiredFields: []string{"ID", "Type", "System"},
	}
}

// ArxObjectValidator provides comprehensive validation for ArxObjects
type ArxObjectValidator struct {
	config   *ValidationConfig
	idRegex  *regexp.Regexp
	typeRegex *regexp.Regexp
}

// NewArxObjectValidator creates a new validator with the given config
func NewArxObjectValidator(config *ValidationConfig) *ArxObjectValidator {
	if config == nil {
		config = DefaultValidationConfig()
	}

	return &ArxObjectValidator{
		config:    config,
		idRegex:   regexp.MustCompile(`^[a-zA-Z0-9_\-]+$`),
		typeRegex: regexp.MustCompile(`^[a-z_]+$`),
	}
}

// ValidationResult contains validation results and sanitized data
type ValidationResult struct {
	IsValid      bool                   `json:"is_valid"`
	Errors       []ValidationError      `json:"errors"`
	Warnings     []ValidationWarning    `json:"warnings"`
	SanitizedObj *ArxObject            `json:"sanitized_object,omitempty"`
}

// ValidationError represents a validation error
type ValidationError struct {
	Field    string `json:"field"`
	Code     string `json:"code"`
	Message  string `json:"message"`
	Value    interface{} `json:"value,omitempty"`
}

// ValidationWarning represents a validation warning
type ValidationWarning struct {
	Field   string `json:"field"`
	Message string `json:"message"`
	Action  string `json:"action"`
}

// ValidateAndSanitize performs comprehensive validation and sanitization
func (v *ArxObjectValidator) ValidateAndSanitize(obj *ArxObject) *ValidationResult {
	result := &ValidationResult{
		IsValid:  true,
		Errors:   make([]ValidationError, 0),
		Warnings: make([]ValidationWarning, 0),
	}

	if obj == nil {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "object",
			Code:    "NULL_OBJECT",
			Message: "ArxObject cannot be nil",
		})
		return result
	}

	// Create a copy for sanitization
	sanitized := *obj

	// Validate and sanitize each field
	v.validateID(&sanitized, result)
	v.validateUUID(&sanitized, result)
	v.validateType(&sanitized, result)
	v.validateSystem(&sanitized, result)
	v.validateCoordinates(&sanitized, result)
	v.validateDimensions(&sanitized, result)
	v.validateConfidence(&sanitized, result)
	v.validateProperties(&sanitized, result)
	v.validateTimestamps(&sanitized, result)
	v.validateStringFields(&sanitized, result)

	// Check required fields
	v.validateRequiredFields(&sanitized, result)

	if result.IsValid {
		result.SanitizedObj = &sanitized
	}

	return result
}

// validateID validates and sanitizes the ID field
func (v *ArxObjectValidator) validateID(obj *ArxObject, result *ValidationResult) {
	if obj.ID == "" {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "ID",
			Code:    "REQUIRED_FIELD",
			Message: "ID is required",
		})
		return
	}

	// Sanitize ID
	obj.ID = strings.TrimSpace(obj.ID)
	
	// Validate length
	if len(obj.ID) > v.config.MaxIDLength {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "ID",
			Code:    "MAX_LENGTH_EXCEEDED",
			Message: fmt.Sprintf("ID length exceeds maximum of %d characters", v.config.MaxIDLength),
			Value:   len(obj.ID),
		})
		return
	}

	// Validate format
	if !v.idRegex.MatchString(obj.ID) {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "ID",
			Code:    "INVALID_FORMAT",
			Message: "ID contains invalid characters. Only letters, numbers, underscores, and hyphens are allowed",
			Value:   obj.ID,
		})
	}

	// Validate UTF-8
	if !utf8.ValidString(obj.ID) {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "ID",
			Code:    "INVALID_ENCODING",
			Message: "ID contains invalid UTF-8 characters",
		})
	}
}

// validateUUID validates the UUID field
func (v *ArxObjectValidator) validateUUID(obj *ArxObject, result *ValidationResult) {
	if obj.UUID == "" {
		// Generate UUID if missing
		obj.UUID = generateUUID()
		result.Warnings = append(result.Warnings, ValidationWarning{
			Field:   "UUID",
			Message: "UUID was missing and has been generated",
			Action:  "generated",
		})
		return
	}

	// Sanitize UUID
	obj.UUID = strings.TrimSpace(obj.UUID)
	obj.UUID = strings.ToLower(obj.UUID)

	// Validate UUID format
	uuidRegex := regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)
	if !uuidRegex.MatchString(obj.UUID) {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "UUID",
			Code:    "INVALID_FORMAT",
			Message: "UUID format is invalid",
			Value:   obj.UUID,
		})
	}
}

// validateType validates and sanitizes the Type field
func (v *ArxObjectValidator) validateType(obj *ArxObject, result *ValidationResult) {
	if obj.Type == "" {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "Type",
			Code:    "REQUIRED_FIELD",
			Message: "Type is required",
		})
		return
	}

	// Sanitize type
	obj.Type = strings.TrimSpace(strings.ToLower(obj.Type))

	// Validate against allowed types
	allowed := false
	for _, allowedType := range v.config.AllowedTypes {
		if obj.Type == allowedType {
			allowed = true
			break
		}
	}

	if !allowed {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "Type",
			Code:    "INVALID_VALUE",
			Message: fmt.Sprintf("Type '%s' is not allowed", obj.Type),
			Value:   obj.Type,
		})
	}

	// Validate format
	if !v.typeRegex.MatchString(obj.Type) {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "Type",
			Code:    "INVALID_FORMAT",
			Message: "Type contains invalid characters. Only lowercase letters and underscores are allowed",
			Value:   obj.Type,
		})
	}
}

// validateSystem validates and sanitizes the System field
func (v *ArxObjectValidator) validateSystem(obj *ArxObject, result *ValidationResult) {
	if obj.System == "" {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "System",
			Code:    "REQUIRED_FIELD",
			Message: "System is required",
		})
		return
	}

	// Sanitize system
	obj.System = strings.TrimSpace(strings.ToLower(obj.System))

	// Validate against allowed systems
	allowed := false
	for _, allowedSystem := range v.config.AllowedSystems {
		if obj.System == allowedSystem {
			allowed = true
			break
		}
	}

	if !allowed {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "System",
			Code:    "INVALID_VALUE",
			Message: fmt.Sprintf("System '%s' is not allowed", obj.System),
			Value:   obj.System,
		})
	}
}

// validateCoordinates validates coordinate values
func (v *ArxObjectValidator) validateCoordinates(obj *ArxObject, result *ValidationResult) {
	coords := []struct {
		name  string
		value *int64
	}{
		{"X", &obj.X},
		{"Y", &obj.Y},
		{"Z", &obj.Z},
	}

	for _, coord := range coords {
		if math.Abs(float64(*coord.value)) > float64(v.config.MaxCoordinate) {
			result.IsValid = false
			result.Errors = append(result.Errors, ValidationError{
				Field:   coord.name,
				Code:    "VALUE_OUT_OF_RANGE",
				Message: fmt.Sprintf("%s coordinate exceeds maximum allowed value", coord.name),
				Value:   *coord.value,
			})
		}
	}
}

// validateDimensions validates dimension values
func (v *ArxObjectValidator) validateDimensions(obj *ArxObject, result *ValidationResult) {
	dimensions := []struct {
		name  string
		value *int64
	}{
		{"Width", &obj.Width},
		{"Height", &obj.Height},
		{"Depth", &obj.Depth},
	}

	for _, dim := range dimensions {
		if *dim.value < 0 {
			// Sanitize negative dimensions
			*dim.value = 0
			result.Warnings = append(result.Warnings, ValidationWarning{
				Field:   dim.name,
				Message: fmt.Sprintf("Negative %s dimension sanitized to 0", dim.name),
				Action:  "sanitized",
			})
		}

		if *dim.value > 0 {
			if *dim.value < v.config.MinDimension {
				result.Warnings = append(result.Warnings, ValidationWarning{
					Field:   dim.name,
					Message: fmt.Sprintf("%s dimension is very small (<%dmm)", dim.name, v.config.MinDimension/1000000),
					Action:  "warning",
				})
			}

			if *dim.value > v.config.MaxDimension {
				result.IsValid = false
				result.Errors = append(result.Errors, ValidationError{
					Field:   dim.name,
					Code:    "VALUE_OUT_OF_RANGE",
					Message: fmt.Sprintf("%s dimension exceeds maximum allowed value", dim.name),
					Value:   *dim.value,
				})
			}
		}
	}
}

// validateConfidence validates confidence scores
func (v *ArxObjectValidator) validateConfidence(obj *ArxObject, result *ValidationResult) {
	confidenceFields := []struct {
		name  string
		value *float32
	}{
		{"Classification", &obj.Confidence.Classification},
		{"Position", &obj.Confidence.Position},
		{"Properties", &obj.Confidence.Properties},
		{"Relationships", &obj.Confidence.Relationships},
		{"Overall", &obj.Confidence.Overall},
	}

	for _, field := range confidenceFields {
		// Sanitize confidence values
		if *field.value < v.config.MinConfidence {
			*field.value = v.config.MinConfidence
			result.Warnings = append(result.Warnings, ValidationWarning{
				Field:   fmt.Sprintf("Confidence.%s", field.name),
				Message: fmt.Sprintf("%s confidence was below minimum and sanitized to %.2f", field.name, v.config.MinConfidence),
				Action:  "sanitized",
			})
		}

		if *field.value > v.config.MaxConfidence {
			*field.value = v.config.MaxConfidence
			result.Warnings = append(result.Warnings, ValidationWarning{
				Field:   fmt.Sprintf("Confidence.%s", field.name),
				Message: fmt.Sprintf("%s confidence was above maximum and sanitized to %.2f", field.name, v.config.MaxConfidence),
				Action:  "sanitized",
			})
		}

		// Check for NaN or Inf
		if math.IsNaN(float64(*field.value)) || math.IsInf(float64(*field.value), 0) {
			*field.value = 0.5 // Default to medium confidence
			result.Warnings = append(result.Warnings, ValidationWarning{
				Field:   fmt.Sprintf("Confidence.%s", field.name),
				Message: fmt.Sprintf("%s confidence had invalid value and was reset to 0.5", field.name),
				Action:  "sanitized",
			})
		}
	}

	// Recalculate overall confidence after sanitization
	obj.Confidence.CalculateOverall()
}

// validateProperties validates and sanitizes the Properties field
func (v *ArxObjectValidator) validateProperties(obj *ArxObject, result *ValidationResult) {
	if obj.Properties == nil {
		obj.Properties = []byte("{}")
		return
	}

	// Check size
	if len(obj.Properties) > v.config.MaxPropertiesSize {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "Properties",
			Code:    "SIZE_LIMIT_EXCEEDED",
			Message: fmt.Sprintf("Properties size exceeds maximum of %d bytes", v.config.MaxPropertiesSize),
			Value:   len(obj.Properties),
		})
		return
	}

	// Validate JSON format
	var props interface{}
	if err := json.Unmarshal(obj.Properties, &props); err != nil {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "Properties",
			Code:    "INVALID_JSON",
			Message: "Properties contains invalid JSON",
			Value:   string(obj.Properties),
		})
		return
	}

	// Sanitize JSON (re-marshal to ensure clean format)
	sanitizedJSON, err := json.Marshal(props)
	if err != nil {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "Properties",
			Code:    "SERIALIZATION_ERROR",
			Message: "Failed to sanitize Properties JSON",
		})
		return
	}

	obj.Properties = sanitizedJSON
}

// validateTimestamps validates timestamp fields
func (v *ArxObjectValidator) validateTimestamps(obj *ArxObject, result *ValidationResult) {
	now := time.Now()

	// Validate CreatedAt
	if obj.CreatedAt.IsZero() {
		obj.CreatedAt = now
		result.Warnings = append(result.Warnings, ValidationWarning{
			Field:   "CreatedAt",
			Message: "CreatedAt was missing and has been set to current time",
			Action:  "generated",
		})
	} else if obj.CreatedAt.After(now.Add(time.Hour)) {
		result.IsValid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "CreatedAt",
			Code:    "FUTURE_TIMESTAMP",
			Message: "CreatedAt cannot be more than 1 hour in the future",
			Value:   obj.CreatedAt,
		})
	}

	// Validate UpdatedAt
	if obj.UpdatedAt.IsZero() {
		obj.UpdatedAt = now
		result.Warnings = append(result.Warnings, ValidationWarning{
			Field:   "UpdatedAt",
			Message: "UpdatedAt was missing and has been set to current time",
			Action:  "generated",
		})
	} else if obj.UpdatedAt.Before(obj.CreatedAt) {
		obj.UpdatedAt = obj.CreatedAt
		result.Warnings = append(result.Warnings, ValidationWarning{
			Field:   "UpdatedAt",
			Message: "UpdatedAt was before CreatedAt and has been corrected",
			Action:  "sanitized",
		})
	}
}

// validateStringFields validates string fields for length and encoding
func (v *ArxObjectValidator) validateStringFields(obj *ArxObject, result *ValidationResult) {
	stringFields := []struct {
		name  string
		value *string
	}{
		{"ExtractionMethod", &obj.ExtractionMethod},
		{"Source", &obj.Source},
	}

	for _, field := range stringFields {
		if field.value != nil && *field.value != "" {
			// Sanitize string
			*field.value = strings.TrimSpace(*field.value)

			// Validate length
			if len(*field.value) > v.config.MaxStringLength {
				*field.value = (*field.value)[:v.config.MaxStringLength]
				result.Warnings = append(result.Warnings, ValidationWarning{
					Field:   field.name,
					Message: fmt.Sprintf("%s was truncated to maximum length", field.name),
					Action:  "truncated",
				})
			}

			// Validate UTF-8
			if !utf8.ValidString(*field.value) {
				result.IsValid = false
				result.Errors = append(result.Errors, ValidationError{
					Field:   field.name,
					Code:    "INVALID_ENCODING",
					Message: fmt.Sprintf("%s contains invalid UTF-8 characters", field.name),
				})
			}
		}
	}
}

// validateRequiredFields ensures all required fields are present
func (v *ArxObjectValidator) validateRequiredFields(obj *ArxObject, result *ValidationResult) {
	for _, field := range v.config.RequiredFields {
		switch field {
		case "ID":
			if obj.ID == "" {
				result.IsValid = false
				result.Errors = append(result.Errors, ValidationError{
					Field:   "ID",
					Code:    "REQUIRED_FIELD",
					Message: "ID is required",
				})
			}
		case "Type":
			if obj.Type == "" {
				result.IsValid = false
				result.Errors = append(result.Errors, ValidationError{
					Field:   "Type",
					Code:    "REQUIRED_FIELD",
					Message: "Type is required",
				})
			}
		case "System":
			if obj.System == "" {
				result.IsValid = false
				result.Errors = append(result.Errors, ValidationError{
					Field:   "System",
					Code:    "REQUIRED_FIELD",
					Message: "System is required",
				})
			}
		}
	}
}

// generateUUID generates a simple UUID for objects missing one
func generateUUID() string {
	// Simple UUID generation - in production, use a proper UUID library
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x",
		time.Now().UnixNano()&0xffffffff,
		time.Now().UnixNano()>>32&0xffff,
		0x4000|(time.Now().UnixNano()>>48&0x0fff),
		0x8000|(time.Now().UnixNano()>>60&0x3fff),
		time.Now().UnixNano()&0xffffffffffff)
}

// ValidateArxObject is a convenience function for basic validation
func ValidateArxObject(obj *ArxObject) error {
	validator := NewArxObjectValidator(nil)
	result := validator.ValidateAndSanitize(obj)
	
	if !result.IsValid {
		return fmt.Errorf("validation failed: %d errors", len(result.Errors))
	}
	
	return nil
}