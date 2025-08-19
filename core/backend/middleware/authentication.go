package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/arxos/arxos/core/backend/services"
)

// ContextKey type for context values
type ContextKey string

const (
	UserContextKey    ContextKey = "user"
	ClaimsContextKey  ContextKey = "claims"
	SessionContextKey ContextKey = "session"
)

// AuthMiddleware provides JWT authentication middleware
type AuthMiddleware struct {
	authService *services.AuthService
	skipPaths   []string // Paths that don't require authentication
}

// NewAuthMiddleware creates a new authentication middleware
func NewAuthMiddleware(authService *services.AuthService) *AuthMiddleware {
	return &AuthMiddleware{
		authService: authService,
		skipPaths: []string{
			"/api/auth/login",
			"/api/auth/register",
			"/api/auth/refresh",
			"/api/health",
			"/api/status",
		},
	}
}

// RequireAuth ensures the request has a valid JWT token
func (m *AuthMiddleware) RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if path should skip authentication
		if m.shouldSkipAuth(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		// Extract token from request
		token, err := m.authService.ExtractTokenFromRequest(r)
		if err != nil {
			http.Error(w, "Authentication required", http.StatusUnauthorized)
			return
		}

		// Check if token is blacklisted
		if m.authService.IsTokenBlacklisted(token) {
			http.Error(w, "Token has been revoked", http.StatusUnauthorized)
			return
		}

		// Validate token
		claims, err := m.authService.ValidateAccessToken(token)
		if err != nil {
			switch err {
			case services.ErrTokenExpired:
				http.Error(w, "Token expired", http.StatusUnauthorized)
			case services.ErrInvalidSignature:
				http.Error(w, "Invalid token signature", http.StatusUnauthorized)
			default:
				http.Error(w, "Invalid token", http.StatusUnauthorized)
			}
			return
		}

		// Add claims to request context
		ctx := context.WithValue(r.Context(), ClaimsContextKey, claims)
		ctx = context.WithValue(ctx, UserContextKey, claims.UserID)
		ctx = context.WithValue(ctx, SessionContextKey, claims.SessionID)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequireRole ensures the user has one of the specified roles
func (m *AuthMiddleware) RequireRole(roles ...string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// First ensure authentication
			claims := r.Context().Value(ClaimsContextKey)
			if claims == nil {
				http.Error(w, "Authentication required", http.StatusUnauthorized)
				return
			}

			// Check role
			userClaims := claims.(*services.JWTClaims)
			hasRole := false
			for _, role := range roles {
				if userClaims.Role == role {
					hasRole = true
					break
				}
			}

			if !hasRole {
				http.Error(w, "Insufficient permissions", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireScope ensures the user has one of the specified scopes
func (m *AuthMiddleware) RequireScope(scopes ...string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims := r.Context().Value(ClaimsContextKey)
			if claims == nil {
				http.Error(w, "Authentication required", http.StatusUnauthorized)
				return
			}

			userClaims := claims.(*services.JWTClaims)
			hasScope := false
			for _, requiredScope := range scopes {
				for _, userScope := range userClaims.Scopes {
					if userScope == requiredScope {
						hasScope = true
						break
					}
				}
				if hasScope {
					break
				}
			}

			if !hasScope {
				http.Error(w, "Insufficient scope", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// OptionalAuth adds user info to context if token is present, but doesn't require it
func (m *AuthMiddleware) OptionalAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Try to extract token
		token, err := m.authService.ExtractTokenFromRequest(r)
		if err == nil && !m.authService.IsTokenBlacklisted(token) {
			// Validate token if present
			if claims, err := m.authService.ValidateAccessToken(token); err == nil {
				// Add claims to context
				ctx := context.WithValue(r.Context(), ClaimsContextKey, claims)
				ctx = context.WithValue(ctx, UserContextKey, claims.UserID)
				ctx = context.WithValue(ctx, SessionContextKey, claims.SessionID)
				r = r.WithContext(ctx)
			}
		}

		next.ServeHTTP(w, r)
	})
}

// shouldSkipAuth checks if the path should skip authentication
func (m *AuthMiddleware) shouldSkipAuth(path string) bool {
	for _, skipPath := range m.skipPaths {
		if strings.HasPrefix(path, skipPath) {
			return true
		}
	}
	return false
}

// GetUserID extracts the user ID from the request context
func GetUserID(r *http.Request) string {
	if userID := r.Context().Value(UserContextKey); userID != nil {
		return userID.(string)
	}
	return ""
}

// GetClaims extracts the JWT claims from the request context
func GetClaims(r *http.Request) *services.JWTClaims {
	if claims := r.Context().Value(ClaimsContextKey); claims != nil {
		return claims.(*services.JWTClaims)
	}
	return nil
}

// GetSessionID extracts the session ID from the request context
func GetSessionID(r *http.Request) string {
	if sessionID := r.Context().Value(SessionContextKey); sessionID != nil {
		return sessionID.(string)
	}
	return ""
}