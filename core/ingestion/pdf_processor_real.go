package ingestion

import (
	"fmt"
	"math"
	"regexp"
	"strings"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/google/uuid"
	"github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/types"
)

// PDFProcessor handles PDF to ArxObject conversion
type PDFProcessor struct {
	confidenceBase float32
	pageCache      map[int]*PDFPage
	symbolPatterns map[string]arxobject.ArxObjectType
}

// PDFPage represents extracted page data
type PDFPage struct {
	Number   int
	Width    float64
	Height   float64
	Lines    []Line
	Texts    []Text
	Shapes   []Shape
	Scale    float64
}

// Line represents a line segment
type Line struct {
	X1, Y1, X2, Y2 float64
	Width          float64
	Color          string
	Layer          string
}

// Text represents text content
type Text struct {
	Content string
	X, Y    float64
	Size    float64
	Font    string
}

// Shape represents a shape (rectangle, circle, etc.)
type Shape struct {
	Type   string // "rect", "circle", "arc"
	Bounds Bounds
	Layer  string
}

// Bounds represents a bounding box
type Bounds struct {
	MinX, MinY, MaxX, MaxY float64
}

// NewPDFProcessor creates a new PDF processor
func NewPDFProcessor() *PDFProcessor {
	return &PDFProcessor{
		confidenceBase: 0.7, // Base confidence for PDF extraction
		pageCache:      make(map[int]*PDFPage),
		symbolPatterns: map[string]arxobject.ArxObjectType{
			"door_arc":     arxobject.ArxObjectType("door"),
			"window_break": arxobject.ArxObjectType("window"),
			"circle_small": arxobject.ArxObjectType("column"),
			"diamond":      arxobject.ArxObjectType("electrical_outlet"),
		},
	}
}

// CanProcess checks if file can be processed
func (p *PDFProcessor) CanProcess(filepath string) bool {
	return strings.HasSuffix(strings.ToLower(filepath), ".pdf")
}

// GetConfidenceBase returns base confidence for PDF format
func (p *PDFProcessor) GetConfidenceBase() float32 {
	return p.confidenceBase
}

// Process extracts ArxObjects from PDF
func (p *PDFProcessor) Process(filepath string) (*ProcessingResult, error) {
	result := &ProcessingResult{
		Objects:  []arxobject.ArxObject{},
		Errors:   []string{},
		Warnings: []string{},
	}

	// Open PDF
	ctx, err := api.ReadContextFile(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to read PDF: %w", err)
	}

	// Process each page
	for pageNum := 1; pageNum <= ctx.PageCount; pageNum++ {
		page, err := p.extractPage(ctx, pageNum)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("Page %d: %v", pageNum, err))
			continue
		}

		// Extract objects from page
		pageObjects := p.extractObjects(page)
		result.Objects = append(result.Objects, pageObjects...)
	}

	// Post-process: find relationships
	p.findRelationships(result.Objects)

	// Post-process: detect rooms from enclosed spaces
	rooms := p.detectRooms(result.Objects)
	result.Objects = append(result.Objects, rooms...)

	return result, nil
}

// extractPage extracts data from a PDF page
func (p *PDFProcessor) extractPage(ctx *model.Context, pageNum int) (*PDFPage, error) {
	// Check cache
	if cached, exists := p.pageCache[pageNum]; exists {
		return cached, nil
	}

	page := &PDFPage{
		Number: pageNum,
		Lines:  []Line{},
		Texts:  []Text{},
		Shapes: []Shape{},
	}

	// Get page dictionary
	pageDict, err := ctx.PageDict(pageNum, false)
	if err != nil {
		return nil, err
	}

	// Get page dimensions
	mediaBox := pageDict.MediaBox()
	if mediaBox != nil {
		page.Width = mediaBox.Width()
		page.Height = mediaBox.Height()
	}

	// Extract content streams
	content, err := ctx.PageContent(pageDict)
	if err != nil {
		return nil, err
	}

	// Parse content streams for graphics
	p.parseContentStream(content, page)

	// Extract text
	p.extractText(ctx, pageNum, page)

	// Detect scale from dimension text
	page.Scale = p.detectScale(page.Texts)

	// Cache the page
	p.pageCache[pageNum] = page

	return page, nil
}

