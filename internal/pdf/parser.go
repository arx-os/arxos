package pdf

import (
	"context"
	"fmt"
	"io"
	"strings"

	"bytes"
	"github.com/unidoc/unipdf/v3/extractor"
	"github.com/unidoc/unipdf/v3/model"
)

// Parser handles PDF parsing and extraction
type Parser struct {
	config *ParserConfig
}

// ParserConfig configures the PDF parser
type ParserConfig struct {
	MaxFileSize    int64  // Maximum file size in bytes
	ExtractText    bool   // Extract text content
	ExtractImages  bool   // Extract embedded images
	ExtractVectors bool   // Extract vector graphics (for floor plans)
}

// DefaultParserConfig returns default parser configuration
func DefaultParserConfig() *ParserConfig {
	return &ParserConfig{
		MaxFileSize:    100 * 1024 * 1024, // 100MB
		ExtractText:    true,
		ExtractImages:  true,
		ExtractVectors: true,
	}
}

// NewParser creates a new PDF parser
func NewParser(config *ParserConfig) *Parser {
	if config == nil {
		config = DefaultParserConfig()
	}
	return &Parser{config: config}
}

// ParseResult contains the extracted PDF data
type ParseResult struct {
	PageCount    int
	Text         map[int]string   // Text by page number
	Images       []ImageData      // Extracted images
	VectorPaths  []VectorPath     // Vector graphics paths
	Metadata     map[string]string
	FloorPlanData *FloorPlanData   // Detected floor plan data
}

// ImageData represents an extracted image
type ImageData struct {
	PageNum int
	Index   int
	Width   int
	Height  int
	Data    []byte
	Format  string // png, jpeg, etc
}

// VectorPath represents vector graphics data
type VectorPath struct {
	PageNum int
	Type    string  // line, rect, curve, etc
	Points  []Point
	Style   PathStyle
}

// Point represents a 2D point
type Point struct {
	X, Y float64
}

// PathStyle contains styling information
type PathStyle struct {
	StrokeWidth float64
	StrokeColor string
	FillColor   string
}

// FloorPlanData represents extracted floor plan information
type FloorPlanData struct {
	Bounds      Rectangle
	Rooms       []Room
	Walls       []Wall
	Doors       []Door
	Equipment   []EquipmentItem
	Scale       float64 // pixels per meter
	Orientation float64 // rotation in degrees
}

// Rectangle represents a bounding box
type Rectangle struct {
	MinX, MinY, MaxX, MaxY float64
}

// Room represents a detected room
type Room struct {
	ID      string
	Name    string
	Bounds  Rectangle
	Type    string // office, conference, bathroom, etc
}

// Wall represents a wall segment
type Wall struct {
	Start, End Point
	Thickness  float64
}

// Door represents a door
type Door struct {
	Position Point
	Width    float64
	Angle    float64
}

// EquipmentItem represents detected equipment
type EquipmentItem struct {
	ID       string
	Type     string // outlet, switch, panel, etc
	Position Point
	Label    string
}

// Parse parses a PDF file and extracts relevant data
func (p *Parser) Parse(ctx context.Context, reader io.Reader) (*ParseResult, error) {
	// Read PDF data
	data, err := io.ReadAll(reader)
	if err != nil {
		return nil, fmt.Errorf("failed to read PDF: %w", err)
	}

	if int64(len(data)) > p.config.MaxFileSize {
		return nil, fmt.Errorf("PDF size exceeds maximum of %d bytes", p.config.MaxFileSize)
	}

	result := &ParseResult{
		Text:     make(map[int]string),
		Metadata: make(map[string]string),
	}

	// Parse with unipdf for text and structure
	if err := p.parseWithUnipdf(ctx, data, result); err != nil {
		return nil, fmt.Errorf("unipdf parse failed: %w", err)
	}

	// Extract vector graphics with pdfcpu
	if p.config.ExtractVectors {
		if err := p.extractVectorGraphics(ctx, data, result); err != nil {
			// Non-fatal: log but continue
			fmt.Printf("Warning: vector extraction failed: %v\n", err)
		}
	}

	// Analyze extracted data for floor plan patterns
	if p.config.ExtractVectors {
		result.FloorPlanData = p.detectFloorPlan(result)
	}

	return result, nil
}

// parseWithUnipdf uses unipdf to extract text and images
func (p *Parser) parseWithUnipdf(ctx context.Context, data []byte, result *ParseResult) error {
	pdfReader, err := model.NewPdfReader(strings.NewReader(string(data)))
	if err != nil {
		return fmt.Errorf("failed to create PDF reader: %w", err)
	}

	numPages, err := pdfReader.GetNumPages()
	if err != nil {
		return fmt.Errorf("failed to get page count: %w", err)
	}
	result.PageCount = numPages

	// Extract text from each page
	if p.config.ExtractText {
		for pageNum := 1; pageNum <= numPages; pageNum++ {
			select {
			case <-ctx.Done():
				return ctx.Err()
			default:
			}

			page, err := pdfReader.GetPage(pageNum)
			if err != nil {
				continue // Skip problematic pages
			}

			ex, err := extractor.New(page)
			if err != nil {
				continue
			}

			text, err := ex.ExtractText()
			if err != nil {
				continue
			}

			result.Text[pageNum] = text
		}
	}

	// Extract metadata
	pdfInfo, err := pdfReader.GetPdfInfo()
	if err == nil && pdfInfo != nil {
		if pdfInfo.Title != nil {
			result.Metadata["title"] = pdfInfo.Title.String()
		}
		if pdfInfo.Author != nil {
			result.Metadata["author"] = pdfInfo.Author.String()
		}
		if pdfInfo.Subject != nil {
			result.Metadata["subject"] = pdfInfo.Subject.String()
		}
	}

	return nil
}

