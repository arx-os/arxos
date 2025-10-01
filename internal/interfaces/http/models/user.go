package models

import (
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

// UserFilter represents filters for user queries
type UserFilter struct {
	Role   string `json:"role"`
	OrgID  string `json:"org_id"`
	Active *bool  `json:"active"`
}

// UserListResponse represents the response for listing users
type UserListResponse struct {
	Users  []*models.User `json:"users"`
	Total  int            `json:"total"`
	Limit  int            `json:"limit"`
	Offset int            `json:"offset"`
}

// CreateUserRequest represents the request to create a user
type CreateUserRequest struct {
	Email    string                 `json:"email" validate:"required,email"`
	Name     string                 `json:"name" validate:"required"`
	Password string                 `json:"password" validate:"required,min=8"`
	Role     string                 `json:"role" validate:"required,oneof=admin user"`
	OrgID    string                 `json:"org_id"`
	IsActive bool                   `json:"is_active"`
	Metadata map[string]interface{} `json:"metadata"`
}

// UpdateUserRequest represents the request to update a user
type UpdateUserRequest struct {
	Name     *string                `json:"name,omitempty"`
	Email    *string                `json:"email,omitempty"`
	Role     *string                `json:"role,omitempty"`
	IsActive *bool                  `json:"is_active,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// UserResponse represents a user in API responses
type UserResponse struct {
	ID        string                 `json:"id"`
	Email     string                 `json:"email"`
	Name      string                 `json:"name"`
	Role      string                 `json:"role"`
	OrgID     string                 `json:"org_id"`
	IsActive  bool                   `json:"is_active"`
	Metadata  map[string]interface{} `json:"metadata"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

// LoginRequest represents a login request
type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required"`
}

// LoginResponse represents a login response
type LoginResponse struct {
	User         *UserResponse `json:"user"`
	AccessToken  string        `json:"access_token"`
	RefreshToken string        `json:"refresh_token"`
	ExpiresIn    int64         `json:"expires_in"`
}

// ChangePasswordRequest represents a change password request
type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password" validate:"required"`
	NewPassword     string `json:"new_password" validate:"required,min=8"`
}

// ResetPasswordRequest represents a password reset request
type ResetPasswordRequest struct {
	Email string `json:"email" validate:"required,email"`
}

// ResetPasswordConfirmRequest represents a password reset confirmation
type ResetPasswordConfirmRequest struct {
	Token       string `json:"token" validate:"required"`
	NewPassword string `json:"new_password" validate:"required,min=8"`
}

// UserStats represents user statistics
type UserStats struct {
	TotalUsers    int `json:"total_users"`
	ActiveUsers   int `json:"active_users"`
	InactiveUsers int `json:"inactive_users"`
	AdminUsers    int `json:"admin_users"`
	RegularUsers  int `json:"regular_users"`
}
