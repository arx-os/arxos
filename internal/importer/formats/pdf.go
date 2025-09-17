package formats

import (
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/importer"
	"github.com/arx-os/arxos/internal/models/building"
)

// PDFImporter handles PDF file imports
type PDFImporter struct {
	extractor   TextExtractor
	parser      FloorPlanParser
	confidence  ConfidenceCalculator
}

// NewPDFImporter creates a new PDF importer
func NewPDFImporter() *PDFImporter {
	return &PDFImporter{
		extractor:  &PDFTextExtractor{},
		parser:     &RegexFloorPlanParser{},
		confidence: &PDFConfidenceCalculator{},
	}
}

// GetFormat returns the format name
func (p *PDFImporter) GetFormat() string {
	return "pdf"
}

// GetCapabilities returns importer capabilities
func (p *PDFImporter) GetCapabilities() importer.ImportCapabilities {
	return importer.ImportCapabilities{
		SupportsSpatial:    false, // PDF typically doesn't have precise spatial data
		SupportsHierarchy:  true,  // Can extract floor/room hierarchy
		SupportsMetadata:   true,
		SupportsConfidence: true,
		SupportsStreaming:  false,
		MaxFileSize:        100 * 1024 * 1024, // 100MB limit
	}
}

// CanImport checks if this importer can handle the input
func (p *PDFImporter) CanImport(input io.Reader) bool {
	// Check PDF magic bytes
	magic := make([]byte, 5)
	n, err := input.Read(magic)
	if err != nil || n < 5 {
		return false
	}

	// PDF files start with %PDF-
	return string(magic) == "%PDF-"
}

// ImportToModel converts PDF to building model
func (p *PDFImporter) ImportToModel(ctx context.Context, input io.Reader, opts importer.ImportOptions) (*building.BuildingModel, error) {
	logger.Info("Starting PDF import")

	// Extract text from PDF
	text, metadata, err := p.extractor.Extract(input)
	if err != nil {
		return nil, fmt.Errorf("failed to extract text from PDF: %w", err)
	}

	if strings.TrimSpace(text) == "" {
		return nil, fmt.Errorf("no text content found in PDF - may be scanned image")
	}

	// Parse floor plan data from text
	planData := p.parser.Parse(text)

	// Create building model
	model := &building.BuildingModel{
		ID:          opts.BuildingID,
		Name:        opts.BuildingName,
		Source:      building.DataSourcePDF,
		ImportedAt:  time.Now(),
		UpdatedAt:   time.Now(),
		Properties:  make(map[string]interface{}),
		Floors:      []building.Floor{},
	}

	// Add metadata
	for k, v := range metadata {
		model.Properties[k] = v
	}

	// Build floor structure
	model.Floors = p.buildFloors(planData)

	// Calculate confidence
	model.Confidence = p.confidence.Calculate(planData, metadata)

	// Log summary
	equipmentCount := len(model.GetAllEquipment())
	logger.Info("PDF import complete: %d floors, %d rooms, %d equipment items",
		len(model.Floors), p.countRooms(model), equipmentCount)

	return model, nil
}

// TextExtractor interface for extracting text from PDFs
type TextExtractor interface {
	Extract(input io.Reader) (text string, metadata map[string]string, err error)
}

// FloorPlanParser interface for parsing floor plan data from text
type FloorPlanParser interface {
	Parse(text string) FloorPlanData
}

// ConfidenceCalculator interface for calculating confidence levels
type ConfidenceCalculator interface {
	Calculate(data FloorPlanData, metadata map[string]string) building.ConfidenceLevel
}

// FloorPlanData represents parsed floor plan information
type FloorPlanData struct {
	Floors    []ParsedFloor
	Equipment []ParsedEquipment
	Metadata  map[string]string
}

// ParsedFloor represents a parsed floor
type ParsedFloor struct {
	Number int
	Name   string
	Rooms  []ParsedRoom
}

