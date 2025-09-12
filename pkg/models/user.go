package models

import (
	"time"
)

// User represents a user account
type User struct {
	ID           string    `json:"id" db:"id"`
	Email        string    `json:"email" db:"email"`
	Name         string    `json:"name" db:"name"`
	PasswordHash string    `json:"-" db:"password_hash"`
	Avatar       string    `json:"avatar,omitempty" db:"avatar"`
	Phone        string    `json:"phone,omitempty" db:"phone"`
	
	// Status
	Status       UserStatus `json:"status" db:"status"`
	EmailVerified bool      `json:"email_verified" db:"email_verified"`
	PhoneVerified bool      `json:"phone_verified" db:"phone_verified"`
	
	// MFA
	MFAEnabled   bool   `json:"mfa_enabled" db:"mfa_enabled"`
	MFASecret    string `json:"-" db:"mfa_secret"`
	
	// Timestamps
	CreatedAt    time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at" db:"updated_at"`
	LastLoginAt  *time.Time `json:"last_login_at,omitempty" db:"last_login_at"`
	
	// Organization context (not stored in user table)
	CurrentOrgID string                `json:"current_org_id,omitempty"`
	Organizations []OrganizationMember  `json:"organizations,omitempty"`
}

// UserStatus represents the user account status
type UserStatus string

const (
	UserStatusActive    UserStatus = "active"
	UserStatusInactive  UserStatus = "inactive"
	UserStatusSuspended UserStatus = "suspended"
)

// UserSession represents an active user session
type UserSession struct {
	ID             string    `json:"id" db:"id"`
	UserID         string    `json:"user_id" db:"user_id"`
	OrganizationID string    `json:"organization_id" db:"organization_id"`
	Token          string    `json:"token" db:"token"`
	RefreshToken   string    `json:"refresh_token" db:"refresh_token"`
	IPAddress      string    `json:"ip_address" db:"ip_address"`
	UserAgent      string    `json:"user_agent" db:"user_agent"`
	ExpiresAt      time.Time `json:"expires_at" db:"expires_at"`
	CreatedAt      time.Time `json:"created_at" db:"created_at"`
	LastAccessAt   time.Time `json:"last_access_at" db:"last_access_at"`
}

// IsExpired checks if the session has expired
func (s *UserSession) IsExpired() bool {
	return time.Now().After(s.ExpiresAt)
}

// UpdateLastAccess updates the last access time
func (s *UserSession) UpdateLastAccess() {
	s.LastAccessAt = time.Now()
}

// UserPreferences stores user-specific preferences
type UserPreferences struct {
	UserID          string `json:"user_id" db:"user_id"`
	Theme           string `json:"theme" db:"theme"` // light, dark, auto
	Language        string `json:"language" db:"language"`
	TimeZone        string `json:"timezone" db:"timezone"`
	DateFormat      string `json:"date_format" db:"date_format"`
	EmailNotifications bool `json:"email_notifications" db:"email_notifications"`
	PushNotifications  bool `json:"push_notifications" db:"push_notifications"`
	DefaultOrgID    string `json:"default_org_id" db:"default_org_id"`
}

// PasswordReset represents a password reset request
type PasswordReset struct {
	ID        string    `json:"id" db:"id"`
	UserID    string    `json:"user_id" db:"user_id"`
	Token     string    `json:"-" db:"token"`
	ExpiresAt time.Time `json:"expires_at" db:"expires_at"`
	UsedAt    *time.Time `json:"used_at,omitempty" db:"used_at"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// EmailVerification represents an email verification token
type EmailVerification struct {
	ID        string    `json:"id" db:"id"`
	UserID    string    `json:"user_id" db:"user_id"`
	Email     string    `json:"email" db:"email"`
	Token     string    `json:"-" db:"token"`
	ExpiresAt time.Time `json:"expires_at" db:"expires_at"`
	VerifiedAt *time.Time `json:"verified_at,omitempty" db:"verified_at"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// IsActive checks if the user account is active
func (u *User) IsActive() bool {
	return u.Status == UserStatusActive
}

// HasVerifiedEmail checks if the user has verified their email
func (u *User) HasVerifiedEmail() bool {
	return u.EmailVerified
}

// CanAccessOrganization checks if user can access an organization
func (u *User) CanAccessOrganization(orgID string) bool {
	for _, org := range u.Organizations {
		if org.OrganizationID == orgID {
			return true
		}
	}
	return false
}

// GetOrganizationRole returns the user's role in an organization
func (u *User) GetOrganizationRole(orgID string) *Role {
	for _, org := range u.Organizations {
		if org.OrganizationID == orgID {
			return &org.Role
		}
	}
	return nil
}

// IsSessionValid checks if a session is still valid
func (s *UserSession) IsSessionValid() bool {
	return time.Now().Before(s.ExpiresAt)
}

// IsExpired checks if a password reset token has expired
func (p *PasswordReset) IsExpired() bool {
	return time.Now().After(p.ExpiresAt)
}

// IsExpired checks if an email verification token has expired
func (e *EmailVerification) IsExpired() bool {
	return time.Now().After(e.ExpiresAt)
}