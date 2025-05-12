// handlers/user.go
package handlers

import (
	"encoding/json"
	"net/http"

	"arxline/db"
	"arxline/middleware/auth"
	"arxline/models"

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
