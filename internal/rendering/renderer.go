// Package rendering provides 3D ASCII isometric rendering for building visualization
package rendering

import (
	"fmt"
	"math"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
)

// Renderer provides 3D isometric ASCII rendering
type Renderer struct {
	width      int
	height     int
	depth      int
	viewAngle  float64 // Rotation angle for isometric view
	tiltAngle  float64 // Tilt angle from horizontal
	scale      float64
	buffer     [][]rune
	depthBuffer [][]float64
	origin     Point3D
}

// Point3D represents a point in 3D space
type Point3D struct {
	X, Y, Z float64
}

// Point2D represents a projected 2D point
type Point2D struct {
	X, Y float64
}

// ViewMode represents different isometric view angles
type ViewMode string

const (
	ViewIsometric   ViewMode = "isometric"   // Classic 30-degree isometric
	ViewDimetric    ViewMode = "dimetric"    // Two equal angles
	ViewTrimetric   ViewMode = "trimetric"   // Three different angles
	ViewTopDown     ViewMode = "topdown"     // Traditional 2D view
	ViewFrontSide   ViewMode = "frontside"   // Front elevation
	ViewRightSide   ViewMode = "rightside"   // Right elevation
)

// NewRenderer creates a new 3D isometric renderer
func NewRenderer(width, height, depth int) *Renderer {
	r := &Renderer{
		width:      width,
		height:     height,
		depth:      depth,
		viewAngle:  math.Pi / 6,  // 30 degrees for isometric
		tiltAngle:  math.Pi / 6,  // 30 degrees tilt
		scale:      1.0,
		buffer:     make([][]rune, height),
		depthBuffer: make([][]float64, height),
		origin:     Point3D{X: float64(width) / 2, Y: float64(height) / 2, Z: 0},
	}

	// Initialize buffers
	for i := range r.buffer {
		r.buffer[i] = make([]rune, width)
		r.depthBuffer[i] = make([]float64, width)
		for j := range r.buffer[i] {
			r.buffer[i][j] = ' '
			r.depthBuffer[i][j] = math.MaxFloat64
		}
	}

	return r
}

// SetViewMode sets predefined view angles
func (r *Renderer) SetViewMode(mode ViewMode) {
	switch mode {
	case ViewIsometric:
		r.viewAngle = math.Pi / 6  // 30 degrees
		r.tiltAngle = math.Pi / 6  // 30 degrees
	case ViewDimetric:
		r.viewAngle = math.Pi / 4  // 45 degrees
		r.tiltAngle = math.Pi / 6  // 30 degrees
	case ViewTrimetric:
		r.viewAngle = math.Pi / 5  // 36 degrees
		r.tiltAngle = math.Pi / 4  // 45 degrees
	case ViewTopDown:
		r.viewAngle = 0
		r.tiltAngle = math.Pi / 2  // 90 degrees (looking straight down)
	case ViewFrontSide:
		r.viewAngle = 0
		r.tiltAngle = 0
	case ViewRightSide:
		r.viewAngle = math.Pi / 2
		r.tiltAngle = 0
	}
}

// Project3DTo2D converts 3D coordinates to 2D screen coordinates using isometric projection
func (r *Renderer) Project3DTo2D(point Point3D) Point2D {
	// Apply rotation around Y axis (viewAngle)
	x := point.X*math.Cos(r.viewAngle) - point.Z*math.Sin(r.viewAngle)
	z := point.X*math.Sin(r.viewAngle) + point.Z*math.Cos(r.viewAngle)
	y := point.Y

	// Apply rotation around X axis (tiltAngle)
	yFinal := y*math.Cos(r.tiltAngle) - z*math.Sin(r.tiltAngle)
	// zFinal is the depth after rotation (used for depth testing but not for 2D projection)
	// _ = y*math.Sin(r.tiltAngle) + z*math.Cos(r.tiltAngle)

	// Project to 2D (orthographic projection after rotation)
	// Scale and center
	screenX := x*r.scale + r.origin.X
	screenY := yFinal*r.scale + r.origin.Y

	return Point2D{X: screenX, Y: screenY}
}

// Clear clears the render buffer
func (r *Renderer) Clear() {
	for i := range r.buffer {
		for j := range r.buffer[i] {
			r.buffer[i][j] = ' '
			r.depthBuffer[i][j] = math.MaxFloat64
		}
	}
}

