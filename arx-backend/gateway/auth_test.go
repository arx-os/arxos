package gateway

import (
	"context"
	"fmt"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestEnhancedAuthMiddleware(t *testing.T) {
	config := AuthConfig{
		JWTSecret:     "test-secret",
		TokenExpiry:   24 * time.Hour,
		RefreshExpiry: 168 * time.Hour,
		Roles:         []string{"admin", "user", "guest"},
		SkipAuthPaths: []string{"/health", "/metrics"},
		OAuth2Enabled: true,
		APIKeyEnabled: true,
		AuditLogging:  true,
		OAuth2Providers: []OAuth2Provider{
			{
				Name:         "google",
				ClientID:     "test-client-id",
				ClientSecret: "test-client-secret",
				AuthURL:      "https://accounts.google.com/o/oauth2/auth",
				TokenURL:     "https://oauth2.googleapis.com/token",
				UserInfoURL:  "https://www.googleapis.com/oauth2/v2/userinfo",
				Scopes:       []string{"openid", "email", "profile"},
			},
		},
		APIKeys: map[string]APIKey{
			"test-api-key": {
				Key:       "test-api-key",
				UserID:    "api-user-1",
				Username:  "api-user",
				Roles:     []string{"user"},
				ExpiresAt: nil,
				CreatedAt: time.Now(),
			},
		},
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)
	assert.NotNil(t, auth)
}

func TestJWTAuthentication(t *testing.T) {
	config := AuthConfig{
		JWTSecret:     "test-secret",
		TokenExpiry:   24 * time.Hour,
		RefreshExpiry: 168 * time.Hour,
		Roles:         []string{"admin", "user", "guest"},
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)

	// Generate token
	token, err := auth.GenerateToken("user-123", "testuser", "test@example.com", []string{"user"}, "jwt", "")
	require.NoError(t, err)
	assert.NotEmpty(t, token)

	// Create request with token
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("Authorization", "Bearer "+token)

	// Validate token
	userContext, err := auth.validateJWTToken(token)
	require.NoError(t, err)
	assert.Equal(t, "user-123", userContext.UserID)
	assert.Equal(t, "testuser", userContext.Username)
	assert.Equal(t, "test@example.com", userContext.Email)
	assert.Equal(t, []string{"user"}, userContext.Roles)
	assert.Equal(t, "jwt", userContext.AuthMethod)
}

func TestAPIKeyAuthentication(t *testing.T) {
	config := AuthConfig{
		JWTSecret:     "test-secret",
		TokenExpiry:   24 * time.Hour,
		APIKeyEnabled: true,
		APIKeys: map[string]APIKey{
			"test-api-key": {
				Key:       "test-api-key",
				UserID:    "api-user-1",
				Username:  "api-user",
				Roles:     []string{"user"},
				ExpiresAt: nil,
				CreatedAt: time.Now(),
			},
		},
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)

	// Test valid API key
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("X-API-Key", "test-api-key")

	userContext, err := auth.validateAPIKey("test-api-key")
	require.NoError(t, err)
	assert.Equal(t, "api-user-1", userContext.UserID)
	assert.Equal(t, "api-user", userContext.Username)
	assert.Equal(t, []string{"user"}, userContext.Roles)
	assert.Equal(t, "api_key", userContext.AuthMethod)

	// Test invalid API key
	_, err = auth.validateAPIKey("invalid-key")
	assert.Error(t, err)
}

func TestOAuth2Authentication(t *testing.T) {
	config := AuthConfig{
		JWTSecret:     "test-secret",
		TokenExpiry:   24 * time.Hour,
		OAuth2Enabled: true,
		OAuth2Providers: []OAuth2Provider{
			{
				Name:         "google",
				ClientID:     "test-client-id",
				ClientSecret: "test-client-secret",
				AuthURL:      "https://accounts.google.com/o/oauth2/auth",
				TokenURL:     "https://oauth2.googleapis.com/token",
				UserInfoURL:  "https://www.googleapis.com/oauth2/v2/userinfo",
				Scopes:       []string{"openid", "email", "profile"},
			},
		},
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)

	// Test OAuth2 token validation
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("X-OAuth2-Token", "test-oauth2-token")

	userContext, err := auth.validateOAuth2Token("test-oauth2-token")
	require.NoError(t, err)
	assert.Equal(t, "oauth2_user", userContext.UserID)
	assert.Equal(t, "oauth2_user", userContext.Username)
	assert.Equal(t, "oauth2@example.com", userContext.Email)
	assert.Equal(t, []string{"user"}, userContext.Roles)
	assert.Equal(t, "oauth2", userContext.AuthMethod)
	assert.Equal(t, "google", userContext.Provider)
}

func TestMultiMethodAuthentication(t *testing.T) {
	config := AuthConfig{
		JWTSecret:     "test-secret",
		TokenExpiry:   24 * time.Hour,
		APIKeyEnabled: true,
		OAuth2Enabled: true,
		APIKeys: map[string]APIKey{
			"test-api-key": {
				Key:       "test-api-key",
				UserID:    "api-user-1",
				Username:  "api-user",
				Roles:     []string{"user"},
				ExpiresAt: nil,
				CreatedAt: time.Now(),
			},
		},
		OAuth2Providers: []OAuth2Provider{
			{
				Name:         "google",
				ClientID:     "test-client-id",
				ClientSecret: "test-client-secret",
				AuthURL:      "https://accounts.google.com/o/oauth2/auth",
				TokenURL:     "https://oauth2.googleapis.com/token",
				UserInfoURL:  "https://www.googleapis.com/oauth2/v2/userinfo",
				Scopes:       []string{"openid", "email", "profile"},
			},
		},
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)

	// Test JWT authentication
	token, _ := auth.GenerateToken("user-123", "testuser", "test@example.com", []string{"user"}, "jwt", "")
	req1 := httptest.NewRequest("GET", "/api/test", nil)
	req1.Header.Set("Authorization", "Bearer "+token)

	userContext1, err := auth.authenticateRequest(req1)
	require.NoError(t, err)
	assert.Equal(t, "user-123", userContext1.UserID)
	assert.Equal(t, "jwt", userContext1.AuthMethod)

	// Test API key authentication
	req2 := httptest.NewRequest("GET", "/api/test", nil)
	req2.Header.Set("X-API-Key", "test-api-key")

	userContext2, err := auth.authenticateRequest(req2)
	require.NoError(t, err)
	assert.Equal(t, "api-user-1", userContext2.UserID)
	assert.Equal(t, "api_key", userContext2.AuthMethod)

	// Test OAuth2 authentication
	req3 := httptest.NewRequest("GET", "/api/test", nil)
	req3.Header.Set("X-OAuth2-Token", "test-oauth2-token")

	userContext3, err := auth.authenticateRequest(req3)
	require.NoError(t, err)
	assert.Equal(t, "oauth2_user", userContext3.UserID)
	assert.Equal(t, "oauth2", userContext3.AuthMethod)
}

func TestSkipAuthPaths(t *testing.T) {
	config := AuthConfig{
		JWTSecret:     "test-secret",
		TokenExpiry:   24 * time.Hour,
		SkipAuthPaths: []string{"/health", "/metrics", "/docs"},
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)

	// Test paths that should skip authentication
	assert.True(t, auth.shouldSkipAuth("/health"))
	assert.True(t, auth.shouldSkipAuth("/metrics"))
	assert.True(t, auth.shouldSkipAuth("/docs"))
	assert.True(t, auth.shouldSkipAuth("/health/status"))

	// Test paths that should require authentication
	assert.False(t, auth.shouldSkipAuth("/api/test"))
	assert.False(t, auth.shouldSkipAuth("/api/v1/users"))
}

func TestUserContextMethods(t *testing.T) {
	userContext := &UserContext{
		UserID:      "user-123",
		Username:    "testuser",
		Email:       "test@example.com",
		Roles:       []string{"user", "moderator"},
		Token:       "test-token",
		AuthMethod:  "jwt",
		Provider:    "google",
		Permissions: []string{"read", "write"},
	}

	// Test role checking
	assert.True(t, userContext.HasRole("user"))
	assert.True(t, userContext.HasRole("moderator"))
	assert.False(t, userContext.HasRole("admin"))

	// Test any role checking
	assert.True(t, userContext.HasAnyRole([]string{"admin", "user"}))
	assert.True(t, userContext.HasAnyRole([]string{"moderator", "admin"}))
	assert.False(t, userContext.HasAnyRole([]string{"admin", "guest"}))

	// Test permission checking
	assert.True(t, userContext.HasPermission("read"))
	assert.True(t, userContext.HasPermission("write"))
	assert.False(t, userContext.HasPermission("delete"))
}

func TestTokenGeneration(t *testing.T) {
	config := AuthConfig{
		JWTSecret:     "test-secret",
		TokenExpiry:   24 * time.Hour,
		RefreshExpiry: 168 * time.Hour,
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)

	// Test JWT token generation
	token, err := auth.GenerateToken("user-123", "testuser", "test@example.com", []string{"user"}, "jwt", "")
	require.NoError(t, err)
	assert.NotEmpty(t, token)

	// Test refresh token generation
	refreshToken, err := auth.GenerateRefreshToken("user-123")
	require.NoError(t, err)
	assert.NotEmpty(t, refreshToken)

	// Test API key generation
	apiKey, err := auth.GenerateAPIKey("user-123", "testuser", []string{"user"}, nil)
	require.NoError(t, err)
	assert.NotEmpty(t, apiKey)
	assert.Len(t, apiKey, 43) // Base64 encoded 32 bytes
}

func TestAuditLogging(t *testing.T) {
	config := AuthConfig{
		JWTSecret:    "test-secret",
		TokenExpiry:  24 * time.Hour,
		AuditLogging: true,
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)

	// Test audit logging
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("User-Agent", "test-agent")
	req.RemoteAddr = "127.0.0.1:12345"

	// Test authentication failure logging
	err = fmt.Errorf("invalid token")
	auth.audit.LogAuthFailure(req, err)

	// Test authentication success logging
	userContext := &UserContext{
		UserID:     "user-123",
		Username:   "testuser",
		AuthMethod: "jwt",
		Roles:      []string{"user"},
	}
	auth.audit.LogAuthSuccess(req, userContext)
}

func TestConfigurationValidation(t *testing.T) {
	// Test valid configuration
	config := AuthConfig{
		JWTSecret:     "test-secret",
		TokenExpiry:   24 * time.Hour,
		RefreshExpiry: 168 * time.Hour,
		Roles:         []string{"admin", "user"},
	}

	auth, err := NewAuthMiddleware(config)
	require.NoError(t, err)
	assert.NotNil(t, auth)

	// Test invalid configuration (empty JWT secret)
	invalidConfig := AuthConfig{
		JWTSecret: "",
	}

	_, err = NewAuthMiddleware(invalidConfig)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "JWT secret cannot be empty")
}

func TestContextExtraction(t *testing.T) {
	// Test user context extraction
	userContext := &UserContext{
		UserID:   "user-123",
		Username: "testuser",
		Roles:    []string{"user"},
	}

	ctx := context.WithValue(context.Background(), "user", userContext)

	extractedUser, ok := GetUserFromContext(ctx)
	assert.True(t, ok)
	assert.Equal(t, userContext, extractedUser)

	// Test missing user context
	emptyCtx := context.Background()
	_, ok = GetUserFromContext(emptyCtx)
	assert.False(t, ok)
}
