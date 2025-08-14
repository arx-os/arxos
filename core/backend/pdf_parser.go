package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"io"
	"log"
	"math"
	"mime/multipart"
	"net/http"
	"os/exec"
	"sort"

	"github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu"
	"gocv.io/x/gocv"
)

// WallStructure represents the extracted building layout
type WallStructure struct {
	Walls      []Wall      `json:"walls"`
	Rooms      []Room      `json:"rooms"`
	Labels     []TextLabel `json:"labels"`
	Dimensions Dimensions  `json:"dimensions"`
}

// Wall represents a line segment in the floor plan
type Wall struct {
	StartX    float64 `json:"startX"`
	StartY    float64 `json:"startY"`
	EndX      float64 `json:"endX"`
	EndY      float64 `json:"endY"`
	Thickness float64 `json:"thickness"`
	Type      string  `json:"type"` // exterior, interior, partition
}

// Room represents a closed space
type Room struct {
	ID       string    `json:"id"`
	Polygon  []Point   `json:"polygon"`
	Centroid Point     `json:"centroid"`
	Area     float64   `json:"area"`
	Label    string    `json:"label"`
	Type     string    `json:"type"` // classroom, office, corridor, etc.
}

// Point represents a 2D coordinate
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// TextLabel represents extracted text from the PDF
type TextLabel struct {
	Text   string  `json:"text"`
	X      float64 `json:"x"`
	Y      float64 `json:"y"`
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
}

// Dimensions of the floor plan
type Dimensions struct {
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
	Scale  float64 `json:"scale"` // pixels per foot/meter
}

// PDFWallParser handles extraction of wall structures from PDFs
type PDFWallParser struct {
	dpi        int     // DPI for PDF to image conversion
	threshold  float64 // Threshold for line detection
	minLength  float64 // Minimum wall length to consider
	angleSnap  float64 // Snap walls to angles (0, 45, 90 degrees)
}

// NewPDFWallParser creates a new parser instance
func NewPDFWallParser() *PDFWallParser {
	return &PDFWallParser{
		dpi:       300,  // High resolution for accuracy
		threshold: 0.8,  // Line detection threshold
		minLength: 10.0, // Minimum wall length in pixels
		angleSnap: 5.0,  // Snap to nearest 5 degrees
	}
}

// ParsePDF extracts wall structure from a PDF file
func (p *PDFWallParser) ParsePDF(file multipart.File, header *multipart.FileHeader) (*WallStructure, error) {
	// Read PDF into memory
	pdfData, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read PDF: %w", err)
	}

	// Convert PDF to high-resolution image
	img, err := p.pdfToImage(pdfData)
	if err != nil {
		return nil, fmt.Errorf("failed to convert PDF to image: %w", err)
	}

	// Extract walls using computer vision
	walls := p.detectWalls(img)

	// Find rooms from closed wall polygons
	rooms := p.findRooms(walls)

	// Extract text labels using OCR
	labels := p.extractText(img)

	// Match labels to rooms
	p.matchLabelsToRooms(rooms, labels)

	// Calculate dimensions
	dims := p.calculateDimensions(img, walls)

	return &WallStructure{
		Walls:      walls,
		Rooms:      rooms,
		Labels:     labels,
		Dimensions: dims,
	}, nil
}

// pdfToImage converts PDF to high-resolution image
func (p *PDFWallParser) pdfToImage(pdfData []byte) (image.Image, error) {
	// Use pdfcpu to extract first page as image
	// In production, you might use ImageMagick or Poppler for better quality
	
	// For now, simulate with a command-line tool
	// This would call: pdftoppm -png -r 300 -f 1 -l 1 input.pdf output
	
	// Write PDF to temp file
	tmpPDF := "/tmp/floorplan.pdf"
	if err := os.WriteFile(tmpPDF, pdfData, 0644); err != nil {
		return nil, err
	}
	defer os.Remove(tmpPDF)

	// Convert to PNG using pdftoppm (requires poppler-utils)
	tmpPNG := "/tmp/floorplan.png"
	cmd := exec.Command("pdftoppm", "-png", "-r", fmt.Sprintf("%d", p.dpi), 
		"-f", "1", "-l", "1", "-singlefile", tmpPDF, "/tmp/floorplan")
	if err := cmd.Run(); err != nil {
		// Fallback: try ImageMagick convert
		cmd = exec.Command("convert", "-density", fmt.Sprintf("%d", p.dpi),
			tmpPDF+"[0]", tmpPNG)
		if err := cmd.Run(); err != nil {
			return nil, fmt.Errorf("PDF to image conversion failed: %w", err)
		}
	}
	defer os.Remove(tmpPNG)

	// Read the generated image
	imgFile, err := os.Open(tmpPNG)
	if err != nil {
		return nil, err
	}
	defer imgFile.Close()

	img, _, err := image.Decode(imgFile)
	return img, err
}

