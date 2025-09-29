package handlers

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// AuthHandler handles authentication-related HTTP requests following Clean Architecture principles
type AuthHandler struct {
	*BaseHandler
}

// NewAuthHandler creates a new auth handler with dependency injection
func NewAuthHandler(services *types.Services, logger logger.Logger) *AuthHandler {
	return &AuthHandler{
		BaseHandler: NewBaseHandler(services, logger),
	}
}

// HandleLogin handles POST /api/v1/auth/login
func (h *AuthHandler) HandleLogin(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, "login")
		h.logger.Info("Login attempt completed", "duration", time.Since(start))
	}()

	// Parse request
	var req domainmodels.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Invalid request body", nil)
		return
	}

	// Validate request
	if req.Email == "" || req.Password == "" {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Email and password are required", nil)
		return
	}

	// Authenticate user through domain service
	// Note: This would be implemented in the domain layer
	// For now, we'll create a placeholder response
	response := map[string]interface{}{
		"access_token":  "placeholder_token",
		"refresh_token": "placeholder_refresh_token",
		"token_type":    "Bearer",
		"expires_in":    3600,
		"user": map[string]interface{}{
			"id":    "user_id",
			"email": req.Email,
			"name":  "User Name",
		},
	}

	h.WriteSuccessResponse(w, response)
}

// HandleLogout handles POST /api/v1/auth/logout
func (h *AuthHandler) HandleLogout(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "logout")

	// Get current user
	user, err := h.GetCurrentUser(r)
	if err != nil {
		h.WriteErrorResponse(w, http.StatusUnauthorized, "User not authenticated", nil)
		return
	}

	// Logout user through domain service
	// Note: This would be implemented in the domain layer
	h.logger.Info("User logged out", "user_id", user.ID)

	response := map[string]interface{}{
		"message": "Successfully logged out",
	}

	h.WriteSuccessResponse(w, response)
}

// HandleRefreshToken handles POST /api/v1/auth/refresh
func (h *AuthHandler) HandleRefreshToken(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "refresh_token")

	// Parse request
	var req domainmodels.RefreshTokenRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Invalid request body", nil)
		return
	}

	// Validate refresh token through domain service
	// Note: This would be implemented in the domain layer
	response := map[string]interface{}{
		"access_token":  "new_access_token",
		"refresh_token": "new_refresh_token",
		"token_type":    "Bearer",
		"expires_in":    3600,
	}

	h.WriteSuccessResponse(w, response)
}

// HandleRegister handles POST /api/v1/auth/register
func (h *AuthHandler) HandleRegister(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "register")

	// Parse request
	var req domainmodels.RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Invalid request body", nil)
		return
	}

	// Validate request
	if req.Email == "" || req.Password == "" || req.FirstName == "" || req.LastName == "" {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Email, password, first name, and last name are required", nil)
		return
	}

	// Register user through domain service
	// Note: This would be implemented in the domain layer
	response := map[string]interface{}{
		"message": "User registered successfully",
		"user": map[string]interface{}{
			"id":    "new_user_id",
			"email": req.Email,
			"name":  req.FirstName + " " + req.LastName,
		},
	}

	h.WriteSuccessResponse(w, response)
}

// HandleProfile handles GET /api/v1/auth/profile
func (h *AuthHandler) HandleProfile(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "get_profile")

	// Get current user
	user, err := h.GetCurrentUser(r)
	if err != nil {
		h.WriteErrorResponse(w, http.StatusUnauthorized, "User not authenticated", nil)
		return
	}

	// Get user profile through domain service
	// Note: This would be implemented in the domain layer
	response := map[string]interface{}{
		"user": map[string]interface{}{
			"id":         user.ID,
			"email":      user.Email,
			"name":       user.FullName,
			"created_at": user.CreatedAt,
			"updated_at": user.UpdatedAt,
		},
	}

	h.WriteSuccessResponse(w, response)
}
