package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// UserRole represents user roles for authorization
type UserRole string

const (
	RoleAdmin       UserRole = "admin"
	RoleFieldWorker UserRole = "field_worker"
	RoleValidator   UserRole = "validator"
	RoleManager     UserRole = "manager"
	RoleOperator    UserRole = "operator"
	RoleViewer      UserRole = "viewer"
	RoleGuest       UserRole = "guest"
)

// Permission represents system permissions
type Permission string

const (
	// Building permissions
	PermCreateBuilding Permission = "create_building"
	PermReadBuilding   Permission = "read_building"
	PermUpdateBuilding Permission = "update_building"
	PermDeleteBuilding Permission = "delete_building"

	// ArxObject permissions
	PermCreateArxObject Permission = "create_arxobject"
	PermReadArxObject   Permission = "read_arxobject"
	PermUpdateArxObject Permission = "update_arxobject"
	PermDeleteArxObject Permission = "delete_arxobject"

	// Ingestion permissions
	PermIngestPDF   Permission = "ingest_pdf"
	PermIngestImage Permission = "ingest_image"
	PermIngestLidar Permission = "ingest_lidar"

	// System permissions
	PermViewAuditLogs Permission = "view_audit_logs"
	PermManageSystem  Permission = "manage_system"
	PermExportData    Permission = "export_data"
)

// AuthUser represents an authenticated user
type AuthUser struct {
	ID          string       `json:"id"`
	Username    string       `json:"username"`
	Email       string       `json:"email"`
	Roles       []UserRole   `json:"roles"`
	Permissions []Permission `json:"permissions"`
	SessionID   string       `json:"session_id"`
	TokenID     string       `json:"token_id"`
}

// HasPermission checks if the user has a specific permission
func (u *AuthUser) HasPermission(permission Permission) bool {
	for _, perm := range u.Permissions {
		if perm == permission {
			return true
		}
	}
	return false
}

// HasRole checks if the user has a specific role
func (u *AuthUser) HasRole(role UserRole) bool {
	for _, r := range u.Roles {
		if r == role {
			return true
		}
	}
	return false
}

// JWTClaims represents JWT token claims
type JWTClaims struct {
	UserID      string       `json:"sub"`
	Username    string       `json:"username"`
	Email       string       `json:"email"`
	Roles       []string     `json:"roles"`
	Permissions []string     `json:"permissions"`
	SessionID   string       `json:"sid"`
	TokenID     string       `json:"jti"`
	TokenType   string       `json:"typ"`
	jwt.RegisteredClaims
}

// AuthConfig holds authentication configuration
type AuthConfig struct {
	JWTSecret           string
	TokenExpiration     time.Duration
	RefreshExpiration   time.Duration
	RequireAuth         bool
	AllowedOrigins      []string
	RolePermissions     map[UserRole][]Permission
}

// NewAuthConfig creates a new auth configuration with defaults
func NewAuthConfig() *AuthConfig {
	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		// In production, this should fail. For development, use a default
		secret = "arxos-dev-secret-key-change-in-production"
	}

	return &AuthConfig{
		JWTSecret:         secret,
		TokenExpiration:   time.Hour,
		RefreshExpiration: 7 * 24 * time.Hour,
		RequireAuth:       true,
		AllowedOrigins:    []string{"*"}, // Configure properly for production
		RolePermissions:   buildRolePermissions(),
	}
}

// NewAuthConfigFromEnv creates auth configuration from environment and server config
func NewAuthConfigFromEnv(config *Config) *AuthConfig {
	tokenExpiration := time.Hour
	if exp := os.Getenv("JWT_EXPIRATION"); exp != "" {
		if duration, err := time.ParseDuration(exp + "s"); err == nil {
			tokenExpiration = duration
		}
	}
	
	refreshExpiration := 7 * 24 * time.Hour
	if exp := os.Getenv("JWT_REFRESH_EXPIRATION"); exp != "" {
		if duration, err := time.ParseDuration(exp + "s"); err == nil {
			refreshExpiration = duration
		}
	}

	return &AuthConfig{
		JWTSecret:         config.JWTSecret,
		TokenExpiration:   tokenExpiration,
		RefreshExpiration: refreshExpiration,
		RequireAuth:       config.EnableAuth,
		AllowedOrigins:    config.CORSOrigins,
		RolePermissions:   buildRolePermissions(),
	}
}

