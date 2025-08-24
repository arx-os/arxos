package services

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"time"
	
	"github.com/arxos/arxos/core/internal/db"
	"gorm.io/gorm"
)

const (
	SessionTokenLength = 32 // bytes
	SessionTTL        = 24 * time.Hour
	SessionCacheSize  = 1000 // Number of sessions to cache in memory
)

var (
	ErrSessionNotFound = errors.New("session not found")
	ErrSessionExpired  = errors.New("session expired")
)

// Session represents a user session stored in PostgreSQL
type Session struct {
	ID              string                 `gorm:"type:uuid;default:gen_random_uuid();primaryKey"`
	SessionToken    string                 `gorm:"uniqueIndex;not null"`
	UserID          uint                   `gorm:"index;not null"`
	RefreshTokenID  string                 `gorm:"type:uuid"`
	Data            map[string]interface{} `gorm:"type:jsonb"`
	ExpiresAt       time.Time             `gorm:"index;not null"`
	LastActivityAt  time.Time             `gorm:"index"`
	UserAgent       string
	IPAddress       string
	CreatedAt       time.Time
}

// SessionService manages user sessions in PostgreSQL
type SessionService struct {
	db    *gorm.DB
	cache map[string]*SessionCache // Simple in-memory cache
}

// SessionCache represents cached session data
type SessionCache struct {
	Session   *Session
	CachedAt  time.Time
}

// NewSessionService creates a new session service
func NewSessionService() *SessionService {
	service := &SessionService{
		db:    db.DB,
		cache: make(map[string]*SessionCache),
	}
	
	// Start cleanup goroutine
	go service.startCleanupWorker()
	
	return service
}

// CreateSession creates a new session for a user
func (s *SessionService) CreateSession(userID uint, userAgent, ipAddress string, data map[string]interface{}) (*Session, error) {
	// Generate session token
	tokenBytes := make([]byte, SessionTokenLength)
	if _, err := rand.Read(tokenBytes); err != nil {
		return nil, fmt.Errorf("failed to generate session token: %w", err)
	}
	
	sessionToken := hex.EncodeToString(tokenBytes)
	
	// Create session
	session := &Session{
		SessionToken:   sessionToken,
		UserID:        userID,
		Data:          data,
		ExpiresAt:     time.Now().Add(SessionTTL),
		LastActivityAt: time.Now(),
		UserAgent:     userAgent,
		IPAddress:     ipAddress,
		CreatedAt:     time.Now(),
	}
	
	// Save to database
	if err := s.db.Create(session).Error; err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}
	
	// Cache the session
	s.cacheSession(session)
	
	return session, nil
}

// GetSession retrieves a session by token
func (s *SessionService) GetSession(sessionToken string) (*Session, error) {
	// Check cache first
	if cached := s.getCachedSession(sessionToken); cached != nil {
		return cached, nil
	}
	
	// Query database
	var session Session
	if err := s.db.Where("session_token = ?", sessionToken).First(&session).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrSessionNotFound
		}
		return nil, fmt.Errorf("database error: %w", err)
	}
	
	// Check if session is expired
	if time.Now().After(session.ExpiresAt) {
		return nil, ErrSessionExpired
	}
	
	// Update last activity
	s.touchSession(&session)
	
	// Cache the session
	s.cacheSession(&session)
	
	return &session, nil
}

// UpdateSession updates session data
func (s *SessionService) UpdateSession(sessionToken string, data map[string]interface{}) error {
	session, err := s.GetSession(sessionToken)
	if err != nil {
		return err
	}
	
	// Merge data
	if session.Data == nil {
		session.Data = make(map[string]interface{})
	}
	for key, value := range data {
		session.Data[key] = value
	}
	
	// Update in database
	if err := s.db.Model(&Session{}).Where("session_token = ?", sessionToken).Updates(map[string]interface{}{
		"data":            session.Data,
		"last_activity_at": time.Now(),
	}).Error; err != nil {
		return fmt.Errorf("failed to update session: %w", err)
	}
	
	// Update cache
	s.cacheSession(session)
	
	return nil
}

// DeleteSession removes a session
func (s *SessionService) DeleteSession(sessionToken string) error {
	// Remove from cache
	s.removeCachedSession(sessionToken)
	
	// Delete from database
	result := s.db.Where("session_token = ?", sessionToken).Delete(&Session{})
	if result.Error != nil {
		return fmt.Errorf("failed to delete session: %w", result.Error)
	}
	
	if result.RowsAffected == 0 {
		return ErrSessionNotFound
	}
	
	return nil
}

// DeleteUserSessions removes all sessions for a user
func (s *SessionService) DeleteUserSessions(userID uint) error {
	// Clear from cache
	s.clearUserSessionsFromCache(userID)
	
	// Delete from database
	return s.db.Where("user_id = ?", userID).Delete(&Session{}).Error
}

