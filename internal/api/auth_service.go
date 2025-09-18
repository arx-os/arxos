package api

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/email"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// AuthServiceImpl implements the AuthService interface
type AuthServiceImpl struct {
	db       database.DB
	orgSvc   OrganizationService
	emailSvc email.EmailService
}

// NewAuthService creates a new auth service
func NewAuthService(db database.DB) AuthService {
	// Use mock email service by default (can be configured later)
	return &AuthServiceImpl{
		db:       db,
		emailSvc: email.NewMockEmailService(),
	}
}

// SetOrganizationService sets the organization service (for resolving roles)
func (s *AuthServiceImpl) SetOrganizationService(orgSvc OrganizationService) {
	s.orgSvc = orgSvc
}

// SetEmailService sets the email service
func (s *AuthServiceImpl) SetEmailService(emailSvc email.EmailService) {
	s.emailSvc = emailSvc
}

// Login authenticates a user and returns tokens
func (s *AuthServiceImpl) Login(ctx context.Context, email, password string) (*AuthResponse, error) {
	// Extract request metadata from context (if available)
	ipAddress := ""
	userAgent := ""
	if reqInfo, ok := ctx.Value("requestInfo").(RequestInfo); ok {
		ipAddress = reqInfo.IPAddress
		userAgent = reqInfo.UserAgent
	}
	// Get user from database
	user, err := s.db.GetUserByEmail(ctx, email)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, errors.New("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Verify password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
		return nil, errors.New("invalid password")
	}

	// Check if user is active
	if !user.IsActive() {
		return nil, errors.New("user account is inactive")
	}

	// Generate tokens
	accessToken := s.generateToken()
	refreshToken := s.generateToken()

	// Get user's primary role and organization
	role, orgID := s.getUserPrimaryRole(ctx, user.ID)

	// Create session in database
	session := &models.UserSession{
		ID:             uuid.New().String(),
		UserID:         user.ID,
		OrganizationID: orgID,
		Token:          accessToken,
		RefreshToken:   refreshToken,
		IPAddress:      ipAddress,
		UserAgent:      userAgent,
		ExpiresAt:      time.Now().Add(15 * time.Minute),
		CreatedAt:      time.Now(),
		LastAccessAt:   time.Now(),
	}

	if err := s.db.CreateSession(ctx, session); err != nil {
		logger.Error("Failed to create session: %v", err)
		return nil, fmt.Errorf("failed to create session: %w", err)
	}

	// Update last login time
	now := time.Now()
	user.LastLogin = &now
	user.UpdatedAt = &now
	if err := s.db.UpdateUser(ctx, user); err != nil {
		logger.Error("Failed to update user last login: %v", err)
	}

	logger.Info("User %s logged in", email)

	// Convert to API User type
	apiUser := &User{
		ID:        user.ID,
		Email:     user.Email,
		Name:      user.FullName,
		OrgID:     orgID,
		Role:      role,
		Active:    user.IsActive(),
		CreatedAt: *user.CreatedAt,
		UpdatedAt: *user.UpdatedAt,
	}
	if user.LastLogin != nil {
		apiUser.LastLoginAt = *user.LastLogin
	}

	return &AuthResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    900, // 15 minutes
		User:         apiUser,
	}, nil
}

// Logout invalidates tokens
func (s *AuthServiceImpl) Logout(ctx context.Context, token string) error {
	// Get session from database
	session, err := s.db.GetSession(ctx, token)
	if err != nil {
		if err == database.ErrNotFound {
			// Token already invalid, treat as success
			return nil
		}
		return fmt.Errorf("failed to get session: %w", err)
	}

	// Delete session from database
	if err := s.db.DeleteSession(ctx, session.ID); err != nil {
		logger.Error("Failed to delete session: %v", err)
		return fmt.Errorf("failed to delete session: %w", err)
	}

	logger.Info("User logged out")
	return nil
}

