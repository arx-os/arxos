package logic

import (
	"context"
	"fmt"
	"math"
	"reflect"
	"strconv"
	"strings"
	"sync"
	"time"

	"go.uber.org/zap"
)

// LogicType represents the type of logic
type LogicType string

const (
	LogicTypeThreshold  LogicType = "threshold"
	LogicTypeTimeBased  LogicType = "time_based"
	LogicTypeSpatial    LogicType = "spatial"
	LogicTypeRelational LogicType = "relational"
	LogicTypeComplex    LogicType = "complex"
)

// LogicOperator represents logical operators
type LogicOperator string

const (
	LogicOperatorAnd  LogicOperator = "and"
	LogicOperatorOr   LogicOperator = "or"
	LogicOperatorNot  LogicOperator = "not"
	LogicOperatorXor  LogicOperator = "xor"
	LogicOperatorNand LogicOperator = "nand"
	LogicOperatorNor  LogicOperator = "nor"
)

// ComparisonOperator represents comparison operators
type ComparisonOperator string

const (
	ComparisonOperatorEqual        ComparisonOperator = "=="
	ComparisonOperatorNotEqual     ComparisonOperator = "!="
	ComparisonOperatorGreaterThan  ComparisonOperator = ">"
	ComparisonOperatorGreaterEqual ComparisonOperator = ">="
	ComparisonOperatorLessThan     ComparisonOperator = "<"
	ComparisonOperatorLessEqual    ComparisonOperator = "<="
	ComparisonOperatorBetween      ComparisonOperator = "between"
	ComparisonOperatorIn           ComparisonOperator = "in"
	ComparisonOperatorNotIn        ComparisonOperator = "not_in"
)

