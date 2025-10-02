// Package middleware provides HTTP middleware following Clean Architecture
package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/arx-os/arxos/pkg/auth"
)

// AuthMiddleware provides authentication middleware
func AuthMiddleware(jwtManager *auth.JWTManager) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip auth for health check and public endpoints
			if isPublicEndpoint(r.URL.Path) {
				next.ServeHTTP(w, r)
				return
			}

			// Extract token from Authorization header
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				http.Error(w, "Authorization header required", http.StatusUnauthorized)
				return
			}

			// Check Bearer token format
			if !strings.HasPrefix(authHeader, "Bearer ") {
				http.Error(w, "Invalid authorization format", http.StatusUnauthorized)
				return
			}

			token := strings.TrimPrefix(authHeader, "Bearer ")
			if token == "" {
				http.Error(w, "Token required", http.StatusUnauthorized)
				return
			}

			// Validate token using JWT manager
			if jwtManager != nil {
				claims, err := jwtManager.ValidateToken(token)
				if err != nil {
					http.Error(w, "Invalid token", http.StatusUnauthorized)
					return
				}

				// Add user context from JWT claims
				ctx := r.Context()
				ctx = context.WithValue(ctx, "user_id", claims.UserID)
				ctx = context.WithValue(ctx, "user_email", claims.Email)
				ctx = context.WithValue(ctx, "user_role", claims.Role)
				ctx = context.WithValue(ctx, "organization_id", claims.OrganizationID)
				ctx = context.WithValue(ctx, "permissions", claims.Permissions)
				ctx = context.WithValue(ctx, "session_id", claims.SessionID)

				next.ServeHTTP(w, r.WithContext(ctx))
			} else {
				// Fallback: basic token validation if JWT manager not available
				if len(token) < 10 {
					http.Error(w, "Invalid token", http.StatusUnauthorized)
					return
				}

				// Add basic user context
				ctx := r.Context()
				ctx = context.WithValue(ctx, "user_id", "user123") // Placeholder
				ctx = context.WithValue(ctx, "user_role", "user")  // Placeholder

				next.ServeHTTP(w, r.WithContext(ctx))
			}
		})
	}
}

// isPublicEndpoint checks if the endpoint is public (no auth required)
func isPublicEndpoint(path string) bool {
	publicPaths := []string{
		"/health",
		"/api/v1/health",
		"/api/v1/auth/login",
		"/api/v1/auth/register",
		"/api/v1/auth/refresh",
	}

	for _, publicPath := range publicPaths {
		if strings.HasPrefix(path, publicPath) {
			return true
		}
	}

	return false
}
