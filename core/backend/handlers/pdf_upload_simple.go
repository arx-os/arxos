package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// SimplePDFUpload handles PDF uploads without complex dependencies
func SimplePDFUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form
	err := r.ParseMultipartForm(50 << 20) // 50MB
	if err != nil {
		http.Error(w, "Failed to parse form: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Get the PDF file
	file, header, err := r.FormFile("pdf")
	if err != nil {
		http.Error(w, "Failed to get PDF file: "+err.Error(), http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Get metadata
	buildingName := r.FormValue("building_name")
	floor := r.FormValue("floor")
	coordinateSystem := r.FormValue("coordinate_system")
	arxObjectsJSON := r.FormValue("arxobjects")

	// Read file content (for logging purposes)
	fileBytes, err := io.ReadAll(file)
	if err != nil {
		http.Error(w, "Failed to read file: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Parse ArxObjects if provided
	var arxObjects interface{}
	if arxObjectsJSON != "" {
		err = json.Unmarshal([]byte(arxObjectsJSON), &arxObjects)
		if err != nil {
			http.Error(w, "Failed to parse ArxObjects: "+err.Error(), http.StatusBadRequest)
			return
		}
	}

	// Generate a simple building ID
	buildingID := fmt.Sprintf("building_%d", time.Now().Unix())

	// Log the upload
	fmt.Printf("PDF Upload received:\n")
	fmt.Printf("  Building Name: %s\n", buildingName)
	fmt.Printf("  Floor: %s\n", floor)
	fmt.Printf("  File: %s (%.2f MB)\n", header.Filename, float64(len(fileBytes))/(1024*1024))
	fmt.Printf("  Coordinate System: %s\n", coordinateSystem)
	fmt.Printf("  Building ID: %s\n", buildingID)
	
	// Count objects if provided
	objectCount := 0
	if arxData, ok := arxObjects.(map[string]interface{}); ok {
		if arxosData, ok := arxData["arxos"].(map[string]interface{}); ok {
			if objects, ok := arxosData["objects"].([]interface{}); ok {
				objectCount = len(objects)
			}
		}
	}

	// Create response
	response := map[string]interface{}{
		"success":     true,
		"building_id": buildingID,
		"message":     fmt.Sprintf("Successfully received PDF with %d objects", objectCount),
		"statistics": map[string]interface{}{
			"total_objects":  objectCount,
			"file_size_mb":   float64(len(fileBytes)) / (1024 * 1024),
			"processing_ms":  100, // Simulated
		},
		"processing_time": "100ms",
	}

	// Send response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}