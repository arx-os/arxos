package web

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/joelpate/arxos/internal/api"
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/internal/search"
	"github.com/joelpate/arxos/pkg/models"
)

// Handler wraps the API services and templates
type Handler struct {
	templates     *Templates
	services      *api.Services
	searchIndexer *search.DatabaseIndexer
	recentSearches *search.RecentSearches
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

	return &Handler{
		templates:      templates,
		services:       services,
		searchIndexer:  searchIndexer,
		recentSearches: search.NewRecentSearches(100),
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
	switch r.Method {
	case http.MethodGet:
		data := PageData{
			Title: "Login",
		}
		if err := h.templates.Render(w, "login", data); err != nil {
			logger.Error("Failed to render login: %v", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
		}

	case http.MethodPost:
		email := r.FormValue("email")
		password := r.FormValue("password")

		resp, err := h.services.Auth.Login(r.Context(), email, password)
		if err != nil {
			// Return login form with error (HTMX partial)
			data := PageData{
				Error: "Invalid email or password",
			}
			h.templates.RenderFragment(w, "login-form", data)
			return
		}

		// Set auth cookie
		http.SetCookie(w, &http.Cookie{
			Name:     "auth_token",
			Value:    resp.AccessToken,
			Path:     "/",
			HttpOnly: true,
			Secure:   r.TLS != nil,
			SameSite: http.SameSiteLaxMode,
			MaxAge:   86400, // 24 hours
		})

		// HTMX redirect
		w.Header().Set("HX-Redirect", "/")
		w.WriteHeader(http.StatusOK)
	}
}

// handleLogout handles user logout
func (h *Handler) handleLogout(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Clear auth cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "auth_token",
		Value:    "",
		Path:     "/",
		HttpOnly: true,
		MaxAge:   -1,
	})

	// HTMX redirect to login
	w.Header().Set("HX-Redirect", "/login")
	w.WriteHeader(http.StatusOK)
}

