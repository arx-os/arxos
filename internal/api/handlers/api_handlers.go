package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"strconv"
	"time"

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
func (s *Server) HandleHealth(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":  "healthy",
		"version": "2.0.0",
		"time":    time.Now().UTC(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Authentication Handlers

// @Summary		User Login
// @Description	Authenticate user and receive access token
// @Tags		Authentication
// @Accept		json
// @Produce		json
// @Param		credentials	body		docs.LoginRequest	true	"Login credentials"
// @Success		200	{object}	docs.AuthResponse	"Successfully authenticated"
// @Failure		400	{object}	docs.ErrorResponse	"Invalid request"
// @Failure		401	{object}	docs.ErrorResponse	"Invalid credentials"
// @Router		/auth/login [post]
func (s *Server) HandleLogin(w http.ResponseWriter, r *http.Request) {
	var req models.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate input
	if req.Email == "" || req.Password == "" {
		respondError(w, http.StatusBadRequest, "Email and password are required")
		return
	}

	// Authenticate user
	response, err := s.services.Auth.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		logger.Error("Login failed for %s: %v", req.Email, err)
		respondError(w, http.StatusUnauthorized, "Invalid email or password")
		return
	}

	respondJSON(w, http.StatusOK, response)
}

// @Summary		User Logout
// @Description	Invalidate the current session
// @Tags		Authentication
// @Security	BearerAuth
// @Success		204	"Successfully logged out"
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Router		/auth/logout [post]
func (s *Server) HandleLogout(w http.ResponseWriter, r *http.Request) {
	token := extractToken(r)
	if token == "" {
		respondError(w, http.StatusUnauthorized, "No token provided")
		return
	}

	if err := s.services.Auth.Logout(r.Context(), token); err != nil {
		logger.Error("Logout failed: %v", err)
	}

	w.WriteHeader(http.StatusNoContent)
}

// @Summary		Refresh Token
// @Description	Refresh access token using refresh token
// @Tags		Authentication
// @Accept		json
// @Produce		json
// @Param		refresh	body		docs.RefreshRequest	true	"Refresh token"
// @Success		200	{object}	docs.AuthResponse	"New tokens generated"
// @Failure		401	{object}	docs.ErrorResponse	"Invalid refresh token"
// @Router		/auth/refresh [post]
func (s *Server) HandleRefreshToken(w http.ResponseWriter, r *http.Request) {
	var req struct {
		RefreshToken string `json:"refresh_token"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	response, err := s.services.Auth.RefreshToken(r.Context(), req.RefreshToken)
	if err != nil {
		respondError(w, http.StatusUnauthorized, "Invalid refresh token")
		return
	}

	respondJSON(w, http.StatusOK, response)
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
func (s *Server) HandleListBuildings(w http.ResponseWriter, r *http.Request) {
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

	buildings, err := s.services.Building.ListBuildings(ctx, userID, limit, offset)
	if err != nil {
		logger.Error("Failed to list buildings: %v", err)
		respondError(w, http.StatusInternalServerError, "Failed to retrieve buildings")
		return
	}

	respondJSON(w, http.StatusOK, buildings)
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
func (s *Server) HandleGetBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	buildingID := chi.URLParam(r, "id")

	building, err := s.services.Building.GetBuilding(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get building %s: %v", buildingID, err)
		respondError(w, http.StatusNotFound, "Building not found")
		return
	}

	respondJSON(w, http.StatusOK, building)
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
func (s *Server) HandleCreateBuilding(w http.ResponseWriter, r *http.Request) {
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

	building := &models.FloorPlan{
		ID:           generateID(),
		Name:         req.Name,
		Address:      req.Address,
		City:         req.City,
		State:        req.State,
		PostalCode:   req.PostalCode,
		Country:      req.Country,
		Floors:       req.Floors,
		TotalArea:    req.TotalArea,
		BuildingType: req.BuildingType,
	}

	if err := s.services.Building.CreateBuilding(ctx, building); err != nil {
		logger.Error("Failed to create building: %v", err)
		respondError(w, http.StatusInternalServerError, "Failed to create building")
		return
	}

	respondJSON(w, http.StatusCreated, building)
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
func (s *Server) HandleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	buildingID := chi.URLParam(r, "id")

	// Get existing building
	building, err := s.services.Building.GetBuilding(ctx, buildingID)
	if err != nil {
		respondError(w, http.StatusNotFound, "Building not found")
		return
	}

	// Parse updates
	var req struct {
		Name       *string  `json:"name,omitempty"`
		Address    *string  `json:"address,omitempty"`
		City       *string  `json:"city,omitempty"`
		State      *string  `json:"state,omitempty"`
		PostalCode *string  `json:"postal_code,omitempty"`
		Country    *string  `json:"country,omitempty"`
		Floors     *int     `json:"floors,omitempty"`
		TotalArea  *float64 `json:"total_area,omitempty"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Apply updates
	if req.Name != nil {
		building.Name = *req.Name
	}
	if req.Address != nil {
		building.Address = *req.Address
	}
	if req.City != nil {
		building.City = *req.City
	}
	if req.State != nil {
		building.State = *req.State
	}
	if req.PostalCode != nil {
		building.PostalCode = *req.PostalCode
	}
	if req.Country != nil {
		building.Country = *req.Country
	}
	if req.Floors != nil {
		building.Floors = *req.Floors
	}
	if req.TotalArea != nil {
		building.TotalArea = *req.TotalArea
	}

	if err := s.services.Building.UpdateBuilding(ctx, building); err != nil {
		logger.Error("Failed to update building: %v", err)
		respondError(w, http.StatusInternalServerError, "Failed to update building")
		return
	}

	respondJSON(w, http.StatusOK, building)
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
func (s *Server) HandleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	buildingID := chi.URLParam(r, "id")

	if err := s.services.Building.DeleteBuilding(ctx, buildingID); err != nil {
		logger.Error("Failed to delete building %s: %v", buildingID, err)
		respondError(w, http.StatusNotFound, "Building not found")
		return
	}

	w.WriteHeader(http.StatusNoContent)
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
func (s *Server) HandleListEquipment(w http.ResponseWriter, r *http.Request) {
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

	equipment, err := s.services.Building.ListEquipment(ctx, buildingID, filters)
	if err != nil {
		logger.Error("Failed to list equipment: %v", err)
		respondError(w, http.StatusInternalServerError, "Failed to retrieve equipment")
		return
	}

	respondJSON(w, http.StatusOK, equipment)
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
func (s *Server) HandleGetEquipment(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	equipmentID := chi.URLParam(r, "id")

	equipment, err := s.services.Building.GetEquipment(ctx, equipmentID)
	if err != nil {
		logger.Error("Failed to get equipment %s: %v", equipmentID, err)
		respondError(w, http.StatusNotFound, "Equipment not found")
		return
	}

	respondJSON(w, http.StatusOK, equipment)
}

// User Handlers

// @Summary		Get Current User
// @Description	Get information about the authenticated user
// @Tags		Users
// @Security	BearerAuth
// @Produce		json
// @Success		200	{object}	docs.UserResponse
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Router		/users/me [get]
func (s *Server) HandleGetCurrentUser(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	userID := getUserID(ctx)

	user, err := s.services.User.GetUser(ctx, userID)
	if err != nil {
		logger.Error("Failed to get user %s: %v", userID, err)
		respondError(w, http.StatusNotFound, "User not found")
		return
	}

	respondJSON(w, http.StatusOK, user)
}

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
func (s *Server) HandleUpdateCurrentUser(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	userID := getUserID(ctx)

	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	user, err := s.services.User.UpdateUser(ctx, userID, updates)
	if err != nil {
		logger.Error("Failed to update user %s: %v", userID, err)
		respondError(w, http.StatusInternalServerError, "Failed to update user")
		return
	}

	respondJSON(w, http.StatusOK, user)
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
func (s *Server) HandleChangePassword(w http.ResponseWriter, r *http.Request) {
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

	if err := s.services.User.ChangePassword(ctx, userID, req.OldPassword, req.NewPassword); err != nil {
		logger.Error("Failed to change password for user %s: %v", userID, err)
		respondError(w, http.StatusUnauthorized, "Invalid old password")
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// Search Handler

// @Summary		Search
// @Description	Search across buildings, equipment, and rooms
// @Tags		Search
// @Security	BearerAuth
// @Produce		json
// @Param		q		query		string	true	"Search query"
// @Param		type	query		string	false	"Filter by type (building, equipment, room)"
// @Param		limit	query		int		false	"Limit results"	default(20)
// @Success		200	{object}	docs.SearchResponse
// @Failure		400	{object}	docs.ErrorResponse	"Invalid query"
// @Failure		401	{object}	docs.ErrorResponse	"Unauthorized"
// @Router		/search [get]
func (s *Server) HandleSearch(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" || len(query) < 2 {
		respondError(w, http.StatusBadRequest, "Search query must be at least 2 characters")
		return
	}

	// Parse parameters
	searchType := r.URL.Query().Get("type")
	limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
	if limit <= 0 || limit > 100 {
		limit = 20
	}

	// Perform search
	results := s.performSearch(r.Context(), query, searchType, limit)

	response := map[string]interface{}{
		"query":   query,
		"results": results,
		"count":   len(results),
	}

	respondJSON(w, http.StatusOK, response)
}

// Helper functions

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

type contextKey string

func getUserID(ctx context.Context) string {
	if userID, ok := ctx.Value(contextKey("user_id")).(string); ok {
		return userID
	}
	return ""
}

func generateID() string {
	return uuid.New().String()
}

func (s *Server) performSearch(ctx context.Context, query, searchType string, limit int) []map[string]interface{} {
	// This would integrate with the search service
	// For now, return empty results
	return []map[string]interface{}{}
}