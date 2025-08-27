package ascii

import (
	"fmt"
	"math"
	"regexp"
	"strconv"
	"strings"
)

// FloorBuilder constructs detailed floor plans from parsed data
type FloorBuilder struct {
	Renderer    *Renderer
	Rooms       []Room
	Corridors   []Corridor
	Scale       float64
	GridSize    float64 // Snap-to-grid size in feet
}

// Corridor represents a hallway or corridor
type Corridor struct {
	ID     string
	Bounds Rectangle
	Type   string // main, secondary, emergency
}

// NewFloorBuilder creates a new floor builder
func NewFloorBuilder() *FloorBuilder {
	return &FloorBuilder{
		Renderer: NewRenderer(120, 50),
		Scale:    2.0,  // 2 feet per character
		GridSize: 5.0,  // 5 foot grid
	}
}

// ParseFloorPlanText parses text-based floor plan data from PDF
func (fb *FloorBuilder) ParseFloorPlanText(text string) {
	lines := strings.Split(text, "\n")
	fb.Rooms = []Room{}
	
	// Patterns for detecting room information
	roomPattern := regexp.MustCompile(`(?i)(?:ROOM|RM|SPACE)\s*(\d+[A-Z]?)\s+(.+?)\s+(\d+)['\s]*x\s*(\d+)`)
	roomWithAreaPattern := regexp.MustCompile(`(?i)(?:ROOM|RM)\s*(\d+[A-Z]?)\s+(.+?)\s+(\d+)\s*(?:SF|SQ\.?\s*FT)`)
	doorPattern := regexp.MustCompile(`(?i)DOOR[:\s]+(.+?)(?:\s+|$)`)
	windowPattern := regexp.MustCompile(`(?i)WINDOW[:\s]+(\d+)['\s]*(?:x\s*(\d+))?`)
	
	var currentRoom *Room
	currentX, currentY := 0.0, 0.0
	
	for _, line := range lines {
		// Parse room with dimensions
		if matches := roomPattern.FindStringSubmatch(line); matches != nil {
			roomNum := matches[1]
			roomName := strings.TrimSpace(matches[2])
			width, _ := strconv.ParseFloat(matches[3], 64)
			depth, _ := strconv.ParseFloat(matches[4], 64)
			
			room := fb.createRoom(roomNum, roomName, currentX, currentY, width, depth)
			fb.Rooms = append(fb.Rooms, room)
			currentRoom = &fb.Rooms[len(fb.Rooms)-1]
			
			// Update position for next room (simple grid layout)
			currentX += width + 10 // 10 foot spacing
			if currentX > 200 { // Wrap to next row
				currentX = 0
				currentY += depth + 10
			}
		} else if matches := roomWithAreaPattern.FindStringSubmatch(line); matches != nil {
			// Room with area only - estimate dimensions
			roomNum := matches[1]
			roomName := strings.TrimSpace(matches[2])
			area, _ := strconv.ParseFloat(matches[3], 64)
			
			// Estimate dimensions (assume roughly square)
			width := math.Sqrt(area)
			depth := area / width
			
			room := fb.createRoom(roomNum, roomName, currentX, currentY, width, depth)
			fb.Rooms = append(fb.Rooms, room)
			currentRoom = &fb.Rooms[len(fb.Rooms)-1]
			
			currentX += width + 10
			if currentX > 200 {
				currentX = 0
				currentY += depth + 10
			}
		}
		
		// Parse door information
		if currentRoom != nil && doorPattern.MatchString(line) {
			matches := doorPattern.FindStringSubmatch(line)
			doorType := strings.ToLower(matches[1])
			
			// Add door to current room
			door := Door{
				Width: 3.0, // Standard door width
				Type:  "single",
			}
			
			if strings.Contains(doorType, "double") {
				door.Type = "double"
				door.Width = 6.0
			} else if strings.Contains(doorType, "sliding") {
				door.Type = "sliding"
			}
			
			// Place door on most likely wall
			fb.placeDoor(currentRoom, door)
		}
		
		// Parse window information
		if currentRoom != nil && windowPattern.MatchString(line) {
			matches := windowPattern.FindStringSubmatch(line)
			windowWidth, _ := strconv.ParseFloat(matches[1], 64)
			
			window := Window{
				Width: windowWidth,
				Type:  "fixed",
			}
			
			fb.placeWindow(currentRoom, window)
		}
	}
	
	// Optimize room layout
	fb.optimizeLayout()
}

