// Package ascii provides Pixatool-inspired ASCII rendering optimizations
package ascii

import (
	"math"
	"strings"
)

// PixatoolRenderer implements advanced ASCII art generation techniques
// inspired by Pixatool for optimal visual clarity
type PixatoolRenderer struct {
	// Character gradients for different density levels
	DensityGradient []rune
	
	// Edge detection characters
	EdgeChars struct {
		Horizontal     rune
		Vertical       rune
		TopLeft        rune
		TopRight       rune
		BottomLeft     rune
		BottomRight    rune
		Cross          rune
		TeeUp          rune
		TeeDown        rune
		TeeLeft        rune
		TeeRight       rune
	}
	
	// Material-specific character sets
	MaterialChars map[string][]rune
	
	// Dithering patterns for textures
	DitheringPatterns map[string][][]rune
	
	// Anti-aliasing for smooth edges
	AntiAlias bool
	
	// Optimization settings
	UseSmartClustering bool
	EdgeEnhancement    bool
	ContrastBoost      float64
}

// NewPixatoolRenderer creates an optimized renderer
func NewPixatoolRenderer() *PixatoolRenderer {
	pr := &PixatoolRenderer{
		AntiAlias:          true,
		UseSmartClustering: true,
		EdgeEnhancement:    true,
		ContrastBoost:      1.2,
	}
	
	// Initialize density gradient (from light to dark)
	pr.DensityGradient = []rune{
		' ', '·', ':', '-', '=', '+', '*', '#', '█',
	}
	
	// Initialize edge characters (box drawing)
	pr.EdgeChars.Horizontal = '─'
	pr.EdgeChars.Vertical = '│'
	pr.EdgeChars.TopLeft = '┌'
	pr.EdgeChars.TopRight = '┐'
	pr.EdgeChars.BottomLeft = '└'
	pr.EdgeChars.BottomRight = '┘'
	pr.EdgeChars.Cross = '┼'
	pr.EdgeChars.TeeUp = '┴'
	pr.EdgeChars.TeeDown = '┬'
	pr.EdgeChars.TeeLeft = '┤'
	pr.EdgeChars.TeeRight = '├'
	
	// Initialize material-specific characters
	pr.MaterialChars = map[string][]rune{
		"concrete": {'█', '▓', '▒', '░'},
		"steel":    {'╬', '╫', '╪', '┼'},
		"glass":    {'═', '─', '╌', '┈'},
		"wood":     {'▓', '≡', '═', '─'},
		"brick":    {'▚', '▞', '▓', '█'},
		"tile":     {'▦', '▤', '▥', '▧'},
		"carpet":   {'░', '▒', '·', '∙'},
		"mesh":     {'╬', '┼', '+', '×'},
		"water":    {'≈', '~', '∽', '∼'},
		"grass":    {'ψ', 'Ψ', '¥', '√'},
		"circuit":  {'─', '│', '┼', '●'},
		"chip":     {'▪', '▫', '□', '▢'},
	}
	
	// Initialize dithering patterns for textures
	pr.DitheringPatterns = map[string][][]rune{
		"checkerboard": {
			{'█', ' '},
			{' ', '█'},
		},
		"diagonal": {
			{'╱', '╲'},
			{'╲', '╱'},
		},
		"dots": {
			{'·', ' ', '·'},
			{' ', '·', ' '},
			{'·', ' ', '·'},
		},
		"gradient": {
			{'█', '▓', '▒', '░'},
		},
		"noise": {
			{'·', ':', '∙', ' '},
			{'∙', ' ', '·', ':'},
			{' ', '∙', ':', '·'},
			{':', '·', ' ', '∙'},
		},
	}
	
	return pr
}

// OptimizeCanvas applies Pixatool-inspired optimizations to raw canvas
func (pr *PixatoolRenderer) OptimizeCanvas(canvas [][]rune, width, height int) [][]rune {
	// Step 1: Edge detection and enhancement
	if pr.EdgeEnhancement {
		canvas = pr.detectAndEnhanceEdges(canvas, width, height)
	}
	
	// Step 2: Smart clustering for similar regions
	if pr.UseSmartClustering {
		canvas = pr.applySmartClustering(canvas, width, height)
	}
	
	// Step 3: Anti-aliasing for smooth transitions
	if pr.AntiAlias {
		canvas = pr.applyAntiAliasing(canvas, width, height)
	}
	
	// Step 4: Contrast adjustment
	if pr.ContrastBoost != 1.0 {
		canvas = pr.adjustContrast(canvas, width, height)
	}
	
	// Step 5: Apply dithering for gradients
	canvas = pr.applyDithering(canvas, width, height)
	
	return canvas
}

// detectAndEnhanceEdges finds and emphasizes edges in the ASCII art
func (pr *PixatoolRenderer) detectAndEnhanceEdges(canvas [][]rune, width, height int) [][]rune {
	result := make([][]rune, height)
	for i := range result {
		result[i] = make([]rune, width)
		copy(result[i], canvas[i])
	}
	
	for y := 1; y < height-1; y++ {
		for x := 1; x < width-1; x++ {
			if pr.isEdgePixel(canvas, x, y, width, height) {
				result[y][x] = pr.selectEdgeChar(canvas, x, y, width, height)
			}
		}
	}
	
	return result
}

