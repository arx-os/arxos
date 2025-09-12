package middleware

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	"golang.org/x/time/rate"
)

// RateLimiter provides rate limiting functionality
type RateLimiter struct {
	visitors map[string]*visitor
	mu       sync.RWMutex
	rate     rate.Limit
	burst    int
	cleanup  *time.Ticker
}

// visitor tracks rate limit state for each client
type visitor struct {
	limiter  *rate.Limiter
	lastSeen time.Time
}

// NewRateLimiter creates a new rate limiter
// rps: requests per second allowed
// burst: maximum burst size
func NewRateLimiter(rps float64, burst int) *RateLimiter {
	rl := &RateLimiter{
		visitors: make(map[string]*visitor),
		rate:     rate.Limit(rps),
		burst:    burst,
		cleanup:  time.NewTicker(1 * time.Minute),
	}

	// Start cleanup goroutine
	go rl.cleanupVisitors()

	return rl
}

// Middleware returns the rate limiting middleware handler
func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get client identifier (IP address)
		clientID := rl.getClientID(r)
		
		// Get or create visitor
		limiter := rl.getVisitor(clientID)
		
		// Check rate limit
		if !limiter.Allow() {
			rl.handleRateLimitExceeded(w, r)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// MiddlewareWithCustomLimits creates middleware with custom limits for specific paths
func (rl *RateLimiter) MiddlewareWithCustomLimits(pathLimits map[string]RateLimit) func(http.Handler) http.Handler {
	// Create per-path rate limiters
	pathLimiters := make(map[string]*RateLimiter)
	for path, limit := range pathLimits {
		pathLimiters[path] = NewRateLimiter(limit.RPS, limit.Burst)
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if path has custom limit
			for path, limiter := range pathLimiters {
				if r.URL.Path == path || (len(path) > 0 && path[len(path)-1] == '/' && 
					len(r.URL.Path) >= len(path) && r.URL.Path[:len(path)] == path) {
					limiter.Middleware(next).ServeHTTP(w, r)
					return
				}
			}

			// Use default rate limiter
			rl.Middleware(next).ServeHTTP(w, r)
		})
	}
}

// getClientID extracts client identifier from request
func (rl *RateLimiter) getClientID(r *http.Request) string {
	// Try to get real IP from headers (for reverse proxy scenarios)
	if ip := r.Header.Get("X-Forwarded-For"); ip != "" {
		return ip
	}
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}
	
	// Fall back to remote address
	return r.RemoteAddr
}

// getVisitor retrieves or creates a visitor's rate limiter
func (rl *RateLimiter) getVisitor(clientID string) *rate.Limiter {
	rl.mu.RLock()
	v, exists := rl.visitors[clientID]
	rl.mu.RUnlock()

	if !exists {
		limiter := rate.NewLimiter(rl.rate, rl.burst)
		rl.mu.Lock()
		rl.visitors[clientID] = &visitor{
			limiter:  limiter,
			lastSeen: time.Now(),
		}
		rl.mu.Unlock()
		return limiter
	}

	// Update last seen time
	rl.mu.Lock()
	v.lastSeen = time.Now()
	rl.mu.Unlock()

	return v.limiter
}

// cleanupVisitors removes old entries from the visitors map
func (rl *RateLimiter) cleanupVisitors() {
	for range rl.cleanup.C {
		rl.mu.Lock()
		for id, v := range rl.visitors {
			if time.Since(v.lastSeen) > 3*time.Minute {
				delete(rl.visitors, id)
			}
		}
		rl.mu.Unlock()
	}
}

// handleRateLimitExceeded sends appropriate response when rate limit is exceeded
func (rl *RateLimiter) handleRateLimitExceeded(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%v", rl.burst))
	w.Header().Set("X-RateLimit-Remaining", "0")
	w.Header().Set("X-RateLimit-Reset", fmt.Sprintf("%d", time.Now().Add(time.Second).Unix()))
	w.Header().Set("Retry-After", "1")
	
	w.WriteHeader(http.StatusTooManyRequests)
	w.Write([]byte(`{"error":"Rate limit exceeded. Please try again later."}`))
}

// Stop stops the cleanup goroutine
func (rl *RateLimiter) Stop() {
	rl.cleanup.Stop()
}

// RateLimit defines rate limiting parameters
type RateLimit struct {
	RPS   float64 // Requests per second
	Burst int     // Maximum burst size
}

