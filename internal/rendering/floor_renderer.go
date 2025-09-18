package rendering

import (
	"fmt"
	"math"
	"strings"

	"github.com/arx-os/arxos/pkg/models"
)

// FloorRenderer converts floor plan data to ASCII representation
type FloorRenderer struct {
	width     int
	height    int
	scale     float64
	grid      [][]rune
	legend    map[rune]string
	equipment map[string]*models.Equipment
	rooms     map[string]*models.Room
}

// ASCII characters for different elements
const (
	CharWallHorizontal = '─'
	CharWallVertical   = '│'
	CharCornerTL       = '┌'
	CharCornerTR       = '┐'
	CharCornerBL       = '└'
	CharCornerBR       = '┘'
	CharTJunctionT     = '┬'
	CharTJunctionB     = '┴'
	CharTJunctionL     = '├'
	CharTJunctionR     = '┤'
	CharCross          = '┼'
	CharDoor           = '▪'
	CharWindow         = '░'
	CharSpace          = ' '
	CharFloor          = '·'

	// Equipment markers
	CharOutlet         = 'o'
	CharSwitch         = 's'
	CharPanel          = 'P'
	CharHVAC           = 'H'
	CharFireAlarm      = 'F'
	CharCamera         = 'C'
	CharAccessPoint    = 'W'
	CharEquipmentOther = 'E'
)

// NewFloorRenderer creates a new floor renderer with specified dimensions
func NewFloorRenderer(width, height int) *FloorRenderer {
	if width <= 0 {
		width = 120
	}
	if height <= 0 {
		height = 40
	}

	fr := &FloorRenderer{
		width:     width,
		height:    height,
		scale:     1.0,
		equipment: make(map[string]*models.Equipment),
		rooms:     make(map[string]*models.Room),
		legend:    make(map[rune]string),
	}

	// Initialize grid
	fr.initGrid()

	// Setup default legend
	fr.setupLegend()

	return fr
}

// initGrid initializes the ASCII grid with spaces
func (fr *FloorRenderer) initGrid() {
	fr.grid = make([][]rune, fr.height)
	for y := 0; y < fr.height; y++ {
		fr.grid[y] = make([]rune, fr.width)
		for x := 0; x < fr.width; x++ {
			fr.grid[y][x] = CharSpace
		}
	}
}

// setupLegend creates the default legend mappings
func (fr *FloorRenderer) setupLegend() {
	fr.legend[CharOutlet] = "Electrical Outlet"
	fr.legend[CharSwitch] = "Light Switch"
	fr.legend[CharPanel] = "Electrical Panel"
	fr.legend[CharHVAC] = "HVAC Unit"
	fr.legend[CharFireAlarm] = "Fire Alarm"
	fr.legend[CharCamera] = "Security Camera"
	fr.legend[CharAccessPoint] = "WiFi Access Point"
	fr.legend[CharDoor] = "Door"
	fr.legend[CharWindow] = "Window"
}

// RenderFromPDF converts PDF parse result to ASCII floor plan
func (fr *FloorRenderer) RenderFromPDF(parseResult *models.FloorPlan) (string, error) {
	if parseResult == nil {
		return "", fmt.Errorf("invalid parse result: no floor plan data")
	}

	// Calculate scale based on floor plan bounds
	fr.calculateScale(parseResult)

	// Clear grid
	fr.initGrid()

	// Render rooms
	for _, room := range parseResult.Rooms {
		fr.renderRoom(*room)
	}

	// Render equipment
	for _, equip := range parseResult.Equipment {
		fr.renderEquipment(*equip)
	}

	// Add room labels
	// Convert to value slice for labels
	rooms := make([]models.Room, len(parseResult.Rooms))
	for i, r := range parseResult.Rooms {
		rooms[i] = *r
	}
	fr.addRoomLabels(rooms)

	// Generate final output with legend
	return fr.generateOutput(), nil
}

