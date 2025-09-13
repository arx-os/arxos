// Package rendering provides visualization and rendering capabilities for ArxOS floor plans.
// It includes ASCII, terminal, and other output formats for building layouts, equipment,
// and spatial data with support for layers and adaptive rendering systems.
package rendering

import (
	"fmt"
	"math"
	"sort"
	"strings"
	
	"github.com/joelpate/arxos/pkg/models"
)

// UniversalRenderer adapts to any floor plan layout
type UniversalRenderer struct {
	Width  int
	Height int
}

// NewUniversalRenderer creates a renderer that works with any floor plan
func NewUniversalRenderer() *UniversalRenderer {
	return &UniversalRenderer{
		Width:  80,  // Standard terminal width
		Height: 24,  // Standard terminal height
	}
}

// RenderAny creates ASCII art for any floor plan
func (r *UniversalRenderer) RenderAny(plan *models.FloorPlan) string {
	var sb strings.Builder
	
	// Header
	sb.WriteString(fmt.Sprintf("%s - %s\n", plan.Building, plan.Name))
	sb.WriteString(strings.Repeat("═", 60) + "\n\n")
	
	// Determine the rendering strategy based on what we have
	if len(plan.Rooms) > 0 {
		// We have rooms - render room-based layout
		sb.WriteString(r.renderRoomLayout(plan))
	} else if len(plan.Equipment) > 0 {
		// Only equipment - render equipment grid
		sb.WriteString(r.renderEquipmentGrid(plan))
	} else {
		// Empty plan - show instructions
		sb.WriteString(r.renderEmptyPlan())
	}
	
	// Legend
	sb.WriteString("\n" + r.renderLegend(plan))
	
	// Status summary
	sb.WriteString("\n" + r.renderStatusSummary(plan))
	
	return sb.String()
}

// renderRoomLayout creates a room-based ASCII layout
func (r *UniversalRenderer) renderRoomLayout(plan *models.FloorPlan) string {
	// Find the bounds of all rooms
	minX, minY, maxX, maxY := r.findBounds(plan)
	
	// Create scaling factors
	scaleX := float64(r.Width-4) / (maxX - minX)
	scaleY := float64(r.Height-10) / (maxY - minY) // Leave room for header/legend
	scale := math.Min(scaleX, scaleY)
	
	// Create grid
	grid := make([][]rune, r.Height-10)
	for i := range grid {
		grid[i] = make([]rune, r.Width)
		for j := range grid[i] {
			grid[i][j] = ' '
		}
	}
	
	// Draw rooms
	for _, room := range plan.Rooms {
		r.drawRoom(grid, room, minX, minY, scale)
	}
	
	// Place equipment
	for _, equip := range plan.Equipment {
		r.placeEquipment(grid, equip, minX, minY, scale)
	}
	
	// Convert grid to string
	return r.gridToString(grid)
}

// renderEquipmentGrid creates a grid layout for equipment only
func (r *UniversalRenderer) renderEquipmentGrid(plan *models.FloorPlan) string {
	var sb strings.Builder
	
	// Sort equipment by type
	equipByType := make(map[string][]models.Equipment)
	for _, equip := range plan.Equipment {
		equipByType[equip.Type] = append(equipByType[equip.Type], equip)
	}
	
	// Create sections for each type
	for eqType, equipment := range equipByType {
		if len(equipment) == 0 {
			continue
		}
		
		sb.WriteString(fmt.Sprintf("%s:\n", strings.ToUpper(eqType)))
		sb.WriteString(strings.Repeat("-", 40) + "\n")
		
		// List equipment in columns
		cols := 3
		for i := 0; i < len(equipment); i += cols {
			for j := 0; j < cols && i+j < len(equipment); j++ {
				eq := equipment[i+j]
				symbol := r.getSymbol(eq)
				name := r.truncateName(eq.Name, 12)
				sb.WriteString(fmt.Sprintf("%s %-12s  ", symbol, name))
			}
			sb.WriteString("\n")
		}
		sb.WriteString("\n")
	}
	
	return sb.String()
}

