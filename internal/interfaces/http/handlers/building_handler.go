package handlers

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase/integration"
	"github.com/arx-os/arxos/internal/usecase/building"
)

// BuildingHandler handles building-related HTTP requests following Clean Architecture
type BuildingHandler struct {
	BaseHandler
	buildingUC *building.BuildingUseCase
	ifcUC      *integration.IFCUseCase
	logger     domain.Logger
}

// NewBuildingHandler creates a new building handler with proper dependency injection
func NewBuildingHandler(
	base BaseHandler,
	buildingUC *building.BuildingUseCase,
	ifcUC *integration.IFCUseCase,
	logger domain.Logger,
) *BuildingHandler {
	return &BuildingHandler{
		BaseHandler: base,
		buildingUC:  buildingUC,
		ifcUC:       ifcUC,
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
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response using BaseHandler
	response := map[string]any{
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

	// Validate content type and parse request body
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	var req domain.CreateBuildingRequest
	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Call use case
	building, err := h.buildingUC.CreateBuilding(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to create building", "error", err)

		// Use DomainError type system for proper error categorization
		if domainErr := domain.GetDomainError(err); domainErr != nil {
			switch domainErr.Type {
			case domain.ErrorTypeValidation:
				h.RespondError(w, http.StatusBadRequest, err)
				return
			case domain.ErrorTypeNotFound:
				h.RespondError(w, http.StatusNotFound, err)
				return
			case domain.ErrorTypeConflict:
				h.RespondError(w, http.StatusConflict, err)
				return
			case domain.ErrorTypeUnauthorized:
				h.RespondError(w, http.StatusUnauthorized, err)
				return
			}
		}

		h.RespondError(w, http.StatusInternalServerError, err)
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
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building ID is required"))
		return
	}

	// Validate ID format (must be valid UUID)
	id := types.FromString(buildingID)
	if !id.IsUUID() {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid building ID format"))
		return
	}

	// Call use case
	building, err := h.buildingUC.GetBuilding(r.Context(), id)
	if err != nil {
		h.logger.Error("Failed to get building", "building_id", buildingID, "error", err)

		// Return 404 if building not found
		if err.Error() == "building not found" || strings.Contains(err.Error(), "not found") {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
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
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building ID is required"))
		return
	}

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	var req domain.UpdateBuildingRequest
	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Set building ID from URL parameter
	req.ID = types.FromString(buildingID)

	// Call use case
	building, err := h.buildingUC.UpdateBuilding(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to update building", "building_id", buildingID, "error", err)

		// Check for validation errors
		if err.Error() == "building name is required" {
			h.RespondError(w, http.StatusBadRequest, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
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
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building ID is required"))
		return
	}

	// Call use case
	err := h.buildingUC.DeleteBuilding(r.Context(), buildingID)
	if err != nil {
		h.logger.Error("Failed to delete building", "building_id", buildingID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
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
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building ID is required"))
		return
	}

	// Parse multipart form data for IFC file upload
	if err := r.ParseMultipartForm(32 << 20); err != nil { // 32 MB max
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("failed to parse multipart form: %v", err))
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("file is required: %v", err))
		return
	}
	defer file.Close()

	h.logger.Info("Received IFC file", "filename", header.Filename, "size", header.Size)

	// Read file data
	fileData := make([]byte, header.Size)
	if _, err := file.Read(fileData); err != nil {
		h.RespondError(w, http.StatusInternalServerError, fmt.Errorf("failed to read file: %v", err))
		return
	}

	// Import via IFC use case
	result, err := h.ifcUC.ImportIFC(r.Context(), buildingID, fileData)
	if err != nil {
		h.logger.Error("IFC import failed", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.logger.Info("IFC import successful", "repository_id", result.RepositoryID, "ifc_file_id", result.IFCFileID)
	h.RespondJSON(w, http.StatusOK, result)
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
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building ID is required"))
		return
	}

	// Get export format from query params (default to "json")
	format := r.URL.Query().Get("format")
	if format == "" {
		format = "json"
	}

	// Export via building use case
	data, err := h.buildingUC.ExportBuilding(r.Context(), buildingID, format)
	if err != nil {
		h.logger.Error("Building export failed", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Set appropriate content type based on format
	var contentType string
	switch format {
	case "json":
		contentType = "application/json"
	case "csv":
		contentType = "text/csv"
	case "ifc":
		contentType = "application/x-step"
	default:
		contentType = "application/octet-stream"
	}

	w.Header().Set("Content-Type", contentType)
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=building-%s.%s", buildingID, format))
	w.WriteHeader(http.StatusOK)
	w.Write(data)
}
