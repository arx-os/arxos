package converter

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/pdfcpu/pdfcpu/pkg/api"
)

// PDFProcessor handles PDF file processing
type PDFProcessor struct {
	config        PDFConfig
	tesseractPath string
}

// PDFConfig contains configuration for PDF processing
type PDFConfig struct {
	EnableOCR          bool
	ExtractTables      bool
	ExtractImages      bool
	PageLimit          int
	TextConfidenceMin  float64
}

// NewPDFProcessor creates a new PDF processor
func NewPDFProcessor(config PDFConfig) *PDFProcessor {
	// Check if tesseract is available
	tesseractPath, err := exec.LookPath("tesseract")
	if err != nil {
		logger.Warn("Tesseract not found, OCR will be disabled")
		config.EnableOCR = false
	}

	return &PDFProcessor{
		config:        config,
		tesseractPath: tesseractPath,
	}
}

// ProcessFile processes a PDF file and extracts equipment data
func (p *PDFProcessor) ProcessFile(pdfPath string) (*Building, error) {
	logger.Info("Processing PDF file: %s", pdfPath)

	// Validate PDF
	if err := api.ValidateFile(pdfPath, nil); err != nil {
		return nil, fmt.Errorf("invalid PDF file: %w", err)
	}

	// Extract text from all pages
	text, err := p.ExtractText(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to extract text: %w", err)
	}

	// Parse equipment from text
	equipment := p.parseEquipmentFromText(strings.Join(text, "\n"))

	// Extract tables if enabled
	if p.config.ExtractTables {
		tables, err := p.ExtractTables(pdfPath)
		if err != nil {
			logger.Warn("Failed to extract tables: %v", err)
		} else {
			// Parse equipment from tables
			tableEquipment := p.parseEquipmentFromTables(tables)
			equipment = append(equipment, tableEquipment...)
		}
	}

	// Create building model
	building := &Building{
		Name:   strings.TrimSuffix(filepath.Base(pdfPath), ".pdf"),
		Floors: []Floor{},
	}

	// Group equipment by floor (if floor info is available)
	floorMap := make(map[int]*Floor)
	for _, eq := range equipment {
		floorNum := p.extractFloorNumber(eq)

		floor, exists := floorMap[floorNum]
		if !exists {
			floor = &Floor{
				Level: floorNum,
				Name:  fmt.Sprintf("Floor %d", floorNum),
				Rooms: []Room{},
			}
			floorMap[floorNum] = floor
			building.Floors = append(building.Floors, *floor)
		}

		// Add equipment to a default room
		if len(floor.Rooms) == 0 {
			floor.Rooms = append(floor.Rooms, Room{
				ID:   fmt.Sprintf("ROOM_%d_1", floorNum),
				Name: "Equipment Room",
				Equipment: []Equipment{},
			})
		}
		floor.Rooms[0].Equipment = append(floor.Rooms[0].Equipment, *eq)
	}

	logger.Info("Extracted %d equipment items from PDF", len(equipment))
	return building, nil
}

// ExtractText extracts text content from PDF
func (p *PDFProcessor) ExtractText(pdfPath string) ([]string, error) {
	// Create temp directory for extraction
	tempDir, err := ioutil.TempDir("", "pdf_extract_*")
	if err != nil {
		return nil, fmt.Errorf("failed to create temp dir: %w", err)
	}
	defer os.RemoveAll(tempDir)

	// Extract content to temp directory
	if err := api.ExtractContentFile(pdfPath, tempDir, nil, nil); err != nil {
		return nil, fmt.Errorf("failed to extract content: %w", err)
	}

	var allText []string

	// Read extracted text files
	files, err := ioutil.ReadDir(tempDir)
	if err != nil {
		return nil, fmt.Errorf("failed to read temp dir: %w", err)
	}

	for _, file := range files {
		if strings.HasSuffix(file.Name(), ".txt") {
			content, err := ioutil.ReadFile(filepath.Join(tempDir, file.Name()))
			if err != nil {
				logger.Warn("Failed to read extracted text: %v", err)
				continue
			}
			allText = append(allText, string(content))
		}
	}

	// If no text found and OCR is enabled, try OCR
	if len(allText) == 0 && p.config.EnableOCR {
		logger.Info("No text found, attempting OCR")
		ocrText, err := p.performOCR(pdfPath)
		if err != nil {
			logger.Warn("OCR failed: %v", err)
		} else {
			allText = ocrText
		}
	}

	return allText, nil
}

