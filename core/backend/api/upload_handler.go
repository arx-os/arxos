// Package api provides HTTP handlers for the Arxos backend
package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"path/filepath"
	"strings"
	"time"

	"arxos/core/arxobject"
	"arxos/core/ingestion"
	"arxos/core/backend/database"
	"github.com/google/uuid"
	"github.com/gorilla/mux"
	"go.uber.org/zap"
)

// UploadHandler manages PDF upload and processing
type UploadHandler struct {
	parser      *ingestion.PDFToArxParser
	ocr         *ingestion.OCRService
	converter   *CoordinateConverter
	storage     *database.ArxObjectStore
	logger      *zap.Logger
	config      UploadConfig
}

// UploadConfig configures the upload handler
type UploadConfig struct {
	MaxFileSize      int64         `json:"max_file_size"`
	AllowedFormats   []string      `json:"allowed_formats"`
	ProcessTimeout   time.Duration `json:"process_timeout"`
	EnableOCR        bool          `json:"enable_ocr"`
	EnableValidation bool          `json:"enable_validation"`
	StorageBackend   string        `json:"storage_backend"`
}

// UploadResponse represents the API response for uploads
type UploadResponse struct {
	Success    bool              `json:"success"`
	BuildingID string            `json:"building_id"`
	Message    string            `json:"message,omitempty"`
	Statistics UploadStatistics  `json:"statistics"`
	Errors     []string          `json:"errors,omitempty"`
	ProcessingTime string        `json:"processing_time"`
}

// UploadStatistics contains processing statistics
type UploadStatistics struct {
	TotalObjects   int     `json:"total_objects"`
	Walls          int     `json:"walls"`
	Rooms          int     `json:"rooms"`
	Symbols        int     `json:"symbols"`
	TextLabels     int     `json:"text_labels"`
	ProcessingMs   int64   `json:"processing_ms"`
	MemoryUsedMB   float64 `json:"memory_used_mb"`
}

// NewUploadHandler creates a new upload handler
func NewUploadHandler(config UploadConfig, logger *zap.Logger) (*UploadHandler, error) {
	// Initialize PDF parser
	parserConfig := ingestion.PDFParserConfig{
		AutoDetectScale:    true,
		DefaultScaleFactor: 1.0,
		CoordinatePrecision: 0.1,
		AngleTolerance:     1.0,
		WallThickness:      300,
		MinWallLength:      500,
		ParallelPages:      true,
		MaxWorkers:         4,
		EnableGPU:          false,
	}
	parser := ingestion.NewPDFToArxParser(parserConfig)

	// Initialize OCR service if enabled
	var ocr *ingestion.OCRService
	if config.EnableOCR {
		ocrConfig := ingestion.OCRConfig{
			Language:      "eng",
			DPI:          300,
			EnableCache:  true,
			CacheTTL:     5 * time.Minute,
			MaxConcurrent: 2,
			Confidence:   60.0,
		}
		var err error
		ocr, err = ingestion.NewOCRService(ocrConfig)
		if err != nil {
			logger.Warn("OCR service initialization failed", zap.Error(err))
		}
	}

	// Initialize coordinate converter
	converter := NewCoordinateConverter()

	// Initialize storage
	storage, err := database.NewArxObjectStore(config.StorageBackend)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize storage: %w", err)
	}

	return &UploadHandler{
		parser:    parser,
		ocr:       ocr,
		converter: converter,
		storage:   storage,
		logger:    logger,
		config:    config,
	}, nil
}

// HandlePDFUpload processes uploaded PDF files
func (h *UploadHandler) HandlePDFUpload(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()
	ctx := r.Context()

	// Add timeout to context
	if h.config.ProcessTimeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, h.config.ProcessTimeout)
		defer cancel()
	}

	// Parse multipart form
	err := r.ParseMultipartForm(h.config.MaxFileSize)
	if err != nil {
		h.sendError(w, http.StatusBadRequest, "Failed to parse upload: %v", err)
		return
	}

	// Get uploaded file
	file, header, err := r.FormFile("pdf")
	if err != nil {
		h.sendError(w, http.StatusBadRequest, "Failed to get file: %v", err)
		return
	}
	defer file.Close()

	// Validate file
	if err := h.validateFile(header); err != nil {
		h.sendError(w, http.StatusBadRequest, "Invalid file: %v", err)
		return
	}

	// Extract metadata from form
	metadata := h.extractMetadata(r)

	// Log upload
	h.logger.Info("Processing PDF upload",
		zap.String("filename", header.Filename),
		zap.Int64("size", header.Size),
		zap.Any("metadata", metadata))

	// Process PDF
	response, err := h.processPDF(ctx, file, metadata)
	if err != nil {
		h.logger.Error("PDF processing failed",
			zap.Error(err),
			zap.String("filename", header.Filename))
		h.sendError(w, http.StatusInternalServerError, "Processing failed: %v", err)
		return
	}

	// Add processing time
	response.ProcessingTime = time.Since(startTime).String()

	// Send response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// processPDF handles the main PDF processing pipeline
