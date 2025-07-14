package middleware

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v4"
	"go.uber.org/zap"
)

// AuthMiddleware handles authentication and authorization
type AuthMiddleware struct {
	config AuthConfig
	logger *zap.Logger
	audit  *AuditLogger
}

// AuthConfig defines authentication configuration
type AuthConfig struct {
	JWTSecret       string            `yaml:"jwt_secret"`
	TokenExpiry     time.Duration     `yaml:"token_expiry"`
	RefreshExpiry   time.Duration     `yaml:"refresh_expiry"`
	Roles           []string          `yaml:"roles"`
	SkipAuthPaths   []string          `yaml:"skip_auth_paths"`
	OAuth2Enabled   bool              `yaml:"oauth2_enabled"`
	OAuth2Providers []OAuth2Provider  `yaml:"oauth2_providers"`
	APIKeyEnabled   bool              `yaml:"api_key_enabled"`
	APIKeys         map[string]APIKey `yaml:"api_keys"`
	AuditLogging    bool              `yaml:"audit_logging"`
}

// OAuth2Provider defines OAuth2 provider configuration
type OAuth2Provider struct {
	Name         string   `yaml:"name"`
	ClientID     string   `yaml:"client_id"`
	ClientSecret string   `yaml:"client_secret"`
	AuthURL      string   `yaml:"auth_url"`
	TokenURL     string   `yaml:"token_url"`
	UserInfoURL  string   `yaml:"user_info_url"`
	Scopes       []string `yaml:"scopes"`
}

// APIKey defines API key configuration
type APIKey struct {
	Key       string     `yaml:"key"`
	UserID    string     `yaml:"user_id"`
	Username  string     `yaml:"username"`
	Roles     []string   `yaml:"roles"`
	ExpiresAt *time.Time `yaml:"expires_at"`
	CreatedAt time.Time  `yaml:"created_at"`
}

// UserContext holds user information from authentication
type UserContext struct {
	UserID      string   `json:"user_id"`
	Username    string   `json:"username"`
	Email       string   `json:"email"`
	Roles       []string `json:"roles"`
	Token       string   `json:"token"`
	AuthMethod  string   `json:"auth_method"`
	Provider    string   `json:"provider,omitempty"`
	Permissions []string `json:"permissions"`
}

// JWTClaims represents JWT token claims
type JWTClaims struct {
	UserID      string   `json:"user_id"`
	Username    string   `json:"username"`
	Email       string   `json:"email"`
	Roles       []string `json:"roles"`
	AuthMethod  string   `json:"auth_method"`
	Provider    string   `json:"provider,omitempty"`
	Permissions []string `json:"permissions"`
	jwt.RegisteredClaims
}

// RefreshTokenClaims represents refresh token claims
type RefreshTokenClaims struct {
	UserID    string `json:"user_id"`
	TokenType string `json:"token_type"`
	jwt.RegisteredClaims
}

// AuditLogger handles audit logging
type AuditLogger struct {
	logger *zap.Logger
}

// NewAuthMiddleware creates a new authentication middleware
func NewAuthMiddleware(config AuthConfig) (*AuthMiddleware, error) {
	if config.JWTSecret == "" {
		return nil, fmt.Errorf("JWT secret cannot be empty")
	}

	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	audit := &AuditLogger{
		logger: logger,
	}

	middleware := &AuthMiddleware{
		config: config,
		logger: logger,
		audit:  audit,
	}

	return middleware, nil
}

// Middleware returns the authentication middleware function
func (am *AuthMiddleware) Middleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if path should skip authentication
			if am.shouldSkipAuth(r.URL.Path) {
				next.ServeHTTP(w, r)
				return
			}

			// Try different authentication methods
			userContext, err := am.authenticateRequest(r)
			if err != nil {
				am.logger.Warn("Authentication failed",
					zap.String("path", r.URL.Path),
					zap.Error(err),
				)
				am.audit.LogAuthFailure(r, err)
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
				return
			}

			// Add user context to request
			ctx := context.WithValue(r.Context(), "user", userContext)
			next.ServeHTTP(w, r.WithContext(ctx))

			// Log successful authentication
			am.audit.LogAuthSuccess(r, userContext)
		})
	}
}

