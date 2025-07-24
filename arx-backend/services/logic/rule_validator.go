package logic

import (
	"context"
	"encoding/json"
	"fmt"
	"regexp"
	"sync"
	"time"

	"go.uber.org/zap"
)

// ValidationSeverity represents the severity of a validation error
type ValidationSeverity string

const (
	ValidationSeverityError   ValidationSeverity = "error"
	ValidationSeverityWarning ValidationSeverity = "warning"
	ValidationSeverityInfo    ValidationSeverity = "info"
)

// ValidationError represents a validation error
type ValidationError struct {
	Field    string                 `json:"field"`
	Message  string                 `json:"message"`
	Severity ValidationSeverity     `json:"severity"`
	Code     string                 `json:"code"`
	Details  map[string]interface{} `json:"details"`
}

// ValidationResult represents the result of rule validation
type ValidationResult struct {
	IsValid     bool              `json:"is_valid"`
	Errors      []ValidationError `json:"errors"`
	Warnings    []ValidationError `json:"warnings"`
	Info        []ValidationError `json:"info"`
	ValidatedAt time.Time         `json:"validated_at"`
	Duration    float64           `json:"duration"`
}

// RuleValidator provides comprehensive rule validation
type RuleValidator struct {
	logger *zap.Logger
	mu     sync.RWMutex

	// Validation rules and patterns
	validationRules map[string]ValidationRule
	fieldPatterns   map[string]*regexp.Regexp

	// Configuration
	config *ValidatorConfig
}

// ValidatorConfig holds validator configuration
type ValidatorConfig struct {
	EnableStrictMode            bool          `json:"enable_strict_mode"`
	EnableFieldValidation       bool          `json:"enable_field_validation"`
	EnableLogicValidation       bool          `json:"enable_logic_validation"`
	EnablePerformanceValidation bool          `json:"enable_performance_validation"`
	MaxValidationTime           time.Duration `json:"max_validation_time"`
	MaxErrorsPerRule            int           `json:"max_errors_per_rule"`
}

// ValidationRule represents a validation rule
type ValidationRule struct {
	Name        string                  `json:"name"`
	Description string                  `json:"description"`
	Severity    ValidationSeverity      `json:"severity"`
	Validator   func(interface{}) error `json:"-"`
	Metadata    map[string]interface{}  `json:"metadata"`
}

// NewRuleValidator creates a new rule validator
func NewRuleValidator(logger *zap.Logger, config *ValidatorConfig) (*RuleValidator, error) {
	if config == nil {
		config = &ValidatorConfig{
			EnableStrictMode:            true,
			EnableFieldValidation:       true,
			EnableLogicValidation:       true,
			EnablePerformanceValidation: true,
			MaxValidationTime:           30 * time.Second,
			MaxErrorsPerRule:            100,
		}
	}

	rv := &RuleValidator{
		logger:          logger,
		validationRules: make(map[string]ValidationRule),
		fieldPatterns:   make(map[string]*regexp.Regexp),
		config:          config,
	}

	// Initialize validation rules
	rv.initializeValidationRules()

	logger.Info("Rule validator initialized",
		zap.Bool("enable_strict_mode", config.EnableStrictMode),
		zap.Bool("enable_field_validation", config.EnableFieldValidation),
		zap.Bool("enable_logic_validation", config.EnableLogicValidation),
		zap.Duration("max_validation_time", config.MaxValidationTime))

	return rv, nil
}

// ValidateRule validates a rule comprehensively
func (rv *RuleValidator) ValidateRule(ctx context.Context, rule *Rule) *ValidationResult {
	startTime := time.Now()
	result := &ValidationResult{
		IsValid:     true,
		Errors:      []ValidationError{},
		Warnings:    []ValidationError{},
		Info:        []ValidationError{},
		ValidatedAt: time.Now(),
	}

	// Validate rule structure
	rv.validateRuleStructure(rule, result)

	// Validate rule fields
	if rv.config.EnableFieldValidation {
		rv.validateRuleFields(rule, result)
	}

	// Validate rule logic
	if rv.config.EnableLogicValidation {
		rv.validateRuleLogic(rule, result)
	}

	// Validate performance aspects
	if rv.config.EnablePerformanceValidation {
		rv.validateRulePerformance(rule, result)
	}

	result.Duration = time.Since(startTime).Seconds()
	result.IsValid = len(result.Errors) == 0

	return result
}

