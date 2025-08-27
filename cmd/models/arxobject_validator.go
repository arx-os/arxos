package models

import (
	"fmt"
	"strings"
)

// ArxObjectValidator validates ArxObject instances
type ArxObjectValidator struct {
	strict bool // If true, enforce all required properties
}

// NewValidator creates a new ArxObject validator
func NewValidator(strict bool) *ArxObjectValidator {
	return &ArxObjectValidator{strict: strict}
}

// Validate performs full validation on an ArxObject
func (v *ArxObjectValidator) Validate(obj *ArxObjectV2) error {
	// Validate ID
	if err := ValidateID(obj.ID); err != nil {
		return fmt.Errorf("invalid ID: %w", err)
	}
	
	// Validate system
	if !isKnownSystem(obj.System) && obj.System != "spatial" {
		return fmt.Errorf("unknown system: %s", obj.System)
	}
	
	// Validate type is not empty
	if obj.Type == "" {
		return fmt.Errorf("object type cannot be empty")
	}
	
	// Validate parent exists if specified
	if obj.Parent != "" {
		if err := ValidateID(obj.Parent); err != nil {
			return fmt.Errorf("invalid parent ID: %w", err)
		}
		
		// Check that parent is a prefix of this object's ID
		if !strings.HasPrefix(obj.ID, obj.Parent) {
			return fmt.Errorf("object ID must be under parent path: %s not under %s", obj.ID, obj.Parent)
		}
	}
	
	// Validate spatial location if present
	if obj.SpatialLocation != "" {
		if err := ValidateID(obj.SpatialLocation); err != nil {
			return fmt.Errorf("invalid spatial location: %w", err)
		}
	}
	
	// Validate confidence range
	if obj.Confidence < 0.0 || obj.Confidence > 1.0 {
		return fmt.Errorf("confidence must be between 0.0 and 1.0: %f", obj.Confidence)
	}
	
	// Validate status
	validStatuses := []string{"active", "inactive", "fault", "maintenance", "planned", "decommissioned"}
	if !contains(validStatuses, obj.Status) {
		return fmt.Errorf("invalid status: %s", obj.Status)
	}
	
	// Validate validation status if present
	if obj.ValidationStatus != "" {
		validValidationStatuses := []string{"pending", "validated", "failed", "partial"}
		if !contains(validValidationStatuses, obj.ValidationStatus) {
			return fmt.Errorf("invalid validation status: %s", obj.ValidationStatus)
		}
	}
	
	// Validate system-specific properties if strict mode
	if v.strict {
		if err := v.validateSystemProperties(obj); err != nil {
			return fmt.Errorf("property validation failed: %w", err)
		}
	}
	
	// Validate relationships
	if err := v.validateRelationships(obj); err != nil {
		return fmt.Errorf("relationship validation failed: %w", err)
	}
	
	return nil
}

// validateSystemProperties validates properties against system schema
func (v *ArxObjectValidator) validateSystemProperties(obj *ArxObjectV2) error {
	schema := GetPropertySchema(obj.System, obj.Type)
	if schema == nil {
		// No schema defined for this system/type combination
		return nil
	}
	
	// Check required properties
	for _, req := range schema.Required {
		if _, ok := obj.Properties[req]; !ok {
			return fmt.Errorf("missing required property: %s", req)
		}
	}
	
	// Validate property types and ranges
	for key, value := range obj.Properties {
		// Check if property is allowed
		if !contains(schema.Required, key) && !contains(schema.Optional, key) {
			// Allow additional properties but log warning in non-strict mode
			if v.strict {
				return fmt.Errorf("unexpected property: %s", key)
			}
			continue
		}
		
		// Check type if defined
		if expectedType, ok := schema.Types[key]; ok {
			if !validateType(value, expectedType) {
				return fmt.Errorf("property %s has wrong type: expected %s", key, expectedType)
			}
		}
		
		// Check valid values if defined
		if validValues, ok := schema.Values[key]; ok {
			valueStr := fmt.Sprintf("%v", value)
			if !contains(validValues, valueStr) {
				return fmt.Errorf("property %s has invalid value: %s", key, valueStr)
			}
		}
		
		// Check ranges if defined
		if validRange, ok := schema.Ranges[key]; ok {
			if !inRange(value, validRange) {
				return fmt.Errorf("property %s value out of range: %v", key, value)
			}
		}
	}
	
	return nil
}

// validateRelationships ensures relationship IDs are valid
func (v *ArxObjectValidator) validateRelationships(obj *ArxObjectV2) error {
	// Define valid relationship types by system
	validRelationships := map[string][]string{
		"electrical": {"fed_from", "powers", "controlled_by", "parallel_with", "wiring_path"},
		"hvac":       {"fed_from", "serves", "controlled_by", "connected_to", "zone"},
		"plumbing":   {"fed_from", "drains_to", "connected_to", "serves"},
		"fire_alarm": {"zone", "controlled_by", "monitors", "triggers"},
		"bas":        {"controls", "monitors", "commanded_by"},
	}
	
	// Get valid relationships for this system
	validRels, ok := validRelationships[obj.System]
	if !ok {
		// No specific relationships defined for this system
		return nil
	}
	
	// Check each relationship
	for relType, relIDs := range obj.Relationships {
		// Check if relationship type is valid for this system
		if !contains(validRels, relType) {
			if v.strict {
				return fmt.Errorf("invalid relationship type %s for system %s", relType, obj.System)
			}
		}
		
		// Validate each related ID
		for _, relID := range relIDs {
			if err := ValidateID(relID); err != nil {
				return fmt.Errorf("invalid ID in relationship %s: %w", relType, err)
			}
		}
	}
	
	// System-specific relationship rules
	if err := v.validateSystemRelationshipRules(obj); err != nil {
		return err
	}
	
	return nil
}

