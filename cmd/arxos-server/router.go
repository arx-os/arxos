package main

import (
	"encoding/json"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/joelpate/arxos/internal/api"
	"github.com/joelpate/arxos/internal/config"
	authMiddleware "github.com/joelpate/arxos/internal/middleware"
	"github.com/joelpate/arxos/internal/telemetry"
	"github.com/joelpate/arxos/pkg/models"
	
	httpSwagger "github.com/swaggo/http-swagger/v2"
)

// NewChiRouter creates a new chi router with all API routes
func NewChiRouter(cfg *config.Config, services *api.Services) http.Handler {
	r := chi.NewRouter()

	// Create handlers wrapper
	h := &handlers{
		services: services,
		config:   cfg,
	}

	// Global middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Compress(5))
	r.Use(h.corsMiddleware)
	
	// Add telemetry middleware
	r.Use(telemetry.HTTPMiddleware)
	
	// Apply validation middleware
	r.Use(authMiddleware.InputValidation)
	
	// Apply rate limiting middleware with custom limits for auth endpoints
	rateLimiter := authMiddleware.NewIPBasedRateLimiter(100, 200) // 100 req/s, burst 200
	r.Use(rateLimiter.MiddlewareWithCustomLimits(authMiddleware.DefaultRateLimits))
	
	// Apply authentication middleware
	authMw := authMiddleware.NewAuthMiddleware(services.Auth)
	r.Use(authMw.Middleware)

	// Health and ready endpoints
	r.Get("/health", h.handleHealth)
	r.Get("/ready", h.handleReady)
	
	// Observability endpoints
	r.Get("/metrics", h.handleMetrics)
	r.Get("/dashboard", h.handleDashboard)
	
	// API Documentation
	r.Get("/docs/*", httpSwagger.WrapHandler)

	// API v1 routes
	r.Route("/api/v1", func(r chi.Router) {
		r.Get("/", h.handleAPIRoot)
		
		// Auth endpoints
		r.Route("/auth", func(r chi.Router) {
			r.Post("/login", h.handleLogin)
			r.Post("/logout", h.handleLogout)
			r.Post("/register", h.handleRegister)
			r.Post("/refresh", h.handleRefresh)
			r.Post("/password-reset", h.handlePasswordReset)
			r.Post("/password-reset/confirm", h.handlePasswordResetConfirm)
		})
		
		// Building endpoints
		r.Route("/buildings", func(r chi.Router) {
			r.Get("/", h.handleListBuildings)
			r.Post("/", h.handleCreateBuilding)
			
			r.Route("/{buildingID}", func(r chi.Router) {
				r.Get("/", h.handleGetBuilding)
				r.Put("/", h.handleUpdateBuilding)
				r.Delete("/", h.handleDeleteBuilding)
				
				// Building equipment sub-route
				r.Get("/equipment", h.handleGetBuildingEquipment)
			})
		})
		
		// Equipment endpoints
		r.Route("/equipment", func(r chi.Router) {
			r.Get("/", h.handleListEquipment)
			r.Post("/", h.handleCreateEquipment)
			
			r.Route("/{equipmentID}", func(r chi.Router) {
				r.Get("/", h.handleGetEquipment)
				r.Put("/", h.handleUpdateEquipment)
				r.Delete("/", h.handleDeleteEquipment)
			})
		})
		
		// Upload endpoints
		r.Post("/upload/pdf", h.handlePDFUpload)
		
		// Organization endpoints
		r.Route("/organizations", func(r chi.Router) {
			r.Get("/", h.handleListOrganizations)
			r.Post("/", h.handleCreateOrganization)
			
			r.Route("/{orgID}", func(r chi.Router) {
				r.Get("/", h.handleGetOrganization)
				r.Put("/", h.handleUpdateOrganization)
				r.Delete("/", h.handleDeleteOrganization)
				
				// Organization sub-resources
				r.Route("/members", func(r chi.Router) {
					r.Get("/", h.handleGetOrganizationMembers)
					r.Post("/", h.handleAddOrganizationMember)
					r.Delete("/{userID}", h.handleRemoveOrganizationMember)
				})
				
				r.Post("/invite", h.handleSendOrganizationInvite)
			})
		})
	})

	return r
}

// Building handlers with proper chi path parameters

func (h *handlers) handleListBuildings(w http.ResponseWriter, r *http.Request) {
	h.handleBuildings(w, r)
}

func (h *handlers) handleCreateBuilding(w http.ResponseWriter, r *http.Request) {
	h.handleBuildings(w, r)
}

func (h *handlers) handleGetBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "buildingID")
	
	building, err := h.services.Building.GetBuilding(r.Context(), buildingID)
	if err != nil {
		respondError(w, http.StatusNotFound, "Building not found")
		return
	}
	
	respondJSON(w, http.StatusOK, building)
}

func (h *handlers) handleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "buildingID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	var building models.FloorPlan
	if err := json.NewDecoder(r.Body).Decode(&building); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	building.ID = buildingID
	if err := h.services.Building.UpdateBuilding(r.Context(), &building); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusOK, building)
}

func (h *handlers) handleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "buildingID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	if err := h.services.Building.DeleteBuilding(r.Context(), buildingID); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	w.WriteHeader(http.StatusNoContent)
}

func (h *handlers) handleGetBuildingEquipment(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "buildingID")
	
	equipment, err := h.services.Building.ListEquipment(r.Context(), buildingID, nil)
	if err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusOK, equipment)
}