// ExtractTables extracts table data from PDF
func (p *PDFProcessor) ExtractTables(pdfPath string) ([]Table, error) {
	var tables []Table

	// For now, use simple text extraction and pattern matching
	// A more sophisticated approach would use table detection libraries
	text, err := p.ExtractText(pdfPath)
	if err != nil {
		return nil, err
	}

	for _, pageText := range text {
		// Look for table-like patterns
		pageTables := p.detectTables(pageText)
		tables = append(tables, pageTables...)
	}

	return tables, nil
}

// parseEquipmentFromText parses equipment from text content
func (p *PDFProcessor) parseEquipmentFromText(text string) []*Equipment {
	var equipment []*Equipment

	// Common equipment patterns
	patterns := []struct {
		regex   *regexp.Regexp
		extractor func([]string) *Equipment
	}{
		{
			// Pattern: "EQUIP-001: HVAC Unit - Model XYZ"
			regex: regexp.MustCompile(`(?i)([\w-]+):\s*([^-]+)\s*-\s*Model\s+(\S+)`),
			extractor: func(matches []string) *Equipment {
				return &Equipment{
					ID:     matches[1],
					Name:   strings.TrimSpace(matches[2]),
					Model:  matches[3],
					Type:   p.inferEquipmentType(matches[2]),
					Status: "OPERATIONAL",
				}
			},
		},
		{
			// Pattern: "Equipment ID: XXX, Type: YYY, Location: ZZZ"
			regex: regexp.MustCompile(`(?i)Equipment\s+ID:\s*(\S+).*?Type:\s*([^,]+).*?Location:\s*([^,\n]+)`),
			extractor: func(matches []string) *Equipment {
				return &Equipment{
					ID:     matches[1],
					Type:   strings.TrimSpace(matches[2]),
					Status: "OPERATIONAL",
				}
			},
		},
		{
			// Pattern for equipment schedules
			regex: regexp.MustCompile(`(?i)(\w+[-/]\d+)\s+(\w+(?:\s+\w+)*)\s+(\w+[-/]\w+)\s+(\d+)\s+(\w+)`),
			extractor: func(matches []string) *Equipment {
				return &Equipment{
					ID:     matches[1],
					Name:   matches[2],
					Model:  matches[3],
					Type:   p.inferEquipmentType(matches[2]),
					Status: "OPERATIONAL",
				}
			},
		},
	}

	// Apply patterns
	for _, pattern := range patterns {
		matches := pattern.regex.FindAllStringSubmatch(text, -1)
		for _, match := range matches {
			if len(match) > 1 {
				eq := pattern.extractor(match)
				if eq != nil && eq.ID != "" {
					equipment = append(equipment, eq)
				}
			}
		}
	}

	// Deduplicate equipment by ID
	seen := make(map[string]bool)
	var unique []*Equipment
	for _, eq := range equipment {
		if !seen[eq.ID] {
			seen[eq.ID] = true
			unique = append(unique, eq)
		}
	}

	return unique
}

// parseEquipmentFromTables parses equipment from tables
func (p *PDFProcessor) parseEquipmentFromTables(tables []Table) []*Equipment {
	var equipment []*Equipment

	for _, table := range tables {
		// Look for equipment schedule tables
		if p.isEquipmentTable(table) {
			tableEquipment := p.extractEquipmentFromTable(table)
			equipment = append(equipment, tableEquipment...)
		}
	}

	return equipment
}

