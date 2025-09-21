package web

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/search"
	"github.com/arx-os/arxos/pkg/models"
)

// Handler wraps the API services and templates
type Handler struct {
	templates      *Templates
	services       *api.Services
	searchIndexer  *search.DatabaseIndexer
	recentSearches *search.RecentSearches
	authService    *AuthService
}

// NewHandler creates a new web handler
func NewHandler(services *api.Services) (*Handler, error) {
	templates, err := NewTemplates()
	if err != nil {
		return nil, fmt.Errorf("failed to load templates: %w", err)
	}

	// Initialize search indexer
	searchIndexer := search.NewDatabaseIndexer(services.DB, 5*time.Minute)

	// Start indexing in background
	ctx := context.Background()
	if err := searchIndexer.Start(ctx); err != nil {
		logger.Error("Failed to start search indexer: %v", err)
		// Continue without search functionality
	}

	// Initialize authentication service
	jwtSecret := []byte("your-secret-key") // TODO: Load from config
	sessionStore := NewMemorySessionStore(5 * time.Minute)
	userServiceAdapter := &userServiceAdapter{apiUserService: services.User}
	authService := NewAuthService(jwtSecret, sessionStore, userServiceAdapter)

	return &Handler{
		templates:      templates,
		services:       services,
		searchIndexer:  searchIndexer,
		recentSearches: search.NewRecentSearches(100),
		authService:    authService,
	}, nil
}

// Routes returns the Chi router for the web UI
func (h *Handler) Routes() http.Handler {
	return NewRouter(h)
}

// handleIndex serves the home page
func (h *Handler) handleIndex(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	data := PageData{
		Title:     "Dashboard",
		NavActive: "dashboard",
		User:      h.getUser(r),
	}

	if err := h.templates.Render(w, "index", data); err != nil {
		logger.Error("Failed to render index: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleLogin handles login page and authentication
func (h *Handler) handleLogin(w http.ResponseWriter, r *http.Request) {
	data := PageData{
		Title:     "Login",
		NavActive: "",
	}

	if err := h.templates.Render(w, "login", data); err != nil {
		logger.Error("Failed to render login: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleLogout handles user logout
func (h *Handler) handleLogout(w http.ResponseWriter, r *http.Request) {
	// Clear session and redirect
	http.Redirect(w, r, "/login", http.StatusSeeOther)
}

// HandleDashboard handles the dashboard page
func (h *Handler) HandleDashboard(w http.ResponseWriter, r *http.Request) {
	// Get dashboard data (placeholder - would need to implement proper API call)
	var buildings []*models.FloorPlan
	// TODO: Implement proper building service call
	// ctx := r.Context()
	// buildings, err := h.services.Building.GetAllBuildings(ctx)

	data := PageData{
		Title:     "Dashboard",
		NavActive: "dashboard",
		User:      h.getUser(r),
		Content: map[string]interface{}{
			"BuildingCount":   len(buildings),
			"RecentBuildings": buildings,
			"EquipmentCount":  h.getTotalEquipmentCount(buildings),
			"FailedEquipment": h.getFailedEquipmentCount(buildings),
		},
	}

	if err := h.templates.Render(w, "dashboard", data); err != nil {
		logger.Error("Failed to render dashboard: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// HandleBuildingsList handles the buildings list page
func (h *Handler) HandleBuildingsList(w http.ResponseWriter, r *http.Request) {
	// Get buildings data (placeholder - would need to implement proper API call)
	var buildings []*models.FloorPlan
	// TODO: Implement proper building service call
	// ctx := r.Context()
	// buildings, err := h.services.Building.GetAllBuildings(ctx)

	data := PageData{
		Title:     "Buildings",
		NavActive: "buildings",
		User:      h.getUser(r),
		Content: map[string]interface{}{
			"Buildings": buildings,
		},
	}

	if err := h.templates.Render(w, "buildings", data); err != nil {
		logger.Error("Failed to render buildings: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// HandleBuildingFloorPlan handles HTMX requests for ASCII floor plans
func (h *Handler) HandleBuildingFloorPlan(w http.ResponseWriter, r *http.Request) {
	// This would integrate with the new consolidated rendering system
	// to generate ASCII floor plans for the web interface

	buildingID := r.URL.Query().Get("id")
	if buildingID == "" {
		http.Error(w, "Building ID required", http.StatusBadRequest)
		return
	}

	// TODO: Use the new ConsolidatedRenderer to generate ASCII
	asciiFloorPlan := "ASCII floor plan would be generated here using the new rendering system"

	data := map[string]interface{}{
		"Building": map[string]interface{}{
			"ID":   buildingID,
			"Name": "Sample Building",
		},
		"ASCIIFloorPlan": asciiFloorPlan,
	}

	if err := h.templates.RenderFragment(w, "floor_plan", data); err != nil {
		logger.Error("Failed to render floor plan fragment: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// Helper methods

func (h *Handler) getUser(r *http.Request) interface{} {
	// Get user from session/context
	return nil // Placeholder
}

func (h *Handler) getTotalEquipmentCount(buildings []*models.FloorPlan) int {
	total := 0
	for _, building := range buildings {
		total += len(building.Equipment)
	}
	return total
}

func (h *Handler) getFailedEquipmentCount(buildings []*models.FloorPlan) int {
	failed := 0
	for _, building := range buildings {
		for _, equipment := range building.Equipment {
			if equipment.Status == models.StatusFailed {
				failed++
			}
		}
	}
	return failed
}

// userServiceAdapter adapts api.UserService to web.UserService interface
type userServiceAdapter struct {
	apiUserService api.UserService
}

func (a *userServiceAdapter) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	apiUser, err := a.apiUserService.GetUserByEmail(ctx, email)
	if err != nil {
		return nil, err
	}
	return &models.User{
		ID:       apiUser.ID,
		Email:    apiUser.Email,
		FullName: apiUser.Name,
		Role:     apiUser.Role,
		IsActive: apiUser.Active,
	}, nil
}

func (a *userServiceAdapter) GetUserByID(ctx context.Context, id string) (*models.User, error) {
	apiUser, err := a.apiUserService.GetUser(ctx, id)
	if err != nil {
		return nil, err
	}
	return &models.User{
		ID:       apiUser.ID,
		Email:    apiUser.Email,
		FullName: apiUser.Name,
		Role:     apiUser.Role,
		IsActive: apiUser.Active,
	}, nil
}

func (a *userServiceAdapter) ValidateCredentials(ctx context.Context, email, password string) (*models.User, error) {
	// This would need to be implemented in the API UserService or we need to handle auth differently
	return nil, errors.New("credential validation not implemented")
}
