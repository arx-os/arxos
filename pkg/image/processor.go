// Package image provides image processing and analysis functionality
package image

import (
	"bytes"
	"compress/zlib"
	"fmt"
	"io"
	"math"

	"github.com/arxos/arxos/internal/types"
)

// Processor implements the ImageProcessor interface
type Processor struct {
	config *types.ParseConfig
}

// NewProcessor creates a new image processor
func NewProcessor() *Processor {
	return &Processor{
		config: types.DefaultParseConfig(),
	}
}

// NewProcessorWithConfig creates a new image processor with custom configuration
func NewProcessorWithConfig(config *types.ParseConfig) *Processor {
	return &Processor{
		config: config,
	}
}

// ProcessImage processes an embedded image and extracts architectural features
func (p *Processor) ProcessImage(img *types.EmbeddedImage) (*types.ProcessedImage, error) {
	if err := p.decodeImageData(img); err != nil {
		return nil, fmt.Errorf("failed to decode image data: %w", err)
	}

	// Detect edges
	edges, err := p.DetectEdges(img)
	if err != nil {
		return nil, fmt.Errorf("failed to detect edges: %w", err)
	}

	// Extract lines from edges
	lines, err := p.ExtractLines(edges)
	if err != nil {
		return nil, fmt.Errorf("failed to extract lines: %w", err)
	}

	// Detect architectural features
	features := p.detectArchitecturalFeatures(img, edges, lines)

	processedImg := &types.ProcessedImage{
		Image:    img,
		Edges:    edges,
		Lines:    lines,
		Features: features,
	}

	return processedImg, nil
}

// DetectEdges performs edge detection on the image
func (p *Processor) DetectEdges(img *types.EmbeddedImage) ([]types.Edge, error) {
	if len(img.DecodedData) == 0 {
		return nil, fmt.Errorf("no decoded image data available")
	}

	edges := []types.Edge{}
	
	width := img.Width
	height := img.Height
	pixels := img.DecodedData
	
	// Use configuration for edge detection parameters
	step := 4
	threshold := p.config.EdgeDetectionThreshold
	
	// Sobel edge detection
	for y := step; y < height-step; y += step {
		for x := step; x < width-step; x += step {
			if y*width+x >= len(pixels) || (y+step)*width+(x+step) >= len(pixels) {
				continue
			}
			
			// Sobel operators
			right := float64(pixels[y*width+(x+step)])
			down := float64(pixels[(y+step)*width+x])
			left := float64(pixels[y*width+(x-step)])
			up := float64(pixels[(y-step)*width+x])
			
			// Calculate gradients
			gradX := (right - left) / 2.0
			gradY := (down - up) / 2.0
			magnitude := math.Sqrt(gradX*gradX + gradY*gradY)
			direction := math.Atan2(gradY, gradX)
			
			if magnitude > threshold {
				edges = append(edges, types.Edge{
					X:         x,
					Y:         y,
					Strength:  magnitude,
					Direction: direction,
				})
			}
		}
	}
	
	return edges, nil
}

// ExtractLines groups edges into line segments
func (p *Processor) ExtractLines(edges []types.Edge) ([]types.Line, error) {
	if len(edges) == 0 {
		return []types.Line{}, nil
	}

	lines := []types.Line{}
	processed := make([]bool, len(edges))
	
	// Group nearby edges with similar directions into lines
	for i, edge1 := range edges {
		if processed[i] {
			continue
		}
		
		lineEdges := []types.Edge{edge1}
		processed[i] = true
		
		// Find nearby edges with similar direction
		for j, edge2 := range edges {
			if processed[j] || i == j {
				continue
			}
			
			// Calculate distance and direction similarity
			distance := math.Sqrt(float64((edge2.X-edge1.X)*(edge2.X-edge1.X) + (edge2.Y-edge1.Y)*(edge2.Y-edge1.Y)))
			directionDiff := math.Abs(edge2.Direction - edge1.Direction)
			
			// Adjust for circular nature of angles
			if directionDiff > math.Pi {
				directionDiff = 2*math.Pi - directionDiff
			}
			
			if distance < 60 && directionDiff < 0.3 {
				lineEdges = append(lineEdges, edge2)
				processed[j] = true
			}
		}
		
		// Create line from clustered edges if we have enough points
		if len(lineEdges) >= 3 {
			line := p.createLineFromEdges(lineEdges)
			
			// Filter lines by length (architectural significance)
			if line.Length > 100 { // Minimum line length for architectural features
				lines = append(lines, line)
			}
		}
	}
	
	return lines, nil
}

// decodeImageData decodes compressed image data
func (p *Processor) decodeImageData(img *types.EmbeddedImage) error {
	if len(img.RawData) == 0 {
		return fmt.Errorf("no raw image data to decode")
	}

	switch img.Filter {
	case "FlateDecode":
		return p.decodeFlateDecode(img)
	case "DCTDecode":
		// JPEG decoding would go here
		return fmt.Errorf("DCTDecode not yet implemented")
	case "LZWDecode":
		// LZW decoding would go here
		return fmt.Errorf("LZWDecode not yet implemented")
	case "":
		// No compression
		img.DecodedData = img.RawData
		return nil
	default:
		return fmt.Errorf("unsupported filter: %s", img.Filter)
	}
}

