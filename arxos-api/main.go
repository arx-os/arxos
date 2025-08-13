package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	"github.com/arxos/arxos-core"
	"github.com/arxos/arxos-ingestion"
	"github.com/arxos/arxos-storage"
)

// Server represents the Arxos API server
type Server struct {
	router      *mux.Router
	arxRepo     *arxoscore.ArxObjectRepository
	ingestion   *ingestion.PDFIngestion
	upgrader    websocket.Upgrader
	clients     map[*websocket.Conn]bool
	broadcast   chan []byte
	authManager *AuthManager
}

// Config holds server configuration
type Config struct {
	Port                string
	DatabaseURL         string
	RedisURL            string
	JWTSecret           string
	Environment         string
	LogLevel            string
	EnableAuth          bool
	MaxUploadSize       int64
	CORSOrigins         []string
	RateLimitPerMinute  int
}

// NewConfigFromEnv creates configuration from environment variables
func NewConfigFromEnv() *Config {
	config := &Config{
		Port:               getEnv("PORT", "8080"),
		DatabaseURL:        getEnv("DATABASE_URL", buildDatabaseURL()),
		RedisURL:           getEnv("REDIS_URL", "redis://localhost:6379"),
		JWTSecret:          getEnv("JWT_SECRET", "arxos-dev-secret-key-change-in-production"),
		Environment:        getEnv("ENVIRONMENT", "development"),
		LogLevel:           getEnv("LOG_LEVEL", "info"),
		EnableAuth:         getBoolEnv("ENABLE_AUTH", true),
		MaxUploadSize:      getIntEnv("MAX_UPLOAD_SIZE", 100*1024*1024), // 100MB default
		CORSOrigins:        getStringSliceEnv("CORS_ORIGINS", []string{"*"}),
		RateLimitPerMinute: getIntEnv("RATE_LIMIT_PER_MINUTE", 60),
	}
	
	// Validate critical configuration
	if config.JWTSecret == "arxos-dev-secret-key-change-in-production" && config.Environment == "production" {
		log.Fatal("JWT_SECRET must be changed in production environment")
	}
	
	return config
}

// buildDatabaseURL constructs database URL from individual components
func buildDatabaseURL() string {
	host := getEnv("POSTGRES_HOST", "localhost")
	port := getEnv("POSTGRES_PORT", "5432")
	db := getEnv("POSTGRES_DB", "arxos")
	user := getEnv("POSTGRES_USER", "arxos")
	password := getEnv("POSTGRES_PASSWORD", "")
	
	if password == "" {
		log.Fatal("POSTGRES_PASSWORD must be set")
	}
	
	return fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable", user, password, host, port, db)
}

// getEnv gets environment variable with default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getBoolEnv gets boolean environment variable with default value
func getBoolEnv(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if parsed, err := strconv.ParseBool(value); err == nil {
			return parsed
		}
	}
	return defaultValue
}

// getIntEnv gets integer environment variable with default value
func getIntEnv(key string, defaultValue int64) int64 {
	if value := os.Getenv(key); value != "" {
		if parsed, err := strconv.ParseInt(value, 10, 64); err == nil {
			return parsed
		}
	}
	return defaultValue
}

// getStringSliceEnv gets string slice from comma-separated environment variable
func getStringSliceEnv(key string, defaultValue []string) []string {
	if value := os.Getenv(key); value != "" {
		return strings.Split(value, ",")
	}
	return defaultValue
}

// NewServer creates a new API server
func NewServer() (*Server, error) {
	config := NewConfigFromEnv()
	
	// Initialize storage
	db, err := storage.NewConnectionWithURL(config.DatabaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	// Initialize repositories
	arxRepo := arxoscore.NewArxObjectRepository(db)

	// Initialize ingestion
	pdfIngestion, err := ingestion.NewPDFIngestion(arxRepo)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize PDF ingestion: %w", err)
	}

	// Initialize authentication
	authConfig := NewAuthConfigFromEnv(config)
	authManager := NewAuthManager(authConfig)

	server := &Server{
		router:      mux.NewRouter(),
		arxRepo:     arxRepo,
		ingestion:   pdfIngestion,
		authManager: authManager,
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				// Check origin against allowed origins
				origin := r.Header.Get("Origin")
				if config.Environment == "development" {
					return true // Allow all origins in development
				}
				
				for _, allowed := range config.CORSOrigins {
					if allowed == "*" || allowed == origin {
						return true
					}
				}
				return false
			},
		},
		clients:   make(map[*websocket.Conn]bool),
		broadcast: make(chan []byte),
	}

	server.setupRoutes()
	return server, nil
}

