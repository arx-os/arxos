package web

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/go-chi/chi/v5"
	chimw "github.com/go-chi/chi/v5/middleware"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/middleware"
)

// NewAuthenticatedRouter creates a router with authentication
func NewAuthenticatedRouter(h *Handler) chi.Router {
	r := chi.NewRouter()

	// Global middleware
	r.Use(chimw.Logger)
	r.Use(chimw.Recoverer)
	r.Use(chimw.Compress(5))
	r.Use(chimw.RealIP)
	r.Use(chimw.RequestID)

	// Security middleware
	r.Use(middleware.SecurityHeaders)
	r.Use(middleware.InputValidation)

	// Rate limiting
	rateLimiter := middleware.NewRateLimiter(10.0, 20) // 10 requests per second, burst of 20
	r.Use(rateLimiter.Middleware)

	// CSRF protection for state-changing operations
	csrfStore := middleware.NewMemoryCSRFStore()
	csrfMiddleware := middleware.NewCSRFMiddleware(csrfStore)
	r.Use(csrfMiddleware.Handler)

	// Public routes (no authentication required)
	r.Group(func(r chi.Router) {
		r.Get("/login", h.handleLogin)
		r.Post("/api/auth/login", h.authService.Login)
		r.Get("/register", h.handleRegister)
		r.Post("/api/auth/register", h.authService.Register)
		r.Get("/forgot-password", h.handleForgotPassword)
		r.Post("/api/auth/forgot-password", h.authService.ForgotPassword)
		r.Get("/reset-password", h.handleResetPassword)
		r.Post("/api/auth/reset-password", h.authService.ResetPassword)
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
	ctx := r.Context()
	
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Parse request body
	var req struct {
		Name       string  `json:"name"`
		Type       string  `json:"type"`
		BuildingID string  `json:"building_id"`
		RoomID     string  `json:"room_id"`
		X          float64 `json:"x"`
		Y          float64 `json:"y"`
		Z          float64 `json:"z"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Validate required fields
	if req.Name == "" || req.Type == "" || req.BuildingID == "" {
		http.Error(w, "Name, type, and building_id are required", http.StatusBadRequest)
		return
	}
	
	// Create equipment using service
	equipment, err := h.services.Equipment.CreateEquipment(ctx, req.Name, req.Type, req.BuildingID, req.RoomID, req.X, req.Y, req.Z)
	if err != nil {
		logger.Error("Failed to create equipment: %v", err)
		http.Error(w, "Failed to create equipment", http.StatusInternalServerError)
		return
	}
	
	// Return created equipment
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(equipment)
}

func (h *Handler) handleUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPut && r.Method != http.MethodPatch {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Extract equipment ID from URL
	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		http.Error(w, "Equipment ID is required", http.StatusBadRequest)
		return
	}
	
	// Parse request body
	var req struct {
		Name string  `json:"name"`
		Type string  `json:"type"`
		X    float64 `json:"x"`
		Y    float64 `json:"y"`
		Z    float64 `json:"z"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Update equipment using service
	equipment, err := h.services.Equipment.UpdateEquipment(ctx, equipmentID, req.Name, req.Type, req.X, req.Y, req.Z)
	if err != nil {
		logger.Error("Failed to update equipment: %v", err)
		http.Error(w, "Failed to update equipment", http.StatusInternalServerError)
		return
	}
	
	// Return updated equipment
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(equipment)
}

func (h *Handler) handleDeleteEquipment(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Extract equipment ID from URL
	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		http.Error(w, "Equipment ID is required", http.StatusBadRequest)
		return
	}
	
	// Delete equipment using service
	if err := h.services.Equipment.DeleteEquipment(ctx, equipmentID); err != nil {
		logger.Error("Failed to delete equipment: %v", err)
		http.Error(w, "Failed to delete equipment", http.StatusInternalServerError)
		return
	}
	
	// Return success response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Equipment deleted successfully",
	})
}

// API handlers placeholders
func (h *Handler) apiBuildingsList(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// Get buildings from service
	buildings, err := h.services.Building.GetBuildings(ctx)
	if err != nil {
		logger.Error("Failed to get buildings: %v", err)
		http.Error(w, "Failed to get buildings", http.StatusInternalServerError)
		return
	}
	
	// Return JSON response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"buildings": buildings,
		"count":     len(buildings),
	})
}

func (h *Handler) apiCreateBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
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
	
	// Create building using service
	building, err := h.services.Building.CreateBuilding(ctx, req.Name)
	if err != nil {
		logger.Error("Failed to create building: %v", err)
		http.Error(w, "Failed to create building", http.StatusInternalServerError)
		return
	}
	
	// Return created building
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(building)
}

