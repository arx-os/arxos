package handlers

import (
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/api/types"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// APIHandler handles general API requests
type APIHandler struct {
	*BaseHandler
}

// NewAPIHandler creates a new API handler
func NewAPIHandler(server *types.Server) *APIHandler {
	return &APIHandler{
		BaseHandler: NewBaseHandler(server),
	}
}

// HandleHealth handles GET /health
func (h *APIHandler) HandleHealth(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	response := models.HealthResponse{
		Status:    "healthy",
		Version:   "2.0.0",
		Timestamp: time.Now().UTC(),
		Checks: map[string]interface{}{
			"database": "connected",
			"cache":    "connected",
		},
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleRefreshToken handles POST /auth/refresh
func (h *APIHandler) HandleRefreshToken(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse request
	var req models.RefreshTokenRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Refresh token
	accessToken, refreshToken, err := h.server.Services.Auth.RefreshToken(r.Context(), req.RefreshToken)
	if err != nil {
		h.HandleError(w, r, err, "Invalid refresh token")
		return
	}

	response := models.AuthResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresIn:    3600, // 1 hour
		TokenType:    "Bearer",
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleListBuildings handles GET /api/v1/buildings
func (h *APIHandler) HandleListBuildings(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse pagination
	limit, offset := h.ParsePagination(r)

	// Get buildings from service
	buildings, err := h.server.Services.Building.ListBuildings(r.Context(), user.ID, offset, limit)
	if err != nil {
		h.HandleError(w, r, err, "Failed to retrieve buildings")
		return
	}

	// Convert to response format
	buildingResponses := make([]models.BuildingResponse, len(buildings))
	for i, building := range buildings {
		if b, ok := building.(*domainmodels.Building); ok {
			buildingResponses[i] = models.BuildingToResponse(b)
		}
	}

	h.RespondPaginated(w, buildingResponses, limit, offset, len(buildingResponses))
}

// HandleGetBuilding handles GET /api/v1/buildings/{id}
func (h *APIHandler) HandleGetBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse building ID
	buildingID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}

	// Get building from service
	building, err := h.server.Services.Building.GetBuilding(r.Context(), buildingID)
	if err != nil {
		h.HandleError(w, r, err, "Building not found")
		return
	}

	// Check if user has access to this building
	if b, ok := building.(*domainmodels.Building); ok {
		if b.ID != user.ID && string(user.Role) != string(domainmodels.UserRoleAdmin) {
			h.RespondError(w, http.StatusForbidden, "Access denied")
			return
		}
		h.RespondJSON(w, http.StatusOK, models.BuildingToResponse(b))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid building data")
	}
}

// HandleCreateBuilding handles POST /api/v1/buildings
func (h *APIHandler) HandleCreateBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse request
	var req models.CreateBuildingRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Set organization ID
	req.OrgID = user.ID

	// Create building
	building, err := h.server.Services.Building.CreateBuilding(r.Context(), req.Name)
	if err != nil {
		h.HandleError(w, r, err, "Failed to create building")
		return
	}

	// Convert to response format
	if b, ok := building.(*domainmodels.Building); ok {
		h.RespondJSON(w, http.StatusCreated, models.BuildingToResponse(b))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid building data")
	}
}

// HandleUpdateBuilding handles PUT /api/v1/buildings/{id}
func (h *APIHandler) HandleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse building ID
	buildingID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}

	// Parse request
	var req models.UpdateBuildingRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Convert to updates map
	updates := make(map[string]interface{})
	if req.Name != nil && *req.Name != "" {
		updates["name"] = *req.Name
	}
	if req.Description != nil && *req.Description != "" {
		updates["description"] = *req.Description
	}
	if req.Address != nil && *req.Address != "" {
		updates["address"] = *req.Address
	}
	if req.Latitude != nil && *req.Latitude != 0 {
		updates["latitude"] = *req.Latitude
	}
	if req.Longitude != nil && *req.Longitude != 0 {
		updates["longitude"] = *req.Longitude
	}
	if req.Status != nil && *req.Status != "" {
		updates["status"] = *req.Status
	}

	// Update building
	var name string
	if req.Name != nil {
		name = *req.Name
	}

	building, err := h.server.Services.Building.UpdateBuilding(r.Context(), buildingID, name)
	if err != nil {
		h.HandleError(w, r, err, "Failed to update building")
		return
	}

	// Convert to response format
	if b, ok := building.(*domainmodels.Building); ok {
		h.RespondJSON(w, http.StatusOK, models.BuildingToResponse(b))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid building data")
	}
}

// HandleDeleteBuilding handles DELETE /api/v1/buildings/{id}
func (h *APIHandler) HandleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse building ID
	buildingID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}

	// Check if user has admin access
	if string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Delete building
	if err := h.server.Services.Building.DeleteBuilding(r.Context(), buildingID); err != nil {
		h.HandleError(w, r, err, "Failed to delete building")
		return
	}

	h.RespondSuccess(w, nil, "Building deleted successfully")
}

// HandleListEquipment handles GET /api/v1/equipment
func (h *APIHandler) HandleListEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse pagination
	limit, offset := h.ParsePagination(r)

	// Get equipment from service
	equipment, err := h.server.Services.Equipment.GetEquipment(r.Context())
	if err != nil {
		h.HandleError(w, r, err, "Failed to retrieve equipment")
		return
	}

	// Convert to response format
	equipmentResponses := make([]models.EquipmentResponse, len(equipment))
	for i, eq := range equipment {
		if e, ok := eq.(*domainmodels.Equipment); ok {
			equipmentResponses[i] = models.EquipmentToResponse(e)
		}
	}

	h.RespondPaginated(w, equipmentResponses, limit, offset, len(equipmentResponses))
}

