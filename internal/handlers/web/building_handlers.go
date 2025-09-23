package web

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
)

// handleNewBuilding handles creation of a new building
func (h *Handler) handleNewBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Parse request body
    var req struct {
        Name string `json:"name"`
    }

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if req.Name == "" {
		http.Error(w, "Building name is required", http.StatusBadRequest)
		return
	}

	// Create new floor plan
    building := &models.FloorPlan{
        ID:   uuid.New().String(),
        Name: req.Name,
        Rooms:       []*models.Room{},
        Equipment:   []*models.Equipment{},
    }

	// Create building using service
	if err := h.services.Building.CreateBuilding(ctx, building); err != nil {
		logger.Error("Failed to create building: %v", err)
		http.Error(w, "Failed to create building", http.StatusInternalServerError)
		return
	}

	// Return created building
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(building)
}

// handleBuildingDetail handles getting building details
func (h *Handler) handleBuildingDetail(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
    buildingID := chi.URLParam(r, "id")

	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// Get building from service
	building, err := h.services.Building.GetBuilding(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get building %s: %v", buildingID, err)
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}

	// Check if this is an HTMX request
	if r.Header.Get("HX-Request") == "true" {
		// Render partial template for HTMX
		data := PageData{
			Content: building,
		}
		if err := h.templates.RenderFragment(w, "building_detail", data); err != nil {
			logger.Error("Failed to render building detail fragment: %v", err)
			http.Error(w, "Template error", http.StatusInternalServerError)
		}
		return
	}

	// Return JSON for API requests
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(building)
}

// handleUpdateBuilding handles updating an existing building
func (h *Handler) handleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	buildingID := chi.URLParam(r, "id")

	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// Get existing building
	building, err := h.services.Building.GetBuilding(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get building %s: %v", buildingID, err)
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}

	// Parse update request
	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Apply updates to building
    if name, ok := updates["name"].(string); ok {
        building.Name = name
    }

	// Update building
	if err := h.services.Building.UpdateBuilding(ctx, building); err != nil {
		logger.Error("Failed to update building %s: %v", buildingID, err)
		http.Error(w, "Failed to update building", http.StatusInternalServerError)
		return
	}

	// Return updated building
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(building)
}

// handleDeleteBuilding handles deleting a building
func (h *Handler) handleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	buildingID := chi.URLParam(r, "id")

	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// Delete building
	if err := h.services.Building.DeleteBuilding(ctx, buildingID); err != nil {
		logger.Error("Failed to delete building %s: %v", buildingID, err)
		http.Error(w, "Failed to delete building", http.StatusInternalServerError)
		return
	}

	// Return success
	w.WriteHeader(http.StatusNoContent)
}

// handleFloorPlanViewer handles the floor plan viewer page
func (h *Handler) handleFloorPlanViewer(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	buildingID := chi.URLParam(r, "id")
	floorStr := r.URL.Query().Get("floor")

	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// Get building
	building, err := h.services.Building.GetBuilding(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get building %s: %v", buildingID, err)
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}

	// Parse floor number
	floor := 1
	if floorStr != "" {
		if f, err := strconv.Atoi(floorStr); err == nil {
			floor = f
		}
	}

	// Get rooms for the floor
	rooms, err := h.services.Building.ListRooms(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get rooms for building %s: %v", buildingID, err)
		rooms = []*models.Room{}
	}

	// Filter rooms by floor (using Level field from FloorPlan)
	floorRooms := make([]*models.Room, 0)
	for _, room := range rooms {
		// Since Room doesn't have Floor field, we'll include all rooms for now
		// TODO: Add proper floor filtering when Room model is updated
		floorRooms = append(floorRooms, room)
	}

	// Get equipment for the floor
	equipment, err := h.services.Building.ListEquipment(ctx, buildingID, map[string]interface{}{
		"floor": floor,
	})
	if err != nil {
		logger.Error("Failed to get equipment for building %s: %v", buildingID, err)
		equipment = []*models.Equipment{}
	}

	// Prepare page data
	data := PageData{
		Title:     "Floor Plan - " + building.Name,
		NavActive: "buildings",
		User:      h.getUser(r),
		Content: map[string]interface{}{
			"Building":     building,
			"CurrentFloor": floor,
			"Rooms":        floorRooms,
			"Equipment":    equipment,
			"TotalFloors":  building.Level, // Use Level field instead of Floors
		},
	}

	// Render template
	if err := h.templates.Render(w, "floor_plan", data); err != nil {
		logger.Error("Failed to render floor plan viewer: %v", err)
		http.Error(w, "Template error", http.StatusInternalServerError)
	}
}

// handleEquipment handles equipment listing and management
func (h *Handler) handleEquipment(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	buildingID := r.URL.Query().Get("building_id")

	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// Get filters from query params
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

	// Get equipment
	equipment, err := h.services.Building.ListEquipment(ctx, buildingID, filters)
	if err != nil {
		logger.Error("Failed to get equipment for building %s: %v", buildingID, err)
		http.Error(w, "Failed to get equipment", http.StatusInternalServerError)
		return
	}

	// Check if this is an HTMX request
	if r.Header.Get("HX-Request") == "true" {
		// Render equipment list fragment
		data := PageData{
			Content: map[string]interface{}{
				"Equipment": equipment,
			},
		}
		if err := h.templates.RenderFragment(w, "equipment_list", data); err != nil {
			logger.Error("Failed to render equipment list fragment: %v", err)
			http.Error(w, "Template error", http.StatusInternalServerError)
		}
		return
	}

	// Return JSON for API requests
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(equipment)
}