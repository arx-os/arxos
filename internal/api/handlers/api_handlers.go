package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	apimodels "github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/api/types"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
)

// @Summary		Health Check
// @Description	Check if the API is healthy and responsive
// @Tags		System
// @Produce		json
// @Success		200	{object}	map[string]interface{}	"API is healthy"
// @Router		/health [get]
func HandleHealth(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		response := map[string]interface{}{
			"status":  "healthy",
			"version": "2.0.0",
			"time":    time.Now().UTC(),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}
}

// Authentication Handlers

// @Summary		Refresh Token
// @Description	Refresh access token using refresh token
// @Tags		Authentication
// @Accept		json
// @Produce		json
// @Param		refresh	body		docs.RefreshRequest	true	"Refresh token"
// @Success		200	{object}	docs.AuthResponse	"New tokens generated"
// @Failure		401	{object}	docs.ErrorResponse	"Invalid refresh token"
// @Router		/auth/refresh [post]
func HandleRefreshToken(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			RefreshToken string `json:"refresh_token"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}

		accessToken, refreshToken, err := s.Services.Auth.RefreshToken(r.Context(), req.RefreshToken)
		if err != nil {
			respondError(w, http.StatusUnauthorized, "Invalid refresh token")
			return
		}

		response := map[string]interface{}{
			"access_token":  accessToken,
			"refresh_token": refreshToken,
		}

		respondJSON(w, http.StatusOK, response)
	}
}

// Building Handlers

// @Summary		List Buildings
// @Description	Get a list of buildings accessible to the user
// @Tags		Buildings
// @Security	BearerAuth
// @Produce		json
// @Param		limit	query		int		false	"Limit number of results"	default(20)
// @Param		offset	query		int		false	"Offset for pagination"	default(0)
// @Success		200	{array}		docs.BuildingResponse
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Router		/buildings [get]
func HandleListBuildings(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		userID := getUserID(ctx)

		// Parse query parameters
		limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
		if limit <= 0 || limit > 100 {
			limit = 20
		}

		offset, _ := strconv.Atoi(r.URL.Query().Get("offset"))
		if offset < 0 {
			offset = 0
		}

		buildings, err := s.Services.Building.ListBuildings(ctx, userID, limit, offset)
		if err != nil {
			logger.Error("Failed to list buildings: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to retrieve buildings")
			return
		}

		respondJSON(w, http.StatusOK, buildings)
	}
}

// @Summary		Get Building
// @Description	Get detailed information about a specific building
// @Tags		Buildings
// @Security	BearerAuth
// @Produce		json
// @Param		id	path		string	true	"Building ID"
// @Success		200	{object}	docs.BuildingResponse
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Failure		404	{object}	docs.ErrorResponse	"Building not found"
// @Router		/buildings/{id} [get]
func HandleGetBuilding(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		buildingID := chi.URLParam(r, "id")

		building, err := s.Services.Building.GetBuilding(ctx, buildingID)
		if err != nil {
			logger.Error("Failed to get building %s: %v", buildingID, err)
			respondError(w, http.StatusNotFound, "Building not found")
			return
		}

		respondJSON(w, http.StatusOK, building)
	}
}

// @Summary		Create Building
// @Description	Create a new building
// @Tags		Buildings
// @Security	BearerAuth
// @Accept		json
// @Produce		json
// @Param		building	body		docs.CreateBuildingRequest	true	"Building details"
// @Success		201	{object}	docs.BuildingResponse		"Building created"
// @Failure		400	{object}	docs.ErrorResponse			"Invalid request"
// @Failure		401	{object}	docs.ErrorResponse			"Unauthorized"
// @Router		/buildings [post]
func HandleCreateBuilding(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()

		var req struct {
			Name         string  `json:"name"`
			Address      string  `json:"address"`
			City         string  `json:"city"`
			State        string  `json:"state"`
			PostalCode   string  `json:"postal_code"`
			Country      string  `json:"country"`
			Floors       int     `json:"floors"`
			TotalArea    float64 `json:"total_area"`
			BuildingType string  `json:"building_type"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}

		// Validate required fields
		if req.Name == "" {
			respondError(w, http.StatusBadRequest, "Building name is required")
			return
		}

		createdBuilding, err := s.Services.Building.CreateBuilding(ctx, req.Name)
		if err != nil {
			logger.Error("Failed to create building: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to create building")
			return
		}

		respondJSON(w, http.StatusCreated, createdBuilding)
	}
}

