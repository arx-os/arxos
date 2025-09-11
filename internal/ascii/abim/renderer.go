// Package abim implements the ASCII Building Information Model
// This is the central nervous system of ArxOS - all data flows through 
// and is visualized in this unified representation.
package abim

import (
	"fmt"
	"sync"
	"time"
	
	"github.com/joelpate/arxos/internal/logger"
)

// Renderer is the main ASCII Building Information Model renderer
// It manages all layers and composites them into a unified view
type Renderer struct {
	layers       map[string]Layer
	layerOrder   []string // Defines z-order
	viewport     *Viewport
	compositor   *Compositor
	updateRate   time.Duration
	mu           sync.RWMutex
	running      bool
	stopCh       chan struct{}
	dirtyRegions []Region
}

// Layer represents a visualization layer in the ABIM
type Layer interface {
	// Render produces the ASCII representation for this layer
	Render(viewport Viewport) [][]rune
	
	// Update advances the layer's state by dt seconds
	Update(dt float64)
	
	// SetVisible controls layer visibility
	SetVisible(visible bool)
	
	// IsVisible returns current visibility state
	IsVisible() bool
	
	// GetZ returns the z-index for layering (higher = on top)
	GetZ() int
	
	// GetName returns the layer name
	GetName() string
	
	// SetDirty marks regions that need re-rendering
	SetDirty(regions []Region)
}

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
	LayerStructure    = 0   // Base floor plan
	LayerEquipment    = 10  // Equipment placement
	LayerConnections  = 20  // Wiring, piping
	LayerParticles    = 30  // Dynamic particles
	LayerEnergy       = 35  // Energy flow overlay
	LayerFailure      = 40  // Failure zones
	LayerAnnotations  = 50  // Text labels
	LayerUI           = 100 // UI overlays
)

// NewRenderer creates a new ABIM renderer
func NewRenderer(width, height int) *Renderer {
	return &Renderer{
		layers:     make(map[string]Layer),
		layerOrder: []string{},
		viewport: &Viewport{
			X:      0,
			Y:      0,
			Width:  width,
			Height: height,
			Zoom:   1.0,
			Floor:  "1",
		},
		compositor:   NewCompositor(),
		updateRate:   time.Second / 30, // 30 FPS
		stopCh:       make(chan struct{}),
		dirtyRegions: []Region{},
	}
}

// AddLayer registers a new layer with the renderer
func (r *Renderer) AddLayer(name string, layer Layer) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	if _, exists := r.layers[name]; exists {
		return fmt.Errorf("layer %s already exists", name)
	}
	
	r.layers[name] = layer
	r.insertLayerOrdered(name, layer.GetZ())
	
	logger.Info("Added layer: %s (z-index: %d)", name, layer.GetZ())
	return nil
}

// RemoveLayer removes a layer from the renderer
func (r *Renderer) RemoveLayer(name string) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	if _, exists := r.layers[name]; !exists {
		return fmt.Errorf("layer %s not found", name)
	}
	
	delete(r.layers, name)
	r.removeFromOrder(name)
	
	logger.Info("Removed layer: %s", name)
	return nil
}

// SetLayerVisible controls layer visibility
func (r *Renderer) SetLayerVisible(name string, visible bool) error {
	r.mu.RLock()
	layer, exists := r.layers[name]
	r.mu.RUnlock()
	
	if !exists {
		return fmt.Errorf("layer %s not found", name)
	}
	
	layer.SetVisible(visible)
	r.markDirty(Region{0, 0, r.viewport.Width, r.viewport.Height})
	return nil
}

// Start begins the render loop
func (r *Renderer) Start() error {
	r.mu.Lock()
	if r.running {
		r.mu.Unlock()
		return fmt.Errorf("renderer already running")
	}
	r.running = true
	r.mu.Unlock()
	
	go r.renderLoop()
	logger.Info("ABIM renderer started (%.0f FPS)", 1.0/r.updateRate.Seconds())
	return nil
}

// Stop halts the render loop
func (r *Renderer) Stop() {
	r.mu.Lock()
	if !r.running {
		r.mu.Unlock()
		return
	}
	r.running = false
	r.mu.Unlock()
	
	close(r.stopCh)
	logger.Info("ABIM renderer stopped")
}

