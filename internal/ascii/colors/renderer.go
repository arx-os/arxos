package colors

import (
	"strings"

	"github.com/joelpate/arxos/pkg/models"
)

// EnhancedRenderer provides 256-color terminal rendering
type EnhancedRenderer struct {
	palette       *Palette
	Width         int  // Exported for external access
	Height        int  // Exported for external access
	buffer        [][]rune
	colorBuffer   [][]Color256
	useColors     bool
	showGradients bool
}

// NewEnhancedRenderer creates a renderer with 256-color support
func NewEnhancedRenderer(width, height int, mode PaletteMode) *EnhancedRenderer {
	r := &EnhancedRenderer{
		palette:       NewPalette(mode),
		Width:         width,
		Height:        height,
		buffer:        make([][]rune, height),
		colorBuffer:   make([][]Color256, height),
		useColors:     SupportsColor256(),
		showGradients: true,
	}
	
	// Initialize buffers
	for i := range r.buffer {
		r.buffer[i] = make([]rune, width)
		r.colorBuffer[i] = make([]Color256, width)
		for j := range r.buffer[i] {
			r.buffer[i][j] = ' '
			r.colorBuffer[i][j] = r.palette.Background
		}
	}
	
	return r
}

// Clear clears both buffers
func (r *EnhancedRenderer) Clear() {
	for i := range r.buffer {
		for j := range r.buffer[i] {
			r.buffer[i][j] = ' '
			r.colorBuffer[i][j] = r.palette.Background
		}
	}
}

// SetPixel sets a colored pixel
func (r *EnhancedRenderer) SetPixel(x, y int, ch rune, color Color256) {
	if x >= 0 && x < r.Width && y >= 0 && y < r.Height {
		r.buffer[y][x] = ch
		r.colorBuffer[y][x] = color
	}
}

// DrawGradientLine draws a line with color gradient
func (r *EnhancedRenderer) DrawGradientLine(x1, y1, x2, y2 int, startColor, endColor Color256, symbol rune) {
	// Calculate line length
	dx := abs(x2 - x1)
	dy := abs(y2 - y1)
	steps := max(dx, dy)
	
	if steps == 0 {
		r.SetPixel(x1, y1, symbol, startColor)
		return
	}
	
	// Generate gradient
	gradient := Gradient(startColor, endColor, steps+1)
	
	// Bresenham's line algorithm with gradient
	sx := 1
	sy := 1
	if x1 > x2 {
		sx = -1
	}
	if y1 > y2 {
		sy = -1
	}
	
	err := dx - dy
	step := 0
	
	for {
		// Set pixel with gradient color
		if step < len(gradient) {
			r.SetPixel(x1, y1, symbol, gradient[step])
		} else {
			r.SetPixel(x1, y1, symbol, endColor)
		}
		
		if x1 == x2 && y1 == y2 {
			break
		}
		
		e2 := 2 * err
		if e2 > -dy {
			err -= dy
			x1 += sx
		}
		if e2 < dx {
			err += dx
			y1 += sy
		}
		step++
	}
}

// DrawEnergyFlow draws animated energy flow with gradient
func (r *EnhancedRenderer) DrawEnergyFlow(path []models.Point, energyLevel float64, frame int) {
	if len(path) < 2 {
		return
	}
	
	// Get color based on energy level
	color := r.palette.GetEnergyColor(energyLevel)
	
	// Animated flow effect
	animOffset := frame % len(path)
	
	for i := 0; i < len(path)-1; i++ {
		// Calculate animated intensity
		intensity := (i + animOffset) % len(path)
		animColor := Color256(uint8(color) - uint8(intensity%8))
		
		// Draw segment
		r.DrawGradientLine(
			int(path[i].X), int(path[i].Y),
			int(path[i+1].X), int(path[i+1].Y),
			animColor, color,
			'═',
		)
	}
}