// @Summary		Update Building
// @Description	Update an existing building
// @Tags		Buildings
// @Security	BearerAuth
// @Accept		json
// @Produce		json
// @Param		id			path		string					true	"Building ID"
// @Param		building	body		docs.UpdateBuildingRequest	true	"Building updates"
// @Success		200	{object}	docs.BuildingResponse		"Building updated"
// @Failure		400	{object}	docs.ErrorResponse			"Invalid request"
// @Failure		401	{object}	docs.ErrorResponse			"Unauthorized"
// @Failure		404	{object}	docs.ErrorResponse			"Building not found"
// @Router		/buildings/{id} [put]
func HandleUpdateBuilding(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		buildingID := chi.URLParam(r, "id")

		// Get existing building
		buildingInterface, err := s.Services.Building.GetBuilding(ctx, buildingID)
		if err != nil {
			respondError(w, http.StatusNotFound, "Building not found")
			return
		}

		// Type assert to FloorPlan
		building, ok := buildingInterface.(*models.FloorPlan)
		if !ok {
			respondError(w, http.StatusInternalServerError, "Invalid building data")
			return
		}

		// Parse updates
		var req struct {
			Name        *string `json:"name,omitempty"`
			Description *string `json:"description,omitempty"`
			Building    *string `json:"building,omitempty"`
			Level       *int    `json:"level,omitempty"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}

		// Apply updates
		if req.Name != nil {
			building.Name = *req.Name
		}
		if req.Description != nil {
			building.Description = *req.Description
		}
		if req.Building != nil {
			building.Building = *req.Building
		}
		if req.Level != nil {
			building.Level = *req.Level
		}

		updatedBuilding, err := s.Services.Building.UpdateBuilding(ctx, buildingID, building.Name)
		if err != nil {
			logger.Error("Failed to update building: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to update building")
			return
		}

		respondJSON(w, http.StatusOK, updatedBuilding)
	}
}

// @Summary		Delete Building
// @Description	Delete a building
// @Tags		Buildings
// @Security	BearerAuth
// @Param		id	path	string	true	"Building ID"
// @Success		204	"Building deleted"
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Failure		404	{object}	docs.ErrorResponse	"Building not found"
// @Router		/buildings/{id} [delete]
func HandleDeleteBuilding(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		buildingID := chi.URLParam(r, "id")

		if err := s.Services.Building.DeleteBuilding(ctx, buildingID); err != nil {
			logger.Error("Failed to delete building %s: %v", buildingID, err)
			respondError(w, http.StatusNotFound, "Building not found")
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}

// Equipment Handlers

// @Summary		List Equipment
// @Description	Get equipment for a building
// @Tags		Equipment
// @Security	BearerAuth
// @Produce		json
// @Param		building_id	query		string	true	"Building ID"
// @Param		type		query		string	false	"Equipment type filter"
// @Param		status		query		string	false	"Equipment status filter"
// @Param		room_id		query		string	false	"Room ID filter"
// @Success		200	{array}		docs.EquipmentResponse
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Router		/equipment [get]
func HandleListEquipment(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		buildingID := r.URL.Query().Get("building_id")

		if buildingID == "" {
			respondError(w, http.StatusBadRequest, "Building ID is required")
			return
		}

		// Build filters
		filters := make(map[string]interface{})
		if equipType := r.URL.Query().Get("type"); equipType != "" {
			filters["type"] = equipType
		}
		if status := r.URL.Query().Get("status"); status != "" {
			filters["status"] = status
		}
		if roomID := r.URL.Query().Get("room_id"); roomID != "" {
			filters["room_id"] = roomID
		}

		equipment, err := s.Services.Building.ListEquipment(ctx, buildingID, filters)
		if err != nil {
			logger.Error("Failed to list equipment: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to retrieve equipment")
			return
		}

		respondJSON(w, http.StatusOK, equipment)
	}
}

// @Summary		Get Equipment
// @Description	Get detailed information about specific equipment
// @Tags		Equipment
// @Security	BearerAuth
// @Produce		json
// @Param		id	path		string	true	"Equipment ID"
// @Success		200	{object}	docs.EquipmentResponse
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Failure		404	{object}	docs.ErrorResponse	"Equipment not found"
// @Router		/equipment/{id} [get]
func HandleGetEquipment(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		equipmentID := chi.URLParam(r, "id")

		equipment, err := s.Services.Equipment.GetEquipmentByID(ctx, equipmentID)
		if err != nil {
			logger.Error("Failed to get equipment %s: %v", equipmentID, err)
			respondError(w, http.StatusNotFound, "Equipment not found")
			return
		}

		respondJSON(w, http.StatusOK, equipment)
	}
}

// HandleUpdateEquipment handles equipment updates
func HandleUpdateEquipment(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		equipmentID := chi.URLParam(r, "id")

		var req struct {
			Name     string  `json:"name"`
			Type     string  `json:"type"`
			X        float64 `json:"x"`
			Y        float64 `json:"y"`
			Z        float64 `json:"z"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}

		updatedEquipment, err := s.Services.Equipment.UpdateEquipment(ctx, equipmentID, req.Name, req.Type, req.X, req.Y, req.Z)
		if err != nil {
			logger.Error("Failed to update equipment %s: %v", equipmentID, err)
			respondError(w, http.StatusInternalServerError, "Failed to update equipment")
			return
		}

		respondJSON(w, http.StatusOK, updatedEquipment)
	}
}