// renderEmptyPlan shows instructions for empty plans
func (r *UniversalRenderer) renderEmptyPlan() string {
	return `No floor plan data found.

To add equipment manually:
  arx add <name> --type <type> --location <x,y>
  
To import from JSON:
  arx import-json template.json
  
To retry PDF parsing:
  arx import <pdf-file> --ocr
`
}

// findBounds calculates the bounding box of all rooms
func (r *UniversalRenderer) findBounds(plan *models.FloorPlan) (minX, minY, maxX, maxY float64) {
	if len(plan.Rooms) == 0 && len(plan.Equipment) == 0 {
		return 0, 0, 100, 50
	}
	
	minX, minY = math.MaxFloat64, math.MaxFloat64
	maxX, maxY = -math.MaxFloat64, -math.MaxFloat64
	
	// Check rooms
	for _, room := range plan.Rooms {
		minX = math.Min(minX, room.Bounds.MinX)
		minY = math.Min(minY, room.Bounds.MinY)
		maxX = math.Max(maxX, room.Bounds.MaxX)
		maxY = math.Max(maxY, room.Bounds.MaxY)
	}
	
	// Check equipment if no rooms
	if len(plan.Rooms) == 0 {
		for _, equip := range plan.Equipment {
			minX = math.Min(minX, equip.Location.X-5)
			minY = math.Min(minY, equip.Location.Y-5)
			maxX = math.Max(maxX, equip.Location.X+5)
			maxY = math.Max(maxY, equip.Location.Y+5)
		}
	}
	
	// Add padding
	padding := 5.0
	return minX - padding, minY - padding, maxX + padding, maxY + padding
}

// drawRoom draws a room on the grid
func (r *UniversalRenderer) drawRoom(grid [][]rune, room models.Room, minX, minY, scale float64) {
	// Convert room bounds to grid coordinates
	x1 := int((room.Bounds.MinX - minX) * scale)
	y1 := int((room.Bounds.MinY - minY) * scale)
	x2 := int((room.Bounds.MaxX - minX) * scale)
	y2 := int((room.Bounds.MaxY - minY) * scale)
	
	// Ensure within grid bounds
	x1 = r.clamp(x1, 0, r.Width-1)
	y1 = r.clamp(y1, 0, len(grid)-1)
	x2 = r.clamp(x2, 0, r.Width-1)
	y2 = r.clamp(y2, 0, len(grid)-1)
	
	// Draw room borders
	for x := x1; x <= x2; x++ {
		if y1 >= 0 && y1 < len(grid) && x >= 0 && x < len(grid[y1]) {
			if grid[y1][x] == ' ' {
				grid[y1][x] = '─'
			}
		}
		if y2 >= 0 && y2 < len(grid) && x >= 0 && x < len(grid[y2]) {
			if grid[y2][x] == ' ' {
				grid[y2][x] = '─'
			}
		}
	}
	
	for y := y1; y <= y2; y++ {
		if y >= 0 && y < len(grid) {
			if x1 >= 0 && x1 < len(grid[y]) && grid[y][x1] == ' ' {
				grid[y][x1] = '│'
			}
			if x2 >= 0 && x2 < len(grid[y]) && grid[y][x2] == ' ' {
				grid[y][x2] = '│'
			}
		}
	}
	
	// Draw corners
	if y1 >= 0 && y1 < len(grid) {
		if x1 >= 0 && x1 < len(grid[y1]) {
			grid[y1][x1] = '┌'
		}
		if x2 >= 0 && x2 < len(grid[y1]) {
			grid[y1][x2] = '┐'
		}
	}
	if y2 >= 0 && y2 < len(grid) {
		if x1 >= 0 && x1 < len(grid[y2]) {
			grid[y2][x1] = '└'
		}
		if x2 >= 0 && x2 < len(grid[y2]) {
			grid[y2][x2] = '┘'
		}
	}
	
	// Add room name (if space permits)
	if x2-x1 > len(room.Name)+2 && y2-y1 > 2 {
		nameY := (y1 + y2) / 2
		nameX := x1 + 2
		for i, ch := range room.Name {
			if nameX+i < x2-1 && nameY >= 0 && nameY < len(grid) {
				grid[nameY][nameX+i] = ch
			}
		}
	}
}

