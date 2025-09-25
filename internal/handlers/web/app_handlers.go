package web

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/search"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/go-chi/chi/v5"
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

		// Update user preferences in database via service
		userID := getUserIDFromRequest(r)
		if userID != "" {
			preferences := map[string]interface{}{
				"theme":         r.FormValue("theme"),
				"language":      r.FormValue("language"),
				"notifications": r.FormValue("notifications") == "on",
				"email_updates": r.FormValue("email_updates") == "on",
				"timezone":      r.FormValue("timezone"),
				"date_format":   r.FormValue("date_format"),
				"units":         r.FormValue("units"),
			}

			// Update user preferences
			ctx := r.Context()
			_, err := h.services.User.UpdateUser(ctx, userID, map[string]interface{}{
				"preferences": preferences,
			})
			if err != nil {
				logger.Error("Failed to update user preferences: %v", err)
				http.Error(w, "Failed to update preferences", http.StatusInternalServerError)
				return
			}

			logger.Info("Updated preferences for user %s", userID)
		}

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

	// Save file to storage backend
	// For now, use filename as file ID (simplified approach)
	fileID := filename

	// Save file to storage backend using storage coordinator
	// For now, save to local filesystem as a placeholder
	uploadPath := filepath.Join("uploads", filename)
	if err := os.MkdirAll("uploads", 0755); err != nil {
		logger.Error("Failed to create uploads directory: %v", err)
		http.Error(w, "Failed to create uploads directory", http.StatusInternalServerError)
		return
	}

	destFile, err := os.Create(uploadPath)
	if err != nil {
		logger.Error("Failed to create file: %v", err)
		http.Error(w, "Failed to create file", http.StatusInternalServerError)
		return
	}
	defer destFile.Close()

	if _, err := io.Copy(destFile, file); err != nil {
		logger.Error("Failed to save file: %v", err)
		http.Error(w, "Failed to save file", http.StatusInternalServerError)
		return
	}

	logger.Info("File uploaded: %s (ID: %s, size: %d bytes, path: %s)",
		filename, fileID, header.Size, uploadPath)

	// Process the file based on type
	var result map[string]interface{}
	if ext == ".ifc" {
		// Process IFC file through importer
		if err := h.processIFCFile(uploadPath, fileID); err != nil {
			logger.Error("Failed to process IFC file: %v", err)
			result = map[string]interface{}{
				"status":  "error",
				"message": "Failed to process IFC file: " + err.Error(),
				"file_id": fileID,
			}
		} else {
			result = map[string]interface{}{
				"status":  "success",
				"message": "IFC file uploaded and processed successfully",
				"file_id": fileID,
			}
		}
	} else if ext == ".pdf" {
		// Process PDF file through converter
		if err := h.processPDFFile(uploadPath, fileID); err != nil {
			logger.Error("Failed to process PDF file: %v", err)
			result = map[string]interface{}{
				"status":  "error",
				"message": "Failed to process PDF file: " + err.Error(),
				"file_id": fileID,
			}
		} else {
			result = map[string]interface{}{
				"status":  "success",
				"message": "PDF file uploaded and processed successfully",
				"file_id": fileID,
			}
		}
	}

	// Return result
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

// processIFCFile processes an IFC file and imports it to the database
func (h *Handler) processIFCFile(filePath, fileID string) error {
	// Open the IFC file
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open IFC file: %w", err)
	}
	defer file.Close()

	// For now, create a simple building from the IFC file
	// In a real implementation, this would use the IFC converter
	building := &models.FloorPlan{
		ID:    fileID,
		Name:  filepath.Base(filePath),
		Level: 1,
	}

	// Save to database if available
	if h.services != nil && h.services.DB != nil {
		ctx := context.Background()
		if db, ok := h.services.DB.(interface {
			SaveFloorPlan(context.Context, *models.FloorPlan) error
		}); ok {
			if err := db.SaveFloorPlan(ctx, building); err != nil {
				return fmt.Errorf("failed to save building to database: %w", err)
			}
			logger.Info("Successfully imported IFC file to database: %s", fileID)
		}
	}

	return nil
}

