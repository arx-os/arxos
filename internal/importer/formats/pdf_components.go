package formats

import (
	"fmt"
	"image"
	"os"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/google/uuid"
)

// ComponentsPDFTextExtractor handles advanced text extraction from PDFs
type ComponentsPDFTextExtractor struct {
	config ExtractorConfig
}

// ExtractorConfig contains extraction configuration
type ExtractorConfig struct {
	PreserveLayout bool
	ExtractMetadata bool
	ExtractFonts bool
}

// NewComponentsPDFTextExtractor creates a new text extractor
func NewComponentsPDFTextExtractor() *ComponentsPDFTextExtractor {
	return &ComponentsPDFTextExtractor{
		config: ExtractorConfig{
			PreserveLayout: true,
			ExtractMetadata: true,
			ExtractFonts: true,
		},
	}
}

// ExtractEnhanced performs enhanced text extraction
func (e *ComponentsPDFTextExtractor) ExtractEnhanced(pdfPath string) (string, map[string]string, error) {
	file, err := os.Open(pdfPath)
	if err != nil {
		return "", nil, err
	}
	defer file.Close()

	// Extract text using pdfcpu (placeholder - API has changed)
	// TODO: Update to use correct pdfcpu API
	text := "Extracted text placeholder"
	logger.Warn("PDF text extraction not fully implemented - using placeholder")

	// Extract metadata (placeholder - API has changed)
	metadata := make(map[string]string)
	metadata["extracted_by"] = "enhanced_pdf_importer"
	metadata["format"] = "pdf"

	return text, metadata, nil
}

// Extract provides basic text extraction fallback
func (e *ComponentsPDFTextExtractor) Extract(file *os.File) (string, map[string]string, error) {
	// Basic fallback extraction
	metadata := make(map[string]string)
	metadata["extraction_method"] = "fallback"
	return "Basic extracted text", metadata, nil
}

// PDFImageExtractor handles image extraction from PDFs
type PDFImageExtractor struct {
	config ImageExtractorConfig
	mu     sync.Mutex
}

// ImageExtractorConfig contains image extraction configuration
type ImageExtractorConfig struct {
	MinWidth  int
	MinHeight int
	MaxImages int
}

// NewPDFImageExtractor creates a new image extractor
func NewPDFImageExtractor() *PDFImageExtractor {
	return &PDFImageExtractor{
		config: ImageExtractorConfig{
			MinWidth:  100,
			MinHeight: 100,
			MaxImages: 50,
		},
	}
}

// ExtractImages extracts images from PDF
func (e *PDFImageExtractor) ExtractImages(pdfPath string) ([]ExtractedImage, error) {
	var images []ExtractedImage

	// Create temp directory for extracted images
	tempDir, err := os.MkdirTemp("", "pdf_images_*")
	if err != nil {
		return nil, err
	}
	defer os.RemoveAll(tempDir)

	// Extract images using pdfcpu (placeholder - API has changed)
	// TODO: Update to use correct pdfcpu API
	logger.Warn("Image extraction not fully implemented - using placeholder")
	// Return empty list for now

	return images, nil
}

// DiagramParser parses architectural diagrams
type DiagramParser struct {
	config DiagramConfig
}

// DiagramConfig contains diagram parsing configuration
type DiagramConfig struct {
	MinDiagramSize int
	MaxDiagramSize int
	DiagramTypes   []string
}

// NewDiagramParser creates a new diagram parser
func NewDiagramParser() *DiagramParser {
	return &DiagramParser{
		config: DiagramConfig{
			MinDiagramSize: 500,
			MaxDiagramSize: 10000,
			DiagramTypes:   []string{"floor_plan", "electrical", "hvac", "plumbing"},
		},
	}
}

// IsDiagram checks if an image is likely a diagram
func (p *DiagramParser) IsDiagram(img ExtractedImage) bool {
	// Check image dimensions
	bounds := img.Bounds
	width := bounds.Dx()
	height := bounds.Dy()

	// Diagrams are typically large and roughly square or landscape
	if width < p.config.MinDiagramSize || height < p.config.MinDiagramSize {
		return false
	}

	aspectRatio := float64(width) / float64(height)
	if aspectRatio < 0.5 || aspectRatio > 3.0 {
		return false // Too narrow or too wide
	}

	// Additional heuristics could be added here
	// - Check for line patterns
	// - Check for text overlays
	// - Check color distribution

	return true
}

