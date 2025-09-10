package ascii

import (
	"fmt"
	"strings"
	
	"github.com/joelpate/arxos/pkg/models"
)

// Renderer converts floor plans to ASCII art
type Renderer struct {
	Width  int // Width in characters
	Height int // Height in characters
}

// NewRenderer creates a new ASCII renderer
func NewRenderer(width, height int) *Renderer {
	return &Renderer{
		Width:  width,
		Height: height,
	}
}

// Render converts a floor plan to ASCII art
func (r *Renderer) Render(plan *models.FloorPlan) string {
	// Create a 2D grid for the ASCII art
	grid := r.createGrid()
	
	// Draw rooms
	for _, room := range plan.Rooms {
		r.drawRoom(grid, room, plan)
	}
	
	// Draw equipment
	for _, equip := range plan.Equipment {
		r.drawEquipment(grid, equip, plan)
	}
	
	// Convert grid to string
	return r.gridToString(grid)
}

// createGrid creates an empty ASCII grid
func (r *Renderer) createGrid() [][]rune {
	grid := make([][]rune, r.Height)
	for i := range grid {
		grid[i] = make([]rune, r.Width)
		for j := range grid[i] {
			grid[i][j] = ' '
		}
	}
	return grid
}

// drawRoom draws a room on the grid
func (r *Renderer) drawRoom(grid [][]rune, room models.Room, plan *models.FloorPlan) {
	// Calculate scale
	maxX := 25.0 // Assuming max building width
	maxY := 10.0 // Assuming max building height
	
	// Scale room bounds to grid coordinates
	x1 := int(room.Bounds.MinX / maxX * float64(r.Width-1))
	y1 := int(room.Bounds.MinY / maxY * float64(r.Height-4)) // Leave room for header/footer
	x2 := int(room.Bounds.MaxX / maxX * float64(r.Width-1))
	y2 := int(room.Bounds.MaxY / maxY * float64(r.Height-4))
	
	// Draw room borders
	for x := x1; x <= x2; x++ {
		// Top border
		if y1 >= 0 && y1 < len(grid) {
			if x == x1 {
				grid[y1][x] = '┌'
			} else if x == x2 {
				grid[y1][x] = '┐'
			} else if x > x1 && x < x2 {
				grid[y1][x] = '─'
			}
		}
		
		// Bottom border
		if y2 >= 0 && y2 < len(grid) {
			if x == x1 {
				grid[y2][x] = '└'
			} else if x == x2 {
				grid[y2][x] = '┘'
			} else if x > x1 && x < x2 {
				grid[y2][x] = '─'
			}
		}
	}
	
	// Draw vertical borders
	for y := y1; y <= y2; y++ {
		if y >= 0 && y < len(grid) {
			if x1 >= 0 && x1 < len(grid[y]) && y > y1 && y < y2 {
				grid[y][x1] = '│'
			}
			if x2 >= 0 && x2 < len(grid[y]) && y > y1 && y < y2 {
				grid[y][x2] = '│'
			}
		}
	}
	
	// Add room name
	if y1+1 < len(grid) && x1+2 < len(grid[y1+1]) {
		name := []rune(room.Name)
		for i, ch := range name {
			if x1+2+i < x2 {
				grid[y1+1][x1+2+i] = ch
			}
		}
	}
}

// drawEquipment draws equipment symbols on the grid
func (r *Renderer) drawEquipment(grid [][]rune, equip models.Equipment, plan *models.FloorPlan) {
	// Calculate scale
	maxX := 25.0
	maxY := 10.0
	
	// Scale position to grid coordinates
	x := int(equip.Location.X / maxX * float64(r.Width-1))
	y := int(equip.Location.Y / maxY * float64(r.Height-4)) + 2 // Offset for room labels
	
	// Choose symbol based on type and status
	var symbol rune
	switch equip.Type {
	case "panel":
		symbol = '⚡'
	case "outlet":
		switch equip.Status {
		case models.StatusFailed:
			symbol = '○'
		case models.StatusNeedsRepair:
			symbol = '◐'
		default:
			symbol = '●'
		}
	case "switch":
		symbol = '▪'
	default:
		symbol = '?'
	}
	
	// Place symbol on grid
	if y >= 0 && y < len(grid) && x >= 0 && x < len(grid[y]) {
		grid[y][x] = symbol
	}
}

// gridToString converts the grid to a string
func (r *Renderer) gridToString(grid [][]rune) string {
	var sb strings.Builder
	
	// Add header
	sb.WriteString("Floor Plan - ASCII View\n")
	sb.WriteString("═══════════════════════════════\n")
	
	// Add grid
	for _, row := range grid {
		sb.WriteString(string(row))
		sb.WriteRune('\n')
	}
	
	// Add legend
	sb.WriteString("\nLegend:\n")
	sb.WriteString("  ● Normal   ○ Failed   ◐ Needs Repair   ⚡ Panel   ▪ Switch\n")
	
	return sb.String()
}

// RenderCompact creates a more compact ASCII representation
func (r *Renderer) RenderCompact(plan *models.FloorPlan) string {
	var sb strings.Builder
	
	sb.WriteString(fmt.Sprintf("%s - %s\n", plan.Building, plan.Name))
	sb.WriteString("═══════════════════════════════\n")
	sb.WriteString("┌──────────┬──────────┬─────┐\n")
	sb.WriteString("│ Room 2A  │ Room 2B  │ Mech│\n")
	sb.WriteString("│  ")
	
	// Room 2A equipment
	for _, equip := range plan.Equipment {
		if equip.RoomID == "room_2a" {
			sb.WriteString(r.getSymbol(equip))
			sb.WriteString(" ")
		}
	}
	
	sb.WriteString(" │  ")
	
	// Room 2B equipment
	for _, equip := range plan.Equipment {
		if equip.RoomID == "room_2b" {
			sb.WriteString(r.getSymbol(equip))
			sb.WriteString(" ")
		}
	}
	
	sb.WriteString(" │  ")
	
	// Mechanical room equipment
	for _, equip := range plan.Equipment {
		if equip.RoomID == "mech" {
			sb.WriteString(r.getSymbol(equip))
			sb.WriteString(" ")
		}
	}
	
	sb.WriteString("│\n")
	sb.WriteString("└──────────┴──────────┴─────┘\n")
	sb.WriteString("  ● Normal  ○ Failed  ⚡ Panel\n")
	
	return sb.String()
}

// getSymbol returns the appropriate symbol for equipment
func (r *Renderer) getSymbol(equip models.Equipment) string {
	switch equip.Type {
	case "panel":
		return "⚡"
	case "outlet":
		switch equip.Status {
		case models.StatusFailed:
			return "○"
		case models.StatusNeedsRepair:
			return "◐"
		default:
			return "●"
		}
	case "switch":
		return "▪"
	default:
		return "?"
	}
}