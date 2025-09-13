package api

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/telemetry"
)

// contextKey is a type for context keys
type contextKey string

const (
	// ContextKeyRequestID is the context key for request ID
	ContextKeyRequestID contextKey = "request_id"
	// ContextKeyUserID is the context key for user ID
	ContextKeyUserID contextKey = "user_id"
	// ContextKeyOrgID is the context key for organization ID
	ContextKeyOrgID contextKey = "org_id"
)

// loggingMiddleware logs all requests
func (s *Server) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		requestID := s.getRequestID(r)
		
		// Add request ID to context
		ctx := context.WithValue(r.Context(), ContextKeyRequestID, requestID)
		r = r.WithContext(ctx)
		
		// Wrap response writer to capture status
		wrapped := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		
		// Log request
		logger.Debug("[%s] %s %s %s", requestID, r.Method, r.URL.Path, r.RemoteAddr)
		
		// Process request
		next.ServeHTTP(wrapped, r)
		
		// Log response
		duration := time.Since(start)
		logger.Info("[%s] %s %s %d %v", requestID, r.Method, r.URL.Path, wrapped.statusCode, duration)
		
		// Track metrics
		telemetry.Metric("api_request_duration_ms", float64(duration.Milliseconds()), map[string]interface{}{
			"method": r.Method,
			"path":   r.URL.Path,
			"status": wrapped.statusCode,
		})
	})
}

// recoveryMiddleware recovers from panics
func (s *Server) recoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				requestID := r.Context().Value(ContextKeyRequestID).(string)
				logger.Error("[%s] Panic recovered: %v", requestID, err)
				
				// Track error
				telemetry.Error("api_panic", fmt.Errorf("%v", err), map[string]interface{}{
					"request_id": requestID,
					"path":       r.URL.Path,
				})
				
				// Send error response
				s.respondError(w, http.StatusInternalServerError, "Internal server error")
			}
		}()
		
		next.ServeHTTP(w, r)
	})
}

// corsMiddleware adds CORS headers
func (s *Server) corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		
		// Check if origin is allowed
		if origin != "" && s.isOriginAllowed(origin) {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Allow-Credentials", "true")
		} else if s.isOriginAllowed("*") {
			w.Header().Set("Access-Control-Allow-Origin", "*")
		}
		
		// Set allowed methods and headers from config
		w.Header().Set("Access-Control-Allow-Methods", strings.Join(s.config.CORS.AllowedMethods, ", "))
		w.Header().Set("Access-Control-Allow-Headers", strings.Join(s.config.CORS.AllowedHeaders, ", "))
		w.Header().Set("Access-Control-Max-Age", fmt.Sprintf("%d", s.config.CORS.MaxAge))
		
		// Handle preflight requests
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}

// isOriginAllowed checks if the given origin is in the allowed list
func (s *Server) isOriginAllowed(origin string) bool {
	for _, allowed := range s.config.CORS.AllowedOrigins {
		if allowed == "*" || allowed == origin {
			return true
		}
	}
	return false
}

// authMiddleware validates authentication
func (s *Server) authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip auth for public endpoints
		publicPaths := []string{
			"/health",
			"/ready",
			"/api/v1/auth/login",
			"/api/v1/auth/register",
		}
		
		for _, path := range publicPaths {
			if r.URL.Path == path {
				next.ServeHTTP(w, r)
				return
			}
		}
		
		// Extract token from header
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			s.respondError(w, http.StatusUnauthorized, "Missing authorization header")
			return
		}
		
		// Validate Bearer token
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			s.respondError(w, http.StatusUnauthorized, "Invalid authorization header format")
			return
		}
		
		token := parts[1]
		
		// Validate token with auth service
		if s.services.Auth == nil {
			// Auth service not configured, skip validation in development
			logger.Warn("Auth service not configured, skipping token validation")
			next.ServeHTTP(w, r)
			return
		}
		
		claims, err := s.services.Auth.ValidateToken(r.Context(), token)
		if err != nil {
			s.respondError(w, http.StatusUnauthorized, "Invalid or expired token")
			return
		}
		
		// Add user info to context
		ctx := r.Context()
		ctx = context.WithValue(ctx, ContextKeyUserID, claims.UserID)
		ctx = context.WithValue(ctx, ContextKeyOrgID, claims.OrgID)
		r = r.WithContext(ctx)
		
		next.ServeHTTP(w, r)
	})
}

