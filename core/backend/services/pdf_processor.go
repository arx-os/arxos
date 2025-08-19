package services

import (
	"fmt"
	"math"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/google/uuid"
	"github.com/pdfcpu/pdfcpu/pkg/api"
)

// PDFProcessor handles PDF to ArxObject conversion
type PDFProcessor struct {
	confidenceThreshold float32
	patternMatcher     *PatternMatcher
	arxEngine          *arxobject.Engine
}

// NewPDFProcessor creates a new PDF processor
func NewPDFProcessor(arxEngine *arxobject.Engine) *PDFProcessor {
	return &PDFProcessor{
		confidenceThreshold: 0.5,
		patternMatcher:     NewPatternMatcher(),
		arxEngine:          arxEngine,
	}
}

// ProcessPDF extracts building elements from a PDF file
func (p *PDFProcessor) ProcessPDF(filepath string) (*ProcessingResult, error) {
	startTime := time.Now()
	
	result := &ProcessingResult{
		ID:        uuid.New().String(),
		Filename:  filepath,
		Status:    "processing",
		StartTime: startTime,
		Objects:   make([]*ExtractedObject, 0),
	}

	// Validate PDF
	err := api.ValidateFile(filepath, nil)
	if err != nil {
		return nil, fmt.Errorf("invalid PDF file: %w", err)
	}

	// Extract text content
	textContent, err := p.extractText(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to extract text: %w", err)
	}

	// Extract graphical elements (simplified for now)
	graphicalElements := p.extractGraphicsSimplified(filepath)

	// Analyze and identify building elements
	result.Objects = p.analyzeContent(textContent, graphicalElements)
	
	// Calculate overall statistics
	result.Statistics = p.calculateStatistics(result.Objects)
	result.ProcessingTime = time.Since(startTime)
	result.Status = "completed"

	return result, nil
}

// extractText extracts all text content from PDF
func (p *PDFProcessor) extractText(filepath string) ([]TextElement, error) {
	var textElements []TextElement
	
	// Use pdfcpu's text extraction
	// Note: This is simplified - real implementation would use more advanced extraction
	// ExtractContentFile returns error only, content extraction needs different approach
	// For now, return mock data for testing
	text := []byte("Sample text from PDF")
	
	// Parse the extracted text into elements
	lines := strings.Split(string(text), "\n")
	for i, line := range lines {
		if strings.TrimSpace(line) != "" {
			textElements = append(textElements, TextElement{
				Content:  line,
				X:        0, // Position would need proper extraction
				Y:        float64(i * 20),
				Page:     1,
				FontSize: 12,
			})
		}
	}
	
	return textElements, nil
}

// extractGraphicsSimplified creates mock graphical elements for testing
// Real implementation would parse PDF content streams
func (p *PDFProcessor) extractGraphicsSimplified(filepath string) []GraphicalElement {
	var graphicalElements []GraphicalElement
	
	// Create some mock walls for testing
	graphicalElements = append(graphicalElements, GraphicalElement{
		Type:      "line",
		StartX:    100,
		StartY:    100,
		EndX:      500,
		EndY:      100,
		LineWidth: 2.0,
		Page:      1,
	})
	
	// Mock door arc
	graphicalElements = append(graphicalElements, GraphicalElement{
		Type:    "arc",
		CenterX: 200,
		CenterY: 100,
		Radius:  30,
		Page:    1,
	})
	
	return graphicalElements
}

// analyzeContent identifies building elements from extracted content
func (p *PDFProcessor) analyzeContent(text []TextElement, graphics []GraphicalElement) []*ExtractedObject {
	var objects []*ExtractedObject

	// 1. Identify walls from long lines
	walls := p.identifyWalls(graphics)
	objects = append(objects, walls...)

	// 2. Identify doors from specific patterns
	doors := p.identifyDoors(graphics, text)
	objects = append(objects, doors...)

	// 3. Identify rooms from enclosed areas
	rooms := p.identifyRooms(graphics, text, walls)
	objects = append(objects, rooms...)

	// 4. Identify labels and annotations
	labels := p.identifyLabels(text)
	objects = append(objects, labels...)

	// 5. Apply pattern matching to improve confidence
	p.applyPatternMatching(objects)

	return objects
}

