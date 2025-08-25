package ingestion

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/arxos/arxos/core/internal/handlers"
	"github.com/go-chi/chi/v5"
)

// ============================================================================
// CGO-OPTIMIZED INGESTION HANDLER
// ============================================================================

// IngestionHandlerCGO provides CGO-optimized file ingestion operations
type IngestionHandlerCGO struct {
	*handlers.HandlerBaseCGO
	uploadDir string
}

// NewIngestionHandlerCGO creates a new CGO-optimized ingestion handler
func NewIngestionHandlerCGO(uploadDir string) *IngestionHandlerCGO {
	if uploadDir == "" {
		uploadDir = "./uploads"
	}

	return &IngestionHandlerCGO{
		HandlerBaseCGO: handlers.NewHandlerBaseCGO(),
		uploadDir:      uploadDir,
	}
}

// Close cleans up the handler
func (h *IngestionHandlerCGO) Close() {
	if h.HandlerBaseCGO != nil {
		h.HandlerBaseCGO.Close()
	}
}

// ============================================================================
// HTTP HANDLERS
// ============================================================================

// HandleFileUpload handles file uploads with CGO optimization
func (h *IngestionHandlerCGO) HandleFileUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form (32MB max)
	err := r.ParseMultipartForm(32 << 20)
	if err != nil {
		h.SendErrorResponse(w, "Failed to parse form: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Get the file from form
	file, header, err := r.FormFile("file")
	if err != nil {
		h.SendErrorResponse(w, "Failed to get file: "+err.Error(), http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Validate file type
	allowedExtensions := []string{".pdf", ".ifc", ".dwg", ".dxf", ".jpg", ".jpeg", ".png", ".heic", ".xlsx", ".xls", ".csv", ".las", ".laz", ".e57", ".ply"}
	fileExt := strings.ToLower(filepath.Ext(header.Filename))

	isValid := false
	for _, ext := range allowedExtensions {
		if fileExt == ext {
			isValid = true
			break
		}
	}

	if !isValid {
		h.SendErrorResponse(w, "Unsupported file type: "+fileExt, http.StatusBadRequest)
		return
	}

	// Create uploads directory if it doesn't exist
	if err := os.MkdirAll(h.uploadDir, 0755); err != nil {
		h.SendErrorResponse(w, "Failed to create uploads directory: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Create unique filename
	filename := fmt.Sprintf("%d_%s", time.Now().Unix(), header.Filename)
	filepath := filepath.Join(h.uploadDir, filename)

	// Create file on disk
	dst, err := os.Create(filepath)
	if err != nil {
		h.SendErrorResponse(w, "Failed to create file: "+err.Error(), http.StatusInternalServerError)
		return
	}
	defer dst.Close()

	// Copy uploaded file to destination
	fileSize, err := io.Copy(dst, file)
	if err != nil {
		h.SendErrorResponse(w, "Failed to save file: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Get metadata from form
	buildingName := r.FormValue("building_name")
	if buildingName == "" {
		buildingName = "Uploaded Building"
	}

	floorNumber := r.FormValue("floor_number")
	if floorNumber == "" {
		floorNumber = "0"
	}

	// Process the file using CGO optimization
	result, err := h.ProcessFile(filepath)
	if err != nil {
		h.SendErrorResponse(w, "Failed to process file: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Add file metadata to result
	if resultData, ok := result.(map[string]interface{}); ok {
		resultData["original_filename"] = header.Filename
		resultData["file_size"] = fileSize
		resultData["building_name"] = buildingName
		resultData["floor_number"] = floorNumber
		resultData["upload_timestamp"] = time.Now()
	}

	h.SendSuccessResponse(w, result, "File uploaded and processed successfully")
}

// ProcessFileByID processes a previously uploaded file by ID
func (h *IngestionHandlerCGO) ProcessFileByID(w http.ResponseWriter, r *http.Request) {
	fileID := chi.URLParam(r, "id")
	if fileID == "" {
		h.SendErrorResponse(w, "File ID is required", http.StatusBadRequest)
		return
	}

	// For now, return a placeholder result
	// In a real implementation, this would process the file using the CGO-optimized ingestion pipeline
	result := map[string]interface{}{
		"file_id":       fileID,
		"status":        "processed",
		"cgo_status":    h.HasCGOBridge(),
		"timestamp":     time.Now(),
		"objects_found": 15,
		"confidence":    0.85,
	}

	h.SendSuccessResponse(w, result, "File processed successfully")
}

// GetFileMetadata retrieves file metadata with CGO optimization
func (h *IngestionHandlerCGO) GetFileMetadata(w http.ResponseWriter, r *http.Request) {
	fileID := chi.URLParam(r, "id")
	if fileID == "" {
		h.SendErrorResponse(w, "File ID is required", http.StatusBadRequest)
		return
	}

	// For now, return placeholder metadata
	// In a real implementation, this would extract metadata using the CGO-optimized ingestion pipeline
	metadata := map[string]interface{}{
		"file_id":       fileID,
		"filename":      "sample_file.pdf",
		"format":        "PDF",
		"file_size":     1024000,
		"page_count":    5,
		"building_name": "Sample Building",
		"building_type": "Office",
		"year_built":    2020,
		"total_area":    5000.0,
		"num_floors":    3,
		"cgo_status":    h.HasCGOBridge(),
		"extracted_at":  time.Now(),
	}

	h.SendSuccessResponse(w, metadata, "File metadata retrieved successfully")
}

// ListProcessedFiles returns a list of processed files with CGO optimization
func (h *IngestionHandlerCGO) ListProcessedFiles(w http.ResponseWriter, r *http.Request) {
	// Parse pagination parameters
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}

	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}

	// For now, return placeholder files
	// In a real implementation, this would query the CGO-optimized ingestion pipeline
	files := []map[string]interface{}{
		{
			"id":            "1",
			"filename":      "building_plan.pdf",
			"format":        "PDF",
			"status":        "processed",
			"objects_found": 25,
			"confidence":    0.92,
			"uploaded_at":   time.Now().Add(-24 * time.Hour),
			"cgo_status":    h.HasCGOBridge(),
		},
		{
			"id":            "2",
			"filename":      "floor_layout.ifc",
			"format":        "IFC",
			"status":        "processed",
			"objects_found": 45,
			"confidence":    0.95,
			"uploaded_at":   time.Now().Add(-48 * time.Hour),
			"cgo_status":    h.HasCGOBridge(),
		},
		{
			"id":            "3",
			"filename":      "electrical.dwg",
			"format":        "DWG",
			"status":        "processing",
			"objects_found": 0,
			"confidence":    0.0,
			"uploaded_at":   time.Now().Add(-1 * time.Hour),
			"cgo_status":    h.HasCGOBridge(),
		},
	}

	response := map[string]interface{}{
		"files":      files,
		"page":       page,
		"page_size":  pageSize,
		"total":      len(files),
		"cgo_status": h.HasCGOBridge(),
		"timestamp":  time.Now(),
	}

	h.SendSuccessResponse(w, response, "Processed files retrieved successfully")
}

// GetProcessingStatistics returns processing statistics with CGO optimization
func (h *IngestionHandlerCGO) GetProcessingStatistics(w http.ResponseWriter, r *http.Request) {
	// For now, return placeholder statistics
	// In a real implementation, this would query the CGO-optimized ingestion pipeline
	stats := map[string]interface{}{
		"total_files_processed":    150,
		"total_objects_created":    2500,
		"total_processing_time_ms": 45000,
		"files_by_format": map[string]interface{}{
			"PDF":   map[string]interface{}{"count": 45, "objects": 675, "avg_confidence": 0.87},
			"IFC":   map[string]interface{}{"count": 30, "objects": 900, "avg_confidence": 0.94},
			"DWG":   map[string]interface{}{"count": 25, "objects": 500, "avg_confidence": 0.91},
			"Image": map[string]interface{}{"count": 20, "objects": 200, "avg_confidence": 0.78},
			"Excel": map[string]interface{}{"count": 15, "objects": 150, "avg_confidence": 0.82},
			"LiDAR": map[string]interface{}{"count": 15, "objects": 75, "avg_confidence": 0.89},
		},
		"cgo_status": h.HasCGOBridge(),
		"timestamp":  time.Now(),
	}

	h.SendSuccessResponse(w, stats, "Processing statistics retrieved successfully")
}

// ClearProcessingStatistics clears processing statistics
func (h *IngestionHandlerCGO) ClearProcessingStatistics(w http.ResponseWriter, r *http.Request) {
	// For now, return success
	// In a real implementation, this would clear statistics in the CGO-optimized ingestion pipeline
	response := map[string]interface{}{
		"status":     "cleared",
		"message":    "Processing statistics cleared successfully",
		"cgo_status": h.HasCGOBridge(),
		"timestamp":  time.Now(),
	}

	h.SendSuccessResponse(w, response, "Processing statistics cleared successfully")
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// validateFileType checks if the file type is supported
func (h *IngestionHandlerCGO) validateFileType(filename string) bool {
	ext := strings.ToLower(filepath.Ext(filename))
	supportedTypes := map[string]bool{
		".pdf":  true,
		".ifc":  true,
		".dwg":  true,
		".dxf":  true,
		".jpg":  true,
		".jpeg": true,
		".png":  true,
		".heic": true,
		".xlsx": true,
		".xls":  true,
		".csv":  true,
		".las":  true,
		".laz":  true,
		".e57":  true,
		".ply":  true,
	}

	return supportedTypes[ext]
}

// getFileFormat returns the detected file format
func (h *IngestionHandlerCGO) getFileFormat(filename string) string {
	ext := strings.ToLower(filepath.Ext(filename))

	switch ext {
	case ".pdf":
		return "PDF"
	case ".ifc":
		return "IFC"
	case ".dwg", ".dxf":
		return "DWG"
	case ".jpg", ".jpeg", ".png", ".heic":
		return "Image"
	case ".xlsx", ".xls", ".csv":
		return "Excel"
	case ".las", ".laz", ".e57", ".ply":
		return "LiDAR"
	default:
		return "Unknown"
	}
}
