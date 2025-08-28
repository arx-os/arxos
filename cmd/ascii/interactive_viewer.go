// Package ascii provides interactive ASCII-BIM visualization
package ascii

import (
	"fmt"
	"math"
	"strings"
	"time"

	"github.com/arxos/arxos/cmd/models"
)

// InteractiveViewer provides real-time interactive ASCII building navigation
type InteractiveViewer struct {
	Renderer        *TerminalRenderer
	CurrentPath     string
	CurrentZoom     ZoomLevel
	TargetZoom      ZoomLevel
	ZoomTransition  float64 // 0.0 to 1.0 for smooth transitions
	ViewportX       float64 // Current viewport center X
	ViewportY       float64 // Current viewport center Y
	TargetX         float64 // Target viewport center X
	TargetY         float64 // Target viewport center Y
	PanSpeed        float64
	ZoomSpeed       float64
	LastUpdate      time.Time
	AnimationActive bool
	Objects         []*models.ArxObject
	FocusObject     *models.ArxObject // Object to focus on when zooming
}

// NewInteractiveViewer creates an interactive viewer with animation support
func NewInteractiveViewer(width, height int) *InteractiveViewer {
	return &InteractiveViewer{
		Renderer:    NewTerminalRenderer(width, height),
		CurrentPath: "/",
		CurrentZoom: ZoomFloor,
		TargetZoom:  ZoomFloor,
		PanSpeed:    5.0,
		ZoomSpeed:   3.0,
		LastUpdate:  time.Now(),
	}
}

// Update processes animations and transitions
func (iv *InteractiveViewer) Update() {
	now := time.Now()
	deltaTime := now.Sub(iv.LastUpdate).Seconds()
	iv.LastUpdate = now

	// Update zoom transition
	if iv.CurrentZoom != iv.TargetZoom {
		iv.AnimationActive = true
		iv.updateZoomTransition(deltaTime)
	}

	// Update pan transition
	if iv.needsPanTransition() {
		iv.AnimationActive = true
		iv.updatePanTransition(deltaTime)
	} else if iv.CurrentZoom == iv.TargetZoom {
		iv.AnimationActive = false
	}
}

// updateZoomTransition smoothly transitions between zoom levels
func (iv *InteractiveViewer) updateZoomTransition(deltaTime float64) {
	transitionSpeed := iv.ZoomSpeed * deltaTime
	
	if iv.ZoomTransition < 1.0 {
		iv.ZoomTransition += transitionSpeed
		if iv.ZoomTransition >= 1.0 {
			iv.ZoomTransition = 0.0
			iv.CurrentZoom = iv.TargetZoom
			
			// When zooming in, center on the focus object if set
			if iv.FocusObject != nil && iv.CurrentZoom > iv.TargetZoom {
				iv.centerOnObject(iv.FocusObject)
			}
		}
	}
}

// updatePanTransition smoothly pans the viewport
func (iv *InteractiveViewer) updatePanTransition(deltaTime float64) {
	panSpeed := iv.PanSpeed * deltaTime
	
	// Smooth interpolation using ease-out curve
	dx := iv.TargetX - iv.ViewportX
	dy := iv.TargetY - iv.ViewportY
	
	iv.ViewportX += dx * panSpeed
	iv.ViewportY += dy * panSpeed
	
	// Snap to target when close enough
	if math.Abs(dx) < 0.1 && math.Abs(dy) < 0.1 {
		iv.ViewportX = iv.TargetX
		iv.ViewportY = iv.TargetY
	}
}

// ZoomIn zooms in one level with smooth transition
func (iv *InteractiveViewer) ZoomIn() {
	if iv.CurrentZoom < ZoomChip {
		iv.TargetZoom = ZoomLevel(int(iv.CurrentZoom) + 1)
		iv.ZoomTransition = 0.0
		
		// Find object at center to focus on
		iv.FocusObject = iv.findObjectAtCenter()
	}
}

// ZoomOut zooms out one level with smooth transition
func (iv *InteractiveViewer) ZoomOut() {
	if iv.CurrentZoom > ZoomCampus {
		iv.TargetZoom = ZoomLevel(int(iv.CurrentZoom) - 1)
		iv.ZoomTransition = 0.0
		iv.FocusObject = nil // No focus when zooming out
	}
}

// ZoomToLevel jumps to specific zoom level
func (iv *InteractiveViewer) ZoomToLevel(level ZoomLevel) {
	if level >= ZoomCampus && level <= ZoomChip {
		iv.TargetZoom = level
		iv.ZoomTransition = 0.0
	}
}

