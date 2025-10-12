package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// IFCHandler handles IFC-related HTTP requests
type IFCHandler struct {
	BaseHandler
	ifcUC  *usecase.IFCUseCase
	logger domain.Logger
}

// NewIFCHandler creates a new IFC handler
func NewIFCHandler(server *types.Server, ifcUC *usecase.IFCUseCase, logger domain.Logger) *IFCHandler {
	return &IFCHandler{
		BaseHandler: nil, // Will be injected by container
		ifcUC:       ifcUC,
		logger:      logger,
	}
}

// ImportIFC handles POST /api/v1/ifc/import
func (h *IFCHandler) ImportIFC(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusAccepted, time.Since(start))
	}()

	h.logger.Info("Import IFC requested")

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req struct {
		RepositoryID string `json:"repository_id"`
		IFCData      string `json:"ifc_data"` // Base64 encoded IFC data
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Validate required fields
	if req.RepositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id is required"))
		return
	}
	if req.IFCData == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("ifc_data is required"))
		return
	}

	// Decode base64 IFC data
	ifcData := []byte(req.IFCData) // In real implementation, decode base64

	// Call use case
	importResult, err := h.ifcUC.ImportIFC(r.Context(), req.RepositoryID, ifcData)
	if err != nil {
		h.logger.Error("Failed to import IFC", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusAccepted, importResult)
}

// ValidateIFC handles POST /api/v1/ifc/validate
func (h *IFCHandler) ValidateIFC(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Validate IFC requested")

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req struct {
		IFCFileID string `json:"ifc_file_id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Validate required fields
	if req.IFCFileID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("ifc_file_id is required"))
		return
	}

	// Call use case
	validationResult, err := h.ifcUC.ValidateIFC(r.Context(), req.IFCFileID)
	if err != nil {
		h.logger.Error("Failed to validate IFC", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	h.RespondJSON(w, http.StatusOK, validationResult)
}

// GetServiceStatus handles GET /api/v1/ifc/status
func (h *IFCHandler) GetServiceStatus(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get IFC service status requested")

	// Call use case
	status := h.ifcUC.GetServiceStatus(r.Context())

	// Return response
	h.RespondJSON(w, http.StatusOK, status)
}

// ExportIFC handles POST /api/v1/ifc/export
func (h *IFCHandler) ExportIFC(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Export IFC requested")

	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building ID is required"))
		return
	}

	// Export IFC from use case
	ifcData, err := h.ifcUC.ExportIFC(r.Context(), buildingID)
	if err != nil {
		h.logger.Error("IFC export failed", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return IFC file as download
	w.Header().Set("Content-Type", "application/x-step")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=building-%s.ifc", buildingID))
	w.WriteHeader(http.StatusOK)
	w.Write(ifcData)
}

// GetImportJob handles GET /api/v1/ifc/import/{job_id}
func (h *IFCHandler) GetImportJob(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Get import job requested")

	jobID := chi.URLParam(r, "job_id")
	if jobID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("job ID is required"))
		return
	}

	// Return stub response (async job tracking not yet implemented)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"job_id":    jobID,
		"status":    "unknown",
		"message":   "Async job tracking not yet implemented. IFC imports are currently synchronous.",
		"createdAt": time.Now(),
	})
}

// GetExportJob handles GET /api/v1/ifc/export/{job_id}
func (h *IFCHandler) GetExportJob(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Get export job requested")

	jobID := chi.URLParam(r, "job_id")
	if jobID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("job ID is required"))
		return
	}

	// Return stub response (async job tracking not yet implemented)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"job_id":    jobID,
		"status":    "unknown",
		"message":   "Async job tracking not yet implemented. IFC exports are currently synchronous.",
		"createdAt": time.Now(),
	})
}

// ListImportJobs handles GET /api/v1/ifc/import
func (h *IFCHandler) ListImportJobs(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("List import jobs requested")

	// Return empty list (async job tracking not yet implemented)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"jobs":    []any{},
		"total":   0,
		"message": "Async job tracking not yet implemented. IFC imports are currently synchronous.",
	})
}

// ListExportJobs handles GET /api/v1/ifc/export
func (h *IFCHandler) ListExportJobs(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("List export jobs requested")

	// Return empty list (async job tracking not yet implemented)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"jobs":    []any{},
		"total":   0,
		"message": "Async job tracking not yet implemented. IFC exports are currently synchronous.",
	})
}

// CancelImportJob handles DELETE /api/v1/ifc/import/{job_id}
func (h *IFCHandler) CancelImportJob(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Cancel import job requested")

	jobID := chi.URLParam(r, "job_id")
	if jobID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("job ID is required"))
		return
	}

	// Return stub response (async job tracking not yet implemented)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"job_id":  jobID,
		"message": "Async job tracking not yet implemented. Cannot cancel synchronous operations.",
	})
}

// CancelExportJob handles DELETE /api/v1/ifc/export/{job_id}
func (h *IFCHandler) CancelExportJob(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Cancel export job requested")

	jobID := chi.URLParam(r, "job_id")
	if jobID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("job ID is required"))
		return
	}

	// Return stub response (async job tracking not yet implemented)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"job_id":  jobID,
		"message": "Async job tracking not yet implemented. Cannot cancel synchronous operations.",
	})
}

// GetImportJobLogs handles GET /api/v1/ifc/import/{job_id}/logs
func (h *IFCHandler) GetImportJobLogs(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Get import job logs requested")

	jobID := chi.URLParam(r, "job_id")
	if jobID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("job ID is required"))
		return
	}

	// Return empty logs (async job tracking not yet implemented)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"job_id":  jobID,
		"logs":    []string{},
		"message": "Async job tracking not yet implemented. No logs available for synchronous operations.",
	})
}

// GetExportJobLogs handles GET /api/v1/ifc/export/{job_id}/logs
func (h *IFCHandler) GetExportJobLogs(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNotImplemented, time.Since(start))
	}()

	h.logger.Info("Get export job logs requested")

	jobID := chi.URLParam(r, "job_id")
	if jobID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("job ID is required"))
		return
	}

	// Return empty logs (async job tracking not yet implemented)
	h.RespondJSON(w, http.StatusOK, map[string]any{
		"job_id":  jobID,
		"logs":    []string{},
		"message": "Async job tracking not yet implemented. No logs available for synchronous operations.",
	})
}