// Condition represents a condition for evaluation
type Condition struct {
	ID         string                 `json:"id"`
	Type       LogicType              `json:"type"`
	Operator   interface{}            `json:"operator"` // LogicOperator or ComparisonOperator
	Operands   []interface{}          `json:"operands"`
	Parameters map[string]interface{} `json:"parameters"`
	Enabled    bool                   `json:"enabled"`
	Priority   int                    `json:"priority"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
}

// ConditionResult represents the result of condition evaluation
type ConditionResult struct {
	ConditionID    string                 `json:"condition_id"`
	Success        bool                   `json:"success"`
	Result         bool                   `json:"result"`
	EvaluationTime float64                `json:"evaluation_time"`
	Context        map[string]interface{} `json:"context"`
	Timestamp      time.Time              `json:"timestamp"`
	Error          *string                `json:"error"`
}

// ComplexCondition represents a complex multi-condition logical expression
type ComplexCondition struct {
	ID         string          `json:"id"`
	Name       string          `json:"name"`
	Conditions []*Condition    `json:"conditions"`
	Operators  []LogicOperator `json:"operators"`
	Precedence []int           `json:"precedence"`
	Enabled    bool            `json:"enabled"`
	CreatedAt  time.Time       `json:"created_at"`
}

// ConditionalLogicEngine provides comprehensive conditional logic evaluation
type ConditionalLogicEngine struct {
	logger *zap.Logger
	mu     sync.RWMutex

	// Condition management
	conditions        map[string]*Condition
	complexConditions map[string]*ComplexCondition

	// Performance tracking
	evaluationStats map[string]*EvaluationStats
	evaluators      map[LogicType]ConditionEvaluator

	// Configuration
	config *ConditionalLogicConfig
}

// ConditionalLogicConfig holds conditional logic configuration
type ConditionalLogicConfig struct {
	EnableCaching             bool          `json:"enable_caching"`
	EnablePerformanceTracking bool          `json:"enable_performance_tracking"`
	MaxEvaluationTime         time.Duration `json:"max_evaluation_time"`
	CacheExpiration           time.Duration `json:"cache_expiration"`
	DefaultTimeout            time.Duration `json:"default_timeout"`
}

// EvaluationStats holds evaluation statistics
type EvaluationStats struct {
	TotalEvaluations      int64         `json:"total_evaluations"`
	SuccessfulEvaluations int64         `json:"successful_evaluations"`
	FailedEvaluations     int64         `json:"failed_evaluations"`
	TotalEvaluationTime   time.Duration `json:"total_evaluation_time"`
	AverageEvaluationTime time.Duration `json:"average_evaluation_time"`
	LastEvaluationTime    time.Time     `json:"last_evaluation_time"`
}

// ConditionEvaluator is the interface for condition evaluators
type ConditionEvaluator interface {
	Evaluate(ctx context.Context, condition *Condition, context map[string]interface{}) (bool, error)
}

// NewConditionalLogicEngine creates a new conditional logic engine
func NewConditionalLogicEngine(logger *zap.Logger, config *ConditionalLogicConfig) (*ConditionalLogicEngine, error) {
	if config == nil {
		config = &ConditionalLogicConfig{
			EnableCaching:             true,
			EnablePerformanceTracking: true,
			MaxEvaluationTime:         5 * time.Second,
			CacheExpiration:           10 * time.Minute,
			DefaultTimeout:            1 * time.Second,
		}
	}

	cle := &ConditionalLogicEngine{
		logger:            logger,
		conditions:        make(map[string]*Condition),
		complexConditions: make(map[string]*ComplexCondition),
		evaluationStats:   make(map[string]*EvaluationStats),
		evaluators:        make(map[LogicType]ConditionEvaluator),
		config:            config,
	}

	// Initialize default evaluators
	cle.initializeDefaultEvaluators()

	logger.Info("Conditional logic engine initialized",
		zap.Bool("enable_caching", config.EnableCaching),
		zap.Bool("enable_performance_tracking", config.EnablePerformanceTracking),
		zap.Duration("max_evaluation_time", config.MaxEvaluationTime))

	return cle, nil
}

// RegisterCondition registers a new condition
func (cle *ConditionalLogicEngine) RegisterCondition(condition *Condition) error {
	cle.mu.Lock()
	defer cle.mu.Unlock()

	if err := cle.validateCondition(condition); err != nil {
		return fmt.Errorf("condition validation failed: %w", err)
	}

	condition.CreatedAt = time.Now()
	condition.UpdatedAt = time.Now()

	cle.conditions[condition.ID] = condition
	cle.evaluationStats[condition.ID] = &EvaluationStats{}

	cle.logger.Info("Condition registered",
		zap.String("condition_id", condition.ID),
		zap.String("type", string(condition.Type)))

	return nil
}

// UnregisterCondition unregisters a condition
func (cle *ConditionalLogicEngine) UnregisterCondition(conditionID string) error {
	cle.mu.Lock()
	defer cle.mu.Unlock()

	if _, exists := cle.conditions[conditionID]; !exists {
		return fmt.Errorf("condition not found: %s", conditionID)
	}

	delete(cle.conditions, conditionID)
	delete(cle.evaluationStats, conditionID)

	cle.logger.Info("Condition unregistered",
		zap.String("condition_id", conditionID))

	return nil
}

// EvaluateCondition evaluates a single condition
func (cle *ConditionalLogicEngine) EvaluateCondition(ctx context.Context, conditionID string, context map[string]interface{}) (*ConditionResult, error) {
	cle.mu.RLock()
	condition, exists := cle.conditions[conditionID]
	cle.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("condition not found: %s", conditionID)
	}

	if !condition.Enabled {
		return &ConditionResult{
			ConditionID: conditionID,
			Success:     true,
			Result:      false,
			Timestamp:   time.Now(),
		}, nil
	}

	startTime := time.Now()
	result, err := cle.evaluateCondition(ctx, condition, context)
	evaluationTime := time.Since(startTime).Seconds()

	conditionResult := &ConditionResult{
		ConditionID:    conditionID,
		Success:        err == nil,
		Result:         result,
		EvaluationTime: evaluationTime,
		Context:        context,
		Timestamp:      time.Now(),
	}

	if err != nil {
		errorMsg := err.Error()
		conditionResult.Error = &errorMsg
	}

	// Update statistics
	cle.updateEvaluationStats(conditionID, evaluationTime, err == nil)

	return conditionResult, err
}

// EvaluateComplexCondition evaluates a complex condition
func (cle *ConditionalLogicEngine) EvaluateComplexCondition(ctx context.Context, complexCondition *ComplexCondition, context map[string]interface{}) (*ConditionResult, error) {
	if !complexCondition.Enabled {
		return &ConditionResult{
			ConditionID: complexCondition.ID,
			Success:     true,
			Result:      false,
			Timestamp:   time.Now(),
		}, nil
	}

	startTime := time.Now()

	// Evaluate all conditions
	var values []bool
	for _, condition := range complexCondition.Conditions {
		result, err := cle.EvaluateCondition(ctx, condition.ID, context)
		if err != nil {
			return &ConditionResult{
				ConditionID:    complexCondition.ID,
				Success:        false,
				Result:         false,
				EvaluationTime: time.Since(startTime).Seconds(),
				Context:        context,
				Timestamp:      time.Now(),
				Error:          &err.Error(),
			}, err
		}
		values = append(values, result.Result)
	}

	// Apply logical operators
	result := cle.applyLogicalOperators(values, complexCondition.Operators, complexCondition.Precedence)

	evaluationTime := time.Since(startTime).Seconds()

	return &ConditionResult{
		ConditionID:    complexCondition.ID,
		Success:        true,
		Result:         result,
		EvaluationTime: evaluationTime,
		Context:        context,
		Timestamp:      time.Now(),
	}, nil
}

// GetLogicStats returns logic evaluation statistics
func (cle *ConditionalLogicEngine) GetLogicStats() map[string]interface{} {
	cle.mu.RLock()
	defer cle.mu.RUnlock()

	stats := map[string]interface{}{
		"total_conditions":        len(cle.conditions),
		"complex_conditions":      len(cle.complexConditions),
		"total_evaluations":       0,
		"successful_evaluations":  0,
		"failed_evaluations":      0,
		"average_evaluation_time": 0.0,
	}

	var totalEvaluations, successfulEvaluations, failedEvaluations int64
	var totalEvaluationTime time.Duration

	for _, evalStats := range cle.evaluationStats {
		totalEvaluations += evalStats.TotalEvaluations
		successfulEvaluations += evalStats.SuccessfulEvaluations
		failedEvaluations += evalStats.FailedEvaluations
		totalEvaluationTime += evalStats.TotalEvaluationTime
	}

	stats["total_evaluations"] = totalEvaluations
	stats["successful_evaluations"] = successfulEvaluations
	stats["failed_evaluations"] = failedEvaluations

	if totalEvaluations > 0 {
		stats["average_evaluation_time"] = totalEvaluationTime.Seconds() / float64(totalEvaluations)
	}

	return stats
}

// GetCondition retrieves a condition by ID
func (cle *ConditionalLogicEngine) GetCondition(conditionID string) (*Condition, bool) {
	cle.mu.RLock()
	defer cle.mu.RUnlock()

	condition, exists := cle.conditions[conditionID]
	return condition, exists
}

// GetAllConditions returns all registered conditions
func (cle *ConditionalLogicEngine) GetAllConditions() map[string]*Condition {
	cle.mu.RLock()
	defer cle.mu.RUnlock()

	result := make(map[string]*Condition)
	for id, condition := range cle.conditions {
		result[id] = condition
	}
	return result
}

// Helper functions

func (cle *ConditionalLogicEngine) validateCondition(condition *Condition) error {
	if condition.ID == "" {
		return fmt.Errorf("condition ID is required")
	}

	if condition.Type == "" {
		return fmt.Errorf("condition type is required")
	}

	// Validate evaluator exists for condition type
	if _, exists := cle.evaluators[condition.Type]; !exists {
		return fmt.Errorf("no evaluator found for condition type: %s", condition.Type)
	}

	return nil
}

func (cle *ConditionalLogicEngine) evaluateCondition(ctx context.Context, condition *Condition, context map[string]interface{}) (bool, error) {
	evaluator, exists := cle.evaluators[condition.Type]
	if !exists {
		return false, fmt.Errorf("no evaluator found for condition type: %s", condition.Type)
	}

	return evaluator.Evaluate(ctx, condition, context)
}

func (cle *ConditionalLogicEngine) applyLogicalOperators(values []bool, operators []LogicOperator, precedence []int) bool {
	if len(values) == 0 {
		return false
	}

	if len(values) == 1 {
		return values[0]
	}

	// Apply operators based on precedence
	result := values[0]
	for i, operator := range operators {
		if i+1 >= len(values) {
			break
		}

		nextValue := values[i+1]
		result = cle.applyLogicalOperator(result, operator, nextValue)
	}

	return result
}

func (cle *ConditionalLogicEngine) applyLogicalOperator(a bool, operator LogicOperator, b bool) bool {
	switch operator {
	case LogicOperatorAnd:
		return a && b
	case LogicOperatorOr:
		return a || b
	case LogicOperatorNot:
		return !a
	case LogicOperatorXor:
		return a != b
	case LogicOperatorNand:
		return !(a && b)
	case LogicOperatorNor:
		return !(a || b)
	default:
		return false
	}
}

func (cle *ConditionalLogicEngine) updateEvaluationStats(conditionID string, evaluationTime float64, success bool) {
	cle.mu.Lock()
	defer cle.mu.Unlock()

	stats, exists := cle.evaluationStats[conditionID]
	if !exists {
		stats = &EvaluationStats{}
		cle.evaluationStats[conditionID] = stats
	}

	stats.TotalEvaluations++
	stats.TotalEvaluationTime += time.Duration(evaluationTime * float64(time.Second))
	stats.LastEvaluationTime = time.Now()

	if success {
		stats.SuccessfulEvaluations++
	} else {
		stats.FailedEvaluations++
	}

	if stats.TotalEvaluations > 0 {
		stats.AverageEvaluationTime = stats.TotalEvaluationTime / time.Duration(stats.TotalEvaluations)
	}
}

func (cle *ConditionalLogicEngine) initializeDefaultEvaluators() {
	cle.evaluators[LogicTypeThreshold] = &ThresholdEvaluator{}
	cle.evaluators[LogicTypeTimeBased] = &TimeBasedEvaluator{}
	cle.evaluators[LogicTypeSpatial] = &SpatialEvaluator{}
	cle.evaluators[LogicTypeRelational] = &RelationalEvaluator{}
	cle.evaluators[LogicTypeComplex] = &ComplexEvaluator{}
}

// ThresholdEvaluator evaluates threshold conditions
type ThresholdEvaluator struct{}

func (te *ThresholdEvaluator) Evaluate(ctx context.Context, condition *Condition, context map[string]interface{}) (bool, error) {
	if len(condition.Operands) < 2 {
		return false, fmt.Errorf("threshold condition requires at least 2 operands")
	}

	// Get field path and expected value
	fieldPath, ok := condition.Operands[0].(string)
	if !ok {
		return false, fmt.Errorf("first operand must be a field path string")
	}

	expectedValue := condition.Operands[1]
	operator, ok := condition.Operator.(ComparisonOperator)
	if !ok {
		return false, fmt.Errorf("invalid comparison operator")
	}

	// Get actual value from context
	actualValue := getNestedValue(context, fieldPath)

	// Apply comparison
	return applyComparison(actualValue, operator, expectedValue), nil
}

// TimeBasedEvaluator evaluates time-based conditions
type TimeBasedEvaluator struct{}

func (tbe *TimeBasedEvaluator) Evaluate(ctx context.Context, condition *Condition, context map[string]interface{}) (bool, error) {
	now := time.Now()

	// Check if current time matches the time condition
	if timeValue, ok := condition.Parameters["time"]; ok {
		if targetTime, ok := timeValue.(string); ok {
			if parsedTime, err := time.Parse(time.RFC3339, targetTime); err == nil {
				return now.After(parsedTime), nil
			}
		}
	}

	// Check time range
	if startTime, ok := condition.Parameters["start_time"]; ok {
		if endTime, ok := condition.Parameters["end_time"]; ok {
			if start, ok := startTime.(string); ok {
				if end, ok := endTime.(string); ok {
					if startParsed, err := time.Parse(time.RFC3339, start); err == nil {
						if endParsed, err := time.Parse(time.RFC3339, end); err == nil {
							return now.After(startParsed) && now.Before(endParsed), nil
						}
					}
				}
			}
		}
	}

	return false, nil
}

// SpatialEvaluator evaluates spatial conditions
type SpatialEvaluator struct{}

func (se *SpatialEvaluator) Evaluate(ctx context.Context, condition *Condition, context map[string]interface{}) (bool, error) {
	// Get location from context
	location, ok := context["location"].(map[string]interface{})
	if !ok {
		return false, fmt.Errorf("location not found in context")
	}

	// Get target location from parameters
	targetLocation, ok := condition.Parameters["target_location"].(map[string]interface{})
	if !ok {
		return false, fmt.Errorf("target location not found in parameters")
	}

	// Calculate distance
	distance := calculateDistance(location, targetLocation)

	// Check if within threshold
	if threshold, ok := condition.Parameters["threshold"].(float64); ok {
		return distance <= threshold, nil
	}

	return false, nil
}

// RelationalEvaluator evaluates relational conditions
type RelationalEvaluator struct{}

func (re *RelationalEvaluator) Evaluate(ctx context.Context, condition *Condition, context map[string]interface{}) (bool, error) {
	// Get relationship data from context
	relationship, ok := context["relationship"].(map[string]interface{})
	if !ok {
		return false, fmt.Errorf("relationship not found in context")
	}

	// Check relationship type
	if expectedType, ok := condition.Parameters["type"].(string); ok {
		if actualType, ok := relationship["type"].(string); ok {
			return actualType == expectedType, nil
		}
	}

	return false, nil
}

// ComplexEvaluator evaluates complex conditions
type ComplexEvaluator struct{}

func (ce *ComplexEvaluator) Evaluate(ctx context.Context, condition *Condition, context map[string]interface{}) (bool, error) {
	// Complex conditions are handled by the main engine
	// This is a placeholder for complex condition evaluation
	return true, nil
}

// Helper functions

func getNestedValue(data map[string]interface{}, fieldPath string) interface{} {
	parts := strings.Split(fieldPath, ".")
	current := data

	for _, part := range parts {
		if val, ok := current[part]; ok {
			if mapVal, ok := val.(map[string]interface{}); ok {
				current = mapVal
			} else {
				return val
			}
		} else {
			return nil
		}
	}

	return current
}

func applyComparison(actual interface{}, operator ComparisonOperator, expected interface{}) bool {
	switch operator {
	case ComparisonOperatorEqual:
		return reflect.DeepEqual(actual, expected)
	case ComparisonOperatorNotEqual:
		return !reflect.DeepEqual(actual, expected)
	case ComparisonOperatorGreaterThan:
		return compareValues(actual, expected) > 0
	case ComparisonOperatorGreaterEqual:
		return compareValues(actual, expected) >= 0
	case ComparisonOperatorLessThan:
		return compareValues(actual, expected) < 0
	case ComparisonOperatorLessEqual:
		return compareValues(actual, expected) <= 0
	case ComparisonOperatorBetween:
		return isBetween(actual, expected)
	case ComparisonOperatorIn:
		return isIn(actual, expected)
	case ComparisonOperatorNotIn:
		return !isIn(actual, expected)
	default:
		return false
	}
}

func compareValues(a, b interface{}) int {
	// Convert to float64 for numeric comparison
	aFloat := toFloat64(a)
	bFloat := toFloat64(b)

	if aFloat < bFloat {
		return -1
	} else if aFloat > bFloat {
		return 1
	}
	return 0
}

func toFloat64(v interface{}) float64 {
	switch val := v.(type) {
	case float64:
		return val
	case float32:
		return float64(val)
	case int:
		return float64(val)
	case int64:
		return float64(val)
	case string:
		if f, err := strconv.ParseFloat(val, 64); err == nil {
			return f
		}
	}
	return 0
}

func isBetween(value, rangeVal interface{}) bool {
	if rangeSlice, ok := rangeVal.([]interface{}); ok && len(rangeSlice) == 2 {
		val := toFloat64(value)
		min := toFloat64(rangeSlice[0])
		max := toFloat64(rangeSlice[1])
		return val >= min && val <= max
	}
	return false
}

func isIn(value, list interface{}) bool {
	if listSlice, ok := list.([]interface{}); ok {
		for _, item := range listSlice {
			if reflect.DeepEqual(value, item) {
				return true
			}
		}
	}
	return false
}

func calculateDistance(loc1, loc2 map[string]interface{}) float64 {
	lat1 := toFloat64(loc1["latitude"])
	lon1 := toFloat64(loc1["longitude"])
	lat2 := toFloat64(loc2["latitude"])
	lon2 := toFloat64(loc2["longitude"])

	// Haversine formula for distance calculation
	const R = 6371 // Earth's radius in kilometers

	lat1Rad := lat1 * math.Pi / 180
	lat2Rad := lat2 * math.Pi / 180
	deltaLat := (lat2 - lat1) * math.Pi / 180
	deltaLon := (lon2 - lon1) * math.Pi / 180

	a := math.Sin(deltaLat/2)*math.Sin(deltaLat/2) +
		math.Cos(lat1Rad)*math.Cos(lat2Rad)*
			math.Sin(deltaLon/2)*math.Sin(deltaLon/2)
	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))

	return R * c
}