// extractVectorGraphics extracts vector paths (placeholder for now)
func (p *Parser) extractVectorGraphics(ctx context.Context, data []byte, result *ParseResult) error {
	// Basic validation using unipdf
	pdfReader, err := model.NewPdfReader(bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("PDF validation failed: %w", err)
	}

	// Check if we can read the pages
	_, err = pdfReader.GetNumPages()
	if err != nil {
		return fmt.Errorf("cannot read PDF pages: %w", err)
	}

	// TODO: Implement actual vector extraction
	// This would involve parsing the PDF content streams
	// and extracting path operations using the unipdf library

	return nil
}

// detectFloorPlan analyzes extracted data to identify floor plan elements
func (p *Parser) detectFloorPlan(result *ParseResult) *FloorPlanData {
	floorPlan := &FloorPlanData{
		Scale: 1.0, // Default scale
	}

	// Analyze text for room labels
	for pageNum, text := range result.Text {
		// Look for common room identifiers
		lines := strings.Split(text, "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if p.looksLikeRoomLabel(line) {
				room := Room{
					Name: line,
					Type: p.classifyRoomType(line),
				}
				floorPlan.Rooms = append(floorPlan.Rooms, room)
			} else if p.looksLikeEquipmentLabel(line) {
				equipment := EquipmentItem{
					Label: line,
					Type:  p.classifyEquipmentType(line),
				}
				floorPlan.Equipment = append(floorPlan.Equipment, equipment)
			}
		}
		
		// For now, we only process the first page with text
		if pageNum == 1 && len(floorPlan.Rooms) > 0 {
			break
		}
	}

	// Analyze vector paths for walls and doors
	for _, path := range result.VectorPaths {
		if p.looksLikeWall(path) {
			wall := Wall{
				Start:     path.Points[0],
				End:       path.Points[len(path.Points)-1],
				Thickness: path.Style.StrokeWidth,
			}
			floorPlan.Walls = append(floorPlan.Walls, wall)
		}
	}

	return floorPlan
}

// Helper methods for pattern detection
func (p *Parser) looksLikeRoomLabel(text string) bool {
	text = strings.ToLower(text)
	roomKeywords := []string{
		"room", "office", "conference", "bathroom", "restroom",
		"kitchen", "lobby", "hall", "corridor", "closet", "storage",
	}
	for _, keyword := range roomKeywords {
		if strings.Contains(text, keyword) {
			return true
		}
	}
	// Check for patterns like "Room 101", "Suite A", etc
	return len(text) < 50 && (strings.Contains(text, " ") || len(text) < 20)
}

func (p *Parser) classifyRoomType(text string) string {
	text = strings.ToLower(text)
	switch {
	case strings.Contains(text, "conference"):
		return "conference"
	case strings.Contains(text, "office"):
		return "office"
	case strings.Contains(text, "bathroom") || strings.Contains(text, "restroom"):
		return "bathroom"
	case strings.Contains(text, "kitchen"):
		return "kitchen"
	case strings.Contains(text, "storage") || strings.Contains(text, "closet"):
		return "storage"
	case strings.Contains(text, "lobby"):
		return "lobby"
	default:
		return "generic"
	}
}

func (p *Parser) looksLikeEquipmentLabel(text string) bool {
	text = strings.ToLower(text)
	equipmentKeywords := []string{
		"switch", "outlet", "panel", "breaker", "hvac",
		"thermostat", "sensor", "camera", "access", "fire",
		"emergency", "exit", "alarm",
	}
	for _, keyword := range equipmentKeywords {
		if strings.Contains(text, keyword) {
			return true
		}
	}
	// Check for patterns like "SW-01", "P-100", etc
	if len(text) < 20 && strings.Contains(text, "-") {
		return true
	}
	return false
}

func (p *Parser) classifyEquipmentType(text string) string {
	text = strings.ToLower(text)
	switch {
	case strings.Contains(text, "switch"):
		return "switch"
	case strings.Contains(text, "outlet"):
		return "outlet"
	case strings.Contains(text, "panel") || strings.Contains(text, "breaker"):
		return "panel"
	case strings.Contains(text, "hvac") || strings.Contains(text, "thermostat"):
		return "hvac"
	case strings.Contains(text, "camera"):
		return "camera"
	case strings.Contains(text, "sensor"):
		return "sensor"
	case strings.Contains(text, "fire") || strings.Contains(text, "alarm"):
		return "fire_safety"
	default:
		return "unknown"
	}
}

func (p *Parser) looksLikeWall(path VectorPath) bool {
	// Walls are typically straight lines with consistent width
	if path.Type != "line" || len(path.Points) != 2 {
		return false
	}
	// Check if stroke width suggests a wall
	return path.Style.StrokeWidth > 1.0
}