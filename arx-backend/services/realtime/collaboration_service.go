package realtime

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// EditStatus represents the status of a collaborative edit
type EditStatus string

const (
	EditStatusPending  EditStatus = "pending"
	EditStatusApproved EditStatus = "approved"
	EditStatusRejected EditStatus = "rejected"
	EditStatusConflict EditStatus = "conflict"
	EditStatusMerged   EditStatus = "merged"
)

// PermissionLevel represents user permission levels
type PermissionLevel string

const (
	PermissionLevelViewer PermissionLevel = "viewer"
	PermissionLevelEditor PermissionLevel = "editor"
	PermissionLevelAdmin  PermissionLevel = "admin"
	PermissionLevelOwner  PermissionLevel = "owner"
)

// CollaborationEventType represents types of collaboration events
type CollaborationEventType string

const (
	CollaborationEventTypeUserJoined        CollaborationEventType = "user_joined"
	CollaborationEventTypeUserLeft          CollaborationEventType = "user_left"
	CollaborationEventTypeEditStarted       CollaborationEventType = "edit_started"
	CollaborationEventTypeEditCompleted     CollaborationEventType = "edit_completed"
	CollaborationEventTypeConflictDetected  CollaborationEventType = "conflict_detected"
	CollaborationEventTypeConflictResolved  CollaborationEventType = "conflict_resolved"
	CollaborationEventTypeAnnotationAdded   CollaborationEventType = "annotation_added"
	CollaborationEventTypeCommentAdded      CollaborationEventType = "comment_added"
	CollaborationEventTypePermissionChanged CollaborationEventType = "permission_changed"
	CollaborationEventTypeSyncRequested     CollaborationEventType = "sync_requested"
	CollaborationEventTypeSyncCompleted     CollaborationEventType = "sync_completed"
)

// UserSession represents a user session in collaboration
type UserSession struct {
	ID             string          `json:"id" gorm:"primaryKey"`
	UserID         string          `json:"user_id"`
	Username       string          `json:"username"`
	SessionID      string          `json:"session_id"`
	RoomID         string          `json:"room_id"`
	Status         string          `json:"status"`
	Permissions    PermissionLevel `json:"permissions"`
	JoinedAt       time.Time       `json:"joined_at"`
	LastActivity   time.Time       `json:"last_activity"`
	ActiveElements json.RawMessage `json:"active_elements"`
	Metadata       json.RawMessage `json:"metadata"`
	CreatedAt      time.Time       `json:"created_at"`
	UpdatedAt      time.Time       `json:"updated_at"`
}

// CollaborativeEdit represents a collaborative edit operation
type CollaborativeEdit struct {
	ID         string          `json:"id" gorm:"primaryKey"`
	UserID     string          `json:"user_id"`
	ElementID  string          `json:"element_id"`
	EditType   string          `json:"edit_type"`
	Data       json.RawMessage `json:"data"`
	Status     EditStatus      `json:"status"`
	Conflicts  json.RawMessage `json:"conflicts"`
	Resolution json.RawMessage `json:"resolution"`
	Metadata   json.RawMessage `json:"metadata"`
	CreatedAt  time.Time       `json:"created_at"`
	UpdatedAt  time.Time       `json:"updated_at"`
}

// ConflictResolution represents conflict resolution information
type ConflictResolution struct {
	ID             string          `json:"id" gorm:"primaryKey"`
	ConflictID     string          `json:"conflict_id"`
	EditIDs        json.RawMessage `json:"edit_ids"`
	DetectedAt     time.Time       `json:"detected_at"`
	ResolvedAt     *time.Time      `json:"resolved_at"`
	ResolutionType string          `json:"resolution_type"`
	ResolvedBy     *string         `json:"resolved_by"`
	ResolutionData json.RawMessage `json:"resolution_data"`
	CreatedAt      time.Time       `json:"created_at"`
	UpdatedAt      time.Time       `json:"updated_at"`
}

