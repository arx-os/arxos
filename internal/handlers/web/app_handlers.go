package web

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/search"
	"github.com/google/uuid"
)

// handleSettings handles user settings page
func (h *Handler) handleSettings(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	switch r.Method {
	case http.MethodGet:
		// Display settings page
		data := PageData{
			Title:     "Settings",
			NavActive: "settings",
			User:      user,
			Content:   nil,
		}

		if err := h.templates.Render(w, "settings", data); err != nil {
			logger.Error("Failed to render settings: %v", err)
			http.Error(w, "Template error", http.StatusInternalServerError)
		}

	case http.MethodPost:
		// Handle settings update
		if err := r.ParseForm(); err != nil {
			http.Error(w, "Invalid form data", http.StatusBadRequest)
			return
		}

		// Update user preferences (simplified for now)
		updates := make(map[string]interface{})
		if name := r.FormValue("name"); name != "" {
			updates["name"] = name
		}
		if email := r.FormValue("email"); email != "" {
			updates["email"] = email
		}
		if theme := r.FormValue("theme"); theme != "" {
			updates["theme"] = theme
		}

		// TODO: Update user preferences in database via service

		// Redirect back to settings with success message
		http.Redirect(w, r, "/settings?success=1", http.StatusSeeOther)

	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleUpload handles file upload for IFC/PDF files
func (h *Handler) handleUpload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse multipart form (32 MB max memory)
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
	ext := strings.ToLower(filepath.Ext(header.Filename))
	if ext != ".ifc" && ext != ".pdf" {
		http.Error(w, "Only IFC and PDF files are allowed", http.StatusBadRequest)
		return
	}

	// Generate unique filename
	filename := fmt.Sprintf("%s-%s%s",
		uuid.New().String(),
		time.Now().Format("20060102-150405"),
		ext,
	)

	// TODO: Save file to storage backend
	// For now, we'll just log the upload
	logger.Info("File uploaded: %s (original: %s, size: %d bytes)",
		filename, header.Filename, header.Size)

	// Process the file based on type
	var result map[string]interface{}
	if ext == ".ifc" {
		// TODO: Process IFC file through importer
		result = map[string]interface{}{
			"status":  "success",
			"message": "IFC file uploaded and queued for processing",
			"file_id": filename,
		}
	} else if ext == ".pdf" {
		// TODO: Process PDF file through converter
		result = map[string]interface{}{
			"status":  "success",
			"message": "PDF file uploaded and queued for conversion",
			"file_id": filename,
		}
	}

	// Return result
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

// handleGlobalSearch handles global search across all entities
func (h *Handler) handleGlobalSearch(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		http.Error(w, "Search query is required", http.StatusBadRequest)
		return
	}

	ctx := r.Context()

	// Perform search using search indexer
	results, err := h.searchIndexer.Search(ctx, query, 20)
	if err != nil {
		logger.Error("Search failed: %v", err)
		results = []search.Result{}
	}

	// Track search for recent searches
	if h.recentSearches != nil {
		userID := "anonymous" // TODO: Get actual user ID from session
		h.recentSearches.AddSearch(userID, query)
	}

	// Format results for response
	formattedResults := make([]map[string]interface{}, len(results))
	for i, result := range results {
		formattedResults[i] = map[string]interface{}{
			"id":          result.ID,
			"type":        result.Type,
			"name":        result.Name,
			"description": result.Description,
			"score":       result.Score,
			"url":         fmt.Sprintf("/%ss/%s", result.Type, result.ID),
		}
	}

	// Check if this is an HTMX request
	if r.Header.Get("HX-Request") == "true" {
		// Render search results fragment
		data := PageData{
			Content: map[string]interface{}{
				"Query":   query,
				"Results": formattedResults,
				"Count":   len(formattedResults),
			},
		}
		if err := h.templates.RenderFragment(w, "search_results", data); err != nil {
			logger.Error("Failed to render search results: %v", err)
			http.Error(w, "Template error", http.StatusInternalServerError)
		}
		return
	}

	// Return JSON for API requests
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"query":   query,
		"results": formattedResults,
		"count":   len(formattedResults),
	})
}

// handleSearchSuggestions handles autocomplete suggestions for search
func (h *Handler) handleSearchSuggestions(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" || len(query) < 2 {
		json.NewEncoder(w).Encode([]string{})
		return
	}

	ctx := r.Context()

	// Get suggestions from search indexer
	suggestions, err := h.searchIndexer.GetSuggestions(ctx, query, 5)
	if err != nil {
		logger.Error("Failed to get suggestions: %v", err)
		suggestions = []string{}
	}

	// Return suggestions
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(suggestions)
}

