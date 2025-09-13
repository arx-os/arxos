package web

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// NewRouter creates a new Chi router for web UI routes
func NewRouter(h *Handler) chi.Router {
	r := chi.NewRouter()

	// Add middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Compress(5))

	// Static files are served directly from embedded templates
	// Note: Static files are handled by the template system

	// Main pages
	r.Get("/", h.HandleDashboard)
	r.Get("/dashboard", h.HandleDashboard)
	r.Get("/login", h.HandleLogin)
	r.Post("/login", h.handleLogin)  // API endpoint
	r.Get("/logout", h.handleLogout)
	
	// Buildings routes
	r.Route("/buildings", func(r chi.Router) {
		r.Get("/", h.HandleBuildingsList)
		r.Get("/new", h.handleNewBuilding)
		r.Post("/new", h.handleNewBuilding)
		
		r.Route("/{buildingID}", func(r chi.Router) {
			r.Get("/", h.handleBuildingDetail)
			r.Put("/", h.handleUpdateBuilding)
			r.Delete("/", h.handleDeleteBuilding)
			r.Get("/floor-plan", h.HandleBuildingFloorPlan)  // HTMX endpoint for ASCII
			r.Get("/view", h.handleFloorPlanViewer)
		})
	})
	
	// Equipment routes
	r.Get("/equipment", h.handleEquipment)
	
	// Settings
	r.Get("/settings", h.handleSettings)
	r.Post("/settings", h.handleSettings)
	
	// Upload
	r.Get("/upload", h.handleUpload)
	r.Post("/upload", h.handleUpload)
	
	// HTMX endpoints
	r.Route("/htmx", func(r chi.Router) {
		r.Get("/search", h.handleGlobalSearch)
		r.Get("/search/suggestions", h.handleSearchSuggestions)
		r.Get("/search/recent", h.handleRecentSearches)
		r.Get("/notifications", h.handleNotifications)
	})
	
	// Visualization endpoints
	r.Get("/viz/svg/{buildingID}", h.handleFloorPlanSVG)
	
	// Server-sent events
	r.Get("/events", h.handleSSE)

	return r
}

// handleBuildingDetail handles individual building pages using Chi's URL params
func (h *Handler) handleBuildingDetail(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "buildingID")
	
	// Get building from service
	building, err := h.services.Building.GetBuilding(r.Context(), buildingID)
	if err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	
	// Render the building detail page using templates
	h.templates.Render(w, "building.html", map[string]interface{}{
		"Building": building,
	})
}

// handleUpdateBuilding handles building updates using Chi's URL params
func (h *Handler) handleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "buildingID")
	
	// Implementation for updating building
	_ = buildingID
	// TODO: Implement building update logic
	
	w.WriteHeader(http.StatusOK)
}

// handleDeleteBuilding handles building deletion using Chi's URL params
func (h *Handler) handleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "buildingID")
	
	// Delete building
	if err := h.services.Building.DeleteBuilding(r.Context(), buildingID); err != nil {
		http.Error(w, "Failed to delete building", http.StatusInternalServerError)
		return
	}
	
	// Redirect to buildings list
	http.Redirect(w, r, "/buildings", http.StatusSeeOther)
}