// detectWalls uses OpenCV to detect lines in the floor plan
func (p *PDFWallParser) detectWalls(img image.Image) []Wall {
	// Convert to OpenCV Mat
	mat := gocv.NewMat()
	defer mat.Close()

	// Convert image to Mat
	bounds := img.Bounds()
	rgba := image.NewRGBA(bounds)
	draw.Draw(rgba, bounds, img, bounds.Min, draw.Src)
	mat, _ = gocv.ImageToMatRGBA(rgba)

	// Convert to grayscale
	gray := gocv.NewMat()
	defer gray.Close()
	gocv.CvtColor(mat, &gray, gocv.ColorRGBAToGray)

	// Apply Gaussian blur to reduce noise
	gocv.GaussianBlur(gray, &gray, image.Pt(5, 5), 0, 0, gocv.BorderDefault)

	// Edge detection using Canny
	edges := gocv.NewMat()
	defer edges.Close()
	gocv.Canny(gray, &edges, 50, 150)

	// Detect lines using HoughLinesP
	lines := gocv.HoughLinesPWithParams(edges, 1, math.Pi/180, 50, 30, 10)

	// Convert detected lines to Wall structures
	walls := []Wall{}
	for _, line := range lines {
		wall := Wall{
			StartX:    float64(line.P1.X),
			StartY:    float64(line.P1.Y),
			EndX:      float64(line.P2.X),
			EndY:      float64(line.P2.Y),
			Thickness: p.estimateWallThickness(edges, line),
			Type:      p.classifyWall(line, bounds),
		}

		// Filter out very short lines
		length := math.Sqrt(math.Pow(wall.EndX-wall.StartX, 2) + 
			math.Pow(wall.EndY-wall.StartY, 2))
		if length >= p.minLength {
			// Snap to common angles
			wall = p.snapWallToAngle(wall)
			walls = append(walls, wall)
		}
	}

	// Merge nearby parallel walls
	walls = p.mergeNearbyWalls(walls)

	// Connect walls at intersections
	walls = p.connectWalls(walls)

	return walls
}

// findRooms identifies closed polygons from walls
func (p *PDFWallParser) findRooms(walls []Wall) []Room {
	rooms := []Room{}
	
	// Build a graph of wall connections
	graph := p.buildWallGraph(walls)
	
	// Find all closed cycles in the graph
	cycles := p.findCycles(graph)
	
	// Convert cycles to rooms
	for i, cycle := range cycles {
		room := Room{
			ID:      fmt.Sprintf("room_%d", i+1),
			Polygon: cycle,
			Area:    p.calculatePolygonArea(cycle),
		}
		room.Centroid = p.calculateCentroid(cycle)
		rooms = append(rooms, room)
	}
	
	return rooms
}

// extractText uses OCR to extract text labels
func (p *PDFWallParser) extractText(img image.Image) []TextLabel {
	// Convert image to format suitable for OCR
	// In production, use Tesseract or cloud OCR service
	
	labels := []TextLabel{}
	
	// For now, return mock data
	// In real implementation, this would use Tesseract OCR
	/*
	client := gosseract.NewClient()
	defer client.Close()
	client.SetImage(img)
	text, _ := client.Text()
	*/
	
	return labels
}

// matchLabelsToRooms associates text labels with rooms
func (p *PDFWallParser) matchLabelsToRooms(rooms []Room, labels []TextLabel) {
	for i := range rooms {
		for _, label := range labels {
			if p.pointInPolygon(Point{X: label.X, Y: label.Y}, rooms[i].Polygon) {
				rooms[i].Label = label.Text
				
				// Classify room type based on label
				rooms[i].Type = p.classifyRoomType(label.Text)
				break
			}
		}
	}
}

