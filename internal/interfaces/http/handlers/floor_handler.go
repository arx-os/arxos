package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// FloorHandler handles floor-related HTTP requests
type FloorHandler struct {
	BaseHandler
	floorUC *usecase.FloorUseCase
	logger  domain.Logger
}

// NewFloorHandler creates a new floor handler
func NewFloorHandler(base BaseHandler, floorUC *usecase.FloorUseCase, logger domain.Logger) *FloorHandler {
	return &FloorHandler{
		BaseHandler: base,
		floorUC:     floorUC,
		logger:      logger,
	}
}

// CreateFloor handles POST /api/v1/floors
func (h *FloorHandler) CreateFloor(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create floor requested")

	// Parse request body
	var req domain.CreateFloorRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.logger.Error("Failed to decode request body", "error", err)
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %w", err))
		return
	}

	// Create floor via use case
	floor, err := h.floorUC.CreateFloor(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to create floor", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return created floor
	h.RespondJSON(w, http.StatusCreated, floor)
}

// GetFloor handles GET /api/v1/floors/{id}
func (h *FloorHandler) GetFloor(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get floor ID from URL
	floorID := chi.URLParam(r, "id")
	if floorID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("floor ID is required"))
		return
	}

	h.logger.Info("Get floor requested", "floor_id", floorID)

	// Get floor via use case
	floor, err := h.floorUC.GetFloor(r.Context(), types.FromString(floorID))
	if err != nil {
		h.logger.Error("Failed to get floor", "floor_id", floorID, "error", err)
		h.RespondError(w, http.StatusNotFound, err)
		return
	}

	// Return floor
	h.RespondJSON(w, http.StatusOK, floor)
}

// ListFloors handles GET /api/v1/floors?building_id={id}
func (h *FloorHandler) ListFloors(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("List floors requested")

	// Get building ID from query parameter
	buildingID := r.URL.Query().Get("building_id")
	if buildingID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building_id query parameter is required"))
		return
	}

	// Parse pagination parameters
	limit := 100
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

	// List floors via use case
	floors, err := h.floorUC.ListFloors(r.Context(), types.FromString(buildingID), limit, offset)
	if err != nil {
		h.logger.Error("Failed to list floors", "building_id", buildingID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return floors
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"floors": floors,
		"total":  len(floors),
		"limit":  limit,
		"offset": offset,
	})
}

// UpdateFloor handles PUT /api/v1/floors/{id}
func (h *FloorHandler) UpdateFloor(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get floor ID from URL
	floorID := chi.URLParam(r, "id")
	if floorID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("floor ID is required"))
		return
	}

	h.logger.Info("Update floor requested", "floor_id", floorID)

	// Parse request body
	var req domain.UpdateFloorRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.logger.Error("Failed to decode request body", "error", err)
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %w", err))
		return
	}

	// Set ID from URL parameter
	req.ID = types.FromString(floorID)

	// Update floor via use case
	floor, err := h.floorUC.UpdateFloor(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to update floor", "floor_id", floorID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return updated floor
	h.RespondJSON(w, http.StatusOK, floor)
}

// DeleteFloor handles DELETE /api/v1/floors/{id}
func (h *FloorHandler) DeleteFloor(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	// Get floor ID from URL
	floorID := chi.URLParam(r, "id")
	if floorID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("floor ID is required"))
		return
	}

	h.logger.Info("Delete floor requested", "floor_id", floorID)

	// Delete floor via use case
	if err := h.floorUC.DeleteFloor(r.Context(), floorID); err != nil {
		h.logger.Error("Failed to delete floor", "floor_id", floorID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return success (no content)
	w.WriteHeader(http.StatusNoContent)
}

// GetFloorRooms handles GET /api/v1/floors/{id}/rooms
func (h *FloorHandler) GetFloorRooms(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get floor ID from URL
	floorID := chi.URLParam(r, "id")
	if floorID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("floor ID is required"))
		return
	}

	h.logger.Info("Get floor rooms requested", "floor_id", floorID)

	// Get rooms for this floor
	rooms, err := h.floorUC.GetFloorRooms(r.Context(), types.FromString(floorID))
	if err != nil {
		h.logger.Error("Failed to get floor rooms", "floor_id", floorID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return rooms
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"rooms":    rooms,
		"total":    len(rooms),
		"floor_id": floorID,
	})
}

// GetFloorEquipment handles GET /api/v1/floors/{id}/equipment
func (h *FloorHandler) GetFloorEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get floor ID from URL
	floorID := chi.URLParam(r, "id")
	if floorID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("floor ID is required"))
		return
	}

	h.logger.Info("Get floor equipment requested", "floor_id", floorID)

	// Get equipment for this floor
	equipment, err := h.floorUC.GetFloorEquipment(r.Context(), types.FromString(floorID))
	if err != nil {
		h.logger.Error("Failed to get floor equipment", "floor_id", floorID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return equipment
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"equipment": equipment,
		"total":     len(equipment),
		"floor_id":  floorID,
	})
}
