package common

import (
	"context"
	"errors"
	"fmt"

	"github.com/arx-os/arxos/pkg/models"
)

// Context keys for user information
type contextKey string

const (
	UserContextKey      contextKey = "user"
	UserIDContextKey    contextKey = "user_id"
	UserEmailContextKey contextKey = "user_email"
	UserRoleContextKey  contextKey = "user_role"
	OrgIDContextKey     contextKey = "org_id"
)

// UserContext represents user information stored in request context
type UserContext struct {
	User   *models.User
	UserID string
	Email  string
	Role   string
	OrgID  string
}

// Common errors
var (
	ErrUserNotInContext = errors.New("user not found in context")
	ErrUserNotActive    = errors.New("user account is not active")
	ErrUserNotFound     = errors.New("user not found")
)

// GetUserFromContext extracts user information from request context
func GetUserFromContext(ctx context.Context) (*UserContext, error) {
	// Try to get full user object first
	if user, ok := ctx.Value(UserContextKey).(*models.User); ok {
		if !user.IsActive {
			return nil, ErrUserNotActive
		}
		return &UserContext{
			User:   user,
			UserID: user.ID,
			Email:  user.Email,
			Role:   user.Role,
			OrgID:  "", // Will be extracted separately if needed
		}, nil
	}

	// Fallback to individual context values
	userID, ok := ctx.Value(UserIDContextKey).(string)
	if !ok || userID == "" {
		return nil, ErrUserNotInContext
	}

	email, _ := ctx.Value(UserEmailContextKey).(string)
	role, _ := ctx.Value(UserRoleContextKey).(string)
	orgID, _ := ctx.Value(OrgIDContextKey).(string)

	return &UserContext{
		User:   nil, // Not available
		UserID: userID,
		Email:  email,
		Role:   role,
		OrgID:  orgID,
	}, nil
}

// GetUserIDFromContext extracts just the user ID from context
func GetUserIDFromContext(ctx context.Context) (string, error) {
	userCtx, err := GetUserFromContext(ctx)
	if err != nil {
		return "", err
	}
	return userCtx.UserID, nil
}

// GetUserEmailFromContext extracts just the user email from context
func GetUserEmailFromContext(ctx context.Context) (string, error) {
	userCtx, err := GetUserFromContext(ctx)
	if err != nil {
		return "", err
	}
	return userCtx.Email, nil
}

// GetUserRoleFromContext extracts just the user role from context
func GetUserRoleFromContext(ctx context.Context) (string, error) {
	userCtx, err := GetUserFromContext(ctx)
	if err != nil {
		return "", err
	}
	return userCtx.Role, nil
}

// GetOrgIDFromContext extracts just the organization ID from context
func GetOrgIDFromContext(ctx context.Context) (string, error) {
	userCtx, err := GetUserFromContext(ctx)
	if err != nil {
		return "", err
	}
	return userCtx.OrgID, nil
}

// RequireUserInContext ensures user is present in context, returns error if not
func RequireUserInContext(ctx context.Context) (*UserContext, error) {
	userCtx, err := GetUserFromContext(ctx)
	if err != nil {
		return nil, fmt.Errorf("authentication required: %w", err)
	}
	return userCtx, nil
}

// RequireRoleInContext ensures user has specific role
func RequireRoleInContext(ctx context.Context, requiredRole string) (*UserContext, error) {
	userCtx, err := RequireUserInContext(ctx)
	if err != nil {
		return nil, err
	}

	if userCtx.Role != requiredRole {
		return nil, fmt.Errorf("insufficient permissions: required role %s, got %s", requiredRole, userCtx.Role)
	}

	return userCtx, nil
}

// RequireAnyRoleInContext ensures user has one of the specified roles
func RequireAnyRoleInContext(ctx context.Context, allowedRoles ...string) (*UserContext, error) {
	userCtx, err := RequireUserInContext(ctx)
	if err != nil {
		return nil, err
	}

	for _, role := range allowedRoles {
		if userCtx.Role == role {
			return userCtx, nil
		}
	}

	return nil, fmt.Errorf("insufficient permissions: required one of roles %v, got %s", allowedRoles, userCtx.Role)
}

// IsUserInContext checks if user is present in context (non-error version)
func IsUserInContext(ctx context.Context) bool {
	_, err := GetUserFromContext(ctx)
	return err == nil
}

// GetUserIDFromContextSafe returns user ID or empty string if not found (non-error version)
func GetUserIDFromContextSafe(ctx context.Context) string {
	userID, err := GetUserIDFromContext(ctx)
	if err != nil {
		return ""
	}
	return userID
}

// GetUserEmailFromContextSafe returns user email or empty string if not found (non-error version)
func GetUserEmailFromContextSafe(ctx context.Context) string {
	email, err := GetUserEmailFromContext(ctx)
	if err != nil {
		return ""
	}
	return email
}

// GetUserRoleFromContextSafe returns user role or empty string if not found (non-error version)
func GetUserRoleFromContextSafe(ctx context.Context) string {
	role, err := GetUserRoleFromContext(ctx)
	if err != nil {
		return ""
	}
	return role
}

// GetOrgIDFromContextSafe returns org ID or empty string if not found (non-error version)
func GetOrgIDFromContextSafe(ctx context.Context) string {
	orgID, err := GetOrgIDFromContext(ctx)
	if err != nil {
		return ""
	}
	return orgID
}