// Annotation represents a collaborative annotation
type Annotation struct {
	ID             string          `json:"id" gorm:"primaryKey"`
	UserID         string          `json:"user_id"`
	ElementID      string          `json:"element_id"`
	AnnotationType string          `json:"annotation_type"`
	Content        string          `json:"content"`
	Position       json.RawMessage `json:"position"`
	Replies        json.RawMessage `json:"replies"`
	Metadata       json.RawMessage `json:"metadata"`
	CreatedAt      time.Time       `json:"created_at"`
	UpdatedAt      time.Time       `json:"updated_at"`
}

// CollaborationConfig represents configuration for collaboration
type CollaborationConfig struct {
	EditTimeout               time.Duration `json:"edit_timeout"`
	ConflictDetectionInterval time.Duration `json:"conflict_detection_interval"`
	AutoResolveConflicts      bool          `json:"auto_resolve_conflicts"`
	MaxEditsPerUser           int           `json:"max_edits_per_user"`
	MaxAnnotationsPerElement  int           `json:"max_annotations_per_element"`
	CacheSize                 int           `json:"cache_size"`
	RequireAuthentication     bool          `json:"require_authentication"`
	SessionTimeout            time.Duration `json:"session_timeout"`
	MaxFailedAttempts         int           `json:"max_failed_attempts"`
}

// CollaborationService handles real-time collaboration
type CollaborationService struct {
	db          *gorm.DB
	mu          sync.RWMutex
	sessions    map[string]*UserSession
	edits       map[string]*CollaborativeEdit
	conflicts   map[string]*ConflictResolution
	annotations map[string]*Annotation
	config      *CollaborationConfig
	eventChan   chan *CollaborationEvent
	stopChan    chan struct{}
	isRunning   bool
}

// CollaborationEvent represents a collaboration event
type CollaborationEvent struct {
	Type      CollaborationEventType `json:"type"`
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
	UserID    string                 `json:"user_id"`
	RoomID    string                 `json:"room_id"`
}

// NewCollaborationService creates a new collaboration service
func NewCollaborationService(db *gorm.DB, config *CollaborationConfig) *CollaborationService {
	if config == nil {
		config = &CollaborationConfig{
			EditTimeout:               5 * time.Minute,
			ConflictDetectionInterval: 5 * time.Second,
			AutoResolveConflicts:      false,
			MaxEditsPerUser:           10,
			MaxAnnotationsPerElement:  50,
			CacheSize:                 1000,
			RequireAuthentication:     true,
			SessionTimeout:            1 * time.Hour,
			MaxFailedAttempts:         3,
		}
	}

	return &CollaborationService{
		db:          db,
		sessions:    make(map[string]*UserSession),
		edits:       make(map[string]*CollaborativeEdit),
		conflicts:   make(map[string]*ConflictResolution),
		annotations: make(map[string]*Annotation),
		config:      config,
		eventChan:   make(chan *CollaborationEvent, 1000),
		stopChan:    make(chan struct{}),
	}
}

// Start starts the collaboration service
func (cs *CollaborationService) Start(ctx context.Context) error {
	cs.mu.Lock()
	defer cs.mu.Unlock()

	if cs.isRunning {
		return fmt.Errorf("collaboration service is already running")
	}

	cs.isRunning = true

	// Start event processing loop
	go cs.eventProcessingLoop(ctx)

	// Start conflict detection loop
	go cs.conflictDetectionLoop(ctx)

	// Start cleanup loop
	go cs.cleanupLoop(ctx)

	return nil
}

// Stop stops the collaboration service
func (cs *CollaborationService) Stop() {
	cs.mu.Lock()
	defer cs.mu.Unlock()

	if !cs.isRunning {
		return
	}

	cs.isRunning = false
	close(cs.stopChan)
}

