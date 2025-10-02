// Package auth provides session management utilities.
package auth

import (
	"crypto/rand"
	"encoding/base64"
	"time"

	"github.com/arx-os/arxos/pkg/errors"
)

// SessionConfig holds configuration for session management
type SessionConfig struct {
	// Session duration
	Duration time.Duration

	// Refresh token duration (longer than session)
	RefreshDuration time.Duration

	// Maximum concurrent sessions per user
	MaxSessionsPerUser int

	// Session cleanup interval
	CleanupInterval time.Duration

	// Whether to extend session on activity
	ExtendOnActivity bool

	// Idle timeout (session expires after this inactivity)
	IdleTimeout time.Duration
}

// DefaultSessionConfig returns a default session configuration
func DefaultSessionConfig() *SessionConfig {
	return &SessionConfig{
		Duration:           24 * time.Hour,     // 24 hours
		RefreshDuration:    7 * 24 * time.Hour, // 7 days
		MaxSessionsPerUser: 5,                  // 5 concurrent sessions
		CleanupInterval:    1 * time.Hour,      // Cleanup every hour
		ExtendOnActivity:   true,
		IdleTimeout:        2 * time.Hour, // 2 hours idle timeout
	}
}

// Session represents an active user session
type Session struct {
	ID               string                 `json:"id"`
	UserID           string                 `json:"user_id"`
	OrganizationID   string                 `json:"organization_id,omitempty"`
	Token            string                 `json:"token"`
	RefreshToken     string                 `json:"refresh_token"`
	IPAddress        string                 `json:"ip_address,omitempty"`
	UserAgent        string                 `json:"user_agent,omitempty"`
	DeviceInfo       map[string]interface{} `json:"device_info,omitempty"`
	IsActive         bool                   `json:"is_active"`
	ExpiresAt        time.Time              `json:"expires_at"`
	RefreshExpiresAt time.Time              `json:"refresh_expires_at"`
	LastActivity     time.Time              `json:"last_activity"`
	LastAccessAt     time.Time              `json:"last_access_at"`
	CreatedAt        time.Time              `json:"created_at"`
	UpdatedAt        time.Time              `json:"updated_at"`
}

// SessionStore defines the interface for session storage
type SessionStore interface {
	// Create creates a new session
	Create(session *Session) error

	// Get retrieves a session by ID
	Get(sessionID string) (*Session, error)

	// GetByToken retrieves a session by token
	GetByToken(token string) (*Session, error)

	// GetByRefreshToken retrieves a session by refresh token
	GetByRefreshToken(refreshToken string) (*Session, error)

	// Update updates an existing session
	Update(session *Session) error

	// Delete deletes a session
	Delete(sessionID string) error

	// DeleteByUserID deletes all sessions for a user
	DeleteByUserID(userID string) error

	// ListByUserID lists all sessions for a user
	ListByUserID(userID string) ([]*Session, error)

	// CleanupExpired removes expired sessions
	CleanupExpired() error
}

// SessionManager handles session operations
type SessionManager struct {
	config *SessionConfig
	store  SessionStore
	jwtMgr *JWTManager
}

// NewSessionManager creates a new session manager
func NewSessionManager(config *SessionConfig, store SessionStore, jwtMgr *JWTManager) *SessionManager {
	if config == nil {
		config = DefaultSessionConfig()
	}
	return &SessionManager{
		config: config,
		store:  store,
		jwtMgr: jwtMgr,
	}
}

// CreateSession creates a new user session
func (sm *SessionManager) CreateSession(userID, organizationID, ipAddress, userAgent string, deviceInfo map[string]interface{}) (*Session, error) {
	// Check session limit
	sessions, err := sm.store.ListByUserID(userID)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to check existing sessions")
	}

	// Count active sessions
	activeCount := 0
	for _, session := range sessions {
		if session.IsActive && session.ExpiresAt.After(time.Now()) {
			activeCount++
		}
	}

	if activeCount >= sm.config.MaxSessionsPerUser {
		// Remove oldest session
		if err := sm.removeOldestSession(sessions); err != nil {
			return nil, errors.Wrap(err, errors.CodeInternal, "failed to remove oldest session")
		}
	}

	// Generate session tokens
	sessionID, err := sm.generateSessionID()
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to generate session ID")
	}

	accessToken, err := sm.generateAccessToken()
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to generate access token")
	}

	refreshToken, err := sm.generateRefreshToken()
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to generate refresh token")
	}

	now := time.Now()
	session := &Session{
		ID:               sessionID,
		UserID:           userID,
		OrganizationID:   organizationID,
		Token:            accessToken,
		RefreshToken:     refreshToken,
		IPAddress:        ipAddress,
		UserAgent:        userAgent,
		DeviceInfo:       deviceInfo,
		IsActive:         true,
		ExpiresAt:        now.Add(sm.config.Duration),
		RefreshExpiresAt: now.Add(sm.config.RefreshDuration),
		LastActivity:     now,
		LastAccessAt:     now,
		CreatedAt:        now,
		UpdatedAt:        now,
	}

	if err := sm.store.Create(session); err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to create session")
	}

	return session, nil
}

