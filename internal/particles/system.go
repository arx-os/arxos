package particles

import (
	"math"
	"math/rand"
	"time"
)

// Particle represents a single ASCII particle in the system
type Particle struct {
	X, Y           float64       // Position
	VX, VY         float64       // Velocity
	Life           float64       // Remaining lifetime (0-1)
	MaxLife        float64       // Total lifetime
	Char           rune          // ASCII character to display
	Intensity      float64       // For density-based rendering
	Color          string        // ANSI color code (optional)
	Type           ParticleType  // Type of particle
	GravityScale   float64       // Multiplier for gravity effect
}

// ParticleType defines different particle behaviors
type ParticleType int

const (
	TypeAir ParticleType = iota
	TypeWater
	TypeElectric
	TypeHeat
	TypeSmoke
	TypePeople
)

// System manages all particles and their physics
type System struct {
	Particles  []Particle
	Width      int
	Height     int
	Gravity    float64
	Wind       float64
	Friction   float64
	MaxParticles int
	SpawnRate  float64
	lastUpdate time.Time
}

// NewSystem creates a new particle system
func NewSystem(width, height int) *System {
	return &System{
		Particles:    make([]Particle, 0, 1000),
		Width:        width,
		Height:       height,
		Gravity:      0.1,
		Wind:         0.0,
		Friction:     0.98,
		MaxParticles: 1000,
		SpawnRate:    10,
		lastUpdate:   time.Now(),
	}
}

// Update advances the particle system by one time step
func (s *System) Update() {
	now := time.Now()
	dt := now.Sub(s.lastUpdate).Seconds()
	s.lastUpdate = now
	
	// Update existing particles
	alive := make([]Particle, 0, len(s.Particles))
	for i := range s.Particles {
		p := &s.Particles[i]
		
		// Apply physics
		p.VY += s.Gravity * p.GravityScale * dt
		p.VX += s.Wind * dt
		
		// Apply friction
		p.VX *= s.Friction
		p.VY *= s.Friction
		
		// Update position
		p.X += p.VX * dt * 60 // Scale for terminal refresh rate
		p.Y += p.VY * dt * 60
		
		// Update lifetime
		p.Life -= dt / p.MaxLife
		
		// Keep particle if still alive and in bounds
		if p.Life > 0 && p.X >= 0 && p.X < float64(s.Width) && 
		   p.Y >= 0 && p.Y < float64(s.Height) {
			alive = append(alive, *p)
		}
	}
	s.Particles = alive
}

// Spawn creates new particles at a position
func (s *System) Spawn(x, y float64, pType ParticleType, count int) {
	for i := 0; i < count && len(s.Particles) < s.MaxParticles; i++ {
		p := Particle{
			X:       x + (rand.Float64() - 0.5) * 2,
			Y:       y + (rand.Float64() - 0.5) * 2,
			VX:      (rand.Float64() - 0.5) * 2,
			VY:      (rand.Float64() - 0.5) * 2,
			Life:    1.0,
			MaxLife: 3.0 + rand.Float64() * 2,
			Type:    pType,
			Intensity: 1.0,
			GravityScale: 1.0,
		}
		
		// Set character and behavior based on type
		switch pType {
		case TypeAir:
			p.Char = '·'
			p.VX *= 3 // Air moves faster horizontally
			p.GravityScale = -0.2 // Air rises slightly
		case TypeWater:
			p.Char = '○'
			p.GravityScale = 3.0 // Water falls faster
		case TypeElectric:
			p.Char = '±'
			p.VX = (rand.Float64() - 0.5) * 10 // Erratic movement
			p.VY = (rand.Float64() - 0.5) * 10
			p.MaxLife = 0.5 // Short lived
			p.GravityScale = 0 // No gravity for electricity
		case TypeHeat:
			p.Char = '°'
			p.GravityScale = -1.5 // Heat rises
			p.VX = (rand.Float64() - 0.5) * 0.5 // Gentle drift
		case TypeSmoke:
			p.Char = '∙'
			p.GravityScale = -0.5 // Smoke rises slowly
		case TypePeople:
			p.Char = '●'
			p.GravityScale = 0 // People don't fall
			// Note: People need less random velocity
			p.VX = (rand.Float64() - 0.5) * 0.5
			p.VY = (rand.Float64() - 0.5) * 0.5
		}
		
		s.Particles = append(s.Particles, p)
	}
}

// Render converts particles to a character grid
func (s *System) Render() [][]rune {
	// Create empty grid
	grid := make([][]rune, s.Height)
	for i := range grid {
		grid[i] = make([]rune, s.Width)
		for j := range grid[i] {
			grid[i][j] = ' '
		}
	}
	
	// Density map for overlapping particles
	density := make([][]int, s.Height)
	for i := range density {
		density[i] = make([]int, s.Width)
	}
	
	// Place particles on grid
	for _, p := range s.Particles {
		x := int(p.X)
		y := int(p.Y)
		
		if x >= 0 && x < s.Width && y >= 0 && y < s.Height {
			density[y][x]++
			
			// Choose character based on density
			if density[y][x] == 1 {
				grid[y][x] = p.Char
			} else if density[y][x] < 4 {
				grid[y][x] = '▪'
			} else if density[y][x] < 8 {
				grid[y][x] = '■'
			} else {
				grid[y][x] = '█'
			}
		}
	}
	
	return grid
}

// EmitFromLine creates particles along a line (for vents, pipes, etc)
func (s *System) EmitFromLine(x1, y1, x2, y2 float64, pType ParticleType, rate float64) {
	steps := int(math.Max(math.Abs(x2-x1), math.Abs(y2-y1)))
	if steps == 0 {
		steps = 1
	}
	
	particlesPerStep := rate / float64(steps)
	
	for i := 0; i <= steps; i++ {
		t := float64(i) / float64(steps)
		x := x1 + t*(x2-x1)
		y := y1 + t*(y2-y1)
		
		if rand.Float64() < particlesPerStep {
			s.Spawn(x, y, pType, 1)
		}
	}
}

// AddForce applies a force to particles in a region
func (s *System) AddForce(cx, cy, radius, fx, fy float64) {
	radiusSq := radius * radius
	
	for i := range s.Particles {
		p := &s.Particles[i]
		dx := p.X - cx
		dy := p.Y - cy
		distSq := dx*dx + dy*dy
		
		if distSq < radiusSq {
			// Apply force with falloff
			strength := 1.0 - (distSq / radiusSq)
			p.VX += fx * strength
			p.VY += fy * strength
		}
	}
}

// Clear removes all particles
func (s *System) Clear() {
	s.Particles = s.Particles[:0]
}