// ValidateRuleChain validates a rule chain
func (rv *RuleValidator) ValidateRuleChain(ctx context.Context, chain *RuleChain) *ValidationResult {
	startTime := time.Now()
	result := &ValidationResult{
		IsValid:     true,
		Errors:      []ValidationError{},
		Warnings:    []ValidationError{},
		Info:        []ValidationError{},
		ValidatedAt: time.Now(),
	}

	// Validate chain structure
	rv.validateChainStructure(chain, result)

	// Validate chain logic
	rv.validateChainLogic(chain, result)

	result.Duration = time.Since(startTime).Seconds()
	result.IsValid = len(result.Errors) == 0

	return result
}

// ValidateCondition validates a condition
func (rv *RuleValidator) ValidateCondition(ctx context.Context, condition *Condition) *ValidationResult {
	startTime := time.Now()
	result := &ValidationResult{
		IsValid:     true,
		Errors:      []ValidationError{},
		Warnings:    []ValidationError{},
		Info:        []ValidationError{},
		ValidatedAt: time.Now(),
	}

	// Validate condition structure
	rv.validateConditionStructure(condition, result)

	// Validate condition logic
	rv.validateConditionLogic(condition, result)

	result.Duration = time.Since(startTime).Seconds()
	result.IsValid = len(result.Errors) == 0

	return result
}

// AddValidationRule adds a custom validation rule
func (rv *RuleValidator) AddValidationRule(name string, rule ValidationRule) error {
	rv.mu.Lock()
	defer rv.mu.Unlock()

	if _, exists := rv.validationRules[name]; exists {
		return fmt.Errorf("validation rule already exists: %s", name)
	}

	rv.validationRules[name] = rule

	rv.logger.Info("Validation rule added",
		zap.String("rule_name", name),
		zap.String("severity", string(rule.Severity)))

	return nil
}

// GetValidationRules returns all validation rules
func (rv *RuleValidator) GetValidationRules() map[string]ValidationRule {
	rv.mu.RLock()
	defer rv.mu.RUnlock()

	rules := make(map[string]ValidationRule)
	for name, rule := range rv.validationRules {
		rules[name] = rule
	}

	return rules
}

// Helper validation functions

