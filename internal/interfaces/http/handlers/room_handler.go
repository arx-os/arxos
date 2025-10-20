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

// RoomHandler handles room-related HTTP requests
type RoomHandler struct {
	BaseHandler
	roomUC *usecase.RoomUseCase
	logger domain.Logger
}

// NewRoomHandler creates a new room handler
func NewRoomHandler(base BaseHandler, roomUC *usecase.RoomUseCase, logger domain.Logger) *RoomHandler {
	return &RoomHandler{
		BaseHandler: base,
		roomUC:      roomUC,
		logger:      logger,
	}
}

// CreateRoom handles POST /api/v1/rooms
func (h *RoomHandler) CreateRoom(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create room requested")

	// Parse request body
	var req domain.CreateRoomRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.logger.Error("Failed to decode request body", "error", err)
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %w", err))
		return
	}

	// Create room via use case
	room, err := h.roomUC.CreateRoom(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to create room", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return created room
	h.RespondJSON(w, http.StatusCreated, room)
}

// GetRoom handles GET /api/v1/rooms/{id}
func (h *RoomHandler) GetRoom(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get room ID from URL
	roomID := chi.URLParam(r, "id")
	if roomID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("room ID is required"))
		return
	}

	h.logger.Info("Get room requested", "room_id", roomID)

	// Get room via use case
	room, err := h.roomUC.GetRoom(r.Context(), types.FromString(roomID))
	if err != nil {
		h.logger.Error("Failed to get room", "room_id", roomID, "error", err)
		h.RespondError(w, http.StatusNotFound, err)
		return
	}

	// Return room
	h.RespondJSON(w, http.StatusOK, room)
}

// ListRooms handles GET /api/v1/rooms?floor_id={id}
func (h *RoomHandler) ListRooms(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("List rooms requested")

	// Get floor ID from query parameter
	floorID := r.URL.Query().Get("floor_id")
	if floorID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("floor_id query parameter is required"))
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

	// List rooms via use case
	rooms, err := h.roomUC.ListRooms(r.Context(), types.FromString(floorID), limit, offset)
	if err != nil {
		h.logger.Error("Failed to list rooms", "floor_id", floorID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return rooms
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"rooms":    rooms,
		"total":    len(rooms),
		"floor_id": floorID,
		"limit":    limit,
		"offset":   offset,
	})
}

// UpdateRoom handles PUT /api/v1/rooms/{id}
func (h *RoomHandler) UpdateRoom(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get room ID from URL
	roomID := chi.URLParam(r, "id")
	if roomID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("room ID is required"))
		return
	}

	h.logger.Info("Update room requested", "room_id", roomID)

	// Parse request body
	var req domain.UpdateRoomRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.logger.Error("Failed to decode request body", "error", err)
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %w", err))
		return
	}

	// Set ID from URL parameter
	req.ID = types.FromString(roomID)

	// Update room via use case
	room, err := h.roomUC.UpdateRoom(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to update room", "room_id", roomID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return updated room
	h.RespondJSON(w, http.StatusOK, room)
}

// DeleteRoom handles DELETE /api/v1/rooms/{id}
func (h *RoomHandler) DeleteRoom(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	// Get room ID from URL
	roomID := chi.URLParam(r, "id")
	if roomID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("room ID is required"))
		return
	}

	h.logger.Info("Delete room requested", "room_id", roomID)

	// Delete room via use case
	if err := h.roomUC.DeleteRoom(r.Context(), roomID); err != nil {
		h.logger.Error("Failed to delete room", "room_id", roomID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return success (no content)
	w.WriteHeader(http.StatusNoContent)
}

// GetRoomEquipment handles GET /api/v1/rooms/{id}/equipment
func (h *RoomHandler) GetRoomEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get room ID from URL
	roomID := chi.URLParam(r, "id")
	if roomID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("room ID is required"))
		return
	}

	h.logger.Info("Get room equipment requested", "room_id", roomID)

	// Get equipment for this room
	equipment, err := h.roomUC.GetRoomEquipment(r.Context(), types.FromString(roomID))
	if err != nil {
		h.logger.Error("Failed to get room equipment", "room_id", roomID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return equipment
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"equipment": equipment,
		"total":     len(equipment),
		"room_id":   roomID,
	})
}
