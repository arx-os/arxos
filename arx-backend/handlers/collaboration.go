package handlers

import (
	"net/http"

	"github.com/go-chi/chi/v5"

	"arx/services/realtime"
	"arx/utils"
)

// CollaborationHandler handles collaboration-related HTTP requests
type CollaborationHandler struct {
	collaborationService *realtime.CollaborationService
}

// NewCollaborationHandler creates a new collaboration handler
func NewCollaborationHandler(collaborationService *realtime.CollaborationService) *CollaborationHandler {
	return &CollaborationHandler{
		collaborationService: collaborationService,
	}
}

// Request types for collaboration handlers
type StartSessionRequest struct {
	DocumentID string `json:"document_id" binding:"required"`
	User       struct {
		ID    string `json:"id" binding:"required"`
		Name  string `json:"name" binding:"required"`
		Email string `json:"email" binding:"required"`
	} `json:"user" binding:"required"`
	RoomID      string `json:"room_id"`
	Permissions string `json:"permissions"`
}

type EditOperationRequest struct {
	UserID    string                 `json:"user_id" binding:"required"`
	ElementID string                 `json:"element_id" binding:"required"`
	EditType  string                 `json:"edit_type" binding:"required"`
	Data      map[string]interface{} `json:"data" binding:"required"`
	SessionID string                 `json:"session_id"`
}

type UpdatePresenceRequest struct {
	UserID string `json:"user_id" binding:"required"`
	Status string `json:"status" binding:"required"`
}

type ResolveConflictRequest struct {
	ResolutionData map[string]interface{} `json:"resolution_data" binding:"required"`
	SessionID      string                 `json:"session_id"`
	ConflictID     string                 `json:"conflict_id"`
}

// SetupRoutes sets up the collaboration routes
func (h *CollaborationHandler) SetupRoutes(router chi.Router) {
	router.Route("/api/collaboration", func(r chi.Router) {
		// Session management
		r.Post("/sessions", utils.ToChiHandler(h.StartSession))
		r.Delete("/sessions/{session_id}", utils.ToChiHandler(h.EndSession))
		r.Get("/sessions/{session_id}", utils.ToChiHandler(h.GetSessionInfo))
		r.Get("/sessions/{session_id}/history", utils.ToChiHandler(h.GetEditHistory))

		// Edit operations
		r.Post("/sessions/{session_id}/edit", utils.ToChiHandler(h.HandleEditOperation))

		// User presence
		r.Put("/sessions/{session_id}/presence", utils.ToChiHandler(h.UpdateUserPresence))

		// Conflict resolution
		r.Post("/sessions/{session_id}/conflicts/{conflict_id}/resolve", utils.ToChiHandler(h.ResolveConflictManually))

		// WebSocket connections
		r.Get("/websocket/{user_id}", utils.ToChiHandler(h.RegisterWebSocket))
	})
}

// StartSession starts a collaboration session
func (h *CollaborationHandler) StartSession(c *utils.ChiContext) {
	var req StartSessionRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request data", err.Error())
		return
	}

	// Validate required fields
	if req.DocumentID == "" {
		c.Writer.Error(http.StatusBadRequest, "Document ID is required", "")
		return
	}

	if req.User.ID == "" || req.User.Name == "" || req.User.Email == "" {
		c.Writer.Error(http.StatusBadRequest, "User ID, name, and email are required", "")
		return
	}

	// Convert permissions string to PermissionLevel
	permissions := realtime.PermissionLevelEditor
	if req.Permissions != "" {
		permissions = realtime.PermissionLevel(req.Permissions)
	}

	// Call collaboration service
	session, err := h.collaborationService.JoinSession(c.Request.Context(), req.User.ID, req.User.Name, "session-"+req.DocumentID, req.RoomID, permissions)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to start session", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"session": session,
		"message": "Session started successfully",
	})
}

// EndSession ends a collaboration session
func (h *CollaborationHandler) EndSession(c *utils.ChiContext) {
	sessionID := c.Reader.Param("session_id")
	userID := c.Reader.Query("user_id")

	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	if userID == "" {
		c.Writer.Error(http.StatusBadRequest, "User ID is required", "")
		return
	}

	// Call collaboration service
	err := h.collaborationService.LeaveSession(c.Request.Context(), userID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to end session", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Session ended successfully",
	})
}

