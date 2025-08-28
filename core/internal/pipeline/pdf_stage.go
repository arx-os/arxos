// Package pipeline - PDF processing stage for Progressive Construction Pipeline
package pipeline

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/confidence"
)

// PDFStage handles PDF analysis and initial ArxObject creation
type PDFStage struct {
	aiServiceURL string
}

// PDFExtractionResult represents the result from AI service PDF processing
type PDFExtractionResult struct {
	Elements     []PDFElement   `json:"elements"`
	Measurements []Measurement  `json:"measurements"`
	Rooms        []Room         `json:"rooms"`
	Scale        ScaleInfo      `json:"scale"`
	Metadata     PDFMetadata    `json:"metadata"`
}

// PDFElement represents an architectural element found in the PDF
type PDFElement struct {
	Type         string    `json:"type"`          // "wall", "door", "window", etc.
	Coordinates  []float64 `json:"coordinates"`   // [x1, y1, x2, y2]
	Dimensions   []float64 `json:"dimensions"`    // [width, height]
	Label        string    `json:"label,omitempty"`
	Confidence   float64   `json:"confidence"`
	Properties   map[string]interface{} `json:"properties,omitempty"`
}

// Measurement represents a dimension annotation found in the PDF
type Measurement struct {
	Value      float64   `json:"value"`
	Unit       string    `json:"unit"`
	Position   []float64 `json:"position"`     // [x, y]
	Direction  string    `json:"direction"`    // "horizontal", "vertical"
	Text       string    `json:"text"`         // Original text
	Confidence float64   `json:"confidence"`
}

// Room represents a room boundary identified in the PDF
type Room struct {
	Name        string    `json:"name"`
	Boundary    []float64 `json:"boundary"`     // Polygon coordinates
	Area        float64   `json:"area"`
	Center      []float64 `json:"center"`       // [x, y]
	Confidence  float64   `json:"confidence"`
}

// ScaleInfo represents scale information extracted from the PDF
type ScaleInfo struct {
	Ratio         float64 `json:"ratio"`          // pixels per unit
	Unit          string  `json:"unit"`           // "mm", "ft", etc.
	ScaleText     string  `json:"scale_text"`     // Original scale annotation
	Confidence    float64 `json:"confidence"`
	IsAutoScaled  bool    `json:"is_auto_scaled"` // Whether scale was auto-detected
}

// PDFMetadata contains metadata about the PDF processing
type PDFMetadata struct {
	FileName      string  `json:"file_name"`
	PageCount     int     `json:"page_count"`
	ProcessedPage int     `json:"processed_page"`
	Resolution    float64 `json:"resolution"`      // DPI
	Dimensions    []int   `json:"dimensions"`      // [width, height] in pixels
}

// NewPDFStage creates a new PDF processing stage
func NewPDFStage() *PDFStage {
	return &PDFStage{
		aiServiceURL: "http://localhost:5000", // Default AI service URL
	}
}

// SetAIServiceURL sets the URL for the AI service
func (ps *PDFStage) SetAIServiceURL(url string) {
	ps.aiServiceURL = url
}

// Process processes a PDF file and returns ArxObjects
func (ps *PDFStage) Process(ctx context.Context, pdfPath string, buildingID string) ([]*arxobject.ArxObjectUnified, error) {
	// Extract data from PDF using AI service
	extractionResult, err := ps.extractFromPDF(ctx, pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to extract data from PDF: %w", err)
	}
	
	// Convert extracted data to ArxObjects
	objects, err := ps.convertToArxObjects(extractionResult, buildingID, pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to convert to ArxObjects: %w", err)
	}
	
	return objects, nil
}

// extractFromPDF calls the AI service to extract data from PDF
func (ps *PDFStage) extractFromPDF(ctx context.Context, pdfPath string) (*PDFExtractionResult, error) {
	// For now, use the existing Python AI service via command line
	// In production, this would be an HTTP API call
	
	cmd := exec.CommandContext(ctx, "python", 
		"ai_service/main.py",
		"--mode", "pdf_extract",
		"--input", pdfPath,
		"--output", "json")
	
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("AI service execution failed: %w", err)
	}
	
	var result PDFExtractionResult
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("failed to parse AI service output: %w", err)
	}
	
	return &result, nil
}

