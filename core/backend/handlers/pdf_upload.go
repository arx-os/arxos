package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"arxos/arxobject"
	"arxos/services"
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

	// Process PDF to extract ArxObjects
	arxEngine := arxobject.NewEngine(nil) // TODO: pass actual DB connection
	
	// Try AI processor first, fall back to basic processor if AI service is not available
	var processingResult *services.ProcessingResult
	var processingErr error
	
	// Check if AI service is enabled
	useAI := os.Getenv("USE_AI_PDF_PROCESSOR") != "false"
	
	if useAI {
		aiProcessor := services.NewAIPDFProcessor(arxEngine)
		processingResult, processingErr = aiProcessor.ProcessPDF(filepath)
		
		if processingErr != nil {
			// Log AI processing error
			response["data"].(map[string]interface{})["ai_warning"] = processingErr.Error()
			
			// Fall back to basic processor
			processor := services.NewPDFProcessor(arxEngine)
			processingResult, processingErr = processor.ProcessPDF(filepath)
		} else {
			response["data"].(map[string]interface{})["processing_method"] = "ai"
		}
	} else {
		// Use basic processor
		processor := services.NewPDFProcessor(arxEngine)
		processingResult, processingErr = processor.ProcessPDF(filepath)
		response["data"].(map[string]interface{})["processing_method"] = "basic"
	}
	
	if processingErr != nil {
		// Log error but continue with partial results
		response["data"].(map[string]interface{})["process_warning"] = processingErr.Error()
	}
	
	// Convert extracted objects to response format
	var extractedObjects []map[string]interface{}
	var needingValidation int
	
	if processingResult != nil && len(processingResult.Objects) > 0 {
		for _, obj := range processingResult.Objects {
			extractedObj := map[string]interface{}{
				"type":       obj.Type,
				"uuid":       obj.ID,
				"confidence": obj.Confidence.Overall,
				"properties": obj.Properties,
			}
			extractedObjects = append(extractedObjects, extractedObj)
			
			if obj.Confidence.Overall < 0.7 {
				needingValidation++
			}
		}
		
		response["data"].(map[string]interface{})["statistics"] = processingResult.Statistics
	} else {
		// Return empty result with error message instead of mock data
		if processingErr != nil {
			response["success"] = false
			response["message"] = "PDF processing failed"
			response["data"].(map[string]interface{})["error"] = processingErr.Error()
			response["data"].(map[string]interface{})["status"] = "failed"
			
			// Still return the response but with empty objects
			extractedObjects = []map[string]interface{}{}
			response["data"].(map[string]interface{})["extracted_objects"] = extractedObjects
			response["data"].(map[string]interface{})["objects_needing_validation"] = 0
			
			// Log the error for debugging
			fmt.Printf("PDF processing error for %s: %v\n", handler.Filename, processingErr)
		} else {
			// Processing succeeded but no objects found
			response["data"].(map[string]interface{})["status"] = "completed"
			response["data"].(map[string]interface{})["message"] = "No objects detected in PDF"
			extractedObjects = []map[string]interface{}{}
		}
	}

	response["data"].(map[string]interface{})["extracted_objects"] = extractedObjects
	response["data"].(map[string]interface{})["objects_needing_validation"] = needingValidation

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

	// Since we process PDFs synchronously for now, always return completed
	// In a production system, this would check a job queue or database
	status := map[string]interface{}{
		"id":     pdfID,
		"status": "completed",
		"message": "PDF processing is synchronous - check upload response for results",
		"note": "Asynchronous processing not yet implemented",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

// ListUploadedPDFs returns a list of uploaded PDFs
func ListUploadedPDFs(w http.ResponseWriter, r *http.Request) {
	// List actual files from upload directory
	uploadDir := "uploads"
	pdfs := []map[string]interface{}{}
	
	files, err := os.ReadDir(uploadDir)
	if err != nil {
		// Upload directory doesn't exist or can't be read
		response := map[string]interface{}{
			"success": true,
			"data":    pdfs,
			"total":   0,
			"message": "No PDFs uploaded yet",
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
		return
	}
	
	for _, file := range files {
		if !file.IsDir() && filepath.Ext(file.Name()) == ".pdf" {
			info, err := file.Info()
			if err != nil {
				continue
			}
			
			// Extract UUID from filename (format: UUID_originalname.pdf)
			parts := strings.SplitN(file.Name(), "_", 2)
			id := parts[0]
			originalName := file.Name()
			if len(parts) > 1 {
				originalName = parts[1]
			}
			
			pdfs = append(pdfs, map[string]interface{}{
				"id":          id,
				"filename":    originalName,
				"upload_date": info.ModTime().UTC(),
				"status":      "completed", // All uploaded PDFs are processed synchronously
				"size":        info.Size(),
			})
		}
	}
	
	// Sort by upload date (newest first)
	// Note: In production, this would be handled by database with proper indexing
	
	response := map[string]interface{}{
		"success": true,
		"data":    pdfs,
		"total":   len(pdfs),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}