package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"strings"

	"arx/db"
	"arx/models"
)

type AdminDeviceRequest struct {
	ID           string `json:"id"`
	Building     string `json:"building"`
	Floor        string `json:"floor"`
	System       string `json:"system"`
	Type         string `json:"type"`
	Instance     int    `json:"instance"`
	PanelID      string `json:"panel_id"`
	CircuitID    string `json:"circuit_id"`
	UpstreamID   string `json:"upstream_id"`
	DownstreamID string `json:"downstream_id"`
	PipeID       string `json:"pipe_id"`
	UserID       int    `json:"user_id"` // For audit/logging
}

// POST /api/admin/device
func AdminCreateDevice(w http.ResponseWriter, r *http.Request) {
	var req AdminDeviceRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON payload", http.StatusBadRequest)
		log.Printf("[ADMIN] Invalid JSON payload: %v", err)
		return
	}
	if !models.IsValidObjectId(req.ID) {
		errMsg := "Invalid object ID format: " + req.ID
		http.Error(w, errMsg, http.StatusBadRequest)
		_ = models.LogChange(db.DB, uint(req.UserID), "Device", req.ID, "validation_failed", map[string]interface{}{
			"error":   errMsg,
			"request": req,
		})
		log.Printf("[ADMIN] Validation failed for user %d: %s", req.UserID, errMsg)
		return
	}
	valid, invalidFields := models.ValidateMetadataLinks(map[string]string{
		"panel_id":      req.PanelID,
		"circuit_id":    req.CircuitID,
		"upstream_id":   req.UpstreamID,
		"downstream_id": req.DownstreamID,
		"pipe_id":       req.PipeID,
	})
	if !valid {
		errMsg := "Invalid metadata link field(s): " + strings.Join(invalidFields, ", ")
		http.Error(w, errMsg, http.StatusBadRequest)
		_ = models.LogChange(db.DB, uint(req.UserID), "Device", req.ID, "validation_failed", map[string]interface{}{
			"error":          errMsg,
			"invalid_fields": invalidFields,
			"request":        req,
		})
		log.Printf("[ADMIN] Validation failed for user %d: %s (object %s)", req.UserID, errMsg, req.ID)
		return
	}
	// Create device in database
	device := models.Device{
		ID:        req.ID,
		Type:      req.Type,
		System:    req.System,
		ProjectID: 1, // Default project ID - should be configurable
		CreatedBy: uint(req.UserID),
		Status:    "active",
		// Add geometry and other fields as needed
	}

	if err := db.DB.Create(&device).Error; err != nil {
		log.Printf("[ADMIN] Failed to create device: %v", err)
		http.Error(w, "Failed to create device", http.StatusInternalServerError)
		return
	}

	// Log the change
	_ = models.LogChange(db.DB, uint(req.UserID), "Device", req.ID, "created", map[string]interface{}{
		"device": device,
		"user":   req.UserID,
	})

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "created",
		"device":  device,
		"message": "Device created successfully",
	})
}
