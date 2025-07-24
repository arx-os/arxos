package logic

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// RuleType represents the type of rule
type RuleType string

const (
	RuleTypeConditional    RuleType = "conditional"
	RuleTypeTransformation RuleType = "transformation"
	RuleTypeValidation     RuleType = "validation"
	RuleTypeWorkflow       RuleType = "workflow"
	RuleTypeAnalysis       RuleType = "analysis"
)

// RuleStatus represents the status of a rule
type RuleStatus string

const (
	RuleStatusActive   RuleStatus = "active"
	RuleStatusInactive RuleStatus = "inactive"
	RuleStatusDraft    RuleStatus = "draft"
	RuleStatusArchived RuleStatus = "archived"
	RuleStatusError    RuleStatus = "error"
)

// ExecutionStatus represents the status of rule execution
type ExecutionStatus string

const (
	ExecutionStatusSuccess ExecutionStatus = "success"
	ExecutionStatusFailed  ExecutionStatus = "failed"
	ExecutionStatusPartial ExecutionStatus = "partial"
	ExecutionStatusTimeout ExecutionStatus = "timeout"
	ExecutionStatusError   ExecutionStatus = "error"
)

// DataType represents the data type for rule evaluation
type DataType string

const (
	DataTypeString  DataType = "string"
	DataTypeNumber  DataType = "number"
	DataTypeBoolean DataType = "boolean"
	DataTypeArray   DataType = "array"
	DataTypeObject  DataType = "object"
	DataTypeNull    DataType = "null"
)

// Rule represents a logic rule
type Rule struct {
	RuleID           string                 `json:"rule_id" db:"rule_id"`
	Name             string                 `json:"name" db:"name"`
	Description      string                 `json:"description" db:"description"`
	RuleType         RuleType               `json:"rule_type" db:"rule_type"`
	Status           RuleStatus             `json:"status" db:"status"`
	Conditions       json.RawMessage        `json:"conditions" db:"conditions"`
	Actions          json.RawMessage        `json:"actions" db:"actions"`
	Priority         int                    `json:"priority" db:"priority"`
	Version          string                 `json:"version" db:"version"`
	CreatedAt        time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time              `json:"updated_at" db:"updated_at"`
	Metadata         map[string]interface{} `json:"metadata" db:"metadata"`
	Tags             []string               `json:"tags" db:"tags"`
	ExecutionCount   int                    `json:"execution_count" db:"execution_count"`
	SuccessCount     int                    `json:"success_count" db:"success_count"`
	ErrorCount       int                    `json:"error_count" db:"error_count"`
	AvgExecutionTime float64                `json:"avg_execution_time" db:"avg_execution_time"`
}

// RuleExecution represents a rule execution result
type RuleExecution struct {
	ExecutionID   string                 `json:"execution_id" db:"execution_id"`
	RuleID        string                 `json:"rule_id" db:"rule_id"`
	InputData     json.RawMessage        `json:"input_data" db:"input_data"`
	OutputData    json.RawMessage        `json:"output_data" db:"output_data"`
	Status        ExecutionStatus        `json:"status" db:"status"`
	ExecutionTime float64                `json:"execution_time" db:"execution_time"`
	ErrorMessage  *string                `json:"error_message" db:"error_message"`
	Timestamp     time.Time              `json:"timestamp" db:"timestamp"`
	Metadata      map[string]interface{} `json:"metadata" db:"metadata"`
}

// RuleChain represents a chain of rules
type RuleChain struct {
	ChainID        string                 `json:"chain_id" db:"chain_id"`
	Name           string                 `json:"name" db:"name"`
	Description    string                 `json:"description" db:"description"`
	Rules          []string               `json:"rules" db:"rules"`
	ExecutionOrder string                 `json:"execution_order" db:"execution_order"`
	Status         RuleStatus             `json:"status" db:"status"`
	CreatedAt      time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt      time.Time              `json:"updated_at" db:"updated_at"`
	Metadata       map[string]interface{} `json:"metadata" db:"metadata"`
}

