// Package building provides building visualization and rendering
package building

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/arxos/arxos/internal/types"
)

// Renderer implements the Renderer interface
type Renderer struct {
	config *types.ParseConfig
}

// NewRenderer creates a new building renderer
func NewRenderer() *Renderer {
	return &Renderer{
		config: types.DefaultParseConfig(),
	}
}

// NewRendererWithConfig creates a new building renderer with custom configuration
func NewRendererWithConfig(config *types.ParseConfig) *Renderer {
	return &Renderer{
		config: config,
	}
}

// RenderASCII renders a campus as ASCII art
func (r *Renderer) RenderASCII(campus *types.Campus) (string, error) {
	if len(campus.Buildings) == 0 {
		return "No buildings found in campus", nil
	}

	var output strings.Builder
	
	// Header
	output.WriteString(fmt.Sprintf("=== %s ===\n", campus.Name))
	output.WriteString(fmt.Sprintf("Method: %s | Scale: %.1f | Bounds: %dx%d\n", 
		campus.Method, campus.Scale, campus.Bounds.Width, campus.Bounds.Height))
	output.WriteString(fmt.Sprintf("Buildings: %d | IDFs: %d\n\n", 
		len(campus.Buildings), len(campus.IDFRooms)))

	// Render each building
	for _, building := range campus.Buildings {
		buildingASCII, err := r.renderBuildingASCII(building, campus.IDFRooms)
		if err != nil {
			return "", fmt.Errorf("failed to render building %s: %w", building.Name, err)
		}
		output.WriteString(buildingASCII)
		output.WriteString("\n")
	}

	// IDF Summary
	if len(campus.IDFRooms) > 0 {
		output.WriteString("=== IDF LOCATIONS ===\n")
		for _, idf := range campus.IDFRooms {
			marker := " "
			if idf.Highlighted {
				marker = "*"
			}
			output.WriteString(fmt.Sprintf("%s %s @ (%d,%d) in Room %s\n", 
				marker, idf.ID, idf.Position.X, idf.Position.Y, idf.RoomNumber))
		}
	}

	return output.String(), nil
}

// renderBuildingASCII renders a single building as ASCII
func (r *Renderer) renderBuildingASCII(building types.Building, idfLocations []types.IDFLocation) (string, error) {
	var output strings.Builder
	
	output.WriteString(fmt.Sprintf("--- %s ---\n", building.Name))
	output.WriteString(fmt.Sprintf("Rooms: %d | Bounds: %dx%d @ (%d,%d)\n", 
		len(building.Rooms), building.Bounds.Width, building.Bounds.Height,
		building.Bounds.X, building.Bounds.Y))

	if len(building.Rooms) == 0 {
		output.WriteString("  No rooms detected\n")
		return output.String(), nil
	}

	// Create a simple ASCII grid
	grid := r.createASCIIGrid(building, idfLocations)
	
	// Render the grid
	for _, row := range grid {
		output.WriteString("  " + row + "\n")
	}
	
	// Room legend
	output.WriteString("\nRooms:\n")
	for _, room := range building.Rooms {
		roomType := room.Type.String()
		area := fmt.Sprintf("%.0f sq", room.Area)
		output.WriteString(fmt.Sprintf("  %s (%s) - %s\n", room.Number, roomType, area))
	}

	return output.String(), nil
}

// createASCIIGrid creates a simple ASCII representation of the building
func (r *Renderer) createASCIIGrid(building types.Building, idfLocations []types.IDFLocation) []string {
	// Calculate grid dimensions
	scale := int(r.config.RenderScale)
	if scale <= 0 {
		scale = 20
	}
	
	maxX := building.Bounds.X + building.Bounds.Width
	maxY := building.Bounds.Y + building.Bounds.Height
	
	gridWidth := (maxX / scale) + 2
	gridHeight := (maxY / scale) + 2
	
	// Limit grid size for readability
	if gridWidth > 80 {
		gridWidth = 80
	}
	if gridHeight > 30 {
		gridHeight = 30
	}

	// Initialize grid with spaces
	grid := make([][]rune, gridHeight)
	for i := range grid {
		grid[i] = make([]rune, gridWidth)
		for j := range grid[i] {
			grid[i][j] = ' '
		}
	}

	// Draw room boundaries
	for _, room := range building.Rooms {
		r.drawRoom(grid, room, scale, building.Bounds)
	}
	
	// Draw IDFs
	for _, idf := range idfLocations {
		r.drawIDF(grid, idf, scale, building.Bounds)
	}

	// Convert grid to strings
	result := make([]string, len(grid))
	for i, row := range grid {
		result[i] = string(row)
	}

	return result
}

