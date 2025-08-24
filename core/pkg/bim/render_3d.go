package bim

import (
	"fmt"
	"math"
	"sort"
)

// Camera represents the 3D viewport camera
type Camera struct {
	Position Point3D
	Target   Point3D
	Up       Point3D
	FOV      float64 // Field of view in degrees
	Near     float64
	Far      float64
	
	// Isometric parameters
	IsometricAngle float64 // 30 degrees for standard isometric
	Zoom           float64
}

// NewIsometricCamera creates a camera for isometric projection
func NewIsometricCamera() *Camera {
	return &Camera{
		Position:       Point3D{X: 1000, Y: 1000, Z: 1000},
		Target:         Point3D{X: 0, Y: 0, Z: 0},
		Up:             Point3D{X: 0, Y: 0, Z: 1},
		IsometricAngle: 30.0, // Standard isometric angle
		Zoom:           1.0,
	}
}

// Project3DToIsometric converts 3D coordinates to isometric 2D projection
func (c *Camera) Project3DToIsometric(point Point3D) (x, y float64) {
	// Isometric projection matrix
	// x_screen = (x - y) * cos(30°)
	// y_screen = (x + y) * sin(30°) - z
	
	angleRad := c.IsometricAngle * math.Pi / 180
	cos30 := math.Cos(angleRad)
	sin30 := math.Sin(angleRad)
	
	x = (point.X - point.Y) * cos30 * c.Zoom
	y = ((point.X + point.Y) * sin30 - point.Z) * c.Zoom
	
	return x, y
}

// RenderFloorTo3DSVG renders a floor in isometric 3D as SVG
func (f *Floor) RenderFloorTo3DSVG(camera *Camera) string {
	svg := fmt.Sprintf(`<g id="floor-%d" data-elevation="%.0f">`, f.Number, f.Elevation)
	
	// Sort walls by depth for proper rendering order
	sortedWalls := make([]*Wall, len(f.Walls))
	copy(sortedWalls, f.Walls)
	sort.Slice(sortedWalls, func(i, j int) bool {
		// Sort by average Y position (back to front)
		avgY1 := (sortedWalls[i].StartPoint.Y + sortedWalls[i].EndPoint.Y) / 2
		avgY2 := (sortedWalls[j].StartPoint.Y + sortedWalls[j].EndPoint.Y) / 2
		return avgY1 < avgY2
	})
	
	// Render floor slab first
	svg += f.renderFloorSlab3D(camera)
	
	// Render walls with 3D extrusion
	for _, wall := range sortedWalls {
		svg += wall.render3DSVG(camera, f.Elevation)
	}
	
	// Render rooms (semi-transparent overlays)
	for _, room := range f.Rooms {
		svg += room.render3DSVG(camera, f.Elevation)
	}
	
	svg += `</g>`
	return svg
}

func (f *Floor) renderFloorSlab3D(camera *Camera) string {
	// Find floor boundaries
	minX, minY := 1000000.0, 1000000.0
	maxX, maxY := -1000000.0, -1000000.0
	
	for _, wall := range f.Walls {
		minX = math.Min(minX, math.Min(wall.StartPoint.X, wall.EndPoint.X))
		minY = math.Min(minY, math.Min(wall.StartPoint.Y, wall.EndPoint.Y))
		maxX = math.Max(maxX, math.Max(wall.StartPoint.X, wall.EndPoint.X))
		maxY = math.Max(maxY, math.Max(wall.StartPoint.Y, wall.EndPoint.Y))
	}
	
	// Create floor slab corners
	corners := []Point3D{
		{X: minX, Y: minY, Z: f.Elevation},
		{X: maxX, Y: minY, Z: f.Elevation},
		{X: maxX, Y: maxY, Z: f.Elevation},
		{X: minX, Y: maxY, Z: f.Elevation},
	}
	
	// Project to 2D
	points := ""
	for _, corner := range corners {
		x, y := camera.Project3DToIsometric(corner)
		points += fmt.Sprintf("%.1f,%.1f ", x, y)
	}
	
	return fmt.Sprintf(
		`<polygon points="%s" fill="#f0f0f0" stroke="#ccc" stroke-width="1" opacity="0.5"/>`,
		points,
	)
}

