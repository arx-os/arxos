package logic

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// RuleManager provides comprehensive rule lifecycle management
type RuleManager struct {
	dbService *DatabaseService
	logger    *zap.Logger
	mu        sync.RWMutex

	// Rule management
	rules      map[string]*Rule
	ruleChains map[string]*RuleChain

	// Rule categories and tags
	categories map[string]*RuleCategory
	tags       map[string]*RuleTag

	// Performance tracking
	ruleStats map[string]*RuleStatistics

	// Configuration
	config *RuleManagerConfig
}

// RuleManagerConfig holds rule manager configuration
type RuleManagerConfig struct {
	EnableAutoActivation  bool          `json:"enable_auto_activation"`
	EnableVersioning      bool          `json:"enable_versioning"`
	MaxRulesPerCategory   int           `json:"max_rules_per_category"`
	RuleValidationTimeout time.Duration `json:"rule_validation_timeout"`
	EnableRuleMetrics     bool          `json:"enable_rule_metrics"`
}

// RuleCategory represents a rule category
type RuleCategory struct {
	ID          string                 `json:"id" db:"id"`
	Name        string                 `json:"name" db:"name"`
	Description string                 `json:"description" db:"description"`
	ParentID    *string                `json:"parent_id" db:"parent_id"`
	CreatedAt   time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at" db:"updated_at"`
	Metadata    map[string]interface{} `json:"metadata" db:"metadata"`
	RuleCount   int                    `json:"rule_count" db:"rule_count"`
}

// RuleTag represents a rule tag
type RuleTag struct {
	ID          string                 `json:"id" db:"id"`
	Name        string                 `json:"name" db:"name"`
	Description string                 `json:"description" db:"description"`
	Color       string                 `json:"color" db:"color"`
	CreatedAt   time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at" db:"updated_at"`
	Metadata    map[string]interface{} `json:"metadata" db:"metadata"`
	RuleCount   int                    `json:"rule_count" db:"rule_count"`
}

// RuleStatistics represents rule execution statistics
type RuleStatistics struct {
	RuleID               string    `json:"rule_id" db:"rule_id"`
	TotalExecutions      int64     `json:"total_executions" db:"total_executions"`
	SuccessfulExecutions int64     `json:"successful_executions" db:"successful_executions"`
	FailedExecutions     int64     `json:"failed_executions" db:"failed_executions"`
	TotalExecutionTime   float64   `json:"total_execution_time" db:"total_execution_time"`
	AverageExecutionTime float64   `json:"average_execution_time" db:"average_execution_time"`
	LastExecutionTime    time.Time `json:"last_execution_time" db:"last_execution_time"`
	SuccessRate          float64   `json:"success_rate" db:"success_rate"`
	CreatedAt            time.Time `json:"created_at" db:"created_at"`
	UpdatedAt            time.Time `json:"updated_at" db:"updated_at"`
}

// RuleVersion represents a rule version
type RuleVersion struct {
	VersionID   string                 `json:"version_id" db:"version_id"`
	RuleID      string                 `json:"rule_id" db:"rule_id"`
	Version     string                 `json:"version" db:"version"`
	Description string                 `json:"description" db:"description"`
	Conditions  json.RawMessage        `json:"conditions" db:"conditions"`
	Actions     json.RawMessage        `json:"actions" db:"actions"`
	Status      RuleStatus             `json:"status" db:"status"`
	CreatedBy   string                 `json:"created_by" db:"created_by"`
	CreatedAt   time.Time              `json:"created_at" db:"created_at"`
	Metadata    map[string]interface{} `json:"metadata" db:"metadata"`
}

