package auth

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/arxos/arxos/core/cgo"
	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

// AuthManagerCGO provides CGO-optimized authentication operations
type AuthManagerCGO struct {
	jwtSecret     []byte
	adminUsername string
	adminPassword string // hashed
	hasCGO        bool
	authOptions   *cgo.ArxAuthOptions
}

// NewAuthManagerCGO creates a new CGO-optimized auth manager
func NewAuthManagerCGO() *AuthManagerCGO {
	// Check if CGO is available
	hasCGO := cgo.IsHealthy()

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

	// Initialize CGO authentication if available
	var authOptions *cgo.ArxAuthOptions
	if hasCGO {
		authOptions = cgo.DefaultAuthOptions()
		authOptions.JWTSecret = string(jwtSecret)
		authOptions.Issuer = "ARXOS"

		// Initialize C core authentication
		if !cgo.InitAuth(authOptions) {
			fmt.Println("Warning: Failed to initialize CGO authentication, falling back to Go implementation")
			hasCGO = false
		}
	}

	return &AuthManagerCGO{
		jwtSecret:     jwtSecret,
		adminUsername: adminUsername,
		adminPassword: string(hashedPassword),
		hasCGO:        hasCGO,
		authOptions:   authOptions,
	}
}

// Close cleans up CGO resources
func (am *AuthManagerCGO) Close() {
	if am.hasCGO {
		cgo.CleanupAuth()
	}
}

// HasCGOBridge returns whether CGO authentication is available
func (am *AuthManagerCGO) HasCGOBridge() bool {
	return am.hasCGO
}