func (w *Wall) render3DSVG(camera *Camera, floorElevation float64) string {
	// Create 3D wall vertices (8 corners of the wall box)
	vertices := w.getWall3DVertices(floorElevation)
	
	// Define faces (quads) - order matters for visibility
	faces := []struct {
		indices []int
		name    string
		color   string
	}{
		{[]int{0, 1, 5, 4}, "front", "#666"},  // Front face
		{[]int{2, 3, 7, 6}, "back", "#777"},   // Back face
		{[]int{0, 2, 6, 4}, "left", "#888"},   // Left face
		{[]int{1, 3, 7, 5}, "right", "#888"},  // Right face
		{[]int{4, 5, 7, 6}, "top", "#555"},    // Top face
	}
	
	svg := fmt.Sprintf(`<g class="wall-3d" data-id="%s">`, w.ID)
	
	// Render each face
	for _, face := range faces {
		if !w.isFaceVisible(vertices, face.indices, camera) {
			continue // Skip back-facing polygons
		}
		
		points := ""
		for _, idx := range face.indices {
			x, y := camera.Project3DToIsometric(vertices[idx])
			points += fmt.Sprintf("%.1f,%.1f ", x, y)
		}
		
		svg += fmt.Sprintf(
			`<polygon points="%s" fill="%s" stroke="#333" stroke-width="0.5" class="wall-face wall-%s"/>`,
			points, face.color, face.name,
		)
	}
	
	// Add wall edges for definition
	edges := [][]int{
		{0, 1}, {1, 3}, {3, 2}, {2, 0}, // Bottom edges
		{4, 5}, {5, 7}, {7, 6}, {6, 4}, // Top edges
		{0, 4}, {1, 5}, {2, 6}, {3, 7}, // Vertical edges
	}
	
	for _, edge := range edges {
		x1, y1 := camera.Project3DToIsometric(vertices[edge[0]])
		x2, y2 := camera.Project3DToIsometric(vertices[edge[1]])
		svg += fmt.Sprintf(
			`<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#000" stroke-width="0.25" opacity="0.5"/>`,
			x1, y1, x2, y2,
		)
	}
	
	svg += `</g>`
	return svg
}

func (w *Wall) getWall3DVertices(floorElevation float64) []Point3D {
	// Calculate perpendicular offset for wall thickness
	dx := w.EndPoint.X - w.StartPoint.X
	dy := w.EndPoint.Y - w.StartPoint.Y
	length := math.Sqrt(dx*dx + dy*dy)
	
	// Perpendicular unit vector
	px := -dy / length * w.Thickness / 2
	py := dx / length * w.Thickness / 2
	
	// 8 vertices of the wall box
	return []Point3D{
		// Bottom face
		{X: w.StartPoint.X - px, Y: w.StartPoint.Y - py, Z: floorElevation},        // 0
		{X: w.StartPoint.X + px, Y: w.StartPoint.Y + py, Z: floorElevation},        // 1
		{X: w.EndPoint.X - px, Y: w.EndPoint.Y - py, Z: floorElevation},            // 2
		{X: w.EndPoint.X + px, Y: w.EndPoint.Y + py, Z: floorElevation},            // 3
		// Top face
		{X: w.StartPoint.X - px, Y: w.StartPoint.Y - py, Z: floorElevation + w.Height}, // 4
		{X: w.StartPoint.X + px, Y: w.StartPoint.Y + py, Z: floorElevation + w.Height}, // 5
		{X: w.EndPoint.X - px, Y: w.EndPoint.Y - py, Z: floorElevation + w.Height},     // 6
		{X: w.EndPoint.X + px, Y: w.EndPoint.Y + py, Z: floorElevation + w.Height},     // 7
	}
}

func (w *Wall) isFaceVisible(vertices []Point3D, face []int, camera *Camera) bool {
	// Simple back-face culling using normal vector
	// Calculate face normal
	v1 := vertices[face[1]].Subtract(vertices[face[0]])
	v2 := vertices[face[2]].Subtract(vertices[face[0]])
	normal := v1.Cross(v2)
	
	// View vector from face center to camera
	center := vertices[face[0]]
	for i := 1; i < len(face); i++ {
		center = center.Add(vertices[face[i]])
	}
	center = center.Scale(1.0 / float64(len(face)))
	
	viewVector := camera.Position.Subtract(center)
	
	// Face is visible if normal points towards camera
	return normal.Dot(viewVector) > 0
}

func (r *Room) render3DSVG(camera *Camera, elevation float64) string {
	if len(r.Boundary) < 3 {
		return ""
	}
	
	// Project room boundary to isometric view
	points := ""
	for _, pt := range r.Boundary {
		pt3d := Point3D{X: pt.X, Y: pt.Y, Z: elevation + 10} // Slightly above floor
		x, y := camera.Project3DToIsometric(pt3d)
		points += fmt.Sprintf("%.1f,%.1f ", x, y)
	}
	
	svg := fmt.Sprintf(
		`<polygon points="%s" fill="rgba(100,200,255,0.1)" stroke="none" class="room-3d" data-id="%s"/>`,
		points, r.ID,
	)
	
	// Add room label
	center := r.calculateCenter()
	center3d := Point3D{X: center.X, Y: center.Y, Z: elevation + r.Height/2}
	cx, cy := camera.Project3DToIsometric(center3d)
	
	svg += fmt.Sprintf(
		`<text x="%.1f" y="%.1f" class="room-label-3d" text-anchor="middle">%s</text>`,
		cx, cy, r.Number,
	)
	
	return svg
}

// Vector operations for Point3D
func (p Point3D) Add(other Point3D) Point3D {
	return Point3D{
		X: p.X + other.X,
		Y: p.Y + other.Y,
		Z: p.Z + other.Z,
	}
}

func (p Point3D) Subtract(other Point3D) Point3D {
	return Point3D{
		X: p.X - other.X,
		Y: p.Y - other.Y,
		Z: p.Z - other.Z,
	}
}

