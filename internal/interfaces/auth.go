package interfaces

import (
	"context"
	"time"
)

// AuthService defines the interface for authentication operations
type AuthService interface {
	// Authentication operations
	Login(ctx context.Context, email, password string) (interface{}, error)
	Register(ctx context.Context, email, password, name string) (interface{}, error)
	Logout(ctx context.Context, token string) error
	
	// Token operations
	GenerateToken(ctx context.Context, userID, email, role, orgID string) (string, error)
	ValidateToken(ctx context.Context, token string) (*TokenClaims, error)
	ValidateTokenClaims(ctx context.Context, token string) (*TokenClaims, error)
	RefreshToken(ctx context.Context, refreshToken string) (string, string, error)
	RevokeToken(ctx context.Context, token string) error

	// Session operations
	CreateSession(ctx context.Context, userID string) (*Session, error)
	GetSession(ctx context.Context, sessionID string) (*Session, error)
	UpdateSession(ctx context.Context, sessionID string) error
	DeleteSession(ctx context.Context, sessionID string) error
	CleanupExpiredSessions(ctx context.Context) error

	// Password operations
	HashPassword(password string) (string, error)
	VerifyPassword(hashedPassword, password string) error
}

// TokenClaims represents JWT token claims
type TokenClaims struct {
	UserID    string    `json:"user_id"`
	Email     string    `json:"email"`
	Role      string    `json:"role"`
	OrgID     string    `json:"org_id"`
	IssuedAt  time.Time `json:"iat"`
	ExpiresAt time.Time `json:"exp"`
}

// Session represents a user session
type Session struct {
	ID        string    `json:"id"`
	UserID    string    `json:"user_id"`
	CreatedAt time.Time `json:"created_at"`
	ExpiresAt time.Time `json:"expires_at"`
	LastUsed  time.Time `json:"last_used"`
}