// decodeFlateDecode decodes FlateDecode (zlib) compressed data
func (p *Processor) decodeFlateDecode(img *types.EmbeddedImage) error {
	reader, err := zlib.NewReader(bytes.NewReader(img.RawData))
	if err != nil {
		return fmt.Errorf("failed to create zlib reader: %w", err)
	}
	defer reader.Close()
	
	decodedData, err := io.ReadAll(reader)
	if err != nil {
		return fmt.Errorf("failed to decode zlib data: %w", err)
	}
	
	img.DecodedData = decodedData
	return nil
}

// createLineFromEdges creates a line segment from a group of edges
func (p *Processor) createLineFromEdges(edges []types.Edge) types.Line {
	if len(edges) == 0 {
		return types.Line{}
	}
	
	// Find bounding box of edges
	minX, minY := edges[0].X, edges[0].Y
	maxX, maxY := edges[0].X, edges[0].Y
	totalStrength := 0.0
	
	for _, edge := range edges {
		if edge.X < minX { minX = edge.X }
		if edge.X > maxX { maxX = edge.X }
		if edge.Y < minY { minY = edge.Y }
		if edge.Y > maxY { maxY = edge.Y }
		totalStrength += edge.Strength
	}
	
	// Calculate line properties
	length := math.Sqrt(float64((maxX-minX)*(maxX-minX) + (maxY-minY)*(maxY-minY)))
	angle := math.Atan2(float64(maxY-minY), float64(maxX-minX))
	weight := totalStrength / float64(len(edges))
	
	return types.Line{
		X1:     minX,
		Y1:     minY,
		X2:     maxX,
		Y2:     maxY,
		Length: length,
		Angle:  angle,
		Weight: weight,
	}
}

// detectArchitecturalFeatures identifies architectural features from image analysis
func (p *Processor) detectArchitecturalFeatures(img *types.EmbeddedImage, edges []types.Edge, lines []types.Line) []types.ImageFeature {
	features := []types.ImageFeature{}
	
	// Detect potential rooms from line patterns
	roomFeatures := p.detectRoomFeatures(lines)
	features = append(features, roomFeatures...)
	
	// Detect wall features
	wallFeatures := p.detectWallFeatures(lines)
	features = append(features, wallFeatures...)
	
	return features
}

// detectRoomFeatures identifies potential room areas from lines
func (p *Processor) detectRoomFeatures(lines []types.Line) []types.ImageFeature {
	features := []types.ImageFeature{}
	
	// Look for rectangular patterns in lines
	for i := 0; i < len(lines) && i < 20; i++ { // Limit analysis for performance
		line1 := lines[i]
		
		// Only consider significant lines
		if line1.Length < 200 {
			continue
		}
		
		for j := i + 1; j < len(lines) && j < 40; j++ {
			line2 := lines[j]
			
			if line2.Length < 200 {
				continue
			}
			
			// Check if lines could form part of a rectangle
			angleDiff := math.Abs(line1.Angle - line2.Angle)
			
			// Lines should be roughly perpendicular
			if angleDiff > math.Pi/4 && angleDiff < 3*math.Pi/4 {
				// Create potential room feature
				minX := minInt(line1.X1, minInt(line1.X2, minInt(line2.X1, line2.X2)))
				minY := minInt(line1.Y1, minInt(line1.Y2, minInt(line2.Y1, line2.Y2)))
				maxX := maxInt(line1.X1, maxInt(line1.X2, maxInt(line2.X1, line2.X2)))
				maxY := maxInt(line1.Y1, maxInt(line1.Y2, maxInt(line2.Y1, line2.Y2)))
				
				width := maxX - minX
				height := maxY - minY
				
				// Filter by reasonable room dimensions
				if width > 100 && height > 100 && width < 800 && height < 600 {
					feature := types.ImageFeature{
						Type: "room",
						Bounds: types.Rect{
							X:      minX,
							Y:      minY,
							Width:  width,
							Height: height,
						},
						Metadata: map[string]interface{}{
							"line1_length": line1.Length,
							"line2_length": line2.Length,
							"confidence":   (line1.Weight + line2.Weight) / 2.0,
						},
					}
					features = append(features, feature)
				}
			}
		}
	}
	
	return features
}

// detectWallFeatures identifies wall segments
func (p *Processor) detectWallFeatures(lines []types.Line) []types.ImageFeature {
	features := []types.ImageFeature{}
	
	for _, line := range lines {
		// Only consider lines long enough to be walls
		if line.Length > 150 {
			feature := types.ImageFeature{
				Type: "wall",
				Bounds: types.Rect{
					X:      minInt(line.X1, line.X2),
					Y:      minInt(line.Y1, line.Y2),
					Width:  absInt(line.X2 - line.X1),
					Height: absInt(line.Y2 - line.Y1),
				},
				Metadata: map[string]interface{}{
					"length":     line.Length,
					"angle":      line.Angle,
					"weight":     line.Weight,
					"x1":         line.X1,
					"y1":         line.Y1,
					"x2":         line.X2,
					"y2":         line.Y2,
				},
			}
			features = append(features, feature)
		}
	}
	
	return features
}

// Utility functions
func minInt(a, b int) int {
	if a < b { return a }
	return b
}

func maxInt(a, b int) int {
	if a > b { return a }
	return b
}

func absInt(a int) int {
	if a < 0 { return -a }
	return a
}