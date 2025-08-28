// Package layers provides the terminal ASCII rendering layer
package layers

import (
	"fmt"
	"sync"
	"time"
	
	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/database"
)

// TerminalLayer implements Layer 5: Pure terminal ASCII rendering
type TerminalLayer struct {
	mu        sync.RWMutex
	canvas    *ASCIICanvas
	viewport  Viewport
	objects   map[string]*arxobject.ArxObjectUnified
	db        database.Service
	
	// Display settings
	width     int
	height    int
	zoomLevel float64
	
	// Navigation state
	currentPath string
	focusObject string
	
	// Performance metrics
	frameRate   float64
	lastRender  time.Time
	renderCount int64
}

// NewTerminalLayer creates a new terminal ASCII layer
func NewTerminalLayer(width, height int) *TerminalLayer {
	return &TerminalLayer{
		canvas:  NewASCIICanvas(width, height),
		objects: make(map[string]*arxobject.ArxObjectUnified),
		width:   width,
		height:  height,
		viewport: Viewport{
			CenterX: 0,
			CenterY: 0,
			Scale:   0.1,  // 1 pixel = 10 world units
			NearZ:   -1000,
			FarZ:    1000,
		},
		zoomLevel:   1.0,
		currentPath: "/",
		lastRender:  time.Now(),
	}
}

// SetDatabase sets the database service
func (t *TerminalLayer) SetDatabase(db database.Service) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.db = db
}

// LoadBuilding loads a building for display
func (t *TerminalLayer) LoadBuilding(buildingID string) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	if t.db == nil {
		return fmt.Errorf("database not initialized")
	}
	
	// Query all objects in the building
	query := database.Query{
		Type: "arxobject",
		Filters: []database.Filter{
			{Field: "building_id", Operator: "=", Value: buildingID},
		},
	}
	
	results, err := t.db.Query(query)
	if err != nil {
		return fmt.Errorf("failed to query building: %w", err)
	}
	
	// Convert results to ArxObjects
	t.objects = make(map[string]*arxobject.ArxObjectUnified)
	for _, result := range results {
		if obj, ok := result.(*arxobject.ArxObjectUnified); ok {
			t.objects[obj.ID] = obj
		}
	}
	
	return nil
}

// LoadFloor loads a specific floor
func (t *TerminalLayer) LoadFloor(buildingID, floorID string) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	if t.db == nil {
		return fmt.Errorf("database not initialized")
	}
	
	// Query objects on the floor
	query := database.Query{
		Type: "arxobject",
		Filters: []database.Filter{
			{Field: "building_id", Operator: "=", Value: buildingID},
			{Field: "floor_id", Operator: "=", Value: floorID},
		},
	}
	
	results, err := t.db.Query(query)
	if err != nil {
		return fmt.Errorf("failed to query floor: %w", err)
	}
	
	// Convert and store objects
	t.objects = make(map[string]*arxobject.ArxObjectUnified)
	for _, result := range results {
		if obj, ok := result.(*arxobject.ArxObjectUnified); ok {
			t.objects[obj.ID] = obj
		}
	}
	
	return nil
}

// Render renders the current view
func (t *TerminalLayer) Render() string {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	// Track render timing
	start := time.Now()
	defer func() {
		duration := time.Since(start)
		t.frameRate = 1.0 / duration.Seconds()
		t.lastRender = time.Now()
		t.renderCount++
	}()
	
	// Get visible objects
	visible := t.getVisibleObjects()
	
	// Render to canvas
	t.canvas.BatchRender(visible, t.viewport)
	
	// Get ASCII output
	output := t.canvas.RenderToString()
	
	// Add status bar
	output = t.addStatusBar(output)
	
	// Add navigation breadcrumb
	output = t.addNavigationBar(output)
	
	return output
}

// getVisibleObjects returns objects visible in current viewport
func (t *TerminalLayer) getVisibleObjects() []*arxobject.ArxObjectUnified {
	visible := []*arxobject.ArxObjectUnified{}
	
	// Calculate viewport bounds
	halfWidth := float64(t.width) / (2.0 * t.viewport.Scale)
	halfHeight := float64(t.height) / (2.0 * t.viewport.Scale)
	
	minX := int64(t.viewport.CenterX - halfWidth)
	maxX := int64(t.viewport.CenterX + halfWidth)
	minY := int64(t.viewport.CenterY - halfHeight)
	maxY := int64(t.viewport.CenterY + halfHeight)
	
	// Filter objects by viewport
	for _, obj := range t.objects {
		bbox := obj.Geometry.BoundingBox
		
		// Check if object intersects viewport
		if bbox.Max.X >= minX && bbox.Min.X <= maxX &&
		   bbox.Max.Y >= minY && bbox.Min.Y <= maxY {
			visible = append(visible, obj)
		}
	}
	
	return visible
}

// addStatusBar adds a status bar to the output
func (t *TerminalLayer) addStatusBar(output string) string {
	status := fmt.Sprintf(
		"[Zoom: %.1fx] [FPS: %.1f] [Objects: %d] [Path: %s]",
		t.zoomLevel,
		t.frameRate,
		len(t.objects),
		t.currentPath,
	)
	
	// Pad status to full width
	for len(status) < t.width {
		status += " "
	}
	
	return output + "\n" + status
}

