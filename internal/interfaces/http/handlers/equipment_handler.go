package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	domaintypes "github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// EquipmentHandler handles equipment-related HTTP requests
type EquipmentHandler struct {
	BaseHandler
	equipmentUC      *usecase.EquipmentUseCase
	relationshipRepo domain.RelationshipRepository
	logger           domain.Logger
}

// NewEquipmentHandler creates a new equipment handler
func NewEquipmentHandler(server *types.Server, equipmentUC *usecase.EquipmentUseCase, relationshipRepo domain.RelationshipRepository, logger domain.Logger) *EquipmentHandler {
	return &EquipmentHandler{
		BaseHandler:      nil, // Will be injected by container
		equipmentUC:      equipmentUC,
		relationshipRepo: relationshipRepo,
		logger:           logger,
	}
}

// ListEquipment handles GET /api/v1/equipment
func (h *EquipmentHandler) ListEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("List equipment requested")

	// Parse query parameters
	limit := 10
	offset := 0
	buildingID := r.URL.Query().Get("building_id")
	floorID := r.URL.Query().Get("floor_id")
	roomID := r.URL.Query().Get("room_id")
	equipmentType := r.URL.Query().Get("type")

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Create filter
	filter := &domain.EquipmentFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Set optional filters
	if buildingID != "" {
		buildingIDTyped := domaintypes.FromString(buildingID)
		filter.BuildingID = &buildingIDTyped
	}
	if floorID != "" {
		floorIDTyped := domaintypes.FromString(floorID)
		filter.FloorID = &floorIDTyped
	}
	if roomID != "" {
		roomIDTyped := domaintypes.FromString(roomID)
		filter.RoomID = &roomIDTyped
	}
	if equipmentType != "" {
		filter.Type = &equipmentType
	}

	// Call use case
	equipment, err := h.equipmentUC.ListEquipment(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to list equipment", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	response := map[string]any{
		"equipment": equipment,
		"limit":     limit,
		"offset":    offset,
		"filters": map[string]any{
			"building_id": buildingID,
			"floor_id":    floorID,
			"room_id":     roomID,
			"type":        equipmentType,
		},
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// CreateEquipment handles POST /api/v1/equipment
func (h *EquipmentHandler) CreateEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create equipment requested")

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req domain.CreateEquipmentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Call use case
	equipment, err := h.equipmentUC.CreateEquipment(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to create equipment", "error", err)

		// Check for validation errors
		if err.Error() == "equipment name is required" || err.Error() == "building ID is required" {
			h.RespondError(w, http.StatusBadRequest, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusCreated, equipment)
}

// GetEquipment handles GET /api/v1/equipment/{id}
func (h *EquipmentHandler) GetEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get equipment requested")

	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("equipment ID is required"))
		return
	}

	// Call use case
	equipment, err := h.equipmentUC.GetEquipment(r.Context(), equipmentID)
	if err != nil {
		h.logger.Error("Failed to get equipment", "equipment_id", equipmentID, "error", err)

		// Check for not found
		if err.Error() == "equipment not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusOK, equipment)
}

// UpdateEquipment handles PUT /api/v1/equipment/{id}
func (h *EquipmentHandler) UpdateEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Update equipment requested")

	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("equipment ID is required"))
		return
	}

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req domain.UpdateEquipmentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Set the ID from URL parameter
	req.ID = domaintypes.FromString(equipmentID)

	// Call use case
	equipment, err := h.equipmentUC.UpdateEquipment(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to update equipment", "equipment_id", equipmentID, "error", err)

		// Check for validation errors
		if err.Error() == "equipment name is required" {
			h.RespondError(w, http.StatusBadRequest, err)
			return
		}

		// Check for not found
		if err.Error() == "equipment not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusOK, equipment)
}

// DeleteEquipment handles DELETE /api/v1/equipment/{id}
func (h *EquipmentHandler) DeleteEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	h.logger.Info("Delete equipment requested")

	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("equipment ID is required"))
		return
	}

	// Call use case
	err := h.equipmentUC.DeleteEquipment(r.Context(), equipmentID)
	if err != nil {
		h.logger.Error("Failed to delete equipment", "equipment_id", equipmentID, "error", err)

		// Check for not found
		if err.Error() == "equipment not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusNoContent, nil)
}

