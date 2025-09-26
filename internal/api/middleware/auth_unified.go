package middleware

import (
	"context"
	"fmt"
	"net/http"
	"strings"

	"github.com/arx-os/arxos/internal/api/types"
	"github.com/arx-os/arxos/internal/common"
	"github.com/arx-os/arxos/internal/common/logger"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// AuthMiddleware handles authentication for API requests
type AuthMiddleware struct {
	authService types.AuthService
}

// NewAuthMiddleware creates a new authentication middleware
func NewAuthMiddleware(authService types.AuthService) *AuthMiddleware {
	return &AuthMiddleware{
		authService: authService,
	}
}

// RequireAuth middleware that requires authentication
func (m *AuthMiddleware) RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract token from Authorization header
		token := m.extractToken(r)
		if token == "" {
			m.respondUnauthorized(w, "Authorization token required")
			return
		}

		// Validate token
		claims, err := m.authService.ValidateToken(r.Context(), token)
		if err != nil {
			logger.Warn("Invalid token: %v", err)
			m.respondUnauthorized(w, "Invalid or expired token")
			return
		}

		// Create user context
		user := &domainmodels.User{
			ID:    claims.UserID,
			Email: claims.Email,
			Role:  claims.Role,
		}

		// Add user to context using our standardized keys
		ctx := context.WithValue(r.Context(), common.UserContextKey, user)
		ctx = context.WithValue(ctx, common.UserIDContextKey, claims.UserID)
		ctx = context.WithValue(ctx, common.UserEmailContextKey, claims.Email)
		ctx = context.WithValue(ctx, common.UserRoleContextKey, claims.Role)
		ctx = context.WithValue(ctx, common.OrgIDContextKey, claims.OrgID)

		// Continue to next handler
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequireRole middleware that requires a specific role
func (m *AuthMiddleware) RequireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// First ensure user is authenticated
			userCtx, err := common.RequireUserInContext(r.Context())
			if err != nil {
				m.respondUnauthorized(w, "Authentication required")
				return
			}

			// Check role
			if userCtx.Role != role {
				m.respondForbidden(w, fmt.Sprintf("Role '%s' required", role))
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireAnyRole middleware that requires one of the specified roles
func (m *AuthMiddleware) RequireAnyRole(roles ...string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// First ensure user is authenticated
			userCtx, err := common.RequireUserInContext(r.Context())
			if err != nil {
				m.respondUnauthorized(w, "Authentication required")
				return
			}

			// Check if user has any of the required roles
			hasRole := false
			for _, role := range roles {
				if userCtx.Role == role {
					hasRole = true
					break
				}
			}

			if !hasRole {
				m.respondForbidden(w, fmt.Sprintf("One of roles %v required", roles))
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireAdmin middleware that requires admin role
func (m *AuthMiddleware) RequireAdmin(next http.Handler) http.Handler {
	return m.RequireRole("admin")(next)
}

// OptionalAuth middleware that adds user context if token is present
func (m *AuthMiddleware) OptionalAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract token from Authorization header
		token := m.extractToken(r)
		if token != "" {
			// Validate token
			claims, err := m.authService.ValidateToken(r.Context(), token)
			if err == nil {
				// Create user context
				user := &domainmodels.User{
					ID:    claims.UserID,
					Email: claims.Email,
					Role:  claims.Role,
				}

				// Add user to context using our standardized keys
				ctx := context.WithValue(r.Context(), common.UserContextKey, user)
				ctx = context.WithValue(ctx, common.UserIDContextKey, claims.UserID)
				ctx = context.WithValue(ctx, common.UserEmailContextKey, claims.Email)
				ctx = context.WithValue(ctx, common.UserRoleContextKey, claims.Role)
				ctx = context.WithValue(ctx, common.OrgIDContextKey, claims.OrgID)

				r = r.WithContext(ctx)
			}
		}

		// Continue to next handler
		next.ServeHTTP(w, r)
	})
}

// extractToken extracts the JWT token from the Authorization header
func (m *AuthMiddleware) extractToken(r *http.Request) string {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return ""
	}

	// Check for Bearer token format
	if !strings.HasPrefix(authHeader, "Bearer ") {
		return ""
	}

	return strings.TrimPrefix(authHeader, "Bearer ")
}

// respondUnauthorized sends an unauthorized response
func (m *AuthMiddleware) respondUnauthorized(w http.ResponseWriter, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	fmt.Fprintf(w, `{"error":"%s","code":"unauthorized"}`, message)
}

// respondForbidden sends a forbidden response
func (m *AuthMiddleware) respondForbidden(w http.ResponseWriter, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusForbidden)
	fmt.Fprintf(w, `{"error":"%s","code":"forbidden"}`, message)
}