// RenderFromFloorPlan renders an ASCII representation from a floor plan model
func (fr *FloorRenderer) RenderFromFloorPlan(plan *models.FloorPlan) (string, error) {
	if plan == nil {
		return "", fmt.Errorf("floor plan is nil")
	}

	// Use the new LayeredRenderer for the core rendering
	layeredRenderer := NewLayeredRenderer(fr.width-4, fr.height-8) // Leave space for borders and legends
	err := layeredRenderer.RenderFloorPlan(plan)
	if err != nil {
		return "", fmt.Errorf("failed to render with layer system: %w", err)
	}

	coreOutput := layeredRenderer.Render()

	// Wrap with the traditional formatted output
	return fr.generateFormattedOutput(plan, coreOutput), nil
}

// calculateScale determines the scale factor for fitting the floor plan
func (fr *FloorRenderer) calculateScale(floorPlan *models.FloorPlan) {
	// Calculate bounds from rooms
	if len(floorPlan.Rooms) == 0 {
		fr.scale = 1.0
		return
	}

	minX, minY := floorPlan.Rooms[0].Bounds.MinX, floorPlan.Rooms[0].Bounds.MinY
	maxX, maxY := floorPlan.Rooms[0].Bounds.MaxX, floorPlan.Rooms[0].Bounds.MaxY

	for _, room := range floorPlan.Rooms {
		if room.Bounds.MinX < minX {
			minX = room.Bounds.MinX
		}
		if room.Bounds.MinY < minY {
			minY = room.Bounds.MinY
		}
		if room.Bounds.MaxX > maxX {
			maxX = room.Bounds.MaxX
		}
		if room.Bounds.MaxY > maxY {
			maxY = room.Bounds.MaxY
		}
	}

	width := maxX - minX
	height := maxY - minY

	if width == 0 || height == 0 {
		fr.scale = 1.0
		return
	}

	scaleX := float64(fr.width-4) / width
	scaleY := float64(fr.height-4) / height
	fr.scale = math.Min(scaleX, scaleY)
}

// calculateScaleFromModel calculates scale from model bounds
func (fr *FloorRenderer) calculateScaleFromModel(plan *models.FloorPlan) {
	// Find min/max bounds from all rooms
	if len(plan.Rooms) == 0 {
		fr.scale = 1.0
		return
	}

	minX, minY := math.MaxFloat64, math.MaxFloat64
	maxX, maxY := -math.MaxFloat64, -math.MaxFloat64

	for _, room := range plan.Rooms {
		minX = math.Min(minX, room.Bounds.MinX)
		minY = math.Min(minY, room.Bounds.MinY)
		maxX = math.Max(maxX, room.Bounds.MaxX)
		maxY = math.Max(maxY, room.Bounds.MaxY)
	}

	width := maxX - minX
	height := maxY - minY

	if width == 0 || height == 0 {
		fr.scale = 1.0
		return
	}

	scaleX := float64(fr.width-4) / width
	scaleY := float64(fr.height-4) / height
	fr.scale = math.Min(scaleX, scaleY)
}

// renderWall renders a wall (currently not used as we render rooms instead)
func (fr *FloorRenderer) renderWall(x1, y1, x2, y2 int) {
	fr.drawLine(x1, y1, x2, y2)
}

// renderRoom renders a room boundary
func (fr *FloorRenderer) renderRoom(room models.Room) {
	x1 := int(room.Bounds.MinX*fr.scale) + 2
	y1 := int(room.Bounds.MinY*fr.scale) + 2
	x2 := int(room.Bounds.MaxX*fr.scale) + 2
	y2 := int(room.Bounds.MaxY*fr.scale) + 2

	// Draw room rectangle
	fr.drawRectangle(x1, y1, x2, y2)

	// Fill room with floor character
	for y := y1 + 1; y < y2; y++ {
		for x := x1 + 1; x < x2; x++ {
			if fr.getChar(x, y) == CharSpace {
				fr.setChar(x, y, CharFloor)
			}
		}
	}
}