// authenticateRequest tries different authentication methods
func (am *AuthMiddleware) authenticateRequest(r *http.Request) (*UserContext, error) {
	// Try JWT token first
	if token, err := am.extractToken(r); err == nil {
		return am.validateJWTToken(token)
	}

	// Try API key
	if apiKey, err := am.extractAPIKey(r); err == nil {
		return am.validateAPIKey(apiKey)
	}

	// Try OAuth2 if enabled
	if am.config.OAuth2Enabled {
		if oauthToken, err := am.extractOAuth2Token(r); err == nil {
			return am.validateOAuth2Token(oauthToken)
		}
	}

	return nil, fmt.Errorf("no valid authentication method found")
}

// shouldSkipAuth checks if the path should skip authentication
func (am *AuthMiddleware) shouldSkipAuth(path string) bool {
	for _, skipPath := range am.config.SkipAuthPaths {
		if strings.HasPrefix(path, skipPath) {
			return true
		}
	}
	return false
}

// extractToken extracts JWT token from request
func (am *AuthMiddleware) extractToken(r *http.Request) (string, error) {
	// Check Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader != "" {
		if strings.HasPrefix(authHeader, "Bearer ") {
			return strings.TrimPrefix(authHeader, "Bearer "), nil
		}
	}

	// Check X-Auth-Token header
	token := r.Header.Get("X-Auth-Token")
	if token != "" {
		return token, nil
	}

	// Check query parameter
	token = r.URL.Query().Get("token")
	if token != "" {
		return token, nil
	}

	return "", fmt.Errorf("no token found in request")
}

// validateJWTToken validates JWT token and returns user context
func (am *AuthMiddleware) validateJWTToken(tokenString string) (*UserContext, error) {
	token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
		// Validate signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(am.config.JWTSecret), nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to parse token: %w", err)
	}

	if claims, ok := token.Claims.(*JWTClaims); ok && token.Valid {
		return &UserContext{
			UserID:      claims.UserID,
			Username:    claims.Username,
			Email:       claims.Email,
			Roles:       claims.Roles,
			Token:       tokenString,
			AuthMethod:  claims.AuthMethod,
			Provider:    claims.Provider,
			Permissions: claims.Permissions,
		}, nil
	}

	return nil, fmt.Errorf("invalid token")
}

// extractAPIKey extracts API key from request
func (am *AuthMiddleware) extractAPIKey(r *http.Request) (string, error) {
	// Check X-API-Key header
	apiKey := r.Header.Get("X-API-Key")
	if apiKey != "" {
		return apiKey, nil
	}

	// Check Authorization header with API key format
	authHeader := r.Header.Get("Authorization")
	if authHeader != "" && strings.HasPrefix(authHeader, "ApiKey ") {
		return strings.TrimPrefix(authHeader, "ApiKey "), nil
	}

	// Check query parameter
	apiKey = r.URL.Query().Get("api_key")
	if apiKey != "" {
		return apiKey, nil
	}

	return "", fmt.Errorf("no API key found in request")
}

// validateAPIKey validates API key and returns user context
func (am *AuthMiddleware) validateAPIKey(apiKey string) (*UserContext, error) {
	if !am.config.APIKeyEnabled {
		return nil, fmt.Errorf("API key authentication is disabled")
	}

	keyConfig, exists := am.config.APIKeys[apiKey]
	if !exists {
		return nil, fmt.Errorf("invalid API key")
	}

	// Check if API key is expired
	if keyConfig.ExpiresAt != nil && time.Now().After(*keyConfig.ExpiresAt) {
		return nil, fmt.Errorf("API key has expired")
	}

	return &UserContext{
		UserID:     keyConfig.UserID,
		Username:   keyConfig.Username,
		Roles:      keyConfig.Roles,
		Token:      apiKey,
		AuthMethod: "api_key",
	}, nil
}

// extractOAuth2Token extracts OAuth2 token from request
func (am *AuthMiddleware) extractOAuth2Token(r *http.Request) (string, error) {
	// Check Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader != "" && strings.HasPrefix(authHeader, "OAuth2 ") {
		return strings.TrimPrefix(authHeader, "OAuth2 "), nil
	}

	// Check X-OAuth2-Token header
	token := r.Header.Get("X-OAuth2-Token")
	if token != "" {
		return token, nil
	}

	return "", fmt.Errorf("no OAuth2 token found in request")
}

