package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"arxos/services"
)

// PDFUploadHandler handles PDF file uploads and processing
func PDFUploadHandler(pdfProcessor *services.PDFProcessor) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Set max file size to 50MB
		r.ParseMultipartForm(50 << 20)

		// Get the file from the request
		file, header, err := r.FormFile("pdf")
		if err != nil {
			respondWithError(w, http.StatusBadRequest, "Failed to get file from request")
			return
		}
		defer file.Close()

		// Create uploads directory if it doesn't exist
		uploadsDir := "uploads"
		if err := os.MkdirAll(uploadsDir, 0755); err != nil {
			respondWithError(w, http.StatusInternalServerError, "Failed to create uploads directory")
			return
		}

		// Create unique filename
		filename := fmt.Sprintf("%d_%s", time.Now().Unix(), header.Filename)
		filepath := filepath.Join(uploadsDir, filename)

		// Save the uploaded file
		dst, err := os.Create(filepath)
		if err != nil {
			respondWithError(w, http.StatusInternalServerError, "Failed to save file")
			return
		}
		defer dst.Close()

		if _, err := io.Copy(dst, file); err != nil {
			respondWithError(w, http.StatusInternalServerError, "Failed to copy file content")
			return
		}

		// Process the PDF using the PDF processor service
		result, err := pdfProcessor.ProcessPDF(filepath)
		if err != nil {
			respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to process PDF: %v", err))
			return
		}

		// Clean up the uploaded file after processing
		defer os.Remove(filepath)

		// Convert result to response format
		response := map[string]interface{}{
			"success": true,
			"data": map[string]interface{}{
				"objects":    result.Objects,
				"statistics": result.Statistics,
				"processing_time": result.ProcessingTime.Seconds(),
			},
			"message": fmt.Sprintf("Successfully processed %d objects", len(result.Objects)),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}
}

// SimplePDFUpload handles PDF uploads and forwards to AI service for processing
func SimplePDFUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form
	err := r.ParseMultipartForm(50 << 20) // 50 MB max
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "Failed to parse form data")
		return
	}

	// Get the file
	file, header, err := r.FormFile("file")
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "No file provided")
		return
	}
	defer file.Close()

	// Read file content
	fileBytes, err := io.ReadAll(file)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to read file")
		return
	}

	// Forward to AI service
	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:8000"
	}

	// Create multipart form for AI service
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	
	// Add file to form
	part, err := writer.CreateFormFile("file", header.Filename)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to create form")
		return
	}
	
	_, err = part.Write(fileBytes)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to write file")
		return
	}
	
	// Add building type
	writer.WriteField("building_type", "general")
	writer.Close()

	// Send to AI service
	req, err := http.NewRequest("POST", aiServiceURL+"/api/v1/convert", body)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to create request")
		return
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		respondWithError(w, http.StatusServiceUnavailable, "AI service unavailable")
		return
	}
	defer resp.Body.Close()

	// Read AI service response
	aiResponse, err := io.ReadAll(resp.Body)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to read AI response")
		return
	}

	// Parse and transform response
	var aiResult map[string]interface{}
	if err := json.Unmarshal(aiResponse, &aiResult); err != nil {
		respondWithError(w, http.StatusInternalServerError, "Invalid AI response")
		return
	}

	// Transform ArxObjects to frontend format
	arxobjects, ok := aiResult["arxobjects"].([]interface{})
	if !ok {
		arxobjects = []interface{}{}
	}

	objects := make([]map[string]interface{}, 0)
	for _, obj := range arxobjects {
		if objMap, ok := obj.(map[string]interface{}); ok {
			// Extract position and dimensions from data field (in mm)
			x, y := 100.0, 100.0
			width, height := 100.0, 10.0
			
			if data, ok := objMap["data"].(map[string]interface{}); ok {
				// Get real-world coordinates in mm
				if xMm, ok := data["x_mm"].(float64); ok {
					x = xMm
				}
				if yMm, ok := data["y_mm"].(float64); ok {
					y = yMm
				}
				if lengthMm, ok := data["length_mm"].(float64); ok {
					width = lengthMm
				}
				if thicknessMm, ok := data["thickness_mm"].(float64); ok {
					height = thicknessMm
				}
			}
			
			// Fallback to geometry if data not available
			if x == 100.0 && y == 100.0 {
				if geometry, ok := objMap["geometry"].(map[string]interface{}); ok {
					if coords, ok := geometry["coordinates"].([]interface{}); ok && len(coords) > 0 {
						if coord, ok := coords[0].([]interface{}); ok && len(coord) >= 2 {
							if xVal, ok := coord[0].(float64); ok {
								x = xVal
							}
							if yVal, ok := coord[1].(float64); ok {
								y = yVal
							}
						}
					}
				}
			}

			// Get confidence
			confidence := 0.5
			if conf, ok := objMap["confidence"].(map[string]interface{}); ok {
				if overall, ok := conf["overall"].(float64); ok {
					confidence = overall
				}
			}

			objects = append(objects, map[string]interface{}{
				"id":         objMap["id"],
				"type":       objMap["type"],
				"x":          x,
				"y":          y,
				"width":      width,
				"height":     height,
				"confidence": confidence,
				"data":       objMap["data"], // Include full data for debugging
			})
		}
	}

	// Create response
	response := map[string]interface{}{
		"success":  true,
		"message":  fmt.Sprintf("Processed %s", header.Filename),
		"filename": header.Filename,
		"objects":  objects,
		"statistics": map[string]interface{}{
			"total_objects":      len(objects),
			"overall_confidence": aiResult["overall_confidence"],
			"processing_time":    aiResult["processing_time"],
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

