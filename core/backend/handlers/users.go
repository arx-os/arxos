// handlers/user.go
package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"

	"github.com/arxos/arxos/core/backend/db"
	"github.com/arxos/arxos/core/backend/middleware/auth"
	"github.com/arxos/arxos/core/backend/models"
	"github.com/golang-jwt/jwt/v4"

	"github.com/go-chi/chi/v5"
	"golang.org/x/crypto/bcrypt"
)

type AuthRequest struct {
	Login    string `json:"login"`
	Email    string `json:"email"`
	Username string `json:"username"`
	Password string `json:"password"`
}

type AuthResponse struct {
	Token string `json:"token"`
}

// getUserFromContext extracts user info from JWT claims in context
func getUserFromContext(ctx context.Context) (*auth.Claims, error) {
	claims, ok := ctx.Value("claims").(*auth.Claims)
	if !ok {
		return nil, fmt.Errorf("no claims in context")
	}
	return claims, nil
}

// getUserIDFromToken validates JWT and extracts user ID
func getUserIDFromToken(r *http.Request) (uint, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return 0, fmt.Errorf("no authorization header")
	}

	tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
	if tokenStr == authHeader {
		return 0, fmt.Errorf("invalid authorization header format")
	}

	// Parse and validate token
	claims := &auth.Claims{}
	token, err := jwt.ParseWithClaims(tokenStr, claims, func(token *jwt.Token) (interface{}, error) {
		// Validate signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		// Get JWT secret from environment
		jwtSecret := []byte(os.Getenv("JWT_SECRET"))
		if len(jwtSecret) == 0 {
			// Use a default for development, but log warning
			jwtSecret = []byte("arxos-default-secret-change-in-production")
		}
		return jwtSecret, nil
	})

	if err != nil {
		return 0, fmt.Errorf("token validation failed: %w", err)
	}

	if !token.Valid {
		return 0, fmt.Errorf("invalid token")
	}

	return claims.UserID, nil
}

func Register(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if req.Username == "" || req.Email == "" || req.Password == "" {
		http.Error(w, "Username, email, and password are required", http.StatusBadRequest)
		return
	}

	// Check if user already exists
	var existingUser models.User
	if err := db.DB.Where("username = ? OR email = ?", req.Username, req.Email).First(&existingUser).Error; err == nil {
		http.Error(w, "User with this username or email already exists", http.StatusConflict)
		return
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		http.Error(w, "Password hashing failed", http.StatusInternalServerError)
		return
	}

	user := models.User{
		Username: req.Username,
		Email:    req.Email,
		Password: string(hashedPassword),
		Role:     "user", // Default role
	}

	if err := db.DB.Create(&user).Error; err != nil {
		http.Error(w, "User creation failed", http.StatusInternalServerError)
		return
	}

	// Generate JWT token for immediate login
	token, err := auth.GenerateJWT(user.ID, user.Role)
	if err != nil {
		// User created but token generation failed - still return success
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"user":    user,
			"message": "User created successfully. Please login.",
		})
		return
	}

	// Return user info with token
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"user":  user,
		"token": token,
	})
}

func Login(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}

	var user models.User
	if err := db.DB.Where("username = ? OR email = ?", req.Login, req.Login).First(&user).Error; err != nil {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password)); err != nil {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}

	// Generate proper JWT token using the auth package
	token, err := auth.GenerateJWT(user.ID, user.Role)
	if err != nil {
		http.Error(w, "Failed to generate token", http.StatusInternalServerError)
		return
	}

	resp := AuthResponse{Token: token}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func Me(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var user models.User
	if err := db.DB.First(&user, userID).Error; err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
}

// User-specific functions only - building functions moved to buildings.go
func SubmitMarkup(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var markup models.Markup
	if err := json.NewDecoder(r.Body).Decode(&markup); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}

	markup.UserID = userID
	if err := db.DB.Create(&markup).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(markup)
}

func ListMarkups(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var markups []models.Markup
	if err := db.DB.Where("user_id = ?", userID).Find(&markups).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(markups)
}

func GetLogs(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get logs for user's buildings
	var logs []models.Log
	query := db.DB.Joins("JOIN buildings ON buildings.id = logs.building_id").
		Where("buildings.owner_id = ?", userID).
		Order("logs.created_at DESC").
		Limit(100)

	if err := query.Find(&logs).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(logs)
}

// HTMX-specific user functions
func HTMXListBuildings(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var buildings []models.Building
	if err := db.DB.Where("owner_id = ?", userID).Find(&buildings).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/html")
	// TODO: Render HTMX template
	fmt.Fprintf(w, "<div>Buildings for user %d</div>", userID)
}

func HTMXListFloors(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	buildingID := chi.URLParam(r, "buildingID")
	var floors []models.Floor
	query := db.DB.Joins("JOIN buildings ON buildings.id = floors.building_id").
		Where("buildings.owner_id = ? AND floors.building_id = ?", userID, buildingID)

	if err := query.Find(&floors).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/html")
	// TODO: Render HTMX template
	fmt.Fprintf(w, "<div>Floors for building %s</div>", buildingID)
}
