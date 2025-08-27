package display

import (
	"fmt"
	"strings"

	"github.com/arxos/arxos/cmd/models"
)

// ASCIIRenderer renders ArxObjects as ASCII art
type ASCIIRenderer struct {
	Width       int
	Height      int
	Canvas      [][]rune
	Objects     []*models.ArxObjectV2
	ViewMode    string  // "floor", "system", "3d", "hardware", "pcb"
	SystemLayer string  // "electrical", "hvac", "plumbing", "hardware", etc.
	Scale       float64 // Pixels per meter
	OffsetX     float64
	OffsetY     float64
	ShowGrid    bool
	ShowLegend  bool
	Highlights  map[string]bool // Highlighted object IDs
	HardwareDetail bool  // Show detailed hardware view
}

// NewASCIIRenderer creates a new ASCII renderer
func NewASCIIRenderer(width, height int) *ASCIIRenderer {
	canvas := make([][]rune, height)
	for i := range canvas {
		canvas[i] = make([]rune, width)
		for j := range canvas[i] {
			canvas[i][j] = ' '
		}
	}

	return &ASCIIRenderer{
		Width:      width,
		Height:     height,
		Canvas:     canvas,
		ViewMode:   "floor",
		Scale:      1.0,
		ShowGrid:   true,
		ShowLegend: true,
		Highlights: make(map[string]bool),
	}
}

// Clear clears the canvas
func (r *ASCIIRenderer) Clear() {
	for i := range r.Canvas {
		for j := range r.Canvas[i] {
			if r.ShowGrid && (i%5 == 0 || j%5 == 0) {
				r.Canvas[i][j] = '·'
			} else {
				r.Canvas[i][j] = ' '
			}
		}
	}
}

// RenderFloorPlan renders a floor plan view
func (r *ASCIIRenderer) RenderFloorPlan(floor string) {
	r.Clear()

	// Group objects by type for this floor
	rooms := []*models.ArxObjectV2{}
	walls := []*models.ArxObjectV2{}
	doors := []*models.ArxObjectV2{}
	windows := []*models.ArxObjectV2{}
	equipment := []*models.ArxObjectV2{}

	for _, obj := range r.Objects {
		if !strings.Contains(obj.ID, floor) {
			continue
		}

		switch obj.Type {
		case "room":
			rooms = append(rooms, obj)
		case "wall":
			walls = append(walls, obj)
		case "door":
			doors = append(doors, obj)
		case "window":
			windows = append(windows, obj)
		case "equipment", "outlet", "switch", "sensor":
			equipment = append(equipment, obj)
		}
	}

	// Render in layers (back to front)
	r.renderRooms(rooms)
	r.renderWalls(walls)
	r.renderDoors(doors)
	r.renderWindows(windows)
	
	if r.SystemLayer != "" {
		r.renderSystemOverlay(equipment)
	}

	// Add labels
	r.renderLabels(rooms)
	
	// Add legend
	if r.ShowLegend {
		r.renderLegend()
	}
}

// renderRooms renders room boundaries
func (r *ASCIIRenderer) renderRooms(rooms []*models.ArxObjectV2) {
	for _, room := range rooms {
		// Get room dimensions from properties
		x, y, width, height := r.getRoomBounds(room)
		
		// Draw room outline
		for i := x; i < x+width && i < r.Width; i++ {
			if y >= 0 && y < r.Height {
				r.Canvas[y][i] = '─'
			}
			if y+height-1 >= 0 && y+height-1 < r.Height {
				r.Canvas[y+height-1][i] = '─'
			}
		}
		
		for j := y; j < y+height && j < r.Height; j++ {
			if x >= 0 && x < r.Width {
				r.Canvas[j][x] = '│'
			}
			if x+width-1 >= 0 && x+width-1 < r.Width {
				r.Canvas[j][x+width-1] = '│'
			}
		}
		
		// Corners
		if x >= 0 && x < r.Width && y >= 0 && y < r.Height {
			r.Canvas[y][x] = '┌'
		}
		if x+width-1 >= 0 && x+width-1 < r.Width && y >= 0 && y < r.Height {
			r.Canvas[y][x+width-1] = '┐'
		}
		if x >= 0 && x < r.Width && y+height-1 >= 0 && y+height-1 < r.Height {
			r.Canvas[y+height-1][x] = '└'
		}
		if x+width-1 >= 0 && x+width-1 < r.Width && y+height-1 >= 0 && y+height-1 < r.Height {
			r.Canvas[y+height-1][x+width-1] = '┘'
		}
		
		// Fill with floor pattern if highlighted
		if r.Highlights[room.ID] {
			for i := y+1; i < y+height-1 && i < r.Height; i++ {
				for j := x+1; j < x+width-1 && j < r.Width; j++ {
					if r.Canvas[i][j] == ' ' || r.Canvas[i][j] == '·' {
						r.Canvas[i][j] = '░'
					}
				}
			}
		}
	}
}

