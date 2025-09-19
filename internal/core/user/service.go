package user

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v4"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// Service handles user and authentication operations
type Service struct {
	repo      Repository
	jwtSecret []byte
	jwtExpiry time.Duration
}

// NewService creates a new user service
func NewService(repo Repository, jwtSecret string, jwtExpiry time.Duration) *Service {
	return &Service{
		repo:      repo,
		jwtSecret: []byte(jwtSecret),
		jwtExpiry: jwtExpiry,
	}
}

// AuthToken represents authentication tokens
type AuthToken struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int64  `json:"expires_in"`
}

// Login authenticates a user and returns tokens
func (s *Service) Login(ctx context.Context, email, password string) (*AuthToken, error) {
	// Get user by email
	user, err := s.repo.GetByEmail(ctx, email)
	if err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}

	// Verify password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}

	// Check if user is active
	if user.Status != StatusActive {
		return nil, fmt.Errorf("account is not active")
	}

	// Generate tokens
	accessToken, err := s.generateJWT(user)
	if err != nil {
		return nil, fmt.Errorf("failed to generate access token: %w", err)
	}

	refreshToken, err := generateSecureToken()
	if err != nil {
		return nil, fmt.Errorf("failed to generate refresh token: %w", err)
	}

	// Create session
	session := &UserSession{
		ID:           uuid.New(),
		UserID:       user.ID,
		Token:        accessToken,
		RefreshToken: refreshToken,
		ExpiresAt:    time.Now().Add(s.jwtExpiry),
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	if err := s.repo.CreateSession(ctx, session); err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}

	// Update last login
	now := time.Now()
	user.LastLogin = &now
	if err := s.repo.Update(ctx, user); err != nil {
		// Log error but don't fail login
		fmt.Printf("Failed to update last login for user %s: %v\n", user.ID, err)
	}

	return &AuthToken{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    int64(s.jwtExpiry.Seconds()),
	}, nil
}

// Logout invalidates a user's session
func (s *Service) Logout(ctx context.Context, token string) error {
	session, err := s.repo.GetSession(ctx, token)
	if err != nil {
		return fmt.Errorf("invalid session")
	}

	if err := s.repo.DeleteSession(ctx, session.ID); err != nil {
		return fmt.Errorf("failed to delete session: %w", err)
	}

	return nil
}

// RefreshToken generates a new access token using a refresh token
func (s *Service) RefreshToken(ctx context.Context, refreshToken string) (*AuthToken, error) {
	// Get session by refresh token
	session, err := s.repo.GetSessionByRefreshToken(ctx, refreshToken)
	if err != nil {
		return nil, fmt.Errorf("invalid refresh token")
	}

	// Check if session is expired
	if time.Now().After(session.ExpiresAt) {
		s.repo.DeleteSession(ctx, session.ID)
		return nil, fmt.Errorf("refresh token expired")
	}

	// Get user
	user, err := s.repo.GetByID(ctx, session.UserID)
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
	if err := s.repo.UpdateSession(ctx, session); err != nil {
		return nil, fmt.Errorf("failed to update session: %w", err)
	}

	return &AuthToken{
		AccessToken:  newAccessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    int64(s.jwtExpiry.Seconds()),
	}, nil
}

// ValidateToken validates a JWT token and returns the user
func (s *Service) ValidateToken(ctx context.Context, tokenString string) (*User, error) {
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

	userIDStr, ok := claims["sub"].(string)
	if !ok {
		return nil, fmt.Errorf("invalid user ID in token")
	}

	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID format: %w", err)
	}

	// Verify session exists
	session, err := s.repo.GetSession(ctx, tokenString)
	if err != nil {
		return nil, fmt.Errorf("session not found")
	}

	if time.Now().After(session.ExpiresAt) {
		s.repo.DeleteSession(ctx, session.ID)
		return nil, fmt.Errorf("session expired")
	}

	// Get user
	user, err := s.repo.GetByID(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("user not found")
	}

	if user.Status != StatusActive {
		return nil, fmt.Errorf("user account is not active")
	}

	return user, nil
}

// CreateUser creates a new user
func (s *Service) CreateUser(ctx context.Context, email, fullName, password, role string) (*User, error) {
	// Check if user already exists
	existing, _ := s.repo.GetByEmail(ctx, email)
	if existing != nil {
		return nil, fmt.Errorf("user with email %s already exists", email)
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	// Create user
	user := NewUser(email, fullName, string(hashedPassword), role)
	if err := s.repo.Create(ctx, user); err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	return user, nil
}

// ResetPassword initiates a password reset
func (s *Service) ResetPassword(ctx context.Context, email string) error {
	// Get user by email
	user, err := s.repo.GetByEmail(ctx, email)
	if err != nil {
		// Don't reveal if user exists
		return nil
	}

	// Generate reset token
	token, err := generateSecureToken()
	if err != nil {
		return fmt.Errorf("failed to generate reset token: %w", err)
	}

	// Create password reset token
	resetToken := &PasswordResetToken{
		ID:        uuid.New(),
		UserID:    user.ID,
		Token:     token,
		ExpiresAt: time.Now().Add(1 * time.Hour),
		CreatedAt: time.Now(),
	}

	if err := s.repo.CreatePasswordResetToken(ctx, resetToken); err != nil {
		return fmt.Errorf("failed to create reset token: %w", err)
	}

	// TODO: Send email with reset link
	fmt.Printf("Password reset token created for user %s: %s\n", user.Email, token)

	return nil
}

// ConfirmPasswordReset completes a password reset
func (s *Service) ConfirmPasswordReset(ctx context.Context, token, newPassword string) error {
	// Get reset token
	resetToken, err := s.repo.GetPasswordResetToken(ctx, token)
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
	user, err := s.repo.GetByID(ctx, resetToken.UserID)
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
	user.UpdatedAt = time.Now()
	if err := s.repo.Update(ctx, user); err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}

	// Mark token as used
	if err := s.repo.MarkPasswordResetTokenUsed(ctx, token); err != nil {
		fmt.Printf("Failed to mark reset token as used: %v\n", err)
	}

	// Invalidate all existing sessions
	if err := s.repo.DeleteUserSessions(ctx, user.ID); err != nil {
		fmt.Printf("Failed to delete user sessions after password reset: %v\n", err)
	}

	return nil
}

// ChangePassword allows a user to change their password
func (s *Service) ChangePassword(ctx context.Context, userID uuid.UUID, oldPassword, newPassword string) error {
	// Get user
	user, err := s.repo.GetByID(ctx, userID)
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
	user.UpdatedAt = time.Now()
	if err := s.repo.Update(ctx, user); err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}

	return nil
}

// CleanupExpiredSessions removes expired sessions and tokens
func (s *Service) CleanupExpiredSessions(ctx context.Context) error {
	if err := s.repo.DeleteExpiredSessions(ctx); err != nil {
		return fmt.Errorf("failed to delete expired sessions: %w", err)
	}

	if err := s.repo.DeleteExpiredPasswordResetTokens(ctx); err != nil {
		return fmt.Errorf("failed to delete expired password reset tokens: %w", err)
	}

	return nil
}

// Helper functions

func (s *Service) generateJWT(user *User) (string, error) {
	claims := jwt.MapClaims{
		"sub":   user.ID.String(),
		"email": user.Email,
		"name":  user.FullName,
		"role":  user.Role,
		"exp":   time.Now().Add(s.jwtExpiry).Unix(),
		"iat":   time.Now().Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(s.jwtSecret)
}

func generateSecureToken() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(b), nil
}