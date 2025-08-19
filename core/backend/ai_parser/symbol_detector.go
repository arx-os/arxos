package ai_parser

import (
	"image"
	"image/color"
	"math"
)

// Symbol represents a detected architectural symbol
type Symbol struct {
	Type       string                 `json:"type"`
	X          float64                `json:"x"`
	Y          float64                `json:"y"`
	Width      float64                `json:"width"`
	Height     float64                `json:"height"`
	Rotation   float64                `json:"rotation"`
	Confidence float32                `json:"confidence"`
	Properties map[string]interface{} `json:"properties"`
	Features   []Feature              `json:"features"`
}

// Feature represents a visual feature used for detection
type Feature struct {
	Type       string  `json:"type"`
	Value      float64 `json:"value"`
	Confidence float32 `json:"confidence"`
}

// SymbolDetector detects architectural symbols in images
type SymbolDetector struct {
	templates    map[string]*SymbolTemplate
	minConfidence float32
}

// SymbolTemplate represents a template for symbol matching
type SymbolTemplate struct {
	Type         string
	Patterns     [][]float64
	Features     []FeatureDescriptor
	MinSize      int
	MaxSize      int
	AspectRatio  float64
}

// FeatureDescriptor describes a feature to look for
type FeatureDescriptor struct {
	Type       string
	Location   string
	Expected   float64
	Tolerance  float64
}

// NewSymbolDetector creates a new symbol detector
func NewSymbolDetector() *SymbolDetector {
	detector := &SymbolDetector{
		templates:     make(map[string]*SymbolTemplate),
		minConfidence: 0.7,
	}
	detector.loadTemplates()
	return detector
}

// loadTemplates loads symbol templates
func (d *SymbolDetector) loadTemplates() {
	// Door template - arc pattern
	d.templates["door"] = &SymbolTemplate{
		Type:        "door",
		MinSize:     30,
		MaxSize:     150,
		AspectRatio: 1.0,
		Features: []FeatureDescriptor{
			{Type: "arc", Location: "center", Expected: 0.25, Tolerance: 0.1},
			{Type: "line", Location: "bottom", Expected: 1.0, Tolerance: 0.1},
		},
	}

	// Window template - parallel lines with center division
	d.templates["window"] = &SymbolTemplate{
		Type:        "window",
		MinSize:     40,
		MaxSize:     200,
		AspectRatio: 3.0,
		Features: []FeatureDescriptor{
			{Type: "parallel_lines", Location: "horizontal", Expected: 2.0, Tolerance: 0.1},
			{Type: "line", Location: "center", Expected: 1.0, Tolerance: 0.1},
		},
	}

	// Electrical outlet - circle with internal elements
	d.templates["outlet"] = &SymbolTemplate{
		Type:        "outlet",
		MinSize:     10,
		MaxSize:     30,
		AspectRatio: 1.0,
		Features: []FeatureDescriptor{
			{Type: "circle", Location: "outer", Expected: 1.0, Tolerance: 0.1},
			{Type: "rectangles", Location: "inner", Expected: 2.0, Tolerance: 0.5},
		},
	}

	// Column - filled rectangle or circle
	d.templates["column"] = &SymbolTemplate{
		Type:        "column",
		MinSize:     20,
		MaxSize:     100,
		AspectRatio: 1.0,
		Features: []FeatureDescriptor{
			{Type: "filled_rect", Location: "center", Expected: 1.0, Tolerance: 0.1},
		},
	}

	// Stairs - parallel lines with direction indicator
	d.templates["stairs"] = &SymbolTemplate{
		Type:        "stairs",
		MinSize:     50,
		MaxSize:     300,
		AspectRatio: 2.0,
		Features: []FeatureDescriptor{
			{Type: "parallel_lines", Location: "vertical", Expected: 5.0, Tolerance: 3.0},
			{Type: "arrow", Location: "end", Expected: 1.0, Tolerance: 0.2},
		},
	}

	// Toilet - characteristic oval and tank shape
	d.templates["toilet"] = &SymbolTemplate{
		Type:        "toilet",
		MinSize:     30,
		MaxSize:     80,
		AspectRatio: 1.5,
		Features: []FeatureDescriptor{
			{Type: "oval", Location: "center", Expected: 1.0, Tolerance: 0.1},
			{Type: "rectangle", Location: "back", Expected: 1.0, Tolerance: 0.1},
		},
	}

	// Sink - rectangle with circular basin
	d.templates["sink"] = &SymbolTemplate{
		Type:        "sink",
		MinSize:     30,
		MaxSize:     100,
		AspectRatio: 1.5,
		Features: []FeatureDescriptor{
			{Type: "rectangle", Location: "outer", Expected: 1.0, Tolerance: 0.1},
			{Type: "circle", Location: "center", Expected: 1.0, Tolerance: 0.1},
		},
	}
}