// buildRolePermissions defines permissions for each role
func buildRolePermissions() map[UserRole][]Permission {
	return map[UserRole][]Permission{
		RoleAdmin: {
			// Full system access
			PermCreateBuilding, PermReadBuilding, PermUpdateBuilding, PermDeleteBuilding,
			PermCreateArxObject, PermReadArxObject, PermUpdateArxObject, PermDeleteArxObject,
			PermIngestPDF, PermIngestImage, PermIngestLidar,
			PermViewAuditLogs, PermManageSystem, PermExportData,
		},
		RoleFieldWorker: {
			// Field workers can read, create, and update but not delete
			PermReadBuilding, PermUpdateBuilding,
			PermCreateArxObject, PermReadArxObject, PermUpdateArxObject,
			PermIngestPDF, PermIngestImage, PermIngestLidar,
			PermExportData,
		},
		RoleValidator: {
			// Validators can read, update, and validate data
			PermReadBuilding, PermUpdateBuilding,
			PermReadArxObject, PermUpdateArxObject,
			PermIngestPDF, PermIngestImage,
			PermExportData,
		},
		RoleManager: {
			// Managers have broad access but can't delete buildings
			PermCreateBuilding, PermReadBuilding, PermUpdateBuilding,
			PermCreateArxObject, PermReadArxObject, PermUpdateArxObject, PermDeleteArxObject,
			PermIngestPDF, PermIngestImage, PermIngestLidar,
			PermExportData,
		},
		RoleOperator: {
			// Operators can read and update
			PermReadBuilding, PermUpdateBuilding,
			PermReadArxObject, PermUpdateArxObject,
			PermIngestPDF, PermIngestImage,
		},
		RoleViewer: {
			// Read-only access
			PermReadBuilding, PermReadArxObject,
		},
		RoleGuest: {
			// Minimal access
			PermReadBuilding,
		},
	}
}

// AuthManager handles authentication and authorization
type AuthManager struct {
	config *AuthConfig
}

// NewAuthManager creates a new authentication manager
func NewAuthManager(config *AuthConfig) *AuthManager {
	return &AuthManager{
		config: config,
	}
}

// GenerateToken creates a JWT token for the user
func (am *AuthManager) GenerateToken(user *AuthUser) (string, error) {
	now := time.Now()
	claims := &JWTClaims{
		UserID:      user.ID,
		Username:    user.Username,
		Email:       user.Email,
		Roles:       roleSliceToString(user.Roles),
		Permissions: permissionSliceToString(user.Permissions),
		SessionID:   user.SessionID,
		TokenID:     user.TokenID,
		TokenType:   "access",
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   user.ID,
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(am.config.TokenExpiration)),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "arxos",
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(am.config.JWTSecret))
}

// ValidateToken parses and validates a JWT token
func (am *AuthManager) ValidateToken(tokenString string) (*AuthUser, error) {
	token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(am.config.JWTSecret), nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to parse token: %w", err)
	}

	if !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}

	claims, ok := token.Claims.(*JWTClaims)
	if !ok {
		return nil, fmt.Errorf("invalid token claims")
	}

	// Convert string slices back to typed slices
	roles := make([]UserRole, len(claims.Roles))
	for i, r := range claims.Roles {
		roles[i] = UserRole(r)
	}

	permissions := make([]Permission, len(claims.Permissions))
	for i, p := range claims.Permissions {
		permissions[i] = Permission(p)
	}

	user := &AuthUser{
		ID:          claims.UserID,
		Username:    claims.Username,
		Email:       claims.Email,
		Roles:       roles,
		Permissions: permissions,
		SessionID:   claims.SessionID,
		TokenID:     claims.TokenID,
	}

	return user, nil
}

