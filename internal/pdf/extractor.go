package pdf

import (
	"context"
	"fmt"
	"os"
	
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// Extractor handles PDF extraction operations
type Extractor struct {
	parser *Parser
}

// NewExtractor creates a new PDF extractor
func NewExtractor() *Extractor {
	return &Extractor{
		parser: NewParser(DefaultParserConfig()),
	}
}

// ExtractFloorPlan extracts a floor plan from a PDF file
func (e *Extractor) ExtractFloorPlan(pdfPath string) (*models.FloorPlan, error) {
	logger.Debug("Extracting floor plan from: %s", pdfPath)
	
	// Open PDF file
	file, err := os.Open(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open PDF: %w", err)
	}
	defer file.Close()
	
	// Parse PDF
	ctx := context.Background()
	result, err := e.parser.Parse(ctx, file)
	if err != nil {
		return nil, fmt.Errorf("failed to parse PDF: %w", err)
	}
	
	// Convert to floor plan
	plan := &models.FloorPlan{
		Name:     "Extracted Floor Plan",
		Building: "Building",
		Level:    1,
	}
	
	// Extract floor plan data if available
	if result.FloorPlanData != nil {
		// Convert from parsed floor plan data
		for _, room := range result.FloorPlanData.Rooms {
			plan.Rooms = append(plan.Rooms, models.Room{
				ID:   room.ID,
				Name: room.Name,
				Bounds: models.Bounds{
					MinX: room.Bounds.MinX,
					MinY: room.Bounds.MinY,
					MaxX: room.Bounds.MaxX,
					MaxY: room.Bounds.MaxY,
				},
			})
		}
		
		for _, equip := range result.FloorPlanData.Equipment {
			plan.Equipment = append(plan.Equipment, models.Equipment{
				ID:     equip.ID,
				Name:   equip.Label,
				Type:   equip.Type,
				Location: models.Point{
					X: equip.Position.X,
					Y: equip.Position.Y,
				},
			})
		}
	}
	
	return plan, nil
}

// ExtractWithOCR extracts a floor plan using OCR
func (e *Extractor) ExtractWithOCR(pdfPath string) (*models.FloorPlan, error) {
	logger.Debug("Extracting floor plan with OCR from: %s", pdfPath)
	
	// For now, return an error as OCR is not yet implemented
	// This will be implemented when we add OCR support
	return nil, fmt.Errorf("OCR extraction not yet implemented")
}

// Exporter handles PDF export operations
type Exporter struct {
	// Configuration can be added here
}

// NewExporter creates a new PDF exporter
func NewExporter() *Exporter {
	return &Exporter{}
}

// Export exports a floor plan to PDF
func (e *Exporter) Export(plan *models.FloorPlan, outputPath string) error {
	logger.Debug("Exporting floor plan to: %s", outputPath)
	
	// For now, return an error as export is not yet implemented
	// This will be implemented when we add PDF generation support
	return fmt.Errorf("PDF export not yet implemented")
}

// ExportFloorPlan exports a floor plan to PDF (alias for Export)
func (e *Exporter) ExportFloorPlan(plan *models.FloorPlan, outputPath string) error {
	return e.Export(plan, outputPath)
}