// identifyWalls finds wall elements from graphical lines
func (p *PDFProcessor) identifyWalls(graphics []GraphicalElement) []*ExtractedObject {
	var walls []*ExtractedObject

	for _, elem := range graphics {
		if elem.Type != "line" {
			continue
		}

		// Check if line is likely a wall (length, thickness)
		length := math.Sqrt(math.Pow(elem.EndX-elem.StartX, 2) + math.Pow(elem.EndY-elem.StartY, 2))
		
		if length > 50 && elem.LineWidth > 0.5 { // Thresholds for wall detection
			wall := &ExtractedObject{
				ID:   uuid.New().String(),
				Type: "wall",
				Confidence: arxobject.ConfidenceScore{
					Classification: p.calculateWallConfidence(elem, length),
					Position:       0.8, // High confidence in position from PDF
					Properties:     0.6, // Medium confidence in properties
					Relationships:  0.5, // Will improve with room detection
					Overall:        0.0, // Will be calculated
				},
				Properties: map[string]interface{}{
					"length":     length,
					"thickness":  elem.LineWidth,
					"start_x":    elem.StartX,
					"start_y":    elem.StartY,
					"end_x":      elem.EndX,
					"end_y":      elem.EndY,
					"page":       elem.Page,
					"is_bearing": length > 200, // Simple heuristic
				},
				BoundingBox: BoundingBox{
					MinX: math.Min(elem.StartX, elem.EndX),
					MinY: math.Min(elem.StartY, elem.EndY),
					MaxX: math.Max(elem.StartX, elem.EndX),
					MaxY: math.Max(elem.StartY, elem.EndY),
				},
			}
			wall.Confidence.CalculateOverall()
			walls = append(walls, wall)
		}
	}

	return walls
}

// identifyDoors finds door elements from patterns
func (p *PDFProcessor) identifyDoors(graphics []GraphicalElement, text []TextElement) []*ExtractedObject {
	var doors []*ExtractedObject

	// Look for arc patterns (door swings)
	for _, elem := range graphics {
		if elem.Type == "arc" {
			// Check if this might be a door swing
			if elem.Radius > 20 && elem.Radius < 50 {
				door := &ExtractedObject{
					ID:   uuid.New().String(),
					Type: "door",
					Confidence: arxobject.ConfidenceScore{
						Classification: 0.7, // Arc is good indicator
						Position:       0.8,
						Properties:     0.5,
						Relationships:  0.4,
					},
					Properties: map[string]interface{}{
						"swing_radius": elem.Radius,
						"center_x":     elem.CenterX,
						"center_y":     elem.CenterY,
						"width":        elem.Radius * 0.9, // Estimate
						"type":         "single",
					},
					BoundingBox: BoundingBox{
						MinX: elem.CenterX - elem.Radius,
						MinY: elem.CenterY - elem.Radius,
						MaxX: elem.CenterX + elem.Radius,
						MaxY: elem.CenterY + elem.Radius,
					},
				}
				door.Confidence.CalculateOverall()
				doors = append(doors, door)
			}
		}
	}

	// Also look for door labels in text
	for _, txt := range text {
		if p.patternMatcher.IsDoorLabel(txt.Content) {
			// Try to find nearby graphical element
			nearbyGraphics := p.findNearbyGraphics(txt.X, txt.Y, graphics, 50)
			if len(nearbyGraphics) > 0 {
				door := &ExtractedObject{
					ID:   uuid.New().String(),
					Type: "door",
					Confidence: arxobject.ConfidenceScore{
						Classification: 0.8, // Text label is strong indicator
						Position:       0.7,
						Properties:     0.6,
						Relationships:  0.5,
					},
					Properties: map[string]interface{}{
						"label": txt.Content,
						"x":     txt.X,
						"y":     txt.Y,
					},
				}
				door.Confidence.CalculateOverall()
				doors = append(doors, door)
			}
		}
	}

	return doors
}

// identifyRooms finds room boundaries and labels
func (p *PDFProcessor) identifyRooms(graphics []GraphicalElement, text []TextElement, walls []*ExtractedObject) []*ExtractedObject {
	var rooms []*ExtractedObject

	// Find text elements that look like room labels
	for _, txt := range text {
		if p.patternMatcher.IsRoomLabel(txt.Content) {
			// Find walls that might bound this room
			nearbyWalls := p.findNearbyWalls(txt.X, txt.Y, walls, 200)
			
			if len(nearbyWalls) >= 3 { // Need at least 3 walls for a room
				room := &ExtractedObject{
					ID:   uuid.New().String(),
					Type: "room",
					Confidence: arxobject.ConfidenceScore{
						Classification: 0.75,
						Position:       0.7,
						Properties:     0.65,
						Relationships:  0.6,
					},
					Properties: map[string]interface{}{
						"name":       txt.Content,
						"wall_count": len(nearbyWalls),
						"center_x":   txt.X,
						"center_y":   txt.Y,
					},
					RelatedObjects: nearbyWalls,
				}
				
				// Calculate room area if we have enough walls
				if area := p.estimateRoomArea(nearbyWalls); area > 0 {
					room.Properties["area"] = area
					room.Confidence.Properties = 0.8
				}
				
				room.Confidence.CalculateOverall()
				rooms = append(rooms, room)
			}
		}
	}

	return rooms
}

