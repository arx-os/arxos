package middleware

import (
	"context"
	"net/http"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// SecurityMiddleware provides security-related middleware
type SecurityMiddleware struct {
	allowedHosts   []string
	trustedProxies []string
	secureHeaders  map[string]string
}

// NewSecurityMiddleware creates a new security middleware
func NewSecurityMiddleware() *SecurityMiddleware {
	return &SecurityMiddleware{
		allowedHosts:   []string{},
		trustedProxies: []string{},
		secureHeaders: map[string]string{
			"X-Content-Type-Options":    "nosniff",
			"X-Frame-Options":           "DENY",
			"X-XSS-Protection":          "1; mode=block",
			"Strict-Transport-Security": "max-age=31536000; includeSubDomains",
			"Referrer-Policy":           "strict-origin-when-cross-origin",
			"Content-Security-Policy":   "default-src 'self'",
		},
	}
}

// SecurityHeaders middleware that adds security headers
func (sm *SecurityMiddleware) SecurityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Add security headers
		for header, value := range sm.secureHeaders {
			w.Header().Set(header, value)
		}

		// Add custom headers based on request
		if r.TLS != nil {
			w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		}

		next.ServeHTTP(w, r)
	})
}

// HostValidation middleware that validates the Host header
func (sm *SecurityMiddleware) HostValidation(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		host := r.Host

		// Remove port from host
		if colon := strings.Index(host, ":"); colon != -1 {
			host = host[:colon]
		}

		// Check if host is allowed
		if len(sm.allowedHosts) > 0 {
			allowed := false
			for _, allowedHost := range sm.allowedHosts {
				if host == allowedHost {
					allowed = true
					break
				}
			}

			if !allowed {
				logger.Warn("Invalid host header: %s", host)
				http.Error(w, "Invalid host", http.StatusBadRequest)
				return
			}
		}

		next.ServeHTTP(w, r)
	})
}

// IPWhitelist middleware that restricts access by IP
func (sm *SecurityMiddleware) IPWhitelist(allowedIPs []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			clientIP := sm.getClientIP(r)

			// Check if IP is allowed
			allowed := false
			for _, allowedIP := range allowedIPs {
				if clientIP == allowedIP {
					allowed = true
					break
				}
			}

			if !allowed {
				logger.Warn("Access denied for IP: %s", clientIP)
				http.Error(w, "Access denied", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequestSizeLimit middleware that limits request size
func (sm *SecurityMiddleware) RequestSizeLimit(maxSize int64) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.ContentLength > maxSize {
				logger.Warn("Request too large: %d bytes (max: %d)", r.ContentLength, maxSize)
				http.Error(w, "Request too large", http.StatusRequestEntityTooLarge)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// TimeoutMiddleware middleware that adds request timeout
func (sm *SecurityMiddleware) TimeoutMiddleware(timeout time.Duration) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Create context with timeout
			ctx := r.Context()
			ctx, cancel := context.WithTimeout(ctx, timeout)
			defer cancel()

			// Update request with new context
			r = r.WithContext(ctx)

			// Create response writer that handles timeouts
			responseWriter := &timeoutResponseWriter{
				ResponseWriter: w,
				timeout:        timeout,
				request:        r,
			}

			next.ServeHTTP(responseWriter, r)
		})
	}
}

// timeoutResponseWriter handles request timeouts
type timeoutResponseWriter struct {
	http.ResponseWriter
	timeout time.Duration
	request *http.Request
}

// WriteHeader handles timeout responses
func (trw *timeoutResponseWriter) WriteHeader(code int) {
	// Check if context is cancelled
	select {
	case <-trw.request.Context().Done():
		trw.ResponseWriter.WriteHeader(http.StatusRequestTimeout)
		return
	default:
		trw.ResponseWriter.WriteHeader(code)
	}
}

// getClientIP extracts the real client IP from request
func (sm *SecurityMiddleware) getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		// Take the first IP in the chain
		if comma := strings.Index(xff, ","); comma != -1 {
			return strings.TrimSpace(xff[:comma])
		}
		return xff
	}

	// Check X-Real-IP header
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
	}

	// Fall back to remote address
	return r.RemoteAddr
}

// CSRFProtection middleware that provides CSRF protection
func (sm *SecurityMiddleware) CSRFProtection(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip CSRF check for safe methods
		if r.Method == "GET" || r.Method == "HEAD" || r.Method == "OPTIONS" {
			next.ServeHTTP(w, r)
			return
		}

		// Check CSRF token
		csrfToken := r.Header.Get("X-CSRF-Token")
		if csrfToken == "" {
			csrfToken = r.FormValue("csrf_token")
		}

		// Validate CSRF token (this would need proper implementation)
		if !sm.validateCSRFToken(csrfToken, r) {
			logger.Warn("Invalid CSRF token for request: %s %s", r.Method, r.URL.Path)
			http.Error(w, "Invalid CSRF token", http.StatusForbidden)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// validateCSRFToken validates the CSRF token
func (sm *SecurityMiddleware) validateCSRFToken(token string, r *http.Request) bool {
	// This would implement proper CSRF token validation
	// For now, just check if token is present
	return token != ""
}

// DefaultSecurityMiddleware creates a security middleware with default settings
func DefaultSecurityMiddleware() *SecurityMiddleware {
	return NewSecurityMiddleware()
}

// ProductionSecurityMiddleware creates a security middleware for production
func ProductionSecurityMiddleware(allowedHosts []string) *SecurityMiddleware {
	sm := NewSecurityMiddleware()
	sm.allowedHosts = allowedHosts

	// Add additional security headers for production
	sm.secureHeaders["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
	sm.secureHeaders["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

	return sm
}
