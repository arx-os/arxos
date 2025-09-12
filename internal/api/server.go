package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/logger"
)

// Server represents the API server
type Server struct {
	addr     string
	services *Services
	server   *http.Server
	router   *http.ServeMux
}

// Services holds all service dependencies
type Services struct {
	Auth         AuthService
	Building     BuildingService
	User         UserService
	Organization OrganizationService
	DB           database.DB // Database interface for services that need direct DB access
}

// NewServer creates a new API server
func NewServer(addr string, services *Services) *Server {
	s := &Server{
		addr:     addr,
		services: services,
		router:   http.NewServeMux(),
	}
	
	s.setupRoutes()
	return s
}

// setupRoutes configures all API routes
func (s *Server) setupRoutes() {
	// Health endpoints
	s.router.HandleFunc("/health", s.handleHealth)
	s.router.HandleFunc("/ready", s.handleReady)
	
	// Auth endpoints
	s.router.HandleFunc("/api/v1/auth/login", s.handleLogin)
	s.router.HandleFunc("/api/v1/auth/logout", s.handleLogout)
	s.router.HandleFunc("/api/v1/auth/register", s.handleRegister)
	s.router.HandleFunc("/api/v1/auth/refresh", s.handleRefresh)
	
	// User endpoints
	s.router.HandleFunc("/api/v1/users/me", s.handleGetCurrentUser)
	s.router.HandleFunc("/api/v1/users", s.handleListUsers)
	s.router.HandleFunc("/api/v1/users/", s.handleGetUser)
	
	// Building endpoints
	s.router.HandleFunc("/api/v1/buildings", s.handleListBuildings)
	s.router.HandleFunc("/api/v1/buildings/create", s.handleCreateBuilding)
	s.router.HandleFunc("/api/v1/buildings/", s.handleBuildingOperations)
	
	// Equipment endpoints
	s.router.HandleFunc("/api/v1/equipment", s.handleListEquipment)
	s.router.HandleFunc("/api/v1/equipment/create", s.handleCreateEquipment)
	s.router.HandleFunc("/api/v1/equipment/", s.handleEquipmentOperations)
	
	// Sync endpoints
	s.router.HandleFunc("/api/v1/sync/push", s.handleSyncPush)
	s.router.HandleFunc("/api/v1/sync/pull", s.handleSyncPull)
	s.router.HandleFunc("/api/v1/sync/status", s.handleSyncStatus)
	
	// Upload endpoints
	s.router.HandleFunc("/api/v1/upload/pdf", s.handlePDFUpload)
	s.router.HandleFunc("/api/v1/upload/progress", s.handleUploadProgress)
}

// Start starts the API server
func (s *Server) Start() error {
	// Apply middleware
	handler := s.loggingMiddleware(s.router)
	handler = s.recoveryMiddleware(handler)
	handler = s.corsMiddleware(handler)
	handler = s.rateLimitMiddleware(handler)
	
	s.server = &http.Server{
		Addr:         s.addr,
		Handler:      handler,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}
	
	logger.Info("API server starting on %s", s.addr)
	return s.server.ListenAndServe()
}

// Stop gracefully stops the server
func (s *Server) Stop(ctx context.Context) error {
	if s.server != nil {
		logger.Info("Stopping API server...")
		return s.server.Shutdown(ctx)
	}
	return nil
}

// Health check handlers

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	s.respondJSON(w, http.StatusOK, map[string]string{
		"status": "healthy",
		"time":   time.Now().Format(time.RFC3339),
	})
}

func (s *Server) handleReady(w http.ResponseWriter, r *http.Request) {
	ready := s.services != nil && 
		s.services.Auth != nil && 
		s.services.Building != nil
	
	if ready {
		s.respondJSON(w, http.StatusOK, map[string]bool{"ready": true})
	} else {
		s.respondJSON(w, http.StatusServiceUnavailable, map[string]bool{"ready": false})
	}
}

// handleBuildingOperations routes building operations based on method
func (s *Server) handleBuildingOperations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetBuilding(w, r)
	case http.MethodPut, http.MethodPatch:
		s.handleUpdateBuilding(w, r)
	case http.MethodDelete:
		s.handleDeleteBuilding(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleEquipmentOperations routes equipment operations based on method
func (s *Server) handleEquipmentOperations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetEquipment(w, r)
	case http.MethodPut, http.MethodPatch:
		s.handleUpdateEquipment(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// Response helpers

func (s *Server) respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	
	if data != nil {
		if err := json.NewEncoder(w).Encode(data); err != nil {
			logger.Error("Failed to encode JSON response: %v", err)
		}
	}
}

func (s *Server) respondError(w http.ResponseWriter, status int, message string) {
	s.respondJSON(w, status, map[string]string{
		"error": message,
		"code":  fmt.Sprintf("%d", status),
	})
}

// Context keys are defined in middleware.go

// getRequestID generates a unique request ID
func (s *Server) getRequestID(r *http.Request) string {
	// Check if request already has an ID (from header)
	if id := r.Header.Get("X-Request-ID"); id != "" {
		return id
	}
	return fmt.Sprintf("%d", time.Now().UnixNano())
}