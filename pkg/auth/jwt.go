// Package auth provides authentication and authorization utilities for ArxOS.
// This package handles JWT tokens, password hashing, session management,
// and role-based access control.
package auth

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"os"
	"time"

	"github.com/arx-os/arxos/pkg/errors"
	"github.com/golang-jwt/jwt/v5"
)

// JWTConfig holds configuration for JWT token generation and validation
type JWTConfig struct {
	// Secret key for signing tokens (use RSA keys in production)
	SecretKey string

	// Token expiration times
	AccessTokenExpiry  time.Duration
	RefreshTokenExpiry time.Duration

	// Issuer and audience for token validation
	Issuer   string
	Audience string

	// Algorithm for signing (default: HS256)
	Algorithm string
}

// DefaultJWTConfig returns a default JWT configuration
// SECURITY: Always load SecretKey from environment variable ARXOS_JWT_SECRET
// Never use default values in production
func DefaultJWTConfig() *JWTConfig {
	secretKey := os.Getenv("ARXOS_JWT_SECRET")
	if secretKey == "" {
		// Only allow empty secret in explicit development mode
		if os.Getenv("ARXOS_ENV") != "development" {
			panic("SECURITY ERROR: ARXOS_JWT_SECRET environment variable must be set in production. Generate a secure key with: openssl rand -base64 32")
		}
		secretKey = "arxos-dev-secret-only-for-local-development"
	}

	return &JWTConfig{
		SecretKey:          secretKey,
		AccessTokenExpiry:  15 * time.Minute,
		RefreshTokenExpiry: 7 * 24 * time.Hour, // 7 days
		Issuer:             "arxos",
		Audience:           "arxos-api",
		Algorithm:          "HS256",
	}
}

// Claims represents the JWT claims structure
type Claims struct {
	UserID         string         `json:"user_id"`
	Email          string         `json:"email"`
	Username       string         `json:"username"`
	Role           string         `json:"role"`
	OrganizationID string         `json:"organization_id,omitempty"`
	Permissions    []string       `json:"permissions,omitempty"`
	SessionID      string         `json:"session_id,omitempty"`
	DeviceInfo     map[string]any `json:"device_info,omitempty"`
	jwt.RegisteredClaims
}

// TokenPair represents a pair of access and refresh tokens
type TokenPair struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	TokenType    string    `json:"token_type"`
	ExpiresIn    int64     `json:"expires_in"`
	ExpiresAt    time.Time `json:"expires_at"`
}

// JWTManager handles JWT token operations
type JWTManager struct {
	config     *JWTConfig
	signingKey any
	verifyKey  any
}

// NewJWTManager creates a new JWT manager
func NewJWTManager(config *JWTConfig) (*JWTManager, error) {
	if config == nil {
		config = DefaultJWTConfig()
	}

	manager := &JWTManager{
		config: config,
	}

	// Set up signing key based on algorithm
	switch config.Algorithm {
	case "HS256", "HS384", "HS512":
		if err := manager.setupHMACKey(); err != nil {
			return nil, errors.Wrap(err, errors.CodeInternal, "failed to setup HMAC key")
		}
	case "RS256", "RS384", "RS512":
		if err := manager.setupRSAKeys(); err != nil {
			return nil, errors.Wrap(err, errors.CodeInternal, "failed to setup RSA keys")
		}
	default:
		return nil, errors.New(errors.CodeInvalidInput, "unsupported JWT algorithm: "+config.Algorithm)
	}

	return manager, nil
}

// setupHMACKey sets up HMAC signing key
func (m *JWTManager) setupHMACKey() error {
	if m.config.SecretKey == "" {
		return errors.New(errors.CodeInvalidInput, "HMAC secret key cannot be empty")
	}
	m.signingKey = []byte(m.config.SecretKey)
	m.verifyKey = m.signingKey
	return nil
}

// setupRSAKeys generates RSA key pair for signing
func (m *JWTManager) setupRSAKeys() error {
	// Generate RSA key pair
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return errors.Wrap(err, errors.CodeInternal, "failed to generate RSA key")
	}

	m.signingKey = privateKey
	m.verifyKey = &privateKey.PublicKey
	return nil
}

// TokenGenerationRequest contains all parameters needed to generate a token pair
type TokenGenerationRequest struct {
	UserID         string
	Email          string
	Username       string
	Role           string
	OrganizationID string
	Permissions    []string
	SessionID      string
	DeviceInfo     map[string]any
}

