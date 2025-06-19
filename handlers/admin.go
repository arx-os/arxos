package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"strings"

	"arxline/db"
	"arxline/models"
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
	// TODO: Save device to DB
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"status":"created"}`))
}
