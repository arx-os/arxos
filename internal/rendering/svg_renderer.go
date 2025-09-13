package rendering

import (
	"fmt"
	"strings"

	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// SVGRenderer generates SVG visualizations for floor plans
type SVGRenderer struct {
	width      float64
	height     float64
	padding    float64
	gridSize   float64
	showGrid   bool
	showLabels bool
}

// NewSVGRenderer creates a new SVG renderer
func NewSVGRenderer() *SVGRenderer {
	return &SVGRenderer{
		width:      800,
		height:     600,
		padding:    20,
		gridSize:   20,
		showGrid:   true,
		showLabels: true,
	}
}

// RenderOptions configures rendering behavior
type RenderOptions struct {
	Width      float64
	Height     float64
	ShowGrid   bool
	ShowLabels bool
	GridSize   float64
	Theme      string // light, dark, blueprint
}

// DefaultRenderOptions returns default rendering options
func DefaultRenderOptions() *RenderOptions {
	return &RenderOptions{
		Width:      800,
		Height:     600,
		ShowGrid:   true,
		ShowLabels: true,
		GridSize:   20,
		Theme:      "light",
	}
}

// RenderFloorPlan generates an SVG visualization of a floor plan
func (r *SVGRenderer) RenderFloorPlan(plan *models.FloorPlan, opts *RenderOptions) string {
	logger.Debug("Starting SVG render for floor plan: %s", plan.Name)
	
	if opts == nil {
		opts = DefaultRenderOptions()
	}

	// Calculate bounds
	logger.Debug("Calculating bounds for %d rooms", len(plan.Rooms))
	bounds := r.calculateBounds(plan)
	logger.Debug("Bounds: MinX=%g, MinY=%g, MaxX=%g, MaxY=%g", bounds.MinX, bounds.MinY, bounds.MaxX, bounds.MaxY)
	
	scale := r.calculateScale(bounds, opts.Width, opts.Height)
	logger.Debug("Scale factor: %g", scale)

	// Start SVG
	var svg strings.Builder
	svg.WriteString(fmt.Sprintf(`<svg width="%g" height="%g" viewBox="0 0 %g %g" xmlns="http://www.w3.org/2000/svg">`,
		opts.Width, opts.Height, opts.Width, opts.Height))
	
	// Add styles
	svg.WriteString(r.renderStyles(opts.Theme))
	
	// Add definitions (patterns, markers, etc.)
	svg.WriteString(r.renderDefs())
	
	// Background
	svg.WriteString(fmt.Sprintf(`<rect width="%g" height="%g" class="svg-background"/>`, opts.Width, opts.Height))
	
	// Grid
	if opts.ShowGrid {
		svg.WriteString(r.renderGrid(opts.Width, opts.Height, opts.GridSize))
	}
	
	// Main group with transform
	svg.WriteString(fmt.Sprintf(`<g transform="translate(%g,%g) scale(%g,%g)">`,
		r.padding, r.padding, scale, scale))
	
	// Render rooms
	for _, room := range plan.Rooms {
		svg.WriteString(r.renderRoom(&room, opts.ShowLabels))
	}
	
	// Render equipment
	for _, equip := range plan.Equipment {
		svg.WriteString(r.renderEquipment(&equip, opts.ShowLabels))
	}
	
	svg.WriteString(`</g>`)
	
	// Title and metadata
	svg.WriteString(r.renderMetadata(plan))
	
	svg.WriteString(`</svg>`)
	
	return svg.String()
}

// renderStyles generates CSS styles for the SVG
func (r *SVGRenderer) renderStyles(theme string) string {
	switch theme {
	case "dark":
		return `<style>
			.svg-background { fill: #1a1a1a; }
			.grid-line { stroke: #333; stroke-width: 0.5; opacity: 0.3; }
			.room { fill: #2a2a2a; stroke: #666; stroke-width: 2; }
			.room-label { fill: #fff; font-family: Arial, sans-serif; font-size: 14px; }
			.equipment { stroke: #4a9eff; stroke-width: 2; }
			.equipment-outlet { fill: #4a9eff; }
			.equipment-switch { fill: #ffa500; }
			.equipment-panel { fill: #ff4444; }
			.equipment-label { fill: #ccc; font-family: Arial, sans-serif; font-size: 10px; }
		</style>`
	case "blueprint":
		return `<style>
			.svg-background { fill: #003366; }
			.grid-line { stroke: #0066cc; stroke-width: 0.5; opacity: 0.2; }
			.room { fill: none; stroke: #fff; stroke-width: 1.5; }
			.room-label { fill: #fff; font-family: "Courier New", monospace; font-size: 12px; }
			.equipment { stroke: #ffff00; stroke-width: 1.5; }
			.equipment-outlet { fill: #ffff00; }
			.equipment-switch { fill: #00ff00; }
			.equipment-panel { fill: #ff00ff; }
			.equipment-label { fill: #ffff00; font-family: "Courier New", monospace; font-size: 9px; }
		</style>`
	default: // light theme
		return `<style>
			.svg-background { fill: #fff; }
			.grid-line { stroke: #e0e0e0; stroke-width: 0.5; }
			.room { fill: #f8f8f8; stroke: #333; stroke-width: 2; }
			.room-label { fill: #333; font-family: Arial, sans-serif; font-size: 14px; }
			.equipment { stroke: #0066cc; stroke-width: 2; }
			.equipment-outlet { fill: #0066cc; }
			.equipment-switch { fill: #ff9900; }
			.equipment-panel { fill: #cc0000; }
			.equipment-label { fill: #666; font-family: Arial, sans-serif; font-size: 10px; }
			.room:hover { fill: #e8f4ff; }
			.equipment:hover { transform: scale(1.2); transform-origin: center; }
		</style>`
	}
}

// renderDefs generates SVG definitions for patterns and markers
func (r *SVGRenderer) renderDefs() string {
	return `<defs>
		<pattern id="hatch" patternUnits="userSpaceOnUse" width="4" height="4">
			<path d="M0,4 l4,-4 M-1,1 l2,-2 M3,5 l2,-2" stroke="#ccc" stroke-width="0.5"/>
		</pattern>
		<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
			<path d="M0,0 L0,6 L9,3 z" fill="#666"/>
		</marker>
	</defs>`
}

// renderGrid generates a background grid
func (r *SVGRenderer) renderGrid(width, height, gridSize float64) string {
	// Safety check to prevent infinite loops
	if gridSize <= 0 {
		gridSize = 20 // Default grid size
	}
	
	var grid strings.Builder
	grid.WriteString(`<g class="grid">`)
	
	// Vertical lines (with safety limit)
	maxLines := int(width/gridSize) + 1
	if maxLines > 1000 {
		maxLines = 1000 // Prevent excessive lines
	}
	for i := 1; i < maxLines; i++ {
		x := float64(i) * gridSize
		if x >= width {
			break
		}
		grid.WriteString(fmt.Sprintf(`<line x1="%g" y1="0" x2="%g" y2="%g" class="grid-line"/>`,
			x, x, height))
	}
	
	// Horizontal lines (with safety limit)
	maxLines = int(height/gridSize) + 1
	if maxLines > 1000 {
		maxLines = 1000 // Prevent excessive lines
	}
	for i := 1; i < maxLines; i++ {
		y := float64(i) * gridSize
		if y >= height {
			break
		}
		grid.WriteString(fmt.Sprintf(`<line x1="0" y1="%g" x2="%g" y2="%g" class="grid-line"/>`,
			y, width, y))
	}
	
	grid.WriteString(`</g>`)
	return grid.String()
}

// renderRoom generates SVG for a room
func (r *SVGRenderer) renderRoom(room *models.Room, showLabel bool) string {
	var svg strings.Builder
	
	// Room rectangle
	svg.WriteString(fmt.Sprintf(`<rect x="%g" y="%g" width="%g" height="%g" class="room" data-room-id="%s"/>`,
		room.Bounds.MinX, room.Bounds.MinY,
		room.Bounds.Width(), room.Bounds.Height(),
		room.ID))
	
	// Room label
	if showLabel && room.Name != "" {
		centerX := room.Bounds.MinX + room.Bounds.Width()/2
		centerY := room.Bounds.MinY + room.Bounds.Height()/2
		svg.WriteString(fmt.Sprintf(`<text x="%g" y="%g" text-anchor="middle" class="room-label">%s</text>`,
			centerX, centerY, room.Name))
	}
	
	return svg.String()
}

// renderEquipment generates SVG for equipment
func (r *SVGRenderer) renderEquipment(equip *models.Equipment, showLabel bool) string {
	var svg strings.Builder
	
	// Different shapes for different equipment types
	switch equip.Type {
	case "outlet":
		svg.WriteString(fmt.Sprintf(`<circle cx="%g" cy="%g" r="5" class="equipment equipment-outlet" data-equipment-id="%s"/>`,
			equip.Location.X, equip.Location.Y, equip.ID))
	case "switch":
		svg.WriteString(fmt.Sprintf(`<rect x="%g" y="%g" width="10" height="10" class="equipment equipment-switch" data-equipment-id="%s"/>`,
			equip.Location.X-5, equip.Location.Y-5, equip.ID))
	case "panel":
		svg.WriteString(fmt.Sprintf(`<rect x="%g" y="%g" width="15" height="20" class="equipment equipment-panel" data-equipment-id="%s"/>`,
			equip.Location.X-7.5, equip.Location.Y-10, equip.ID))
	default:
		// Generic equipment
		svg.WriteString(fmt.Sprintf(`<circle cx="%g" cy="%g" r="4" class="equipment" data-equipment-id="%s"/>`,
			equip.Location.X, equip.Location.Y, equip.ID))
	}
	
	// Equipment label
	if showLabel && equip.Name != "" {
		svg.WriteString(fmt.Sprintf(`<text x="%g" y="%g" text-anchor="middle" class="equipment-label">%s</text>`,
			equip.Location.X, equip.Location.Y+15, equip.Name))
	}
	
	// Status indicator
	if equip.Status == models.StatusFailed {
		svg.WriteString(fmt.Sprintf(`<circle cx="%g" cy="%g" r="8" fill="none" stroke="red" stroke-width="2" opacity="0.5"/>`,
			equip.Location.X, equip.Location.Y))
	} else if equip.Status == models.StatusNeedsRepair {
		svg.WriteString(fmt.Sprintf(`<circle cx="%g" cy="%g" r="8" fill="none" stroke="orange" stroke-width="2" opacity="0.5"/>`,
			equip.Location.X, equip.Location.Y))
	}
	
	return svg.String()
}

// renderMetadata adds title and metadata to the SVG
func (r *SVGRenderer) renderMetadata(plan *models.FloorPlan) string {
	return fmt.Sprintf(`<text x="10" y="20" class="room-label">%s - Level %d</text>`,
		plan.Building, plan.Level)
}

// calculateBounds determines the bounding box of all elements
func (r *SVGRenderer) calculateBounds(plan *models.FloorPlan) models.Bounds {
	if len(plan.Rooms) == 0 {
		return models.Bounds{MinX: 0, MinY: 0, MaxX: 100, MaxY: 100}
	}
	
	bounds := plan.Rooms[0].Bounds
	
	for _, room := range plan.Rooms[1:] {
		if room.Bounds.MinX < bounds.MinX {
			bounds.MinX = room.Bounds.MinX
		}
		if room.Bounds.MinY < bounds.MinY {
			bounds.MinY = room.Bounds.MinY
		}
		if room.Bounds.MaxX > bounds.MaxX {
			bounds.MaxX = room.Bounds.MaxX
		}
		if room.Bounds.MaxY > bounds.MaxY {
			bounds.MaxY = room.Bounds.MaxY
		}
	}
	
	return bounds
}

// calculateScale determines the scale factor to fit the floor plan
func (r *SVGRenderer) calculateScale(bounds models.Bounds, width, height float64) float64 {
	availableWidth := width - 2*r.padding
	availableHeight := height - 2*r.padding
	
	boundsWidth := bounds.Width()
	boundsHeight := bounds.Height()
	
	// Prevent division by zero
	if boundsWidth <= 0 || boundsHeight <= 0 {
		return 1.0
	}
	
	scaleX := availableWidth / boundsWidth
	scaleY := availableHeight / boundsHeight
	
	// Use the smaller scale to ensure everything fits
	if scaleX < scaleY {
		return scaleX
	}
	return scaleY
}

// RenderConnection renders a connection between equipment
func (r *SVGRenderer) RenderConnection(from, to models.Point, connectionType string) string {
	color := "#666"
	switch connectionType {
	case "power":
		color = "#ff0000"
	case "data":
		color = "#0000ff"
	case "hvac":
		color = "#00ff00"
	}
	
	return fmt.Sprintf(`<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="1" stroke-dasharray="5,5" marker-end="url(#arrow)"/>`,
		from.X, from.Y, to.X, to.Y, color)
}