package ascii

import (
	"strings"
	"testing"
)

// TestPixatoolRendererCreation tests creation of Pixatool renderer
func TestPixatoolRendererCreation(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	// Test default settings
	if !pr.AntiAlias {
		t.Error("AntiAlias should be enabled by default")
	}
	if !pr.UseSmartClustering {
		t.Error("Smart clustering should be enabled by default")
	}
	if !pr.EdgeEnhancement {
		t.Error("Edge enhancement should be enabled by default")
	}
	if pr.ContrastBoost != 1.2 {
		t.Errorf("Expected contrast boost 1.2, got %v", pr.ContrastBoost)
	}
	
	// Test density gradient
	if len(pr.DensityGradient) != 9 {
		t.Errorf("Expected 9 density levels, got %d", len(pr.DensityGradient))
	}
	
	// Test material characters
	materials := []string{"concrete", "steel", "glass", "wood", "brick", "circuit", "chip"}
	for _, mat := range materials {
		if _, exists := pr.MaterialChars[mat]; !exists {
			t.Errorf("Missing material characters for %s", mat)
		}
	}
	
	// Test dithering patterns
	patterns := []string{"checkerboard", "diagonal", "dots", "gradient", "noise"}
	for _, pattern := range patterns {
		if _, exists := pr.DitheringPatterns[pattern]; !exists {
			t.Errorf("Missing dithering pattern for %s", pattern)
		}
	}
}

// TestEdgeDetection tests edge detection algorithm
func TestEdgeDetection(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	// Create test canvas with clear edge
	canvas := [][]rune{
		{' ', ' ', ' ', ' ', ' '},
		{' ', '█', '█', '█', ' '},
		{' ', '█', ' ', '█', ' '},
		{' ', '█', '█', '█', ' '},
		{' ', ' ', ' ', ' ', ' '},
	}
	
	// Test edge detection at corner
	isEdge := pr.isEdgePixel(canvas, 1, 1, 5, 5)
	if !isEdge {
		t.Error("Corner should be detected as edge")
	}
	
	// Test non-edge (center of solid area)
	canvas2 := [][]rune{
		{'█', '█', '█'},
		{'█', '█', '█'},
		{'█', '█', '█'},
	}
	isEdge = pr.isEdgePixel(canvas2, 1, 1, 3, 3)
	if isEdge {
		t.Error("Center of solid area should not be edge")
	}
	
	// Test empty space
	isEdge = pr.isEdgePixel(canvas, 0, 0, 5, 5)
	if isEdge {
		t.Error("Empty space should not be edge")
	}
}

// TestEdgeCharacterSelection tests proper edge character selection
func TestEdgeCharacterSelection(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	testCases := []struct {
		name     string
		canvas   [][]rune
		x, y     int
		expected rune
	}{
		{
			name: "Horizontal line",
			canvas: [][]rune{
				{' ', ' ', ' '},
				{'█', '█', '█'},
				{' ', ' ', ' '},
			},
			x: 1, y: 1,
			expected: pr.EdgeChars.Horizontal,
		},
		{
			name: "Vertical line",
			canvas: [][]rune{
				{' ', '█', ' '},
				{' ', '█', ' '},
				{' ', '█', ' '},
			},
			x: 1, y: 1,
			expected: pr.EdgeChars.Vertical,
		},
		{
			name: "Cross junction",
			canvas: [][]rune{
				{' ', '█', ' '},
				{'█', '█', '█'},
				{' ', '█', ' '},
			},
			x: 1, y: 1,
			expected: pr.EdgeChars.Cross,
		},
		{
			name: "Top-left corner",
			canvas: [][]rune{
				{' ', ' ', ' '},
				{' ', '█', '█'},
				{' ', '█', ' '},
			},
			x: 1, y: 1,
			expected: pr.EdgeChars.TopLeft,
		},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			char := pr.selectEdgeChar(tc.canvas, tc.x, tc.y, 3, 3)
			if char != tc.expected {
				t.Errorf("Expected character %c, got %c", tc.expected, char)
			}
		})
	}
}