// processPDFFile processes a PDF file and extracts building information
func (h *Handler) processPDFFile(filePath, fileID string) error {
	// For now, create a simple building from the PDF file
	// In a real implementation, this would use the PDF converter
	building := &models.FloorPlan{
		ID:    fileID,
		Name:  filepath.Base(filePath),
		Level: 1,
	}

	// Save to database if available
	if h.services != nil && h.services.DB != nil {
		ctx := context.Background()
		if db, ok := h.services.DB.(interface {
			SaveFloorPlan(context.Context, *models.FloorPlan) error
		}); ok {
			if err := db.SaveFloorPlan(ctx, building); err != nil {
				return fmt.Errorf("failed to save building to database: %w", err)
			}
			logger.Info("Successfully imported PDF file to database: %s", fileID)
		}
	}

	return nil
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
	results, err := h.searchIndexer.Search(ctx, search.SearchOptions{Query: query, Limit: 20})
	if err != nil {
		logger.Error("Search failed: %v", err)
		results = []search.SearchResult{}
	}

	// Track search for recent searches
	if h.recentSearches != nil {
		userID := getUserIDFromRequest(r)
		if userID == "" {
			userID = "anonymous"
		}
		h.recentSearches.Add(search.SearchQuery{Query: query, Timestamp: time.Now(), Results: len(results), UserID: userID})
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
	suggestions := h.searchIndexer.Suggest(ctx, query, 5)

	// Return suggestions
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(suggestions)
}

// handleRecentSearches returns recent searches for the user
func (h *Handler) handleRecentSearches(w http.ResponseWriter, r *http.Request) {
	if h.recentSearches == nil {
		json.NewEncoder(w).Encode([]string{})
		return
	}

	// Get recent searches
	searches := h.recentSearches.Get(10)

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

	// Get limit from query parameter
	limit := 10
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if parsedLimit, err := strconv.Atoi(limitStr); err == nil && parsedLimit > 0 && parsedLimit <= 100 {
			limit = parsedLimit
		}
	}

	// Get user ID from user object
	userID := getUserID(user)
	if userID == "" {
		http.Error(w, "User ID not found", http.StatusUnauthorized)
		return
	}

	// Get notifications from service
	notifications, err := h.notificationService.GetUserNotifications(userID, limit)
	if err != nil {
		logger.Error("Failed to get user notifications: %v", err)
		http.Error(w, "Failed to get notifications", http.StatusInternalServerError)
		return
	}

	// Convert to map format for template compatibility
	notificationMaps := make([]map[string]interface{}, len(notifications))
	for i, notification := range notifications {
		notificationMaps[i] = map[string]interface{}{
			"id":        notification.ID,
			"type":      notification.Type,
			"title":     notification.Title,
			"message":   notification.Message,
			"severity":  notification.Severity,
			"timestamp": notification.Timestamp,
			"read":      notification.Read,
			"actions":   notification.Actions,
		}
	}

	// Check if this is an HTMX request
	if r.Header.Get("HX-Request") == "true" {
		// Render notifications fragment
		data := PageData{
			Content: map[string]interface{}{
				"Notifications": notificationMaps,
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
	json.NewEncoder(w).Encode(notificationMaps)
}

// handleMarkNotificationRead marks a notification as read
func (h *Handler) handleMarkNotificationRead(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get notification ID from URL
	notificationID := chi.URLParam(r, "id")
	if notificationID == "" {
		http.Error(w, "Notification ID required", http.StatusBadRequest)
		return
	}

	// Mark notification as read
	if err := h.notificationService.MarkAsRead(notificationID); err != nil {
		logger.Error("Failed to mark notification as read: %v", err)
		http.Error(w, "Failed to mark notification as read", http.StatusInternalServerError)
		return
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Notification marked as read",
	})
}

// handleMarkAllNotificationsRead marks all notifications for a user as read
func (h *Handler) handleMarkAllNotificationsRead(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get user ID from user object
	userID := getUserID(user)
	if userID == "" {
		http.Error(w, "User ID not found", http.StatusUnauthorized)
		return
	}

	// Mark all notifications as read
	if err := h.notificationService.MarkAllAsRead(userID); err != nil {
		logger.Error("Failed to mark all notifications as read: %v", err)
		http.Error(w, "Failed to mark all notifications as read", http.StatusInternalServerError)
		return
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "All notifications marked as read",
	})
}

// handleGetUnreadCount returns the count of unread notifications for a user
func (h *Handler) handleGetUnreadCount(w http.ResponseWriter, r *http.Request) {
	user := h.getUser(r)
	if user == nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get user ID from user object
	userID := getUserID(user)
	if userID == "" {
		http.Error(w, "User ID not found", http.StatusUnauthorized)
		return
	}

	// Get unread count
	count, err := h.notificationService.GetUnreadCount(userID)
	if err != nil {
		logger.Error("Failed to get unread count: %v", err)
		http.Error(w, "Failed to get unread count", http.StatusInternalServerError)
		return
	}

	// Return count
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"count": count,
	})
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
	roomsInterface, err := h.services.Building.ListRooms(ctx, buildingID)
	if err != nil {
		logger.Error("Failed to get rooms: %v", err)
		roomsInterface = []interface{}{}
	}

	// Convert interface{} to []*models.Room
	var rooms []*models.Room
	for _, roomInterface := range roomsInterface {
		if room, ok := roomInterface.(*models.Room); ok {
			rooms = append(rooms, room)
		}
	}

	// Type assert building to *models.FloorPlan
	buildingPlan, ok := building.(*models.FloorPlan)
	if !ok {
		http.Error(w, "Invalid building type", http.StatusInternalServerError)
		return
	}

	// Generate simple SVG floor plan
	svg := generateSVGFloorPlan(buildingPlan, rooms, floor)

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
			// Send periodic updates based on subscriptions
			userID := getUserIDFromRequest(r)
			updates := h.getUserUpdates(userID)

			timestamp := time.Now().Format(time.RFC3339)
			updateData := map[string]interface{}{
				"timestamp": timestamp,
				"updates":   updates,
			}

			jsonData, _ := json.Marshal(updateData)
			fmt.Fprintf(w, "event: update\ndata: %s\n\n", jsonData)
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