// DataContext represents data context for rule evaluation
type DataContext struct {
	Data      map[string]interface{}                     `json:"data"`
	Variables map[string]interface{}                     `json:"variables"`
	Functions map[string]func([]interface{}) interface{} `json:"-"`
	Metadata  map[string]interface{}                     `json:"metadata"`
}

// RuleEngine provides comprehensive rule-based logic processing
type RuleEngine struct {
	dbService *DatabaseService
	logger    *zap.Logger
	mu        sync.RWMutex

	// Rule management
	rules  map[string]*Rule
	chains map[string]*RuleChain

	// Performance tracking
	executionStats   map[string]*ExecutionStats
	builtinFunctions map[string]func([]interface{}) interface{}

	// Configuration
	config *RuleEngineConfig
}

// RuleEngineConfig holds rule engine configuration
type RuleEngineConfig struct {
	MaxExecutionTime          time.Duration `json:"max_execution_time"`
	MaxConcurrentRules        int           `json:"max_concurrent_rules"`
	EnableCaching             bool          `json:"enable_caching"`
	EnablePerformanceTracking bool          `json:"enable_performance_tracking"`
	DefaultTimeout            time.Duration `json:"default_timeout"`
}

// ExecutionStats holds execution statistics
type ExecutionStats struct {
	TotalExecutions      int64         `json:"total_executions"`
	SuccessfulExecutions int64         `json:"successful_executions"`
	FailedExecutions     int64         `json:"failed_executions"`
	TotalExecutionTime   time.Duration `json:"total_execution_time"`
	AverageExecutionTime time.Duration `json:"average_execution_time"`
	LastExecutionTime    time.Time     `json:"last_execution_time"`
}

// NewRuleEngine creates a new rule engine
func NewRuleEngine(dbService *DatabaseService, logger *zap.Logger, config *RuleEngineConfig) (*RuleEngine, error) {
	if config == nil {
		config = &RuleEngineConfig{
			MaxExecutionTime:          30 * time.Second,
			MaxConcurrentRules:        100,
			EnableCaching:             true,
			EnablePerformanceTracking: true,
			DefaultTimeout:            5 * time.Second,
		}
	}

	re := &RuleEngine{
		dbService:        dbService,
		logger:           logger,
		rules:            make(map[string]*Rule),
		chains:           make(map[string]*RuleChain),
		executionStats:   make(map[string]*ExecutionStats),
		builtinFunctions: make(map[string]func([]interface{}) interface{}),
		config:           config,
	}

	// Initialize builtin functions
	re.initializeBuiltinFunctions()

	// Load existing rules
	if err := re.loadRules(); err != nil {
		return nil, fmt.Errorf("failed to load rules: %w", err)
	}

	// Load existing rule chains
	if err := re.loadRuleChains(); err != nil {
		return nil, fmt.Errorf("failed to load rule chains: %w", err)
	}

	logger.Info("Rule engine initialized",
		zap.Int("rule_count", len(re.rules)),
		zap.Int("chain_count", len(re.chains)),
		zap.Duration("max_execution_time", config.MaxExecutionTime),
		zap.Int("max_concurrent_rules", config.MaxConcurrentRules))

	return re, nil
}

