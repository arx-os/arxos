package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"time"

	// "github.com/arxos/arxos/core/backend/handlers"
	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/rs/cors"
)

// handlePDFUpload processes PDF uploads and forwards to AI service
func handlePDFUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form
	err := r.ParseMultipartForm(50 << 20) // 50 MB max
	if err != nil {
		http.Error(w, "Failed to parse form data", http.StatusBadRequest)
		return
	}

	// Get the file
	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "No file provided", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Read file content
	fileBytes, err := io.ReadAll(file)
	if err != nil {
		http.Error(w, "Failed to read file", http.StatusInternalServerError)
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
		http.Error(w, "Failed to create form", http.StatusInternalServerError)
		return
	}

	_, err = part.Write(fileBytes)
	if err != nil {
		http.Error(w, "Failed to write file", http.StatusInternalServerError)
		return
	}

	// Add building type
	writer.WriteField("building_type", "general")
	writer.Close()

	// Send to AI service
	req, err := http.NewRequest("POST", aiServiceURL+"/api/v1/convert", body)
	if err != nil {
		http.Error(w, "Failed to create request", http.StatusInternalServerError)
		return
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, "AI service unavailable", http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()

	// Read AI service response
	aiResponse, err := io.ReadAll(resp.Body)
	if err != nil {
		http.Error(w, "Failed to read AI response", http.StatusInternalServerError)
		return
	}

	// Parse and transform response
	var aiResult map[string]interface{}
	if err := json.Unmarshal(aiResponse, &aiResult); err != nil {
		http.Error(w, "Invalid AI response", http.StatusInternalServerError)
		return
	}

	// Extract ArxObjects from AI response
	arxobjects, ok := aiResult["arxobjects"].([]interface{})
	if !ok {
		arxobjects = []interface{}{}
	}

	// Convert ArxObjects to frontend format
	frontendObjects := make([]map[string]interface{}, 0)
	for _, obj := range arxobjects {
		if objMap, ok := obj.(map[string]interface{}); ok {
			// Create frontend-friendly object
			frontendObj := map[string]interface{}{
				"id":   objMap["id"],
				"type": objMap["type"],
			}
			
			// Handle confidence
			if conf, ok := objMap["confidence"].(map[string]interface{}); ok {
				frontendObj["confidence"] = conf["overall"]
			}
			
			// Pass through geometry if present
			if geometry, ok := objMap["geometry"]; ok {
				frontendObj["geometry"] = geometry
			}
			
			// Pass through data if present
			if data, ok := objMap["data"]; ok {
				frontendObj["data"] = data
			}
			
			// Handle position for objects without geometry
			if position, ok := objMap["position"].(map[string]interface{}); ok {
				// Convert nanometers to millimeters
				if x, ok := position["x"].(float64); ok {
					frontendObj["x"] = x / 1e6
				}
				if y, ok := position["y"].(float64); ok {
					frontendObj["y"] = y / 1e6
				}
			}
			
			// Handle dimensions
			if dimensions, ok := objMap["dimensions"].(map[string]interface{}); ok {
				if w, ok := dimensions["width"].(float64); ok {
					frontendObj["width"] = w / 1e6
				}
				if h, ok := dimensions["height"].(float64); ok {
					frontendObj["height"] = h / 1e6
				}
			}
			
			frontendObjects = append(frontendObjects, frontendObj)
		}
	}

	// Create response
	response := map[string]interface{}{
		"success":     true,
		"message":     fmt.Sprintf("Processed %s", header.Filename),
		"filename":    header.Filename,
		"arxobjects":  frontendObjects,  // Frontend expects 'arxobjects' not 'objects'
		"statistics": map[string]interface{}{
			"total_objects":      len(frontendObjects),
			"overall_confidence": aiResult["overall_confidence"],
			"processing_time":    aiResult["processing_time"],
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

func main() {
	log.Println("🚀 Starting ARXOS backend server...")

	// Set up router
	r := chi.NewRouter()
	r.Use(chimiddleware.Logger)
	r.Use(cors.AllowAll().Handler)

	// Add request logging middleware
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			// Call next handler
			next.ServeHTTP(w, r)

			// Log request
			duration := time.Since(start)
			log.Printf("Request: %s %s - Duration: %v", r.Method, r.URL.Path, duration)
		})
	})

	// TODO: Serve main application interface
	// For now, redirect to API health check
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "/api/health", http.StatusTemporaryRedirect)
	})

	// Import handlers package
	// Note: In production, this would be properly imported
	// For now, we'll create a simple inline handler
	
	// PDF upload endpoints
	r.Post("/upload/pdf", handlePDFUpload) // Original endpoint
	// r.Post("/api/v1/upload/pdf", handlers.EnhancedPDFUpload) // Enhanced with BIM processing (temporarily disabled)
	
	r.Route("/api", func(r chi.Router) {
		// Public health check endpoint
		r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"status":"ok","message":"ARXOS backend is running"}`))
		})

		// SQLite test endpoints (for testing without PostgreSQL)
		r.Get("/test/sqlite/db", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"success":true,"message":"SQLite test endpoint ready"}`))
		})

		r.Get("/test/sqlite/arxobject-pipeline", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"success":true,"message":"ArxObject pipeline test endpoint ready"}`))
		})

		r.Post("/test/sqlite/pdf-upload", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"success":true,"message":"PDF upload test endpoint ready"}`))
		})
	})

	// Start server
	log.Println("🚀 Server running on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
