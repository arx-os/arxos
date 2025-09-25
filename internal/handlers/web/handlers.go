package web

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/api/types"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/notifications"
	"github.com/arx-os/arxos/internal/search"
	"github.com/arx-os/arxos/pkg/models"
)

// Handler wraps the API services and templates
type Handler struct {
	templates           *Templates
	services            *types.Services
	searchIndexer       *search.DatabaseIndexer
	recentSearches      *search.RecentSearches
	authService         *AuthService
	notificationService *notifications.NotificationService
	notificationManager *notifications.NotificationManager
}

// NewHandler creates a new web handler
func NewHandler(services *types.Services) (*Handler, error) {
	templates, err := NewTemplates()
	if err != nil {
		return nil, fmt.Errorf("failed to load templates: %w", err)
	}

	// Initialize search indexer
	var searchIndexer *search.DatabaseIndexer
	// Note: Database interface compatibility needs to be addressed
	// searchIndexer := search.NewDatabaseIndexer(services.DB, 5*time.Minute)

	// Initialize authentication service
	jwtSecret := []byte(getJWTSecret())
	sessionStore := NewMemorySessionStore(5 * time.Minute)
	userServiceAdapter := &userServiceAdapter{
		apiUserService: services.User,
		apiAuthService: services.Auth,
	}
	authService := NewAuthService(jwtSecret, sessionStore, userServiceAdapter)

	// Initialize notification service
	notificationService := notifications.NewNotificationService()
	notificationManager := notifications.NewNotificationManager(notificationService)

	return &Handler{
		templates:           templates,
		services:            services,
		searchIndexer:       searchIndexer,
		recentSearches:      search.NewRecentSearches(100),
		authService:         authService,
		notificationService: notificationService,
		notificationManager: notificationManager,
	}, nil
}