// CreateRule creates a new rule
func (re *RuleEngine) CreateRule(ctx context.Context, name, description string, ruleType RuleType,
	conditions, actions json.RawMessage, priority int, tags []string, metadata map[string]interface{}) (string, error) {

	ruleID := generateRuleID()
	now := time.Now()

	rule := &Rule{
		RuleID:      ruleID,
		Name:        name,
		Description: description,
		RuleType:    ruleType,
		Status:      RuleStatusDraft,
		Conditions:  conditions,
		Actions:     actions,
		Priority:    priority,
		Version:     "1.0",
		CreatedAt:   now,
		UpdatedAt:   now,
		Metadata:    metadata,
		Tags:        tags,
	}

	// Validate rule
	if err := re.validateRule(rule); err != nil {
		return "", fmt.Errorf("rule validation failed: %w", err)
	}

	// Save rule to database
	if err := re.saveRule(ctx, rule); err != nil {
		return "", fmt.Errorf("failed to save rule: %w", err)
	}

	// Add to memory cache
	re.mu.Lock()
	re.rules[ruleID] = rule
	re.mu.Unlock()

	re.logger.Info("Rule created",
		zap.String("rule_id", ruleID),
		zap.String("name", name),
		zap.String("type", string(ruleType)))

	return ruleID, nil
}

// GetRule retrieves a rule by ID
func (re *RuleEngine) GetRule(ctx context.Context, ruleID string) (*Rule, error) {
	re.mu.RLock()
	rule, exists := re.rules[ruleID]
	re.mu.RUnlock()

	if exists {
		return rule, nil
	}

	// Load from database
	rule, err := re.loadRuleFromDB(ctx, ruleID)
	if err != nil {
		return nil, fmt.Errorf("failed to load rule: %w", err)
	}

	if rule != nil {
		re.mu.Lock()
		re.rules[ruleID] = rule
		re.mu.Unlock()
	}

	return rule, nil
}

// ListRules lists rules with optional filtering
func (re *RuleEngine) ListRules(ctx context.Context, ruleType *RuleType, status *RuleStatus, tags []string) ([]*Rule, error) {
	re.mu.RLock()
	defer re.mu.RUnlock()

	var rules []*Rule
	for _, rule := range re.rules {
		if ruleType != nil && rule.RuleType != *ruleType {
			continue
		}
		if status != nil && rule.Status != *status {
			continue
		}
		if len(tags) > 0 && !containsAllTags(rule.Tags, tags) {
			continue
		}
		rules = append(rules, rule)
	}

	return rules, nil
}

// UpdateRule updates an existing rule
func (re *RuleEngine) UpdateRule(ctx context.Context, ruleID string, updates map[string]interface{}) error {
	rule, err := re.GetRule(ctx, ruleID)
	if err != nil {
		return fmt.Errorf("failed to get rule: %w", err)
	}

	if rule == nil {
		return fmt.Errorf("rule not found: %s", ruleID)
	}

	// Apply updates
	if name, ok := updates["name"].(string); ok {
		rule.Name = name
	}
	if description, ok := updates["description"].(string); ok {
		rule.Description = description
	}
	if status, ok := updates["status"].(RuleStatus); ok {
		rule.Status = status
	}
	if conditions, ok := updates["conditions"].(json.RawMessage); ok {
		rule.Conditions = conditions
	}
	if actions, ok := updates["actions"].(json.RawMessage); ok {
		rule.Actions = actions
	}
	if priority, ok := updates["priority"].(int); ok {
		rule.Priority = priority
	}
	if tags, ok := updates["tags"].([]string); ok {
		rule.Tags = tags
	}
	if metadata, ok := updates["metadata"].(map[string]interface{}); ok {
		rule.Metadata = metadata
	}

	rule.UpdatedAt = time.Now()

	// Validate updated rule
	if err := re.validateRule(rule); err != nil {
		return fmt.Errorf("rule validation failed: %w", err)
	}

	// Save to database
	if err := re.saveRule(ctx, rule); err != nil {
		return fmt.Errorf("failed to save rule: %w", err)
	}

	// Update memory cache
	re.mu.Lock()
	re.rules[ruleID] = rule
	re.mu.Unlock()

	re.logger.Info("Rule updated",
		zap.String("rule_id", ruleID),
		zap.String("name", rule.Name))

	return nil
}

