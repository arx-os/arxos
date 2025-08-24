package auth

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

type AuthManager struct {
	jwtSecret     []byte
	adminUsername string
	adminPassword string // hashed
}

type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type LoginResponse struct {
	Token        string    `json:"token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
}

type Claims struct {
	Username string `json:"username"`
	IsAdmin  bool   `json:"is_admin"`
	jwt.RegisteredClaims
}

// NewAuthManager creates a new auth manager with admin credentials
func NewAuthManager() *AuthManager {
	// Get JWT secret from environment or file
	jwtSecret := getJWTSecret()
	
	// Get admin credentials from environment
	adminUsername := os.Getenv("ARXOS_ADMIN_USERNAME")
	adminPassword := os.Getenv("ARXOS_ADMIN_PASSWORD")
	
	// Validate required configuration
	if adminUsername == "" || adminPassword == "" {
		panic("CRITICAL: ARXOS_ADMIN_USERNAME and ARXOS_ADMIN_PASSWORD environment variables must be set")
	}
	
	// Hash the admin password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(adminPassword), bcrypt.DefaultCost)
	if err != nil {
		panic(fmt.Sprintf("Failed to hash admin password: %v", err))
	}
	
	return &AuthManager{
		jwtSecret:     jwtSecret,
		adminUsername: adminUsername,
		adminPassword: string(hashedPassword),
	}
}

// getJWTSecret retrieves or generates a persistent JWT secret
func getJWTSecret() []byte {
	// First, check environment variable
	if secret := os.Getenv("JWT_SECRET"); secret != "" {
		return []byte(secret)
	}
	
	// Check for JWT secret file
	secretFile := os.Getenv("JWT_SECRET_FILE")
	if secretFile == "" {
		secretFile = "/etc/arxos/jwt.key"
	}
	
	// Try to read existing secret
	if data, err := ioutil.ReadFile(secretFile); err == nil && len(data) > 0 {
		return data
	}
	
	// Generate new secret and save it
	secret := make([]byte, 32)
	if _, err := rand.Read(secret); err != nil {
		panic(fmt.Sprintf("Failed to generate JWT secret: %v", err))
	}
	
	// Encode as hex for storage
	encodedSecret := hex.EncodeToString(secret)
	
	// Try to save the secret (non-fatal if it fails)
	os.MkdirAll("/etc/arxos", 0700)
	ioutil.WriteFile(secretFile, []byte(encodedSecret), 0600)
	
	return []byte(encodedSecret)
}

// Login handles user authentication
func (am *AuthManager) Login(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	// Validate credentials
	if req.Username != am.adminUsername {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}
	
	if err := bcrypt.CompareHashAndPassword([]byte(am.adminPassword), []byte(req.Password)); err != nil {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}
	
	// Create token with 1 hour expiration
	expiresAt := time.Now().Add(1 * time.Hour)
	claims := &Claims{
		Username: req.Username,
		IsAdmin:  true,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expiresAt),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
			Issuer:    "arxos",
			Subject:   req.Username,
		},
	}
	
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(am.jwtSecret)
	if err != nil {
		http.Error(w, "Failed to create token", http.StatusInternalServerError)
		return
	}
	
	// Set secure cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "arxos_token",
		Value:    tokenString,
		Expires:  expiresAt,
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteStrictMode,
		Path:     "/",
	})
	
	// Generate refresh token
	userAgent := r.Header.Get("User-Agent")
	ipAddress := r.RemoteAddr
	refreshToken, _, err := GenerateRefreshToken(1, userAgent, ipAddress) // TODO: Use actual user ID
	if err != nil {
		http.Error(w, "Failed to generate refresh token", http.StatusInternalServerError)
		return
	}
	
	// Return tokens in response
	resp := LoginResponse{
		Token:        tokenString,
		RefreshToken: refreshToken,
		ExpiresAt:    expiresAt,
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// RefreshTokenRequest represents a token refresh request
type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token"`
}

