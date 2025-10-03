package middleware

import (
	"net/http"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/pkg/auth"
)

// MiddlewareManager manages all HTTP middleware
type MiddlewareManager struct {
	logger     domain.Logger
	jwtManager *auth.JWTManager
	cors       *CORSMiddleware
}

// NewMiddlewareManager creates a new middleware manager
func NewMiddlewareManager(logger domain.Logger, jwtManager *auth.JWTManager) *MiddlewareManager {
	return &MiddlewareManager{
		logger:     logger,
		jwtManager: jwtManager,
		cors:       DefaultCORSMiddleware(),
	}
}

// ApplyCommonMiddleware applies common middleware to all routes
func (mm *MiddlewareManager) ApplyCommonMiddleware(handler http.Handler) http.Handler {
	// Apply middleware in order (last applied is outermost)
	handler = SecurityMiddleware()(handler)
	handler = RequestIDMiddleware()(handler)
	handler = LoggingMiddleware(mm.logger)(handler)
	handler = ErrorHandlerMiddleware(mm.logger)(handler)
	handler = mm.cors.Middleware(handler)

	return handler
}

// ApplyAPIMiddleware applies API-specific middleware
func (mm *MiddlewareManager) ApplyAPIMiddleware(handler http.Handler) http.Handler {
	// Apply common middleware first
	handler = mm.ApplyCommonMiddleware(handler)

	// Add API-specific middleware
	handler = RateLimit(100, 1*60*60*1000*1000*1000)(handler) // 100 requests per hour
	handler = AuthMiddleware(mm.jwtManager)(handler)

	return handler
}

// ApplyPublicMiddleware applies middleware for public endpoints
func (mm *MiddlewareManager) ApplyPublicMiddleware(handler http.Handler) http.Handler {
	// Apply common middleware
	handler = mm.ApplyCommonMiddleware(handler)

	// Add public-specific middleware (lighter rate limiting)
	handler = RateLimit(1000, 1*60*60*1000*1000*1000)(handler) // 1000 requests per hour

	return handler
}

// ApplyHealthMiddleware applies middleware for health check endpoints
func (mm *MiddlewareManager) ApplyHealthMiddleware(handler http.Handler) http.Handler {
	// Minimal middleware for health checks
	handler = RequestIDMiddleware()(handler)
	handler = LoggingMiddleware(mm.logger)(handler)
	handler = SecurityMiddleware()(handler)

	return handler
}

// SetCORSConfig updates CORS configuration
func (mm *MiddlewareManager) SetCORSConfig(allowedOrigins, allowedMethods, allowedHeaders []string, maxAge int) {
	mm.cors = NewCORSMiddleware(allowedOrigins, allowedMethods, allowedHeaders, maxAge)
}

// GetCORSMiddleware returns the CORS middleware instance
func (mm *MiddlewareManager) GetCORSMiddleware() *CORSMiddleware {
	return mm.cors
}

// CreateHandlerChain creates a middleware chain for a specific handler
func (mm *MiddlewareManager) CreateHandlerChain(handler http.Handler, middlewareType string) http.Handler {
	switch middlewareType {
	case "api":
		return mm.ApplyAPIMiddleware(handler)
	case "public":
		return mm.ApplyPublicMiddleware(handler)
	case "health":
		return mm.ApplyHealthMiddleware(handler)
	default:
		return mm.ApplyCommonMiddleware(handler)
	}
}