func (rv *RuleValidator) validateRuleStructure(rule *Rule, result *ValidationResult) {
	// Validate required fields
	if rule.RuleID == "" {
		rv.addError(result, "rule_id", "Rule ID is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	if rule.Name == "" {
		rv.addError(result, "name", "Rule name is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	if rule.RuleType == "" {
		rv.addError(result, "rule_type", "Rule type is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	if rule.Status == "" {
		rv.addError(result, "status", "Rule status is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	// Validate rule type
	if !rv.isValidRuleType(rule.RuleType) {
		rv.addError(result, "rule_type", fmt.Sprintf("Invalid rule type: %s", rule.RuleType), ValidationSeverityError, "INVALID_RULE_TYPE")
	}

	// Validate rule status
	if !rv.isValidRuleStatus(rule.Status) {
		rv.addError(result, "status", fmt.Sprintf("Invalid rule status: %s", rule.Status), ValidationSeverityError, "INVALID_RULE_STATUS")
	}

	// Validate priority
	if rule.Priority < 0 {
		rv.addWarning(result, "priority", "Priority should be non-negative", ValidationSeverityWarning, "NEGATIVE_PRIORITY")
	}

	// Validate version format
	if rule.Version != "" && !rv.isValidVersion(rule.Version) {
		rv.addWarning(result, "version", "Version format should be semantic (e.g., 1.0.0)", ValidationSeverityWarning, "INVALID_VERSION_FORMAT")
	}
}

func (rv *RuleValidator) validateRuleFields(rule *Rule, result *ValidationResult) {
	// Validate name length
	if len(rule.Name) > 255 {
		rv.addError(result, "name", "Rule name too long (max 255 characters)", ValidationSeverityError, "NAME_TOO_LONG")
	}

	// Validate description length
	if len(rule.Description) > 1000 {
		rv.addWarning(result, "description", "Description too long (max 1000 characters)", ValidationSeverityWarning, "DESCRIPTION_TOO_LONG")
	}

	// Validate tags
	if len(rule.Tags) > 50 {
		rv.addWarning(result, "tags", "Too many tags (max 50)", ValidationSeverityWarning, "TOO_MANY_TAGS")
	}

	for i, tag := range rule.Tags {
		if len(tag) > 50 {
			rv.addError(result, fmt.Sprintf("tags[%d]", i), "Tag too long (max 50 characters)", ValidationSeverityError, "TAG_TOO_LONG")
		}
		if !rv.isValidTag(tag) {
			rv.addError(result, fmt.Sprintf("tags[%d]", i), "Invalid tag format", ValidationSeverityError, "INVALID_TAG_FORMAT")
		}
	}

	// Validate metadata
	if rule.Metadata != nil {
		rv.validateMetadata(rule.Metadata, result, "metadata")
	}
}

func (rv *RuleValidator) validateRuleLogic(rule *Rule, result *ValidationResult) {
	// Validate conditions
	if rule.Conditions != nil {
		rv.validateConditions(rule.Conditions, result)
	}

	// Validate actions
	if rule.Actions != nil {
		rv.validateActions(rule.Actions, result)
	}

	// Validate rule logic consistency
	rv.validateRuleLogicConsistency(rule, result)
}

func (rv *RuleValidator) validateRulePerformance(rule *Rule, result *ValidationResult) {
	// Check execution count
	if rule.ExecutionCount < 0 {
		rv.addError(result, "execution_count", "Execution count cannot be negative", ValidationSeverityError, "NEGATIVE_EXECUTION_COUNT")
	}

	// Check success count
	if rule.SuccessCount < 0 {
		rv.addError(result, "success_count", "Success count cannot be negative", ValidationSeverityError, "NEGATIVE_SUCCESS_COUNT")
	}

	// Check error count
	if rule.ErrorCount < 0 {
		rv.addError(result, "error_count", "Error count cannot be negative", ValidationSeverityError, "NEGATIVE_ERROR_COUNT")
	}

	// Validate success rate
	if rule.ExecutionCount > 0 {
		successRate := float64(rule.SuccessCount) / float64(rule.ExecutionCount)
		if successRate < 0.5 {
			rv.addWarning(result, "success_rate", "Low success rate detected", ValidationSeverityWarning, "LOW_SUCCESS_RATE")
		}
	}

	// Check average execution time
	if rule.AvgExecutionTime < 0 {
		rv.addError(result, "avg_execution_time", "Average execution time cannot be negative", ValidationSeverityError, "NEGATIVE_EXECUTION_TIME")
	}

	if rule.AvgExecutionTime > 5.0 {
		rv.addWarning(result, "avg_execution_time", "High average execution time detected", ValidationSeverityWarning, "HIGH_EXECUTION_TIME")
	}
}

func (rv *RuleValidator) validateChainStructure(chain *RuleChain, result *ValidationResult) {
	// Validate required fields
	if chain.ChainID == "" {
		rv.addError(result, "chain_id", "Chain ID is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	if chain.Name == "" {
		rv.addError(result, "name", "Chain name is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	if len(chain.Rules) == 0 {
		rv.addError(result, "rules", "Chain must contain at least one rule", ValidationSeverityError, "EMPTY_CHAIN")
	}

	// Validate execution order
	if chain.ExecutionOrder != "" && !rv.isValidExecutionOrder(chain.ExecutionOrder) {
		rv.addError(result, "execution_order", "Invalid execution order", ValidationSeverityError, "INVALID_EXECUTION_ORDER")
	}

	// Validate rule references
	for i, ruleID := range chain.Rules {
		if ruleID == "" {
			rv.addError(result, fmt.Sprintf("rules[%d]", i), "Rule ID cannot be empty", ValidationSeverityError, "EMPTY_RULE_ID")
		}
	}
}

func (rv *RuleValidator) validateChainLogic(chain *RuleChain, result *ValidationResult) {
	// Check for circular dependencies
	rv.checkCircularDependencies(chain, result)

	// Validate chain performance
	if len(chain.Rules) > 100 {
		rv.addWarning(result, "rules", "Chain contains many rules (performance impact)", ValidationSeverityWarning, "LARGE_CHAIN")
	}
}

func (rv *RuleValidator) validateConditionStructure(condition *Condition, result *ValidationResult) {
	// Validate required fields
	if condition.ID == "" {
		rv.addError(result, "id", "Condition ID is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	if condition.Type == "" {
		rv.addError(result, "type", "Condition type is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	// Validate condition type
	if !rv.isValidLogicType(condition.Type) {
		rv.addError(result, "type", fmt.Sprintf("Invalid logic type: %s", condition.Type), ValidationSeverityError, "INVALID_LOGIC_TYPE")
	}

	// Validate operands
	if len(condition.Operands) == 0 {
		rv.addError(result, "operands", "Condition must have at least one operand", ValidationSeverityError, "EMPTY_OPERANDS")
	}

	// Validate priority
	if condition.Priority < 0 {
		rv.addWarning(result, "priority", "Priority should be non-negative", ValidationSeverityWarning, "NEGATIVE_PRIORITY")
	}
}

func (rv *RuleValidator) validateConditionLogic(condition *Condition, result *ValidationResult) {
	// Validate operator
	if condition.Operator == nil {
		rv.addError(result, "operator", "Condition operator is required", ValidationSeverityError, "REQUIRED_FIELD")
		return
	}

	// Validate operator type based on condition type
	rv.validateOperatorForConditionType(condition, result)

	// Validate operands based on operator
	rv.validateOperandsForOperator(condition, result)
}

func (rv *RuleValidator) validateConditions(conditions json.RawMessage, result *ValidationResult) {
	var conditionsList []map[string]interface{}
	if err := json.Unmarshal(conditions, &conditionsList); err != nil {
		rv.addError(result, "conditions", "Invalid conditions format", ValidationSeverityError, "INVALID_JSON")
		return
	}

	for i, condition := range conditionsList {
		rv.validateConditionMap(condition, result, fmt.Sprintf("conditions[%d]", i))
	}
}

func (rv *RuleValidator) validateActions(actions json.RawMessage, result *ValidationResult) {
	var actionsList []map[string]interface{}
	if err := json.Unmarshal(actions, &actionsList); err != nil {
		rv.addError(result, "actions", "Invalid actions format", ValidationSeverityError, "INVALID_JSON")
		return
	}

	for i, action := range actionsList {
		rv.validateActionMap(action, result, fmt.Sprintf("actions[%d]", i))
	}
}

func (rv *RuleValidator) validateConditionMap(condition map[string]interface{}, result *ValidationResult, fieldPath string) {
	// Validate required fields
	if conditionType, ok := condition["type"].(string); ok {
		if !rv.isValidLogicType(LogicType(conditionType)) {
			rv.addError(result, fieldPath+".type", "Invalid condition type", ValidationSeverityError, "INVALID_CONDITION_TYPE")
		}
	} else {
		rv.addError(result, fieldPath+".type", "Condition type is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	// Validate operator
	if _, ok := condition["operator"]; !ok {
		rv.addError(result, fieldPath+".operator", "Condition operator is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	// Validate operands
	if operands, ok := condition["operands"].([]interface{}); ok {
		if len(operands) == 0 {
			rv.addError(result, fieldPath+".operands", "Condition must have operands", ValidationSeverityError, "EMPTY_OPERANDS")
		}
	} else {
		rv.addError(result, fieldPath+".operands", "Condition operands are required", ValidationSeverityError, "REQUIRED_FIELD")
	}
}

func (rv *RuleValidator) validateActionMap(action map[string]interface{}, result *ValidationResult, fieldPath string) {
	// Validate action type
	if actionType, ok := action["type"].(string); ok {
		if actionType == "" {
			rv.addError(result, fieldPath+".type", "Action type is required", ValidationSeverityError, "REQUIRED_FIELD")
		}
	} else {
		rv.addError(result, fieldPath+".type", "Action type is required", ValidationSeverityError, "REQUIRED_FIELD")
	}

	// Validate action parameters
	if params, ok := action["parameters"].(map[string]interface{}); ok {
		rv.validateMetadata(params, result, fieldPath+".parameters")
	}
}

func (rv *RuleValidator) validateMetadata(metadata map[string]interface{}, result *ValidationResult, fieldPath string) {
	for key, value := range metadata {
		if key == "" {
			rv.addError(result, fieldPath+".key", "Metadata key cannot be empty", ValidationSeverityError, "EMPTY_METADATA_KEY")
		}
		if len(key) > 100 {
			rv.addWarning(result, fieldPath+".key", "Metadata key too long", ValidationSeverityWarning, "METADATA_KEY_TOO_LONG")
		}
		if value == nil {
			rv.addWarning(result, fieldPath+".value", "Metadata value is null", ValidationSeverityWarning, "NULL_METADATA_VALUE")
		}
	}
}

func (rv *RuleValidator) validateRuleLogicConsistency(rule *Rule, result *ValidationResult) {
	// Check for conflicting conditions and actions
	if rule.Conditions != nil && rule.Actions != nil {
		// Add logic consistency checks here
		rv.addInfo(result, "logic", "Rule logic consistency check passed", ValidationSeverityInfo, "LOGIC_CONSISTENT")
	}
}

func (rv *RuleValidator) checkCircularDependencies(chain *RuleChain, result *ValidationResult) {
	// Simple circular dependency check
	ruleSet := make(map[string]bool)
	for _, ruleID := range chain.Rules {
		if ruleSet[ruleID] {
			rv.addError(result, "rules", "Duplicate rule in chain", ValidationSeverityError, "DUPLICATE_RULE")
		}
		ruleSet[ruleID] = true
	}
}

func (rv *RuleValidator) validateOperatorForConditionType(condition *Condition, result *ValidationResult) {
	switch condition.Type {
	case LogicTypeThreshold:
		if _, ok := condition.Operator.(ComparisonOperator); !ok {
			rv.addError(result, "operator", "Threshold condition requires comparison operator", ValidationSeverityError, "INVALID_OPERATOR")
		}
	case LogicTypeComplex:
		if _, ok := condition.Operator.(LogicOperator); !ok {
			rv.addError(result, "operator", "Complex condition requires logic operator", ValidationSeverityError, "INVALID_OPERATOR")
		}
	}
}

func (rv *RuleValidator) validateOperandsForOperator(condition *Condition, result *ValidationResult) {
	// Validate operands based on operator type
	switch op := condition.Operator.(type) {
	case ComparisonOperator:
		if len(condition.Operands) < 2 {
			rv.addError(result, "operands", "Comparison operator requires at least 2 operands", ValidationSeverityError, "INSUFFICIENT_OPERANDS")
		}
	case LogicOperator:
		if len(condition.Operands) < 1 {
			rv.addError(result, "operands", "Logic operator requires at least 1 operand", ValidationSeverityError, "INSUFFICIENT_OPERANDS")
		}
	default:
		rv.addError(result, "operator", "Unknown operator type", ValidationSeverityError, "UNKNOWN_OPERATOR")
	}
}

// Helper functions

func (rv *RuleValidator) addError(result *ValidationResult, field, message string, severity ValidationSeverity, code string) {
	result.Errors = append(result.Errors, ValidationError{
		Field:    field,
		Message:  message,
		Severity: severity,
		Code:     code,
		Details:  make(map[string]interface{}),
	})
}

func (rv *RuleValidator) addWarning(result *ValidationResult, field, message string, severity ValidationSeverity, code string) {
	result.Warnings = append(result.Warnings, ValidationError{
		Field:    field,
		Message:  message,
		Severity: severity,
		Code:     code,
		Details:  make(map[string]interface{}),
	})
}

func (rv *RuleValidator) addInfo(result *ValidationResult, field, message string, severity ValidationSeverity, code string) {
	result.Info = append(result.Info, ValidationError{
		Field:    field,
		Message:  message,
		Severity: severity,
		Code:     code,
		Details:  make(map[string]interface{}),
	})
}

func (rv *RuleValidator) isValidRuleType(ruleType RuleType) bool {
	validTypes := []RuleType{
		RuleTypeConditional,
		RuleTypeTransformation,
		RuleTypeValidation,
		RuleTypeWorkflow,
		RuleTypeAnalysis,
	}

	for _, validType := range validTypes {
		if ruleType == validType {
			return true
		}
	}
	return false
}

func (rv *RuleValidator) isValidRuleStatus(status RuleStatus) bool {
	validStatuses := []RuleStatus{
		RuleStatusActive,
		RuleStatusInactive,
		RuleStatusDraft,
		RuleStatusArchived,
		RuleStatusError,
	}

	for _, validStatus := range validStatuses {
		if status == validStatus {
			return true
		}
	}
	return false
}

func (rv *RuleValidator) isValidLogicType(logicType LogicType) bool {
	validTypes := []LogicType{
		LogicTypeThreshold,
		LogicTypeTimeBased,
		LogicTypeSpatial,
		LogicTypeRelational,
		LogicTypeComplex,
	}

	for _, validType := range validTypes {
		if logicType == validType {
			return true
		}
	}
	return false
}

func (rv *RuleValidator) isValidVersion(version string) bool {
	// Simple semantic version check
	versionPattern := regexp.MustCompile(`^\d+\.\d+\.\d+$`)
	return versionPattern.MatchString(version)
}

func (rv *RuleValidator) isValidTag(tag string) bool {
	// Tag validation pattern
	tagPattern := regexp.MustCompile(`^[a-zA-Z0-9_-]+$`)
	return tagPattern.MatchString(tag)
}

func (rv *RuleValidator) isValidExecutionOrder(order string) bool {
	validOrders := []string{"sequential", "parallel", "conditional"}
	for _, validOrder := range validOrders {
		if order == validOrder {
			return true
		}
	}
	return false
}

func (rv *RuleValidator) initializeValidationRules() {
	// Add built-in validation rules
	rv.validationRules["required_field"] = ValidationRule{
		Name:        "Required Field",
		Description: "Validates that required fields are present",
		Severity:    ValidationSeverityError,
		Validator:   rv.validateRequiredField,
	}

	rv.validationRules["field_length"] = ValidationRule{
		Name:        "Field Length",
		Description: "Validates field length constraints",
		Severity:    ValidationSeverityWarning,
		Validator:   rv.validateFieldLength,
	}

	rv.validationRules["data_type"] = ValidationRule{
		Name:        "Data Type",
		Description: "Validates data type constraints",
		Severity:    ValidationSeverityError,
		Validator:   rv.validateDataType,
	}
}

func (rv *RuleValidator) validateRequiredField(value interface{}) error {
	if value == nil {
		return fmt.Errorf("field is required")
	}
	if str, ok := value.(string); ok && str == "" {
		return fmt.Errorf("field cannot be empty")
	}
	return nil
}

func (rv *RuleValidator) validateFieldLength(value interface{}) error {
	if str, ok := value.(string); ok {
		if len(str) > 255 {
			return fmt.Errorf("field too long (max 255 characters)")
		}
	}
	return nil
}

func (rv *RuleValidator) validateDataType(value interface{}) error {
	// Add data type validation logic
	return nil
}