// Register creates a new user account
func (s *AuthServiceImpl) Register(ctx context.Context, email, password, name string) (*User, error) {
	// Check if user already exists
	_, err := s.db.GetUserByEmail(ctx, email)
	if err == nil {
		return nil, errors.New("user already exists")
	}
	if err != database.ErrNotFound {
		return nil, fmt.Errorf("failed to check user existence: %w", err)
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	// Create user model
	now := time.Now()
	user := &models.User{
		ID:            s.generateID(),
		Email:         email,
		FullName:      name,
		PasswordHash:  string(hashedPassword),
		Status:        "active",
		EmailVerified: false,
		PhoneVerified: false,
		MFAEnabled:    false,
		CreatedAt:     &now,
		UpdatedAt:     &now,
	}

	// Store user in database
	if err := s.db.CreateUser(ctx, user); err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	logger.Info("User %s registered", email)

	// Return API user type (without password hash)
	return &User{
		ID:        user.ID,
		Email:     user.Email,
		Name:      user.FullName,
		Role:      "user",
		Active:    user.IsActive(),
		CreatedAt: *user.CreatedAt,
		UpdatedAt: *user.UpdatedAt,
	}, nil
}

// ValidateToken validates an access token
func (s *AuthServiceImpl) ValidateToken(ctx context.Context, token string) (*TokenClaims, error) {
	// Get session from database
	session, err := s.db.GetSession(ctx, token)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, errors.New("token not found")
		}
		return nil, fmt.Errorf("failed to get session: %w", err)
	}

	// Check expiration
	if time.Now().After(session.ExpiresAt) {
		// Delete expired session
		s.db.DeleteSession(ctx, session.ID)
		return nil, errors.New("token expired")
	}

	// Update last access time
	session.LastAccessAt = time.Now()
	s.db.UpdateSession(ctx, session)

	// Get user to construct claims
	user, err := s.db.GetUser(ctx, session.UserID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Get user's role
	role, orgID := s.getUserPrimaryRole(ctx, user.ID)

	// Construct claims from session
	claims := &TokenClaims{
		UserID:    session.UserID,
		Email:     user.Email,
		OrgID:     orgID,
		Role:      role,
		ExpiresAt: session.ExpiresAt,
		IssuedAt:  session.CreatedAt,
	}

	return claims, nil
}

// RefreshToken generates new tokens from refresh token
func (s *AuthServiceImpl) RefreshToken(ctx context.Context, refreshToken string) (*AuthResponse, error) {
	// Get session by refresh token
	session, err := s.db.GetSessionByRefreshToken(ctx, refreshToken)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, errors.New("invalid refresh token")
		}
		return nil, fmt.Errorf("failed to get session: %w", err)
	}

	// Check if session is expired (refresh tokens typically have longer expiry)
	// For now, we'll allow refresh as long as the session exists

	// Get user from database
	user, err := s.db.GetUser(ctx, session.UserID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, errors.New("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Generate new tokens
	newAccessToken := s.generateToken()
	newRefreshToken := s.generateToken()

	// Get user's primary role and organization
	role, orgID := s.getUserPrimaryRole(ctx, user.ID)

	// Update the existing session with new tokens
	session.Token = newAccessToken
	session.RefreshToken = newRefreshToken
	session.ExpiresAt = time.Now().Add(15 * time.Minute)
	session.OrganizationID = orgID
	session.LastAccessAt = time.Now()

	if err := s.db.UpdateSession(ctx, session); err != nil {
		logger.Error("Failed to update session: %v", err)
		return nil, fmt.Errorf("failed to update session: %w", err)
	}

	// Convert to API User type
	apiUser := &User{
		ID:        user.ID,
		Email:     user.Email,
		Name:      user.FullName,
		OrgID:     orgID,
		Role:      role,
		Active:    user.IsActive(),
		CreatedAt: *user.CreatedAt,
		UpdatedAt: *user.UpdatedAt,
	}
	if user.LastLogin != nil {
		apiUser.LastLoginAt = *user.LastLogin
	}

	return &AuthResponse{
		AccessToken:  newAccessToken,
		RefreshToken: newRefreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    900,
		User:         apiUser,
	}, nil
}

// RevokeToken revokes an access token
func (s *AuthServiceImpl) RevokeToken(ctx context.Context, token string) error {
	// Get session from database
	session, err := s.db.GetSession(ctx, token)
	if err != nil {
		if err == database.ErrNotFound {
			// Token already invalid, treat as success
			return nil
		}
		return fmt.Errorf("failed to get session: %w", err)
	}

	// Delete session
	if err := s.db.DeleteSession(ctx, session.ID); err != nil {
		return fmt.Errorf("failed to delete session: %w", err)
	}

	return nil
}

// ChangePassword changes a user's password
func (s *AuthServiceImpl) ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error {
	// Get user from database
	user, err := s.db.GetUser(ctx, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return errors.New("user not found")
		}
		return fmt.Errorf("failed to get user: %w", err)
	}

	// Verify old password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(oldPassword)); err != nil {
		return errors.New("invalid old password")
	}

	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}

	// Update password
	user.PasswordHash = string(hashedPassword)
	now := time.Now()
	user.UpdatedAt = &now
	if err := s.db.UpdateUser(ctx, user); err != nil {
		return fmt.Errorf("failed to update user: %w", err)
	}

	logger.Info("Password changed for user %s", user.Email)
	return nil
}

// ResetPassword initiates password reset
func (s *AuthServiceImpl) ResetPassword(ctx context.Context, email string) error {
	// Check if user exists
	user, err := s.db.GetUserByEmail(ctx, email)
	if err != nil {
		// Don't reveal if user exists or not for security
		if err == database.ErrNotFound {
			logger.Info("Password reset requested for non-existent email: %s", email)
			return nil
		}
		logger.Error("Failed to check user for password reset: %v", err)
		return fmt.Errorf("failed to process password reset request")
	}

	// Create password reset token
	token := generateSecureToken()
	resetToken := &models.PasswordResetToken{
		ID:        s.generateID(),
		UserID:    user.ID,
		Token:     token,
		ExpiresAt: time.Now().Add(1 * time.Hour),
		CreatedAt: time.Now(),
	}

	// Store token in database
	if err := s.db.CreatePasswordResetToken(ctx, resetToken); err != nil {
		logger.Error("Failed to store password reset token: %v", err)
		return fmt.Errorf("failed to process password reset request")
	}

	// Send password reset email
	if s.emailSvc != nil {
		if err := s.emailSvc.SendPasswordReset(ctx, email, resetToken.Token); err != nil {
			logger.Error("Failed to send password reset email: %v", err)
			// Don't fail the request if email fails, token is still valid
		}
	}

	logger.Info("Password reset token created for %s", email)
	return nil
}