// DetectSymbols detects symbols in images
func (d *SymbolDetector) DetectSymbols(images []image.Image) []Symbol {
	symbols := []Symbol{}
	
	for _, img := range images {
		// Preprocess image
		processed := d.preprocessImage(img)
		
		// Detect edges
		edges := d.detectEdges(processed)
		
		// Find contours
		contours := d.findContours(edges)
		
		// Match against templates
		for _, contour := range contours {
			if symbol := d.matchTemplate(contour, processed); symbol != nil {
				symbols = append(symbols, *symbol)
			}
		}
		
		// Detect complex patterns
		patterns := d.detectComplexPatterns(processed, edges)
		symbols = append(symbols, patterns...)
	}
	
	// Remove duplicates and merge overlapping detections
	symbols = d.mergeDetections(symbols)
	
	return symbols
}

// preprocessImage preprocesses an image for symbol detection
func (d *SymbolDetector) preprocessImage(img image.Image) *image.Gray {
	bounds := img.Bounds()
	gray := image.NewGray(bounds)
	
	// Convert to grayscale
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			r, g, b, _ := img.At(x, y).RGBA()
			grayVal := uint8((r + g + b) / 3 >> 8)
			gray.SetGray(x, y, color.Gray{grayVal})
		}
	}
	
	// Apply adaptive thresholding
	return d.adaptiveThreshold(gray)
}

// adaptiveThreshold applies adaptive thresholding
func (d *SymbolDetector) adaptiveThreshold(img *image.Gray) *image.Gray {
	bounds := img.Bounds()
	result := image.NewGray(bounds)
	windowSize := 15
	
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			// Calculate local mean
			sum := 0
			count := 0
			for dy := -windowSize/2; dy <= windowSize/2; dy++ {
				for dx := -windowSize/2; dx <= windowSize/2; dx++ {
					nx, ny := x+dx, y+dy
					if nx >= bounds.Min.X && nx < bounds.Max.X && 
					   ny >= bounds.Min.Y && ny < bounds.Max.Y {
						sum += int(img.GrayAt(nx, ny).Y)
						count++
					}
				}
			}
			
			mean := sum / count
			pixel := img.GrayAt(x, y).Y
			if int(pixel) > mean-10 {
				result.SetGray(x, y, color.Gray{255})
			} else {
				result.SetGray(x, y, color.Gray{0})
			}
		}
	}
	
	return result
}

// detectEdges detects edges using Canny edge detection
func (d *SymbolDetector) detectEdges(img *image.Gray) *image.Gray {
	bounds := img.Bounds()
	edges := image.NewGray(bounds)
	
	// Simplified edge detection using Sobel operators
	sobelX := [][]int{
		{-1, 0, 1},
		{-2, 0, 2},
		{-1, 0, 1},
	}
	
	sobelY := [][]int{
		{-1, -2, -1},
		{0, 0, 0},
		{1, 2, 1},
	}
	
	for y := bounds.Min.Y + 1; y < bounds.Max.Y - 1; y++ {
		for x := bounds.Min.X + 1; x < bounds.Max.X - 1; x++ {
			gx, gy := 0, 0
			
			// Apply Sobel operators
			for dy := -1; dy <= 1; dy++ {
				for dx := -1; dx <= 1; dx++ {
					pixel := int(img.GrayAt(x+dx, y+dy).Y)
					gx += pixel * sobelX[dy+1][dx+1]
					gy += pixel * sobelY[dy+1][dx+1]
				}
			}
			
			// Calculate gradient magnitude
			magnitude := math.Sqrt(float64(gx*gx + gy*gy))
			if magnitude > 100 {
				edges.SetGray(x, y, color.Gray{255})
			} else {
				edges.SetGray(x, y, color.Gray{0})
			}
		}
	}
	
	return edges
}

