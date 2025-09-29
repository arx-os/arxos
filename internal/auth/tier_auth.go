package auth

import (
	"context"
	"database/sql"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/database"
)

// Tier represents the three-tier ecosystem architecture
type Tier string

const (
	// Layer 1: FREE - Like Git
	TierCore Tier = "core"
	// Layer 2: FREEMIUM - Like GitHub Free
	TierHardware Tier = "hardware"
	// Layer 3: PAID - Like GitHub Pro
	TierWorkflow Tier = "workflow"
)

// TierInfo contains information about each tier
type TierInfo struct {
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Price        string                 `json:"price"`
	Features     []string               `json:"features"`
	Limits       map[string]interface{} `json:"limits"`
	APIEndpoints []string               `json:"api_endpoints"`
}

// GetTierInfo returns information about a specific tier
func GetTierInfo(tier Tier) TierInfo {
	switch tier {
	case TierCore:
		return TierInfo{
			Name:        "ArxOS Core",
			Description: "The 'Git' of buildings - free platform",
			Price:       "FREE",
			Features: []string{
				"Pure Go/TinyGo codebase",
				"Path-based architecture",
				"PostGIS spatial intelligence",
				"CLI commands",
				"Basic REST APIs",
				"Version control",
				"Hardware designs",
			},
			Limits: map[string]interface{}{
				"buildings":  -1, // unlimited
				"users":      5,
				"api_calls":  1000,
				"storage_gb": 10,
				"support":    "community",
			},
			APIEndpoints: []string{
				"/api/v1/buildings",
				"/api/v1/equipment",
				"/api/v1/spatial",
				"/api/v1/export",
				"/api/v1/import",
			},
		}

	case TierHardware:
		return TierInfo{
			Name:        "Hardware Platform",
			Description: "The 'GitHub Free' - IoT ecosystem",
			Price:       "FREEMIUM",
			Features: []string{
				"Certified hardware marketplace",
				"Device templates and SDK",
				"Gateway software",
				"Protocol translation",
				"Basic device management",
				"Community support",
			},
			Limits: map[string]interface{}{
				"certified_devices": 10,
				"marketplace_sales": 5,
				"support":           "community",
				"commission":        "5-10%",
			},
			APIEndpoints: []string{
				"/api/v1/hardware/devices",
				"/api/v1/hardware/templates",
				"/api/v1/hardware/gateway",
				"/api/v1/hardware/marketplace",
			},
		}

	case TierWorkflow:
		return TierInfo{
			Name:        "Workflow Automation",
			Description: "The 'GitHub Pro' - enterprise CMMS/CAFM platform",
			Price:       "PAID",
			Features: []string{
				"Visual workflow builder (n8n)",
				"CMMS/CAFM features",
				"Physical building automation",
				"Enterprise integrations",
				"Advanced analytics",
				"Professional support",
			},
			Limits: map[string]interface{}{
				"buildings":    -1, // unlimited
				"users":        -1, // unlimited
				"workflows":    -1, // unlimited
				"integrations": 400,
				"api_calls":    -1, // unlimited
				"storage_gb":   -1, // unlimited
				"support":      "professional",
				"sla":          "99.9%",
			},
			APIEndpoints: []string{
				"/api/v1/workflows",
				"/api/v1/automation",
				"/api/v1/cmmc",
				"/api/v1/analytics",
				"/api/v1/integrations",
				"/api/v1/enterprise",
			},
		}

	default:
		return TierInfo{}
	}
}

// TierAuthManager handles tier-based authentication and authorization
type TierAuthManager struct {
	db *database.PostGISDB
}

// NewTierAuthManager creates a new tier-based authentication manager
func NewTierAuthManager(db *database.PostGISDB) *TierAuthManager {
	return &TierAuthManager{
		db: db,
	}
}