// validateSystemRelationshipRules enforces system-specific relationship rules
func (v *ArxObjectValidator) validateSystemRelationshipRules(obj *ArxObjectV2) error {
	switch obj.System {
	case "electrical":
		// Electrical objects must have fed_from unless they are service entry
		if obj.Type != "service" && obj.Type != "transformer" {
			if fed, ok := obj.Relationships["fed_from"]; !ok || len(fed) == 0 {
				if v.strict {
					return fmt.Errorf("electrical component must have fed_from relationship")
				}
			}
		}
		
	case "hvac":
		// VAV boxes must have fed_from (AHU) and serves (zones/rooms)
		if obj.Type == "vav" {
			if fed, ok := obj.Relationships["fed_from"]; !ok || len(fed) == 0 {
				if v.strict {
					return fmt.Errorf("VAV box must have fed_from relationship to AHU")
				}
			}
			if serves, ok := obj.Relationships["serves"]; !ok || len(serves) == 0 {
				if v.strict {
					return fmt.Errorf("VAV box must serve at least one zone/room")
				}
			}
		}
		
	case "plumbing":
		// Fixtures must have fed_from and drains_to
		if obj.Type == "fixture" {
			if fed, ok := obj.Relationships["fed_from"]; !ok || len(fed) == 0 {
				if v.strict {
					return fmt.Errorf("plumbing fixture must have fed_from relationship")
				}
			}
			if drains, ok := obj.Relationships["drains_to"]; !ok || len(drains) == 0 {
				if v.strict {
					return fmt.Errorf("plumbing fixture must have drains_to relationship")
				}
			}
		}
	}
	
	return nil
}

// ValidateElectricalCircuit validates electrical circuit integrity
func (v *ArxObjectValidator) ValidateElectricalCircuit(breaker *ArxObjectV2, devices []*ArxObjectV2) error {
	if breaker.System != "electrical" || breaker.Type != "breaker" {
		return fmt.Errorf("not a breaker object")
	}
	
	// Get breaker rating
	breakerAmps, ok := breaker.Properties["breaker_amps"].(int)
	if !ok {
		return fmt.Errorf("breaker missing amp rating")
	}
	
	voltage, ok := breaker.Properties["voltage"].(float64)
	if !ok {
		voltage = 120 // Default to 120V
	}
	
	// Calculate total load
	totalLoad := 0.0
	for _, device := range devices {
		if load, ok := device.Properties["connected_load"].(float64); ok {
			totalLoad += load
		}
	}
	
	// Convert to amps
	totalAmps := totalLoad / voltage
	
	// Check if within breaker rating (80% rule for continuous loads)
	if totalAmps > float64(breakerAmps)*0.8 {
		return fmt.Errorf("circuit overloaded: %.1fA on %dA breaker", totalAmps, breakerAmps)
	}
	
	return nil
}

// ValidateHVACZoning validates HVAC zone configuration
func (v *ArxObjectValidator) ValidateHVACZoning(zone *ArxObjectV2, rooms []*ArxObjectV2) error {
	if zone.System != "hvac" || zone.Type != "zone" {
		return fmt.Errorf("not an HVAC zone object")
	}
	
	// Check that zone has at least one room
	if len(rooms) == 0 {
		return fmt.Errorf("zone must contain at least one room")
	}
	
	// Check that all rooms have temperature sensors
	for _, room := range rooms {
		hasSensor := false
		if controlled, ok := room.Relationships["controlled_by"]; ok {
			for _, controller := range controlled {
				if strings.Contains(controller, "sensor") && strings.Contains(controller, "temp") {
					hasSensor = true
					break
				}
			}
		}
		if !hasSensor && v.strict {
			return fmt.Errorf("room %s lacks temperature sensor for zone control", room.ID)
		}
	}
	
	return nil
}

// Helper functions

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func validateType(value interface{}, expectedType string) bool {
	switch expectedType {
	case "string":
		_, ok := value.(string)
		return ok
	case "int":
		_, ok := value.(int)
		return ok
	case "float":
		_, ok := value.(float64)
		return ok
	case "bool":
		_, ok := value.(bool)
		return ok
	default:
		return true // Unknown type, allow
	}
}

func inRange(value interface{}, validRange interface{}) bool {
	switch r := validRange.(type) {
	case []int:
		if v, ok := value.(int); ok {
			for _, valid := range r {
				if v == valid {
					return true
				}
			}
		}
	case []float64:
		if v, ok := value.(float64); ok {
			for _, valid := range r {
				if v == valid {
					return true
				}
			}
		}
	case []string:
		if v, ok := value.(string); ok {
			for _, valid := range r {
				if v == valid {
					return true
				}
			}
		}
	}
	return false
}