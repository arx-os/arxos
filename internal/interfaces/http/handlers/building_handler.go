package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// BuildingHandler handles building-related HTTP requests
type BuildingHandler struct {
	*types.BaseHandler
	buildingUC *usecase.BuildingUseCase
	logger     domain.Logger
}

// NewBuildingHandler creates a new building handler
func NewBuildingHandler(server *types.Server, buildingUC *usecase.BuildingUseCase, logger domain.Logger) *BuildingHandler {
	return &BuildingHandler{
		BaseHandler: types.NewBaseHandler(server),
		buildingUC:  buildingUC,
		logger:      logger,
	}
}

// ListBuildings handles GET /api/v1/buildings
func (h *BuildingHandler) ListBuildings(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("List buildings requested")

	// Parse query parameters
	limit := 10
	offset := 0

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Create filter
	filter := &domain.BuildingFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Call use case
	buildings, err := h.buildingUC.ListBuildings(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to list buildings", "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response using BaseHandler
	response := map[string]interface{}{
		"buildings": buildings,
		"limit":     limit,
		"offset":    offset,
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// CreateBuilding handles POST /api/v1/buildings
func (h *BuildingHandler) CreateBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create building requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req domain.CreateBuildingRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Call use case
	building, err := h.buildingUC.CreateBuilding(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to create building", "error", err)

		// Check for validation errors
		if err.Error() == "building name is required" {
			h.HandleError(w, r, err, http.StatusBadRequest)
			return
		}

		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response using BaseHandler
	h.RespondJSON(w, http.StatusCreated, building)
}

// GetBuilding handles GET /api/v1/buildings/{id}
func (h *BuildingHandler) GetBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get building requested")

	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.HandleError(w, r, fmt.Errorf("building ID is required"), http.StatusBadRequest)
		return
	}

	// Call use case
	building, err := h.buildingUC.GetBuilding(r.Context(), buildingID)
	if err != nil {
		h.logger.Error("Failed to get building", "building_id", buildingID, "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response using BaseHandler
	h.RespondJSON(w, http.StatusOK, building)
}

// UpdateBuilding handles PUT /api/v1/buildings/{id}
func (h *BuildingHandler) UpdateBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Update building requested")

	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.HandleError(w, r, fmt.Errorf("building ID is required"), http.StatusBadRequest)
		return
	}

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req domain.UpdateBuildingRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Call use case
	building, err := h.buildingUC.UpdateBuilding(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to update building", "building_id", buildingID, "error", err)

		// Check for validation errors
		if err.Error() == "building name is required" {
			h.HandleError(w, r, err, http.StatusBadRequest)
			return
		}

		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response using BaseHandler
	h.RespondJSON(w, http.StatusOK, building)
}

// DeleteBuilding handles DELETE /api/v1/buildings/{id}
func (h *BuildingHandler) DeleteBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	h.logger.Info("Delete building requested")

	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.HandleError(w, r, fmt.Errorf("building ID is required"), http.StatusBadRequest)
		return
	}

	// Call use case
	err := h.buildingUC.DeleteBuilding(r.Context(), buildingID)
	if err != nil {
		h.logger.Error("Failed to delete building", "building_id", buildingID, "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response using BaseHandler
	h.RespondJSON(w, http.StatusNoContent, nil)
}

// ImportBuilding handles POST /api/v1/buildings/{id}/import
func (h *BuildingHandler) ImportBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Import building requested")

	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.HandleError(w, r, fmt.Errorf("building ID is required"), http.StatusBadRequest)
		return
	}

	// TODO: Implement IFC import logic
	h.HandleError(w, r, fmt.Errorf("import functionality not yet implemented"), http.StatusNotImplemented)
}

// ExportBuilding handles GET /api/v1/buildings/{id}/export
func (h *BuildingHandler) ExportBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Export building requested")

	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.HandleError(w, r, fmt.Errorf("building ID is required"), http.StatusBadRequest)
		return
	}

	// TODO: Implement IFC export logic
	h.HandleError(w, r, fmt.Errorf("export functionality not yet implemented"), http.StatusNotImplemented)
}
