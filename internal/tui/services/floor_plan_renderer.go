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
	symbolMap  map[string]rune // Type → Symbol mapping (configurable)
}

// NewFloorPlanRenderer creates a new floor plan renderer
func NewFloorPlanRenderer(width, height int, scale float64) *FloorPlanRenderer {
	return &FloorPlanRenderer{
		width:      width,
		height:     height,
		scale:      scale,
		showGrid:   true,
		showLabels: true,
		symbolMap:  getDefaultSymbolMap(),
	}
}

// getDefaultSymbolMap returns default symbol mappings for common types
// Users can override these or add new mappings for custom types
func getDefaultSymbolMap() map[string]rune {
	return map[string]rune{
		// Building equipment (common)
		"hvac":       'H',
		"hvac_unit":  'H',
		"electrical": 'E',
		"lighting":   'L',
		"light":      'L',
		"fire":       'F',
		"fire_alarm": 'F',
		"plumbing":   'P',
		"outlet":     'O',
		"switch":     'S',
		"panel":      'P',
		"door":       'D',

		// Generic
		"generic":   '•',
		"equipment": '⚙',
		"furniture": '◘',

		// Custom examples (ship, warehouse, etc.)
		"torpedo":   'T',
		"cargo":     'C',
		"container": 'C',
		"forklift":  'F',
		"sandwich":  'S',
		"food_item": 'F',

		// Fallback
		"unknown": '?',
	}
}

// RenderFloorPlan renders a complete floor plan
// Works for any spatial level (floor, deck, level, etc.)
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
		return fmt.Sprintf("Level %d not found", floorNumber)
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

	// Render item list
	result.WriteString(fpr.renderEquipmentList(floorData.Equipment))

	return result.String()
}

// renderHeader renders the floor plan header
// Uses generic "Structure" and "Level" for domain-agnostic display
func (fpr *FloorPlanRenderer) renderHeader(structureID string, levelNumber int) string {
	header := fmt.Sprintf("Structure: %s - Level %d", structureID, levelNumber)
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

	// Add real room structure from spatial data
	fpr.addRealRoomStructure(grid, floor)

	return grid
}

// addRealRoomStructure adds real room walls and structure from spatial data
func (fpr *FloorPlanRenderer) addRealRoomStructure(grid [][]rune, floor *FloorSpatialData) {
	// If no room data, fall back to basic structure
	if len(floor.Rooms) == 0 {
		fpr.addBasicRoomStructure(grid)
		return
	}

	// Add outer walls based on floor bounds
	fpr.addOuterWalls(grid, floor.Bounds)

	// Add individual rooms
	for _, room := range floor.Rooms {
		fpr.addRoomToGrid(grid, room, floor.Bounds)
	}
}

// addOuterWalls adds outer walls based on floor bounds
func (fpr *FloorPlanRenderer) addOuterWalls(grid [][]rune, bounds Bounds) {
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
}

