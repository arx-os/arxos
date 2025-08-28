// Package layers provides Go bindings for the C ASCII rendering engine
package layers

/*
#cgo CFLAGS: -I../../ascii
#cgo LDFLAGS: -L../../ascii -lpixatool
#include "pixatool_engine.h"
#include <stdlib.h>
*/
import "C"
import (
	"fmt"
	"unsafe"
	
	"github.com/arxos/arxos/core/internal/arxobject"
)

// MaterialType represents different building materials
type MaterialType int

const (
	MaterialEmpty         MaterialType = C.MATERIAL_EMPTY
	MaterialWall          MaterialType = C.MATERIAL_WALL
	MaterialDoor          MaterialType = C.MATERIAL_DOOR
	MaterialWindow        MaterialType = C.MATERIAL_WINDOW
	MaterialEquipment     MaterialType = C.MATERIAL_EQUIPMENT
	MaterialOutlet        MaterialType = C.MATERIAL_OUTLET
	MaterialPanel         MaterialType = C.MATERIAL_PANEL
	MaterialRoomOffice    MaterialType = C.MATERIAL_ROOM_OFFICE
	MaterialRoomCorridor  MaterialType = C.MATERIAL_ROOM_CORRIDOR
	MaterialRoomClassroom MaterialType = C.MATERIAL_ROOM_CLASSROOM
	MaterialRoomLarge     MaterialType = C.MATERIAL_ROOM_LARGE
)

// ASCIICanvas wraps the C ASCII canvas
type ASCIICanvas struct {
	canvas *C.ASCIICanvas
	Width  int
	Height int
}

// NewASCIICanvas creates a new ASCII rendering canvas
func NewASCIICanvas(width, height int) *ASCIICanvas {
	cCanvas := C.create_ascii_canvas(C.int(width), C.int(height))
	if cCanvas == nil {
		return nil
	}
	
	return &ASCIICanvas{
		canvas: cCanvas,
		Width:  width,
		Height: height,
	}
}

// Destroy frees the canvas resources
func (c *ASCIICanvas) Destroy() {
	if c.canvas != nil {
		C.destroy_canvas(c.canvas)
		c.canvas = nil
	}
}

// RenderToASCII converts the render buffer to ASCII characters
func (c *ASCIICanvas) RenderToASCII() {
	if c.canvas != nil {
		C.render_to_ascii(c.canvas)
	}
}

// DetectEdges runs edge detection on the render buffer
func (c *ASCIICanvas) DetectEdges() {
	if c.canvas != nil {
		C.detect_edges(c.canvas)
	}
}

// ApplyAntialiasing smooths the rendered output
func (c *ASCIICanvas) ApplyAntialiasing() {
	if c.canvas != nil {
		C.apply_antialiasing(c.canvas)
	}
}

// ApplyDithering adds dithering for better depth perception
func (c *ASCIICanvas) ApplyDithering() {
	if c.canvas != nil {
		C.apply_dithering(c.canvas)
	}
}

// RenderWall draws a wall segment
func (c *ASCIICanvas) RenderWall(x1, y1, x2, y2 int, depth float32) {
	if c.canvas != nil {
		C.render_wall(c.canvas, C.int(x1), C.int(y1), C.int(x2), C.int(y2), C.float(depth))
	}
}

// RenderDoor draws a door
func (c *ASCIICanvas) RenderDoor(x, y, width int, horizontal bool) {
	if c.canvas != nil {
		horiz := 0
		if horizontal {
			horiz = 1
		}
		C.render_door(c.canvas, C.int(x), C.int(y), C.int(width), C.int(horiz))
	}
}

// RenderEquipment draws equipment of a specific type
func (c *ASCIICanvas) RenderEquipment(x, y int, materialType MaterialType) {
	if c.canvas != nil {
		C.render_equipment(c.canvas, C.int(x), C.int(y), C.MaterialType(materialType))
	}
}

// FillRoom fills a room with a specific material type
func (c *ASCIICanvas) FillRoom(x, y, width, height int, roomType MaterialType) {
	if c.canvas != nil {
		C.fill_room(c.canvas, C.int(x), C.int(y), C.int(width), C.int(height), C.MaterialType(roomType))
	}
}

// GetASCIIBuffer returns the rendered ASCII as a string
func (c *ASCIICanvas) GetASCIIBuffer() string {
	if c.canvas == nil || c.canvas.ascii_buffer == nil {
		return ""
	}
	
	// Calculate buffer size
	bufferSize := c.Width * c.Height
	
	// Convert C string to Go string
	return C.GoStringN(c.canvas.ascii_buffer, C.int(bufferSize))
}

