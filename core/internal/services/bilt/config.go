package bilt

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
)

// Default earning rates for different contribution types (BILT tokens)
func defaultEarningRates() map[string]float64 {
	return map[string]float64{
		// Primary data collection
		"scan":         10.0, // 3D/laser scanning a component
		"measurement":  5.0,  // Physical measurements
		"photo":        2.0,  // Photo documentation
		"validation":   3.0,  // Validating existing data
		"annotation":   1.0,  // Adding notes/annotations
		
		// Specialized contributions
		"electrical_trace": 15.0, // Tracing electrical circuits
		"hvac_mapping":     12.0, // Mapping HVAC systems
		"plumbing_trace":   12.0, // Tracing plumbing
		"structural_scan":  20.0, // Structural element scanning
		
		// Quality improvements
		"error_correction": 8.0,  // Fixing errors in existing data
		"precision_update": 6.0,  // Improving precision of measurements
		"metadata_update":  2.0,  // Adding metadata
		
		// Batch operations
		"bulk_validation": 25.0,  // Validating multiple components
		"floor_scan":      50.0,  // Scanning entire floor
		"room_inventory":  30.0,  // Complete room inventory
		
		// Default rate for unknown types
		"default": 1.0,
	}
}

// Default quality weights for scoring
func defaultQualityWeights() QualityWeights {
	return QualityWeights{
		Accuracy:     0.30, // 30% weight
		Completeness: 0.25, // 25% weight
		Consistency:  0.20, // 20% weight
		Freshness:    0.15, // 15% weight
		Validation:   0.10, // 10% weight
	}
}

// Default bonus multipliers for special conditions
func defaultBonusMultipliers() map[string]float64 {
	return map[string]float64{
		"first_scan":       2.0,  // First time scanning an object
		"critical_system":  1.5,  // Critical infrastructure
		"after_hours":      1.3,  // Work done after hours
		"high_precision":   1.4,  // GPS accuracy < 1 meter
		"complete_room":    1.5,  // Scanning all objects in a room
		"hazardous_area":   2.0,  // Working in hazardous areas
		"emergency_repair": 3.0,  // Emergency repair documentation
		"weekly_streak":    1.2,  // Contributing every day for a week
		"monthly_leader":   1.5,  // Top contributor for the month
	}
}

// Required fields for different object types
func getRequiredFields(objectType string) []string {
	requiredFields := map[string][]string{
		"outlet": {
			"voltage",
			"load",
			"type",
			"location",
		},
		"circuit": {
			"breaker_rating",
			"voltage",
			"phase",
			"wire_gauge",
		},
		"panel": {
			"voltage",
			"phase",
			"main_breaker",
			"circuit_count",
		},
		"hvac_unit": {
			"model",
			"capacity",
			"refrigerant_type",
			"age",
		},
		"thermostat": {
			"model",
			"setpoint",
			"current_temp",
			"zone",
		},
		"room": {
			"area",
			"height",
			"occupancy_type",
			"hvac_zone",
		},
		"door": {
			"type",
			"material",
			"fire_rating",
			"width",
			"height",
		},
		"window": {
			"type",
			"glazing",
			"width",
			"height",
		},
	}
	
	if fields, exists := requiredFields[objectType]; exists {
		return fields
	}
	
	// Default required fields for unknown types
	return []string{"type", "location", "status"}
}

// Extract object type from path
func extractObjectType(path string) string {
	// Parse the path to determine object type
	parts := strings.Split(strings.TrimPrefix(path, "/"), "/")
	
	if len(parts) == 0 {
		return "unknown"
	}
	
	// Check last part of path for type hints
	lastPart := strings.ToLower(parts[len(parts)-1])
	
	if strings.Contains(lastPart, "outlet") {
		return "outlet"
	} else if strings.Contains(lastPart, "circuit") {
		return "circuit"
	} else if strings.Contains(lastPart, "panel") {
		return "panel"
	} else if strings.Contains(lastPart, "breaker") {
		return "breaker"
	} else if strings.Contains(lastPart, "thermostat") {
		return "thermostat"
	} else if strings.Contains(lastPart, "ahu") || strings.Contains(lastPart, "air-handler") {
		return "hvac_unit"
	} else if strings.Contains(lastPart, "room") {
		return "room"
	} else if strings.Contains(lastPart, "door") {
		return "door"
	} else if strings.Contains(lastPart, "window") {
		return "window"
	}
	
	// Check system type from path
	if len(parts) > 0 {
		switch parts[0] {
		case "electrical":
			return "electrical_component"
		case "hvac":
			return "hvac_component"
		case "plumbing":
			return "plumbing_component"
		case "structural":
			return "structural_component"
		}
	}
	
	return "component"
}

