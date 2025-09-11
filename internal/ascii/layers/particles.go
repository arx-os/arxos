package layers

import (
	"github.com/joelpate/arxos/internal/ascii/abim"
	"github.com/joelpate/arxos/internal/particles"
)

// ParticleLayer renders dynamic particle effects
type ParticleLayer struct {
	system  *particles.System
	visible bool
	dirty   []abim.Region
}

// NewParticleLayer creates a new particle visualization layer
func NewParticleLayer(width, height int) *ParticleLayer {
	return &ParticleLayer{
		system:  particles.NewSystem(width, height),
		visible: true,
		dirty:   []abim.Region{},
	}
}

// Render produces the ASCII representation of particles
func (p *ParticleLayer) Render(viewport abim.Viewport) [][]rune {
	// Get particle render from system
	systemRender := p.system.Render()
	
	// Initialize render buffer
	buffer := make([][]rune, viewport.Height)
	for i := range buffer {
		buffer[i] = make([]rune, viewport.Width)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}
	
	if !p.visible {
		return buffer
	}
	
	// Copy particle render to buffer with viewport adjustment
	for y := 0; y < len(systemRender) && y < viewport.Height; y++ {
		for x := 0; x < len(systemRender[y]) && x < viewport.Width; x++ {
			// Apply viewport offset and zoom
			worldX := int((float64(x)/viewport.Zoom) + viewport.X)
			worldY := int((float64(y)/viewport.Zoom) + viewport.Y)
			
			// Check if particle is in viewport
			if worldX >= 0 && worldX < len(systemRender[0]) && 
			   worldY >= 0 && worldY < len(systemRender) {
				char := systemRender[worldY][worldX]
				if char != ' ' && char != 0 {
					buffer[y][x] = char
				}
			}
		}
	}
	
	return buffer
}

// Update advances the particle system
func (p *ParticleLayer) Update(dt float64) {
	p.system.Update()
	
	// Mark areas with particles as dirty for re-rendering
	p.updateDirtyRegions()
}

func (p *ParticleLayer) updateDirtyRegions() {
	// Clear previous dirty regions
	p.dirty = []abim.Region{}
	
	// Mark regions with active particles as dirty
	// This is a simplified approach - could be optimized
	if len(p.system.Particles) > 0 {
		minX, minY := int(p.system.Particles[0].X), int(p.system.Particles[0].Y)
		maxX, maxY := minX, minY
		
		for _, particle := range p.system.Particles {
			x, y := int(particle.X), int(particle.Y)
			if x < minX {
				minX = x
			}
			if x > maxX {
				maxX = x
			}
			if y < minY {
				minY = y
			}
			if y > maxY {
				maxY = y
			}
		}
		
		// Add some padding
		p.dirty = append(p.dirty, abim.Region{
			X:      minX - 1,
			Y:      minY - 1,
			Width:  maxX - minX + 3,
			Height: maxY - minY + 3,
		})
	}
}

// SetVisible controls layer visibility
func (p *ParticleLayer) SetVisible(visible bool) {
	p.visible = visible
}

// IsVisible returns current visibility state
func (p *ParticleLayer) IsVisible() bool {
	return p.visible
}

// GetZ returns the z-index for layering
func (p *ParticleLayer) GetZ() int {
	return abim.LayerParticles
}

// GetName returns the layer name
func (p *ParticleLayer) GetName() string {
	return "particles"
}

// SetDirty marks regions that need re-rendering
func (p *ParticleLayer) SetDirty(regions []abim.Region) {
	p.dirty = regions
}

// GetSystem returns the underlying particle system for direct manipulation
func (p *ParticleLayer) GetSystem() *particles.System {
	return p.system
}

// SpawnParticles creates particles at a specific location
func (p *ParticleLayer) SpawnParticles(x, y float64, pType particles.ParticleType, count int) {
	p.system.Spawn(x, y, pType, count)
}

// SetPhysics configures particle physics parameters
func (p *ParticleLayer) SetPhysics(gravity, wind, friction float64) {
	p.system.Gravity = gravity
	p.system.Wind = wind
	p.system.Friction = friction
}

// Clear removes all particles
func (p *ParticleLayer) Clear() {
	p.system.Clear()
}