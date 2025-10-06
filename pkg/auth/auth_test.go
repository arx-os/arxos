package auth

import (
	"testing"
	"time"

	"github.com/arx-os/arxos/pkg/errors"
)

func TestJWTManager(t *testing.T) {
	config := DefaultJWTConfig()
	jwtMgr, err := NewJWTManager(config)
	if err != nil {
		t.Fatalf("Failed to create JWT manager: %v", err)
	}

	// Test token generation
	tokenPair, err := jwtMgr.GenerateTokenPair(
		"user123",
		"test@example.com",
		"testuser",
		"admin",
		"org123",
		[]string{"read", "write"},
		"session123",
		map[string]any{"device": "mobile"},
	)
	if err != nil {
		t.Fatalf("Failed to generate token pair: %v", err)
	}

	if tokenPair.AccessToken == "" {
		t.Error("Access token should not be empty")
	}
	if tokenPair.RefreshToken == "" {
		t.Error("Refresh token should not be empty")
	}
	if tokenPair.TokenType != "Bearer" {
		t.Errorf("Expected TokenType 'Bearer', got '%s'", tokenPair.TokenType)
	}

	// Test token validation
	claims, err := jwtMgr.ValidateToken(tokenPair.AccessToken)
	if err != nil {
		t.Fatalf("Failed to validate token: %v", err)
	}

	if claims.UserID != "user123" {
		t.Errorf("Expected UserID 'user123', got '%s'", claims.UserID)
	}
	if claims.Email != "test@example.com" {
		t.Errorf("Expected Email 'test@example.com', got '%s'", claims.Email)
	}
	if claims.Role != "admin" {
		t.Errorf("Expected Role 'admin', got '%s'", claims.Role)
	}

	// Test token refresh
	newTokenPair, err := jwtMgr.RefreshToken(tokenPair.RefreshToken)
	if err != nil {
		t.Fatalf("Failed to refresh token: %v", err)
	}

	if newTokenPair.AccessToken == tokenPair.AccessToken {
		t.Error("New access token should be different from old one")
	}

	// Test expired token
	expiredConfig := DefaultJWTConfig()
	expiredConfig.AccessTokenExpiry = -time.Hour // Expired in the past
	expiredJwtMgr, err := NewJWTManager(expiredConfig)
	if err != nil {
		t.Fatalf("Failed to create expired JWT manager: %v", err)
	}

	expiredTokenPair, err := expiredJwtMgr.GenerateTokenPair(
		"user123",
		"test@example.com",
		"testuser",
		"admin",
		"org123",
		[]string{"read", "write"},
		"session123",
		nil,
	)
	if err != nil {
		t.Fatalf("Failed to generate expired token: %v", err)
	}

	_, err = expiredJwtMgr.ValidateToken(expiredTokenPair.AccessToken)
	if err == nil {
		t.Error("Expected error for expired token")
	}
	if !errors.IsUnauthorized(err) {
		t.Errorf("Expected unauthorized error, got: %v", err)
	}
}

func TestPasswordManager(t *testing.T) {
	config := DefaultPasswordConfig()
	pm := NewPasswordManager(config)

	// Test password hashing
	password := "TestPassword123!"
	hash, err := pm.HashPassword(password)
	if err != nil {
		t.Fatalf("Failed to hash password: %v", err)
	}

	if hash == "" {
		t.Error("Hash should not be empty")
	}

	// Test password verification
	err = pm.VerifyPassword(password, hash)
	if err != nil {
		t.Fatalf("Failed to verify password: %v", err)
	}

	// Test wrong password
	err = pm.VerifyPassword("WrongPassword", hash)
	if err == nil {
		t.Error("Expected error for wrong password")
	}

	// Test password strength validation
	tests := []struct {
		password   string
		shouldPass bool
	}{
		{"short", false},           // Too short
		{"TestPassword123!", true}, // Valid
		{"nouppercase123!", false}, // No uppercase
		{"NOLOWERCASE123!", false}, // No lowercase
		{"NoNumbers!", false},      // No numbers
		{"NoSpecial123", false},    // No special chars
		{"", false},                // Empty
	}

	for _, tt := range tests {
		t.Run(tt.password, func(t *testing.T) {
			err := pm.ValidatePasswordStrength(tt.password)
			if tt.shouldPass && err != nil {
				t.Errorf("Expected password to pass validation, got error: %v", err)
			}
			if !tt.shouldPass && err == nil {
				t.Errorf("Expected password to fail validation, but it passed")
			}
		})
	}

	// Test secure password generation
	securePassword, err := pm.GenerateSecurePassword(12)
	if err != nil {
		t.Fatalf("Failed to generate secure password: %v", err)
	}

	if len(securePassword) != 12 {
		t.Errorf("Expected password length 12, got %d", len(securePassword))
	}

	err = pm.ValidatePasswordStrength(securePassword)
	if err != nil {
		t.Errorf("Generated password should be valid: %v", err)
	}

	// Test password strength calculation
	strength := pm.CalculatePasswordStrength("TestPassword123!")
	if strength == PasswordStrengthVeryWeak {
		t.Error("Strong password should not be very weak")
	}
}