// TestCharDensity tests character density calculations
func TestCharDensity(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	testCases := []struct {
		char     rune
		expected float64
	}{
		{' ', 0.0},
		{'█', 1.0},
		{'▓', 0.75},
		{'▒', 0.5},
		{'░', 0.25},
		{'·', 0.125}, // From density gradient
	}
	
	for _, tc := range testCases {
		density := pr.getCharDensity(tc.char)
		if density < tc.expected-0.01 || density > tc.expected+0.01 {
			t.Errorf("Character %c: expected density %v, got %v", 
				tc.char, tc.expected, density)
		}
	}
}

// TestDensityToChar tests density to character mapping
func TestDensityToChar(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	testCases := []struct {
		density  float64
		expected rune
	}{
		{0.0, ' '},
		{0.125, '·'},
		{0.5, '+'},
		{1.0, '█'},
		{-0.5, ' '},  // Test clamping
		{1.5, '█'},   // Test clamping
	}
	
	for _, tc := range testCases {
		char := pr.getDensityChar(tc.density)
		if char != tc.expected {
			t.Errorf("Density %v: expected character %c, got %c", 
				tc.density, tc.expected, char)
		}
	}
}

// TestAntiAliasing tests anti-aliasing functionality
func TestAntiAliasing(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	// Create canvas with sharp transition
	canvas := [][]rune{
		{'█', '█', '█', ' ', ' '},
		{'█', '█', '█', ' ', ' '},
		{'█', '█', '█', ' ', ' '},
	}
	
	// Check that sharp transition is detected
	needsAA := pr.needsAntiAliasing(canvas, 2, 1, 5, 3)
	if !needsAA {
		t.Error("Sharp transition should need anti-aliasing")
	}
	
	// Check that uniform area doesn't need AA
	needsAA = pr.needsAntiAliasing(canvas, 1, 1, 5, 3)
	if needsAA {
		t.Error("Uniform area should not need anti-aliasing")
	}
}

// TestSmartClustering tests character clustering
func TestSmartClustering(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	// Create canvas with mixed densities
	canvas := [][]rune{
		{'▓', '▓', '▒'},
		{'▓', '█', '▒'},
		{'▓', '▓', '░'},
	}
	
	// Apply clustering
	result := pr.applySmartClustering(canvas, 3, 3)
	
	// Center should be averaged
	centerChar := result[1][1]
	centerDensity := pr.getCharDensity(centerChar)
	
	// Should be between 0.5 and 0.75 (average of surrounding)
	if centerDensity < 0.5 || centerDensity > 0.8 {
		t.Errorf("Clustering produced unexpected density: %v", centerDensity)
	}
}

// TestContrastAdjustment tests contrast boost
func TestContrastAdjustment(t *testing.T) {
	pr := NewPixatoolRenderer()
	pr.ContrastBoost = 1.5
	
	// Create canvas with mid-tones
	canvas := [][]rune{
		{'▒', '▒', '▒'},
		{'▒', '▒', '▒'},
		{'▒', '▒', '▒'},
	}
	
	result := pr.adjustContrast(canvas, 3, 3)
	
	// All characters should be adjusted
	for y := 0; y < 3; y++ {
		for x := 0; x < 3; x++ {
			if result[y][x] == canvas[y][x] {
				t.Error("Contrast adjustment had no effect")
			}
		}
	}
}

// TestDithering tests dithering application
func TestDithering(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	// Create canvas with gradient
	canvas := [][]rune{
		{'░', '░', '▒', '▒'},
		{'░', '░', '▒', '▒'},
		{'▒', '▒', '▓', '▓'},
		{'▒', '▒', '▓', '▓'},
	}
	
	result := pr.applyDithering(canvas, 4, 4)
	
	// Check that mid-tones are dithered
	changed := false
	for y := 0; y < 4; y++ {
		for x := 0; x < 4; x++ {
			if result[y][x] != canvas[y][x] {
				changed = true
				break
			}
		}
	}
	
	if !changed {
		t.Error("Dithering should modify mid-tone areas")
	}
}

