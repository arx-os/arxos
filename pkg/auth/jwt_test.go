package auth

import (
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestDefaultJWTConfig(t *testing.T) {
	t.Run("development mode with no secret", func(t *testing.T) {
		// Set development environment
		os.Setenv("ARXOS_ENV", "development")
		os.Unsetenv("ARXOS_JWT_SECRET")
		defer os.Unsetenv("ARXOS_ENV")

		config := DefaultJWTConfig()

		assert.NotEmpty(t, config.SecretKey)
		assert.Contains(t, config.SecretKey, "dev")
		assert.Equal(t, 15*time.Minute, config.AccessTokenExpiry)
		assert.Equal(t, 7*24*time.Hour, config.RefreshTokenExpiry)
		assert.Equal(t, "arxos", config.Issuer)
		assert.Equal(t, "arxos-api", config.Audience)
		assert.Equal(t, "HS256", config.Algorithm)
	})

	t.Run("production mode requires secret", func(t *testing.T) {
		// Set production environment
		os.Setenv("ARXOS_ENV", "production")
		os.Unsetenv("ARXOS_JWT_SECRET")
		defer os.Unsetenv("ARXOS_ENV")

		// Should panic without secret
		assert.Panics(t, func() {
			DefaultJWTConfig()
		})
	})

	t.Run("uses environment secret when provided", func(t *testing.T) {
		testSecret := "test-secret-key-for-testing"
		os.Setenv("ARXOS_JWT_SECRET", testSecret)
		defer os.Unsetenv("ARXOS_JWT_SECRET")

		config := DefaultJWTConfig()

		assert.Equal(t, testSecret, config.SecretKey)
	})
}

func TestNewJWTManager(t *testing.T) {
	t.Run("creates manager with HMAC algorithm", func(t *testing.T) {
		config := &JWTConfig{
			SecretKey:          "test-secret-key",
			AccessTokenExpiry:  15 * time.Minute,
			RefreshTokenExpiry: 7 * 24 * time.Hour,
			Issuer:             "test",
			Audience:           "test-api",
			Algorithm:          "HS256",
		}

		manager, err := NewJWTManager(config)

		require.NoError(t, err)
		assert.NotNil(t, manager)
		assert.NotNil(t, manager.signingKey)
		assert.NotNil(t, manager.verifyKey)
	})

	t.Run("creates manager with RSA algorithm", func(t *testing.T) {
		config := &JWTConfig{
			SecretKey:          "test-secret-key",
			AccessTokenExpiry:  15 * time.Minute,
			RefreshTokenExpiry: 7 * 24 * time.Hour,
			Issuer:             "test",
			Audience:           "test-api",
			Algorithm:          "RS256",
		}

		manager, err := NewJWTManager(config)

		require.NoError(t, err)
		assert.NotNil(t, manager)
		assert.NotNil(t, manager.signingKey)
		assert.NotNil(t, manager.verifyKey)
	})

	t.Run("fails with unsupported algorithm", func(t *testing.T) {
		config := &JWTConfig{
			SecretKey:          "test-secret-key",
			AccessTokenExpiry:  15 * time.Minute,
			RefreshTokenExpiry: 7 * 24 * time.Hour,
			Issuer:             "test",
			Audience:           "test-api",
			Algorithm:          "UNSUPPORTED",
		}

		manager, err := NewJWTManager(config)

		assert.Error(t, err)
		assert.Nil(t, manager)
		assert.Contains(t, err.Error(), "unsupported JWT algorithm")
	})

	t.Run("fails with empty secret for HMAC", func(t *testing.T) {
		config := &JWTConfig{
			SecretKey:          "",
			AccessTokenExpiry:  15 * time.Minute,
			RefreshTokenExpiry: 7 * 24 * time.Hour,
			Issuer:             "test",
			Audience:           "test-api",
			Algorithm:          "HS256",
		}

		manager, err := NewJWTManager(config)

		assert.Error(t, err)
		assert.Nil(t, manager)
		assert.Contains(t, err.Error(), "HMAC secret key cannot be empty")
	})
}

func TestGenerateTokenPair(t *testing.T) {
	config := &JWTConfig{
		SecretKey:          "test-secret-key-for-jwt-testing",
		AccessTokenExpiry:  15 * time.Minute,
		RefreshTokenExpiry: 7 * 24 * time.Hour,
		Issuer:             "test",
		Audience:           "test-api",
		Algorithm:          "HS256",
	}

	manager, err := NewJWTManager(config)
	require.NoError(t, err)

	t.Run("generates valid token pair", func(t *testing.T) {
		req := &TokenGenerationRequest{
			UserID:         "user123",
			Email:          "test@example.com",
			Username:       "testuser",
			Role:           "admin",
			OrganizationID: "org123",
			Permissions:    []string{"read", "write"},
			SessionID:      "session123",
			DeviceInfo:     map[string]any{"platform": "web"},
		}

		tokenPair, err := manager.GenerateTokenPair(req)

		require.NoError(t, err)
		assert.NotNil(t, tokenPair)
		assert.NotEmpty(t, tokenPair.AccessToken)
		assert.NotEmpty(t, tokenPair.RefreshToken)
		assert.Equal(t, "Bearer", tokenPair.TokenType)
		assert.Greater(t, tokenPair.ExpiresIn, int64(0))
		assert.False(t, tokenPair.ExpiresAt.IsZero())
	})

	t.Run("access and refresh tokens are different", func(t *testing.T) {
		req := &TokenGenerationRequest{
			UserID:   "user123",
			Email:    "test@example.com",
			Username: "testuser",
			Role:     "user",
		}

		tokenPair, err := manager.GenerateTokenPair(req)

		require.NoError(t, err)
		assert.NotEqual(t, tokenPair.AccessToken, tokenPair.RefreshToken)
	})
}

func TestValidateToken(t *testing.T) {
	config := &JWTConfig{
		SecretKey:          "test-secret-key-for-jwt-testing",
		AccessTokenExpiry:  15 * time.Minute,
		RefreshTokenExpiry: 7 * 24 * time.Hour,
		Issuer:             "test",
		Audience:           "test-api",
		Algorithm:          "HS256",
	}

	manager, err := NewJWTManager(config)
	require.NoError(t, err)

	t.Run("validates valid token", func(t *testing.T) {
		req := &TokenGenerationRequest{
			UserID:         "user123",
			Email:          "test@example.com",
			Username:       "testuser",
			Role:           "admin",
			OrganizationID: "org123",
			Permissions:    []string{"read", "write"},
			SessionID:      "session123",
		}

		tokenPair, err := manager.GenerateTokenPair(req)
		require.NoError(t, err)

		claims, err := manager.ValidateToken(tokenPair.AccessToken)

		assert.NoError(t, err)
		assert.NotNil(t, claims)
		assert.Equal(t, req.UserID, claims.UserID)
		assert.Equal(t, req.Email, claims.Email)
		assert.Equal(t, req.Username, claims.Username)
		assert.Equal(t, req.Role, claims.Role)
		assert.Equal(t, req.OrganizationID, claims.OrganizationID)
		assert.Equal(t, req.Permissions, claims.Permissions)
		assert.Equal(t, req.SessionID, claims.SessionID)
	})

	t.Run("fails with invalid token string", func(t *testing.T) {
		claims, err := manager.ValidateToken("invalid.token.string")

		assert.Error(t, err)
		assert.Nil(t, claims)
	})

	t.Run("fails with empty token", func(t *testing.T) {
		claims, err := manager.ValidateToken("")

		assert.Error(t, err)
		assert.Nil(t, claims)
	})

	t.Run("fails with wrong issuer", func(t *testing.T) {
		// Create manager with different issuer
		wrongConfig := &JWTConfig{
			SecretKey:          "test-secret-key-for-jwt-testing",
			AccessTokenExpiry:  15 * time.Minute,
			RefreshTokenExpiry: 7 * 24 * time.Hour,
			Issuer:             "wrong-issuer",
			Audience:           "test-api",
			Algorithm:          "HS256",
		}
		wrongManager, err := NewJWTManager(wrongConfig)
		require.NoError(t, err)

		req := &TokenGenerationRequest{
			UserID:   "user123",
			Email:    "test@example.com",
			Username: "testuser",
			Role:     "user",
		}
		tokenPair, err := wrongManager.GenerateTokenPair(req)
		require.NoError(t, err)

		// Try to validate with original manager (different issuer)
		claims, err := manager.ValidateToken(tokenPair.AccessToken)

		assert.Error(t, err)
		assert.Nil(t, claims)
		assert.Contains(t, err.Error(), "invalid token issuer")
	})
}

func TestRefreshToken(t *testing.T) {
	config := &JWTConfig{
		SecretKey:          "test-secret-key-for-jwt-testing",
		AccessTokenExpiry:  15 * time.Minute,
		RefreshTokenExpiry: 7 * 24 * time.Hour,
		Issuer:             "test",
		Audience:           "test-api",
		Algorithm:          "HS256",
	}

	manager, err := NewJWTManager(config)
	require.NoError(t, err)

	t.Run("refreshes token successfully", func(t *testing.T) {
		req := &TokenGenerationRequest{
			UserID:   "user123",
			Email:    "test@example.com",
			Username: "testuser",
			Role:     "user",
		}

		originalPair, err := manager.GenerateTokenPair(req)
		require.NoError(t, err)

		time.Sleep(1 * time.Second) // Ensure different timestamps

		newPair, err := manager.RefreshToken(originalPair.RefreshToken)

		assert.NoError(t, err)
		assert.NotNil(t, newPair)
		assert.NotEqual(t, originalPair.AccessToken, newPair.AccessToken)
		assert.NotEqual(t, originalPair.RefreshToken, newPair.RefreshToken)
	})

	t.Run("fails with invalid refresh token", func(t *testing.T) {
		newPair, err := manager.RefreshToken("invalid.refresh.token")

		assert.Error(t, err)
		assert.Nil(t, newPair)
		assert.Contains(t, err.Error(), "invalid refresh token")
	})
}

func TestExtractTokenFromHeader(t *testing.T) {
	t.Run("extracts valid bearer token", func(t *testing.T) {
		header := "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

		token, err := ExtractTokenFromHeader(header)

		assert.NoError(t, err)
		assert.Equal(t, "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", token)
	})

	t.Run("fails with empty header", func(t *testing.T) {
		token, err := ExtractTokenFromHeader("")

		assert.Error(t, err)
		assert.Empty(t, token)
		assert.Contains(t, err.Error(), "missing authorization header")
	})

	t.Run("fails without Bearer prefix", func(t *testing.T) {
		header := "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

		token, err := ExtractTokenFromHeader(header)

		assert.Error(t, err)
		assert.Empty(t, token)
		assert.Contains(t, err.Error(), "invalid authorization header format")
	})

	t.Run("fails with Bearer but no token", func(t *testing.T) {
		header := "Bearer "

		token, err := ExtractTokenFromHeader(header)

		assert.Error(t, err)
		assert.Empty(t, token)
		assert.Contains(t, err.Error(), "empty token")
	})
}

func TestGenerateRSAKeyPair(t *testing.T) {
	t.Run("generates valid RSA key pair", func(t *testing.T) {
		privateKey, publicKey, err := GenerateRSAKeyPair()

		assert.NoError(t, err)
		assert.NotEmpty(t, privateKey)
		assert.NotEmpty(t, publicKey)
		assert.Contains(t, privateKey, "BEGIN RSA PRIVATE KEY")
		assert.Contains(t, publicKey, "BEGIN RSA PUBLIC KEY")
	})
}

func TestIsTokenExpired(t *testing.T) {
	config := &JWTConfig{
		SecretKey:          "test-secret-key-for-jwt-testing",
		AccessTokenExpiry:  1 * time.Second, // Short expiry for testing
		RefreshTokenExpiry: 7 * 24 * time.Hour,
		Issuer:             "test",
		Audience:           "test-api",
		Algorithm:          "HS256",
	}

	manager, err := NewJWTManager(config)
	require.NoError(t, err)

	t.Run("detects non-expired token", func(t *testing.T) {
		req := &TokenGenerationRequest{
			UserID:   "user123",
			Email:    "test@example.com",
			Username: "testuser",
			Role:     "user",
		}

		tokenPair, err := manager.GenerateTokenPair(req)
		require.NoError(t, err)

		expired, err := IsTokenExpired(tokenPair.AccessToken)

		assert.NoError(t, err)
		assert.False(t, expired)
	})

	t.Run("detects expired token", func(t *testing.T) {
		req := &TokenGenerationRequest{
			UserID:   "user123",
			Email:    "test@example.com",
			Username: "testuser",
			Role:     "user",
		}

		tokenPair, err := manager.GenerateTokenPair(req)
		require.NoError(t, err)

		// Wait for token to expire
		time.Sleep(2 * time.Second)

		expired, err := IsTokenExpired(tokenPair.AccessToken)

		assert.NoError(t, err)
		assert.True(t, expired)
	})

	t.Run("fails with invalid token", func(t *testing.T) {
		expired, err := IsTokenExpired("invalid.token.string")

		assert.Error(t, err)
		assert.False(t, expired)
	})
}

func TestTokenClaims(t *testing.T) {
	config := &JWTConfig{
		SecretKey:          "test-secret-key-for-jwt-testing",
		AccessTokenExpiry:  15 * time.Minute,
		RefreshTokenExpiry: 7 * 24 * time.Hour,
		Issuer:             "test",
		Audience:           "test-api",
		Algorithm:          "HS256",
	}

	manager, err := NewJWTManager(config)
	require.NoError(t, err)

	t.Run("includes all provided claims", func(t *testing.T) {
		deviceInfo := map[string]any{
			"platform": "web",
			"browser":  "chrome",
			"version":  "100.0",
		}

		req := &TokenGenerationRequest{
			UserID:         "user123",
			Email:          "test@example.com",
			Username:       "testuser",
			Role:           "admin",
			OrganizationID: "org123",
			Permissions:    []string{"read", "write", "delete"},
			SessionID:      "session123",
			DeviceInfo:     deviceInfo,
		}

		tokenPair, err := manager.GenerateTokenPair(req)
		require.NoError(t, err)

		claims, err := manager.ValidateToken(tokenPair.AccessToken)
		require.NoError(t, err)

		assert.Equal(t, req.UserID, claims.UserID)
		assert.Equal(t, req.Email, claims.Email)
		assert.Equal(t, req.Username, claims.Username)
		assert.Equal(t, req.Role, claims.Role)
		assert.Equal(t, req.OrganizationID, claims.OrganizationID)
		assert.Equal(t, req.Permissions, claims.Permissions)
		assert.Equal(t, req.SessionID, claims.SessionID)
		assert.Equal(t, deviceInfo, claims.DeviceInfo)
	})
}
