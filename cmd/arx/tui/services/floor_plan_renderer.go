package services

import (
	"fmt"
	"math"
	"strings"
)

// FloorPlanRenderer renders professional ASCII floor plans
type FloorPlanRenderer struct {
	width      int
	height     int
	scale      float64 // meters per character
	showGrid   bool
	showLabels bool
}

// NewFloorPlanRenderer creates a new floor plan renderer
func NewFloorPlanRenderer(width, height int, scale float64) *FloorPlanRenderer {
	return &FloorPlanRenderer{
		width:      width,
		height:     height,
		scale:      scale,
		showGrid:   true,
		showLabels: true,
	}
}

// RenderFloorPlan renders a complete floor plan
func (fpr *FloorPlanRenderer) RenderFloorPlan(spatialData *SpatialData, floorNumber int) string {
	var result strings.Builder

	// Find the floor data
	var floorData *FloorSpatialData
	for _, floor := range spatialData.Floors {
		if floor.FloorNumber == floorNumber {
			floorData = &floor
			break
		}
	}

	if floorData == nil {
		return fmt.Sprintf("Floor %d not found", floorNumber)
	}

	// Render header
	result.WriteString(fpr.renderHeader(spatialData.BuildingID, floorNumber))
	result.WriteString("\n\n")

	// Render the floor plan
	result.WriteString(fpr.renderFloorLayout(floorData))
	result.WriteString("\n\n")

	// Render legend
	result.WriteString(fpr.renderLegend())
	result.WriteString("\n\n")

	// Render equipment list
	result.WriteString(fpr.renderEquipmentList(floorData.Equipment))

	return result.String()
}

// renderHeader renders the floor plan header
func (fpr *FloorPlanRenderer) renderHeader(buildingID string, floorNumber int) string {
	header := fmt.Sprintf("Building: %s - Floor %d", buildingID, floorNumber)
	header += fmt.Sprintf(" (Scale: 1:%.0f)", fpr.scale*100) // Convert to cm scale

	// Center the header
	padding := (fpr.width - len(header)) / 2
	if padding < 0 {
		padding = 0
	}

	return strings.Repeat("─", padding) + " " + header + " " + strings.Repeat("─", padding)
}

// renderFloorLayout renders the main floor layout
func (fpr *FloorPlanRenderer) renderFloorLayout(floor *FloorSpatialData) string {
	// Create a 2D grid for the floor
	grid := fpr.createGrid(floor)

	// Add equipment to the grid
	fpr.addEquipmentToGrid(grid, floor.Equipment)

	// Add grid lines if enabled
	if fpr.showGrid {
		fpr.addGridLines(grid)
	}

	// Convert grid to string
	return fpr.gridToString(grid)
}

// createGrid creates an empty grid for the floor
func (fpr *FloorPlanRenderer) createGrid(floor *FloorSpatialData) [][]rune {
	// Calculate grid dimensions based on floor bounds and scale
	gridWidth := int(math.Ceil(floor.Bounds.Width / fpr.scale))
	gridHeight := int(math.Ceil(floor.Bounds.Height / fpr.scale))

	// Ensure grid fits within terminal width
	if gridWidth > fpr.width-10 {
		gridWidth = fpr.width - 10
	}
	if gridHeight > fpr.height-10 {
		gridHeight = fpr.height - 10
	}

	// Create empty grid
	grid := make([][]rune, gridHeight)
	for i := range grid {
		grid[i] = make([]rune, gridWidth)
		for j := range grid[i] {
			grid[i][j] = ' ' // Empty space
		}
	}

	// Add basic room structure (mock for now)
	fpr.addBasicRoomStructure(grid)

	return grid
}

// addBasicRoomStructure adds basic room walls and structure
func (fpr *FloorPlanRenderer) addBasicRoomStructure(grid [][]rune) {
	height := len(grid)
	width := len(grid[0])

	// Add outer walls
	for i := 0; i < height; i++ {
		if i == 0 || i == height-1 {
			// Top and bottom walls
			for j := 0; j < width; j++ {
				grid[i][j] = '─'
			}
		} else {
			// Side walls
			grid[i][0] = '│'
			grid[i][width-1] = '│'
		}
	}

	// Add corners
	grid[0][0] = '┌'
	grid[0][width-1] = '┐'
	grid[height-1][0] = '└'
	grid[height-1][width-1] = '┘'

	// Add some internal rooms (mock structure)
	roomHeight := height / 3
	roomWidth := width / 2

	// Room 1 (top-left)
	for i := 1; i < roomHeight; i++ {
		grid[i][roomWidth] = '│'
	}
	for j := 1; j < roomWidth; j++ {
		grid[roomHeight][j] = '─'
	}
	grid[roomHeight][roomWidth] = '┼'

	// Room 2 (top-right)
	for i := 1; i < roomHeight; i++ {
		grid[i][roomWidth] = '│'
	}

	// Room 3 (bottom)
	for j := 1; j < width-1; j++ {
		grid[roomHeight*2][j] = '─'
	}
	grid[roomHeight*2][0] = '├'
	grid[roomHeight*2][width-1] = '┤'
}

