// handlers/user.go
package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/arxos/arxos/core/backend/db"
	"github.com/arxos/arxos/core/backend/models"

	"github.com/go-chi/chi/v5"
	"golang.org/x/crypto/bcrypt"
)

type AuthRequest struct {
	Login    string `json:"login"`
	Email    string `json:"email"`
	Username string `json:"username"`
	Password string `json:"password"`
}

type LegacyAuthResponse struct {
	Token string `json:"token"`
}

func getUserIDFromToken(r *http.Request) (uint, error) {
	token := r.Header.Get("Authorization")
	if token == "" {
		return 0, fmt.Errorf("no token provided")
	}
	// TODO: Implement proper JWT token validation
	// For now, return a mock user ID
	return 1, nil
}

func Register(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
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
	}

	if err := db.DB.Create(&user).Error; err != nil {
		http.Error(w, "User creation failed", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
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

	// TODO: Generate proper JWT token
	token := "mock-jwt-token-" + fmt.Sprintf("%d", user.ID)

	resp := LegacyAuthResponse{Token: token}
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
