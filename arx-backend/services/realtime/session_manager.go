package realtime

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// SessionStatus represents the status of a session
type SessionStatus string

const (
	SessionStatusActive   SessionStatus = "active"
	SessionStatusInactive SessionStatus = "inactive"
	SessionStatusExpired  SessionStatus = "expired"
	SessionStatusSuspended SessionStatus = "suspended"
)

// SessionType represents the type of session
type SessionType string

const (
	SessionTypeCollaboration SessionType = "collaboration"
	SessionTypeViewing       SessionType = "viewing"
	SessionTypeEditing       SessionType = "editing"
	SessionTypePresentation  SessionType = "presentation"
)

// SessionState represents the state of a session
type SessionState struct {
	ID              string           `json:"id" gorm:"primaryKey"`
	SessionID       string           `json:"session_id"`
	UserID          string           `json:"user_id"`
	RoomID          string           `json:"room_id"`
	Status          SessionStatus    `json:"status"`
	Type            SessionType      `json:"type"`
	CurrentElement  *string          `json:"current_element"`
	Viewport        json.RawMessage  `json:"viewport"`
	ZoomLevel       float64          `json:"zoom_level"`
	PanOffset       json.RawMessage  `json:"pan_offset"`
	SelectedElements json.RawMessage `json:"selected_elements"`
	LastActivity    time.Time        `json:"last_activity"`
	Metadata        json.RawMessage  `json:"metadata"`
	CreatedAt       time.Time        `json:"created_at"`
	UpdatedAt       time.Time        `json:"updated_at"`
}

// SessionActivity represents session activity
type SessionActivity struct {
	ID          string           `json:"id" gorm:"primaryKey"`
	SessionID   string           `json:"session_id"`
	UserID      string           `json:"user_id"`
	ActivityType string          `json:"activity_type"`
	ElementID   *string          `json:"element_id"`
	Data        json.RawMessage  `json:"data"`
	Timestamp   time.Time        `json:"timestamp"`
	CreatedAt   time.Time        `json:"created_at"`
}

// SessionConfig represents session configuration
type SessionConfig struct {
	SessionTimeout        time.Duration `json:"session_timeout"`
	ActivityTimeout       time.Duration `json:"activity_timeout"`
	MaxSessionsPerUser    int           `json:"max_sessions_per_user"`
	MaxUsersPerSession    int           `json:"max_users_per_session"`
	EnableActivityLogging bool          `json:"enable_activity_logging"`
	EnableStatePersistence bool         `json:"enable_state_persistence"`
	CleanupInterval       time.Duration `json:"cleanup_interval"`
}

// SessionManager manages user sessions and session state
type SessionManager struct {
	db              *gorm.DB
	mu              sync.RWMutex
	sessions        map[string]*SessionState
	userSessions    map[string][]string // user_id -> session_ids
	roomSessions    map[string][]string // room_id -> session_ids
	config          *SessionConfig
	activityChan    chan *SessionActivity
	stopChan        chan struct{}
	isRunning       bool
}

// NewSessionManager creates a new session manager
func NewSessionManager(db *gorm.DB, config *SessionConfig) *SessionManager {
	if config == nil {
		config = &SessionConfig{
			SessionTimeout:        1 * time.Hour,
			ActivityTimeout:        5 * time.Minute,
			MaxSessionsPerUser:    3,
			MaxUsersPerSession:    50,
			EnableActivityLogging: true,
			EnableStatePersistence: true,
			CleanupInterval:       5 * time.Minute,
		}
	}

	return &SessionManager{
		db:           db,
		sessions:     make(map[string]*SessionState),
		userSessions: make(map[string][]string),
		roomSessions: make(map[string][]string),
		config:       config,
		activityChan: make(chan *SessionActivity, 1000),
		stopChan:     make(chan struct{}),
	}
}

