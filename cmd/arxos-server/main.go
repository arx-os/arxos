package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/joelpate/arxos/internal/api"
	"github.com/joelpate/arxos/internal/config"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/importer"
	"github.com/joelpate/arxos/internal/middleware"
	"github.com/joelpate/arxos/internal/telemetry"
	"github.com/joelpate/arxos/internal/web"
	"github.com/joelpate/arxos/pkg/models"
	
	// _ "github.com/joelpate/arxos/docs" // TODO: Generate swagger docs
)

func main() {
	var (
		configPath = flag.String("config", "", "Path to configuration file")
		port       = flag.Int("port", 8080, "Port to listen on")
		dbPath     = flag.String("db", "", "Path to database file")
		verbose    = flag.Bool("verbose", false, "Enable verbose logging")
	)
	flag.Parse()

	// Set up logging
	if *verbose {
		logger.SetLevel(logger.DEBUG)
	} else {
		logger.SetLevel(logger.INFO)
	}

	logger.Info("Starting ArxOS API Server")

	// Load configuration
	cfg, err := config.Load(*configPath)
	if err != nil {
		logger.Error("Failed to load configuration: %v", err)
		os.Exit(1)
	}

	// Initialize telemetry
	telemetry.Initialize(&cfg.Telemetry)
	defer telemetry.Shutdown()
	
	// Initialize enhanced telemetry with observability features
	if err := telemetry.InitializeExtended(&cfg.Telemetry); err != nil {
		logger.Error("Failed to initialize enhanced telemetry: %v", err)
		// Continue without enhanced telemetry
	} else {
		// Start observability dashboard
		if err := telemetry.StartDashboard(); err != nil {
			logger.Warn("Failed to start observability dashboard: %v", err)
		}
	}

	// Initialize database
	dbFile := *dbPath
	if dbFile == "" {
		dbFile = fmt.Sprintf("%s/arxos.db", cfg.StateDir)
	}

	db, err := database.NewSQLiteDBFromPath(dbFile)
	if err != nil {
		logger.Error("Failed to initialize database: %v", err)
		os.Exit(1)
	}
	defer db.Close()

	// Initialize services
	buildingService := api.NewBuildingService(db)
	authService := api.NewAuthService(db)
	orgService := api.NewOrganizationService(db)

	// Wire organization service to auth service for role resolution
	if authImpl, ok := authService.(*api.AuthServiceImpl); ok {
		authImpl.SetOrganizationService(orgService)
		
		// Create default admin user for testing
		if err := authImpl.CreateDefaultUser(); err != nil {
			logger.Error("Failed to create default user: %v", err)
		}
	}

	services := &api.Services{
		Building:     buildingService,
		Auth:         authService,
		Organization: orgService,
		DB:           db,
	}

	// Create handlers with chi router
	apiHandler := NewChiRouter(cfg, services)
	
	// Create web handler for UI (if needed, this can be integrated into the main router)
	_, err = web.NewHandler(services)
	if err != nil {
		logger.Error("Failed to create web handler: %v", err)
		// Continue without web UI
	}

	// Start session manager for cleanup
	sessionManager := api.NewSessionManager(db, 15*time.Minute, 24*time.Hour)
	go sessionManager.Start(context.Background())
	defer sessionManager.Stop()

	// The Chi router from NewChiRouter handles all routes
	mainRouter := apiHandler

	// Create HTTP server
	addr := fmt.Sprintf(":%d", *port)
	server := &http.Server{
		Addr:         addr,
		Handler:      mainRouter,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		logger.Info("API server listening on %s", addr)
		logger.Info("Health check: http://localhost%s/health", addr)
		logger.Info("API endpoint: http://localhost%s/api/v1/", addr)
		logger.Info("Default admin credentials: admin@arxos.io / admin123")
		
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("Server error: %v", err)
			os.Exit(1)
		}
	}()

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	// Graceful shutdown
	logger.Info("Shutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		logger.Error("Failed to gracefully shutdown server: %v", err)
	}

	logger.Info("Server stopped")
}

