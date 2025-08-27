package ascii

import (
	"fmt"
	"math"
	"strings"
)

// Renderer creates detailed ASCII building visualizations
type Renderer struct {
	Width      int
	Height     int
	Canvas     [][]rune
	Scale      float64 // feet per character
	OffsetX    float64
	OffsetY    float64
	ShowGrid   bool
	ShowDims   bool
	DetailLevel int // 1=basic, 2=normal, 3=detailed
}

// NewRenderer creates a new ASCII renderer
func NewRenderer(width, height int) *Renderer {
	r := &Renderer{
		Width:       width,
		Height:      height,
		Scale:       2.0, // 2 feet per character by default
		DetailLevel: 2,
	}
	r.Clear()
	return r
}

// Clear clears the canvas
func (r *Renderer) Clear() {
	r.Canvas = make([][]rune, r.Height)
	for i := range r.Canvas {
		r.Canvas[i] = make([]rune, r.Width)
		for j := range r.Canvas[i] {
			r.Canvas[i][j] = ' '
		}
	}
}

// Point represents a 2D coordinate
type Point struct {
	X, Y float64
}

// Room represents a room with walls
type Room struct {
	ID        string
	Number    string
	Name      string
	Bounds    Rectangle
	Walls     []Wall
	Doors     []Door
	Windows   []Window
	Equipment []Equipment
}

// Rectangle represents a rectangular area
type Rectangle struct {
	X, Y, Width, Height float64
}

// Wall represents a wall segment
type Wall struct {
	Start     Point
	End       Point
	Type      string // exterior, interior, partition
	Thickness float64
	HasDoor   bool
	HasWindow bool
}

// Door represents a door
type Door struct {
	Position Point
	Width    float64
	Type     string // single, double, sliding
	SwingDir string // in, out, both
	Wall     string // which wall it's on: north, south, east, west
}

// Window represents a window
type Window struct {
	Position Point
	Width    float64
	Type     string // fixed, casement, sliding
	Wall     string
}

// Equipment represents building equipment
type Equipment struct {
	ID       string
	Type     string // outlet, switch, vav, thermostat, etc.
	Position Point
	Symbol   rune
	Size     float64
}

// RenderFloorPlan renders a detailed floor plan
func (r *Renderer) RenderFloorPlan(rooms []Room) {
	r.Clear()
	
	// Draw each room
	for _, room := range rooms {
		r.drawRoom(room)
	}
	
	// Draw dimensions if enabled
	if r.ShowDims {
		r.drawDimensions(rooms)
	}
}

// drawRoom draws a single room with all details
func (r *Renderer) drawRoom(room Room) {
	// Draw walls
	for _, wall := range room.Walls {
		r.drawWall(wall)
	}
	
	// Draw doors
	for _, door := range room.Doors {
		r.drawDoor(door)
	}
	
	// Draw windows
	for _, window := range room.Windows {
		r.drawWindow(window)
	}
	
	// Draw room number/name
	if room.Number != "" {
		r.drawRoomLabel(room)
	}
	
	// Draw equipment
	for _, eq := range room.Equipment {
		r.drawEquipment(eq)
	}
}

// drawWall draws a wall segment
func (r *Renderer) drawWall(wall Wall) {
	x1, y1 := r.worldToCanvas(wall.Start.X, wall.Start.Y)
	x2, y2 := r.worldToCanvas(wall.End.X, wall.End.Y)
	
	// Determine wall character based on type and direction
	var wallChar rune
	isHorizontal := math.Abs(wall.End.Y-wall.Start.Y) < 0.1
	isVertical := math.Abs(wall.End.X-wall.Start.X) < 0.1
	
	switch wall.Type {
	case "exterior":
		if r.DetailLevel >= 2 {
			if isHorizontal {
				wallChar = '═'
			} else if isVertical {
				wallChar = '║'
			} else {
				wallChar = '▓'
			}
		} else {
			wallChar = '#'
		}
	case "interior":
		if isHorizontal {
			wallChar = '─'
		} else if isVertical {
			wallChar = '│'
		} else {
			wallChar = '/'
		}
	default:
		if isHorizontal {
			wallChar = '-'
		} else if isVertical {
			wallChar = '|'
		} else {
			wallChar = '/'
		}
	}
	
	// Draw the wall line
	if isHorizontal {
		if y1 >= 0 && y1 < r.Height {
			for x := min(x1, x2); x <= max(x1, x2) && x < r.Width; x++ {
				if x >= 0 {
					r.Canvas[y1][x] = wallChar
				}
			}
		}
	} else if isVertical {
		if x1 >= 0 && x1 < r.Width {
			for y := min(y1, y2); y <= max(y1, y2) && y < r.Height; y++ {
				if y >= 0 {
					r.Canvas[y][x1] = wallChar
				}
			}
		}
	} else {
		// Diagonal wall - use Bresenham's line algorithm
		r.drawLine(x1, y1, x2, y2, wallChar)
	}
	
	// Draw corners if detail level is high
	if r.DetailLevel >= 2 {
		r.drawCorners()
	}
}

