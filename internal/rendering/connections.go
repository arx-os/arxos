package rendering

import (
	"math"
	"sort"

	"github.com/arx-os/arxos/internal/connections"
	"github.com/arx-os/arxos/pkg/models"
)

// ConnectionLayer renders wiring, piping, and other connections between equipment
type ConnectionLayer struct {
	connManager *connections.Manager
	connections []ConnectionPath
	visible     bool
	dirty       []Region
	showLabels  bool
	pathStyles  map[connections.ConnectionType]PathStyle
}

// ConnectionPath represents a rendered connection between equipment
type ConnectionPath struct {
	ID          string
	Type        connections.ConnectionType
	FromID      string
	ToID        string
	Points      []models.Point
	Active      bool
	Load        float64 // 0-1 representing current load/usage
	Capacity    float64
}

// PathStyle defines how different connection types are rendered
type PathStyle struct {
	Character    rune
	ActiveChar   rune
	OverloadChar rune
	Color        string // For future color support
}

// NewConnectionLayer creates a new connection visualization layer
func NewConnectionLayer(connManager *connections.Manager) *ConnectionLayer {
	return &ConnectionLayer{
		connManager: connManager,
		connections: []ConnectionPath{},
		visible:     true,
		dirty:       []Region{},
		showLabels:  false,
		pathStyles:  defaultPathStyles(),
	}
}

// defaultPathStyles returns standard rendering styles for connection types
func defaultPathStyles() map[connections.ConnectionType]PathStyle {
	return map[connections.ConnectionType]PathStyle{
		connections.TypeElectrical: {
			Character:    '─',
			ActiveChar:   '═',
			OverloadChar: '▬',
		},
		connections.TypeData: {
			Character:    '┄',
			ActiveChar:   '┅',
			OverloadChar: '▪',
		},
		connections.TypeWater: {
			Character:    '~',
			ActiveChar:   '≈',
			OverloadChar: '▓',
		},
		connections.TypeGas: {
			Character:    '∼',
			ActiveChar:   '≋',
			OverloadChar: '█',
		},
		connections.TypeHVAC: {
			Character:    '░',
			ActiveChar:   '▒',
			OverloadChar: '▓',
		},
		connections.TypeFiber: {
			Character:    '·',
			ActiveChar:   '•',
			OverloadChar: '◆',
		},
	}
}

// Render produces the ASCII representation of connections
func (c *ConnectionLayer) Render(viewport Viewport) [][]rune {
	// Initialize render buffer
	buffer := make([][]rune, viewport.Height)
	for i := range buffer {
		buffer[i] = make([]rune, viewport.Width)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}

	if !c.visible {
		return buffer
	}

	// Render all connections
	for _, conn := range c.connections {
		c.renderConnection(buffer, conn, viewport)
	}

	return buffer
}

func (c *ConnectionLayer) renderConnection(buffer [][]rune, conn ConnectionPath, vp Viewport) {
	if len(conn.Points) < 2 {
		return
	}

	style := c.pathStyles[conn.Type]
	char := c.getConnectionCharacter(conn, style)

	// Render path segments
	for i := 0; i < len(conn.Points)-1; i++ {
		c.renderPathSegment(buffer, conn.Points[i], conn.Points[i+1], char, vp)
	}

	// Render connection points (junctions)
	for _, point := range conn.Points {
		c.renderJunction(buffer, point, conn.Type, vp)
	}

	// Render labels if enabled and zoom is sufficient
	if c.showLabels && vp.Zoom >= 1.5 {
		c.renderConnectionLabel(buffer, conn, vp)
	}
}

func (c *ConnectionLayer) renderPathSegment(buffer [][]rune, from, to models.Point, char rune, vp Viewport) {
	// Convert to viewport coordinates
	x1 := int((from.X - vp.X) * vp.Zoom)
	y1 := int((from.Y - vp.Y) * vp.Zoom)
	x2 := int((to.X - vp.X) * vp.Zoom)
	y2 := int((to.Y - vp.Y) * vp.Zoom)

	// Use Bresenham's line algorithm for clean line rendering
	points := c.bresenhamLine(x1, y1, x2, y2)

	for _, point := range points {
		if point.X >= 0 && point.X < vp.Width && point.Y >= 0 && point.Y < vp.Height {
			// Choose appropriate character based on direction
			dirChar := c.getDirectionalCharacter(char, x1, y1, x2, y2)
			buffer[point.Y][point.X] = dirChar
		}
	}
}

