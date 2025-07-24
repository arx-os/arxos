package bim

import (
	"fmt"
	"regexp"
	"strings"
	"time"

	"go.uber.org/zap"
)

// ValidationLevel represents the level of validation
type ValidationLevel string

const (
	ValidationLevelError   ValidationLevel = "error"
	ValidationLevelWarning ValidationLevel = "warning"
	ValidationLevelInfo    ValidationLevel = "info"
)

// ValidationRule represents a validation rule
type ValidationRule struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Level       ValidationLevel        `json:"level"`
	Condition   string                 `json:"condition"`
	Message     string                 `json:"message"`
	Enabled     bool                   `json:"enabled"`
	Properties  map[string]interface{} `json:"properties"`
}

// BIMValidator provides comprehensive BIM validation functionality
type BIMValidator struct {
	logger   *zap.Logger
	rules    map[string]*ValidationRule
	patterns map[string]*regexp.Regexp
}

// NewBIMValidator creates a new BIM validator
func NewBIMValidator(logger *zap.Logger) (*BIMValidator, error) {
	validator := &BIMValidator{
		logger:   logger,
		rules:    make(map[string]*ValidationRule),
		patterns: make(map[string]*regexp.Regexp),
	}

	// Initialize default validation rules
	validator.initializeDefaultRules()

	logger.Info("BIM validator initialized",
		zap.Int("rule_count", len(validator.rules)))

	return validator, nil
}

// ValidateModel validates a complete BIM model
func (bv *BIMValidator) ValidateModel(model *BIMModel) *BIMValidationResult {
	result := &BIMValidationResult{
		Valid:     true,
		Errors:    []string{},
		Warnings:  []string{},
		Details:   make(map[string]interface{}),
		Timestamp: time.Now(),
	}

	// Validate model structure
	bv.validateModelStructure(model, result)

	// Validate all elements
	for _, element := range model.Elements {
		elementResult := bv.ValidateElement(element)
		if !elementResult.Valid {
			result.Valid = false
			result.Errors = append(result.Errors, elementResult.Errors...)
		}
		result.Warnings = append(result.Warnings, elementResult.Warnings...)
	}

	// Validate relationships
	bv.validateModelRelationships(model, result)

	// Validate model consistency
	bv.validateModelConsistency(model, result)

	return result
}

// ValidateElement validates a single BIM element
func (bv *BIMValidator) ValidateElement(element *BIMElement) *BIMValidationResult {
	result := &BIMValidationResult{
		Valid:     true,
		ElementID: element.ID,
		Errors:    []string{},
		Warnings:  []string{},
		Details:   make(map[string]interface{}),
		Timestamp: time.Now(),
	}

	// Validate element ID
	bv.validateElementID(element, result)

	// Validate element name
	bv.validateElementName(element, result)

	// Validate element type
	bv.validateElementType(element, result)

	// Validate element geometry
	bv.validateElementGeometry(element, result)

	// Validate element properties
	bv.validateElementProperties(element, result)

	// Validate element status
	bv.validateElementStatus(element, result)

	// Apply custom validation rules
	bv.applyValidationRules(element, result)

	return result
}

// AddValidationRule adds a custom validation rule
func (bv *BIMValidator) AddValidationRule(rule *ValidationRule) error {
	if rule.ID == "" {
		return fmt.Errorf("validation rule must have an ID")
	}

	if _, exists := bv.rules[rule.ID]; exists {
		return fmt.Errorf("validation rule with ID %s already exists", rule.ID)
	}

	bv.rules[rule.ID] = rule

	// Compile regex pattern if condition contains regex
	if strings.Contains(rule.Condition, "regex:") {
		pattern := strings.TrimPrefix(rule.Condition, "regex:")
		compiled, err := regexp.Compile(pattern)
		if err != nil {
			return fmt.Errorf("invalid regex pattern in rule %s: %w", rule.ID, err)
		}
		bv.patterns[rule.ID] = compiled
	}

	bv.logger.Info("Added validation rule",
		zap.String("rule_id", rule.ID),
		zap.String("rule_name", rule.Name))

	return nil
}

// RemoveValidationRule removes a validation rule
func (bv *BIMValidator) RemoveValidationRule(ruleID string) error {
	if _, exists := bv.rules[ruleID]; !exists {
		return fmt.Errorf("validation rule %s not found", ruleID)
	}

	delete(bv.rules, ruleID)
	delete(bv.patterns, ruleID)

	bv.logger.Info("Removed validation rule",
		zap.String("rule_id", ruleID))

	return nil
}