// GetEquipmentByBuilding handles GET /api/v1/buildings/{building_id}/equipment
func (h *EquipmentHandler) GetEquipmentByBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get equipment by building requested")

	buildingID := chi.URLParam(r, "building_id")
	if buildingID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building ID is required"))
		return
	}

	// Parse query parameters
	limit := 10
	offset := 0

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Create filter
	filter := &domain.EquipmentFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Set building filter
	if buildingID != "" {
		buildingIDTyped := domaintypes.FromString(buildingID)
		filter.BuildingID = &buildingIDTyped
	}

	// Call use case
	equipment, err := h.equipmentUC.ListEquipment(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to get equipment by building", "building_id", buildingID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	response := map[string]any{
		"building_id": buildingID,
		"equipment":   equipment,
		"limit":       limit,
		"offset":      offset,
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// GetEquipmentByFloor handles GET /api/v1/buildings/{building_id}/floors/{floor_id}/equipment
func (h *EquipmentHandler) GetEquipmentByFloor(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get equipment by floor requested")

	buildingID := chi.URLParam(r, "building_id")
	floorID := chi.URLParam(r, "floor_id")

	if buildingID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building ID is required"))
		return
	}

	if floorID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("floor ID is required"))
		return
	}

	// Parse query parameters
	limit := 10
	offset := 0

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Create filter
	filter := &domain.EquipmentFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Set building and floor filters
	if buildingID != "" {
		buildingIDTyped := domaintypes.FromString(buildingID)
		filter.BuildingID = &buildingIDTyped
	}
	if floorID != "" {
		floorIDTyped := domaintypes.FromString(floorID)
		filter.FloorID = &floorIDTyped
	}

	// Call use case
	equipment, err := h.equipmentUC.ListEquipment(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to get equipment by floor", "building_id", buildingID, "floor_id", floorID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	response := map[string]any{
		"building_id": buildingID,
		"floor_id":    floorID,
		"equipment":   equipment,
		"limit":       limit,
		"offset":      offset,
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// GetByPath handles GET /api/v1/equipment/path/{path}
// Get equipment by exact path match
func (h *EquipmentHandler) GetByPath(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get path from URL parameter
	path := chi.URLParam(r, "path")
	if path == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("path parameter is required"))
		return
	}

	// Get equipment repository from context
	equipmentRepo := h.equipmentUC.GetRepository()
	if equipmentRepo == nil {
		h.RespondError(w, http.StatusInternalServerError, fmt.Errorf("equipment repository not available"))
		return
	}

	// Query by exact path
	equipment, err := equipmentRepo.GetByPath(r.Context(), path)
	if err != nil {
		h.logger.Error("Failed to get equipment by path", "path", path, "error", err)
		h.RespondError(w, http.StatusNotFound, err)
		return
	}

	h.RespondJSON(w, http.StatusOK, equipment)
}

// FindByPath handles GET /api/v1/equipment/path-pattern?pattern=/B1/3/*/HVAC/*
// Find equipment matching a path pattern (supports wildcards)
func (h *EquipmentHandler) FindByPath(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get path pattern from query parameter
	pathPattern := r.URL.Query().Get("pattern")
	if pathPattern == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("pattern parameter is required"))
		return
	}

	// Get optional filters
	status := r.URL.Query().Get("status")
	eqType := r.URL.Query().Get("type")
	
	// Parse limit
	limit := 100
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	// Get equipment repository from context
	equipmentRepo := h.equipmentUC.GetRepository()
	if equipmentRepo == nil {
		h.RespondError(w, http.StatusInternalServerError, fmt.Errorf("equipment repository not available"))
		return
	}

	// Query by path pattern
	equipment, err := equipmentRepo.FindByPath(r.Context(), pathPattern)
	if err != nil {
		h.logger.Error("Failed to find equipment by path pattern", "pattern", pathPattern, "error", err)
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Apply additional filters if specified
	if status != "" {
		filtered := make([]*domain.Equipment, 0)
		for _, eq := range equipment {
			if eq.Status == status {
				filtered = append(filtered, eq)
			}
		}
		equipment = filtered
	}

	if eqType != "" {
		filtered := make([]*domain.Equipment, 0)
		for _, eq := range equipment {
			if eq.Type == eqType {
				filtered = append(filtered, eq)
			}
		}
		equipment = filtered
	}

	// Apply limit
	if len(equipment) > limit {
		equipment = equipment[:limit]
	}

	// Return response
	response := map[string]any{
		"pattern":   pathPattern,
		"equipment": equipment,
		"count":     len(equipment),
		"limit":     limit,
	}
	h.RespondJSON(w, http.StatusOK, response)
}