// ConfirmPasswordReset confirms password reset with token
func (s *AuthServiceImpl) ConfirmPasswordReset(ctx context.Context, token, newPassword string) error {
	// Get password reset token from database
	resetToken, err := s.db.GetPasswordResetToken(ctx, token)
	if err != nil {
		if err == database.ErrNotFound {
			return errors.New("invalid or expired reset token")
		}
		return fmt.Errorf("failed to verify reset token: %w", err)
	}

	// Check if token is valid
	if resetToken.Used || time.Now().After(resetToken.ExpiresAt) {
		return errors.New("invalid or expired reset token")
	}

	// Get user
	user, err := s.db.GetUser(ctx, resetToken.UserID)
	if err != nil {
		if err == database.ErrNotFound {
			return errors.New("user not found")
		}
		return fmt.Errorf("failed to get user: %w", err)
	}

	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}

	// Update user's password
	user.PasswordHash = string(hashedPassword)
	now := time.Now()
	user.UpdatedAt = &now
	if err := s.db.UpdateUser(ctx, user); err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}

	// Mark token as used
	if err := s.db.MarkPasswordResetTokenUsed(ctx, token); err != nil {
		logger.Error("Failed to mark password reset token as used: %v", err)
		// Don't fail the request, password was already updated
	}

	// Invalidate all existing sessions for this user (force re-login)
	if err := s.db.DeleteUserSessions(ctx, user.ID); err != nil {
		logger.Error("Failed to invalidate user sessions after password reset: %v", err)
		// Don't fail the request
	}

	logger.Info("Password reset completed for user %s", user.Email)
	return nil
}

// Helper methods

func (s *AuthServiceImpl) generateToken() string {
	b := make([]byte, 32)
	rand.Read(b)
	return base64.URLEncoding.EncodeToString(b)
}

func (s *AuthServiceImpl) generateID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return fmt.Sprintf("%x", b)
}

// CreateDefaultUser creates a default admin user for testing
func (s *AuthServiceImpl) CreateDefaultUser() error {
	ctx := context.Background()

	// Check if admin user already exists
	_, err := s.db.GetUserByEmail(ctx, "admin@arxos.io")
	if err == nil {
		// User already exists
		return nil
	}
	if err != database.ErrNotFound {
		return fmt.Errorf("failed to check for existing admin user: %w", err)
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte("admin123"), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash admin password: %w", err)
	}

	// Create admin user
	now := time.Now()
	user := &models.User{
		ID:            "admin",
		Email:         "admin@arxos.io",
		FullName:      "Admin User",
		PasswordHash:  string(hashedPassword),
		Status:        "active",
		EmailVerified: true,
		PhoneVerified: false,
		MFAEnabled:    false,
		CreatedAt:     &now,
		UpdatedAt:     &now,
	}

	if err := s.db.CreateUser(ctx, user); err != nil {
		return fmt.Errorf("failed to create admin user: %w", err)
	}

	logger.Info("Created default admin user (admin@arxos.io / admin123)")
	return nil
}

// getUserPrimaryRole gets the user's primary role and organization
func (s *AuthServiceImpl) getUserPrimaryRole(ctx context.Context, userID string) (string, string) {
	// If organization service is not available, return default
	if s.orgSvc == nil {
		return "user", ""
	}

	// Get user's organizations
	orgs, err := s.orgSvc.ListOrganizations(ctx, userID)
	if err != nil {
		logger.Error("Failed to get user organizations: %v", err)
		return "user", ""
	}

	// If user has no organizations, return default
	if len(orgs) == 0 {
		return "user", ""
	}

	// Use the first organization (in a real app, we might have logic for "current" org)
	primaryOrg := orgs[0]

	// Get user's role in this organization
	role, err := s.orgSvc.GetMemberRole(ctx, primaryOrg.ID, userID)
	if err != nil {
		logger.Error("Failed to get user role in organization %s: %v", primaryOrg.ID, err)
		return "user", primaryOrg.ID
	}

	if role == nil {
		return "user", primaryOrg.ID
	}

	return string(*role), primaryOrg.ID
}

// generateSecureToken generates a cryptographically secure random token
func generateSecureToken() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		// Fallback to less secure method if crypto/rand fails
		return hex.EncodeToString([]byte(time.Now().String()))
	}
	return hex.EncodeToString(b)
}