// addEquipmentToGrid adds equipment symbols to the grid
func (fpr *FloorPlanRenderer) addEquipmentToGrid(grid [][]rune, equipment []EquipmentSpatialData) {
	height := len(grid)
	width := len(grid[0])

	for _, eq := range equipment {
		// Convert real coordinates to grid coordinates
		gridX := int(eq.X / fpr.scale)
		gridY := int(eq.Y / fpr.scale)

		// Ensure coordinates are within bounds
		if gridX >= 0 && gridX < width && gridY >= 0 && gridY < height {
			// Choose symbol based on equipment type
			symbol := fpr.getEquipmentSymbol(eq.Type)
			grid[gridY][gridX] = symbol
		}
	}
}

// getEquipmentSymbol returns the ASCII symbol for equipment type
func (fpr *FloorPlanRenderer) getEquipmentSymbol(equipmentType string) rune {
	switch strings.ToLower(equipmentType) {
	case "hvac":
		return 'H'
	case "electrical":
		return 'E'
	case "lighting":
		return 'L'
	case "fire":
		return 'F'
	case "plumbing":
		return 'P'
	case "outlet":
		return 'O'
	case "switch":
		return 'S'
	case "panel":
		return 'P'
	default:
		return '?'
	}
}

// addGridLines adds coordinate grid lines
func (fpr *FloorPlanRenderer) addGridLines(grid [][]rune) {
	height := len(grid)
	width := len(grid[0])

	// Add horizontal grid lines every 5 characters
	for i := 5; i < height; i += 5 {
		for j := 0; j < width; j++ {
			if grid[i][j] == ' ' {
				grid[i][j] = '·'
			}
		}
	}

	// Add vertical grid lines every 5 characters
	for j := 5; j < width; j += 5 {
		for i := 0; i < height; i++ {
			if grid[i][j] == ' ' {
				grid[i][j] = '·'
			}
		}
	}
}

// gridToString converts the grid to a string representation
func (fpr *FloorPlanRenderer) gridToString(grid [][]rune) string {
	var result strings.Builder

	for _, row := range grid {
		result.WriteString(string(row))
		result.WriteString("\n")
	}

	return result.String()
}

// renderLegend renders the equipment legend
func (fpr *FloorPlanRenderer) renderLegend() string {
	var result strings.Builder

	result.WriteString("Equipment Legend:\n")
	result.WriteString("┌─────────────────────────────────────┐\n")

	legendItems := []struct {
		symbol rune
		name   string
	}{
		{'H', "HVAC"},
		{'E', "Electrical"},
		{'L', "Lighting"},
		{'F', "Fire Safety"},
		{'P', "Plumbing/Panel"},
		{'O', "Outlet"},
		{'S', "Switch"},
	}

	for _, item := range legendItems {
		result.WriteString(fmt.Sprintf("│ %c = %-25s │\n", item.symbol, item.name))
	}

	result.WriteString("└─────────────────────────────────────┘\n")
	result.WriteString(fmt.Sprintf("Grid Scale: 1 character = %.1fm\n", fpr.scale))

	return result.String()
}

// renderEquipmentList renders a detailed equipment list
func (fpr *FloorPlanRenderer) renderEquipmentList(equipment []EquipmentSpatialData) string {
	if len(equipment) == 0 {
		return "No equipment found on this floor."
	}

	var result strings.Builder

	result.WriteString("Equipment Details:\n")
	result.WriteString("┌─────────────────────────────────────────────────────────────────┐\n")
	result.WriteString("│ ID          │ Type        │ Position (m)     │ Grid Position   │\n")
	result.WriteString("├─────────────────────────────────────────────────────────────────┤\n")

	for _, eq := range equipment {
		gridX := int(eq.X / fpr.scale)
		gridY := int(eq.Y / fpr.scale)

		result.WriteString(fmt.Sprintf("│ %-11s │ %-10s │ (%6.1f, %6.1f) │ (%3d, %3d)      │\n",
			eq.ID, eq.Type, eq.X, eq.Y, gridX, gridY))
	}

	result.WriteString("└─────────────────────────────────────────────────────────────────┘\n")

	return result.String()
}

// SetOptions configures renderer options
func (fpr *FloorPlanRenderer) SetOptions(showGrid, showLabels bool) {
	fpr.showGrid = showGrid
	fpr.showLabels = showLabels
}

// SetScale sets the rendering scale
func (fpr *FloorPlanRenderer) SetScale(scale float64) {
	fpr.scale = scale
}

// SetDimensions sets the terminal dimensions
func (fpr *FloorPlanRenderer) SetDimensions(width, height int) {
	fpr.width = width
	fpr.height = height
}
