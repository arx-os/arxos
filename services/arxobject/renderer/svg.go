// Package renderer provides ultra-fast ArxObject to SVG rendering
package renderer

import (
	"fmt"
	"io"
	"strings"
	"sync"

	"github.com/arxos/arxos/services/arxobject/engine"
)

// SVGRenderer renders ArxObjects directly to SVG
type SVGRenderer struct {
	width      int
	height     int
	viewBox    ViewBox
	scale      float64
	
	// Performance optimizations
	buffer     strings.Builder
	bufferPool sync.Pool
	
	// Style management
	styles     map[string]string
	classes    map[engine.ArxObjectType]string
}

// ViewBox defines the SVG viewport
type ViewBox struct {
	MinX, MinY, Width, Height float64
}

// RenderOptions configures rendering behavior
type RenderOptions struct {
	ShowLabels      bool
	ShowDimensions  bool
	ShowGrid        bool
	GridSpacing     float64
	Layer           string // floor, ceiling, elevation
	Precision       int    // decimal places for coordinates
	Optimize        bool   // enable SVG optimization
}

// NewSVGRenderer creates a new SVG renderer
func NewSVGRenderer(width, height int) *SVGRenderer {
	return &SVGRenderer{
		width:   width,
		height:  height,
		scale:   1.0,
		styles:  makeDefaultStyles(),
		classes: makeDefaultClasses(),
		bufferPool: sync.Pool{
			New: func() interface{} {
				return new(strings.Builder)
			},
		},
	}
}

// SetViewBox sets the coordinate space
func (r *SVGRenderer) SetViewBox(minX, minY, width, height float64) {
	r.viewBox = ViewBox{
		MinX:   minX,
		MinY:   minY,
		Width:  width,
		Height: height,
	}
	r.scale = float64(r.width) / width
}

// RenderObject renders a single ArxObject to SVG
func (r *SVGRenderer) RenderObject(obj *engine.ArxObject, opts *RenderOptions) string {
	if opts == nil {
		opts = &RenderOptions{Precision: 2}
	}
	
	// Get buffer from pool
	buf := r.bufferPool.Get().(*strings.Builder)
	defer r.bufferPool.Put(buf)
	buf.Reset()
	
	// Render based on layer
	switch opts.Layer {
	case "elevation":
		r.renderElevation(buf, obj, opts)
	case "ceiling":
		r.renderCeiling(buf, obj, opts)
	default:
		r.renderFloorPlan(buf, obj, opts)
	}
	
	return buf.String()
}

// RenderBatch renders multiple objects efficiently
func (r *SVGRenderer) RenderBatch(objects []*engine.ArxObject, opts *RenderOptions) string {
	if opts == nil {
		opts = &RenderOptions{Precision: 2}
	}
	
	r.buffer.Reset()
	
	// Write SVG header
	r.writeSVGHeader()
	
	// Write styles
	r.writeStyles()
	
	// Write grid if requested
	if opts.ShowGrid {
		r.writeGrid(opts.GridSpacing)
	}
	
	// Group objects by type for efficient rendering
	grouped := r.groupByType(objects)
	
	// Render each group
	for objType, objs := range grouped {
		r.buffer.WriteString(fmt.Sprintf(`<g class="%s">`, r.classes[objType]))
		
		for _, obj := range objs {
			r.renderObjectToBuffer(obj, opts)
		}
		
		r.buffer.WriteString("</g>")
	}
	
	// Write SVG footer
	r.writeSVGFooter()
	
	result := r.buffer.String()
	
	// Optimize if requested
	if opts.Optimize {
		result = r.optimizeSVG(result)
	}
	
	return result
}

// Private rendering methods

func (r *SVGRenderer) renderFloorPlan(buf *strings.Builder, obj *engine.ArxObject, opts *RenderOptions) {
	// Convert coordinates to SVG space
	x := r.toSVGCoordX(float64(obj.X) / 1000.0)
	y := r.toSVGCoordY(float64(obj.Y) / 1000.0)
	width := r.toSVGScale(float64(obj.Length) / 1000.0)
	height := r.toSVGScale(float64(obj.Width) / 1000.0)
	
	class := r.classes[obj.Type]
	
	// Render based on object type
	switch obj.Type {
	case engine.ElectricalOutlet:
		r.renderOutlet(buf, x, y, class)
	case engine.ElectricalPanel:
		r.renderPanel(buf, x, y, width, height, class)
	case engine.StructuralColumn:
		r.renderColumn(buf, x, y, width, height, class)
	case engine.StructuralWall:
		r.renderWall(buf, x, y, width, height, obj.RotationZ, class)
	default:
		// Generic rectangle
		buf.WriteString(fmt.Sprintf(
			`<rect x="%.*f" y="%.*f" width="%.*f" height="%.*f" class="%s"/>`,
			opts.Precision, x-width/2,
			opts.Precision, y-height/2,
			opts.Precision, width,
			opts.Precision, height,
			class,
		))
	}
	
	// Add label if requested
	if opts.ShowLabels {
		buf.WriteString(fmt.Sprintf(
			`<text x="%.*f" y="%.*f" class="label">%d</text>`,
			opts.Precision, x,
			opts.Precision, y,
			obj.ID,
		))
	}
}

