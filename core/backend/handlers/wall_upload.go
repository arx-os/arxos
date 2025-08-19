package handlers

import (
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"time"
	
	// "github.com/arxos/arxos/core/arxobject"
	// "github.com/arxos/arxos/core/backend/converters"
)

// WallUploadRequest represents the incoming wall data from the frontend
type WallUploadRequest struct {
	BuildingName string                     `json:"building_name"`
	Floor        int                        `json:"floor"`
	Objects      []WallObject               `json:"objects"`
	Metadata     WallUploadMetadata         `json:"metadata"`
}

// WallObject represents a wall from the frontend
type WallObject struct {
	Type       string  `json:"type"`       // "wall"
	X          float64 `json:"x"`          // Center X
	Y          float64 `json:"y"`          // Center Y
	Length     float64 `json:"length"`     // Wall length
	Thickness  float64 `json:"thickness"`  // Wall thickness
	Rotation   float64 `json:"rotation"`   // Rotation in degrees
	Confidence float64 `json:"confidence"` // Detection confidence
	Source     string  `json:"source"`     // "detected" or "user"
}

// WallUploadMetadata contains PDF/canvas metadata
type WallUploadMetadata struct {
	CanvasWidth  int     `json:"canvas_width"`
	CanvasHeight int     `json:"canvas_height"`
	PDFScale     float64 `json:"pdf_scale"`
}

// WallUploadResponse is sent back to the frontend
type WallUploadResponse struct {
	Success      bool                   `json:"success"`
	BuildingID   string                 `json:"building_id,omitempty"`
	Message      string                 `json:"message"`
	Statistics   map[string]interface{} `json:"statistics,omitempty"`
	ProcessingMS int64                  `json:"processing_ms"`
}

// HandleWallUpload processes wall data from the PDF extractor
func HandleWallUpload(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()
	
	// Parse request
	var req WallUploadRequest
	if err := json.NewDecoder(r.Body).Err; err != nil {
		sendWallError(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendWallError(w, "Failed to parse request: "+err.Error(), http.StatusBadRequest)
		return
	}
	
	// Validate request
	if len(req.Objects) == 0 {
		sendWallError(w, "No walls provided", http.StatusBadRequest)
		return
	}
	
	// Convert walls to ArxObjects
	converter := converters.NewWallConverter()
	
	// Set scale based on building dimensions (assume 50m x 30m building for now)
	// In production, this would come from the request or be calculated
	converter.SetScaleFromPDF(
		req.Metadata.CanvasWidth,
		req.Metadata.CanvasHeight,
		50.0, // Building width in meters
		30.0, // Building height in meters
	)
	
	// Convert each wall object
	arxObjects := make([]*arxobject.ArxObject, 0, len(req.Objects))
	wallCount := 0
	userWallCount := 0
	totalConfidence := 0.0
	
	for _, obj := range req.Objects {
		if obj.Type != "wall" {
			continue
		}
		
		// Convert frontend wall format to WallSegment
		// The frontend sends center + length + rotation, we need to convert to endpoints
		halfLength := obj.Length / 2.0
		cos := math.Cos(obj.Rotation * math.Pi / 180.0)
		sin := math.Sin(obj.Rotation * math.Pi / 180.0)
		
		wallSegment := converters.WallSegment{
			X1:         obj.X - halfLength*cos,
			Y1:         obj.Y - halfLength*sin,
			X2:         obj.X + halfLength*cos,
			Y2:         obj.Y + halfLength*sin,
			Thickness:  obj.Thickness,
			Confidence: obj.Confidence,
			Type:       obj.Source,
		}
		
		arxObj := converter.ConvertWallToArxObject(wallSegment)
		arxObjects = append(arxObjects, arxObj)
		
		wallCount++
		totalConfidence += obj.Confidence
		
		if obj.Source == "user" {
			userWallCount++
		}
	}
	
	// In a real implementation, we would:
	// 1. Generate a building ID
	// 2. Store in database
	// 3. Process relationships between walls
	// For now, we'll just return success
	
	buildingID := generateBuildingID()
	
	// Calculate statistics
	avgConfidence := 0.0
	if wallCount > 0 {
		avgConfidence = totalConfidence / float64(wallCount)
	}
	
	stats := map[string]interface{}{
		"total_walls":     wallCount,
		"detected_walls":  wallCount - userWallCount,
		"user_walls":      userWallCount,
		"avg_confidence":  avgConfidence,
		"floor":           req.Floor,
	}
	
	// Send response
	processingTime := time.Since(startTime).Milliseconds()
	
	response := WallUploadResponse{
		Success:      true,
		BuildingID:   buildingID,
		Message:      fmt.Sprintf("Successfully processed %d walls", wallCount),
		Statistics:   stats,
		ProcessingMS: processingTime,
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func sendWallError(w http.ResponseWriter, message string, status int) {
	response := WallUploadResponse{
		Success: false,
		Message: message,
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(response)
}

func generateBuildingID() string {
	// Simple UUID generation
	return fmt.Sprintf("bld_%d", time.Now().Unix())
}