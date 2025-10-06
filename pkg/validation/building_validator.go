// Package validation provides building-specific validation rules for ArxOS.
package validation

import (
	"regexp"
	"strings"
	"time"
)

// BuildingValidator validates building data according to ArxOS business rules
type BuildingValidator struct {
	*BaseValidator
}

// NewBuildingValidator creates a new building validator
func NewBuildingValidator() *BuildingValidator {
	bv := NewBaseValidator()

	// Building ID validation
	bv.AddRule("id", ValidationRule{
		Name:        "building_id",
		Description: "Building ID must be a valid UUID or alphanumeric identifier",
		Required:    true,
		Type:        "string",
		Min:         1,
		Max:         100,
		Custom: func(value any) bool {
			if str, ok := value.(string); ok {
				return isValidBuildingID(str)
			}
			return false
		},
	})

	// Building name validation
	bv.AddRule("name", ValidationRule{
		Name:        "building_name",
		Description: "Building name must be between 1 and 200 characters",
		Required:    true,
		Type:        "string",
		Min:         1,
		Max:         200,
		Custom: func(value any) bool {
			if str, ok := value.(string); ok {
				return isValidBuildingName(str)
			}
			return false
		},
	})

	// Building address validation
	bv.AddRule("address", ValidationRule{
		Name:        "building_address",
		Description: "Building address must be a valid address format",
		Required:    false,
		Type:        "string",
		Max:         500,
		Custom: func(value any) bool {
			if str, ok := value.(string); ok {
				return isValidAddress(str)
			}
			return true // Empty address is valid
		},
	})

	// Building type validation
	bv.AddRule("building_type", ValidationRule{
		Name:        "building_type",
		Description: "Building type must be one of the valid types",
		Required:    false,
		Type:        "string",
		Options: []any{
			"office", "residential", "commercial", "industrial",
			"educational", "healthcare", "retail", "warehouse", "mixed",
		},
	})

	// Building status validation
	bv.AddRule("status", ValidationRule{
		Name:        "building_status",
		Description: "Building status must be one of the valid statuses",
		Required:    false,
		Type:        "string",
		Options: []any{
			"active", "inactive", "maintenance", "construction", "demolished",
		},
	})

	// Grid scale validation
	bv.AddRule("grid_scale", ValidationRule{
		Name:        "grid_scale",
		Description: "Grid scale must be a positive number",
		Required:    false,
		Type:        "float64",
		Min:         0.001,  // 1mm minimum
		Max:         1000.0, // 1km maximum
	})

	// Coverage validation
	bv.AddRule("coverage", ValidationRule{
		Name:        "coverage",
		Description: "Coverage must be between 0 and 100 percent",
		Required:    false,
		Type:        "float64",
		Min:         0.0,
		Max:         100.0,
	})

	return &BuildingValidator{BaseValidator: bv}
}

// ValidateBuilding validates a building struct
func (bv *BuildingValidator) ValidateBuilding(building any) *ValidationResult {
	result := bv.Validate(building)

	// Additional business rule validations
	if result.IsValid() {
		bv.validateBusinessRules(building, result)
	}

	return result
}

// validateBusinessRules validates additional business rules
func (bv *BuildingValidator) validateBusinessRules(building any, result *ValidationResult) {
	// This would contain additional business logic validation
	// For example, checking that certain combinations of fields are valid
	// or that the building meets specific requirements
}

// FloorValidator validates floor data
type FloorValidator struct {
	*BaseValidator
}

// NewFloorValidator creates a new floor validator
func NewFloorValidator() *FloorValidator {
	bv := NewBaseValidator()

	// Floor ID validation
	bv.AddRule("id", ValidationRule{
		Name:        "floor_id",
		Description: "Floor ID must be a valid identifier",
		Required:    true,
		Type:        "string",
		Min:         1,
		Max:         100,
	})

	// Floor level validation
	bv.AddRule("level", ValidationRule{
		Name:        "floor_level",
		Description: "Floor level must be a valid integer",
		Required:    true,
		Type:        "int",
		Min:         -10, // Basement levels
		Max:         200, // Very tall buildings
	})

	// Floor name validation
	bv.AddRule("name", ValidationRule{
		Name:        "floor_name",
		Description: "Floor name must be between 1 and 100 characters",
		Required:    true,
		Type:        "string",
		Min:         1,
		Max:         100,
	})

	// Floor height validation
	bv.AddRule("height", ValidationRule{
		Name:        "floor_height",
		Description: "Floor height must be a positive number",
		Required:    false,
		Type:        "float64",
		Min:         0.1,  // 10cm minimum
		Max:         20.0, // 20m maximum
	})

	return &FloorValidator{BaseValidator: bv}
}

