// handlers/user.go
package handlers

import (
	"encoding/json"
	"net/http"
	"os"
	"time"

	"arxline/db"
	"arxline/middleware/auth"
	"arxline/models"

	"github.com/go-chi/chi/v5"
	"github.com/golang-jwt/jwt/v4"
	"golang.org/x/crypto/bcrypt"
)

type AuthRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type AuthResponse struct {
	Token string `json:"token"`
}

func Register(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	json.NewDecoder(r.Body).Decode(&req)

	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		http.Error(w, "Hash error", 500)
		return
	}

	user := models.User{Email: req.Email, Password: string(hash)}
	if err := db.DB.Create(&user).Error; err != nil {
		http.Error(w, "User exists or DB error", 400)
		return
	}

	token, _ := auth.GenerateJWT(user.ID)
	json.NewEncoder(w).Encode(AuthResponse{Token: token})
}

func Login(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	json.NewDecoder(r.Body).Decode(&req)

	var user models.User
	err := db.DB.Where("email = ?", req.Email).First(&user).Error
	if err != nil {
		http.Error(w, "Invalid credentials", 400)
		return
	}

	err = bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password))
	if err != nil {
		http.Error(w, "Invalid credentials", 400)
		return
	}

	token, _ := auth.GenerateJWT(user.ID)
	json.NewEncoder(w).Encode(AuthResponse{Token: token})
}

func Me(w http.ResponseWriter, r *http.Request) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		http.Error(w, "Missing token", http.StatusUnauthorized)
		return
	}
	tokenStr := authHeader[7:]
	claims := &auth.Claims{}
	token, err := jwt.ParseWithClaims(tokenStr, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(os.Getenv("JWT_SECRET")), nil
	})
	if err != nil || !token.Valid {
		http.Error(w, "Invalid token", http.StatusUnauthorized)
		return
	}
	var user models.User
	if err := db.DB.First(&user, claims.UserID).Error; err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}
	json.NewEncoder(w).Encode(user)
}

// ListBuildings returns all buildings owned by the current user
func ListBuildings(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var buildings []models.Building
	db.DB.Where("owner_id = ?", userID).Find(&buildings)
	json.NewEncoder(w).Encode(buildings)
}

// CreateBuilding creates a new building (Owner only)
func CreateBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var b models.Building
	if err := json.NewDecoder(r.Body).Decode(&b); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	b.OwnerID = userID
	if err := db.DB.Create(&b).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(b)
}

// GetBuilding returns details for a specific building (owner only)
func GetBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	idParam := chi.URLParam(r, "id")
	var b models.Building
	if err := db.DB.First(&b, idParam).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	json.NewEncoder(w).Encode(b)
}

// UpdateBuilding updates building metadata (owner only)
func UpdateBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	idParam := chi.URLParam(r, "id")
	var b models.Building
	if err := db.DB.First(&b, idParam).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	var update models.Building
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	b.Name = update.Name
	b.Address = update.Address
	if err := db.DB.Save(&b).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(b)
}

// ListFloors returns all floors for a given building (owner only)
func ListFloors(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	buildingID := chi.URLParam(r, "id")
	var b models.Building
	if err := db.DB.First(&b, buildingID).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	var floors []models.Floor
	db.DB.Where("building_id = ?", buildingID).Find(&floors)
	json.NewEncoder(w).Encode(floors)
}

// SubmitMarkup allows a user to submit a markup for a building/floor
func SubmitMarkup(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var m models.Markup
	if err := json.NewDecoder(r.Body).Decode(&m); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	m.UserID = userID
	m.CreatedAt = time.Now()
	if err := db.DB.Create(&m).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(m)
}

// GetLogs returns all logs for a building
func GetLogs(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	buildingID := chi.URLParam(r, "building_id")
	var b models.Building
	if err := db.DB.First(&b, buildingID).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	var logs []models.Log
	db.DB.Where("building_id = ?", buildingID).Order("created_at desc").Find(&logs)
	json.NewEncoder(w).Encode(logs)
}