// addRoomToGrid adds a single room to the grid
func (fpr *FloorPlanRenderer) addRoomToGrid(grid [][]rune, room RoomSpatialData, floorBounds Bounds) {
	height := len(grid)
	width := len(grid[0])

	// Convert room coordinates to grid coordinates
	// Room coordinates are relative to floor bounds
	roomMinX := int((room.X - room.Width/2 - floorBounds.X) / fpr.scale)
	roomMinY := int((room.Y - room.Height/2 - floorBounds.Y) / fpr.scale)
	roomMaxX := int((room.X + room.Width/2 - floorBounds.X) / fpr.scale)
	roomMaxY := int((room.Y + room.Height/2 - floorBounds.Y) / fpr.scale)

	// Ensure coordinates are within grid bounds
	if roomMinX < 0 {
		roomMinX = 0
	}
	if roomMinY < 0 {
		roomMinY = 0
	}
	if roomMaxX >= width {
		roomMaxX = width - 1
	}
	if roomMaxY >= height {
		roomMaxY = height - 1
	}

	// Draw room walls (only if room is large enough to be visible)
	if roomMaxX > roomMinX+1 && roomMaxY > roomMinY+1 {
		// Top and bottom walls
		for j := roomMinX; j <= roomMaxX; j++ {
			if roomMinY >= 0 && roomMinY < height {
				grid[roomMinY][j] = '─'
			}
			if roomMaxY >= 0 && roomMaxY < height {
				grid[roomMaxY][j] = '─'
			}
		}

		// Left and right walls
		for i := roomMinY; i <= roomMaxY; i++ {
			if roomMinX >= 0 && roomMinX < width {
				grid[i][roomMinX] = '│'
			}
			if roomMaxX >= 0 && roomMaxX < width {
				grid[i][roomMaxX] = '│'
			}
		}

		// Add corners
		if roomMinX >= 0 && roomMinX < width && roomMinY >= 0 && roomMinY < height {
			grid[roomMinY][roomMinX] = '┌'
		}
		if roomMaxX >= 0 && roomMaxX < width && roomMinY >= 0 && roomMinY < height {
			grid[roomMinY][roomMaxX] = '┐'
		}
		if roomMinX >= 0 && roomMinX < width && roomMaxY >= 0 && roomMaxY < height {
			grid[roomMaxY][roomMinX] = '└'
		}
		if roomMaxX >= 0 && roomMaxX < width && roomMaxY >= 0 && roomMaxY < height {
			grid[roomMaxY][roomMaxX] = '┘'
		}

		// Add room label in the center if there's space
		centerX := (roomMinX + roomMaxX) / 2
		centerY := (roomMinY + roomMaxY) / 2
		if centerX >= 0 && centerX < width && centerY >= 0 && centerY < height {
			// Only add label if the room is large enough
			if roomMaxX-roomMinX > 4 && roomMaxY-roomMinY > 2 {
				roomLabel := room.Number
				if len(roomLabel) > roomMaxX-roomMinX-1 {
					roomLabel = roomLabel[:roomMaxX-roomMinX-1]
				}
				for i, char := range roomLabel {
					if centerX+i >= 0 && centerX+i < width && centerY >= 0 && centerY < height {
						grid[centerY][centerX+i] = char
					}
				}
			}
		}
	}
}

// addBasicRoomStructure adds basic room walls and structure (fallback)
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
// Supports custom types with intelligent fallback to first letter
func (fpr *FloorPlanRenderer) getEquipmentSymbol(itemType string) rune {
	// Check if we have a custom mapping
	if symbol, exists := fpr.symbolMap[strings.ToLower(itemType)]; exists {
		return symbol
	}

	// Fallback: Use first letter of type (uppercase)
	// This allows ANY custom type to render intelligently
	// e.g., "refrigerator" → 'R', "missile" → 'M'
	if len(itemType) > 0 {
		return rune(strings.ToUpper(itemType)[0])
	}

	// Ultimate fallback
	return '?'
}

// SetSymbol allows users to set custom symbol mappings for item types
// This makes the renderer truly domain-agnostic
func (fpr *FloorPlanRenderer) SetSymbol(itemType string, symbol rune) {
	fpr.symbolMap[strings.ToLower(itemType)] = symbol
}

// GetSymbolMap returns a copy of the current symbol mappings
func (fpr *FloorPlanRenderer) GetSymbolMap() map[string]rune {
	result := make(map[string]rune, len(fpr.symbolMap))
	for k, v := range fpr.symbolMap {
		result[k] = v
	}
	return result
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

// renderLegend renders the item symbol legend
// Shows common symbols and notes that custom types use first letter
func (fpr *FloorPlanRenderer) renderLegend() string {
	var result strings.Builder

	result.WriteString("Item Legend:\n")
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
		{'•', "Generic Item"},
	}

	for _, item := range legendItems {
		result.WriteString(fmt.Sprintf("│ %c = %-25s │\n", item.symbol, item.name))
	}

	result.WriteString("│                                     │\n")
	result.WriteString("│ Custom types use first letter      │\n")
	result.WriteString("│ (e.g., Torpedo=T, Cargo=C)         │\n")

	result.WriteString("└─────────────────────────────────────┘\n")
	result.WriteString(fmt.Sprintf("Grid Scale: 1 character = %.1fm\n", fpr.scale))

	return result.String()
}

// renderEquipmentList renders a detailed item list
// Domain-agnostic: works for equipment, cargo, inventory, etc.
func (fpr *FloorPlanRenderer) renderEquipmentList(equipment []EquipmentSpatialData) string {
	if len(equipment) == 0 {
		return "No items found on this level."
	}

	var result strings.Builder

	result.WriteString("Item Details:\n")
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