func (h *Handler) apiBuildingDetail(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// Extract building ID from URL
	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}
	
	// Get building from service
	building, err := h.services.Building.GetBuilding(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get building: %v", err)
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	
	// Return building details
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(building)
}

func (h *Handler) apiUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPut && r.Method != http.MethodPatch {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Extract building ID from URL
	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}
	
	// Parse request body
	var req struct {
		Name string `json:"name"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Update building using service
	building, err := h.services.Building.UpdateBuilding(ctx, buildingID, req.Name)
	if err != nil {
		logger.Error("Failed to update building: %v", err)
		http.Error(w, "Failed to update building", http.StatusInternalServerError)
		return
	}
	
	// Return updated building
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(building)
}

func (h *Handler) apiDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Extract building ID from URL
	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}
	
	// Delete building using service
	if err := h.services.Building.DeleteBuilding(ctx, buildingID); err != nil {
		logger.Error("Failed to delete building: %v", err)
		http.Error(w, "Failed to delete building", http.StatusInternalServerError)
		return
	}
	
	// Return success response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Building deleted successfully",
	})
}

func (h *Handler) apiEquipmentList(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// Get equipment from service
	equipment, err := h.services.Equipment.GetEquipment(ctx)
	if err != nil {
		logger.Error("Failed to get equipment: %v", err)
		http.Error(w, "Failed to get equipment", http.StatusInternalServerError)
		return
	}
	
	// Return JSON response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"equipment": equipment,
		"count":     len(equipment),
	})
}

func (h *Handler) apiCreateEquipment(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Parse request body
	var req struct {
		Name        string  `json:"name"`
		Type        string  `json:"type"`
		BuildingID  string  `json:"building_id"`
		RoomID      string  `json:"room_id"`
		X           float64 `json:"x"`
		Y           float64 `json:"y"`
		Z           float64 `json:"z"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Validate required fields
	if req.Name == "" || req.Type == "" || req.BuildingID == "" {
		http.Error(w, "Name, type, and building_id are required", http.StatusBadRequest)
		return
	}
	
	// Create equipment using service
	equipment, err := h.services.Equipment.CreateEquipment(ctx, req.Name, req.Type, req.BuildingID, req.RoomID, req.X, req.Y, req.Z)
	if err != nil {
		logger.Error("Failed to create equipment: %v", err)
		http.Error(w, "Failed to create equipment", http.StatusInternalServerError)
		return
	}
	
	// Return created equipment
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(equipment)
}

func (h *Handler) apiEquipmentDetail(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// Extract equipment ID from URL
	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		http.Error(w, "Equipment ID is required", http.StatusBadRequest)
		return
	}
	
	// Get equipment from service
	equipment, err := h.services.Equipment.GetEquipmentByID(ctx, equipmentID)
	if err != nil {
		logger.Error("Failed to get equipment: %v", err)
		http.Error(w, "Equipment not found", http.StatusNotFound)
		return
	}
	
	// Return equipment details
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(equipment)
}

func (h *Handler) apiUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPut && r.Method != http.MethodPatch {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Extract equipment ID from URL
	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		http.Error(w, "Equipment ID is required", http.StatusBadRequest)
		return
	}
	
	// Parse request body
	var req struct {
		Name   string  `json:"name"`
		Type   string  `json:"type"`
		X      float64 `json:"x"`
		Y      float64 `json:"y"`
		Z      float64 `json:"z"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Update equipment using service
	equipment, err := h.services.Equipment.UpdateEquipment(ctx, equipmentID, req.Name, req.Type, req.X, req.Y, req.Z)
	if err != nil {
		logger.Error("Failed to update equipment: %v", err)
		http.Error(w, "Failed to update equipment", http.StatusInternalServerError)
		return
	}
	
	// Return updated equipment
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(equipment)
}

func (h *Handler) apiDeleteEquipment(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Extract equipment ID from URL
	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		http.Error(w, "Equipment ID is required", http.StatusBadRequest)
		return
	}
	
	// Delete equipment using service
	if err := h.services.Equipment.DeleteEquipment(ctx, equipmentID); err != nil {
		logger.Error("Failed to delete equipment: %v", err)
		http.Error(w, "Failed to delete equipment", http.StatusInternalServerError)
		return
	}
	
	// Return success response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Equipment deleted successfully",
	})
}

func (h *Handler) apiSpatialQuery(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Parse request body
	var req struct {
		Query string `json:"query"`
		Limit int    `json:"limit"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	if req.Query == "" {
		http.Error(w, "Query is required", http.StatusBadRequest)
		return
	}
	
	if req.Limit <= 0 {
		req.Limit = 100
	}
	
	// Execute spatial query using service
	results, err := h.services.Search.SpatialQuery(ctx, req.Query, req.Limit)
	if err != nil {
		logger.Error("Failed to execute spatial query: %v", err)
		http.Error(w, "Failed to execute spatial query", http.StatusInternalServerError)
		return
	}
	
	// Return results
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"results": results,
		"count":   len(results),
	})
}