// parseContentStream parses PDF content stream for graphics
func (p *PDFProcessor) parseContentStream(content []byte, page *PDFPage) {
	// This is simplified - real implementation would use proper PDF parsing
	// Look for common PDF operators:
	// m = moveto
	// l = lineto
	// re = rectangle
	// S = stroke
	// f = fill

	contentStr := string(content)
	lines := strings.Split(contentStr, "\n")

	var currentX, currentY float64
	var currentPath []Point

	for _, line := range lines {
		tokens := strings.Fields(line)
		if len(tokens) == 0 {
			continue
		}

		operator := tokens[len(tokens)-1]

		switch operator {
		case "m": // moveto
			if len(tokens) >= 3 {
				currentX = parseFloat(tokens[0])
				currentY = parseFloat(tokens[1])
				currentPath = []Point{{currentX, currentY}}
			}

		case "l": // lineto
			if len(tokens) >= 3 {
				x := parseFloat(tokens[0])
				y := parseFloat(tokens[1])
				if len(currentPath) > 0 {
					page.Lines = append(page.Lines, Line{
						X1: currentX,
						Y1: currentY,
						X2: x,
						Y2: y,
						Width: 1.0, // Default width
					})
				}
				currentX = x
				currentY = y
				currentPath = append(currentPath, Point{x, y})
			}

		case "re": // rectangle
			if len(tokens) >= 5 {
				x := parseFloat(tokens[0])
				y := parseFloat(tokens[1])
				w := parseFloat(tokens[2])
				h := parseFloat(tokens[3])
				page.Shapes = append(page.Shapes, Shape{
					Type: "rect",
					Bounds: Bounds{
						MinX: x,
						MinY: y,
						MaxX: x + w,
						MaxY: y + h,
					},
				})
			}

		case "S", "s": // stroke path
			// Path completed
			currentPath = []Point{}
		}
	}
}

// extractText extracts text from page
func (p *PDFProcessor) extractText(ctx *model.Context, pageNum int, page *PDFPage) {
	// Extract text with position information
	// This is simplified - would use pdfcpu's text extraction API
	
	// For now, create some sample text extraction
	// In production, use proper text extraction
}

// extractObjects converts page elements to ArxObjects
func (p *PDFProcessor) extractObjects(page *PDFPage) []arxobject.ArxObject {
	objects := []arxobject.ArxObject{}

	// Extract walls from lines
	walls := p.extractWalls(page.Lines)
	objects = append(objects, walls...)

	// Extract doors from arcs and specific patterns
	doors := p.extractDoors(page)
	objects = append(objects, doors...)

	// Extract columns from small rectangles/circles
	columns := p.extractColumns(page.Shapes)
	objects = append(objects, columns...)

	// Extract labeled objects from text
	labeledObjects := p.extractLabeledObjects(page.Texts, page)
	objects = append(objects, labeledObjects...)

	return objects
}

// extractWalls identifies walls from lines
func (p *PDFProcessor) extractWalls(lines []Line) []arxobject.ArxObject {
	walls := []arxobject.ArxObject{}

	for _, line := range lines {
		// Check if line is likely a wall
		length := math.Sqrt(math.Pow(line.X2-line.X1, 2) + math.Pow(line.Y2-line.Y1, 2))
		
		// Walls are typically longer lines
		if length > 50 && line.Width >= 0.5 {
			wall := CreateArxObject(
				arxobject.ArxObjectType("wall"),
				arxobject.ConfidenceScore{
					Classification: 0.75,
					Position:       0.85,
					Properties:     0.6,
					Relationships:  0.5,
					Overall:        0.7,
				},
			)

			wall.Geometry = arxobject.Geometry{
				Type: "LineString",
				Coordinates: [][]float64{
					{line.X1, line.Y1},
					{line.X2, line.Y2},
				},
			}

			wall.Data["length"] = length
			wall.Data["thickness"] = line.Width
			wall.Data["is_load_bearing"] = line.Width > 2.0

			walls = append(walls, wall)
		}
	}

	return walls
}

