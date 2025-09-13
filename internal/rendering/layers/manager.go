package layers

import (
	"fmt"
	"sort"
	"sync"
)

// Manager implements the LayerManager interface
type Manager struct {
	layers map[string]Layer
	mu     sync.RWMutex
}

// NewManager creates a new layer manager
func NewManager() *Manager {
	return &Manager{
		layers: make(map[string]Layer),
	}
}

// AddLayer adds a new layer to the manager
func (m *Manager) AddLayer(layer Layer) error {
	if layer == nil {
		return fmt.Errorf("cannot add nil layer")
	}
	
	m.mu.Lock()
	defer m.mu.Unlock()
	
	name := layer.GetName()
	if _, exists := m.layers[name]; exists {
		return fmt.Errorf("layer %s already exists", name)
	}
	
	m.layers[name] = layer
	return nil
}

// RemoveLayer removes a layer by name
func (m *Manager) RemoveLayer(name string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	if _, exists := m.layers[name]; !exists {
		return fmt.Errorf("layer %s not found", name)
	}
	
	delete(m.layers, name)
	return nil
}

// GetLayer returns a layer by name
func (m *Manager) GetLayer(name string) (Layer, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	layer, exists := m.layers[name]
	return layer, exists
}

// GetLayers returns all layers sorted by priority
func (m *Manager) GetLayers() []Layer {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	layers := make([]Layer, 0, len(m.layers))
	for _, layer := range m.layers {
		layers = append(layers, layer)
	}
	
	// Sort by priority (lower priority renders first)
	sort.Slice(layers, func(i, j int) bool {
		return layers[i].GetPriority() < layers[j].GetPriority()
	})
	
	return layers
}

// SetLayerVisible sets the visibility of a layer
func (m *Manager) SetLayerVisible(name string, visible bool) error {
	m.mu.RLock()
	layer, exists := m.layers[name]
	m.mu.RUnlock()
	
	if !exists {
		return fmt.Errorf("layer %s not found", name)
	}
	
	layer.SetVisible(visible)
	return nil
}

// RenderAll renders all visible layers to the buffer
func (m *Manager) RenderAll(buffer [][]rune, viewport Viewport) {
	layers := m.GetLayers()
	
	for _, layer := range layers {
		if layer.IsVisible() {
			layer.Render(buffer, viewport)
		}
	}
}

// UpdateAll updates all layers
func (m *Manager) UpdateAll(deltaTime float64) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	for _, layer := range m.layers {
		layer.Update(deltaTime)
	}
}

// Clear removes all layers
func (m *Manager) Clear() {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.layers = make(map[string]Layer)
}

// GetLayerNames returns the names of all layers
func (m *Manager) GetLayerNames() []string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	names := make([]string, 0, len(m.layers))
	for name := range m.layers {
		names = append(names, name)
	}
	
	sort.Strings(names)
	return names
}

// SetLayerPriority changes the priority of a layer
func (m *Manager) SetLayerPriority(name string, priority int) error {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	layer, exists := m.layers[name]
	if !exists {
		return fmt.Errorf("layer %s not found", name)
	}
	
	// This would require the Layer interface to have a SetPriority method
	// For now, we can't change priority after creation
	_ = layer
	_ = priority
	
	return fmt.Errorf("changing layer priority not yet implemented")
}