func (h *Handler) apiProximitySearch(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Parse request body
	var req struct {
		X      float64 `json:"x"`
		Y      float64 `json:"y"`
		Z      float64 `json:"z"`
		Radius float64 `json:"radius"`
		Limit  int     `json:"limit"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	if req.Radius <= 0 {
		req.Radius = 10.0
	}
	if req.Limit <= 0 {
		req.Limit = 50
	}
	
	// Execute proximity search using service
	results, err := h.services.Search.ProximitySearch(ctx, req.X, req.Y, req.Z, req.Radius, req.Limit)
	if err != nil {
		logger.Error("Failed to execute proximity search: %v", err)
		http.Error(w, "Failed to execute proximity search", http.StatusInternalServerError)
		return
	}
	
	// Return results
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"results": results,
		"count":   len(results),
	})
}

func (h *Handler) apiImportIFC(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Parse multipart form
	if err := r.ParseMultipartForm(32 << 20); err != nil {
		http.Error(w, "Failed to parse form", http.StatusBadRequest)
		return
	}
	
	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "Failed to get file", http.StatusBadRequest)
		return
	}
	defer file.Close()
	
	// Validate file type
	if !strings.HasSuffix(strings.ToLower(header.Filename), ".ifc") {
		http.Error(w, "Only IFC files are allowed", http.StatusBadRequest)
		return
	}
	
	// Import IFC file using service
	result, err := h.services.Import.ImportIFC(ctx, file, header.Filename)
	if err != nil {
		logger.Error("Failed to import IFC file: %v", err)
		http.Error(w, "Failed to import IFC file", http.StatusInternalServerError)
		return
	}
	
	// Return import result
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *Handler) apiExportBIM(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Parse request body
	var req struct {
		BuildingID string `json:"building_id"`
		Format     string `json:"format"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	if req.BuildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}
	
	if req.Format == "" {
		req.Format = "bim.txt"
	}
	
	// Export BIM data using service
	result, err := h.services.Export.ExportBIM(ctx, req.BuildingID, req.Format)
	if err != nil {
		logger.Error("Failed to export BIM data: %v", err)
		http.Error(w, "Failed to export BIM data", http.StatusInternalServerError)
		return
	}
	
	// Return export result
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *Handler) apiConnectionGraph(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// Extract building ID from URL
	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}
	
	// Get connection graph using service
	graph, err := h.services.Building.GetConnectionGraph(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get connection graph: %v", err)
		http.Error(w, "Failed to get connection graph", http.StatusInternalServerError)
		return
	}
	
	// Return connection graph
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(graph)
}

func (h *Handler) apiCreateConnection(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Parse request body
	var req struct {
		FromEquipmentID string `json:"from_equipment_id"`
		ToEquipmentID   string `json:"to_equipment_id"`
		ConnectionType  string `json:"connection_type"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Validate required fields
	if req.FromEquipmentID == "" || req.ToEquipmentID == "" || req.ConnectionType == "" {
		http.Error(w, "From equipment ID, to equipment ID, and connection type are required", http.StatusBadRequest)
		return
	}
	
	// Create connection using service
	connection, err := h.services.Building.CreateConnection(ctx, req.FromEquipmentID, req.ToEquipmentID, req.ConnectionType)
	if err != nil {
		logger.Error("Failed to create connection: %v", err)
		http.Error(w, "Failed to create connection", http.StatusInternalServerError)
		return
	}
	
	// Return created connection
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(connection)
}

func (h *Handler) apiDeleteConnection(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Extract connection ID from URL
	connectionID := chi.URLParam(r, "id")
	if connectionID == "" {
		http.Error(w, "Connection ID is required", http.StatusBadRequest)
		return
	}
	
	// Delete connection using service
	if err := h.services.Building.DeleteConnection(ctx, connectionID); err != nil {
		logger.Error("Failed to delete connection: %v", err)
		http.Error(w, "Failed to delete connection", http.StatusInternalServerError)
		return
	}
	
	// Return success response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Connection deleted successfully",
	})
}
