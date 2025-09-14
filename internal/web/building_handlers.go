package web

import (
	"net/http"
	"strings"

	// "github.com/joelpate/arxos/internal/rendering" // TODO: Fix rendering pointer issues
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// HandleBuildingsList handles the buildings list page
func (h *Handler) HandleBuildingsList(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get buildings from database
	buildings, err := h.services.DB.GetAllFloorPlans(r.Context())
	if err != nil {
		logger.Error("Failed to get buildings: %v", err)
		h.renderError(w, r, "Failed to load buildings", http.StatusInternalServerError)
		return
	}

	// Prepare template data
	data := map[string]interface{}{
		"Buildings": buildings,
		"User":      h.getUserFromContext(r),
	}

	// Render the buildings page
	if err := h.templates.Render(w, "pages/buildings.html", data); err != nil {
		logger.Error("Failed to render buildings page: %v", err)
		h.renderError(w, r, "Failed to render page", http.StatusInternalServerError)
	}
}

// HandleBuildingFloorPlan handles the AJAX request for ASCII floor plan
func (h *Handler) HandleBuildingFloorPlan(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract building ID from URL
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 3 {
		http.Error(w, "Invalid building ID", http.StatusBadRequest)
		return
	}
	buildingID := parts[2]

	// Get building from database
	building, err := h.services.DB.GetFloorPlan(r.Context(), buildingID)
	if err != nil {
		logger.Error("Failed to get building: %v", err)
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}

	// Generate ASCII floor plan - TODO: Fix rendering pointer issues
	// renderer := rendering.NewFloorRenderer(80, 30)
	// asciiPlan, err := renderer.RenderFromFloorPlan(building)
	// if err != nil {
	// 	logger.Error("Failed to render ASCII floor plan: %v", err)
	// 	http.Error(w, "Failed to generate floor plan", http.StatusInternalServerError)
	// 	return
	// }
	asciiPlan := "Floor plan rendering temporarily disabled"

	// Calculate equipment statistics
	failedCount := 0
	needsRepairCount := 0
	for _, equip := range building.Equipment {
		switch equip.Status {
		case "FAILED":
			failedCount++
		case "DEGRADED":
			needsRepairCount++
		}
	}

	// Prepare template data
	data := map[string]interface{}{
		"Building":             building,
		"ASCIIFloorPlan":       asciiPlan,
		"FailedEquipmentCount": failedCount,
		"NeedsRepairCount":     needsRepairCount,
	}

	// Render just the floor plan partial
	if err := h.templates.RenderFragment(w, "floor-plan", data); err != nil {
		logger.Error("Failed to render floor plan partial: %v", err)
		http.Error(w, "Failed to render floor plan", http.StatusInternalServerError)
	}
}

// HandleLogin handles the login page
func (h *Handler) HandleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Check if already logged in
	if h.isAuthenticated(r) {
		http.Redirect(w, r, "/dashboard", http.StatusSeeOther)
		return
	}

	// Prepare template data
	data := map[string]interface{}{
		"DemoMode":     true, // Show demo credentials
		"DefaultEmail": "admin@arxos.io",
	}

	// Render the login page
	if err := h.templates.Render(w, "pages/login.html", data); err != nil {
		logger.Error("Failed to render login page: %v", err)
		h.renderError(w, r, "Failed to render page", http.StatusInternalServerError)
	}
}

// HandleDashboard handles the dashboard page
func (h *Handler) HandleDashboard(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Check authentication
	if !h.isAuthenticated(r) {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	// Get summary data
	buildings, err := h.services.DB.GetAllFloorPlans(r.Context())
	if err != nil {
		logger.Error("Failed to get buildings: %v", err)
		buildings = []*models.FloorPlan{}
	}

	// Calculate totals
	totalEquipment := 0
	totalRooms := 0
	failedEquipment := 0
	for _, b := range buildings {
		totalRooms += len(b.Rooms)
		totalEquipment += len(b.Equipment)
		for _, e := range b.Equipment {
			if e.Status == models.StatusFailed {
				failedEquipment++
			}
		}
	}

	// Prepare template data
	data := map[string]interface{}{
		"User":            h.getUserFromContext(r),
		"BuildingCount":   len(buildings),
		"RoomCount":       totalRooms,
		"EquipmentCount":  totalEquipment,
		"FailedEquipment": failedEquipment,
		"RecentBuildings": buildings, // TODO: Limit to recent 5
	}

	// Render the dashboard page
	if err := h.templates.Render(w, "pages/dashboard.html", data); err != nil {
		logger.Error("Failed to render dashboard: %v", err)
		h.renderError(w, r, "Failed to render page", http.StatusInternalServerError)
	}
}

// Helper methods

func (h *Handler) isAuthenticated(r *http.Request) bool {
	// Check for session cookie or auth header
	// This would integrate with the auth middleware
	// For now, return false to show login page
	return false
}

func (h *Handler) getUserFromContext(r *http.Request) *models.User {
	// Get user from context (set by auth middleware)
	// For now, return nil
	return nil
}

func (h *Handler) renderError(w http.ResponseWriter, r *http.Request, message string, statusCode int) {
	w.WriteHeader(statusCode)
	data := map[string]interface{}{
		"Error":   message,
		"Code":    statusCode,
		"User":    h.getUserFromContext(r),
	}
	
	if err := h.templates.Render(w, "pages/error.html", data); err != nil {
		// Fallback to plain text error
		http.Error(w, message, statusCode)
	}
}