// JoinSession joins a user to a collaboration session
func (cs *CollaborationService) JoinSession(ctx context.Context, userID, username, sessionID, roomID string, permissions PermissionLevel) (*UserSession, error) {
	// Check if user is already in a session
	cs.mu.Lock()
	if existingSession, exists := cs.sessions[userID]; exists {
		// Remove from existing session
		cs.leaveSession(userID)
	}
	cs.mu.Unlock()

	// Create new session
	session := &UserSession{
		ID:             generateSessionID(),
		UserID:         userID,
		Username:       username,
		SessionID:      sessionID,
		RoomID:         roomID,
		Status:         "active",
		Permissions:    permissions,
		JoinedAt:       time.Now(),
		LastActivity:   time.Now(),
		ActiveElements: json.RawMessage("[]"),
		Metadata:       json.RawMessage("{}"),
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}

	if err := cs.db.WithContext(ctx).Create(session).Error; err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}

	cs.mu.Lock()
	cs.sessions[userID] = session
	cs.mu.Unlock()

	// Broadcast user joined event
	cs.broadcastEvent(&CollaborationEvent{
		Type:      CollaborationEventTypeUserJoined,
		Data:      map[string]interface{}{"user_id": userID, "username": username, "room_id": roomID},
		Timestamp: time.Now(),
		UserID:    userID,
		RoomID:    roomID,
	})

	return session, nil
}

// LeaveSession removes a user from a collaboration session
func (cs *CollaborationService) LeaveSession(ctx context.Context, userID string) error {
	cs.mu.Lock()
	session, exists := cs.sessions[userID]
	if !exists {
		cs.mu.Unlock()
		return fmt.Errorf("user not in session")
	}

	roomID := session.RoomID
	cs.leaveSession(userID)
	cs.mu.Unlock()

	// Update database
	cs.db.WithContext(ctx).Model(session).Updates(map[string]interface{}{
		"status":     "inactive",
		"updated_at": time.Now(),
	})

	// Broadcast user left event
	cs.broadcastEvent(&CollaborationEvent{
		Type:      CollaborationEventTypeUserLeft,
		Data:      map[string]interface{}{"user_id": userID, "room_id": roomID},
		Timestamp: time.Now(),
		UserID:    userID,
		RoomID:    roomID,
	})

	return nil
}

