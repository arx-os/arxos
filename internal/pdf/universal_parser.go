package pdf

import (
	"fmt"
	"io"
	"math"
	"path/filepath"
	"regexp"
	"strings"
	"time"
	
	"github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"
	
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// UniversalParser handles ANY PDF floor plan
type UniversalParser struct {
	config *model.Configuration
}

// NewUniversalParser creates a parser that works with any PDF
func NewUniversalParser() *UniversalParser {
	return &UniversalParser{
		config: model.NewDefaultConfiguration(),
	}
}

// ParseAnyPDF attempts multiple strategies to extract floor plan data
func (p *UniversalParser) ParseAnyPDF(pdfPath string) (*models.FloorPlan, error) {
	logger.Info("Starting universal PDF parse: %s", pdfPath)
	
	plan := &models.FloorPlan{
		Name:      strings.TrimSuffix(filepath.Base(pdfPath), filepath.Ext(pdfPath)),
		Building:  "Imported Building",
		Level:     1,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Rooms:     []models.Room{},
		Equipment: []models.Equipment{},
	}
	
	// Strategy 1: Try text extraction
	textData, err := p.extractAllText(pdfPath)
	if err == nil && len(textData) > 0 {
		logger.Info("Found %d text elements in PDF", len(textData))
		p.parseTextElements(textData, plan)
	}
	
	// Strategy 2: Try content stream parsing (for embedded text)
	if len(plan.Equipment) == 0 {
		contentData, err := p.extractContentStream(pdfPath)
		if err == nil {
			logger.Info("Parsing content stream data")
			p.parseContentStream(contentData, plan)
		}
	}
	
	// Strategy 3: Look for form fields (interactive PDFs)
	if len(plan.Equipment) == 0 {
		formData, err := p.extractFormFields(pdfPath)
		if err == nil && len(formData) > 0 {
			logger.Info("Found %d form fields", len(formData))
			p.parseFormFields(formData, plan)
		}
	}
	
	// Strategy 4: If all else fails, create structure for manual input
	if len(plan.Equipment) == 0 && len(plan.Rooms) == 0 {
		logger.Warn("Could not extract data from PDF automatically")
		p.createManualEntryTemplate(plan)
	}
	
	// Auto-generate spatial layout
	p.generateSpatialLayout(plan)
	
	return plan, nil
}

// extractAllText attempts to extract all text from the PDF
func (p *UniversalParser) extractAllText(pdfPath string) ([]TextData, error) {
	var textData []TextData
	
	// Try to extract text using pdfcpu
	// This would need proper implementation with pdfcpu's text extraction
	// For now, we'll simulate the extraction
	
	// Read the PDF file
	ctx, err := api.ReadContextFile(pdfPath)
	if err != nil {
		return nil, err
	}
	
	// Process each page
	for pageNum := 1; pageNum <= ctx.PageCount; pageNum++ {
		// Extract text from page (simplified - real implementation would parse content streams)
		pageText := p.extractPageText(ctx, pageNum)
		textData = append(textData, pageText...)
	}
	
	return textData, nil
}

// TextData represents extracted text with position
type TextData struct {
	Text     string
	X        float64
	Y        float64
	FontSize float64
	Page     int
}

// extractPageText extracts text from a specific page
func (p *UniversalParser) extractPageText(ctx *model.Context, pageNum int) []TextData {
	var textData []TextData
	
	// This is a simplified version - real implementation would parse PDF operators
	// For now, return empty to trigger fallback strategies
	
	return textData
}

// parseTextElements converts text elements to floor plan objects
func (p *UniversalParser) parseTextElements(textData []TextData, plan *models.FloorPlan) {
	// Patterns for common equipment and room labels
	equipmentPatterns := []struct {
		pattern *regexp.Regexp
		eqType  string
	}{
		{regexp.MustCompile(`(?i)\b(MDF|Main.?Dist.*Frame)\s*[\-_]?\s*(\w+)`), "mdf"},
		{regexp.MustCompile(`(?i)\b(IDF|Inter.*Dist.*Frame)\s*[\-_]?\s*(\w+)`), "idf"},
		{regexp.MustCompile(`(?i)\b(AP|Access.?Point|WAP)\s*[\-_]?\s*(\w+)`), "access_point"},
		{regexp.MustCompile(`(?i)\b(SW|Switch)\s*[\-_]?\s*(\w+)`), "switch"},
		{regexp.MustCompile(`(?i)\b(Panel|Breaker)\s*[\-_]?\s*(\w+)`), "panel"},
		{regexp.MustCompile(`(?i)\b(Outlet|Receptacle)\s*[\-_]?\s*(\w+)`), "outlet"},
		{regexp.MustCompile(`(?i)\b(Server|Rack)\s*[\-_]?\s*(\w+)`), "server"},
	}
	
	roomPatterns := []struct {
		pattern *regexp.Regexp
		rmType  string
	}{
		{regexp.MustCompile(`(?i)\b(Room|Rm|Suite|Ste)\s*(\d+\w?)`), "room"},
		{regexp.MustCompile(`(?i)\b(Office|Ofc)\s*(\d+\w?)`), "office"},
		{regexp.MustCompile(`(?i)\b(Classroom|Class)\s*(\d+\w?)`), "classroom"},
		{regexp.MustCompile(`(?i)\b(Lab|Laboratory)\s*(\d+\w?)`), "lab"},
		{regexp.MustCompile(`(?i)\b(Hallway|Hall|Corridor)\s*(\w+)?`), "hallway"},
	}
	
	// Process each text element
	for _, text := range textData {
		// Check for equipment
		for _, eq := range equipmentPatterns {
			if matches := eq.pattern.FindStringSubmatch(text.Text); matches != nil {
				equipment := models.Equipment{
					ID:       p.generateID(text.Text),
					Name:     strings.TrimSpace(text.Text),
					Type:     eq.eqType,
					Location: models.Point{X: text.X, Y: text.Y},
					Status:   models.StatusNormal,
				}
				plan.Equipment = append(plan.Equipment, equipment)
				logger.Debug("Found equipment: %s at (%.1f, %.1f)", equipment.Name, text.X, text.Y)
			}
		}
		
		// Check for rooms
		for _, rm := range roomPatterns {
			if matches := rm.pattern.FindStringSubmatch(text.Text); matches != nil {
				room := models.Room{
					ID:   p.generateID(text.Text),
					Name: strings.TrimSpace(text.Text),
					Bounds: models.Bounds{
						MinX: text.X - 10,
						MinY: text.Y - 10,
						MaxX: text.X + 10,
						MaxY: text.Y + 10,
					},
				}
				plan.Rooms = append(plan.Rooms, room)
				logger.Debug("Found room: %s at (%.1f, %.1f)", room.Name, text.X, text.Y)
			}
		}
	}
}

// extractContentStream attempts to parse raw PDF content streams
func (p *UniversalParser) extractContentStream(pdfPath string) (string, error) {
	// This would parse the raw PDF operators
	// For now, return empty to trigger next strategy
	return "", fmt.Errorf("content stream parsing not yet implemented")
}

// parseContentStream extracts data from content stream
func (p *UniversalParser) parseContentStream(content string, plan *models.FloorPlan) {
	// Parse PostScript-like commands
	// Look for text operators (Tj, TJ, etc.)
	// This is complex and would need a full PostScript parser
}

// extractFormFields extracts interactive form fields from PDF
func (p *UniversalParser) extractFormFields(pdfPath string) (map[string]string, error) {
	// Extract form fields if the PDF is interactive
	// Many CAD exports include form fields with metadata
	return nil, fmt.Errorf("form field extraction not yet implemented")
}

// parseFormFields converts form fields to floor plan objects
func (p *UniversalParser) parseFormFields(fields map[string]string, plan *models.FloorPlan) {
	for fieldName, fieldValue := range fields {
		// Check if field contains equipment or room data
		logger.Debug("Form field: %s = %s", fieldName, fieldValue)
	}
}

// createManualEntryTemplate creates a template for manual data entry
func (p *UniversalParser) createManualEntryTemplate(plan *models.FloorPlan) {
	logger.Info("Creating template for manual entry")
	
	// Create a grid of rooms for manual population
	gridSize := 3 // 3x3 grid
	roomWidth := 30.0
	roomHeight := 20.0
	
	for row := 0; row < gridSize; row++ {
		for col := 0; col < gridSize; col++ {
			roomID := fmt.Sprintf("area_%d%d", row+1, col+1)
			room := models.Room{
				ID:   roomID,
				Name: fmt.Sprintf("Area %d-%d", row+1, col+1),
				Bounds: models.Bounds{
					MinX: float64(col) * roomWidth,
					MinY: float64(row) * roomHeight,
					MaxX: float64(col+1) * roomWidth,
					MaxY: float64(row+1) * roomHeight,
				},
				Equipment: []string{},
			}
			plan.Rooms = append(plan.Rooms, room)
		}
	}
	
	// Add instruction equipment
	instruction := models.Equipment{
		ID:   "instruction",
		Name: "Use 'arx add' to add equipment",
		Type: "note",
		Location: models.Point{
			X: roomWidth * float64(gridSize) / 2,
			Y: roomHeight * float64(gridSize) / 2,
		},
		Status: models.StatusUnknown,
		Notes:  "PDF could not be parsed automatically. Please add equipment manually.",
	}
	plan.Equipment = append(plan.Equipment, instruction)
}

// generateSpatialLayout arranges items spatially if no coordinates exist
func (p *UniversalParser) generateSpatialLayout(plan *models.FloorPlan) {
	// If equipment has no valid positions, arrange them in a grid
	needsLayout := false
	for _, equip := range plan.Equipment {
		if equip.Location.X == 0 && equip.Location.Y == 0 {
			needsLayout = true
			break
		}
	}
	
	if !needsLayout {
		return
	}
	
	logger.Info("Generating spatial layout for %d items", len(plan.Equipment))
	
	// Arrange equipment in a grid pattern
	cols := int(math.Ceil(math.Sqrt(float64(len(plan.Equipment)))))
	spacing := 15.0
	
	for i := range plan.Equipment {
		row := i / cols
		col := i % cols
		
		plan.Equipment[i].Location = models.Point{
			X: float64(col) * spacing + spacing,
			Y: float64(row) * spacing + spacing,
		}
		
		// Assign to nearest room
		if len(plan.Rooms) > 0 {
			plan.Equipment[i].RoomID = p.findNearestRoom(plan.Equipment[i].Location, plan.Rooms)
		}
	}
}

// findNearestRoom finds the room containing or nearest to a point
func (p *UniversalParser) findNearestRoom(point models.Point, rooms []models.Room) string {
	// First check if point is inside any room
	for _, room := range rooms {
		if room.Bounds.Contains(point) {
			return room.ID
		}
	}
	
	// Find nearest room center
	if len(rooms) > 0 {
		nearestRoom := rooms[0].ID
		minDist := p.distance(point, p.roomCenter(rooms[0]))
		
		for _, room := range rooms[1:] {
			dist := p.distance(point, p.roomCenter(room))
			if dist < minDist {
				minDist = dist
				nearestRoom = room.ID
			}
		}
		return nearestRoom
	}
	
	return ""
}

// roomCenter calculates the center of a room
func (p *UniversalParser) roomCenter(room models.Room) models.Point {
	return models.Point{
		X: (room.Bounds.MinX + room.Bounds.MaxX) / 2,
		Y: (room.Bounds.MinY + room.Bounds.MaxY) / 2,
	}
}

// distance calculates distance between two points
func (p *UniversalParser) distance(p1, p2 models.Point) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	return math.Sqrt(dx*dx + dy*dy)
}

// generateID creates a valid ID from text
func (p *UniversalParser) generateID(text string) string {
	// Remove special characters and spaces
	id := strings.ToLower(text)
	id = regexp.MustCompile(`[^a-z0-9_]`).ReplaceAllString(id, "_")
	id = regexp.MustCompile(`_+`).ReplaceAllString(id, "_")
	id = strings.Trim(id, "_")
	
	if id == "" {
		id = fmt.Sprintf("item_%d", time.Now().Unix())
	}
	
	return id
}

// Parse implements the Parser interface
func (p *UniversalParser) Parse(reader io.Reader) (*models.FloorPlan, error) {
	// For now, this expects a file path - would need to adapt for io.Reader
	return nil, fmt.Errorf("Parse from io.Reader not yet implemented")
}

// Export implements the Parser interface
func (p *UniversalParser) Export(plan *models.FloorPlan, writer io.Writer) error {
	// PDF export with markups - Phase 2
	return fmt.Errorf("PDF export not yet implemented")
}