func (h *UploadHandler) processPDF(ctx context.Context, file io.Reader, metadata map[string]string) (*UploadResponse, error) {
	processingStart := time.Now()
	
	// Generate building ID
	buildingID := uuid.New().String()
	
	// Update parser config with building ID
	h.parser.Config.BuildingID = parseBuildingID(buildingID)
	h.parser.Config.FloorNumber = parseFloorNumber(metadata["floor"])

	// Parse PDF to ArxObjects
	h.logger.Debug("Starting PDF parsing")
	objects, err := h.parser.ParsePDF(ctx, file)
	if err != nil {
		return nil, fmt.Errorf("PDF parsing failed: %w", err)
	}

	// Run OCR if enabled and we have an OCR service
	var ocrResults []*ingestion.RoomInfo
	if h.config.EnableOCR && h.ocr != nil {
		h.logger.Debug("Running OCR extraction")
		// This would need the rendered pages as images
		// For now, we'll skip the actual OCR processing
		// ocrResults, _ = h.runOCR(ctx, pdfPages)
	}

	// Convert coordinates from PDF to nanometers
	h.logger.Debug("Converting coordinates to nanometers")
	convertedObjects := h.convertCoordinates(objects, metadata)

	// Validate objects if enabled
	if h.config.EnableValidation {
		h.logger.Debug("Validating objects")
		validationErrors := h.validateObjects(convertedObjects)
		if len(validationErrors) > 0 {
			h.logger.Warn("Validation warnings", zap.Strings("warnings", validationErrors))
		}
	}

	// Store in database
	h.logger.Debug("Storing objects in database")
	err = h.storage.StoreBatch(ctx, buildingID, convertedObjects)
	if err != nil {
		return nil, fmt.Errorf("database storage failed: %w", err)
	}

	// Calculate statistics
	stats := h.calculateStatistics(convertedObjects, processingStart)

	// Build response
	response := &UploadResponse{
		Success:    true,
		BuildingID: buildingID,
		Message:    fmt.Sprintf("Successfully processed %d objects", len(convertedObjects)),
		Statistics: stats,
	}

	// Add OCR results if available
	if len(ocrResults) > 0 {
		response.Statistics.TextLabels = len(ocrResults)
		response.Message += fmt.Sprintf(" and extracted %d room numbers", len(ocrResults))
	}

	h.logger.Info("PDF processing completed",
		zap.String("building_id", buildingID),
		zap.Int("objects", len(convertedObjects)),
		zap.Duration("duration", time.Since(processingStart)))

	return response, nil
}