// renderWalls renders individual walls
func (r *ASCIIRenderer) renderWalls(walls []*models.ArxObjectV2) {
	for _, wall := range walls {
		// Determine wall position and orientation
		if wall.Position == nil {
			continue
		}
		
		x, y := r.worldToCanvas(wall.Coordinates)
		
		switch wall.Position.Wall {
		case "north":
			r.drawHorizontalWall(x, y, 10)
		case "south":
			r.drawHorizontalWall(x, y+10, 10)
		case "east":
			r.drawVerticalWall(x+10, y, 10)
		case "west":
			r.drawVerticalWall(x, y, 10)
		}
	}
}

// renderDoors renders doors in walls
func (r *ASCIIRenderer) renderDoors(doors []*models.ArxObjectV2) {
	for _, door := range doors {
		x, y := r.worldToCanvas(door.Coordinates)
		
		// Door symbol depends on orientation
		if door.Position != nil {
			switch door.Position.Wall {
			case "north", "south":
				r.drawSymbol(x, y, '╫') // Horizontal door
			case "east", "west":
				r.drawSymbol(x, y, '╪') // Vertical door
			default:
				r.drawSymbol(x, y, 'D')
			}
		} else {
			r.drawSymbol(x, y, 'D')
		}
	}
}

// renderWindows renders windows in walls
func (r *ASCIIRenderer) renderWindows(windows []*models.ArxObjectV2) {
	for _, window := range windows {
		x, y := r.worldToCanvas(window.Coordinates)
		
		// Window symbol
		if window.Position != nil {
			switch window.Position.Wall {
			case "north", "south":
				r.drawSymbol(x, y, '═') // Horizontal window
			case "east", "west":
				r.drawSymbol(x, y, '║') // Vertical window
			default:
				r.drawSymbol(x, y, 'W')
			}
		} else {
			r.drawSymbol(x, y, 'W')
		}
	}
}

// renderSystemOverlay renders system components
func (r *ASCIIRenderer) renderSystemOverlay(equipment []*models.ArxObjectV2) {
	for _, eq := range equipment {
		if eq.System != r.SystemLayer && r.SystemLayer != "all" {
			continue
		}
		
		x, y := r.worldToCanvas(eq.Coordinates)
		symbol := r.getSystemSymbol(eq)
		
		r.drawSymbol(x, y, symbol)
		
		// Draw connections if available
		if paths, ok := eq.Relationships["wiring_path"]; ok && r.SystemLayer == "electrical" {
			r.drawConnectionPaths(eq, paths, '·')
		} else if paths, ok := eq.Relationships["duct_path"]; ok && r.SystemLayer == "hvac" {
			r.drawConnectionPaths(eq, paths, '≈')
		} else if paths, ok := eq.Relationships["pipe_path"]; ok && r.SystemLayer == "plumbing" {
			r.drawConnectionPaths(eq, paths, '~')
		}
	}
}

// renderLabels adds room labels
func (r *ASCIIRenderer) renderLabels(rooms []*models.ArxObjectV2) {
	for _, room := range rooms {
		x, y, width, height := r.getRoomBounds(room)
		
		// Center the label in the room
		label := r.getRoomLabel(room)
		labelX := x + (width-len(label))/2
		labelY := y + height/2
		
		if labelX > 0 && labelY > 0 && labelX+len(label) < r.Width && labelY < r.Height {
			for i, ch := range label {
				if labelX+i < r.Width {
					r.Canvas[labelY][labelX+i] = ch
				}
			}
		}
	}
}