func (c *ConnectionLayer) renderJunction(buffer [][]rune, point models.Point, connType connections.ConnectionType, vp Viewport) {
	// Convert to viewport coordinates
	x := int((point.X - vp.X) * vp.Zoom)
	y := int((point.Y - vp.Y) * vp.Zoom)

	// Skip if outside viewport
	if x < 0 || x >= vp.Width || y < 0 || y >= vp.Height {
		return
	}

	// Render junction symbol based on connection type
	var junctionChar rune
	switch connType {
	case connections.TypeElectrical:
		junctionChar = '●'
	case connections.TypeData:
		junctionChar = '◉'
	case connections.TypeWater:
		junctionChar = '○'
	case connections.TypeGas:
		junctionChar = '◎'
	case connections.TypeHVAC:
		junctionChar = '⊙'
	case connections.TypeFiber:
		junctionChar = '◦'
	default:
		junctionChar = '▪'
	}

	buffer[y][x] = junctionChar
}

func (c *ConnectionLayer) renderConnectionLabel(buffer [][]rune, conn ConnectionPath, vp Viewport) {
	if len(conn.Points) == 0 {
		return
	}

	// Find midpoint of connection for label placement
	midPoint := conn.Points[len(conn.Points)/2]
	x := int((midPoint.X - vp.X) * vp.Zoom)
	y := int((midPoint.Y - vp.Y) * vp.Zoom)

	// Skip if outside viewport
	if y < 0 || y >= vp.Height {
		return
	}

	// Create label text
	label := string(conn.Type)[0:3] // First 3 chars of type
	if conn.Load > 0 {
		label += "*" // Indicate active connection
	}

	// Place label
	startX := x - len(label)/2
	if startX < 0 {
		startX = 0
	}

	for i, ch := range label {
		if startX+i < vp.Width {
			buffer[y][startX+i] = ch
		}
	}
}

func (c *ConnectionLayer) getConnectionCharacter(conn ConnectionPath, style PathStyle) rune {
	utilizationPercent := conn.Load / conn.Capacity * 100

	if utilizationPercent > 90 {
		return style.OverloadChar
	} else if conn.Active && utilizationPercent > 10 {
		return style.ActiveChar
	}
	return style.Character
}

func (c *ConnectionLayer) getDirectionalCharacter(baseChar rune, x1, y1, x2, y2 int) rune {
	dx := x2 - x1
	dy := y2 - y1

	// Determine primary direction
	if abs(dx) > abs(dy) {
		// Horizontal line
		return '─'
	} else if abs(dy) > abs(dx) {
		// Vertical line
		return '│'
	} else {
		// Diagonal - use corner characters
		if (dx > 0 && dy > 0) || (dx < 0 && dy < 0) {
			return '╲'
		} else {
			return '╱'
		}
	}
}

