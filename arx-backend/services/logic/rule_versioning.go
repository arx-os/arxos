package logic

import (
	"context"
	"encoding/json"
	"fmt"
	"reflect"
	"sort"
	"sync"
	"time"

	"go.uber.org/zap"
)

// VersionStatus represents the status of a version
type VersionStatus string

const (
	VersionStatusDraft      VersionStatus = "draft"
	VersionStatusActive     VersionStatus = "active"
	VersionStatusDeprecated VersionStatus = "deprecated"
	VersionStatusArchived   VersionStatus = "archived"
)

// VersionChangeType represents the type of change
type VersionChangeType string

const (
	VersionChangeTypeCreated    VersionChangeType = "created"
	VersionChangeTypeModified   VersionChangeType = "modified"
	VersionChangeTypeActivated  VersionChangeType = "activated"
	VersionChangeTypeDeprecated VersionChangeType = "deprecated"
	VersionChangeTypeArchived   VersionChangeType = "archived"
)

// VersionChange represents a version change
type VersionChange struct {
	ChangeID      string                 `json:"change_id" db:"change_id"`
	RuleID        string                 `json:"rule_id" db:"rule_id"`
	VersionID     string                 `json:"version_id" db:"version_id"`
	ChangeType    VersionChangeType      `json:"change_type" db:"change_type"`
	Description   string                 `json:"description" db:"description"`
	ChangedBy     string                 `json:"changed_by" db:"changed_by"`
	ChangedAt     time.Time              `json:"changed_at" db:"changed_at"`
	PreviousValue json.RawMessage        `json:"previous_value" db:"previous_value"`
	NewValue      json.RawMessage        `json:"new_value" db:"new_value"`
	Metadata      map[string]interface{} `json:"metadata" db:"metadata"`
}

// VersionDiff represents a version difference
type VersionDiff struct {
	Field         string      `json:"field"`
	PreviousValue interface{} `json:"previous_value"`
	NewValue      interface{} `json:"new_value"`
	ChangeType    string      `json:"change_type"`
	Severity      string      `json:"severity"`
	Description   string      `json:"description"`
}

// VersionComparison represents a version comparison result
type VersionComparison struct {
	RuleID             string        `json:"rule_id"`
	Version1           string        `json:"version1"`
	Version2           string        `json:"version2"`
	Differences        []VersionDiff `json:"differences"`
	BreakingChanges    []VersionDiff `json:"breaking_changes"`
	NonBreakingChanges []VersionDiff `json:"non_breaking_changes"`
	ComparisonTime     time.Time     `json:"comparison_time"`
}

// RuleVersioning provides comprehensive rule versioning capabilities
type RuleVersioning struct {
	dbService *DatabaseService
	logger    *zap.Logger
	mu        sync.RWMutex

	// Version management
	versions       map[string]*RuleVersion
	versionChanges map[string]*VersionChange

	// Configuration
	config *VersioningConfig
}

// VersioningConfig holds versioning configuration
type VersioningConfig struct {
	EnableAutoVersioning    bool          `json:"enable_auto_versioning"`
	EnableChangeTracking    bool          `json:"enable_change_tracking"`
	MaxVersionsPerRule      int           `json:"max_versions_per_rule"`
	VersionRetentionDays    int           `json:"version_retention_days"`
	EnableVersionComparison bool          `json:"enable_version_comparison"`
	AutoArchiveThreshold    time.Duration `json:"auto_archive_threshold"`
}

// NewRuleVersioning creates a new rule versioning service
func NewRuleVersioning(dbService *DatabaseService, logger *zap.Logger, config *VersioningConfig) (*RuleVersioning, error) {
	if config == nil {
		config = &VersioningConfig{
			EnableAutoVersioning:    true,
			EnableChangeTracking:    true,
			MaxVersionsPerRule:      50,
			VersionRetentionDays:    365,
			EnableVersionComparison: true,
			AutoArchiveThreshold:    30 * 24 * time.Hour, // 30 days
		}
	}

	rv := &RuleVersioning{
		dbService:      dbService,
		logger:         logger,
		versions:       make(map[string]*RuleVersion),
		versionChanges: make(map[string]*VersionChange),
		config:         config,
	}

	logger.Info("Rule versioning initialized",
		zap.Bool("enable_auto_versioning", config.EnableAutoVersioning),
		zap.Bool("enable_change_tracking", config.EnableChangeTracking),
		zap.Int("max_versions_per_rule", config.MaxVersionsPerRule))

	return rv, nil
}

