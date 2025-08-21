package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

// PDFUploadHandler handles PDF file uploads and processing
type PDFUploadHandler struct {
	db          *sql.DB
	tileService *TileService
	wsHub       *Hub
}

// NewPDFUploadHandler creates a new PDF upload handler
func NewPDFUploadHandler(db *sql.DB, tileService *TileService, wsHub *Hub) *PDFUploadHandler {
	return &PDFUploadHandler{
		db:          db,
		tileService: tileService,
		wsHub:       wsHub,
	}
}

// HandleUpload handles PDF file upload
func (h *PDFUploadHandler) HandleUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form (32MB max)
	err := r.ParseMultipartForm(32 << 20)
	if err != nil {
		http.Error(w, "Failed to parse form", http.StatusBadRequest)
		return
	}

	// Get the file from form
	file, header, err := r.FormFile("pdf")
	if err != nil {
		http.Error(w, "Failed to get file", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Validate file type
	if filepath.Ext(header.Filename) != ".pdf" {
		http.Error(w, "Only PDF files are allowed", http.StatusBadRequest)
		return
	}

	// Create uploads directory if it doesn't exist
	uploadsDir := "./uploads"
	if err := os.MkdirAll(uploadsDir, 0755); err != nil {
		http.Error(w, "Failed to create uploads directory", http.StatusInternalServerError)
		return
	}

	// Create unique filename
	filename := fmt.Sprintf("%d_%s", time.Now().Unix(), header.Filename)
	filepath := filepath.Join(uploadsDir, filename)

	// Create file on disk
	dst, err := os.Create(filepath)
	if err != nil {
		http.Error(w, "Failed to create file", http.StatusInternalServerError)
		return
	}
	defer dst.Close()

	// Copy uploaded file to destination
	fileSize, err := io.Copy(dst, file)
	if err != nil {
		http.Error(w, "Failed to save file", http.StatusInternalServerError)
		return
	}

	log.Printf("PDF uploaded: %s (size: %d bytes)", filename, fileSize)

	// Get metadata from form
	buildingName := r.FormValue("building_name")
	if buildingName == "" {
		buildingName = "Uploaded Building"
	}
	floorNumber := r.FormValue("floor_number")
	if floorNumber == "" {
		floorNumber = "0"
	}

	// Process the PDF
	result, err := h.processPDF(filepath, buildingName, floorNumber)
	if err != nil {
		log.Printf("Error processing PDF: %v", err)
		http.Error(w, fmt.Sprintf("Failed to process PDF: %v", err), http.StatusInternalServerError)
		return
	}

	// Send response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)

	// Broadcast update via WebSocket
	update := map[string]interface{}{
		"type":    "pdf_processed",
		"message": fmt.Sprintf("PDF processed: %s", buildingName),
		"stats":   result,
	}
	if data, err := json.Marshal(update); err == nil {
		h.wsHub.broadcast <- data
	}
}

// ProcessingResult represents the result of PDF processing
type ProcessingResult struct {
	Success      bool                   `json:"success"`
	Message      string                 `json:"message"`
	BuildingName string                 `json:"building_name"`
	FloorNumber  string                 `json:"floor_number"`
	ObjectCount  int                    `json:"object_count"`
	Objects      []ArxObject            `json:"objects"`
	Statistics   map[string]int         `json:"statistics"`
	ProcessTime  float64                `json:"process_time_seconds"`
}

// processPDF processes the uploaded PDF and creates ArxObjects
func (h *PDFUploadHandler) processPDF(filepath, buildingName, floorNumber string) (*ProcessingResult, error) {
	startTime := time.Now()
	
	// Process PDF using AI service
	objects, stats, err := h.processWithAIService(filepath, buildingName, floorNumber)
	if err != nil {
		return nil, fmt.Errorf("AI service processing failed: %v", err)
	}
	
	// Store objects in database
	storedCount := 0
	for _, obj := range objects {
		if err := h.storeObject(&obj); err != nil {
			log.Printf("Failed to store object: %v", err)
		} else {
			storedCount++
		}
	}

	// Clear tile cache to reflect new data
	h.tileService.ClearCache()

	processTime := time.Since(startTime).Seconds()
	
	return &ProcessingResult{
		Success:      true,
		Message:      fmt.Sprintf("Successfully processed PDF and created %d objects", storedCount),
		BuildingName: buildingName,
		FloorNumber:  floorNumber,
		ObjectCount:  storedCount,
		Objects:      objects[:min(10, len(objects))], // Return first 10 objects as sample
		Statistics:   stats,
		ProcessTime:  processTime,
	}, nil
}

// processWithAIService processes PDF through the AI service
func (h *PDFUploadHandler) processWithAIService(pdfPath, buildingName, floorNumber string) ([]ArxObject, map[string]int, error) {
	var objects []ArxObject
	stats := make(map[string]int)
	
	// Open PDF file
	pdfFile, err := os.Open(pdfPath)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to open PDF: %v", err)
	}
	defer pdfFile.Close()
	
	// Create multipart form
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	
	// Add file to form
	part, err := writer.CreateFormFile("file", filepath.Base(pdfPath))
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create form file: %v", err)
	}
	
	if _, err := io.Copy(part, pdfFile); err != nil {
		return nil, nil, fmt.Errorf("failed to copy file: %v", err)
	}
	
	// Add building type
	writer.WriteField("building_type", "general")
	writer.Close()
	
	// Send to AI service
	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:8000"
	}
	
	req, err := http.NewRequest("POST", aiServiceURL+"/api/v1/convert", body)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create request: %v", err)
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())
	
	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, nil, fmt.Errorf("AI service request failed: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, nil, fmt.Errorf("AI service returned status %d: %s", resp.StatusCode, string(bodyBytes))
	}
	
	// Parse AI service response
	var aiResult struct {
		ArxObjects []struct {
			ID         string                 `json:"id"`
			Type       string                 `json:"type"`
			System     string                 `json:"system"`
			Geometry   map[string]interface{} `json:"geometry"`
			Properties map[string]interface{} `json:"properties"`
			Confidence struct {
				Overall float64 `json:"overall"`
			} `json:"confidence"`
		} `json:"arxobjects"`
		OverallConfidence float64 `json:"overall_confidence"`
	}
	
	if err := json.NewDecoder(resp.Body).Decode(&aiResult); err != nil {
		return nil, nil, fmt.Errorf("failed to decode AI response: %v", err)
	}
	
	// Convert AI objects to ArxObjects
	floorZ := parseFloat(floorNumber) * 3000
	
	for _, aiObj := range aiResult.ArxObjects {
		// Extract position from geometry
		x, y := 0.0, 0.0
		width, height := 100, 100
		
		if geometry, ok := aiObj.Geometry["coordinates"].([]interface{}); ok && len(geometry) > 0 {
			if coords, ok := geometry[0].([]interface{}); ok && len(coords) >= 2 {
				if xVal, ok := coords[0].(float64); ok {
					x = xVal * 1000 // Convert to mm
				}
				if yVal, ok := coords[1].(float64); ok {
					y = yVal * 1000 // Convert to mm
				}
			}
			// Calculate dimensions from bounding box if available
			if len(geometry) > 1 {
				if coords2, ok := geometry[1].([]interface{}); ok && len(coords2) >= 2 {
					if xVal2, ok := coords2[0].(float64); ok {
						width = int((xVal2 - x/1000) * 1000)
					}
					if yVal2, ok := coords2[1].(float64); ok {
						height = int((yVal2 - y/1000) * 1000)
					}
				}
			}
		}
		
		// Add metadata
		aiObj.Properties["building"] = buildingName
		aiObj.Properties["floor"] = floorNumber
		aiObj.Properties["confidence"] = aiObj.Confidence.Overall
		
		propsJSON, _ := json.Marshal(aiObj.Properties)
		
		objects = append(objects, ArxObject{
			Type:       aiObj.Type,
			System:     aiObj.System,
			X:          x,
			Y:          y,
			Z:          floorZ,
			Width:      width,
			Height:     height,
			ScaleMin:   5,
			ScaleMax:   10,
			Properties: json.RawMessage(propsJSON),
		})
		
		stats[aiObj.Type]++
	}
	
	log.Printf("Processed %d objects from AI service: %v", len(objects), stats)
	
	return objects, stats, nil
}

// storeObject stores an ArxObject in the database
func (h *PDFUploadHandler) storeObject(obj *ArxObject) error {
	if h.db == nil {
		return fmt.Errorf("database not available")
	}
	
	query := `
	INSERT INTO arx_objects (
		type, system, x, y, z, width, height, 
		scale_min, scale_max, properties, confidence, extraction_method
	) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
	RETURNING id, uuid
	`
	
	// Extract confidence from properties if available
	confidence := 0.85 // default confidence
	if obj.Properties != nil {
		var props map[string]interface{}
		if err := json.Unmarshal(obj.Properties, &props); err == nil {
			if conf, ok := props["confidence"].(float64); ok {
				confidence = conf
			}
		}
	}
	
	err := h.db.QueryRow(query,
		obj.Type, obj.System, obj.X, obj.Y, obj.Z,
		obj.Width, obj.Height, obj.ScaleMin, obj.ScaleMax,
		obj.Properties, confidence, "pdf",
	).Scan(&obj.ID, &obj.UUID)
	
	return err
}

// Helper functions
func parseFloat(s string) float64 {
	var f float64
	fmt.Sscanf(s, "%f", &f)
	return f
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}