// Render produces the current frame
func (r *Renderer) Render() [][]rune {
	r.mu.RLock()
	defer r.mu.RUnlock()
	
	// Collect renders from all visible layers in order
	layerRenders := make([][][]rune, 0, len(r.layerOrder))
	
	for _, name := range r.layerOrder {
		layer := r.layers[name]
		if layer.IsVisible() {
			rendered := layer.Render(*r.viewport)
			layerRenders = append(layerRenders, rendered)
		}
	}
	
	// Composite all layers
	return r.compositor.Composite(layerRenders, r.viewport.Width, r.viewport.Height)
}

// Update advances all layers by dt seconds
func (r *Renderer) Update(dt float64) {
	r.mu.RLock()
	layers := make([]Layer, 0, len(r.layers))
	for _, layer := range r.layers {
		layers = append(layers, layer)
	}
	r.mu.RUnlock()
	
	// Update all layers
	for _, layer := range layers {
		layer.Update(dt)
	}
	
	// Update viewport if following a target
	if r.viewport.FollowTarget != "" {
		r.updateFollowTarget()
	}
}

// SetViewport updates the viewport settings
func (r *Renderer) SetViewport(vp Viewport) {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	oldVP := *r.viewport
	*r.viewport = vp
	
	// Mark dirty if viewport changed
	if oldVP.X != vp.X || oldVP.Y != vp.Y || 
	   oldVP.Zoom != vp.Zoom || oldVP.Floor != vp.Floor {
		r.markDirty(Region{0, 0, vp.Width, vp.Height})
	}
}

// Pan moves the viewport by dx, dy
func (r *Renderer) Pan(dx, dy float64) {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	r.viewport.X += dx
	r.viewport.Y += dy
	r.markDirty(Region{0, 0, r.viewport.Width, r.viewport.Height})
}

// Zoom adjusts the zoom level
func (r *Renderer) Zoom(factor float64) {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	r.viewport.Zoom *= factor
	if r.viewport.Zoom < 0.1 {
		r.viewport.Zoom = 0.1
	} else if r.viewport.Zoom > 10.0 {
		r.viewport.Zoom = 10.0
	}
	r.markDirty(Region{0, 0, r.viewport.Width, r.viewport.Height})
}

// SetFloor changes the current floor
func (r *Renderer) SetFloor(floor string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	r.viewport.Floor = floor
	r.markDirty(Region{0, 0, r.viewport.Width, r.viewport.Height})
}

// GetLayerNames returns all registered layer names
func (r *Renderer) GetLayerNames() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	
	names := make([]string, len(r.layerOrder))
	copy(names, r.layerOrder)
	return names
}

// Private methods

func (r *Renderer) renderLoop() {
	ticker := time.NewTicker(r.updateRate)
	defer ticker.Stop()
	
	lastUpdate := time.Now()
	
	for {
		select {
		case <-r.stopCh:
			return
		case now := <-ticker.C:
			dt := now.Sub(lastUpdate).Seconds()
			lastUpdate = now
			
			// Update all layers
			r.Update(dt)
			
			// Note: Actual rendering would be triggered by dirty regions
			// and sent to the terminal output
		}
	}
}

func (r *Renderer) insertLayerOrdered(name string, z int) {
	// Insert layer name in z-order
	inserted := false
	for i, existingName := range r.layerOrder {
		if r.layers[existingName].GetZ() > z {
			r.layerOrder = append(r.layerOrder[:i], append([]string{name}, r.layerOrder[i:]...)...)
			inserted = true
			break
		}
	}
	
	if !inserted {
		r.layerOrder = append(r.layerOrder, name)
	}
}

func (r *Renderer) removeFromOrder(name string) {
	for i, n := range r.layerOrder {
		if n == name {
			r.layerOrder = append(r.layerOrder[:i], r.layerOrder[i+1:]...)
			break
		}
	}
}

func (r *Renderer) markDirty(region Region) {
	// Optimize: merge overlapping regions
	r.dirtyRegions = append(r.dirtyRegions, region)
}

func (r *Renderer) updateFollowTarget() {
	// This would update viewport position to follow a specific equipment
	// Implementation would query equipment position from appropriate layer
}