// detectTables detects table structures in text
func (p *PDFProcessor) detectTables(text string) []Table {
	var tables []Table

	lines := strings.Split(text, "\n")
	var currentTable *Table

	for _, line := range lines {
		// Simple heuristic: lines with multiple tab/space separations might be table rows
		fields := regexp.MustCompile(`\s{2,}|\t+`).Split(line, -1)

		if len(fields) >= 3 {
			// Potential table row
			if currentTable == nil {
				currentTable = &Table{
					Headers: fields,
					Rows:    [][]string{},
				}
			} else {
				currentTable.Rows = append(currentTable.Rows, fields)
			}
		} else if currentTable != nil && len(currentTable.Rows) > 0 {
			// End of table
			tables = append(tables, *currentTable)
			currentTable = nil
		}
	}

	// Add last table if exists
	if currentTable != nil && len(currentTable.Rows) > 0 {
		tables = append(tables, *currentTable)
	}

	return tables
}

// isEquipmentTable checks if a table contains equipment data
func (p *PDFProcessor) isEquipmentTable(table Table) bool {
	// Check headers for equipment-related keywords
	keywords := []string{"equipment", "tag", "id", "type", "model", "serial"}

	headerText := strings.ToLower(strings.Join(table.Headers, " "))
	for _, keyword := range keywords {
		if strings.Contains(headerText, keyword) {
			return true
		}
	}

	return false
}

// extractEquipmentFromTable extracts equipment from a table
func (p *PDFProcessor) extractEquipmentFromTable(table Table) []*Equipment {
	var equipment []*Equipment

	// Map headers to indices
	headerMap := make(map[string]int)
	for i, header := range table.Headers {
		headerMap[strings.ToLower(header)] = i
	}

	// Extract equipment from rows
	for _, row := range table.Rows {
		eq := &Equipment{
			Status: "OPERATIONAL",
		}

		// Map common fields
		if idx, exists := headerMap["id"]; exists && idx < len(row) {
			eq.ID = row[idx]
		} else if idx, exists := headerMap["tag"]; exists && idx < len(row) {
			eq.ID = row[idx]
		}

		if idx, exists := headerMap["name"]; exists && idx < len(row) {
			eq.Name = row[idx]
		} else if idx, exists := headerMap["description"]; exists && idx < len(row) {
			eq.Name = row[idx]
		}

		if idx, exists := headerMap["type"]; exists && idx < len(row) {
			eq.Type = row[idx]
		}

		if idx, exists := headerMap["model"]; exists && idx < len(row) {
			eq.Model = row[idx]
		}

		if idx, exists := headerMap["serial"]; exists && idx < len(row) {
			eq.Serial = row[idx]
		}

		if eq.ID != "" {
			equipment = append(equipment, eq)
		}
	}

	return equipment
}

// performOCR performs OCR on PDF pages
func (p *PDFProcessor) performOCR(pdfPath string) ([]string, error) {
	if p.tesseractPath == "" {
		return nil, fmt.Errorf("tesseract not available")
	}

	// Convert PDF to images first (requires additional tools)
	// For now, return error
	return nil, fmt.Errorf("OCR not yet fully implemented")
}

// inferEquipmentType infers equipment type from name/description
func (p *PDFProcessor) inferEquipmentType(text string) string {
	text = strings.ToLower(text)

	typeMap := map[string][]string{
		"HVAC":       {"hvac", "ac", "air condition", "air handler", "heating", "cooling", "ventilation", "ahu", "vav", "fcu"},
		"ELECTRICAL": {"electrical", "panel", "breaker", "transformer", "ups", "generator"},
		"PLUMBING":   {"pump", "valve", "pipe", "water", "drain", "sewer", "tank"},
		"FIRE":       {"fire", "smoke", "sprinkler", "alarm", "extinguisher"},
		"LIGHTING":   {"light", "lamp", "luminaire", "fixture"},
		"SECURITY":   {"camera", "access", "door", "lock", "sensor", "motion"},
		"NETWORK":    {"network", "switch", "router", "wifi", "access point", "server"},
	}

	for equipType, keywords := range typeMap {
		for _, keyword := range keywords {
			if strings.Contains(text, keyword) {
				return equipType
			}
		}
	}

	return "GENERAL"
}

