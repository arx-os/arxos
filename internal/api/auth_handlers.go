package api

import (
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// handleLogin handles user login
func (s *Server) handleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	if s.services.Auth == nil {
		s.respondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}
	
	response, err := s.services.Auth.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Invalid credentials")
		return
	}
	
	s.respondJSON(w, http.StatusOK, response)
}

// handleLogout handles user logout
func (s *Server) handleLogout(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	// Extract token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		s.respondError(w, http.StatusUnauthorized, "Authorization header required")
		return
	}
	
	// Parse Bearer token
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || parts[0] != "Bearer" {
		s.respondError(w, http.StatusUnauthorized, "Invalid authorization header format")
		return
	}
	
	token := parts[1]
	if token == "" {
		s.respondError(w, http.StatusUnauthorized, "Token required")
		return
	}
	
	if s.services.Auth == nil {
		s.respondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}
	
	// Revoke the token (delete session)
	if err := s.services.Auth.RevokeToken(r.Context(), token); err != nil {
		logger.Error("Failed to revoke token: %v", err)
		// Don't expose internal errors, just return success
		// Token might already be invalid
	}
	
	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Logged out successfully",
	})
}

// handleRefresh handles token refresh
func (s *Server) handleRefresh(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	var req struct {
		RefreshToken string `json:"refresh_token"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	if req.RefreshToken == "" {
		s.respondError(w, http.StatusBadRequest, "Refresh token is required")
		return
	}
	
	if s.services.Auth == nil {
		s.respondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}
	
	// Refresh the token
	response, err := s.services.Auth.RefreshToken(r.Context(), req.RefreshToken)
	if err != nil {
		logger.Error("Token refresh failed: %v", err)
		s.respondError(w, http.StatusUnauthorized, "Invalid or expired refresh token")
		return
	}
	
	s.respondJSON(w, http.StatusOK, response)
}

// handleRegister handles user registration
func (s *Server) handleRegister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
		Name     string `json:"name"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	if s.services.Auth == nil {
		s.respondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}
	
	user, err := s.services.Auth.Register(r.Context(), req.Email, req.Password, req.Name)
	if err != nil {
		s.respondError(w, http.StatusBadRequest, "Registration failed")
		return
	}
	
	s.respondJSON(w, http.StatusCreated, user)
}

// handleGetCurrentUser returns the current user
func (s *Server) handleGetCurrentUser(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	userID := r.Context().Value(ContextKeyUserID)
	if userID == nil {
		s.respondError(w, http.StatusUnauthorized, "User not authenticated")
		return
	}
	
	// TODO: Implement get current user
	s.respondJSON(w, http.StatusOK, map[string]string{"user_id": userID.(string)})
}

// handleGetUser returns a user by ID
func (s *Server) handleGetUser(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	// Extract user ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		s.respondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}
	userID := parts[4]
	
	// TODO: Implement get user
	s.respondJSON(w, http.StatusOK, map[string]string{"user_id": userID})
}

// handleListUsers lists all users
func (s *Server) handleListUsers(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	// TODO: Implement list users
	s.respondJSON(w, http.StatusOK, []interface{}{})
}

// handleListBuildings lists all buildings
func (s *Server) handleListBuildings(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	// Get user ID from context
	userID := ""
	if uid := r.Context().Value(ContextKeyUserID); uid != nil {
		userID = uid.(string)
	}
	
	// Parse query parameters
	limit := 100
	offset := 0
	// TODO: Parse limit and offset from query params
	
	buildings, err := s.services.Building.ListBuildings(r.Context(), userID, limit, offset)
	if err != nil {
		logger.Error("Failed to list buildings: %v", err)
		s.respondError(w, http.StatusInternalServerError, "Failed to list buildings")
		return
	}
	
	s.respondJSON(w, http.StatusOK, buildings)
}

// handleCreateBuilding creates a new building
func (s *Server) handleCreateBuilding(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	var building models.FloorPlan
	if err := json.NewDecoder(r.Body).Decode(&building); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	if err := s.services.Building.CreateBuilding(r.Context(), &building); err != nil {
		logger.Error("Failed to create building: %v", err)
		s.respondError(w, http.StatusInternalServerError, "Failed to create building")
		return
	}
	
	s.respondJSON(w, http.StatusCreated, building)
}

// handleGetBuilding returns a building by ID
func (s *Server) handleGetBuilding(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	// Extract building ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		s.respondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}
	buildingID := parts[4]
	
	building, err := s.services.Building.GetBuilding(r.Context(), buildingID)
	if err != nil {
		logger.Error("Failed to get building: %v", err)
		s.respondError(w, http.StatusNotFound, "Building not found")
		return
	}
	
	s.respondJSON(w, http.StatusOK, building)
}

// handleUpdateBuilding updates a building
func (s *Server) handleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPut && r.Method != http.MethodPatch {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	// Extract building ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		s.respondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}
	buildingID := parts[4]
	
	var building models.FloorPlan
	if err := json.NewDecoder(r.Body).Decode(&building); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	// Ensure ID matches
	if building.Name == "" {
		building.Name = buildingID
	}
	
	if err := s.services.Building.UpdateBuilding(r.Context(), &building); err != nil {
		logger.Error("Failed to update building: %v", err)
		s.respondError(w, http.StatusInternalServerError, "Failed to update building")
		return
	}
	
	s.respondJSON(w, http.StatusOK, building)
}

// handleDeleteBuilding deletes a building
func (s *Server) handleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodDelete {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	// Extract building ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		s.respondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}
	buildingID := parts[4]
	
	if err := s.services.Building.DeleteBuilding(r.Context(), buildingID); err != nil {
		logger.Error("Failed to delete building: %v", err)
		s.respondError(w, http.StatusInternalServerError, "Failed to delete building")
		return
	}
	
	s.respondJSON(w, http.StatusNoContent, nil)
}

// handleListEquipment lists equipment for a building
func (s *Server) handleListEquipment(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	// Extract building ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		s.respondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}
	buildingID := parts[4]
	
	// Parse filters from query params
	filters := make(map[string]interface{})
	if typeFilter := r.URL.Query().Get("type"); typeFilter != "" {
		filters["type"] = typeFilter
	}
	if statusFilter := r.URL.Query().Get("status"); statusFilter != "" {
		filters["status"] = statusFilter
	}
	if roomFilter := r.URL.Query().Get("room_id"); roomFilter != "" {
		filters["room_id"] = roomFilter
	}
	
	equipment, err := s.services.Building.ListEquipment(r.Context(), buildingID, filters)
	if err != nil {
		logger.Error("Failed to list equipment: %v", err)
		s.respondError(w, http.StatusInternalServerError, "Failed to list equipment")
		return
	}
	
	s.respondJSON(w, http.StatusOK, equipment)
}

// handleCreateEquipment creates new equipment
func (s *Server) handleCreateEquipment(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	var equipment models.Equipment
	if err := json.NewDecoder(r.Body).Decode(&equipment); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	if err := s.services.Building.CreateEquipment(r.Context(), &equipment); err != nil {
		logger.Error("Failed to create equipment: %v", err)
		s.respondError(w, http.StatusInternalServerError, "Failed to create equipment")
		return
	}
	
	s.respondJSON(w, http.StatusCreated, equipment)
}

// handleGetEquipment returns equipment by ID
func (s *Server) handleGetEquipment(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	// Extract equipment ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		s.respondError(w, http.StatusBadRequest, "Invalid equipment ID")
		return
	}
	equipmentID := parts[4]
	
	equipment, err := s.services.Building.GetEquipment(r.Context(), equipmentID)
	if err != nil {
		logger.Error("Failed to get equipment: %v", err)
		s.respondError(w, http.StatusNotFound, "Equipment not found")
		return
	}
	
	s.respondJSON(w, http.StatusOK, equipment)
}

