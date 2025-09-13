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
	"github.com/joelpate/arxos/internal/common/logger"
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

	// Get all equipment across buildings
	buildings, err := h.services.Building.ListBuildings(r.Context(), user.ID, 100, 0)
	if err != nil {
		logger.Error("Failed to list buildings: %v", err)
		buildings = []*models.FloorPlan{}
	}

	// Collect all equipment
	var allEquipment []*models.Equipment
	equipmentByStatus := map[string]int{
		"normal":       0,
		"needs-repair": 0,
		"failed":       0,
	}

	for _, b := range buildings {
		for i := range b.Equipment {
			allEquipment = append(allEquipment, &b.Equipment[i])
			switch b.Equipment[i].Status {
			case models.StatusNormal:
				equipmentByStatus["normal"]++
			case models.StatusNeedsRepair:
				equipmentByStatus["needs-repair"]++
			case models.StatusFailed:
				equipmentByStatus["failed"]++
			}
		}
	}

	content := map[string]interface{}{
		"Equipment":         allEquipment,
		"TotalCount":        len(allEquipment),
		"NormalCount":       equipmentByStatus["normal"],
		"NeedsRepairCount":  equipmentByStatus["needs-repair"],
		"FailedCount":       equipmentByStatus["failed"],
	}

	// Check if this is an HTMX request
	if r.Header.Get("HX-Request") == "true" {
		h.templates.RenderFragment(w, "equipment-list", content)
		return
	}

	data := PageData{
		Title:     "Equipment",
		NavActive: "equipment",
		User:      user,
		Content:   content,
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

	switch r.Method {
	case http.MethodGet:
		// Get current settings
		settings := map[string]interface{}{
			"EmailNotifications": true,
			"AutoRefresh":        true,
			"RefreshInterval":    30,
			"Theme":              "light",
			"Timezone":           "America/New_York",
		}

		data := PageData{
			Title:     "Settings",
			NavActive: "settings",
			User:      user,
			Content:   settings,
		}

		if err := h.templates.Render(w, "settings", data); err != nil {
			logger.Error("Failed to render settings: %v", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
		}

	case http.MethodPost:
		// Update settings
		emailNotifications := r.FormValue("email_notifications") == "on"
		autoRefresh := r.FormValue("auto_refresh") == "on"
		refreshInterval, _ := strconv.Atoi(r.FormValue("refresh_interval"))
		theme := r.FormValue("theme")
		timezone := r.FormValue("timezone")

		// Save settings (in production, this would go to database)
		logger.Info("Updated settings for user %s: notifications=%v, refresh=%v, interval=%d, theme=%s, tz=%s",
			user.ID, emailNotifications, autoRefresh, refreshInterval, theme, timezone)

		// Return success message
		data := PageData{
			Success: "Settings updated successfully",
		}
		h.templates.RenderFragment(w, "form-success", data)

	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleGlobalSearch handles HTMX global search requests
func (h *Handler) handleGlobalSearch(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		w.WriteHeader(http.StatusOK)
		return
	}

	user := h.getUser(r)
	if user == nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Track recent search
	h.recentSearches.Add(search.SearchQuery{
		Query:     query,
		Timestamp: time.Now(),
		UserID:    user.ID,
	})

	// Search buildings
	buildings, _ := h.services.Building.ListBuildings(r.Context(), user.ID, 100, 0)
	var buildingResults []*models.FloorPlan
	for _, b := range buildings {
		if strings.Contains(strings.ToLower(b.Name), strings.ToLower(query)) ||
		   strings.Contains(strings.ToLower(b.Building), strings.ToLower(query)) {
			buildingResults = append(buildingResults, b)
		}
	}

	// Search equipment
	var equipmentResults []*models.Equipment
	for _, b := range buildings {
		for i := range b.Equipment {
			if strings.Contains(strings.ToLower(b.Equipment[i].Name), strings.ToLower(query)) ||
			   strings.Contains(strings.ToLower(b.Equipment[i].Type), strings.ToLower(query)) {
				equipmentResults = append(equipmentResults, &b.Equipment[i])
			}
		}
	}

	results := map[string]interface{}{
		"Query":            query,
		"BuildingResults":  buildingResults,
		"EquipmentResults": equipmentResults,
		"TotalResults":     len(buildingResults) + len(equipmentResults),
	}

	// Return search results as HTML fragments
	h.templates.RenderFragment(w, "search-results", results)
}

// handleSearchSuggestions handles search autocomplete suggestions
func (h *Handler) handleSearchSuggestions(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" || len(query) < 2 {
		w.WriteHeader(http.StatusOK)
		return
	}

	user := h.getUser(r)
	if user == nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get suggestions from search indexer
	suggestions := []string{}
	// TODO: Implement suggestions from search indexer

	data := map[string]interface{}{
		"Suggestions": suggestions,
	}

	h.templates.RenderFragment(w, "search-suggestions", data)
}

// handleRecentSearches handles recent searches display
func (h *Handler) handleRecentSearches(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get recent searches for this user
	recent := []search.SearchQuery{}
	// TODO: Implement user-filtered recent searches

	data := map[string]interface{}{
		"RecentSearches": recent,
	}

	h.templates.RenderFragment(w, "recent-searches", data)
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

	switch r.Method {
	case http.MethodGet:
		data := PageData{
			Title:     "Import Building",
			User:      user,
			NavActive: "upload",
		}

		if err := h.templates.Render(w, "upload", data); err != nil {
			logger.Error("Failed to render upload page: %v", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
		}

	case http.MethodPost:
		// Parse multipart form (max 32 MB)
		if err := r.ParseMultipartForm(32 << 20); err != nil {
			data := PageData{
				Error: "Failed to parse upload",
			}
			h.templates.RenderFragment(w, "upload-result", data)
			return
		}

		// Get the file
		file, header, err := r.FormFile("file")
		if err != nil {
			data := PageData{
				Error: "No file uploaded",
			}
			h.templates.RenderFragment(w, "upload-result", data)
			return
		}
		defer file.Close()

		// Check file type
		if !strings.HasSuffix(strings.ToLower(header.Filename), ".pdf") {
			data := PageData{
				Error: "Only PDF files are supported",
			}
			h.templates.RenderFragment(w, "upload-result", data)
			return
		}

		// Process the PDF (would call PDF parser here)
		buildingName := r.FormValue("name")
		if buildingName == "" {
			buildingName = strings.TrimSuffix(header.Filename, ".pdf")
		}

		logger.Info("Processing uploaded PDF: %s (size: %d bytes) as building: %s",
			header.Filename, header.Size, buildingName)

		// In production, this would:
		// 1. Save the file temporarily
		// 2. Call the PDF parser
		// 3. Convert to FloorPlan model
		// 4. Save to database
		// 5. Generate ASCII representation

		// Return success result
		data := map[string]interface{}{
			"Success":      "Building imported successfully",
			"BuildingName": buildingName,
			"FileName":     header.Filename,
			"FileSize":     header.Size,
		}
		h.templates.RenderFragment(w, "upload-result", data)

	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
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

// handleFloorPlanViewer handles the interactive floor plan viewer
func (h *Handler) handleFloorPlanViewer(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	// Extract building ID from URL
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 4 {
		http.NotFound(w, r)
		return
	}
	buildingID := parts[2]

	// Get building details
	building, err := h.services.Building.GetBuilding(r.Context(), buildingID)
	if err != nil {
		http.NotFound(w, r)
		return
	}

	data := PageData{
		Title:     fmt.Sprintf("%s - Floor Plan", building.Name),
		NavActive: "buildings",
		User:      user,
		Content:   building,
	}

	if err := h.templates.Render(w, "floor-viewer", data); err != nil {
		logger.Error("Failed to render floor viewer: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// handleFloorPlanSVG generates SVG representation of floor plan
func (h *Handler) handleFloorPlanSVG(w http.ResponseWriter, r *http.Request) {
	// Extract building ID from URL
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 3 {
		http.Error(w, "Invalid building ID", http.StatusBadRequest)
		return
	}
	buildingID := parts[2]

	// Get building from database
	building, err := h.services.Building.GetBuilding(r.Context(), buildingID)
	if err != nil {
		http.NotFound(w, r)
		return
	}

	// Generate SVG (simplified version)
	w.Header().Set("Content-Type", "image/svg+xml")
	fmt.Fprintf(w, `<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
		<rect width="800" height="600" fill="#f0f0f0"/>
		<text x="400" y="300" text-anchor="middle" font-size="24">%s</text>
	</svg>`, building.Name)
}