func TestRBACManager(t *testing.T) {
	config := DefaultRBACConfig()
	rbac := NewRBACManager(config)

	// Test permission checking
	if !rbac.CheckPermission(RoleSuperAdmin, PermissionUserRead) {
		t.Error("Super admin should have user read permission")
	}

	if !rbac.CheckPermission(RoleAdmin, PermissionBuildingWrite) {
		t.Error("Admin should have building write permission")
	}

	if rbac.CheckPermission(RoleViewer, PermissionUserDelete) {
		t.Error("Viewer should not have user delete permission")
	}

	// Test multiple permissions
	permissions := []Permission{PermissionBuildingRead, PermissionEquipmentRead}
	if !rbac.CheckMultiplePermissions(RoleViewer, permissions) {
		t.Error("Viewer should have both building and equipment read permissions")
	}

	// Test any permission
	permissions = []Permission{PermissionUserDelete, PermissionBuildingRead}
	if !rbac.CheckAnyPermission(RoleViewer, permissions) {
		t.Error("Viewer should have at least one of the permissions")
	}

	// Test role existence
	if !rbac.RoleExists(RoleAdmin) {
		t.Error("Admin role should exist")
	}

	if rbac.RoleExists("nonexistent") {
		t.Error("Nonexistent role should not exist")
	}

	// Test custom role creation
	err := rbac.CreateCustomRole(
		"custom_role",
		"Custom role for testing",
		[]Permission{PermissionBuildingRead},
		[]Role{RoleViewer},
	)
	if err != nil {
		t.Fatalf("Failed to create custom role: %v", err)
	}

	if !rbac.RoleExists("custom_role") {
		t.Error("Custom role should exist after creation")
	}

	if !rbac.CheckPermission("custom_role", PermissionBuildingRead) {
		t.Error("Custom role should have building read permission")
	}

	// Test role permissions retrieval
	permissions = rbac.GetRolePermissions(RoleAdmin)
	if len(permissions) == 0 {
		t.Error("Admin role should have permissions")
	}

	// Test authorization context
	ctx := &AuthorizationContext{
		UserID:       "user123",
		Role:         RoleAdmin,
		Permissions:  []Permission{PermissionBuildingRead},
		ResourceType: "building",
		Action:       "read",
	}

	err = rbac.Authorize(ctx)
	if err != nil {
		t.Errorf("Admin should be authorized: %v", err)
	}

	// Test insufficient permissions
	ctx.Permissions = []Permission{PermissionUserDelete}
	err = rbac.Authorize(ctx)
	if err == nil {
		t.Error("Admin should not be authorized for user delete")
	}
}

func TestAPIKeyManager(t *testing.T) {
	config := DefaultAPIKeyConfig()
	store := &mockAPIKeyStore{}
	akm := NewAPIKeyManager(config, store)

	// Test API key creation
	req := &APIKeyCreateRequest{
		Name:        "Test API Key",
		UserID:      "user123",
		Permissions: map[string]any{"read": true},
		RateLimit:   1000,
	}

	response, err := akm.CreateAPIKey(req)
	if err != nil {
		t.Fatalf("Failed to create API key: %v", err)
	}

	if response.Key == "" {
		t.Error("API key should not be empty")
	}

	if response.Name != req.Name {
		t.Errorf("Expected name '%s', got '%s'", req.Name, response.Name)
	}

	// Test API key validation
	apiKey, err := akm.ValidateAPIKey(response.Key)
	if err != nil {
		t.Fatalf("Failed to validate API key: %v", err)
	}

	if apiKey.Name != req.Name {
		t.Errorf("Expected name '%s', got '%s'", req.Name, apiKey.Name)
	}

	// Test invalid API key
	_, err = akm.ValidateAPIKey("invalid_key")
	if err == nil {
		t.Error("Expected error for invalid API key")
	}

	// Test permission checking
	if !CheckPermission(apiKey, "read") {
		t.Error("API key should have read permission")
	}

	if CheckPermission(apiKey, "write") {
		t.Error("API key should not have write permission")
	}
}

