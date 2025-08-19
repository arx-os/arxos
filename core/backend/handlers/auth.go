package handlers

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/arxos/arxos/core/backend/middleware"
	"github.com/arxos/arxos/core/backend/services"
	"github.com/google/uuid"
	"github.com/go-redis/redis/v8"
	"gorm.io/gorm"
)

// AuthHandler handles authentication endpoints
type AuthHandler struct {
	authService *services.AuthService
	db          *gorm.DB
}

// NewAuthHandler creates a new authentication handler
func NewAuthHandler(db *gorm.DB, redisClient *redis.Client, jwtSecret, refreshSecret string) *AuthHandler {
	return &AuthHandler{
		authService: services.NewAuthService(jwtSecret, refreshSecret, redisClient),
		db:          db,
	}
}

// LoginRequest contains login credentials
type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required,min=8"`
}

// RegisterRequest contains registration data
type RegisterRequest struct {
	Email     string `json:"email" validate:"required,email"`
	Password  string `json:"password" validate:"required,min=8"`
	FirstName string `json:"first_name" validate:"required"`
	LastName  string `json:"last_name" validate:"required"`
	Role      string `json:"role,omitempty"`
}

// RefreshRequest contains refresh token
type RefreshRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}

// AuthResponse contains authentication response data
type AuthResponse struct {
	Success      bool                  `json:"success"`
	Message      string                `json:"message,omitempty"`
	AccessToken  string                `json:"access_token,omitempty"`
	RefreshToken string                `json:"refresh_token,omitempty"`
	ExpiresAt    time.Time             `json:"expires_at,omitempty"`
	TokenType    string                `json:"token_type,omitempty"`
	User         *UserResponse         `json:"user,omitempty"`
}

// UserResponse contains user data in responses
type UserResponse struct {
	ID        string    `json:"id"`
	Email     string    `json:"email"`
	FirstName string    `json:"first_name"`
	LastName  string    `json:"last_name"`
	Role      string    `json:"role"`
	CreatedAt time.Time `json:"created_at"`
}

// Login handles user login
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondJSON(w, http.StatusBadRequest, AuthResponse{
			Success: false,
			Message: "Invalid request body",
		})
		return
	}

	// Find user by email
	var user User
	if err := h.db.Where("email = ?", req.Email).First(&user).Error; err != nil {
		respondJSON(w, http.StatusUnauthorized, AuthResponse{
			Success: false,
			Message: "Invalid email or password",
		})
		return
	}

	// Verify password
	if !h.authService.VerifyPassword(req.Password, user.PasswordHash) {
		respondJSON(w, http.StatusUnauthorized, AuthResponse{
			Success: false,
			Message: "Invalid email or password",
		})
		return
	}

	// Generate token pair
	scopes := h.getUserScopes(user.Role)
	tokenPair, err := h.authService.GenerateTokenPair(user.ID, user.Email, user.Role, scopes)
	if err != nil {
		respondJSON(w, http.StatusInternalServerError, AuthResponse{
			Success: false,
			Message: "Failed to generate tokens",
		})
		return
	}

	// Update last login
	h.db.Model(&user).Update("last_login", time.Now())

	respondJSON(w, http.StatusOK, AuthResponse{
		Success:      true,
		AccessToken:  tokenPair.AccessToken,
		RefreshToken: tokenPair.RefreshToken,
		ExpiresAt:    tokenPair.ExpiresAt,
		TokenType:    tokenPair.TokenType,
		User: &UserResponse{
			ID:        user.ID,
			Email:     user.Email,
			FirstName: user.FirstName,
			LastName:  user.LastName,
			Role:      user.Role,
			CreatedAt: user.CreatedAt,
		},
	})
}

// Register handles user registration
func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	var req RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondJSON(w, http.StatusBadRequest, AuthResponse{
			Success: false,
			Message: "Invalid request body",
		})
		return
	}

	// Check if user already exists
	var existingUser User
	if err := h.db.Where("email = ?", req.Email).First(&existingUser).Error; err == nil {
		respondJSON(w, http.StatusConflict, AuthResponse{
			Success: false,
			Message: "User with this email already exists",
		})
		return
	}

	// Hash password
	hashedPassword, err := h.authService.HashPassword(req.Password)
	if err != nil {
		respondJSON(w, http.StatusInternalServerError, AuthResponse{
			Success: false,
			Message: "Failed to process password",
		})
		return
	}

	// Set default role if not provided
	if req.Role == "" {
		req.Role = "user"
	}

	// Create user
	user := User{
		ID:           uuid.New().String(),
		Email:        req.Email,
		PasswordHash: hashedPassword,
		FirstName:    req.FirstName,
		LastName:     req.LastName,
		Role:         req.Role,
		IsActive:     true,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	if err := h.db.Create(&user).Error; err != nil {
		respondJSON(w, http.StatusInternalServerError, AuthResponse{
			Success: false,
			Message: "Failed to create user",
		})
		return
	}

	// Generate token pair
	scopes := h.getUserScopes(user.Role)
	tokenPair, err := h.authService.GenerateTokenPair(user.ID, user.Email, user.Role, scopes)
	if err != nil {
		respondJSON(w, http.StatusInternalServerError, AuthResponse{
			Success: false,
			Message: "Failed to generate tokens",
		})
		return
	}

	respondJSON(w, http.StatusCreated, AuthResponse{
		Success:      true,
		Message:      "User registered successfully",
		AccessToken:  tokenPair.AccessToken,
		RefreshToken: tokenPair.RefreshToken,
		ExpiresAt:    tokenPair.ExpiresAt,
		TokenType:    tokenPair.TokenType,
		User: &UserResponse{
			ID:        user.ID,
			Email:     user.Email,
			FirstName: user.FirstName,
			LastName:  user.LastName,
			Role:      user.Role,
			CreatedAt: user.CreatedAt,
		},
	})
}

