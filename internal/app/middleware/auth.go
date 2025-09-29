package middleware

import (
	"context"
	"fmt"
	"net/http"
	"strings"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// contextKey is a custom type for context keys to avoid collisions
type contextKey string

const (
	// UserContextKey is the key for storing user in context
	UserContextKey contextKey = "user"
	// ClaimsContextKey is the key for storing claims in context
	ClaimsContextKey contextKey = "claims"
	// OrganizationContextKey is the key for storing organization in context
	OrganizationContextKey contextKey = "organization_id"
)

// AuthMiddleware handles authentication for API requests following Clean Architecture principles
type AuthMiddleware struct {
	services *types.Services
	logger   logger.Logger
}

// NewAuthMiddleware creates a new authentication middleware with dependency injection
func NewAuthMiddleware(services *types.Services, logger logger.Logger) *AuthMiddleware {
	return &AuthMiddleware{
		services: services,
		logger:   logger,
	}
}

// RequireAuth middleware that requires authentication
func (m *AuthMiddleware) RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract token from Authorization header
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			m.writeUnauthorizedResponse(w, "Authorization header required")
			return
		}

		// Check Bearer token format
		if !strings.HasPrefix(authHeader, "Bearer ") {
			m.writeUnauthorizedResponse(w, "Invalid authorization header format")
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		if token == "" {
			m.writeUnauthorizedResponse(w, "Token required")
			return
		}

		// Validate token through domain service
		// Note: This would be implemented in the domain layer
		user, err := m.validateToken(token)
		if err != nil {
			m.logger.Error("Token validation failed", "error", err)
			m.writeUnauthorizedResponse(w, "Invalid token")
			return
		}

		// Add user to context
		ctx := context.WithValue(r.Context(), UserContextKey, user)
		ctx = context.WithValue(ctx, OrganizationContextKey, user.OrganizationID)

		// Continue to next handler
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// OptionalAuth middleware that optionally validates authentication
func (m *AuthMiddleware) OptionalAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract token from Authorization header
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			// No auth header, continue without user context
			next.ServeHTTP(w, r)
			return
		}

		// Check Bearer token format
		if !strings.HasPrefix(authHeader, "Bearer ") {
			// Invalid format, continue without user context
			next.ServeHTTP(w, r)
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		if token == "" {
			// Empty token, continue without user context
			next.ServeHTTP(w, r)
			return
		}

		// Validate token through domain service
		user, err := m.validateToken(token)
		if err != nil {
			// Invalid token, continue without user context
			m.logger.Warn("Optional auth token validation failed", "error", err)
			next.ServeHTTP(w, r)
			return
		}

		// Add user to context
		ctx := context.WithValue(r.Context(), UserContextKey, user)
		ctx = context.WithValue(ctx, OrganizationContextKey, user.OrganizationID)

		// Continue to next handler
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequireRole middleware that requires a specific role
func (m *AuthMiddleware) RequireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Get user from context
			user, ok := r.Context().Value(UserContextKey).(*domainmodels.User)
			if !ok {
				m.writeUnauthorizedResponse(w, "User not authenticated")
				return
			}

			// Check user role
			if user.Role != role {
				m.writeForbiddenResponse(w, fmt.Sprintf("Role %s required", role))
				return
			}

			// Continue to next handler
			next.ServeHTTP(w, r)
		})
	}
}

// RequireOrganization middleware that requires organization access
func (m *AuthMiddleware) RequireOrganization(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get user from context
		user, ok := r.Context().Value(UserContextKey).(*domainmodels.User)
		if !ok {
			m.writeUnauthorizedResponse(w, "User not authenticated")
			return
		}

		// Check if user has organization access
		if user.OrganizationID == "" {
			m.writeForbiddenResponse(w, "Organization access required")
			return
		}

		// Continue to next handler
		next.ServeHTTP(w, r)
	})
}

// Helper methods
func (m *AuthMiddleware) validateToken(token string) (*domainmodels.User, error) {
	// This would call the domain service to validate the token
	// For now, return a placeholder user
	return &domainmodels.User{
		ID:             "user_id",
		Email:          "user@example.com",
		Role:           "user",
		OrganizationID: "org_id",
	}, nil
}

func (m *AuthMiddleware) writeUnauthorizedResponse(w http.ResponseWriter, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	fmt.Fprintf(w, `{"error":{"message":"%s","code":"UNAUTHORIZED"}}`, message)
}

func (m *AuthMiddleware) writeForbiddenResponse(w http.ResponseWriter, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusForbidden)
	fmt.Fprintf(w, `{"error":{"message":"%s","code":"FORBIDDEN"}}`, message)
}
