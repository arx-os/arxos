// Package logic_engine provides business logic and rules processing
package logic_engine

import (
	"fmt"
	"github.com/arxos/arxos/core/internal/arxobject"
)

// LogicEngine processes business rules and logic
type LogicEngine struct {
	rules []Rule
}

// Rule represents a business rule
type Rule struct {
	ID          string
	Name        string
	Description string
	Condition   func(*arxobject.ArxObject) bool
	Action      func(*arxobject.ArxObject) error
	Priority    int
}

// NewLogicEngine creates a new logic engine
func NewLogicEngine() *LogicEngine {
	return &LogicEngine{
		rules: make([]Rule, 0),
	}
}

// AddRule adds a new rule to the engine
func (e *LogicEngine) AddRule(rule Rule) {
	e.rules = append(e.rules, rule)
}

// ProcessObject applies all rules to an ArxObject
func (e *LogicEngine) ProcessObject(obj *arxobject.ArxObject) error {
	for _, rule := range e.rules {
		if rule.Condition(obj) {
			if err := rule.Action(obj); err != nil {
				return fmt.Errorf("rule %s failed: %w", rule.Name, err)
			}
		}
	}
	return nil
}

// ProcessBatch processes multiple objects
func (e *LogicEngine) ProcessBatch(objects []*arxobject.ArxObject) error {
	for _, obj := range objects {
		if err := e.ProcessObject(obj); err != nil {
			return err
		}
	}
	return nil
}

// DefaultRules returns a set of default rules
func DefaultRules() []Rule {
	return []Rule{
		{
			ID:          "confidence_threshold",
			Name:        "Confidence Threshold",
			Description: "Mark objects below confidence threshold",
			Condition: func(obj *arxobject.ArxObject) bool {
				return obj.Confidence < 0.5
			},
			Action: func(obj *arxobject.ArxObject) error {
				obj.SetProperty("needs_review", true)
				return nil
			},
			Priority: 1,
		},
		{
			ID:          "validation_required",
			Name:        "Validation Required",
			Description: "Mark critical objects for validation",
			Condition: func(obj *arxobject.ArxObject) bool {
				return obj.Type == arxobject.TypeFireSprinkler || 
					   obj.Type == arxobject.TypeEmergencyExit
			},
			Action: func(obj *arxobject.ArxObject) error {
				obj.SetProperty("validation_required", true)
				obj.SetProperty("priority", "high")
				return nil
			},
			Priority: 2,
		},
	}
}

// Validate checks if an object passes all validation rules
func (e *LogicEngine) Validate(obj *arxobject.ArxObject) (bool, []string) {
	var errors []string
	
	// Check required fields
	if obj.Name == "" {
		errors = append(errors, "name is required")
	}
	
	if obj.Type == "" {
		errors = append(errors, "type is required")
	}
	
	if obj.BuildingID == "" {
		errors = append(errors, "building_id is required")
	}
	
	// Check confidence
	if obj.Confidence < 0 || obj.Confidence > 1 {
		errors = append(errors, "confidence must be between 0 and 1")
	}
	
	return len(errors) == 0, errors
}