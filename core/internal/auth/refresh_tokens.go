package auth

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"time"
	
	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
	"gorm.io/gorm"
)

const (
	RefreshTokenLength = 32 // bytes
	RefreshTokenTTL    = 7 * 24 * time.Hour // 7 days
	MaxRefreshTokens   = 5 // Maximum refresh tokens per user
)

var (
	ErrInvalidRefreshToken = errors.New("invalid refresh token")
	ErrExpiredRefreshToken = errors.New("refresh token expired")
	ErrRevokedRefreshToken = errors.New("refresh token revoked")
)

// RefreshToken represents a refresh token in the database
type RefreshToken struct {
	ID           string    `gorm:"type:uuid;default:gen_random_uuid();primaryKey"`
	UserID       uint      `gorm:"index"`
	TokenHash    string    `gorm:"uniqueIndex;not null"`
	ExpiresAt    time.Time `gorm:"not null"`
	CreatedAt    time.Time
	LastUsedAt   *time.Time
	UserAgent    string
	IPAddress    string
	IsRevoked    bool      `gorm:"default:false"`
	RevokedAt    *time.Time
	RevokedReason string
}

// GenerateRefreshToken creates a new refresh token for a user
func GenerateRefreshToken(userID uint, userAgent, ipAddress string) (string, *RefreshToken, error) {
	// Generate random token
	tokenBytes := make([]byte, RefreshTokenLength)
	if _, err := rand.Read(tokenBytes); err != nil {
		return "", nil, fmt.Errorf("failed to generate refresh token: %w", err)
	}
	
	token := hex.EncodeToString(tokenBytes)
	
	// Hash the token for storage
	hasher := sha256.New()
	hasher.Write([]byte(token))
	tokenHash := hex.EncodeToString(hasher.Sum(nil))
	
	// Clean up old tokens if user has too many
	if err := cleanupOldRefreshTokens(userID); err != nil {
		// Log error but don't fail the operation
		fmt.Printf("Warning: failed to cleanup old refresh tokens: %v\n", err)
	}
	
	// Create refresh token record
	refreshToken := &RefreshToken{
		UserID:    userID,
		TokenHash: tokenHash,
		ExpiresAt: time.Now().Add(RefreshTokenTTL),
		CreatedAt: time.Now(),
		UserAgent: userAgent,
		IPAddress: ipAddress,
	}
	
	// Save to database
	if err := db.DB.Create(refreshToken).Error; err != nil {
		return "", nil, fmt.Errorf("failed to save refresh token: %w", err)
	}
	
	return token, refreshToken, nil
}

// ValidateRefreshToken validates a refresh token and returns the associated user ID
func ValidateRefreshToken(token string) (uint, error) {
	// Hash the provided token
	hasher := sha256.New()
	hasher.Write([]byte(token))
	tokenHash := hex.EncodeToString(hasher.Sum(nil))
	
	// Find the token in database
	var refreshToken RefreshToken
	if err := db.DB.Where("token_hash = ?", tokenHash).First(&refreshToken).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return 0, ErrInvalidRefreshToken
		}
		return 0, fmt.Errorf("database error: %w", err)
	}
	
	// Check if token is revoked
	if refreshToken.IsRevoked {
		return 0, ErrRevokedRefreshToken
	}
	
	// Check if token is expired
	if time.Now().After(refreshToken.ExpiresAt) {
		return 0, ErrExpiredRefreshToken
	}
	
	// Update last used timestamp
	now := time.Now()
	refreshToken.LastUsedAt = &now
	db.DB.Save(&refreshToken)
	
	return refreshToken.UserID, nil
}

// RevokeRefreshToken revokes a specific refresh token
func RevokeRefreshToken(token string, reason string) error {
	// Hash the provided token
	hasher := sha256.New()
	hasher.Write([]byte(token))
	tokenHash := hex.EncodeToString(hasher.Sum(nil))
	
	now := time.Now()
	return db.DB.Model(&RefreshToken{}).
		Where("token_hash = ?", tokenHash).
		Updates(map[string]interface{}{
			"is_revoked":     true,
			"revoked_at":     now,
			"revoked_reason": reason,
		}).Error
}

// RevokeAllUserRefreshTokens revokes all refresh tokens for a user
func RevokeAllUserRefreshTokens(userID uint, reason string) error {
	now := time.Now()
	return db.DB.Model(&RefreshToken{}).
		Where("user_id = ? AND is_revoked = ?", userID, false).
		Updates(map[string]interface{}{
			"is_revoked":     true,
			"revoked_at":     now,
			"revoked_reason": reason,
		}).Error
}

// cleanupOldRefreshTokens removes expired tokens and limits active tokens per user
func cleanupOldRefreshTokens(userID uint) error {
	// Delete expired tokens
	if err := db.DB.Where("user_id = ? AND expires_at < ?", userID, time.Now()).
		Delete(&RefreshToken{}).Error; err != nil {
		return err
	}
	
	// Get active tokens count
	var count int64
	db.DB.Model(&RefreshToken{}).
		Where("user_id = ? AND is_revoked = ? AND expires_at > ?", userID, false, time.Now()).
		Count(&count)
	
	// If user has too many active tokens, revoke the oldest ones
	if count >= MaxRefreshTokens {
		var oldestTokens []RefreshToken
		db.DB.Where("user_id = ? AND is_revoked = ? AND expires_at > ?", userID, false, time.Now()).
			Order("created_at ASC").
			Limit(int(count - MaxRefreshTokens + 1)).
			Find(&oldestTokens)
		
		for _, token := range oldestTokens {
			now := time.Now()
			token.IsRevoked = true
			token.RevokedAt = &now
			token.RevokedReason = "Maximum token limit exceeded"
			db.DB.Save(&token)
		}
	}
	
	return nil
}

// CleanupExpiredTokens removes all expired refresh tokens from the database
func CleanupExpiredTokens() error {
	return db.DB.Where("expires_at < ?", time.Now()).Delete(&RefreshToken{}).Error
}

// GetActiveRefreshTokens returns all active refresh tokens for a user
func GetActiveRefreshTokens(userID uint) ([]RefreshToken, error) {
	var tokens []RefreshToken
	err := db.DB.Where("user_id = ? AND is_revoked = ? AND expires_at > ?", 
		userID, false, time.Now()).
		Order("created_at DESC").
		Find(&tokens).Error
	return tokens, err
}

// RefreshTokenInfo provides information about a refresh token without exposing the actual token
type RefreshTokenInfo struct {
	ID         string    `json:"id"`
	CreatedAt  time.Time `json:"created_at"`
	ExpiresAt  time.Time `json:"expires_at"`
	LastUsedAt *time.Time `json:"last_used_at,omitempty"`
	UserAgent  string    `json:"user_agent"`
	IPAddress  string    `json:"ip_address"`
	IsActive   bool      `json:"is_active"`
}

// GetRefreshTokenInfo returns information about a user's refresh tokens
func GetRefreshTokenInfo(userID uint) ([]RefreshTokenInfo, error) {
	tokens, err := GetActiveRefreshTokens(userID)
	if err != nil {
		return nil, err
	}
	
	info := make([]RefreshTokenInfo, len(tokens))
	for i, token := range tokens {
		info[i] = RefreshTokenInfo{
			ID:         token.ID,
			CreatedAt:  token.CreatedAt,
			ExpiresAt:  token.ExpiresAt,
			LastUsedAt: token.LastUsedAt,
			UserAgent:  token.UserAgent,
			IPAddress:  token.IPAddress,
			IsActive:   !token.IsRevoked && time.Now().Before(token.ExpiresAt),
		}
	}
	
	return info, nil
}