// PrintCanvas outputs the canvas to stdout
func (c *ASCIICanvas) PrintCanvas() {
	if c.canvas != nil {
		C.print_canvas(c.canvas)
	}
}

// SetScaleFactor adjusts the rendering scale
func (c *ASCIICanvas) SetScaleFactor(scale float32) {
	if c.canvas != nil {
		c.canvas.scale_factor = C.float(scale)
	}
}

// SetDepthRange sets the depth buffer range
func (c *ASCIICanvas) SetDepthRange(min, max float32) {
	if c.canvas != nil {
		c.canvas.depth_range_min = C.float(min)
		c.canvas.depth_range_max = C.float(max)
	}
}

// RenderArxObject renders an ArxObject to the canvas
func (c *ASCIICanvas) RenderArxObject(obj *arxobject.ArxObjectUnified, viewport Viewport) {
	if c.canvas == nil || obj == nil {
		return
	}
	
	// Convert world coordinates to screen coordinates
	screenX, screenY := c.worldToScreen(
		float64(obj.Geometry.Position.X),
		float64(obj.Geometry.Position.Y),
		viewport,
	)
	
	// Calculate depth for z-buffering
	depth := c.calculateDepth(float64(obj.Geometry.Position.Z), viewport)
	
	// Render based on object type
	material := c.getMaterialForType(obj.Type)
	
	switch obj.Type {
	case arxobject.TypeWall:
		// Render wall segments
		bbox := obj.Geometry.BoundingBox
		x1, y1 := c.worldToScreen(float64(bbox.Min.X), float64(bbox.Min.Y), viewport)
		x2, y2 := c.worldToScreen(float64(bbox.Max.X), float64(bbox.Max.Y), viewport)
		c.RenderWall(x1, y1, x2, y2, float32(depth))
		
	case arxobject.TypeDoor:
		// Determine door orientation
		width := obj.Geometry.BoundingBox.Max.X - obj.Geometry.BoundingBox.Min.X
		height := obj.Geometry.BoundingBox.Max.Y - obj.Geometry.BoundingBox.Min.Y
		horizontal := width > height
		
		doorWidth := 3 // Default door width in ASCII chars
		if horizontal {
			doorWidth = int(float64(width) * viewport.Scale)
		} else {
			doorWidth = int(float64(height) * viewport.Scale)
		}
		
		c.RenderDoor(screenX, screenY, doorWidth, horizontal)
		
	case arxobject.TypeWindow:
		c.RenderEquipment(screenX, screenY, MaterialWindow)
		
	case arxobject.TypeElectricalPanel:
		c.RenderEquipment(screenX, screenY, MaterialPanel)
		
	case arxobject.TypeElectricalOutlet:
		c.RenderEquipment(screenX, screenY, MaterialOutlet)
		
	case arxobject.TypeRoom:
		// Fill room area
		bbox := obj.Geometry.BoundingBox
		x1, y1 := c.worldToScreen(float64(bbox.Min.X), float64(bbox.Min.Y), viewport)
		x2, y2 := c.worldToScreen(float64(bbox.Max.X), float64(bbox.Max.Y), viewport)
		width := x2 - x1
		height := y2 - y1
		
		// Determine room type from properties
		roomMaterial := MaterialRoomOffice
		if roomType, exists := obj.Properties["room_type"]; exists {
			switch roomType.(string) {
			case "corridor":
				roomMaterial = MaterialRoomCorridor
			case "classroom":
				roomMaterial = MaterialRoomClassroom
			case "large":
				roomMaterial = MaterialRoomLarge
			}
		}
		
		c.FillRoom(x1, y1, width, height, roomMaterial)
		
	default:
		// Render as generic equipment
		c.RenderEquipment(screenX, screenY, material)
	}
}

// worldToScreen converts world coordinates to screen coordinates
func (c *ASCIICanvas) worldToScreen(worldX, worldY float64, viewport Viewport) (int, int) {
	// Apply viewport transformation
	screenX := (worldX - viewport.CenterX) * viewport.Scale + float64(c.Width)/2
	screenY := (worldY - viewport.CenterY) * viewport.Scale + float64(c.Height)/2
	
	// Clamp to canvas bounds
	if screenX < 0 {
		screenX = 0
	} else if screenX >= float64(c.Width) {
		screenX = float64(c.Width - 1)
	}
	
	if screenY < 0 {
		screenY = 0
	} else if screenY >= float64(c.Height) {
		screenY = float64(c.Height - 1)
	}
	
	return int(screenX), int(screenY)
}

