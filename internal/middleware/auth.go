// Package middleware provides HTTP middleware components for ArxOS web applications.
// It includes authentication, rate limiting, validation, and other request processing
// middleware for secure and efficient API operations.
package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/common/logger"
)

// contextKey is a custom type for context keys to avoid collisions
type contextKey string

const (
	// UserContextKey is the key for storing user in context
	UserContextKey contextKey = "user"
	// ClaimsContextKey is the key for storing claims in context
	ClaimsContextKey contextKey = "claims"
)

// AuthMiddleware provides JWT authentication middleware
type AuthMiddleware struct {
	authService api.AuthService
	// List of paths that don't require authentication
	publicPaths map[string]bool
}

// NewAuthMiddleware creates a new authentication middleware
func NewAuthMiddleware(authService api.AuthService) *AuthMiddleware {
	return &AuthMiddleware{
		authService: authService,
		publicPaths: map[string]bool{
			"/health":               true,
			"/ready":                true,
			"/api/v1/":              true,
			"/api/v1/auth/login":    true,
			"/api/v1/auth/register": true,
		},
	}
}

// Middleware returns the HTTP middleware function
func (m *AuthMiddleware) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if path is public
		if m.isPublicPath(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		// Extract token from Authorization header
		token := m.extractToken(r)
		if token == "" {
			// Check cookie as fallback
			if cookie, err := r.Cookie("auth_token"); err == nil {
				token = cookie.Value
			}
		}

		if token == "" {
			logger.Debug("No token provided for path: %s", r.URL.Path)
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		// Validate token
		claims, err := m.authService.ValidateToken(r.Context(), token)
		if err != nil {
			logger.Debug("Invalid token: %v", err)
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		// Add user info to context
		ctx := context.WithValue(r.Context(), ClaimsContextKey, claims)
		ctx = context.WithValue(ctx, UserContextKey, &api.User{
			ID:    claims.UserID,
			Email: claims.Email,
			Role:  claims.Role,
			OrgID: claims.OrgID,
		})

		// Continue with authenticated request
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// extractToken extracts the JWT token from the Authorization header
func (m *AuthMiddleware) extractToken(r *http.Request) string {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return ""
	}

	// Check for Bearer token
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
		return ""
	}

	return parts[1]
}

// isPublicPath checks if a path doesn't require authentication
func (m *AuthMiddleware) isPublicPath(path string) bool {
	// Check exact match
	if m.publicPaths[path] {
		return true
	}

	// Check if it's a static file or web UI path (not API)
	if !strings.HasPrefix(path, "/api/") {
		return true
	}

	return false
}

// RequireRole returns middleware that requires a specific role
func RequireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := r.Context().Value(ClaimsContextKey).(*api.TokenClaims)
			if !ok {
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
				return
			}

			if claims.Role != role && claims.Role != "admin" {
				http.Error(w, "Forbidden", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// GetUser retrieves the authenticated user from the request context
func GetUser(r *http.Request) *api.User {
	user, ok := r.Context().Value(UserContextKey).(*api.User)
	if !ok {
		return nil
	}
	return user
}

// GetClaims retrieves the JWT claims from the request context
func GetClaims(r *http.Request) *api.TokenClaims {
	claims, ok := r.Context().Value(ClaimsContextKey).(*api.TokenClaims)
	if !ok {
		return nil
	}
	return claims
}