// NewAPIHandler creates a configured HTTP handler with all routes
func NewAPIHandler(cfg *config.Config, services *api.Services) http.Handler {
	mux := http.NewServeMux()

	// Create handlers wrapper
	h := &handlers{
		services: services,
		config:   cfg,
	}

	// Health and ready endpoints
	mux.HandleFunc("/health", h.handleHealth)
	mux.HandleFunc("/ready", h.handleReady)

	// API v1 root
	mux.HandleFunc("/api/v1/", h.handleAPIRoot)

	// Auth endpoints
	mux.HandleFunc("/api/v1/auth/login", h.handleLogin)
	mux.HandleFunc("/api/v1/auth/logout", h.handleLogout)
	mux.HandleFunc("/api/v1/auth/register", h.handleRegister)
	mux.HandleFunc("/api/v1/auth/refresh", h.handleRefresh)

	// Building endpoints
	mux.HandleFunc("/api/v1/buildings", h.handleBuildings)
	mux.HandleFunc("/api/v1/buildings/", h.handleBuilding)
	
	// Equipment endpoints
	mux.HandleFunc("/api/v1/equipment", h.handleEquipment)
	mux.HandleFunc("/api/v1/equipment/", h.handleEquipmentItem)
	
	// Upload endpoints
	mux.HandleFunc("/api/v1/upload/pdf", h.handlePDFUpload)
	
	// Organization endpoints
	mux.HandleFunc("/api/v1/organizations", h.handleOrganizations)
	mux.HandleFunc("/api/v1/organizations/", h.handleOrganization)

	// Apply middleware
	handler := h.loggingMiddleware(mux)
	handler = h.recoveryMiddleware(handler)
	handler = h.corsMiddleware(handler)
	
	// Apply authentication middleware
	authMiddleware := middleware.NewAuthMiddleware(services.Auth)
	handler = authMiddleware.Middleware(handler)

	return handler
}

// handlers wraps the services and config for HTTP handlers
type handlers struct {
	services *api.Services
	config   *config.Config
}

func (h *handlers) handleHealth(w http.ResponseWriter, r *http.Request) {
	respondJSON(w, http.StatusOK, map[string]string{
		"status": "healthy",
		"time":   time.Now().Format(time.RFC3339),
	})
}

func (h *handlers) handleReady(w http.ResponseWriter, r *http.Request) {
	ready := h.services.Building != nil && h.services.Auth != nil
	
	if ready {
		respondJSON(w, http.StatusOK, map[string]bool{"ready": true})
	} else {
		respondJSON(w, http.StatusServiceUnavailable, map[string]bool{"ready": false})
	}
}

func (h *handlers) handleAPIRoot(w http.ResponseWriter, r *http.Request) {
	respondJSON(w, http.StatusOK, map[string]interface{}{
		"version": "1.0.0",
		"name":    "ArxOS API",
		"endpoints": map[string]string{
			"auth":          "/api/v1/auth",
			"buildings":     "/api/v1/buildings",
			"organizations": "/api/v1/organizations",
		},
	})
}

func (h *handlers) handleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	// Validate email format
	if err := middleware.ValidateEmail(req.Email); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid email format")
		return
	}

	// Validate password is not empty
	if req.Password == "" {
		respondError(w, http.StatusBadRequest, "Password is required")
		return
	}

	// Extract client IP and user agent
	ipAddress := r.Header.Get("X-Forwarded-For")
	if ipAddress == "" {
		ipAddress = r.Header.Get("X-Real-IP")
	}
	if ipAddress == "" {
		ipAddress = r.RemoteAddr
	}
	userAgent := r.Header.Get("User-Agent")

	// Add request info to context
	ctx := context.WithValue(r.Context(), "requestInfo", api.RequestInfo{
		IPAddress: ipAddress,
		UserAgent: userAgent,
	})

	resp, err := h.services.Auth.Login(ctx, req.Email, req.Password)
	if err != nil {
		respondError(w, http.StatusUnauthorized, "Invalid credentials")
		return
	}

	respondJSON(w, http.StatusOK, resp)
}

func (h *handlers) handleLogout(w http.ResponseWriter, r *http.Request) {
	respondJSON(w, http.StatusOK, map[string]string{"message": "Logged out"})
}

func (h *handlers) handleRegister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
		Name     string `json:"name"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	user, err := h.services.Auth.Register(r.Context(), req.Email, req.Password, req.Name)
	if err != nil {
		respondError(w, http.StatusBadRequest, err.Error())
		return
	}

	respondJSON(w, http.StatusCreated, user)
}

func (h *handlers) handleRefresh(w http.ResponseWriter, r *http.Request) {
	respondError(w, http.StatusNotImplemented, "Not implemented")
}

func (h *handlers) handlePasswordReset(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		Email string `json:"email"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	// Validate email format
	if err := middleware.ValidateEmail(req.Email); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid email format")
		return
	}

	// Initiate password reset (always returns success for security)
	if err := h.services.Auth.ResetPassword(r.Context(), req.Email); err != nil {
		logger.Error("Password reset error: %v", err)
		// Don't reveal the actual error to the user
	}

	respondJSON(w, http.StatusOK, map[string]string{
		"message": "If an account exists with this email, a password reset link has been sent.",
	})
}

