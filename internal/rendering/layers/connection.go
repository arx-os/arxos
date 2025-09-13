package layers

import (
	"github.com/joelpate/arxos/pkg/models"
)

// Connection represents a connection between pieces of equipment
type Connection struct {
	ID       string         `json:"id"`
	Type     ConnectionType `json:"type"`
	FromID   string         `json:"from_id"`   // Source equipment ID
	ToID     string         `json:"to_id"`     // Destination equipment ID
	Points   []models.Point `json:"points"`    // Path points for the connection
	Status   ConnectionStatus `json:"status"`
}

// ConnectionType defines the type of connection
type ConnectionType string

const (
	ConnectionElectrical ConnectionType = "electrical"
	ConnectionData       ConnectionType = "data"
	ConnectionPlumbing   ConnectionType = "plumbing"
	ConnectionHVAC       ConnectionType = "hvac"
	ConnectionGas        ConnectionType = "gas"
	ConnectionFiber      ConnectionType = "fiber"
)

// ConnectionStatus defines the status of a connection
type ConnectionStatus string

const (
	ConnectionStatusActive      ConnectionStatus = "active"
	ConnectionStatusInactive    ConnectionStatus = "inactive"
	ConnectionStatusMaintenance ConnectionStatus = "maintenance"
	ConnectionStatusFailed      ConnectionStatus = "failed"
)

// ConnectionLayer renders connections between equipment
type ConnectionLayer struct {
	*BaseLayer
	connections []Connection
	equipment   []models.Equipment // For resolving equipment positions
	showLabels  bool
	styleMap    map[ConnectionType]ConnectionStyle
}

// ConnectionStyle defines how connections are rendered
type ConnectionStyle struct {
	Char    rune
	Active  rune
	Failed  rune
	Color   string // For future color support
}

// Default connection styles
var defaultConnectionStyles = map[ConnectionType]ConnectionStyle{
	ConnectionElectrical: {Char: '─', Active: '═', Failed: '✗'},
	ConnectionData:       {Char: '┈', Active: '━', Failed: '✗'},
	ConnectionPlumbing:   {Char: '~', Active: '≈', Failed: '✗'},
	ConnectionHVAC:       {Char: '▬', Active: '▬', Failed: '✗'},
	ConnectionGas:        {Char: '─', Active: '━', Failed: '✗'},
	ConnectionFiber:      {Char: '┅', Active: '┉', Failed: '✗'},
}

// NewConnectionLayer creates a new connection layer
func NewConnectionLayer(connections []Connection, equipment []models.Equipment) *ConnectionLayer {
	layer := &ConnectionLayer{
		BaseLayer:   NewBaseLayer("connections", PriorityConnection),
		connections: connections,
		equipment:   equipment,
		showLabels:  false,
		styleMap:    make(map[ConnectionType]ConnectionStyle),
	}
	
	// Copy default styles
	for k, v := range defaultConnectionStyles {
		layer.styleMap[k] = v
	}
	
	// Calculate bounds from connection points
	if len(connections) > 0 {
		minX, minY := float64(1e9), float64(1e9)
		maxX, maxY := float64(-1e9), float64(-1e9)
		
		for _, conn := range connections {
			for _, point := range conn.Points {
				if point.X < minX {
					minX = point.X
				}
				if point.Y < minY {
					minY = point.Y
				}
				if point.X > maxX {
					maxX = point.X
				}
				if point.Y > maxY {
					maxY = point.Y
				}
			}
		}
		
		layer.bounds = Bounds{
			MinX: minX - 1,
			MinY: minY - 1,
			MaxX: maxX + 1,
			MaxY: maxY + 1,
		}
	}
	
	return layer
}

// SetConnections updates the connections list
func (c *ConnectionLayer) SetConnections(connections []Connection) {
	c.connections = connections
}

// SetShowLabels enables/disables connection labels
func (c *ConnectionLayer) SetShowLabels(show bool) {
	c.showLabels = show
}

// SetStyle sets a custom style for a connection type
func (c *ConnectionLayer) SetStyle(connType ConnectionType, style ConnectionStyle) {
	c.styleMap[connType] = style
}

// Render renders the connections to the buffer
func (c *ConnectionLayer) Render(buffer [][]rune, viewport Viewport) {
	for _, conn := range c.connections {
		c.renderConnection(buffer, viewport, conn)
	}
}