// DrawTemperatureMap draws a temperature heatmap
func (r *EnhancedRenderer) DrawTemperatureMap(temps [][]float64) {
	if len(temps) == 0 {
		return
	}
	
	for y := range temps {
		if y >= r.Height {
			break
		}
		for x := range temps[y] {
			if x >= r.Width {
				break
			}
			
			temp := temps[y][x]
			color := r.palette.GetTemperatureColor(temp)
			
			// Use different symbols for temperature ranges
			var symbol rune
			if temp < 15 {
				symbol = '░'
			} else if temp < 25 {
				symbol = '▒'
			} else {
				symbol = '▓'
			}
			
			r.SetPixel(x, y, symbol, color)
		}
	}
}

// DrawEquipment draws equipment with appropriate colors
func (r *EnhancedRenderer) DrawEquipment(equip models.Equipment) {
	color := r.palette.GetEquipmentColor(equip.Type, string(equip.Status))
	
	// Get symbol for equipment type
	symbol := r.getEquipmentSymbol(equip.Type)
	
	// Draw equipment with status-based effects
	x, y := int(equip.Location.X), int(equip.Location.Y)
	
	if equip.Status == models.StatusFailed {
		// Flashing effect for failed equipment
		r.DrawBox(x-1, y-1, 3, 3, '!', StatusFailed)
	} else if equip.Status == models.StatusNeedsRepair {
		// Warning box for equipment needing repair
		r.DrawBox(x-1, y-1, 3, 3, '?', StatusWarning)
	}
	
	r.SetPixel(x, y, symbol, color)
}

// DrawBox draws a colored box
func (r *EnhancedRenderer) DrawBox(x, y, width, height int, border rune, color Color256) {
	// Top and bottom borders
	for i := 0; i < width; i++ {
		r.SetPixel(x+i, y, border, color)
		r.SetPixel(x+i, y+height-1, border, color)
	}
	
	// Left and right borders
	for i := 0; i < height; i++ {
		r.SetPixel(x, y+i, border, color)
		r.SetPixel(x+width-1, y+i, border, color)
	}
}

// DrawRoom draws a room with colored walls
func (r *EnhancedRenderer) DrawRoom(room models.Room) {
	wallColor := r.palette.GetStructuralColor("wall")
	
	x1 := int(room.Bounds.MinX)
	y1 := int(room.Bounds.MinY)
	x2 := int(room.Bounds.MaxX)
	y2 := int(room.Bounds.MaxY)
	
	// Draw walls with proper corner characters
	// Top wall
	for x := x1 + 1; x < x2; x++ {
		r.SetPixel(x, y1, '─', wallColor)
	}
	// Bottom wall
	for x := x1 + 1; x < x2; x++ {
		r.SetPixel(x, y2, '─', wallColor)
	}
	// Left wall
	for y := y1 + 1; y < y2; y++ {
		r.SetPixel(x1, y, '│', wallColor)
	}
	// Right wall
	for y := y1 + 1; y < y2; y++ {
		r.SetPixel(x2, y, '│', wallColor)
	}
	
	// Corners
	r.SetPixel(x1, y1, '┌', wallColor)
	r.SetPixel(x2, y1, '┐', wallColor)
	r.SetPixel(x1, y2, '└', wallColor)
	r.SetPixel(x2, y2, '┘', wallColor)
	
	// Draw room label with appropriate color
	labelColor := r.palette.Foreground
	// Color code based on room name keywords
	if strings.Contains(strings.ToLower(room.Name), "mechanical") {
		labelColor = r.palette.adaptColor(Color256(33)) // Blue for mechanical
	} else if strings.Contains(strings.ToLower(room.Name), "electrical") {
		labelColor = r.palette.adaptColor(Color256(226)) // Yellow for electrical
	}
	
	label := room.Name
	if len(label) > (x2 - x1 - 2) {
		label = label[:x2-x1-2]
	}
	
	labelX := x1 + (x2-x1-len(label))/2
	labelY := y1 + (y2-y1)/2
	
	for i, ch := range label {
		r.SetPixel(labelX+i, labelY, ch, labelColor)
	}
}