// isEdgePixel detects if a pixel is on an edge
func (pr *PixatoolRenderer) isEdgePixel(canvas [][]rune, x, y, width, height int) bool {
	center := canvas[y][x]
	if center == ' ' {
		return false
	}
	
	// Check neighbors for differences
	differences := 0
	for dy := -1; dy <= 1; dy++ {
		for dx := -1; dx <= 1; dx++ {
			if dx == 0 && dy == 0 {
				continue
			}
			nx, ny := x+dx, y+dy
			if nx >= 0 && nx < width && ny >= 0 && ny < height {
				if canvas[ny][nx] != center {
					differences++
				}
			}
		}
	}
	
	return differences >= 3 // Edge if 3+ neighbors are different
}

// selectEdgeChar chooses the appropriate edge character
func (pr *PixatoolRenderer) selectEdgeChar(canvas [][]rune, x, y, width, height int) rune {
	// Analyze connectivity in 4 directions
	top := y > 0 && canvas[y-1][x] != ' '
	bottom := y < height-1 && canvas[y+1][x] != ' '
	left := x > 0 && canvas[y][x-1] != ' '
	right := x < width-1 && canvas[y][x+1] != ' '
	
	// Select appropriate box drawing character
	connections := 0
	if top {
		connections++
	}
	if bottom {
		connections++
	}
	if left {
		connections++
	}
	if right {
		connections++
	}
	
	switch connections {
	case 4:
		return pr.EdgeChars.Cross
	case 3:
		if !top {
			return pr.EdgeChars.TeeUp
		} else if !bottom {
			return pr.EdgeChars.TeeDown
		} else if !left {
			return pr.EdgeChars.TeeLeft
		} else {
			return pr.EdgeChars.TeeRight
		}
	case 2:
		if top && bottom {
			return pr.EdgeChars.Vertical
		} else if left && right {
			return pr.EdgeChars.Horizontal
		} else if top && right {
			return pr.EdgeChars.BottomLeft
		} else if top && left {
			return pr.EdgeChars.BottomRight
		} else if bottom && right {
			return pr.EdgeChars.TopLeft
		} else {
			return pr.EdgeChars.TopRight
		}
	case 1:
		if top || bottom {
			return pr.EdgeChars.Vertical
		} else {
			return pr.EdgeChars.Horizontal
		}
	default:
		return canvas[y][x]
	}
}

// applySmartClustering groups similar characters for cleaner appearance
func (pr *PixatoolRenderer) applySmartClustering(canvas [][]rune, width, height int) [][]rune {
	result := make([][]rune, height)
	for i := range result {
		result[i] = make([]rune, width)
		copy(result[i], canvas[i])
	}
	
	// Group similar density regions
	for y := 1; y < height-1; y++ {
		for x := 1; x < width-1; x++ {
			result[y][x] = pr.clusterChar(canvas, x, y, width, height)
		}
	}
	
	return result
}

// clusterChar determines the best character based on neighboring density
func (pr *PixatoolRenderer) clusterChar(canvas [][]rune, x, y, width, height int) rune {
	// Calculate average density in 3x3 region
	densitySum := 0.0
	count := 0
	
	for dy := -1; dy <= 1; dy++ {
		for dx := -1; dx <= 1; dx++ {
			nx, ny := x+dx, y+dy
			if nx >= 0 && nx < width && ny >= 0 && ny < height {
				densitySum += pr.getCharDensity(canvas[ny][nx])
				count++
			}
		}
	}
	
	avgDensity := densitySum / float64(count)
	return pr.getDensityChar(avgDensity)
}

// applyAntiAliasing smooths transitions between different regions
func (pr *PixatoolRenderer) applyAntiAliasing(canvas [][]rune, width, height int) [][]rune {
	result := make([][]rune, height)
	for i := range result {
		result[i] = make([]rune, width)
		copy(result[i], canvas[i])
	}
	
	for y := 1; y < height-1; y++ {
		for x := 1; x < width-1; x++ {
			if pr.needsAntiAliasing(canvas, x, y, width, height) {
				result[y][x] = pr.getAntiAliasChar(canvas, x, y, width, height)
			}
		}
	}
	
	return result
}

// needsAntiAliasing checks if a pixel needs smoothing
func (pr *PixatoolRenderer) needsAntiAliasing(canvas [][]rune, x, y, width, height int) bool {
	center := pr.getCharDensity(canvas[y][x])
	
	// Check for sharp transitions
	maxDiff := 0.0
	for dy := -1; dy <= 1; dy++ {
		for dx := -1; dx <= 1; dx++ {
			if dx == 0 && dy == 0 {
				continue
			}
			nx, ny := x+dx, y+dy
			if nx >= 0 && nx < width && ny >= 0 && ny < height {
				diff := math.Abs(center - pr.getCharDensity(canvas[ny][nx]))
				if diff > maxDiff {
					maxDiff = diff
				}
			}
		}
	}
	
	return maxDiff > 0.3 // Threshold for sharp transition
}