// DrawBox draws a 3D box in isometric view
func (r *Renderer) DrawBox(x, y, z, width, height, depth float64, symbol rune) {
	// Define 8 vertices of the box
	vertices := []Point3D{
		{x, y, z},                          // 0: front bottom left
		{x + width, y, z},                  // 1: front bottom right
		{x + width, y + height, z},         // 2: front top right
		{x, y + height, z},                 // 3: front top left
		{x, y, z + depth},                  // 4: back bottom left
		{x + width, y, z + depth},          // 5: back bottom right
		{x + width, y + height, z + depth}, // 6: back top right
		{x, y + height, z + depth},         // 7: back top left
	}

	// Define edges (pairs of vertex indices)
	edges := [][2]int{
		// Front face
		{0, 1}, {1, 2}, {2, 3}, {3, 0},
		// Back face
		{4, 5}, {5, 6}, {6, 7}, {7, 4},
		// Connecting edges
		{0, 4}, {1, 5}, {2, 6}, {3, 7},
	}

	// Draw edges
	for _, edge := range edges {
		v1 := vertices[edge[0]]
		v2 := vertices[edge[1]]
		r.DrawLine3D(v1, v2, symbol)
	}

	// Draw corner markers for visibility
	for _, v := range vertices {
		p := r.Project3DTo2D(v)
		r.SetPixel(int(p.X), int(p.Y), '+', v.Z)
	}
}

// DrawLine3D draws a line between two 3D points
func (r *Renderer) DrawLine3D(p1, p2 Point3D, symbol rune) {
	// Project to 2D
	start := r.Project3DTo2D(p1)
	end := r.Project3DTo2D(p2)

	// Bresenham's line algorithm in 2D
	r.DrawLine2D(start, end, symbol, (p1.Z+p2.Z)/2)
}

// DrawLine2D draws a line between two 2D points
func (r *Renderer) DrawLine2D(p1, p2 Point2D, symbol rune, depth float64) {
	x0, y0 := int(p1.X), int(p1.Y)
	x1, y1 := int(p2.X), int(p2.Y)

	dx := abs(x1 - x0)
	dy := abs(y1 - y0)
	sx := 1
	sy := 1

	if x0 > x1 {
		sx = -1
	}
	if y0 > y1 {
		sy = -1
	}

	err := dx - dy

	for {
		r.SetPixel(x0, y0, symbol, depth)

		if x0 == x1 && y0 == y1 {
			break
		}

		e2 := 2 * err
		if e2 > -dy {
			err -= dy
			x0 += sx
		}
		if e2 < dx {
			err += dx
			y0 += sy
		}
	}
}

// SetPixel sets a pixel with depth testing
func (r *Renderer) SetPixel(x, y int, symbol rune, depth float64) {
	if x >= 0 && x < r.width && y >= 0 && y < r.height {
		// Only draw if this pixel is closer than what's already there
		if depth < r.depthBuffer[y][x] {
			r.buffer[y][x] = symbol
			r.depthBuffer[y][x] = depth
		}
	}
}

// RenderFloorPlan renders a floor plan in 3D isometric view
func (r *Renderer) RenderFloorPlan(plan *models.FloorPlan, floorZ float64) {
	r.Clear()

	// Draw rooms as 3D boxes
	for _, room := range plan.Rooms {
		r.DrawRoom(*room, floorZ)
	}

	// Draw equipment at their positions
	for _, equip := range plan.Equipment {
		r.DrawEquipment(*equip, floorZ)
	}

	// Draw floor grid for reference
	r.DrawFloorGrid(floorZ)
}

// DrawRoom draws a room as a 3D box
func (r *Renderer) DrawRoom(room models.Room, floorZ float64) {
	wallHeight := 10.0 // Standard wall height

	// Draw room box
	r.DrawBox(
		room.Bounds.MinX,
		floorZ,
		room.Bounds.MinY,
		room.Bounds.Width(),
		wallHeight,
		room.Bounds.Height(),
		'│',
	)

	// Draw room label
	centerX := (room.Bounds.MinX + room.Bounds.MaxX) / 2
	centerY := (room.Bounds.MinY + room.Bounds.MaxY) / 2
	labelPoint := r.Project3DTo2D(Point3D{X: centerX, Y: floorZ + 1, Z: centerY})
	
	// Place room name
	r.DrawText(int(labelPoint.X), int(labelPoint.Y), room.Name, floorZ)
}

// DrawEquipment draws equipment in 3D space
func (r *Renderer) DrawEquipment(equip models.Equipment, floorZ float64) {
	// Different symbols for different equipment types
	symbol := r.GetEquipmentSymbol(equip.Type)
	
	// Equipment is slightly above floor level
	equipPoint := Point3D{
		X: equip.Location.X,
		Y: floorZ + 2,
		Z: equip.Location.Y,
	}

	// Project to screen
	screenPoint := r.Project3DTo2D(equipPoint)
	
	// Draw equipment with status indication
	if equip.Status == models.StatusFailed {
		symbol = '✗'
	} else if equip.Status == models.StatusDegraded {
		symbol = '⚠'
	}

	r.SetPixel(int(screenPoint.X), int(screenPoint.Y), symbol, equipPoint.Z)

	// Draw vertical line to show height
	basePoint := Point3D{X: equip.Location.X, Y: floorZ, Z: equip.Location.Y}
	r.DrawLine3D(basePoint, equipPoint, '┊')
}

