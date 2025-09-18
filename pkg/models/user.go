package models

import (
	"time"
)

// User represents a user account
type User struct {
	ID           string     `json:"id" db:"id"`
	Email        string     `json:"email" db:"email"`
	Username     string     `json:"username" db:"username"`
	FullName     string     `json:"full_name" db:"full_name"`
	PasswordHash string     `json:"-" db:"password_hash"`
	Avatar       string     `json:"avatar,omitempty" db:"avatar"`
	Phone        string     `json:"phone,omitempty" db:"phone"`
	Role         string     `json:"role" db:"role"`
	Status       string     `json:"status" db:"status"`
	LastLogin    *time.Time `json:"last_login,omitempty" db:"last_login"`
	CreatedAt    *time.Time `json:"created_at" db:"created_at"`
	UpdatedAt    *time.Time `json:"updated_at" db:"updated_at"`

	// MFA
	MFAEnabled bool   `json:"mfa_enabled" db:"mfa_enabled"`
	MFASecret  string `json:"-" db:"mfa_secret"`

	// Email verification
	EmailVerified bool `json:"email_verified" db:"email_verified"`
	PhoneVerified bool `json:"phone_verified" db:"phone_verified"`

	// Organization context (not stored in user table)
	CurrentOrgID  string               `json:"current_org_id,omitempty"`
	Organizations []OrganizationMember `json:"organizations,omitempty"`
}

// UserPreferences stores user-specific preferences
type UserPreferences struct {
	UserID             string `json:"user_id" db:"user_id"`
	Theme              string `json:"theme" db:"theme"` // light, dark, auto
	Language           string `json:"language" db:"language"`
	TimeZone           string `json:"timezone" db:"timezone"`
	DateFormat         string `json:"date_format" db:"date_format"`
	EmailNotifications bool   `json:"email_notifications" db:"email_notifications"`
	PushNotifications  bool   `json:"push_notifications" db:"push_notifications"`
	DefaultOrgID       string `json:"default_org_id" db:"default_org_id"`
}

// EmailVerification represents an email verification token
type EmailVerification struct {
	ID         string     `json:"id" db:"id"`
	UserID     string     `json:"user_id" db:"user_id"`
	Email      string     `json:"email" db:"email"`
	Token      string     `json:"-" db:"token"`
	ExpiresAt  time.Time  `json:"expires_at" db:"expires_at"`
	VerifiedAt *time.Time `json:"verified_at,omitempty" db:"verified_at"`
	CreatedAt  time.Time  `json:"created_at" db:"created_at"`
}

// IsActive checks if the user account is active
func (u *User) IsActive() bool {
	return u.Status == "active"
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

// IsExpired checks if an email verification token has expired
func (e *EmailVerification) IsExpired() bool {
	return time.Now().After(e.ExpiresAt)
}