// EquipmentValidator validates equipment data
type EquipmentValidator struct {
	*BaseValidator
}

// NewEquipmentValidator creates a new equipment validator
func NewEquipmentValidator() *EquipmentValidator {
	bv := NewBaseValidator()

	// Equipment ID validation
	bv.AddRule("id", ValidationRule{
		Name:        "equipment_id",
		Description: "Equipment ID must be a valid identifier",
		Required:    true,
		Type:        "string",
		Min:         1,
		Max:         100,
	})

	// Equipment name validation
	bv.AddRule("name", ValidationRule{
		Name:        "equipment_name",
		Description: "Equipment name must be between 1 and 200 characters",
		Required:    true,
		Type:        "string",
		Min:         1,
		Max:         200,
	})

	// Equipment type validation
	bv.AddRule("type", ValidationRule{
		Name:        "equipment_type",
		Description: "Equipment type must be a valid type",
		Required:    true,
		Type:        "string",
		Options: []any{
			"hvac", "electrical", "plumbing", "security", "fire_safety",
			"lighting", "elevator", "generator", "sensor", "controller",
		},
	})

	// Equipment path validation
	bv.AddRule("path", ValidationRule{
		Name:        "equipment_path",
		Description: "Equipment path must follow the universal path format",
		Required:    false,
		Type:        "string",
		Pattern:     `^[A-Z0-9]+(/[A-Z0-9]+)*$`,
		Custom: func(value any) bool {
			if str, ok := value.(string); ok {
				return isValidEquipmentPath(str)
			}
			return true // Empty path is valid
		},
	})

	// Equipment status validation
	bv.AddRule("status", ValidationRule{
		Name:        "equipment_status",
		Description: "Equipment status must be a valid status",
		Required:    false,
		Type:        "string",
		Options: []any{
			"OPERATIONAL", "DEGRADED", "FAILED", "MAINTENANCE", "OFFLINE", "UNKNOWN",
		},
	})

	// Equipment model validation
	bv.AddRule("model", ValidationRule{
		Name:        "equipment_model",
		Description: "Equipment model must be a valid model identifier",
		Required:    false,
		Type:        "string",
		Max:         100,
	})

	return &EquipmentValidator{BaseValidator: bv}
}

// RoomValidator validates room data
type RoomValidator struct {
	*BaseValidator
}

// NewRoomValidator creates a new room validator
func NewRoomValidator() *RoomValidator {
	bv := NewBaseValidator()

	// Room ID validation
	bv.AddRule("id", ValidationRule{
		Name:        "room_id",
		Description: "Room ID must be a valid identifier",
		Required:    true,
		Type:        "string",
		Min:         1,
		Max:         100,
	})

	// Room name validation
	bv.AddRule("name", ValidationRule{
		Name:        "room_name",
		Description: "Room name must be between 1 and 100 characters",
		Required:    true,
		Type:        "string",
		Min:         1,
		Max:         100,
	})

	// Room type validation
	bv.AddRule("type", ValidationRule{
		Name:        "room_type",
		Description: "Room type must be a valid type",
		Required:    false,
		Type:        "string",
		Options: []any{
			"office", "conference", "lobby", "restroom", "storage", "mechanical",
			"electrical", "server", "kitchen", "break_room", "reception",
		},
	})

	// Room area validation
	bv.AddRule("area", ValidationRule{
		Name:        "room_area",
		Description: "Room area must be a positive number in square meters",
		Required:    false,
		Type:        "float64",
		Min:         0.1,     // 0.1 square meters minimum
		Max:         10000.0, // 10,000 square meters maximum
	})

	return &RoomValidator{BaseValidator: bv}
}

