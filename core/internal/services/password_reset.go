package services

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"strings"
	"time"
	
	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

const (
	PasswordResetTokenLength = 32 // bytes
	PasswordResetTokenTTL    = 1 * time.Hour
)

var (
	ErrInvalidResetToken = errors.New("invalid or expired reset token")
	ErrTokenAlreadyUsed  = errors.New("reset token has already been used")
)

// PasswordResetService handles password reset operations
type PasswordResetService struct {
	db          *gorm.DB
	userService *UserService
}

// NewPasswordResetService creates a new password reset service
func NewPasswordResetService() *PasswordResetService {
	return &PasswordResetService{
		db:          db.DB,
		userService: NewUserService(),
	}
}

// PasswordResetToken represents a password reset token in the database
type PasswordResetToken struct {
	ID        string     `gorm:"type:uuid;default:gen_random_uuid();primaryKey"`
	UserID    uint       `gorm:"index;not null"`
	TokenHash string     `gorm:"uniqueIndex;not null"`
	ExpiresAt time.Time  `gorm:"not null"`
	UsedAt    *time.Time
	CreatedAt time.Time
}

// InitiatePasswordReset creates a password reset token for a user
func (s *PasswordResetService) InitiatePasswordReset(email string) (string, error) {
	// Find user by email
	var user models.User
	if err := s.db.Where("email = ?", email).First(&user).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			// Don't reveal if email exists or not for security
			return "", nil
		}
		return "", fmt.Errorf("database error: %w", err)
	}
	
	// Invalidate any existing unused reset tokens for this user
	s.invalidateExistingTokens(user.ID)
	
	// Generate reset token
	tokenBytes := make([]byte, PasswordResetTokenLength)
	if _, err := rand.Read(tokenBytes); err != nil {
		return "", fmt.Errorf("failed to generate token: %w", err)
	}
	
	token := hex.EncodeToString(tokenBytes)
	
	// Hash token for storage
	hasher := sha256.New()
	hasher.Write([]byte(token))
	tokenHash := hex.EncodeToString(hasher.Sum(nil))
	
	// Create reset token record
	resetToken := PasswordResetToken{
		UserID:    user.ID,
		TokenHash: tokenHash,
		ExpiresAt: time.Now().Add(PasswordResetTokenTTL),
		CreatedAt: time.Now(),
	}
	
	if err := s.db.Create(&resetToken).Error; err != nil {
		return "", fmt.Errorf("failed to save reset token: %w", err)
	}
	
	// TODO: Send email with reset link
	// For now, return the token (in production, this would be sent via email)
	resetURL := fmt.Sprintf("https://arxos.io/reset-password?token=%s", token)
	
	// Log for development (remove in production)
	fmt.Printf("Password reset URL for user %s: %s\n", email, resetURL)
	
	return token, nil
}

// ValidateResetToken validates a password reset token
func (s *PasswordResetService) ValidateResetToken(token string) (uint, error) {
	// Hash the provided token
	hasher := sha256.New()
	hasher.Write([]byte(token))
	tokenHash := hex.EncodeToString(hasher.Sum(nil))
	
	// Find token in database
	var resetToken PasswordResetToken
	if err := s.db.Where("token_hash = ?", tokenHash).First(&resetToken).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return 0, ErrInvalidResetToken
		}
		return 0, fmt.Errorf("database error: %w", err)
	}
	
	// Check if token has been used
	if resetToken.UsedAt != nil {
		return 0, ErrTokenAlreadyUsed
	}
	
	// Check if token is expired
	if time.Now().After(resetToken.ExpiresAt) {
		return 0, ErrInvalidResetToken
	}
	
	return resetToken.UserID, nil
}

