package web

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
)

// AuthService handles authentication and authorization
type AuthService struct {
	jwtSecret    []byte
	sessionStore SessionStore
	userService  UserService
}

// SessionStore interface for session management
type SessionStore interface {
	Get(sessionID string) (*Session, error)
	Set(sessionID string, session *Session) error
	Delete(sessionID string) error
}

// UserService interface for user operations
type UserService interface {
	GetUserByEmail(ctx context.Context, email string) (*models.User, error)
	GetUserByID(ctx context.Context, id string) (*models.User, error)
	ValidateCredentials(ctx context.Context, email, password string) (*models.User, error)
}

// Session represents a user session
type Session struct {
	ID        string    `json:"id"`
	UserID    string    `json:"user_id"`
	Email     string    `json:"email"`
	Name      string    `json:"name"`
	Role      string    `json:"role"`
	ExpiresAt time.Time `json:"expires_at"`
	CreatedAt time.Time `json:"created_at"`
}

// JWTClaims represents JWT token claims
type JWTClaims struct {
	UserID string `json:"user_id"`
	Email  string `json:"email"`
	Name   string `json:"name"`
	Role   string `json:"role"`
	jwt.RegisteredClaims
}

// NewAuthService creates a new authentication service
func NewAuthService(jwtSecret []byte, sessionStore SessionStore, userService UserService) *AuthService {
	return &AuthService{
		jwtSecret:    jwtSecret,
		sessionStore: sessionStore,
		userService:  userService,
	}
}

// AuthMiddleware provides authentication middleware
func (a *AuthService) AuthMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Check for JWT token in Authorization header
		authHeader := r.Header.Get("Authorization")
		if authHeader != "" {
			if a.validateJWT(r, authHeader) {
				next(w, r)
				return
			}
		}

		// Check for session cookie
		cookie, err := r.Cookie("session_id")
		if err == nil && a.validateSession(r, cookie.Value) {
			next(w, r)
			return
		}

		// No valid authentication found
		if strings.HasPrefix(r.URL.Path, "/api/") {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
		} else {
			http.Redirect(w, r, "/login?redirect="+r.URL.Path, http.StatusSeeOther)
		}
	}
}

// RequireRole middleware ensures user has specific role
func (a *AuthService) RequireRole(role string) func(http.HandlerFunc) http.HandlerFunc {
	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			user := GetUserFromContext(r.Context())
			if user == nil {
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
				return
			}

			if !a.hasRole(user.Role, role) {
				http.Error(w, "Forbidden", http.StatusForbidden)
				return
			}

			next(w, r)
		}
	}
}

// Login handles user authentication
func (a *AuthService) Login(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// Validate credentials
	user, err := a.userService.ValidateCredentials(r.Context(), req.Email, req.Password)
	if err != nil {
		logger.Warn("Failed login attempt for %s: %v", req.Email, err)
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}

	// Create JWT token
	token, err := a.generateJWT(user)
	if err != nil {
		logger.Error("Failed to generate JWT: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Create session
	sessionID := a.generateSessionID()
	session := &Session{
		ID:        sessionID,
		UserID:    user.ID,
		Email:     user.Email,
		Name:      user.FullName,
		Role:      user.Role,
		ExpiresAt: time.Now().Add(24 * time.Hour),
		CreatedAt: time.Now(),
	}

	if err := a.sessionStore.Set(sessionID, session); err != nil {
		logger.Error("Failed to store session: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Set session cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "session_id",
		Value:    sessionID,
		Path:     "/",
		Expires:  session.ExpiresAt,
		HttpOnly: true,
		Secure:   r.TLS != nil,
		SameSite: http.SameSiteStrictMode,
	})

	// Return token and user info
	response := map[string]interface{}{
		"token":      token,
		"expires_at": session.ExpiresAt.Unix(),
		"user": map[string]string{
			"id":    user.ID,
			"email": user.Email,
			"name":  user.FullName,
			"role":  user.Role,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Logout handles user logout
func (a *AuthService) Logout(w http.ResponseWriter, r *http.Request) {
	// Delete session from store
	if cookie, err := r.Cookie("session_id"); err == nil {
		a.sessionStore.Delete(cookie.Value)
	}

	// Clear session cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "session_id",
		Value:    "",
		Path:     "/",
		Expires:  time.Now().Add(-time.Hour),
		HttpOnly: true,
		Secure:   r.TLS != nil,
		SameSite: http.SameSiteStrictMode,
	})

	// Redirect or return success
	if strings.HasPrefix(r.URL.Path, "/api/") {
		w.WriteHeader(http.StatusNoContent)
	} else {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
	}
}

// validateJWT validates JWT token from Authorization header
func (a *AuthService) validateJWT(r *http.Request, authHeader string) bool {
	// Extract token from "Bearer <token>" format
	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || parts[0] != "Bearer" {
		return false
	}

	tokenString := parts[1]

	// Parse and validate token
	token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
		// Validate signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, jwt.ErrInvalidKey
		}
		return a.jwtSecret, nil
	})

	if err != nil || !token.Valid {
		return false
	}

	claims, ok := token.Claims.(*JWTClaims)
	if !ok {
		return false
	}

	// Get user from database
	user, err := a.userService.GetUserByID(r.Context(), claims.UserID)
	if err != nil {
		return false
	}

	// Add user to request context
	ctx := context.WithValue(r.Context(), contextKeyUser, user)
	*r = *r.WithContext(ctx)

	return true
}

// validateSession validates session from cookie
func (a *AuthService) validateSession(r *http.Request, sessionID string) bool {
	session, err := a.sessionStore.Get(sessionID)
	if err != nil {
		return false
	}

	// Check expiration
	if time.Now().After(session.ExpiresAt) {
		a.sessionStore.Delete(sessionID)
		return false
	}

	// Get user from database
	user, err := a.userService.GetUserByID(r.Context(), session.UserID)
	if err != nil {
		return false
	}

	// Add user to request context
	ctx := context.WithValue(r.Context(), contextKeyUser, user)
	*r = *r.WithContext(ctx)

	return true
}

// generateJWT generates a JWT token for the user
func (a *AuthService) generateJWT(user *models.User) (string, error) {
	now := time.Now()
	claims := JWTClaims{
		UserID: user.ID,
		Email:  user.Email,
		Name:   user.FullName,
		Role:   user.Role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(now.Add(24 * time.Hour)),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "arxos",
			Subject:   user.ID,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(a.jwtSecret)
}

// generateSessionID generates a secure random session ID
func (a *AuthService) generateSessionID() string {
	b := make([]byte, 32)
	rand.Read(b)
	return base64.URLEncoding.EncodeToString(b)
}

// hasRole checks if user role has required permissions
func (a *AuthService) hasRole(userRole, requiredRole string) bool {
	// Role hierarchy: admin > manager > user > viewer
	roleLevel := map[string]int{
		"admin":   4,
		"manager": 3,
		"user":    2,
		"viewer":  1,
	}

	userLevel, ok1 := roleLevel[userRole]
	requiredLevel, ok2 := roleLevel[requiredRole]

	if !ok1 || !ok2 {
		return false
	}

	return userLevel >= requiredLevel
}

// Context key for user
type contextKey string

const contextKeyUser contextKey = "user"

// GetUserFromContext retrieves user from request context
func GetUserFromContext(ctx context.Context) *models.User {
	if user, ok := ctx.Value(contextKeyUser).(*models.User); ok {
		return user
	}
	return nil
}

// HashPassword hashes a password using bcrypt
func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

// CheckPasswordHash compares password with hash
func CheckPasswordHash(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}