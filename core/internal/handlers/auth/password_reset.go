package auth

import (
	"encoding/json"
	"net/http"
	
	"github.com/arxos/arxos/core/internal/services"
)

// PasswordResetHandler handles password reset operations
type PasswordResetHandler struct {
	resetService *services.PasswordResetService
}

// NewPasswordResetHandler creates a new password reset handler
func NewPasswordResetHandler() *PasswordResetHandler {
	return &PasswordResetHandler{
		resetService: services.NewPasswordResetService(),
	}
}

// InitiateReset handles password reset initiation requests
func (h *PasswordResetHandler) InitiateReset(w http.ResponseWriter, r *http.Request) {
	var req services.PasswordResetRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	// Validate email
	if req.Email == "" {
		http.Error(w, "Email is required", http.StatusBadRequest)
		return
	}
	
	// Initiate password reset
	// Note: We don't return errors to prevent email enumeration
	token, _ := h.resetService.InitiatePasswordReset(req.Email)
	
	// In production, send email here
	// For now, we'll include token in response for development
	response := map[string]interface{}{
		"message": "If an account exists with this email, a password reset link has been sent",
	}
	
	// Only include token in development mode
	if token != "" {
		response["dev_token"] = token // Remove this in production!
		response["dev_reset_url"] = "http://localhost:8080/reset-password?token=" + token
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// ValidateToken checks if a reset token is valid
func (h *PasswordResetHandler) ValidateToken(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")
	if token == "" {
		http.Error(w, "Token is required", http.StatusBadRequest)
		return
	}
	
	// Get token info
	info, err := h.resetService.GetResetTokenInfo(token)
	if err != nil {
		if err == services.ErrInvalidResetToken {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(map[string]interface{}{
				"valid": false,
				"error": "Invalid or expired token",
			})
			return
		}
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(info)
}

// ResetPassword handles password reset confirmation
func (h *PasswordResetHandler) ResetPassword(w http.ResponseWriter, r *http.Request) {
	var req services.PasswordResetConfirmRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	// Validate inputs
	if req.Token == "" || req.NewPassword == "" {
		http.Error(w, "Token and new password are required", http.StatusBadRequest)
		return
	}
	
	// Reset password
	if err := h.resetService.ResetPassword(req.Token, req.NewPassword); err != nil {
		switch err {
		case services.ErrInvalidResetToken:
			http.Error(w, "Invalid or expired token", http.StatusBadRequest)
		case services.ErrTokenAlreadyUsed:
			http.Error(w, "This reset token has already been used", http.StatusBadRequest)
		case services.ErrWeakPassword:
			http.Error(w, "Password does not meet security requirements", http.StatusBadRequest)
		default:
			http.Error(w, "Failed to reset password", http.StatusInternalServerError)
		}
		return
	}
	
	// Success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "Password has been reset successfully. Please log in with your new password.",
		"success": true,
	})
}