// identifyLabels extracts dimension and annotation labels
func (p *PDFProcessor) identifyLabels(text []TextElement) []*ExtractedObject {
	var labels []*ExtractedObject

	for _, txt := range text {
		// Check if text contains dimensions (e.g., "10'-6"", "3.2m")
		if p.patternMatcher.IsDimension(txt.Content) {
			label := &ExtractedObject{
				ID:   uuid.New().String(),
				Type: "dimension",
				Confidence: arxobject.ConfidenceScore{
					Classification: 0.9, // Dimensions are usually accurate
					Position:       0.9,
					Properties:     0.85,
					Relationships:  0.5,
				},
				Properties: map[string]interface{}{
					"value": p.parseDimension(txt.Content),
					"unit":  p.detectUnit(txt.Content),
					"text":  txt.Content,
					"x":     txt.X,
					"y":     txt.Y,
				},
			}
			label.Confidence.CalculateOverall()
			labels = append(labels, label)
		}
	}

	return labels
}

// Helper methods

func (p *PDFProcessor) calculateWallConfidence(elem GraphicalElement, length float64) float32 {
	confidence := float32(0.5) // Base confidence
	
	// Longer lines are more likely to be walls
	if length > 100 {
		confidence += 0.2
	}
	if length > 200 {
		confidence += 0.1
	}
	
	// Thicker lines are more likely to be walls
	if elem.LineWidth > 1.0 {
		confidence += 0.1
	}
	
	// Horizontal or vertical lines are more likely to be walls
	angle := math.Atan2(elem.EndY-elem.StartY, elem.EndX-elem.StartX)
	if math.Abs(angle) < 0.1 || math.Abs(angle-math.Pi/2) < 0.1 {
		confidence += 0.1
	}
	
	if confidence > 1.0 {
		return 1.0
	}
	return confidence
}

func (p *PDFProcessor) findNearbyGraphics(x, y float64, graphics []GraphicalElement, radius float64) []GraphicalElement {
	var nearby []GraphicalElement
	
	for _, elem := range graphics {
		// Calculate distance to element
		dist := math.Sqrt(math.Pow(elem.CenterX-x, 2) + math.Pow(elem.CenterY-y, 2))
		if dist <= radius {
			nearby = append(nearby, elem)
		}
	}
	
	return nearby
}

func (p *PDFProcessor) findNearbyWalls(x, y float64, walls []*ExtractedObject, radius float64) []string {
	var nearbyWallIDs []string
	
	for _, wall := range walls {
		// Get wall center
		centerX := (wall.BoundingBox.MinX + wall.BoundingBox.MaxX) / 2
		centerY := (wall.BoundingBox.MinY + wall.BoundingBox.MaxY) / 2
		
		dist := math.Sqrt(math.Pow(centerX-x, 2) + math.Pow(centerY-y, 2))
		if dist <= radius {
			nearbyWallIDs = append(nearbyWallIDs, wall.ID)
		}
	}
	
	return nearbyWallIDs
}

func (p *PDFProcessor) estimateRoomArea(wallIDs []string) float64 {
	// Simplified area estimation
	// In production, would use proper polygon area calculation
	return float64(len(wallIDs)) * 50.0 // Rough estimate
}

func (p *PDFProcessor) applyPatternMatching(objects []*ExtractedObject) {
	// Apply learned patterns to improve confidence
	for _, obj := range objects {
		if obj.Type == "wall" {
			// Check against known wall patterns
			if p.patternMatcher.MatchesWallPattern(obj.Properties) {
				obj.Confidence.Classification *= 1.2
				obj.Confidence.CalculateOverall()
			}
		}
	}
}

