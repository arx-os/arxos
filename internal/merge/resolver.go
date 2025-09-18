package merge

import (
	"fmt"
	"math"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
)

// ResolutionMethod defines how to resolve conflicts
type ResolutionMethod string

const (
	MethodAutomatic   ResolutionMethod = "automatic"    // Resolve automatically based on rules
	MethodManual      ResolutionMethod = "manual"       // Require manual intervention
	MethodFieldVerify ResolutionMethod = "field_verify" // Require field verification
	MethodIgnore      ResolutionMethod = "ignore"       // Ignore the conflict
)

// ConflictResolver handles conflict resolution between data sources
type ConflictResolver struct {
	rules                []ResolutionRule
	history              []ResolutionHistory
	confidenceManager    *spatial.ConfidenceManager
	defaultMethod        ResolutionMethod
	autoResolveThreshold float64 // Confidence threshold for automatic resolution
}

// ResolutionRule defines a rule for automatic conflict resolution
type ResolutionRule struct {
	ID           string           `json:"id"`
	Name         string           `json:"name"`
	Description  string           `json:"description"`
	ConflictType string           `json:"conflict_type"` // "position", "dimension", "type"
	Condition    RuleCondition    `json:"condition"`
	Action       ResolutionAction `json:"action"`
	Priority     int              `json:"priority"` // Higher priority rules are evaluated first
	Enabled      bool             `json:"enabled"`
}

// RuleCondition defines when a rule applies
type RuleCondition struct {
	MinDifference       float64                 `json:"min_difference,omitempty"`
	MaxDifference       float64                 `json:"max_difference,omitempty"`
	SourceTypes         []string                `json:"source_types,omitempty"`
	MinConfidence       spatial.ConfidenceLevel `json:"min_confidence,omitempty"`
	TimeDifferenceHours float64                 `json:"time_difference_hours,omitempty"`
}

// ResolutionAction defines what action to take
type ResolutionAction struct {
	Method          ResolutionMethod `json:"method"`
	PreferSource    string           `json:"prefer_source,omitempty"` // "highest_confidence", "most_recent", "lidar", etc.
	UseAverage      bool             `json:"use_average,omitempty"`
	NotifyUser      bool             `json:"notify_user"`
	RequireApproval bool             `json:"require_approval"`
}

// ResolutionHistory tracks resolution decisions
type ResolutionHistory struct {
	ID          string           `json:"id"`
	Conflict    Conflict         `json:"conflict"`
	Method      ResolutionMethod `json:"method"`
	RuleApplied *ResolutionRule  `json:"rule_applied,omitempty"`
	Resolution  interface{}      `json:"resolution"`
	ResolvedBy  string           `json:"resolved_by"` // "system" or user ID
	Timestamp   time.Time        `json:"timestamp"`
	Notes       string           `json:"notes,omitempty"`
}

// NewConflictResolver creates a new conflict resolver
func NewConflictResolver(confidenceManager *spatial.ConfidenceManager) *ConflictResolver {
	resolver := &ConflictResolver{
		confidenceManager:    confidenceManager,
		defaultMethod:        MethodManual,
		autoResolveThreshold: 0.8,
		history:              make([]ResolutionHistory, 0),
	}

	// Add default resolution rules
	resolver.addDefaultRules()

	return resolver
}