// drawRoom draws a room on the ASCII grid
func (r *Renderer) drawRoom(grid [][]rune, room types.Room, scale int, buildingBounds types.Rect) {
	if scale <= 0 {
		return
	}

	// Calculate grid coordinates
	x1 := (room.Bounds.X - buildingBounds.X) / scale
	y1 := (room.Bounds.Y - buildingBounds.Y) / scale
	x2 := ((room.Bounds.X + room.Bounds.Width) - buildingBounds.X) / scale
	y2 := ((room.Bounds.Y + room.Bounds.Height) - buildingBounds.Y) / scale

	// Clamp to grid bounds
	if x1 < 0 { x1 = 0 }
	if y1 < 0 { y1 = 0 }
	if x2 >= len(grid[0]) { x2 = len(grid[0]) - 1 }
	if y2 >= len(grid) { y2 = len(grid) - 1 }

	// Choose room symbol based on type
	symbol := r.getRoomSymbol(room.Type)
	
	// Draw room outline
	for x := x1; x <= x2; x++ {
		if y1 < len(grid) && x < len(grid[y1]) {
			grid[y1][x] = '-' // Top border
		}
		if y2 < len(grid) && x < len(grid[y2]) {
			grid[y2][x] = '-' // Bottom border
		}
	}
	
	for y := y1; y <= y2; y++ {
		if y < len(grid) && x1 < len(grid[y]) {
			grid[y][x1] = '|' // Left border
		}
		if y < len(grid) && x2 < len(grid[y]) {
			grid[y][x2] = '|' // Right border
		}
	}
	
	// Draw corners
	if y1 < len(grid) && x1 < len(grid[y1]) {
		grid[y1][x1] = '+'
	}
	if y1 < len(grid) && x2 < len(grid[y1]) {
		grid[y1][x2] = '+'
	}
	if y2 < len(grid) && x1 < len(grid[y2]) {
		grid[y2][x1] = '+'
	}
	if y2 < len(grid) && x2 < len(grid[y2]) {
		grid[y2][x2] = '+'
	}

	// Fill room interior with symbol
	for y := y1 + 1; y < y2; y++ {
		for x := x1 + 1; x < x2; x++ {
			if y < len(grid) && x < len(grid[y]) {
				grid[y][x] = symbol
			}
		}
	}
}

// drawIDF draws an IDF on the ASCII grid
func (r *Renderer) drawIDF(grid [][]rune, idf types.IDFLocation, scale int, buildingBounds types.Rect) {
	if scale <= 0 {
		return
	}

	// Calculate grid coordinates
	x := (idf.Position.X - buildingBounds.X) / scale
	y := (idf.Position.Y - buildingBounds.Y) / scale

	// Clamp to grid bounds
	if x < 0 || y < 0 || y >= len(grid) || x >= len(grid[y]) {
		return
	}

	// Use different symbols for IDF vs MDF
	symbol := 'I'
	if strings.Contains(strings.ToUpper(idf.ID), "MDF") {
		symbol = 'M'
	}

	grid[y][x] = symbol
}

// getRoomSymbol returns an ASCII symbol for a room type
func (r *Renderer) getRoomSymbol(roomType types.RoomType) rune {
	switch roomType {
	case types.Classroom:
		return 'C'
	case types.Office:
		return 'O'
	case types.IDF:
		return 'I'
	case types.MDF:
		return 'M'
	case types.Utility:
		return 'U'
	case types.Storage:
		return 'S'
	case types.Restroom:
		return 'R'
	case types.HallwayType:
		return 'H'
	case types.Entrance:
		return 'E'
	default:
		return '.'
	}
}