// StartEdit starts a collaborative edit
func (cs *CollaborationService) StartEdit(ctx context.Context, userID, elementID, editType string, data map[string]interface{}) (*CollaborativeEdit, error) {
	// Check if user has permission to edit
	if !cs.canEdit(userID, elementID) {
		return nil, fmt.Errorf("user does not have permission to edit")
	}

	// Check if element is already being edited
	if cs.isElementBeingEdited(elementID) {
		return nil, fmt.Errorf("element is already being edited")
	}

	edit := &CollaborativeEdit{
		ID:        generateEditID(),
		UserID:    userID,
		ElementID: elementID,
		EditType:  editType,
		Data:      mustMarshalJSON(data),
		Status:    EditStatusPending,
		Conflicts: json.RawMessage("[]"),
		Metadata:  json.RawMessage("{}"),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if err := cs.db.WithContext(ctx).Create(edit).Error; err != nil {
		return nil, fmt.Errorf("failed to create edit: %w", err)
	}

	cs.mu.Lock()
	cs.edits[edit.ID] = edit
	cs.mu.Unlock()

	// Broadcast edit started event
	cs.broadcastEvent(&CollaborationEvent{
		Type:      CollaborationEventTypeEditStarted,
		Data:      map[string]interface{}{"edit_id": edit.ID, "element_id": elementID, "user_id": userID},
		Timestamp: time.Now(),
		UserID:    userID,
		RoomID:    cs.getUserRoomID(userID),
	})

	return edit, nil
}

// CompleteEdit completes a collaborative edit
func (cs *CollaborationService) CompleteEdit(ctx context.Context, editID string, finalData map[string]interface{}) error {
	cs.mu.Lock()
	edit, exists := cs.edits[editID]
	if !exists {
		cs.mu.Unlock()
		return fmt.Errorf("edit not found")
	}

	edit.Data = mustMarshalJSON(finalData)
	edit.Status = EditStatusApproved
	edit.UpdatedAt = time.Now()
	cs.mu.Unlock()

	// Update database
	cs.db.WithContext(ctx).Save(edit)

	// Broadcast edit completed event
	cs.broadcastEvent(&CollaborationEvent{
		Type:      CollaborationEventTypeEditCompleted,
		Data:      map[string]interface{}{"edit_id": editID, "element_id": edit.ElementID, "user_id": edit.UserID},
		Timestamp: time.Now(),
		UserID:    edit.UserID,
		RoomID:    cs.getUserRoomID(edit.UserID),
	})

	return nil
}

// AddAnnotation adds a collaborative annotation
func (cs *CollaborationService) AddAnnotation(ctx context.Context, userID, elementID, annotationType, content string, position map[string]interface{}) (*Annotation, error) {
	annotation := &Annotation{
		ID:             generateAnnotationID(),
		UserID:         userID,
		ElementID:      elementID,
		AnnotationType: annotationType,
		Content:        content,
		Position:       mustMarshalJSON(position),
		Replies:        json.RawMessage("[]"),
		Metadata:       json.RawMessage("{}"),
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}

	if err := cs.db.WithContext(ctx).Create(annotation).Error; err != nil {
		return nil, fmt.Errorf("failed to create annotation: %w", err)
	}

	cs.mu.Lock()
	cs.annotations[annotation.ID] = annotation
	cs.mu.Unlock()

	// Broadcast annotation added event
	cs.broadcastEvent(&CollaborationEvent{
		Type:      CollaborationEventTypeAnnotationAdded,
		Data:      map[string]interface{}{"annotation_id": annotation.ID, "element_id": elementID, "user_id": userID},
		Timestamp: time.Now(),
		UserID:    userID,
		RoomID:    cs.getUserRoomID(userID),
	})

	return annotation, nil
}

// ResolveConflict resolves a conflict
func (cs *CollaborationService) ResolveConflict(ctx context.Context, conflictID string, resolutionType string, resolvedBy string, resolutionData map[string]interface{}) error {
	cs.mu.Lock()
	conflict, exists := cs.conflicts[conflictID]
	if !exists {
		cs.mu.Unlock()
		return fmt.Errorf("conflict not found")
	}

	now := time.Now()
	conflict.ResolvedAt = &now
	conflict.ResolutionType = resolutionType
	conflict.ResolvedBy = &resolvedBy
	conflict.ResolutionData = mustMarshalJSON(resolutionData)
	conflict.UpdatedAt = now
	cs.mu.Unlock()

	// Update database
	cs.db.WithContext(ctx).Save(conflict)

	// Broadcast conflict resolved event
	cs.broadcastEvent(&CollaborationEvent{
		Type:      CollaborationEventTypeConflictResolved,
		Data:      map[string]interface{}{"conflict_id": conflictID, "resolved_by": resolvedBy},
		Timestamp: time.Now(),
		UserID:    resolvedBy,
		RoomID:    cs.getUserRoomID(resolvedBy),
	})

	return nil
}

// GetSessionUsers gets all users in a session
func (cs *CollaborationService) GetSessionUsers(ctx context.Context, roomID string) ([]UserSession, error) {
	var sessions []UserSession
	if err := cs.db.WithContext(ctx).Where("room_id = ? AND status = ?", roomID, "active").Find(&sessions).Error; err != nil {
		return nil, fmt.Errorf("failed to get session users: %w", err)
	}
	return sessions, nil
}

// GetActiveEdits gets all active edits
func (cs *CollaborationService) GetActiveEdits(ctx context.Context) ([]CollaborativeEdit, error) {
	var edits []CollaborativeEdit
	if err := cs.db.WithContext(ctx).Where("status IN ?", []string{"pending", "conflict"}).Find(&edits).Error; err != nil {
		return nil, fmt.Errorf("failed to get active edits: %w", err)
	}
	return edits, nil
}

// GetElementAnnotations gets annotations for an element
func (cs *CollaborationService) GetElementAnnotations(ctx context.Context, elementID string) ([]Annotation, error) {
	var annotations []Annotation
	if err := cs.db.WithContext(ctx).Where("element_id = ?", elementID).Find(&annotations).Error; err != nil {
		return nil, fmt.Errorf("failed to get element annotations: %w", err)
	}
	return annotations, nil
}

// SetUserPermission sets a user's permission level
func (cs *CollaborationService) SetUserPermission(ctx context.Context, userID string, permission PermissionLevel) error {
	cs.mu.Lock()
	session, exists := cs.sessions[userID]
	if !exists {
		cs.mu.Unlock()
		return fmt.Errorf("user not in session")
	}

	session.Permissions = permission
	session.UpdatedAt = time.Now()
	cs.mu.Unlock()

	// Update database
	cs.db.WithContext(ctx).Save(session)

	// Broadcast permission changed event
	cs.broadcastEvent(&CollaborationEvent{
		Type:      CollaborationEventTypePermissionChanged,
		Data:      map[string]interface{}{"user_id": userID, "permission": permission},
		Timestamp: time.Now(),
		UserID:    userID,
		RoomID:    session.RoomID,
	})

	return nil
}

// leaveSession removes a user from their session
func (cs *CollaborationService) leaveSession(userID string) {
	if session, exists := cs.sessions[userID]; exists {
		delete(cs.sessions, userID)
		// Clean up any active edits by this user
		for editID, edit := range cs.edits {
			if edit.UserID == userID && edit.Status == EditStatusPending {
				delete(cs.edits, editID)
			}
		}
	}
}

// canEdit checks if a user can edit an element
func (cs *CollaborationService) canEdit(userID, elementID string) bool {
	cs.mu.RLock()
	defer cs.mu.RUnlock()

	session, exists := cs.sessions[userID]
	if !exists {
		return false
	}

	return session.Permissions == PermissionLevelEditor ||
		session.Permissions == PermissionLevelAdmin ||
		session.Permissions == PermissionLevelOwner
}

// isElementBeingEdited checks if an element is currently being edited
func (cs *CollaborationService) isElementBeingEdited(elementID string) bool {
	cs.mu.RLock()
	defer cs.mu.RUnlock()

	for _, edit := range cs.edits {
		if edit.ElementID == elementID && edit.Status == EditStatusPending {
			return true
		}
	}
	return false
}

// getUserRoomID gets the room ID for a user
func (cs *CollaborationService) getUserRoomID(userID string) string {
	cs.mu.RLock()
	defer cs.mu.RUnlock()

	if session, exists := cs.sessions[userID]; exists {
		return session.RoomID
	}
	return ""
}

// broadcastEvent broadcasts a collaboration event
func (cs *CollaborationService) broadcastEvent(event *CollaborationEvent) {
	select {
	case cs.eventChan <- event:
	default:
		// Channel is full, drop event
	}
}

// eventProcessingLoop processes collaboration events
func (cs *CollaborationService) eventProcessingLoop(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-cs.stopChan:
			return
		case event := <-cs.eventChan:
			cs.processEvent(event)
		}
	}
}