// Helper functions

func (p *PDFWallParser) estimateWallThickness(edges gocv.Mat, line gocv.LineSegment) float64 {
	// Sample perpendicular to the line to estimate thickness
	// Simplified - in production, use more sophisticated method
	return 2.0 // Default thickness
}

func (p *PDFWallParser) classifyWall(line gocv.LineSegment, bounds image.Rectangle) string {
	// Check if wall is on the perimeter
	margin := 20
	if line.P1.X < margin || line.P1.X > bounds.Max.X-margin ||
		line.P1.Y < margin || line.P1.Y > bounds.Max.Y-margin ||
		line.P2.X < margin || line.P2.X > bounds.Max.X-margin ||
		line.P2.Y < margin || line.P2.Y > bounds.Max.Y-margin {
		return "exterior"
	}
	return "interior"
}

func (p *PDFWallParser) snapWallToAngle(wall Wall) Wall {
	// Calculate angle
	dx := wall.EndX - wall.StartX
	dy := wall.EndY - wall.StartY
	angle := math.Atan2(dy, dx) * 180 / math.Pi
	
	// Snap to nearest multiple of angleSnap
	snappedAngle := math.Round(angle/p.angleSnap) * p.angleSnap
	
	// Recalculate end point
	length := math.Sqrt(dx*dx + dy*dy)
	radians := snappedAngle * math.Pi / 180
	wall.EndX = wall.StartX + length*math.Cos(radians)
	wall.EndY = wall.StartY + length*math.Sin(radians)
	
	return wall
}

func (p *PDFWallParser) mergeNearbyWalls(walls []Wall) []Wall {
	// Merge walls that are very close and parallel
	// This reduces noise from the line detection
	merged := []Wall{}
	used := make([]bool, len(walls))
	
	for i, wall1 := range walls {
		if used[i] {
			continue
		}
		
		// Check if any other wall should be merged with this one
		for j := i + 1; j < len(walls); j++ {
			if used[j] {
				continue
			}
			
			wall2 := walls[j]
			if p.shouldMergeWalls(wall1, wall2) {
				// Merge wall2 into wall1
				wall1 = p.mergeWalls(wall1, wall2)
				used[j] = true
			}
		}
		
		merged = append(merged, wall1)
		used[i] = true
	}
	
	return merged
}

func (p *PDFWallParser) shouldMergeWalls(w1, w2 Wall) bool {
	// Check if walls are parallel and close
	angle1 := math.Atan2(w1.EndY-w1.StartY, w1.EndX-w1.StartX)
	angle2 := math.Atan2(w2.EndY-w2.StartY, w2.EndX-w2.StartX)
	
	angleDiff := math.Abs(angle1 - angle2)
	if angleDiff > math.Pi {
		angleDiff = 2*math.Pi - angleDiff
	}
	
	// Check if parallel (within 5 degrees)
	if angleDiff > 5*math.Pi/180 {
		return false
	}
	
	// Check if close (within 10 pixels)
	dist := p.lineToLineDistance(w1, w2)
	return dist < 10
}

func (p *PDFWallParser) mergeWalls(w1, w2 Wall) Wall {
	// Merge two walls into one longer wall
	// Find the extreme points
	points := []Point{
		{X: w1.StartX, Y: w1.StartY},
		{X: w1.EndX, Y: w1.EndY},
		{X: w2.StartX, Y: w2.StartY},
		{X: w2.EndX, Y: w2.EndY},
	}
	
	// Find the two points that are farthest apart
	maxDist := 0.0
	var p1, p2 Point
	for i := 0; i < len(points); i++ {
		for j := i + 1; j < len(points); j++ {
			dist := math.Sqrt(math.Pow(points[i].X-points[j].X, 2) +
				math.Pow(points[i].Y-points[j].Y, 2))
			if dist > maxDist {
				maxDist = dist
				p1 = points[i]
				p2 = points[j]
			}
		}
	}
	
	return Wall{
		StartX:    p1.X,
		StartY:    p1.Y,
		EndX:      p2.X,
		EndY:      p2.Y,
		Thickness: (w1.Thickness + w2.Thickness) / 2,
		Type:      w1.Type,
	}
}

