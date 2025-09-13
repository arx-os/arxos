package rendering

// Compositor blends multiple layers into a single output
type Compositor struct {
	blendMode    BlendMode
	opacity      map[string]float64
	priorityMode PriorityMode
}

// BlendMode defines how layers are combined
type BlendMode int

const (
	BlendReplace   BlendMode = iota // Top layer replaces bottom
	BlendOverlay                     // Transparent spaces show through
	BlendAdditive                    // Characters combine
	BlendPriority                    // Based on character priority
)

// PriorityMode defines character priority rules
type PriorityMode int

const (
	PriorityNormal    PriorityMode = iota // Standard layering
	PriorityStructure                      // Structure always visible
	PriorityAlerts                         // Alerts on top
)

// NewCompositor creates a new layer compositor
func NewCompositor() *Compositor {
	return &Compositor{
		blendMode:    BlendOverlay,
		opacity:      make(map[string]float64),
		priorityMode: PriorityNormal,
	}
}

// SetBlendMode changes the compositing blend mode
func (c *Compositor) SetBlendMode(mode BlendMode) {
	c.blendMode = mode
}

// SetLayerOpacity sets opacity for a specific layer (0.0-1.0)
func (c *Compositor) SetLayerOpacity(layerName string, opacity float64) {
	if opacity < 0 {
		opacity = 0
	} else if opacity > 1 {
		opacity = 1
	}
	c.opacity[layerName] = opacity
}

// Composite combines multiple layer renders into one
func (c *Compositor) Composite(layers [][][]rune, width, height int) [][]rune {
	// Initialize output buffer
	output := make([][]rune, height)
	for i := range output {
		output[i] = make([]rune, width)
		for j := range output[i] {
			output[i][j] = ' ' // Default to space
		}
	}
	
	// Apply each layer in order
	for layerIdx, layer := range layers {
		c.applyLayer(output, layer, layerIdx, width, height)
	}
	
	return output
}

// applyLayer blends a single layer onto the output
func (c *Compositor) applyLayer(output, layer [][]rune, layerIdx, width, height int) {
	layerHeight := len(layer)
	layerWidth := 0
	if layerHeight > 0 {
		layerWidth = len(layer[0])
	}
	
	// Ensure we don't exceed bounds
	maxY := height
	if layerHeight < maxY {
		maxY = layerHeight
	}
	
	for y := 0; y < maxY; y++ {
		maxX := width
		if layerWidth < maxX {
			maxX = layerWidth
		}
		
		for x := 0; x < maxX; x++ {
			char := layer[y][x]
			
			// Apply blending based on mode
			switch c.blendMode {
			case BlendReplace:
				output[y][x] = char
				
			case BlendOverlay:
				// Only apply non-space characters
				if char != ' ' && char != 0 {
					output[y][x] = char
				}
				
			case BlendAdditive:
				// Combine characters based on priority
				output[y][x] = c.combineChars(output[y][x], char)
				
			case BlendPriority:
				// Use character priority system
				if c.getCharPriority(char) > c.getCharPriority(output[y][x]) {
					output[y][x] = char
				}
			}
		}
	}
}

// combineChars combines two characters for additive blending
func (c *Compositor) combineChars(existing, new rune) rune {
	// If either is space, use the other
	if existing == ' ' || existing == 0 {
		return new
	}
	if new == ' ' || new == 0 {
		return existing
	}
	
	// Priority system for combining
	existingPri := c.getCharPriority(existing)
	newPri := c.getCharPriority(new)
	
	if newPri > existingPri {
		return new
	}
	return existing
}

// getCharPriority returns rendering priority for a character
func (c *Compositor) getCharPriority(char rune) int {
	// Higher priority renders on top
	switch char {
	case ' ', 0:
		return 0
		
	// Structure characters (walls, floors)
	case '─', '│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼':
		return 10
	case '═', '║', '╔', '╗', '╚', '╝', '╠', '╣', '╦', '╩', '╬':
		return 11
		
	// Fill patterns
	case '░', '▒', '▓':
		return 5
		
	// Equipment symbols
	case '●', '○', '◉', '◎', '◐', '◑':
		return 20
	case '▲', '▼', '◆', '◇', '■', '□':
		return 21
		
	// Electrical symbols
	case '⚡', '⚙', '⊕', '⊖', '⊗':
		return 30
		
	// Particles and effects
	case '*', '•', '·', '°', '∘':
		return 25
	case '~', '≈', '≋':
		return 26
		
	// Alerts and warnings
	case '!', '‼', '⚠', '☠', '☢', '☣':
		return 100
		
	// Status indicators
	case '✓', '✗', '✔', '✖', '✘':
		return 50
		
	// Arrows and flow
	case '→', '←', '↑', '↓', '↔', '↕':
		return 35
	case '⇒', '⇐', '⇑', '⇓', '⇔', '⇕':
		return 36
		
	default:
		// Letters and numbers
		if (char >= 'A' && char <= 'Z') || (char >= 'a' && char <= 'z') || 
		   (char >= '0' && char <= '9') {
			return 40
		}
		return 15
	}
}

// MergeRegions optimizes dirty regions by merging overlapping ones
func MergeRegions(regions []Region) []Region {
	if len(regions) <= 1 {
		return regions
	}
	
	merged := []Region{}
	
	for _, r := range regions {
		added := false
		for i, m := range merged {
			if regionsOverlap(r, m) {
				// Merge regions
				merged[i] = mergeTwo(r, m)
				added = true
				break
			}
		}
		
		if !added {
			merged = append(merged, r)
		}
	}
	
	// Recursively merge until no more merging possible
	if len(merged) < len(regions) {
		return MergeRegions(merged)
	}
	
	return merged
}

func regionsOverlap(a, b Region) bool {
	return !(a.X+a.Width < b.X || b.X+b.Width < a.X ||
		a.Y+a.Height < b.Y || b.Y+b.Height < a.Y)
}

func mergeTwo(a, b Region) Region {
	minX := a.X
	if b.X < minX {
		minX = b.X
	}
	
	minY := a.Y
	if b.Y < minY {
		minY = b.Y
	}
	
	maxX := a.X + a.Width
	if b.X+b.Width > maxX {
		maxX = b.X + b.Width
	}
	
	maxY := a.Y + a.Height
	if b.Y+b.Height > maxY {
		maxY = b.Y + b.Height
	}
	
	return Region{
		X:      minX,
		Y:      minY,
		Width:  maxX - minX,
		Height: maxY - minY,
	}
}