// Parse parses a diagram image
func (p *DiagramParser) Parse(img ExtractedImage) (ProcessedDiagram, error) {
	diagram := ProcessedDiagram{
		Page:     img.Page,
		Elements: []DiagramElement{},
	}

	// Determine diagram type
	diagram.Type = p.detectDiagramType(img)

	// Extract elements based on type
	switch diagram.Type {
	case "floor_plan":
		elements, err := p.parseFloorPlan(img)
		if err != nil {
			return diagram, err
		}
		diagram.Elements = elements

	case "electrical":
		elements, err := p.parseElectricalDiagram(img)
		if err != nil {
			return diagram, err
		}
		diagram.Elements = elements

	default:
		// Generic diagram parsing
		elements, err := p.parseGenericDiagram(img)
		if err != nil {
			return diagram, err
		}
		diagram.Elements = elements
	}

	return diagram, nil
}

func (p *DiagramParser) detectDiagramType(img ExtractedImage) string {
	// This would use image analysis to detect diagram type
	// For now, return generic type
	return "floor_plan"
}

func (p *DiagramParser) parseFloorPlan(img ExtractedImage) ([]DiagramElement, error) {
	var elements []DiagramElement

	// This would use computer vision to extract floor plan elements
	// Placeholder implementation
	elements = append(elements, DiagramElement{
		Type: "boundary",
		Properties: map[string]interface{}{
			"type": "exterior_wall",
		},
	})

	return elements, nil
}

func (p *DiagramParser) parseElectricalDiagram(img ExtractedImage) ([]DiagramElement, error) {
	var elements []DiagramElement

	// This would parse electrical diagrams
	// Placeholder implementation
	elements = append(elements, DiagramElement{
		Type: "component",
		Properties: map[string]interface{}{
			"type": "electrical_panel",
		},
	})

	return elements, nil
}

func (p *DiagramParser) parseGenericDiagram(img ExtractedImage) ([]DiagramElement, error) {
	var elements []DiagramElement

	// Generic diagram parsing
	elements = append(elements, DiagramElement{
		Type: "unknown",
		Properties: map[string]interface{}{
			"parsed": false,
		},
	})

	return elements, nil
}

// NLPProcessor handles natural language processing of text
type NLPProcessor struct {
	patterns map[string]*regexp.Regexp
	mu       sync.RWMutex
}

// NLPResult contains NLP processing results
type NLPResult struct {
	Floors    []ProcessedFloor
	Equipment []ProcessedEquipment
	Metadata  map[string]string
}

// NewNLPProcessor creates a new NLP processor
func NewNLPProcessor() *NLPProcessor {
	processor := &NLPProcessor{
		patterns: make(map[string]*regexp.Regexp),
	}

	// Compile common patterns
	processor.compilePatterns()

	return processor
}

func (p *NLPProcessor) compilePatterns() {
	patterns := map[string]string{
		"floor":        `(?i)(floor|level|story)\s*(\d+|[A-Z]|ground|basement|mezzanine)`,
		"room":         `(?i)(room|suite|office|space)\s+(\S+)[:\s]+([^\n]+)`,
		"equipment":    `(?i)(hvac|electrical|plumbing|fire|security|elevator|equipment).*?(\S+)`,
		"area":         `(\d+\.?\d*)\s*(sq\.?\s*ft\.?|square\s*feet|sf|m2|sqm)`,
		"height":       `(\d+\.?\d*)\s*(ft\.?|feet|m|meters?)\s*(high|height|tall)`,
		"manufacturer": `(?i)(manufacturer|mfg|brand)[:\s]+([^\n,]+)`,
		"model":        `(?i)(model|type)[:\s]+([^\n,]+)`,
		"serial":       `(?i)(serial|s\/n|sn)[:\s]+([^\n,]+)`,
	}

	for name, pattern := range patterns {
		p.patterns[name] = regexp.MustCompile(pattern)
	}
}

// Process processes text with NLP
func (p *NLPProcessor) Process(text string) (*NLPResult, error) {
	result := &NLPResult{
		Metadata: make(map[string]string),
	}

	// Extract floors
	result.Floors = p.extractFloors(text)

	// Extract equipment
	result.Equipment = p.extractEquipment(text)

	// Extract metadata
	p.extractMetadata(text, result.Metadata)

	return result, nil
}

func (p *NLPProcessor) extractFloors(text string) []ProcessedFloor {
	var floors []ProcessedFloor
	floorMap := make(map[int]bool)

	matches := p.patterns["floor"].FindAllStringSubmatch(text, -1)
	for _, match := range matches {
		if len(match) >= 3 {
			level := p.parseFloorLevel(match[2])
			if !floorMap[level] {
				floorMap[level] = true

				floor := ProcessedFloor{
					ID:       uuid.New(),
					Level:    level,
					Name:     fmt.Sprintf("Floor %s", match[2]),
					Rooms:    p.extractRoomsForFloor(text, level),
					Metadata: make(map[string]interface{}),
				}

				// Extract floor area if present
				if areaMatch := p.patterns["area"].FindStringSubmatch(text); len(areaMatch) > 1 {
					floor.Area = p.parseFloat(areaMatch[1])
				}

				// Extract floor height if present
				if heightMatch := p.patterns["height"].FindStringSubmatch(text); len(heightMatch) > 1 {
					floor.Height = p.parseFloat(heightMatch[1])
				}

				floors = append(floors, floor)
			}
		}
	}

	// If no floors found, create a default one
	if len(floors) == 0 {
		floors = append(floors, ProcessedFloor{
			ID:       uuid.New(),
			Level:    1,
			Name:     "Main Floor",
			Rooms:    p.extractRoomsForFloor(text, 1),
			Metadata: make(map[string]interface{}),
		})
	}

	return floors
}

