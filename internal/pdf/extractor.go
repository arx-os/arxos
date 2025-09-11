package pdf

import (
	"fmt"
	"path/filepath"
	"strings"
	"time"
	
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/internal/ocr"
	"github.com/joelpate/arxos/pkg/models"
)

// Extractor is the main PDF extraction interface
type Extractor struct{}

// NewExtractor creates a new PDF extractor
func NewExtractor() *Extractor {
	return &Extractor{}
}

// ExtractFloorPlan extracts floor plan data from ANY PDF file
func (e *Extractor) ExtractFloorPlan(pdfPath string) (*models.FloorPlan, error) {
	logger.Info("Extracting floor plan from: %s", pdfPath)
	
	// Use the universal parser for ALL PDFs
	return ParsePDF(pdfPath)
}

// ExtractWithOCR extracts floor plan data using OCR
func (e *Extractor) ExtractWithOCR(pdfPath string) (*models.FloorPlan, error) {
	logger.Info("Extracting floor plan with OCR from: %s", pdfPath)
	
	// Create OCR extractor
	ocrExtractor := ocr.NewExtractor()
	
	// Check if OCR is available
	if !ocrExtractor.IsOCRAvailable() {
		return nil, fmt.Errorf("OCR tools not available (tesseract not found)")
	}
	
	// Extract text using OCR
	text, err := ocrExtractor.ExtractTextFromPDF(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("OCR extraction failed: %w", err)
	}
	
	logger.Info("OCR extracted %d characters", len(text))
	
	// Create floor plan from OCR text
	plan := &models.FloorPlan{
		Name:      strings.TrimSuffix(filepath.Base(pdfPath), filepath.Ext(pdfPath)),
		Building:  "OCR Imported Building",
		Level:     1,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Rooms:     []models.Room{},
		Equipment: []models.Equipment{},
	}
	
	// Extract equipment information
	equipmentInfo := ocrExtractor.ExtractEquipmentInfo(text)
	
	// Create default room if we have equipment
	if len(equipmentInfo) > 0 {
		plan.Rooms = append(plan.Rooms, models.Room{
			ID:   "ocr_room",
			Name: "OCR Extracted Room",
			Bounds: models.Bounds{
				MinX: 0,
				MinY: 0, 
				MaxX: 100,
				MaxY: 100,
			},
		})
		
		// Add equipment
		for i, info := range equipmentInfo {
			equip := models.Equipment{
				ID:       fmt.Sprintf("ocr_%s_%d", info.Type, i+1),
				Name:     info.Name,
				Type:     info.Type,
				RoomID:   "ocr_room",
				Location: models.Point{X: float64(10 + i*5), Y: 50},
				Status:   models.StatusUnknown,
				Notes:    "Extracted via OCR",
			}
			plan.Equipment = append(plan.Equipment, equip)
		}
	}
	
	logger.Info("Created floor plan with %d rooms and %d equipment items from OCR", 
		len(plan.Rooms), len(plan.Equipment))
	
	return plan, nil
}