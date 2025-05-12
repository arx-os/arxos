// handlers/projects.go
package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"arxline/db"
	"arxline/models"

	"github.com/go-chi/chi/v5"
	"github.com/golang-jwt/jwt/v4"
)

func getUserID(r *http.Request) (uint, error) {
	tokenStr := r.Header.Get("Authorization")[7:]
	token, _ := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
		return []byte("your-secret"), nil
	})

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		id := uint(claims["user_id"].(float64))
		return id, nil
	}
	return 0, http.ErrNoCookie
}

func ListProjects(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserID(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var projects []models.Project
	db.DB.Where("user_id = ?", userID).Find(&projects)
	json.NewEncoder(w).Encode(projects)
}

func CreateProject(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserID(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var p models.Project
	json.NewDecoder(r.Body).Decode(&p)
	p.UserID = userID
	db.DB.Create(&p)
	json.NewEncoder(w).Encode(p)
}

func GetProject(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserID(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	idParam := chi.URLParam(r, "id")
	id, err := strconv.Atoi(idParam)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	var p models.Project
	db.DB.First(&p, id)
	if p.UserID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	json.NewEncoder(w).Encode(p)
}