// validateOAuth2Token validates OAuth2 token and returns user context
func (am *AuthMiddleware) validateOAuth2Token(token string) (*UserContext, error) {
	// This is a simplified OAuth2 validation
	// In a real implementation, you would validate against the OAuth2 provider
	for _, provider := range am.config.OAuth2Providers {
		// Validate token with provider
		userInfo, err := am.validateWithOAuth2Provider(provider, token)
		if err == nil {
			return userInfo, nil
		}
	}

	return nil, fmt.Errorf("OAuth2 token validation failed")
}

// validateWithOAuth2Provider validates token with specific OAuth2 provider
func (am *AuthMiddleware) validateWithOAuth2Provider(provider OAuth2Provider, token string) (*UserContext, error) {
	// This is a placeholder implementation
	// In a real implementation, you would make HTTP requests to validate the token
	return &UserContext{
		UserID:     "oauth2_user",
		Username:   "oauth2_user",
		Email:      "oauth2@example.com",
		Roles:      []string{"user"},
		Token:      token,
		AuthMethod: "oauth2",
		Provider:   provider.Name,
	}, nil
}

// GenerateToken generates a new JWT token for a user
func (am *AuthMiddleware) GenerateToken(userID, username, email string, roles []string, authMethod, provider string) (string, error) {
	claims := &JWTClaims{
		UserID:     userID,
		Username:   username,
		Email:      email,
		Roles:      roles,
		AuthMethod: authMethod,
		Provider:   provider,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(am.config.TokenExpiry)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(am.config.JWTSecret))
}

// GenerateRefreshToken generates a refresh token
func (am *AuthMiddleware) GenerateRefreshToken(userID string) (string, error) {
	claims := &RefreshTokenClaims{
		UserID:    userID,
		TokenType: "refresh",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(am.config.RefreshExpiry)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(am.config.JWTSecret))
}

// GenerateAPIKey generates a new API key
func (am *AuthMiddleware) GenerateAPIKey(userID, username string, roles []string, expiry *time.Time) (string, error) {
	// Generate random API key
	keyBytes := make([]byte, 32)
	if _, err := rand.Read(keyBytes); err != nil {
		return "", fmt.Errorf("failed to generate API key: %w", err)
	}

	apiKey := base64.URLEncoding.EncodeToString(keyBytes)

	// Store API key in configuration (in a real implementation, this would be in a database)
	am.config.APIKeys[apiKey] = APIKey{
		Key:       apiKey,
		UserID:    userID,
		Username:  username,
		Roles:     roles,
		ExpiresAt: expiry,
		CreatedAt: time.Now(),
	}

	return apiKey, nil
}

// GetUserFromContext extracts user context from request context
func GetUserFromContext(ctx context.Context) (*UserContext, bool) {
	user, ok := ctx.Value("user").(*UserContext)
	return user, ok
}

// HasRole checks if user has a specific role
func (uc *UserContext) HasRole(role string) bool {
	for _, userRole := range uc.Roles {
		if userRole == role {
			return true
		}
	}
	return false
}

// HasAnyRole checks if user has any of the specified roles
func (uc *UserContext) HasAnyRole(roles []string) bool {
	for _, role := range roles {
		if uc.HasRole(role) {
			return true
		}
	}
	return false
}

// HasPermission checks if user has a specific permission
func (uc *UserContext) HasPermission(permission string) bool {
	for _, userPermission := range uc.Permissions {
		if userPermission == permission {
			return true
		}
	}
	return false
}

// LogAuthFailure logs authentication failure
func (al *AuditLogger) LogAuthFailure(r *http.Request, err error) {
	al.logger.Warn("Authentication failure",
		zap.String("ip", r.RemoteAddr),
		zap.String("path", r.URL.Path),
		zap.String("method", r.Method),
		zap.String("user_agent", r.UserAgent()),
		zap.Error(err),
	)
}

// LogAuthSuccess logs successful authentication
func (al *AuditLogger) LogAuthSuccess(r *http.Request, user *UserContext) {
	al.logger.Info("Authentication success",
		zap.String("ip", r.RemoteAddr),
		zap.String("path", r.URL.Path),
		zap.String("method", r.Method),
		zap.String("user_id", user.UserID),
		zap.String("username", user.Username),
		zap.String("auth_method", user.AuthMethod),
		zap.Strings("roles", user.Roles),
	)
}

// UpdateConfig updates the authentication configuration
func (am *AuthMiddleware) UpdateConfig(config AuthConfig) error {
	if config.JWTSecret == "" {
		return fmt.Errorf("JWT secret cannot be empty")
	}

	am.config = config
	am.logger.Info("Authentication configuration updated")

	return nil
}