// Contour represents a detected contour
type Contour struct {
	Points   []image.Point
	Bounds   image.Rectangle
	Area     float64
	Perimeter float64
	Centroid image.Point
}

// findContours finds contours in an edge image
func (d *SymbolDetector) findContours(edges *image.Gray) []Contour {
	contours := []Contour{}
	bounds := edges.Bounds()
	visited := make(map[image.Point]bool)
	
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			pt := image.Point{x, y}
			if edges.GrayAt(x, y).Y == 255 && !visited[pt] {
				contour := d.traceContour(edges, pt, visited)
				if len(contour.Points) > 10 { // Minimum contour size
					contours = append(contours, contour)
				}
			}
		}
	}
	
	return contours
}

// traceContour traces a contour from a starting point
func (d *SymbolDetector) traceContour(edges *image.Gray, start image.Point, visited map[image.Point]bool) Contour {
	contour := Contour{
		Points: []image.Point{},
	}
	
	// Simple flood fill to find connected components
	stack := []image.Point{start}
	minX, minY := start.X, start.Y
	maxX, maxY := start.X, start.Y
	
	for len(stack) > 0 {
		pt := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		
		if visited[pt] {
			continue
		}
		
		visited[pt] = true
		contour.Points = append(contour.Points, pt)
		
		// Update bounds
		if pt.X < minX { minX = pt.X }
		if pt.X > maxX { maxX = pt.X }
		if pt.Y < minY { minY = pt.Y }
		if pt.Y > maxY { maxY = pt.Y }
		
		// Check 8-connected neighbors
		for dy := -1; dy <= 1; dy++ {
			for dx := -1; dx <= 1; dx++ {
				if dx == 0 && dy == 0 {
					continue
				}
				
				nx, ny := pt.X+dx, pt.Y+dy
				npt := image.Point{nx, ny}
				
				if nx >= edges.Bounds().Min.X && nx < edges.Bounds().Max.X &&
				   ny >= edges.Bounds().Min.Y && ny < edges.Bounds().Max.Y &&
				   edges.GrayAt(nx, ny).Y == 255 && !visited[npt] {
					stack = append(stack, npt)
				}
			}
		}
	}
	
	contour.Bounds = image.Rect(minX, minY, maxX, maxY)
	contour.Area = float64(len(contour.Points))
	contour.Perimeter = d.calculatePerimeter(contour.Points)
	contour.Centroid = image.Point{
		X: (minX + maxX) / 2,
		Y: (minY + maxY) / 2,
	}
	
	return contour
}

// calculatePerimeter calculates the perimeter of a contour
func (d *SymbolDetector) calculatePerimeter(points []image.Point) float64 {
	if len(points) < 2 {
		return 0
	}
	
	perimeter := 0.0
	for i := 0; i < len(points); i++ {
		next := (i + 1) % len(points)
		dx := float64(points[next].X - points[i].X)
		dy := float64(points[next].Y - points[i].Y)
		perimeter += math.Sqrt(dx*dx + dy*dy)
	}
	
	return perimeter
}

// matchTemplate matches a contour against templates
func (d *SymbolDetector) matchTemplate(contour Contour, img *image.Gray) *Symbol {
	bounds := contour.Bounds
	width := bounds.Max.X - bounds.Min.X
	height := bounds.Max.Y - bounds.Min.Y
	
	if width < 10 || height < 10 {
		return nil
	}
	
	aspectRatio := float64(width) / float64(height)
	
	// Try to match against each template
	bestMatch := (*Symbol)(nil)
	bestConfidence := float32(0.0)
	
	for _, template := range d.templates {
		// Check size constraints
		avgSize := (width + height) / 2
		if avgSize < template.MinSize || avgSize > template.MaxSize {
			continue
		}
		
		// Check aspect ratio
		if math.Abs(aspectRatio-template.AspectRatio) > 0.5 {
			continue
		}
		
		// Extract features and calculate confidence
		features := d.extractFeatures(contour, img)
		confidence := d.calculateFeatureConfidence(features, template.Features)
		
		if confidence > bestConfidence && confidence > d.minConfidence {
			bestConfidence = confidence
			bestMatch = &Symbol{
				Type:       template.Type,
				X:          float64(bounds.Min.X),
				Y:          float64(bounds.Min.Y),
				Width:      float64(width),
				Height:     float64(height),
				Confidence: confidence,
				Features:   features,
				Properties: make(map[string]interface{}),
			}
		}
	}
	
	return bestMatch
}