// extractDoors identifies doors from patterns
func (p *PDFProcessor) extractDoors(page *PDFPage) []arxobject.ArxObject {
	doors := []arxobject.ArxObject{}

	// Look for arc patterns (door swings)
	for _, shape := range page.Shapes {
		if shape.Type == "arc" {
			// Check if arc radius is reasonable for a door
			radius := (shape.Bounds.MaxX - shape.Bounds.MinX) / 2
			if radius > 20 && radius < 50 {
				door := CreateArxObject(
					arxobject.ArxObjectType("door"),
					arxobject.ConfidenceScore{
						Classification: 0.7,
						Position:       0.8,
						Properties:     0.5,
						Relationships:  0.4,
						Overall:        0.6,
					},
				)

				door.Geometry = arxobject.Geometry{
					Type:        "Point",
					Coordinates: [][]float64{{shape.Bounds.MinX + radius, shape.Bounds.MinY + radius}},
				}

				door.Data["swing_radius"] = radius
				door.Data["type"] = "single"

				doors = append(doors, door)
			}
		}
	}

	return doors
}

// extractColumns identifies columns from shapes
func (p *PDFProcessor) extractColumns(shapes []Shape) []arxobject.ArxObject {
	columns := []arxobject.ArxObject{}

	for _, shape := range shapes {
		if shape.Type == "rect" {
			width := shape.Bounds.MaxX - shape.Bounds.MinX
			height := shape.Bounds.MaxY - shape.Bounds.MinY

			// Columns are typically small, square-ish shapes
			if width > 5 && width < 30 && height > 5 && height < 30 {
				aspectRatio := width / height
				if aspectRatio > 0.7 && aspectRatio < 1.3 {
					column := CreateArxObject(
						arxobject.ArxObjectType("column"),
						arxobject.ConfidenceScore{
							Classification: 0.65,
							Position:       0.85,
							Properties:     0.5,
							Relationships:  0.4,
							Overall:        0.6,
						},
					)

					column.Geometry = arxobject.Geometry{
						Type: "Polygon",
						Coordinates: [][]float64{
							{shape.Bounds.MinX, shape.Bounds.MinY},
							{shape.Bounds.MaxX, shape.Bounds.MinY},
							{shape.Bounds.MaxX, shape.Bounds.MaxY},
							{shape.Bounds.MinX, shape.Bounds.MaxY},
							{shape.Bounds.MinX, shape.Bounds.MinY},
						},
					}

					column.Data["width"] = width
					column.Data["height"] = height

					columns = append(columns, column)
				}
			}
		}
	}

	return columns
}

// extractLabeledObjects extracts objects from text labels
func (p *PDFProcessor) extractLabeledObjects(texts []Text, page *PDFPage) []arxobject.ArxObject {
	objects := []arxobject.ArxObject{}

	roomPattern := regexp.MustCompile(`(?i)(room|office|conference|bath|kitchen|lobby)`)
	electricalPattern := regexp.MustCompile(`(?i)(panel|electrical|breaker)`)
	hvacPattern := regexp.MustCompile(`(?i)(hvac|mechanical|ac|heating)`)

	for _, text := range texts {
		content := strings.ToLower(text.Content)

		var objType arxobject.ArxObjectType
		var confidence float32 = 0.8

		switch {
		case roomPattern.MatchString(content):
			objType = arxobject.ArxObjectType("room")
		case electricalPattern.MatchString(content):
			objType = arxobject.ArxObjectType("electrical_panel")
			confidence = 0.85
		case hvacPattern.MatchString(content):
			objType = arxobject.ArxObjectType("hvac_unit")
			confidence = 0.75
		default:
			continue
		}

		obj := CreateArxObject(
			objType,
			arxobject.ConfidenceScore{
				Classification: confidence,
				Position:       0.7,
				Properties:     0.8,
				Relationships:  0.5,
				Overall:        confidence * 0.9,
			},
		)

		obj.Geometry = arxobject.Geometry{
			Type:        "Point",
			Coordinates: [][]float64{{text.X, text.Y}},
		}

		obj.Data["label"] = text.Content
		obj.Data["font_size"] = text.Size

		objects = append(objects, obj)
	}

	return objects
}