// UserTierInfo contains user tier information
type UserTierInfo struct {
	UserID    string                 `json:"user_id"`
	Tier      Tier                   `json:"tier"`
	Status    string                 `json:"status"`
	StartedAt time.Time              `json:"started_at"`
	ExpiresAt *time.Time             `json:"expires_at,omitempty"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// TierLimits contains user tier limits
type TierLimits struct {
	UserID      string                 `json:"user_id"`
	Tier        Tier                   `json:"tier"`
	Limits      map[string]interface{} `json:"limits"`
	Usage       map[string]int         `json:"usage"`
	WithinLimit map[string]bool        `json:"within_limit"`
}

// GetUserTier retrieves user's current tier information
func (tam *TierAuthManager) GetUserTier(ctx context.Context, userID string) (Tier, error) {
	query := `
		SELECT tier 
		FROM user_tiers 
		WHERE user_id = $1 AND status = 'active'
		ORDER BY started_at DESC
		LIMIT 1
	`

	var tier string
	err := tam.db.QueryRow(ctx, query, userID).Scan(&tier)
	if err != nil {
		if err == sql.ErrNoRows {
			// Default to core tier if no tier found
			return TierCore, nil
		}
		return "", fmt.Errorf("failed to get user tier: %w", err)
	}

	return Tier(tier), nil
}

// GetUserTierInfo retrieves detailed user tier information
func (tam *TierAuthManager) GetUserTierInfo(ctx context.Context, userID string) (*UserTierInfo, error) {
	query := `
		SELECT ut.user_id, ut.tier, ut.status, ut.started_at, ut.expires_at, ut.metadata
		FROM user_tiers ut
		WHERE ut.user_id = $1 AND ut.status = 'active'
		ORDER BY ut.started_at DESC
		LIMIT 1
	`

	var tierInfo UserTierInfo
	err := tam.db.QueryRow(ctx, query, userID).Scan(
		&tierInfo.UserID,
		&tierInfo.Tier,
		&tierInfo.Status,
		&tierInfo.StartedAt,
		&tierInfo.ExpiresAt,
		&tierInfo.Metadata,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			// Return default core tier info
			return &UserTierInfo{
				UserID:    userID,
				Tier:      TierCore,
				Status:    "active",
				StartedAt: time.Now(),
				Metadata:  make(map[string]interface{}),
			}, nil
		}
		return nil, fmt.Errorf("failed to get user tier info: %w", err)
	}

	return &tierInfo, nil
}

// GetUserLimits retrieves user's tier limits and current usage
func (tam *TierAuthManager) GetUserLimits(ctx context.Context, userID string, tier Tier) (map[string]interface{}, error) {
	// Get tier limits from ecosystem_tiers table
	tierInfo := GetTierInfo(tier)
	limits := tierInfo.Limits

	// Get current usage from tier_usage table
	usageQuery := `
		SELECT resource, usage_count
		FROM tier_usage
		WHERE user_id = $1 AND tier = $2
		AND period_start >= date_trunc('month', NOW())
	`

	rows, err := tam.db.Query(ctx, usageQuery, userID, string(tier))
	if err != nil {
		return nil, fmt.Errorf("failed to get user usage: %w", err)
	}
	defer rows.Close()

	usage := make(map[string]int)
	for rows.Next() {
		var resource string
		var count int
		if err := rows.Scan(&resource, &count); err != nil {
			return nil, fmt.Errorf("failed to scan usage: %w", err)
		}
		usage[resource] = count
	}

	// Add usage information to limits
	limits["current_usage"] = usage

	return limits, nil
}

// SetUserTier sets a user's tier (for tier upgrades/downgrades)
func (tam *TierAuthManager) SetUserTier(ctx context.Context, userID string, tier Tier, metadata map[string]interface{}) error {
	// Validate tier transition
	currentTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get current tier: %w", err)
	}

	// Validate tier transition (simplified for now)
	if !isValidTierTransition(currentTier, tier) {
		return fmt.Errorf("invalid tier transition from %s to %s", currentTier, tier)
	}

	// Deactivate current tier
	deactivateQuery := `
		UPDATE user_tiers 
		SET status = 'inactive', updated_at = NOW()
		WHERE user_id = $1 AND status = 'active'
	`

	_, err = tam.db.Exec(ctx, deactivateQuery, userID)
	if err != nil {
		return fmt.Errorf("failed to deactivate current tier: %w", err)
	}

	// Set new tier
	insertQuery := `
		INSERT INTO user_tiers (user_id, tier, status, metadata, started_at, updated_at)
		VALUES ($1, $2, 'active', $3, NOW(), NOW())
		ON CONFLICT (user_id, tier) 
		DO UPDATE SET status = 'active', metadata = $3, started_at = NOW(), updated_at = NOW()
	`

	_, err = tam.db.Exec(ctx, insertQuery, userID, string(tier), metadata)
	if err != nil {
		return fmt.Errorf("failed to set user tier: %w", err)
	}

	return nil
}

// CheckTierAccess validates if a user has access to a specific tier
func (tam *TierAuthManager) CheckTierAccess(ctx context.Context, userID string, requiredTier Tier) error {
	userTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user tier: %w", err)
	}

	// Check if user's tier provides access to required tier
	if !tam.hasTierAccess(userTier, requiredTier) {
		return fmt.Errorf("user tier '%s' does not provide access to '%s'", userTier, requiredTier)
	}

	// Check if tier is still active (not expired)
	tierInfo, err := tam.GetUserTierInfo(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get tier info: %w", err)
	}

	if tierInfo.ExpiresAt != nil && time.Now().After(*tierInfo.ExpiresAt) {
		return fmt.Errorf("tier access expired")
	}

	return nil
}

// CheckFeatureAccess validates if a user can access a specific feature
func (tam *TierAuthManager) CheckFeatureAccess(ctx context.Context, userID string, feature string) error {
	userTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user tier: %w", err)
	}

	// Check if feature is available in user's tier
	if !isFeatureAvailableInTier(userTier, feature) {
		return fmt.Errorf("feature '%s' not available in tier '%s'", feature, userTier)
	}

	return nil
}

// CheckEndpointAccess validates if a user can access a specific API endpoint
func (tam *TierAuthManager) CheckEndpointAccess(ctx context.Context, userID string, endpoint string) error {
	userTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user tier: %w", err)
	}

	// Check if endpoint is available in user's tier
	if !isEndpointAvailableInTier(userTier, endpoint) {
		return fmt.Errorf("endpoint '%s' not available in tier '%s'", endpoint, userTier)
	}

	return nil
}

// CheckResourceLimit validates if a user is within their resource limits
func (tam *TierAuthManager) CheckResourceLimit(ctx context.Context, userID string, resource string, increment int) error {
	userTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user tier: %w", err)
	}

	// Get current usage
	usageQuery := `
		SELECT usage_count
		FROM tier_usage
		WHERE user_id = $1 AND tier = $2 AND resource = $3
		AND period_start >= date_trunc('month', NOW())
	`

	var currentUsage int
	err = tam.db.QueryRow(ctx, usageQuery, userID, string(userTier), resource).Scan(&currentUsage)
	if err != nil && err != sql.ErrNoRows {
		return fmt.Errorf("failed to get current usage: %w", err)
	}

	// Get tier limits
	limits, err := tam.GetUserLimits(ctx, userID, userTier)
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

	if currentUsage+increment > limitValue {
		return fmt.Errorf("resource limit exceeded for '%s': %d/%d", resource, currentUsage+increment, limitValue)
	}

	return nil
}

// TrackResourceUsage records resource usage for a user
func (tam *TierAuthManager) TrackResourceUsage(ctx context.Context, userID string, resource string, increment int) error {
	userTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user tier: %w", err)
	}

	// Insert or update usage
	upsertQuery := `
		INSERT INTO tier_usage (user_id, tier, resource, usage_count, period_start, period_end, updated_at)
		VALUES ($1, $2, $3, $4, date_trunc('month', NOW()), date_trunc('month', NOW()) + interval '1 month', NOW())
		ON CONFLICT (user_id, tier, resource, period_start)
		DO UPDATE SET 
			usage_count = tier_usage.usage_count + $4,
			updated_at = NOW()
	`

	_, err = tam.db.Exec(ctx, upsertQuery, userID, string(userTier), resource, increment)
	if err != nil {
		return fmt.Errorf("failed to track resource usage: %w", err)
	}

	return nil
}

// GetAvailableFeatures returns all features available to a user
func (tam *TierAuthManager) GetAvailableFeatures(ctx context.Context, userID string) ([]string, error) {
	userTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user tier: %w", err)
	}

	tierInfo := GetTierInfo(userTier)
	return tierInfo.Features, nil
}

// GetAvailableEndpoints returns all API endpoints available to a user
func (tam *TierAuthManager) GetAvailableEndpoints(ctx context.Context, userID string) ([]string, error) {
	userTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user tier: %w", err)
	}

	tierInfo := GetTierInfo(userTier)
	return tierInfo.APIEndpoints, nil
}

// GetTierLimits returns the limits for a user's tier
func (tam *TierAuthManager) GetTierLimits(ctx context.Context, userID string) (*TierLimits, error) {
	userTier, err := tam.GetUserTier(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user tier: %w", err)
	}

	limits, err := tam.GetUserLimits(ctx, userID, userTier)
	if err != nil {
		return nil, fmt.Errorf("failed to get user limits: %w", err)
	}

	// Extract usage and limits
	usage := make(map[string]int)
	withinLimit := make(map[string]bool)

	if usageData, exists := limits["current_usage"]; exists {
		if usageMap, ok := usageData.(map[string]int); ok {
			usage = usageMap
		}
	}

	// Calculate within_limit for each resource
	for resource, limit := range limits {
		if resource == "current_usage" {
			continue
		}

		limitValue, ok := limit.(int)
		if !ok {
			continue
		}

		currentUsage := usage[resource]
		withinLimit[resource] = limitValue == -1 || currentUsage < limitValue
	}

	return &TierLimits{
		UserID:      userID,
		Tier:        userTier,
		Limits:      limits,
		Usage:       usage,
		WithinLimit: withinLimit,
	}, nil
}

// Helper function to check if a tier provides access to another tier
func (tam *TierAuthManager) hasTierAccess(userTier, requiredTier Tier) bool {
	// Define tier hierarchy: core < hardware < workflow
	tierHierarchy := map[Tier]int{
		TierCore:     1,
		TierHardware: 2,
		TierWorkflow: 3,
	}

	userLevel, userExists := tierHierarchy[userTier]
	requiredLevel, requiredExists := tierHierarchy[requiredTier]

	if !userExists || !requiredExists {
		return false
	}

	// User can access their tier or lower tiers
	return userLevel >= requiredLevel
}

// Helper function to validate tier transitions
func isValidTierTransition(fromTier, toTier Tier) bool {
	// Allow any transition for now (can be restricted later)
	return true
}

// Helper function to check if a feature is available in a tier
func isFeatureAvailableInTier(tier Tier, feature string) bool {
	tierInfo := GetTierInfo(tier)
	for _, tierFeature := range tierInfo.Features {
		if tierFeature == feature {
			return true
		}
	}
	return false
}

// Helper function to check if an endpoint is available in a tier
func isEndpointAvailableInTier(tier Tier, endpoint string) bool {
	tierInfo := GetTierInfo(tier)
	for _, tierEndpoint := range tierInfo.APIEndpoints {
		if tierEndpoint == endpoint {
			return true
		}
	}
	return false
}

// Tier-based authentication middleware
type TierAuthMiddleware struct {
	authManager *TierAuthManager
}

// NewTierAuthMiddleware creates a new tier-based authentication middleware
func NewTierAuthMiddleware(authManager *TierAuthManager) *TierAuthMiddleware {
	return &TierAuthMiddleware{
		authManager: authManager,
	}
}

// RequireTier creates middleware that requires a specific tier
func (tam *TierAuthMiddleware) RequireTier(requiredTier Tier) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract user ID from context (set by previous auth middleware)
			userID := r.Context().Value("user_id")
			if userID == nil {
				http.Error(w, "Authentication required", http.StatusUnauthorized)
				return
			}

			// Check tier access
			err := tam.authManager.CheckTierAccess(r.Context(), userID.(string), requiredTier)
			if err != nil {
				http.Error(w, "Insufficient tier access", http.StatusForbidden)
				return
			}

			// Add tier to context
			ctx := r.Context()
			ctx = context.WithValue(ctx, "user_tier", requiredTier)
			r = r.WithContext(ctx)

			next.ServeHTTP(w, r)
		})
	}
}

// RequireFeature creates middleware that requires a specific feature
func (tam *TierAuthMiddleware) RequireFeature(feature string) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract user ID from context
			userID := r.Context().Value("user_id")
			if userID == nil {
				http.Error(w, "Authentication required", http.StatusUnauthorized)
				return
			}

			// Check feature access
			err := tam.authManager.CheckFeatureAccess(r.Context(), userID.(string), feature)
			if err != nil {
				http.Error(w, "Feature not available", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// TrackUsage creates middleware that tracks resource usage
func (tam *TierAuthMiddleware) TrackUsage(resource string, increment int) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract user ID from context
			userID := r.Context().Value("user_id")
			if userID != nil {
				// Check limit before tracking
				err := tam.authManager.CheckResourceLimit(r.Context(), userID.(string), resource, increment)
				if err != nil {
					http.Error(w, "Resource limit exceeded", http.StatusTooManyRequests)
					return
				}

				// Track usage
				err = tam.authManager.TrackResourceUsage(r.Context(), userID.(string), resource, increment)
				if err != nil {
					// Log error but don't fail the request
					fmt.Printf("Failed to track usage: %v\n", err)
				}
			}

			next.ServeHTTP(w, r)
		})
	}
}
