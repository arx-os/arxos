package rendering

// Viewport defines the visible area of the building
type Viewport struct {
	X, Y          float64 // Position in building coordinates
	Width, Height int     // Terminal dimensions in characters
	Zoom          float64 // Zoom level (1.0 = normal)
	Floor         string  // Current floor being viewed
	FollowTarget  string  // Equipment ID to follow (if any)
}

// Region represents a rectangular area for dirty rectangle optimization
type Region struct {
	X, Y, Width, Height int
}

// LayerPriority defines standard z-indices for layers
const (
	LayerStructure   = 0   // Base floor plan
	LayerEquipment   = 10  // Equipment placement
	LayerConnections = 20  // Wiring, piping
	LayerParticles   = 30  // Dynamic particles
	LayerEnergy      = 35  // Energy flow overlay
	LayerFailure     = 40  // Failure zones
	LayerAnnotations = 50  // Text labels
	LayerUI          = 100 // UI overlays
)
