package api

import (
	"context"
	"time"

	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/logger"
)

// SessionCleanup manages periodic cleanup of expired sessions
type SessionCleanup struct {
	db       database.DB
	interval time.Duration
	stop     chan bool
}

// NewSessionCleanup creates a new session cleanup service
func NewSessionCleanup(db database.DB, interval time.Duration) *SessionCleanup {
	if interval <= 0 {
		interval = 1 * time.Hour // Default to hourly cleanup
	}
	return &SessionCleanup{
		db:       db,
		interval: interval,
		stop:     make(chan bool),
	}
}

// Start begins the periodic cleanup process
func (sc *SessionCleanup) Start(ctx context.Context) {
	ticker := time.NewTicker(sc.interval)
	defer ticker.Stop()

	logger.Info("Starting session cleanup service (interval: %v)", sc.interval)
	
	// Run initial cleanup
	sc.cleanup(ctx)

	for {
		select {
		case <-ticker.C:
			sc.cleanup(ctx)
		case <-sc.stop:
			logger.Info("Stopping session cleanup service")
			return
		case <-ctx.Done():
			logger.Info("Session cleanup service stopped due to context cancellation")
			return
		}
	}
}

// Stop stops the cleanup process
func (sc *SessionCleanup) Stop() {
	close(sc.stop)
}

// cleanup performs the actual cleanup of expired sessions
func (sc *SessionCleanup) cleanup(ctx context.Context) {
	if err := sc.db.DeleteExpiredSessions(ctx); err != nil {
		logger.Error("Failed to clean up expired sessions: %v", err)
	} else {
		logger.Debug("Expired sessions cleaned up successfully")
	}
}