// Start starts the session manager
func (sm *SessionManager) Start(ctx context.Context) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	if sm.isRunning {
		return fmt.Errorf("session manager is already running")
	}

	sm.isRunning = true

	// Start activity processing loop
	go sm.activityProcessingLoop(ctx)

	// Start cleanup loop
	go sm.cleanupLoop(ctx)

	return nil
}

// Stop stops the session manager
func (sm *SessionManager) Stop() {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	if !sm.isRunning {
		return
	}

	sm.isRunning = false
	close(sm.stopChan)
}

// CreateSession creates a new session
func (sm *SessionManager) CreateSession(ctx context.Context, userID, roomID string, sessionType SessionType) (*SessionState, error) {
	// Check if user has too many active sessions
	if sm.getUserSessionCount(userID) >= sm.config.MaxSessionsPerUser {
		return nil, fmt.Errorf("user has too many active sessions")
	}

	// Check if room has too many users
	if sm.getRoomSessionCount(roomID) >= sm.config.MaxUsersPerSession {
		return nil, fmt.Errorf("room has too many users")
	}

	sessionID := generateSessionID()
	session := &SessionState{
		ID:              sessionID,
		SessionID:       sessionID,
		UserID:          userID,
		RoomID:          roomID,
		Status:          SessionStatusActive,
		Type:            sessionType,
		ZoomLevel:       1.0,
		SelectedElements: json.RawMessage("[]"),
		LastActivity:    time.Now(),
		Metadata:        json.RawMessage("{}"),
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}

	if err := sm.db.WithContext(ctx).Create(session).Error; err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}

	sm.mu.Lock()
	sm.sessions[sessionID] = session
	sm.userSessions[userID] = append(sm.userSessions[userID], sessionID)
	sm.roomSessions[roomID] = append(sm.roomSessions[roomID], sessionID)
	sm.mu.Unlock()

	// Log session creation activity
	sm.logActivity(ctx, sessionID, userID, "session_created", nil, map[string]interface{}{
		"session_type": sessionType,
		"room_id":      roomID,
	})

	return session, nil
}

// GetSession gets a session by ID
func (sm *SessionManager) GetSession(ctx context.Context, sessionID string) (*SessionState, error) {
	var session SessionState
	if err := sm.db.WithContext(ctx).Where("session_id = ?", sessionID).First(&session).Error; err != nil {
		return nil, fmt.Errorf("session not found: %w", err)
	}
	return &session, nil
}

// UpdateSession updates a session
func (sm *SessionManager) UpdateSession(ctx context.Context, sessionID string, updates map[string]interface{}) error {
	updates["updated_at"] = time.Now()

	if err := sm.db.WithContext(ctx).Model(&SessionState{}).Where("session_id = ?", sessionID).Updates(updates).Error; err != nil {
		return fmt.Errorf("failed to update session: %w", err)
	}

	// Update local cache
	sm.mu.Lock()
	if session, exists := sm.sessions[sessionID]; exists {
		session.UpdatedAt = time.Now()
	}
	sm.mu.Unlock()

	return nil
}

// EndSession ends a session
func (sm *SessionManager) EndSession(ctx context.Context, sessionID string) error {
	session, err := sm.GetSession(ctx, sessionID)
	if err != nil {
		return err
	}

	// Update session status
	updates := map[string]interface{}{
		"status":     SessionStatusInactive,
		"updated_at": time.Now(),
	}

	if err := sm.UpdateSession(ctx, sessionID, updates); err != nil {
		return err
	}

	// Remove from local cache
	sm.mu.Lock()
	delete(sm.sessions, sessionID)
	sm.removeUserSession(session.UserID, sessionID)
	sm.removeRoomSession(session.RoomID, sessionID)
	sm.mu.Unlock()

	// Log session end activity
	sm.logActivity(ctx, sessionID, session.UserID, "session_ended", nil, nil)

	return nil
}