// NewRuleManager creates a new rule manager
func NewRuleManager(dbService *DatabaseService, logger *zap.Logger, config *RuleManagerConfig) (*RuleManager, error) {
	if config == nil {
		config = &RuleManagerConfig{
			EnableAutoActivation:  true,
			EnableVersioning:      true,
			MaxRulesPerCategory:   1000,
			RuleValidationTimeout: 30 * time.Second,
			EnableRuleMetrics:     true,
		}
	}

	rm := &RuleManager{
		dbService:  dbService,
		logger:     logger,
		rules:      make(map[string]*Rule),
		ruleChains: make(map[string]*RuleChain),
		categories: make(map[string]*RuleCategory),
		tags:       make(map[string]*RuleTag),
		ruleStats:  make(map[string]*RuleStatistics),
		config:     config,
	}

	// Load existing data
	if err := rm.loadCategories(); err != nil {
		return nil, fmt.Errorf("failed to load categories: %w", err)
	}

	if err := rm.loadTags(); err != nil {
		return nil, fmt.Errorf("failed to load tags: %w", err)
	}

	if err := rm.loadRuleStatistics(); err != nil {
		return nil, fmt.Errorf("failed to load rule statistics: %w", err)
	}

	logger.Info("Rule manager initialized",
		zap.Bool("enable_auto_activation", config.EnableAutoActivation),
		zap.Bool("enable_versioning", config.EnableVersioning),
		zap.Int("max_rules_per_category", config.MaxRulesPerCategory))

	return rm, nil
}

// CreateCategory creates a new rule category
func (rm *RuleManager) CreateCategory(ctx context.Context, name, description string, parentID *string, metadata map[string]interface{}) (string, error) {
	categoryID := generateCategoryID()
	now := time.Now()

	category := &RuleCategory{
		ID:          categoryID,
		Name:        name,
		Description: description,
		ParentID:    parentID,
		CreatedAt:   now,
		UpdatedAt:   now,
		Metadata:    metadata,
		RuleCount:   0,
	}

	// Validate category
	if err := rm.validateCategory(category); err != nil {
		return "", fmt.Errorf("category validation failed: %w", err)
	}

	// Save to database
	if err := rm.saveCategory(ctx, category); err != nil {
		return "", fmt.Errorf("failed to save category: %w", err)
	}

	// Add to memory cache
	rm.mu.Lock()
	rm.categories[categoryID] = category
	rm.mu.Unlock()

	rm.logger.Info("Category created",
		zap.String("category_id", categoryID),
		zap.String("name", name))

	return categoryID, nil
}

// GetCategory retrieves a category by ID
func (rm *RuleManager) GetCategory(ctx context.Context, categoryID string) (*RuleCategory, error) {
	rm.mu.RLock()
	category, exists := rm.categories[categoryID]
	rm.mu.RUnlock()

	if exists {
		return category, nil
	}

	// Load from database
	category, err := rm.loadCategoryFromDB(ctx, categoryID)
	if err != nil {
		return nil, fmt.Errorf("failed to load category: %w", err)
	}

	if category != nil {
		rm.mu.Lock()
		rm.categories[categoryID] = category
		rm.mu.Unlock()
	}

	return category, nil
}

// ListCategories lists all categories
func (rm *RuleManager) ListCategories(ctx context.Context, parentID *string) ([]*RuleCategory, error) {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	var categories []*RuleCategory
	for _, category := range rm.categories {
		if parentID != nil {
			if category.ParentID == nil || *category.ParentID != *parentID {
				continue
			}
		} else if category.ParentID != nil {
			continue
		}
		categories = append(categories, category)
	}

	return categories, nil
}

// CreateTag creates a new rule tag
func (rm *RuleManager) CreateTag(ctx context.Context, name, description, color string, metadata map[string]interface{}) (string, error) {
	tagID := generateTagID()
	now := time.Now()

	tag := &RuleTag{
		ID:          tagID,
		Name:        name,
		Description: description,
		Color:       color,
		CreatedAt:   now,
		UpdatedAt:   now,
		Metadata:    metadata,
		RuleCount:   0,
	}

	// Validate tag
	if err := rm.validateTag(tag); err != nil {
		return "", fmt.Errorf("tag validation failed: %w", err)
	}

	// Save to database
	if err := rm.saveTag(ctx, tag); err != nil {
		return "", fmt.Errorf("failed to save tag: %w", err)
	}

	// Add to memory cache
	rm.mu.Lock()
	rm.tags[tagID] = tag
	rm.mu.Unlock()

	rm.logger.Info("Tag created",
		zap.String("tag_id", tagID),
		zap.String("name", name))

	return tagID, nil
}

