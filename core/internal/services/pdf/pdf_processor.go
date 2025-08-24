package pdf

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"time"

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/google/uuid"
)

// ProcessingResult represents the result of PDF processing
type ProcessingResult struct {
	ID             string                 `json:"id"`
	Filename       string                 `json:"filename"`
	Status         string                 `json:"status"`
	StartTime      time.Time              `json:"start_time"`
	ProcessingTime time.Duration          `json:"processing_time"`
	Objects        []*ExtractedObject     `json:"objects"`
	Statistics     map[string]interface{} `json:"statistics"`
}

// ExtractedObject represents an object extracted from PDF
type ExtractedObject struct {
	ID          string                    `json:"id"`
	Type        string                    `json:"type"`
	Confidence  arxobject.ConfidenceScore `json:"confidence"`
	Properties  map[string]interface{}    `json:"properties"`
	BoundingBox BoundingBox               `json:"bounding_box"`
}

// BoundingBox represents a 2D bounding box
type BoundingBox struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
}

// PDFProcessor handles PDF to ArxObject conversion by calling the AI service
type PDFProcessor struct {
	aiServiceURL string
	arxEngine    *arxobject.Engine
	httpClient   *http.Client
}

// NewPDFProcessor creates a new PDF processor that uses the AI service
func NewPDFProcessor(arxEngine *arxobject.Engine) *PDFProcessor {
	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:8000" // Default to local AI service
	}

	return &PDFProcessor{
		aiServiceURL: aiServiceURL,
		arxEngine:    arxEngine,
		httpClient: &http.Client{
			Timeout: 60 * time.Second, // 60 second timeout for PDF processing
		},
	}
}

// ProcessPDF sends the PDF to the Python AI service for processing
func (p *PDFProcessor) ProcessPDF(filepath string) (*ProcessingResult, error) {
	startTime := time.Now()

	// Open the PDF file
	file, err := os.Open(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to open PDF file: %w", err)
	}
	defer file.Close()

	// Get file info
	fileInfo, err := file.Stat()
	if err != nil {
		return nil, fmt.Errorf("failed to get file info: %w", err)
	}

	// Create multipart form
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add the file to the form
	part, err := writer.CreateFormFile("file", fileInfo.Name())
	if err != nil {
		return nil, fmt.Errorf("failed to create form file: %w", err)
	}

	_, err = io.Copy(part, file)
	if err != nil {
		return nil, fmt.Errorf("failed to copy file content: %w", err)
	}

	// Add building type if available
	buildingType := os.Getenv("DEFAULT_BUILDING_TYPE")
	if buildingType == "" {
		buildingType = "school" // Default for testing with school floor plans
	}
	writer.WriteField("building_type", buildingType)

	err = writer.Close()
	if err != nil {
		return nil, fmt.Errorf("failed to close multipart writer: %w", err)
	}

	// Create the request
	url := fmt.Sprintf("%s/api/v1/convert", p.aiServiceURL)
	req, err := http.NewRequest("POST", url, body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())

	// Send the request
	resp, err := p.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request to AI service: %w", err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("AI service returned error %d: %s", resp.StatusCode, string(bodyBytes))
	}

	// Parse the response
	var aiResponse AIServiceResponse
	err = json.NewDecoder(resp.Body).Decode(&aiResponse)
	if err != nil {
		return nil, fmt.Errorf("failed to decode AI service response: %w", err)
	}

	// Convert AI response to our ProcessingResult format
	result := &ProcessingResult{
		ID:             uuid.New().String(),
		Filename:       filepath,
		Status:         "completed",
		StartTime:      startTime,
		ProcessingTime: time.Since(startTime),
		Objects:        make([]*ExtractedObject, 0, len(aiResponse.ArxObjects)),
		Statistics:     make(map[string]interface{}),
	}

	// Convert ArxObjects from AI service to our format
	for _, aiObj := range aiResponse.ArxObjects {
		extractedObj := &ExtractedObject{
			ID:   aiObj.ID,
			Type: aiObj.Type,
			Confidence: arxobject.ConfidenceScore{
				Classification: float32(aiObj.Confidence.Classification),
				Position:       float32(aiObj.Confidence.Position),
				Properties:     float32(aiObj.Confidence.Properties),
				Relationships:  float32(aiObj.Confidence.Relationships),
				Overall:        float32(aiObj.Confidence.Overall),
			},
			Properties: aiObj.Data,
		}

		// Extract bounding box if available in geometry
		if aiObj.Geometry != nil {
			if coords, ok := aiObj.Geometry["coordinates"].([]interface{}); ok && len(coords) > 0 {
				// Simple bounding box calculation from coordinates
				extractedObj.BoundingBox = calculateBoundingBox(coords)
			}
		}

		result.Objects = append(result.Objects, extractedObj)
	}

	// Populate statistics
	result.Statistics["total_objects"] = len(result.Objects)
	result.Statistics["overall_confidence"] = aiResponse.OverallConfidence
	result.Statistics["processing_time_seconds"] = aiResponse.ProcessingTime
	result.Statistics["uncertainties"] = len(aiResponse.Uncertainties)

	// Count objects by type
	typeCounts := make(map[string]int)
	for _, obj := range result.Objects {
		typeCounts[obj.Type]++
	}
	result.Statistics["objects_by_type"] = typeCounts

	// Store ArxObjects in the engine if needed
	if p.arxEngine != nil {
		for _, obj := range result.Objects {
			arxObj := convertToArxObject(obj)
			if err := p.arxEngine.CreateObject(arxObj); err != nil {
				// Log error but don't fail the whole process
				fmt.Printf("Warning: failed to store ArxObject %s: %v\n", obj.ID, err)
			}
		}
	}

	return result, nil
}

