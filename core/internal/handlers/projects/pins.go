package projects

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arxos/arxos/core/internal/models"

	"github.com/go-chi/chi/v5"
)

// POST /api/pins
func CreatePin(w http.ResponseWriter, r *http.Request) {
	var req struct {
		ProjectID uint    `json:"project_id"`
		FloorID   uint    `json:"floor_id"`
		MessageID uint    `json:"message_id"`
		X         float64 `json:"x"`
		Y         float64 `json:"y"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid input", http.StatusBadRequest)
		return
	}
	// TODO: get user from context/session if needed
	createdBy := uint(0)
	pin := models.Pin{
		ProjectID: req.ProjectID,
		FloorID:   req.FloorID,
		MessageID: req.MessageID,
		X:         req.X,
		Y:         req.Y,
		CreatedBy: createdBy,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	if err := models.DB.Create(&pin).Error; err != nil {
		http.Error(w, "Failed to create pin", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(pin)
}

// GET /api/pins?floor_id=123
func GetPinsForFloor(w http.ResponseWriter, r *http.Request) {
	floorIDStr := r.URL.Query().Get("floor_id")
	if floorIDStr == "" {
		http.Error(w, "Missing floor_id", http.StatusBadRequest)
		return
	}
	var floorID uint
	_, err := fmt.Sscanf(floorIDStr, "%d", &floorID)
	if err != nil {
		http.Error(w, "Invalid floor_id", http.StatusBadRequest)
		return
	}
	var pins []models.Pin
	if err := models.DB.Where("floor_id = ?", floorID).Find(&pins).Error; err != nil {
		http.Error(w, "Failed to fetch pins", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(pins)
}

// PATCH /api/pins/{id}
func UpdatePinPosition(w http.ResponseWriter, r *http.Request) {
	idStr := chi.URLParam(r, "id")
	var pinID uint
	_, err := fmt.Sscanf(idStr, "%d", &pinID)
	if err != nil {
		http.Error(w, "Invalid pin id", http.StatusBadRequest)
		return
	}
	var req struct {
		X float64 `json:"x"`
		Y float64 `json:"y"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid input", http.StatusBadRequest)
		return
	}
	var pin models.Pin
	if err := models.DB.First(&pin, pinID).Error; err != nil {
		http.Error(w, "Pin not found", http.StatusNotFound)
		return
	}
	pin.X = req.X
	pin.Y = req.Y
	pin.UpdatedAt = time.Now()
	if err := models.DB.Save(&pin).Error; err != nil {
		http.Error(w, "Failed to update pin", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(pin)
}
