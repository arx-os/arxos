package middleware

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
	"golang.org/x/time/rate"
	"gorm.io/datatypes"
)

// RateLimitTier represents different rate limiting tiers
type RateLimitTier string

const (
	TierAnonymous  RateLimitTier = "anonymous"
	TierFree       RateLimitTier = "free"
	TierPro        RateLimitTier = "pro"
	TierEnterprise RateLimitTier = "enterprise"
	TierAdmin      RateLimitTier = "admin"
)

// RateLimitConfig defines rate limits for different tiers
type RateLimitConfig struct {
	RequestsPerMinute int
	Burst             int
	UploadMB          int    // Max upload size in MB
	APICallsPerDay    int    // Daily API call limit
	WebSocketConns    int    // Max concurrent WebSocket connections
	BuildingQuota     int    // Max buildings allowed
	StorageGB         int    // Max storage in GB
	Description       string // Tier description
}

// TierConfigs defines rate limits for each tier
var TierConfigs = map[RateLimitTier]RateLimitConfig{
	TierAnonymous: {
		RequestsPerMinute: 10,
		Burst:             5,
		UploadMB:          0, // No uploads for anonymous
		APICallsPerDay:    100,
		WebSocketConns:    0, // No WebSocket for anonymous
		BuildingQuota:     0,
		StorageGB:         0,
		Description:       "Anonymous users - limited read-only access",
	},
	TierFree: {
		RequestsPerMinute: 60,
		Burst:             20,
		UploadMB:          50,
		APICallsPerDay:    1000,
		WebSocketConns:    2,
		BuildingQuota:     3,
		StorageGB:         5,
		Description:       "Free tier - basic access",
	},
	TierPro: {
		RequestsPerMinute: 300,
		Burst:             100,
		UploadMB:          500,
		APICallsPerDay:    10000,
		WebSocketConns:    10,
		BuildingQuota:     50,
		StorageGB:         100,
		Description:       "Pro tier - enhanced capabilities",
	},
	TierEnterprise: {
		RequestsPerMinute: 1000,
		Burst:             500,
		UploadMB:          2000,
		APICallsPerDay:    100000,
		WebSocketConns:    100,
		BuildingQuota:     -1, // Unlimited
		StorageGB:         1000,
		Description:       "Enterprise tier - maximum performance",
	},
	TierAdmin: {
		RequestsPerMinute: -1, // Unlimited
		Burst:             -1,
		UploadMB:          -1,
		APICallsPerDay:    -1,
		WebSocketConns:    -1,
		BuildingQuota:     -1,
		StorageGB:         -1,
		Description:       "Admin tier - unlimited access",
	},
}

// EndpointLimits defines specific limits for critical endpoints
var EndpointLimits = map[string]map[RateLimitTier]int{
	"/api/auth/login": {
		TierAnonymous:  5,  // 5 attempts per minute
		TierFree:       10,
		TierPro:        20,
		TierEnterprise: 50,
		TierAdmin:      -1,
	},
	"/api/auth/register": {
		TierAnonymous:  2, // 2 registrations per minute
		TierFree:       5,
		TierPro:        10,
		TierEnterprise: 50,
		TierAdmin:      -1,
	},
	"/api/buildings/upload": {
		TierAnonymous:  0, // No uploads
		TierFree:       5,
		TierPro:        20,
		TierEnterprise: 100,
		TierAdmin:      -1,
	},
	"/api/ai/detect": {
		TierAnonymous:  0, // No AI access
		TierFree:       10,
		TierPro:        100,
		TierEnterprise: 1000,
		TierAdmin:      -1,
	},
}

// RateLimiter manages rate limiting for all users
type RateLimiter struct {
	limiters   map[string]*UserLimiter
	mu         sync.RWMutex
	cleanupTTL time.Duration
}

// UserLimiter holds rate limiters for a specific user
type UserLimiter struct {
	Tier           RateLimitTier
	GeneralLimiter *rate.Limiter
	EndpointLimiters map[string]*rate.Limiter
	DailyCounter   *DailyCounter
	LastAccess     time.Time
	WebSocketCount int
	mu             sync.Mutex
}