// processEvent processes a collaboration event
func (cs *CollaborationService) processEvent(event *CollaborationEvent) {
	// In a real implementation, this would send the event to connected clients
	// For now, we just log it
	fmt.Printf("Collaboration event: %s from user %s in room %s\n", event.Type, event.UserID, event.RoomID)
}

// conflictDetectionLoop detects conflicts between edits
func (cs *CollaborationService) conflictDetectionLoop(ctx context.Context) {
	ticker := time.NewTicker(cs.config.ConflictDetectionInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-cs.stopChan:
			return
		case <-ticker.C:
			cs.detectConflicts(ctx)
		}
	}
}

// detectConflicts detects conflicts between pending edits
func (cs *CollaborationService) detectConflicts(ctx context.Context) {
	cs.mu.RLock()
	pendingEdits := make([]*CollaborativeEdit, 0)
	for _, edit := range cs.edits {
		if edit.Status == EditStatusPending {
			pendingEdits = append(pendingEdits, edit)
		}
	}
	cs.mu.RUnlock()

	// Check for conflicts between edits on the same element
	elementEdits := make(map[string][]*CollaborativeEdit)
	for _, edit := range pendingEdits {
		elementEdits[edit.ElementID] = append(elementEdits[edit.ElementID], edit)
	}

	for elementID, edits := range elementEdits {
		if len(edits) > 1 {
			// Conflict detected
			conflict := &ConflictResolution{
				ID:             generateConflictID(),
				ConflictID:     generateConflictID(),
				EditIDs:        mustMarshalJSON([]string{edits[0].ID, edits[1].ID}),
				DetectedAt:     time.Now(),
				ResolutionType: "manual",
				ResolutionData: json.RawMessage("{}"),
				CreatedAt:      time.Now(),
				UpdatedAt:      time.Now(),
			}

			cs.db.WithContext(ctx).Create(conflict)

			cs.mu.Lock()
			cs.conflicts[conflict.ID] = conflict
			// Mark edits as conflicting
			for _, edit := range edits {
				edit.Status = EditStatusConflict
				edit.Conflicts = mustMarshalJSON([]string{conflict.ID})
				cs.db.WithContext(ctx).Save(edit)
			}
			cs.mu.Unlock()

			// Broadcast conflict detected event
			cs.broadcastEvent(&CollaborationEvent{
				Type:      CollaborationEventTypeConflictDetected,
				Data:      map[string]interface{}{"conflict_id": conflict.ID, "element_id": elementID},
				Timestamp: time.Now(),
				UserID:    "",
				RoomID:    cs.getUserRoomID(edits[0].UserID),
			})
		}
	}
}

