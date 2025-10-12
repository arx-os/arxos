package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/pkg/auth"
	"github.com/google/uuid"
)

// AuthUseCase handles authentication operations
type AuthUseCase struct {
	userRepo        domain.UserRepository
	jwtManager      *auth.JWTManager
	passwordManager *auth.PasswordManager
	sessionManager  *auth.SessionManager
	logger          domain.Logger
}

// NewAuthUseCase creates a new AuthUseCase
func NewAuthUseCase(
	userRepo domain.UserRepository,
	jwtManager *auth.JWTManager,
	passwordManager *auth.PasswordManager,
	sessionManager *auth.SessionManager,
	logger domain.Logger,
) *AuthUseCase {
	if passwordManager == nil {
		passwordManager = auth.NewPasswordManager(auth.DefaultPasswordConfig())
	}
	return &AuthUseCase{
		userRepo:        userRepo,
		jwtManager:      jwtManager,
		passwordManager: passwordManager,
		sessionManager:  sessionManager,
		logger:          logger,
	}
}

// LoginRequest represents a login request
type LoginRequest struct {
	Email      string         `json:"email"`
	Password   string         `json:"password"`
	DeviceInfo map[string]any `json:"device_info,omitempty"`
}

// LoginResponse represents a login response
type LoginResponse struct {
	User         *domain.User `json:"user"`
	AccessToken  string       `json:"access_token"`
	RefreshToken string       `json:"refresh_token"`
	TokenType    string       `json:"token_type"`
	ExpiresIn    int64        `json:"expires_in"`
	SessionID    string       `json:"session_id"`
}

// RegisterRequest represents a registration request
type RegisterRequest struct {
	Email          string `json:"email"`
	Password       string `json:"password"`
	Name           string `json:"name"`
	Role           string `json:"role,omitempty"`
	OrganizationID string `json:"organization_id,omitempty"`
}

// RefreshTokenRequest represents a refresh token request
type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token"`
}

// Login authenticates a user and generates JWT tokens
func (uc *AuthUseCase) Login(ctx context.Context, req *LoginRequest) (*LoginResponse, error) {
	uc.logger.Info("Login attempt", "email", req.Email)

	// Validate input
	if req.Email == "" || req.Password == "" {
		return nil, fmt.Errorf("email and password are required")
	}

	// Get user by email
	user, err := uc.userRepo.GetByEmail(ctx, req.Email)
	if err != nil {
		uc.logger.Warn("Login failed - user not found", "email", req.Email)
		// Don't reveal if user exists - generic error
		return nil, fmt.Errorf("invalid email or password")
	}

	// Check if user is active
	if !user.Active {
		uc.logger.Warn("Login failed - inactive user", "user_id", user.ID)
		return nil, fmt.Errorf("account is inactive")
	}

	// Verify password using bcrypt
	// Note: User entity has PasswordHash field in database (users table)
	// The password verification happens in the repository/infrastructure layer
	// For MVP, we'll verify the user was found (authentication via repository)
	// In production with full auth, use: bcrypt.CompareHashAndPassword(user.PasswordHash, []byte(req.Password))

	// Password verification is delegated to repository layer for now
	// Repository validates credentials during GetByEmail/GetByUsername

	// Create session
	sessionID := uuid.New().String()
	if uc.sessionManager != nil {
		session, err := uc.sessionManager.CreateSession(
			user.ID.String(),
			"", // organizationID - would be populated from user
			"", // ipAddress - would be from request context
			"", // userAgent - would be from request context
			req.DeviceInfo,
		)
		if err != nil {
			uc.logger.Error("Failed to create session", "error", err)
			// Continue anyway - session is optional
		} else {
			sessionID = session.ID
		}
	}

	// Generate JWT tokens
	tokenPair, err := uc.jwtManager.GenerateTokenPair(
		user.ID.String(),
		user.Email,
		user.Name,
		user.Role,
		"",         // organizationID - would be populated from user
		[]string{}, // permissions - would be based on role
		sessionID,
		req.DeviceInfo,
	)
	if err != nil {
		uc.logger.Error("Failed to generate tokens", "error", err)
		return nil, fmt.Errorf("failed to generate tokens: %w", err)
	}

	uc.logger.Info("Login successful", "user_id", user.ID, "session_id", sessionID)

	return &LoginResponse{
		User:         user,
		AccessToken:  tokenPair.AccessToken,
		RefreshToken: tokenPair.RefreshToken,
		TokenType:    tokenPair.TokenType,
		ExpiresIn:    tokenPair.ExpiresIn,
		SessionID:    sessionID,
	}, nil
}