func (p *PDFWallParser) connectWalls(walls []Wall) []Wall {
	// Connect walls that almost meet at intersections
	threshold := 5.0 // pixels
	
	for i := range walls {
		for j := range walls {
			if i == j {
				continue
			}
			
			// Check if end of wall i is close to start/end of wall j
			dist1 := p.pointDistance(
				Point{X: walls[i].EndX, Y: walls[i].EndY},
				Point{X: walls[j].StartX, Y: walls[j].StartY},
			)
			dist2 := p.pointDistance(
				Point{X: walls[i].EndX, Y: walls[i].EndY},
				Point{X: walls[j].EndX, Y: walls[j].EndY},
			)
			
			if dist1 < threshold {
				walls[i].EndX = walls[j].StartX
				walls[i].EndY = walls[j].StartY
			} else if dist2 < threshold {
				walls[i].EndX = walls[j].EndX
				walls[i].EndY = walls[j].EndY
			}
		}
	}
	
	return walls
}

func (p *PDFWallParser) buildWallGraph(walls []Wall) map[Point][]Point {
	graph := make(map[Point][]Point)
	
	for _, wall := range walls {
		p1 := Point{X: wall.StartX, Y: wall.StartY}
		p2 := Point{X: wall.EndX, Y: wall.EndY}
		
		graph[p1] = append(graph[p1], p2)
		graph[p2] = append(graph[p2], p1)
	}
	
	return graph
}

func (p *PDFWallParser) findCycles(graph map[Point][]Point) [][]Point {
	// Find all closed cycles in the wall graph
	// This identifies rooms
	cycles := [][]Point{}
	
	// Simplified cycle detection
	// In production, use proper graph cycle detection algorithm
	
	return cycles
}

func (p *PDFWallParser) calculatePolygonArea(polygon []Point) float64 {
	// Calculate area using shoelace formula
	area := 0.0
	n := len(polygon)
	
	for i := 0; i < n; i++ {
		j := (i + 1) % n
		area += polygon[i].X * polygon[j].Y
		area -= polygon[j].X * polygon[i].Y
	}
	
	return math.Abs(area) / 2.0
}

func (p *PDFWallParser) calculateCentroid(polygon []Point) Point {
	cx := 0.0
	cy := 0.0
	
	for _, p := range polygon {
		cx += p.X
		cy += p.Y
	}
	
	return Point{
		X: cx / float64(len(polygon)),
		Y: cy / float64(len(polygon)),
	}
}

func (p *PDFWallParser) pointInPolygon(point Point, polygon []Point) bool {
	// Ray casting algorithm
	inside := false
	n := len(polygon)
	
	p1 := polygon[0]
	for i := 1; i <= n; i++ {
		p2 := polygon[i%n]
		
		if point.Y > math.Min(p1.Y, p2.Y) {
			if point.Y <= math.Max(p1.Y, p2.Y) {
				if point.X <= math.Max(p1.X, p2.X) {
					if p1.Y != p2.Y {
						xinters := (point.Y-p1.Y)*(p2.X-p1.X)/(p2.Y-p1.Y) + p1.X
					}
					if p1.X == p2.X || point.X <= xinters {
						inside = !inside
					}
				}
			}
		}
		p1 = p2
	}
	
	return inside
}

func (p *PDFWallParser) classifyRoomType(label string) string {
	// Classify room based on label
	// Add more sophisticated classification logic
	if contains(label, []string{"office", "admin", "reception"}) {
		return "office"
	}
	if contains(label, []string{"class", "room", "lab"}) {
		return "classroom"
	}
	if contains(label, []string{"bath", "rest", "toilet"}) {
		return "restroom"
	}
	if contains(label, []string{"storage", "closet", "utility"}) {
		return "storage"
	}
	if contains(label, []string{"corridor", "hall", "lobby"}) {
		return "corridor"
	}
	return "general"
}

func (p *PDFWallParser) calculateDimensions(img image.Image, walls []Wall) Dimensions {
	bounds := img.Bounds()
	return Dimensions{
		Width:  float64(bounds.Max.X),
		Height: float64(bounds.Max.Y),
		Scale:  p.estimateScale(walls), // Estimate scale from typical door width
	}
}