// convertToArxObjects converts PDF extraction results to ArxObjects
func (ps *PDFStage) convertToArxObjects(result *PDFExtractionResult, buildingID string, sourcePath string) ([]*arxobject.ArxObjectUnified, error) {
	var objects []*arxobject.ArxObjectUnified
	
	// Convert rooms first (they become containers for other elements)
	roomObjects, err := ps.convertRooms(result.Rooms, buildingID, sourcePath, &result.Scale)
	if err != nil {
		return nil, fmt.Errorf("failed to convert rooms: %w", err)
	}
	objects = append(objects, roomObjects...)
	
	// Convert architectural elements
	elementObjects, err := ps.convertElements(result.Elements, buildingID, sourcePath, &result.Scale)
	if err != nil {
		return nil, fmt.Errorf("failed to convert elements: %w", err)
	}
	objects = append(objects, elementObjects...)
	
	return objects, nil
}

// convertRooms converts room boundaries to ArxObjects
func (ps *PDFStage) convertRooms(rooms []Room, buildingID string, sourcePath string, scale *ScaleInfo) ([]*arxobject.ArxObjectUnified, error) {
	var objects []*arxobject.ArxObjectUnified
	
	for i, room := range rooms {
		obj, err := ps.createRoomArxObject(room, buildingID, sourcePath, scale, i)
		if err != nil {
			return nil, fmt.Errorf("failed to create room object: %w", err)
		}
		objects = append(objects, obj)
	}
	
	return objects, nil
}

// convertElements converts PDF elements to ArxObjects
func (ps *PDFStage) convertElements(elements []PDFElement, buildingID string, sourcePath string, scale *ScaleInfo) ([]*arxobject.ArxObjectUnified, error) {
	var objects []*arxobject.ArxObjectUnified
	
	for i, element := range elements {
		obj, err := ps.createElementArxObject(element, buildingID, sourcePath, scale, i)
		if err != nil {
			return nil, fmt.Errorf("failed to create element object: %w", err)
		}
		objects = append(objects, obj)
	}
	
	return objects, nil
}

// createRoomArxObject creates an ArxObject for a room
func (ps *PDFStage) createRoomArxObject(room Room, buildingID string, sourcePath string, scale *ScaleInfo, index int) (*arxobject.ArxObjectUnified, error) {
	// Convert PDF coordinates to real-world coordinates
	realCoords := ps.convertCoordinates(room.Boundary, scale)
	
	// Create geometry
	geometry := arxobject.Geometry{
		Type:        "polygon",
		Coordinates: realCoords,
		// Area calculation in square millimeters
		Area: room.Area * scale.Ratio * scale.Ratio,
	}
	
	// Create confidence assessment
	conf := confidence.NewConfidence()
	conf.UpdateSource(room.Confidence, "pdf_extraction", map[string]interface{}{
		"room_detection": room.Confidence,
		"boundary_confidence": room.Confidence * 0.9, // Boundary typically less confident
	})
	
	// Create ArxObject
	obj := &arxobject.ArxObjectUnified{
		ID:          fmt.Sprintf("%s/f1/room/%d", buildingID, index+1),
		Type:        arxobject.TypeRoom,
		Name:        room.Name,
		Description: fmt.Sprintf("Room extracted from PDF: %s", room.Name),
		BuildingID:  buildingID,
		FloorID:     "f1", // Assume first floor for PDF
		Geometry:    geometry,
		Properties: arxobject.Properties{
			"area_sqm":       room.Area,
			"center_x":       room.Center[0],
			"center_y":       room.Center[1],
			"pdf_extracted":  true,
		},
		Confidence:   conf,
		SourceType:   "pdf",
		SourceFile:   filepath.Base(sourcePath),
		Version:      1,
	}
	
	return obj, nil
}

