package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"path/filepath"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"arx/services/export"
	"arx/utils"
)

// ExportHandler handles export-related HTTP requests
type ExportHandler struct {
	exportService *export.ExportService
}

// NewExportHandler creates a new export handler
func NewExportHandler(exportService *export.ExportService) *ExportHandler {
	return &ExportHandler{
		exportService: exportService,
	}
}

// ExportDataRequest represents export data request
type ExportDataRequest struct {
	Data       map[string]interface{} `json:"data" binding:"required"`
	OutputPath string                 `json:"output_path" binding:"required"`
	Format     export.ExportFormat    `json:"format" binding:"required"`
	Config     *export.ExportConfig   `json:"config"`
}

// ExportDataResponse represents export data response
type ExportDataResponse struct {
	Success    bool                   `json:"success"`
	OutputPath string                 `json:"output_path"`
	FileSize   int64                  `json:"file_size"`
	ExportTime float64                `json:"export_time"`
	Metadata   map[string]interface{} `json:"metadata"`
	Error      string                 `json:"error,omitempty"`
}

// BatchExportRequest represents batch export request
type BatchExportRequest struct {
	Exports []ExportDataRequest `json:"exports" binding:"required"`
}

// ValidateExportRequest represents export validation request
type ValidateExportRequest struct {
	Data   map[string]interface{} `json:"data" binding:"required"`
	Format export.ExportFormat    `json:"format" binding:"required"`
}

// ValidateExportResponse represents export validation response
type ValidateExportResponse struct {
	Valid   bool   `json:"valid"`
	Message string `json:"message"`
}