// DeleteRule deletes a rule
func (re *RuleEngine) DeleteRule(ctx context.Context, ruleID string) error {
	rule, err := re.GetRule(ctx, ruleID)
	if err != nil {
		return fmt.Errorf("failed to get rule: %w", err)
	}

	if rule == nil {
		return fmt.Errorf("rule not found: %s", ruleID)
	}

	// Delete from database
	if err := re.deleteRuleFromDB(ctx, ruleID); err != nil {
		return fmt.Errorf("failed to delete rule from database: %w", err)
	}

	// Remove from memory cache
	re.mu.Lock()
	delete(re.rules, ruleID)
	delete(re.executionStats, ruleID)
	re.mu.Unlock()

	re.logger.Info("Rule deleted",
		zap.String("rule_id", ruleID),
		zap.String("name", rule.Name))

	return nil
}

// ExecuteRule executes a rule with given data
func (re *RuleEngine) ExecuteRule(ctx context.Context, ruleID string, data map[string]interface{}, context *DataContext) (*RuleExecution, error) {
	rule, err := re.GetRule(ctx, ruleID)
	if err != nil {
		return nil, fmt.Errorf("failed to get rule: %w", err)
	}

	if rule == nil {
		return nil, fmt.Errorf("rule not found: %s", ruleID)
	}

	if rule.Status != RuleStatusActive {
		return nil, fmt.Errorf("rule is not active: %s", ruleID)
	}

	executionID := generateExecutionID()
	startTime := time.Now()

	// Create execution context
	if context == nil {
		context = &DataContext{
			Data:      data,
			Variables: make(map[string]interface{}),
			Functions: re.builtinFunctions,
			Metadata:  make(map[string]interface{}),
		}
	} else {
		context.Data = data
		if context.Functions == nil {
			context.Functions = re.builtinFunctions
		}
	}

	// Execute rule
	outputData, err := re.executeRuleLogic(rule, context)
	executionTime := time.Since(startTime).Seconds()

	// Create execution result
	execution := &RuleExecution{
		ExecutionID:   executionID,
		RuleID:        ruleID,
		InputData:     mustMarshalJSON(data),
		OutputData:    mustMarshalJSON(outputData),
		Status:        ExecutionStatusSuccess,
		ExecutionTime: executionTime,
		Timestamp:     time.Now(),
		Metadata:      make(map[string]interface{}),
	}

	if err != nil {
		execution.Status = ExecutionStatusFailed
		errorMsg := err.Error()
		execution.ErrorMessage = &errorMsg
	}

	// Save execution to database
	if err := re.saveExecution(ctx, execution); err != nil {
		re.logger.Error("Failed to save execution", zap.Error(err))
	}

	// Update rule statistics
	re.updateRuleStats(rule, executionTime, execution.Status == ExecutionStatusSuccess)

	re.logger.Info("Rule executed",
		zap.String("rule_id", ruleID),
		zap.String("execution_id", executionID),
		zap.String("status", string(execution.Status)),
		zap.Float64("execution_time", executionTime))

	return execution, err
}

// ExecuteRuleChain executes a chain of rules
func (re *RuleEngine) ExecuteRuleChain(ctx context.Context, chainID string, data map[string]interface{}, context *DataContext) ([]*RuleExecution, error) {
	chain, err := re.GetRuleChain(ctx, chainID)
	if err != nil {
		return nil, fmt.Errorf("failed to get rule chain: %w", err)
	}

	if chain == nil {
		return nil, fmt.Errorf("rule chain not found: %s", chainID)
	}

	if chain.Status != RuleStatusActive {
		return nil, fmt.Errorf("rule chain is not active: %s", chainID)
	}

	var executions []*RuleExecution
	currentData := data

	for _, ruleID := range chain.Rules {
		execution, err := re.ExecuteRule(ctx, ruleID, currentData, context)
		if err != nil {
			re.logger.Error("Rule execution failed in chain",
				zap.String("chain_id", chainID),
				zap.String("rule_id", ruleID),
				zap.Error(err))

			// Continue with next rule or stop based on chain configuration
			if chain.ExecutionOrder == "sequential" {
				break
			}
			continue
		}

		executions = append(executions, execution)

		// Update data for next rule in chain
		var outputData map[string]interface{}
		if err := json.Unmarshal(execution.OutputData, &outputData); err == nil {
			currentData = outputData
		}
	}

	return executions, nil
}