// renderRoomModel renders a room from the model
func (fr *FloorRenderer) renderRoomModel(room *models.Room) {
	x1 := int(room.Bounds.MinX*fr.scale) + 2
	y1 := int(room.Bounds.MinY*fr.scale) + 2
	x2 := int(room.Bounds.MaxX*fr.scale) + 2
	y2 := int(room.Bounds.MaxY*fr.scale) + 2

	fr.drawRectangle(x1, y1, x2, y2)

	// Fill with floor character
	for y := y1 + 1; y < y2; y++ {
		for x := x1 + 1; x < x2; x++ {
			if fr.getChar(x, y) == CharSpace {
				fr.setChar(x, y, CharFloor)
			}
		}
	}

	fr.rooms[room.ID] = room
}

// renderEquipment renders equipment marker
func (fr *FloorRenderer) renderEquipment(equip models.Equipment) {
	x := int(equip.Location.X*fr.scale) + 2
	y := int(equip.Location.Y*fr.scale) + 2

	char := fr.getEquipmentChar(equip.Type)
	fr.setChar(x, y, char)
}

// renderEquipmentModel renders equipment from model
func (fr *FloorRenderer) renderEquipmentModel(equip *models.Equipment) {
	x := int(equip.Location.X*fr.scale) + 2
	y := int(equip.Location.Y*fr.scale) + 2

	char := fr.getEquipmentChar(equip.Type)
	fr.setChar(x, y, char)

	fr.equipment[equip.ID] = equip
}

// getEquipmentChar returns the appropriate character for equipment type
func (fr *FloorRenderer) getEquipmentChar(equipType string) rune {
	switch strings.ToLower(equipType) {
	case "outlet", "electrical_outlet":
		return CharOutlet
	case "switch", "light_switch":
		return CharSwitch
	case "panel", "electrical_panel":
		return CharPanel
	case "hvac", "air_conditioner", "heater":
		return CharHVAC
	case "fire_alarm", "smoke_detector":
		return CharFireAlarm
	case "camera", "security_camera":
		return CharCamera
	case "wifi", "access_point", "router":
		return CharAccessPoint
	default:
		return CharEquipmentOther
	}
}

// drawLine draws a line between two points
func (fr *FloorRenderer) drawLine(x1, y1, x2, y2 int) {
	dx := abs(x2 - x1)
	dy := abs(y2 - y1)

	// Determine if line is more horizontal or vertical
	if dx > dy {
		// Horizontal line
		if x1 > x2 {
			x1, x2 = x2, x1
		}
		for x := x1; x <= x2; x++ {
			fr.setChar(x, y1, CharWallHorizontal)
		}
	} else {
		// Vertical line
		if y1 > y2 {
			y1, y2 = y2, y1
		}
		for y := y1; y <= y2; y++ {
			fr.setChar(x1, y, CharWallVertical)
		}
	}
}

// drawRectangle draws a rectangle with proper corner characters
func (fr *FloorRenderer) drawRectangle(x1, y1, x2, y2 int) {
	// Ensure coordinates are ordered correctly
	if x1 > x2 {
		x1, x2 = x2, x1
	}
	if y1 > y2 {
		y1, y2 = y2, y1
	}

	// Top and bottom walls
	for x := x1 + 1; x < x2; x++ {
		fr.setChar(x, y1, CharWallHorizontal)
		fr.setChar(x, y2, CharWallHorizontal)
	}

	// Left and right walls
	for y := y1 + 1; y < y2; y++ {
		fr.setChar(x1, y, CharWallVertical)
		fr.setChar(x2, y, CharWallVertical)
	}

	// Corners
	fr.setChar(x1, y1, CharCornerTL)
	fr.setChar(x2, y1, CharCornerTR)
	fr.setChar(x1, y2, CharCornerBL)
	fr.setChar(x2, y2, CharCornerBR)
}

