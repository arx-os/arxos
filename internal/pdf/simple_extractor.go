package pdf

import (
	"fmt"
	"os"
	"strings"
	
	"github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"
	
	"github.com/joelpate/arxos/internal/logger"
	arxmodels "github.com/joelpate/arxos/pkg/models"
)

// SimpleTextExtractor uses pdfcpu's built-in text extraction
type SimpleTextExtractor struct {
	config *model.Configuration
}

// NewSimpleTextExtractor creates a new simple text extractor
func NewSimpleTextExtractor() *SimpleTextExtractor {
	return &SimpleTextExtractor{
		config: model.NewDefaultConfiguration(),
	}
}

// ExtractText extracts all text from a PDF using pdfcpu's API
func (se *SimpleTextExtractor) ExtractText(pdfPath string) (string, error) {
	logger.Info("Extracting text using pdfcpu API from: %s", pdfPath)
	
	// Open the input file
	f, err := os.Open(pdfPath)
	if err != nil {
		return "", fmt.Errorf("failed to open PDF: %w", err)
	}
	defer f.Close()
	
	// Create temp directory for extraction
	tempDir := "/tmp/arxos_pdf_extract"
	os.MkdirAll(tempDir, 0755)
	defer os.RemoveAll(tempDir) // Clean up after
	
	// Extract content to temp directory (nil means all pages)
	err = api.ExtractContent(f, tempDir, "content", nil, se.config)
	if err != nil {
		// ExtractContent might not work for all PDFs, try fallback
		logger.Warn("ExtractContent failed: %v, trying fallback", err)
		return se.extractTextFallback(pdfPath)
	}
	
	// Read all extracted content files
	var allText strings.Builder
	files, err := os.ReadDir(tempDir)
	if err == nil {
		for _, file := range files {
			if !file.IsDir() {
				content, err := os.ReadFile(fmt.Sprintf("%s/%s", tempDir, file.Name()))
				if err == nil {
					allText.Write(content)
					allText.WriteString("\n")
				}
			}
		}
	}
	
	text := allText.String()
	logger.Info("Extracted %d characters of text", len(text))
	
	return text, nil
}

// extractTextFallback uses a simpler approach for text extraction
func (se *SimpleTextExtractor) extractTextFallback(pdfPath string) (string, error) {
	// Read the PDF context
	ctx, err := api.ReadContextFile(pdfPath)
	if err != nil {
		return "", fmt.Errorf("failed to read PDF: %w", err)
	}
	
	// Validate the context
	if err := api.ValidateContext(ctx); err != nil {
		return "", fmt.Errorf("invalid PDF: %w", err)
	}
	
	// For now, return empty string to trigger manual template
	// A full implementation would parse content streams here
	logger.Info("PDF appears to be image-based or has no extractable text")
	return "", nil
}

// ExtractAndParse extracts text and parses it into a floor plan
func (se *SimpleTextExtractor) ExtractAndParse(pdfPath string) (*arxmodels.FloorPlan, error) {
	// Extract text
	text, err := se.ExtractText(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to extract text: %w", err)
	}
	
	// Create floor plan
	plan := &arxmodels.FloorPlan{
		Name:      strings.TrimSuffix(pdfPath, ".pdf"),
		Building:  "Imported Building",
		Level:     1,
		Rooms:     []arxmodels.Room{},
		Equipment: []arxmodels.Equipment{},
	}
	
	// Parse the text for equipment and rooms
	se.parseText(text, plan)
	
	return plan, nil
}

// parseText parses extracted text into floor plan objects
func (se *SimpleTextExtractor) parseText(text string, plan *arxmodels.FloorPlan) {
	lines := strings.Split(text, "\n")
	
	// Track what we find
	roomCount := 0
	equipCount := 0
	
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		
		logger.Debug("Parsing line: %s", line)
		
		// Look for common room indicators
		lowerLine := strings.ToLower(line)
		if strings.Contains(lowerLine, "room") || 
		   strings.Contains(lowerLine, "office") ||
		   strings.Contains(lowerLine, "classroom") ||
		   strings.Contains(lowerLine, "lab") {
			roomCount++
			room := arxmodels.Room{
				ID:   fmt.Sprintf("room_%d", roomCount),
				Name: line,
				Bounds: arxmodels.Bounds{
					MinX: float64(roomCount-1) * 30,
					MinY: 0,
					MaxX: float64(roomCount) * 30,
					MaxY: 20,
				},
			}
			plan.Rooms = append(plan.Rooms, room)
			logger.Info("Found room: %s", line)
		}
		
		// Look for equipment indicators
		if strings.Contains(lowerLine, "mdf") ||
		   strings.Contains(lowerLine, "idf") ||
		   strings.Contains(lowerLine, "switch") ||
		   strings.Contains(lowerLine, "panel") ||
		   strings.Contains(lowerLine, "access point") ||
		   strings.Contains(lowerLine, "ap-") {
			equipCount++
			equip := arxmodels.Equipment{
				ID:   fmt.Sprintf("equip_%d", equipCount),
				Name: line,
				Type: se.determineEquipmentType(lowerLine),
				Location: arxmodels.Point{
					X: float64(equipCount) * 15,
					Y: 10,
				},
				Status: arxmodels.StatusNormal,
			}
			plan.Equipment = append(plan.Equipment, equip)
			logger.Info("Found equipment: %s (type: %s)", line, equip.Type)
		}
	}
	
	logger.Info("Parsed %d rooms and %d equipment items", len(plan.Rooms), len(plan.Equipment))
}

// determineEquipmentType determines the equipment type from text
func (se *SimpleTextExtractor) determineEquipmentType(text string) string {
	if strings.Contains(text, "mdf") {
		return "mdf"
	}
	if strings.Contains(text, "idf") {
		return "idf"
	}
	if strings.Contains(text, "switch") {
		return "switch"
	}
	if strings.Contains(text, "panel") {
		return "panel"
	}
	if strings.Contains(text, "access point") || strings.Contains(text, "ap-") {
		return "access_point"
	}
	if strings.Contains(text, "outlet") {
		return "outlet"
	}
	return "equipment"
}