// renderLegend adds a legend to the display
func (r *ASCIIRenderer) renderLegend() {
	legendY := r.Height - 10
	legendX := r.Width - 30
	
	if legendY < 0 || legendX < 0 {
		return
	}
	
	legends := []string{
		"═══ LEGEND ═══",
		"│ ─ │ Walls",
		"│ D │ Door",
		"│ W │ Window",
	}
	
	if r.SystemLayer == "electrical" {
		legends = append(legends,
			"│ ⚡ │ Panel",
			"│ ◉ │ Outlet",
			"│ ◈ │ Switch",
			"│ · │ Wiring",
		)
	} else if r.SystemLayer == "hvac" {
		legends = append(legends,
			"│ ⟐ │ VAV Box",
			"│ ▤ │ Diffuser",
			"│ ◎ │ Return",
			"│ ≈ │ Duct",
		)
	} else if r.SystemLayer == "plumbing" {
		legends = append(legends,
			"│ ◊ │ Valve",
			"│ ○ │ Fixture",
			"│ ▽ │ Drain",
			"│ ~ │ Pipe",
		)
	}
	
	for i, line := range legends {
		if legendY+i < r.Height {
			for j, ch := range line {
				if legendX+j < r.Width {
					r.Canvas[legendY+i][legendX+j] = ch
				}
			}
		}
	}
}

// Helper methods

func (r *ASCIIRenderer) getRoomBounds(room *models.ArxObjectV2) (x, y, width, height int) {
	// Extract from room ID or properties
	// For demo, use fixed positions based on room number
	roomNum := strings.Split(room.ID, "/")
	if len(roomNum) > 0 {
		switch roomNum[len(roomNum)-1] {
		case "101":
			return 5, 5, 12, 8
		case "102":
			return 20, 5, 12, 8
		case "103":
			return 35, 5, 12, 8
		case "104":
			return 50, 5, 12, 8
		default:
			return 5, 5, 10, 6
		}
	}
	return 5, 5, 10, 6
}

func (r *ASCIIRenderer) getRoomLabel(room *models.ArxObjectV2) string {
	if room.Name != "" {
		return room.Name
	}
	parts := strings.Split(room.ID, "/")
	if len(parts) > 0 {
		return parts[len(parts)-1]
	}
	return "?"
}

func (r *ASCIIRenderer) worldToCanvas(coords *models.Coordinates) (int, int) {
	if coords == nil {
		return 0, 0
	}
	
	x := int((coords.X - r.OffsetX) * r.Scale)
	y := int((coords.Y - r.OffsetY) * r.Scale)
	
	return x, y
}

func (r *ASCIIRenderer) drawSymbol(x, y int, symbol rune) {
	if x >= 0 && x < r.Width && y >= 0 && y < r.Height {
		r.Canvas[y][x] = symbol
	}
}

func (r *ASCIIRenderer) drawHorizontalWall(x, y, length int) {
	for i := 0; i < length && x+i < r.Width; i++ {
		if y >= 0 && y < r.Height {
			r.Canvas[y][x+i] = '─'
		}
	}
}

func (r *ASCIIRenderer) drawVerticalWall(x, y, length int) {
	for i := 0; i < length && y+i < r.Height; i++ {
		if x >= 0 && x < r.Width {
			r.Canvas[y+i][x] = '│'
		}
	}
}

func (r *ASCIIRenderer) getSystemSymbol(obj *models.ArxObjectV2) rune {
	// Return appropriate symbol based on type and system
	symbolMap := map[string]map[string]rune{
		"electrical": {
			"panel":   '⚡',
			"breaker": '▣',
			"outlet":  '◉',
			"switch":  '◈',
			"light":   '☀',
			"sensor":  '◐',
		},
		"hvac": {
			"vav":      '⟐',
			"diffuser": '▤',
			"return":   '◎',
			"sensor":   '◑',
			"damper":   '◧',
			"fan":      '※',
		},
		"plumbing": {
			"valve":   '◊',
			"fixture": '○',
			"drain":   '▽',
			"pump":    '◈',
			"meter":   '◙',
		},
		"fire_alarm": {
			"detector": '●',
			"pull":     '▪',
			"horn":     '♫',
			"sprinkler": '✱',
		},
	}
	
	if systemSymbols, ok := symbolMap[obj.System]; ok {
		if symbol, ok := systemSymbols[obj.Type]; ok {
			return symbol
		}
	}
	
	// Default symbols
	switch obj.Type {
	case "sensor":
		return '◐'
	case "equipment":
		return '▧'
	default:
		return '?'
	}
}

