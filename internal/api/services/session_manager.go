package services

import (
	"context"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
)

// SessionManager handles session lifecycle management
type SessionManager struct {
	db              database.DB
	cleanupInterval time.Duration
	sessionTimeout  time.Duration
	stopChan        chan struct{}
}

// NewSessionManager creates a new session manager
func NewSessionManager(db database.DB, cleanupInterval, sessionTimeout time.Duration) *SessionManager {
	if cleanupInterval <= 0 {
		cleanupInterval = 15 * time.Minute // Default: clean every 15 minutes
	}
	if sessionTimeout <= 0 {
		sessionTimeout = 24 * time.Hour // Default: 24 hour session timeout
	}

	return &SessionManager{
		db:              db,
		cleanupInterval: cleanupInterval,
		sessionTimeout:  sessionTimeout,
		stopChan:        make(chan struct{}),
	}
}

// Start begins the session cleanup routine
func (sm *SessionManager) Start(ctx context.Context) {
	logger.Info("Starting session manager with cleanup interval: %v", sm.cleanupInterval)

	ticker := time.NewTicker(sm.cleanupInterval)
	defer ticker.Stop()

	// Run initial cleanup
	sm.cleanup(ctx)

	for {
		select {
		case <-ctx.Done():
			logger.Info("Session manager stopping due to context cancellation")
			return
		case <-sm.stopChan:
			logger.Info("Session manager stopping")
			return
		case <-ticker.C:
			sm.cleanup(ctx)
		}
	}
}

// Stop stops the session manager
func (sm *SessionManager) Stop() {
	close(sm.stopChan)
}

// cleanup removes expired sessions
func (sm *SessionManager) cleanup(ctx context.Context) {
	logger.Debug("Running session cleanup")

	// Create a new context with timeout for cleanup operation
	cleanupCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	// Delete expired sessions
	if err := sm.db.DeleteExpiredSessions(cleanupCtx); err != nil {
		logger.Error("Failed to delete expired sessions: %v", err)
		return
	}

	// Also clean up sessions that haven't been accessed in sessionTimeout
	if err := sm.deleteInactiveSessions(cleanupCtx); err != nil {
		logger.Error("Failed to delete inactive sessions: %v", err)
		return
	}

	logger.Debug("Session cleanup completed")
}

// deleteInactiveSessions removes sessions that haven't been accessed recently
func (sm *SessionManager) deleteInactiveSessions(ctx context.Context) error {
	// This would need to be implemented in the database layer
	// For now, we'll rely on the expires_at field
	// In a production system, you'd track last_accessed_at separately
	return nil
}

// ValidateSession checks if a session is still valid
func (sm *SessionManager) ValidateSession(ctx context.Context, token string) (bool, error) {
	session, err := sm.db.GetSession(ctx, token)
	if err != nil {
		if err == database.ErrNotFound {
			return false, nil
		}
		return false, err
	}

	// Check if session is expired
	if session.ExpiresAt.Before(time.Now()) {
		// Session expired, delete it
		_ = sm.db.DeleteSession(ctx, session.ID)
		return false, nil
	}

	// Check if session has been inactive too long
	inactiveTime := time.Since(session.LastAccessAt)
	if inactiveTime > sm.sessionTimeout {
		// Session inactive too long, delete it
		_ = sm.db.DeleteSession(ctx, session.ID)
		return false, nil
	}

	// Update last accessed time
	session.LastAccessAt = time.Now()
	if err := sm.db.UpdateSession(ctx, session); err != nil {
		logger.Error("Failed to update session last access: %v", err)
		// Don't fail validation if we can't update last access
	}

	return true, nil
}

// ExtendSession extends the expiration time of a session
func (sm *SessionManager) ExtendSession(ctx context.Context, token string, duration time.Duration) error {
	session, err := sm.db.GetSession(ctx, token)
	if err != nil {
		return err
	}

	session.ExpiresAt = time.Now().Add(duration)
	session.LastAccessAt = time.Now()

	return sm.db.UpdateSession(ctx, session)
}

// GetActiveSessions returns the count of active sessions for a user
func (sm *SessionManager) GetActiveSessions(ctx context.Context, userID string) (int, error) {
	// This would need a new database method to count sessions by user
	// For now, return 0
	return 0, nil
}

// RevokeAllUserSessions invalidates all sessions for a user
func (sm *SessionManager) RevokeAllUserSessions(ctx context.Context, userID string) error {
	return sm.db.DeleteUserSessions(ctx, userID)
}