// GetEquipmentSymbol returns appropriate symbol for equipment type
func (r *Renderer) GetEquipmentSymbol(equipType string) rune {
	symbols := map[string]rune{
		"outlet":       '●',
		"switch":       '▪',
		"panel":        '▣',
		"light":        '◊',
		"sensor":       '◉',
		"alarm":        '🔔',
		"junction_box": '▫',
		"appliance":    '▤',
		"default":      '•',
	}

	if symbol, exists := symbols[equipType]; exists {
		return symbol
	}
	return symbols["default"]
}

// DrawFloorGrid draws a reference grid on the floor
func (r *Renderer) DrawFloorGrid(floorZ float64) {
	gridSize := 10.0
	maxSize := 100.0

	// Draw grid lines
	for x := 0.0; x <= maxSize; x += gridSize {
		// X-parallel lines
		r.DrawLine3D(
			Point3D{X: x, Y: floorZ, Z: 0},
			Point3D{X: x, Y: floorZ, Z: maxSize},
			'·',
		)
	}

	for z := 0.0; z <= maxSize; z += gridSize {
		// Z-parallel lines
		r.DrawLine3D(
			Point3D{X: 0, Y: floorZ, Z: z},
			Point3D{X: maxSize, Y: floorZ, Z: z},
			'·',
		)
	}
}

// DrawText draws text at a specific position
func (r *Renderer) DrawText(x, y int, text string, depth float64) {
	for i, ch := range text {
		r.SetPixel(x+i, y, ch, depth)
	}
}

// Render returns the rendered ASCII output
func (r *Renderer) Render() string {
	var output strings.Builder
	
	for _, row := range r.buffer {
		output.WriteString(string(row))
		output.WriteRune('\n')
	}
	
	return output.String()
}

// RenderMultiFloor renders multiple floors in isometric view
func (r *Renderer) RenderMultiFloor(floors []*models.FloorPlan, floorHeight float64) {
	r.Clear()

	for i, floor := range floors {
		floorZ := float64(i) * floorHeight
		
		// Draw this floor
		for _, room := range floor.Rooms {
			r.DrawRoom(*room, floorZ)
		}
		
		for _, equip := range floor.Equipment {
			r.DrawEquipment(*equip, floorZ)
		}
		
		// Draw floor separator
		if i > 0 {
			r.DrawFloorSeparator(floorZ)
		}
	}
}

// DrawFloorSeparator draws a visual separator between floors
func (r *Renderer) DrawFloorSeparator(floorZ float64) {
	maxSize := 100.0
	step := 5.0
	
	for x := 0.0; x <= maxSize; x += step {
		for z := 0.0; z <= maxSize; z += step {
			point := r.Project3DTo2D(Point3D{X: x, Y: floorZ, Z: z})
			r.SetPixel(int(point.X), int(point.Y), '─', floorZ)
		}
	}
}

// Utility functions


// RotateView rotates the viewing angle
func (r *Renderer) RotateView(deltaAngle float64) {
	r.viewAngle += deltaAngle
	// Keep angle in 0-2π range
	for r.viewAngle > 2*math.Pi {
		r.viewAngle -= 2 * math.Pi
	}
	for r.viewAngle < 0 {
		r.viewAngle += 2 * math.Pi
	}
	logger.Debug("View angle: %.2f degrees", r.viewAngle*180/math.Pi)
}

// TiltView adjusts the tilt angle
func (r *Renderer) TiltView(deltaTilt float64) {
	r.tiltAngle += deltaTilt
	// Clamp tilt between 0 and π/2 (0-90 degrees)
	if r.tiltAngle < 0 {
		r.tiltAngle = 0
	}
	if r.tiltAngle > math.Pi/2 {
		r.tiltAngle = math.Pi / 2
	}
	logger.Debug("Tilt angle: %.2f degrees", r.tiltAngle*180/math.Pi)
}

// Zoom adjusts the scale factor
func (r *Renderer) Zoom(factor float64) {
	r.scale *= factor
	// Clamp scale to reasonable bounds
	if r.scale < 0.1 {
		r.scale = 0.1
	}
	if r.scale > 10.0 {
		r.scale = 10.0
	}
	logger.Debug("Scale: %.2f", r.scale)
}

// GetViewInfo returns current view parameters
func (r *Renderer) GetViewInfo() string {
	return fmt.Sprintf("View: %.0f° Tilt: %.0f° Scale: %.1fx",
		r.viewAngle*180/math.Pi,
		r.tiltAngle*180/math.Pi,
		r.scale)
}