// createRoom creates a room with walls
func (fb *FloorBuilder) createRoom(number, name string, x, y, width, depth float64) Room {
	room := Room{
		ID:     fmt.Sprintf("room_%s", number),
		Number: number,
		Name:   name,
		Bounds: Rectangle{
			X:      x,
			Y:      y,
			Width:  width,
			Height: depth,
		},
		Walls:     []Wall{},
		Doors:     []Door{},
		Windows:   []Window{},
		Equipment: []Equipment{},
	}
	
	// Create walls
	// North wall
	room.Walls = append(room.Walls, Wall{
		Start:     Point{x, y},
		End:       Point{x + width, y},
		Type:      "interior",
		Thickness: 0.5,
	})
	
	// South wall
	room.Walls = append(room.Walls, Wall{
		Start:     Point{x, y + depth},
		End:       Point{x + width, y + depth},
		Type:      "interior",
		Thickness: 0.5,
	})
	
	// West wall
	room.Walls = append(room.Walls, Wall{
		Start:     Point{x, y},
		End:       Point{x, y + depth},
		Type:      "interior",
		Thickness: 0.5,
	})
	
	// East wall
	room.Walls = append(room.Walls, Wall{
		Start:     Point{x + width, y},
		End:       Point{x + width, y + depth},
		Type:      "interior",
		Thickness: 0.5,
	})
	
	return room
}

// placeDoor intelligently places a door on a room
func (fb *FloorBuilder) placeDoor(room *Room, door Door) {
	// Typically place door on the south wall or wall facing corridor
	// For now, place on south wall at 1/3 position
	
	door.Position = Point{
		X: room.Bounds.X + room.Bounds.Width/3,
		Y: room.Bounds.Y + room.Bounds.Height,
	}
	door.Wall = "south"
	door.SwingDir = "in"
	
	room.Doors = append(room.Doors, door)
	
	// Mark wall as having door
	for i := range room.Walls {
		if room.Walls[i].Start.Y == door.Position.Y || room.Walls[i].End.Y == door.Position.Y {
			room.Walls[i].HasDoor = true
			break
		}
	}
}

// placeWindow places a window on an exterior wall
func (fb *FloorBuilder) placeWindow(room *Room, window Window) {
	// Determine which walls are likely exterior
	// For now, place on north wall if y=0, or east/west walls
	
	if room.Bounds.Y == 0 {
		// North wall - likely exterior
		window.Position = Point{
			X: room.Bounds.X + room.Bounds.Width/2,
			Y: room.Bounds.Y,
		}
		window.Wall = "north"
	} else {
		// East wall
		window.Position = Point{
			X: room.Bounds.X + room.Bounds.Width,
			Y: room.Bounds.Y + room.Bounds.Height/2,
		}
		window.Wall = "east"
	}
	
	room.Windows = append(room.Windows, window)
	
	// Mark wall as having window
	for i := range room.Walls {
		wall := &room.Walls[i]
		if (window.Wall == "north" && wall.Start.Y == room.Bounds.Y) ||
		   (window.Wall == "east" && wall.Start.X == room.Bounds.X+room.Bounds.Width) {
			wall.HasWindow = true
			break
		}
	}
}

// optimizeLayout arranges rooms in a more realistic layout
func (fb *FloorBuilder) optimizeLayout() {
	if len(fb.Rooms) == 0 {
		return
	}
	
	// Find rooms that should be adjacent (sequential room numbers)
	for i := 0; i < len(fb.Rooms)-1; i++ {
		room1 := &fb.Rooms[i]
		room2 := &fb.Rooms[i+1]
		
		// Check if room numbers are sequential
		num1, _ := strconv.Atoi(strings.TrimSuffix(room1.Number, "A"))
		num2, _ := strconv.Atoi(strings.TrimSuffix(room2.Number, "A"))
		
		if num2 == num1+1 {
			// Place room2 adjacent to room1
			fb.makeAdjacent(room1, room2)
		}
	}
	
	// Add corridors between room groups
	fb.addCorridors()
	
	// Upgrade shared walls to proper types
	fb.updateWallTypes()
}

