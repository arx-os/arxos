package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
)

// ComponentHandler handles component-related HTTP requests
type ComponentHandler struct {
	*types.BaseHandler
	componentUC component.ComponentService
	logger      domain.Logger
}

// NewComponentHandler creates a new component handler
func NewComponentHandler(server *types.Server, componentUC component.ComponentService, logger domain.Logger) *ComponentHandler {
	return &ComponentHandler{
		BaseHandler: types.NewBaseHandler(server),
		componentUC: componentUC,
		logger:      logger,
	}
}

// ListComponents handles GET /api/v1/components
func (h *ComponentHandler) ListComponents(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("List components requested")

	// Parse query parameters
	limit := 10
	offset := 0
	buildingID := r.URL.Query().Get("building_id")
	componentType := r.URL.Query().Get("type")
	status := r.URL.Query().Get("status")

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
	filter := component.ComponentFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Set optional filters
	if buildingID != "" {
		filter.Building = buildingID
	}
	if componentType != "" {
		// Convert string to ComponentType if needed
		filter.Type = (*component.ComponentType)(&componentType)
	}
	if status != "" {
		// Convert string to ComponentStatus if needed
		filter.Status = (*component.ComponentStatus)(&status)
	}

	// Call use case
	components, err := h.componentUC.ListComponents(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to list components", "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response
	response := map[string]interface{}{
		"components": components,
		"limit":      limit,
		"offset":     offset,
		"filters": map[string]interface{}{
			"building_id": buildingID,
			"type":        componentType,
			"status":      status,
		},
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// CreateComponent handles POST /api/v1/components
func (h *ComponentHandler) CreateComponent(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create component requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req component.CreateComponentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Call use case
	component, err := h.componentUC.CreateComponent(r.Context(), req)
	if err != nil {
		h.logger.Error("Failed to create component", "error", err)

		// Check for validation errors
		if err.Error() == "component name is required" || err.Error() == "building ID is required" {
			h.HandleError(w, r, err, http.StatusBadRequest)
			return
		}

		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusCreated, component)
}

// GetComponent handles GET /api/v1/components/{id}
func (h *ComponentHandler) GetComponent(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get component requested")

	componentID := chi.URLParam(r, "id")
	if componentID == "" {
		h.HandleError(w, r, fmt.Errorf("component ID is required"), http.StatusBadRequest)
		return
	}

	// Call use case
	component, err := h.componentUC.GetComponent(r.Context(), componentID)
	if err != nil {
		h.logger.Error("Failed to get component", "component_id", componentID, "error", err)

		// Check for not found
		if err.Error() == "component not found" {
			h.HandleError(w, r, err, http.StatusNotFound)
			return
		}

		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusOK, component)
}

// UpdateComponent handles PUT /api/v1/components/{id}
func (h *ComponentHandler) UpdateComponent(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Update component requested")

	componentID := chi.URLParam(r, "id")
	if componentID == "" {
		h.HandleError(w, r, fmt.Errorf("component ID is required"), http.StatusBadRequest)
		return
	}

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req component.UpdateComponentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Set the ID from URL parameter
	req.ID = componentID

	// Call use case
	component, err := h.componentUC.UpdateComponent(r.Context(), req)
	if err != nil {
		h.logger.Error("Failed to update component", "component_id", componentID, "error", err)

		// Check for validation errors
		if err.Error() == "component name is required" {
			h.HandleError(w, r, err, http.StatusBadRequest)
			return
		}

		// Check for not found
		if err.Error() == "component not found" {
			h.HandleError(w, r, err, http.StatusNotFound)
			return
		}

		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusOK, component)
}

// DeleteComponent handles DELETE /api/v1/components/{id}
func (h *ComponentHandler) DeleteComponent(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	h.logger.Info("Delete component requested")

	componentID := chi.URLParam(r, "id")
	if componentID == "" {
		h.HandleError(w, r, fmt.Errorf("component ID is required"), http.StatusBadRequest)
		return
	}

	// Call use case
	err := h.componentUC.DeleteComponent(r.Context(), componentID)
	if err != nil {
		h.logger.Error("Failed to delete component", "component_id", componentID, "error", err)

		// Check for not found
		if err.Error() == "component not found" {
			h.HandleError(w, r, err, http.StatusNotFound)
			return
		}

		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusNoContent, nil)
}

// GetComponentsByBuilding handles GET /api/v1/buildings/{building_id}/components
func (h *ComponentHandler) GetComponentsByBuilding(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get components by building requested")

	buildingID := chi.URLParam(r, "building_id")
	if buildingID == "" {
		h.HandleError(w, r, fmt.Errorf("building ID is required"), http.StatusBadRequest)
		return
	}

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
	filter := component.ComponentFilter{
		Limit:    limit,
		Offset:   offset,
		Building: buildingID,
	}

	// Call use case
	components, err := h.componentUC.ListComponents(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to get components by building", "building_id", buildingID, "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response
	response := map[string]interface{}{
		"building_id": buildingID,
		"components":  components,
		"limit":       limit,
		"offset":      offset,
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// UpdateComponentStatus handles PATCH /api/v1/components/{id}/status
func (h *ComponentHandler) UpdateComponentStatus(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Update component status requested")

	componentID := chi.URLParam(r, "id")
	if componentID == "" {
		h.HandleError(w, r, fmt.Errorf("component ID is required"), http.StatusBadRequest)
		return
	}

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req struct {
		Status string `json:"status"`
		Notes  string `json:"notes,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Convert string to ComponentStatus
	status := component.ComponentStatus(req.Status)

	// Call use case
	err := h.componentUC.UpdateStatus(r.Context(), componentID, status, "api_user")
	if err != nil {
		h.logger.Error("Failed to update component status", "component_id", componentID, "error", err)

		// Check for not found
		if err.Error() == "component not found" {
			h.HandleError(w, r, err, http.StatusNotFound)
			return
		}

		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Get updated component
	updatedComponent, err := h.componentUC.GetComponent(r.Context(), componentID)
	if err != nil {
		h.logger.Error("Failed to get updated component", "component_id", componentID, "error", err)
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusOK, updatedComponent)
}

// GetComponentHistory handles GET /api/v1/components/{id}/history
func (h *ComponentHandler) GetComponentHistory(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Get component history requested")

	componentID := chi.URLParam(r, "id")
	if componentID == "" {
		h.HandleError(w, r, fmt.Errorf("component ID is required"), http.StatusBadRequest)
		return
	}

	// TODO: Implement GetComponentHistory in use case
	h.HandleError(w, r, fmt.Errorf("component history functionality not yet implemented"), http.StatusNotImplemented)
}
