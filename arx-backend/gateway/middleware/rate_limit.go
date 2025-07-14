package middleware

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	"go.uber.org/zap"
	"golang.org/x/time/rate"
)

// RateLimitMiddleware handles rate limiting
type RateLimitMiddleware struct {
	config   RateLimitConfig
	logger   *zap.Logger
	limiters map[string]*rate.Limiter
	mu       sync.RWMutex
}

// RateLimitConfig defines rate limiting configuration
type RateLimitConfig struct {
	RequestsPerSecond int      `yaml:"requests_per_second"`
	Burst             int      `yaml:"burst"`
	PerUser           bool     `yaml:"per_user"`
	PerService        bool     `yaml:"per_service"`
	SkipPaths         []string `yaml:"skip_paths"`
	BypassRoles       []string `yaml:"bypass_roles"`
}

// NewRateLimitMiddleware creates a new rate limiting middleware
func NewRateLimitMiddleware(config RateLimitConfig) (*RateLimitMiddleware, error) {
	if config.RequestsPerSecond <= 0 {
		return nil, fmt.Errorf("requests per second must be positive")
	}

	if config.Burst <= 0 {
		return nil, fmt.Errorf("burst must be positive")
	}

	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	middleware := &RateLimitMiddleware{
		config:   config,
		logger:   logger,
		limiters: make(map[string]*rate.Limiter),
	}

	return middleware, nil
}

// Middleware returns the rate limiting middleware function
func (rl *RateLimitMiddleware) Middleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if path should skip rate limiting
			if rl.shouldSkipRateLimit(r.URL.Path) {
				next.ServeHTTP(w, r)
				return
			}

			// Get rate limiter key
			key := rl.getRateLimitKey(r)
			if key == "" {
				// No key found, skip rate limiting
				next.ServeHTTP(w, r)
				return
			}

			// Get or create rate limiter
			limiter := rl.getLimiter(key)
			if limiter == nil {
				http.Error(w, "Rate limit error", http.StatusInternalServerError)
				return
			}

			// Check rate limit
			if !limiter.Allow() {
				rl.logger.Warn("Rate limit exceeded",
					zap.String("key", key),
					zap.String("path", r.URL.Path),
					zap.String("remote_addr", r.RemoteAddr),
				)

				w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", rl.config.RequestsPerSecond))
				w.Header().Set("X-RateLimit-Remaining", "0")
				w.Header().Set("X-RateLimit-Reset", fmt.Sprintf("%d", time.Now().Add(time.Second).Unix()))
				http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
				return
			}

			// Add rate limit headers
			w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", rl.config.RequestsPerSecond))
			w.Header().Set("X-RateLimit-Remaining", fmt.Sprintf("%d", int(limiter.TokensAt(time.Now()))))
			w.Header().Set("X-RateLimit-Reset", fmt.Sprintf("%d", time.Now().Add(time.Second).Unix()))

			next.ServeHTTP(w, r)
		})
	}
}

// shouldSkipRateLimit checks if the path should skip rate limiting
func (rl *RateLimitMiddleware) shouldSkipRateLimit(path string) bool {
	for _, skipPath := range rl.config.SkipPaths {
		if path == skipPath {
			return true
		}
	}
	return false
}

// getRateLimitKey generates a rate limit key based on configuration
func (rl *RateLimitMiddleware) getRateLimitKey(r *http.Request) string {
	var keys []string

	// Add service-based key if enabled
	if rl.config.PerService {
		service := r.Header.Get("X-Gateway-Service")
		if service != "" {
			keys = append(keys, "service:"+service)
		}
	}

	// Add user-based key if enabled
	if rl.config.PerUser {
		// Try to get user from context (set by auth middleware)
		if user, ok := GetUserFromContext(r.Context()); ok {
			keys = append(keys, "user:"+user.UserID)
		} else {
			// Fallback to IP address
			keys = append(keys, "ip:"+r.RemoteAddr)
		}
	}

	// If no specific keys, use global
	if len(keys) == 0 {
		keys = append(keys, "global")
	}

	// Join keys with separator
	if len(keys) == 1 {
		return keys[0]
	}

	// For multiple keys, create a combined key
	combined := ""
	for i, key := range keys {
		if i > 0 {
			combined += "|"
		}
		combined += key
	}
	return combined
}

// getLimiter gets or creates a rate limiter for the given key
func (rl *RateLimitMiddleware) getLimiter(key string) *rate.Limiter {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, exists := rl.limiters[key]
	if !exists {
		limiter = rate.NewLimiter(rate.Limit(rl.config.RequestsPerSecond), rl.config.Burst)
		rl.limiters[key] = limiter
	}

	return limiter
}

// UpdateConfig updates the rate limiting configuration
func (rl *RateLimitMiddleware) UpdateConfig(config RateLimitConfig) error {
	if config.RequestsPerSecond <= 0 {
		return fmt.Errorf("requests per second must be positive")
	}

	if config.Burst <= 0 {
		return fmt.Errorf("burst must be positive")
	}

	rl.mu.Lock()
	defer rl.mu.Unlock()

	// Clear existing limiters when config changes
	rl.limiters = make(map[string]*rate.Limiter)
	rl.config = config

	rl.logger.Info("Rate limiting configuration updated",
		zap.Int("requests_per_second", config.RequestsPerSecond),
		zap.Int("burst", config.Burst),
		zap.Bool("per_user", config.PerUser),
		zap.Bool("per_service", config.PerService),
	)

	return nil
}

// GetStats returns rate limiting statistics
func (rl *RateLimitMiddleware) GetStats() map[string]interface{} {
	rl.mu.RLock()
	defer rl.mu.RUnlock()

	stats := make(map[string]interface{})
	for key, limiter := range rl.limiters {
		stats[key] = map[string]interface{}{
			"tokens_at": limiter.TokensAt(time.Now()),
			"limit":     rl.config.RequestsPerSecond,
			"burst":     rl.config.Burst,
		}
	}

	return stats
}

// ResetStats resets all rate limiters
func (rl *RateLimitMiddleware) ResetStats() {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	rl.limiters = make(map[string]*rate.Limiter)
	rl.logger.Info("Rate limiting statistics reset")
}
