package layers

import (
	"github.com/arx-os/arxos/pkg/models"
)

// StructureLayer renders the building structure (walls, rooms, doors)
type StructureLayer struct {
	*BaseLayer
	floorPlan *models.FloorPlan
	style     WallStyle
}

// WallStyle defines how walls are rendered
type WallStyle int

const (
	WallStyleSingle WallStyle = iota // Single line box drawing
	WallStyleDouble                   // Double line box drawing
	WallStyleASCII                    // Basic ASCII characters
	WallStyleThick                    // Thick/bold lines
)

// Wall drawing characters for different styles
var wallChars = map[WallStyle]struct {
	Horizontal   rune
	Vertical     rune
	TopLeft      rune
	TopRight     rune
	BottomLeft   rune
	BottomRight  rune
	Cross        rune
	TeeUp        rune
	TeeDown      rune
	TeeLeft      rune
	TeeRight     rune
}{
	WallStyleSingle: {
		Horizontal:  '─',
		Vertical:    '│',
		TopLeft:     '┌',
		TopRight:    '┐',
		BottomLeft:  '└',
		BottomRight: '┘',
		Cross:       '┼',
		TeeUp:       '┴',
		TeeDown:     '┬',
		TeeLeft:     '┤',
		TeeRight:    '├',
	},
	WallStyleDouble: {
		Horizontal:  '═',
		Vertical:    '║',
		TopLeft:     '╔',
		TopRight:    '╗',
		BottomLeft:  '╚',
		BottomRight: '╝',
		Cross:       '╬',
		TeeUp:       '╩',
		TeeDown:     '╦',
		TeeLeft:     '╣',
		TeeRight:    '╠',
	},
	WallStyleASCII: {
		Horizontal:  '-',
		Vertical:    '|',
		TopLeft:     '+',
		TopRight:    '+',
		BottomLeft:  '+',
		BottomRight: '+',
		Cross:       '+',
		TeeUp:       '+',
		TeeDown:     '+',
		TeeLeft:     '+',
		TeeRight:    '+',
	},
	WallStyleThick: {
		Horizontal:  '━',
		Vertical:    '┃',
		TopLeft:     '┏',
		TopRight:    '┓',
		BottomLeft:  '┗',
		BottomRight: '┛',
		Cross:       '╋',
		TeeUp:       '┻',
		TeeDown:     '┳',
		TeeLeft:     '┫',
		TeeRight:    '┣',
	},
}

// NewStructureLayer creates a new structure layer
func NewStructureLayer(floorPlan *models.FloorPlan) *StructureLayer {
	layer := &StructureLayer{
		BaseLayer: NewBaseLayer("structure", PriorityStructure),
		floorPlan: floorPlan,
		style:     WallStyleSingle,
	}
	
	// Calculate bounds from floor plan
	if floorPlan != nil && len(floorPlan.Rooms) > 0 {
		minX, minY := float64(1e9), float64(1e9)
		maxX, maxY := float64(-1e9), float64(-1e9)
		
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
		
		layer.bounds = Bounds{
			MinX: minX,
			MinY: minY,
			MaxX: maxX,
			MaxY: maxY,
		}
	}
	
	return layer
}

// SetStyle sets the wall rendering style
func (s *StructureLayer) SetStyle(style WallStyle) {
	s.style = style
}

// Render renders the structure to the buffer
func (s *StructureLayer) Render(buffer [][]rune, viewport Viewport) {
	if s.floorPlan == nil {
		return
	}
	
	chars := wallChars[s.style]
	
	// Render each room
	for _, room := range s.floorPlan.Rooms {
		s.renderRoom(buffer, viewport, *room, chars)
	}
	
	// Note: Door rendering removed as Room model doesn't include Doors field
}

// renderRoom renders a single room to the buffer
func (s *StructureLayer) renderRoom(buffer [][]rune, viewport Viewport, room models.Room, chars struct {
	Horizontal   rune
	Vertical     rune
	TopLeft      rune
	TopRight     rune
	BottomLeft   rune
	BottomRight  rune
	Cross        rune
	TeeUp        rune
	TeeDown      rune
	TeeLeft      rune
	TeeRight     rune
}) {
	// Convert world coordinates to screen coordinates
	screenMinX := int((room.Bounds.MinX - viewport.X) * viewport.Zoom)
	screenMinY := int((room.Bounds.MinY - viewport.Y) * viewport.Zoom)
	screenMaxX := int((room.Bounds.MaxX - viewport.X) * viewport.Zoom)
	screenMaxY := int((room.Bounds.MaxY - viewport.Y) * viewport.Zoom)
	
	// Clip to viewport
	if screenMaxX < 0 || screenMinX >= viewport.Width ||
		screenMaxY < 0 || screenMinY >= viewport.Height {
		return // Room is outside viewport
	}
	
	// Draw horizontal walls
	for x := screenMinX; x <= screenMaxX; x++ {
		if x >= 0 && x < viewport.Width {
			// Top wall
			if screenMinY >= 0 && screenMinY < viewport.Height {
				if x == screenMinX {
					s.setBufferChar(buffer, x, screenMinY, chars.TopLeft)
				} else if x == screenMaxX {
					s.setBufferChar(buffer, x, screenMinY, chars.TopRight)
				} else {
					s.setBufferChar(buffer, x, screenMinY, chars.Horizontal)
				}
			}
			
			// Bottom wall
			if screenMaxY >= 0 && screenMaxY < viewport.Height {
				if x == screenMinX {
					s.setBufferChar(buffer, x, screenMaxY, chars.BottomLeft)
				} else if x == screenMaxX {
					s.setBufferChar(buffer, x, screenMaxY, chars.BottomRight)
				} else {
					s.setBufferChar(buffer, x, screenMaxY, chars.Horizontal)
				}
			}
		}
	}
	
	// Draw vertical walls
	for y := screenMinY; y <= screenMaxY; y++ {
		if y >= 0 && y < viewport.Height {
			// Left wall
			if screenMinX >= 0 && screenMinX < viewport.Width {
				if y != screenMinY && y != screenMaxY {
					s.setBufferChar(buffer, screenMinX, y, chars.Vertical)
				}
			}
			
			// Right wall
			if screenMaxX >= 0 && screenMaxX < viewport.Width {
				if y != screenMinY && y != screenMaxY {
					s.setBufferChar(buffer, screenMaxX, y, chars.Vertical)
				}
			}
		}
	}
	
	// Fill interior with dots (floor)
	for y := screenMinY + 1; y < screenMaxY; y++ {
		for x := screenMinX + 1; x < screenMaxX; x++ {
			if x >= 0 && x < viewport.Width && y >= 0 && y < viewport.Height {
				if buffer[y][x] == ' ' || buffer[y][x] == 0 {
					buffer[y][x] = '·'
				}
			}
		}
	}
	
	// Add room name label in center
	if room.Name != "" {
		centerX := (screenMinX + screenMaxX) / 2
		centerY := (screenMinY + screenMaxY) / 2
		nameRunes := []rune(room.Name)
		startX := centerX - len(nameRunes)/2
		
		for i, ch := range nameRunes {
			x := startX + i
			if x >= 0 && x < viewport.Width && centerY >= 0 && centerY < viewport.Height {
				buffer[centerY][x] = ch
			}
		}
	}
}


// setBufferChar safely sets a character in the buffer
func (s *StructureLayer) setBufferChar(buffer [][]rune, x, y int, char rune) {
	if y >= 0 && y < len(buffer) && x >= 0 && x < len(buffer[y]) {
		buffer[y][x] = char
	}
}