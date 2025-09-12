package models

import (
	"crypto/rand"
	"encoding/hex"
	"time"
)

// PasswordResetToken represents a password reset token
type PasswordResetToken struct {
	ID        string    `json:"id" db:"id"`
	UserID    string    `json:"user_id" db:"user_id"`
	Token     string    `json:"token" db:"token"`
	ExpiresAt time.Time `json:"expires_at" db:"expires_at"`
	Used      bool      `json:"used" db:"used"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	UsedAt    *time.Time `json:"used_at,omitempty" db:"used_at"`
}

// IsExpired checks if the token has expired
func (t *PasswordResetToken) IsExpired() bool {
	return time.Now().After(t.ExpiresAt)
}

// IsValid checks if the token is valid (not used and not expired)
func (t *PasswordResetToken) IsValid() bool {
	return !t.Used && !t.IsExpired()
}

// MarkAsUsed marks the token as used
func (t *PasswordResetToken) MarkAsUsed() {
	t.Used = true
	now := time.Now()
	t.UsedAt = &now
}

// GenerateResetToken generates a secure random token
func GenerateResetToken() (string, error) {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil
}

// NewPasswordResetToken creates a new password reset token
func NewPasswordResetToken(userID string, expirationHours int) (*PasswordResetToken, error) {
	token, err := GenerateResetToken()
	if err != nil {
		return nil, err
	}
	
	bytes := make([]byte, 16)
	if _, err := rand.Read(bytes); err != nil {
		return nil, err
	}
	
	return &PasswordResetToken{
		ID:        hex.EncodeToString(bytes),
		UserID:    userID,
		Token:     token,
		ExpiresAt: time.Now().Add(time.Duration(expirationHours) * time.Hour),
		Used:      false,
		CreatedAt: time.Now(),
	}, nil
}