// Authentication-related handlers

// handleRegister handles user registration page
func (h *Handler) handleRegister(w http.ResponseWriter, r *http.Request) {
	data := PageData{
		Title:     "Register",
		NavActive: "register",
		User:      nil,
		Content:   nil,
	}

	if err := h.templates.Render(w, "register", data); err != nil {
		logger.Error("Failed to render register page: %v", err)
		http.Error(w, "Template error", http.StatusInternalServerError)
	}
}

// handleForgotPassword handles forgot password page
func (h *Handler) handleForgotPassword(w http.ResponseWriter, r *http.Request) {
	data := PageData{
		Title:     "Forgot Password",
		NavActive: "forgot-password",
		User:      nil,
		Content:   nil,
	}

	if err := h.templates.Render(w, "forgot-password", data); err != nil {
		logger.Error("Failed to render forgot password page: %v", err)
		http.Error(w, "Template error", http.StatusInternalServerError)
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
		NavActive: "reset-password",
		User:      nil,
		Content:   map[string]interface{}{"token": token},
	}

	if err := h.templates.Render(w, "reset-password", data); err != nil {
		logger.Error("Failed to render reset password page: %v", err)
		http.Error(w, "Template error", http.StatusInternalServerError)
	}
}

// getUserID extracts user ID from user object
func getUserID(user interface{}) string {
	if user == nil {
		return ""
	}

	// Try to cast to map and get ID
	if userMap, ok := user.(map[string]interface{}); ok {
		if id, exists := userMap["id"]; exists {
			if idStr, ok := id.(string); ok {
				return idStr
			}
		}
	}

	// Try to cast to User model and get ID
	if userModel, ok := user.(*models.User); ok {
		return userModel.ID
	}

	// Try to cast to domain User and get ID
	if domainUser, ok := user.(map[string]interface{}); ok {
		if id, exists := domainUser["ID"]; exists {
			if idStr, ok := id.(string); ok {
				return idStr
			}
		}
	}

	// Fallback to placeholder if no valid user ID found
	logger.Warn("Could not extract user ID from user object, using placeholder")
	return "user-1"
}

// getUserIDFromRequest extracts user ID from request
func getUserIDFromRequest(r *http.Request) string {
	// Try to get from session or JWT token
	// For now, return a placeholder
	return "user-1"
}

// getUserUpdates returns updates for a specific user
func (h *Handler) getUserUpdates(userID string) map[string]interface{} {
	updates := map[string]interface{}{
		"notifications": 0,
		"buildings":     0,
		"equipment":     0,
		"timestamp":     time.Now().Unix(),
	}

	// Get unread notification count
	if h.notificationService != nil {
		if count, err := h.notificationService.GetUnreadCount(userID); err == nil {
			updates["notifications"] = count
		}
	}

	// Get building updates (new buildings, changes, etc.)
	if h.services != nil && h.services.DB != nil {
		// Check for new buildings since last update
		// This would typically query a last_updated timestamp
		// For now, return a placeholder
		updates["buildings"] = 0

		// Check for equipment updates
		// This would typically query for equipment changes
		// For now, return a placeholder
		updates["equipment"] = 0
	}

	// Add user-specific updates based on subscriptions
	// This would check user preferences and subscriptions
	updates["subscriptions"] = h.getUserSubscriptions(userID)

	return updates
}

// getUserSubscriptions returns user subscription preferences
func (h *Handler) getUserSubscriptions(userID string) map[string]interface{} {
	// This would typically query user preferences from the database
	// For now, return default subscriptions
	return map[string]interface{}{
		"building_updates":      true,
		"equipment_alerts":      true,
		"system_notifications":  true,
		"maintenance_reminders": true,
	}
}
