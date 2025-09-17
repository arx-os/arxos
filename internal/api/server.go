// Package api provides the HTTP API server and REST endpoints for ArxOS.
// It handles authentication, building management, equipment operations, and user
// management with configurable CORS, rate limiting, and security middleware.
package api

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/common/logger"
)

// Config holds configuration for the API server
type Config struct {
	CORS      CORSConfig      `json:"cors"`
	RateLimit RateLimitConfig `json:"rate_limit"`
	TLS       TLSConfig       `json:"tls"`
}

// CORSConfig configures Cross-Origin Resource Sharing
type CORSConfig struct {
	AllowedOrigins []string `json:"allowed_origins"`
	AllowedMethods []string `json:"allowed_methods"`
	AllowedHeaders []string `json:"allowed_headers"`
	MaxAge         int      `json:"max_age"`
}

// RateLimitConfig configures rate limiting
type RateLimitConfig struct {
	RequestsPerMinute int           `json:"requests_per_minute"`
	BurstSize         int           `json:"burst_size"`
	CleanupInterval   time.Duration `json:"cleanup_interval"`
	ClientTTL         time.Duration `json:"client_ttl"`
}

// TLSConfig configures TLS/HTTPS settings
type TLSConfig struct {
	Enabled      bool     `json:"enabled"`
	CertFile     string   `json:"cert_file"`
	KeyFile      string   `json:"key_file"`
	AutoCert     bool     `json:"auto_cert"`
	AutoCertDomains []string `json:"auto_cert_domains"`
	MinVersion   uint16   `json:"min_version"`
}

// Server represents the API server
type Server struct {
	addr     string
	config   *Config
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

// DefaultConfig returns a default API server configuration
func DefaultConfig() *Config {
	return &Config{
		CORS: CORSConfig{
			AllowedOrigins: []string{"*"}, // Configurable in production
			AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
			AllowedHeaders: []string{"Content-Type", "Authorization", "X-Request-ID"},
			MaxAge:         3600,
		},
		RateLimit: RateLimitConfig{
			RequestsPerMinute: 100,
			BurstSize:         10,
			CleanupInterval:   1 * time.Minute,
			ClientTTL:         5 * time.Minute,
		},
		TLS: TLSConfig{
			Enabled:    false,
			MinVersion: 0x0303, // TLS 1.2
		},
	}
}

// NewServer creates a new API server with default configuration.
// It initializes the HTTP server with the provided address and service dependencies,
// setting up all routes and middleware with sensible defaults.
func NewServer(addr string, services *Services) *Server {
	return NewServerWithConfig(addr, services, DefaultConfig())
}

// NewServerWithConfig creates a new API server with custom configuration.
// This allows for fine-tuning of CORS settings, rate limiting, and other security
// parameters while maintaining the same service dependencies and route structure.
func NewServerWithConfig(addr string, services *Services, config *Config) *Server {
	s := &Server{
		addr:     addr,
		config:   config,
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

// Routes returns the configured router with middleware applied
func (s *Server) Routes() http.Handler {
	// Apply middleware
	handler := s.loggingMiddleware(s.router)
	handler = s.recoveryMiddleware(handler)
	handler = s.corsMiddleware(handler)
	handler = s.rateLimitMiddleware(handler)
	return handler
}

// Start starts the API server
func (s *Server) Start() error {
	s.server = &http.Server{
		Addr:         s.addr,
		Handler:      s.Routes(),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	logger.Info("API server starting on %s", s.addr)
	return s.server.ListenAndServe()
}

// StartTLS starts the API server with TLS/HTTPS
func (s *Server) StartTLS(certFile, keyFile string) error {
	s.server = &http.Server{
		Addr:         s.addr,
		Handler:      s.Routes(),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Configure TLS
	if s.config.TLS.MinVersion > 0 {
		s.server.TLSConfig = &tls.Config{
			MinVersion: s.config.TLS.MinVersion,
			CipherSuites: []uint16{
				tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
				tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
				tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,
				tls.TLS_RSA_WITH_AES_128_GCM_SHA256,
				tls.TLS_RSA_WITH_AES_256_GCM_SHA384,
			},
			PreferServerCipherSuites: true,
		}
	}

	logger.Info("API server starting on %s with TLS", s.addr)
	return s.server.ListenAndServeTLS(certFile, keyFile)
}

// StartWithConfig starts the server based on configuration
func (s *Server) StartWithConfig() error {
	if s.config.TLS.Enabled {
		if s.config.TLS.AutoCert {
			return s.StartAutoCert()
		}
		return s.StartTLS(s.config.TLS.CertFile, s.config.TLS.KeyFile)
	}
	return s.Start()
}

// StartAutoCert starts the server with automatic certificate management
func (s *Server) StartAutoCert() error {
	// This would use Let's Encrypt or similar
	// For now, return an error indicating it's not implemented
	return fmt.Errorf("auto-cert not yet implemented")
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