// UpdateSessionState updates session state
func (sm *SessionManager) UpdateSessionState(ctx context.Context, sessionID string, state map[string]interface{}) error {
	// Update session state
	updates := map[string]interface{}{
		"last_activity": time.Now(),
		"updated_at":    time.Now(),
	}

	// Update specific state fields
	if currentElement, ok := state["current_element"].(string); ok {
		updates["current_element"] = currentElement
	}
	if viewport, ok := state["viewport"].(map[string]interface{}); ok {
		updates["viewport"] = mustMarshalJSON(viewport)
	}
	if zoomLevel, ok := state["zoom_level"].(float64); ok {
		updates["zoom_level"] = zoomLevel
	}
	if panOffset, ok := state["pan_offset"].(map[string]interface{}); ok {
		updates["pan_offset"] = mustMarshalJSON(panOffset)
	}
	if selectedElements, ok := state["selected_elements"].([]interface{}); ok {
		updates["selected_elements"] = mustMarshalJSON(selectedElements)
	}

	return sm.UpdateSession(ctx, sessionID, updates)
}

// GetUserSessions gets all sessions for a user
func (sm *SessionManager) GetUserSessions(ctx context.Context, userID string) ([]SessionState, error) {
	var sessions []SessionState
	if err := sm.db.WithContext(ctx).Where("user_id = ?", userID).Find(&sessions).Error; err != nil {
		return nil, fmt.Errorf("failed to get user sessions: %w", err)
	}
	return sessions, nil
}

// GetRoomSessions gets all sessions in a room
func (sm *SessionManager) GetRoomSessions(ctx context.Context, roomID string) ([]SessionState, error) {
	var sessions []SessionState
	if err := sm.db.WithContext(ctx).Where("room_id = ? AND status = ?", roomID, SessionStatusActive).Find(&sessions).Error; err != nil {
		return nil, fmt.Errorf("failed to get room sessions: %w", err)
	}
	return sessions, nil
}

// GetSessionActivities gets activities for a session
func (sm *SessionManager) GetSessionActivities(ctx context.Context, sessionID string, limit int) ([]SessionActivity, error) {
	var activities []SessionActivity
	if err := sm.db.WithContext(ctx).Where("session_id = ?", sessionID).Order("timestamp DESC").Limit(limit).Find(&activities).Error; err != nil {
		return nil, fmt.Errorf("failed to get session activities: %w", err)
	}
	return activities, nil
}

// LogActivity logs a session activity
func (sm *SessionManager) LogActivity(ctx context.Context, sessionID, userID, activityType string, elementID *string, data map[string]interface{}) error {
	return sm.logActivity(ctx, sessionID, userID, activityType, elementID, data)
}

// logActivity logs a session activity
func (sm *SessionManager) logActivity(ctx context.Context, sessionID, userID, activityType string, elementID *string, data map[string]interface{}) {
	if !sm.config.EnableActivityLogging {
		return
	}

	activity := &SessionActivity{
		ID:           generateActivityID(),
		SessionID:    sessionID,
		UserID:       userID,
		ActivityType: activityType,
		ElementID:    elementID,
		Data:         mustMarshalJSON(data),
		Timestamp:    time.Now(),
		CreatedAt:    time.Now(),
	}

	sm.db.WithContext(ctx).Create(activity)

	// Send to activity channel for processing
	select {
	case sm.activityChan <- activity:
	default:
		// Channel is full, drop activity
	}
}

// getUserSessionCount gets the number of active sessions for a user
func (sm *SessionManager) getUserSessionCount(userID string) int {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	if sessions, exists := sm.userSessions[userID]; exists {
		return len(sessions)
	}
	return 0
}

// getRoomSessionCount gets the number of active sessions in a room
func (sm *SessionManager) getRoomSessionCount(roomID string) int {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	if sessions, exists := sm.roomSessions[roomID]; exists {
		return len(sessions)
	}
	return 0
}

// removeUserSession removes a session from user sessions
func (sm *SessionManager) removeUserSession(userID, sessionID string) {
	if sessions, exists := sm.userSessions[userID]; exists {
		for i, session := range sessions {
			if session == sessionID {
				sm.userSessions[userID] = append(sessions[:i], sessions[i+1:]...)
				break
			}
		}
	}
}