// DailyCounter tracks daily API usage
type DailyCounter struct {
	Count     int
	ResetTime time.Time
	mu        sync.Mutex
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter() *RateLimiter {
	rl := &RateLimiter{
		limiters:   make(map[string]*UserLimiter),
		cleanupTTL: 1 * time.Hour,
	}

	// Start cleanup goroutine
	go rl.cleanup()

	return rl
}

// cleanup removes inactive limiters
func (rl *RateLimiter) cleanup() {
	ticker := time.NewTicker(30 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		rl.mu.Lock()
		now := time.Now()
		for key, limiter := range rl.limiters {
			if now.Sub(limiter.LastAccess) > rl.cleanupTTL {
				delete(rl.limiters, key)
			}
		}
		rl.mu.Unlock()
	}
}

// GetUserTier determines the user's rate limit tier
func GetUserTier(ctx context.Context) RateLimitTier {
	// Check if user is authenticated
	userID := ctx.Value("user_id")
	if userID == nil {
		return TierAnonymous
	}

	// Get user from database
	var user models.User
	if err := db.GormDB.Where("id = ?", userID).First(&user).Error; err != nil {
		return TierFree // Default to free if user not found
	}

	// Check admin status
	if user.IsAdmin {
		return TierAdmin
	}

	// Check subscription tier
	switch user.SubscriptionTier {
	case "pro":
		return TierPro
	case "enterprise":
		return TierEnterprise
	case "free":
		return TierFree
	default:
		return TierFree
	}
}

// getLimiter gets or creates a limiter for a user
func (rl *RateLimiter) getLimiter(identifier string, tier RateLimitTier) *UserLimiter {
	rl.mu.RLock()
	limiter, exists := rl.limiters[identifier]
	rl.mu.RUnlock()

	if exists {
		limiter.LastAccess = time.Now()
		return limiter
	}

	// Create new limiter
	rl.mu.Lock()
	defer rl.mu.Unlock()

	// Double-check after acquiring write lock
	if limiter, exists = rl.limiters[identifier]; exists {
		return limiter
	}

	config := TierConfigs[tier]

	// Create general limiter
	var generalLimiter *rate.Limiter
	if config.RequestsPerMinute > 0 {
		generalLimiter = rate.NewLimiter(
			rate.Limit(float64(config.RequestsPerMinute)/60.0),
			config.Burst,
		)
	} else if config.RequestsPerMinute < 0 {
		// Unlimited
		generalLimiter = rate.NewLimiter(rate.Inf, 0)
	} else {
		// Zero means no access
		generalLimiter = rate.NewLimiter(0, 0)
	}

	limiter = &UserLimiter{
		Tier:             tier,
		GeneralLimiter:   generalLimiter,
		EndpointLimiters: make(map[string]*rate.Limiter),
		DailyCounter: &DailyCounter{
			ResetTime: time.Now().Add(24 * time.Hour),
		},
		LastAccess: time.Now(),
	}

	rl.limiters[identifier] = limiter
	return limiter
}

// RateLimitMiddleware applies rate limiting based on user tier
func RateLimitMiddleware(next http.Handler) http.Handler {
	rl := NewRateLimiter()

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get user tier
		tier := GetUserTier(r.Context())

		// Get identifier (user ID or IP for anonymous)
		identifier := getUserIdentifier(r)

		// Get limiter for user
		userLimiter := rl.getLimiter(identifier, tier)

		// Check endpoint-specific limits
		if !checkEndpointLimit(userLimiter, r.URL.Path, tier) {
			handleRateLimitExceeded(w, r, tier, "endpoint")
			return
		}

		// Check general rate limit
		if !userLimiter.GeneralLimiter.Allow() {
			handleRateLimitExceeded(w, r, tier, "general")
			return
		}

		// Check daily API limit
		config := TierConfigs[tier]
		if config.APICallsPerDay > 0 {
			if !userLimiter.DailyCounter.Check(config.APICallsPerDay) {
				handleRateLimitExceeded(w, r, tier, "daily")
				return
			}
		}

		// Add rate limit headers
		addRateLimitHeaders(w, userLimiter, tier)

		// Log API usage for analytics
		logAPIUsage(r, identifier, tier)

		next.ServeHTTP(w, r)
	})
}

