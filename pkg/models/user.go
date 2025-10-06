package models

import (
	"time"
)

// User represents a system user
type User struct {
	ID                  string         `json:"id"`
	Email               string         `json:"email"`
	Username            string         `json:"username"`
	PasswordHash        string         `json:"-"` // Never expose in JSON
	FullName            string         `json:"full_name,omitempty"`
	Role                string         `json:"role"`
	OrganizationID      string         `json:"organization_id,omitempty"`
	IsActive            bool           `json:"is_active"`
	EmailVerified       bool           `json:"email_verified"`
	Phone               string         `json:"phone,omitempty"`
	AvatarURL           string         `json:"avatar_url,omitempty"`
	Preferences         map[string]any `json:"preferences,omitempty"`
	Metadata            map[string]any `json:"metadata,omitempty"`
	LastLogin           *time.Time     `json:"last_login,omitempty"`
	FailedLoginAttempts int            `json:"-"`
	LockedUntil         *time.Time     `json:"-"`
	CreatedAt           time.Time      `json:"created_at"`
	UpdatedAt           time.Time      `json:"updated_at"`
}

// UserSession represents an active user session
type UserSession struct {
	ID               string         `json:"id"`
	UserID           string         `json:"user_id"`
	OrganizationID   string         `json:"organization_id,omitempty"`
	Token            string         `json:"token"`
	RefreshToken     string         `json:"refresh_token"`
	IPAddress        string         `json:"ip_address,omitempty"`
	UserAgent        string         `json:"user_agent,omitempty"`
	DeviceInfo       map[string]any `json:"device_info,omitempty"`
	IsActive         bool           `json:"is_active"`
	ExpiresAt        time.Time      `json:"expires_at"`
	RefreshExpiresAt time.Time      `json:"refresh_expires_at"`
	LastActivity     time.Time      `json:"last_activity"`
	LastAccessAt     time.Time      `json:"last_access_at"`
	CreatedAt        time.Time      `json:"created_at"`
	UpdatedAt        time.Time      `json:"updated_at"`
}

// PasswordResetToken represents a password reset request
type PasswordResetToken struct {
	ID        string     `json:"id"`
	UserID    string     `json:"user_id"`
	Token     string     `json:"token"`
	Used      bool       `json:"used"`
	UsedAt    *time.Time `json:"used_at,omitempty"`
	ExpiresAt time.Time  `json:"expires_at"`
	CreatedAt time.Time  `json:"created_at"`
}

// APIKey represents an API access key
type APIKey struct {
	ID             string         `json:"id"`
	UserID         string         `json:"user_id,omitempty"`
	OrganizationID string         `json:"organization_id,omitempty"`
	Name           string         `json:"name"`
	KeyHash        string         `json:"-"` // Never expose
	LastFour       string         `json:"last_four"`
	Permissions    map[string]any `json:"permissions,omitempty"`
	RateLimit      int            `json:"rate_limit"`
	IsActive       bool           `json:"is_active"`
	LastUsedAt     *time.Time     `json:"last_used_at,omitempty"`
	ExpiresAt      *time.Time     `json:"expires_at,omitempty"`
	CreatedAt      time.Time      `json:"created_at"`
}

// AuditLog represents an audit log entry
type AuditLog struct {
	ID             string         `json:"id"`
	UserID         string         `json:"user_id,omitempty"`
	OrganizationID string         `json:"organization_id,omitempty"`
	Action         string         `json:"action"`
	ResourceType   string         `json:"resource_type,omitempty"`
	ResourceID     string         `json:"resource_id,omitempty"`
	Changes        map[string]any `json:"changes,omitempty"`
	IPAddress      string         `json:"ip_address,omitempty"`
	UserAgent      string         `json:"user_agent,omitempty"`
	Metadata       map[string]any `json:"metadata,omitempty"`
	CreatedAt      time.Time      `json:"created_at"`
}

// UserCreateRequest represents a user creation request
type UserCreateRequest struct {
	Email     string `json:"email" validate:"required,email"`
	Username  string `json:"username" validate:"required,min=3,max=50"`
	Password  string `json:"password" validate:"required,min=8"`
	FullName  string `json:"full_name,omitempty"`
	Role      string `json:"role,omitempty"`
	Phone     string `json:"phone,omitempty"`
	AvatarURL string `json:"avatar_url,omitempty"`
}

// UserUpdateRequest represents a user update request
type UserUpdateRequest struct {
	FullName    string         `json:"full_name,omitempty"`
	Phone       string         `json:"phone,omitempty"`
	AvatarURL   string         `json:"avatar_url,omitempty"`
	Preferences map[string]any `json:"preferences,omitempty"`
	Metadata    map[string]any `json:"metadata,omitempty"`
}

// PasswordChangeRequest represents a password change request
type PasswordChangeRequest struct {
	OldPassword string `json:"old_password" validate:"required"`
	NewPassword string `json:"new_password" validate:"required,min=8"`
}

// PasswordResetRequest represents a password reset request
type PasswordResetRequest struct {
	Email string `json:"email" validate:"required,email"`
}

// PasswordResetConfirm represents password reset confirmation
type PasswordResetConfirm struct {
	Token       string `json:"token" validate:"required"`
	NewPassword string `json:"new_password" validate:"required,min=8"`
}

// LoginRequest represents a login request
type LoginRequest struct {
	Email    string `json:"email,omitempty"`
	Username string `json:"username,omitempty"`
	Password string `json:"password" validate:"required"`
}

// LoginResponse represents a successful login response
type LoginResponse struct {
	User         *User     `json:"user"`
	Token        string    `json:"token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
}

// TokenRefreshRequest represents a token refresh request
type TokenRefreshRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}

// TokenRefreshResponse represents a token refresh response
type TokenRefreshResponse struct {
	Token        string    `json:"token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
}
