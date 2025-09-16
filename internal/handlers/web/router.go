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

	// Static files served from web/ directory
	// Note: Static files are handled by the template system or file server

	// Main pages
	r.Get("/", h.HandleDashboard)
	r.Get("/dashboard", h.HandleDashboard)
	r.Get("/login", h.handleLogin)
	r.Post("/login", h.handleLogin) // Handle both GET and POST
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
			r.Get("/floor-plan", h.HandleBuildingFloorPlan) // HTMX endpoint for ASCII
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

// Placeholder handlers (would need to be implemented)

func (h *Handler) handleNewBuilding(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleBuildingDetail(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleFloorPlanViewer(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleEquipment(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleSettings(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleUpload(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleGlobalSearch(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleSearchSuggestions(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleRecentSearches(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleNotifications(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleFloorPlanSVG(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleSSE(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}