// GetTag retrieves a tag by ID
func (rm *RuleManager) GetTag(ctx context.Context, tagID string) (*RuleTag, error) {
	rm.mu.RLock()
	tag, exists := rm.tags[tagID]
	rm.mu.RUnlock()

	if exists {
		return tag, nil
	}

	// Load from database
	tag, err := rm.loadTagFromDB(ctx, tagID)
	if err != nil {
		return nil, fmt.Errorf("failed to load tag: %w", err)
	}

	if tag != nil {
		rm.mu.Lock()
		rm.tags[tagID] = tag
		rm.mu.Unlock()
	}

	return tag, nil
}

// ListTags lists all tags
func (rm *RuleManager) ListTags(ctx context.Context) ([]*RuleTag, error) {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	var tags []*RuleTag
	for _, tag := range rm.tags {
		tags = append(tags, tag)
	}

	return tags, nil
}

// CreateRuleVersion creates a new version of a rule
func (rm *RuleManager) CreateRuleVersion(ctx context.Context, ruleID, version, description string, conditions, actions json.RawMessage, createdBy string, metadata map[string]interface{}) (string, error) {
	// Check if rule exists
	rule, err := rm.GetRule(ctx, ruleID)
	if err != nil {
		return "", fmt.Errorf("failed to get rule: %w", err)
	}

	if rule == nil {
		return "", fmt.Errorf("rule not found: %s", ruleID)
	}

	versionID := generateVersionID()
	now := time.Now()

	ruleVersion := &RuleVersion{
		VersionID:   versionID,
		RuleID:      ruleID,
		Version:     version,
		Description: description,
		Conditions:  conditions,
		Actions:     actions,
		Status:      RuleStatusDraft,
		CreatedBy:   createdBy,
		CreatedAt:   now,
		Metadata:    metadata,
	}

	// Validate version
	if err := rm.validateRuleVersion(ruleVersion); err != nil {
		return "", fmt.Errorf("rule version validation failed: %w", err)
	}

	// Save to database
	if err := rm.saveRuleVersion(ctx, ruleVersion); err != nil {
		return "", fmt.Errorf("failed to save rule version: %w", err)
	}

	rm.logger.Info("Rule version created",
		zap.String("version_id", versionID),
		zap.String("rule_id", ruleID),
		zap.String("version", version))

	return versionID, nil
}

// GetRuleVersions retrieves all versions of a rule
func (rm *RuleManager) GetRuleVersions(ctx context.Context, ruleID string) ([]*RuleVersion, error) {
	versions, err := rm.loadRuleVersionsFromDB(ctx, ruleID)
	if err != nil {
		return nil, fmt.Errorf("failed to load rule versions: %w", err)
	}

	return versions, nil
}

// ActivateRuleVersion activates a specific rule version
func (rm *RuleManager) ActivateRuleVersion(ctx context.Context, versionID string) error {
	// Get rule version
	version, err := rm.loadRuleVersionFromDB(ctx, versionID)
	if err != nil {
		return fmt.Errorf("failed to load rule version: %w", err)
	}

	if version == nil {
		return fmt.Errorf("rule version not found: %s", versionID)
	}

	// Update rule with version data
	rule, err := rm.GetRule(ctx, version.RuleID)
	if err != nil {
		return fmt.Errorf("failed to get rule: %w", err)
	}

	rule.Conditions = version.Conditions
	rule.Actions = version.Actions
	rule.Version = version.Version
	rule.Status = RuleStatusActive
	rule.UpdatedAt = time.Now()

	// Save updated rule
	if err := rm.saveRule(ctx, rule); err != nil {
		return fmt.Errorf("failed to save rule: %w", err)
	}

	// Update version status
	version.Status = RuleStatusActive
	if err := rm.saveRuleVersion(ctx, version); err != nil {
		return fmt.Errorf("failed to save rule version: %w", err)
	}

	rm.logger.Info("Rule version activated",
		zap.String("version_id", versionID),
		zap.String("rule_id", version.RuleID))

	return nil
}