// Login handles user authentication using CGO when available
func (am *AuthManagerCGO) Login(w http.ResponseWriter, r *http.Request) {
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

	var tokenString string
	var expiresAt time.Time
	var refreshToken string

	if am.hasCGO {
		// Use CGO authentication
		result := am.cgoAuthenticateUser(req.Username, req.Password)
		if result != nil && result.Success {
			tokenString = result.Token
			expiresAt = result.ExpiresAt
			refreshToken = result.RefreshToken
		} else {
			// Fallback to Go implementation
			tokenString, expiresAt, refreshToken = am.goAuthenticateUser(req.Username, req.Password)
		}
	} else {
		// Use Go implementation
		tokenString, expiresAt, refreshToken = am.goAuthenticateUser(req.Username, req.Password)
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

	// Return tokens in response
	resp := LoginResponse{
		Token:        tokenString,
		RefreshToken: refreshToken,
		ExpiresAt:    expiresAt,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// cgoAuthenticateUser authenticates user using CGO
func (am *AuthManagerCGO) cgoAuthenticateUser(username, password string) *cgo.ArxAuthResult {
	if !am.hasCGO {
		return nil
	}

	result := cgo.AuthenticateUser(username, password)
	if result == nil {
		return nil
	}

	return result
}

// goAuthenticateUser authenticates user using Go implementation
func (am *AuthManagerCGO) goAuthenticateUser(username, password string) (string, time.Time, string) {
	// Create token with 1 hour expiration
	expiresAt := time.Now().Add(1 * time.Hour)
	claims := &Claims{
		Username: username,
		IsAdmin:  true,
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
		// Return empty values on error - caller should handle
		return "", time.Time{}, ""
	}

	// Generate refresh token
	userAgent := r.Header.Get("User-Agent")
	ipAddress := r.RemoteAddr
	refreshToken, _, err := GenerateRefreshToken(1, userAgent, ipAddress)
	if err != nil {
		// Return empty refresh token on error
		refreshToken = ""
	}

	return tokenString, expiresAt, refreshToken
}

// RefreshToken handles token refresh requests
func (am *AuthManagerCGO) RefreshToken(w http.ResponseWriter, r *http.Request) {
	var req RefreshTokenRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	var userID uint32
	var err error

	if am.hasCGO {
		// Use CGO refresh token validation
		userID = cgo.ValidateRefreshToken(req.RefreshToken)
		if userID == 0 {
			// Fallback to Go implementation
			userID, err = ValidateRefreshToken(req.RefreshToken)
			if err != nil {
				http.Error(w, "Invalid refresh token", http.StatusUnauthorized)
				return
			}
		}
	} else {
		// Use Go implementation
		userID, err = ValidateRefreshToken(req.RefreshToken)
		if err != nil {
			http.Error(w, "Invalid refresh token", http.StatusUnauthorized)
			return
		}
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
	var newRefreshToken string

	if am.hasCGO {
		// Use CGO refresh token generation
		newRefreshToken = cgo.GenerateRefreshToken(userID, userAgent, ipAddress)
		if newRefreshToken == "" {
			// Fallback to Go implementation
			newRefreshToken, _, err = GenerateRefreshToken(userID, userAgent, ipAddress)
			if err != nil {
				newRefreshToken = req.RefreshToken
			}
		}
	} else {
		// Use Go implementation
		newRefreshToken, _, err = GenerateRefreshToken(userID, userAgent, ipAddress)
		if err != nil {
			newRefreshToken = req.RefreshToken
		}
	}

	// Revoke old refresh token
	if am.hasCGO {
		cgo.RevokeRefreshToken(req.RefreshToken, "Rotated")
	} else {
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
func (am *AuthManagerCGO) Logout(w http.ResponseWriter, r *http.Request) {
	// Get refresh token from request if provided
	var req struct {
		RefreshToken string `json:"refresh_token"`
	}
	json.NewDecoder(r.Body).Decode(&req)

	// Revoke refresh token if provided
	if req.RefreshToken != "" {
		if am.hasCGO {
			cgo.RevokeRefreshToken(req.RefreshToken, "User logout")
		} else {
			RevokeRefreshToken(req.RefreshToken, "User logout")
		}
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
func (am *AuthManagerCGO) Middleware(next http.Handler) http.Handler {
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
		var isValid bool
		if am.hasCGO {
			// Use CGO JWT verification
			isValid = am.cgoVerifyJWT(tokenString)
		} else {
			// Use Go JWT verification
			isValid = am.goVerifyJWT(tokenString)
		}

		if !isValid {
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

// cgoVerifyJWT verifies JWT using CGO
func (am *AuthManagerCGO) cgoVerifyJWT(tokenString string) bool {
	if !am.hasCGO {
		return false
	}

	// Parse JWT using CGO
	jwtToken := cgo.ParseJWT(tokenString, string(am.jwtSecret))
	if jwtToken == nil {
		return false
	}
	defer cgo.DestroyJWT(jwtToken)

	// Verify JWT using CGO
	return cgo.VerifyJWT(jwtToken, string(am.jwtSecret))
}

// goVerifyJWT verifies JWT using Go implementation
func (am *AuthManagerCGO) goVerifyJWT(tokenString string) bool {
	claims := &Claims{}
	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return am.jwtSecret, nil
	})

	return err == nil && token.Valid
}

// ChangePassword allows admin to change password
func (am *AuthManagerCGO) ChangePassword(w http.ResponseWriter, r *http.Request) {
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
func (am *AuthManagerCGO) GenerateSecureToken() string {
	if am.hasCGO {
		// Use CGO secure token generation
		token := cgo.GenerateSecureToken(32)
		if token != "" {
			return token
		}
	}

	// Fallback to Go implementation
	return GenerateSecureToken()
}

// GetCGOStatus returns the current CGO status
func (am *AuthManagerCGO) GetCGOStatus() map[string]interface{} {
	status := map[string]interface{}{
		"has_cgo": am.hasCGO,
	}

	if am.hasCGO {
		status["auth_healthy"] = cgo.IsAuthHealthy()
		status["auth_stats"] = cgo.GetAuthStatistics()
	}

	return status
}
