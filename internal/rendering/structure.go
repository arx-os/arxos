package rendering

import (
	"github.com/arx-os/arxos/pkg/models"
)

// StructureLayer renders the base floor plan with rooms and walls
type StructureLayer struct {
	floorPlan *models.FloorPlan
	visible   bool
	dirty     []Region
}

// NewStructureLayer creates a new structure visualization layer
func NewStructureLayer(floorPlan *models.FloorPlan) *StructureLayer {
	return &StructureLayer{
		floorPlan: floorPlan,
		visible:   true,
		dirty:     []Region{},
	}
}

// Render produces the ASCII representation of the structure
func (s *StructureLayer) Render(viewport Viewport) [][]rune {
	// Initialize render buffer
	buffer := make([][]rune, viewport.Height)
	for i := range buffer {
		buffer[i] = make([]rune, viewport.Width)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}
	
	if s.floorPlan == nil || !s.visible {
		return buffer
	}
	
	// Render rooms
	for _, room := range s.floorPlan.Rooms {
		s.renderRoom(buffer, *room, viewport)
	}
	
	// Render walls and connections between rooms
	s.renderWalls(buffer, viewport)
	
	return buffer
}

func (s *StructureLayer) renderRoom(buffer [][]rune, room models.Room, vp Viewport) {
	// Convert room bounds to viewport coordinates
	minX := int((room.Bounds.MinX - vp.X) * vp.Zoom)
	maxX := int((room.Bounds.MaxX - vp.X) * vp.Zoom)
	minY := int((room.Bounds.MinY - vp.Y) * vp.Zoom)
	maxY := int((room.Bounds.MaxY - vp.Y) * vp.Zoom)
	
	// Clip to viewport
	if minX < 0 {
		minX = 0
	}
	if maxX >= vp.Width {
		maxX = vp.Width - 1
	}
	if minY < 0 {
		minY = 0
	}
	if maxY >= vp.Height {
		maxY = vp.Height - 1
	}
	
	// Skip if room is outside viewport
	if minX >= vp.Width || maxX < 0 || minY >= vp.Height || maxY < 0 {
		return
	}
	
	// Draw room boundaries
	for y := minY; y <= maxY; y++ {
		for x := minX; x <= maxX; x++ {
			if y < 0 || y >= vp.Height || x < 0 || x >= vp.Width {
				continue
			}
			
			// Determine wall character based on position
			isTop := y == minY
			isBottom := y == maxY
			isLeft := x == minX
			isRight := x == maxX
			
			if isTop && isLeft {
				buffer[y][x] = '┌'
			} else if isTop && isRight {
				buffer[y][x] = '┐'
			} else if isBottom && isLeft {
				buffer[y][x] = '└'
			} else if isBottom && isRight {
				buffer[y][x] = '┘'
			} else if isTop || isBottom {
				buffer[y][x] = '─'
			} else if isLeft || isRight {
				buffer[y][x] = '│'
			}
		}
	}
	
	// Add room label if space permits
	if maxX-minX > len(room.Name)+2 && maxY-minY > 2 {
		labelX := minX + (maxX-minX-len(room.Name))/2
		labelY := minY + (maxY-minY)/2
		
		if labelY >= 0 && labelY < vp.Height {
			for i, ch := range room.Name {
				if labelX+i >= 0 && labelX+i < vp.Width {
					buffer[labelY][labelX+i] = ch
				}
			}
		}
	}
}

func (s *StructureLayer) renderWalls(buffer [][]rune, vp Viewport) {
	// Render heavy walls for main structure
	// This would be based on wall definitions in the floor plan
	
	// For now, we enhance existing walls with heavier characters
	for y := 0; y < vp.Height; y++ {
		for x := 0; x < vp.Width; x++ {
			// Detect wall intersections and upgrade characters
			if s.isWallIntersection(buffer, x, y) {
				buffer[y][x] = s.getIntersectionChar(buffer, x, y)
			}
		}
	}
}

func (s *StructureLayer) isWallIntersection(buffer [][]rune, x, y int) bool {
	if y >= len(buffer) || x >= len(buffer[y]) {
		return false
	}
	
	char := buffer[y][x]
	return char == '─' || char == '│' || char == '┌' || char == '┐' || 
	       char == '└' || char == '┘' || char == '├' || char == '┤' || 
	       char == '┬' || char == '┴' || char == '┼'
}

func (s *StructureLayer) getIntersectionChar(buffer [][]rune, x, y int) rune {
	// Check adjacent cells to determine intersection type
	hasTop := y > 0 && s.isVerticalWall(buffer[y-1][x])
	hasBottom := y < len(buffer)-1 && s.isVerticalWall(buffer[y+1][x])
	hasLeft := x > 0 && s.isHorizontalWall(buffer[y][x-1])
	hasRight := x < len(buffer[y])-1 && s.isHorizontalWall(buffer[y][x+1])
	
	// Return appropriate intersection character
	if hasTop && hasBottom && hasLeft && hasRight {
		return '┼'
	} else if hasTop && hasBottom && hasLeft {
		return '┤'
	} else if hasTop && hasBottom && hasRight {
		return '├'
	} else if hasTop && hasLeft && hasRight {
		return '┴'
	} else if hasBottom && hasLeft && hasRight {
		return '┬'
	}
	
	return buffer[y][x] // Keep original if no intersection
}

func (s *StructureLayer) isVerticalWall(char rune) bool {
	return char == '│' || char == '├' || char == '┤' || char == '┼'
}

func (s *StructureLayer) isHorizontalWall(char rune) bool {
	return char == '─' || char == '┬' || char == '┴' || char == '┼'
}

// Update advances the layer's state (structure is mostly static)
func (s *StructureLayer) Update(dt float64) {
	// Structure layer is static, no updates needed
	// Could add effects like damage visualization here
}

// SetVisible controls layer visibility
func (s *StructureLayer) SetVisible(visible bool) {
	s.visible = visible
}

// IsVisible returns current visibility state
func (s *StructureLayer) IsVisible() bool {
	return s.visible
}

// GetZ returns the z-index for layering
func (s *StructureLayer) GetZ() int {
	return LayerStructure
}

// GetName returns the layer name
func (s *StructureLayer) GetName() string {
	return "structure"
}

// SetDirty marks regions that need re-rendering
func (s *StructureLayer) SetDirty(regions []Region) {
	s.dirty = regions
}

// UpdateFloorPlan updates the floor plan data
func (s *StructureLayer) UpdateFloorPlan(floorPlan *models.FloorPlan) {
	s.floorPlan = floorPlan
	// Mark entire viewport as dirty
	s.dirty = []Region{{0, 0, 1000, 1000}} // Large region to force full redraw
}