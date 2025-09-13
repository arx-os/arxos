package importer

import (
	"bufio"
	"fmt"
	"io"
	"regexp"
	"time"
	
	"github.com/joelpate/arxos/pkg/models"
)

// Parser is the generic parser interface
type Parser struct {
	config ParserConfig
}

// ParserConfig configures the parser behavior
type ParserConfig struct {
	// Grid settings
	GridSize      int
	MinRoomArea   float64
	MinWallLength float64
	
	// Pattern matching
	RoomNumberPattern *regexp.Regexp
	DoorPattern       *regexp.Regexp
	WindowPattern     *regexp.Regexp
}

// DefaultParserConfig returns default parser configuration
func DefaultParserConfig() ParserConfig {
	return ParserConfig{
		GridSize:      10,
		MinRoomArea:   10.0,
		MinWallLength: 3.0,
		RoomNumberPattern: regexp.MustCompile(`\b\d{3,4}\b`),
		DoorPattern:       regexp.MustCompile(`(?i)\bdoor\b`),
		WindowPattern:     regexp.MustCompile(`(?i)\bwindow\b`),
	}
}

// NewParser creates a new parser with the given configuration
func NewParser(config ParserConfig) *Parser {
	return &Parser{
		config: config,
	}
}

// Parse is the generic parse method that delegates to appropriate parser
func (p *Parser) Parse(reader io.Reader) (*models.FloorPlan, error) {
	// For now, default to PDF parsing
	// In a real implementation, this would detect the file type
	return p.ParsePDF(reader)
}

// ParsePDF parses a PDF file and extracts floor plan data
func (p *Parser) ParsePDF(reader io.Reader) (*models.FloorPlan, error) {
	// This is a simplified implementation
	// In a real system, this would use a PDF parsing library
	
	scanner := bufio.NewScanner(reader)
	plan := &models.FloorPlan{
		ID:        fmt.Sprintf("floor_%d", time.Now().Unix()),
		Name:      "Imported Floor Plan",
		Building:  "Unknown Building",
		Level:     1,
		Rooms:     []models.Room{},
		Equipment: []models.Equipment{},
	}
	
	lineNum := 0
	for scanner.Scan() {
		line := scanner.Text()
		lineNum++
		
		// Extract room numbers
		if matches := p.config.RoomNumberPattern.FindAllString(line, -1); len(matches) > 0 {
			for _, match := range matches {
				room := models.Room{
					ID:   fmt.Sprintf("room_%s", match),
					Name: fmt.Sprintf("Room %s", match),
					Bounds: models.Bounds{
						MinX: float64(lineNum * 10),
						MinY: 0,
						MaxX: float64(lineNum*10 + 100),
						MaxY: 100,
					},
				}
				plan.Rooms = append(plan.Rooms, room)
			}
		}
		
		// Detect doors
		if p.config.DoorPattern.MatchString(line) {
			// Add door as equipment
			equipment := models.Equipment{
				ID:   fmt.Sprintf("door_%d", lineNum),
				Name: "Door",
				Type: "door",
				Location: models.Point{
					X: float64(lineNum * 10),
					Y: 50,
				},
			}
			plan.Equipment = append(plan.Equipment, equipment)
		}
	}
	
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error scanning PDF: %w", err)
	}
	
	return plan, nil
}

// ParseIFC parses an IFC file and extracts building data
func (p *Parser) ParseIFC(reader io.Reader) (*models.FloorPlan, error) {
	// Delegate to IFCParser for IFC-specific parsing
	ifcParser := NewIFCParser()
	return ifcParser.Parse(reader, "imported.ifc")
}