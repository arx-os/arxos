package services

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	redis8 "github.com/go-redis/redis/v8"
	redis9 "github.com/redis/go-redis/v9"
	"golang.org/x/crypto/bcrypt"
)

var (
	ErrInvalidToken     = errors.New("invalid token")
	ErrTokenExpired     = errors.New("token expired")
	ErrInvalidSignature = errors.New("invalid signature")
	ErrMissingToken     = errors.New("missing token")
	ErrInvalidUser      = errors.New("invalid user credentials")
	ErrRefreshExpired   = errors.New("refresh token expired")
)

// AuthService handles all authentication operations
type AuthService struct {
	jwtSecret       []byte
	refreshSecret   []byte
	accessExpiry    time.Duration
	refreshExpiry   time.Duration
	redis8          *redis8.Client // v8 client from existing system
	redis9          *redis9.Client // v9 client (optional)
	issuer          string
	allowedOrigins  []string
}

// JWTClaims contains the claims for our JWT tokens
type JWTClaims struct {
	UserID    string   `json:"user_id"`
	Email     string   `json:"email"`
	Role      string   `json:"role"`
	Scopes    []string `json:"scopes,omitempty"`
	SessionID string   `json:"session_id"`
	jwt.RegisteredClaims
}

// RefreshClaims contains claims for refresh tokens
type RefreshClaims struct {
	UserID    string `json:"user_id"`
	SessionID string `json:"session_id"`
	jwt.RegisteredClaims
}

// TokenPair contains both access and refresh tokens
type TokenPair struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
	TokenType    string    `json:"token_type"`
}

// NewAuthService creates a new authentication service
func NewAuthService(jwtSecret, refreshSecret string, redisClient *redis8.Client) *AuthService {
	if jwtSecret == "" {
		// Generate a secure random secret if not provided
		jwtSecret = generateRandomSecret(64)
	}
	if refreshSecret == "" {
		refreshSecret = generateRandomSecret(64)
	}

	return &AuthService{
		jwtSecret:      []byte(jwtSecret),
		refreshSecret:  []byte(refreshSecret),
		accessExpiry:   15 * time.Minute, // Short-lived access tokens
		refreshExpiry:  7 * 24 * time.Hour, // Long-lived refresh tokens
		redis8:         redisClient,
		issuer:         "arxos-api",
		allowedOrigins: []string{"http://localhost:3000", "https://arxos.io"},
	}
}

// GenerateTokenPair creates a new access and refresh token pair
func (a *AuthService) GenerateTokenPair(userID, email, role string, scopes []string) (*TokenPair, error) {
	sessionID := uuid.New().String()
	
	// Generate access token
	accessToken, expiresAt, err := a.generateAccessToken(userID, email, role, scopes, sessionID)
	if err != nil {
		return nil, fmt.Errorf("failed to generate access token: %w", err)
	}
	
	// Generate refresh token
	refreshToken, err := a.generateRefreshToken(userID, sessionID)
	if err != nil {
		return nil, fmt.Errorf("failed to generate refresh token: %w", err)
	}
	
	// Store session in Redis
	ctx := context.Background()
	sessionKey := fmt.Sprintf("session:%s", sessionID)
	sessionData := map[string]interface{}{
		"user_id":    userID,
		"email":      email,
		"role":       role,
		"created_at": time.Now().Unix(),
		"ip":         "", // Can be populated from request
	}
	
	if a.redis8 != nil {
		err = a.redis8.HSet(ctx, sessionKey, sessionData).Err()
		if err != nil {
			return nil, fmt.Errorf("failed to store session: %w", err)
		}
		a.redis8.Expire(ctx, sessionKey, a.refreshExpiry)
	}
	
	return &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresAt:    expiresAt,
		TokenType:    "Bearer",
	}, nil
}

// generateAccessToken creates a new JWT access token
func (a *AuthService) generateAccessToken(userID, email, role string, scopes []string, sessionID string) (string, time.Time, error) {
	expiresAt := time.Now().Add(a.accessExpiry)
	
	claims := JWTClaims{
		UserID:    userID,
		Email:     email,
		Role:      role,
		Scopes:    scopes,
		SessionID: sessionID,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    a.issuer,
			Subject:   userID,
			ExpiresAt: jwt.NewNumericDate(expiresAt),
			NotBefore: jwt.NewNumericDate(time.Now()),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			ID:        uuid.New().String(),
		},
	}
	
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signedToken, err := token.SignedString(a.jwtSecret)
	if err != nil {
		return "", time.Time{}, err
	}
	
	return signedToken, expiresAt, nil
}

// generateRefreshToken creates a new refresh token
func (a *AuthService) generateRefreshToken(userID, sessionID string) (string, error) {
	claims := RefreshClaims{
		UserID:    userID,
		SessionID: sessionID,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    a.issuer,
			Subject:   userID,
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(a.refreshExpiry)),
			NotBefore: jwt.NewNumericDate(time.Now()),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			ID:        uuid.New().String(),
		},
	}
	
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(a.refreshSecret)
}