// addDefaultRules adds default conflict resolution rules
func (r *ConflictResolver) addDefaultRules() {
	// Rule 1: Small position differences with high confidence
	r.AddRule(ResolutionRule{
		ID:           "pos_small_diff_high_conf",
		Name:         "Small Position Difference - High Confidence",
		Description:  "Automatically resolve small position differences when confidence is high",
		ConflictType: "position",
		Condition: RuleCondition{
			MaxDifference: 0.3, // 30cm
			MinConfidence: spatial.ConfidenceHigh,
		},
		Action: ResolutionAction{
			Method:       MethodAutomatic,
			PreferSource: "highest_confidence",
			NotifyUser:   false,
		},
		Priority: 10,
		Enabled:  true,
	})

	// Rule 2: Prefer LiDAR for dimensions
	r.AddRule(ResolutionRule{
		ID:           "dim_prefer_lidar",
		Name:         "Dimension Conflict - Prefer LiDAR",
		Description:  "Prefer LiDAR measurements for dimension conflicts",
		ConflictType: "dimension",
		Condition: RuleCondition{
			SourceTypes: []string{"lidar"},
		},
		Action: ResolutionAction{
			Method:       MethodAutomatic,
			PreferSource: "lidar",
			NotifyUser:   true,
		},
		Priority: 9,
		Enabled:  true,
	})

	// Rule 3: Large position differences require verification
	r.AddRule(ResolutionRule{
		ID:           "pos_large_diff",
		Name:         "Large Position Difference",
		Description:  "Large position differences require field verification",
		ConflictType: "position",
		Condition: RuleCondition{
			MinDifference: 3.0, // 3 meters
		},
		Action: ResolutionAction{
			Method:          MethodFieldVerify,
			NotifyUser:      true,
			RequireApproval: true,
		},
		Priority: 8,
		Enabled:  true,
	})

	// Rule 4: Type conflicts with recent data
	r.AddRule(ResolutionRule{
		ID:           "type_recent_data",
		Name:         "Type Conflict - Use Recent",
		Description:  "Use most recent data for type conflicts",
		ConflictType: "type",
		Condition: RuleCondition{
			TimeDifferenceHours: 168, // 1 week
		},
		Action: ResolutionAction{
			Method:       MethodAutomatic,
			PreferSource: "most_recent",
			NotifyUser:   true,
		},
		Priority: 7,
		Enabled:  true,
	})

	// Rule 5: Average small dimension differences
	r.AddRule(ResolutionRule{
		ID:           "dim_small_diff_average",
		Name:         "Small Dimension Difference - Average",
		Description:  "Average small dimension differences",
		ConflictType: "dimension",
		Condition: RuleCondition{
			MaxDifference: 0.1, // 10%
		},
		Action: ResolutionAction{
			Method:     MethodAutomatic,
			UseAverage: true,
			NotifyUser: false,
		},
		Priority: 6,
		Enabled:  true,
	})
}

// AddRule adds a resolution rule
func (r *ConflictResolver) AddRule(rule ResolutionRule) {
	r.rules = append(r.rules, rule)
	// Sort rules by priority (descending)
	sort.Slice(r.rules, func(i, j int) bool {
		return r.rules[i].Priority > r.rules[j].Priority
	})
}

// ResolveConflict resolves a conflict based on rules
func (r *ConflictResolver) ResolveConflict(conflict Conflict) (*ResolutionResult, error) {
	// Find applicable rule
	rule := r.findApplicableRule(conflict)

	if rule != nil {
		// Apply rule action
		return r.applyRule(conflict, rule)
	}

	// No rule found, use default method
	return r.applyDefaultResolution(conflict)
}

// ResolutionResult represents the result of conflict resolution
type ResolutionResult struct {
	Method         ResolutionMethod        `json:"method"`
	ResolvedValue  interface{}             `json:"resolved_value"`
	Confidence     spatial.ConfidenceLevel `json:"confidence"`
	RuleApplied    *ResolutionRule         `json:"rule_applied,omitempty"`
	RequiresAction bool                    `json:"requires_action"`
	ActionRequired string                  `json:"action_required,omitempty"`
}

// findApplicableRule finds the first applicable rule for a conflict
func (r *ConflictResolver) findApplicableRule(conflict Conflict) *ResolutionRule {
	for _, rule := range r.rules {
		if !rule.Enabled {
			continue
		}

		if rule.ConflictType != conflict.Type {
			continue
		}

		if r.conditionMatches(conflict, rule.Condition) {
			return &rule
		}
	}
	return nil
}