// createElementArxObject creates an ArxObject for an architectural element
func (ps *PDFStage) createElementArxObject(element PDFElement, buildingID string, sourcePath string, scale *ScaleInfo, index int) (*arxobject.ArxObjectUnified, error) {
	// Convert PDF coordinates to real-world coordinates
	realCoords := ps.convertCoordinates(element.Coordinates, scale)
	
	// Determine ArxObject type
	objType := ps.mapElementType(element.Type)
	
	// Create geometry based on element type
	geometry := ps.createElementGeometry(element, realCoords)
	
	// Create confidence assessment
	conf := confidence.NewConfidence()
	conf.UpdateSource(element.Confidence, "pdf_extraction", map[string]interface{}{
		"element_detection": element.Confidence,
		"type_confidence":   element.Confidence,
	})
	
	// Create properties
	properties := arxobject.Properties{
		"pdf_extracted": true,
		"element_type":  element.Type,
		"pdf_label":     element.Label,
	}
	
	// Add element-specific properties
	for key, value := range element.Properties {
		properties[key] = value
	}
	
	// Create ArxObject
	obj := &arxobject.ArxObjectUnified{
		ID:          fmt.Sprintf("%s/f1/%s/%d", buildingID, strings.ToLower(element.Type), index+1),
		Type:        objType,
		Name:        ps.generateElementName(element, index),
		Description: fmt.Sprintf("%s extracted from PDF", strings.Title(element.Type)),
		BuildingID:  buildingID,
		FloorID:     "f1",
		Geometry:    geometry,
		Properties:  properties,
		Confidence:  conf,
		SourceType:  "pdf",
		SourceFile:  filepath.Base(sourcePath),
		Version:     1,
	}
	
	return obj, nil
}

// convertCoordinates converts PDF pixel coordinates to real-world coordinates (in mm)
func (ps *PDFStage) convertCoordinates(coords []float64, scale *ScaleInfo) []float64 {
	realCoords := make([]float64, len(coords))
	
	// Convert based on scale ratio and unit
	unitMultiplier := ps.getUnitMultiplier(scale.Unit)
	
	for i, coord := range coords {
		// Convert: PDF pixels → real units → millimeters
		realCoords[i] = coord / scale.Ratio * unitMultiplier
	}
	
	return realCoords
}

// getUnitMultiplier returns multiplier to convert to millimeters
func (ps *PDFStage) getUnitMultiplier(unit string) float64 {
	switch strings.ToLower(unit) {
	case "mm", "millimeter", "millimeters":
		return 1.0
	case "cm", "centimeter", "centimeters":
		return 10.0
	case "m", "meter", "meters":
		return 1000.0
	case "in", "inch", "inches":
		return 25.4
	case "ft", "foot", "feet":
		return 304.8
	default:
		return 1.0 // Default to millimeters
	}
}

// mapElementType maps PDF element types to ArxObject types
func (ps *PDFStage) mapElementType(elementType string) arxobject.ArxObjectType {
	switch strings.ToLower(elementType) {
	case "wall":
		return arxobject.TypeWall
	case "door":
		return arxobject.TypeDoor
	case "window":
		return arxobject.TypeWindow
	case "column":
		return arxobject.TypeColumn
	case "beam":
		return arxobject.TypeBeam
	default:
		return arxobject.TypeCustom
	}
}

// createElementGeometry creates geometry based on element type
func (ps *PDFStage) createElementGeometry(element PDFElement, realCoords []float64) arxobject.Geometry {
	switch strings.ToLower(element.Type) {
	case "wall":
		return arxobject.Geometry{
			Type:        "line",
			Coordinates: realCoords,
			Width:       ps.getDefaultWidth(element.Type),
		}
	case "door", "window":
		return arxobject.Geometry{
			Type:        "rectangle",
			Coordinates: realCoords,
			Width:       element.Dimensions[0],
			Height:      element.Dimensions[1],
		}
	default:
		return arxobject.Geometry{
			Type:        "point",
			Coordinates: realCoords[:2], // Just x, y
		}
	}
}

// getDefaultWidth returns default width for element types (in mm)
func (ps *PDFStage) getDefaultWidth(elementType string) float64 {
	switch strings.ToLower(elementType) {
	case "wall":
		return 150.0 // 6 inches typical interior wall
	case "door":
		return 800.0 // Standard door width
	case "window":
		return 1200.0 // Standard window width
	default:
		return 100.0
	}
}

// generateElementName generates a descriptive name for an element
func (ps *PDFStage) generateElementName(element PDFElement, index int) string {
	if element.Label != "" {
		return element.Label
	}
	
	return fmt.Sprintf("%s_%d", strings.Title(element.Type), index+1)
}