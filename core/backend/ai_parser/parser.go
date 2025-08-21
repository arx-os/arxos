package ai_parser

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"math"
	"sort"
	"time"
)

// AIParser represents the AI-powered PDF parsing service
type AIParser struct {
	config           *ParserConfig
	symbolDetector   *SymbolDetector
	textExtractor    *TextExtractor
	patternRecognizer *PatternRecognizer
	confidenceScorer *ConfidenceScorer
}

// ParserConfig contains configuration for the AI parser
type ParserConfig struct {
	MinConfidence     float32
	SymbolLibraryPath string
	OCRLanguage       string
	EnableDeepLearning bool
	MaxProcessingTime time.Duration
}

// ParseResult represents the result of parsing a PDF
type ParseResult struct {
	Elements      []DetectedElement   `json:"elements"`
	Relationships []ElementRelation   `json:"relationships"`
	Metadata      DocumentMetadata    `json:"metadata"`
	Statistics    ParseStatistics     `json:"statistics"`
	ProcessTime   time.Duration       `json:"process_time"`
}

// DetectedElement represents a detected architectural element
type DetectedElement struct {
	ID           string              `json:"id"`
	Type         string              `json:"type"`
	System       string              `json:"system"`
	Bounds       BoundingBox         `json:"bounds"`
	Confidence   ConfidenceScore     `json:"confidence"`
	Properties   map[string]interface{} `json:"properties"`
	Annotations  []Annotation        `json:"annotations"`
	Pattern      string              `json:"pattern"`
}

// BoundingBox represents the location and size of an element
type BoundingBox struct {
	X      float64 `json:"x"`
	Y      float64 `json:"y"`
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
	Rotation float64 `json:"rotation"`
}

// ConfidenceScore represents multi-dimensional confidence
type ConfidenceScore struct {
	Overall        float32 `json:"overall"`
	Classification float32 `json:"classification"`
	Position       float32 `json:"position"`
	Properties     float32 `json:"properties"`
	OCR            float32 `json:"ocr"`
}

// ElementRelation represents relationships between elements
type ElementRelation struct {
	Source     string  `json:"source"`
	Target     string  `json:"target"`
	Type       string  `json:"type"`
	Confidence float32 `json:"confidence"`
	Properties map[string]interface{} `json:"properties"`
}

// Annotation represents text or dimensional annotations
type Annotation struct {
	Type       string  `json:"type"`
	Text       string  `json:"text"`
	Position   Point   `json:"position"`
	Confidence float32 `json:"confidence"`
}

// Point represents a 2D point
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// DocumentMetadata contains metadata extracted from the document
type DocumentMetadata struct {
	Title        string            `json:"title"`
	Scale        string            `json:"scale"`
	DrawingNumber string           `json:"drawing_number"`
	Date         string            `json:"date"`
	Author       string            `json:"author"`
	Building     string            `json:"building"`
	Floor        string            `json:"floor"`
	Units        string            `json:"units"`
	North        float64           `json:"north_angle"`
	Grid         []GridLine        `json:"grid"`
	Properties   map[string]string `json:"properties"`
}

// GridLine represents a construction grid line
type GridLine struct {
	Label    string  `json:"label"`
	Type     string  `json:"type"` // horizontal, vertical
	Position float64 `json:"position"`
}

// ParseStatistics contains statistics about the parsing process
type ParseStatistics struct {
	TotalElements    int            `json:"total_elements"`
	ElementsByType   map[string]int `json:"elements_by_type"`
	ElementsBySystem map[string]int `json:"elements_by_system"`
	ConfidenceDistribution map[string]int `json:"confidence_distribution"`
	ProcessingSteps  []ProcessStep  `json:"processing_steps"`
}

// ProcessStep represents a step in the processing pipeline
type ProcessStep struct {
	Name     string        `json:"name"`
	Duration time.Duration `json:"duration"`
	Items    int           `json:"items"`
	Success  bool          `json:"success"`
}

// NewAIParser creates a new AI parser instance
func NewAIParser(config *ParserConfig) *AIParser {
	return &AIParser{
		config:           config,
		symbolDetector:   NewSymbolDetector(),
		textExtractor:    NewTextExtractor(),
		patternRecognizer: NewPatternRecognizer(),
		confidenceScorer: NewConfidenceScorer(),
	}
}