// setupRoutes configures all API routes
func (s *Server) setupRoutes() {
	// API prefix
	api := s.router.PathPrefix("/api/v1").Subrouter()

	// Authentication endpoints (no auth required)
	api.HandleFunc("/auth/login", s.handleLogin).Methods("POST")

	// Apply authentication middleware to all other routes
	api.Use(s.authManager.AuthMiddleware)

	// ArxObject endpoints
	arxObjectRoutes := api.PathPrefix("/arxobjects").Subrouter()
	arxObjectRoutes.HandleFunc("", s.getArxObjects).Methods("GET")
	arxObjectRoutes.HandleFunc("", s.authManager.RequirePermission(PermCreateArxObject)(http.HandlerFunc(s.createArxObject))).Methods("POST")
	arxObjectRoutes.HandleFunc("/{id}", s.getArxObject).Methods("GET")
	arxObjectRoutes.HandleFunc("/{id}", s.authManager.RequirePermission(PermUpdateArxObject)(http.HandlerFunc(s.updateArxObject))).Methods("PUT")
	arxObjectRoutes.HandleFunc("/{id}", s.authManager.RequirePermission(PermDeleteArxObject)(http.HandlerFunc(s.deleteArxObject))).Methods("DELETE")

	// Hierarchy endpoints
	api.HandleFunc("/arxobjects/{id}/children", s.getChildren).Methods("GET")
	api.HandleFunc("/arxobjects/{id}/parent", s.getParent).Methods("GET")
	api.HandleFunc("/arxobjects/{id}/ancestors", s.getAncestors).Methods("GET")

	// Spatial queries
	api.HandleFunc("/arxobjects/spatial/viewport", s.getObjectsInViewport).Methods("POST")
	api.HandleFunc("/arxobjects/spatial/overlaps/{id}", s.getOverlaps).Methods("GET")
	api.HandleFunc("/arxobjects/spatial/nearby/{id}", s.getNearbyObjects).Methods("GET")

	// System filtering
	api.HandleFunc("/systems", s.getSystems).Methods("GET")
	api.HandleFunc("/systems/{system}/objects", s.getObjectsBySystem).Methods("GET")

	// Ingestion endpoints - require specific permissions
	ingestRoutes := api.PathPrefix("/ingest").Subrouter()
	ingestRoutes.HandleFunc("/pdf", s.authManager.RequirePermission(PermIngestPDF)(http.HandlerFunc(s.ingestPDF))).Methods("POST")
	ingestRoutes.HandleFunc("/image", s.authManager.RequirePermission(PermIngestImage)(http.HandlerFunc(s.ingestImage))).Methods("POST")
	ingestRoutes.HandleFunc("/lidar", s.authManager.RequirePermission(PermIngestLidar)(http.HandlerFunc(s.startLidarSession))).Methods("POST")

	// Symbol library endpoints
	api.HandleFunc("/symbols", s.getSymbols).Methods("GET")
	api.HandleFunc("/symbols/categories", s.getSymbolCategories).Methods("GET")

	// WebSocket for real-time updates
	api.HandleFunc("/ws", s.handleWebSocket)

	// Health check
	api.HandleFunc("/health", s.healthCheck).Methods("GET")

	// CORS middleware
	s.router.Use(corsMiddleware)
}

// corsMiddleware adds CORS headers
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// getArxObjects returns all ArxObjects with optional filtering
func (s *Server) getArxObjects(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query()
	
	// Parse filter parameters
	system := query.Get("system")
	objType := query.Get("type")
	parentID := query.Get("parent_id")
	
	// Get objects from repository
	objects, err := s.arxRepo.FindAll()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Apply filters
	var filtered []*arxoscore.ArxObject
	for _, obj := range objects {
		if system != "" && obj.System != system {
			continue
		}
		if objType != "" && obj.Type != objType {
			continue
		}
		if parentID != "" && obj.ParentID != parentID {
			continue
		}
		filtered = append(filtered, obj)
	}

	respondJSON(w, filtered)
}