// checkEndpointLimit checks endpoint-specific rate limits
func checkEndpointLimit(limiter *UserLimiter, path string, tier RateLimitTier) bool {
	limits, exists := EndpointLimits[path]
	if !exists {
		return true // No specific limit for this endpoint
	}

	limit, exists := limits[tier]
	if !exists || limit < 0 {
		return true // No limit or unlimited for this tier
	}

	if limit == 0 {
		return false // No access to this endpoint
	}

	// Get or create endpoint limiter
	limiter.mu.Lock()
	endpointLimiter, exists := limiter.EndpointLimiters[path]
	if !exists {
		endpointLimiter = rate.NewLimiter(
			rate.Limit(float64(limit)/60.0),
			limit/10, // Burst is 10% of limit
		)
		limiter.EndpointLimiters[path] = endpointLimiter
	}
	limiter.mu.Unlock()

	return endpointLimiter.Allow()
}

// Check increments and checks the daily counter
func (dc *DailyCounter) Check(limit int) bool {
	dc.mu.Lock()
	defer dc.mu.Unlock()

	// Reset if day has passed
	if time.Now().After(dc.ResetTime) {
		dc.Count = 0
		dc.ResetTime = time.Now().Add(24 * time.Hour)
	}

	if dc.Count >= limit {
		return false
	}

	dc.Count++
	return true
}

// getUserIdentifier gets a unique identifier for rate limiting
func getUserIdentifier(r *http.Request) string {
	// Try to get user ID from context
	if userID := r.Context().Value("user_id"); userID != nil {
		return fmt.Sprintf("user:%v", userID)
	}

	// Use IP address for anonymous users
	ip := r.Header.Get("X-Real-IP")
	if ip == "" {
		ip = r.Header.Get("X-Forwarded-For")
	}
	if ip == "" {
		ip = r.RemoteAddr
	}

	return fmt.Sprintf("ip:%s", ip)
}

// handleRateLimitExceeded handles rate limit exceeded responses
func handleRateLimitExceeded(w http.ResponseWriter, r *http.Request, tier RateLimitTier, limitType string) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-RateLimit-Tier", string(tier))
	w.Header().Set("X-RateLimit-Type", limitType)
	w.WriteHeader(http.StatusTooManyRequests)

	response := map[string]interface{}{
		"error": "Rate limit exceeded",
		"tier":  tier,
		"type":  limitType,
	}

	// Add specific messages based on limit type
	switch limitType {
	case "endpoint":
		response["message"] = "Too many requests to this endpoint. Please wait before trying again."
	case "daily":
		response["message"] = "Daily API limit reached. Limit resets at midnight UTC."
		response["upgrade_url"] = "/pricing"
	case "general":
		response["message"] = "Too many requests. Please slow down."
	}

	// Log rate limit violation
	logSecurityAlert(r, "rate_limit_exceeded", map[string]interface{}{
		"tier":       tier,
		"limit_type": limitType,
		"path":       r.URL.Path,
	})

	json.NewEncoder(w).Encode(response)
}

// addRateLimitHeaders adds rate limit information headers
func addRateLimitHeaders(w http.ResponseWriter, limiter *UserLimiter, tier RateLimitTier) {
	config := TierConfigs[tier]

	w.Header().Set("X-RateLimit-Tier", string(tier))

	if config.RequestsPerMinute > 0 {
		w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", config.RequestsPerMinute))

		// Get remaining tokens (approximate)
		tokens := int(limiter.GeneralLimiter.Tokens())
		w.Header().Set("X-RateLimit-Remaining", fmt.Sprintf("%d", tokens))
	}

	if config.APICallsPerDay > 0 {
		remaining := config.APICallsPerDay - limiter.DailyCounter.Count
		w.Header().Set("X-RateLimit-Daily-Remaining", fmt.Sprintf("%d", remaining))
		w.Header().Set("X-RateLimit-Reset", limiter.DailyCounter.ResetTime.Format(time.RFC3339))
	}
}