// conditionMatches checks if a conflict matches a rule condition
func (r *ConflictResolver) conditionMatches(conflict Conflict, condition RuleCondition) bool {
	// Check difference range
	if condition.MinDifference > 0 && conflict.Difference < condition.MinDifference {
		return false
	}
	if condition.MaxDifference > 0 && conflict.Difference > condition.MaxDifference {
		return false
	}

	// Check source types
	if len(condition.SourceTypes) > 0 {
		hasType := false
		for _, sourceType := range condition.SourceTypes {
			if conflict.Source1.Type == sourceType || conflict.Source2.Type == sourceType {
				hasType = true
				break
			}
		}
		if !hasType {
			return false
		}
	}

	// Check confidence
	if condition.MinConfidence > 0 {
		if conflict.Source1.Confidence < condition.MinConfidence &&
			conflict.Source2.Confidence < condition.MinConfidence {
			return false
		}
	}

	// Check time difference
	if condition.TimeDifferenceHours > 0 {
		timeDiff := math.Abs(conflict.Source1.Timestamp.Sub(conflict.Source2.Timestamp).Hours())
		if timeDiff < condition.TimeDifferenceHours {
			return false
		}
	}

	return true
}

// applyRule applies a resolution rule to a conflict
func (r *ConflictResolver) applyRule(conflict Conflict, rule *ResolutionRule) (*ResolutionResult, error) {
	result := &ResolutionResult{
		Method:      rule.Action.Method,
		RuleApplied: rule,
	}

	switch rule.Action.Method {
	case MethodAutomatic:
		// Resolve automatically based on action
		if rule.Action.UseAverage {
			result.ResolvedValue = r.calculateAverage(conflict)
			result.Confidence = r.calculateAverageConfidence(conflict)
		} else if rule.Action.PreferSource != "" {
			result.ResolvedValue = r.selectPreferredValue(conflict, rule.Action.PreferSource)
			result.Confidence = r.selectPreferredConfidence(conflict, rule.Action.PreferSource)
		}

		if rule.Action.NotifyUser {
			result.RequiresAction = true
			result.ActionRequired = "review_automatic_resolution"
		}

	case MethodManual:
		result.RequiresAction = true
		result.ActionRequired = "manual_resolution_required"

	case MethodFieldVerify:
		result.RequiresAction = true
		result.ActionRequired = "field_verification_required"

	case MethodIgnore:
		// Use value from higher confidence source
		if conflict.Source1.Confidence >= conflict.Source2.Confidence {
			result.ResolvedValue = conflict.Value1
			result.Confidence = conflict.Source1.Confidence
		} else {
			result.ResolvedValue = conflict.Value2
			result.Confidence = conflict.Source2.Confidence
		}
	}

	// Record resolution in history
	r.recordResolution(conflict, result, rule)

	return result, nil
}

// applyDefaultResolution applies default resolution when no rule matches
func (r *ConflictResolver) applyDefaultResolution(conflict Conflict) (*ResolutionResult, error) {
	result := &ResolutionResult{
		Method:         r.defaultMethod,
		RequiresAction: true,
	}

	switch r.defaultMethod {
	case MethodAutomatic:
		// Use highest confidence
		if conflict.Source1.Confidence >= conflict.Source2.Confidence {
			result.ResolvedValue = conflict.Value1
			result.Confidence = conflict.Source1.Confidence
		} else {
			result.ResolvedValue = conflict.Value2
			result.Confidence = conflict.Source2.Confidence
		}
		result.ActionRequired = "review_default_resolution"

	case MethodManual:
		result.ActionRequired = "manual_resolution_required"

	default:
		result.ActionRequired = "resolution_required"
	}

	// Record resolution
	r.recordResolution(conflict, result, nil)

	return result, nil
}

// calculateAverage calculates average value for numeric conflicts
func (r *ConflictResolver) calculateAverage(conflict Conflict) interface{} {
	switch conflict.Type {
	case "position":
		if p1, ok1 := conflict.Value1.(spatial.Point3D); ok1 {
			if p2, ok2 := conflict.Value2.(spatial.Point3D); ok2 {
				return spatial.Point3D{
					X: (p1.X + p2.X) / 2,
					Y: (p1.Y + p2.Y) / 2,
					Z: (p1.Z + p2.Z) / 2,
				}
			}
		}
	case "dimension":
		if d1, ok1 := conflict.Value1.(Dimensions); ok1 {
			if d2, ok2 := conflict.Value2.(Dimensions); ok2 {
				return Dimensions{
					Length: (d1.Length + d2.Length) / 2,
					Width:  (d1.Width + d2.Width) / 2,
					Height: (d1.Height + d2.Height) / 2,
				}
			}
		}
	}
	return conflict.Value1 // Default to first value
}

