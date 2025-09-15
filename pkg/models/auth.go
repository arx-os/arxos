package models

import "time"

// AuthToken represents an authentication token response
type AuthToken struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int64  `json:"expires_in"`
}

// UserSession represents an active user session
type UserSession struct {
	ID             string    `json:"id"`
	UserID         string    `json:"user_id"`
	OrganizationID string    `json:"organization_id,omitempty"`
	Token          string    `json:"token"`
	RefreshToken   string    `json:"refresh_token"`
	UserAgent      string    `json:"user_agent,omitempty"`
	IPAddress      string    `json:"ip_address,omitempty"`
	ExpiresAt      time.Time `json:"expires_at"`
	LastAccessAt   time.Time `json:"last_access_at"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

// PasswordResetToken represents a password reset token
type PasswordResetToken struct {
	ID        string     `json:"id"`
	UserID    string     `json:"user_id"`
	Token     string     `json:"token"`
	Used      bool       `json:"used"`
	UsedAt    *time.Time `json:"used_at,omitempty"`
	ExpiresAt time.Time  `json:"expires_at"`
	CreatedAt time.Time  `json:"created_at"`
}

// LoginRequest represents a login request
type LoginRequest struct {
	Username string `json:"username"` // Can be email or username
	Password string `json:"password"`
}

// RefreshTokenRequest represents a token refresh request
type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token"`
}

// PasswordResetRequest represents a password reset request
type PasswordResetRequest struct {
	Email string `json:"email"`
}

// PasswordResetConfirmRequest represents a password reset confirmation
type PasswordResetConfirmRequest struct {
	Token       string `json:"token"`
	NewPassword string `json:"new_password"`
}

// ChangePasswordRequest represents a password change request
type ChangePasswordRequest struct {
	OldPassword string `json:"old_password"`
	NewPassword string `json:"new_password"`
}