// RenderJSON renders a campus as JSON
func (r *Renderer) RenderJSON(campus *types.Campus) ([]byte, error) {
	// Create a simplified structure for JSON output
	jsonCampus := map[string]interface{}{
		"name":      campus.Name,
		"method":    campus.Method,
		"scale":     campus.Scale,
		"bounds":    campus.Bounds,
		"buildings": make([]map[string]interface{}, len(campus.Buildings)),
		"idf_rooms": make([]map[string]interface{}, len(campus.IDFRooms)),
		"stats": map[string]interface{}{
			"total_buildings": len(campus.Buildings),
			"total_rooms":     r.countTotalRooms(campus),
			"total_idfs":      len(campus.IDFRooms),
		},
	}

	// Convert buildings
	for i, building := range campus.Buildings {
		jsonCampus["buildings"].([]map[string]interface{})[i] = map[string]interface{}{
			"name":      building.Name,
			"bounds":    building.Bounds,
			"rooms":     r.convertRoomsToJSON(building.Rooms),
			"hallways":  building.Hallways,
			"entrances": building.Entrances,
		}
	}

	// Convert IDFs
	for i, idf := range campus.IDFRooms {
		jsonCampus["idf_rooms"].([]map[string]interface{})[i] = map[string]interface{}{
			"id":          idf.ID,
			"position":    idf.Position,
			"size":        idf.Size,
			"equipment":   idf.Equipment,
			"room_number": idf.RoomNumber,
			"highlighted": idf.Highlighted,
		}
	}

	return json.MarshalIndent(jsonCampus, "", "  ")
}

// convertRoomsToJSON converts rooms to JSON-compatible format
func (r *Renderer) convertRoomsToJSON(rooms []types.Room) []map[string]interface{} {
	jsonRooms := make([]map[string]interface{}, len(rooms))
	
	for i, room := range rooms {
		jsonRooms[i] = map[string]interface{}{
			"number":    room.Number,
			"type":      room.Type.String(),
			"bounds":    room.Bounds,
			"doors":     room.Doors,
			"area":      room.Area,
			"equipment": room.Equipment,
		}
	}
	
	return jsonRooms
}

// countTotalRooms counts all rooms across all buildings
func (r *Renderer) countTotalRooms(campus *types.Campus) int {
	total := 0
	for _, building := range campus.Buildings {
		total += len(building.Rooms)
	}
	return total
}

// RenderStats renders campus statistics
func (r *Renderer) RenderStats(campus *types.Campus) string {
	var output strings.Builder
	
	output.WriteString("=== CAMPUS STATISTICS ===\n")
	output.WriteString(fmt.Sprintf("Name: %s\n", campus.Name))
	output.WriteString(fmt.Sprintf("Method: %s\n", campus.Method))
	output.WriteString(fmt.Sprintf("Total Area: %d sq units\n", campus.Bounds.Width*campus.Bounds.Height))
	output.WriteString(fmt.Sprintf("Buildings: %d\n", len(campus.Buildings)))
	output.WriteString(fmt.Sprintf("Total Rooms: %d\n", r.countTotalRooms(campus)))
	output.WriteString(fmt.Sprintf("IDF Locations: %d\n", len(campus.IDFRooms)))
	
	// Room type breakdown
	roomTypes := r.analyzeRoomTypes(campus)
	if len(roomTypes) > 0 {
		output.WriteString("\nRoom Types:\n")
		for roomType, count := range roomTypes {
			output.WriteString(fmt.Sprintf("  %s: %d\n", roomType, count))
		}
	}
	
	return output.String()
}

// analyzeRoomTypes analyzes the distribution of room types
func (r *Renderer) analyzeRoomTypes(campus *types.Campus) map[string]int {
	typeCount := make(map[string]int)
	
	for _, building := range campus.Buildings {
		for _, room := range building.Rooms {
			typeCount[room.Type.String()]++
		}
	}
	
	return typeCount
}