package security

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"sync"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// UserRole represents user roles for RBAC
type UserRole string

const (
	RoleAdmin      UserRole = "admin"
	RoleEngineer   UserRole = "engineer"
	RoleViewer     UserRole = "viewer"
	RoleContractor UserRole = "contractor"
	RoleGuest      UserRole = "guest"
)

// Permission represents permissions for resource access control
type Permission string

const (
	PermissionRead          Permission = "read"
	PermissionWrite         Permission = "write"
	PermissionDelete        Permission = "delete"
	PermissionManageUsers   Permission = "manage_users"
	PermissionManageSystem  Permission = "manage_system"
	PermissionExportData    Permission = "export_data"
	PermissionImportData    Permission = "import_data"
	PermissionViewAuditLogs Permission = "view_audit_logs"
)

// User represents a user entity with attributes for ABAC
type User struct {
	ID         string                 `json:"id"`
	Username   string                 `json:"username"`
	Email      string                 `json:"email"`
	Roles      []UserRole             `json:"roles"`
	Attributes map[string]interface{} `json:"attributes"`
	IsActive   bool                   `json:"is_active"`
	CreatedAt  time.Time              `json:"created_at"`
	LastLogin  *time.Time             `json:"last_login,omitempty"`
}

// Resource represents a resource entity for access control
type Resource struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	Attributes map[string]interface{} `json:"attributes"`
	OwnerID    string                 `json:"owner_id"`
	CreatedAt  time.Time              `json:"created_at"`
}

// Session represents a user session
type Session struct {
	ID           string                 `json:"id"`
	UserID       string                 `json:"user_id"`
	Data         map[string]interface{} `json:"data"`
	CreatedAt    time.Time              `json:"created_at"`
	LastActivity time.Time              `json:"last_activity"`
	ExpiresAt    time.Time              `json:"expires_at"`
}

// TokenClaims represents JWT token claims
type TokenClaims struct {
	UserID   string     `json:"user_id"`
	Username string     `json:"username"`
	Roles    []UserRole `json:"roles"`
	jwt.RegisteredClaims
}

// AuthService provides authentication and authorization services
type AuthService struct {
	secretKey          string
	algorithm          string
	tokenExpiry        time.Duration
	refreshTokenExpiry time.Duration
	sessionTimeout     time.Duration
	activeSessions     map[string]*Session
	sessionMutex       sync.RWMutex
	rolePermissions    map[UserRole][]Permission
	rbacMutex          sync.RWMutex
}

// NewAuthService creates a new authentication service
func NewAuthService(secretKey string) *AuthService {
	as := &AuthService{
		secretKey:          secretKey,
		algorithm:          "HS256",
		tokenExpiry:        24 * time.Hour,
		refreshTokenExpiry: 7 * 24 * time.Hour,
		sessionTimeout:     8 * time.Hour,
		activeSessions:     make(map[string]*Session),
		rolePermissions:    make(map[UserRole][]Permission),
	}

	// Initialize default role permissions
	as.initializeRolePermissions()

	return as
}

// initializeRolePermissions sets up default role permissions
func (as *AuthService) initializeRolePermissions() {
	as.rbacMutex.Lock()
	defer as.rbacMutex.Unlock()

	as.rolePermissions[RoleAdmin] = []Permission{
		PermissionRead, PermissionWrite, PermissionDelete,
		PermissionManageUsers, PermissionManageSystem,
		PermissionExportData, PermissionImportData,
		PermissionViewAuditLogs,
	}

	as.rolePermissions[RoleEngineer] = []Permission{
		PermissionRead, PermissionWrite, PermissionExportData,
		PermissionImportData,
	}

	as.rolePermissions[RoleViewer] = []Permission{
		PermissionRead,
	}

	as.rolePermissions[RoleContractor] = []Permission{
		PermissionRead, PermissionWrite,
	}

	as.rolePermissions[RoleGuest] = []Permission{
		PermissionRead,
	}
}

// HashPassword hashes a password using bcrypt
func (as *AuthService) HashPassword(password string) (string, error) {
	hashedBytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", fmt.Errorf("failed to hash password: %w", err)
	}
	return string(hashedBytes), nil
}

// VerifyPassword verifies a password against its hash
func (as *AuthService) VerifyPassword(password, hashedPassword string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(password))
	return err == nil
}

// GenerateToken generates a JWT token for a user
func (as *AuthService) GenerateToken(user *User) (string, error) {
	now := time.Now()
	claims := &TokenClaims{
		UserID:   user.ID,
		Username: user.Username,
		Roles:    user.Roles,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(now.Add(as.tokenExpiry)),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "arxos",
			Subject:   user.ID,
			ID:        uuid.New().String(),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(as.secretKey))
}

// GenerateRefreshToken generates a refresh token
func (as *AuthService) GenerateRefreshToken(user *User) (string, error) {
	now := time.Now()
	claims := &TokenClaims{
		UserID:   user.ID,
		Username: user.Username,
		Roles:    user.Roles,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(now.Add(as.refreshTokenExpiry)),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "arxos",
			Subject:   user.ID,
			ID:        uuid.New().String(),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(as.secretKey))
}

// VerifyToken verifies and decodes a JWT token
func (as *AuthService) VerifyToken(tokenString string) (*TokenClaims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &TokenClaims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(as.secretKey), nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to parse token: %w", err)
	}

	if claims, ok := token.Claims.(*TokenClaims); ok && token.Valid {
		return claims, nil
	}

	return nil, fmt.Errorf("invalid token")
}