// drawDoor draws a door opening
func (r *Renderer) drawDoor(door Door) {
	x, y := r.worldToCanvas(door.Position.X, door.Position.Y)
	
	// Door representation based on type and detail level
	if r.DetailLevel >= 3 {
		// Detailed door with swing arc
		switch door.Type {
		case "double":
			r.setChar(x-1, y, '⟨')
			r.setChar(x, y, ' ')
			r.setChar(x+1, y, '⟩')
		case "sliding":
			r.setChar(x-1, y, '[')
			r.setChar(x, y, '=')
			r.setChar(x+1, y, ']')
		default: // single
			if door.SwingDir == "in" {
				r.setChar(x, y, '⌐')
			} else {
				r.setChar(x, y, '¬')
			}
		}
	} else if r.DetailLevel >= 2 {
		// Simple door
		r.setChar(x, y, '◦')
	} else {
		// Basic door
		r.setChar(x, y, 'D')
	}
}

// drawWindow draws a window
func (r *Renderer) drawWindow(window Window) {
	x, y := r.worldToCanvas(window.Position.X, window.Position.Y)
	width := int(window.Width / r.Scale)
	
	if r.DetailLevel >= 2 {
		// Detailed window
		for i := 0; i < width && x+i < r.Width; i++ {
			r.setChar(x+i, y, '≈')
		}
	} else {
		// Basic window
		r.setChar(x, y, 'W')
	}
}

// drawEquipment draws equipment symbols
func (r *Renderer) drawEquipment(eq Equipment) {
	x, y := r.worldToCanvas(eq.Position.X, eq.Position.Y)
	
	// Select symbol based on equipment type
	symbol := r.getEquipmentSymbol(eq.Type)
	r.setChar(x, y, symbol)
	
	// Add label if detail level is high
	if r.DetailLevel >= 3 && eq.ID != "" {
		label := eq.ID
		if len(label) > 6 {
			label = label[:6]
		}
		r.drawText(x+2, y, label, false)
	}
}

// getEquipmentSymbol returns the appropriate symbol for equipment type
func (r *Renderer) getEquipmentSymbol(eqType string) rune {
	symbols := map[string]rune{
		// Electrical
		"outlet":        '⊙',
		"outlet_duplex": '⊕',
		"outlet_gfci":   '⊗',
		"switch":        '◈',
		"switch_3way":   '◇',
		"panel":         '▣',
		"breaker":       '═',
		"junction_box":  '□',
		"light":         '☀',
		"light_recessed":'○',
		
		// HVAC
		"diffuser":      '╬',
		"return":        '╪',
		"vav":           '▢',
		"thermostat":    '◫',
		"damper":        '◊',
		"fan":           '※',
		"ahu":           '▦',
		
		// Plumbing
		"valve":         '◎',
		"drain":         '◉',
		"water_heater":  '♨',
		"pump":          '◙',
		
		// Fire/Safety
		"sprinkler":     '✦',
		"smoke_detector":'◐',
		"pull_station":  '▲',
		"exit_sign":     '➤',
		"fire_ext":      '🔥', // Will fallback to FE if not supported
		
		// Data/Comm
		"data_outlet":   '◱',
		"wifi_ap":       '◵',
		"camera":        '◉',
		"speaker":       '♫',
		
		// Other
		"sensor":        '◦',
		"meter":         '▥',
	}
	
	if symbol, ok := symbols[eqType]; ok {
		return symbol
	}
	
	// Fallback symbols
	if strings.Contains(eqType, "outlet") {
		return '◯'
	}
	if strings.Contains(eqType, "switch") {
		return '◇'
	}
	if strings.Contains(eqType, "light") {
		return '☼'
	}
	
	return '•'
}

// drawRoomLabel draws the room number and name
func (r *Renderer) drawRoomLabel(room Room) {
	// Find center of room
	centerX := room.Bounds.X + room.Bounds.Width/2
	centerY := room.Bounds.Y + room.Bounds.Height/2
	
	x, y := r.worldToCanvas(centerX, centerY)
	
	// Draw room number
	if room.Number != "" {
		r.drawText(x, y, room.Number, true)
	}
	
	// Draw room name below if detail level is high
	if r.DetailLevel >= 2 && room.Name != "" {
		name := room.Name
		if len(name) > 12 {
			name = name[:12]
		}
		r.drawText(x, y+1, name, true)
	}
}