// ParsedRoom represents a parsed room
type ParsedRoom struct {
	Number     string
	Name       string
	Type       string
	Area       float64
	Equipment  []string
}

// ParsedEquipment represents parsed equipment
type ParsedEquipment struct {
	ID           string
	Name         string
	Type         string
	Room         string
	Floor        string
	Manufacturer string
	Model        string
}

// PDFTextExtractor extracts text from PDFs
type PDFTextExtractor struct{}

// Extract extracts text and metadata from PDF
func (e *PDFTextExtractor) Extract(input io.Reader) (string, map[string]string, error) {
	// Save input to temporary file for processing
	tmpFile, err := os.CreateTemp("", "pdf_import_*.pdf")
	if err != nil {
		return "", nil, fmt.Errorf("failed to create temp file: %w", err)
	}
	defer os.Remove(tmpFile.Name())

	// Copy input to temp file
	if _, err := io.Copy(tmpFile, input); err != nil {
		return "", nil, fmt.Errorf("failed to save PDF: %w", err)
	}
	tmpFile.Close()

	// Try different extraction methods
	text, extractMethod, err := e.extractWithFallbacks(tmpFile.Name())
	if err != nil {
		return "", nil, err
	}

	metadata := map[string]string{
		"extraction_method": extractMethod,
		"extracted_at":      time.Now().Format(time.RFC3339),
	}

	return text, metadata, nil
}

// extractWithFallbacks tries multiple extraction methods
func (e *PDFTextExtractor) extractWithFallbacks(pdfPath string) (string, string, error) {
	// Method 1: Try pdftotext (most reliable)
	if text, err := e.tryPdfToText(pdfPath); err == nil && text != "" {
		return text, "pdftotext", nil
	}

	// Method 2: Try basic extraction (fallback)
	if text, err := e.tryBasicExtraction(pdfPath); err == nil && text != "" {
		return text, "basic", nil
	}

	return "", "none", fmt.Errorf("all text extraction methods failed")
}

// tryPdfToText uses pdftotext command
func (e *PDFTextExtractor) tryPdfToText(pdfPath string) (string, error) {
	cmd := exec.Command("pdftotext", "-layout", pdfPath, "-")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("pdftotext failed: %w", err)
	}
	return string(output), nil
}

// tryBasicExtraction uses basic text extraction
func (e *PDFTextExtractor) tryBasicExtraction(pdfPath string) (string, error) {
	// This would use a Go PDF library for basic extraction
	// For now, return error to force pdftotext
	return "", fmt.Errorf("basic extraction not implemented")
}

// RegexFloorPlanParser parses floor plan data using regex patterns
type RegexFloorPlanParser struct{}

// Parse extracts floor plan data from text
func (p *RegexFloorPlanParser) Parse(text string) FloorPlanData {
	data := FloorPlanData{
		Floors:    p.parseFloors(text),
		Equipment: p.parseEquipment(text),
		Metadata:  make(map[string]string),
	}

	// Extract metadata
	if match := regexp.MustCompile(`(?i)building[:\s]+([^\n]+)`).FindStringSubmatch(text); len(match) > 1 {
		data.Metadata["building_name"] = strings.TrimSpace(match[1])
	}
	if match := regexp.MustCompile(`(?i)address[:\s]+([^\n]+)`).FindStringSubmatch(text); len(match) > 1 {
		data.Metadata["address"] = strings.TrimSpace(match[1])
	}

	return data
}