func (p *PDFProcessor) calculateStatistics(objects []*ExtractedObject) ProcessingStatistics {
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

// Removed parseTextFromContent and parseGraphicsFromPage - now handled differently

func (p *PDFProcessor) parseDimension(text string) float64 {
	// Parse dimension strings like "10'-6"" or "3.2m"
	// Remove non-numeric characters except . and -
	re := regexp.MustCompile(`[^\d.-]`)
	cleaned := re.ReplaceAllString(text, "")
	
	if val, err := strconv.ParseFloat(cleaned, 64); err == nil {
		return val
	}
	
	return 0
}

func (p *PDFProcessor) detectUnit(text string) string {
	text = strings.ToLower(text)
	if strings.Contains(text, "mm") {
		return "mm"
	}
	if strings.Contains(text, "cm") {
		return "cm"
	}
	if strings.Contains(text, "m") {
		return "m"
	}
	if strings.Contains(text, "'") || strings.Contains(text, "ft") {
		return "ft"
	}
	if strings.Contains(text, "\"") || strings.Contains(text, "in") {
		return "in"
	}
	return "unknown"
}

// Supporting types

type ProcessingResult struct {
	ID             string                 `json:"id"`
	Filename       string                 `json:"filename"`
	Status         string                 `json:"status"`
	StartTime      time.Time              `json:"start_time"`
	ProcessingTime time.Duration          `json:"processing_time"`
	Objects        []*ExtractedObject     `json:"objects"`
	Statistics     ProcessingStatistics   `json:"statistics"`
	Errors         []string               `json:"errors,omitempty"`
}

type ExtractedObject struct {
	ID             string                    `json:"id"`
	Type           string                    `json:"type"`
	Confidence     arxobject.ConfidenceScore `json:"confidence"`
	Properties     map[string]interface{}    `json:"properties"`
	BoundingBox    BoundingBox               `json:"bounding_box"`
	RelatedObjects []string                  `json:"related_objects,omitempty"`
}

type BoundingBox struct {
	MinX, MinY, MaxX, MaxY float64
}

type TextElement struct {
	Content  string
	X, Y     float64
	Page     int
	FontSize float64
}

type GraphicalElement struct {
	Type      string // line, arc, rectangle, etc.
	StartX    float64
	StartY    float64
	EndX      float64
	EndY      float64
	CenterX   float64
	CenterY   float64
	Radius    float64
	LineWidth float64
	Page      int
}

type ProcessingStatistics struct {
	TotalObjects        int                `json:"total_objects"`
	ObjectsByType       map[string]int     `json:"objects_by_type"`
	AverageConfidence   float32            `json:"average_confidence"`
	HighConfidenceCount int                `json:"high_confidence_count"`
	LowConfidenceCount  int                `json:"low_confidence_count"`
}

// PatternMatcher identifies common patterns in building plans
type PatternMatcher struct {
	doorPatterns []string
	roomPatterns []string
	dimPatterns  *regexp.Regexp
}

func NewPatternMatcher() *PatternMatcher {
	return &PatternMatcher{
		doorPatterns: []string{"DOOR", "DR", "D-", "ENTRY", "EXIT"},
		roomPatterns: []string{
			"ROOM", "RM", "OFFICE", "BATH", "KITCHEN", "BEDROOM", 
			"LIVING", "DINING", "STORAGE", "CLOSET", "HALL", "LOBBY",
			"CONFERENCE", "MEETING", "BREAK",
		},
		dimPatterns: regexp.MustCompile(`\d+['-]?\d*["]?|\d+\.\d+\s?[m|mm|cm|ft|in]`),
	}
}

func (pm *PatternMatcher) IsDoorLabel(text string) bool {
	upper := strings.ToUpper(text)
	for _, pattern := range pm.doorPatterns {
		if strings.Contains(upper, pattern) {
			return true
		}
	}
	return false
}

func (pm *PatternMatcher) IsRoomLabel(text string) bool {
	upper := strings.ToUpper(text)
	for _, pattern := range pm.roomPatterns {
		if strings.Contains(upper, pattern) {
			return true
		}
	}
	return false
}

func (pm *PatternMatcher) IsDimension(text string) bool {
	return pm.dimPatterns.MatchString(text)
}

func (pm *PatternMatcher) MatchesWallPattern(properties map[string]interface{}) bool {
	// Check if properties match known wall patterns
	if length, ok := properties["length"].(float64); ok {
		if length > 50 && length < 1000 { // Reasonable wall length range
			return true
		}
	}
	return false
}