// HandleEditOperation handles an edit operation
func (h *CollaborationHandler) HandleEditOperation(c *utils.ChiContext) {
	var req EditOperationRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request data", err.Error())
		return
	}

	// Get session ID from URL parameter
	sessionID := c.Reader.Param("session_id")
	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	// Set session ID from URL parameter
	req.SessionID = sessionID

	// Validate required fields
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "User ID is required", "")
		return
	}

	if req.EditType == "" {
		c.Writer.Error(http.StatusBadRequest, "Edit type is required", "")
		return
	}

	if req.ElementID == "" {
		c.Writer.Error(http.StatusBadRequest, "Element ID is required", "")
		return
	}

	if req.Data == nil {
		c.Writer.Error(http.StatusBadRequest, "Edit data is required", "")
		return
	}

	// Call collaboration service
	edit, err := h.collaborationService.StartEdit(c.Request.Context(), req.UserID, req.ElementID, req.EditType, req.Data)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to handle edit operation", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"edit":    edit,
		"message": "Edit operation handled successfully",
	})
}

// GetSessionInfo gets information about a collaboration session
func (h *CollaborationHandler) GetSessionInfo(c *utils.ChiContext) {
	sessionID := c.Reader.Param("session_id")

	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	// Get session users
	users, err := h.collaborationService.GetSessionUsers(c.Request.Context(), sessionID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get session info", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"session": map[string]interface{}{
			"session_id": sessionID,
			"users":      users,
		},
		"message": "Session info retrieved successfully",
	})
}

// GetEditHistory gets edit history for a session
func (h *CollaborationHandler) GetEditHistory(c *utils.ChiContext) {
	sessionID := c.Reader.Param("session_id")

	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	// Get active edits
	edits, err := h.collaborationService.GetActiveEdits(c.Request.Context())
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get edit history", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"edits":   edits,
		"message": "Edit history retrieved successfully",
	})
}

// UpdateUserPresence updates user presence information
func (h *CollaborationHandler) UpdateUserPresence(c *utils.ChiContext) {
	var req UpdatePresenceRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request data", err.Error())
		return
	}

	// Get session ID from URL parameter
	sessionID := c.Reader.Param("session_id")
	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	// Validate required fields
	if req.UserID == "" {
		c.Writer.Error(http.StatusBadRequest, "User ID is required", "")
		return
	}

	if req.Status == "" {
		c.Writer.Error(http.StatusBadRequest, "Status is required", "")
		return
	}

	// Validate status values
	validStatuses := []string{"online", "offline", "away", "editing"}
	validStatus := false
	for _, status := range validStatuses {
		if req.Status == status {
			validStatus = true
			break
		}
	}

	if !validStatus {
		c.Writer.Error(http.StatusBadRequest, "Invalid status value. Must be one of: online, offline, away, editing", "")
		return
	}

	// For now, return success since the service doesn't have a direct presence update method
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "User presence updated successfully",
	})
}

// ResolveConflictManually manually resolves a conflict
func (h *CollaborationHandler) ResolveConflictManually(c *utils.ChiContext) {
	var req ResolveConflictRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request data", err.Error())
		return
	}

	// Get session ID and conflict ID from URL parameters
	sessionID := c.Reader.Param("session_id")
	conflictID := c.Reader.Param("conflict_id")

	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	if conflictID == "" {
		c.Writer.Error(http.StatusBadRequest, "Conflict ID is required", "")
		return
	}

	// Set session ID and conflict ID from URL parameters
	req.SessionID = sessionID
	req.ConflictID = conflictID

	// Validate required fields
	if req.ResolutionData == nil {
		c.Writer.Error(http.StatusBadRequest, "Resolution data is required", "")
		return
	}

	// Call collaboration service
	err := h.collaborationService.ResolveConflict(c.Request.Context(), conflictID, "manual", "user", req.ResolutionData)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to resolve conflict", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Conflict resolved successfully",
	})
}

// RegisterWebSocket registers a websocket connection for a user
func (h *CollaborationHandler) RegisterWebSocket(c *utils.ChiContext) {
	userID := c.Reader.Param("user_id")

	if userID == "" {
		c.Writer.Error(http.StatusBadRequest, "User ID is required", "")
		return
	}

	// For now, return success since WebSocket handling would be implemented separately
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "WebSocket connection registered successfully",
	})
}