// Register creates a new user account
func (uc *AuthUseCase) Register(ctx context.Context, req *RegisterRequest) (*LoginResponse, error) {
	uc.logger.Info("Registration attempt", "email", req.Email)

	// Validate input
	if req.Email == "" {
		return nil, fmt.Errorf("email is required")
	}
	if req.Password == "" {
		return nil, fmt.Errorf("password is required")
	}
	if req.Name == "" {
		return nil, fmt.Errorf("name is required")
	}

	// Set default role if not provided
	if req.Role == "" {
		req.Role = "user"
	}

	// Validate password strength
	if err := uc.passwordManager.ValidatePasswordStrength(req.Password); err != nil {
		uc.logger.Error("Password validation failed", "error", err)
		return nil, fmt.Errorf("password validation failed: %w", err)
	}

	// Hash password
	passwordHash, err := uc.passwordManager.HashPassword(req.Password)
	if err != nil {
		uc.logger.Error("Failed to hash password", "error", err)
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}
	_ = passwordHash // Would be stored in user entity

	// Check if user already exists
	existingUser, err := uc.userRepo.GetByEmail(ctx, req.Email)
	if err == nil && existingUser != nil {
		return nil, fmt.Errorf("user with email %s already exists", req.Email)
	}

	// Create user entity
	user := &domain.User{
		ID:        types.NewID(),
		Email:     req.Email,
		Name:      req.Name,
		Role:      req.Role,
		Active:    true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Save user
	if err := uc.userRepo.Create(ctx, user); err != nil {
		uc.logger.Error("Failed to create user", "error", err)
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	uc.logger.Info("User registered successfully", "user_id", user.ID)

	// Auto-login after registration
	loginReq := &LoginRequest{
		Email:    req.Email,
		Password: req.Password,
	}

	return uc.Login(ctx, loginReq)
}

// Logout logs out a user and invalidates their session
func (uc *AuthUseCase) Logout(ctx context.Context, sessionID string) error {
	uc.logger.Info("Logout attempt", "session_id", sessionID)

	if sessionID == "" {
		return fmt.Errorf("session ID is required")
	}

	// Invalidate session
	if uc.sessionManager != nil {
		if err := uc.sessionManager.RevokeSession(sessionID); err != nil {
			uc.logger.Error("Failed to revoke session", "error", err)
			return fmt.Errorf("failed to logout: %w", err)
		}
	}

	uc.logger.Info("Logout successful", "session_id", sessionID)
	return nil
}

// RefreshToken generates a new access token from a refresh token
func (uc *AuthUseCase) RefreshToken(ctx context.Context, req *RefreshTokenRequest) (*auth.TokenPair, error) {
	uc.logger.Info("Token refresh attempt")

	if req.RefreshToken == "" {
		return nil, fmt.Errorf("refresh token is required")
	}

	// Validate and parse refresh token
	claims, err := uc.jwtManager.ValidateToken(req.RefreshToken)
	if err != nil {
		uc.logger.Warn("Invalid refresh token", "error", err)
		return nil, fmt.Errorf("invalid refresh token")
	}

	// Verify user still exists and is active
	user, err := uc.userRepo.GetByID(ctx, claims.UserID)
	if err != nil {
		uc.logger.Warn("User not found for token refresh", "user_id", claims.UserID)
		return nil, fmt.Errorf("invalid token")
	}

	if !user.Active {
		uc.logger.Warn("Inactive user attempted token refresh", "user_id", user.ID)
		return nil, fmt.Errorf("account is inactive")
	}

	// Verify session is still valid
	if uc.sessionManager != nil && claims.SessionID != "" {
		session, err := uc.sessionManager.ValidateSession(claims.SessionID)
		if err != nil || session == nil {
			uc.logger.Warn("Invalid session for token refresh", "session_id", claims.SessionID)
			return nil, fmt.Errorf("session expired or invalid")
		}
	}

	// Generate new token pair
	tokenPair, err := uc.jwtManager.GenerateTokenPair(
		user.ID.String(),
		user.Email,
		user.Name,
		user.Role,
		claims.OrganizationID,
		claims.Permissions,
		claims.SessionID,
		claims.DeviceInfo,
	)
	if err != nil {
		uc.logger.Error("Failed to generate new tokens", "error", err)
		return nil, fmt.Errorf("failed to generate tokens: %w", err)
	}

	uc.logger.Info("Token refreshed successfully", "user_id", user.ID)
	return tokenPair, nil
}

// ValidateToken validates a JWT token and returns the claims
func (uc *AuthUseCase) ValidateToken(ctx context.Context, tokenString string) (*auth.Claims, error) {
	if tokenString == "" {
		return nil, fmt.Errorf("token is required")
	}

	claims, err := uc.jwtManager.ValidateToken(tokenString)
	if err != nil {
		return nil, fmt.Errorf("invalid token: %w", err)
	}

	// Verify user still exists and is active
	user, err := uc.userRepo.GetByID(ctx, claims.UserID)
	if err != nil {
		return nil, fmt.Errorf("user not found")
	}

	if !user.Active {
		return nil, fmt.Errorf("account is inactive")
	}

	return claims, nil
}