// RefreshToken generates a new access token from a refresh token
func (as *AuthService) RefreshToken(refreshToken string) (string, error) {
	claims, err := as.VerifyToken(refreshToken)
	if err != nil {
		return "", fmt.Errorf("invalid refresh token: %w", err)
	}

	// Create user object from claims
	user := &User{
		ID:       claims.UserID,
		Username: claims.Username,
		Roles:    claims.Roles,
	}

	return as.GenerateToken(user)
}

// CreateSession creates a new session for a user
func (as *AuthService) CreateSession(userID string, sessionData map[string]interface{}) (*Session, error) {
	sessionID, err := generateSessionID()
	if err != nil {
		return nil, fmt.Errorf("failed to generate session ID: %w", err)
	}

	now := time.Now()
	session := &Session{
		ID:           sessionID,
		UserID:       userID,
		Data:         sessionData,
		CreatedAt:    now,
		LastActivity: now,
		ExpiresAt:    now.Add(as.sessionTimeout),
	}

	as.sessionMutex.Lock()
	as.activeSessions[sessionID] = session
	as.sessionMutex.Unlock()

	return session, nil
}

// GetSession retrieves session data
func (as *AuthService) GetSession(sessionID string) (*Session, error) {
	as.sessionMutex.RLock()
	session, exists := as.activeSessions[sessionID]
	as.sessionMutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("session not found")
	}

	// Check if session has expired
	if time.Now().After(session.ExpiresAt) {
		as.RemoveSession(sessionID)
		return nil, fmt.Errorf("session has expired")
	}

	// Update last activity
	as.sessionMutex.Lock()
	session.LastActivity = time.Now()
	session.ExpiresAt = time.Now().Add(as.sessionTimeout)
	as.sessionMutex.Unlock()

	return session, nil
}

// RemoveSession removes a session
func (as *AuthService) RemoveSession(sessionID string) {
	as.sessionMutex.Lock()
	delete(as.activeSessions, sessionID)
	as.sessionMutex.Unlock()
}

// CleanupExpiredSessions removes expired sessions
func (as *AuthService) CleanupExpiredSessions() {
	as.sessionMutex.Lock()
	defer as.sessionMutex.Unlock()

	now := time.Now()
	for sessionID, session := range as.activeSessions {
		if now.After(session.ExpiresAt) {
			delete(as.activeSessions, sessionID)
		}
	}
}

// CheckPermission checks if a user has a specific permission
func (as *AuthService) CheckPermission(user *User, permission Permission) bool {
	as.rbacMutex.RLock()
	defer as.rbacMutex.RUnlock()

	for _, role := range user.Roles {
		if permissions, exists := as.rolePermissions[role]; exists {
			for _, perm := range permissions {
				if perm == permission {
					return true
				}
			}
		}
	}
	return false
}

// GetUserPermissions returns all permissions for a user
func (as *AuthService) GetUserPermissions(user *User) []Permission {
	as.rbacMutex.RLock()
	defer as.rbacMutex.RUnlock()

	permissions := make(map[Permission]bool)
	for _, role := range user.Roles {
		if rolePerms, exists := as.rolePermissions[role]; exists {
			for _, perm := range rolePerms {
				permissions[perm] = true
			}
		}
	}

	result := make([]Permission, 0, len(permissions))
	for perm := range permissions {
		result = append(result, perm)
	}
	return result
}

// AddRolePermission adds a permission to a role
func (as *AuthService) AddRolePermission(role UserRole, permission Permission) {
	as.rbacMutex.Lock()
	defer as.rbacMutex.Unlock()

	if as.rolePermissions[role] == nil {
		as.rolePermissions[role] = make([]Permission, 0)
	}

	// Check if permission already exists
	for _, existingPerm := range as.rolePermissions[role] {
		if existingPerm == permission {
			return
		}
	}

	as.rolePermissions[role] = append(as.rolePermissions[role], permission)
}

// RemoveRolePermission removes a permission from a role
func (as *AuthService) RemoveRolePermission(role UserRole, permission Permission) {
	as.rbacMutex.Lock()
	defer as.rbacMutex.Unlock()

	if permissions, exists := as.rolePermissions[role]; exists {
		for i, perm := range permissions {
			if perm == permission {
				as.rolePermissions[role] = append(permissions[:i], permissions[i+1:]...)
				break
			}
		}
	}
}

// ValidateUserCredentials validates user credentials
func (as *AuthService) ValidateUserCredentials(username, password string, hashedPassword string) bool {
	// Verify password
	if !as.VerifyPassword(password, hashedPassword) {
		return false
	}

	// Additional validation can be added here (e.g., check if user is active)
	return true
}

// generateSessionID generates a secure session ID
func generateSessionID() (string, error) {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(bytes), nil
}

// GetActiveSessionsCount returns the number of active sessions
func (as *AuthService) GetActiveSessionsCount() int {
	as.sessionMutex.RLock()
	defer as.sessionMutex.RUnlock()
	return len(as.activeSessions)
}

// GetSessionStats returns session statistics
func (as *AuthService) GetSessionStats() map[string]interface{} {
	as.sessionMutex.RLock()
	defer as.sessionMutex.RUnlock()

	now := time.Now()
	activeCount := 0
	expiredCount := 0

	for _, session := range as.activeSessions {
		if now.Before(session.ExpiresAt) {
			activeCount++
		} else {
			expiredCount++
		}
	}

	return map[string]interface{}{
		"total_sessions":   len(as.activeSessions),
		"active_sessions":  activeCount,
		"expired_sessions": expiredCount,
		"session_timeout":  as.sessionTimeout.String(),
	}
}