// calculateDepth maps Z coordinate to depth buffer value
func (c *ASCIICanvas) calculateDepth(worldZ float64, viewport Viewport) float64 {
	// Normalize Z to 0-1 range based on viewport
	normalized := (worldZ - viewport.NearZ) / (viewport.FarZ - viewport.NearZ)
	
	// Clamp to valid range
	if normalized < 0 {
		normalized = 0
	} else if normalized > 1 {
		normalized = 1
	}
	
	return normalized
}

// getMaterialForType returns the material type for an ArxObject type
func (c *ASCIICanvas) getMaterialForType(objType arxobject.ArxObjectType) MaterialType {
	switch objType {
	case arxobject.TypeWall:
		return MaterialWall
	case arxobject.TypeDoor:
		return MaterialDoor
	case arxobject.TypeWindow:
		return MaterialWindow
	case arxobject.TypeElectricalPanel:
		return MaterialPanel
	case arxobject.TypeElectricalOutlet:
		return MaterialOutlet
	case arxobject.TypeRoom:
		return MaterialRoomOffice
	case arxobject.TypeFloor:
		return MaterialRoomCorridor
	default:
		return MaterialEquipment
	}
}

// Viewport defines the viewing parameters
type Viewport struct {
	CenterX float64  // World X coordinate at center of view
	CenterY float64  // World Y coordinate at center of view
	Scale   float64  // Zoom level (pixels per world unit)
	NearZ   float64  // Near clipping plane
	FarZ    float64  // Far clipping plane
}

// BatchRender renders multiple ArxObjects efficiently
func (c *ASCIICanvas) BatchRender(objects []*arxobject.ArxObjectUnified, viewport Viewport) {
	if c.canvas == nil {
		return
	}
	
	// Clear canvas first
	c.Clear()
	
	// Sort objects by depth for proper rendering order
	sortedObjects := c.sortByDepth(objects, viewport)
	
	// Render each object
	for _, obj := range sortedObjects {
		c.RenderArxObject(obj, viewport)
	}
	
	// Apply post-processing
	c.DetectEdges()
	c.ApplyAntialiasing()
	c.ApplyDithering()
	c.RenderToASCII()
}

// sortByDepth sorts objects by their Z coordinate (far to near)
func (c *ASCIICanvas) sortByDepth(objects []*arxobject.ArxObjectUnified, viewport Viewport) []*arxobject.ArxObjectUnified {
	// Simple bubble sort for now (can optimize later)
	sorted := make([]*arxobject.ArxObjectUnified, len(objects))
	copy(sorted, objects)
	
	for i := 0; i < len(sorted); i++ {
		for j := i + 1; j < len(sorted); j++ {
			if sorted[i].Geometry.Position.Z < sorted[j].Geometry.Position.Z {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}
	
	return sorted
}

// Clear resets the canvas
func (c *ASCIICanvas) Clear() {
	if c.canvas == nil {
		return
	}
	
	// Clear ASCII buffer
	if c.canvas.ascii_buffer != nil {
		bufferSize := c.Width * c.Height
		for i := 0; i < bufferSize; i++ {
			*(*C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(c.canvas.ascii_buffer)) + uintptr(i))) = C.char(' ')
		}
	}
	
	// Clear render buffer
	if c.canvas.render_buffer != nil {
		bufferSize := c.Width * c.Height
		for i := 0; i < bufferSize; i++ {
			pixel := (*C.PixelData)(unsafe.Pointer(uintptr(unsafe.Pointer(c.canvas.render_buffer)) + uintptr(i)*unsafe.Sizeof(C.PixelData{})))
			pixel.depth = C.float(1.0)
			pixel.luminance = C.float(0.0)
			pixel.edge_strength = C.float(0.0)
			pixel.material_type = C.int(MaterialEmpty)
			pixel.normal_x = C.float(0.0)
			pixel.normal_y = C.float(0.0)
			pixel.normal_z = C.float(0.0)
		}
	}
}

// RenderToString returns the ASCII representation as a string
func (c *ASCIICanvas) RenderToString() string {
	if c.canvas == nil {
		return ""
	}
	
	buffer := c.GetASCIIBuffer()
	
	// Format with line breaks
	result := ""
	for y := 0; y < c.Height; y++ {
		start := y * c.Width
		end := start + c.Width
		if end > len(buffer) {
			end = len(buffer)
		}
		if start < len(buffer) {
			result += buffer[start:end] + "\n"
		}
	}
	
	return result
}