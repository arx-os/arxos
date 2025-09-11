package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
	
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/internal/portfolio"
	"github.com/joelpate/arxos/pkg/models"
)

// Server represents the REST API server
type Server struct {
	addr      string
	port      int
	portfolio *portfolio.Manager
	router    *http.ServeMux
	server    *http.Server
}

// NewServer creates a new API server
func NewServer(addr string, port int, portfolioManager *portfolio.Manager) *Server {
	if addr == "" {
		addr = "0.0.0.0"
	}
	if port == 0 {
		port = 8080
	}
	
	s := &Server{
		addr:      addr,
		port:      port,
		portfolio: portfolioManager,
		router:    http.NewServeMux(),
	}
	
	s.setupRoutes()
	
	return s
}

// setupRoutes configures all API routes
func (s *Server) setupRoutes() {
	// Health check
	s.router.HandleFunc("/health", s.handleHealth)
	
	// Portfolio endpoints
	s.router.HandleFunc("/api/v1/portfolios", s.handlePortfolios)
	s.router.HandleFunc("/api/v1/portfolios/", s.handlePortfolioByID)
	
	// Building endpoints
	s.router.HandleFunc("/api/v1/buildings", s.handleBuildings)
	s.router.HandleFunc("/api/v1/buildings/", s.handleBuildingByID)
	
	// Floor plan endpoints
	s.router.HandleFunc("/api/v1/floors", s.handleFloorPlans)
	s.router.HandleFunc("/api/v1/floors/", s.handleFloorPlanByID)
	
	// Equipment endpoints
	s.router.HandleFunc("/api/v1/equipment", s.handleEquipment)
	s.router.HandleFunc("/api/v1/equipment/", s.handleEquipmentByID)
	s.router.HandleFunc("/api/v1/equipment/search", s.handleEquipmentSearch)
	s.router.HandleFunc("/api/v1/equipment/nearby", s.handleEquipmentNearby)
	
	// Query endpoint
	s.router.HandleFunc("/api/v1/query", s.handleQuery)
	
	// Statistics endpoint
	s.router.HandleFunc("/api/v1/stats", s.handleStatistics)
	
	// WebSocket for real-time updates
	s.router.HandleFunc("/ws", s.handleWebSocket)
}

// Start starts the API server
func (s *Server) Start() error {
	s.server = &http.Server{
		Addr:         fmt.Sprintf("%s:%d", s.addr, s.port),
		Handler:      s.corsMiddleware(s.loggingMiddleware(s.router)),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}
	
	logger.Info("Starting API server on %s:%d", s.addr, s.port)
	
	return s.server.ListenAndServe()
}

// Stop gracefully stops the API server
func (s *Server) Stop(ctx context.Context) error {
	logger.Info("Stopping API server...")
	return s.server.Shutdown(ctx)
}

// Middleware

func (s *Server) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		
		// Wrap response writer to capture status code
		wrapped := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		
		next.ServeHTTP(wrapped, r)
		
		logger.Info("%s %s %d %v", r.Method, r.URL.Path, wrapped.statusCode, time.Since(start))
	})
}

func (s *Server) corsMiddleware(next http.Handler) http.Handler {
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

// Handlers

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":  "healthy",
		"time":    time.Now().Unix(),
		"version": "1.0.0",
	}
	
	s.writeJSON(w, http.StatusOK, response)
}