// RefreshToken handles token refresh requests
func (am *AuthManager) RefreshToken(w http.ResponseWriter, r *http.Request) {
	var req RefreshTokenRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	// Validate refresh token
	userID, err := ValidateRefreshToken(req.RefreshToken)
	if err != nil {
		if err == ErrInvalidRefreshToken || err == ErrExpiredRefreshToken || err == ErrRevokedRefreshToken {
			http.Error(w, err.Error(), http.StatusUnauthorized)
		} else {
			http.Error(w, "Internal server error", http.StatusInternalServerError)
		}
		return
	}
	
	// TODO: Get actual user from database
	// For now, using admin as placeholder
	username := am.adminUsername
	
	// Create new access token
	expiresAt := time.Now().Add(1 * time.Hour)
	claims := &Claims{
		Username: username,
		IsAdmin:  true, // TODO: Get from user record
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expiresAt),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
			Issuer:    "arxos",
			Subject:   username,
		},
	}
	
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(am.jwtSecret)
	if err != nil {
		http.Error(w, "Failed to create token", http.StatusInternalServerError)
		return
	}
	
	// Generate new refresh token (rotate on use)
	userAgent := r.Header.Get("User-Agent")
	ipAddress := r.RemoteAddr
	newRefreshToken, _, err := GenerateRefreshToken(userID, userAgent, ipAddress)
	if err != nil {
		// Log error but continue with existing refresh token
		fmt.Printf("Warning: failed to rotate refresh token: %v\n", err)
		newRefreshToken = req.RefreshToken
	} else {
		// Revoke old refresh token
		RevokeRefreshToken(req.RefreshToken, "Rotated")
	}
	
	// Return new tokens
	resp := LoginResponse{
		Token:        tokenString,
		RefreshToken: newRefreshToken,
		ExpiresAt:    expiresAt,
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// Logout clears the session and revokes refresh tokens
func (am *AuthManager) Logout(w http.ResponseWriter, r *http.Request) {
	// Get refresh token from request if provided
	var req struct {
		RefreshToken string `json:"refresh_token"`
	}
	json.NewDecoder(r.Body).Decode(&req)
	
	// Revoke refresh token if provided
	if req.RefreshToken != "" {
		RevokeRefreshToken(req.RefreshToken, "User logout")
	}
	
	// Clear cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "arxos_token",
		Value:    "",
		Expires:  time.Now().Add(-1 * time.Hour),
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteStrictMode,
		Path:     "/",
	})
	
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message":"Logged out successfully"}`))
}

// Middleware protects routes requiring authentication
func (am *AuthManager) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip auth for login page and static assets
		path := r.URL.Path
		if path == "/login" || path == "/api/auth/login" || 
		   strings.HasPrefix(path, "/static/") || 
		   path == "/favicon.ico" {
			next.ServeHTTP(w, r)
			return
		}
		
		// Check for token in cookie first
		var tokenString string
		cookie, err := r.Cookie("arxos_token")
		if err == nil {
			tokenString = cookie.Value
		}
		
		// Check Authorization header if no cookie
		if tokenString == "" {
			authHeader := r.Header.Get("Authorization")
			if authHeader != "" {
				parts := strings.Split(authHeader, " ")
				if len(parts) == 2 && parts[0] == "Bearer" {
					tokenString = parts[1]
				}
			}
		}
		
		// No token found
		if tokenString == "" {
			// Redirect to login page for browser requests
			if r.Header.Get("Accept") != "" && strings.Contains(r.Header.Get("Accept"), "text/html") {
				http.Redirect(w, r, "/login", http.StatusTemporaryRedirect)
				return
			}
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}
		
		// Validate token
		claims := &Claims{}
		token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}
			return am.jwtSecret, nil
		})
		
		if err != nil || !token.Valid {
			// Invalid token - redirect to login
			if strings.Contains(r.Header.Get("Accept"), "text/html") {
				http.Redirect(w, r, "/login", http.StatusTemporaryRedirect)
				return
			}
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}
		
		// Token is valid - proceed
		next.ServeHTTP(w, r)
	})
}

// ChangePassword allows admin to change password
func (am *AuthManager) ChangePassword(w http.ResponseWriter, r *http.Request) {
	var req struct {
		OldPassword string `json:"old_password"`
		NewPassword string `json:"new_password"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	// Verify old password
	if err := bcrypt.CompareHashAndPassword([]byte(am.adminPassword), []byte(req.OldPassword)); err != nil {
		http.Error(w, "Invalid old password", http.StatusUnauthorized)
		return
	}
	
	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.NewPassword), bcrypt.DefaultCost)
	if err != nil {
		http.Error(w, "Failed to hash password", http.StatusInternalServerError)
		return
	}
	
	am.adminPassword = string(hashedPassword)
	
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message":"Password changed successfully"}`))
}

// GenerateSecureToken creates a random secure token
func GenerateSecureToken() string {
	b := make([]byte, 32)
	rand.Read(b)
	return hex.EncodeToString(b)
}