// convertCoordinates converts from normalized/pixel coordinates to nanometers
func (h *UploadHandler) convertCoordinates(objects []*arxobject.ArxObjectOptimized, metadata map[string]string) []*arxobject.ArxObjectOptimized {
	// Get scale factor from metadata or use default
	scaleFactor := h.parseScaleFactor(metadata["scale"])
	if scaleFactor == 0 {
		scaleFactor = 1.0 // 1 PDF unit = 1mm default
	}

	// Get dimensions from metadata
	buildingWidth := parseFloat(metadata["width_meters"], 100.0) // Default 100m
	buildingHeight := parseFloat(metadata["height_meters"], 100.0)

	converted := make([]*arxobject.ArxObjectOptimized, len(objects))
	
	for i, obj := range objects {
		// Create a copy
		newObj := *obj
		
		// Convert coordinates based on the coordinate system used
		if metadata["coordinate_system"] == "normalized" {
			// Convert from normalized (0-1) to nanometers
			newObj.X = h.converter.NormalizedToNanometers(float64(obj.X)/1e9, buildingWidth)
			newObj.Y = h.converter.NormalizedToNanometers(float64(obj.Y)/1e9, buildingHeight)
		} else {
			// Convert from PDF units to nanometers using scale factor
			newObj.X = int64(float64(obj.X) * scaleFactor * float64(arxobject.Millimeter))
			newObj.Y = int64(float64(obj.Y) * scaleFactor * float64(arxobject.Millimeter))
		}
		
		// Z coordinate based on floor number
		floorNumber := parseFloorNumber(metadata["floor"])
		newObj.Z = int64(floorNumber) * 3 * arxobject.Meter // 3m per floor
		
		// Dimensions are already in nanometers from the parser
		// Just ensure they're scaled correctly
		newObj.Length = int64(float64(obj.Length) * scaleFactor)
		newObj.Width = int64(float64(obj.Width) * scaleFactor)
		newObj.Height = int64(float64(obj.Height) * scaleFactor)
		
		converted[i] = &newObj
	}
	
	return converted
}

// validateObjects performs validation on ArxObjects
func (h *UploadHandler) validateObjects(objects []*arxobject.ArxObjectOptimized) []string {
	var errors []string
	
	for i, obj := range objects {
		// Check ID
		if obj.ID == 0 {
			errors = append(errors, fmt.Sprintf("Object %d: missing ID", i))
		}
		
		// Check coordinates are within reasonable bounds
		maxCoord := int64(10000 * arxobject.Meter) // 10km max
		if abs(obj.X) > maxCoord || abs(obj.Y) > maxCoord || abs(obj.Z) > maxCoord {
			errors = append(errors, fmt.Sprintf("Object %d: coordinates out of range", i))
		}
		
		// Check dimensions are positive
		if obj.Length <= 0 || obj.Width <= 0 {
			errors = append(errors, fmt.Sprintf("Object %d: invalid dimensions", i))
		}
		
		// Check type flags
		if obj.GetType() == 0 {
			errors = append(errors, fmt.Sprintf("Object %d: missing type", i))
		}
	}
	
	return errors
}

// validateFile validates the uploaded file
func (h *UploadHandler) validateFile(header *multipart.FileHeader) error {
	// Check file size
	if header.Size > h.config.MaxFileSize {
		return fmt.Errorf("file size %d exceeds maximum %d", header.Size, h.config.MaxFileSize)
	}
	
	// Check file extension
	ext := strings.ToLower(filepath.Ext(header.Filename))
	valid := false
	for _, allowed := range h.config.AllowedFormats {
		if ext == allowed {
			valid = true
			break
		}
	}
	
	if !valid {
		return fmt.Errorf("file format %s not allowed", ext)
	}
	
	return nil
}

// extractMetadata extracts metadata from the request
func (h *UploadHandler) extractMetadata(r *http.Request) map[string]string {
	metadata := make(map[string]string)
	
	// Extract from form values
	metadata["building_name"] = r.FormValue("building_name")
	metadata["floor"] = r.FormValue("floor")
	metadata["scale"] = r.FormValue("scale")
	metadata["coordinate_system"] = r.FormValue("coordinate_system")
	metadata["width_meters"] = r.FormValue("width_meters")
	metadata["height_meters"] = r.FormValue("height_meters")
	
	// Set defaults
	if metadata["coordinate_system"] == "" {
		metadata["coordinate_system"] = "normalized"
	}
	if metadata["floor"] == "" {
		metadata["floor"] = "1"
	}
	
	return metadata
}

// calculateStatistics calculates processing statistics
func (h *UploadHandler) calculateStatistics(objects []*arxobject.ArxObjectOptimized, startTime time.Time) UploadStatistics {
	stats := UploadStatistics{
		TotalObjects: len(objects),
		ProcessingMs: time.Since(startTime).Milliseconds(),
	}
	
	// Count object types
	for _, obj := range objects {
		switch obj.GetType() {
		case arxobject.StructuralWall:
			stats.Walls++
		case arxobject.Room:
			stats.Rooms++
		default:
			stats.Symbols++
		}
	}
	
	// Calculate memory usage (approximate)
	stats.MemoryUsedMB = float64(len(objects)*128) / (1024 * 1024)
	
	return stats
}