// makeAdjacent places room2 adjacent to room1
func (fb *FloorBuilder) makeAdjacent(room1, room2 *Room) {
	// Place room2 to the right of room1 if possible
	room2.Bounds.X = room1.Bounds.X + room1.Bounds.Width
	room2.Bounds.Y = room1.Bounds.Y
	
	// Update walls
	fb.updateRoomWalls(room2)
	
	// Merge adjacent walls
	fb.mergeAdjacentWalls(room1, room2)
}

// updateRoomWalls updates wall positions based on room bounds
func (fb *FloorBuilder) updateRoomWalls(room *Room) {
	x := room.Bounds.X
	y := room.Bounds.Y
	width := room.Bounds.Width
	height := room.Bounds.Height
	
	// Update wall positions
	if len(room.Walls) >= 4 {
		// North wall
		room.Walls[0].Start = Point{x, y}
		room.Walls[0].End = Point{x + width, y}
		
		// South wall
		room.Walls[1].Start = Point{x, y + height}
		room.Walls[1].End = Point{x + width, y + height}
		
		// West wall
		room.Walls[2].Start = Point{x, y}
		room.Walls[2].End = Point{x, y + height}
		
		// East wall
		room.Walls[3].Start = Point{x + width, y}
		room.Walls[3].End = Point{x + width, y + height}
	}
}

// mergeAdjacentWalls combines walls between adjacent rooms
func (fb *FloorBuilder) mergeAdjacentWalls(room1, room2 *Room) {
	// Check if rooms share a wall
	for i := range room1.Walls {
		wall1 := &room1.Walls[i]
		for j := range room2.Walls {
			wall2 := &room2.Walls[j]
			
			// Check if walls are the same (opposite sides of same wall)
			if (wall1.Start == wall2.End && wall1.End == wall2.Start) ||
			   (wall1.Start == wall2.Start && wall1.End == wall2.End) {
				// This is a shared wall - mark as interior partition
				wall1.Type = "partition"
				wall2.Type = "partition"
			}
		}
	}
}

// addCorridors adds corridors to connect rooms
func (fb *FloorBuilder) addCorridors() {
	// Simple corridor addition - create a main corridor
	if len(fb.Rooms) < 2 {
		return
	}
	
	// Find the bounds of all rooms
	minY := fb.Rooms[0].Bounds.Y
	maxY := minY + fb.Rooms[0].Bounds.Height
	minX := fb.Rooms[0].Bounds.X
	maxX := minX + fb.Rooms[0].Bounds.Width
	
	for _, room := range fb.Rooms[1:] {
		minY = math.Min(minY, room.Bounds.Y)
		maxY = math.Max(maxY, room.Bounds.Y+room.Bounds.Height)
		minX = math.Min(minX, room.Bounds.X)
		maxX = math.Max(maxX, room.Bounds.X+room.Bounds.Width)
	}
	
	// Create main corridor along the south of rooms
	corridor := Corridor{
		ID: "main_corridor",
		Bounds: Rectangle{
			X:      minX,
			Y:      maxY + 2,
			Width:  maxX - minX,
			Height: 8, // 8 foot wide corridor
		},
		Type: "main",
	}
	
	fb.Corridors = append(fb.Corridors, corridor)
	
	// Update room doors to open to corridor
	for i := range fb.Rooms {
		room := &fb.Rooms[i]
		if len(room.Doors) > 0 {
			// Move door to face corridor
			room.Doors[0].Position.Y = room.Bounds.Y + room.Bounds.Height
		}
	}
}

