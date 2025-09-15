package services

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v4"
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
	"golang.org/x/crypto/bcrypt"
)

// AuthService handles authentication and authorization
type AuthService struct {
	db        database.DB
	jwtSecret []byte
	jwtExpiry time.Duration
}

// NewAuthService creates a new authentication service
func NewAuthService(db database.DB, jwtSecret string, jwtExpiry time.Duration) *AuthService {
	return &AuthService{
		db:        db,
		jwtSecret: []byte(jwtSecret),
		jwtExpiry: jwtExpiry,
	}
}

// Login authenticates a user and returns a JWT token
func (s *AuthService) Login(ctx context.Context, username, password string) (*models.AuthToken, error) {
	// Get user by email (username can be email)
	user, err := s.db.GetUserByEmail(ctx, username)
	if err != nil {
		logger.Debug("Login failed for user %s: %v", username, err)
		return nil, fmt.Errorf("invalid credentials")
	}

	// Verify password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
		logger.Debug("Password mismatch for user %s", username)
		return nil, fmt.Errorf("invalid credentials")
	}

	// Check if user is active
	if user.Status != "active" {
		logger.Warn("Login attempt for inactive user %s", username)
		return nil, fmt.Errorf("account is not active")
	}

	// Generate tokens
	accessToken, err := s.generateJWT(user)
	if err != nil {
		return nil, fmt.Errorf("failed to generate access token: %w", err)
	}

	refreshToken, err := s.generateRefreshToken()
	if err != nil {
		return nil, fmt.Errorf("failed to generate refresh token: %w", err)
	}

	// Create session
	session := &models.UserSession{
		ID:           generateID(),
		UserID:       user.ID,
		Token:        accessToken,
		RefreshToken: refreshToken,
		ExpiresAt:    time.Now().Add(s.jwtExpiry),
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	if err := s.db.CreateSession(ctx, session); err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}

	// Update last login
	user.LastLogin = timePtr(time.Now())
	if err := s.db.UpdateUser(ctx, user); err != nil {
		logger.Warn("Failed to update last login for user %s: %v", user.ID, err)
	}

	logger.Info("User %s logged in successfully", user.Email)

	return &models.AuthToken{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    int64(s.jwtExpiry.Seconds()),
	}, nil
}

// Logout invalidates a user's session
func (s *AuthService) Logout(ctx context.Context, token string) error {
	session, err := s.db.GetSession(ctx, token)
	if err != nil {
		return fmt.Errorf("invalid session")
	}

	if err := s.db.DeleteSession(ctx, session.ID); err != nil {
		return fmt.Errorf("failed to delete session: %w", err)
	}

	logger.Info("User session %s logged out", session.ID)
	return nil
}

// RefreshToken generates a new access token using a refresh token
func (s *AuthService) RefreshToken(ctx context.Context, refreshToken string) (*models.AuthToken, error) {
	// Get session by refresh token
	session, err := s.db.GetSessionByRefreshToken(ctx, refreshToken)
	if err != nil {
		return nil, fmt.Errorf("invalid refresh token")
	}

	// Check if session is expired
	if time.Now().After(session.ExpiresAt) {
		s.db.DeleteSession(ctx, session.ID)
		return nil, fmt.Errorf("refresh token expired")
	}

	// Get user
	user, err := s.db.GetUser(ctx, session.UserID)
	if err != nil {
		return nil, fmt.Errorf("user not found")
	}

	// Generate new access token
	newAccessToken, err := s.generateJWT(user)
	if err != nil {
		return nil, fmt.Errorf("failed to generate access token: %w", err)
	}

	// Update session
	session.Token = newAccessToken
	session.UpdatedAt = time.Now()
	if err := s.db.UpdateSession(ctx, session); err != nil {
		return nil, fmt.Errorf("failed to update session: %w", err)
	}

	return &models.AuthToken{
		AccessToken:  newAccessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    int64(s.jwtExpiry.Seconds()),
	}, nil
}

