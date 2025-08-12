// Package validator provides high-performance constraint validation for ArxObjects
package validator

import (
	"fmt"
	"math"
	"sync"

	"github.com/arxos/arxos/services/arxobject/engine"
)

// ConstraintType defines types of constraints
type ConstraintType uint8

const (
	// Spatial constraints
	ConstraintClearance ConstraintType = iota
	ConstraintAccessibility
	ConstraintCollision
	
	// Electrical constraints
	ConstraintVoltageMatch
	ConstraintLoadCapacity
	ConstraintCircuitBalance
	
	// Structural constraints
	ConstraintLoadLimit
	ConstraintMaterialCompatibility
	ConstraintSpanLimit
	
	// Code compliance
	ConstraintNEC
	ConstraintIBC
	ConstraintADA
)

// Severity levels for violations
type Severity uint8

const (
	SeverityInfo Severity = iota
	SeverityWarning
	SeverityError
	SeverityCritical
)

// Violation represents a constraint violation
type Violation struct {
	ObjectID       uint64
	ConstraintType ConstraintType
	Field          string
	Message        string
	Severity       string
	Value          interface{}
	Expected       interface{}
}

// Validator provides fast constraint validation
type Validator struct {
	engine     *engine.Engine
	rules      map[ConstraintType]ValidationRule
	cache      map[uint64]*ValidationResult
	cacheMu    sync.RWMutex
	
	// Performance metrics
	validations uint64
	violations  uint64
}

// ValidationRule defines a constraint validation function
type ValidationRule func(obj *engine.ArxObject, context map[string]interface{}) []Violation

// ValidationResult caches validation results
type ValidationResult struct {
	ObjectID   uint64
	Valid      bool
	Violations []Violation
	Timestamp  int64
}

// NewValidator creates a new constraint validator
func NewValidator() *Validator {
	v := &Validator{
		rules: make(map[ConstraintType]ValidationRule),
		cache: make(map[uint64]*ValidationResult),
	}
	
	// Register built-in validation rules
	v.registerBuiltinRules()
	
	return v
}

// SetEngine sets the ArxObject engine
func (v *Validator) SetEngine(e *engine.Engine) {
	v.engine = e
}

// ValidateObject validates all constraints for an object
func (v *Validator) ValidateObject(obj *engine.ArxObject) []Violation {
	v.validations++
	
	// Check cache
	v.cacheMu.RLock()
	if cached, exists := v.cache[obj.ID]; exists {
		// Cache valid for 60 seconds
		if obj.UpdatedAt-cached.Timestamp < 60 {
			v.cacheMu.RUnlock()
			return cached.Violations
		}
	}
	v.cacheMu.RUnlock()
	
	violations := []Violation{}
	
	// Apply all relevant rules based on object type
	rules := v.getRulesForType(obj.Type)
	for _, rule := range rules {
		if vios := rule(obj, nil); len(vios) > 0 {
			violations = append(violations, vios...)
		}
	}
	
	// Cache result
	v.cacheMu.Lock()
	v.cache[obj.ID] = &ValidationResult{
		ObjectID:   obj.ID,
		Valid:      len(violations) == 0,
		Violations: violations,
		Timestamp:  obj.UpdatedAt,
	}
	v.cacheMu.Unlock()
	
	v.violations += uint64(len(violations))
	
	return violations
}

// ValidateSpatialConstraints checks spatial constraints
func (v *Validator) ValidateSpatialConstraints(obj *engine.ArxObject, clearance float32) []Violation {
	violations := []Violation{}
	
	// Check minimum clearances based on object type
	minClearance := v.getMinimumClearance(obj.Type)
	if clearance < minClearance {
		violations = append(violations, Violation{
			ObjectID:       obj.ID,
			ConstraintType: ConstraintClearance,
			Field:          "clearance",
			Message:        fmt.Sprintf("Insufficient clearance: %0.2fm required, %0.2fm found", minClearance, clearance),
			Severity:       "error",
			Value:          clearance,
			Expected:       minClearance,
		})
	}
	
	// Check accessibility requirements
	if v.requiresAccessibility(obj.Type) {
		if !v.checkAccessibility(obj) {
			violations = append(violations, Violation{
				ObjectID:       obj.ID,
				ConstraintType: ConstraintAccessibility,
				Field:          "accessibility",
				Message:        "Object does not meet ADA accessibility requirements",
				Severity:       "error",
			})
		}
	}
	
	return violations
}