func (p Point3D) Scale(factor float64) Point3D {
	return Point3D{
		X: p.X * factor,
		Y: p.Y * factor,
		Z: p.Z * factor,
	}
}

func (p Point3D) Cross(other Point3D) Point3D {
	return Point3D{
		X: p.Y*other.Z - p.Z*other.Y,
		Y: p.Z*other.X - p.X*other.Z,
		Z: p.X*other.Y - p.Y*other.X,
	}
}

func (p Point3D) Dot(other Point3D) float64 {
	return p.X*other.X + p.Y*other.Y + p.Z*other.Z
}

func (r *Room) calculateCenter() Point3D {
	if len(r.Boundary) == 0 {
		return Point3D{}
	}
	
	center := Point3D{}
	for _, pt := range r.Boundary {
		center.X += pt.X
		center.Y += pt.Y
		center.Z += pt.Z
	}
	
	n := float64(len(r.Boundary))
	return Point3D{
		X: center.X / n,
		Y: center.Y / n,
		Z: center.Z / n,
	}
}

// Canvas-based 3D rendering for smooth animations

// Render3DToCanvas generates Canvas drawing commands
func (f *Floor) Render3DToCanvas(camera *Camera) string {
	js := `
	function render3DFloor(ctx, floor) {
		ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
		ctx.save();
		
		// Center the view
		ctx.translate(ctx.canvas.width / 2, ctx.canvas.height / 2);
		
		// Draw floor slab
		ctx.fillStyle = '#f0f0f0';
		ctx.strokeStyle = '#ccc';
		ctx.beginPath();
	`
	
	// Add floor slab vertices
	minX, minY := 1000000.0, 1000000.0
	maxX, maxY := -1000000.0, -1000000.0
	
	for _, wall := range f.Walls {
		minX = math.Min(minX, math.Min(wall.StartPoint.X, wall.EndPoint.X))
		minY = math.Min(minY, math.Min(wall.StartPoint.Y, wall.EndPoint.Y))
		maxX = math.Max(maxX, math.Max(wall.StartPoint.X, wall.EndPoint.X))
		maxY = math.Max(maxY, math.Max(wall.StartPoint.Y, wall.EndPoint.Y))
	}
	
	corners := []Point3D{
		{X: minX, Y: minY, Z: f.Elevation},
		{X: maxX, Y: minY, Z: f.Elevation},
		{X: maxX, Y: maxY, Z: f.Elevation},
		{X: minX, Y: maxY, Z: f.Elevation},
	}
	
	for i, corner := range corners {
		x, y := camera.Project3DToIsometric(corner)
		if i == 0 {
			js += fmt.Sprintf("ctx.moveTo(%.1f, %.1f);\n", x, y)
		} else {
			js += fmt.Sprintf("ctx.lineTo(%.1f, %.1f);\n", x, y)
		}
	}
	
	js += `
		ctx.closePath();
		ctx.globalAlpha = 0.5;
		ctx.fill();
		ctx.globalAlpha = 1.0;
		ctx.stroke();
		
		// Draw walls
	`
	
	// Sort and render walls
	sortedWalls := make([]*Wall, len(f.Walls))
	copy(sortedWalls, f.Walls)
	sort.Slice(sortedWalls, func(i, j int) bool {
		avgY1 := (sortedWalls[i].StartPoint.Y + sortedWalls[i].EndPoint.Y) / 2
		avgY2 := (sortedWalls[j].StartPoint.Y + sortedWalls[j].EndPoint.Y) / 2
		return avgY1 < avgY2
	})
	
	for _, wall := range sortedWalls {
		js += wall.renderToCanvas3D(camera, f.Elevation)
	}
	
	js += `
		ctx.restore();
	}
	`
	
	return js
}

func (w *Wall) renderToCanvas3D(camera *Camera, elevation float64) string {
	vertices := w.getWall3DVertices(elevation)
	
	js := `
		// Wall ` + w.ID + `
		ctx.save();
	`
	
	// Define faces to render
	faces := []struct {
		indices []int
		color   string
	}{
		{[]int{0, 1, 5, 4}, "#666"}, // Front
		{[]int{4, 5, 7, 6}, "#555"}, // Top
		{[]int{1, 3, 7, 5}, "#888"}, // Right side
	}
	
	for _, face := range faces {
		js += fmt.Sprintf("ctx.fillStyle = '%s';\n", face.color)
		js += "ctx.beginPath();\n"
		
		for i, idx := range face.indices {
			x, y := camera.Project3DToIsometric(vertices[idx])
			if i == 0 {
				js += fmt.Sprintf("ctx.moveTo(%.1f, %.1f);\n", x, y)
			} else {
				js += fmt.Sprintf("ctx.lineTo(%.1f, %.1f);\n", x, y)
			}
		}
		
		js += "ctx.closePath();\n"
		js += "ctx.fill();\n"
		js += "ctx.stroke();\n"
	}
	
	js += "ctx.restore();\n"
	
	return js
}