func TestSessionManager(t *testing.T) {
	config := DefaultSessionConfig()
	store := &mockSessionStore{}
	jwtMgr, _ := NewJWTManager(DefaultJWTConfig())
	sm := NewSessionManager(config, store, jwtMgr)

	// Test session creation
	session, err := sm.CreateSession(
		"user123",
		"org123",
		"192.168.1.1",
		"Mozilla/5.0",
		map[string]any{"device": "desktop"},
	)
	if err != nil {
		t.Fatalf("Failed to create session: %v", err)
	}

	if session.UserID != "user123" {
		t.Errorf("Expected UserID 'user123', got '%s'", session.UserID)
	}

	if !session.IsActive {
		t.Error("Session should be active")
	}

	// Test session validation
	validatedSession, err := sm.ValidateSession(session.ID)
	if err != nil {
		t.Fatalf("Failed to validate session: %v", err)
	}

	if validatedSession.ID != session.ID {
		t.Errorf("Expected session ID '%s', got '%s'", session.ID, validatedSession.ID)
	}

	// Test session revocation
	err = sm.RevokeSession(session.ID)
	if err != nil {
		t.Fatalf("Failed to revoke session: %v", err)
	}

	// Test validation of revoked session
	_, err = sm.ValidateSession(session.ID)
	if err == nil {
		t.Error("Expected error for revoked session")
	}
}

// Mock implementations for testing

type mockAPIKeyStore struct {
	keys map[string]*APIKey
}

func (m *mockAPIKeyStore) Create(apiKey *APIKey) error {
	if m.keys == nil {
		m.keys = make(map[string]*APIKey)
	}
	m.keys[apiKey.ID] = apiKey
	return nil
}

func (m *mockAPIKeyStore) Get(id string) (*APIKey, error) {
	if key, exists := m.keys[id]; exists {
		return key, nil
	}
	return nil, errors.New(errors.CodeNotFound, "API key not found")
}

func (m *mockAPIKeyStore) GetByHash(hash string) (*APIKey, error) {
	for _, key := range m.keys {
		if key.KeyHash == hash {
			return key, nil
		}
	}
	return nil, errors.New(errors.CodeNotFound, "API key not found")
}

func (m *mockAPIKeyStore) Update(apiKey *APIKey) error {
	if _, exists := m.keys[apiKey.ID]; !exists {
		return errors.New(errors.CodeNotFound, "API key not found")
	}
	m.keys[apiKey.ID] = apiKey
	return nil
}

func (m *mockAPIKeyStore) Delete(id string) error {
	delete(m.keys, id)
	return nil
}

func (m *mockAPIKeyStore) ListByUserID(userID string) ([]*APIKey, error) {
	var keys []*APIKey
	for _, key := range m.keys {
		if key.UserID == userID {
			keys = append(keys, key)
		}
	}
	return keys, nil
}

func (m *mockAPIKeyStore) ListByOrganizationID(organizationID string) ([]*APIKey, error) {
	var keys []*APIKey
	for _, key := range m.keys {
		if key.OrganizationID == organizationID {
			keys = append(keys, key)
		}
	}
	return keys, nil
}

func (m *mockAPIKeyStore) CleanupExpired() error {
	return nil
}

type mockSessionStore struct {
	sessions map[string]*Session
}

func (m *mockSessionStore) Create(session *Session) error {
	if m.sessions == nil {
		m.sessions = make(map[string]*Session)
	}
	m.sessions[session.ID] = session
	return nil
}

func (m *mockSessionStore) Get(sessionID string) (*Session, error) {
	if session, exists := m.sessions[sessionID]; exists {
		return session, nil
	}
	return nil, errors.New(errors.CodeNotFound, "session not found")
}

func (m *mockSessionStore) GetByToken(token string) (*Session, error) {
	for _, session := range m.sessions {
		if session.Token == token {
			return session, nil
		}
	}
	return nil, errors.New(errors.CodeNotFound, "session not found")
}

func (m *mockSessionStore) GetByRefreshToken(refreshToken string) (*Session, error) {
	for _, session := range m.sessions {
		if session.RefreshToken == refreshToken {
			return session, nil
		}
	}
	return nil, errors.New(errors.CodeNotFound, "session not found")
}

func (m *mockSessionStore) Update(session *Session) error {
	if _, exists := m.sessions[session.ID]; !exists {
		return errors.New(errors.CodeNotFound, "session not found")
	}
	m.sessions[session.ID] = session
	return nil
}

func (m *mockSessionStore) Delete(sessionID string) error {
	delete(m.sessions, sessionID)
	return nil
}

func (m *mockSessionStore) DeleteByUserID(userID string) error {
	for id, session := range m.sessions {
		if session.UserID == userID {
			delete(m.sessions, id)
		}
	}
	return nil
}

func (m *mockSessionStore) ListByUserID(userID string) ([]*Session, error) {
	var sessions []*Session
	for _, session := range m.sessions {
		if session.UserID == userID {
			sessions = append(sessions, session)
		}
	}
	return sessions, nil
}

func (m *mockSessionStore) CleanupExpired() error {
	return nil
}
