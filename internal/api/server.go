// Package api provides the HTTP API server and REST endpoints for ArxOS.
// It handles authentication, building management, equipment operations, and user
// management with configurable CORS, rate limiting, and security middleware.
package api

import (
	"context"
	"crypto/tls"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/core/user"
	"github.com/arx-os/arxos/internal/database"
	"github.com/google/uuid"
	"golang.org/x/time/rate"
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
	Enabled         bool     `json:"enabled"`
	CertFile        string   `json:"cert_file"`
	KeyFile         string   `json:"key_file"`
	AutoCert        bool     `json:"auto_cert"`
	AutoCertDomains []string `json:"auto_cert_domains"`
	MinVersion      uint16   `json:"min_version"`
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
	Equipment    EquipmentService
	DB           database.ExtendedDB // Extended database interface with additional operations
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
	s.router.HandleFunc("/api/v1/users", s.handleUsers)
	s.router.HandleFunc("/api/v1/users/me", s.handleGetCurrentUser)
	s.router.HandleFunc("/api/v1/users/reset-password", s.handleRequestPasswordReset)
	s.router.HandleFunc("/api/v1/users/reset-password/confirm", s.handleConfirmPasswordReset)
	s.router.HandleFunc("/api/v1/users/{id}", s.handleUserOperations)
	s.router.HandleFunc("/api/v1/users/{id}/change-password", s.handleChangePassword)
	s.router.HandleFunc("/api/v1/users/{id}/organizations", s.handleGetUserOrganizations)
	s.router.HandleFunc("/api/v1/users/{id}/sessions", s.handleUserSessions)

	// Organization endpoints
	s.router.HandleFunc("/api/v1/organizations", s.handleOrganizations)
	s.router.HandleFunc("/api/v1/organizations/{id}", s.handleOrganizationOperations)
	s.router.HandleFunc("/api/v1/organizations/{id}/members", s.handleOrganizationMembers)
	s.router.HandleFunc("/api/v1/organizations/{id}/members/{user_id}", s.handleOrganizationMember)
	s.router.HandleFunc("/api/v1/organizations/{id}/invitations", s.handleOrganizationInvitations)
	s.router.HandleFunc("/api/v1/organizations/{id}/invitations/{invitation_id}", s.handleRevokeOrganizationInvitation)
	s.router.HandleFunc("/api/v1/invitations/accept", s.handleAcceptOrganizationInvitation)

	// Building endpoints
	s.router.HandleFunc("/api/v1/buildings", s.handleBuildings)
	s.router.HandleFunc("/api/v1/buildings/{id}", s.handleBuildingOperations)

	// Equipment endpoints
	s.router.HandleFunc("/api/v1/equipment", s.handleEquipment)
	s.router.HandleFunc("/api/v1/equipment/{id}", s.handleEquipmentOperations)

	// Sync endpoints
	s.router.HandleFunc("/api/v1/sync/push", s.HandleSyncPush)
	s.router.HandleFunc("/api/v1/sync/pull", s.HandleSyncPull)
	s.router.HandleFunc("/api/v1/sync/status", s.HandleSyncStatus)

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

	// Apply local rate limiting (cycle-free)
	rps := float64(s.config.RateLimit.RequestsPerMinute) / 60.0
	if rps <= 0 {
		rps = 100.0 / 60.0
	}
	burst := s.config.RateLimit.BurstSize
	if burst <= 0 {
		burst = 10
	}
	ipRL := newIPRateLimiter(rps, burst)
	handler = ipRL.Middleware(handler)

	return handler
}

// --- simple in-package IP-based rate limiter to avoid import cycles ---

type ipRateLimiter struct {
	visitors map[string]*rate.Limiter
	burst    int
	rate     rate.Limit
	mu       sync.RWMutex
}

func newIPRateLimiter(rps float64, burst int) *ipRateLimiter {
	return &ipRateLimiter{
		visitors: make(map[string]*rate.Limiter),
		burst:    burst,
		rate:     rate.Limit(rps),
	}
}

func (l *ipRateLimiter) getLimiter(key string) *rate.Limiter {
	l.mu.RLock()
	lim, ok := l.visitors[key]
	l.mu.RUnlock()
	if ok {
		return lim
	}
	lim = rate.NewLimiter(l.rate, l.burst)
	l.mu.Lock()
	l.visitors[key] = lim
	l.mu.Unlock()
	return lim
}

