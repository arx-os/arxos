package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/google/uuid"
)

// SimplePDFUpload handles basic PDF upload for testing
// This is a placeholder until full PDF processing is implemented
func SimplePDFUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form (32 MB max memory)
	err := r.ParseMultipartForm(32 << 20)
	if err != nil {
		http.Error(w, "Failed to parse form data", http.StatusBadRequest)
		return
	}

	// Get the file from form data
	file, handler, err := r.FormFile("pdf")
	if err != nil {
		http.Error(w, "Failed to get file from form", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Validate file extension
	ext := filepath.Ext(handler.Filename)
	if ext != ".pdf" {
		http.Error(w, "Only PDF files are allowed", http.StatusBadRequest)
		return
	}

	// Validate file size (50MB max)
	if handler.Size > 50*1024*1024 {
		http.Error(w, "File size exceeds 50MB limit", http.StatusRequestEntityTooLarge)
		return
	}

	// Create uploads directory if it doesn't exist
	uploadDir := "uploads"
	if err := os.MkdirAll(uploadDir, 0755); err != nil {
		http.Error(w, "Failed to create upload directory", http.StatusInternalServerError)
		return
	}

	// Generate unique filename
	uniqueID := uuid.New().String()
	filename := fmt.Sprintf("%s_%s", uniqueID, handler.Filename)
	filepath := filepath.Join(uploadDir, filename)

	// Create destination file
	dst, err := os.Create(filepath)
	if err != nil {
		http.Error(w, "Failed to create destination file", http.StatusInternalServerError)
		return
	}
	defer dst.Close()

	// Copy uploaded file to destination
	written, err := io.Copy(dst, file)
	if err != nil {
		http.Error(w, "Failed to save uploaded file", http.StatusInternalServerError)
		return
	}

	// Prepare response
	response := map[string]interface{}{
		"success": true,
		"message": "PDF uploaded successfully",
		"data": map[string]interface{}{
			"id":           uniqueID,
			"filename":     handler.Filename,
			"size":         written,
			"upload_time":  time.Now().UTC(),
			"status":       "uploaded",
			"process_info": "PDF processing will be implemented in the next phase",
		},
	}

	// TODO: In production, this would trigger PDF processing:
	// 1. Extract text and metadata using pdfplumber or similar
	// 2. Identify building elements (walls, doors, rooms, etc.)
	// 3. Convert to ArxObjects with initial confidence scores
	// 4. Store in database
	// 5. Queue for validation if confidence is low
	
	// For now, create mock ArxObjects for testing
	mockObjects := []map[string]interface{}{
		{
			"type":       "wall",
			"confidence": 0.65,
			"uuid":       uuid.New().String(),
			"properties": map[string]interface{}{
				"length": 5000,
				"height": 3000,
				"material": "concrete",
			},
		},
		{
			"type":       "door", 
			"confidence": 0.45,
			"uuid":       uuid.New().String(),
			"properties": map[string]interface{}{
				"width": 900,
				"height": 2100,
				"type": "single",
			},
		},
		{
			"type":       "room",
			"confidence": 0.80,
			"uuid":       uuid.New().String(),
			"properties": map[string]interface{}{
				"name": "Office 101",
				"area": 25.5,
				"occupancy": 2,
			},
		},
	}

	response["data"].(map[string]interface{})["extracted_objects"] = mockObjects
	response["data"].(map[string]interface{})["objects_needing_validation"] = 2

	// Send JSON response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// PDFProcessingStatus returns the processing status of an uploaded PDF
func PDFProcessingStatus(w http.ResponseWriter, r *http.Request) {
	// Get PDF ID from URL parameter
	pdfID := r.URL.Query().Get("id")
	if pdfID == "" {
		http.Error(w, "PDF ID is required", http.StatusBadRequest)
		return
	}

	// TODO: Implement actual status checking from database
	// For now, return mock status
	status := map[string]interface{}{
		"id":     pdfID,
		"status": "processing",
		"progress": map[string]interface{}{
			"current_step": "extracting_elements",
			"total_steps":  5,
			"completed":    2,
			"percentage":   40,
		},
		"stats": map[string]interface{}{
			"pages_processed":    5,
			"total_pages":        12,
			"objects_extracted":  47,
			"confidence_average": 0.72,
		},
		"estimated_completion": time.Now().Add(2 * time.Minute).UTC(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

// ListUploadedPDFs returns a list of uploaded PDFs
func ListUploadedPDFs(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual listing from database
	// For now, return mock data
	pdfs := []map[string]interface{}{
		{
			"id":          "abc-123",
			"filename":    "building_plans_v2.pdf",
			"upload_date": time.Now().Add(-24 * time.Hour).UTC(),
			"status":      "completed",
			"pages":       12,
			"objects":     156,
		},
		{
			"id":          "def-456",
			"filename":    "floor_2_electrical.pdf",
			"upload_date": time.Now().Add(-2 * time.Hour).UTC(),
			"status":      "processing",
			"pages":       8,
			"objects":     0,
		},
	}

	response := map[string]interface{}{
		"success": true,
		"data":    pdfs,
		"total":   len(pdfs),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}