// Refresh handles token refresh
func (h *AuthHandler) Refresh(w http.ResponseWriter, r *http.Request) {
	var req RefreshRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondJSON(w, http.StatusBadRequest, AuthResponse{
			Success: false,
			Message: "Invalid request body",
		})
		return
	}

	// Refresh the access token
	tokenPair, err := h.authService.RefreshAccessToken(req.RefreshToken)
	if err != nil {
		respondJSON(w, http.StatusUnauthorized, AuthResponse{
			Success: false,
			Message: "Invalid or expired refresh token",
		})
		return
	}

	respondJSON(w, http.StatusOK, AuthResponse{
		Success:      true,
		AccessToken:  tokenPair.AccessToken,
		RefreshToken: tokenPair.RefreshToken,
		ExpiresAt:    tokenPair.ExpiresAt,
		TokenType:    tokenPair.TokenType,
	})
}

// Logout handles user logout
func (h *AuthHandler) Logout(w http.ResponseWriter, r *http.Request) {
	// Extract token from request
	token, err := h.authService.ExtractTokenFromRequest(r)
	if err != nil {
		respondJSON(w, http.StatusOK, AuthResponse{
			Success: true,
			Message: "Logged out successfully",
		})
		return
	}

	// Revoke the token
	if err := h.authService.RevokeToken(token); err != nil {
		// Log error but still return success
		// User is effectively logged out client-side
	}

	respondJSON(w, http.StatusOK, AuthResponse{
		Success: true,
		Message: "Logged out successfully",
	})
}

// GetProfile returns the current user's profile
func (h *AuthHandler) GetProfile(w http.ResponseWriter, r *http.Request) {
	userID := middleware.GetUserID(r)
	if userID == "" {
		respondJSON(w, http.StatusUnauthorized, AuthResponse{
			Success: false,
			Message: "Authentication required",
		})
		return
	}

	var user User
	if err := h.db.First(&user, "id = ?", userID).Error; err != nil {
		respondJSON(w, http.StatusNotFound, AuthResponse{
			Success: false,
			Message: "User not found",
		})
		return
	}

	respondJSON(w, http.StatusOK, AuthResponse{
		Success: true,
		User: &UserResponse{
			ID:        user.ID,
			Email:     user.Email,
			FirstName: user.FirstName,
			LastName:  user.LastName,
			Role:      user.Role,
			CreatedAt: user.CreatedAt,
		},
	})
}

// UpdatePassword handles password update
func (h *AuthHandler) UpdatePassword(w http.ResponseWriter, r *http.Request) {
	userID := middleware.GetUserID(r)
	if userID == "" {
		respondJSON(w, http.StatusUnauthorized, AuthResponse{
			Success: false,
			Message: "Authentication required",
		})
		return
	}

	var req struct {
		CurrentPassword string `json:"current_password" validate:"required"`
		NewPassword     string `json:"new_password" validate:"required,min=8"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondJSON(w, http.StatusBadRequest, AuthResponse{
			Success: false,
			Message: "Invalid request body",
		})
		return
	}

	var user User
	if err := h.db.First(&user, "id = ?", userID).Error; err != nil {
		respondJSON(w, http.StatusNotFound, AuthResponse{
			Success: false,
			Message: "User not found",
		})
		return
	}

	// Verify current password
	if !h.authService.VerifyPassword(req.CurrentPassword, user.PasswordHash) {
		respondJSON(w, http.StatusUnauthorized, AuthResponse{
			Success: false,
			Message: "Current password is incorrect",
		})
		return
	}

	// Hash new password
	hashedPassword, err := h.authService.HashPassword(req.NewPassword)
	if err != nil {
		respondJSON(w, http.StatusInternalServerError, AuthResponse{
			Success: false,
			Message: "Failed to process password",
		})
		return
	}

	// Update password
	if err := h.db.Model(&user).Update("password_hash", hashedPassword).Error; err != nil {
		respondJSON(w, http.StatusInternalServerError, AuthResponse{
			Success: false,
			Message: "Failed to update password",
		})
		return
	}

	respondJSON(w, http.StatusOK, AuthResponse{
		Success: true,
		Message: "Password updated successfully",
	})
}

// getUserScopes returns scopes based on user role
func (h *AuthHandler) getUserScopes(role string) []string {
	switch role {
	case "admin":
		return []string{"read", "write", "delete", "admin"}
	case "manager":
		return []string{"read", "write", "delete"}
	case "user":
		return []string{"read", "write"}
	default:
		return []string{"read"}
	}
}

// User model (should be in models package)
type User struct {
	ID           string    `gorm:"primary_key;type:uuid;default:gen_random_uuid()"`
	Email        string    `gorm:"unique;not null"`
	PasswordHash string    `gorm:"not null"`
	FirstName    string    `gorm:"not null"`
	LastName     string    `gorm:"not null"`
	Role         string    `gorm:"not null;default:'user'"`
	IsActive     bool      `gorm:"default:true"`
	LastLogin    *time.Time
	CreatedAt    time.Time
	UpdatedAt    time.Time
}

// respondJSON sends a JSON response
func respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}