// extractFloorNumber extracts floor number from equipment data
func (p *PDFProcessor) extractFloorNumber(eq *Equipment) int {
	// Look for floor patterns in ID, name
	patterns := []string{eq.ID, eq.Name}

	floorRegex := regexp.MustCompile(`(?i)(?:floor|level|flr|fl)[\s-]*(\d+)`)

	for _, text := range patterns {
		matches := floorRegex.FindStringSubmatch(text)
		if len(matches) > 1 {
			if floor, err := strconv.Atoi(matches[1]); err == nil {
				return floor
			}
		}
	}

	// Check for floor in path format (e.g., "3/A/301")
	if strings.Contains(eq.ID, "/") {
		parts := strings.Split(eq.ID, "/")
		if len(parts) > 0 {
			if floor, err := strconv.Atoi(parts[0]); err == nil {
				return floor
			}
		}
	}

	// Default to floor 1
	return 1
}

// Table represents a table structure
type Table struct {
	Headers []string
	Rows    [][]string
}

// ExtractMetadata extracts document metadata
func (p *PDFProcessor) ExtractMetadata(pdfPath string) (map[string]string, error) {
	metadata := make(map[string]string)

	// For now, we'll just return basic info
	// A full implementation would parse the PDF metadata
	info, err := os.Stat(pdfPath)
	if err != nil {
		return nil, err
	}

	metadata["filename"] = info.Name()
	metadata["size"] = fmt.Sprintf("%d", info.Size())
	metadata["modified"] = info.ModTime().String()

	return metadata, nil
}

// ProcessPDFFile is the main entry point for PDF processing
func ProcessPDFFile(filename string) error {
	config := PDFConfig{
		EnableOCR:         false, // Disabled by default
		ExtractTables:     true,
		ExtractImages:     false,
		PageLimit:         100,
		TextConfidenceMin: 0.8,
	}

	processor := NewPDFProcessor(config)

	// Process the file
	building, err := processor.ProcessFile(filename)
	if err != nil {
		return fmt.Errorf("failed to process PDF: %w", err)
	}

	// Log results
	logger.Info("Processed PDF: %s", filename)
	logger.Info("  Building: %s", building.Name)
	logger.Info("  Floors: %d", len(building.Floors))

	totalEquipment := 0
	for i := range building.Floors {
		for j := range building.Floors[i].Rooms {
			totalEquipment += len(building.Floors[i].Rooms[j].Equipment)
		}
	}
	logger.Info("  Total Equipment: %d", totalEquipment)

	return nil
}

// ExtractPDFContent extracts raw content from PDF for analysis
func ExtractPDFContent(r io.ReadSeeker) (string, error) {
	// Create temp file to write PDF
	tempFile, err := ioutil.TempFile("", "pdf_*.pdf")
	if err != nil {
		return "", fmt.Errorf("failed to create temp file: %w", err)
	}
	defer os.Remove(tempFile.Name())

	// Copy PDF to temp file
	if _, err := io.Copy(tempFile, r); err != nil {
		return "", fmt.Errorf("failed to write PDF: %w", err)
	}
	tempFile.Close()

	// Create temp directory for extraction
	tempDir, err := ioutil.TempDir("", "pdf_extract_*")
	if err != nil {
		return "", fmt.Errorf("failed to create temp dir: %w", err)
	}
	defer os.RemoveAll(tempDir)

	// Extract content
	if err := api.ExtractContentFile(tempFile.Name(), tempDir, nil, nil); err != nil {
		return "", fmt.Errorf("failed to extract content: %w", err)
	}

	var allText strings.Builder

	// Read extracted text files
	files, err := ioutil.ReadDir(tempDir)
	if err != nil {
		return "", fmt.Errorf("failed to read temp dir: %w", err)
	}

	for _, file := range files {
		if strings.HasSuffix(file.Name(), ".txt") {
			content, err := ioutil.ReadFile(filepath.Join(tempDir, file.Name()))
			if err != nil {
				continue
			}
			allText.WriteString(string(content))
			allText.WriteString("\n")
		}
	}

	return allText.String(), nil
}