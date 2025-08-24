package ingestion

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

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/services"
	"github.com/arxos/arxos/core/wall_composition/types"
)

// EnhancedPDFUpload handles PDF uploads with BIM processing
func EnhancedPDFUpload(w http.ResponseWriter, r *http.Request) {
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

	// Step 1: Send to AI service for initial extraction
	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:5000"
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

	// Parse AI response
	var aiResult map[string]interface{}
	if err := json.Unmarshal(aiResponse, &aiResult); err != nil {
		respondWithError(w, http.StatusInternalServerError, "Invalid AI response")
		return
	}

	// Extract ArxObjects from AI response
	arxobjectsRaw, ok := aiResult["arxobjects"].([]interface{})
	if !ok {
		arxobjectsRaw = []interface{}{}
	}

	// Convert to ArxObject slice
	arxobjects := make([]arxobject.ArxObject, 0, len(arxobjectsRaw))
	for _, objRaw := range arxobjectsRaw {
		if objMap, ok := objRaw.(map[string]interface{}); ok {
			obj := arxobject.ArxObject{
				ID:   getStringField(objMap, "id"),
				Type: getStringField(objMap, "type"),
				System: getStringField(objMap, "system"),
				Confidence: getFloatField(objMap, "confidence"),
				Data: objMap["data"].(map[string]interface{}),
			}
			
			// Handle coordinates
			if coords := getCoordinates(objMap); coords != nil {
				obj.X = int32(coords[0])
				obj.Y = int32(coords[1])
				if len(coords) > 2 {
					obj.Width = int16(coords[2])
					obj.Height = int16(coords[3])
				}
			}
			
			// Store geometry if present
			if geometry, ok := objMap["geometry"]; ok {
				obj.Geometry = geometry
			}
			
			arxobjects = append(arxobjects, obj)
		}
	}

	// Step 2: Process through BIM processor
	processor := services.NewPDFToBIMProcessor(services.DefaultProcessorConfig())
	bimResult, err := processor.ProcessArxObjects(arxobjects)
	if err != nil {
		log.Printf("BIM processing error: %v", err)
		// Continue with raw objects if BIM processing fails
		bimResult = &services.BIMResult{
			WallStructures: []*types.WallStructure{},
			Rooms:          []*services.Room{},
			Confidence:     0.5,
		}
	}

	// Step 3: Convert to frontend format
	frontendObjects := convertToFrontendFormat(bimResult, arxobjects)

	// Generate building ID
	buildingID := fmt.Sprintf("building_%d", time.Now().Unix())

	// Store in database (if available)
	storedCount := 0
	db, err := connectToDatabase()
	if err == nil {
		defer db.Close()
		
		// Store building
		err = ensureBuildingExists(db, buildingID, header.Filename)
		if err != nil {
			log.Printf("Failed to ensure building exists: %v", err)
		}
		
		// Store ArxObjects
		for _, obj := range arxobjects {
			err = storeArxObject(db, &obj)
			if err != nil {
				log.Printf("Failed to store ArxObject: %v", err)
			} else {
				storedCount++
			}
		}
	}

	// Create response
	response := map[string]interface{}{
		"success":     true,
		"message":     fmt.Sprintf("Processed %s with BIM enhancement", header.Filename),
		"filename":    header.Filename,
		"building_id": buildingID,
		"arxobjects":  frontendObjects,
		"bim": map[string]interface{}{
			"walls":      len(bimResult.WallStructures),
			"rooms":      len(bimResult.Rooms),
			"doors":      len(bimResult.Doors),
			"windows":    len(bimResult.Windows),
			"confidence": bimResult.Confidence,
		},
		"statistics": map[string]interface{}{
			"total_objects":      len(frontendObjects),
			"walls_composed":     len(bimResult.WallStructures),
			"rooms_detected":     len(bimResult.Rooms),
			"overall_confidence": bimResult.Confidence,
			"processing_time":    aiResult["processing_time"],
			"stored_in_db":       storedCount > 0,
			"stored_count":       storedCount,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// convertToFrontendFormat converts BIM result to format expected by frontend
func convertToFrontendFormat(bimResult *services.BIMResult, rawObjects []arxobject.ArxObject) []map[string]interface{} {
	result := []map[string]interface{}{}
	
	// Add composed walls
	for _, wall := range bimResult.WallStructures {
		wallObj := map[string]interface{}{
			"id":         wall.ID,
			"type":       "wall",
			"confidence": wall.Confidence,
			"geometry": map[string]interface{}{
				"type": "LineString",
				"coordinates": [][]float64{
					{wall.StartPoint.ToMillimeters().X, wall.StartPoint.ToMillimeters().Y},
					{wall.EndPoint.ToMillimeters().X, wall.EndPoint.ToMillimeters().Y},
				},
			},
			"data": map[string]interface{}{
				"thickness_mm": wall.Thickness,
				"length_mm":    wall.Length,
				"segments":     len(wall.Segments),
			},
		}
		result = append(result, wallObj)
	}
	
	// Add detected rooms
	for _, room := range bimResult.Rooms {
		coords := [][]float64{}
		for _, point := range room.Boundaries {
			coords = append(coords, []float64{
				point.ToMillimeters().X,
				point.ToMillimeters().Y,
			})
		}
		
		roomObj := map[string]interface{}{
			"id":   room.ID,
			"type": "room",
			"geometry": map[string]interface{}{
				"type":        "Polygon",
				"coordinates": []interface{}{coords},
			},
			"data": map[string]interface{}{
				"area_sqm": room.Area / 1000000.0, // Convert mm² to m²
				"label":    room.Label,
			},
		}
		result = append(result, roomObj)
	}
	
	// Add doors
	for _, door := range bimResult.Doors {
		doorObj := map[string]interface{}{
			"id":   door.ID,
			"type": "door",
			"x":    door.Position.ToMillimeters().X,
			"y":    door.Position.ToMillimeters().Y,
			"width": door.Width,
			"data": map[string]interface{}{
				"wall_id": door.WallID,
			},
		}
		result = append(result, doorObj)
	}
	
	// Add windows
	for _, window := range bimResult.Windows {
		windowObj := map[string]interface{}{
			"id":     window.ID,
			"type":   "window",
			"x":      window.Position.ToMillimeters().X,
			"y":      window.Position.ToMillimeters().Y,
			"width":  window.Width,
			"height": window.Height,
			"data": map[string]interface{}{
				"wall_id": window.WallID,
			},
		}
		result = append(result, windowObj)
	}
	
	// Add other objects that weren't processed
	for _, obj := range rawObjects {
		// Skip if already processed as wall
		isWall := false
		for _, wall := range bimResult.WallStructures {
			for _, arxID := range wall.ArxObjects {
				if fmt.Sprintf("%d", arxID) == obj.ID {
					isWall = true
					break
				}
			}
			if isWall {
				break
			}
		}
		
		if !isWall && obj.Type != "wall" && obj.Type != "line" {
			// Add non-wall objects
			otherObj := map[string]interface{}{
				"id":         obj.ID,
				"type":       obj.Type,
				"confidence": obj.Confidence,
				"x":          float64(obj.X) / 1e6, // nm to mm
				"y":          float64(obj.Y) / 1e6,
				"width":      float64(obj.Width) / 1e6,
				"height":     float64(obj.Height) / 1e6,
				"data":       obj.Data,
			}
			
			if obj.Geometry != nil {
				otherObj["geometry"] = obj.Geometry
			}
			
			result = append(result, otherObj)
		}
	}
	
	return result
}

// Helper functions
func getStringField(m map[string]interface{}, key string) string {
	if val, ok := m[key].(string); ok {
		return val
	}
	return ""
}

func getFloatField(m map[string]interface{}, key string) float32 {
	if val, ok := m[key].(float64); ok {
		return float32(val)
	}
	return 0.5 // Default confidence
}

func getCoordinates(m map[string]interface{}) []float64 {
	// Try to extract coordinates from various formats
	if geometry, ok := m["geometry"].(map[string]interface{}); ok {
		if coords, ok := geometry["coordinates"].([]interface{}); ok {
			if len(coords) > 0 {
				// Handle LineString or Point
				if firstCoord, ok := coords[0].([]interface{}); ok {
					result := []float64{}
					for _, val := range firstCoord {
						if num, ok := val.(float64); ok {
							result = append(result, num)
						}
					}
					return result
				}
			}
		}
	}
	
	// Fallback to x,y properties
	if x, ok := m["x"].(float64); ok {
		if y, ok := m["y"].(float64); ok {
			result := []float64{x, y}
			if w, ok := m["width"].(float64); ok {
				result = append(result, w)
			}
			if h, ok := m["height"].(float64); ok {
				result = append(result, h)
			}
			return result
		}
	}
	
	return nil
}