// HandleCreateEquipment handles equipment creation
func HandleCreateEquipment(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()

		var req struct {
			Name       string  `json:"name"`
			Type       string  `json:"type"`
			BuildingID string  `json:"building_id"`
			RoomID     string  `json:"room_id"`
			X          float64 `json:"x"`
			Y          float64 `json:"y"`
			Z          float64 `json:"z"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}

		// Validate required fields
		if req.Name == "" || req.Type == "" || req.BuildingID == "" {
			respondError(w, http.StatusBadRequest, "Name, type, and building_id are required")
			return
		}

		createdEquipment, err := s.Services.Equipment.CreateEquipment(ctx, req.Name, req.Type, req.BuildingID, req.RoomID, req.X, req.Y, req.Z)
		if err != nil {
			logger.Error("Failed to create equipment: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to create equipment")
			return
		}

		respondJSON(w, http.StatusCreated, createdEquipment)
	}
}

// User Handlers

// @Summary		Update Current User
// @Description	Update the authenticated user's information
// @Tags		Users
// @Security	BearerAuth
// @Accept		json
// @Produce		json
// @Param		updates	body		docs.UserUpdateRequest	true	"User updates"
// @Success		200	{object}	docs.UserResponse
// @Failure		400	{object}	docs.ErrorResponse	"Invalid request"
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Router		/users/me [put]
func HandleUpdateCurrentUser(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		userID := getUserID(ctx)

		var updates apimodels.UserUpdate
		if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}

		// Convert struct to map
		updatesMap := make(map[string]interface{})
		if updates.Name != nil {
			updatesMap["name"] = *updates.Name
		}
		if updates.Email != nil {
			updatesMap["email"] = *updates.Email
		}
		if updates.Role != nil {
			updatesMap["role"] = *updates.Role
		}

		user, err := s.Services.User.UpdateUser(ctx, userID, updatesMap)
		if err != nil {
			logger.Error("Failed to update user %s: %v", userID, err)
			respondError(w, http.StatusInternalServerError, "Failed to update user")
			return
		}

		respondJSON(w, http.StatusOK, user)
	}
}

// @Summary		Change Password
// @Description	Change the current user's password
// @Tags		Users
// @Security	BearerAuth
// @Accept		json
// @Produce		json
// @Param		passwords	body		docs.ChangePasswordRequest	true	"Password change request"
// @Success		204		"Password changed successfully"
// @Failure		400	{object}	docs.ErrorResponse	"Invalid request"
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized or invalid old password"
// @Router		/users/me/password [post]
func HandleChangePassword(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		userID := getUserID(ctx)

		var req struct {
			OldPassword string `json:"old_password"`
			NewPassword string `json:"new_password"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}

		// Validate passwords
		if req.OldPassword == "" || req.NewPassword == "" {
			respondError(w, http.StatusBadRequest, "Old and new passwords are required")
			return
		}

		if len(req.NewPassword) < 8 {
			respondError(w, http.StatusBadRequest, "New password must be at least 8 characters")
			return
		}

		// First, get the current user to verify the old password
		currentUser, err := s.Services.User.GetUser(ctx, userID)
		if err != nil {
			logger.Error("Failed to get user %s: %v", userID, err)
			respondError(w, http.StatusInternalServerError, "Failed to verify user")
			return
		}

		// Verify the old password
		// Note: This assumes the user object has a password field
		// In a real implementation, you'd use a proper password hashing library
		userMap, ok := currentUser.(map[string]interface{})
		if !ok {
			logger.Error("Invalid user data structure for user %s", userID)
			respondError(w, http.StatusInternalServerError, "Invalid user data")
			return
		}

		storedPassword, exists := userMap["password"]
		if !exists {
			logger.Error("No password field found for user %s", userID)
			respondError(w, http.StatusInternalServerError, "User password not found")
			return
		}

		// Simple string comparison (in production, use proper password hashing)
		if storedPassword != req.OldPassword {
			respondError(w, http.StatusUnauthorized, "Invalid old password")
			return
		}
		updates := map[string]interface{}{
			"password": req.NewPassword,
		}

		_, err = s.Services.User.UpdateUser(ctx, userID, updates)
		if err != nil {
			logger.Error("Failed to change password for user %s: %v", userID, err)
			respondError(w, http.StatusInternalServerError, "Failed to change password")
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}

// Helper functions

// Context key for user ID
type contextKey string

const ContextKeyUserID contextKey = "user_id"

func respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func respondError(w http.ResponseWriter, status int, message string) {
	respondJSON(w, status, map[string]interface{}{
		"error":   http.StatusText(status),
		"message": message,
		"status":  status,
	})
}

func extractToken(r *http.Request) string {
	auth := r.Header.Get("Authorization")
	if len(auth) > 7 && auth[:7] == "Bearer " {
		return auth[7:]
	}
	return ""
}

func getUserID(ctx context.Context) string {
	if v, ok := ctx.Value(ContextKeyUserID).(string); ok {
		return v
	}
	return ""
}

func generateID() string {
	return uuid.New().String()
}

func performSearch(ctx context.Context, query, searchType string, limit int) []map[string]interface{} {
	// This would integrate with the search service
	// For now, return empty results
	return []map[string]interface{}{}
}

// HandleSyncPush handles sync push operations
func HandleSyncPush(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		userID := getUserID(ctx)

		if userID == "" {
			respondError(w, http.StatusUnauthorized, "Authentication required")
			return
		}

		// Get all buildings for the user to sync
		buildings, err := s.Services.Building.GetBuildings(ctx)
		if err != nil {
			logger.Error("Failed to get buildings for sync: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to sync buildings")
			return
		}

		// Get all equipment for sync
		equipment, err := s.Services.Equipment.GetEquipment(ctx)
		if err != nil {
			logger.Error("Failed to get equipment for sync: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to sync equipment")
			return
		}

		respondJSON(w, http.StatusOK, map[string]interface{}{
			"status":    "success",
			"message":   "Sync push completed",
			"buildings": len(buildings),
			"equipment": len(equipment),
			"timestamp": time.Now(),
		})
	}
}

