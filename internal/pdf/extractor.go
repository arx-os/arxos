package pdf

import (
	"github.com/joelpate/arxos/internal/logger"
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