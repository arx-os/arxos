package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/arx-os/arxos/internal/api/types"
	"github.com/arx-os/arxos/internal/common/logger"
)

// HandleLogin handles user login
func HandleLogin(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if s.Services.Auth == nil {
		s.RespondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}

	response, err := s.Services.Auth.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		s.RespondError(w, http.StatusUnauthorized, "Invalid credentials")
		return
		}

		s.RespondJSON(w, http.StatusOK, response)
	}
}

// HandleLogout handles user logout
func HandleLogout(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Extract token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		s.RespondError(w, http.StatusUnauthorized, "Authorization header required")
		return
	}

	// Parse Bearer token
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || parts[0] != "Bearer" {
		s.RespondError(w, http.StatusUnauthorized, "Invalid authorization header format")
		return
	}

	token := parts[1]
	if token == "" {
		s.RespondError(w, http.StatusUnauthorized, "Token required")
		return
	}

	if s.Services.Auth == nil {
		s.RespondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}

	// Revoke the token (delete session)
	if err := s.Services.Auth.RevokeToken(r.Context(), token); err != nil {
		logger.Error("Failed to revoke token: %v", err)
		// Don't expose internal errors, just return success
		// Token might already be invalid
	}

		s.RespondJSON(w, http.StatusOK, map[string]interface{}{
			"success": true,
			"message": "Logged out successfully",
		})
	}
}

// HandleRefresh handles token refresh
func HandleRefresh(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		RefreshToken string `json:"refresh_token"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if req.RefreshToken == "" {
		s.RespondError(w, http.StatusBadRequest, "Refresh token is required")
		return
	}

	if s.Services.Auth == nil {
		s.RespondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}

	// Refresh the token
	accessToken, refreshToken, err := s.Services.Auth.RefreshToken(r.Context(), req.RefreshToken)
	if err != nil {
		logger.Error("Token refresh failed: %v", err)
		s.RespondError(w, http.StatusUnauthorized, "Invalid or expired refresh token")
		return
	}

		s.RespondJSON(w, http.StatusOK, map[string]interface{}{
			"access_token":  accessToken,
			"refresh_token": refreshToken,
		})
	}
}

// HandleRegister handles user registration
func HandleRegister(s *types.Server) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.RespondError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
		Name     string `json:"name"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if s.Services.Auth == nil {
		s.RespondError(w, http.StatusNotImplemented, "Authentication service not configured")
		return
	}

	user, err := s.Services.Auth.Register(r.Context(), req.Email, req.Password, req.Name)
	if err != nil {
		s.RespondError(w, http.StatusBadRequest, "Registration failed")
		return
	}

		s.RespondJSON(w, http.StatusCreated, user)
	}
}
