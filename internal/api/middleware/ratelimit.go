package middleware

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// RateLimiter provides rate limiting functionality
type RateLimiter struct {
	requests    map[string][]time.Time
	mu          sync.RWMutex
	limit       int
	window      time.Duration
	cleanupTick time.Duration
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
	rl := &RateLimiter{
		requests:    make(map[string][]time.Time),
		limit:       limit,
		window:      window,
		cleanupTick: window / 2, // Clean up every half window
	}

	// Start cleanup goroutine
	go rl.cleanup()

	return rl
}

// RateLimitMiddleware provides rate limiting based on client IP
func (rl *RateLimiter) RateLimitMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		clientID := rl.getClientID(r)

		if !rl.Allow(clientID) {
			logger.Warn("Rate limit exceeded for client: %s", clientID)
			rl.respondRateLimited(w)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// UserRateLimitMiddleware provides rate limiting based on user ID
func (rl *RateLimiter) UserRateLimitMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get user ID from context
		userID, ok := r.Context().Value("user_id").(string)
		if !ok {
			// Fall back to IP-based rate limiting
			clientID := rl.getClientID(r)
			if !rl.Allow(clientID) {
				logger.Warn("Rate limit exceeded for client: %s", clientID)
				rl.respondRateLimited(w)
				return
			}
		} else {
			// Use user-based rate limiting
			if !rl.Allow(userID) {
				logger.Warn("Rate limit exceeded for user: %s", userID)
				rl.respondRateLimited(w)
				return
			}
		}

		next.ServeHTTP(w, r)
	})
}

// Allow checks if a request is allowed for the given client
func (rl *RateLimiter) Allow(clientID string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	cutoff := now.Add(-rl.window)

	// Get existing requests for this client
	requests := rl.requests[clientID]

	// Remove old requests
	var validRequests []time.Time
	for _, reqTime := range requests {
		if reqTime.After(cutoff) {
			validRequests = append(validRequests, reqTime)
		}
	}

	// Check if we're under the limit
	if len(validRequests) >= rl.limit {
		return false
	}

	// Add current request
	validRequests = append(validRequests, now)
	rl.requests[clientID] = validRequests

	return true
}

// getClientID extracts client identifier from request
func (rl *RateLimiter) getClientID(r *http.Request) string {
	// Try to get real IP from headers
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		return xff
	}
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
	}

	// Fall back to remote address
	return r.RemoteAddr
}

// cleanup removes old entries from the rate limiter
func (rl *RateLimiter) cleanup() {
	ticker := time.NewTicker(rl.cleanupTick)
	defer ticker.Stop()

	for range ticker.C {
		rl.mu.Lock()
		now := time.Now()
		cutoff := now.Add(-rl.window)

		for clientID, requests := range rl.requests {
			var validRequests []time.Time
			for _, reqTime := range requests {
				if reqTime.After(cutoff) {
					validRequests = append(validRequests, reqTime)
				}
			}

			if len(validRequests) == 0 {
				delete(rl.requests, clientID)
			} else {
				rl.requests[clientID] = validRequests
			}
		}
		rl.mu.Unlock()
	}
}

// respondRateLimited sends a rate limited response
func (rl *RateLimiter) respondRateLimited(w http.ResponseWriter) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Retry-After", fmt.Sprintf("%.0f", rl.window.Seconds()))
	w.WriteHeader(http.StatusTooManyRequests)
	fmt.Fprintf(w, `{"error":"Rate limit exceeded","code":"rate_limit_exceeded","retry_after":%.0f}`, rl.window.Seconds())
}

// GetStats returns current rate limiter statistics
func (rl *RateLimiter) GetStats() map[string]interface{} {
	rl.mu.RLock()
	defer rl.mu.RUnlock()

	now := time.Now()
	cutoff := now.Add(-rl.window)

	totalClients := len(rl.requests)
	totalRequests := 0

	for _, requests := range rl.requests {
		validRequests := 0
		for _, reqTime := range requests {
			if reqTime.After(cutoff) {
				validRequests++
			}
		}
		totalRequests += validRequests
	}

	return map[string]interface{}{
		"total_clients":  totalClients,
		"total_requests": totalRequests,
		"limit":          rl.limit,
		"window_seconds": rl.window.Seconds(),
	}
}

// DefaultRateLimiter creates a rate limiter with default settings
func DefaultRateLimiter() *RateLimiter {
	return NewRateLimiter(100, time.Minute) // 100 requests per minute
}

// StrictRateLimiter creates a strict rate limiter for sensitive endpoints
func StrictRateLimiter() *RateLimiter {
	return NewRateLimiter(10, time.Minute) // 10 requests per minute
}