// createArxObject creates a new ArxObject
func (s *Server) createArxObject(w http.ResponseWriter, r *http.Request) {
	var obj arxoscore.ArxObject
	if err := json.NewDecoder(r.Body).Decode(&obj); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Create in repository
	if err := s.arxRepo.Create(&obj); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Broadcast update to WebSocket clients
	s.broadcastUpdate("create", &obj)

	respondJSON(w, obj)
}

// getArxObject returns a single ArxObject by ID
func (s *Server) getArxObject(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	obj, err := s.arxRepo.FindByID(id)
	if err != nil {
		http.Error(w, "Object not found", http.StatusNotFound)
		return
	}

	respondJSON(w, obj)
}

// updateArxObject updates an existing ArxObject
func (s *Server) updateArxObject(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	var obj arxoscore.ArxObject
	if err := json.NewDecoder(r.Body).Decode(&obj); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	obj.ID = id
	if err := s.arxRepo.Update(&obj); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Broadcast update
	s.broadcastUpdate("update", &obj)

	respondJSON(w, obj)
}

// deleteArxObject deletes an ArxObject
func (s *Server) deleteArxObject(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	if err := s.arxRepo.Delete(id); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Broadcast deletion
	s.broadcastUpdate("delete", &arxoscore.ArxObject{ID: id})

	w.WriteHeader(http.StatusNoContent)
}

// getChildren returns all children of an ArxObject
func (s *Server) getChildren(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	children, err := s.arxRepo.FindChildren(id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	respondJSON(w, children)
}

// getParent returns the parent of an ArxObject
func (s *Server) getParent(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	obj, err := s.arxRepo.FindByID(id)
	if err != nil {
		http.Error(w, "Object not found", http.StatusNotFound)
		return
	}

	if obj.ParentID == "" {
		http.Error(w, "Object has no parent", http.StatusNotFound)
		return
	}

	parent, err := s.arxRepo.FindByID(obj.ParentID)
	if err != nil {
		http.Error(w, "Parent not found", http.StatusNotFound)
		return
	}

	respondJSON(w, parent)
}

// getAncestors returns all ancestors of an ArxObject
func (s *Server) getAncestors(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	ancestors, err := s.arxRepo.FindAncestors(id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	respondJSON(w, ancestors)
}

// getObjectsInViewport returns objects visible in a viewport
func (s *Server) getObjectsInViewport(w http.ResponseWriter, r *http.Request) {
	var viewport struct {
		MinX  float64 `json:"min_x"`
		MinY  float64 `json:"min_y"`
		MaxX  float64 `json:"max_x"`
		MaxY  float64 `json:"max_y"`
		Scale float64 `json:"scale"`
		Limit int     `json:"limit"`
	}

	if err := json.NewDecoder(r.Body).Decode(&viewport); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if viewport.Limit == 0 {
		viewport.Limit = 1000
	}

	objects, err := s.arxRepo.FindInViewport(
		viewport.MinX, viewport.MinY,
		viewport.MaxX, viewport.MaxY,
		viewport.Scale, viewport.Limit,
	)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	respondJSON(w, objects)
}

// getOverlaps returns overlapping objects
func (s *Server) getOverlaps(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	overlaps, err := s.arxRepo.FindOverlaps(id, 50.0) // 50mm threshold
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	respondJSON(w, overlaps)
}

// getNearbyObjects returns nearby objects
func (s *Server) getNearbyObjects(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]
	
	query := r.URL.Query()
	radius := 500.0 // Default 500mm radius
	if r := query.Get("radius"); r != "" {
		fmt.Sscanf(r, "%f", &radius)
	}

	nearby, err := s.arxRepo.FindNearby(id, radius)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	respondJSON(w, nearby)
}

// getSystems returns all unique systems
func (s *Server) getSystems(w http.ResponseWriter, r *http.Request) {
	systems := []string{
		"electrical",
		"mechanical",
		"plumbing",
		"fire_protection",
		"structural",
		"architectural",
		"hvac",
		"data",
		"controls",
	}
	respondJSON(w, systems)
}

// getObjectsBySystem returns all objects in a system
func (s *Server) getObjectsBySystem(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	system := vars["system"]

	objects, err := s.arxRepo.FindBySystem(system)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	respondJSON(w, objects)
}

// ingestPDF handles PDF ingestion
func (s *Server) ingestPDF(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form
	if err := r.ParseMultipartForm(32 << 20); err != nil { // 32MB max
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	file, _, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "File required", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Read file data
	var pdfData []byte
	if _, err := file.Read(pdfData); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	buildingID := r.FormValue("building_id")
	if buildingID == "" {
		buildingID = fmt.Sprintf("arx:building_%d", time.Now().Unix())
	}

	// Process PDF
	objects, err := s.ingestion.IngestPDF(pdfData, buildingID, map[string]interface{}{
		"source": "api_upload",
	})
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	respondJSON(w, map[string]interface{}{
		"success": true,
		"objects_created": len(objects),
		"building_id": buildingID,
	})
}

// ingestImage handles image ingestion (photo of paper map)
func (s *Server) ingestImage(w http.ResponseWriter, r *http.Request) {
	// Similar to PDF but for images
	http.Error(w, "Image ingestion not yet implemented", http.StatusNotImplemented)
}

// startLidarSession starts a LiDAR capture session
func (s *Server) startLidarSession(w http.ResponseWriter, r *http.Request) {
	// Would initialize LiDAR capture
	http.Error(w, "LiDAR capture not yet implemented", http.StatusNotImplemented)
}

// getSymbols returns the symbol library
func (s *Server) getSymbols(w http.ResponseWriter, r *http.Request) {
	// Would return symbol library from ingestion bridge
	symbols := []map[string]interface{}{
		{"id": "electrical_outlet", "name": "Electrical Outlet", "system": "electrical"},
		{"id": "light_fixture", "name": "Light Fixture", "system": "electrical"},
		{"id": "hvac_duct", "name": "HVAC Duct", "system": "mechanical"},
		{"id": "sprinkler", "name": "Sprinkler", "system": "fire_protection"},
	}
	respondJSON(w, symbols)
}

// getSymbolCategories returns symbol categories
func (s *Server) getSymbolCategories(w http.ResponseWriter, r *http.Request) {
	categories := []string{
		"electrical",
		"mechanical",
		"plumbing",
		"fire_protection",
		"structural",
		"architectural",
	}
	respondJSON(w, categories)
}

// handleWebSocket handles WebSocket connections for real-time updates
func (s *Server) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}
	defer conn.Close()

	s.clients[conn] = true
	defer delete(s.clients, conn)

	// Keep connection alive and handle messages
	for {
		var msg map[string]interface{}
		if err := conn.ReadJSON(&msg); err != nil {
			break
		}

		// Handle different message types
		switch msg["type"] {
		case "ping":
			conn.WriteJSON(map[string]string{"type": "pong"})
		case "subscribe":
			// Handle subscription to specific objects/systems
		}
	}
}

