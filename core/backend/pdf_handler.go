package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math/rand"
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
	
	// Use ACTUAL PDF parser - NO DEMO FALLBACK
	parser := NewActualPDFParser(filepath)
	objects, stats, err := parser.ParsePDFForReal(buildingName, floorNumber)
	if err != nil {
		return nil, fmt.Errorf("PDF parsing failed (NO DEMO FALLBACK): %w", err)
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
	h.tileService.clearCache()

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

// generateDemoObjectsFromPDF generates demo ArxObjects from a PDF
// In production, this would actually parse the PDF
func (h *PDFUploadHandler) generateDemoObjectsFromPDF(buildingName, floorNumber string) ([]ArxObject, map[string]int) {
	var objects []ArxObject
	stats := make(map[string]int)
	
	// Random seed based on building name for consistency
	rand.Seed(int64(len(buildingName)))
	
	// Base position for this building
	baseX := rand.Float64() * 10000
	baseY := rand.Float64() * 10000
	floorZ := parseFloat(floorNumber) * 3000
	
	// Generate building outline (walls)
	walls := []struct {
		x, y, w, h float64
		name       string
	}{
		{baseX, baseY, 8000, 100, "North Wall"},
		{baseX, baseY + 5900, 8000, 100, "South Wall"},
		{baseX, baseY, 100, 6000, "West Wall"},
		{baseX + 7900, baseY, 100, 6000, "East Wall"},
	}
	
	for _, wall := range walls {
		objects = append(objects, ArxObject{
			Type:     "wall",
			System:   "structural",
			X:        wall.x,
			Y:        wall.y,
			Z:        floorZ,
			Width:    int(wall.w),
			Height:   int(wall.h),
			ScaleMin: 4,
			ScaleMax: 9,
			Properties: json.RawMessage(fmt.Sprintf(`{"name":"%s","building":"%s","floor":"%s","confidence":0.92}`, 
				wall.name, buildingName, floorNumber)),
		})
		stats["wall"]++
	}
	
	// Generate rooms (grid layout)
	roomWidth := 2500.0
	roomHeight := 2800.0
	for i := 0; i < 3; i++ {
		for j := 0; j < 2; j++ {
			roomX := baseX + 500 + float64(i)*roomWidth
			roomY := baseY + 500 + float64(j)*roomHeight
			roomName := fmt.Sprintf("Room %d%d", i+1, j+1)
			
			// Room boundary
			objects = append(objects, ArxObject{
				Type:     "room",
				System:   "structural",
				X:        roomX,
				Y:        roomY,
				Z:        floorZ,
				Width:    int(roomWidth - 100),
				Height:   int(roomHeight - 100),
				ScaleMin: 5,
				ScaleMax: 9,
				Properties: json.RawMessage(fmt.Sprintf(`{"name":"%s","building":"%s","floor":"%s","area_sqft":%d,"confidence":0.88}`,
					roomName, buildingName, floorNumber, int((roomWidth-100)*(roomHeight-100)/1000000*10.764))),
			})
			stats["room"]++
			
			// Door
			objects = append(objects, ArxObject{
				Type:     "door",
				System:   "structural",
				X:        roomX + roomWidth/2 - 450,
				Y:        roomY,
				Z:        floorZ,
				Width:    900,
				Height:   100,
				ScaleMin: 6,
				ScaleMax: 9,
				Properties: json.RawMessage(fmt.Sprintf(`{"room":"%s","type":"single","confidence":0.91}`, roomName)),
			})
			stats["door"]++
			
			// Windows (2 per room)
			for w := 0; w < 2; w++ {
				objects = append(objects, ArxObject{
					Type:     "window",
					System:   "structural",
					X:        roomX + 500 + float64(w)*1500,
					Y:        roomY + roomHeight - 100,
					Z:        floorZ + 1000,
					Width:    1200,
					Height:   100,
					ScaleMin: 6,
					ScaleMax: 9,
					Properties: json.RawMessage(`{"type":"double_hung","confidence":0.85}`),
				})
				stats["window"]++
			}
			
			// Electrical outlets (4 per room)
			for e := 0; e < 4; e++ {
				var outletX, outletY float64
				switch e {
				case 0:
					outletX, outletY = roomX+200, roomY+200
				case 1:
					outletX, outletY = roomX+roomWidth-300, roomY+200
				case 2:
					outletX, outletY = roomX+200, roomY+roomHeight-300
				case 3:
					outletX, outletY = roomX+roomWidth-300, roomY+roomHeight-300
				}
				
				objects = append(objects, ArxObject{
					Type:     "outlet",
					System:   "electrical",
					X:        outletX,
					Y:        outletY,
					Z:        floorZ + 300,
					Width:    100,
					Height:   150,
					ScaleMin: 7,
					ScaleMax: 9,
					Properties: json.RawMessage(`{"voltage":"120V","amperage":"15A","confidence":0.82}`),
				})
				stats["outlet"]++
			}
			
			// HVAC vent
			objects = append(objects, ArxObject{
				Type:     "vent",
				System:   "hvac",
				X:        roomX + roomWidth/2 - 200,
				Y:        roomY + roomHeight/2 - 100,
				Z:        floorZ + 2900,
				Width:    400,
				Height:   200,
				ScaleMin: 7,
				ScaleMax: 9,
				Properties: json.RawMessage(`{"type":"supply","size":"12x6","confidence":0.79}`),
			})
			stats["vent"]++
			
			// Light fixture
			objects = append(objects, ArxObject{
				Type:     "light",
				System:   "electrical",
				X:        roomX + roomWidth/2 - 300,
				Y:        roomY + roomHeight/2 - 300,
				Z:        floorZ + 2900,
				Width:    600,
				Height:   600,
				ScaleMin: 7,
				ScaleMax: 9,
				Properties: json.RawMessage(`{"type":"recessed_led","wattage":"40W","confidence":0.86}`),
			})
			stats["light"]++
		}
	}
	
	// Add corridor
	objects = append(objects, ArxObject{
		Type:     "corridor",
		System:   "structural",
		X:        baseX + 500,
		Y:        baseY + 2900,
		Z:        floorZ,
		Width:    7000,
		Height:   200,
		ScaleMin: 5,
		ScaleMax: 10,
		Properties: json.RawMessage(fmt.Sprintf(`{"name":"Main Corridor","building":"%s","floor":"%s","confidence":0.90}`,
			buildingName, floorNumber)),
	})
	stats["corridor"]++
	
	// Add some plumbing (bathrooms)
	objects = append(objects, ArxObject{
		Type:     "pipe",
		System:   "plumbing",
		X:        baseX + 7500,
		Y:        baseY + 1000,
		Z:        floorZ,
		Width:    50,
		Height:   2000,
		ScaleMin: 7,
		ScaleMax: 10,
		Properties: json.RawMessage(`{"type":"water_supply","diameter":"2inch","confidence":0.75}`),
	})
	stats["pipe"]++
	
	log.Printf("Generated %d objects from PDF: %v", len(objects), stats)
	
	return objects, stats
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