func (r *ASCIIRenderer) drawConnectionPaths(start *models.ArxObjectV2, paths []string, pathSymbol rune) {
	// Draw connection paths between objects (simplified)
	// In real implementation, would use pathfinding algorithm
	// For now, just indicate connections exist
}

// ToString converts canvas to string
func (r *ASCIIRenderer) ToString() string {
	lines := []string{}
	for _, row := range r.Canvas {
		lines = append(lines, string(row))
	}
	return strings.Join(lines, "\n")
}

// RenderInteractive creates an interactive view (like Minecraft F3 debug)
func (r *ASCIIRenderer) RenderInteractive(currentObj *models.ArxObjectV2) string {
	var sb strings.Builder
	
	// Top bar
	sb.WriteString(fmt.Sprintf("╔%s╗\n", strings.Repeat("═", r.Width-2)))
	
	// Current object info (like Minecraft F3)
	if currentObj != nil {
		sb.WriteString(fmt.Sprintf("║ Location: %s%s║\n", 
			currentObj.ID, 
			strings.Repeat(" ", r.Width-len(currentObj.ID)-13)))
		
		sb.WriteString(fmt.Sprintf("║ Type: %s | System: %s%s║\n",
			currentObj.Type,
			currentObj.System,
			strings.Repeat(" ", r.Width-len(currentObj.Type)-len(currentObj.System)-21)))
			
		if currentObj.Coordinates != nil {
			sb.WriteString(fmt.Sprintf("║ Coords: X:%.1f Y:%.1f Z:%.1f%s║\n",
				currentObj.Coordinates.X,
				currentObj.Coordinates.Y,
				currentObj.Coordinates.Z,
				strings.Repeat(" ", r.Width-35)))
		}
	}
	
	sb.WriteString(fmt.Sprintf("╠%s╣\n", strings.Repeat("═", r.Width-2)))
	
	// Main view
	sb.WriteString(r.ToString())
	
	// Bottom bar with controls
	sb.WriteString(fmt.Sprintf("\n╠%s╣\n", strings.Repeat("═", r.Width-2)))
	sb.WriteString(fmt.Sprintf("║ [W,A,S,D] Navigate | [E] Interact | [Tab] Switch View | [L] Layers%s║\n",
		strings.Repeat(" ", r.Width-71)))
	sb.WriteString(fmt.Sprintf("╚%s╝", strings.Repeat("═", r.Width-2)))
	
	return sb.String()
}

// MinecraftStyle3D creates a pseudo-3D view
func (r *ASCIIRenderer) MinecraftStyle3D() string {
	// Simple isometric view
	var view strings.Builder
	
	view.WriteString("    ╱▔▔▔▔▔▔╲\n")
	view.WriteString("   ╱         ╲\n")
	view.WriteString("  ╱   ROOM    ╲\n")
	view.WriteString(" ╱    101      ╲\n")
	view.WriteString("╱_______________╲\n")
	view.WriteString("│               │╲\n")
	view.WriteString("│  ◉     ◈     │ ╲\n")
	view.WriteString("│ outlet switch │  ╲\n")
	view.WriteString("│               │   │\n")
	view.WriteString("│      ╫        │   │\n")
	view.WriteString("│     door      │   │\n")
	view.WriteString("│_______________│   │\n")
	view.WriteString(" ╲              ╲   │\n")
	view.WriteString("  ╲              ╲  │\n")
	view.WriteString("   ╲              ╲ │\n")
	view.WriteString("    ╲______________╲│\n")
	
	return view.String()
}