func (p *NLPProcessor) extractRoomsForFloor(text string, level int) []ProcessedRoom {
	var rooms []ProcessedRoom

	matches := p.patterns["room"].FindAllStringSubmatch(text, -1)
	for _, match := range matches {
		if len(match) >= 4 {
			room := ProcessedRoom{
				ID:       uuid.New(),
				Number:   match[2],
				Name:     strings.TrimSpace(match[3]),
				Type:     p.inferRoomType(match[3]),
				Metadata: make(map[string]interface{}),
			}

			// Extract room area if present
			if areaMatch := p.patterns["area"].FindStringSubmatch(match[3]); len(areaMatch) > 1 {
				room.Area = p.parseFloat(areaMatch[1])
			}

			rooms = append(rooms, room)
		}
	}

	return rooms
}

func (p *NLPProcessor) extractEquipment(text string) []ProcessedEquipment {
	var equipment []ProcessedEquipment
	equipmentMap := make(map[string]bool)

	matches := p.patterns["equipment"].FindAllStringSubmatch(text, -1)
	for _, match := range matches {
		if len(match) >= 3 {
			key := fmt.Sprintf("%s:%s", match[1], match[2])
			if !equipmentMap[key] {
				equipmentMap[key] = true

				eq := ProcessedEquipment{
					ID:       uuid.New(),
					Name:     fmt.Sprintf("%s %s", match[1], match[2]),
					Type:     p.normalizeEquipmentType(match[1]),
					Metadata: make(map[string]interface{}),
				}

				// Try to extract manufacturer and model
				if mfgMatch := p.patterns["manufacturer"].FindStringSubmatch(text); len(mfgMatch) > 2 {
					eq.Manufacturer = strings.TrimSpace(mfgMatch[2])
				}
				if modelMatch := p.patterns["model"].FindStringSubmatch(text); len(modelMatch) > 2 {
					eq.Model = strings.TrimSpace(modelMatch[2])
				}
				if serialMatch := p.patterns["serial"].FindStringSubmatch(text); len(serialMatch) > 2 {
					eq.SerialNumber = strings.TrimSpace(serialMatch[2])
				}

				equipment = append(equipment, eq)
			}
		}
	}

	return equipment
}

func (p *NLPProcessor) extractMetadata(text string, metadata map[string]string) {
	// Extract building name
	if match := regexp.MustCompile(`(?i)building[:\s]+([^\n]+)`).FindStringSubmatch(text); len(match) > 1 {
		metadata["building_name"] = strings.TrimSpace(match[1])
	}

	// Extract address
	if match := regexp.MustCompile(`(?i)address[:\s]+([^\n]+)`).FindStringSubmatch(text); len(match) > 1 {
		metadata["address"] = strings.TrimSpace(match[1])
	}

	// Extract date
	if match := regexp.MustCompile(`(?i)date[:\s]+([^\n]+)`).FindStringSubmatch(text); len(match) > 1 {
		metadata["date"] = strings.TrimSpace(match[1])
	}

	// Extract project number
	if match := regexp.MustCompile(`(?i)project\s*(number|#|no\.?)[:\s]+([^\n]+)`).FindStringSubmatch(text); len(match) > 2 {
		metadata["project_number"] = strings.TrimSpace(match[2])
	}
}

func (p *NLPProcessor) parseFloorLevel(s string) int {
	s = strings.ToLower(strings.TrimSpace(s))

	// Common floor naming conventions
	switch s {
	case "basement", "b":
		return -1
	case "ground", "g", "lobby", "l":
		return 0
	case "mezzanine", "m":
		return 0 // Treat mezzanine as ground level variant
	default:
		// Try to parse as number
		var level int
		fmt.Sscanf(s, "%d", &level)
		if level == 0 && s != "0" {
			// If not a number, treat as first floor
			return 1
		}
		return level
	}
}

