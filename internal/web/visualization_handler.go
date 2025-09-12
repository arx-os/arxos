package web

import (
	"fmt"
	"net/http"
	"strings"

	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/internal/visualization"
	"github.com/joelpate/arxos/pkg/models"
)

// handleFloorPlanSVG generates and returns an SVG visualization of a floor plan
func (h *Handler) handleFloorPlanSVG(w http.ResponseWriter, r *http.Request) {
	// Extract building ID from path
	path := strings.TrimPrefix(r.URL.Path, "/viz/svg/")
	buildingID := strings.TrimSuffix(path, "/")
	
	// Debug logging
	logger.Info("SVG request for path: %s, extracted ID: %s", r.URL.Path, buildingID)
	
	if buildingID == "" {
		http.Error(w, "Building ID required", http.StatusBadRequest)
		return
	}

	// Skip auth check for testing (normally we'd check h.getUser(r))
	
	// Get the floor plan from the database
	floorPlan, err := h.services.Building.GetBuilding(r.Context(), buildingID)
	if err != nil {
		logger.Error("Failed to get floor plan %s: %v", buildingID, err)
		http.Error(w, "Floor plan not found", http.StatusNotFound)
		return
	}
	
	// Get rooms for the floor plan
	rooms, err := h.services.Building.ListRooms(r.Context(), buildingID)
	if err != nil {
		logger.Error("Failed to get rooms for floor plan %s: %v", buildingID, err)
		// Continue without rooms rather than failing completely
		rooms = []*models.Room{}
	}
	
	// Get equipment for the floor plan
	equipment, err := h.services.Building.ListEquipment(r.Context(), buildingID, nil)
	if err != nil {
		logger.Error("Failed to get equipment for floor plan %s: %v", buildingID, err)
		// Continue without equipment rather than failing completely
		equipment = []*models.Equipment{}
	}
	
	// Populate the floor plan with rooms and equipment
	if rooms != nil {
		floorPlan.Rooms = make([]models.Room, len(rooms))
		for i, room := range rooms {
			floorPlan.Rooms[i] = *room
		}
	}
	
	if equipment != nil {
		floorPlan.Equipment = make([]models.Equipment, len(equipment))
		for i, eq := range equipment {
			floorPlan.Equipment[i] = *eq
		}
	}
	
	// Parse rendering options from query params
	opts := &visualization.RenderOptions{
		Width:      800,
		Height:     600,
		ShowGrid:   r.URL.Query().Get("grid") != "false",
		ShowLabels: r.URL.Query().Get("labels") != "false",
		Theme:      r.URL.Query().Get("theme"),
	}
	
	if opts.Theme == "" {
		opts.Theme = "light"
	}
	
	// Create renderer and generate SVG
	renderer := visualization.NewSVGRenderer()
	svg := renderer.RenderFloorPlan(floorPlan, opts)
	
	// Set content type and write SVG
	w.Header().Set("Content-Type", "image/svg+xml")
	w.Header().Set("Cache-Control", "no-cache") // Allow dynamic updates
	fmt.Fprint(w, svg)
}

// handleFloorPlanViewer serves the interactive floor plan viewer
func (h *Handler) handleFloorPlanViewer(w http.ResponseWriter, r *http.Request) {
	buildingID := strings.TrimPrefix(r.URL.Path, "/buildings/view/")
	buildingID = strings.TrimSuffix(buildingID, "/")
	
	user := h.getUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	// Get floor plan data from database
	floorPlan, err := h.services.Building.GetBuilding(r.Context(), buildingID)
	if err != nil {
		logger.Error("Failed to get floor plan %s: %v", buildingID, err)
		http.Error(w, "Floor plan not found", http.StatusNotFound)
		return
	}
	
	data := PageData{
		Title:     fmt.Sprintf("%s - Floor Plan", floorPlan.Name),
		User:      user,
		NavActive: "buildings",
		Content: map[string]interface{}{
			"BuildingID": buildingID,
			"FloorPlan":  floorPlan,
		},
	}

	if err := h.templates.Render(w, "floor-viewer", data); err != nil {
		logger.Error("Failed to render floor viewer: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleEquipmentUpdate handles HTMX requests to update equipment status
func (h *Handler) handleEquipmentUpdate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost && r.Method != http.MethodPatch {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	equipmentID := r.FormValue("equipment_id")
	status := r.FormValue("status")
	notes := r.FormValue("notes")

	// Validate status
	validStatuses := map[string]bool{
		"normal":       true,
		"needs-repair": true,
		"failed":       true,
	}

	if !validStatuses[status] {
		http.Error(w, "Invalid status", http.StatusBadRequest)
		return
	}

	// Update equipment (mock for now)
	logger.Info("Updating equipment %s: status=%s, notes=%s", equipmentID, status, notes)

	// Return updated SVG fragment for HTMX to replace
	// This would regenerate just the equipment element
	svg := fmt.Sprintf(`<circle cx="50" cy="50" r="5" class="equipment equipment-%s" data-equipment-id="%s"/>`,
		status, equipmentID)
	
	w.Header().Set("Content-Type", "image/svg+xml")
	fmt.Fprint(w, svg)
}

