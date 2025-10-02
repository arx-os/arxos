package middleware

import (
	"fmt"
	"net/http"
	"sync"
	"time"
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
			fmt.Printf("Rate limit exceeded for client: %s\n", clientID)
			rl.respondRateLimited(w)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// Allow checks if a client is allowed to make a request
func (rl *RateLimiter) Allow(clientID string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	windowStart := now.Add(-rl.window)

	// Get or create request history for client
	requests, exists := rl.requests[clientID]
	if !exists {
		requests = make([]time.Time, 0)
	}

	// Remove old requests outside the window
	var validRequests []time.Time
	for _, reqTime := range requests {
		if reqTime.After(windowStart) {
			validRequests = append(validRequests, reqTime)
		}
	}

	// Check if adding this request would exceed the limit
	if len(validRequests) >= rl.limit {
		return false
	}

	// Add current request
	validRequests = append(validRequests, now)
	rl.requests[clientID] = validRequests

	return true
}

// GetRemainingRequests returns the number of remaining requests for a client
func (rl *RateLimiter) GetRemainingRequests(clientID string) int {
	rl.mu.RLock()
	defer rl.mu.RUnlock()

	now := time.Now()
	windowStart := now.Add(-rl.window)

	requests, exists := rl.requests[clientID]
	if !exists {
		return rl.limit
	}

	// Count valid requests in the window
	validCount := 0
	for _, reqTime := range requests {
		if reqTime.After(windowStart) {
			validCount++
		}
	}

	return rl.limit - validCount
}

// Reset resets the rate limit for a specific client
func (rl *RateLimiter) Reset(clientID string) {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	delete(rl.requests, clientID)
}

// getClientID extracts client identifier from request
func (rl *RateLimiter) getClientID(r *http.Request) string {
	// Try to get real IP from X-Forwarded-For or X-Real-IP headers
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		return forwarded
	}
	if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
		return realIP
	}

	// Fall back to RemoteAddr
	return r.RemoteAddr
}

// respondRateLimited sends rate limit exceeded response
func (rl *RateLimiter) respondRateLimited(w http.ResponseWriter) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", rl.limit))
	w.Header().Set("X-RateLimit-Window", rl.window.String())
	w.WriteHeader(http.StatusTooManyRequests)

	// In a real implementation, you would use json.NewEncoder here
	fmt.Fprintf(w, `{"error":"Rate limit exceeded","message":"Too many requests. Please try again later."}`)
}

// cleanup removes old request entries periodically
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

// Middleware returns the rate limiting middleware function
func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return rl.RateLimitMiddleware(next)
}