// renderConnection renders a single connection
func (c *ConnectionLayer) renderConnection(buffer [][]rune, viewport Viewport, conn Connection) {
	if len(conn.Points) < 2 {
		return // Need at least 2 points to draw a connection
	}
	
	style, exists := c.styleMap[conn.Type]
	if !exists {
		style = ConnectionStyle{Char: '·', Active: '●', Failed: '✗'}
	}
	
	// Choose character based on connection status
	char := style.Char
	if conn.Status == ConnectionStatusFailed {
		char = style.Failed
	} else if conn.Status == ConnectionStatusActive {
		char = style.Active
	}
	
	// Draw lines between consecutive points
	for i := 0; i < len(conn.Points)-1; i++ {
		from := conn.Points[i]
		to := conn.Points[i+1]
		c.drawLine(buffer, viewport, from, to, char)
	}
	
	// Draw connection label if enabled
	if c.showLabels && conn.ID != "" {
		// Place label at the midpoint of the first segment
		if len(conn.Points) >= 2 {
			midX := (conn.Points[0].X + conn.Points[1].X) / 2
			midY := (conn.Points[0].Y + conn.Points[1].Y) / 2
			screenX := int((midX - viewport.X) * viewport.Zoom)
			screenY := int((midY - viewport.Y) * viewport.Zoom)
			c.drawLabel(buffer, viewport, screenX, screenY, conn.ID)
		}
	}
}

// drawLine draws a line between two points
func (c *ConnectionLayer) drawLine(buffer [][]rune, viewport Viewport, from, to models.Point, char rune) {
	// Convert world coordinates to screen coordinates
	x1 := int((from.X - viewport.X) * viewport.Zoom)
	y1 := int((from.Y - viewport.Y) * viewport.Zoom)
	x2 := int((to.X - viewport.X) * viewport.Zoom)
	y2 := int((to.Y - viewport.Y) * viewport.Zoom)
	
	// Use Bresenham's line algorithm for smooth lines
	dx := abs(x2 - x1)
	dy := abs(y2 - y1)
	sx := 1
	if x1 > x2 {
		sx = -1
	}
	sy := 1
	if y1 > y2 {
		sy = -1
	}
	err := dx - dy
	
	x, y := x1, y1
	for {
		// Set character if within viewport
		if x >= 0 && x < viewport.Width && y >= 0 && y < viewport.Height {
			if y < len(buffer) && x < len(buffer[y]) {
				buffer[y][x] = char
			}
		}
		
		if x == x2 && y == y2 {
			break
		}
		
		e2 := 2 * err
		if e2 > -dy {
			err -= dy
			x += sx
		}
		if e2 < dx {
			err += dx
			y += sy
		}
	}
}

// drawLabel draws a text label for a connection
func (c *ConnectionLayer) drawLabel(buffer [][]rune, viewport Viewport, x, y int, label string) {
	// Draw label above the connection line if there's space
	labelY := y - 1
	if labelY < 0 {
		// Try below if no space above
		labelY = y + 1
		if labelY >= viewport.Height {
			return // No space for label
		}
	}
	
	// Center the label on the connection
	labelRunes := []rune(label)
	startX := x - len(labelRunes)/2
	
	// Draw the label
	for i, ch := range labelRunes {
		labelX := startX + i
		if labelX >= 0 && labelX < viewport.Width && labelY >= 0 && labelY < len(buffer) {
			buffer[labelY][labelX] = ch
		}
	}
}

// GetConnectionAt returns the connection at the given world coordinates
func (c *ConnectionLayer) GetConnectionAt(x, y float64) *Connection {
	tolerance := 0.5 // How close to connection path to count as "at"
	
	for i := range c.connections {
		conn := &c.connections[i]
		
		// Check if point is near any segment of the connection
		for j := 0; j < len(conn.Points)-1; j++ {
			from := conn.Points[j]
			to := conn.Points[j+1]
			
			if c.pointNearLine(x, y, from.X, from.Y, to.X, to.Y, tolerance) {
				return conn
			}
		}
	}
	
	return nil
}

// pointNearLine checks if a point is within tolerance distance of a line segment
func (c *ConnectionLayer) pointNearLine(px, py, x1, y1, x2, y2, tolerance float64) bool {
	// Calculate distance from point to line segment
	A := px - x1
	B := py - y1
	C := x2 - x1
	D := y2 - y1
	
	dot := A*C + B*D
	lenSq := C*C + D*D
	
	if lenSq == 0 {
		// Line is a point
		dx := px - x1
		dy := py - y1
		return dx*dx+dy*dy <= tolerance*tolerance
	}
	
	param := dot / lenSq
	
	var xx, yy float64
	if param < 0 {
		xx, yy = x1, y1
	} else if param > 1 {
		xx, yy = x2, y2
	} else {
		xx = x1 + param*C
		yy = y1 + param*D
	}
	
	dx := px - xx
	dy := py - yy
	return dx*dx+dy*dy <= tolerance*tolerance
}

// abs returns the absolute value of an integer
func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

// Update can be used for animations (e.g., flowing data indicators)
func (c *ConnectionLayer) Update(deltaTime float64) {
	// Could implement flowing animations for active connections here
	// For now, static rendering
}