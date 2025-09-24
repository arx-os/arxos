package handlers

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/api/types"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// AuthHandler handles authentication-related HTTP requests
type AuthHandler struct {
	server *types.Server
}

// NewAuthHandler creates a new auth handler
func NewAuthHandler(server *types.Server) *AuthHandler {
	return &AuthHandler{
		server: server,
	}
}

// HandleLogin handles POST /api/v1/auth/login
func (h *AuthHandler) HandleLogin(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.server.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse request
	var req domainmodels.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.server.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.server.ValidateRequest(req); err != nil {
		h.server.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Authenticate user
	authResult, err := h.server.Services.Auth.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		h.server.RespondError(w, http.StatusUnauthorized, "Invalid credentials")
		return
	}

	// Convert to response format
	if user, ok := authResult.(*domainmodels.User); ok {
		// Generate tokens
		accessToken, err := h.server.Services.Auth.GenerateToken(r.Context(), user.ID, user.Email, string(user.Role), "")
		if err != nil {
			h.server.RespondError(w, http.StatusInternalServerError, "Failed to generate access token")
			return
		}

		refreshToken, err := h.server.Services.Auth.GenerateToken(r.Context(), user.ID, user.Email, string(user.Role), "")
		if err != nil {
			h.server.RespondError(w, http.StatusInternalServerError, "Failed to generate refresh token")
			return
		}

		// Convert domain user to API user
		apiUser := &models.User{
			ID:        user.ID,
			Email:     user.Email,
			Name:      user.FullName,
			Role:      user.Role,
			Active:    user.IsActive,
			CreatedAt: user.CreatedAt,
			UpdatedAt: user.UpdatedAt,
		}

		response := models.AuthResponse{
			AccessToken:  accessToken,
			RefreshToken: refreshToken,
			ExpiresIn:    3600, // 1 hour
			TokenType:    "Bearer",
			User:         apiUser,
		}

		h.server.RespondJSON(w, http.StatusOK, response)
	} else {
		h.server.RespondError(w, http.StatusInternalServerError, "Invalid user data")
	}
}

// HandleLogout handles POST /api/v1/auth/logout
func (h *AuthHandler) HandleLogout(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.server.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		h.server.RespondError(w, http.StatusBadRequest, "Authorization header required")
		return
	}

	// Extract token (assuming "Bearer <token>" format)
	token := authHeader
	if len(authHeader) > 7 && authHeader[:7] == "Bearer " {
		token = authHeader[7:]
	}

	// Logout user
	if err := h.server.Services.Auth.Logout(r.Context(), token); err != nil {
		h.server.RespondError(w, http.StatusInternalServerError, "Failed to logout")
		return
	}

	h.server.RespondJSON(w, http.StatusOK, map[string]string{"message": "Logged out successfully"})
}

// HandleRefresh handles POST /api/v1/auth/refresh
func (h *AuthHandler) HandleRefresh(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.server.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse request
	var req domainmodels.TokenRefreshRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.server.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Refresh token
	accessToken, refreshToken, err := h.server.Services.Auth.RefreshToken(r.Context(), req.RefreshToken)
	if err != nil {
		h.server.RespondError(w, http.StatusUnauthorized, "Failed to refresh token")
		return
	}

	// For now, return a simple response without user data
	// In a real implementation, you would extract user info from the token
	response := models.AuthResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresIn:    3600, // 1 hour
		TokenType:    "Bearer",
		User:         nil, // User data would be extracted from token
	}

	h.server.RespondJSON(w, http.StatusOK, response)
}

// HandleRegister handles POST /api/v1/auth/register
func (h *AuthHandler) HandleRegister(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.server.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse request
	var req domainmodels.UserCreateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.server.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.server.ValidateRequest(req); err != nil {
		h.server.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Register user
	user, err := h.server.Services.Auth.Register(r.Context(), req.Email, req.Password, req.Username)
	if err != nil {
		h.server.RespondError(w, http.StatusInternalServerError, "Failed to register user")
		return
	}

	// Convert interface{} to domain user
	domainUser, ok := user.(*domainmodels.User)
	if !ok {
		h.server.RespondError(w, http.StatusInternalServerError, "Invalid user data")
		return
	}

	// Generate tokens
	accessToken, err := h.server.Services.Auth.GenerateToken(r.Context(), domainUser.ID, domainUser.Email, string(domainUser.Role), "")
	if err != nil {
		h.server.RespondError(w, http.StatusInternalServerError, "Failed to generate access token")
		return
	}

	refreshToken, err := h.server.Services.Auth.GenerateToken(r.Context(), domainUser.ID, domainUser.Email, string(domainUser.Role), "")
	if err != nil {
		h.server.RespondError(w, http.StatusInternalServerError, "Failed to generate refresh token")
		return
	}

	// Convert domain user to API user
	apiUser := &models.User{
		ID:        domainUser.ID,
		Email:     domainUser.Email,
		Name:      domainUser.FullName,
		Role:      domainUser.Role,
		Active:    domainUser.IsActive,
		CreatedAt: domainUser.CreatedAt,
		UpdatedAt: domainUser.UpdatedAt,
	}

	response := models.AuthResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresIn:    3600, // 1 hour
		TokenType:    "Bearer",
		User:         apiUser,
	}

	h.server.RespondJSON(w, http.StatusCreated, response)
}

// HandleLogin is a convenience function for the server
func HandleLogin(server *types.Server) http.HandlerFunc {
	handler := NewAuthHandler(server)
	return handler.HandleLogin
}

// HandleLogout is a convenience function for the server
func HandleLogout(server *types.Server) http.HandlerFunc {
	handler := NewAuthHandler(server)
	return handler.HandleLogout
}

// HandleRefresh is a convenience function for the server
func HandleRefresh(server *types.Server) http.HandlerFunc {
	handler := NewAuthHandler(server)
	return handler.HandleRefresh
}

// HandleRegister is a convenience function for the server
func HandleRegister(server *types.Server) http.HandlerFunc {
	handler := NewAuthHandler(server)
	return handler.HandleRegister
}