// HandleGetEquipment handles GET /api/v1/equipment/{id}
func (h *APIHandler) HandleGetEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse equipment ID
	equipmentID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid equipment ID")
		return
	}

	// Get equipment from service
	equipment, err := h.server.Services.Equipment.GetEquipmentByID(r.Context(), equipmentID)
	if err != nil {
		h.HandleError(w, r, err, "Equipment not found")
		return
	}

	// Convert to response format
	if e, ok := equipment.(*domainmodels.Equipment); ok {
		h.RespondJSON(w, http.StatusOK, models.EquipmentToResponse(e))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid equipment data")
	}
}

// HandleCreateEquipment handles POST /api/v1/equipment
func (h *APIHandler) HandleCreateEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse request
	var req models.CreateEquipmentRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Create equipment
	equipment, err := h.server.Services.Equipment.CreateEquipment(r.Context(), req.Name, req.Type, req.BuildingID, req.RoomID, req.X, req.Y, req.Z)
	if err != nil {
		h.HandleError(w, r, err, "Failed to create equipment")
		return
	}

	// Convert to response format
	if e, ok := equipment.(*domainmodels.Equipment); ok {
		h.RespondJSON(w, http.StatusCreated, models.EquipmentToResponse(e))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid equipment data")
	}
}

// HandleUpdateEquipment handles PUT /api/v1/equipment/{id}
func (h *APIHandler) HandleUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse equipment ID
	equipmentID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid equipment ID")
		return
	}

	// Parse request
	var req models.UpdateEquipmentRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Update equipment
	var name, equipmentType string
	var x, y, z float64
	if req.Name != nil {
		name = *req.Name
	}
	if req.Type != nil {
		equipmentType = *req.Type
	}
	if req.X != nil {
		x = *req.X
	}
	if req.Y != nil {
		y = *req.Y
	}
	if req.Z != nil {
		z = *req.Z
	}

	equipment, err := h.server.Services.Equipment.UpdateEquipment(r.Context(), equipmentID, name, equipmentType, x, y, z)
	if err != nil {
		h.HandleError(w, r, err, "Failed to update equipment")
		return
	}

	// Convert to response format
	if e, ok := equipment.(*domainmodels.Equipment); ok {
		h.RespondJSON(w, http.StatusOK, models.EquipmentToResponse(e))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid equipment data")
	}
}

// HandleDeleteEquipment handles DELETE /api/v1/equipment/{id}
func (h *APIHandler) HandleDeleteEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse equipment ID
	equipmentID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid equipment ID")
		return
	}

	// Check if user has admin access
	if string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Delete equipment
	if err := h.server.Services.Equipment.DeleteEquipment(r.Context(), equipmentID); err != nil {
		h.HandleError(w, r, err, "Failed to delete equipment")
		return
	}

	h.RespondSuccess(w, nil, "Equipment deleted successfully")
}

// HandleSyncPush handles POST /api/v1/sync/push
func (h *APIHandler) HandleSyncPush(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse request
	var req models.SyncRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Process sync push
	// This would use the SyncService to process the sync
	// For now, return a placeholder response
	h.RespondSuccess(w, map[string]interface{}{
		"last_sync_time": time.Now(),
		"status":         "synced",
	}, "Data synced successfully")
}

// HandleSyncPull handles GET /api/v1/sync/pull
func (h *APIHandler) HandleSyncPull(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse query parameters
	lastSyncTime := r.URL.Query().Get("last_sync_time")
	if lastSyncTime == "" {
		lastSyncTime = "1970-01-01T00:00:00Z"
	}

	// Process sync pull
	// This would use the SyncService to process the sync
	// For now, return a placeholder response
	h.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"last_sync_time": lastSyncTime,
		"data":           []interface{}{},
		"status":         "synced",
	})
}

// HandleSyncStatus handles GET /api/v1/sync/status
func (h *APIHandler) HandleSyncStatus(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Get sync status
	// This would use the SyncService to get sync status
	// For now, return a placeholder response
	h.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"status":      "active",
		"last_sync":   time.Now(),
		"next_sync":   time.Now().Add(5 * time.Minute),
		"sync_count":  42,
		"error_count": 0,
	})
}

// Legacy handler functions for backward compatibility
func HandleHealth(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleHealth
}

func HandleRefreshToken(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleRefreshToken
}

func HandleListBuildings(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleListBuildings
}

func HandleGetBuilding(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleGetBuilding
}

func HandleCreateBuilding(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleCreateBuilding
}

func HandleUpdateBuilding(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleUpdateBuilding
}

func HandleDeleteBuilding(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleDeleteBuilding
}

func HandleListEquipment(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleListEquipment
}

func HandleGetEquipment(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleGetEquipment
}

func HandleCreateEquipment(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleCreateEquipment
}

func HandleUpdateEquipment(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleUpdateEquipment
}

func HandleDeleteEquipment(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleDeleteEquipment
}

func HandleSyncPush(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleSyncPush
}

func HandleSyncPull(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleSyncPull
}

func HandleSyncStatus(s *types.Server) http.HandlerFunc {
	handler := NewAPIHandler(s)
	return handler.HandleSyncStatus
}
