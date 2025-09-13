// Package layers provides the layer abstraction for the ABIM rendering system
package layers


// Layer represents a rendering layer in the ABIM system
type Layer interface {
	// GetName returns the unique name of this layer
	GetName() string
	
	// GetPriority returns the rendering priority (lower renders first)
	GetPriority() int
	
	// IsVisible returns whether this layer should be rendered
	IsVisible() bool
	
	// SetVisible sets the visibility of this layer
	SetVisible(visible bool)
	
	// Render renders this layer to the provided buffer
	// The buffer is a 2D grid of runes that the layer can modify
	Render(buffer [][]rune, viewport Viewport)
	
	// Update updates the layer state (for animations, etc.)
	// deltaTime is in seconds
	Update(deltaTime float64)
	
	// GetBounds returns the bounding box of content in this layer
	GetBounds() Bounds
}

// Viewport defines the visible area for rendering
type Viewport struct {
	X, Y          float64 // Position in world coordinates
	Width, Height int     // Size in characters
	Zoom          float64 // Zoom level (1.0 = normal)
	Floor         string  // Current floor being viewed
}

// Bounds represents a rectangular boundary
type Bounds struct {
	MinX, MinY float64
	MaxX, MaxY float64
}

// LayerManager manages multiple layers for composited rendering
type LayerManager interface {
	// AddLayer adds a new layer to the manager
	AddLayer(layer Layer) error
	
	// RemoveLayer removes a layer by name
	RemoveLayer(name string) error
	
	// GetLayer returns a layer by name
	GetLayer(name string) (Layer, bool)
	
	// GetLayers returns all layers sorted by priority
	GetLayers() []Layer
	
	// SetLayerVisible sets the visibility of a layer
	SetLayerVisible(name string, visible bool) error
	
	// RenderAll renders all visible layers to the buffer
	RenderAll(buffer [][]rune, viewport Viewport)
	
	// UpdateAll updates all layers
	UpdateAll(deltaTime float64)
}

// Priority constants for standard layers
const (
	PriorityBackground = 0    // Background/grid layer
	PriorityStructure  = 10   // Walls, rooms, doors
	PriorityEquipment  = 20   // Equipment and fixtures
	PriorityConnection = 30   // Wiring, pipes, etc.
	PriorityOverlay    = 40   // Temperature, energy flow
	PriorityFailure    = 50   // Failure indicators
	PriorityParticle   = 60   // Particle effects
	PriorityUI         = 100  // UI elements, labels
)

// BaseLayer provides common functionality for all layers
type BaseLayer struct {
	name     string
	priority int
	visible  bool
	bounds   Bounds
}

// GetName returns the layer name
func (b *BaseLayer) GetName() string {
	return b.name
}

// GetPriority returns the layer priority
func (b *BaseLayer) GetPriority() int {
	return b.priority
}

// IsVisible returns whether the layer is visible
func (b *BaseLayer) IsVisible() bool {
	return b.visible
}

// SetVisible sets the layer visibility
func (b *BaseLayer) SetVisible(visible bool) {
	b.visible = visible
}

// GetBounds returns the layer bounds
func (b *BaseLayer) GetBounds() Bounds {
	return b.bounds
}

// Update does nothing by default (can be overridden)
func (b *BaseLayer) Update(deltaTime float64) {
	// Default implementation does nothing
}

// Render is a default implementation that does nothing
// Concrete layers should override this
func (b *BaseLayer) Render(buffer [][]rune, viewport Viewport) {
	// Default implementation does nothing
}

// NewBaseLayer creates a new base layer
func NewBaseLayer(name string, priority int) *BaseLayer {
	return &BaseLayer{
		name:     name,
		priority: priority,
		visible:  true,
		bounds:   Bounds{},
	}
}