// RenderHardwareView renders a hardware/PCB view
func (r *ASCIIRenderer) RenderHardwareView(deviceID string) string {
	var view strings.Builder
	
	if r.ViewMode == "pcb" {
		// PCB layout view
		view.WriteString("\n╔════════════════════════════════════════╗\n")
		view.WriteString("║         PCB Layout: Main Board        ║\n")
		view.WriteString("╠════════════════════════════════════════╣\n")
		view.WriteString("║                                        ║\n")
		view.WriteString("║  ┌──[U1]──┐    R1    C1    ┌─[K1]─┐  ║\n")
		view.WriteString("║  │ ESP32  │    ═══   ┴┬┴   │Relay │  ║\n")
		view.WriteString("║  │        │                 └──┬──┘  ║\n")
		view.WriteString("║  │    ○TP1│    R2    C2        │     ║\n")
		view.WriteString("║  │        │    ═══   ┴┬┴       │     ║\n")
		view.WriteString("║  └────────┘                    │     ║\n")
		view.WriteString("║       │                        │     ║\n")
		view.WriteString("║  ═════╧═══════════════════════╧════  ║\n")
		view.WriteString("║       Power Trace (5V)               ║\n")
		view.WriteString("║                                      ║\n")
		view.WriteString("║  [J1] Terminal Block                 ║\n")
		view.WriteString("║   1:LINE  2:NEUTRAL  3:GROUND       ║\n")
		view.WriteString("║                                      ║\n")
		view.WriteString("╚══════════════════════════════════════╝\n")
		view.WriteString("\nLegend: [U#]=IC  R#=Resistor  C#=Capacitor\n")
		view.WriteString("        K#=Relay  J#=Connector  TP#=TestPoint\n")
	} else {
		// Component hierarchy view
		view.WriteString("\n═══ Hardware Hierarchy ═══\n\n")
		view.WriteString("📦 Device: Smart Outlet\n")
		view.WriteString("├─ 🔧 Hardware\n")
		view.WriteString("│  ├─ 📟 PCB: main\n")
		view.WriteString("│  │  ├─ 🔲 U1: ESP32-WROOM-32 (MCU)\n")
		view.WriteString("│  │  │  ├─ Pin 1: VCC (3.3V)\n")
		view.WriteString("│  │  │  ├─ Pin 5: GPIO2 (Relay Control)\n")
		view.WriteString("│  │  │  └─ Pin 9: GND\n")
		view.WriteString("│  │  ├─ 🔴 R1-R4: 10K Resistors\n")
		view.WriteString("│  │  ├─ 🔵 C1-C2: 100nF Capacitors\n")
		view.WriteString("│  │  ├─ ⚡ K1: 5V Relay\n")
		view.WriteString("│  │  └─ 🔌 J1: AC Terminal Block\n")
		view.WriteString("│  ├─ 🔌 Wiring\n")
		view.WriteString("│  │  ├─ Line Wire (14 AWG)\n")
		view.WriteString("│  │  ├─ Neutral Wire (14 AWG)\n")
		view.WriteString("│  │  └─ Ground Wire (14 AWG)\n")
		view.WriteString("│  └─ 📦 Enclosure\n")
		view.WriteString("│     └─ NEMA 5-15R Receptacle\n")
		view.WriteString("└─ 📊 Test Points\n")
		view.WriteString("   ├─ TP1: 5V Rail\n")
		view.WriteString("   └─ TP2: MCU Clock\n")
	}
	
	return view.String()
}

// RenderCircuitTrace shows electrical path visualization
func (r *ASCIIRenderer) RenderCircuitTrace() string {
	var trace strings.Builder
	
	trace.WriteString("\n═══ Circuit Trace Visualization ═══\n\n")
	trace.WriteString("🏢 Building Power Distribution\n")
	trace.WriteString("│\n")
	trace.WriteString("├─⚡ Transformer (480V → 208V)\n")
	trace.WriteString("│  │\n")
	trace.WriteString("│  └─📊 Main Meter\n")
	trace.WriteString("│     │\n")
	trace.WriteString("│     └─🔌 Panel: MDF\n")
	trace.WriteString("│        │\n")
	trace.WriteString("│        ├─ Breaker 1 (20A) → Lighting Circuit\n")
	trace.WriteString("│        ├─ Breaker 12 (15A) → Outlet Circuit ←── YOU ARE HERE\n")
	trace.WriteString("│        │                     │\n")
	trace.WriteString("│        │                     └─ Wire Run (45m, 14 AWG)\n")
	trace.WriteString("│        │                        │\n")
	trace.WriteString("│        │                        └─🔌 Smart Outlet (f1_r101_north_1)\n")
	trace.WriteString("│        │                           │\n")
	trace.WriteString("│        │                           └─[Hardware Level]\n")
	trace.WriteString("│        │                              ├─ PCB: main\n")
	trace.WriteString("│        │                              │  ├─ U1: MCU\n")
	trace.WriteString("│        │                              │  └─ K1: Relay\n")
	trace.WriteString("│        │                              └─ AC Terminals\n")
	trace.WriteString("│        └─ Breaker 24 (30A) → HVAC Circuit\n")
	trace.WriteString("│\n")
	trace.WriteString("└─ Other Distribution...\n")
	
	return trace.String()
}