func (r *SVGRenderer) renderElevation(buf *strings.Builder, obj *engine.ArxObject, opts *RenderOptions) {
	// Elevation view (X-Z plane)
	x := r.toSVGCoordX(float64(obj.X) / 1000.0)
	z := r.toSVGCoordY(float64(obj.Z) / 1000.0) // Z becomes Y in elevation
	width := r.toSVGScale(float64(obj.Length) / 1000.0)
	height := r.toSVGScale(float64(obj.Height) / 1000.0)
	
	class := r.classes[obj.Type]
	
	buf.WriteString(fmt.Sprintf(
		`<rect x="%.*f" y="%.*f" width="%.*f" height="%.*f" class="%s"/>`,
		opts.Precision, x-width/2,
		opts.Precision, z-height/2,
		opts.Precision, width,
		opts.Precision, height,
		class,
	))
}

func (r *SVGRenderer) renderCeiling(buf *strings.Builder, obj *engine.ArxObject, opts *RenderOptions) {
	// Ceiling plan - only render ceiling-mounted objects
	if !r.isCeilingMounted(obj.Type) {
		return
	}
	
	r.renderFloorPlan(buf, obj, opts)
}

// Specific object renderers

func (r *SVGRenderer) renderOutlet(buf *strings.Builder, x, y float64, class string) {
	// Render electrical outlet symbol
	buf.WriteString(fmt.Sprintf(
		`<circle cx="%.2f" cy="%.2f" r="8" class="%s"/>`,
		x, y, class,
	))
	// Add outlet slots
	buf.WriteString(fmt.Sprintf(
		`<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="%s-slot"/>`,
		x-4, y, x+4, y, class,
	))
}

func (r *SVGRenderer) renderPanel(buf *strings.Builder, x, y, w, h float64, class string) {
	// Render electrical panel
	buf.WriteString(fmt.Sprintf(
		`<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" class="%s"/>`,
		x-w/2, y-h/2, w, h, class,
	))
	// Add panel lines
	for i := 0; i < 4; i++ {
		yOffset := y - h/2 + float64(i+1)*h/5
		buf.WriteString(fmt.Sprintf(
			`<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="%s-breaker"/>`,
			x-w/2+2, yOffset, x+w/2-2, yOffset, class,
		))
	}
}

func (r *SVGRenderer) renderColumn(buf *strings.Builder, x, y, w, h float64, class string) {
	// Render structural column (square with X)
	buf.WriteString(fmt.Sprintf(
		`<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" class="%s"/>`,
		x-w/2, y-h/2, w, h, class,
	))
	// Add X pattern
	buf.WriteString(fmt.Sprintf(
		`<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="%s-x"/>`,
		x-w/2, y-h/2, x+w/2, y+h/2, class,
	))
	buf.WriteString(fmt.Sprintf(
		`<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="%s-x"/>`,
		x-w/2, y+h/2, x+w/2, y-h/2, class,
	))
}

func (r *SVGRenderer) renderWall(buf *strings.Builder, x, y, w, h float64, rotation int16, class string) {
	// Render wall with rotation
	transform := ""
	if rotation != 0 {
		transform = fmt.Sprintf(` transform="rotate(%d %.2f %.2f)"`, rotation/10, x, y)
	}
	
	buf.WriteString(fmt.Sprintf(
		`<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" class="%s"%s/>`,
		x-w/2, y-h/2, w, h, class, transform,
	))
}

// Helper methods

func (r *SVGRenderer) writeSVGHeader() {
	r.buffer.WriteString(fmt.Sprintf(
		`<svg width="%d" height="%d" viewBox="%.2f %.2f %.2f %.2f" xmlns="http://www.w3.org/2000/svg">`,
		r.width, r.height,
		r.viewBox.MinX, r.viewBox.MinY,
		r.viewBox.Width, r.viewBox.Height,
	))
}

func (r *SVGRenderer) writeSVGFooter() {
	r.buffer.WriteString("</svg>")
}

func (r *SVGRenderer) writeStyles() {
	r.buffer.WriteString("<style>")
	for selector, style := range r.styles {
		r.buffer.WriteString(fmt.Sprintf("%s{%s}", selector, style))
	}
	r.buffer.WriteString("</style>")
}

func (r *SVGRenderer) writeGrid(spacing float64) {
	r.buffer.WriteString(`<g class="grid">`)
	
	// Vertical lines
	for x := r.viewBox.MinX; x <= r.viewBox.MinX+r.viewBox.Width; x += spacing {
		r.buffer.WriteString(fmt.Sprintf(
			`<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="grid-line"/>`,
			x, r.viewBox.MinY, x, r.viewBox.MinY+r.viewBox.Height,
		))
	}
	
	// Horizontal lines
	for y := r.viewBox.MinY; y <= r.viewBox.MinY+r.viewBox.Height; y += spacing {
		r.buffer.WriteString(fmt.Sprintf(
			`<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="grid-line"/>`,
			r.viewBox.MinX, y, r.viewBox.MinX+r.viewBox.Width, y,
		))
	}
	
	r.buffer.WriteString("</g>")
}

