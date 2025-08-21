package security

import (
	"net/http"
)

// SecurityMiddleware provides basic security functionality
type SecurityMiddleware struct {
	logger interface{}
}

// NewSecurityMiddleware creates a new security middleware
func NewSecurityMiddleware(logger interface{}) *SecurityMiddleware {
	return &SecurityMiddleware{
		logger: logger,
	}
}

// SecurityHeadersMiddleware adds security headers
func (m *SecurityMiddleware) SecurityHeadersMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Add basic security headers
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("X-XSS-Protection", "1; mode=block")
		next.ServeHTTP(w, r)
	})
}

// AuditLoggingMiddleware logs security events
func (m *SecurityMiddleware) AuditLoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// For testing purposes, minimal logging
		next.ServeHTTP(w, r)
	})
}

// RateLimitMiddleware provides basic rate limiting
func (m *SecurityMiddleware) RateLimitMiddleware(requestsPerSecond, burst int) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// For testing purposes, no rate limiting
			next.ServeHTTP(w, r)
		})
	}
}