func (l *ipRateLimiter) clientID(r *http.Request) string {
	if ip := r.Header.Get("X-Forwarded-For"); ip != "" {
		return ip
	}
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}
	return r.RemoteAddr
}

func (l *ipRateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		lim := l.getLimiter(l.clientID(r))
		if !lim.Allow() {
			w.WriteHeader(http.StatusTooManyRequests)
			w.Write([]byte(`{"error":"rate limit exceeded"}`))
			return
		}
		next.ServeHTTP(w, r)
	})
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

// Response helpers are defined in helpers.go

// authenticate verifies the request authentication and returns the user
func (s *Server) authenticate(r *http.Request) (*user.User, error) {
	// Extract token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return nil, fmt.Errorf("authorization header required")
	}

	// Parse Bearer token
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || parts[0] != "Bearer" {
		return nil, fmt.Errorf("invalid authorization header format")
	}

	token := parts[1]
	if token == "" {
		return nil, fmt.Errorf("token required")
	}

	// Validate token with auth service
	claims, err := s.services.Auth.ValidateTokenClaims(r.Context(), token)
	if err != nil {
		return nil, err
	}

	// Get user from database
	apiUser, err := s.services.User.GetUser(r.Context(), claims.UserID)
	if err != nil {
		return nil, err
	}

	// Convert API User to user.User
	userID, err := uuid.Parse(apiUser.ID)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID: %w", err)
	}

	return &user.User{
		ID:       userID,
		Email:    apiUser.Email,
		FullName: apiUser.Name,
		Role:     apiUser.Role,
		Status:   "active",
	}, nil
}

// parseIntParam parses an integer parameter with default and max values
func parseIntParam(param string, defaultVal, maxVal int) int {
	if param == "" {
		return defaultVal
	}

	val, err := strconv.Atoi(param)
	if err != nil || val < 0 {
		return defaultVal
	}

	if val > maxVal {
		return maxVal
	}

	return val
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

// Combined handlers that dispatch based on HTTP method

// handleUsers handles /api/v1/users
func (s *Server) handleUsers(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetUsers(w, r)
	case http.MethodPost:
		s.handleCreateUser(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleUserOperations handles /api/v1/users/{id}
func (s *Server) handleUserOperations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetUser(w, r)
	case http.MethodPut:
		s.handleUpdateUser(w, r)
	case http.MethodDelete:
		s.handleDeleteUser(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleUserSessions handles /api/v1/users/{id}/sessions
func (s *Server) handleUserSessions(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetUserSessions(w, r)
	case http.MethodDelete:
		s.handleRevokeUserSessions(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleOrganizations handles /api/v1/organizations
func (s *Server) handleOrganizations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetOrganizations(w, r)
	case http.MethodPost:
		s.handleCreateOrganization(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleOrganizationOperations handles /api/v1/organizations/{id}
func (s *Server) handleOrganizationOperations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetOrganization(w, r)
	case http.MethodPut:
		s.handleUpdateOrganization(w, r)
	case http.MethodDelete:
		s.handleDeleteOrganization(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleOrganizationMembers handles /api/v1/organizations/{id}/members
func (s *Server) handleOrganizationMembers(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetOrganizationMembers(w, r)
	case http.MethodPost:
		s.handleAddOrganizationMember(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleOrganizationMember handles /api/v1/organizations/{id}/members/{user_id}
func (s *Server) handleOrganizationMember(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodPut:
		s.handleUpdateOrganizationMember(w, r)
	case http.MethodDelete:
		s.handleRemoveOrganizationMember(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleOrganizationInvitations handles /api/v1/organizations/{id}/invitations
func (s *Server) handleOrganizationInvitations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleGetOrganizationInvitations(w, r)
	case http.MethodPost:
		s.handleCreateOrganizationInvitation(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleBuildings handles /api/v1/buildings
func (s *Server) handleBuildings(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.HandleListBuildings(w, r)
	case http.MethodPost:
		s.HandleCreateBuilding(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}

// handleEquipment handles /api/v1/equipment
func (s *Server) handleEquipment(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.HandleListEquipment(w, r)
	case http.MethodPost:
		s.HandleCreateEquipment(w, r)
	default:
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
	}
}
