package web

import (
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// NewRouter creates a new Chi router with only implemented routes
func NewRouter(h *Handler) chi.Router {
	r := chi.NewRouter()

	// Add middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Compress(5))

	// Main pages - Only keep implemented handlers
	r.Get("/", h.HandleDashboard)
	r.Get("/dashboard", h.HandleDashboard)
	r.Get("/login", h.handleLogin)
	r.Post("/login", h.handleLogin)
	r.Get("/logout", h.handleLogout)

	// Buildings routes - Only implemented endpoints
	r.Route("/buildings", func(r chi.Router) {
		r.Get("/", h.HandleBuildingsList)

		r.Route("/{buildingID}", func(r chi.Router) {
			r.Get("/floor-plan", h.HandleBuildingFloorPlan) // HTMX endpoint for ASCII
		})
	})

	return r
}