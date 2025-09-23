package api

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
)

// handleLogin handles user login
func (s *Server) handleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if s.services.Auth == nil {
		s.respondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}

	response, err := s.services.Auth.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Invalid credentials")
		return
	}

	s.respondJSON(w, http.StatusOK, response)
}

// handleLogout handles user logout
func (s *Server) handleLogout(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Extract token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		s.respondError(w, http.StatusUnauthorized, "Authorization header required")
		return
	}

	// Parse Bearer token
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || parts[0] != "Bearer" {
		s.respondError(w, http.StatusUnauthorized, "Invalid authorization header format")
		return
	}

	token := parts[1]
	if token == "" {
		s.respondError(w, http.StatusUnauthorized, "Token required")
		return
	}

	if s.services.Auth == nil {
		s.respondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}

	// Revoke the token (delete session)
	if err := s.services.Auth.RevokeToken(r.Context(), token); err != nil {
		logger.Error("Failed to revoke token: %v", err)
		// Don't expose internal errors, just return success
		// Token might already be invalid
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Logged out successfully",
	})
}

// handleRefresh handles token refresh
func (s *Server) handleRefresh(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		RefreshToken string `json:"refresh_token"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if req.RefreshToken == "" {
		s.respondError(w, http.StatusBadRequest, "Refresh token is required")
		return
	}

	if s.services.Auth == nil {
		s.respondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}

	// Refresh the token
	response, err := s.services.Auth.RefreshToken(r.Context(), req.RefreshToken)
	if err != nil {
		logger.Error("Token refresh failed: %v", err)
		s.respondError(w, http.StatusUnauthorized, "Invalid or expired refresh token")
		return
	}

	s.respondJSON(w, http.StatusOK, response)
}

// handleRegister handles user registration
func (s *Server) handleRegister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.respondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
		Name     string `json:"name"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if s.services.Auth == nil {
		s.respondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}

	user, err := s.services.Auth.Register(r.Context(), req.Email, req.Password, req.Name)
	if err != nil {
		s.respondError(w, http.StatusBadRequest, "Registration failed")
		return
	}

	s.respondJSON(w, http.StatusCreated, user)
}