// GetValidationRules returns all validation rules
func (bv *BIMValidator) GetValidationRules() map[string]*ValidationRule {
	result := make(map[string]*ValidationRule)
	for id, rule := range bv.rules {
		result[id] = rule
	}
	return result
}

// validateModelStructure validates the structure of a BIM model
func (bv *BIMValidator) validateModelStructure(model *BIMModel, result *BIMValidationResult) {
	// Check required fields
	if model.ID == "" {
		result.Valid = false
		result.Errors = append(result.Errors, "Model ID is required")
	}

	if model.Name == "" {
		result.Valid = false
		result.Errors = append(result.Errors, "Model name is required")
	}

	if model.Version == "" {
		result.Warnings = append(result.Warnings, "Model version is not specified")
	}

	// Check for duplicate element IDs
	elementIDs := make(map[string]bool)
	for _, element := range model.Elements {
		if elementIDs[element.ID] {
			result.Valid = false
			result.Errors = append(result.Errors, fmt.Sprintf("Duplicate element ID: %s", element.ID))
		}
		elementIDs[element.ID] = true
	}
}

// validateModelRelationships validates relationships in a BIM model
func (bv *BIMValidator) validateModelRelationships(model *BIMModel, result *BIMValidationResult) {
	// Check for orphaned elements (elements without relationships)
	connectedElements := make(map[string]bool)

	// This would require access to relationships, which are stored separately
	// For now, we'll add a placeholder validation
	if len(model.Elements) > 0 {
		result.Details["element_count"] = len(model.Elements)
	}
}

// validateModelConsistency validates the consistency of a BIM model
func (bv *BIMValidator) validateModelConsistency(model *BIMModel, result *BIMValidationResult) {
	// Check for system type consistency
	systemTypes := make(map[BIMSystemType]int)
	for _, element := range model.Elements {
		systemTypes[element.SystemType]++
	}

	// Check for element type consistency
	elementTypes := make(map[BIMElementType]int)
	for _, element := range model.Elements {
		elementTypes[element.Type]++
	}

	result.Details["system_type_distribution"] = systemTypes
	result.Details["element_type_distribution"] = elementTypes
}

// validateElementID validates an element ID
func (bv *BIMValidator) validateElementID(element *BIMElement, result *BIMValidationResult) {
	if element.ID == "" {
		result.Valid = false
		result.Errors = append(result.Errors, "Element ID is required")
		return
	}

	// Check ID format (alphanumeric with underscores and hyphens)
	validIDPattern := regexp.MustCompile(`^[a-zA-Z0-9_-]+$`)
	if !validIDPattern.MatchString(element.ID) {
		result.Valid = false
		result.Errors = append(result.Errors, "Element ID contains invalid characters")
	}

	// Check ID length
	if len(element.ID) > 100 {
		result.Valid = false
		result.Errors = append(result.Errors, "Element ID is too long (max 100 characters)")
	}
}

// validateElementName validates an element name
func (bv *BIMValidator) validateElementName(element *BIMElement, result *BIMValidationResult) {
	if element.Name == "" {
		result.Valid = false
		result.Errors = append(result.Errors, "Element name is required")
		return
	}

	// Check name length
	if len(element.Name) > 200 {
		result.Valid = false
		result.Errors = append(result.Errors, "Element name is too long (max 200 characters)")
	}

	// Check for reserved names
	reservedNames := []string{"null", "undefined", "none", "unknown"}
	for _, reserved := range reservedNames {
		if strings.ToLower(element.Name) == reserved {
			result.Warnings = append(result.Warnings, fmt.Sprintf("Element name '%s' is a reserved word", element.Name))
		}
	}
}

