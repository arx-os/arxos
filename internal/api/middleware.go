package api

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/logger"
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
		// TODO: Make CORS origins configurable
		origin := r.Header.Get("Origin")
		if origin == "" {
			origin = "*"
		}
		
		w.Header().Set("Access-Control-Allow-Origin", origin)
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		w.Header().Set("Access-Control-Max-Age", "3600")
		
		// Handle preflight requests
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		
		next.ServeHTTP(w, r)
	})
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

// rateLimitMiddleware implements rate limiting
func (s *Server) rateLimitMiddleware(next http.Handler) http.Handler {
	// Simple in-memory rate limiter
	// TODO: Use Redis for distributed rate limiting
	
	type client struct {
		limiter  *rateLimiter
		lastSeen time.Time
	}
	
	var (
		clients = make(map[string]*client)
		mu      sync.Mutex
		
		// Clean up old clients every minute
		cleanup = time.NewTicker(1 * time.Minute)
	)
	
	go func() {
		for range cleanup.C {
			mu.Lock()
			for ip, c := range clients {
				if time.Since(c.lastSeen) > 5*time.Minute {
					delete(clients, ip)
				}
			}
			mu.Unlock()
		}
	}()
	
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get client IP
		ip := r.RemoteAddr
		if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
			ip = strings.Split(forwarded, ",")[0]
		}
		
		// Get or create rate limiter for client
		mu.Lock()
		c, exists := clients[ip]
		if !exists {
			c = &client{
				limiter: newRateLimiter(100, 1*time.Minute), // 100 requests per minute
			}
			clients[ip] = c
		}
		c.lastSeen = time.Now()
		mu.Unlock()
		
		// Check rate limit
		if !c.limiter.allow() {
			s.respondError(w, http.StatusTooManyRequests, "Rate limit exceeded")
			return
		}
		
		next.ServeHTTP(w, r)
	})
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

// rateLimiter implements a simple token bucket rate limiter
type rateLimiter struct {
	tokens    int
	maxTokens int
	refillAt  time.Time
	interval  time.Duration
	mu        sync.Mutex
}

func newRateLimiter(maxTokens int, interval time.Duration) *rateLimiter {
	return &rateLimiter{
		tokens:    maxTokens,
		maxTokens: maxTokens,
		refillAt:  time.Now().Add(interval),
		interval:  interval,
	}
}

func (rl *rateLimiter) allow() bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	
	now := time.Now()
	if now.After(rl.refillAt) {
		rl.tokens = rl.maxTokens
		rl.refillAt = now.Add(rl.interval)
	}
	
	if rl.tokens > 0 {
		rl.tokens--
		return true
	}
	
	return false
}