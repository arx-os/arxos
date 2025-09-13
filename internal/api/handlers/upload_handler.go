package handlers

import (
	"net/http"
)

const (
	maxUploadSize = 100 * 1024 * 1024 // 100MB
)

// UploadResponse represents the response for file uploads
type UploadResponse struct {
	Success   bool              `json:"success"`
	Message   string            `json:"message,omitempty"`
	Data      interface{}       `json:"data,omitempty"`
	Errors    []string          `json:"errors,omitempty"`
	Warnings  []string          `json:"warnings,omitempty"`
}

// HandlePDFUpload handles PDF file uploads for building import
// TODO: Refactor to work without Server receiver
func HandlePDFUpload(w http.ResponseWriter, r *http.Request) {
	// Temporarily disabled during refactoring
	http.Error(w, "PDF upload temporarily disabled during refactoring", http.StatusServiceUnavailable)
	return
	/*
	// Check authentication
	userID := r.Context().Value("user_id")
	if userID == nil {
		s.respondJSON(w, http.StatusUnauthorized, map[string]string{
			"error": "Authentication required",
		})
		return
	}

	// Limit upload size
	r.Body = http.MaxBytesReader(w, r.Body, maxUploadSize)
	
	// Parse multipart form
	if err := r.ParseMultipartForm(maxUploadSize); err != nil {
		s.respondJSON(w, http.StatusBadRequest, UploadResponse{
			Success: false,
			Message: "File too large or invalid form data",
			Errors:  []string{err.Error()},
		})
		return
	}

	// Get the file
	file, header, err := r.FormFile("file")
	if err != nil {
		s.respondJSON(w, http.StatusBadRequest, UploadResponse{
			Success: false,
			Message: "No file provided",
			Errors:  []string{err.Error()},
		})
		return
	}
	defer file.Close()

	// Check file type
	if header.Header.Get("Content-Type") != "application/pdf" {
		// Also check file extension as fallback
		if len(header.Filename) < 4 || header.Filename[len(header.Filename)-4:] != ".pdf" {
			s.respondJSON(w, http.StatusBadRequest, UploadResponse{
				Success: false,
				Message: "Only PDF files are supported",
			})
			return
		}
	}

	logger.Info("Processing PDF upload: %s (%d bytes)", header.Filename, header.Size)

	// Get import options from form
	options := pdf.ImportOptions{
		BuildingName: r.FormValue("building_name"),
		BuildingID:   r.FormValue("building_id"),
		Level:        1, // Default level
		UserID:       userID.(string),
		Overwrite:    r.FormValue("overwrite") == "true",
	}

	// Parse level if provided
	if levelStr := r.FormValue("level"); levelStr != "" {
		var level int
		if _, err := fmt.Sscanf(levelStr, "%d", &level); err == nil {
			options.Level = level
		}
	}

	// If building name not provided, use filename
	if options.BuildingName == "" {
		options.BuildingName = header.Filename
		if len(options.BuildingName) > 4 && options.BuildingName[len(options.BuildingName)-4:] == ".pdf" {
			options.BuildingName = options.BuildingName[:len(options.BuildingName)-4]
		}
	}

	// Create importer with database from services
	if s.services.DB == nil {
		s.respondJSON(w, http.StatusInternalServerError, UploadResponse{
			Success: false,
			Message: "Database service not available",
		})
		return
	}
	
	// Type assert to database interface
	db, ok := s.services.DB.(database.DB)
	if !ok {
		s.respondJSON(w, http.StatusInternalServerError, UploadResponse{
			Success: false,
			Message: "Invalid database service",
		})
		return
	}
	
	importer := pdf.NewImporter(db)

	// Import with timeout
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Minute)
	defer cancel()

	// Process import
	result, err := importer.Import(ctx, file, options)
	if err != nil {
		logger.Error("PDF import failed: %v", err)
		s.respondJSON(w, http.StatusInternalServerError, UploadResponse{
			Success: false,
			Message: "Import failed",
			Errors:  []string{err.Error()},
		})
		return
	}

	// Return success response
	s.respondJSON(w, http.StatusOK, UploadResponse{
		Success:  true,
		Message:  fmt.Sprintf("Successfully imported %d rooms and %d equipment items", result.RoomsImported, result.EquipImported),
		Data: map[string]interface{}{
			"building_id":     result.BuildingID,
			"rooms_imported":  result.RoomsImported,
			"equip_imported":  result.EquipImported,
			"import_duration": result.Duration.String(),
		},
		Warnings: result.Warnings,
	})
	*/
}

// HandleUploadProgress handles SSE for upload progress
// TODO: Refactor to work without Server receiver
func HandleUploadProgress(w http.ResponseWriter, r *http.Request) {
	// Temporarily disabled during refactoring
	http.Error(w, "Upload progress temporarily disabled during refactoring", http.StatusServiceUnavailable)
	return
	/*
	// Set SSE headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")

	// Create event stream
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	// Send initial event
	fmt.Fprintf(w, "data: %s\n\n", `{"status":"connected"}`)
	flusher.Flush()

	// Keep connection alive and send progress updates
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-r.Context().Done():
			return
		case <-ticker.C:
			// In production, this would get actual progress from import job
			// For now, just keep connection alive
			fmt.Fprintf(w, ": keepalive\n\n")
			flusher.Flush()
		}
	}
	*/
}