// ParsePDF parses a PDF file and extracts architectural elements
func (p *AIParser) ParsePDF(pdfPath string) (*ParseResult, error) {
	startTime := time.Now()
	result := &ParseResult{
		Elements:      []DetectedElement{},
		Relationships: []ElementRelation{},
		Statistics:    ParseStatistics{
			ElementsByType:   make(map[string]int),
			ElementsBySystem: make(map[string]int),
			ConfidenceDistribution: make(map[string]int),
			ProcessingSteps:  []ProcessStep{},
		},
	}

	// Step 1: Convert PDF to images
	stepStart := time.Now()
	images, err := p.convertPDFToImages(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to convert PDF: %w", err)
	}
	result.Statistics.ProcessingSteps = append(result.Statistics.ProcessingSteps, ProcessStep{
		Name:     "PDF Conversion",
		Duration: time.Since(stepStart),
		Items:    len(images),
		Success:  true,
	})

	// Step 2: Extract text and metadata
	stepStart = time.Now()
	metadata, textBlocks := p.textExtractor.ExtractFromImages(images)
	result.Metadata = metadata
	result.Statistics.ProcessingSteps = append(result.Statistics.ProcessingSteps, ProcessStep{
		Name:     "Text Extraction",
		Duration: time.Since(stepStart),
		Items:    len(textBlocks),
		Success:  true,
	})

	// Step 3: Detect architectural symbols
	stepStart = time.Now()
	symbols := p.symbolDetector.DetectSymbols(images)
	result.Statistics.ProcessingSteps = append(result.Statistics.ProcessingSteps, ProcessStep{
		Name:     "Symbol Detection",
		Duration: time.Since(stepStart),
		Items:    len(symbols),
		Success:  true,
	})

	// Step 4: Recognize patterns (walls, rooms, etc.)
	stepStart = time.Now()
	patterns := p.patternRecognizer.RecognizePatterns(images, symbols)
	result.Statistics.ProcessingSteps = append(result.Statistics.ProcessingSteps, ProcessStep{
		Name:     "Pattern Recognition",
		Duration: time.Since(stepStart),
		Items:    len(patterns),
		Success:  true,
	})

	// Step 5: Combine and correlate all detected elements
	stepStart = time.Now()
	elements := p.combineDetections(symbols, patterns, textBlocks)
	result.Elements = elements
	result.Statistics.ProcessingSteps = append(result.Statistics.ProcessingSteps, ProcessStep{
		Name:     "Element Correlation",
		Duration: time.Since(stepStart),
		Items:    len(elements),
		Success:  true,
	})

	// Step 6: Identify relationships between elements
	stepStart = time.Now()
	relationships := p.identifyRelationships(elements)
	result.Relationships = relationships
	result.Statistics.ProcessingSteps = append(result.Statistics.ProcessingSteps, ProcessStep{
		Name:     "Relationship Analysis",
		Duration: time.Since(stepStart),
		Items:    len(relationships),
		Success:  true,
	})

	// Step 7: Calculate confidence scores
	stepStart = time.Now()
	p.calculateConfidenceScores(result)
	result.Statistics.ProcessingSteps = append(result.Statistics.ProcessingSteps, ProcessStep{
		Name:     "Confidence Scoring",
		Duration: time.Since(stepStart),
		Items:    len(result.Elements),
		Success:  true,
	})

	// Calculate statistics
	p.calculateStatistics(result)
	result.ProcessTime = time.Since(startTime)

	return result, nil
}

// convertPDFToImages converts PDF pages to images for processing
func (p *AIParser) convertPDFToImages(pdfPath string) ([]image.Image, error) {
	// Call AI service for PDF processing
	return nil, fmt.Errorf("PDF processing should use AI service at %s/api/v1/convert", p.aiServiceURL)
}