// AuthMiddleware provides JWT authentication middleware
func (am *AuthManager) AuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip auth for health check and public endpoints
		if r.URL.Path == "/api/v1/health" || r.URL.Path == "/api/v1/auth/login" {
			next.ServeHTTP(w, r)
			return
		}

		// Extract token from Authorization header
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			if am.config.RequireAuth {
				http.Error(w, "Authorization header required", http.StatusUnauthorized)
				return
			}
			next.ServeHTTP(w, r)
			return
		}

		// Parse Bearer token
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			http.Error(w, "Invalid authorization header format", http.StatusUnauthorized)
			return
		}

		tokenString := parts[1]

		// Validate token
		user, err := am.ValidateToken(tokenString)
		if err != nil {
			http.Error(w, fmt.Sprintf("Invalid token: %v", err), http.StatusUnauthorized)
			return
		}

		// Add user to request context
		ctx := context.WithValue(r.Context(), "user", user)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequirePermission middleware requires specific permission
func (am *AuthManager) RequirePermission(permission Permission) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			user := getUserFromContext(r.Context())
			if user == nil {
				http.Error(w, "Authentication required", http.StatusUnauthorized)
				return
			}

			if !user.HasPermission(permission) {
				http.Error(w, fmt.Sprintf("Permission %s required", permission), http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireRole middleware requires specific role
func (am *AuthManager) RequireRole(role UserRole) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			user := getUserFromContext(r.Context())
			if user == nil {
				http.Error(w, "Authentication required", http.StatusUnauthorized)
				return
			}

			if !user.HasRole(role) {
				http.Error(w, fmt.Sprintf("Role %s required", role), http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// LoginRequest represents a login request
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// LoginResponse represents a login response
type LoginResponse struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
	User         AuthUser  `json:"user"`
}

// handleLogin processes login requests
func (s *Server) handleLogin(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Mock user authentication - in production, verify against database
	user := s.authenticateUser(req.Username, req.Password)
	if user == nil {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}

	// Generate tokens
	accessToken, err := s.authManager.GenerateToken(user)
	if err != nil {
		http.Error(w, "Failed to generate token", http.StatusInternalServerError)
		return
	}

	// For this implementation, refresh token is the same as access token
	// In production, implement proper refresh token logic
	refreshToken := accessToken

	response := LoginResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresAt:    time.Now().Add(s.authManager.config.TokenExpiration),
		User:         *user,
	}

	respondJSON(w, response)
}

// authenticateUser validates user credentials (mock implementation)
func (s *Server) authenticateUser(username, password string) *AuthUser {
	// Mock users for testing - in production, verify against database
	mockUsers := map[string]*AuthUser{
		"admin": {
			ID:       "admin_001",
			Username: "admin",
			Email:    "admin@arxos.com",
			Roles:    []UserRole{RoleAdmin},
		},
		"fieldworker": {
			ID:       "field_001",
			Username: "fieldworker",
			Email:    "field@arxos.com",
			Roles:    []UserRole{RoleFieldWorker},
		},
		"validator": {
			ID:       "val_001",
			Username: "validator",
			Email:    "validator@arxos.com",
			Roles:    []UserRole{RoleValidator},
		},
	}

	// Mock password check - in production, use proper password hashing
	mockPasswords := map[string]string{
		"admin":       "admin123",
		"fieldworker": "field123",
		"validator":   "valid123",
	}

	user, exists := mockUsers[username]
	if !exists {
		return nil
	}

	expectedPassword, exists := mockPasswords[username]
	if !exists || password != expectedPassword {
		return nil
	}

	// Set permissions based on roles
	permissions := []Permission{}
	for _, role := range user.Roles {
		if rolePerms, exists := s.authManager.config.RolePermissions[role]; exists {
			permissions = append(permissions, rolePerms...)
		}
	}

	user.Permissions = permissions
	user.SessionID = fmt.Sprintf("session_%d", time.Now().Unix())
	user.TokenID = fmt.Sprintf("token_%d", time.Now().Unix())

	return user
}

// getUserFromContext extracts user from request context
func getUserFromContext(ctx context.Context) *AuthUser {
	user, ok := ctx.Value("user").(*AuthUser)
	if !ok {
		return nil
	}
	return user
}

// Helper functions
func roleSliceToString(roles []UserRole) []string {
	result := make([]string, len(roles))
	for i, role := range roles {
		result[i] = string(role)
	}
	return result
}

func permissionSliceToString(permissions []Permission) []string {
	result := make([]string, len(permissions))
	for i, perm := range permissions {
		result[i] = string(perm)
	}
	return result
}