// DefaultRateLimits provides sensible defaults for different endpoints
var DefaultRateLimits = map[string]RateLimit{
	"/api/v1/auth/login":    {RPS: 5, Burst: 10},   // Strict limit for login
	"/api/v1/auth/register": {RPS: 2, Burst: 5},    // Strict limit for registration
	"/api/v1/auth/refresh":  {RPS: 10, Burst: 20},  // Moderate limit for refresh
	"/api/v1/upload/":       {RPS: 1, Burst: 3},    // Strict limit for uploads
	"/api/v1/":              {RPS: 100, Burst: 200}, // General API limit
	"/health":               {RPS: 1000, Burst: 1000}, // High limit for health checks
}

// IPBasedRateLimiter provides more sophisticated rate limiting with IP reputation
type IPBasedRateLimiter struct {
	*RateLimiter
	blacklist   map[string]time.Time
	blacklistMu sync.RWMutex
	reputation  map[string]int // Track reputation score
	reputationMu sync.RWMutex
}

// NewIPBasedRateLimiter creates an IP-based rate limiter with reputation tracking
func NewIPBasedRateLimiter(rps float64, burst int) *IPBasedRateLimiter {
	return &IPBasedRateLimiter{
		RateLimiter: NewRateLimiter(rps, burst),
		blacklist:   make(map[string]time.Time),
		reputation:  make(map[string]int),
	}
}

// Middleware returns the IP-based rate limiting middleware
func (irl *IPBasedRateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		clientID := irl.getClientID(r)
		
		// Check if IP is blacklisted
		if irl.isBlacklisted(clientID) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte(`{"error":"Access denied"}`))
			return
		}

		// Check rate limit with reputation adjustment
		limiter := irl.getVisitorWithReputation(clientID)
		if !limiter.Allow() {
			// Decrease reputation on rate limit violation
			irl.decreaseReputation(clientID)
			
			// Auto-blacklist if reputation is too low
			if irl.getReputation(clientID) < -10 {
				irl.blacklistIP(clientID, 1*time.Hour)
			}
			
			irl.handleRateLimitExceeded(w, r)
			return
		}

		// Increase reputation for good behavior
		irl.increaseReputation(clientID)
		
		next.ServeHTTP(w, r)
	})
}

// getVisitorWithReputation adjusts rate limit based on IP reputation
func (irl *IPBasedRateLimiter) getVisitorWithReputation(clientID string) *rate.Limiter {
	reputation := irl.getReputation(clientID)
	
	// Adjust rate based on reputation
	adjustedRate := irl.rate
	adjustedBurst := irl.burst
	
	if reputation < 0 {
		// Reduce rate for bad reputation
		adjustedRate = adjustedRate / 2
		adjustedBurst = adjustedBurst / 2
	} else if reputation > 10 {
		// Slightly increase rate for good reputation
		adjustedRate = adjustedRate * 1.5
		adjustedBurst = int(float64(adjustedBurst) * 1.5)
	}
	
	irl.mu.RLock()
	v, exists := irl.visitors[clientID]
	irl.mu.RUnlock()

	if !exists {
		limiter := rate.NewLimiter(adjustedRate, adjustedBurst)
		irl.mu.Lock()
		irl.visitors[clientID] = &visitor{
			limiter:  limiter,
			lastSeen: time.Now(),
		}
		irl.mu.Unlock()
		return limiter
	}

	irl.mu.Lock()
	v.lastSeen = time.Now()
	irl.mu.Unlock()

	return v.limiter
}

// isBlacklisted checks if an IP is blacklisted
func (irl *IPBasedRateLimiter) isBlacklisted(clientID string) bool {
	irl.blacklistMu.RLock()
	defer irl.blacklistMu.RUnlock()
	
	if expiry, exists := irl.blacklist[clientID]; exists {
		if time.Now().Before(expiry) {
			return true
		}
		// Remove expired blacklist entry
		delete(irl.blacklist, clientID)
	}
	return false
}

// blacklistIP adds an IP to the blacklist
func (irl *IPBasedRateLimiter) blacklistIP(clientID string, duration time.Duration) {
	irl.blacklistMu.Lock()
	defer irl.blacklistMu.Unlock()
	irl.blacklist[clientID] = time.Now().Add(duration)
}

// getReputation returns the reputation score for an IP
func (irl *IPBasedRateLimiter) getReputation(clientID string) int {
	irl.reputationMu.RLock()
	defer irl.reputationMu.RUnlock()
	return irl.reputation[clientID]
}

// increaseReputation improves IP reputation
func (irl *IPBasedRateLimiter) increaseReputation(clientID string) {
	irl.reputationMu.Lock()
	defer irl.reputationMu.Unlock()
	
	if irl.reputation[clientID] < 100 {
		irl.reputation[clientID]++
	}
}

// decreaseReputation reduces IP reputation
func (irl *IPBasedRateLimiter) decreaseReputation(clientID string) {
	irl.reputationMu.Lock()
	defer irl.reputationMu.Unlock()
	
	irl.reputation[clientID]--
}