func (r *SVGRenderer) renderObjectToBuffer(obj *engine.ArxObject, opts *RenderOptions) {
	// Efficient single-pass rendering
	x := float64(obj.X) / 1000.0
	y := float64(obj.Y) / 1000.0
	
	switch obj.Type {
	case engine.ElectricalOutlet:
		r.buffer.WriteString(fmt.Sprintf(
			`<circle cx="%.*f" cy="%.*f" r="8"/>`,
			opts.Precision, x, opts.Precision, y,
		))
	default:
		w := float64(obj.Length) / 1000.0
		h := float64(obj.Width) / 1000.0
		r.buffer.WriteString(fmt.Sprintf(
			`<rect x="%.*f" y="%.*f" width="%.*f" height="%.*f"/>`,
			opts.Precision, x-w/2, opts.Precision, y-h/2,
			opts.Precision, w, opts.Precision, h,
		))
	}
}

func (r *SVGRenderer) groupByType(objects []*engine.ArxObject) map[engine.ArxObjectType][]*engine.ArxObject {
	grouped := make(map[engine.ArxObjectType][]*engine.ArxObject)
	for _, obj := range objects {
		grouped[obj.Type] = append(grouped[obj.Type], obj)
	}
	return grouped
}

func (r *SVGRenderer) toSVGCoordX(x float64) float64 {
	return x * r.scale
}

func (r *SVGRenderer) toSVGCoordY(y float64) float64 {
	return y * r.scale
}

func (r *SVGRenderer) toSVGScale(val float64) float64 {
	return val * r.scale
}

func (r *SVGRenderer) isCeilingMounted(objType engine.ArxObjectType) bool {
	switch objType {
	case engine.FireSprinkler, engine.SmokeDetector, engine.HVACDiffuser:
		return true
	default:
		return false
	}
}

func (r *SVGRenderer) optimizeSVG(svg string) string {
	// Simple SVG optimizations
	// - Remove redundant spaces
	// - Combine adjacent transforms
	// - Merge similar paths
	
	// This is a placeholder for more sophisticated optimization
	svg = strings.ReplaceAll(svg, "  ", " ")
	svg = strings.ReplaceAll(svg, "> <", "><")
	
	return svg
}

func makeDefaultStyles() map[string]string {
	return map[string]string{
		".electrical-outlet": "fill:none;stroke:#ff0000;stroke-width:2",
		".electrical-panel":  "fill:#ffcccc;stroke:#ff0000;stroke-width:2",
		".structural-column": "fill:#666666;stroke:#000000;stroke-width:3",
		".structural-wall":   "fill:#cccccc;stroke:#000000;stroke-width:2",
		".grid-line":         "stroke:#e0e0e0;stroke-width:0.5",
		".label":             "font-size:10px;text-anchor:middle",
	}
}

func makeDefaultClasses() map[engine.ArxObjectType]string {
	return map[engine.ArxObjectType]string{
		engine.ElectricalOutlet:  "electrical-outlet",
		engine.ElectricalPanel:   "electrical-panel",
		engine.StructuralColumn:  "structural-column",
		engine.StructuralWall:    "structural-wall",
		engine.StructuralBeam:    "structural-beam",
		engine.HVACDuct:          "hvac-duct",
		engine.PlumbingPipe:      "plumbing-pipe",
	}
}

// StreamRenderer provides streaming SVG generation
type StreamRenderer struct {
	*SVGRenderer
	writer io.Writer
}

// NewStreamRenderer creates a streaming renderer
func NewStreamRenderer(w io.Writer, width, height int) *StreamRenderer {
	return &StreamRenderer{
		SVGRenderer: NewSVGRenderer(width, height),
		writer:      w,
	}
}

// StreamObject writes an object directly to the stream
func (sr *StreamRenderer) StreamObject(obj *engine.ArxObject, opts *RenderOptions) error {
	svg := sr.RenderObject(obj, opts)
	_, err := sr.writer.Write([]byte(svg))
	return err
}

// StreamBatch streams multiple objects efficiently
func (sr *StreamRenderer) StreamBatch(objects []*engine.ArxObject, opts *RenderOptions) error {
	// Write header
	header := fmt.Sprintf(
		`<svg width="%d" height="%d" viewBox="%.2f %.2f %.2f %.2f" xmlns="http://www.w3.org/2000/svg">`,
		sr.width, sr.height,
		sr.viewBox.MinX, sr.viewBox.MinY,
		sr.viewBox.Width, sr.viewBox.Height,
	)
	if _, err := sr.writer.Write([]byte(header)); err != nil {
		return err
	}
	
	// Stream objects one by one
	for _, obj := range objects {
		svg := sr.RenderObject(obj, opts)
		if _, err := sr.writer.Write([]byte(svg)); err != nil {
			return err
		}
	}
	
	// Write footer
	if _, err := sr.writer.Write([]byte("</svg>")); err != nil {
		return err
	}
	
	return nil
}