// placeEquipment places equipment symbol on the grid
func (r *UniversalRenderer) placeEquipment(grid [][]rune, equip models.Equipment, minX, minY, scale float64) {
	// Convert position to grid coordinates
	x := int((equip.Location.X - minX) * scale)
	y := int((equip.Location.Y - minY) * scale)
	
	// Ensure within bounds
	if y >= 0 && y < len(grid) && x >= 0 && x < len(grid[y]) {
		// Don't overwrite room borders
		if grid[y][x] == ' ' || grid[y][x] == '·' {
			grid[y][x] = r.getSymbolRune(equip)
		}
	}
}

// getSymbol returns a string symbol for equipment
func (r *UniversalRenderer) getSymbol(equip models.Equipment) string {
	// Status indicators
	if equip.Status == models.StatusFailed {
		return "✗"
	} else if equip.Status == models.StatusNeedsRepair {
		return "⚠"
	}
	
	// Type-specific symbols
	switch equip.Type {
	case "mdf":
		return "⚡"
	case "idf":
		return "◉"
	case "outlet":
		return "●"
	case "switch":
		return "▪"
	case "panel":
		return "▣"
	case "access_point", "ap":
		return "📡"
	case "server":
		return "▦"
	default:
		return "•"
	}
}

// getSymbolRune returns a rune symbol for grid placement
func (r *UniversalRenderer) getSymbolRune(equip models.Equipment) rune {
	symbol := r.getSymbol(equip)
	if len(symbol) > 0 {
		return []rune(symbol)[0]
	}
	return '•'
}

// gridToString converts the grid to a string
func (r *UniversalRenderer) gridToString(grid [][]rune) string {
	var sb strings.Builder
	for _, row := range grid {
		sb.WriteString(string(row))
		sb.WriteRune('\n')
	}
	return sb.String()
}

// renderLegend creates the legend section
func (r *UniversalRenderer) renderLegend(plan *models.FloorPlan) string {
	// Collect unique equipment types
	types := make(map[string]bool)
	for _, equip := range plan.Equipment {
		types[equip.Type] = true
	}
	
	if len(types) == 0 {
		return ""
	}
	
	var sb strings.Builder
	sb.WriteString("Legend:\n")
	
	// Show symbols for present equipment types
	typeList := make([]string, 0, len(types))
	for t := range types {
		typeList = append(typeList, t)
	}
	sort.Strings(typeList)
	
	for _, t := range typeList {
		sample := models.Equipment{Type: t, Status: models.StatusNormal}
		symbol := r.getSymbol(sample)
		sb.WriteString(fmt.Sprintf("  %s %s\n", symbol, t))
	}
	
	// Status indicators
	sb.WriteString("\nStatus:\n")
	sb.WriteString("  ✓ Normal   ⚠ Needs Repair   ✗ Failed\n")
	
	return sb.String()
}

// renderStatusSummary creates a summary of equipment status
func (r *UniversalRenderer) renderStatusSummary(plan *models.FloorPlan) string {
	if len(plan.Equipment) == 0 {
		return ""
	}
	
	// Count by status
	statusCount := make(map[models.EquipmentStatus]int)
	for _, equip := range plan.Equipment {
		statusCount[equip.Status]++
	}
	
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("Total Equipment: %d\n", len(plan.Equipment)))
	
	if statusCount[models.StatusNormal] > 0 {
		sb.WriteString(fmt.Sprintf("  Normal: %d\n", statusCount[models.StatusNormal]))
	}
	if statusCount[models.StatusNeedsRepair] > 0 {
		sb.WriteString(fmt.Sprintf("  ⚠ Needs Repair: %d\n", statusCount[models.StatusNeedsRepair]))
	}
	if statusCount[models.StatusFailed] > 0 {
		sb.WriteString(fmt.Sprintf("  ✗ Failed: %d\n", statusCount[models.StatusFailed]))
	}
	
	return sb.String()
}

// clamp constrains a value between min and max
func (r *UniversalRenderer) clamp(value, min, max int) int {
	if value < min {
		return min
	}
	if value > max {
		return max
	}
	return value
}

// truncateName shortens a name to fit in the given width
func (r *UniversalRenderer) truncateName(name string, maxLen int) string {
	if len(name) <= maxLen {
		return name
	}
	return name[:maxLen-1] + "…"
}