func (c *ConnectionLayer) bresenhamLine(x1, y1, x2, y2 int) []struct{ X, Y int } {
	points := []struct{ X, Y int }{}
	
	dx := abs(x2 - x1)
	dy := abs(y2 - y1)
	
	x, y := x1, y1
	
	var xInc, yInc int
	if x1 < x2 {
		xInc = 1
	} else {
		xInc = -1
	}
	if y1 < y2 {
		yInc = 1
	} else {
		yInc = -1
	}
	
	error := dx - dy
	
	for {
		points = append(points, struct{ X, Y int }{x, y})
		
		if x == x2 && y == y2 {
			break
		}
		
		error2 := 2 * error
		
		if error2 > -dy {
			error -= dy
			x += xInc
		}
		
		if error2 < dx {
			error += dx
			y += yInc
		}
	}
	
	return points
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

// Update refreshes connection data and states
func (c *ConnectionLayer) Update(dt float64) {
	// Refresh connections from manager
	allConnections, err := c.connManager.GetAllConnections()
	if err != nil {
		return
	}

	// Convert to renderable paths
	c.connections = c.connections[:0] // Clear slice
	for _, conn := range allConnections {
		path := c.connectionToPath(conn)
		if path != nil {
			c.connections = append(c.connections, *path)
		}
	}

	// Sort by type for consistent rendering order
	sort.Slice(c.connections, func(i, j int) bool {
		return string(c.connections[i].Type) < string(c.connections[j].Type)
	})
}

func (c *ConnectionLayer) connectionToPath(conn *connections.Connection) *ConnectionPath {
	// Get path points from connection manager
	points, err := c.connManager.GetConnectionPath(conn.ID)
	if err != nil || len(points) < 2 {
		return nil
	}

	// Convert to models.Point
	modelPoints := make([]models.Point, len(points))
	for i, p := range points {
		modelPoints[i] = models.Point{X: p.X, Y: p.Y}
	}

	return &ConnectionPath{
		ID:       conn.ID,
		Type:     conn.Type,
		FromID:   conn.FromEquipmentID,
		ToID:     conn.ToEquipmentID,
		Points:   modelPoints,
		Active:   conn.Status == "active",
		Load:     conn.CurrentLoad,
		Capacity: conn.Capacity,
	}
}

// SetVisible controls layer visibility
func (c *ConnectionLayer) SetVisible(visible bool) {
	c.visible = visible
}

// IsVisible returns current visibility state
func (c *ConnectionLayer) IsVisible() bool {
	return c.visible
}

// GetZ returns the z-index for layering
func (c *ConnectionLayer) GetZ() int {
	return LayerConnections
}

// GetName returns the layer name
func (c *ConnectionLayer) GetName() string {
	return "connections"
}

// SetDirty marks regions that need re-rendering
func (c *ConnectionLayer) SetDirty(regions []Region) {
	c.dirty = regions
}

// SetShowLabels controls connection label visibility
func (c *ConnectionLayer) SetShowLabels(show bool) {
	c.showLabels = show
	c.dirty = []Region{{0, 0, 1000, 1000}} // Force redraw
}

// SetPathStyle allows customizing how connection types are rendered
func (c *ConnectionLayer) SetPathStyle(connType connections.ConnectionType, style PathStyle) {
	c.pathStyles[connType] = style
}

// HighlightConnection marks a specific connection for highlighting
func (c *ConnectionLayer) HighlightConnection(connectionID string, highlight bool) {
	for i := range c.connections {
		if c.connections[i].ID == connectionID {
			// Mark connection's path as dirty for re-rendering
			for _, point := range c.connections[i].Points {
				x := int(point.X)
				y := int(point.Y)
				c.dirty = append(c.dirty, Region{x-1, y-1, 3, 3})
			}
			break
		}
	}
}

// GetConnectionsAt returns connections near a specific point
func (c *ConnectionLayer) GetConnectionsAt(x, y int, vp Viewport, tolerance float64) []ConnectionPath {
	// Convert viewport coordinates to world coordinates
	worldX := vp.X + float64(x)/vp.Zoom
	worldY := vp.Y + float64(y)/vp.Zoom
	queryPoint := models.Point{X: worldX, Y: worldY}

	var nearbyConnections []ConnectionPath
	
	for _, conn := range c.connections {
		if c.isPointNearPath(queryPoint, conn.Points, tolerance) {
			nearbyConnections = append(nearbyConnections, conn)
		}
	}

	return nearbyConnections
}

func (c *ConnectionLayer) isPointNearPath(point models.Point, path []models.Point, tolerance float64) bool {
	for i := 0; i < len(path)-1; i++ {
		if c.distanceToSegment(point, path[i], path[i+1]) <= tolerance {
			return true
		}
	}
	return false
}

func (c *ConnectionLayer) distanceToSegment(point, segStart, segEnd models.Point) float64 {
	// Calculate distance from point to line segment
	dx := segEnd.X - segStart.X
	dy := segEnd.Y - segStart.Y
	
	if dx == 0 && dy == 0 {
		// Degenerate case: segment is a point
		return c.distance(point, segStart)
	}
	
	// Parameter t represents position along segment (0 = start, 1 = end)
	t := ((point.X-segStart.X)*dx + (point.Y-segStart.Y)*dy) / (dx*dx + dy*dy)
	
	if t < 0 {
		// Closest point is segment start
		return c.distance(point, segStart)
	} else if t > 1 {
		// Closest point is segment end
		return c.distance(point, segEnd)
	} else {
		// Closest point is on the segment
		closest := models.Point{
			X: segStart.X + t*dx,
			Y: segStart.Y + t*dy,
		}
		return c.distance(point, closest)
	}
}

func (c *ConnectionLayer) distance(p1, p2 models.Point) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	return math.Sqrt(dx*dx + dy*dy)
}