// WebSocketRateLimiter checks WebSocket connection limits
func WebSocketRateLimiter(identifier string, tier RateLimitTier) error {
	config := TierConfigs[tier]

	if config.WebSocketConns == 0 {
		return fmt.Errorf("WebSocket connections not allowed for tier %s", tier)
	}

	if config.WebSocketConns < 0 {
		return nil // Unlimited
	}

	// This would need to track active WebSocket connections
	// Implementation depends on WebSocket server setup
	return nil
}

// CheckUploadSize validates upload size against tier limits
func CheckUploadSize(r *http.Request, tier RateLimitTier) error {
	config := TierConfigs[tier]

	if config.UploadMB == 0 {
		return fmt.Errorf("uploads not allowed for tier %s", tier)
	}

	if config.UploadMB < 0 {
		return nil // Unlimited
	}

	// Check Content-Length header
	contentLength := r.ContentLength
	maxBytes := int64(config.UploadMB) * 1024 * 1024

	if contentLength > maxBytes {
		return fmt.Errorf("upload size %d exceeds limit of %d MB for tier %s",
			contentLength, config.UploadMB, tier)
	}

	return nil
}

// logAPIUsage logs API usage for analytics and billing
func logAPIUsage(r *http.Request, identifier string, tier RateLimitTier) {
	// This would log to database or analytics service
	usage := models.APIUsage{
		Identifier: identifier,
		Tier:       string(tier),
		Endpoint:   r.URL.Path,
		Method:     r.Method,
		Timestamp:  time.Now(),
		IP:         r.RemoteAddr,
		UserAgent:  r.UserAgent(),
	}

	// Async logging to avoid blocking
	go func() {
		db.GormDB.Create(&usage)
	}()
}

// logSecurityAlert logs security-related events for rate limiting
func logSecurityAlert(r *http.Request, alertType string, details map[string]interface{}) {
	// Log to security monitoring system
	go func() {
		detailsJSON, _ := json.Marshal(details)
		alert := models.SecurityAlert{
			AlertType: alertType,
			Severity:  "medium",
			IPAddress: r.RemoteAddr,
			UserAgent: r.UserAgent(),
			Path:      r.URL.Path,
			Method:    r.Method,
			Details:   datatypes.JSON(detailsJSON),
			CreatedAt: time.Now(),
		}
		db.GormDB.Create(&alert)
	}()
}

// GetTierUsageStats returns usage statistics for a user
func GetTierUsageStats(userID uint) (map[string]interface{}, error) {
	var user models.User
	if err := db.GormDB.Where("id = ?", userID).First(&user).Error; err != nil {
		return nil, err
	}

	tier := TierFree
	if user.IsAdmin {
		tier = TierAdmin
	} else if user.SubscriptionTier != "" {
		tier = RateLimitTier(user.SubscriptionTier)
	}

	config := TierConfigs[tier]

	// Get current usage from database
	var dailyUsage int64
	today := time.Now().Truncate(24 * time.Hour)
	db.GormDB.Model(&models.APIUsage{}).
		Where("identifier = ? AND timestamp >= ?", fmt.Sprintf("user:%d", userID), today).
		Count(&dailyUsage)

	// Get storage usage
	var storageUsed int64
	db.GormDB.Model(&models.Building{}).
		Where("user_id = ?", userID).
		Select("COALESCE(SUM(file_size), 0)").
		Scan(&storageUsed)

	// Get building count
	var buildingCount int64
	db.GormDB.Model(&models.Building{}).
		Where("user_id = ?", userID).
		Count(&buildingCount)

	return map[string]interface{}{
		"tier":                tier,
		"tier_description":    config.Description,
		"requests_per_minute": config.RequestsPerMinute,
		"daily_api_limit":     config.APICallsPerDay,
		"daily_api_used":      dailyUsage,
		"upload_limit_mb":     config.UploadMB,
		"building_quota":      config.BuildingQuota,
		"buildings_used":      buildingCount,
		"storage_limit_gb":    config.StorageGB,
		"storage_used_gb":     float64(storageUsed) / (1024 * 1024 * 1024),
		"websocket_limit":     config.WebSocketConns,
	}, nil
}