// validateElementType validates an element type
func (bv *BIMValidator) validateElementType(element *BIMElement, result *BIMValidationResult) {
	if element.Type == "" {
		result.Valid = false
		result.Errors = append(result.Errors, "Element type is required")
		return
	}

	// Check if element type is valid
	validTypes := map[BIMElementType]bool{
		BIMElementTypeRoom:       true,
		BIMElementTypeWall:       true,
		BIMElementTypeDoor:       true,
		BIMElementTypeWindow:     true,
		BIMElementTypeDevice:     true,
		BIMElementTypeEquipment:  true,
		BIMElementTypeZone:       true,
		BIMElementTypeFloor:      true,
		BIMElementTypeCeiling:    true,
		BIMElementTypeFoundation: true,
		BIMElementTypeRoof:       true,
		BIMElementTypeStair:      true,
		BIMElementTypeElevator:   true,
		BIMElementTypeDuct:       true,
		BIMElementTypePipe:       true,
		BIMElementTypeCable:      true,
		BIMElementTypeConduit:    true,
	}

	if !validTypes[element.Type] {
		result.Valid = false
		result.Errors = append(result.Errors, fmt.Sprintf("Invalid element type: %s", element.Type))
	}
}

// validateElementGeometry validates element geometry
func (bv *BIMValidator) validateElementGeometry(element *BIMElement, result *BIMValidationResult) {
	if element.Geometry == nil {
		result.Warnings = append(result.Warnings, "Element has no geometry")
		return
	}

	// Validate geometry type
	validGeometryTypes := []string{"point", "line", "polygon", "circle", "rectangle", "box"}
	validType := false
	for _, validType := range validGeometryTypes {
		if element.Geometry.Type == validType {
			validType = true
			break
		}
	}

	if !validType {
		result.Valid = false
		result.Errors = append(result.Errors, fmt.Sprintf("Invalid geometry type: %s", element.Geometry.Type))
	}

	// Validate coordinates
	if element.Geometry.Coordinates != nil {
		for i, coord := range element.Geometry.Coordinates {
			if len(coord) < 2 || len(coord) > 3 {
				result.Valid = false
				result.Errors = append(result.Errors, fmt.Sprintf("Invalid coordinate at index %d: must have 2-3 dimensions", i))
			}
		}
	}

	// Validate center point
	if element.Geometry.Center != nil {
		if element.Geometry.Center.X < -1000000 || element.Geometry.Center.X > 1000000 {
			result.Warnings = append(result.Warnings, "Center X coordinate is outside reasonable range")
		}
		if element.Geometry.Center.Y < -1000000 || element.Geometry.Center.Y > 1000000 {
			result.Warnings = append(result.Warnings, "Center Y coordinate is outside reasonable range")
		}
		if element.Geometry.Center.Z < -1000 || element.Geometry.Center.Z > 1000 {
			result.Warnings = append(result.Warnings, "Center Z coordinate is outside reasonable range")
		}
	}

	// Validate dimensions
	if element.Geometry.Dimensions != nil {
		if element.Geometry.Dimensions.Width <= 0 {
			result.Warnings = append(result.Warnings, "Width must be positive")
		}
		if element.Geometry.Dimensions.Height <= 0 {
			result.Warnings = append(result.Warnings, "Height must be positive")
		}
		if element.Geometry.Dimensions.Depth <= 0 {
			result.Warnings = append(result.Warnings, "Depth must be positive")
		}
	}
}

// validateElementProperties validates element properties
func (bv *BIMValidator) validateElementProperties(element *BIMElement, result *BIMValidationResult) {
	if element.Properties == nil {
		result.Warnings = append(result.Warnings, "Element has no properties")
		return
	}

	// Check for required properties based on element type
	requiredProps := bv.getRequiredProperties(element.Type)
	for _, prop := range requiredProps {
		if _, exists := element.Properties[prop]; !exists {
			result.Warnings = append(result.Warnings, fmt.Sprintf("Missing recommended property: %s", prop))
		}
	}

	// Validate property values
	for key, value := range element.Properties {
		if value == nil {
			result.Warnings = append(result.Warnings, fmt.Sprintf("Property '%s' has null value", key))
		}
	}
}

// validateElementStatus validates element status
func (bv *BIMValidator) validateElementStatus(element *BIMElement, result *BIMValidationResult) {
	if element.Status == "" {
		result.Valid = false
		result.Errors = append(result.Errors, "Element status is required")
		return
	}

	// Check if status is valid
	validStatuses := map[BIMElementStatus]bool{
		BIMElementStatusActive:      true,
		BIMElementStatusInactive:    true,
		BIMElementStatusMaintenance: true,
		BIMElementStatusFailed:      true,
		BIMElementStatusWarning:     true,
		BIMElementStatusCritical:    true,
	}

	if !validStatuses[element.Status] {
		result.Valid = false
		result.Errors = append(result.Errors, fmt.Sprintf("Invalid element status: %s", element.Status))
	}
}