// addRoomLabels adds room name labels
func (fr *FloorRenderer) addRoomLabels(rooms []models.Room) {
	for _, room := range rooms {
		if room.Name == "" {
			continue
		}

		// Calculate center of room
		centerX := int((room.Bounds.MinX+room.Bounds.MaxX)/2*fr.scale) + 2
		centerY := int((room.Bounds.MinY+room.Bounds.MaxY)/2*fr.scale) + 2

		// Place label (truncate if necessary)
		label := room.Name
		if len(label) > 10 {
			label = label[:10]
		}

		// Center the label
		startX := centerX - len(label)/2
		for i, ch := range label {
			x := startX + i
			if fr.getChar(x, centerY) == CharFloor {
				fr.setChar(x, centerY, ch)
			}
		}
	}
}

// addRoomLabelsFromModel adds room labels from model
func (fr *FloorRenderer) addRoomLabelsFromModel(rooms []models.Room) {
	for _, room := range rooms {
		if room.Name == "" {
			continue
		}

		centerX := int((room.Bounds.MinX+room.Bounds.MaxX)/2*fr.scale) + 2
		centerY := int((room.Bounds.MinY+room.Bounds.MaxY)/2*fr.scale) + 2

		label := room.Name
		if len(label) > 10 {
			label = label[:10]
		}

		startX := centerX - len(label)/2
		for i, ch := range label {
			x := startX + i
			if fr.getChar(x, centerY) == CharFloor {
				fr.setChar(x, centerY, ch)
			}
		}
	}
}

// setChar safely sets a character in the grid
func (fr *FloorRenderer) setChar(x, y int, char rune) {
	if x >= 0 && x < fr.width && y >= 0 && y < fr.height {
		fr.grid[y][x] = char
	}
}

// getChar safely gets a character from the grid
func (fr *FloorRenderer) getChar(x, y int) rune {
	if x >= 0 && x < fr.width && y >= 0 && y < fr.height {
		return fr.grid[y][x]
	}
	return CharSpace
}

// generateOutput creates the final ASCII output with legend
func (fr *FloorRenderer) generateOutput() string {
	var sb strings.Builder

	// Add title
	sb.WriteString("╔" + strings.Repeat("═", fr.width-2) + "╗\n")
	title := " FLOOR PLAN "
	padding := (fr.width - len(title)) / 2
	sb.WriteString("║" + strings.Repeat(" ", padding) + title + strings.Repeat(" ", fr.width-padding-len(title)-2) + "║\n")
	sb.WriteString("╠" + strings.Repeat("═", fr.width-2) + "╣\n")

	// Add grid
	for y := 0; y < fr.height; y++ {
		sb.WriteString("║")
		for x := 0; x < fr.width; x++ {
			sb.WriteRune(fr.grid[y][x])
		}
		sb.WriteString("║\n")
	}

	// Add bottom border
	sb.WriteString("╠" + strings.Repeat("═", fr.width-2) + "╣\n")

	// Add legend
	sb.WriteString("║ LEGEND:" + strings.Repeat(" ", fr.width-10) + "║\n")

	usedChars := make(map[rune]bool)
	for y := 0; y < fr.height; y++ {
		for x := 0; x < fr.width; x++ {
			char := fr.grid[y][x]
			if _, exists := fr.legend[char]; exists {
				usedChars[char] = true
			}
		}
	}

	for char, description := range fr.legend {
		if usedChars[char] {
			line := fmt.Sprintf(" %c = %s", char, description)
			if len(line) > fr.width-4 {
				line = line[:fr.width-4]
			}
			sb.WriteString("║" + line + strings.Repeat(" ", fr.width-len(line)-2) + "║\n")
		}
	}

	// Add statistics
	sb.WriteString("╠" + strings.Repeat("═", fr.width-2) + "╣\n")
	stats := fmt.Sprintf(" Rooms: %d | Equipment: %d", len(fr.rooms), len(fr.equipment))
	sb.WriteString("║" + stats + strings.Repeat(" ", fr.width-len(stats)-2) + "║\n")

	// Close box
	sb.WriteString("╚" + strings.Repeat("═", fr.width-2) + "╝\n")

	return sb.String()
}