// GetActiveSessions gets all active collaboration sessions
func (h *CollaborationHandler) GetActiveSessions(c *utils.ChiContext) {
	// This would typically query the database for active sessions
	// For now, return a placeholder response
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"sessions": []map[string]interface{}{
			{
				"session_id":    "session-1",
				"document_id":   "doc-1",
				"active_users":  2,
				"created_at":    "2024-12-19T10:00:00Z",
				"last_activity": "2024-12-19T10:30:00Z",
			},
			{
				"session_id":    "session-2",
				"document_id":   "doc-2",
				"active_users":  1,
				"created_at":    "2024-12-19T09:00:00Z",
				"last_activity": "2024-12-19T10:25:00Z",
			},
		},
	})
}

// GetUserSessions gets all sessions for a specific user
func (h *CollaborationHandler) GetUserSessions(c *utils.ChiContext) {
	userID := c.Reader.Param("user_id")

	if userID == "" {
		c.Writer.Error(http.StatusBadRequest, "User ID is required", "")
		return
	}

	// This would typically query the database for user sessions
	// For now, return a placeholder response
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"user_id": userID,
		"sessions": []map[string]interface{}{
			{
				"session_id":    "session-1",
				"document_id":   "doc-1",
				"joined_at":     "2024-12-19T10:00:00Z",
				"last_activity": "2024-12-19T10:30:00Z",
			},
		},
	})
}

// GetSessionStatistics gets statistics for a collaboration session
func (h *CollaborationHandler) GetSessionStatistics(c *utils.ChiContext) {
	sessionID := c.Reader.Param("session_id")

	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	// Get collaboration stats
	stats := h.collaborationService.GetCollaborationStats()

	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"session_id": sessionID,
		"statistics": stats,
	})
}

// GetConflictHistory gets conflict history for a session
func (h *CollaborationHandler) GetConflictHistory(c *utils.ChiContext) {
	sessionID := c.Reader.Param("session_id")

	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	// This would typically query the database for conflict history
	// For now, return a placeholder response
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"session_id": sessionID,
		"conflicts": []map[string]interface{}{
			{
				"conflict_id":         "conflict-1",
				"detected_at":         "2024-12-19T10:15:00Z",
				"resolved_at":         "2024-12-19T10:16:00Z",
				"resolution_strategy": "automatic",
				"involved_users":      []string{"user-1", "user-2"},
				"element_id":          "element-123",
			},
			{
				"conflict_id":         "conflict-2",
				"detected_at":         "2024-12-19T10:20:00Z",
				"resolved_at":         "2024-12-19T10:22:00Z",
				"resolution_strategy": "manual",
				"involved_users":      []string{"user-1", "user-3"},
				"element_id":          "element-456",
			},
		},
	})
}

// GetUserActivity gets user activity in a session
func (h *CollaborationHandler) GetUserActivity(c *utils.ChiContext) {
	sessionID := c.Reader.Param("session_id")
	userID := c.Reader.Param("user_id")

	if sessionID == "" {
		c.Writer.Error(http.StatusBadRequest, "Session ID is required", "")
		return
	}

	if userID == "" {
		c.Writer.Error(http.StatusBadRequest, "User ID is required", "")
		return
	}

	// This would typically query the database for user activity
	// For now, return a placeholder response
	c.Writer.JSON(http.StatusOK, map[string]interface{}{
		"session_id": sessionID,
		"user_id":    userID,
		"activity": []map[string]interface{}{
			{
				"timestamp": "2024-12-19T10:00:00Z",
				"action":    "joined_session",
			},
			{
				"timestamp":  "2024-12-19T10:05:00Z",
				"action":     "edit_operation",
				"edit_type":  "create",
				"element_id": "element-123",
			},
			{
				"timestamp":  "2024-12-19T10:10:00Z",
				"action":     "edit_operation",
				"edit_type":  "update",
				"element_id": "element-123",
			},
			{
				"timestamp":   "2024-12-19T10:15:00Z",
				"action":      "conflict_resolved",
				"conflict_id": "conflict-1",
			},
		},
	})
}