// Equipment handlers with proper chi path parameters

func (h *handlers) handleListEquipment(w http.ResponseWriter, r *http.Request) {
	h.handleEquipment(w, r)
}

func (h *handlers) handleCreateEquipment(w http.ResponseWriter, r *http.Request) {
	h.handleEquipment(w, r)
}

func (h *handlers) handleGetEquipment(w http.ResponseWriter, r *http.Request) {
	equipmentID := chi.URLParam(r, "equipmentID")
	
	equipment, err := h.services.Building.GetEquipment(r.Context(), equipmentID)
	if err != nil {
		respondError(w, http.StatusNotFound, "Equipment not found")
		return
	}
	
	respondJSON(w, http.StatusOK, equipment)
}

func (h *handlers) handleUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	equipmentID := chi.URLParam(r, "equipmentID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	var equipment models.Equipment
	if err := json.NewDecoder(r.Body).Decode(&equipment); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	equipment.ID = equipmentID
	if err := h.services.Building.UpdateEquipment(r.Context(), &equipment); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusOK, equipment)
}

func (h *handlers) handleDeleteEquipment(w http.ResponseWriter, r *http.Request) {
	equipmentID := chi.URLParam(r, "equipmentID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	if err := h.services.Building.DeleteEquipment(r.Context(), equipmentID); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	w.WriteHeader(http.StatusNoContent)
}

// Organization handlers with proper chi path parameters

func (h *handlers) handleListOrganizations(w http.ResponseWriter, r *http.Request) {
	user := authMiddleware.GetUser(r)
	userID := ""
	if user != nil {
		userID = user.ID
	}
	
	orgs, err := h.services.Organization.ListOrganizations(r.Context(), userID)
	if err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusOK, orgs)
}

func (h *handlers) handleCreateOrganization(w http.ResponseWriter, r *http.Request) {
	user := authMiddleware.GetUser(r)
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	// Only admins can create organizations
	if user.Role != "admin" {
		respondError(w, http.StatusForbidden, "Admin role required")
		return
	}
	
	var org models.Organization
	if err := json.NewDecoder(r.Body).Decode(&org); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	if org.Name == "" {
		respondError(w, http.StatusBadRequest, "Organization name is required")
		return
	}
	
	// Create organization with current user as owner
	if err := h.services.Organization.CreateOrganization(r.Context(), &org, user.ID); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusCreated, org)
}

func (h *handlers) handleGetOrganization(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "orgID")
	
	org, err := h.services.Organization.GetOrganization(r.Context(), orgID)
	if err != nil {
		respondError(w, http.StatusNotFound, "Organization not found")
		return
	}
	
	// Check if organization is active
	if org.Status != "active" {
		respondError(w, http.StatusForbidden, "Organization is not active")
		return
	}
	
	respondJSON(w, http.StatusOK, org)
}

func (h *handlers) handleUpdateOrganization(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "orgID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	// Check if user is admin of this organization
	members, err := h.services.Organization.GetMembers(r.Context(), orgID)
	if err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	isAdmin := false
	for _, member := range members {
		if member.UserID == user.ID && (member.Role == models.RoleAdmin || member.Role == models.RoleOwner) {
			isAdmin = true
			break
		}
	}
	
	if !isAdmin {
		respondError(w, http.StatusForbidden, "Organization admin role required")
		return
	}
	
	var update models.Organization
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	update.ID = orgID
	
	if err := h.services.Organization.UpdateOrganization(r.Context(), &update); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusOK, update)
}

func (h *handlers) handleDeleteOrganization(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "orgID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	// Only system admins can delete organizations
	if user.Role != "admin" {
		respondError(w, http.StatusForbidden, "System admin role required")
		return
	}
	
	if err := h.services.Organization.DeleteOrganization(r.Context(), orgID); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	w.WriteHeader(http.StatusNoContent)
}

func (h *handlers) handleGetOrganizationMembers(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "orgID")
	
	members, err := h.services.Organization.GetMembers(r.Context(), orgID)
	if err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusOK, members)
}

func (h *handlers) handleAddOrganizationMember(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "orgID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	var req struct {
		UserID string `json:"user_id"`
		Role   string `json:"role"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	if err := h.services.Organization.AddMember(r.Context(), orgID, req.UserID, models.Role(req.Role)); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusCreated, map[string]interface{}{
		"success": true,
		"org_id":  orgID,
		"user_id": req.UserID,
		"role":    req.Role,
	})
}

func (h *handlers) handleRemoveOrganizationMember(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "orgID")
	userID := chi.URLParam(r, "userID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	if err := h.services.Organization.RemoveMember(r.Context(), orgID, userID); err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	w.WriteHeader(http.StatusNoContent)
}

func (h *handlers) handleSendOrganizationInvite(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "orgID")
	user := authMiddleware.GetUser(r)
	
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	var invite struct {
		Email string `json:"email"`
		Role  string `json:"role"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&invite); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	invitation, err := h.services.Organization.CreateInvitation(
		r.Context(), 
		orgID, 
		invite.Email, 
		models.Role(invite.Role),
		user.ID,
	)
	
	if err != nil {
		respondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Invitation sent",
		"data": map[string]string{
			"id":      invitation.ID,
			"email":   invitation.Email,
			"org_id":  orgID,
			"role":    invite.Role,
		},
	})
}