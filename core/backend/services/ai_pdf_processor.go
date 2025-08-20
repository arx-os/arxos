package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"time"

	"arxos/arxobject"
	"github.com/google/uuid"
)

// AIPDFProcessor uses the Python AI service for PDF processing
type AIPDFProcessor struct {
	aiServiceURL string
	httpClient   *http.Client
	arxEngine    *arxobject.Engine
}

// NewAIPDFProcessor creates a new AI-powered PDF processor
func NewAIPDFProcessor(arxEngine *arxobject.Engine) *AIPDFProcessor {
	aiURL := os.Getenv("AI_SERVICE_URL")
	if aiURL == "" {
		aiURL = "http://localhost:8000" // Default to local Python service
	}

	return &AIPDFProcessor{
		aiServiceURL: aiURL,
		httpClient: &http.Client{
			Timeout: 60 * time.Second, // 60 second timeout for PDF processing
		},
		arxEngine: arxEngine,
	}
}

// ProcessPDF sends PDF to Python AI service for extraction
func (p *AIPDFProcessor) ProcessPDF(filepath string) (*ProcessingResult, error) {
	// Open the PDF file
	file, err := os.Open(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to open PDF: %w", err)
	}
	defer file.Close()

	// Create multipart form
	var requestBody bytes.Buffer
	writer := multipart.NewWriter(&requestBody)

	// Add file to form
	part, err := writer.CreateFormFile("file", filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to create form file: %w", err)
	}

	_, err = io.Copy(part, file)
	if err != nil {
		return nil, fmt.Errorf("failed to copy file: %w", err)
	}

	// Add optional parameters
	writer.WriteField("building_type", "educational") // Can be dynamic
	writer.WriteField("building_name", "School Building")

	err = writer.Close()
	if err != nil {
		return nil, fmt.Errorf("failed to close multipart writer: %w", err)
	}

	// Make request to Python AI service
	req, err := http.NewRequest("POST", p.aiServiceURL+"/api/v1/convert", &requestBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())

	resp, err := p.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("AI service request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("AI service returned status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var aiResult AIConversionResult
	if err := json.NewDecoder(resp.Body).Decode(&aiResult); err != nil {
		return nil, fmt.Errorf("failed to decode AI response: %w", err)
	}

	// Convert AI result to our format
	return p.convertAIResult(aiResult), nil
}

// convertAIResult converts Python AI service result to Go ProcessingResult
func (p *AIPDFProcessor) convertAIResult(aiResult AIConversionResult) *ProcessingResult {
	result := &ProcessingResult{
		ID:        uuid.New().String(),
		Filename:  aiResult.Filename,
		Status:    "completed",
		StartTime: time.Now(),
		Objects:   make([]*ExtractedObject, 0),
	}

	// Convert ArxObjects from AI service
	for _, aiObj := range aiResult.ArxObjects {
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

		// Extract geometry if present
		if aiObj.Geometry != nil {
			if coords, ok := aiObj.Geometry["coordinates"].([]interface{}); ok && len(coords) > 0 {
				// Handle different geometry types
				switch aiObj.Geometry["type"] {
				case "LineString":
					if len(coords) >= 2 {
						extractedObj.BoundingBox = p.calculateLineBounds(coords)
					}
				case "Polygon":
					extractedObj.BoundingBox = p.calculatePolygonBounds(coords)
				case "Point":
					if coord, ok := coords[0].([]interface{}); ok && len(coord) >= 2 {
						x, _ := coord[0].(float64)
						y, _ := coord[1].(float64)
						extractedObj.BoundingBox = BoundingBox{
							MinX: x - 5, MinY: y - 5,
							MaxX: x + 5, MaxY: y + 5,
						}
					}
				}
			}
		}

		// Add relationships
		for _, rel := range aiObj.Relationships {
			extractedObj.RelatedObjects = append(extractedObj.RelatedObjects, rel.TargetID)
		}

		result.Objects = append(result.Objects, extractedObj)
	}

	// Calculate statistics
	result.Statistics = p.calculateStatistics(result.Objects)
	result.ProcessingTime = time.Duration(aiResult.ProcessingTime * float64(time.Second))

	return result
}

func (p *AIPDFProcessor) calculateLineBounds(coords []interface{}) BoundingBox {
	bounds := BoundingBox{
		MinX: 1e9, MinY: 1e9,
		MaxX: -1e9, MaxY: -1e9,
	}

	for _, coord := range coords {
		if point, ok := coord.([]interface{}); ok && len(point) >= 2 {
			if x, ok := point[0].(float64); ok {
				if x < bounds.MinX {
					bounds.MinX = x
				}
				if x > bounds.MaxX {
					bounds.MaxX = x
				}
			}
			if y, ok := point[1].(float64); ok {
				if y < bounds.MinY {
					bounds.MinY = y
				}
				if y > bounds.MaxY {
					bounds.MaxY = y
				}
			}
		}
	}

	return bounds
}

func (p *AIPDFProcessor) calculatePolygonBounds(coords []interface{}) BoundingBox {
	// For polygons, first element is the outer ring
	if len(coords) > 0 {
		if ring, ok := coords[0].([]interface{}); ok {
			return p.calculateLineBounds(ring)
		}
	}
	return BoundingBox{}
}

func (p *AIPDFProcessor) calculateStatistics(objects []*ExtractedObject) ProcessingStatistics {
	stats := ProcessingStatistics{
		TotalObjects:      len(objects),
		ObjectsByType:     make(map[string]int),
		AverageConfidence: 0,
	}

	var totalConfidence float32
	for _, obj := range objects {
		stats.ObjectsByType[obj.Type]++
		totalConfidence += obj.Confidence.Overall

		if obj.Confidence.Overall < 0.5 {
			stats.LowConfidenceCount++
		} else if obj.Confidence.Overall > 0.8 {
			stats.HighConfidenceCount++
		}
	}

	if len(objects) > 0 {
		stats.AverageConfidence = totalConfidence / float32(len(objects))
	}

	return stats
}

// AIConversionResult represents the response from Python AI service
type AIConversionResult struct {
	ArxObjects         []AIArxObject   `json:"arxobjects"`
	OverallConfidence  float64         `json:"overall_confidence"`
	Uncertainties      []AIUncertainty `json:"uncertainties"`
	ProcessingTime     float64         `json:"processing_time"`
	Filename           string          `json:"filename,omitempty"`
}

type AIArxObject struct {
	ID            string                 `json:"id"`
	Type          string                 `json:"type"`
	Data          map[string]interface{} `json:"data"`
	Confidence    AIConfidence           `json:"confidence"`
	Geometry      map[string]interface{} `json:"geometry,omitempty"`
	Relationships []AIRelationship       `json:"relationships"`
	Metadata      map[string]interface{} `json:"metadata"`
}

type AIConfidence struct {
	Classification float64 `json:"classification"`
	Position       float64 `json:"position"`
	Properties     float64 `json:"properties"`
	Relationships  float64 `json:"relationships"`
	Overall        float64 `json:"overall"`
}

type AIRelationship struct {
	Type       string                 `json:"type"`
	TargetID   string                 `json:"targetId"`
	Confidence float64                `json:"confidence"`
	Properties map[string]interface{} `json:"properties"`
}

type AIUncertainty struct {
	ObjectType string                 `json:"object_type"`
	Location   map[string]interface{} `json:"location"`
	Confidence float64                `json:"confidence"`
	Reason     string                 `json:"reason"`
}