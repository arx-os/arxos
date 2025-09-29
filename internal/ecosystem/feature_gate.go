package ecosystem

import (
	"context"
	"fmt"
	"strings"
)

// FeatureGate manages tier-based feature access control
type FeatureGate struct {
	userTierResolver UserTierResolver
}

// UserTierResolver resolves a user's tier access
type UserTierResolver interface {
	GetUserTier(ctx context.Context, userID string) (Tier, error)
	GetUserLimits(ctx context.Context, userID string, tier Tier) (map[string]interface{}, error)
}

// NewFeatureGate creates a new feature gate
func NewFeatureGate(resolver UserTierResolver) *FeatureGate {
	return &FeatureGate{
		userTierResolver: resolver,
	}
}

// CheckFeatureAccess validates if a user can access a specific feature
func (fg *FeatureGate) CheckFeatureAccess(ctx context.Context, userID string, feature string) error {
	userTier, err := fg.userTierResolver.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to resolve user tier: %w", err)
	}

	// Check if feature is available in user's tier
	if !IsFeatureAvailable(userTier, feature) {
		return fmt.Errorf("feature '%s' not available in tier '%s'", feature, userTier)
	}

	return nil
}

// CheckEndpointAccess validates if a user can access a specific API endpoint
func (fg *FeatureGate) CheckEndpointAccess(ctx context.Context, userID string, endpoint string) error {
	userTier, err := fg.userTierResolver.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to resolve user tier: %w", err)
	}

	// Check if endpoint is available in user's tier
	if !IsEndpointAvailable(userTier, endpoint) {
		return fmt.Errorf("endpoint '%s' not available in tier '%s'", endpoint, userTier)
	}

	return nil
}

// CheckLimits validates if a user is within their tier limits
func (fg *FeatureGate) CheckLimits(ctx context.Context, userID string, resource string, currentUsage int) error {
	userTier, err := fg.userTierResolver.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to resolve user tier: %w", err)
	}

	limits, err := fg.userTierResolver.GetUserLimits(ctx, userID, userTier)
	if err != nil {
		return fmt.Errorf("failed to get user limits: %w", err)
	}

	limit, exists := limits[resource]
	if !exists {
		// No limit defined for this resource
		return nil
	}

	limitValue, ok := limit.(int)
	if !ok {
		return fmt.Errorf("invalid limit type for resource '%s'", resource)
	}

	if limitValue == -1 {
		// Unlimited
		return nil
	}

	if currentUsage >= limitValue {
		return fmt.Errorf("limit exceeded for resource '%s': %d/%d", resource, currentUsage, limitValue)
	}

	return nil
}

// GetAvailableFeatures returns all features available to a user
func (fg *FeatureGate) GetAvailableFeatures(ctx context.Context, userID string) ([]string, error) {
	userTier, err := fg.userTierResolver.GetUserTier(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to resolve user tier: %w", err)
	}

	tierInfo := GetTierInfo(userTier)
	return tierInfo.Features, nil
}

// GetAvailableEndpoints returns all API endpoints available to a user
func (fg *FeatureGate) GetAvailableEndpoints(ctx context.Context, userID string) ([]string, error) {
	userTier, err := fg.userTierResolver.GetUserTier(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to resolve user tier: %w", err)
	}

	tierInfo := GetTierInfo(userTier)
	return tierInfo.APIEndpoints, nil
}

// GetUserLimits returns the limits for a user's tier
func (fg *FeatureGate) GetUserLimits(ctx context.Context, userID string) (map[string]interface{}, error) {
	userTier, err := fg.userTierResolver.GetUserTier(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to resolve user tier: %w", err)
	}

	limits, err := fg.userTierResolver.GetUserLimits(ctx, userID, userTier)
	if err != nil {
		return nil, fmt.Errorf("failed to get user limits: %w", err)
	}

	return limits, nil
}

// Feature definitions for tier mapping
var (
	// Core Tier Features (FREE)
	CoreFeatures = []string{
		"building_management",
		"equipment_management",
		"spatial_queries",
		"import_export",
		"basic_cli",
		"version_control",
		"hardware_designs",
		"community_support",
	}

	// Hardware Tier Features (FREEMIUM)
	HardwareFeatures = []string{
		"device_management",
		"gateway_deployment",
		"device_templates",
		"firmware_updates",
		"protocol_translation",
		"basic_automation",
		"certified_marketplace",
		"hardware_support",
	}

	// Workflow Tier Features (PAID)
	WorkflowFeatures = []string{
		"visual_workflows",
		"workflow_automation",
		"cmmc_features",
		"work_order_management",
		"maintenance_scheduling",
		"predictive_analytics",
		"enterprise_integrations",
		"advanced_reporting",
		"professional_support",
		"unlimited_resources",
	}

	// API Endpoints by tier
	CoreEndpoints = []string{
		"/api/v1/core/buildings",
		"/api/v1/core/equipment",
		"/api/v1/core/spatial",
		"/api/v1/core/import",
		"/api/v1/core/export",
	}

	HardwareEndpoints = []string{
		"/api/v1/hardware/devices",
		"/api/v1/hardware/templates",
		"/api/v1/hardware/gateway",
		"/api/v1/hardware/marketplace",
	}

	WorkflowEndpoints = []string{
		"/api/v1/workflow/workflows",
		"/api/v1/workflow/cmmc",
		"/api/v1/workflow/automation",
		"/api/v1/workflow/analytics",
		"/api/v1/workflow/integrations",
	}
)

