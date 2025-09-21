package web

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// NewAuthenticatedRouter creates a router with authentication
func NewAuthenticatedRouter(h *Handler) chi.Router {
	r := chi.NewRouter()

	// Global middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Compress(5))
	r.Use(middleware.RealIP)
	r.Use(middleware.RequestID)

	// Public routes (no authentication required)
	r.Group(func(r chi.Router) {
		r.Get("/login", h.handleLogin)
		r.Post("/api/auth/login", h.authService.Login)
		r.Get("/health", h.handleHealth)

		// Static assets (CSS, JS, images)
		r.Get("/static/*", h.handleStatic)
	})

	// Protected routes (authentication required)
	r.Group(func(r chi.Router) {
		// Apply authentication middleware
		r.Use(h.authMiddleware)

		// Logout
		r.Post("/api/auth/logout", h.authService.Logout)
		r.Get("/logout", h.authService.Logout)

		// Dashboard and main pages
		r.Get("/", h.HandleDashboard)
		r.Get("/dashboard", h.HandleDashboard)

		// Buildings routes with authorization
		r.Route("/buildings", func(r chi.Router) {
			r.Get("/", h.HandleBuildingsList)

			r.Group(func(r chi.Router) {
				// Require at least "user" role to create/modify
				r.Use(h.requireRole("user"))

				r.Get("/new", h.handleNewBuilding)
				r.Post("/new", h.handleNewBuilding)

				r.Route("/{buildingID}", func(r chi.Router) {
					r.Get("/", h.handleBuildingDetail)
					r.Put("/", h.handleUpdateBuilding)
					r.Get("/floor-plan", h.HandleBuildingFloorPlan)
					r.Get("/view", h.handleFloorPlanViewer)

					// Admin only operations
					r.Group(func(r chi.Router) {
						r.Use(h.requireRole("admin"))
						r.Delete("/", h.handleDeleteBuilding)
					})
				})
			})
		})

		// Equipment routes
		r.Route("/equipment", func(r chi.Router) {
			r.Get("/", h.handleEquipment)

			r.Group(func(r chi.Router) {
				r.Use(h.requireRole("user"))
				r.Post("/", h.handleCreateEquipment)
				r.Put("/{equipmentID}", h.handleUpdateEquipment)

				r.Group(func(r chi.Router) {
					r.Use(h.requireRole("admin"))
					r.Delete("/{equipmentID}", h.handleDeleteEquipment)
				})
			})
		})

		// Settings (user role required)
		r.Group(func(r chi.Router) {
			r.Use(h.requireRole("user"))
			r.Get("/settings", h.handleSettings)
			r.Post("/settings", h.handleSettings)
		})

		// Upload (user role required)
		r.Group(func(r chi.Router) {
			r.Use(h.requireRole("user"))
			r.Get("/upload", h.handleUpload)
			r.Post("/upload", h.handleUpload)
		})

		// HTMX endpoints (authenticated)
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

		// API routes with authentication
		r.Route("/api", func(r chi.Router) {
			r.Use(h.apiAuthMiddleware)

			// Buildings API
			r.Route("/buildings", func(r chi.Router) {
				r.Get("/", h.apiBuildingsList)
				r.Post("/", h.apiCreateBuilding)
				r.Get("/{buildingID}", h.apiBuildingDetail)
				r.Put("/{buildingID}", h.apiUpdateBuilding)
				r.Delete("/{buildingID}", h.apiDeleteBuilding)
			})

			// Equipment API
			r.Route("/equipment", func(r chi.Router) {
				r.Get("/", h.apiEquipmentList)
				r.Post("/", h.apiCreateEquipment)
				r.Get("/{equipmentID}", h.apiEquipmentDetail)
				r.Put("/{equipmentID}", h.apiUpdateEquipment)
				r.Delete("/{equipmentID}", h.apiDeleteEquipment)
			})

			// Spatial queries API
			r.Post("/spatial/query", h.apiSpatialQuery)
			r.Get("/spatial/proximity", h.apiProximitySearch)

			// Import/Export API
			r.Post("/import/ifc", h.apiImportIFC)
			r.Get("/export/bim", h.apiExportBIM)

			// Connections API
			r.Route("/connections", func(r chi.Router) {
				r.Get("/graph", h.apiConnectionGraph)
				r.Post("/", h.apiCreateConnection)
				r.Delete("/{connectionID}", h.apiDeleteConnection)
			})
		})
	})

	return r
}

// authMiddleware is the main authentication middleware for web routes
func (h *Handler) authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		h.authService.AuthMiddleware(next.ServeHTTP)(w, r)
	})
}

// apiAuthMiddleware is authentication middleware specifically for API routes
func (h *Handler) apiAuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// API routes should return JSON errors
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte(`{"error":"Authentication required"}`))
			return
		}

		h.authService.AuthMiddleware(next.ServeHTTP)(w, r)
	})
}

// requireRole returns middleware that checks for specific role
func (h *Handler) requireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			h.authService.RequireRole(role)(next.ServeHTTP)(w, r)
		})
	}
}

// handleHealth is a health check endpoint
func (h *Handler) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"healthy","service":"arxos-web"}`))
}

// handleStatic serves static files
func (h *Handler) handleStatic(w http.ResponseWriter, r *http.Request) {
	// Serve static files from web/static directory
	http.StripPrefix("/static/", http.FileServer(http.Dir("web/static"))).ServeHTTP(w, r)
}

// Placeholder handlers for new endpoints
func (h *Handler) handleCreateEquipment(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) handleDeleteEquipment(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

// API handlers placeholders
func (h *Handler) apiBuildingsList(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiCreateBuilding(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiBuildingDetail(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiEquipmentList(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiCreateEquipment(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiEquipmentDetail(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiDeleteEquipment(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiSpatialQuery(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiProximitySearch(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiImportIFC(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiExportBIM(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiConnectionGraph(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiCreateConnection(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (h *Handler) apiDeleteConnection(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}