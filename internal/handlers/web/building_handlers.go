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
		Name        string  `json:"name"`
		Address     string  `json:"address"`
		City        string  `json:"city"`
		State       string  `json:"state"`
		PostalCode  string  `json:"postal_code"`
		Country     string  `json:"country"`
		Floors      int     `json:"floors"`
		TotalArea   float64 `json:"total_area"`
		BuildingType string `json:"building_type"`
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
		ID:          uuid.New().String(),
		Name:        req.Name,
		Address:     req.Address,
		City:        req.City,
		State:       req.State,
		PostalCode:  req.PostalCode,
		Country:     req.Country,
		Floors:      req.Floors,
		TotalArea:   req.TotalArea,
		BuildingType: req.BuildingType,
		Equipment:   []*models.Equipment{},
		Rooms:       []*models.Room{},
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
	if address, ok := updates["address"].(string); ok {
		building.Address = address
	}
	if city, ok := updates["city"].(string); ok {
		building.City = city
	}
	if state, ok := updates["state"].(string); ok {
		building.State = state
	}
	if postalCode, ok := updates["postal_code"].(string); ok {
		building.PostalCode = postalCode
	}
	if country, ok := updates["country"].(string); ok {
		building.Country = country
	}
	if floors, ok := updates["floors"].(float64); ok {
		building.Floors = int(floors)
	}
	if totalArea, ok := updates["total_area"].(float64); ok {
		building.TotalArea = totalArea
	}
	if buildingType, ok := updates["building_type"].(string); ok {
		building.BuildingType = buildingType
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

	// Filter rooms by floor
	floorRooms := make([]*models.Room, 0)
	for _, room := range rooms {
		if room.Floor == floor {
			floorRooms = append(floorRooms, room)
		}
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
			"TotalFloors":  building.Floors,
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