// ValidateToken validates a JWT token and returns the user ID
func (s *AuthService) ValidateToken(ctx context.Context, tokenString string) (*models.User, error) {
	// Parse and validate JWT
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return s.jwtSecret, nil
	})

	if err != nil {
		return nil, fmt.Errorf("invalid token: %w", err)
	}

	if !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}

	// Extract claims
	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return nil, fmt.Errorf("invalid token claims")
	}

	userID, ok := claims["sub"].(string)
	if !ok {
		return nil, fmt.Errorf("invalid user ID in token")
	}

	// Verify session exists
	session, err := s.db.GetSession(ctx, tokenString)
	if err != nil {
		return nil, fmt.Errorf("session not found")
	}

	if time.Now().After(session.ExpiresAt) {
		s.db.DeleteSession(ctx, session.ID)
		return nil, fmt.Errorf("session expired")
	}

	// Get user
	user, err := s.db.GetUser(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("user not found")
	}

	if user.Status != "active" {
		return nil, fmt.Errorf("user account is not active")
	}

	return user, nil
}

// ResetPassword initiates a password reset
func (s *AuthService) ResetPassword(ctx context.Context, email string) error {
	// Get user by email
	user, err := s.db.GetUserByEmail(ctx, email)
	if err != nil {
		// Don't reveal if user exists
		logger.Debug("Password reset requested for non-existent email: %s", email)
		return nil
	}

	// Generate reset token
	token, err := generateSecureToken()
	if err != nil {
		return fmt.Errorf("failed to generate reset token: %w", err)
	}

	// Create password reset token
	resetToken := &models.PasswordResetToken{
		ID:        generateID(),
		UserID:    user.ID,
		Token:     token,
		ExpiresAt: time.Now().Add(1 * time.Hour),
		CreatedAt: time.Now(),
	}

	if err := s.db.CreatePasswordResetToken(ctx, resetToken); err != nil {
		return fmt.Errorf("failed to create reset token: %w", err)
	}

	// TODO: Send email with reset link
	logger.Info("Password reset token created for user %s", user.Email)

	return nil
}

// ConfirmPasswordReset completes a password reset
func (s *AuthService) ConfirmPasswordReset(ctx context.Context, token, newPassword string) error {
	// Get reset token
	resetToken, err := s.db.GetPasswordResetToken(ctx, token)
	if err != nil {
		return fmt.Errorf("invalid or expired reset token")
	}

	// Check if expired
	if time.Now().After(resetToken.ExpiresAt) {
		return fmt.Errorf("reset token has expired")
	}

	// Check if already used
	if resetToken.Used {
		return fmt.Errorf("reset token has already been used")
	}

	// Get user
	user, err := s.db.GetUser(ctx, resetToken.UserID)
	if err != nil {
		return fmt.Errorf("user not found")
	}

	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}

	// Update user password
	user.PasswordHash = string(hashedPassword)
	user.UpdatedAt = timePtr(time.Now())
	if err := s.db.UpdateUser(ctx, user); err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}

	// Mark token as used
	if err := s.db.MarkPasswordResetTokenUsed(ctx, token); err != nil {
		logger.Warn("Failed to mark reset token as used: %v", err)
	}

	// Invalidate all existing sessions
	if err := s.db.DeleteUserSessions(ctx, user.ID); err != nil {
		logger.Warn("Failed to delete user sessions after password reset: %v", err)
	}

	logger.Info("Password reset completed for user %s", user.Email)
	return nil
}

// ChangePassword allows a user to change their password
func (s *AuthService) ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error {
	// Get user
	user, err := s.db.GetUser(ctx, userID)
	if err != nil {
		return fmt.Errorf("user not found")
	}

	// Verify old password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(oldPassword)); err != nil {
		return fmt.Errorf("current password is incorrect")
	}

	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}

	// Update password
	user.PasswordHash = string(hashedPassword)
	user.UpdatedAt = timePtr(time.Now())
	if err := s.db.UpdateUser(ctx, user); err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}

	logger.Info("Password changed for user %s", user.Email)
	return nil
}

// Helper functions

func (s *AuthService) generateJWT(user *models.User) (string, error) {
	claims := jwt.MapClaims{
		"sub":   user.ID,
		"email": user.Email,
		"name":  user.FullName,
		"role":  user.Role,
		"exp":   time.Now().Add(s.jwtExpiry).Unix(),
		"iat":   time.Now().Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(s.jwtSecret)
}

func (s *AuthService) generateRefreshToken() (string, error) {
	return generateSecureToken()
}

func generateSecureToken() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(b), nil
}

func generateID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return fmt.Sprintf("%x", b)
}

func timePtr(t time.Time) *time.Time {
	return &t
}