// extractFeatures extracts features from a contour
func (d *SymbolDetector) extractFeatures(contour Contour, img *image.Gray) []Feature {
	features := []Feature{}
	
	// Circularity
	circularity := 4 * math.Pi * contour.Area / (contour.Perimeter * contour.Perimeter)
	features = append(features, Feature{
		Type:       "circularity",
		Value:      circularity,
		Confidence: 0.9,
	})
	
	// Compactness
	bounds := contour.Bounds
	boundingArea := float64((bounds.Max.X - bounds.Min.X) * (bounds.Max.Y - bounds.Min.Y))
	compactness := contour.Area / boundingArea
	features = append(features, Feature{
		Type:       "compactness",
		Value:      compactness,
		Confidence: 0.9,
	})
	
	// Detect specific patterns
	if d.hasArcPattern(contour, img) {
		features = append(features, Feature{
			Type:       "arc",
			Value:      1.0,
			Confidence: 0.85,
		})
	}
	
	if d.hasParallelLines(contour, img) {
		features = append(features, Feature{
			Type:       "parallel_lines",
			Value:      1.0,
			Confidence: 0.80,
		})
	}
	
	return features
}

// hasArcPattern checks if contour contains an arc pattern
func (d *SymbolDetector) hasArcPattern(contour Contour, img *image.Gray) bool {
	// Simplified arc detection
	// Check if points form a curved pattern
	if len(contour.Points) < 10 {
		return false
	}
	
	// Sample points and check curvature
	step := len(contour.Points) / 10
	angles := []float64{}
	
	for i := step; i < len(contour.Points)-step; i += step {
		p1 := contour.Points[i-step]
		p2 := contour.Points[i]
		p3 := contour.Points[i+step]
		
		angle := d.calculateAngle(p1, p2, p3)
		angles = append(angles, angle)
	}
	
	// Check if angles are consistent (indicating arc)
	if len(angles) < 3 {
		return false
	}
	
	avgAngle := 0.0
	for _, a := range angles {
		avgAngle += a
	}
	avgAngle /= float64(len(angles))
	
	variance := 0.0
	for _, a := range angles {
		variance += (a - avgAngle) * (a - avgAngle)
	}
	variance /= float64(len(angles))
	
	// Low variance in angles indicates arc
	return variance < 0.1 && avgAngle > 0.1 && avgAngle < math.Pi-0.1
}

// hasParallelLines checks for parallel lines in contour
func (d *SymbolDetector) hasParallelLines(contour Contour, img *image.Gray) bool {
	// Simplified parallel line detection
	bounds := contour.Bounds
	
	// Check for horizontal parallel lines
	lineCount := 0
	for y := bounds.Min.Y; y < bounds.Max.Y; y += 5 {
		hasLine := false
		consecutivePixels := 0
		
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			if img.GrayAt(x, y).Y == 0 { // Black pixel
				consecutivePixels++
				if consecutivePixels > (bounds.Max.X-bounds.Min.X)/2 {
					hasLine = true
					break
				}
			} else {
				consecutivePixels = 0
			}
		}
		
		if hasLine {
			lineCount++
		}
	}
	
	return lineCount >= 2
}

// calculateAngle calculates angle between three points
func (d *SymbolDetector) calculateAngle(p1, p2, p3 image.Point) float64 {
	v1x := float64(p1.X - p2.X)
	v1y := float64(p1.Y - p2.Y)
	v2x := float64(p3.X - p2.X)
	v2y := float64(p3.Y - p2.Y)
	
	dot := v1x*v2x + v1y*v2y
	det := v1x*v2y - v1y*v2x
	
	return math.Atan2(det, dot)
}