// GetRuleStatistics retrieves statistics for a rule
func (rm *RuleManager) GetRuleStatistics(ctx context.Context, ruleID string) (*RuleStatistics, error) {
	rm.mu.RLock()
	stats, exists := rm.ruleStats[ruleID]
	rm.mu.RUnlock()

	if exists {
		return stats, nil
	}

	// Load from database
	stats, err := rm.loadRuleStatisticsFromDB(ctx, ruleID)
	if err != nil {
		return nil, fmt.Errorf("failed to load rule statistics: %w", err)
	}

	if stats != nil {
		rm.mu.Lock()
		rm.ruleStats[ruleID] = stats
		rm.mu.Unlock()
	}

	return stats, nil
}

// UpdateRuleStatistics updates rule execution statistics
func (rm *RuleManager) UpdateRuleStatistics(ctx context.Context, ruleID string, executionTime float64, success bool) error {
	rm.mu.Lock()
	defer rm.mu.Unlock()

	stats, exists := rm.ruleStats[ruleID]
	if !exists {
		stats = &RuleStatistics{
			RuleID:    ruleID,
			CreatedAt: time.Now(),
		}
		rm.ruleStats[ruleID] = stats
	}

	stats.TotalExecutions++
	stats.TotalExecutionTime += executionTime
	stats.LastExecutionTime = time.Now()
	stats.UpdatedAt = time.Now()

	if success {
		stats.SuccessfulExecutions++
	} else {
		stats.FailedExecutions++
	}

	if stats.TotalExecutions > 0 {
		stats.AverageExecutionTime = stats.TotalExecutionTime / float64(stats.TotalExecutions)
		stats.SuccessRate = float64(stats.SuccessfulExecutions) / float64(stats.TotalExecutions) * 100
	}

	// Save to database
	if err := rm.saveRuleStatistics(ctx, stats); err != nil {
		return fmt.Errorf("failed to save rule statistics: %w", err)
	}

	return nil
}

// GetRuleMetrics returns comprehensive rule metrics
func (rm *RuleManager) GetRuleMetrics(ctx context.Context) map[string]interface{} {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	metrics := map[string]interface{}{
		"total_rules":           len(rm.rules),
		"total_categories":      len(rm.categories),
		"total_tags":            len(rm.tags),
		"active_rules":          0,
		"inactive_rules":        0,
		"draft_rules":           0,
		"archived_rules":        0,
		"total_executions":      0,
		"successful_executions": 0,
		"failed_executions":     0,
		"average_success_rate":  0.0,
	}

	var totalExecutions, successfulExecutions, failedExecutions int64
	var totalSuccessRate float64
	var activeRules, inactiveRules, draftRules, archivedRules int

	for _, rule := range rm.rules {
		switch rule.Status {
		case RuleStatusActive:
			activeRules++
		case RuleStatusInactive:
			inactiveRules++
		case RuleStatusDraft:
			draftRules++
		case RuleStatusArchived:
			archivedRules++
		}
	}

	for _, stats := range rm.ruleStats {
		totalExecutions += stats.TotalExecutions
		successfulExecutions += stats.SuccessfulExecutions
		failedExecutions += stats.FailedExecutions
		totalSuccessRate += stats.SuccessRate
	}

	metrics["active_rules"] = activeRules
	metrics["inactive_rules"] = inactiveRules
	metrics["draft_rules"] = draftRules
	metrics["archived_rules"] = archivedRules
	metrics["total_executions"] = totalExecutions
	metrics["successful_executions"] = successfulExecutions
	metrics["failed_executions"] = failedExecutions

	if len(rm.ruleStats) > 0 {
		metrics["average_success_rate"] = totalSuccessRate / float64(len(rm.ruleStats))
	}

	return metrics
}