// applyValidationRules applies custom validation rules
func (bv *BIMValidator) applyValidationRules(element *BIMElement, result *BIMValidationResult) {
	for ruleID, rule := range bv.rules {
		if !rule.Enabled {
			continue
		}

		// Apply rule based on condition
		if bv.evaluateRuleCondition(rule, element) {
			switch rule.Level {
			case ValidationLevelError:
				result.Valid = false
				result.Errors = append(result.Errors, rule.Message)
			case ValidationLevelWarning:
				result.Warnings = append(result.Warnings, rule.Message)
			case ValidationLevelInfo:
				// Info level doesn't affect validation result
			}
		}
	}
}

// evaluateRuleCondition evaluates a validation rule condition
func (bv *BIMValidator) evaluateRuleCondition(rule *ValidationRule, element *BIMElement) bool {
	// Simple condition evaluation - can be extended for complex conditions
	switch rule.Condition {
	case "has_geometry":
		return element.Geometry != nil
	case "has_properties":
		return len(element.Properties) > 0
	case "has_metadata":
		return len(element.Metadata) > 0
	case "is_active":
		return element.Status == BIMElementStatusActive
	case "is_device":
		return element.Type == BIMElementTypeDevice
	case "is_equipment":
		return element.Type == BIMElementTypeEquipment
	default:
		// Check if condition is a regex pattern
		if pattern, exists := bv.patterns[rule.ID]; exists {
			return pattern.MatchString(element.Name)
		}
		return false
	}
}

// getRequiredProperties returns required properties for an element type
func (bv *BIMValidator) getRequiredProperties(elementType BIMElementType) []string {
	switch elementType {
	case BIMElementTypeRoom:
		return []string{"area", "height", "room_type"}
	case BIMElementTypeWall:
		return []string{"thickness", "material", "height"}
	case BIMElementTypeDoor:
		return []string{"width", "height", "door_type"}
	case BIMElementTypeWindow:
		return []string{"width", "height", "window_type"}
	case BIMElementTypeDevice:
		return []string{"device_type", "manufacturer", "model"}
	case BIMElementTypeEquipment:
		return []string{"equipment_type", "capacity", "manufacturer"}
	default:
		return []string{}
	}
}

// initializeDefaultRules initializes default validation rules
func (bv *BIMValidator) initializeDefaultRules() {
	defaultRules := []*ValidationRule{
		{
			ID:          "rule_001",
			Name:        "Element Name Pattern",
			Description: "Element names should follow a consistent pattern",
			Level:       ValidationLevelWarning,
			Condition:   "regex:^[A-Z][a-zA-Z0-9_\\s-]+$",
			Message:     "Element name should start with uppercase letter and contain only alphanumeric characters, spaces, underscores, and hyphens",
			Enabled:     true,
		},
		{
			ID:          "rule_002",
			Name:        "Geometry Required",
			Description: "Elements should have geometry defined",
			Level:       ValidationLevelWarning,
			Condition:   "has_geometry",
			Message:     "Element should have geometry defined",
			Enabled:     true,
		},
		{
			ID:          "rule_003",
			Name:        "Properties Required",
			Description: "Elements should have properties defined",
			Level:       ValidationLevelInfo,
			Condition:   "has_properties",
			Message:     "Element should have properties defined",
			Enabled:     true,
		},
		{
			ID:          "rule_004",
			Name:        "Device Validation",
			Description: "Device elements should have device-specific properties",
			Level:       ValidationLevelWarning,
			Condition:   "is_device",
			Message:     "Device elements should have device_type, manufacturer, and model properties",
			Enabled:     true,
		},
		{
			ID:          "rule_005",
			Name:        "Equipment Validation",
			Description: "Equipment elements should have equipment-specific properties",
			Level:       ValidationLevelWarning,
			Condition:   "is_equipment",
			Message:     "Equipment elements should have equipment_type, capacity, and manufacturer properties",
			Enabled:     true,
		},
	}

	for _, rule := range defaultRules {
		bv.rules[rule.ID] = rule

		// Compile regex patterns
		if strings.Contains(rule.Condition, "regex:") {
			pattern := strings.TrimPrefix(rule.Condition, "regex:")
			if compiled, err := regexp.Compile(pattern); err == nil {
				bv.patterns[rule.ID] = compiled
			}
		}
	}
}
