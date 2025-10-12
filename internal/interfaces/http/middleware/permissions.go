package middleware

import (
	"context"
	"net/http"

	"github.com/arx-os/arxos/pkg/auth"
)

// RequirePermission creates middleware that checks if user has required permission
func RequirePermission(rbacManager *auth.RBACManager, permission auth.Permission) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract user role from context (set by auth middleware)
			role, ok := r.Context().Value("user_role").(string)
			if !ok || role == "" {
				http.Error(w, "Forbidden: no role in context", http.StatusForbidden)
				return
			}

			// Check if user's role has the required permission
			if !rbacManager.CheckPermission(auth.Role(role), permission) {
				http.Error(w, "Forbidden: insufficient permissions", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireAnyPermission creates middleware that checks if user has any of the permissions
func RequireAnyPermission(rbacManager *auth.RBACManager, permissions ...auth.Permission) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			role, ok := r.Context().Value("user_role").(string)
			if !ok || role == "" {
				http.Error(w, "Forbidden: no role in context", http.StatusForbidden)
				return
			}

			// Check if user has any of the required permissions
			if !rbacManager.CheckAnyPermission(auth.Role(role), permissions) {
				http.Error(w, "Forbidden: insufficient permissions", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireAllPermissions creates middleware that checks if user has all permissions
func RequireAllPermissions(rbacManager *auth.RBACManager, permissions ...auth.Permission) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			role, ok := r.Context().Value("user_role").(string)
			if !ok || role == "" {
				http.Error(w, "Forbidden: no role in context", http.StatusForbidden)
				return
			}

			// Check if user has all required permissions
			if !rbacManager.CheckMultiplePermissions(auth.Role(role), permissions) {
				http.Error(w, "Forbidden: insufficient permissions", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireRole creates middleware that checks if user has required role
func RequireRole(rbacManager *auth.RBACManager, requiredRoles ...auth.Role) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			role, ok := r.Context().Value("user_role").(string)
			if !ok || role == "" {
				http.Error(w, "Forbidden: no role in context", http.StatusForbidden)
				return
			}

			// Check if user has one of the required roles
			userRole := auth.Role(role)
			hasRole := false
			for _, reqRole := range requiredRoles {
				if userRole == reqRole {
					hasRole = true
					break
				}
			}

			if !hasRole {
				http.Error(w, "Forbidden: insufficient role", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireOrganization creates middleware that validates user belongs to organization
func RequireOrganization() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			orgID, ok := r.Context().Value("organization_id").(string)
			if !ok || orgID == "" {
				http.Error(w, "Forbidden: no organization context", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// InjectAuthContext is a helper to create authorization context for RBAC checks
func InjectAuthContext(ctx context.Context) *auth.AuthorizationContext {
	userID, _ := ctx.Value("user_id").(string)
	role, _ := ctx.Value("user_role").(string)
	orgID, _ := ctx.Value("organization_id").(string)

	// Extract permissions from context (slice of strings)
	var permissions []auth.Permission
	if perms, ok := ctx.Value("permissions").([]string); ok {
		for _, p := range perms {
			permissions = append(permissions, auth.Permission(p))
		}
	}

	return &auth.AuthorizationContext{
		UserID:         userID,
		Role:           auth.Role(role),
		OrganizationID: orgID,
		Permissions:    permissions,
	}
}