// parseFloors extracts floor information
func (p *RegexFloorPlanParser) parseFloors(text string) []ParsedFloor {
	var floors []ParsedFloor

	// Look for floor patterns
	floorPattern := regexp.MustCompile(`(?i)(floor|level|story)\s*(\d+|[A-Z]|ground|basement)`)
	matches := floorPattern.FindAllStringSubmatch(text, -1)

	floorNumbers := make(map[int]bool)
	for _, match := range matches {
		floorNum := p.parseFloorNumber(match[2])
		if !floorNumbers[floorNum] {
			floorNumbers[floorNum] = true
			floors = append(floors, ParsedFloor{
				Number: floorNum,
				Name:   fmt.Sprintf("Floor %d", floorNum),
				Rooms:  p.parseRooms(text, floorNum),
			})
		}
	}

	// If no floors found, create a default one
	if len(floors) == 0 {
		floors = append(floors, ParsedFloor{
			Number: 1,
			Name:   "Main Floor",
			Rooms:  p.parseRooms(text, 1),
		})
	}

	return floors
}

// parseFloorNumber converts floor string to number
func (p *RegexFloorPlanParser) parseFloorNumber(s string) int {
	s = strings.ToLower(s)
	switch s {
	case "ground", "g":
		return 0
	case "basement", "b":
		return -1
	default:
		if n, err := strconv.Atoi(s); err == nil {
			return n
		}
		// Convert letters to numbers (A=1, B=2, etc.)
		if len(s) == 1 && s[0] >= 'a' && s[0] <= 'z' {
			return int(s[0] - 'a' + 1)
		}
		return 1
	}
}

// parseRooms extracts room information
func (p *RegexFloorPlanParser) parseRooms(text string, floorNum int) []ParsedRoom {
	var rooms []ParsedRoom

	// Common room patterns
	patterns := []string{
		`(?i)room\s+(\S+)[:\s]+([^\n]+)`,
		`(?i)(\d{3,4})\s+[-–]\s+([^\n]+)`,
		`(?i)suite\s+(\S+)[:\s]+([^\n]+)`,
	}

	for _, pattern := range patterns {
		re := regexp.MustCompile(pattern)
		matches := re.FindAllStringSubmatch(text, -1)

		for _, match := range matches {
			if len(match) >= 3 {
				room := ParsedRoom{
					Number: match[1],
					Name:   strings.TrimSpace(match[2]),
					Type:   p.inferRoomType(match[2]),
				}

				// Parse area if present
				if areaMatch := regexp.MustCompile(`(\d+)\s*(sq|sf|sqft|m2)`).FindStringSubmatch(match[2]); len(areaMatch) > 1 {
					if area, err := strconv.ParseFloat(areaMatch[1], 64); err == nil {
						room.Area = area
					}
				}

				rooms = append(rooms, room)
			}
		}
	}

	return rooms
}

// parseEquipment extracts equipment information
func (p *RegexFloorPlanParser) parseEquipment(text string) []ParsedEquipment {
	var equipment []ParsedEquipment

	// Equipment patterns
	patterns := []string{
		`(?i)(hvac|air handler|ahu|vav|fcu)[-\s]*(\S+)`,
		`(?i)(panel|breaker|electrical)[-\s]*(\S+)`,
		`(?i)(pump|valve|boiler|chiller)[-\s]*(\S+)`,
		`(?i)(sensor|thermostat|detector)[-\s]*(\S+)`,
	}

	for _, pattern := range patterns {
		re := regexp.MustCompile(pattern)
		matches := re.FindAllStringSubmatch(text, -1)

		for _, match := range matches {
			if len(match) >= 2 {
				eq := ParsedEquipment{
					ID:   match[2],
					Type: strings.ToLower(match[1]),
					Name: fmt.Sprintf("%s %s", match[1], match[2]),
				}
				equipment = append(equipment, eq)
			}
		}
	}

	return equipment
}

