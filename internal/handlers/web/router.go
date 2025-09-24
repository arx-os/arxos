package web

import (
	appmw "github.com/arx-os/arxos/internal/middleware"
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
	r.Use(appmw.RequestID)
	
	// Security middleware
	r.Use(appmw.SecurityHeaders)
	r.Use(appmw.InputValidation)
	
	// CSRF protection for state-changing operations
	csrfStore := appmw.NewMemoryCSRFStore()
	csrfMiddleware := appmw.NewCSRFMiddleware(csrfStore)
	r.Use(csrfMiddleware.Handler)

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