// handleBuildings handles the buildings list page
func (h *Handler) handleBuildings(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	// Get query parameters
	search := r.URL.Query().Get("search")
	// sort := r.URL.Query().Get("sort") // TODO: implement sorting
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}

	// Fetch buildings from API
	buildings, err := h.services.Building.ListBuildings(r.Context(), user.ID, 20, (page-1)*20)
	if err != nil {
		logger.Error("Failed to list buildings: %v", err)
		buildings = []*models.FloorPlan{}
	}

	// Filter by search
	if search != "" {
		filtered := []*models.FloorPlan{}
		for _, b := range buildings {
			if strings.Contains(strings.ToLower(b.Name), strings.ToLower(search)) {
				filtered = append(filtered, b)
			}
		}
		buildings = filtered
	}

	// Prepare page data
	content := map[string]interface{}{
		"Buildings":  buildings,
		"Page":       page,
		"HasPages":   len(buildings) == 20,
		"HasPrev":    page > 1,
		"PrevPage":   page - 1,
		"HasNext":    len(buildings) == 20,
		"NextPage":   page + 1,
		"StartItem":  (page-1)*20 + 1,
		"EndItem":    (page-1)*20 + len(buildings),
		"TotalItems": len(buildings), // This would come from API
	}

	// Check if this is an HTMX request
	if r.Header.Get("HX-Request") == "true" {
		// Return only the buildings list
		h.templates.RenderFragment(w, "buildings-list", content)
		return
	}

	// Full page render
	data := PageData{
		Title:     "Buildings",
		NavActive: "buildings",
		User:      user,
		Content:   content,
	}

	if err := h.templates.Render(w, "buildings", data); err != nil {
		logger.Error("Failed to render buildings: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleBuilding handles individual building pages
func (h *Handler) handleBuilding(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	// Extract building ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 3 {
		http.NotFound(w, r)
		return
	}
	buildingID := parts[2]

	switch r.Method {
	case http.MethodGet:
		// Get building details
		building, err := h.services.Building.GetBuilding(r.Context(), buildingID)
		if err != nil {
			http.NotFound(w, r)
			return
		}

		data := PageData{
			Title:     building.Name,
			NavActive: "buildings",
			User:      user,
			Content:   building,
		}

		if err := h.templates.Render(w, "building", data); err != nil {
			logger.Error("Failed to render building: %v", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
		}

	case http.MethodDelete:
		// Delete building
		if err := h.services.Building.DeleteBuilding(r.Context(), buildingID); err != nil {
			http.Error(w, "Failed to delete building", http.StatusInternalServerError)
			return
		}

		// HTMX response - empty means remove the element
		w.WriteHeader(http.StatusOK)

	case http.MethodPut, http.MethodPatch:
		// Update building
		var building models.FloorPlan
		if err := json.NewDecoder(r.Body).Decode(&building); err != nil {
			http.Error(w, "Invalid request", http.StatusBadRequest)
			return
		}

		if err := h.services.Building.UpdateBuilding(r.Context(), &building); err != nil {
			http.Error(w, "Failed to update building", http.StatusInternalServerError)
			return
		}

		// Return updated building fragment
		h.templates.RenderFragment(w, "building-card", building)

	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleNewBuilding handles the new building form
func (h *Handler) handleNewBuilding(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	switch r.Method {
	case http.MethodGet:
		// Return the new building form modal
		h.templates.RenderFragment(w, "building-form", nil)

	case http.MethodPost:
		// Create new building
		building := &models.FloorPlan{
			Name:      r.FormValue("name"),
			Building:  r.FormValue("building"),
			Level:     1,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		if err := h.services.Building.CreateBuilding(r.Context(), building); err != nil {
			data := PageData{
				Error: "Failed to create building",
			}
			h.templates.RenderFragment(w, "form-errors", data)
			return
		}

		// Return new building row for list
		h.templates.RenderFragment(w, "building-row", building)
	}
}

// handleEquipment handles equipment pages
func (h *Handler) handleEquipment(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	data := PageData{
		Title:     "Equipment",
		NavActive: "equipment",
		User:      user,
	}

	if err := h.templates.Render(w, "equipment", data); err != nil {
		logger.Error("Failed to render equipment: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleSettings handles settings page
func (h *Handler) handleSettings(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	data := PageData{
		Title:     "Settings",
		NavActive: "settings",
		User:      user,
	}

	if err := h.templates.Render(w, "settings", data); err != nil {
		logger.Error("Failed to render settings: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleSearch handles HTMX search requests
func (h *Handler) handleSearch(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		w.WriteHeader(http.StatusOK)
		return
	}

	// Perform search across buildings and equipment
	results := []interface{}{}

	// Return search results as HTML fragments
	h.templates.RenderFragment(w, "search-results", results)
}

// handleNotifications handles notification requests
func (h *Handler) handleNotifications(w http.ResponseWriter, r *http.Request) {
	// Get recent notifications
	notifications := []map[string]interface{}{
		{
			"id":      "1",
			"message": "Equipment maintenance due",
			"time":    time.Now().Add(-30 * time.Minute),
		},
	}

	h.templates.RenderFragment(w, "notifications", notifications)
}

// handleUpload handles the PDF upload page
func (h *Handler) handleUpload(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	data := PageData{
		Title:     "Import Building",
		User:      user,
		NavActive: "upload",
	}

	if err := h.templates.Render(w, "upload", data); err != nil {
		logger.Error("Failed to render upload page: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleSSE handles server-sent events for real-time updates
func (h *Handler) handleSSE(w http.ResponseWriter, r *http.Request) {
	// Set headers for SSE
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	// Send periodic updates
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			fmt.Fprintf(w, "event: heartbeat\ndata: %d\n\n", time.Now().Unix())
			w.(http.Flusher).Flush()
		case <-r.Context().Done():
			return
		}
	}
}

// getUser gets the current user from the request
func (h *Handler) getUser(r *http.Request) *api.User {
	cookie, err := r.Cookie("auth_token")
	if err != nil {
		return nil
	}

	claims, err := h.services.Auth.ValidateToken(r.Context(), cookie.Value)
	if err != nil {
		return nil
	}

	// Get user from claims
	user := &api.User{
		ID:    claims.UserID,
		Email: claims.Email,
		Name:  claims.Email, // Would come from user service
		Role:  claims.Role,
	}

	return user
}