// getAntiAliasChar returns a smoothed character
func (pr *PixatoolRenderer) getAntiAliasChar(canvas [][]rune, x, y, width, height int) rune {
	// Bilinear interpolation of surrounding densities
	densitySum := 0.0
	weightSum := 0.0
	
	for dy := -1; dy <= 1; dy++ {
		for dx := -1; dx <= 1; dx++ {
			nx, ny := x+dx, y+dy
			if nx >= 0 && nx < width && ny >= 0 && ny < height {
				weight := 1.0 / (1.0 + math.Abs(float64(dx)) + math.Abs(float64(dy)))
				densitySum += pr.getCharDensity(canvas[ny][nx]) * weight
				weightSum += weight
			}
		}
	}
	
	smoothDensity := densitySum / weightSum
	return pr.getDensityChar(smoothDensity)
}

// adjustContrast enhances visual contrast
func (pr *PixatoolRenderer) adjustContrast(canvas [][]rune, width, height int) [][]rune {
	result := make([][]rune, height)
	for i := range result {
		result[i] = make([]rune, width)
	}
	
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			density := pr.getCharDensity(canvas[y][x])
			// Apply contrast curve
			adjusted := math.Pow(density, 1.0/pr.ContrastBoost)
			result[y][x] = pr.getDensityChar(adjusted)
		}
	}
	
	return result
}

// applyDithering adds texture patterns for gradients
func (pr *PixatoolRenderer) applyDithering(canvas [][]rune, width, height int) [][]rune {
	// Apply ordered dithering for smooth gradients
	ditherMatrix := [][]float64{
		{0, 8, 2, 10},
		{12, 4, 14, 6},
		{3, 11, 1, 9},
		{15, 7, 13, 5},
	}
	
	result := make([][]rune, height)
	for i := range result {
		result[i] = make([]rune, width)
		copy(result[i], canvas[i])
	}
	
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			density := pr.getCharDensity(canvas[y][x])
			if density > 0.1 && density < 0.9 {
				// Apply dithering to mid-tones
				threshold := ditherMatrix[y%4][x%4] / 16.0
				if density < threshold {
					result[y][x] = pr.getDensityChar(density - 0.1)
				} else {
					result[y][x] = pr.getDensityChar(density + 0.1)
				}
			}
		}
	}
	
	return result
}

// RenderWithMaterial applies material-specific textures
func (pr *PixatoolRenderer) RenderWithMaterial(canvas [][]rune, material string, x, y, width, height int) {
	chars, exists := pr.MaterialChars[material]
	if !exists {
		return // Unknown material
	}
	
	// Apply material texture pattern
	pattern, hasPattern := pr.DitheringPatterns[material]
	
	for dy := 0; dy < height; dy++ {
		for dx := 0; dx < width; dx++ {
			canvasX, canvasY := x+dx, y+dy
			if canvasX >= 0 && canvasX < len(canvas[0]) && canvasY >= 0 && canvasY < len(canvas) {
				if hasPattern {
					// Use pattern
					patternX := dx % len(pattern[0])
					patternY := dy % len(pattern)
					canvas[canvasY][canvasX] = pattern[patternY][patternX]
				} else {
					// Use material character based on position
					charIndex := (dx + dy) % len(chars)
					canvas[canvasY][canvasX] = chars[charIndex]
				}
			}
		}
	}
}

// Helper functions

func (pr *PixatoolRenderer) getCharDensity(ch rune) float64 {
	// Map character to density value 0.0 to 1.0
	for i, gradChar := range pr.DensityGradient {
		if ch == gradChar {
			return float64(i) / float64(len(pr.DensityGradient)-1)
		}
	}
	
	// Special cases
	switch ch {
	case ' ':
		return 0.0
	case '█':
		return 1.0
	case '▓':
		return 0.75
	case '▒':
		return 0.5
	case '░':
		return 0.25
	default:
		return 0.5 // Default medium density
	}
}

func (pr *PixatoolRenderer) getDensityChar(density float64) rune {
	// Clamp density to valid range
	if density < 0 {
		density = 0
	} else if density > 1 {
		density = 1
	}
	
	// Map density to character
	index := int(density * float64(len(pr.DensityGradient)-1))
	return pr.DensityGradient[index]
}

// GenerateTextureString creates a texture pattern string
func (pr *PixatoolRenderer) GenerateTextureString(material string, width, height int) string {
	canvas := make([][]rune, height)
	for i := range canvas {
		canvas[i] = make([]rune, width)
		for j := range canvas[i] {
			canvas[i][j] = ' '
		}
	}
	
	pr.RenderWithMaterial(canvas, material, 0, 0, width, height)
	
	var result strings.Builder
	for _, row := range canvas {
		result.WriteString(string(row))
		result.WriteRune('\n')
	}
	
	return result.String()
}