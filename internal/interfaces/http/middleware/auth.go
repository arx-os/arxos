package middleware

import (
	"context"
	"net/http"
	"strings"

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

// User represents a user in the middleware context
type User struct {
	ID    string `json:"id"`
	Email string `json:"email"`
	Role  string `json:"role"`
	OrgID string `json:"org_id"`
}

// AuthMiddleware provides JWT authentication middleware
type AuthMiddleware struct {
	authService AuthService
	// List of paths that don't require authentication
	publicPaths map[string]bool
}

// AuthService interface for authentication operations
type AuthService interface {
	ValidateToken(token string) (*User, error)
	ExtractToken(r *http.Request) (string, error)
}

// NewAuthMiddleware creates a new authentication middleware
func NewAuthMiddleware(authService AuthService) *AuthMiddleware {
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

// Middleware returns the authentication middleware function
func (m *AuthMiddleware) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if the path is public
		if m.isPublicPath(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		// Extract token from request
		token, err := m.authService.ExtractToken(r)
		if err != nil {
			logger.Error("Failed to extract token: %v", err)
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		// Validate token
		user, err := m.authService.ValidateToken(token)
		if err != nil {
			logger.Error("Invalid token: %v", err)
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		// Add user to context
		ctx := context.WithValue(r.Context(), UserContextKey, user)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// isPublicPath checks if a path is public (doesn't require authentication)
func (m *AuthMiddleware) isPublicPath(path string) bool {
	// Check exact matches first
	if m.publicPaths[path] {
		return true
	}

	// Check prefix matches
	for publicPath := range m.publicPaths {
		if strings.HasPrefix(path, publicPath) {
			return true
		}
	}

	return false
}

// GetUserFromContext extracts user from request context
func GetUserFromContext(ctx context.Context) (*User, bool) {
	user, ok := ctx.Value(UserContextKey).(*User)
	return user, ok
}

// RequireRole creates middleware that requires a specific role
func RequireRole(requiredRole string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			user, ok := GetUserFromContext(r.Context())
			if !ok {
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
				return
			}

			if user.Role != requiredRole {
				http.Error(w, "Forbidden", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireOrganization creates middleware that requires organization membership
func RequireOrganization(orgID string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			user, ok := GetUserFromContext(r.Context())
			if !ok {
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
				return
			}

			if user.OrgID != orgID {
				http.Error(w, "Forbidden", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}