// TestMaterialRendering tests material-specific texture rendering
func TestMaterialRendering(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	materials := []string{"concrete", "steel", "glass", "wood", "brick"}
	
	for _, material := range materials {
		t.Run(material, func(t *testing.T) {
			// Create blank canvas
			canvas := make([][]rune, 5)
			for i := range canvas {
				canvas[i] = make([]rune, 5)
				for j := range canvas[i] {
					canvas[i][j] = ' '
				}
			}
			
			// Apply material
			pr.RenderWithMaterial(canvas, material, 0, 0, 5, 5)
			
			// Check that material was applied
			nonEmpty := 0
			for y := 0; y < 5; y++ {
				for x := 0; x < 5; x++ {
					if canvas[y][x] != ' ' {
						nonEmpty++
					}
				}
			}
			
			if nonEmpty == 0 {
				t.Errorf("Material %s did not render any characters", material)
			}
		})
	}
}

// TestGenerateTextureString tests texture string generation
func TestGenerateTextureString(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	materials := []string{"concrete", "circuit", "water"}
	
	for _, material := range materials {
		texture := pr.GenerateTextureString(material, 10, 5)
		
		// Check dimensions
		lines := strings.Split(strings.TrimRight(texture, "\n"), "\n")
		if len(lines) != 5 {
			t.Errorf("Material %s: expected 5 lines, got %d", material, len(lines))
		}
		
		// Check that it contains material-specific characters
		chars := pr.MaterialChars[material]
		found := false
		for _, char := range chars {
			if strings.ContainsRune(texture, char) {
				found = true
				break
			}
		}
		
		if !found {
			t.Errorf("Material %s texture doesn't contain expected characters", material)
		}
	}
}

// TestOptimizeCanvas tests the full optimization pipeline
func TestOptimizeCanvas(t *testing.T) {
	pr := NewPixatoolRenderer()
	
	// Create test canvas
	canvas := [][]rune{
		{' ', ' ', '█', '█', '█', ' ', ' '},
		{' ', '█', '▓', '▓', '▓', '█', ' '},
		{'█', '▓', '▒', '░', '▒', '▓', '█'},
		{'█', '▓', '░', ' ', '░', '▓', '█'},
		{'█', '▓', '▒', '░', '▒', '▓', '█'},
		{' ', '█', '▓', '▓', '▓', '█', ' '},
		{' ', ' ', '█', '█', '█', ' ', ' '},
	}
	
	// Apply optimizations
	result := pr.OptimizeCanvas(canvas, 7, 7)
	
	// Result should be different from input
	different := false
	for y := 0; y < 7; y++ {
		for x := 0; x < 7; x++ {
			if result[y][x] != canvas[y][x] {
				different = true
				break
			}
		}
		if different {
			break
		}
	}
	
	if !different {
		t.Error("Optimization had no effect on canvas")
	}
	
	// Result should have same dimensions
	if len(result) != 7 {
		t.Errorf("Expected 7 rows, got %d", len(result))
	}
	for i, row := range result {
		if len(row) != 7 {
			t.Errorf("Row %d: expected 7 columns, got %d", i, len(row))
		}
	}
}

// BenchmarkEdgeDetection benchmarks edge detection performance
func BenchmarkEdgeDetection(b *testing.B) {
	pr := NewPixatoolRenderer()
	
	// Create large canvas
	canvas := make([][]rune, 100)
	for i := range canvas {
		canvas[i] = make([]rune, 100)
		for j := range canvas[i] {
			if i%10 == 0 || j%10 == 0 {
				canvas[i][j] = '█'
			} else {
				canvas[i][j] = ' '
			}
		}
	}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		_ = pr.detectAndEnhanceEdges(canvas, 100, 100)
	}
}

// BenchmarkOptimizeCanvas benchmarks full optimization pipeline
func BenchmarkOptimizeCanvas(b *testing.B) {
	pr := NewPixatoolRenderer()
	
	// Create realistic canvas
	canvas := make([][]rune, 80)
	for i := range canvas {
		canvas[i] = make([]rune, 40)
		for j := range canvas[i] {
			// Create pattern
			if i%5 == 0 {
				canvas[i][j] = '█'
			} else if j%3 == 0 {
				canvas[i][j] = '▓'
			} else {
				canvas[i][j] = '░'
			}
		}
	}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		_ = pr.OptimizeCanvas(canvas, 80, 40)
	}
}