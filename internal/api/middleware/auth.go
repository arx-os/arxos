package middleware

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/api/types"
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

		// Add user to context
		ctx := context.WithValue(r.Context(), "user", user)
		ctx = context.WithValue(ctx, "user_id", claims.UserID)
		ctx = context.WithValue(ctx, "user_email", claims.Email)
		ctx = context.WithValue(ctx, "user_role", claims.Role)
		ctx = context.WithValue(ctx, "org_id", claims.OrgID)

		// Continue to next handler
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequireRole middleware that requires a specific role
func (m *AuthMiddleware) RequireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Get user from context (set by RequireAuth)
			user, ok := r.Context().Value("user").(*domainmodels.User)
			if !ok {
				m.respondUnauthorized(w, "User not found in context")
				return
			}

			// Check if user has required role
			if user.Role != role && user.Role != string(domainmodels.UserRoleAdmin) {
				m.respondForbidden(w, fmt.Sprintf("Role '%s' required", role))
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireAdmin middleware that requires admin role
func (m *AuthMiddleware) RequireAdmin(next http.Handler) http.Handler {
	return m.RequireRole(string(domainmodels.UserRoleAdmin))(next)
}

// RequireOrgAccess middleware that requires organization access
func (m *AuthMiddleware) RequireOrgAccess(orgID string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Get user from context
			user, ok := r.Context().Value("user").(*domainmodels.User)
			if !ok {
				m.respondUnauthorized(w, "User not found in context")
				return
			}

			// Get organization ID from context
			userOrgID, ok := r.Context().Value("org_id").(string)
			if !ok {
				m.respondForbidden(w, "Organization access required")
				return
			}

			// Check if user has access to the organization
			if userOrgID != orgID && user.Role != string(domainmodels.UserRoleAdmin) {
				m.respondForbidden(w, "Access denied to organization")
				return
			}

			next.ServeHTTP(w, r)
		})
	}
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

				// Add user to context
				ctx := context.WithValue(r.Context(), "user", user)
				ctx = context.WithValue(ctx, "user_id", claims.UserID)
				ctx = context.WithValue(ctx, "user_email", claims.Email)
				ctx = context.WithValue(ctx, "user_role", claims.Role)
				ctx = context.WithValue(ctx, "org_id", claims.OrgID)

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

// TokenRefreshMiddleware handles token refresh
func (m *AuthMiddleware) TokenRefreshMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if token is about to expire
		_, ok := r.Context().Value("user").(*domainmodels.User)
		if !ok {
			next.ServeHTTP(w, r)
			return
		}

		// Check token expiration (this would need to be implemented in the auth service)
		// For now, just pass through
		next.ServeHTTP(w, r)
	})
}

// RateLimitMiddleware provides rate limiting based on user
func (m *AuthMiddleware) RateLimitMiddleware(requestsPerMinute int) func(http.Handler) http.Handler {
	// This would implement rate limiting based on user ID
	// For now, just pass through
	return func(next http.Handler) http.Handler {
		return next
	}
}

// AuditMiddleware logs user actions
func (m *AuthMiddleware) AuditMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Get user info from context
		userID := r.Context().Value("user_id")
		userEmail := r.Context().Value("user_email")

		// Log the request
		logger.Info("API Request: %s %s - User: %s (%s) - %s",
			r.Method, r.URL.Path, userID, userEmail, r.RemoteAddr)

		// Continue to next handler
		next.ServeHTTP(w, r)

		// Log the response
		duration := time.Since(start)
		logger.Info("API Response: %s %s - Duration: %v",
			r.Method, r.URL.Path, duration)
	})
}