// broadcastUpdate sends updates to all WebSocket clients
func (s *Server) broadcastUpdate(action string, obj *arxoscore.ArxObject) {
	update := map[string]interface{}{
		"type":   "update",
		"action": action,
		"object": obj,
		"timestamp": time.Now().Unix(),
	}

	data, _ := json.Marshal(update)
	
	for client := range s.clients {
		if err := client.WriteMessage(websocket.TextMessage, data); err != nil {
			client.Close()
			delete(s.clients, client)
		}
	}
}

// healthCheck returns server health status
func (s *Server) healthCheck(w http.ResponseWriter, r *http.Request) {
	respondJSON(w, map[string]interface{}{
		"status": "healthy",
		"timestamp": time.Now().Unix(),
		"version": "1.0.0",
	})
}

// respondJSON sends JSON response
func respondJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// Start starts the server
func (s *Server) Start(config *Config) error {
	log.Printf("Starting Arxos API server on port %s", config.Port)
	log.Printf("Environment: %s", config.Environment)
	log.Printf("Auth enabled: %v", config.EnableAuth)
	log.Printf("CORS origins: %v", config.CORSOrigins)
	log.Printf("Max upload size: %d bytes", config.MaxUploadSize)
	
	return http.ListenAndServe(":"+config.Port, s.router)
}

func main() {
	config := NewConfigFromEnv()
	
	// Set up logging based on environment
	if config.Environment == "production" {
		// In production, you might want structured logging
		log.SetFlags(log.LstdFlags | log.LUTC)
	} else {
		// Development logging
		log.SetFlags(log.LstdFlags | log.Lshortfile)
	}

	server, err := NewServer()
	if err != nil {
		log.Fatalf("Failed to create server: %v", err)
	}

	if err := server.Start(config); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}