// ValidateElectricalConstraints checks electrical system constraints
func (v *Validator) ValidateElectricalConstraints(obj *engine.ArxObject) []Violation {
	violations := []Violation{}
	
	// Only apply to electrical objects
	if !v.isElectrical(obj.Type) {
		return violations
	}
	
	// Check voltage compatibility
	if voltage := obj.GetProperty("voltage"); voltage != nil {
		if circuit := obj.GetProperty("circuit"); circuit != nil {
			// Get circuit object and check voltage match
			circuitID := circuit.(uint64)
			if circuitObj, exists := v.engine.GetObject(circuitID); exists {
				circuitVoltage := circuitObj.GetProperty("voltage")
				if circuitVoltage != nil && voltage != circuitVoltage {
					violations = append(violations, Violation{
						ObjectID:       obj.ID,
						ConstraintType: ConstraintVoltageMatch,
						Field:          "voltage",
						Message:        "Voltage mismatch with circuit",
						Severity:       "error",
						Value:          voltage,
						Expected:       circuitVoltage,
					})
				}
			}
		}
	}
	
	// Check load capacity
	if load := obj.GetProperty("load"); load != nil {
		if capacity := obj.GetProperty("capacity"); capacity != nil {
			loadVal := load.(float64)
			capVal := capacity.(float64)
			
			if loadVal > capVal {
				violations = append(violations, Violation{
					ObjectID:       obj.ID,
					ConstraintType: ConstraintLoadCapacity,
					Field:          "load",
					Message:        "Load exceeds capacity",
					Severity:       "critical",
					Value:          loadVal,
					Expected:       fmt.Sprintf("<= %v", capVal),
				})
			} else if loadVal > capVal*0.8 {
				violations = append(violations, Violation{
					ObjectID:       obj.ID,
					ConstraintType: ConstraintLoadCapacity,
					Field:          "load",
					Message:        "Load exceeds 80% of capacity",
					Severity:       "warning",
					Value:          loadVal,
					Expected:       fmt.Sprintf("<= %v", capVal*0.8),
				})
			}
		}
	}
	
	return violations
}

// ValidateStructuralConstraints checks structural constraints
func (v *Validator) ValidateStructuralConstraints(obj *engine.ArxObject) []Violation {
	violations := []Violation{}
	
	// Only apply to structural objects
	if !v.isStructural(obj.Type) {
		return violations
	}
	
	// Check load limits
	if load := obj.GetProperty("applied_load"); load != nil {
		if maxLoad := obj.GetProperty("max_load"); maxLoad != nil {
			loadVal := load.(float64)
			maxVal := maxLoad.(float64)
			
			if loadVal > maxVal {
				violations = append(violations, Violation{
					ObjectID:       obj.ID,
					ConstraintType: ConstraintLoadLimit,
					Field:          "applied_load",
					Message:        "Applied load exceeds structural capacity",
					Severity:       "critical",
					Value:          loadVal,
					Expected:       fmt.Sprintf("<= %v", maxVal),
				})
			}
		}
	}
	
	// Check span limits for beams
	if obj.Type == engine.StructuralBeam {
		span := float64(obj.Length) / 1000.0 // Convert mm to m
		maxSpan := v.getMaxSpan(obj)
		
		if span > maxSpan {
			violations = append(violations, Violation{
				ObjectID:       obj.ID,
				ConstraintType: ConstraintSpanLimit,
				Field:          "span",
				Message:        fmt.Sprintf("Beam span exceeds limit: %0.2fm > %0.2fm", span, maxSpan),
				Severity:       "error",
				Value:          span,
				Expected:       maxSpan,
			})
		}
	}
	
	return violations
}

// ValidateCodeCompliance checks building code compliance
func (v *Validator) ValidateCodeCompliance(obj *engine.ArxObject, code string) []Violation {
	violations := []Violation{}
	
	switch code {
	case "NEC":
		violations = append(violations, v.validateNEC(obj)...)
	case "IBC":
		violations = append(violations, v.validateIBC(obj)...)
	case "ADA":
		violations = append(violations, v.validateADA(obj)...)
	}
	
	return violations
}

// Private helper methods

func (v *Validator) registerBuiltinRules() {
	// Spatial rules
	v.rules[ConstraintClearance] = func(obj *engine.ArxObject, ctx map[string]interface{}) []Violation {
		clearance := float32(0.1) // Default 10cm
		if c, ok := ctx["clearance"].(float32); ok {
			clearance = c
		}
		return v.ValidateSpatialConstraints(obj, clearance)
	}
	
	// Electrical rules
	v.rules[ConstraintVoltageMatch] = func(obj *engine.ArxObject, ctx map[string]interface{}) []Violation {
		return v.ValidateElectricalConstraints(obj)
	}
	
	// Structural rules
	v.rules[ConstraintLoadLimit] = func(obj *engine.ArxObject, ctx map[string]interface{}) []Violation {
		return v.ValidateStructuralConstraints(obj)
	}
}

func (v *Validator) getRulesForType(objType engine.ArxObjectType) []ValidationRule {
	rules := []ValidationRule{}
	
	// Add rules based on object type
	if v.isElectrical(objType) {
		rules = append(rules, v.rules[ConstraintVoltageMatch])
		rules = append(rules, v.rules[ConstraintLoadCapacity])
	}
	
	if v.isStructural(objType) {
		rules = append(rules, v.rules[ConstraintLoadLimit])
		rules = append(rules, v.rules[ConstraintSpanLimit])
	}
	
	// All objects get spatial rules
	rules = append(rules, v.rules[ConstraintClearance])
	
	return rules
}