// updateWallTypes updates wall types based on location
func (fb *FloorBuilder) updateWallTypes() {
	// Determine exterior walls
	if len(fb.Rooms) == 0 {
		return
	}
	
	// Find overall building bounds
	minX, minY := fb.Rooms[0].Bounds.X, fb.Rooms[0].Bounds.Y
	maxX := minX + fb.Rooms[0].Bounds.Width
	maxY := minY + fb.Rooms[0].Bounds.Height
	
	for _, room := range fb.Rooms[1:] {
		minX = math.Min(minX, room.Bounds.X)
		minY = math.Min(minY, room.Bounds.Y)
		maxX = math.Max(maxX, room.Bounds.X+room.Bounds.Width)
		maxY = math.Max(maxY, room.Bounds.Y+room.Bounds.Height)
	}
	
	// Mark exterior walls
	for i := range fb.Rooms {
		room := &fb.Rooms[i]
		for j := range room.Walls {
			wall := &room.Walls[j]
			
			// Check if wall is on building perimeter
			isExterior := false
			
			// North wall
			if wall.Start.Y == minY && wall.End.Y == minY {
				isExterior = true
			}
			// South wall
			if wall.Start.Y == maxY && wall.End.Y == maxY {
				isExterior = true
			}
			// West wall
			if wall.Start.X == minX && wall.End.X == minX {
				isExterior = true
			}
			// East wall
			if wall.Start.X == maxX && wall.End.X == maxX {
				isExterior = true
			}
			
			if isExterior {
				wall.Type = "exterior"
				wall.Thickness = 1.0 // Thicker exterior walls
			}
		}
	}
}

// AddEquipment adds equipment to rooms based on type
func (fb *FloorBuilder) AddEquipment(roomNumber string, equipment []Equipment) {
	for i := range fb.Rooms {
		if fb.Rooms[i].Number == roomNumber {
			fb.Rooms[i].Equipment = append(fb.Rooms[i].Equipment, equipment...)
			
			// Position equipment intelligently
			fb.positionEquipment(&fb.Rooms[i])
			break
		}
	}
}

// positionEquipment places equipment at logical positions in room
func (fb *FloorBuilder) positionEquipment(room *Room) {
	for i := range room.Equipment {
		eq := &room.Equipment[i]
		
		switch eq.Type {
		case "outlet", "outlet_duplex":
			// Place outlets along walls at standard height
			// Distribute along perimeter
			eq.Position = Point{
				X: room.Bounds.X + 2, // 2 feet from corner
				Y: room.Bounds.Y + room.Bounds.Height - 0.5, // Near wall
			}
			
		case "switch", "switch_3way":
			// Place switches near doors
			if len(room.Doors) > 0 {
				door := room.Doors[0]
				eq.Position = Point{
					X: door.Position.X + 2,
					Y: door.Position.Y,
				}
			} else {
				eq.Position = Point{
					X: room.Bounds.X + 2,
					Y: room.Bounds.Y + 0.5,
				}
			}
			
		case "diffuser", "return":
			// HVAC in ceiling - place in center
			eq.Position = Point{
				X: room.Bounds.X + room.Bounds.Width/2,
				Y: room.Bounds.Y + room.Bounds.Height/2,
			}
			
		case "thermostat":
			// Place on interior wall at 4 feet height
			eq.Position = Point{
				X: room.Bounds.X + room.Bounds.Width - 1,
				Y: room.Bounds.Y + room.Bounds.Height/2,
			}
		}
	}
}

// Render creates the final ASCII visualization
func (fb *FloorBuilder) Render() string {
	// Auto-fit to canvas
	fb.autoFit()
	
	// Set detail level
	fb.Renderer.DetailLevel = 3 // Maximum detail
	
	// Render rooms
	fb.Renderer.RenderFloorPlan(fb.Rooms)
	
	// Render corridors
	for _, corridor := range fb.Corridors {
		fb.renderCorridor(corridor)
	}
	
	// Add title and legend
	output := fb.addHeader()
	output += fb.Renderer.ToString()
	output += fb.addLegend()
	
	return output
}