// Helper functions

func generateCategoryID() string {
	return fmt.Sprintf("cat_%d", time.Now().UnixNano())
}

func generateTagID() string {
	return fmt.Sprintf("tag_%d", time.Now().UnixNano())
}

func generateVersionID() string {
	return fmt.Sprintf("ver_%d", time.Now().UnixNano())
}

func (rm *RuleManager) validateCategory(category *RuleCategory) error {
	if category.Name == "" {
		return fmt.Errorf("category name is required")
	}

	// Check if category name already exists
	for _, existingCategory := range rm.categories {
		if existingCategory.Name == category.Name && existingCategory.ID != category.ID {
			return fmt.Errorf("category name already exists: %s", category.Name)
		}
	}

	return nil
}

func (rm *RuleManager) validateTag(tag *RuleTag) error {
	if tag.Name == "" {
		return fmt.Errorf("tag name is required")
	}

	// Check if tag name already exists
	for _, existingTag := range rm.tags {
		if existingTag.Name == tag.Name && existingTag.ID != tag.ID {
			return fmt.Errorf("tag name already exists: %s", tag.Name)
		}
	}

	return nil
}

func (rm *RuleManager) validateRuleVersion(version *RuleVersion) error {
	if version.Version == "" {
		return fmt.Errorf("version is required")
	}

	if version.CreatedBy == "" {
		return fmt.Errorf("created by is required")
	}

	return nil
}

// Database operations (to be implemented)
func (rm *RuleManager) loadCategories() error {
	// TODO: Implement loading categories from database
	return nil
}

func (rm *RuleManager) loadTags() error {
	// TODO: Implement loading tags from database
	return nil
}

func (rm *RuleManager) loadRuleStatistics() error {
	// TODO: Implement loading rule statistics from database
	return nil
}

func (rm *RuleManager) saveCategory(ctx context.Context, category *RuleCategory) error {
	// TODO: Implement saving category to database
	return nil
}

func (rm *RuleManager) loadCategoryFromDB(ctx context.Context, categoryID string) (*RuleCategory, error) {
	// TODO: Implement loading category from database
	return nil, nil
}

func (rm *RuleManager) saveTag(ctx context.Context, tag *RuleTag) error {
	// TODO: Implement saving tag to database
	return nil
}

func (rm *RuleManager) loadTagFromDB(ctx context.Context, tagID string) (*RuleTag, error) {
	// TODO: Implement loading tag from database
	return nil, nil
}

func (rm *RuleManager) saveRuleVersion(ctx context.Context, version *RuleVersion) error {
	// TODO: Implement saving rule version to database
	return nil
}

func (rm *RuleManager) loadRuleVersionFromDB(ctx context.Context, versionID string) (*RuleVersion, error) {
	// TODO: Implement loading rule version from database
	return nil, nil
}

func (rm *RuleManager) loadRuleVersionsFromDB(ctx context.Context, ruleID string) ([]*RuleVersion, error) {
	// TODO: Implement loading rule versions from database
	return nil, nil
}

func (rm *RuleManager) saveRuleStatistics(ctx context.Context, stats *RuleStatistics) error {
	// TODO: Implement saving rule statistics to database
	return nil
}

func (rm *RuleManager) loadRuleStatisticsFromDB(ctx context.Context, ruleID string) (*RuleStatistics, error) {
	// TODO: Implement loading rule statistics from database
	return nil, nil
}

func (rm *RuleManager) GetRule(ctx context.Context, ruleID string) (*Rule, error) {
	// TODO: Implement getting rule
	return nil, nil
}

func (rm *RuleManager) saveRule(ctx context.Context, rule *Rule) error {
	// TODO: Implement saving rule
	return nil
}