// Enhanced feature availability checking
func IsFeatureAvailableInTier(tier Tier, feature string) bool {
	switch tier {
	case TierCore:
		return contains(CoreFeatures, feature)
	case TierHardware:
		return contains(CoreFeatures, feature) || contains(HardwareFeatures, feature)
	case TierWorkflow:
		return contains(CoreFeatures, feature) || contains(HardwareFeatures, feature) || contains(WorkflowFeatures, feature)
	default:
		return false
	}
}

// Enhanced endpoint availability checking
func IsEndpointAvailableInTier(tier Tier, endpoint string) bool {
	switch tier {
	case TierCore:
		return contains(CoreEndpoints, endpoint) || strings.HasPrefix(endpoint, "/api/v1/core/")
	case TierHardware:
		return contains(CoreEndpoints, endpoint) || contains(HardwareEndpoints, endpoint) ||
			strings.HasPrefix(endpoint, "/api/v1/core/") || strings.HasPrefix(endpoint, "/api/v1/hardware/")
	case TierWorkflow:
		return contains(CoreEndpoints, endpoint) || contains(HardwareEndpoints, endpoint) || contains(WorkflowEndpoints, endpoint) ||
			strings.HasPrefix(endpoint, "/api/v1/core/") || strings.HasPrefix(endpoint, "/api/v1/hardware/") || strings.HasPrefix(endpoint, "/api/v1/workflow/")
	default:
		return false
	}
}

// Helper function to check if a slice contains a string
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// Tier upgrade/downgrade validation
type TierTransition struct {
	FromTier Tier `json:"from_tier"`
	ToTier   Tier `json:"to_tier"`
}

// ValidateTierTransition validates if a tier transition is allowed
func ValidateTierTransition(transition TierTransition) error {
	// Define allowed transitions
	allowedTransitions := map[Tier][]Tier{
		TierCore:     {TierCore, TierHardware, TierWorkflow}, // Can stay, upgrade to hardware, or upgrade to workflow
		TierHardware: {TierCore, TierHardware, TierWorkflow}, // Can downgrade, stay, or upgrade
		TierWorkflow: {TierCore, TierHardware, TierWorkflow}, // Can downgrade to any tier
	}

	allowed, exists := allowedTransitions[transition.FromTier]
	if !exists {
		return fmt.Errorf("unknown source tier: %s", transition.FromTier)
	}

	for _, allowedTier := range allowed {
		if allowedTier == transition.ToTier {
			return nil
		}
	}

	return fmt.Errorf("transition from %s to %s is not allowed", transition.FromTier, transition.ToTier)
}

// Feature migration helper
type FeatureMigration struct {
	Feature     string                 `json:"feature"`
	FromTier    Tier                   `json:"from_tier"`
	ToTier      Tier                   `json:"to_tier"`
	DataLoss    bool                   `json:"data_loss"`
	MigrationFn func() error           `json:"-"` // Function to handle migration
	Metadata    map[string]interface{} `json:"metadata"`
}

// MigrateFeature migrates a feature from one tier to another
func MigrateFeature(ctx context.Context, migration FeatureMigration) error {
	// Validate transition
	transition := TierTransition{
		FromTier: migration.FromTier,
		ToTier:   migration.ToTier,
	}

	if err := ValidateTierTransition(transition); err != nil {
		return fmt.Errorf("invalid tier transition for feature migration: %w", err)
	}

	// Check if feature is available in target tier
	if !IsFeatureAvailableInTier(migration.ToTier, migration.Feature) {
		return fmt.Errorf("feature '%s' not available in target tier '%s'", migration.Feature, migration.ToTier)
	}

	// Execute migration if function provided
	if migration.MigrationFn != nil {
		if err := migration.MigrationFn(); err != nil {
			return fmt.Errorf("feature migration failed: %w", err)
		}
	}

	return nil
}

// Usage tracking for limits
type UsageTracker struct {
	UserID    string                 `json:"user_id"`
	Resource  string                 `json:"resource"`
	Usage     int                    `json:"usage"`
	Limit     int                    `json:"limit"`
	Timestamp int64                  `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// TrackUsage records usage for a specific resource
func TrackUsage(ctx context.Context, userID string, resource string, increment int) error {
	// TODO: Implement usage tracking in database
	// This would update usage counters for rate limiting and quota management
	return nil
}

// GetUsage returns current usage for a user and resource
func GetUsage(ctx context.Context, userID string, resource string) (*UsageTracker, error) {
	// TODO: Implement usage retrieval from database
	return &UsageTracker{
		UserID:   userID,
		Resource: resource,
		Usage:    0,
		Limit:    -1, // Unlimited
	}, nil
}