// combineDetections combines detections from different sources
func (p *AIParser) combineDetections(symbols []Symbol, patterns []Pattern, textBlocks []TextBlock) []DetectedElement {
	elements := []DetectedElement{}
	idCounter := 0

	// Convert symbols to elements
	for _, sym := range symbols {
		idCounter++
		elem := DetectedElement{
			ID:     fmt.Sprintf("E%06d", idCounter),
			Type:   sym.Type,
			System: p.inferSystem(sym.Type),
			Bounds: BoundingBox{
				X:      sym.X,
				Y:      sym.Y,
				Width:  sym.Width,
				Height: sym.Height,
			},
			Confidence: ConfidenceScore{
				Classification: sym.Confidence,
				Position:       0.95,
				Properties:     0.80,
				OCR:            0.00,
				Overall:        sym.Confidence * 0.9,
			},
			Properties: sym.Properties,
		}
		elements = append(elements, elem)
	}

	// Add patterns as elements
	for _, pat := range patterns {
		idCounter++
		elem := DetectedElement{
			ID:      fmt.Sprintf("E%06d", idCounter),
			Type:    pat.Type,
			System:  p.inferSystem(pat.Type),
			Pattern: pat.PatternID,
			Bounds: BoundingBox{
				X:      pat.Bounds.X,
				Y:      pat.Bounds.Y,
				Width:  pat.Bounds.Width,
				Height: pat.Bounds.Height,
			},
			Confidence: ConfidenceScore{
				Classification: pat.Confidence,
				Position:       0.92,
				Properties:     0.75,
				Overall:        pat.Confidence * 0.85,
			},
			Properties: pat.Properties,
		}
		elements = append(elements, elem)
	}

	// Associate text annotations with nearby elements
	for i := range elements {
		for _, text := range textBlocks {
			if p.isNear(elements[i].Bounds, text.Bounds, 50) {
				elements[i].Annotations = append(elements[i].Annotations, Annotation{
					Type:       "label",
					Text:       text.Text,
					Position:   Point{X: text.Bounds.X, Y: text.Bounds.Y},
					Confidence: text.Confidence,
				})
				// Update OCR confidence
				elements[i].Confidence.OCR = text.Confidence
			}
		}
	}

	return elements
}

// identifyRelationships identifies relationships between elements
func (p *AIParser) identifyRelationships(elements []DetectedElement) []ElementRelation {
	relations := []ElementRelation{}

	for i, elem1 := range elements {
		for j, elem2 := range elements {
			if i >= j {
				continue
			}

			// Check for adjacency
			if p.isAdjacent(elem1.Bounds, elem2.Bounds) {
				relations = append(relations, ElementRelation{
					Source:     elem1.ID,
					Target:     elem2.ID,
					Type:       "adjacent",
					Confidence: 0.95,
				})
			}

			// Check for containment
			if p.contains(elem1.Bounds, elem2.Bounds) {
				relations = append(relations, ElementRelation{
					Source:     elem1.ID,
					Target:     elem2.ID,
					Type:       "contains",
					Confidence: 0.98,
				})
			}

			// Check for alignment
			if p.isAligned(elem1.Bounds, elem2.Bounds) {
				relations = append(relations, ElementRelation{
					Source:     elem1.ID,
					Target:     elem2.ID,
					Type:       "aligned",
					Confidence: 0.90,
				})
			}

			// Check for connection (doors to rooms, etc.)
			if p.isConnected(elem1, elem2) {
				relations = append(relations, ElementRelation{
					Source:     elem1.ID,
					Target:     elem2.ID,
					Type:       "connected",
					Confidence: 0.88,
					Properties: map[string]interface{}{
						"connection_type": p.getConnectionType(elem1.Type, elem2.Type),
					},
				})
			}
		}
	}

	return relations
}

// calculateConfidenceScores calculates final confidence scores
func (p *AIParser) calculateConfidenceScores(result *ParseResult) {
	for i := range result.Elements {
		elem := &result.Elements[i]
		
		// Weight different confidence factors
		weights := map[string]float32{
			"classification": 0.40,
			"position":       0.25,
			"properties":     0.20,
			"ocr":            0.15,
		}

		// Calculate weighted average
		overall := elem.Confidence.Classification * weights["classification"] +
			elem.Confidence.Position * weights["position"] +
			elem.Confidence.Properties * weights["properties"]

		if elem.Confidence.OCR > 0 {
			overall += elem.Confidence.OCR * weights["ocr"]
		} else {
			// Redistribute OCR weight if no OCR
			overall = overall / (1 - weights["ocr"])
		}

		// Boost confidence if element has relationships
		relationCount := 0
		for _, rel := range result.Relationships {
			if rel.Source == elem.ID || rel.Target == elem.ID {
				relationCount++
			}
		}
		if relationCount > 0 {
			overall = float32(math.Min(float64(overall*1.1), 1.0))
		}

		elem.Confidence.Overall = overall
	}
}