// addNavigationBar adds navigation breadcrumb
func (t *TerminalLayer) addNavigationBar(output string) string {
	nav := fmt.Sprintf("ArxOS > %s", t.currentPath)
	
	// Add focus object if any
	if t.focusObject != "" {
		if obj, exists := t.objects[t.focusObject]; exists {
			nav += fmt.Sprintf(" > %s (%s)", obj.Name, obj.Type)
		}
	}
	
	// Pad to full width
	for len(nav) < t.width {
		nav += " "
	}
	
	return nav + "\n" + output
}

// Navigation methods

// NavigateTo navigates to a specific path
func (t *TerminalLayer) NavigateTo(path string) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	t.currentPath = path
	
	// Parse path to determine what to load
	// Format: /building/floor/zone/object
	// TODO: Implement path parsing and loading
	
	return nil
}

// Pan moves the viewport
func (t *TerminalLayer) Pan(dx, dy float64) {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	t.viewport.CenterX += dx / t.viewport.Scale
	t.viewport.CenterY += dy / t.viewport.Scale
}

// Zoom adjusts the zoom level
func (t *TerminalLayer) Zoom(factor float64) {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	t.zoomLevel *= factor
	t.viewport.Scale *= factor
	
	// Clamp zoom level
	if t.zoomLevel < 0.1 {
		t.zoomLevel = 0.1
		t.viewport.Scale = 0.01
	} else if t.zoomLevel > 100 {
		t.zoomLevel = 100
		t.viewport.Scale = 10
	}
}

// ZoomToFit adjusts viewport to fit all objects
func (t *TerminalLayer) ZoomToFit() {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	if len(t.objects) == 0 {
		return
	}
	
	// Find bounding box of all objects
	var minX, minY, maxX, maxY int64
	first := true
	
	for _, obj := range t.objects {
		bbox := obj.Geometry.BoundingBox
		
		if first {
			minX = bbox.Min.X
			minY = bbox.Min.Y
			maxX = bbox.Max.X
			maxY = bbox.Max.Y
			first = false
		} else {
			if bbox.Min.X < minX {
				minX = bbox.Min.X
			}
			if bbox.Min.Y < minY {
				minY = bbox.Min.Y
			}
			if bbox.Max.X > maxX {
				maxX = bbox.Max.X
			}
			if bbox.Max.Y > maxY {
				maxY = bbox.Max.Y
			}
		}
	}
	
	// Center viewport
	t.viewport.CenterX = float64(minX+maxX) / 2.0
	t.viewport.CenterY = float64(minY+maxY) / 2.0
	
	// Calculate scale to fit
	worldWidth := float64(maxX - minX)
	worldHeight := float64(maxY - minY)
	
	scaleX := float64(t.width) / worldWidth
	scaleY := float64(t.height) / worldHeight
	
	// Use smaller scale to fit both dimensions
	if scaleX < scaleY {
		t.viewport.Scale = scaleX * 0.9 // 90% to add margin
	} else {
		t.viewport.Scale = scaleY * 0.9
	}
	
	t.zoomLevel = t.viewport.Scale * 10
}

// FocusObject focuses on a specific object
func (t *TerminalLayer) FocusObject(objectID string) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	obj, exists := t.objects[objectID]
	if !exists {
		return fmt.Errorf("object not found: %s", objectID)
	}
	
	// Center viewport on object
	t.viewport.CenterX = float64(obj.Geometry.Position.X)
	t.viewport.CenterY = float64(obj.Geometry.Position.Y)
	
	// Set focus
	t.focusObject = objectID
	
	// Update path
	t.currentPath = obj.GetPath()
	
	return nil
}

// GetObjectAtPosition returns the object at screen coordinates
func (t *TerminalLayer) GetObjectAtPosition(screenX, screenY int) *arxobject.ArxObjectUnified {
	t.mu.RLock()
	defer t.mu.RUnlock()
	
	// Convert screen to world coordinates
	worldX := (float64(screenX) - float64(t.width)/2) / t.viewport.Scale + t.viewport.CenterX
	worldY := (float64(screenY) - float64(t.height)/2) / t.viewport.Scale + t.viewport.CenterY
	
	// Find object containing this point
	for _, obj := range t.objects {
		bbox := obj.Geometry.BoundingBox
		
		if float64(bbox.Min.X) <= worldX && worldX <= float64(bbox.Max.X) &&
		   float64(bbox.Min.Y) <= worldY && worldY <= float64(bbox.Max.Y) {
			return obj
		}
	}
	
	return nil
}

// Resize adjusts the canvas size
func (t *TerminalLayer) Resize(width, height int) {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	// Destroy old canvas
	if t.canvas != nil {
		t.canvas.Destroy()
	}
	
	// Create new canvas
	t.canvas = NewASCIICanvas(width, height)
	t.width = width
	t.height = height
}

// GetStats returns rendering statistics
func (t *TerminalLayer) GetStats() map[string]interface{} {
	t.mu.RLock()
	defer t.mu.RUnlock()
	
	return map[string]interface{}{
		"width":        t.width,
		"height":       t.height,
		"zoom_level":   t.zoomLevel,
		"viewport":     t.viewport,
		"object_count": len(t.objects),
		"frame_rate":   t.frameRate,
		"render_count": t.renderCount,
		"current_path": t.currentPath,
		"focus_object": t.focusObject,
	}
}

// Destroy cleans up resources
func (t *TerminalLayer) Destroy() {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	if t.canvas != nil {
		t.canvas.Destroy()
		t.canvas = nil
	}
}