// DrawLegend draws a color legend
func (r *EnhancedRenderer) DrawLegend(x, y int) {
	legendItems := []struct {
		symbol rune
		color  Color256
		label  string
	}{
		{'●', OutletOrange, "Outlet"},
		{'▪', SwitchBlue, "Switch"},
		{'▣', PanelRed, "Panel"},
		{'◊', LightYellow, "Light"},
		{'◉', SensorGreen, "Sensor"},
		{'✗', StatusFailed, "Failed"},
		{'⚠', StatusWarning, "Warning"},
		{'✓', StatusNormal, "Normal"},
	}
	
	for i, item := range legendItems {
		r.SetPixel(x, y+i, item.symbol, item.color)
		for j, ch := range item.label {
			r.SetPixel(x+2+j, y+i, ch, r.palette.Foreground)
		}
	}
}

// Render outputs the colored terminal display
func (r *EnhancedRenderer) Render() string {
	var output strings.Builder
	
	if !r.useColors {
		// Fallback to non-colored output
		for _, row := range r.buffer {
			output.WriteString(string(row))
			output.WriteRune('\n')
		}
		return output.String()
	}
	
	// Render with colors
	for y, row := range r.buffer {
		currentColor := Color256(0)
		coloredText := ""
		
		for x, ch := range row {
			color := r.colorBuffer[y][x]
			
			if color != currentColor {
				// Output accumulated text with previous color
				if coloredText != "" {
					if currentColor == r.palette.Background {
						output.WriteString(coloredText)
					} else {
						output.WriteString(currentColor.Format(coloredText))
					}
					coloredText = ""
				}
				currentColor = color
			}
			
			coloredText += string(ch)
		}
		
		// Output remaining text
		if coloredText != "" {
			if currentColor == r.palette.Background {
				output.WriteString(coloredText)
			} else {
				output.WriteString(currentColor.Format(coloredText))
			}
		}
		
		output.WriteRune('\n')
	}
	
	return output.String()
}

// getEquipmentSymbol returns symbol for equipment type
func (r *EnhancedRenderer) getEquipmentSymbol(equipType string) rune {
	symbols := map[string]rune{
		"outlet":       '●',
		"switch":       '▪',
		"panel":        '▣',
		"light":        '◊',
		"sensor":       '◉',
		"alarm":        '🔔',
		"junction_box": '▫',
		"appliance":    '▤',
	}
	
	if symbol, exists := symbols[equipType]; exists {
		return symbol
	}
	return '•'
}

// Helper functions
func abs(n int) int {
	if n < 0 {
		return -n
	}
	return n
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// SetPaletteMode changes the color palette mode
func (r *EnhancedRenderer) SetPaletteMode(mode PaletteMode) {
	r.palette = NewPalette(mode)
	
	// Update background color for all empty cells
	for y := range r.colorBuffer {
		for x := range r.colorBuffer[y] {
			if r.buffer[y][x] == ' ' {
				r.colorBuffer[y][x] = r.palette.Background
			}
		}
	}
}

// EnableColors enables or disables color output
func (r *EnhancedRenderer) EnableColors(enable bool) {
	r.useColors = enable
}

// RenderFloorPlan renders a complete floor plan with enhanced colors
func (r *EnhancedRenderer) RenderFloorPlan(plan *models.FloorPlan) {
	r.Clear()
	
	// Draw grid background
	gridColor := r.palette.GetStructuralColor("grid")
	for y := 0; y < r.Height; y += 5 {
		for x := 0; x < r.Width; x += 10 {
			r.SetPixel(x, y, '·', gridColor)
		}
	}
	
	// Draw rooms
	for _, room := range plan.Rooms {
		r.DrawRoom(room)
	}
	
	// Draw equipment
	for _, equip := range plan.Equipment {
		r.DrawEquipment(equip)
	}
	
	// Draw legend
	r.DrawLegend(r.Width-20, 2)
}

// AnimateFrame renders an animated frame with effects
func (r *EnhancedRenderer) AnimateFrame(plan *models.FloorPlan, frame int) {
	r.RenderFloorPlan(plan)
	
	// Add animated effects
	// Example: pulsing failed equipment
	for _, equip := range plan.Equipment {
		if equip.Status == models.StatusFailed {
			// Pulsing effect
			intensity := (frame % 20) / 10
			color := StatusFailed
			if intensity == 1 {
				color = BrightRed
			}
			
			x, y := int(equip.Location.X), int(equip.Location.Y)
			symbol := r.getEquipmentSymbol(equip.Type)
			r.SetPixel(x, y, symbol, color)
		}
	}
}