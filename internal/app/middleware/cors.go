package middleware

import (
	"net/http"
	"strings"
)

// CORSMiddleware handles Cross-Origin Resource Sharing following Clean Architecture principles
type CORSMiddleware struct {
	allowedOrigins []string
	allowedMethods []string
	allowedHeaders []string
	maxAge         int
}

// NewCORSMiddleware creates a new CORS middleware with dependency injection
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
		[]string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token", "X-Requested-With"},
		86400, // 24 hours
	)
}

// Handler returns the CORS middleware handler
func (c *CORSMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		c.setCORSHeaders(w, r)

		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		// Continue to next handler
		next.ServeHTTP(w, r)
	})
}

// setCORSHeaders sets the appropriate CORS headers
func (c *CORSMiddleware) setCORSHeaders(w http.ResponseWriter, r *http.Request) {
	origin := r.Header.Get("Origin")

	// Check if origin is allowed
	if c.isOriginAllowed(origin) {
		w.Header().Set("Access-Control-Allow-Origin", origin)
	} else {
		w.Header().Set("Access-Control-Allow-Origin", "*")
	}

	// Set other CORS headers
	w.Header().Set("Access-Control-Allow-Methods", strings.Join(c.allowedMethods, ", "))
	w.Header().Set("Access-Control-Allow-Headers", strings.Join(c.allowedHeaders, ", "))
	w.Header().Set("Access-Control-Max-Age", string(rune(c.maxAge)))
	w.Header().Set("Access-Control-Allow-Credentials", "true")
}

// isOriginAllowed checks if the origin is in the allowed list
func (c *CORSMiddleware) isOriginAllowed(origin string) bool {
	if len(c.allowedOrigins) == 0 {
		return false
	}

	// Allow all origins if "*" is in the list
	for _, allowed := range c.allowedOrigins {
		if allowed == "*" {
			return true
		}
		if allowed == origin {
			return true
		}
	}

	return false
}