// cleanupLoop cleans up expired sessions and edits
func (cs *CollaborationService) cleanupLoop(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-cs.stopChan:
			return
		case <-ticker.C:
			cs.cleanupExpired(ctx)
		}
	}
}

// cleanupExpired cleans up expired sessions and edits
func (cs *CollaborationService) cleanupExpired(ctx context.Context) {
	expiredTime := time.Now().Add(-cs.config.SessionTimeout)

	// Clean up expired sessions
	var expiredSessions []UserSession
	cs.db.WithContext(ctx).Where("last_activity < ? AND status = ?", expiredTime, "active").Find(&expiredSessions)

	for _, session := range expiredSessions {
		cs.LeaveSession(ctx, session.UserID)
	}

	// Clean up expired edits
	editExpiredTime := time.Now().Add(-cs.config.EditTimeout)
	var expiredEdits []CollaborativeEdit
	cs.db.WithContext(ctx).Where("created_at < ? AND status = ?", editExpiredTime, EditStatusPending).Find(&expiredEdits)

	for _, edit := range expiredEdits {
		cs.mu.Lock()
		delete(cs.edits, edit.ID)
		cs.mu.Unlock()

		cs.db.WithContext(ctx).Model(&edit).Update("status", EditStatusRejected)
	}
}

// GetCollaborationStats gets collaboration statistics
func (cs *CollaborationService) GetCollaborationStats() map[string]interface{} {
	cs.mu.RLock()
	defer cs.mu.RUnlock()

	var totalSessions, activeSessions int64
	var totalEdits, pendingEdits, conflictEdits int64
	var totalAnnotations int64

	cs.db.Model(&UserSession{}).Count(&totalSessions)
	cs.db.Model(&UserSession{}).Where("status = ?", "active").Count(&activeSessions)
	cs.db.Model(&CollaborativeEdit{}).Count(&totalEdits)
	cs.db.Model(&CollaborativeEdit{}).Where("status = ?", EditStatusPending).Count(&pendingEdits)
	cs.db.Model(&CollaborativeEdit{}).Where("status = ?", EditStatusConflict).Count(&conflictEdits)
	cs.db.Model(&Annotation{}).Count(&totalAnnotations)

	return map[string]interface{}{
		"total_sessions":      totalSessions,
		"active_sessions":     activeSessions,
		"total_edits":         totalEdits,
		"pending_edits":       pendingEdits,
		"conflict_edits":      conflictEdits,
		"total_annotations":   totalAnnotations,
		"current_sessions":    len(cs.sessions),
		"current_edits":       len(cs.edits),
		"current_conflicts":   len(cs.conflicts),
		"current_annotations": len(cs.annotations),
		"is_running":          cs.isRunning,
	}
}

// Helper functions
func generateSessionID() string {
	return fmt.Sprintf("session_%d", time.Now().UnixNano())
}

func generateEditID() string {
	return fmt.Sprintf("edit_%d", time.Now().UnixNano())
}

func generateAnnotationID() string {
	return fmt.Sprintf("annotation_%d", time.Now().UnixNano())
}

func generateConflictID() string {
	return fmt.Sprintf("conflict_%d", time.Now().UnixNano())
}

func mustMarshalJSON(v interface{}) json.RawMessage {
	data, _ := json.Marshal(v)
	return data
}
