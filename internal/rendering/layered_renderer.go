package rendering

import (
	"fmt"
	"strings"
	
	"github.com/arx-os/arxos/internal/rendering/layers"
	"github.com/arx-os/arxos/pkg/models"
)

// LayeredRenderer is a renderer that uses the layer system for composition
type LayeredRenderer struct {
	width       int
	height      int
	buffer      [][]rune
	layerMgr    *layers.Manager
	viewport    layers.Viewport
}

// NewLayeredRenderer creates a new layered renderer
func NewLayeredRenderer(width, height int) *LayeredRenderer {
	r := &LayeredRenderer{
		width:    width,
		height:   height,
		buffer:   make([][]rune, height),
		layerMgr: layers.NewManager(),
		viewport: layers.Viewport{
			X:      0,
			Y:      0,
			Width:  width,
			Height: height,
			Zoom:   1.0,
			Floor:  "",
		},
	}
	
	// Initialize buffer
	for i := range r.buffer {
		r.buffer[i] = make([]rune, width)
	}
	
	r.Clear()
	return r
}

// Clear clears the render buffer
func (r *LayeredRenderer) Clear() {
	for i := range r.buffer {
		for j := range r.buffer[i] {
			r.buffer[i][j] = ' '
		}
	}
}

// AddLayer adds a layer to the renderer
func (r *LayeredRenderer) AddLayer(layer layers.Layer) error {
	return r.layerMgr.AddLayer(layer)
}

// RemoveLayer removes a layer by name
func (r *LayeredRenderer) RemoveLayer(name string) error {
	return r.layerMgr.RemoveLayer(name)
}

// GetLayer returns a layer by name
func (r *LayeredRenderer) GetLayer(name string) (layers.Layer, bool) {
	return r.layerMgr.GetLayer(name)
}

// SetLayerVisible sets the visibility of a layer
func (r *LayeredRenderer) SetLayerVisible(name string, visible bool) error {
	return r.layerMgr.SetLayerVisible(name, visible)
}

// GetLayerNames returns the names of all layers
func (r *LayeredRenderer) GetLayerNames() []string {
	return r.layerMgr.GetLayerNames()
}

// SetViewport sets the viewport for rendering
func (r *LayeredRenderer) SetViewport(viewport layers.Viewport) {
	r.viewport = viewport
	r.viewport.Width = r.width
	r.viewport.Height = r.height
}

// GetViewport returns the current viewport
func (r *LayeredRenderer) GetViewport() layers.Viewport {
	return r.viewport
}

// Pan moves the viewport by the given offset
func (r *LayeredRenderer) Pan(dx, dy float64) {
	r.viewport.X += dx
	r.viewport.Y += dy
}

// Zoom changes the zoom level
func (r *LayeredRenderer) Zoom(factor float64) {
	r.viewport.Zoom *= factor
	if r.viewport.Zoom < 0.1 {
		r.viewport.Zoom = 0.1
	}
	if r.viewport.Zoom > 10.0 {
		r.viewport.Zoom = 10.0
	}
}

// Update updates all layers
func (r *LayeredRenderer) Update(deltaTime float64) {
	r.layerMgr.UpdateAll(deltaTime)
}

// Render renders all layers to the buffer
func (r *LayeredRenderer) Render() string {
	// Clear buffer
	r.Clear()
	
	// Render all layers
	r.layerMgr.RenderAll(r.buffer, r.viewport)
	
	// Convert buffer to string
	var output strings.Builder
	for _, row := range r.buffer {
		output.WriteString(string(row))
		output.WriteRune('\n')
	}
	
	return output.String()
}

// RenderFloorPlan sets up layers for a floor plan and renders it
func (r *LayeredRenderer) RenderFloorPlan(plan *models.FloorPlan) error {
	if plan == nil {
		return fmt.Errorf("floor plan is nil")
	}
	
	// Clear existing layers
	r.layerMgr.Clear()
	
	// Add structure layer
	structureLayer := layers.NewStructureLayer(plan)
	if err := r.AddLayer(structureLayer); err != nil {
		return fmt.Errorf("failed to add structure layer: %w", err)
	}
	
	// Add equipment layer
	if len(plan.Equipment) > 0 {
		equipmentLayer := layers.NewEquipmentLayer(plan.Equipment)
		if err := r.AddLayer(equipmentLayer); err != nil {
			return fmt.Errorf("failed to add equipment layer: %w", err)
		}
	}
	
	// Note: Connection layer would be added here when connection data is available
	// For now, connections are not part of the FloorPlan model
	
	// Set viewport to show the entire floor plan
	r.FitToContent()
	
	return nil
}

// AddConnectionLayer adds a connection layer to the renderer
func (r *LayeredRenderer) AddConnectionLayer(connections []layers.Connection, equipment []models.Equipment) error {
	connectionLayer := layers.NewConnectionLayer(connections, equipment)
	return r.AddLayer(connectionLayer)
}

// FitToContent adjusts the viewport to show all layers
func (r *LayeredRenderer) FitToContent() {
	allLayers := r.layerMgr.GetLayers()
	if len(allLayers) == 0 {
		return
	}
	
	// Find the bounds of all content
	minX, minY := float64(1e9), float64(1e9)
	maxX, maxY := float64(-1e9), float64(-1e9)
	
	for _, layer := range allLayers {
		bounds := layer.GetBounds()
		if bounds.MinX < minX {
			minX = bounds.MinX
		}
		if bounds.MinY < minY {
			minY = bounds.MinY
		}
		if bounds.MaxX > maxX {
			maxX = bounds.MaxX
		}
		if bounds.MaxY > maxY {
			maxY = bounds.MaxY
		}
	}
	
	// Calculate zoom to fit content
	contentWidth := maxX - minX
	contentHeight := maxY - minY
	
	if contentWidth > 0 && contentHeight > 0 {
		zoomX := float64(r.width-4) / contentWidth   // Leave some margin
		zoomY := float64(r.height-4) / contentHeight
		
		// Use the smaller zoom to ensure everything fits
		zoom := zoomX
		if zoomY < zoom {
			zoom = zoomY
		}
		
		// Limit zoom range
		if zoom < 0.1 {
			zoom = 0.1
		}
		if zoom > 2.0 {
			zoom = 2.0
		}
		
		// Center the content
		r.viewport.X = minX - 2/zoom // Small margin
		r.viewport.Y = minY - 2/zoom
		r.viewport.Zoom = zoom
	}
}

// GetInfo returns information about the renderer state
func (r *LayeredRenderer) GetInfo() string {
	layerCount := len(r.layerMgr.GetLayerNames())
	visibleCount := 0
	
	for _, layer := range r.layerMgr.GetLayers() {
		if layer.IsVisible() {
			visibleCount++
		}
	}
	
	return fmt.Sprintf("Viewport: (%.1f, %.1f) Zoom: %.1fx | Layers: %d visible / %d total",
		r.viewport.X, r.viewport.Y, r.viewport.Zoom,
		visibleCount, layerCount)
}