// handleRecentSearches returns recent searches for the user
func (h *Handler) handleRecentSearches(w http.ResponseWriter, r *http.Request) {
	userID := "anonymous" // TODO: Get actual user ID from session

	if h.recentSearches == nil {
		json.NewEncoder(w).Encode([]string{})
		return
	}

	// Get recent searches
	searches := h.recentSearches.GetRecentSearches(userID, 10)

	// Return recent searches
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(searches)
}

// handleNotifications handles user notifications
func (h *Handler) handleNotifications(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// TODO: Implement notification system
	notifications := []map[string]interface{}{
		{
			"id":        "1",
			"type":      "info",
			"title":     "System Update",
			"message":   "ArxOS has been updated to version 2.0",
			"timestamp": time.Now().Add(-1 * time.Hour),
			"read":      false,
		},
		{
			"id":        "2",
			"type":      "warning",
			"title":     "Maintenance Scheduled",
			"message":   "HVAC system maintenance scheduled for tomorrow",
			"timestamp": time.Now().Add(-24 * time.Hour),
			"read":      true,
		},
	}

	// Check if this is an HTMX request
	if r.Header.Get("HX-Request") == "true" {
		// Render notifications fragment
		data := PageData{
			Content: map[string]interface{}{
				"Notifications": notifications,
			},
		}
		if err := h.templates.RenderFragment(w, "notifications", data); err != nil {
			logger.Error("Failed to render notifications: %v", err)
			http.Error(w, "Template error", http.StatusInternalServerError)
		}
		return
	}

	// Return JSON for API requests
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(notifications)
}

// handleFloorPlanSVG generates SVG floor plan visualization
func (h *Handler) handleFloorPlanSVG(w http.ResponseWriter, r *http.Request) {
	buildingID := r.URL.Query().Get("building_id")
	floor := r.URL.Query().Get("floor")

	if buildingID == "" {
		http.Error(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	ctx := r.Context()

	// Get building
	building, err := h.services.Building.GetBuilding(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get building %s: %v", buildingID, err)
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}

	// Get rooms for the floor
	rooms, err := h.services.Building.ListRooms(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get rooms: %v", err)
		rooms = []*models.Room{}
	}

	// Generate simple SVG floor plan
	svg := generateSVGFloorPlan(building, rooms, floor)

	// Return SVG
	w.Header().Set("Content-Type", "image/svg+xml")
	w.Header().Set("Cache-Control", "public, max-age=3600")
	io.WriteString(w, svg)
}

// handleSSE handles Server-Sent Events for real-time updates
func (h *Handler) handleSSE(w http.ResponseWriter, r *http.Request) {
	// Set headers for SSE
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Create event stream
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}

	// Send initial connection message
	fmt.Fprintf(w, "event: connected\ndata: {\"status\":\"connected\"}\n\n")
	flusher.Flush()

	// Create ticker for periodic updates
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	// Listen for client disconnect
	clientGone := r.Context().Done()

	for {
		select {
		case <-clientGone:
			logger.Debug("SSE client disconnected")
			return

		case <-ticker.C:
			// Send periodic updates
			// TODO: Send actual updates based on subscriptions
			timestamp := time.Now().Format(time.RFC3339)
			fmt.Fprintf(w, "event: ping\ndata: {\"timestamp\":\"%s\"}\n\n", timestamp)
			flusher.Flush()
		}
	}
}

// Helper function to generate simple SVG floor plan
func generateSVGFloorPlan(building *models.FloorPlan, rooms []*models.Room, floor string) string {
	// Simple SVG generation - in production, use a proper rendering library
	svg := `<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="600" fill="white" stroke="black" stroke-width="2"/>
  <text x="400" y="30" text-anchor="middle" font-size="24" font-weight="bold">%s - Floor %s</text>
`
	svg = fmt.Sprintf(svg, building.Name, floor)

	// Add rooms as rectangles
	for i, room := range rooms {
		x := 50 + (i%4)*180
		y := 60 + (i/4)*120
		roomSVG := fmt.Sprintf(`
  <g>
    <rect x="%d" y="%d" width="160" height="100" fill="lightblue" stroke="black" stroke-width="1"/>
    <text x="%d" y="%d" text-anchor="middle" font-size="14">%s</text>
  </g>`,
			x, y, x+80, y+50, room.Name)
		svg += roomSVG
	}

	svg += "\n</svg>"
	return svg
}