package models

import "time"

// AuthToken represents an authentication token
type AuthToken struct {
	Token     string     `json:"token"`
	UserID    string     `json:"user_id"`
	ExpiresAt time.Time  `json:"expires_at"`
	CreatedAt time.Time  `json:"created_at"`
	RefreshToken string `json:"refresh_token,omitempty"`
}