// calculateFeatureConfidence calculates confidence based on features
func (d *SymbolDetector) calculateFeatureConfidence(features []Feature, expected []FeatureDescriptor) float32 {
	if len(expected) == 0 {
		return 0.5
	}
	
	totalScore := float32(0.0)
	matchCount := 0
	
	for _, exp := range expected {
		for _, feat := range features {
			if feat.Type == exp.Type {
				// Calculate similarity
				diff := math.Abs(feat.Value - exp.Expected)
				if diff <= exp.Tolerance {
					score := float32(1.0 - diff/exp.Tolerance)
					totalScore += score * feat.Confidence
					matchCount++
				}
				break
			}
		}
	}
	
	if matchCount == 0 {
		return 0.0
	}
	
	return totalScore / float32(len(expected))
}

// detectComplexPatterns detects complex multi-element patterns
func (d *SymbolDetector) detectComplexPatterns(img, edges *image.Gray) []Symbol {
	symbols := []Symbol{}
	
	// Detect room boundaries
	rooms := d.detectRooms(edges)
	for _, room := range rooms {
		symbols = append(symbols, room)
	}
	
	// Detect wall segments
	walls := d.detectWalls(edges)
	for _, wall := range walls {
		symbols = append(symbols, wall)
	}
	
	return symbols
}

// detectRooms detects room boundaries
func (d *SymbolDetector) detectRooms(edges *image.Gray) []Symbol {
	// Simplified room detection - look for large rectangular areas
	rooms := []Symbol{}
	
	// This would use more sophisticated algorithms in production
	// such as Hough transform for line detection and
	// polygon detection for room boundaries
	
	return rooms
}

// detectWalls detects wall segments
func (d *SymbolDetector) detectWalls(edges *image.Gray) []Symbol {
	// Simplified wall detection - look for thick lines
	walls := []Symbol{}
	
	// This would use line detection algorithms
	// and pattern matching for wall patterns
	
	return walls
}

// mergeDetections merges overlapping detections
func (d *SymbolDetector) mergeDetections(symbols []Symbol) []Symbol {
	if len(symbols) <= 1 {
		return symbols
	}
	
	merged := []Symbol{}
	used := make([]bool, len(symbols))
	
	for i := 0; i < len(symbols); i++ {
		if used[i] {
			continue
		}
		
		current := symbols[i]
		group := []Symbol{current}
		
		// Find overlapping symbols
		for j := i + 1; j < len(symbols); j++ {
			if used[j] {
				continue
			}
			
			if d.overlaps(current, symbols[j]) && current.Type == symbols[j].Type {
				group = append(group, symbols[j])
				used[j] = true
			}
		}
		
		// Merge the group
		if len(group) == 1 {
			merged = append(merged, current)
		} else {
			merged = append(merged, d.mergeGroup(group))
		}
	}
	
	return merged
}

// overlaps checks if two symbols overlap
func (d *SymbolDetector) overlaps(s1, s2 Symbol) bool {
	return !(s1.X+s1.Width < s2.X || s2.X+s2.Width < s1.X ||
		s1.Y+s1.Height < s2.Y || s2.Y+s2.Height < s1.Y)
}

// mergeGroup merges a group of symbols
func (d *SymbolDetector) mergeGroup(group []Symbol) Symbol {
	if len(group) == 0 {
		return Symbol{}
	}
	
	merged := group[0]
	
	// Find bounding box
	minX, minY := merged.X, merged.Y
	maxX, maxY := merged.X+merged.Width, merged.Y+merged.Height
	totalConfidence := merged.Confidence
	
	for i := 1; i < len(group); i++ {
		s := group[i]
		if s.X < minX { minX = s.X }
		if s.Y < minY { minY = s.Y }
		if s.X+s.Width > maxX { maxX = s.X + s.Width }
		if s.Y+s.Height > maxY { maxY = s.Y + s.Height }
		totalConfidence += s.Confidence
	}
	
	merged.X = minX
	merged.Y = minY
	merged.Width = maxX - minX
	merged.Height = maxY - minY
	merged.Confidence = totalConfidence / float32(len(group))
	
	return merged
}