// Check if path represents a critical system
func isCriticalSystem(path string) bool {
	criticalPaths := []string{
		"/electrical/main-panel",
		"/electrical/emergency",
		"/hvac/chillers",
		"/fire",
		"/security/access-control",
		"/plumbing/main-shutoff",
		"/network/core-switch",
		"/structural/load-bearing",
	}
	
	for _, critical := range criticalPaths {
		if strings.HasPrefix(path, critical) {
			return true
		}
	}
	
	return false
}

// Check if timestamp is after normal working hours
func isAfterHours(timestamp time.Time) bool {
	hour := timestamp.Hour()
	weekday := timestamp.Weekday()
	
	// After hours: before 8am, after 6pm, or weekends
	if hour < 8 || hour >= 18 {
		return true
	}
	
	if weekday == time.Saturday || weekday == time.Sunday {
		return true
	}
	
	return false
}

// Generate unique transaction ID
func generateTransactionID() string {
	bytes := make([]byte, 8)
	rand.Read(bytes)
	return fmt.Sprintf("tx_%s_%d", hex.EncodeToString(bytes), time.Now().UnixNano())
}

// Generate unique contribution ID
func generateContributionID() string {
	bytes := make([]byte, 8)
	rand.Read(bytes)
	return fmt.Sprintf("contrib_%s_%d", hex.EncodeToString(bytes), time.Now().UnixNano())
}

// RewardTiers defines token reward tiers based on contribution quality
type RewardTiers struct {
	Excellent float64 // 90-100% quality
	Good      float64 // 70-89% quality
	Average   float64 // 50-69% quality
	Poor      float64 // Below 50% (no reward)
}

// GetRewardTiers returns the reward multipliers for different quality tiers
func GetRewardTiers() RewardTiers {
	return RewardTiers{
		Excellent: 1.5,
		Good:      1.0,
		Average:   0.7,
		Poor:      0.0,
	}
}

// ContributionStats tracks statistics for contributions
type ContributionStats struct {
	TotalContributions int
	AcceptedCount      int
	RejectedCount      int
	TotalTokensEarned  float64
	AverageQuality     float64
	TopDataType        string
	TopObjectPath      string
	ContributionsByType map[string]int
	ContributionsByPath map[string]int
}

// ValidationRules defines rules for validating contributions
type ValidationRules struct {
	MinConfidence    float64
	MaxDataAge       time.Duration
	MinGPSAccuracy   float64
	RequiredFields   []string
	ForbiddenValues  map[string]interface{}
	ValueRanges      map[string]ValueRange
}

// ValueRange defines acceptable range for a numeric value
type ValueRange struct {
	Min float64
	Max float64
}

// GetValidationRules returns validation rules for an object type
func GetValidationRules(objectType string) ValidationRules {
	// Default rules
	rules := ValidationRules{
		MinConfidence:  0.5,
		MaxDataAge:     90 * 24 * time.Hour, // 90 days
		MinGPSAccuracy: 10.0,                // 10 meters
		RequiredFields: getRequiredFields(objectType),
		ValueRanges:    make(map[string]ValueRange),
	}
	
	// Type-specific rules
	switch objectType {
	case "outlet":
		rules.ValueRanges["voltage"] = ValueRange{Min: 100, Max: 250}
		rules.ValueRanges["load"] = ValueRange{Min: 0, Max: 30}
		
	case "circuit":
		rules.ValueRanges["breaker_rating"] = ValueRange{Min: 15, Max: 100}
		rules.ValueRanges["voltage"] = ValueRange{Min: 100, Max: 600}
		
	case "panel":
		rules.ValueRanges["voltage"] = ValueRange{Min: 100, Max: 600}
		rules.ValueRanges["circuit_count"] = ValueRange{Min: 1, Max: 84}
		
	case "thermostat":
		rules.ValueRanges["setpoint"] = ValueRange{Min: 50, Max: 90}
		rules.ValueRanges["current_temp"] = ValueRange{Min: 32, Max: 120}
		
	case "room":
		rules.ValueRanges["area"] = ValueRange{Min: 10, Max: 10000}
		rules.ValueRanges["height"] = ValueRange{Min: 7, Max: 30}
	}
	
	return rules
}