// GetPerformanceMetrics returns performance metrics
func (re *RuleEngine) GetPerformanceMetrics() map[string]interface{} {
	re.mu.RLock()
	defer re.mu.RUnlock()

	metrics := map[string]interface{}{
		"total_rules":            len(re.rules),
		"total_chains":           len(re.chains),
		"total_executions":       0,
		"successful_executions":  0,
		"failed_executions":      0,
		"average_execution_time": 0.0,
	}

	var totalExecutions, successfulExecutions, failedExecutions int64
	var totalExecutionTime time.Duration

	for _, stats := range re.executionStats {
		totalExecutions += stats.TotalExecutions
		successfulExecutions += stats.SuccessfulExecutions
		failedExecutions += stats.FailedExecutions
		totalExecutionTime += stats.TotalExecutionTime
	}

	metrics["total_executions"] = totalExecutions
	metrics["successful_executions"] = successfulExecutions
	metrics["failed_executions"] = failedExecutions

	if totalExecutions > 0 {
		metrics["average_execution_time"] = totalExecutionTime.Seconds() / float64(totalExecutions)
	}

	return metrics
}

// Helper functions

func generateRuleID() string {
	return fmt.Sprintf("rule_%d", time.Now().UnixNano())
}

func generateExecutionID() string {
	return fmt.Sprintf("exec_%d", time.Now().UnixNano())
}

func mustMarshalJSON(v interface{}) json.RawMessage {
	data, _ := json.Marshal(v)
	return data
}

func containsAllTags(ruleTags, requiredTags []string) bool {
	tagSet := make(map[string]bool)
	for _, tag := range ruleTags {
		tagSet[tag] = true
	}

	for _, requiredTag := range requiredTags {
		if !tagSet[requiredTag] {
			return false
		}
	}
	return true
}

// Database operations (to be implemented)
func (re *RuleEngine) loadRules() error {
	// TODO: Implement loading rules from database
	return nil
}

func (re *RuleEngine) loadRuleChains() error {
	// TODO: Implement loading rule chains from database
	return nil
}

func (re *RuleEngine) loadRuleFromDB(ctx context.Context, ruleID string) (*Rule, error) {
	// TODO: Implement loading rule from database
	return nil, nil
}

func (re *RuleEngine) saveRule(ctx context.Context, rule *Rule) error {
	// TODO: Implement saving rule to database
	return nil
}

func (re *RuleEngine) deleteRuleFromDB(ctx context.Context, ruleID string) error {
	// TODO: Implement deleting rule from database
	return nil
}

func (re *RuleEngine) saveExecution(ctx context.Context, execution *RuleExecution) error {
	// TODO: Implement saving execution to database
	return nil
}

func (re *RuleEngine) validateRule(rule *Rule) error {
	// TODO: Implement rule validation
	return nil
}

func (re *RuleEngine) executeRuleLogic(rule *Rule, context *DataContext) (map[string]interface{}, error) {
	// TODO: Implement rule logic execution
	return make(map[string]interface{}), nil
}

func (re *RuleEngine) updateRuleStats(rule *Rule, executionTime float64, success bool) {
	// TODO: Implement rule statistics update
}

func (re *RuleEngine) initializeBuiltinFunctions() {
	// TODO: Implement builtin functions
}

func (re *RuleEngine) GetRuleChain(ctx context.Context, chainID string) (*RuleChain, error) {
	// TODO: Implement getting rule chain
	return nil, nil
}