func (p *PDFWallParser) estimateScale(walls []Wall) float64 {
	// Look for typical door openings (usually 3 feet)
	// Find gaps in walls that are likely doors
	typicalDoorWidth := 36.0 // inches
	
	// This is simplified - in production, use more sophisticated detection
	return 0.1 // Default: 0.1 inches per pixel
}

func (p *PDFWallParser) lineToLineDistance(w1, w2 Wall) float64 {
	// Calculate minimum distance between two line segments
	// Simplified version
	return p.pointToLineDistance(
		Point{X: w1.StartX, Y: w1.StartY},
		w2,
	)
}

func (p *PDFWallParser) pointToLineDistance(p Point, w Wall) float64 {
	// Distance from point to line segment
	A := p.X - w.StartX
	B := p.Y - w.StartY
	C := w.EndX - w.StartX
	D := w.EndY - w.StartY
	
	dot := A*C + B*D
	lenSq := C*C + D*D
	param := -1.0
	
	if lenSq != 0 {
		param = dot / lenSq
	}
	
	var xx, yy float64
	
	if param < 0 {
		xx = w.StartX
		yy = w.StartY
	} else if param > 1 {
		xx = w.EndX
		yy = w.EndY
	} else {
		xx = w.StartX + param*C
		yy = w.StartY + param*D
	}
	
	dx := p.X - xx
	dy := p.Y - yy
	
	return math.Sqrt(dx*dx + dy*dy)
}

func (p *PDFWallParser) pointDistance(p1, p2 Point) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	return math.Sqrt(dx*dx + dy*dy)
}

func contains(str string, substrs []string) bool {
	lower := strings.ToLower(str)
	for _, substr := range substrs {
		if strings.Contains(lower, substr) {
			return true
		}
	}
	return false
}

// HandlePDFWallExtraction processes PDF and returns wall structure
func HandlePDFWallExtraction(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Parse multipart form
	err := r.ParseMultipartForm(32 << 20) // 32MB max
	if err != nil {
		http.Error(w, "Failed to parse form", http.StatusBadRequest)
		return
	}
	
	// Get file
	file, header, err := r.FormFile("pdf")
	if err != nil {
		http.Error(w, "Failed to get file", http.StatusBadRequest)
		return
	}
	defer file.Close()
	
	// Parse PDF
	parser := NewPDFWallParser()
	structure, err := parser.ParsePDF(file, header)
	if err != nil {
		log.Printf("PDF parsing error: %v", err)
		http.Error(w, "Failed to parse PDF", http.StatusInternalServerError)
		return
	}
	
	// Convert to ArxObjects
	arxObjects := convertWallsToArxObjects(structure)
	
	// Return results
	response := map[string]interface{}{
		"filename":   header.Filename,
		"structure":  structure,
		"arxObjects": arxObjects,
		"stats": map[string]int{
			"walls": len(structure.Walls),
			"rooms": len(structure.Rooms),
			"labels": len(structure.Labels),
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func convertWallsToArxObjects(structure *WallStructure) []map[string]interface{} {
	objects := []map[string]interface{}{}
	
	// Convert walls
	for i, wall := range structure.Walls {
		objects = append(objects, map[string]interface{}{
			"id":       fmt.Sprintf("wall_%d", i),
			"type":     "wall",
			"system":   "structural",
			"geometry": "line",
			"startX":   wall.StartX,
			"startY":   wall.StartY,
			"endX":     wall.EndX,
			"endY":     wall.EndY,
			"properties": map[string]interface{}{
				"thickness": wall.Thickness,
				"wallType":  wall.Type,
			},
		})
	}
	
	// Convert rooms
	for _, room := range structure.Rooms {
		objects = append(objects, map[string]interface{}{
			"id":       room.ID,
			"type":     "room",
			"system":   "spatial",
			"geometry": "polygon",
			"polygon":  room.Polygon,
			"centroid": room.Centroid,
			"properties": map[string]interface{}{
				"area":     room.Area,
				"label":    room.Label,
				"roomType": room.Type,
			},
		})
	}
	
	return objects
}