// generateFormattedOutput creates formatted output wrapping the layered renderer output
func (fr *FloorRenderer) generateFormattedOutput(plan *models.FloorPlan, coreOutput string) string {
	var sb strings.Builder

	// Add title
	sb.WriteString("╔" + strings.Repeat("═", fr.width-2) + "╗\n")
	title := " FLOOR PLAN "
	padding := (fr.width - len(title)) / 2
	sb.WriteString("║" + strings.Repeat(" ", padding) + title + strings.Repeat(" ", fr.width-padding-len(title)-2) + "║\n")
	sb.WriteString("╠" + strings.Repeat("═", fr.width-2) + "╣\n")

	// Split the core output into lines and center it
	lines := strings.Split(strings.TrimRight(coreOutput, "\n"), "\n")
	maxCoreWidth := 0
	for _, line := range lines {
		if len(line) > maxCoreWidth {
			maxCoreWidth = len(line)
		}
	}

	// Add the core output with proper padding
	for _, line := range lines {
		// Truncate line if it's too long
		if len(line) > fr.width-2 {
			line = line[:fr.width-2]
		}

		// Center the line within the frame
		leftPad := (fr.width - 2 - len(line)) / 2
		rightPad := fr.width - 2 - leftPad - len(line)
		if leftPad < 0 {
			leftPad = 0
		}
		if rightPad < 0 {
			rightPad = 0
		}
		sb.WriteString("║" + strings.Repeat(" ", leftPad) + line + strings.Repeat(" ", rightPad) + "║\n")
	}

	// Add bottom border
	sb.WriteString("╠" + strings.Repeat("═", fr.width-2) + "╣\n")

	// Add legend
	sb.WriteString("║ LEGEND:" + strings.Repeat(" ", fr.width-10) + "║\n")
	sb.WriteString("║ o = Electrical Outlet" + strings.Repeat(" ", fr.width-24) + "║\n")
	sb.WriteString("║ s = Light Switch" + strings.Repeat(" ", fr.width-19) + "║\n")
	sb.WriteString("║ P = Electrical Panel" + strings.Repeat(" ", fr.width-23) + "║\n")

	// Add statistics
	sb.WriteString("╠" + strings.Repeat("═", fr.width-2) + "╣\n")
	stats := fmt.Sprintf(" Rooms: %d | Equipment: %d", len(plan.Rooms), len(plan.Equipment))
	sb.WriteString("║" + stats + strings.Repeat(" ", fr.width-len(stats)-2) + "║\n")

	// Close box
	sb.WriteString("╚" + strings.Repeat("═", fr.width-2) + "╝\n")

	return sb.String()
}

// abs returns absolute value of integer

// GetASCII returns the current ASCII representation
func (fr *FloorRenderer) GetASCII() string {
	return fr.generateOutput()
}

// GetEquipmentAt returns equipment at a specific grid position
func (fr *FloorRenderer) GetEquipmentAt(x, y int) *models.Equipment {
	// This would need to track equipment positions
	// For now, return nil
	return nil
}

// HighlightEquipment highlights specific equipment on the floor plan
func (fr *FloorRenderer) HighlightEquipment(equipmentID string, highlightChar rune) {
	if equip, exists := fr.equipment[equipmentID]; exists {
		x := int(equip.Location.X*fr.scale) + 2
		y := int(equip.Location.Y*fr.scale) + 2
		fr.setChar(x, y, highlightChar)
	}
}