// detectRooms detects rooms from enclosed wall spaces
func (p *PDFProcessor) detectRooms(objects []arxobject.ArxObject) []arxobject.ArxObject {
	rooms := []arxobject.ArxObject{}

	// Get all walls
	walls := filterObjectsByType(objects, arxobject.ArxObjectType("wall"))

	// Find enclosed spaces (simplified - would use proper polygon detection)
	// For now, just create a room if we have enough walls in proximity

	// Group walls by proximity
	// This is a simplified implementation
	// Real implementation would use computational geometry

	return rooms
}

// findRelationships identifies relationships between objects
func (p *PDFProcessor) findRelationships(objects []arxobject.ArxObject) {
	// Find spatial relationships
	for i, obj1 := range objects {
		for j, obj2 := range objects {
			if i == j {
				continue
			}

			// Check if objects are connected
			if p.areConnected(obj1, obj2) {
				rel := arxobject.Relationship{
					Type:       "connected_to",
					TargetID:   obj2.ID,
					Confidence: 0.7,
					Properties: map[string]interface{}{
						"distance": p.calculateDistance(obj1, obj2),
					},
				}
				objects[i].Relationships = append(objects[i].Relationships, rel)
			}
		}
	}
}

// Helper functions

func (p *PDFProcessor) areConnected(obj1, obj2 arxobject.ArxObject) bool {
	// Check if objects are spatially connected
	// Simplified - would use proper spatial analysis
	dist := p.calculateDistance(obj1, obj2)
	return dist < 10 // Within 10 units
}

func (p *PDFProcessor) calculateDistance(obj1, obj2 arxobject.ArxObject) float64 {
	// Calculate distance between objects
	// Simplified - would use proper geometric distance
	if obj1.Geometry.Type == "Point" && obj2.Geometry.Type == "Point" {
		coords1 := obj1.Geometry.Coordinates[0]
		coords2 := obj2.Geometry.Coordinates[0]
		return math.Sqrt(math.Pow(coords2[0]-coords1[0], 2) + math.Pow(coords2[1]-coords1[1], 2))
	}
	return 999999 // Far apart
}

func (p *PDFProcessor) detectScale(texts []Text) float64 {
	// Look for scale indicators in text
	scalePattern := regexp.MustCompile(`(?i)scale[:\s]+1[:\s](\d+)`)
	
	for _, text := range texts {
		if matches := scalePattern.FindStringSubmatch(text.Content); len(matches) > 1 {
			if scale := parseFloat(matches[1]); scale > 0 {
				return scale
			}
		}
	}
	
	return 1.0 // Default scale
}

func filterObjectsByType(objects []arxobject.ArxObject, objType arxobject.ArxObjectType) []arxobject.ArxObject {
	filtered := []arxobject.ArxObject{}
	for _, obj := range objects {
		if obj.Type == objType {
			filtered = append(filtered, obj)
		}
	}
	return filtered
}

func parseFloat(s string) float64 {
	// Parse float with error handling
	var f float64
	fmt.Sscanf(s, "%f", &f)
	return f
}

// Point represents a 2D point
type Point struct {
	X, Y float64
}