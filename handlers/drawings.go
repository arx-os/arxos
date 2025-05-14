// handlers/drawings.go
package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"arxline/db"
	"arxline/models"
	"os"

	"github.com/go-chi/chi/v5"
	"github.com/golang-jwt/jwt/v4"
)

func getUserIDFromToken(r *http.Request) (uint, error) {
	tokenStr := r.Header.Get("Authorization")[7:]
	token, _ := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
		return []byte(os.Getenv("JWT_SECRET")), nil
	})
	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		return uint(claims["user_id"].(float64)), nil
	}
	return 0, http.ErrNoCookie
}

func ListDrawings(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "projectID")
	var drawings []models.Drawing
	db.DB.Where("project_id = ?", projectID).Find(&drawings)
	json.NewEncoder(w).Encode(drawings)
}

func CreateDrawing(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	projectIDStr := chi.URLParam(r, "projectID")
	projectID, err := strconv.Atoi(projectIDStr)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}

	var drawing models.Drawing
	if err := json.NewDecoder(r.Body).Decode(&drawing); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	drawing.ProjectID = uint(projectID)
	db.DB.Create(&drawing)
	json.NewEncoder(w).Encode(drawing)
}

func GetDrawing(w http.ResponseWriter, r *http.Request) {
	drawingIDStr := chi.URLParam(r, "drawingID")
	drawingID, err := strconv.Atoi(drawingIDStr)
	if err != nil {
		http.Error(w, "Invalid drawing ID", http.StatusBadRequest)
		return
	}

	var drawing models.Drawing
	if err := db.DB.First(&drawing, drawingID).Error; err != nil {
		http.Error(w, "Drawing not found", http.StatusNotFound)
		return
	}
	json.NewEncoder(w).Encode(drawing)
}