// ResetPassword resets a user's password using a valid reset token
func (s *PasswordResetService) ResetPassword(token string, newPassword string) error {
	// Validate token and get user ID
	userID, err := s.ValidateResetToken(token)
	if err != nil {
		return err
	}
	
	// Validate password strength
	if !isStrongPassword(newPassword) {
		return ErrWeakPassword
	}
	
	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}
	
	// Start transaction
	tx := s.db.Begin()
	
	// Update user password
	if err := tx.Model(&models.User{}).Where("id = ?", userID).Updates(map[string]interface{}{
		"password":              string(hashedPassword),
		"failed_login_attempts": 0,        // Reset failed attempts
		"locked_until":          nil,      // Unlock account if it was locked
	}).Error; err != nil {
		tx.Rollback()
		return fmt.Errorf("failed to update password: %w", err)
	}
	
	// Mark token as used
	hasher := sha256.New()
	hasher.Write([]byte(token))
	tokenHash := hex.EncodeToString(hasher.Sum(nil))
	
	now := time.Now()
	if err := tx.Model(&PasswordResetToken{}).Where("token_hash = ?", tokenHash).Update("used_at", now).Error; err != nil {
		tx.Rollback()
		return fmt.Errorf("failed to mark token as used: %w", err)
	}
	
	// Invalidate all refresh tokens for this user (force re-login)
	if err := tx.Exec(`
		UPDATE refresh_tokens 
		SET is_revoked = true, revoked_at = ?, revoked_reason = ?
		WHERE user_id = ? AND is_revoked = false
	`, now, "Password reset", userID).Error; err != nil {
		tx.Rollback()
		return fmt.Errorf("failed to revoke refresh tokens: %w", err)
	}
	
	// Commit transaction
	if err := tx.Commit().Error; err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}
	
	return nil
}

// invalidateExistingTokens marks all unused reset tokens for a user as used
func (s *PasswordResetService) invalidateExistingTokens(userID uint) {
	now := time.Now()
	s.db.Model(&PasswordResetToken{}).
		Where("user_id = ? AND used_at IS NULL", userID).
		Update("used_at", now)
}

// CleanupExpiredTokens removes expired password reset tokens
func (s *PasswordResetService) CleanupExpiredTokens() error {
	// Delete tokens that are either expired or used
	return s.db.Where("expires_at < ? OR used_at IS NOT NULL", time.Now()).
		Delete(&PasswordResetToken{}).Error
}

// PasswordResetRequest represents a password reset initiation request
type PasswordResetRequest struct {
	Email string `json:"email" validate:"required,email"`
}

// PasswordResetConfirmRequest represents a password reset confirmation request
type PasswordResetConfirmRequest struct {
	Token       string `json:"token" validate:"required"`
	NewPassword string `json:"new_password" validate:"required,min=8"`
}

// GetResetTokenInfo returns information about a reset token (for validation UI)
func (s *PasswordResetService) GetResetTokenInfo(token string) (map[string]interface{}, error) {
	// Hash the provided token
	hasher := sha256.New()
	hasher.Write([]byte(token))
	tokenHash := hex.EncodeToString(hasher.Sum(nil))
	
	// Find token in database
	var resetToken PasswordResetToken
	if err := s.db.Where("token_hash = ?", tokenHash).First(&resetToken).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrInvalidResetToken
		}
		return nil, fmt.Errorf("database error: %w", err)
	}
	
	// Get user info
	var user models.User
	if err := s.db.First(&user, resetToken.UserID).Error; err != nil {
		return nil, fmt.Errorf("user not found: %w", err)
	}
	
	// Return token status
	info := map[string]interface{}{
		"valid":      resetToken.UsedAt == nil && time.Now().Before(resetToken.ExpiresAt),
		"expires_at": resetToken.ExpiresAt,
		"created_at": resetToken.CreatedAt,
		"email":      maskEmail(user.Email), // Partially mask email for privacy
	}
	
	if resetToken.UsedAt != nil {
		info["valid"] = false
		info["used_at"] = *resetToken.UsedAt
	}
	
	if time.Now().After(resetToken.ExpiresAt) {
		info["valid"] = false
		info["expired"] = true
	}
	
	return info, nil
}

// maskEmail partially masks an email address for privacy
func maskEmail(email string) string {
	parts := strings.Split(email, "@")
	if len(parts) != 2 {
		return "***"
	}
	
	username := parts[0]
	domain := parts[1]
	
	if len(username) <= 2 {
		return "***@" + domain
	}
	
	masked := username[:2] + strings.Repeat("*", len(username)-2) + "@" + domain
	return masked
}