// Pan moves the viewport
func (iv *InteractiveViewer) Pan(dx, dy float64) {
	scale := getScaleForZoom(iv.CurrentZoom)
	iv.TargetX += dx / scale
	iv.TargetY += dy / scale
	
	// Constrain to reasonable bounds
	iv.constrainViewport()
}

// CenterOn centers the viewport on a specific path
func (iv *InteractiveViewer) CenterOn(path string) error {
	// Find the object at the path
	obj := iv.findObjectByPath(path)
	if obj == nil {
		return fmt.Errorf("object not found: %s", path)
	}
	
	iv.centerOnObject(obj)
	return nil
}

// centerOnObject centers viewport on an object
func (iv *InteractiveViewer) centerOnObject(obj *models.ArxObject) {
	if obj != nil {
		iv.TargetX = obj.Position.X
		iv.TargetY = obj.Position.Y
		iv.FocusObject = obj
	}
}

// Render generates the current view with transitions
func (iv *InteractiveViewer) Render() string {
	// Apply any interpolated rendering during transitions
	if iv.AnimationActive {
		return iv.renderTransition()
	}
	
	// Normal rendering
	return iv.renderNormal()
}

// renderTransition creates smooth transition between zoom levels
func (iv *InteractiveViewer) renderTransition() string {
	var output strings.Builder
	
	// Clear screen
	output.WriteString("\033[2J\033[H")
	
	// Calculate interpolated scale
	currentScale := getScaleForZoom(iv.CurrentZoom)
	targetScale := getScaleForZoom(iv.TargetZoom)
	
	// Use exponential interpolation for smooth zoom
	t := iv.easeInOutCubic(iv.ZoomTransition)
	scale := currentScale + (targetScale-currentScale)*t
	
	// Get interpolated character set
	charSet := iv.getInterpolatedCharSet(iv.CurrentZoom, iv.TargetZoom, t)
	
	// Render with interpolated values
	canvas := iv.renderWithScale(scale, charSet)
	
	// Add transition indicator
	output.WriteString(iv.renderHeader(true))
	output.WriteString(canvas)
	output.WriteString(iv.renderFooter())
	
	return output.String()
}

// renderNormal renders the stable view
func (iv *InteractiveViewer) renderNormal() string {
	var output strings.Builder
	
	// Clear screen
	output.WriteString("\033[2J\033[H")
	
	// Get current character set
	charSet := iv.Renderer.CharSets[iv.CurrentZoom]
	scale := getScaleForZoom(iv.CurrentZoom)
	
	// Render current view
	canvas := iv.renderWithScale(scale, charSet)
	
	// Add UI elements
	output.WriteString(iv.renderHeader(false))
	output.WriteString(canvas)
	output.WriteString(iv.renderFooter())
	
	return output.String()
}

// renderWithScale renders objects at specific scale
func (iv *InteractiveViewer) renderWithScale(scale float64, charSet CharacterSet) string {
	// Clear canvas
	iv.Renderer.clearCanvas()
	
	// Render visible objects
	for _, obj := range iv.Objects {
		if iv.isObjectVisible(obj, scale) {
			iv.renderObjectScaled(obj, scale, charSet)
		}
	}
	
	return iv.Renderer.canvasToString()
}

// renderObjectScaled renders an object with specific scale and characters
func (iv *InteractiveViewer) renderObjectScaled(obj *models.ArxObject, scale float64, charSet CharacterSet) {
	// Calculate screen position
	screenX := int((obj.Position.X - iv.ViewportX) * scale + float64(iv.Renderer.Width/2))
	screenY := int((obj.Position.Y - iv.ViewportY) * scale + float64(iv.Renderer.Height/2))
	
	// Skip if outside viewport
	if screenX < 0 || screenX >= iv.Renderer.Width || screenY < 0 || screenY >= iv.Renderer.Height {
		return
	}
	
	// Get character for object type
	char := iv.Renderer.getCharForType(obj.Type, charSet)
	
	// Place on canvas
	iv.Renderer.Canvas[screenY][screenX] = char
	
	// Add details at higher zoom levels
	if iv.CurrentZoom >= ZoomRoom && len(obj.Name) > 0 {
		iv.renderLabel(obj.Name, screenX, screenY+1)
	}
}