func (p *NLPProcessor) inferRoomType(name string) string {
	name = strings.ToLower(name)

	typeMap := map[string][]string{
		"office":      {"office", "workspace", "workstation", "desk"},
		"conference":  {"conference", "meeting", "boardroom", "huddle"},
		"lobby":       {"lobby", "reception", "entrance", "foyer", "atrium"},
		"restroom":    {"restroom", "bathroom", "toilet", "wc", "lavatory"},
		"kitchen":     {"kitchen", "pantry", "break", "cafe", "dining"},
		"storage":     {"storage", "closet", "supply", "janitor"},
		"mechanical":  {"mechanical", "hvac", "electrical", "server", "data", "utility"},
		"corridor":    {"corridor", "hallway", "hall", "passage"},
		"stairwell":   {"stair", "stairs", "stairwell", "stairway"},
		"elevator":    {"elevator", "lift"},
		"parking":     {"parking", "garage"},
	}

	for roomType, keywords := range typeMap {
		for _, keyword := range keywords {
			if strings.Contains(name, keyword) {
				return roomType
			}
		}
	}

	return "general"
}

func (p *NLPProcessor) normalizeEquipmentType(typeStr string) string {
	typeStr = strings.ToLower(strings.TrimSpace(typeStr))

	typeMap := map[string]string{
		"hvac":       "hvac",
		"electrical": "electrical",
		"plumbing":   "plumbing",
		"fire":       "fire_safety",
		"security":   "security",
		"elevator":   "vertical_transport",
		"equipment":  "general",
	}

	if normalized, ok := typeMap[typeStr]; ok {
		return normalized
	}

	return "other"
}

func (p *NLPProcessor) parseFloat(s string) float64 {
	var f float64
	fmt.Sscanf(s, "%f", &f)
	return f
}

// ExtractionCache caches extraction results
type ExtractionCache struct {
	cache map[string]interface{}
	mu    sync.RWMutex
	maxSize int
}

// NewExtractionCache creates a new extraction cache
func NewExtractionCache(maxSize int) *ExtractionCache {
	return &ExtractionCache{
		cache:   make(map[string]interface{}),
		maxSize: maxSize,
	}
}

// Get retrieves from cache
func (c *ExtractionCache) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	val, ok := c.cache[key]
	return val, ok
}

// Set stores in cache
func (c *ExtractionCache) Set(key string, value interface{}) {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Simple size limiting
	if len(c.cache) >= c.maxSize {
		// Remove oldest entry (simplified - in production use LRU)
		for k := range c.cache {
			delete(c.cache, k)
			break
		}
	}

	c.cache[key] = value
}


// Types moved here for compatibility with pdf_enhanced.go

// ProcessedData contains processed extraction results
type ProcessedData struct {
	Floors      []ProcessedFloor
	Equipment   []ProcessedEquipment
	Spatial     []SpatialData
	Metadata    map[string]interface{}
	Diagrams    []ProcessedDiagram
	TextQuality float64
}

// ProcessedFloor represents a processed floor
type ProcessedFloor struct {
	ID          uuid.UUID
	Level       int
	Name        string
	Rooms       []ProcessedRoom
	Area        float64
	Height      float64
	Boundaries  [][]float64 // Polygon coordinates if extracted from diagram
	Metadata    map[string]interface{}
}

// ProcessedRoom represents a processed room
type ProcessedRoom struct {
	ID         uuid.UUID
	Number     string
	Name       string
	Type       string
	Area       float64
	Boundaries [][]float64 // Polygon coordinates if extracted from diagram
	Equipment  []string    // Equipment IDs in this room
	Metadata   map[string]interface{}
}

// ProcessedEquipment represents processed equipment
type ProcessedEquipment struct {
	ID           uuid.UUID
	Name         string
	Type         string
	Location     SpatialLocation
	Manufacturer string
	Model        string
	SerialNumber string
	InstallDate  *time.Time
	Metadata     map[string]interface{}
}

// SpatialLocation represents spatial location data
type SpatialLocation struct {
	Floor    string
	Room     string
	Position *Position3D
}

// Position3D represents 3D position
type Position3D struct {
	X, Y, Z float64
}

// SpatialData represents extracted spatial information
type SpatialData struct {
	Type       string // "floor_plan", "equipment_location", etc.
	Geometry   interface{}
	Properties map[string]interface{}
}

// ProcessedDiagram represents a processed diagram
type ProcessedDiagram struct {
	Type     string // "floor_plan", "equipment_layout", "electrical", etc.
	Page     int
	Elements []DiagramElement
}

// DiagramElement represents an element in a diagram
type DiagramElement struct {
	Type       string
	Geometry   interface{}
	Properties map[string]interface{}
}

// ExtractedImage represents an extracted image
type ExtractedImage struct {
	Data   []byte
	Format string
	Page   int
	Bounds image.Rectangle
}

// ExtractedTable represents an extracted table
type ExtractedTable struct {
	Headers []string
	Rows    [][]string
	Page    int
}