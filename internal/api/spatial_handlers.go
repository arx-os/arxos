package api

import (
	"encoding/json"
	"net/http"

	"github.com/arx-os/arxos/internal/database"
	"github.com/go-chi/chi/v5"
)

// SpatialHandlers handles AR anchor and spatial endpoints
type SpatialHandlers struct {
	db *database.SQLiteDB
}

// NewSpatialHandlers creates new spatial handlers
func NewSpatialHandlers(db *database.SQLiteDB) *SpatialHandlers {
	return &SpatialHandlers{db: db}
}

// Routes returns the spatial routes
func (h *SpatialHandlers) Routes() chi.Router {
	r := chi.NewRouter()

	r.Post("/anchors", h.CreateAnchor)
	r.Get("/anchors/{buildingUUID}/{equipmentPath}", h.GetAnchor)
	r.Put("/anchors/{buildingUUID}/{equipmentPath}", h.UpdateAnchor)
	r.Delete("/anchors/{buildingUUID}/{equipmentPath}", h.DeleteAnchor)
	r.Get("/anchors/nearby", h.FindNearbyAnchors)

	return r
}

// CreateAnchor handles POST /api/v1/spatial/anchors
func (h *SpatialHandlers) CreateAnchor(w http.ResponseWriter, r *http.Request) {
	var anchor database.SpatialAnchor
	if err := json.NewDecoder(r.Body).Decode(&anchor); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Get user from context
	userID := r.Context().Value("user_id").(string)
	anchor.CreatedBy = userID

	// Save anchor
	if err := h.db.SaveSpatialAnchor(r.Context(), &anchor); err != nil {
		http.Error(w, "Failed to save anchor", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(anchor)
}

// GetAnchor handles GET /api/v1/spatial/anchors/{buildingUUID}/{equipmentPath}
func (h *SpatialHandlers) GetAnchor(w http.ResponseWriter, r *http.Request) {
	buildingUUID := chi.URLParam(r, "buildingUUID")
	equipmentPath := chi.URLParam(r, "equipmentPath")

	anchor, err := h.db.GetSpatialAnchor(r.Context(), buildingUUID, equipmentPath)
	if err != nil {
		http.Error(w, "Anchor not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(anchor)
}

// UpdateAnchor handles PUT /api/v1/spatial/anchors/{buildingUUID}/{equipmentPath}
func (h *SpatialHandlers) UpdateAnchor(w http.ResponseWriter, r *http.Request) {
	buildingUUID := chi.URLParam(r, "buildingUUID")
	equipmentPath := chi.URLParam(r, "equipmentPath")

	var anchor database.SpatialAnchor
	if err := json.NewDecoder(r.Body).Decode(&anchor); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Ensure correct IDs
	anchor.BuildingUUID = buildingUUID
	anchor.EquipmentPath = equipmentPath

	// Update anchor
	if err := h.db.SaveSpatialAnchor(r.Context(), &anchor); err != nil {
		http.Error(w, "Failed to update anchor", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// DeleteAnchor handles DELETE /api/v1/spatial/anchors/{buildingUUID}/{equipmentPath}
func (h *SpatialHandlers) DeleteAnchor(w http.ResponseWriter, r *http.Request) {
	buildingUUID := chi.URLParam(r, "buildingUUID")
	equipmentPath := chi.URLParam(r, "equipmentPath")

	if err := h.db.DeleteSpatialAnchor(r.Context(), buildingUUID, equipmentPath); err != nil {
		http.Error(w, "Failed to delete anchor", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// FindNearbyAnchors handles GET /api/v1/spatial/anchors/nearby?building={uuid}&x={x}&y={y}&floor={floor}&radius={radius}
func (h *SpatialHandlers) FindNearbyAnchors(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()

	buildingUUID := q.Get("building")
	x := parseFloat(q.Get("x"), 0)
	y := parseFloat(q.Get("y"), 0)
	floor := parseInt(q.Get("floor"), 1)
	radius := parseFloat(q.Get("radius"), 10)

	anchors, err := h.db.FindNearbyAnchors(r.Context(), buildingUUID, x, y, floor, radius)
	if err != nil {
		http.Error(w, "Failed to find anchors", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(anchors)
}

// Helper functions
func parseFloat(s string, defaultVal float64) float64 {
	// Implementation would parse string to float64
	return defaultVal
}

func parseInt(s string, defaultVal int) int {
	// Implementation would parse string to int
	return defaultVal
}