// calculateStatistics calculates parsing statistics
func (p *AIParser) calculateStatistics(result *ParseResult) {
	result.Statistics.TotalElements = len(result.Elements)

	for _, elem := range result.Elements {
		// Count by type
		result.Statistics.ElementsByType[elem.Type]++
		
		// Count by system
		result.Statistics.ElementsBySystem[elem.System]++
		
		// Confidence distribution
		confLevel := "low"
		if elem.Confidence.Overall > 0.85 {
			confLevel = "high"
		} else if elem.Confidence.Overall > 0.60 {
			confLevel = "medium"
		}
		result.Statistics.ConfidenceDistribution[confLevel]++
	}
}

// Helper methods

func (p *AIParser) inferSystem(elementType string) string {
	systemMap := map[string]string{
		"wall":       "structural",
		"column":     "structural",
		"door":       "architectural",
		"window":     "architectural",
		"room":       "architectural",
		"outlet":     "electrical",
		"switch":     "electrical",
		"light":      "electrical",
		"duct":       "hvac",
		"diffuser":   "hvac",
		"pipe":       "plumbing",
		"valve":      "plumbing",
		"sprinkler":  "fire",
	}
	
	if system, ok := systemMap[elementType]; ok {
		return system
	}
	return "unknown"
}

func (p *AIParser) isNear(b1, b2 BoundingBox, threshold float64) bool {
	centerX1 := b1.X + b1.Width/2
	centerY1 := b1.Y + b1.Height/2
	centerX2 := b2.X + b2.Width/2
	centerY2 := b2.Y + b2.Height/2
	
	distance := math.Sqrt(math.Pow(centerX2-centerX1, 2) + math.Pow(centerY2-centerY1, 2))
	return distance < threshold
}

func (p *AIParser) isAdjacent(b1, b2 BoundingBox) bool {
	// Check if boxes share an edge
	threshold := 5.0
	
	// Horizontal adjacency
	if math.Abs((b1.X+b1.Width)-b2.X) < threshold || math.Abs((b2.X+b2.Width)-b1.X) < threshold {
		// Check vertical overlap
		return !(b1.Y+b1.Height < b2.Y || b2.Y+b2.Height < b1.Y)
	}
	
	// Vertical adjacency
	if math.Abs((b1.Y+b1.Height)-b2.Y) < threshold || math.Abs((b2.Y+b2.Height)-b1.Y) < threshold {
		// Check horizontal overlap
		return !(b1.X+b1.Width < b2.X || b2.X+b2.Width < b1.X)
	}
	
	return false
}

func (p *AIParser) contains(b1, b2 BoundingBox) bool {
	return b1.X <= b2.X && 
		b1.Y <= b2.Y && 
		b1.X+b1.Width >= b2.X+b2.Width && 
		b1.Y+b1.Height >= b2.Y+b2.Height
}

func (p *AIParser) isAligned(b1, b2 BoundingBox) bool {
	threshold := 5.0
	
	// Check horizontal alignment
	if math.Abs(b1.Y-b2.Y) < threshold || 
	   math.Abs((b1.Y+b1.Height)-(b2.Y+b2.Height)) < threshold {
		return true
	}
	
	// Check vertical alignment
	if math.Abs(b1.X-b2.X) < threshold || 
	   math.Abs((b1.X+b1.Width)-(b2.X+b2.Width)) < threshold {
		return true
	}
	
	return false
}

func (p *AIParser) isConnected(elem1, elem2 DetectedElement) bool {
	// Special logic for doors and rooms
	if elem1.Type == "door" && elem2.Type == "room" {
		return p.isAdjacent(elem1.Bounds, elem2.Bounds)
	}
	if elem1.Type == "room" && elem2.Type == "door" {
		return p.isAdjacent(elem1.Bounds, elem2.Bounds)
	}
	
	// Windows and walls
	if elem1.Type == "window" && elem2.Type == "wall" {
		return p.contains(elem2.Bounds, elem1.Bounds)
	}
	
	return false
}

func (p *AIParser) getConnectionType(type1, type2 string) string {
	if (type1 == "door" && type2 == "room") || (type1 == "room" && type2 == "door") {
		return "entrance"
	}
	if (type1 == "window" && type2 == "wall") || (type1 == "wall" && type2 == "window") {
		return "opening"
	}
	return "generic"
}