// calculateAverageConfidence calculates average confidence
func (r *ConflictResolver) calculateAverageConfidence(conflict Conflict) spatial.ConfidenceLevel {
	avg := (int(conflict.Source1.Confidence) + int(conflict.Source2.Confidence)) / 2
	return spatial.ConfidenceLevel(avg)
}

// selectPreferredValue selects value based on preference
func (r *ConflictResolver) selectPreferredValue(conflict Conflict, preference string) interface{} {
	switch preference {
	case "highest_confidence":
		if conflict.Source1.Confidence >= conflict.Source2.Confidence {
			return conflict.Value1
		}
		return conflict.Value2
	case "most_recent":
		if conflict.Source1.Timestamp.After(conflict.Source2.Timestamp) {
			return conflict.Value1
		}
		return conflict.Value2
	case "lidar":
		if conflict.Source1.Type == "lidar" {
			return conflict.Value1
		}
		if conflict.Source2.Type == "lidar" {
			return conflict.Value2
		}
	}
	return conflict.Value1 // Default to first value
}

// selectPreferredConfidence selects confidence based on preference
func (r *ConflictResolver) selectPreferredConfidence(conflict Conflict, preference string) spatial.ConfidenceLevel {
	switch preference {
	case "highest_confidence":
		if conflict.Source1.Confidence >= conflict.Source2.Confidence {
			return conflict.Source1.Confidence
		}
		return conflict.Source2.Confidence
	case "most_recent":
		if conflict.Source1.Timestamp.After(conflict.Source2.Timestamp) {
			return conflict.Source1.Confidence
		}
		return conflict.Source2.Confidence
	case "lidar":
		if conflict.Source1.Type == "lidar" {
			return conflict.Source1.Confidence
		}
		if conflict.Source2.Type == "lidar" {
			return conflict.Source2.Confidence
		}
	}
	return conflict.Source1.Confidence
}

// recordResolution records resolution in history
func (r *ConflictResolver) recordResolution(conflict Conflict, result *ResolutionResult, rule *ResolutionRule) {
	history := ResolutionHistory{
		ID:          fmt.Sprintf("res_%d", time.Now().UnixNano()),
		Conflict:    conflict,
		Method:      result.Method,
		RuleApplied: rule,
		Resolution:  result.ResolvedValue,
		ResolvedBy:  "system",
		Timestamp:   time.Now(),
	}

	r.history = append(r.history, history)
}

// GetHistory returns resolution history
func (r *ConflictResolver) GetHistory() []ResolutionHistory {
	return r.history
}

// GetRecentHistory returns recent resolution history
func (r *ConflictResolver) GetRecentHistory(since time.Duration) []ResolutionHistory {
	cutoff := time.Now().Add(-since)
	recent := make([]ResolutionHistory, 0)

	for _, h := range r.history {
		if h.Timestamp.After(cutoff) {
			recent = append(recent, h)
		}
	}

	return recent
}

// SetDefaultMethod sets the default resolution method
func (r *ConflictResolver) SetDefaultMethod(method ResolutionMethod) {
	r.defaultMethod = method
}

// SetAutoResolveThreshold sets the confidence threshold for automatic resolution
func (r *ConflictResolver) SetAutoResolveThreshold(threshold float64) {
	r.autoResolveThreshold = threshold
}

// GetRules returns all resolution rules
func (r *ConflictResolver) GetRules() []ResolutionRule {
	return r.rules
}

// EnableRule enables or disables a rule
func (r *ConflictResolver) EnableRule(ruleID string, enabled bool) error {
	for i := range r.rules {
		if r.rules[i].ID == ruleID {
			r.rules[i].Enabled = enabled
			return nil
		}
	}
	return fmt.Errorf("rule %s not found", ruleID)
}