func (v *Validator) getMinimumClearance(objType engine.ArxObjectType) float32 {
	// Return minimum clearance in meters based on object type
	switch objType {
	case engine.ElectricalPanel:
		return 0.9 // 3 feet for electrical panels
	case engine.ElectricalOutlet:
		return 0.15 // 6 inches for outlets
	case engine.HVACUnit:
		return 0.6 // 2 feet for HVAC units
	default:
		return 0.1 // 4 inches default
	}
}

func (v *Validator) requiresAccessibility(objType engine.ArxObjectType) bool {
	// Check if object type requires ADA compliance
	switch objType {
	case engine.ElectricalOutlet, engine.ElectricalPanel:
		return true
	default:
		return false
	}
}

func (v *Validator) checkAccessibility(obj *engine.ArxObject) bool {
	// Check ADA height requirements
	heightMM := obj.Z
	heightInches := float64(heightMM) / 25.4
	
	switch obj.Type {
	case engine.ElectricalOutlet:
		// Outlets must be between 15" and 48" AFF
		return heightInches >= 15 && heightInches <= 48
	case engine.ElectricalPanel:
		// Panels must have controls below 48" AFF
		return heightInches <= 48
	default:
		return true
	}
}

func (v *Validator) isElectrical(objType engine.ArxObjectType) bool {
	return objType >= engine.ElectricalOutlet && objType <= engine.ElectricalConduit
}

func (v *Validator) isStructural(objType engine.ArxObjectType) bool {
	return objType >= engine.StructuralBeam && objType <= engine.StructuralFoundation
}

func (v *Validator) getMaxSpan(obj *engine.ArxObject) float64 {
	// Calculate max span based on material and dimensions
	// This is simplified - real calculation would consider material properties
	
	depth := float64(obj.Height) / 1000.0 // Convert to meters
	
	// Rough span-to-depth ratio (simplified)
	spanToDepthRatio := 20.0 // For steel beam
	
	if material := obj.GetProperty("material"); material != nil {
		switch material.(string) {
		case "wood":
			spanToDepthRatio = 15.0
		case "concrete":
			spanToDepthRatio = 12.0
		case "steel":
			spanToDepthRatio = 20.0
		}
	}
	
	return depth * spanToDepthRatio
}

func (v *Validator) validateNEC(obj *engine.ArxObject) []Violation {
	violations := []Violation{}
	
	// NEC electrical code validation
	if v.isElectrical(obj.Type) {
		// Example: Check GFCI requirements
		if obj.Type == engine.ElectricalOutlet {
			if location := obj.GetProperty("location"); location != nil {
				// GFCI required in wet locations
				if v.isWetLocation(location.(string)) {
					if gfci := obj.GetProperty("gfci"); gfci == nil || !gfci.(bool) {
						violations = append(violations, Violation{
							ObjectID:       obj.ID,
							ConstraintType: ConstraintNEC,
							Field:          "gfci",
							Message:        "NEC requires GFCI protection in wet locations",
							Severity:       "error",
						})
					}
				}
			}
		}
	}
	
	return violations
}

func (v *Validator) validateIBC(obj *engine.ArxObject) []Violation {
	violations := []Violation{}
	
	// International Building Code validation
	// Add IBC-specific rules here
	
	return violations
}

func (v *Validator) validateADA(obj *engine.ArxObject) []Violation {
	violations := []Violation{}
	
	// ADA compliance validation
	if !v.checkAccessibility(obj) {
		violations = append(violations, Violation{
			ObjectID:       obj.ID,
			ConstraintType: ConstraintADA,
			Field:          "height",
			Message:        "Does not meet ADA accessibility requirements",
			Severity:       "error",
		})
	}
	
	return violations
}

func (v *Validator) isWetLocation(location string) bool {
	wetLocations := []string{"bathroom", "kitchen", "exterior", "garage", "laundry"}
	for _, wet := range wetLocations {
		if location == wet {
			return true
		}
	}
	return false
}

// BatchValidate validates multiple objects efficiently
func (v *Validator) BatchValidate(objectIDs []uint64) map[uint64][]Violation {
	results := make(map[uint64][]Violation)
	
	// Use goroutines for parallel validation
	var wg sync.WaitGroup
	var mu sync.Mutex
	
	for _, id := range objectIDs {
		wg.Add(1)
		go func(objID uint64) {
			defer wg.Done()
			
			if obj, exists := v.engine.GetObject(objID); exists {
				violations := v.ValidateObject(obj)
				
				mu.Lock()
				results[objID] = violations
				mu.Unlock()
			}
		}(id)
	}
	
	wg.Wait()
	return results
}

// ClearCache clears the validation cache
func (v *Validator) ClearCache() {
	v.cacheMu.Lock()
	v.cache = make(map[uint64]*ValidationResult)
	v.cacheMu.Unlock()
}

// GetStats returns validator statistics
func (v *Validator) GetStats() map[string]uint64 {
	return map[string]uint64{
		"validations": v.validations,
		"violations":  v.violations,
		"cache_size":  uint64(len(v.cache)),
	}
}