// AIServiceResponse represents the response from the Python AI service
type AIServiceResponse struct {
	ArxObjects        []AIArxObject          `json:"arxobjects"`
	OverallConfidence float64                `json:"overall_confidence"`
	Uncertainties     []AIUncertainty        `json:"uncertainties"`
	ProcessingTime    float64                `json:"processing_time"`
	Metadata          map[string]interface{} `json:"metadata"`
}

// AIArxObject represents an ArxObject from the AI service
type AIArxObject struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	Data       map[string]interface{} `json:"data"`
	Confidence AIConfidenceScore      `json:"confidence"`
	Geometry   map[string]interface{} `json:"geometry"`
	Metadata   AIMetadata             `json:"metadata"`
}

// AIConfidenceScore represents confidence scores from the AI service
type AIConfidenceScore struct {
	Classification float64 `json:"classification"`
	Position       float64 `json:"position"`
	Properties     float64 `json:"properties"`
	Relationships  float64 `json:"relationships"`
	Overall        float64 `json:"overall"`
}

// AIMetadata represents metadata from the AI service
type AIMetadata struct {
	Source       string    `json:"source"`
	SourceDetail string    `json:"source_detail"`
	Created      time.Time `json:"created"`
	Validated    bool      `json:"validated"`
}

// AIUncertainty represents uncertainty information from the AI service
type AIUncertainty struct {
	ObjectID   string  `json:"object_id"`
	Confidence float64 `json:"confidence"`
	Reason     string  `json:"reason"`
}

// calculateBoundingBox calculates a bounding box from coordinates
func calculateBoundingBox(coords []interface{}) BoundingBox {
	if len(coords) == 0 {
		return BoundingBox{}
	}

	minX, minY := float64(1e9), float64(1e9)
	maxX, maxY := float64(-1e9), float64(-1e9)

	for _, coord := range coords {
		if point, ok := coord.([]interface{}); ok && len(point) >= 2 {
			if x, ok := point[0].(float64); ok {
				minX = minFloat64(minX, x)
				maxX = maxFloat64(maxX, x)
			}
			if y, ok := point[1].(float64); ok {
				minY = minFloat64(minY, y)
				maxY = maxFloat64(maxY, y)
			}
		}
	}

	return BoundingBox{
		MinX: minX,
		MinY: minY,
		MaxX: maxX,
		MaxY: maxY,
	}
}

// convertToArxObject converts an ExtractedObject to an ArxObject for storage
func convertToArxObject(extracted *ExtractedObject) *arxobject.ArxObject {
	// Generate coordinates from bounding box center
	centerX := int64((extracted.BoundingBox.MinX + extracted.BoundingBox.MaxX) / 2 * 1000000) // Convert to nanometers
	centerY := int64((extracted.BoundingBox.MinY + extracted.BoundingBox.MaxY) / 2 * 1000000)

	width := int64((extracted.BoundingBox.MaxX - extracted.BoundingBox.MinX) * 1000000)
	height := int64((extracted.BoundingBox.MaxY - extracted.BoundingBox.MinY) * 1000000)

	// Marshal properties to JSON
	propertiesJSON, _ := json.Marshal(extracted.Properties)

	return &arxobject.ArxObject{
		ID:               extracted.ID,
		UUID:             uuid.New().String(),
		Type:             extracted.Type,
		System:           determineSystem(extracted.Type),
		X:                centerX,
		Y:                centerY,
		Z:                0, // Default to ground level
		Width:            width,
		Height:           height,
		Depth:            100000000, // Default 100mm depth in nanometers
		ScaleMin:         0,
		ScaleMax:         9,
		Properties:       propertiesJSON,
		Confidence:       extracted.Confidence,
		ExtractionMethod: "ai_pdf_extraction",
		Source:           "pdf",
		CreatedAt:        time.Now(),
		UpdatedAt:        time.Now(),
	}
}

// determineSystem determines the system type from object type
func determineSystem(objectType string) string {
	switch objectType {
	case "wall", "column", "beam", "slab", "foundation":
		return "structural"
	case "door", "window":
		return "architectural"
	case "room", "space", "corridor":
		return "spatial"
	case "electrical_outlet", "electrical_panel", "electrical_switch":
		return "electrical"
	case "hvac_duct", "hvac_unit", "hvac_vent":
		return "hvac"
	case "plumbing_pipe", "plumbing_fixture":
		return "plumbing"
	default:
		return "general"
	}
}

// Helper functions
func minFloat64(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func maxFloat64(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}