// ValidateAccessToken validates a JWT access token and returns the claims
func (a *AuthService) ValidateAccessToken(tokenString string) (*JWTClaims, error) {
	// Parse and validate token
	token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
		// Verify signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return a.jwtSecret, nil
	})
	
	if err != nil {
		// JWT v5 uses errors.Is for checking error types
		if errors.Is(err, jwt.ErrTokenExpired) {
			return nil, ErrTokenExpired
		}
		if errors.Is(err, jwt.ErrSignatureInvalid) {
			return nil, ErrInvalidSignature
		}
		return nil, ErrInvalidToken
	}
	
	claims, ok := token.Claims.(*JWTClaims)
	if !ok || !token.Valid {
		return nil, ErrInvalidToken
	}
	
	// Verify session is still valid in Redis
	if a.redis8 != nil {
		ctx := context.Background()
		sessionKey := fmt.Sprintf("session:%s", claims.SessionID)
		exists, err := a.redis8.Exists(ctx, sessionKey).Result()
		if err != nil || exists == 0 {
			return nil, errors.New("session not found or expired")
		}
	}
	
	return claims, nil
}

// RefreshAccessToken uses a refresh token to generate a new access token
func (a *AuthService) RefreshAccessToken(refreshTokenString string) (*TokenPair, error) {
	// Parse refresh token
	token, err := jwt.ParseWithClaims(refreshTokenString, &RefreshClaims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return a.refreshSecret, nil
	})
	
	if err != nil || !token.Valid {
		return nil, ErrRefreshExpired
	}
	
	claims, ok := token.Claims.(*RefreshClaims)
	if !ok {
		return nil, ErrInvalidToken
	}
	
	// Get session data from Redis
	if a.redis8 != nil {
		ctx := context.Background()
		sessionKey := fmt.Sprintf("session:%s", claims.SessionID)
		sessionData, err := a.redis8.HGetAll(ctx, sessionKey).Result()
		if err != nil || len(sessionData) == 0 {
			return nil, errors.New("session not found")
		}
		
		// Generate new access token with same session ID
		email := sessionData["email"]
		role := sessionData["role"]
		scopes := strings.Split(sessionData["scopes"], ",")
		
		accessToken, expiresAt, err := a.generateAccessToken(claims.UserID, email, role, scopes, claims.SessionID)
		if err != nil {
			return nil, err
		}
		
		return &TokenPair{
			AccessToken:  accessToken,
			RefreshToken: refreshTokenString, // Keep the same refresh token
			ExpiresAt:    expiresAt,
			TokenType:    "Bearer",
		}, nil
	}
	
	// If Redis is not available, generate new token pair
	// This is less secure but allows the system to work without Redis
	return a.GenerateTokenPair(claims.UserID, "", "user", nil)
}

// RevokeToken revokes a token by adding it to a blacklist
func (a *AuthService) RevokeToken(tokenString string) error {
	claims, err := a.ValidateAccessToken(tokenString)
	if err != nil {
		// Even if token is invalid, try to revoke it
		claims = &JWTClaims{}
	}
	
	if a.redis8 != nil {
		ctx := context.Background()
		// Add to blacklist
		blacklistKey := fmt.Sprintf("blacklist:%s", tokenString[:20]) // Use first 20 chars as key
		err := a.redis8.Set(ctx, blacklistKey, time.Now().Unix(), a.accessExpiry).Err()
		if err != nil {
			return fmt.Errorf("failed to blacklist token: %w", err)
		}
		
		// Remove session if exists
		if claims.SessionID != "" {
			sessionKey := fmt.Sprintf("session:%s", claims.SessionID)
			a.redis8.Del(ctx, sessionKey)
		}
	}
	
	return nil
}

// ExtractTokenFromRequest extracts the JWT token from the HTTP request
func (a *AuthService) ExtractTokenFromRequest(r *http.Request) (string, error) {
	// Check Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader != "" {
		parts := strings.Split(authHeader, " ")
		if len(parts) == 2 && strings.ToLower(parts[0]) == "bearer" {
			return parts[1], nil
		}
	}
	
	// Check cookie
	cookie, err := r.Cookie("access_token")
	if err == nil && cookie.Value != "" {
		return cookie.Value, nil
	}
	
	// Check query parameter (less secure, use with caution)
	if token := r.URL.Query().Get("token"); token != "" {
		return token, nil
	}
	
	return "", ErrMissingToken
}

// HashPassword hashes a plaintext password using bcrypt
func (a *AuthService) HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

// VerifyPassword checks if a plaintext password matches a hash
func (a *AuthService) VerifyPassword(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

// IsTokenBlacklisted checks if a token has been revoked
func (a *AuthService) IsTokenBlacklisted(tokenString string) bool {
	if a.redis8 == nil {
		return false
	}
	
	ctx := context.Background()
	blacklistKey := fmt.Sprintf("blacklist:%s", tokenString[:20])
	exists, _ := a.redis8.Exists(ctx, blacklistKey).Result()
	return exists > 0
}

// ValidateOrigin checks if the request origin is allowed
func (a *AuthService) ValidateOrigin(origin string) bool {
	for _, allowed := range a.allowedOrigins {
		if origin == allowed {
			return true
		}
	}
	return false
}

// generateRandomSecret generates a cryptographically secure random secret
func generateRandomSecret(length int) string {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		panic("failed to generate random secret")
	}
	return base64.URLEncoding.EncodeToString(bytes)
}

// SetAccessExpiry updates the access token expiry duration
func (a *AuthService) SetAccessExpiry(duration time.Duration) {
	a.accessExpiry = duration
}

// SetRefreshExpiry updates the refresh token expiry duration
func (a *AuthService) SetRefreshExpiry(duration time.Duration) {
	a.refreshExpiry = duration
}