// drawDimensions adds dimension lines
func (r *Renderer) drawDimensions(rooms []Room) {
	if len(rooms) == 0 {
		return
	}
	
	// Find overall bounds
	minX, minY := rooms[0].Bounds.X, rooms[0].Bounds.Y
	maxX, maxY := minX+rooms[0].Bounds.Width, minY+rooms[0].Bounds.Height
	
	for _, room := range rooms[1:] {
		minX = math.Min(minX, room.Bounds.X)
		minY = math.Min(minY, room.Bounds.Y)
		maxX = math.Max(maxX, room.Bounds.X+room.Bounds.Width)
		maxY = math.Max(maxY, room.Bounds.Y+room.Bounds.Height)
	}
	
	// Draw horizontal dimension
	width := maxX - minX
	x1, _ := r.worldToCanvas(minX, maxY+5)
	x2, y := r.worldToCanvas(maxX, maxY+5)
	
	if y < r.Height-2 {
		// Draw dimension line
		for x := x1; x <= x2 && x < r.Width; x++ {
			r.setChar(x, y, '─')
		}
		r.setChar(x1, y, '├')
		r.setChar(x2, y, '┤')
		
		// Draw dimension text
		dimText := fmt.Sprintf("%.0f'", width)
		r.drawText((x1+x2)/2-len(dimText)/2, y-1, dimText, false)
	}
	
	// Draw vertical dimension
	height := maxY - minY
	x, y1 := r.worldToCanvas(maxX+5, minY)
	_, y2 := r.worldToCanvas(maxX+5, maxY)
	
	if x < r.Width-10 {
		for y := y1; y <= y2 && y < r.Height; y++ {
			r.setChar(x, y, '│')
		}
		r.setChar(x, y1, '┬')
		r.setChar(x, y2, '┴')
		
		// Draw dimension text
		dimText := fmt.Sprintf("%.0f'", height)
		r.drawText(x+2, (y1+y2)/2, dimText, false)
	}
}

// drawCorners intelligently draws corner characters
func (r *Renderer) drawCorners() {
	// Check each position for corner conditions
	for y := 1; y < r.Height-1; y++ {
		for x := 1; x < r.Width-1; x++ {
			curr := r.Canvas[y][x]
			
			// Skip if not a wall character
			if curr != '═' && curr != '║' && curr != '─' && curr != '│' {
				continue
			}
			
			// Check neighbors
			top := r.Canvas[y-1][x]
			bottom := r.Canvas[y+1][x]
			left := r.Canvas[y][x-1]
			right := r.Canvas[y][x+1]
			
			// Determine corner type
			hasTop := isWallChar(top)
			hasBottom := isWallChar(bottom)
			hasLeft := isWallChar(left)
			hasRight := isWallChar(right)
			
			// Select appropriate corner character
			if hasTop && hasRight && !hasBottom && !hasLeft {
				r.Canvas[y][x] = '╔'
			} else if hasTop && hasLeft && !hasBottom && !hasRight {
				r.Canvas[y][x] = '╗'
			} else if hasBottom && hasRight && !hasTop && !hasLeft {
				r.Canvas[y][x] = '╚'
			} else if hasBottom && hasLeft && !hasTop && !hasRight {
				r.Canvas[y][x] = '╝'
			} else if hasTop && hasBottom && hasRight && !hasLeft {
				r.Canvas[y][x] = '╠'
			} else if hasTop && hasBottom && hasLeft && !hasRight {
				r.Canvas[y][x] = '╣'
			} else if hasLeft && hasRight && hasBottom && !hasTop {
				r.Canvas[y][x] = '╦'
			} else if hasLeft && hasRight && hasTop && !hasBottom {
				r.Canvas[y][x] = '╩'
			} else if hasTop && hasBottom && hasLeft && hasRight {
				r.Canvas[y][x] = '╬'
			}
		}
	}
}

// Helper functions

func (r *Renderer) worldToCanvas(worldX, worldY float64) (int, int) {
	x := int((worldX - r.OffsetX) / r.Scale)
	y := int((worldY - r.OffsetY) / r.Scale)
	return x, y
}

func (r *Renderer) setChar(x, y int, char rune) {
	if x >= 0 && x < r.Width && y >= 0 && y < r.Height {
		r.Canvas[y][x] = char
	}
}

func (r *Renderer) drawText(x, y int, text string, centered bool) {
	if centered {
		x -= len(text) / 2
	}
	
	for i, ch := range text {
		r.setChar(x+i, y, ch)
	}
}

func (r *Renderer) drawLine(x1, y1, x2, y2 int, char rune) {
	// Bresenham's line algorithm
	dx := abs(x2 - x1)
	dy := abs(y2 - y1)
	sx := 1
	sy := 1
	
	if x1 > x2 {
		sx = -1
	}
	if y1 > y2 {
		sy = -1
	}
	
	err := dx - dy
	
	for {
		r.setChar(x1, y1, char)
		
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
	}
}

// ToString converts canvas to string
func (r *Renderer) ToString() string {
	var sb strings.Builder
	for _, row := range r.Canvas {
		sb.WriteString(string(row))
		sb.WriteRune('\n')
	}
	return sb.String()
}

// Utility functions
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func abs(a int) int {
	if a < 0 {
		return -a
	}
	return a
}

func isWallChar(r rune) bool {
	wallChars := []rune{'═', '║', '─', '│', '/', '\\', '#', '▓'}
	for _, wc := range wallChars {
		if r == wc {
			return true
		}
	}
	return false
}