// rateLimitMiddleware implements configurable rate limiting
func (s *Server) rateLimitMiddleware(next http.Handler) http.Handler {
	// In-memory rate limiter with configurable limits
	// Note: For distributed systems, consider using Redis for rate limiting
	
	type client struct {
		limiter  *rateLimiter
		lastSeen time.Time
	}
	
	var (
		clients = make(map[string]*client)
		mu      sync.Mutex
		
		// Configurable cleanup interval
		cleanup = time.NewTicker(s.config.RateLimit.CleanupInterval)
	)
	
	go func() {
		for range cleanup.C {
			mu.Lock()
			for ip, c := range clients {
				if time.Since(c.lastSeen) > s.config.RateLimit.ClientTTL {
					delete(clients, ip)
				}
			}
			mu.Unlock()
		}
	}()
	
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get client IP (handle proxy headers properly)
		ip := s.getClientIP(r)
		
		// Get or create rate limiter for client
		mu.Lock()
		c, exists := clients[ip]
		if !exists {
			c = &client{
				limiter: newRateLimiter(
					s.config.RateLimit.RequestsPerMinute,
					s.config.RateLimit.BurstSize,
					1*time.Minute,
				),
			}
			clients[ip] = c
		}
		c.lastSeen = time.Now()
		mu.Unlock()
		
		// Check rate limit
		if !c.limiter.allow() {
			w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", s.config.RateLimit.RequestsPerMinute))
			w.Header().Set("X-RateLimit-Remaining", "0")
			w.Header().Set("Retry-After", "60")
			s.respondError(w, http.StatusTooManyRequests, "Rate limit exceeded")
			return
		}
		
		// Add rate limit headers
		remaining := c.limiter.remaining()
		w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", s.config.RateLimit.RequestsPerMinute))
		w.Header().Set("X-RateLimit-Remaining", fmt.Sprintf("%d", remaining))
		
		next.ServeHTTP(w, r)
	})
}

// getClientIP extracts the real client IP from the request
func (s *Server) getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header (proxy/load balancer)
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		// Take the first IP in the chain
		ips := strings.Split(forwarded, ",")
		return strings.TrimSpace(ips[0])
	}
	
	// Check X-Real-IP header (nginx)
	if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
		return realIP
	}
	
	// Fallback to RemoteAddr
	ip := r.RemoteAddr
	if idx := strings.LastIndex(ip, ":"); idx != -1 {
		ip = ip[:idx] // Remove port
	}
	return ip
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (w *responseWriter) WriteHeader(code int) {
	w.statusCode = code
	w.ResponseWriter.WriteHeader(code)
}

// rateLimiter implements a token bucket rate limiter with burst support
type rateLimiter struct {
	tokens     int
	maxTokens  int
	burstSize  int
	refillAt   time.Time
	interval   time.Duration
	mu         sync.Mutex
}

func newRateLimiter(maxTokens, burstSize int, interval time.Duration) *rateLimiter {
	// Burst size should not exceed max tokens
	if burstSize > maxTokens {
		burstSize = maxTokens
	}
	
	return &rateLimiter{
		tokens:    burstSize, // Start with burst allowance
		maxTokens: maxTokens,
		burstSize: burstSize,
		refillAt:  time.Now().Add(interval),
		interval:  interval,
	}
}

func (rl *rateLimiter) allow() bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	
	rl.refill()
	
	if rl.tokens > 0 {
		rl.tokens--
		return true
	}
	
	return false
}

func (rl *rateLimiter) remaining() int {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	
	rl.refill()
	return rl.tokens
}

func (rl *rateLimiter) refill() {
	now := time.Now()
	if now.After(rl.refillAt) {
		// Calculate how many intervals have passed
		intervals := int(now.Sub(rl.refillAt) / rl.interval) + 1
		
		// Add tokens based on intervals passed, but don't exceed max
		tokensToAdd := intervals * rl.maxTokens / int(rl.interval/time.Minute)
		rl.tokens = min(rl.tokens + tokensToAdd, rl.maxTokens)
		
		// Update refill time
		rl.refillAt = now.Add(rl.interval)
	}
}

// min returns the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}