// autoFit adjusts scale and offset to fit all rooms
func (fb *FloorBuilder) autoFit() {
	if len(fb.Rooms) == 0 {
		return
	}
	
	// Find bounds
	minX, minY := fb.Rooms[0].Bounds.X, fb.Rooms[0].Bounds.Y
	maxX := minX + fb.Rooms[0].Bounds.Width
	maxY := minY + fb.Rooms[0].Bounds.Height
	
	for _, room := range fb.Rooms[1:] {
		minX = math.Min(minX, room.Bounds.X)
		minY = math.Min(minY, room.Bounds.Y)
		maxX = math.Max(maxX, room.Bounds.X+room.Bounds.Width)
		maxY = math.Max(maxY, room.Bounds.Y+room.Bounds.Height)
	}
	
	// Include corridors
	for _, corridor := range fb.Corridors {
		minX = math.Min(minX, corridor.Bounds.X)
		minY = math.Min(minY, corridor.Bounds.Y)
		maxX = math.Max(maxX, corridor.Bounds.X+corridor.Bounds.Width)
		maxY = math.Max(maxY, corridor.Bounds.Y+corridor.Bounds.Height)
	}
	
	// Calculate scale to fit
	width := maxX - minX
	height := maxY - minY
	
	scaleX := width / float64(fb.Renderer.Width-10)
	scaleY := height / float64(fb.Renderer.Height-10)
	
	fb.Renderer.Scale = math.Max(scaleX, scaleY)
	if fb.Renderer.Scale < 1.0 {
		fb.Renderer.Scale = 1.0
	}
	
	// Center in canvas
	fb.Renderer.OffsetX = minX - 5
	fb.Renderer.OffsetY = minY - 5
}

// renderCorridor renders a corridor
func (fb *FloorBuilder) renderCorridor(corridor Corridor) {
	// Draw corridor as open space with dashed boundaries
	x1, y1 := fb.Renderer.worldToCanvas(corridor.Bounds.X, corridor.Bounds.Y)
	x2, y2 := fb.Renderer.worldToCanvas(
		corridor.Bounds.X+corridor.Bounds.Width,
		corridor.Bounds.Y+corridor.Bounds.Height,
	)
	
	// Draw dashed lines for corridor boundaries
	for x := x1; x <= x2; x++ {
		if x%2 == 0 {
			fb.Renderer.setChar(x, y1, '·')
			fb.Renderer.setChar(x, y2, '·')
		}
	}
	
	// Label corridor
	centerX := (x1 + x2) / 2
	centerY := (y1 + y2) / 2
	fb.Renderer.drawText(centerX, centerY, "CORRIDOR", true)
}

// addHeader adds a title header
func (fb *FloorBuilder) addHeader() string {
	header := "\n╔════════════════════════════════════════════════════════════════════╗\n"
	header += "║                      FLOOR PLAN - DETAILED VIEW                    ║\n"
	header += "╚════════════════════════════════════════════════════════════════════╝\n\n"
	return header
}

// addLegend adds a legend for symbols
func (fb *FloorBuilder) addLegend() string {
	legend := "\n╔═══════════════ LEGEND ═══════════════╗\n"
	legend += "║ WALLS:                                ║\n"
	legend += "║   ═══ Exterior Wall                   ║\n"
	legend += "║   ─── Interior Wall                   ║\n"
	legend += "║   ··· Partition                       ║\n"
	legend += "║                                       ║\n"
	legend += "║ OPENINGS:                             ║\n"
	legend += "║   ◦   Single Door                     ║\n"
	legend += "║   ⟨ ⟩ Double Door                     ║\n"
	legend += "║   ≈≈≈ Window                          ║\n"
	legend += "║                                       ║\n"
	legend += "║ ELECTRICAL:                           ║\n"
	legend += "║   ⊙   Outlet      ◈   Switch          ║\n"
	legend += "║   ☀   Light       ▣   Panel           ║\n"
	legend += "║                                       ║\n"
	legend += "║ HVAC:                                 ║\n"
	legend += "║   ╬   Diffuser    ╪   Return          ║\n"
	legend += "║   ◫   Thermostat  ▢   VAV Box         ║\n"
	legend += "╚═══════════════════════════════════════╝\n"
	
	return legend
}