// ExportProgressResponse represents export progress response
type ExportProgressResponse struct {
	JobID     string                 `json:"job_id"`
	Status    string                 `json:"status"`
	Progress  float64                `json:"progress"`
	Message   string                 `json:"message"`
	StartTime time.Time              `json:"start_time"`
	EndTime   *time.Time             `json:"end_time,omitempty"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// ExportStatisticsResponse represents export statistics response
type ExportStatisticsResponse struct {
	TotalExports      int64                `json:"total_exports"`
	SuccessfulExports int64                `json:"successful_exports"`
	FailedExports     int64                `json:"failed_exports"`
	AverageExportTime float64              `json:"average_export_time"`
	FormatUsage       map[string]int64     `json:"format_usage"`
	RecentExports     []ExportDataResponse `json:"recent_exports"`
}

// RegisterExportRoutes registers export routes
func (h *ExportHandler) RegisterExportRoutes(router chi.Router) {
	router.Route("/api/v1/export", func(r chi.Router) {
		// Export data to various formats
		r.Post("/data", utils.ToChiHandler(h.ExportData))
		r.Post("/ifc", utils.ToChiHandler(h.ExportToIFC))
		r.Post("/gltf", utils.ToChiHandler(h.ExportToGLTF))
		r.Post("/dxf", utils.ToChiHandler(h.ExportToDXF))
		r.Post("/step", utils.ToChiHandler(h.ExportToSTEP))
		r.Post("/iges", utils.ToChiHandler(h.ExportToIGES))
		r.Post("/parasolid", utils.ToChiHandler(h.ExportToParasolid))

		// Export management
		r.Get("/formats", utils.ToChiHandler(h.GetSupportedFormats))
		r.Get("/history", utils.ToChiHandler(h.GetExportHistory))
		r.Get("/statistics", utils.ToChiHandler(h.GetExportStatistics))
		r.Post("/validate", utils.ToChiHandler(h.ValidateExportData))
		r.Post("/batch", utils.ToChiHandler(h.BatchExport))

		// Export progress and control
		r.Get("/progress/{job_id}", utils.ToChiHandler(h.GetExportProgress))
		r.Post("/cancel/{job_id}", utils.ToChiHandler(h.CancelExport))
		r.Get("/download/{filename}", utils.ToChiHandler(h.DownloadExport))
	})
}

// ExportData handles general export data requests
func (h *ExportHandler) ExportData(c *utils.ChiContext) {
	var req ExportDataRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	// Convert data to JSON
	dataJSON, err := json.Marshal(req.Data)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid data format", err.Error())
		return
	}

	// Create export job
	jobID, err := h.exportService.CreateExportJob(c.Request.Context(), dataJSON, req.OutputPath, req.Format, export.ExportQualityStandard, req.Config.CustomOptions)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create export job", err.Error())
		return
	}

	// Execute the job
	result, err := h.exportService.ExecuteExportJob(c.Request.Context(), jobID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Export failed", err.Error())
		return
	}

	errorMsg := ""
	if result.ErrorMessage != nil {
		errorMsg = *result.ErrorMessage
	}

	response := ExportDataResponse{
		Success:    result.Success,
		OutputPath: result.OutputPath,
		FileSize:   result.FileSize,
		ExportTime: result.ExportTime,
		Metadata:   result.Metadata,
		Error:      errorMsg,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ExportToIFC handles IFC export requests
func (h *ExportHandler) ExportToIFC(c *utils.ChiContext) {
	var req struct {
		Data       map[string]interface{} `json:"data" binding:"required"`
		OutputPath string                 `json:"output_path" binding:"required"`
		Options    map[string]interface{} `json:"options"`
	}

	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	// Convert data to JSON
	dataJSON, err := json.Marshal(req.Data)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid data format", err.Error())
		return
	}

	// Create export job for IFC format
	jobID, err := h.exportService.CreateExportJob(c.Request.Context(), dataJSON, req.OutputPath, export.ExportFormatIFCLite, export.ExportQualityStandard, req.Options)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create IFC export job", err.Error())
		return
	}

	// Execute the job
	result, err := h.exportService.ExecuteExportJob(c.Request.Context(), jobID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "IFC export failed", err.Error())
		return
	}

	errorMsg := ""
	if result.ErrorMessage != nil {
		errorMsg = *result.ErrorMessage
	}

	response := ExportDataResponse{
		Success:    result.Success,
		OutputPath: result.OutputPath,
		FileSize:   result.FileSize,
		ExportTime: result.ExportTime,
		Metadata:   result.Metadata,
		Error:      errorMsg,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ExportToGLTF handles GLTF export requests
func (h *ExportHandler) ExportToGLTF(c *utils.ChiContext) {
	var req struct {
		Data       map[string]interface{} `json:"data" binding:"required"`
		OutputPath string                 `json:"output_path" binding:"required"`
		Options    map[string]interface{} `json:"options"`
	}

	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	// Convert data to JSON
	dataJSON, err := json.Marshal(req.Data)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid data format", err.Error())
		return
	}

	// Create export job for GLTF format
	jobID, err := h.exportService.CreateExportJob(c.Request.Context(), dataJSON, req.OutputPath, export.ExportFormatGLTF, export.ExportQualityStandard, req.Options)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create GLTF export job", err.Error())
		return
	}

	// Execute the job
	result, err := h.exportService.ExecuteExportJob(c.Request.Context(), jobID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "GLTF export failed", err.Error())
		return
	}

	errorMsg := ""
	if result.ErrorMessage != nil {
		errorMsg = *result.ErrorMessage
	}

	response := ExportDataResponse{
		Success:    result.Success,
		OutputPath: result.OutputPath,
		FileSize:   result.FileSize,
		ExportTime: result.ExportTime,
		Metadata:   result.Metadata,
		Error:      errorMsg,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ExportToDXF handles DXF export requests
func (h *ExportHandler) ExportToDXF(c *utils.ChiContext) {
	var req struct {
		Data       map[string]interface{} `json:"data" binding:"required"`
		OutputPath string                 `json:"output_path" binding:"required"`
		Options    map[string]interface{} `json:"options"`
	}

	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	// Convert data to JSON
	dataJSON, err := json.Marshal(req.Data)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid data format", err.Error())
		return
	}

	// Create export job for DXF format
	jobID, err := h.exportService.CreateExportJob(c.Request.Context(), dataJSON, req.OutputPath, export.ExportFormatDXF, export.ExportQualityStandard, req.Options)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create DXF export job", err.Error())
		return
	}

	// Execute the job
	result, err := h.exportService.ExecuteExportJob(c.Request.Context(), jobID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "DXF export failed", err.Error())
		return
	}

	errorMsg := ""
	if result.ErrorMessage != nil {
		errorMsg = *result.ErrorMessage
	}

	response := ExportDataResponse{
		Success:    result.Success,
		OutputPath: result.OutputPath,
		FileSize:   result.FileSize,
		ExportTime: result.ExportTime,
		Metadata:   result.Metadata,
		Error:      errorMsg,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ExportToSTEP handles STEP export requests
func (h *ExportHandler) ExportToSTEP(c *utils.ChiContext) {
	var req struct {
		Data       map[string]interface{} `json:"data" binding:"required"`
		OutputPath string                 `json:"output_path" binding:"required"`
		Version    export.STEPVersion     `json:"version"`
		Options    map[string]interface{} `json:"options"`
	}

	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	if req.Version == "" {
		req.Version = export.STEPVersionAP214
	}

	result, err := h.exportService.ExportToSTEP(req.Data, req.OutputPath, req.Version, req.Options)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "STEP export failed", err.Error())
		return
	}

	response := ExportDataResponse{
		Success:    result.Success,
		OutputPath: result.OutputPath,
		FileSize:   result.FileSize,
		ExportTime: result.ExportTime,
		Metadata:   result.Metadata,
		Error:      result.Error,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ExportToIGES handles IGES export requests
func (h *ExportHandler) ExportToIGES(c *utils.ChiContext) {
	var req struct {
		Data       map[string]interface{} `json:"data" binding:"required"`
		OutputPath string                 `json:"output_path" binding:"required"`
		Options    map[string]interface{} `json:"options"`
	}

	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	result, err := h.exportService.ExportToIGES(req.Data, req.OutputPath, req.Options)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "IGES export failed", err.Error())
		return
	}

	response := ExportDataResponse{
		Success:    result.Success,
		OutputPath: result.OutputPath,
		FileSize:   result.FileSize,
		ExportTime: result.ExportTime,
		Metadata:   result.Metadata,
		Error:      result.Error,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// ExportToParasolid handles Parasolid export requests
func (h *ExportHandler) ExportToParasolid(c *utils.ChiContext) {
	var req struct {
		Data       map[string]interface{} `json:"data" binding:"required"`
		OutputPath string                 `json:"output_path" binding:"required"`
		Options    map[string]interface{} `json:"options"`
	}

	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	result, err := h.exportService.ExportToParasolid(req.Data, req.OutputPath, req.Options)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Parasolid export failed", err.Error())
		return
	}

	response := ExportDataResponse{
		Success:    result.Success,
		OutputPath: result.OutputPath,
		FileSize:   result.FileSize,
		ExportTime: result.ExportTime,
		Metadata:   result.Metadata,
		Error:      result.Error,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// GetSupportedFormats returns list of supported export formats
func (h *ExportHandler) GetSupportedFormats(c *utils.ChiContext) {
	formats, err := h.exportService.GetSupportedFormats()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get formats", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{"formats": formats})
}

// GetExportHistory returns export history
func (h *ExportHandler) GetExportHistory(c *utils.ChiContext) {
	limitStr := c.Reader.Query("limit")
	if limitStr == "" {
		limitStr = "50"
	}

	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid limit parameter", "")
		return
	}

	history, err := h.exportService.GetExportHistory(limit)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get history", err.Error())
		return
	}

	var responses []ExportDataResponse
	for _, result := range history {
		response := ExportDataResponse{
			Success:    result.Success,
			OutputPath: result.OutputPath,
			FileSize:   result.FileSize,
			ExportTime: result.ExportTime,
			Metadata:   result.Metadata,
			Error:      result.Error,
		}
		responses = append(responses, response)
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{"history": responses})
}

// GetExportStatistics returns export statistics
func (h *ExportHandler) GetExportStatistics(c *utils.ChiContext) {
	statistics, err := h.exportService.GetExportStatistics()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get statistics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, statistics)
}

// ValidateExportData validates export data
func (h *ExportHandler) ValidateExportData(c *utils.ChiContext) {
	var req ValidateExportRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	valid, message, err := h.exportService.ValidateExportData(req.Data, req.Format)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Validation failed", err.Error())
		return
	}

	response := ValidateExportResponse{
		Valid:   valid,
		Message: message,
	}

	c.Writer.JSON(http.StatusOK, response)
}

// BatchExport handles batch export requests
func (h *ExportHandler) BatchExport(c *utils.ChiContext) {
	var req BatchExportRequest
	if err := c.Reader.ShouldBindJSON(&req); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request", err.Error())
		return
	}

	// Convert to service format
	exports := make([]map[string]interface{}, len(req.Exports))
	for i, exp := range req.Exports {
		exports[i] = map[string]interface{}{
			"data":        exp.Data,
			"output_path": exp.OutputPath,
			"format":      exp.Format,
			"config":      exp.Config,
		}
	}

	results, err := h.exportService.BatchExport(exports)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Batch export failed", err.Error())
		return
	}

	var responses []ExportDataResponse
	for _, result := range results {
		response := ExportDataResponse{
			Success:    result.Success,
			OutputPath: result.OutputPath,
			FileSize:   result.FileSize,
			ExportTime: result.ExportTime,
			Metadata:   result.Metadata,
			Error:      result.Error,
		}
		responses = append(responses, response)
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{"results": responses})
}

// GetExportProgress returns export progress for a specific job
func (h *ExportHandler) GetExportProgress(c *utils.ChiContext) {
	jobID := c.Reader.Param("job_id")
	if jobID == "" {
		c.Writer.Error(http.StatusBadRequest, "Job ID is required", "")
		return
	}

	progress, err := h.exportService.GetExportProgress(jobID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get progress", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, progress)
}

// CancelExport cancels an export job
func (h *ExportHandler) CancelExport(c *utils.ChiContext) {
	jobID := c.Reader.Param("job_id")
	if jobID == "" {
		c.Writer.Error(http.StatusBadRequest, "Job ID is required", "")
		return
	}

	err := h.exportService.CancelExport(jobID)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to cancel export", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, map[string]interface{}{"message": "Export cancelled successfully"})
}

// DownloadExport downloads an exported file
func (h *ExportHandler) DownloadExport(c *utils.ChiContext) {
	filename := c.Reader.Param("filename")
	if filename == "" {
		c.Writer.Error(http.StatusBadRequest, "Filename is required", "")
		return
	}

	// Validate filename for security
	if !isValidFilename(filename) {
		c.Writer.Error(http.StatusBadRequest, "Invalid filename", "")
		return
	}

	fileData, err := h.exportService.DownloadExport(filename)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to download file", err.Error())
		return
	}

	// Set appropriate headers
	c.Writer.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
	c.Writer.Header().Set("Content-Type", getContentType(filename))
	c.Writer.Write(http.StatusOK, getContentType(filename), fileData)
}

// Helper functions

// isValidFilename validates filename for security
func isValidFilename(filename string) bool {
	// Basic validation - check for path traversal and invalid characters
	if filename == "" || len(filename) > 255 {
		return false
	}

	// Check for path traversal attempts
	if filepath.Clean(filename) != filename {
		return false
	}

	// Check for invalid characters
	for _, char := range filename {
		if char < 32 || char > 126 {
			return false
		}
	}

	return true
}

// getContentType returns content type based on file extension
func getContentType(filename string) string {
	ext := filepath.Ext(filename)
	switch ext {
	case ".ifc":
		return "application/ifc"
	case ".gltf", ".glb":
		return "model/gltf-binary"
	case ".dxf":
		return "application/dxf"
	case ".step", ".stp":
		return "application/step"
	case ".iges", ".igs":
		return "application/iges"
	case ".x_t", ".xmt_txt":
		return "application/parasolid"
	case ".xlsx", ".xls":
		return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
	case ".parquet":
		return "application/octet-stream"
	case ".geojson":
		return "application/geo+json"
	default:
		return "application/octet-stream"
	}
}