// sendError sends an error response
func (h *UploadHandler) sendError(w http.ResponseWriter, code int, format string, args ...interface{}) {
	message := fmt.Sprintf(format, args...)
	response := UploadResponse{
		Success: false,
		Message: message,
		Errors:  []string{message},
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(response)
}

// CoordinateConverter handles coordinate system conversions
type CoordinateConverter struct {
	// Could add projection parameters here if needed
}

func NewCoordinateConverter() *CoordinateConverter {
	return &CoordinateConverter{}
}

// NormalizedToNanometers converts normalized coordinates (0-1) to nanometers
func (c *CoordinateConverter) NormalizedToNanometers(normalized float64, dimensionMeters float64) int64 {
	meters := normalized * dimensionMeters
	nanometers := meters * float64(arxobject.Meter)
	return int64(nanometers)
}

// PixelsToNanometers converts pixel coordinates to nanometers
func (c *CoordinateConverter) PixelsToNanometers(pixels float64, pixelsPerMeter float64) int64 {
	meters := pixels / pixelsPerMeter
	nanometers := meters * float64(arxobject.Meter)
	return int64(nanometers)
}

// Helper functions

func parseBuildingID(id string) uint64 {
	// Convert UUID string to uint64 (simplified)
	// In production, use a proper mapping
	hash := uint64(0)
	for _, c := range id {
		hash = hash*31 + uint64(c)
	}
	return hash
}

func parseFloorNumber(floor string) int {
	if floor == "" {
		return 1
	}
	// Parse floor number, handling various formats
	var num int
	fmt.Sscanf(floor, "%d", &num)
	return num
}

func parseFloat(s string, defaultVal float64) float64 {
	if s == "" {
		return defaultVal
	}
	var val float64
	fmt.Sscanf(s, "%f", &val)
	if val == 0 {
		return defaultVal
	}
	return val
}

func (h *UploadHandler) parseScaleFactor(scale string) float64 {
	if scale == "" {
		return 1.0
	}
	
	// Parse scale formats like "1:100" or "1/100"
	if strings.Contains(scale, ":") {
		parts := strings.Split(scale, ":")
		if len(parts) == 2 {
			var denominator float64
			fmt.Sscanf(parts[1], "%f", &denominator)
			if denominator > 0 {
				return denominator
			}
		}
	}
	
	// Parse direct scale factor
	var factor float64
	fmt.Sscanf(scale, "%f", &factor)
	return factor
}

func abs(x int64) int64 {
	if x < 0 {
		return -x
	}
	return x
}

// RegisterRoutes registers HTTP routes for the upload handler
func (h *UploadHandler) RegisterRoutes(router *mux.Router) {
	router.HandleFunc("/api/buildings/upload", h.HandlePDFUpload).Methods("POST")
	router.HandleFunc("/api/buildings/{id}", h.GetBuilding).Methods("GET")
	router.HandleFunc("/api/buildings/{id}/objects", h.GetBuildingObjects).Methods("GET")
	router.HandleFunc("/api/buildings/{id}/tiles/{z}/{x}/{y}", h.GetTile).Methods("GET")
}

// GetBuilding retrieves building information
func (h *UploadHandler) GetBuilding(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	buildingID := vars["id"]
	
	building, err := h.storage.GetBuilding(r.Context(), buildingID)
	if err != nil {
		h.sendError(w, http.StatusNotFound, "Building not found: %v", err)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(building)
}

// GetBuildingObjects retrieves objects for a building
func (h *UploadHandler) GetBuildingObjects(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	buildingID := vars["id"]
	
	// Parse query parameters for filtering
	objType := r.URL.Query().Get("type")
	floor := r.URL.Query().Get("floor")
	
	objects, err := h.storage.GetBuildingObjects(r.Context(), buildingID, objType, floor)
	if err != nil {
		h.sendError(w, http.StatusInternalServerError, "Failed to retrieve objects: %v", err)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(objects)
}

// GetTile retrieves a map tile for visualization
func (h *UploadHandler) GetTile(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	buildingID := vars["id"]
	z := vars["z"]
	x := vars["x"]
	y := vars["y"]
	
	// This would generate or retrieve a pre-rendered tile
	// For now, return a placeholder response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"building_id": buildingID,
		"tile": fmt.Sprintf("%s/%s/%s", z, x, y),
		"status": "not_implemented",
	})
}