// GenerateTokenPair creates both access and refresh tokens
func (m *JWTManager) GenerateTokenPair(req *TokenGenerationRequest) (*TokenPair, error) {
	now := time.Now()

	// Create access token claims
	accessClaims := &Claims{
		UserID:         req.UserID,
		Email:          req.Email,
		Username:       req.Username,
		Role:           req.Role,
		OrganizationID: req.OrganizationID,
		Permissions:    req.Permissions,
		SessionID:      req.SessionID,
		DeviceInfo:     req.DeviceInfo,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    m.config.Issuer,
			Audience:  []string{m.config.Audience},
			Subject:   req.UserID,
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(m.config.AccessTokenExpiry)),
			NotBefore: jwt.NewNumericDate(now),
		},
	}

	// Create refresh token claims
	refreshClaims := &Claims{
		UserID:         req.UserID,
		Email:          req.Email,
		Username:       req.Username,
		Role:           req.Role,
		OrganizationID: req.OrganizationID,
		Permissions:    req.Permissions,
		SessionID:      req.SessionID,
		DeviceInfo:     req.DeviceInfo,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    m.config.Issuer,
			Audience:  []string{m.config.Audience},
			Subject:   req.UserID,
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(m.config.RefreshTokenExpiry)),
			NotBefore: jwt.NewNumericDate(now),
		},
	}

	// Generate tokens
	accessToken, err := m.generateToken(accessClaims)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to generate access token")
	}

	refreshToken, err := m.generateToken(refreshClaims)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to generate refresh token")
	}

	return &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    int64(m.config.AccessTokenExpiry.Seconds()),
		ExpiresAt:    now.Add(m.config.AccessTokenExpiry),
	}, nil
}

// generateToken creates a JWT token with the given claims
func (m *JWTManager) generateToken(claims *Claims) (string, error) {
	token := jwt.NewWithClaims(jwt.GetSigningMethod(m.config.Algorithm), claims)

	tokenString, err := token.SignedString(m.signingKey)
	if err != nil {
		return "", errors.Wrap(err, errors.CodeInternal, "failed to sign token")
	}

	return tokenString, nil
}

// ValidateToken validates a JWT token and returns the claims
func (m *JWTManager) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (any, error) {
		// Verify the signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); ok && m.config.Algorithm[:2] == "HS" {
			return m.verifyKey, nil
		}
		if _, ok := token.Method.(*jwt.SigningMethodRSA); ok && m.config.Algorithm[:2] == "RS" {
			return m.verifyKey, nil
		}
		return nil, errors.New(errors.CodeUnauthorized, "unexpected signing method: "+token.Header["alg"].(string))
	})

	if err != nil {
		// Check for specific JWT errors
		if err.Error() == "token is expired" {
			return nil, errors.New(errors.CodeTokenExpired, "token has expired")
		}
		if err.Error() == "token is not valid yet" {
			return nil, errors.New(errors.CodeUnauthorized, "token is not valid yet")
		}
		return nil, errors.Wrap(err, errors.CodeUnauthorized, "failed to parse token")
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, errors.New(errors.CodeUnauthorized, "invalid token claims")
	}

	// Validate issuer and audience
	if claims.Issuer != m.config.Issuer {
		return nil, errors.New(errors.CodeUnauthorized, "invalid token issuer")
	}

	if len(claims.Audience) == 0 || claims.Audience[0] != m.config.Audience {
		return nil, errors.New(errors.CodeUnauthorized, "invalid token audience")
	}

	return claims, nil
}

// RefreshToken generates a new access token from a refresh token
func (m *JWTManager) RefreshToken(refreshTokenString string) (*TokenPair, error) {
	claims, err := m.ValidateToken(refreshTokenString)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeUnauthorized, "invalid refresh token")
	}

	// Generate new token pair
	return m.GenerateTokenPair(&TokenGenerationRequest{
		UserID:         claims.UserID,
		Email:          claims.Email,
		Username:       claims.Username,
		Role:           claims.Role,
		OrganizationID: claims.OrganizationID,
		Permissions:    claims.Permissions,
		SessionID:      claims.SessionID,
		DeviceInfo:     claims.DeviceInfo,
	})
}

// ExtractTokenFromHeader extracts token from Authorization header
func ExtractTokenFromHeader(authHeader string) (string, error) {
	if authHeader == "" {
		return "", errors.New(errors.CodeUnauthorized, "missing authorization header")
	}

	// Check for Bearer token format
	const bearerPrefix = "Bearer "
	if len(authHeader) < len(bearerPrefix) || authHeader[:len(bearerPrefix)] != bearerPrefix {
		return "", errors.New(errors.CodeUnauthorized, "invalid authorization header format")
	}

	token := authHeader[len(bearerPrefix):]
	if token == "" {
		return "", errors.New(errors.CodeUnauthorized, "empty token")
	}

	return token, nil
}

// GenerateRSAKeyPair generates a new RSA key pair for production use
func GenerateRSAKeyPair() (privateKeyPEM, publicKeyPEM string, err error) {
	// Generate private key
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return "", "", errors.Wrap(err, errors.CodeInternal, "failed to generate RSA private key")
	}

	// Encode private key to PEM
	privateKeyPEMBytes := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(privateKey),
	})

	// Encode public key to PEM
	publicKeyPEMBytes := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PUBLIC KEY",
		Bytes: x509.MarshalPKCS1PublicKey(&privateKey.PublicKey),
	})

	return string(privateKeyPEMBytes), string(publicKeyPEMBytes), nil
}

// IsTokenExpired checks if a token is expired without full validation
func IsTokenExpired(tokenString string) (bool, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (any, error) {
		return []byte("dummy"), nil // We only want to check expiration
	})

	if err != nil {
		if err.Error() == "token is expired" {
			return true, nil
		}
		return false, errors.Wrap(err, errors.CodeUnauthorized, "failed to parse token")
	}

	claims, ok := token.Claims.(*Claims)
	if !ok {
		return false, errors.New(errors.CodeUnauthorized, "invalid token claims")
	}

	return claims.ExpiresAt.Time.Before(time.Now()), nil
}