// CreateVersion creates a new version of a rule
func (rv *RuleVersioning) CreateVersion(ctx context.Context, ruleID, version, description string, conditions, actions json.RawMessage, createdBy string, metadata map[string]interface{}) (string, error) {
	// Validate version format
	if !rv.isValidVersionFormat(version) {
		return "", fmt.Errorf("invalid version format: %s", version)
	}

	// Check if version already exists
	if rv.versionExists(ctx, ruleID, version) {
		return "", fmt.Errorf("version already exists: %s", version)
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
	if err := rv.validateVersion(ruleVersion); err != nil {
		return "", fmt.Errorf("version validation failed: %w", err)
	}

	// Save to database
	if err := rv.saveVersion(ctx, ruleVersion); err != nil {
		return "", fmt.Errorf("failed to save version: %w", err)
	}

	// Add to memory cache
	rv.mu.Lock()
	rv.versions[versionID] = ruleVersion
	rv.mu.Unlock()

	// Track version change
	if rv.config.EnableChangeTracking {
		rv.trackVersionChange(ctx, ruleVersion, VersionChangeTypeCreated, "Version created", createdBy, nil, ruleVersion)
	}

	rv.logger.Info("Rule version created",
		zap.String("version_id", versionID),
		zap.String("rule_id", ruleID),
		zap.String("version", version))

	return versionID, nil
}

// GetVersion retrieves a specific version
func (rv *RuleVersioning) GetVersion(ctx context.Context, versionID string) (*RuleVersion, error) {
	rv.mu.RLock()
	version, exists := rv.versions[versionID]
	rv.mu.RUnlock()

	if exists {
		return version, nil
	}

	// Load from database
	version, err := rv.loadVersionFromDB(ctx, versionID)
	if err != nil {
		return nil, fmt.Errorf("failed to load version: %w", err)
	}

	if version != nil {
		rv.mu.Lock()
		rv.versions[versionID] = version
		rv.mu.Unlock()
	}

	return version, nil
}

// GetVersions retrieves all versions of a rule
func (rv *RuleVersioning) GetVersions(ctx context.Context, ruleID string) ([]*RuleVersion, error) {
	versions, err := rv.loadVersionsFromDB(ctx, ruleID)
	if err != nil {
		return nil, fmt.Errorf("failed to load versions: %w", err)
	}

	// Sort versions by semantic version
	sort.Slice(versions, func(i, j int) bool {
		return rv.compareVersions(versions[i].Version, versions[j].Version) < 0
	})

	return versions, nil
}

// ActivateVersion activates a specific version
func (rv *RuleVersioning) ActivateVersion(ctx context.Context, versionID string, activatedBy string) error {
	version, err := rv.GetVersion(ctx, versionID)
	if err != nil {
		return fmt.Errorf("failed to get version: %w", err)
	}

	if version == nil {
		return fmt.Errorf("version not found: %s", versionID)
	}

	// Deactivate other versions of the same rule
	if err := rv.deactivateOtherVersions(ctx, version.RuleID, versionID); err != nil {
		return fmt.Errorf("failed to deactivate other versions: %w", err)
	}

	// Update version status
	previousStatus := version.Status
	version.Status = RuleStatusActive
	version.UpdatedAt = time.Now()

	// Save to database
	if err := rv.saveVersion(ctx, version); err != nil {
		return fmt.Errorf("failed to save version: %w", err)
	}

	// Update memory cache
	rv.mu.Lock()
	rv.versions[versionID] = version
	rv.mu.Unlock()

	// Track version change
	if rv.config.EnableChangeTracking {
		rv.trackVersionChange(ctx, version, VersionChangeTypeActivated, "Version activated", activatedBy, &previousStatus, &version.Status)
	}

	rv.logger.Info("Rule version activated",
		zap.String("version_id", versionID),
		zap.String("rule_id", version.RuleID),
		zap.String("version", version.Version))

	return nil
}

// DeprecateVersion deprecates a specific version
func (rv *RuleVersioning) DeprecateVersion(ctx context.Context, versionID string, deprecatedBy string, reason string) error {
	version, err := rv.GetVersion(ctx, versionID)
	if err != nil {
		return fmt.Errorf("failed to get version: %w", err)
	}

	if version == nil {
		return fmt.Errorf("version not found: %s", versionID)
	}

	previousStatus := version.Status
	version.Status = RuleStatusArchived
	version.UpdatedAt = time.Now()

	// Update metadata with deprecation info
	if version.Metadata == nil {
		version.Metadata = make(map[string]interface{})
	}
	version.Metadata["deprecated_by"] = deprecatedBy
	version.Metadata["deprecated_at"] = time.Now()
	version.Metadata["deprecation_reason"] = reason

	// Save to database
	if err := rv.saveVersion(ctx, version); err != nil {
		return fmt.Errorf("failed to save version: %w", err)
	}

	// Update memory cache
	rv.mu.Lock()
	rv.versions[versionID] = version
	rv.mu.Unlock()

	// Track version change
	if rv.config.EnableChangeTracking {
		rv.trackVersionChange(ctx, version, VersionChangeTypeDeprecated, fmt.Sprintf("Version deprecated: %s", reason), deprecatedBy, &previousStatus, &version.Status)
	}

	rv.logger.Info("Rule version deprecated",
		zap.String("version_id", versionID),
		zap.String("rule_id", version.RuleID),
		zap.String("version", version.Version),
		zap.String("reason", reason))

	return nil
}

// CompareVersions compares two versions of a rule
func (rv *RuleVersioning) CompareVersions(ctx context.Context, ruleID, version1, version2 string) (*VersionComparison, error) {
	// Get both versions
	v1, err := rv.getVersionByRuleAndVersion(ctx, ruleID, version1)
	if err != nil {
		return nil, fmt.Errorf("failed to get version 1: %w", err)
	}

	v2, err := rv.getVersionByRuleAndVersion(ctx, ruleID, version2)
	if err != nil {
		return nil, fmt.Errorf("failed to get version 2: %w", err)
	}

	if v1 == nil || v2 == nil {
		return nil, fmt.Errorf("one or both versions not found")
	}

	comparison := &VersionComparison{
		RuleID:         ruleID,
		Version1:       version1,
		Version2:       version2,
		ComparisonTime: time.Now(),
	}

	// Compare versions
	rv.compareVersionFields(v1, v2, comparison)

	return comparison, nil
}

// GetVersionChanges retrieves version changes for a rule
func (rv *RuleVersioning) GetVersionChanges(ctx context.Context, ruleID string, limit int) ([]*VersionChange, error) {
	if limit <= 0 {
		limit = 100
	}

	changes, err := rv.loadVersionChangesFromDB(ctx, ruleID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to load version changes: %w", err)
	}

	return changes, nil
}

// GetActiveVersion retrieves the active version of a rule
func (rv *RuleVersioning) GetActiveVersion(ctx context.Context, ruleID string) (*RuleVersion, error) {
	versions, err := rv.GetVersions(ctx, ruleID)
	if err != nil {
		return nil, fmt.Errorf("failed to get versions: %w", err)
	}

	for _, version := range versions {
		if version.Status == RuleStatusActive {
			return version, nil
		}
	}

	return nil, fmt.Errorf("no active version found for rule: %s", ruleID)
}

// GetLatestVersion retrieves the latest version of a rule
func (rv *RuleVersioning) GetLatestVersion(ctx context.Context, ruleID string) (*RuleVersion, error) {
	versions, err := rv.GetVersions(ctx, ruleID)
	if err != nil {
		return nil, fmt.Errorf("failed to get versions: %w", err)
	}

	if len(versions) == 0 {
		return nil, fmt.Errorf("no versions found for rule: %s", ruleID)
	}

	return versions[len(versions)-1], nil
}

// CleanupOldVersions cleans up old versions based on retention policy
func (rv *RuleVersioning) CleanupOldVersions(ctx context.Context) error {
	cutoffDate := time.Now().AddDate(0, 0, -rv.config.VersionRetentionDays)

	oldVersions, err := rv.loadOldVersionsFromDB(ctx, cutoffDate)
	if err != nil {
		return fmt.Errorf("failed to load old versions: %w", err)
	}

	for _, version := range oldVersions {
		if err := rv.archiveVersion(ctx, version.VersionID); err != nil {
			rv.logger.Error("Failed to archive old version",
				zap.String("version_id", version.VersionID),
				zap.Error(err))
		}
	}

	rv.logger.Info("Cleanup completed",
		zap.Int("archived_versions", len(oldVersions)))

	return nil
}

// Helper functions

func (rv *RuleVersioning) isValidVersionFormat(version string) bool {
	// Simple semantic version check
	// This can be enhanced with more sophisticated version parsing
	return len(version) > 0 && len(version) <= 50
}

func (rv *RuleVersioning) versionExists(ctx context.Context, ruleID, version string) bool {
	// Check if version already exists for the rule
	versions, err := rv.GetVersions(ctx, ruleID)
	if err != nil {
		return false
	}

	for _, v := range versions {
		if v.Version == version {
			return true
		}
	}

	return false
}

func (rv *RuleVersioning) validateVersion(version *RuleVersion) error {
	if version.RuleID == "" {
		return fmt.Errorf("rule ID is required")
	}

	if version.Version == "" {
		return fmt.Errorf("version is required")
	}

	if version.CreatedBy == "" {
		return fmt.Errorf("created by is required")
	}

	return nil
}

func (rv *RuleVersioning) deactivateOtherVersions(ctx context.Context, ruleID, activeVersionID string) error {
	versions, err := rv.GetVersions(ctx, ruleID)
	if err != nil {
		return err
	}

	for _, version := range versions {
		if version.VersionID != activeVersionID && version.Status == RuleStatusActive {
			version.Status = RuleStatusArchived
			version.UpdatedAt = time.Now()

			if err := rv.saveVersion(ctx, version); err != nil {
				return fmt.Errorf("failed to deactivate version %s: %w", version.VersionID, err)
			}

			// Update memory cache
			rv.mu.Lock()
			rv.versions[version.VersionID] = version
			rv.mu.Unlock()
		}
	}

	return nil
}

func (rv *RuleVersioning) trackVersionChange(ctx context.Context, version *RuleVersion, changeType VersionChangeType, description, changedBy string, previousValue, newValue interface{}) {
	changeID := generateChangeID()
	now := time.Now()

	change := &VersionChange{
		ChangeID:    changeID,
		RuleID:      version.RuleID,
		VersionID:   version.VersionID,
		ChangeType:  changeType,
		Description: description,
		ChangedBy:   changedBy,
		ChangedAt:   now,
		Metadata:    make(map[string]interface{}),
	}

	if previousValue != nil {
		change.PreviousValue = mustMarshalJSON(previousValue)
	}
	if newValue != nil {
		change.NewValue = mustMarshalJSON(newValue)
	}

	// Save change to database
	if err := rv.saveVersionChange(ctx, change); err != nil {
		rv.logger.Error("Failed to save version change", zap.Error(err))
	}

	// Add to memory cache
	rv.mu.Lock()
	rv.versionChanges[changeID] = change
	rv.mu.Unlock()
}

func (rv *RuleVersioning) compareVersions(v1, v2 string) int {
	// Simple version comparison - can be enhanced with semantic version parsing
	if v1 == v2 {
		return 0
	}
	if v1 < v2 {
		return -1
	}
	return 1
}

func (rv *RuleVersioning) compareVersionFields(v1, v2 *RuleVersion, comparison *VersionComparison) {
	// Compare conditions
	if !reflect.DeepEqual(v1.Conditions, v2.Conditions) {
		comparison.Differences = append(comparison.Differences, VersionDiff{
			Field:         "conditions",
			PreviousValue: v1.Conditions,
			NewValue:      v2.Conditions,
			ChangeType:    "modified",
			Severity:      "high",
			Description:   "Rule conditions changed",
		})
		comparison.BreakingChanges = append(comparison.BreakingChanges, VersionDiff{
			Field:         "conditions",
			PreviousValue: v1.Conditions,
			NewValue:      v2.Conditions,
			ChangeType:    "modified",
			Severity:      "high",
			Description:   "Rule conditions changed",
		})
	}

	// Compare actions
	if !reflect.DeepEqual(v1.Actions, v2.Actions) {
		comparison.Differences = append(comparison.Differences, VersionDiff{
			Field:         "actions",
			PreviousValue: v1.Actions,
			NewValue:      v2.Actions,
			ChangeType:    "modified",
			Severity:      "medium",
			Description:   "Rule actions changed",
		})
		comparison.NonBreakingChanges = append(comparison.NonBreakingChanges, VersionDiff{
			Field:         "actions",
			PreviousValue: v1.Actions,
			NewValue:      v2.Actions,
			ChangeType:    "modified",
			Severity:      "medium",
			Description:   "Rule actions changed",
		})
	}

	// Compare description
	if v1.Description != v2.Description {
		comparison.Differences = append(comparison.Differences, VersionDiff{
			Field:         "description",
			PreviousValue: v1.Description,
			NewValue:      v2.Description,
			ChangeType:    "modified",
			Severity:      "low",
			Description:   "Rule description changed",
		})
		comparison.NonBreakingChanges = append(comparison.NonBreakingChanges, VersionDiff{
			Field:         "description",
			PreviousValue: v1.Description,
			NewValue:      v2.Description,
			ChangeType:    "modified",
			Severity:      "low",
			Description:   "Rule description changed",
		})
	}
}

func (rv *RuleVersioning) archiveVersion(ctx context.Context, versionID string) error {
	version, err := rv.GetVersion(ctx, versionID)
	if err != nil {
		return err
	}

	version.Status = RuleStatusArchived
	version.UpdatedAt = time.Now()

	return rv.saveVersion(ctx, version)
}

func generateVersionID() string {
	return fmt.Sprintf("ver_%d", time.Now().UnixNano())
}

func generateChangeID() string {
	return fmt.Sprintf("chg_%d", time.Now().UnixNano())
}

func mustMarshalJSON(v interface{}) json.RawMessage {
	data, _ := json.Marshal(v)
	return data
}

// Database operations (to be implemented)
func (rv *RuleVersioning) saveVersion(ctx context.Context, version *RuleVersion) error {
	// TODO: Implement saving version to database
	return nil
}

func (rv *RuleVersioning) loadVersionFromDB(ctx context.Context, versionID string) (*RuleVersion, error) {
	// TODO: Implement loading version from database
	return nil, nil
}

func (rv *RuleVersioning) loadVersionsFromDB(ctx context.Context, ruleID string) ([]*RuleVersion, error) {
	// TODO: Implement loading versions from database
	return nil, nil
}

func (rv *RuleVersioning) getVersionByRuleAndVersion(ctx context.Context, ruleID, version string) (*RuleVersion, error) {
	// TODO: Implement getting version by rule ID and version
	return nil, nil
}

func (rv *RuleVersioning) saveVersionChange(ctx context.Context, change *VersionChange) error {
	// TODO: Implement saving version change to database
	return nil
}

func (rv *RuleVersioning) loadVersionChangesFromDB(ctx context.Context, ruleID string, limit int) ([]*VersionChange, error) {
	// TODO: Implement loading version changes from database
	return nil, nil
}

func (rv *RuleVersioning) loadOldVersionsFromDB(ctx context.Context, cutoffDate time.Time) ([]*RuleVersion, error) {
	// TODO: Implement loading old versions from database
	return nil, nil
}
