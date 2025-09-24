package middleware

import (
	"net/http"

	"github.com/arx-os/arxos/internal/api/types"
)

// MiddlewareChain manages middleware execution order
type MiddlewareChain struct {
	middlewares []func(http.Handler) http.Handler
}

// NewMiddlewareChain creates a new middleware chain
func NewMiddlewareChain() *MiddlewareChain {
	return &MiddlewareChain{
		middlewares: make([]func(http.Handler) http.Handler, 0),
	}
}

// Add adds a middleware to the chain
func (mc *MiddlewareChain) Add(middleware func(http.Handler) http.Handler) *MiddlewareChain {
	mc.middlewares = append(mc.middlewares, middleware)
	return mc
}

// Build builds the middleware chain
func (mc *MiddlewareChain) Build(handler http.Handler) http.Handler {
	// Apply middlewares in reverse order (last added is first executed)
	for i := len(mc.middlewares) - 1; i >= 0; i-- {
		handler = mc.middlewares[i](handler)
	}
	return handler
}

// DefaultChain creates a default middleware chain for API routes
func DefaultChain(authService types.AuthService) *MiddlewareChain {
	// Create middleware instances
	recovery := DefaultRecoveryMiddleware()
	logging := DefaultLoggingMiddleware()
	cors := DefaultCORSMiddleware()
	rateLimiter := DefaultRateLimiter()
	validation := DefaultValidationMiddleware()
	security := DefaultSecurityMiddleware()
	metrics := NewMetricsMiddleware()

	return NewMiddlewareChain().
		Add(recovery.Recovery).
		Add(logging.Logging).
		Add(security.SecurityHeaders).
		Add(cors.CORS).
		Add(rateLimiter.RateLimitMiddleware).
		Add(validation.ValidateJSON).
		Add(metrics.Metrics)
}

// AuthChain creates a middleware chain for authenticated routes
func AuthChain(authService types.AuthService) *MiddlewareChain {
	// Create middleware instances
	recovery := DefaultRecoveryMiddleware()
	logging := DefaultLoggingMiddleware()
	cors := DefaultCORSMiddleware()
	auth := NewAuthMiddleware(authService)
	rateLimiter := DefaultRateLimiter()
	validation := DefaultValidationMiddleware()
	security := DefaultSecurityMiddleware()
	metrics := NewMetricsMiddleware()

	return NewMiddlewareChain().
		Add(recovery.Recovery).
		Add(logging.Logging).
		Add(security.SecurityHeaders).
		Add(cors.CORS).
		Add(rateLimiter.UserRateLimitMiddleware).
		Add(validation.ValidateJSON).
		Add(metrics.Metrics).
		Add(auth.RequireAuth)
}

// AdminChain creates a middleware chain for admin-only routes
func AdminChain(authService types.AuthService) *MiddlewareChain {
	// Create middleware instances
	recovery := DefaultRecoveryMiddleware()
	logging := DefaultLoggingMiddleware()
	cors := DefaultCORSMiddleware()
	auth := NewAuthMiddleware(authService)
	rateLimiter := StrictRateLimiter() // Stricter rate limiting for admin
	validation := DefaultValidationMiddleware()
	security := DefaultSecurityMiddleware()
	metrics := NewMetricsMiddleware()

	return NewMiddlewareChain().
		Add(recovery.Recovery).
		Add(logging.Logging).
		Add(security.SecurityHeaders).
		Add(cors.CORS).
		Add(rateLimiter.UserRateLimitMiddleware).
		Add(validation.ValidateJSON).
		Add(metrics.Metrics).
		Add(auth.RequireAuth).
		Add(auth.RequireAdmin)
}

// PublicChain creates a middleware chain for public routes
func PublicChain() *MiddlewareChain {
	// Create middleware instances
	recovery := DefaultRecoveryMiddleware()
	logging := DefaultLoggingMiddleware()
	cors := DefaultCORSMiddleware()
	rateLimiter := DefaultRateLimiter()
	validation := DefaultValidationMiddleware()
	security := DefaultSecurityMiddleware()
	metrics := NewMetricsMiddleware()

	return NewMiddlewareChain().
		Add(recovery.Recovery).
		Add(logging.Logging).
		Add(security.SecurityHeaders).
		Add(cors.CORS).
		Add(rateLimiter.RateLimitMiddleware).
		Add(validation.ValidateJSON).
		Add(metrics.Metrics)
}

// OptionalAuthChain creates a middleware chain for routes that optionally require auth
func OptionalAuthChain(authService types.AuthService) *MiddlewareChain {
	// Create middleware instances
	recovery := DefaultRecoveryMiddleware()
	logging := DefaultLoggingMiddleware()
	cors := DefaultCORSMiddleware()
	auth := NewAuthMiddleware(authService)
	rateLimiter := DefaultRateLimiter()
	validation := DefaultValidationMiddleware()
	security := DefaultSecurityMiddleware()
	metrics := NewMetricsMiddleware()

	return NewMiddlewareChain().
		Add(recovery.Recovery).
		Add(logging.Logging).
		Add(security.SecurityHeaders).
		Add(cors.CORS).
		Add(rateLimiter.RateLimitMiddleware).
		Add(validation.ValidateJSON).
		Add(metrics.Metrics).
		Add(auth.OptionalAuth)
}

// HealthChain creates a minimal middleware chain for health checks
func HealthChain() *MiddlewareChain {
	// Create middleware instances
	recovery := DefaultRecoveryMiddleware()
	cors := DefaultCORSMiddleware()
	security := DefaultSecurityMiddleware()

	return NewMiddlewareChain().
		Add(recovery.Recovery).
		Add(security.SecurityHeaders).
		Add(cors.CORS)
}

// MetricsChain creates a middleware chain for metrics endpoints
func MetricsChain() *MiddlewareChain {
	// Create middleware instances
	recovery := DefaultRecoveryMiddleware()
	cors := DefaultCORSMiddleware()
	security := DefaultSecurityMiddleware()

	return NewMiddlewareChain().
		Add(recovery.Recovery).
		Add(security.SecurityHeaders).
		Add(cors.CORS)
}