// Routes returns the Chi router for the web UI
func (h *Handler) Routes() http.Handler {
	return NewAuthenticatedRouter(h)
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
	buildingsInterface, err := h.services.Building.ListBuildings(ctx, userID, 10, 0)
	if err != nil {
		logger.Error("Failed to get buildings: %v", err)
		buildingsInterface = []interface{}{}
	}

	// Convert interface{} to []*models.FloorPlan
	var buildings []*models.FloorPlan
	for _, buildingInterface := range buildingsInterface {
		if building, ok := buildingInterface.(*models.FloorPlan); ok {
			buildings = append(buildings, building)
		}
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
	buildingsInterface, err := h.services.Building.ListBuildings(ctx, userID, limit, offset)
	if err != nil {
		logger.Error("Failed to list buildings: %v", err)
		buildingsInterface = []interface{}{}
	}

	// Convert interface{} to []*models.FloorPlan
	var buildings []*models.FloorPlan
	for _, buildingInterface := range buildingsInterface {
		if building, ok := buildingInterface.(*models.FloorPlan); ok {
			buildings = append(buildings, building)
		}
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

	// Use the new ConsolidatedRenderer to generate ASCII
	asciiFloorPlan := h.generateASCIIFloorPlan(buildingID)

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

// generateASCIIFloorPlan generates an ASCII representation of a floor plan
func (h *Handler) generateASCIIFloorPlan(buildingID string) string {
	ctx := context.Background()

	// Get building data
	buildingInterface, err := h.services.Building.GetBuilding(ctx, buildingID)
	if err != nil {
		return fmt.Sprintf("Error loading building: %v", err)
	}

	building, ok := buildingInterface.(*models.FloorPlan)
	if !ok {
		return "Error: Invalid building type"
	}

	// Get rooms and equipment
	roomsInterface, err := h.services.Building.ListRooms(ctx, buildingID)
	if err != nil {
		roomsInterface = []interface{}{}
	}

	equipmentInterface, err := h.services.Building.ListEquipment(ctx, buildingID, map[string]interface{}{})
	if err != nil {
		equipmentInterface = []interface{}{}
	}

	// Convert to typed slices
	var rooms []*models.Room
	for _, roomInterface := range roomsInterface {
		if room, ok := roomInterface.(*models.Room); ok {
			rooms = append(rooms, room)
		}
	}

	var equipment []*models.Equipment
	for _, eqInterface := range equipmentInterface {
		if eq, ok := eqInterface.(*models.Equipment); ok {
			equipment = append(equipment, eq)
		}
	}

	// Generate ASCII representation
	return h.renderASCIIFloorPlan(building, rooms, equipment)
}

// renderASCIIFloorPlan creates an ASCII representation of the floor plan
func (h *Handler) renderASCIIFloorPlan(building *models.FloorPlan, rooms []*models.Room, equipment []*models.Equipment) string {
	var output strings.Builder

	// Header
	output.WriteString(fmt.Sprintf("Building: %s (Level %d)\n", building.Name, building.Level))
	output.WriteString(strings.Repeat("=", 50) + "\n")

	// Create a simple grid representation
	gridSize := 40
	grid := make([][]rune, gridSize)
	for i := range grid {
		grid[i] = make([]rune, gridSize)
		for j := range grid[i] {
			grid[i][j] = ' '
		}
	}

	// Place rooms as rectangles
	for i, room := range rooms {
		if i >= 5 { // Limit to first 5 rooms for display
			break
		}

		// Calculate room position (simplified)
		x := (i%3)*12 + 2
		y := (i/3)*8 + 2
		width := 10
		height := 6

		// Draw room boundary
		for dy := 0; dy < height; dy++ {
			for dx := 0; dx < width; dx++ {
				if dy == 0 || dy == height-1 || dx == 0 || dx == width-1 {
					if x+dx < gridSize && y+dy < gridSize {
						grid[y+dy][x+dx] = '#'
					}
				} else {
					if x+dx < gridSize && y+dy < gridSize {
						grid[y+dy][x+dx] = '.'
					}
				}
			}
		}

		// Add room label
		label := room.Name
		if len(label) > 8 {
			label = label[:8]
		}
		for j, char := range label {
			if x+2+j < gridSize && y+1 < gridSize {
				grid[y+1][x+2+j] = char
			}
		}
	}

	// Place equipment as symbols
	equipmentSymbols := map[string]rune{
		"outlet": 'O',
		"switch": 'S',
		"panel":  'P',
		"light":  'L',
		"hvac":   'H',
	}

	for i, eq := range equipment {
		if i >= 10 { // Limit equipment display
			break
		}

		// Calculate equipment position (simplified)
		x := (i%8)*5 + 1
		y := (i/8)*3 + 1

		symbol := 'E' // Default equipment symbol
		if s, exists := equipmentSymbols[eq.Type]; exists {
			symbol = s
		}

		if x < gridSize && y < gridSize {
			grid[y][x] = symbol
		}
	}

	// Render the grid
	for y := 0; y < gridSize; y++ {
		for x := 0; x < gridSize; x++ {
			output.WriteRune(grid[y][x])
		}
		output.WriteRune('\n')
	}

	// Add legend
	output.WriteString("\nLegend:\n")
	output.WriteString("# - Room walls\n")
	output.WriteString(". - Room interior\n")
	output.WriteString("O - Outlet\n")
	output.WriteString("S - Switch\n")
	output.WriteString("P - Panel\n")
	output.WriteString("L - Light\n")
	output.WriteString("H - HVAC\n")
	output.WriteString("E - Equipment\n")

	// Add statistics
	output.WriteString("\nStatistics:\n")
	output.WriteString(fmt.Sprintf("Rooms: %d\n", len(rooms)))
	output.WriteString(fmt.Sprintf("Equipment: %d\n", len(equipment)))

	return output.String()
}

// Helper functions for extracting values from interface{} maps
func getString(m map[string]interface{}, key string) string {
	if val, ok := m[key]; ok {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

func getBool(m map[string]interface{}, key string) bool {
	if val, ok := m[key]; ok {
		if b, ok := val.(bool); ok {
			return b
		}
	}
	return false
}

// userServiceAdapter adapts types.UserService to web.UserService interface
type userServiceAdapter struct {
	apiUserService types.UserService
	apiAuthService types.AuthService
}

func (a *userServiceAdapter) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	apiUserInterface, err := a.apiUserService.GetUserByEmail(ctx, email)
	if err != nil {
		return nil, err
	}

	// Type assert to map
	var apiUser map[string]interface{}
	if userMap, ok := apiUserInterface.(map[string]interface{}); ok {
		apiUser = userMap
	} else {
		return nil, fmt.Errorf("invalid user type")
	}

	return &models.User{
		ID:       getString(apiUser, "id"),
		Email:    getString(apiUser, "email"),
		FullName: getString(apiUser, "name"),
		Role:     getString(apiUser, "role"),
		IsActive: getBool(apiUser, "active"),
	}, nil
}

func (a *userServiceAdapter) GetUserByID(ctx context.Context, id string) (*models.User, error) {
	apiUserInterface, err := a.apiUserService.GetUser(ctx, id)
	if err != nil {
		return nil, err
	}

	// Type assert to map or struct
	var apiUser map[string]interface{}
	if userMap, ok := apiUserInterface.(map[string]interface{}); ok {
		apiUser = userMap
	} else {
		return nil, fmt.Errorf("invalid user type")
	}

	return &models.User{
		ID:       getString(apiUser, "id"),
		Email:    getString(apiUser, "email"),
		FullName: getString(apiUser, "name"),
		Role:     getString(apiUser, "role"),
		IsActive: getBool(apiUser, "active"),
	}, nil
}

func (a *userServiceAdapter) ValidateCredentials(ctx context.Context, email, password string) (*models.User, error) {
	// Use the API AuthService to validate credentials
	authResponseInterface, err := a.apiAuthService.Login(ctx, email, password)
	if err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}

	// Type assert auth response
	var authResponse map[string]interface{}
	if responseMap, ok := authResponseInterface.(map[string]interface{}); ok {
		authResponse = responseMap
	} else {
		return nil, fmt.Errorf("invalid auth response type")
	}

	// Get user details from the auth response
	userInterface, ok := authResponse["user"]
	if !ok {
		return nil, fmt.Errorf("no user in auth response")
	}

	var apiUser map[string]interface{}
	if userMap, ok := userInterface.(map[string]interface{}); ok {
		apiUser = userMap
	} else {
		return nil, fmt.Errorf("invalid user type in auth response")
	}

	return &models.User{
		ID:       getString(apiUser, "id"),
		Email:    getString(apiUser, "email"),
		FullName: getString(apiUser, "name"),
		Role:     getString(apiUser, "role"),
		IsActive: getBool(apiUser, "active"),
	}, nil
}

func (a *userServiceAdapter) CreateUser(ctx context.Context, email, password, name string) (*models.User, error) {
	// Use the API AuthService to register user
	apiUserInterface, err := a.apiAuthService.Register(ctx, email, password, name)
	if err != nil {
		return nil, fmt.Errorf("registration failed: %w", err)
	}

	// Type assert to map
	var apiUser map[string]interface{}
	if userMap, ok := apiUserInterface.(map[string]interface{}); ok {
		apiUser = userMap
	} else {
		return nil, fmt.Errorf("invalid user type")
	}

	return &models.User{
		ID:       getString(apiUser, "id"),
		Email:    getString(apiUser, "email"),
		FullName: getString(apiUser, "name"),
		Role:     getString(apiUser, "role"),
		IsActive: getBool(apiUser, "active"),
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
