package web

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"strconv"
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
	jwtSecret := []byte(getJWTSecret())
	sessionStore := NewMemorySessionStore(5 * time.Minute)
	userServiceAdapter := &userServiceAdapter{
		apiUserService: services.User,
		apiAuthService: services.Auth,
	}
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

// handleRegister handles user registration page
func (h *Handler) handleRegister(w http.ResponseWriter, r *http.Request) {
	data := PageData{
		Title:     "Register",
		NavActive: "",
	}

	if err := h.templates.Render(w, "register", data); err != nil {
		logger.Error("Failed to render register: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleForgotPassword handles forgot password page
func (h *Handler) handleForgotPassword(w http.ResponseWriter, r *http.Request) {
	data := PageData{
		Title:     "Forgot Password",
		NavActive: "",
	}

	if err := h.templates.Render(w, "forgot-password", data); err != nil {
		logger.Error("Failed to render forgot-password: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleResetPassword handles password reset page
func (h *Handler) handleResetPassword(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")
	if token == "" {
		http.Error(w, "Reset token is required", http.StatusBadRequest)
		return
	}

	data := PageData{
		Title:     "Reset Password",
		NavActive: "",
		Content:   map[string]interface{}{"token": token},
	}

	if err := h.templates.Render(w, "reset-password", data); err != nil {
		logger.Error("Failed to render reset-password: %v", err)
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
	ctx := r.Context()

	// Get user from session
	user := h.getUser(r)
	userID := ""
	if user != nil {
		// Extract user ID from interface
		if u, ok := user.(map[string]interface{}); ok {
			if id, ok := u["id"].(string); ok {
				userID = id
			}
		}
	}

	// Get buildings from service
	buildings, err := h.services.Building.ListBuildings(ctx, userID, 10, 0)
	if err != nil {
		logger.Error("Failed to get buildings: %v", err)
		buildings = []*models.FloorPlan{}
	}

	data := PageData{
		Title:     "Dashboard",
		NavActive: "dashboard",
		User:      user,
		Content: map[string]interface{}{
			"BuildingCount":   len(buildings),
			"RecentBuildings": buildings,
			"EquipmentCount":  h.getTotalEquipmentCount(buildings),
			"FailedEquipment": h.getFailedEquipmentCount(buildings),
		},
		CurrentTime: time.Now(),
	}

	if err := h.templates.Render(w, "dashboard", data); err != nil {
		logger.Error("Failed to render dashboard: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// HandleBuildingsList handles the buildings list page
func (h *Handler) HandleBuildingsList(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Get user from session
	user := h.getUser(r)
	userID := ""
	if user != nil {
		// Extract user ID from interface
		if u, ok := user.(map[string]interface{}); ok {
			if id, ok := u["id"].(string); ok {
				userID = id
			}
		}
	}

	// Get pagination parameters
	limit := 20
	offset := 0
	if pageStr := r.URL.Query().Get("page"); pageStr != "" {
		if page, err := strconv.Atoi(pageStr); err == nil && page > 0 {
			offset = (page - 1) * limit
		}
	}

	// Get buildings from service
	buildings, err := h.services.Building.ListBuildings(ctx, userID, limit, offset)
	if err != nil {
		logger.Error("Failed to list buildings: %v", err)
		buildings = []*models.FloorPlan{}
	}

	data := PageData{
		Title:     "Buildings",
		NavActive: "buildings",
		User:      user,
		Content: map[string]interface{}{
			"Buildings": buildings,
			"Page":      (offset / limit) + 1,
			"HasMore":   len(buildings) == limit,
		},
		CurrentTime: time.Now(),
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

// getJWTSecret returns the JWT secret from environment/config with a safe fallback for development.
func getJWTSecret() string {
	if val := os.Getenv("ARXOS_JWT_SECRET"); val != "" {
		return val
	}
	return "dev-secret-not-for-production"
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
	apiAuthService api.AuthService
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
	// Use the API AuthService to validate credentials
	authResponse, err := a.apiAuthService.Login(ctx, email, password)
	if err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}

	// Get user details from the auth response
	apiUser := authResponse.User
	return &models.User{
		ID:       apiUser.ID,
		Email:    apiUser.Email,
		FullName: apiUser.Name,
		Role:     apiUser.Role,
		IsActive: apiUser.Active,
	}, nil
}

func (a *userServiceAdapter) CreateUser(ctx context.Context, email, password, name string) (*models.User, error) {
	// Use the API AuthService to register user
	apiUser, err := a.apiAuthService.Register(ctx, email, password, name)
	if err != nil {
		return nil, fmt.Errorf("registration failed: %w", err)
	}

	return &models.User{
		ID:       apiUser.ID,
		Email:    apiUser.Email,
		FullName: apiUser.Name,
		Role:     apiUser.Role,
		IsActive: apiUser.Active,
	}, nil
}

func (a *userServiceAdapter) RequestPasswordReset(ctx context.Context, email string) error {
	// Use the API UserService to request password reset
	return a.apiUserService.RequestPasswordReset(ctx, email)
}

func (a *userServiceAdapter) ResetPassword(ctx context.Context, token, newPassword string) error {
	// Use the API UserService to reset password
	return a.apiUserService.ConfirmPasswordReset(ctx, token, newPassword)
}