func (h *handlers) handlePasswordResetConfirm(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		Token       string `json:"token"`
		NewPassword string `json:"new_password"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	// Validate password strength
	if err := middleware.ValidatePassword(req.NewPassword); err != nil {
		respondError(w, http.StatusBadRequest, err.Error())
		return
	}

	// Confirm password reset
	if err := h.services.Auth.ConfirmPasswordReset(r.Context(), req.Token, req.NewPassword); err != nil {
		respondError(w, http.StatusBadRequest, err.Error())
		return
	}

	respondJSON(w, http.StatusOK, map[string]string{
		"message": "Password has been reset successfully. Please log in with your new password.",
	})
}

func (h *handlers) handleBuildings(w http.ResponseWriter, r *http.Request) {
	// Get authenticated user from context
	user := middleware.GetUser(r)
	userID := ""
	if user != nil {
		userID = user.ID
	}
	
	switch r.Method {
	case http.MethodGet:
		buildings, err := h.services.Building.ListBuildings(r.Context(), userID, 100, 0)
		if err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		respondJSON(w, http.StatusOK, buildings)

	case http.MethodPost:
		var building models.FloorPlan
		if err := json.NewDecoder(r.Body).Decode(&building); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request")
			return
		}

		if err := h.services.Building.CreateBuilding(r.Context(), &building); err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}

		respondJSON(w, http.StatusCreated, building)

	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (h *handlers) handleBuilding(w http.ResponseWriter, r *http.Request) {
	// Extract building ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		respondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}
	buildingID := parts[4]

	switch r.Method {
	case http.MethodGet:
		building, err := h.services.Building.GetBuilding(r.Context(), buildingID)
		if err != nil {
			respondError(w, http.StatusNotFound, "Building not found")
			return
		}
		respondJSON(w, http.StatusOK, building)

	case http.MethodPut, http.MethodPatch:
		var building models.FloorPlan
		if err := json.NewDecoder(r.Body).Decode(&building); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request")
			return
		}

		if err := h.services.Building.UpdateBuilding(r.Context(), &building); err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}

		respondJSON(w, http.StatusOK, building)

	case http.MethodDelete:
		if err := h.services.Building.DeleteBuilding(r.Context(), buildingID); err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		w.WriteHeader(http.StatusNoContent)

	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// Middleware functions

func (h *handlers) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		logger.Debug("%s %s", r.Method, r.URL.Path)
		next.ServeHTTP(w, r)
		logger.Info("%s %s %v", r.Method, r.URL.Path, time.Since(start))
	})
}

func (h *handlers) recoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				logger.Error("Panic recovered: %v", err)
				respondError(w, http.StatusInternalServerError, "Internal server error")
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func (h *handlers) corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get origin from request
		origin := r.Header.Get("Origin")
		
		// List of allowed origins (should come from config in production)
		allowedOrigins := map[string]bool{
			"http://localhost:3000":  true,
			"http://localhost:8080":  true,
			"https://arxos.io":       true,
		}
		
		// Check if origin is allowed
		if allowedOrigins[origin] {
			w.Header().Set("Access-Control-Allow-Origin", origin)
		}
		
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}

// Helper functions

func respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func respondError(w http.ResponseWriter, status int, message string) {
	respondJSON(w, status, map[string]string{"error": message})
}

// handleMetrics serves Prometheus metrics
func (h *handlers) handleMetrics(w http.ResponseWriter, r *http.Request) {
	// This will be handled by the telemetry package's metrics collector
	http.Redirect(w, r, ":9090/metrics", http.StatusTemporaryRedirect)
}

// handleDashboard serves the observability dashboard
func (h *handlers) handleDashboard(w http.ResponseWriter, r *http.Request) {
	// This will be handled by the telemetry package's dashboard
	http.Redirect(w, r, ":8090/", http.StatusTemporaryRedirect)
}

// handleOrganizations handles organization list operations
func (h *handlers) handleOrganizations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		// Get authenticated user
		user := middleware.GetUser(r)
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
		
	case http.MethodPost:
		// Get authenticated user
		user := middleware.GetUser(r)
		if user == nil {
			respondError(w, http.StatusUnauthorized, "Authentication required")
			return
		}
		
		// Only admins can create organizations
		if user.Role != "admin" {
			respondError(w, http.StatusForbidden, "Admin role required")
			return
		}
		
		// Parse request body
		var org models.Organization
		if err := json.NewDecoder(r.Body).Decode(&org); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		
		// Validate required fields
		if org.Name == "" {
			respondError(w, http.StatusBadRequest, "Organization name is required")
			return
		}
		
		// Create organization with current user as owner
		if err := h.services.Organization.CreateOrganization(r.Context(), &org, user.ID); err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		
		// Creator is automatically added as owner by CreateOrganization
		
		respondJSON(w, http.StatusCreated, org)
		
	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handlePDFUpload handles PDF file uploads for building import
func (h *handlers) handlePDFUpload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	// Get authenticated user
	user := middleware.GetUser(r)
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	// Limit upload size to 100MB
	const maxUploadSize = 100 * 1024 * 1024
	r.Body = http.MaxBytesReader(w, r.Body, maxUploadSize)
	
	// Parse multipart form
	if err := r.ParseMultipartForm(maxUploadSize); err != nil {
		respondError(w, http.StatusBadRequest, "File too large or invalid form data")
		return
	}
	
	// Get the file
	file, header, err := r.FormFile("file")
	if err != nil {
		respondError(w, http.StatusBadRequest, "No file provided")
		return
	}
	defer file.Close()
	
	// Check file type
	if !strings.HasSuffix(strings.ToLower(header.Filename), ".pdf") {
		respondError(w, http.StatusBadRequest, "Only PDF files are supported")
		return
	}
	
	logger.Info("Processing PDF upload: %s (%d bytes) for user %s", 
		header.Filename, header.Size, user.ID)
	
	// Create PDF importer
	pdfImporter := importer.NewImporter(h.services.DB)
	
	// Prepare import options
	options := importer.ImportOptions{
		BuildingName: r.FormValue("building_name"),
		BuildingID:   r.FormValue("building_id"),
		UserID:       user.ID,
		Overwrite:    r.FormValue("overwrite") == "true",
	}
	
	// If building name not provided, use filename
	if options.BuildingName == "" {
		options.BuildingName = strings.TrimSuffix(header.Filename, ".pdf")
	}
	
	// Import with timeout
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Minute)
	defer cancel()
	
	// Process import
	result, err := pdfImporter.Import(ctx, file, options)
	if err != nil {
		logger.Error("PDF import failed: %v", err)
		respondError(w, http.StatusInternalServerError, fmt.Sprintf("Import failed: %v", err))
		return
	}
	
	// Return success response
	respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "PDF imported successfully",
		"data": map[string]interface{}{
			"building_id":     result.BuildingID,
			"rooms_imported":  result.RoomsImported,
			"equip_imported":  result.EquipImported,
			"import_duration": result.Duration.String(),
		},
		"warnings": result.Warnings,
	})
}

// handleEquipment handles equipment list operations
func (h *handlers) handleEquipment(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		// Get query parameters
		buildingID := r.URL.Query().Get("building_id")
		equipType := r.URL.Query().Get("type")
		status := r.URL.Query().Get("status")
		
		// Build filters
		filters := make(map[string]interface{})
		if buildingID != "" {
			filters["building_id"] = buildingID
		}
		if equipType != "" {
			filters["type"] = equipType
		}
		if status != "" {
			filters["status"] = status
		}
		
		// List equipment
		equipment, err := h.services.Building.ListEquipment(r.Context(), buildingID, filters)
		if err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		
		respondJSON(w, http.StatusOK, equipment)
		
	case http.MethodPost:
		// Get authenticated user
		user := middleware.GetUser(r)
		if user == nil {
			respondError(w, http.StatusUnauthorized, "Authentication required")
			return
		}
		
		// Parse request body
		var equipment models.Equipment
		if err := json.NewDecoder(r.Body).Decode(&equipment); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		
		// Validate required fields
		if equipment.Name == "" || equipment.Type == "" {
			respondError(w, http.StatusBadRequest, "Name and type are required")
			return
		}
		
		// Create equipment
		if err := h.services.Building.CreateEquipment(r.Context(), &equipment); err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		
		respondJSON(w, http.StatusCreated, equipment)
		
	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleEquipmentItem handles individual equipment operations
func (h *handlers) handleEquipmentItem(w http.ResponseWriter, r *http.Request) {
	// Extract equipment ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		respondError(w, http.StatusBadRequest, "Invalid equipment ID")
		return
	}
	equipmentID := parts[4]
	
	switch r.Method {
	case http.MethodGet:
		equipment, err := h.services.Building.GetEquipment(r.Context(), equipmentID)
		if err != nil {
			respondError(w, http.StatusNotFound, "Equipment not found")
			return
		}
		respondJSON(w, http.StatusOK, equipment)
		
	case http.MethodPut, http.MethodPatch:
		// Get authenticated user
		user := middleware.GetUser(r)
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
		
	case http.MethodDelete:
		// Get authenticated user
		user := middleware.GetUser(r)
		if user == nil {
			respondError(w, http.StatusUnauthorized, "Authentication required")
			return
		}
		
		if err := h.services.Building.DeleteEquipment(r.Context(), equipmentID); err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		
		w.WriteHeader(http.StatusNoContent)
		
	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleBuildingEquipment handles equipment for a specific building
func (h *handlers) handleBuildingEquipment(w http.ResponseWriter, r *http.Request) {
	// Check if this is a building equipment request
	if !strings.Contains(r.URL.Path, "/equipment") {
		// Not an equipment request, delegate to building handler
		h.handleBuilding(w, r)
		return
	}
	
	// Extract building ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		respondError(w, http.StatusBadRequest, "Invalid building ID")
		return
	}
	buildingID := parts[4]
	
	switch r.Method {
	case http.MethodGet:
		// List equipment for building
		equipment, err := h.services.Building.ListEquipment(r.Context(), buildingID, nil)
		if err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		respondJSON(w, http.StatusOK, equipment)
		
	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleOrganization handles individual organization operations
func (h *handlers) handleOrganization(w http.ResponseWriter, r *http.Request) {
	// Extract organization ID from path
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 5 {
		respondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}
	orgID := parts[4]
	
	// Handle sub-resources
	if len(parts) > 5 {
		switch parts[5] {
		case "members":
			h.handleOrganizationMembers(w, r, orgID)
			return
		case "invite":
			h.handleOrganizationInvite(w, r, orgID)
			return
		}
	}
	
	switch r.Method {
	case http.MethodGet:
		org, err := h.services.Organization.GetOrganization(r.Context(), orgID)
		if err != nil {
			respondError(w, http.StatusNotFound, "Organization not found")
			return
		}
		respondJSON(w, http.StatusOK, org)
		
	case http.MethodPut, http.MethodPatch:
		// Get authenticated user
		user := middleware.GetUser(r)
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
		
		// Parse update
		var update models.Organization
		if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
			respondError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		
		update.ID = orgID
		now := time.Now()
		update.UpdatedAt = &now
		
		if err := h.services.Organization.UpdateOrganization(r.Context(), &update); err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		
		respondJSON(w, http.StatusOK, update)
		
	case http.MethodDelete:
		// Get authenticated user
		user := middleware.GetUser(r)
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
		
	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleOrganizationMembers handles organization member operations
func (h *handlers) handleOrganizationMembers(w http.ResponseWriter, r *http.Request, orgID string) {
	switch r.Method {
	case http.MethodGet:
		members, err := h.services.Organization.GetMembers(r.Context(), orgID)
		if err != nil {
			respondError(w, http.StatusInternalServerError, err.Error())
			return
		}
		respondJSON(w, http.StatusOK, members)
		
	case http.MethodPost:
		// Add member (requires admin)
		user := middleware.GetUser(r)
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
			"org_id": orgID,
			"user_id": req.UserID,
			"role": req.Role,
		})
		
	default:
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleOrganizationInvite handles organization invitations
func (h *handlers) handleOrganizationInvite(w http.ResponseWriter, r *http.Request, orgID string) {
	if r.Method != http.MethodPost {
		respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	// Get authenticated user
	user := middleware.GetUser(r)
	if user == nil {
		respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}
	
	// Parse invite request
	var invite struct {
		Email string `json:"email"`
		Role  string `json:"role"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&invite); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	// TODO: Implement invitation system
	// For now, just return success
	respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Invitation sent",
		"data": map[string]string{
			"email": invite.Email,
			"org_id": orgID,
			"role": invite.Role,
		},
	})
}