// SpatialValidator validates spatial data
type SpatialValidator struct {
	*BaseValidator
}

// NewSpatialValidator creates a new spatial validator
func NewSpatialValidator() *SpatialValidator {
	bv := NewBaseValidator()

	// Coordinate validation
	bv.AddRule("x", ValidationRule{
		Name:        "x_coordinate",
		Description: "X coordinate must be a valid number",
		Required:    false,
		Type:        "float64",
		Min:         -1000000.0, // -1km minimum
		Max:         1000000.0,  // 1km maximum
	})

	bv.AddRule("y", ValidationRule{
		Name:        "y_coordinate",
		Description: "Y coordinate must be a valid number",
		Required:    false,
		Type:        "float64",
		Min:         -1000000.0, // -1km minimum
		Max:         1000000.0,  // 1km maximum
	})

	bv.AddRule("z", ValidationRule{
		Name:        "z_coordinate",
		Description: "Z coordinate must be a valid number",
		Required:    false,
		Type:        "float64",
		Min:         -1000.0, // -1km minimum (underground)
		Max:         1000.0,  // 1km maximum (very tall)
	})

	return &SpatialValidator{BaseValidator: bv}
}

// Helper functions for custom validation

func isValidBuildingID(id string) bool {
	// Allow UUIDs or alphanumeric identifiers
	if isValidUUID(id) {
		return true
	}

	// Allow alphanumeric identifiers with underscores and hyphens
	pattern := `^[a-zA-Z0-9_-]+$`
	matched, _ := regexp.MatchString(pattern, id)
	return matched && len(id) >= 1 && len(id) <= 100
}

func isValidBuildingName(name string) bool {
	// Building names should not be empty and should not contain only whitespace
	trimmed := strings.TrimSpace(name)
	if len(trimmed) == 0 {
		return false
	}

	// Check for invalid characters
	invalidChars := []string{"<", ">", "\"", "'", "&", "\n", "\r", "\t"}
	for _, char := range invalidChars {
		if strings.Contains(name, char) {
			return false
		}
	}

	return true
}

func isValidAddress(address string) bool {
	if len(address) == 0 {
		return true // Empty address is valid
	}

	// Basic address validation - should contain at least a number and some text
	hasNumber := regexp.MustCompile(`\d`).MatchString(address)
	hasText := regexp.MustCompile(`[a-zA-Z]`).MatchString(address)

	return hasNumber && hasText && len(address) <= 500
}

func isValidEquipmentPath(path string) bool {
	if len(path) == 0 {
		return true // Empty path is valid
	}

	// Universal path format: N/3/A/301/E
	// Each segment should be alphanumeric
	segments := strings.Split(path, "/")
	if len(segments) == 0 {
		return false
	}

	for _, segment := range segments {
		if len(segment) == 0 {
			return false
		}

		// Each segment should be alphanumeric
		matched, _ := regexp.MatchString(`^[A-Z0-9]+$`, segment)
		if !matched {
			return false
		}
	}

	return true
}

// ValidationContext provides context for validation
type ValidationContext struct {
	BuildingID string         `json:"building_id,omitempty"`
	UserID     string         `json:"user_id,omitempty"`
	Operation  string         `json:"operation,omitempty"` // create, update, delete
	Timestamp  time.Time      `json:"timestamp"`
	Metadata   map[string]any `json:"metadata,omitempty"`
}

// NewValidationContext creates a new validation context
func NewValidationContext(buildingID, userID, operation string) *ValidationContext {
	return &ValidationContext{
		BuildingID: buildingID,
		UserID:     userID,
		Operation:  operation,
		Timestamp:  time.Now(),
		Metadata:   make(map[string]any),
	}
}

// ValidateWithContext validates data with additional context
func (vc *ValidationContext) ValidateWithContext(validator Validator, data any) *ValidationResult {
	result := validator.Validate(data)

	// Add context-specific validations
	if vc.Operation == "delete" {
		// Additional validations for delete operations
		// For example, check if the entity can be safely deleted
	}

	return result
}