// inferRoomType infers room type from name
func (p *RegexFloorPlanParser) inferRoomType(name string) string {
	name = strings.ToLower(name)

	typeMap := map[string][]string{
		"office":     {"office", "workspace", "workstation"},
		"conference": {"conference", "meeting", "boardroom"},
		"lobby":      {"lobby", "reception", "entrance", "foyer"},
		"restroom":   {"restroom", "bathroom", "toilet", "wc"},
		"kitchen":    {"kitchen", "pantry", "break room"},
		"storage":    {"storage", "closet", "utility"},
		"mechanical": {"mechanical", "hvac", "electrical", "server"},
		"corridor":   {"corridor", "hallway", "hall"},
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

// PDFConfidenceCalculator calculates confidence for PDF imports
type PDFConfidenceCalculator struct{}

// Calculate determines confidence level based on extracted data
func (c *PDFConfidenceCalculator) Calculate(data FloorPlanData, metadata map[string]string) building.ConfidenceLevel {
	score := 0
	maxScore := 5

	// Check data completeness
	if len(data.Floors) > 0 {
		score++
	}
	if len(data.Equipment) > 0 {
		score++
	}
	if len(metadata) > 2 {
		score++
	}

	// Check room details
	hasRoomNumbers := false
	hasRoomTypes := false
	for _, floor := range data.Floors {
		for _, room := range floor.Rooms {
			if room.Number != "" {
				hasRoomNumbers = true
			}
			if room.Type != "general" {
				hasRoomTypes = true
			}
		}
	}
	if hasRoomNumbers {
		score++
	}
	if hasRoomTypes {
		score++
	}

	// Calculate confidence based on score
	percentage := float64(score) / float64(maxScore)
	switch {
	case percentage >= 0.8:
		return building.ConfidenceMedium // PDF can't be High
	case percentage >= 0.6:
		return building.ConfidenceLow
	case percentage >= 0.4:
		return building.ConfidenceEstimated
	default:
		return building.ConfidenceEstimated
	}
}

// buildFloors converts parsed data to building floors
func (p *PDFImporter) buildFloors(data FloorPlanData) []building.Floor {
	var floors []building.Floor

	for _, parsedFloor := range data.Floors {
		floor := building.Floor{
			ID:         fmt.Sprintf("floor_%d", parsedFloor.Number),
			Number:     parsedFloor.Number,
			Name:       parsedFloor.Name,
			Rooms:      []building.Room{},
			Equipment:  []building.Equipment{},
			Confidence: building.ConfidenceEstimated,
			Properties: make(map[string]interface{}),
		}

		// Add rooms
		for _, parsedRoom := range parsedFloor.Rooms {
			room := building.Room{
				ID:         fmt.Sprintf("room_%s", parsedRoom.Number),
				Number:     parsedRoom.Number,
				Name:       parsedRoom.Name,
				Type:       parsedRoom.Type,
				Area:       parsedRoom.Area,
				FloorID:    floor.ID,
				Confidence: building.ConfidenceEstimated,
				Properties: make(map[string]interface{}),
			}
			floor.Rooms = append(floor.Rooms, room)
		}

		// Add equipment for this floor
		for _, parsedEq := range data.Equipment {
			// Try to match equipment to rooms
			var roomID string
			for _, room := range floor.Rooms {
				if strings.Contains(parsedEq.Name, room.Number) {
					roomID = room.ID
					break
				}
			}

			equipment := building.Equipment{
				ID:         parsedEq.ID,
				Name:       parsedEq.Name,
				Type:       parsedEq.Type,
				Status:     "operational",
				FloorID:    floor.ID,
				RoomID:     roomID,
				Confidence: building.ConfidenceEstimated,
				Properties: make(map[string]interface{}),
			}

			if parsedEq.Manufacturer != "" {
				equipment.Manufacturer = parsedEq.Manufacturer
			}
			if parsedEq.Model != "" {
				equipment.Model = parsedEq.Model
			}

			floor.Equipment = append(floor.Equipment, equipment)
		}

		floors = append(floors, floor)
	}

	return floors
}

// countRooms counts total rooms in the model
func (p *PDFImporter) countRooms(model *building.BuildingModel) int {
	count := 0
	for _, floor := range model.Floors {
		count += len(floor.Rooms)
	}
	return count
}