// handleUpdateEquipment updates equipment
func (s *Server) handleUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPut && r.Method != http.MethodPatch {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	if s.services.Building == nil {
		s.respondError(w, http.StatusNotImplemented, "Building service not configured")
		return
	}
	
	// Extract equipment ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		s.respondError(w, http.StatusBadRequest, "Invalid equipment ID")
		return
	}
	equipmentID := parts[4]
	
	var equipment models.Equipment
	if err := json.NewDecoder(r.Body).Decode(&equipment); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	// Ensure ID matches
	equipment.ID = equipmentID
	
	if err := s.services.Building.UpdateEquipment(r.Context(), &equipment); err != nil {
		logger.Error("Failed to update equipment: %v", err)
		s.respondError(w, http.StatusInternalServerError, "Failed to update equipment")
		return
	}
	
	s.respondJSON(w, http.StatusOK, equipment)
}

// Sync handlers

// handleSyncPush handles sync push from CLI
func (s *Server) handleSyncPush(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	var syncReq SyncRequest
	if err := json.NewDecoder(r.Body).Decode(&syncReq); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	// TODO: Implement sync push logic
	logger.Info("Received sync push for building %s with %d changes", syncReq.BuildingID, len(syncReq.Changes))
	
	response := SyncResponse{
		BuildingID: syncReq.BuildingID,
		Changes:    []Change{},
		Conflicts:  []Conflict{},
		LastSync:   time.Now(),
	}
	
	s.respondJSON(w, http.StatusOK, response)
}

// handleSyncPull handles sync pull from CLI
func (s *Server) handleSyncPull(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	var syncReq SyncRequest
	if err := json.NewDecoder(r.Body).Decode(&syncReq); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	// TODO: Implement sync pull logic
	logger.Info("Received sync pull for building %s since %v", syncReq.BuildingID, syncReq.LastSync)
	
	response := SyncResponse{
		BuildingID: syncReq.BuildingID,
		Changes:    []Change{},
		Conflicts:  []Conflict{},
		LastSync:   time.Now(),
	}
	
	s.respondJSON(w, http.StatusOK, response)
}

// handleSyncStatus returns sync status
func (s *Server) handleSyncStatus(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	buildingID := r.URL.Query().Get("building_id")
	if buildingID == "" {
		s.respondError(w, http.StatusBadRequest, "Missing building_id parameter")
		return
	}
	
	// TODO: Implement sync status logic
	status := map[string]interface{}{
		"building_id": buildingID,
		"last_sync":   time.Now().Add(-1 * time.Hour),
		"pending":     0,
		"conflicts":   0,
		"status":      "synced",
	}
	
	s.respondJSON(w, http.StatusOK, status)
}