package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	"github.com/arxos/arxos-core"
	"github.com/arxos/arxos-ingestion"
	"github.com/arxos/arxos-storage"
)

// Server represents the Arxos API server
type Server struct {
	router     *mux.Router
	arxRepo    *arxoscore.ArxObjectRepository
	ingestion  *ingestion.PDFIngestion
	upgrader   websocket.Upgrader
	clients    map[*websocket.Conn]bool
	broadcast  chan []byte
}

// NewServer creates a new API server
func NewServer() (*Server, error) {
	// Initialize storage
	db, err := storage.NewConnection()
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

	server := &Server{
		router:    mux.NewRouter(),
		arxRepo:   arxRepo,
		ingestion: pdfIngestion,
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins in development
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

	// ArxObject endpoints
	api.HandleFunc("/arxobjects", s.getArxObjects).Methods("GET")
	api.HandleFunc("/arxobjects", s.createArxObject).Methods("POST")
	api.HandleFunc("/arxobjects/{id}", s.getArxObject).Methods("GET")
	api.HandleFunc("/arxobjects/{id}", s.updateArxObject).Methods("PUT")
	api.HandleFunc("/arxobjects/{id}", s.deleteArxObject).Methods("DELETE")

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

	// Ingestion endpoints
	api.HandleFunc("/ingest/pdf", s.ingestPDF).Methods("POST")
	api.HandleFunc("/ingest/image", s.ingestImage).Methods("POST")
	api.HandleFunc("/ingest/lidar", s.startLidarSession).Methods("POST")

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
func (s *Server) Start(port string) error {
	log.Printf("Starting Arxos API server on port %s", port)
	return http.ListenAndServe(":"+port, s.router)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	server, err := NewServer()
	if err != nil {
		log.Fatalf("Failed to create server: %v", err)
	}

	if err := server.Start(port); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}