// ExtendSession extends the expiration time of a session
func (s *SessionService) ExtendSession(sessionToken string) error {
	newExpiry := time.Now().Add(SessionTTL)
	
	if err := s.db.Model(&Session{}).Where("session_token = ?", sessionToken).Updates(map[string]interface{}{
		"expires_at":      newExpiry,
		"last_activity_at": time.Now(),
	}).Error; err != nil {
		return fmt.Errorf("failed to extend session: %w", err)
	}
	
	// Update cache if present
	if cached := s.getCachedSession(sessionToken); cached != nil {
		cached.ExpiresAt = newExpiry
		cached.LastActivityAt = time.Now()
	}
	
	return nil
}

// GetUserSessions retrieves all active sessions for a user
func (s *SessionService) GetUserSessions(userID uint) ([]*Session, error) {
	var sessions []*Session
	
	err := s.db.Where("user_id = ? AND expires_at > ?", userID, time.Now()).
		Order("last_activity_at DESC").
		Find(&sessions).Error
	
	if err != nil {
		return nil, fmt.Errorf("failed to get user sessions: %w", err)
	}
	
	return sessions, nil
}

// CleanupExpiredSessions removes expired sessions from the database
func (s *SessionService) CleanupExpiredSessions() error {
	// Clear expired sessions from cache
	s.clearExpiredFromCache()
	
	// Delete expired sessions from database
	result := s.db.Where("expires_at < ?", time.Now()).Delete(&Session{})
	if result.Error != nil {
		return fmt.Errorf("failed to cleanup expired sessions: %w", result.Error)
	}
	
	fmt.Printf("Cleaned up %d expired sessions\n", result.RowsAffected)
	return nil
}

// touchSession updates the last activity timestamp
func (s *SessionService) touchSession(session *Session) {
	// Only update if more than 1 minute has passed since last activity
	if time.Since(session.LastActivityAt) > time.Minute {
		session.LastActivityAt = time.Now()
		s.db.Model(&Session{}).Where("id = ?", session.ID).Update("last_activity_at", session.LastActivityAt)
	}
}

// Cache management functions

func (s *SessionService) cacheSession(session *Session) {
	// Limit cache size
	if len(s.cache) >= SessionCacheSize {
		// Remove oldest cached entry
		var oldestToken string
		var oldestTime time.Time = time.Now()
		
		for token, cached := range s.cache {
			if cached.CachedAt.Before(oldestTime) {
				oldestTime = cached.CachedAt
				oldestToken = token
			}
		}
		
		if oldestToken != "" {
			delete(s.cache, oldestToken)
		}
	}
	
	s.cache[session.SessionToken] = &SessionCache{
		Session:  session,
		CachedAt: time.Now(),
	}
}

func (s *SessionService) getCachedSession(sessionToken string) *Session {
	if cached, exists := s.cache[sessionToken]; exists {
		// Check if cached session is still valid
		if time.Now().Before(cached.Session.ExpiresAt) {
			return cached.Session
		}
		// Remove expired session from cache
		delete(s.cache, sessionToken)
	}
	return nil
}

func (s *SessionService) removeCachedSession(sessionToken string) {
	delete(s.cache, sessionToken)
}

func (s *SessionService) clearUserSessionsFromCache(userID uint) {
	for token, cached := range s.cache {
		if cached.Session.UserID == userID {
			delete(s.cache, token)
		}
	}
}

func (s *SessionService) clearExpiredFromCache() {
	now := time.Now()
	for token, cached := range s.cache {
		if now.After(cached.Session.ExpiresAt) {
			delete(s.cache, token)
		}
	}
}

// startCleanupWorker runs periodic cleanup of expired sessions
func (s *SessionService) startCleanupWorker() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()
	
	for range ticker.C {
		if err := s.CleanupExpiredSessions(); err != nil {
			fmt.Printf("Error cleaning up sessions: %v\n", err)
		}
	}
}

// SessionInfo provides session information for API responses
type SessionInfo struct {
	ID             string    `json:"id"`
	UserAgent      string    `json:"user_agent"`
	IPAddress      string    `json:"ip_address"`
	LastActivityAt time.Time `json:"last_activity_at"`
	ExpiresAt      time.Time `json:"expires_at"`
	CreatedAt      time.Time `json:"created_at"`
	IsCurrent      bool      `json:"is_current"`
}

// GetSessionInfo returns user-friendly session information
func (s *SessionService) GetSessionInfo(userID uint, currentToken string) ([]*SessionInfo, error) {
	sessions, err := s.GetUserSessions(userID)
	if err != nil {
		return nil, err
	}
	
	info := make([]*SessionInfo, len(sessions))
	for i, session := range sessions {
		info[i] = &SessionInfo{
			ID:             session.ID,
			UserAgent:      session.UserAgent,
			IPAddress:      session.IPAddress,
			LastActivityAt: session.LastActivityAt,
			ExpiresAt:      session.ExpiresAt,
			CreatedAt:      session.CreatedAt,
			IsCurrent:      session.SessionToken == currentToken,
		}
	}
	
	return info, nil
}