// renderLabel adds text label near an object
func (iv *InteractiveViewer) renderLabel(text string, x, y int) {
	if y >= 0 && y < iv.Renderer.Height {
		for i, ch := range text {
			if x+i >= 0 && x+i < iv.Renderer.Width {
				iv.Renderer.Canvas[y][x+i] = ch
			}
		}
	}
}

// getInterpolatedCharSet blends character sets during transition
func (iv *InteractiveViewer) getInterpolatedCharSet(from, to ZoomLevel, t float64) CharacterSet {
	// For smooth transitions, we can blend between character sets
	// For now, switch at midpoint
	if t < 0.5 {
		return iv.Renderer.CharSets[from]
	}
	return iv.Renderer.CharSets[to]
}

// renderHeader creates the top UI bar
func (iv *InteractiveViewer) renderHeader(transitioning bool) string {
	var header strings.Builder
	
	borderLine := strings.Repeat("═", iv.Renderer.Width-2)
	header.WriteString(fmt.Sprintf("╔%s╗\n", borderLine))
	
	// Status line
	status := fmt.Sprintf(" %s │ Zoom: %s", iv.CurrentPath, getZoomName(iv.CurrentZoom))
	if transitioning {
		status += fmt.Sprintf(" → %s", getZoomName(iv.TargetZoom))
	}
	if iv.FocusObject != nil {
		status += fmt.Sprintf(" │ Focus: %s", iv.FocusObject.Name)
	}
	
	header.WriteString(fmt.Sprintf("║%s║\n", padOrTruncate(status, iv.Renderer.Width-2)))
	header.WriteString(fmt.Sprintf("╠%s╣\n", borderLine))
	
	return header.String()
}

// renderFooter creates the bottom control bar
func (iv *InteractiveViewer) renderFooter() string {
	var footer strings.Builder
	
	borderLine := strings.Repeat("═", iv.Renderer.Width-2)
	footer.WriteString(fmt.Sprintf("╠%s╣\n", borderLine))
	
	// Controls
	controls := " +/- zoom │ ↑↓←→ pan │ 0-6 level │ / search │ q quit "
	footer.WriteString(fmt.Sprintf("║%s║\n", padOrTruncate(controls, iv.Renderer.Width-2)))
	footer.WriteString(fmt.Sprintf("╚%s╝\n", borderLine))
	
	return footer.String()
}

// Helper methods

func (iv *InteractiveViewer) needsPanTransition() bool {
	return math.Abs(iv.ViewportX-iv.TargetX) > 0.01 || math.Abs(iv.ViewportY-iv.TargetY) > 0.01
}

func (iv *InteractiveViewer) isObjectVisible(obj *models.ArxObject, scale float64) bool {
	// Calculate screen position
	screenX := (obj.Position.X - iv.ViewportX) * scale
	screenY := (obj.Position.Y - iv.ViewportY) * scale
	
	// Check if within viewport with margin
	margin := 10.0
	return screenX >= -margin && screenX < float64(iv.Renderer.Width)+margin &&
		screenY >= -margin && screenY < float64(iv.Renderer.Height)+margin
}

func (iv *InteractiveViewer) findObjectAtCenter() *models.ArxObject {
	// Find the object closest to viewport center
	var closest *models.ArxObject
	minDist := math.MaxFloat64
	
	for _, obj := range iv.Objects {
		dist := math.Sqrt(math.Pow(obj.Position.X-iv.ViewportX, 2) + 
			math.Pow(obj.Position.Y-iv.ViewportY, 2))
		if dist < minDist {
			minDist = dist
			closest = obj
		}
	}
	
	return closest
}

func (iv *InteractiveViewer) findObjectByPath(path string) *models.ArxObject {
	// Find object matching the path
	for _, obj := range iv.Objects {
		if obj.Path == path {
			return obj
		}
	}
	return nil
}

func (iv *InteractiveViewer) constrainViewport() {
	// Keep viewport within reasonable bounds based on zoom level
	maxBound := 1000.0 / getScaleForZoom(iv.CurrentZoom)
	
	if iv.TargetX < -maxBound {
		iv.TargetX = -maxBound
	} else if iv.TargetX > maxBound {
		iv.TargetX = maxBound
	}
	
	if iv.TargetY < -maxBound {
		iv.TargetY = -maxBound
	} else if iv.TargetY > maxBound {
		iv.TargetY = maxBound
	}
}

// easeInOutCubic provides smooth acceleration and deceleration
func (iv *InteractiveViewer) easeInOutCubic(t float64) float64 {
	if t < 0.5 {
		return 4 * t * t * t
	}
	p := 2*t - 2
	return 1 + p*p*p/2
}