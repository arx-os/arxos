package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/google/uuid"
	"github.com/rs/cors"
)

// ArxObject represents a simplified building object
type ArxObject struct {
	UUID       string                 `json:"uuid"`
	Type       string                 `json:"type"`
	Properties map[string]interface{} `json:"properties"`
	Confidence float32                `json:"confidence"`
}

// ProcessingResult from PDF extraction
type ProcessingResult struct {
	Success          bool                   `json:"success"`
	Message          string                 `json:"message,omitempty"`
	ExtractedObjects []ArxObject            `json:"extracted_objects"`
	Statistics       map[string]interface{} `json:"statistics"`
}

func main() {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(cors.AllowAll().Handler)

	// Serve static files
	fileServer := http.FileServer(http.Dir("."))
	r.Handle("/*", fileServer)

	// PDF upload endpoint
	r.Post("/api/buildings/upload", handlePDFUpload)

	// Health check
	r.Get("/api/health", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
	})

	log.Println("🚀 Simple Arxos server running on :8080")
	log.Println("📄 Open http://localhost:8080/pdf_wall_extractor.html to test PDF upload")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatal(err)
	}
}

func handlePDFUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form
	err := r.ParseMultipartForm(50 << 20) // 50MB max
	if err != nil {
		http.Error(w, "Failed to parse form", http.StatusBadRequest)
		return
	}

	// Get the PDF file
	file, header, err := r.FormFile("pdf")
	if err != nil {
		http.Error(w, "Failed to get PDF file", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Save the PDF temporarily
	tempDir := "./uploads"
	os.MkdirAll(tempDir, 0755)
	
	tempFile := filepath.Join(tempDir, fmt.Sprintf("%d_%s", time.Now().Unix(), header.Filename))
	dst, err := os.Create(tempFile)
	if err != nil {
		http.Error(w, "Failed to save file", http.StatusInternalServerError)
		return
	}
	defer dst.Close()

	_, err = io.Copy(dst, file)
	if err != nil {
		http.Error(w, "Failed to write file", http.StatusInternalServerError)
		return
	}

	// Process the PDF (simplified extraction)
	objects := extractObjects(tempFile)

	// Calculate statistics
	stats := calculateStats(objects)

	// Return result
	result := map[string]interface{}{
		"success": true,
		"data": ProcessingResult{
			Success:          true,
			Message:          fmt.Sprintf("Processed %s", header.Filename),
			ExtractedObjects: objects,
			Statistics:       stats,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func extractObjects(filepath string) []ArxObject {
	// Simulate extraction with realistic objects
	objects := []ArxObject{
		{
			UUID: uuid.New().String(),
			Type: "wall",
			Properties: map[string]interface{}{
				"start_x": 100,
				"start_y": 100,
				"end_x":   500,
				"end_y":   100,
				"thickness": 200,
			},
			Confidence: 0.85,
		},
		{
			UUID: uuid.New().String(),
			Type: "wall",
			Properties: map[string]interface{}{
				"start_x": 500,
				"start_y": 100,
				"end_x":   500,
				"end_y":   400,
				"thickness": 200,
			},
			Confidence: 0.82,
		},
		{
			UUID: uuid.New().String(),
			Type: "wall",
			Properties: map[string]interface{}{
				"start_x": 500,
				"start_y": 400,
				"end_x":   100,
				"end_y":   400,
				"thickness": 200,
			},
			Confidence: 0.79,
		},
		{
			UUID: uuid.New().String(),
			Type: "wall",
			Properties: map[string]interface{}{
				"start_x": 100,
				"start_y": 400,
				"end_x":   100,
				"end_y":   100,
				"thickness": 200,
			},
			Confidence: 0.88,
		},
		{
			UUID: uuid.New().String(),
			Type: "door",
			Properties: map[string]interface{}{
				"center_x": 300,
				"center_y": 100,
				"width":    80,
				"swing":    "inward",
			},
			Confidence: 0.75,
		},
		{
			UUID: uuid.New().String(),
			Type: "room",
			Properties: map[string]interface{}{
				"center_x": 300,
				"center_y": 250,
				"area":     120000,
				"name":     "Main Room",
			},
			Confidence: 0.92,
		},
	}

	// Add more objects for realism
	for i := 0; i < 5; i++ {
		objects = append(objects, ArxObject{
			UUID: uuid.New().String(),
			Type: "column",
			Properties: map[string]interface{}{
				"x":        150 + i*100,
				"y":        200,
				"diameter": 30,
			},
			Confidence: 0.70 + float32(i)*0.02,
		})
	}

	return objects
}

func calculateStats(objects []ArxObject) map[string]interface{} {
	typeCount := make(map[string]int)
	var totalConfidence float32
	var highConf, medConf, lowConf int

	for _, obj := range objects {
		typeCount[obj.Type]++
		totalConfidence += obj.Confidence
		
		if obj.Confidence >= 0.8 {
			highConf++
		} else if obj.Confidence >= 0.6 {
			medConf++
		} else {
			lowConf++
		}
	}

	return map[string]interface{}{
		"TotalObjects":      len(objects),
		"TypeCounts":        typeCount,
		"AverageConfidence": totalConfidence / float32(len(objects)),
		"HighConfidence":    highConf,
		"MediumConfidence":  medConf,
		"LowConfidence":     lowConf,
	}
}