package pdf

import (
	"io"
	
	"github.com/joelpate/arxos/pkg/models"
)

// Parser defines the interface for PDF parsing
type Parser interface {
	// Parse extracts floor plan data from a PDF
	Parse(reader io.Reader) (*models.FloorPlan, error)
	
	// Export writes a floor plan with markups back to PDF
	Export(plan *models.FloorPlan, writer io.Writer) error
}

// TextElement represents text found in a PDF
type TextElement struct {
	Text     string
	Position models.Point
	FontSize float64
}

// NewParser creates a new universal PDF parser
func NewParser() Parser {
	return NewUniversalParser()
}

// ParsePDF is the single entry point for parsing ANY PDF
func ParsePDF(pdfPath string) (*models.FloorPlan, error) {
	parser := NewUniversalParser()
	return parser.ParseAnyPDF(pdfPath)
}