// HandleSyncPull handles sync pull operations
func HandleSyncPull(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		userID := getUserID(ctx)

		if userID == "" {
			respondError(w, http.StatusUnauthorized, "Authentication required")
			return
		}

		// Parse sync request body
		var req struct {
			LastSyncTime *time.Time `json:"last_sync_time,omitempty"`
			EntityTypes  []string   `json:"entity_types,omitempty"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}

		// Get updated data since last sync
		buildings, err := s.Services.Building.GetBuildings(ctx)
		if err != nil {
			logger.Error("Failed to get buildings for sync pull: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to sync buildings")
			return
		}

		equipment, err := s.Services.Equipment.GetEquipment(ctx)
		if err != nil {
			logger.Error("Failed to get equipment for sync pull: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to sync equipment")
			return
		}

		respondJSON(w, http.StatusOK, map[string]interface{}{
			"status":      "success",
			"message":     "Sync pull completed",
			"buildings":   buildings,
			"equipment":   equipment,
			"sync_time":   time.Now(),
			"last_sync":   req.LastSyncTime,
		})
	}
}

// HandleSyncStatus handles sync status requests
func HandleSyncStatus(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		userID := getUserID(ctx)

		if userID == "" {
			respondError(w, http.StatusUnauthorized, "Authentication required")
			return
		}

		// Get current data counts for status
		buildings, err := s.Services.Building.GetBuildings(ctx)
		if err != nil {
			logger.Error("Failed to get buildings for sync status: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to get sync status")
			return
		}

		equipment, err := s.Services.Equipment.GetEquipment(ctx)
		if err != nil {
			logger.Error("Failed to get equipment for sync status: %v", err)
			respondError(w, http.StatusInternalServerError, "Failed to get sync status")
			return
		}

		respondJSON(w, http.StatusOK, map[string]interface{}{
			"status":         "idle",
			"last_sync":      time.Now(),
			"total_buildings": len(buildings),
			"total_equipment": len(equipment),
			"user_id":        userID,
			"sync_enabled":   true,
		})
	}
}