// removeRoomSession removes a session from room sessions
func (sm *SessionManager) removeRoomSession(roomID, sessionID string) {
	if sessions, exists := sm.roomSessions[roomID]; exists {
		for i, session := range sessions {
			if session == sessionID {
				sm.roomSessions[roomID] = append(sessions[:i], sessions[i+1:]...)
				break
			}
		}
	}
}

// activityProcessingLoop processes session activities
func (sm *SessionManager) activityProcessingLoop(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-sm.stopChan:
			return
		case activity := <-sm.activityChan:
			sm.processActivity(activity)
		}
	}
}

// processActivity processes a session activity
func (sm *SessionManager) processActivity(activity *SessionActivity) {
	// Update session last activity
	sm.db.Model(&SessionState{}).Where("session_id = ?", activity.SessionID).Updates(map[string]interface{}{
		"last_activity": activity.Timestamp,
		"updated_at":    activity.Timestamp,
	})

	// In a real implementation, this could trigger notifications, analytics, etc.
	fmt.Printf("Session activity: %s by user %s in session %s\n", activity.ActivityType, activity.UserID, activity.SessionID)
}

// cleanupLoop cleans up expired sessions
func (sm *SessionManager) cleanupLoop(ctx context.Context) {
	ticker := time.NewTicker(sm.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-sm.stopChan:
			return
		case <-ticker.C:
			sm.cleanupExpiredSessions(ctx)
		}
	}
}

// cleanupExpiredSessions cleans up expired sessions
func (sm *SessionManager) cleanupExpiredSessions(ctx context.Context) {
	expiredTime := time.Now().Add(-sm.config.SessionTimeout)

	var expiredSessions []SessionState
	sm.db.WithContext(ctx).Where("last_activity < ? AND status = ?", expiredTime, SessionStatusActive).Find(&expiredSessions)

	for _, session := range expiredSessions {
		// Update session status to expired
		sm.db.WithContext(ctx).Model(&session).Updates(map[string]interface{}{
			"status":     SessionStatusExpired,
			"updated_at": time.Now(),
		})

		// Remove from local cache
		sm.mu.Lock()
		delete(sm.sessions, session.SessionID)
		sm.removeUserSession(session.UserID, session.SessionID)
		sm.removeRoomSession(session.RoomID, session.SessionID)
		sm.mu.Unlock()

		// Log session expiration activity
		sm.logActivity(ctx, session.SessionID, session.UserID, "session_expired", nil, nil)
	}
}

// GetSessionStats gets session statistics
func (sm *SessionManager) GetSessionStats() map[string]interface{} {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	var totalSessions, activeSessions, expiredSessions int64
	sm.db.Model(&SessionState{}).Count(&totalSessions)
	sm.db.Model(&SessionState{}).Where("status = ?", SessionStatusActive).Count(&activeSessions)
	sm.db.Model(&SessionState{}).Where("status = ?", SessionStatusExpired).Count(&expiredSessions)

	var totalActivities int64
	sm.db.Model(&SessionActivity{}).Count(&totalActivities)

	return map[string]interface{}{
		"total_sessions":     totalSessions,
		"active_sessions":    activeSessions,
		"expired_sessions":   expiredSessions,
		"total_activities":   totalActivities,
		"current_sessions":   len(sm.sessions),
		"current_users":      len(sm.userSessions),
		"current_rooms":      len(sm.roomSessions),
		"is_running":         sm.isRunning,
	}
}

// Helper functions
func generateSessionID() string {
	return fmt.Sprintf("session_%d", time.Now().UnixNano())
}

func generateActivityID() string {
	return fmt.Sprintf("activity_%d", time.Now().UnixNano())
}

func mustMarshalJSON(v interface{}) json.RawMessage {
	data, _ := json.Marshal(v)
	return data
} 