func (s *Server) handlePortfolios(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.getPortfolios(w, r)
	case http.MethodPost:
		s.createPortfolio(w, r)
	default:
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (s *Server) getPortfolios(w http.ResponseWriter, r *http.Request) {
	portfolios, err := s.portfolio.ListPortfolios()
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	s.writeJSON(w, http.StatusOK, portfolios)
}

func (s *Server) createPortfolio(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name  string `json:"name"`
		Owner string `json:"owner"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	portfolio, err := s.portfolio.CreatePortfolio(req.Name, req.Owner)
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	s.writeJSON(w, http.StatusCreated, portfolio)
}

func (s *Server) handlePortfolioByID(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/api/v1/portfolios/")
	
	switch r.Method {
	case http.MethodGet:
		portfolio, err := s.portfolio.LoadPortfolio(id)
		if err != nil {
			s.writeError(w, http.StatusNotFound, err.Error())
			return
		}
		s.writeJSON(w, http.StatusOK, portfolio)
		
	case http.MethodDelete:
		// Implement portfolio deletion
		s.writeError(w, http.StatusNotImplemented, "Portfolio deletion not implemented")
		
	default:
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (s *Server) handleBuildings(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.getBuildings(w, r)
	case http.MethodPost:
		s.createBuilding(w, r)
	default:
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (s *Server) getBuildings(w http.ResponseWriter, r *http.Request) {
	// Get buildings from active portfolio
	// Implementation depends on portfolio manager methods
	s.writeError(w, http.StatusNotImplemented, "Building listing not implemented")
}

func (s *Server) createBuilding(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name       string  `json:"name"`
		Address    string  `json:"address"`
		Type       string  `json:"type"`
		SquareFeet float64 `json:"square_feet"`
		Floors     int     `json:"floors"`
		YearBuilt  int     `json:"year_built"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	building, err := s.portfolio.AddBuilding(req.Name, req.Address, req.Type, 
		req.SquareFeet, req.Floors, req.YearBuilt)
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	s.writeJSON(w, http.StatusCreated, building)
}

func (s *Server) handleBuildingByID(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/api/v1/buildings/")
	
	switch r.Method {
	case http.MethodGet:
		building, err := s.portfolio.GetBuilding(id)
		if err != nil {
			s.writeError(w, http.StatusNotFound, err.Error())
			return
		}
		s.writeJSON(w, http.StatusOK, building)
		
	case http.MethodPut:
		// Update building
		s.writeError(w, http.StatusNotImplemented, "Building update not implemented")
		
	case http.MethodDelete:
		// Delete building
		s.writeError(w, http.StatusNotImplemented, "Building deletion not implemented")
		
	default:
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (s *Server) handleFloorPlans(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		buildingID := r.URL.Query().Get("building_id")
		if buildingID == "" {
			s.writeError(w, http.StatusBadRequest, "building_id parameter required")
			return
		}
		
		building, err := s.portfolio.GetBuilding(buildingID)
		if err != nil {
			s.writeError(w, http.StatusNotFound, err.Error())
			return
		}
		
		s.writeJSON(w, http.StatusOK, building.FloorPlans)
		
	case http.MethodPost:
		s.createFloorPlan(w, r)
		
	default:
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (s *Server) createFloorPlan(w http.ResponseWriter, r *http.Request) {
	var req struct {
		BuildingID string             `json:"building_id"`
		FloorPlan  *models.FloorPlan  `json:"floor_plan"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	if err := s.portfolio.AddFloorPlan(req.BuildingID, req.FloorPlan); err != nil {
		s.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	s.writeJSON(w, http.StatusCreated, map[string]string{"status": "created"})
}

func (s *Server) handleFloorPlanByID(w http.ResponseWriter, r *http.Request) {
	// Implementation for specific floor plan operations
	s.writeError(w, http.StatusNotImplemented, "Floor plan operations not implemented")
}

func (s *Server) handleEquipment(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.getEquipment(w, r)
	case http.MethodPost:
		s.createEquipment(w, r)
	default:
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

func (s *Server) getEquipment(w http.ResponseWriter, r *http.Request) {
	// Get query parameters for filtering
	_ = r.URL.Query().Get("building_id")
	_ = r.URL.Query().Get("floor_id")
	_ = r.URL.Query().Get("status")
	
	// Implementation would filter equipment based on parameters
	s.writeError(w, http.StatusNotImplemented, "Equipment listing not implemented")
}

func (s *Server) createEquipment(w http.ResponseWriter, r *http.Request) {
	var equipment models.Equipment
	
	if err := json.NewDecoder(r.Body).Decode(&equipment); err != nil {
		s.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	// Implementation would add equipment to specified floor plan
	s.writeError(w, http.StatusNotImplemented, "Equipment creation not implemented")
}

func (s *Server) handleEquipmentByID(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/api/v1/equipment/")
	
	switch r.Method {
	case http.MethodGet:
		// Get equipment by ID
		s.writeError(w, http.StatusNotImplemented, "Equipment retrieval not implemented")
		
	case http.MethodPut:
		// Update equipment
		var updates map[string]interface{}
		if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
			s.writeError(w, http.StatusBadRequest, "Invalid request body")
			return
		}
		
		// Implementation would update equipment
		s.writeError(w, http.StatusNotImplemented, "Equipment update not implemented")
		
	case http.MethodDelete:
		// Delete equipment
		s.writeError(w, http.StatusNotImplemented, "Equipment deletion not implemented")
		
	default:
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
	
	_ = id // Use id when implemented
}

func (s *Server) handleEquipmentSearch(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	query := r.URL.Query().Get("q")
	if query == "" {
		s.writeError(w, http.StatusBadRequest, "Query parameter 'q' required")
		return
	}
	
	// Implementation would search equipment across portfolio
	s.writeError(w, http.StatusNotImplemented, "Equipment search not implemented")
}

func (s *Server) handleEquipmentNearby(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	x := r.URL.Query().Get("x")
	y := r.URL.Query().Get("y")
	radius := r.URL.Query().Get("radius")
	
	if x == "" || y == "" || radius == "" {
		s.writeError(w, http.StatusBadRequest, "Parameters x, y, and radius required")
		return
	}
	
	// Parse parameters and find nearby equipment
	// Implementation would use spatial index
	s.writeError(w, http.StatusNotImplemented, "Nearby equipment search not implemented")
}

func (s *Server) handleQuery(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	var req struct {
		Query string `json:"query"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}
	
	results, err := s.portfolio.QueryAcrossPortfolio(req.Query)
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	s.writeJSON(w, http.StatusOK, results)
}

func (s *Server) handleStatistics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		s.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}
	
	stats, err := s.portfolio.GetPortfolioStatistics()
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	s.writeJSON(w, http.StatusOK, stats)
}

func (s *Server) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	// WebSocket implementation for real-time updates
	// Would use gorilla/websocket or similar library
	s.writeError(w, http.StatusNotImplemented, "WebSocket not implemented")
}

// Helper methods

func (s *Server) writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	
	if err := json.NewEncoder(w).Encode(data); err != nil {
		logger.Error("Failed to encode JSON response: %v", err)
	}
}

func (s *Server) writeError(w http.ResponseWriter, status int, message string) {
	s.writeJSON(w, status, map[string]string{
		"error": message,
		"code":  fmt.Sprintf("%d", status),
	})
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// APIResponse represents a standard API response
type APIResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
	Meta    *Meta       `json:"meta,omitempty"`
}

// Meta contains metadata about the response
type Meta struct {
	Page       int    `json:"page,omitempty"`
	PerPage    int    `json:"per_page,omitempty"`
	Total      int    `json:"total,omitempty"`
	TotalPages int    `json:"total_pages,omitempty"`
	Timestamp  int64  `json:"timestamp"`
	Version    string `json:"version"`
}