package middleware

import (
	"net/http"
	"strings"
)

// CORSMiddleware handles Cross-Origin Resource Sharing
type CORSMiddleware struct {
	allowedOrigins []string
	allowedMethods []string
	allowedHeaders []string
	maxAge         int
}

// NewCORSMiddleware creates a new CORS middleware
func NewCORSMiddleware(allowedOrigins, allowedMethods, allowedHeaders []string, maxAge int) *CORSMiddleware {
	return &CORSMiddleware{
		allowedOrigins: allowedOrigins,
		allowedMethods: allowedMethods,
		allowedHeaders: allowedHeaders,
		maxAge:         maxAge,
	}
}

// DefaultCORSMiddleware creates a CORS middleware with default settings
func DefaultCORSMiddleware() *CORSMiddleware {
	return NewCORSMiddleware(
		[]string{"*"}, // Allow all origins in development
		[]string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
		[]string{"Content-Type", "Authorization", "X-Request-ID", "X-Requested-With"},
		3600, // 1 hour
	)
}

// CORS middleware that handles preflight requests and adds CORS headers
func (m *CORSMiddleware) CORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")

		// Check if origin is allowed
		if m.isOriginAllowed(origin) {
			w.Header().Set("Access-Control-Allow-Origin", origin)
		}

		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Methods", strings.Join(m.allowedMethods, ", "))
		w.Header().Set("Access-Control-Allow-Headers", strings.Join(m.allowedHeaders, ", "))
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		w.Header().Set("Access-Control-Max-Age", string(rune(m.maxAge)))

		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// isOriginAllowed checks if an origin is in the allowed list
func (m *CORSMiddleware) isOriginAllowed(origin string) bool {
	// Allow all origins if "*" is in the list
	for _, allowed := range m.allowedOrigins {
		if allowed == "*" {
			return true
		}
		if allowed == origin {
			return true
		}
	}
	return false
}

// Middleware returns the CORS middleware function
func (m *CORSMiddleware) Middleware(next http.Handler) http.Handler {
	return m.CORS(next)
}