// ValidateSession validates a session and returns it
func (sm *SessionManager) ValidateSession(sessionID string) (*Session, error) {
	session, err := sm.store.Get(sessionID)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeUnauthorized, "session not found")
	}

	if !session.IsActive {
		return nil, errors.New(errors.CodeUnauthorized, "session is inactive")
	}

	if session.ExpiresAt.Before(time.Now()) {
		// Mark session as expired
		session.IsActive = false
		sm.store.Update(session)
		return nil, errors.New(errors.CodeTokenExpired, "session has expired")
	}

	// Check idle timeout
	if sm.config.IdleTimeout > 0 {
		if time.Since(session.LastActivity) > sm.config.IdleTimeout {
			// Mark session as expired due to inactivity
			session.IsActive = false
			sm.store.Update(session)
			return nil, errors.New(errors.CodeTokenExpired, "session expired due to inactivity")
		}
	}

	// Update last access time
	session.LastAccessAt = time.Now()
	if sm.config.ExtendOnActivity {
		session.LastActivity = time.Now()
	}

	if err := sm.store.Update(session); err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to update session")
	}

	return session, nil
}

// RefreshSession refreshes a session using refresh token
func (sm *SessionManager) RefreshSession(refreshToken string) (*Session, error) {
	session, err := sm.store.GetByRefreshToken(refreshToken)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeUnauthorized, "invalid refresh token")
	}

	if !session.IsActive {
		return nil, errors.New(errors.CodeUnauthorized, "session is inactive")
	}

	if session.RefreshExpiresAt.Before(time.Now()) {
		// Mark session as expired
		session.IsActive = false
		sm.store.Update(session)
		return nil, errors.New(errors.CodeTokenExpired, "refresh token has expired")
	}

	// Generate new tokens
	newAccessToken, err := sm.generateAccessToken()
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to generate new access token")
	}

	newRefreshToken, err := sm.generateRefreshToken()
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to generate new refresh token")
	}

	// Update session
	now := time.Now()
	session.Token = newAccessToken
	session.RefreshToken = newRefreshToken
	session.ExpiresAt = now.Add(sm.config.Duration)
	session.RefreshExpiresAt = now.Add(sm.config.RefreshDuration)
	session.LastActivity = now
	session.LastAccessAt = now
	session.UpdatedAt = now

	if err := sm.store.Update(session); err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to update session")
	}

	return session, nil
}

// RevokeSession revokes a session
func (sm *SessionManager) RevokeSession(sessionID string) error {
	session, err := sm.store.Get(sessionID)
	if err != nil {
		return errors.Wrap(err, errors.CodeNotFound, "session not found")
	}

	session.IsActive = false
	session.UpdatedAt = time.Now()

	return sm.store.Update(session)
}

// RevokeAllUserSessions revokes all sessions for a user
func (sm *SessionManager) RevokeAllUserSessions(userID string) error {
	return sm.store.DeleteByUserID(userID)
}

// ListUserSessions lists all active sessions for a user
func (sm *SessionManager) ListUserSessions(userID string) ([]*Session, error) {
	sessions, err := sm.store.ListByUserID(userID)
	if err != nil {
		return nil, errors.Wrap(err, errors.CodeInternal, "failed to list user sessions")
	}

	// Filter active sessions
	var activeSessions []*Session
	for _, session := range sessions {
		if session.IsActive && session.ExpiresAt.After(time.Now()) {
			activeSessions = append(activeSessions, session)
		}
	}

	return activeSessions, nil
}

// CleanupExpiredSessions removes expired sessions
func (sm *SessionManager) CleanupExpiredSessions() error {
	return sm.store.CleanupExpired()
}

// Helper methods

func (sm *SessionManager) generateSessionID() (string, error) {
	bytes := make([]byte, 32)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(bytes), nil
}

func (sm *SessionManager) generateAccessToken() (string, error) {
	bytes := make([]byte, 32)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(bytes), nil
}

func (sm *SessionManager) generateRefreshToken() (string, error) {
	bytes := make([]byte, 32)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(bytes), nil
}

func (sm *SessionManager) removeOldestSession(sessions []*Session) error {
	if len(sessions) == 0 {
		return nil
	}

	// Find oldest active session
	var oldestSession *Session
	for _, session := range sessions {
		if session.IsActive && session.ExpiresAt.After(time.Now()) {
			if oldestSession == nil || session.CreatedAt.Before(oldestSession.CreatedAt) {
				oldestSession = session
			}
		}
	}

	if oldestSession != nil {
		return sm.store.Delete(oldestSession.ID)
	}

	return nil
}

// SessionInfo represents session information for display
type SessionInfo struct {
	ID           string                 `json:"id"`
	IPAddress    string                 `json:"ip_address"`
	UserAgent    string                 `json:"user_agent"`
	DeviceInfo   map[string]interface{} `json:"device_info"`
	IsCurrent    bool                   `json:"is_current"`
	LastActivity time.Time              `json:"last_activity"`
	CreatedAt    time.Time              `json:"created_at"`
	ExpiresAt    time.Time              `json:"expires_at"`
}

// GetSessionInfo returns session information for display
func (sm *SessionManager) GetSessionInfo(session *Session, currentSessionID string) *SessionInfo {
	return &SessionInfo{
		ID:           session.ID,
		IPAddress:    session.IPAddress,
		UserAgent:    session.UserAgent,
		DeviceInfo:   session.DeviceInfo,
		IsCurrent:    session.ID == currentSessionID,
		LastActivity: session.LastActivity,
		CreatedAt:    session.CreatedAt,
		ExpiresAt:    session.ExpiresAt,
	}
}
