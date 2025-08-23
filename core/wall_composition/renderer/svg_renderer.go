package renderer

import (
	"fmt"
	"math"
	"strings"

	"github.com/arxos/arxos/core/wall_composition/spatial"
	"github.com/arxos/arxos/core/wall_composition/types"
)

// SVGRenderer converts wall structures into SVG output
type SVGRenderer struct {
	config RenderConfig
}

// RenderConfig holds configuration for SVG rendering
type RenderConfig struct {
	Width            float64           // SVG width in mm
	Height           float64           // SVG height in mm
	Scale            float64           // Scale factor (mm per SVG unit)
	StrokeWidth      float64           // Default stroke width
	ConfidenceColors map[string]string // Color mapping for confidence levels
	ShowConfidence   bool              // Whether to show confidence indicators
	ShowDimensions   bool              // Whether to show wall dimensions
	ShowMetadata     bool              // Whether to show wall metadata
}

// DefaultRenderConfig returns sensible default configuration values
func DefaultRenderConfig() RenderConfig {
	return RenderConfig{
		Width:       297.0, // A4 width in mm
		Height:      210.0, // A4 height in mm
		Scale:       1.0,   // 1:1 scale (1 SVG unit = 1mm)
		StrokeWidth: 2.0,   // 2mm stroke width
		ConfidenceColors: map[string]string{
			"high":   "#00FF00", // Green for high confidence
			"medium": "#FFFF00", // Yellow for medium confidence
			"low":    "#FF0000", // Red for low confidence
		},
		ShowConfidence: true,
		ShowDimensions: true,
		ShowMetadata:   false,
	}
}

// NewSVGRenderer creates a new SVG renderer with the given configuration
func NewSVGRenderer(config RenderConfig) *SVGRenderer {
	return &SVGRenderer{
		config: config,
	}
}

// RenderWallStructures renders a list of wall structures to SVG
func (r *SVGRenderer) RenderWallStructures(structures []*types.WallStructure) (string, error) {
	if len(structures) == 0 {
		return r.renderEmptySVG(), nil
	}

	// Calculate bounding box for all structures
	bounds := r.calculateBoundingBox(structures)

	// Adjust SVG dimensions if needed
	svgWidth := math.Max(float64(bounds.Width()), r.config.Width)
	svgHeight := math.Max(float64(bounds.Height()), r.config.Height)

	// Build SVG content
	var svgBuilder strings.Builder

	// SVG header
	svgBuilder.WriteString(fmt.Sprintf(`<svg width="%.2fmm" height="%.2fmm" viewBox="0 0 %.2f %.2f" xmlns="http://www.w3.org/2000/svg">`,
		svgWidth, svgHeight, svgWidth, svgHeight))
	svgBuilder.WriteString("\n")

	// SVG definitions (styles, patterns, etc.)
	r.renderSVGDefinitions(&svgBuilder)

	// Render each wall structure
	for i, structure := range structures {
		structureSVG := r.renderWallStructure(structure, i)
		svgBuilder.WriteString(structureSVG)
		svgBuilder.WriteString("\n")
	}

	// Render confidence indicators if enabled
	if r.config.ShowConfidence {
		r.renderConfidenceIndicators(&svgBuilder, structures)
	}

	// Render dimensions if enabled
	if r.config.ShowDimensions {
		r.renderDimensionLabels(&svgBuilder, structures)
	}

	// SVG footer
	svgBuilder.WriteString("</svg>")

	return svgBuilder.String(), nil
}

// renderEmptySVG renders an empty SVG with just the header
func (r *SVGRenderer) renderEmptySVG() string {
	return fmt.Sprintf(`<svg width="%.2fmm" height="%.2fmm" viewBox="0 0 %.2f %.2f" xmlns="http://www.w3.org/2000/svg">
  <text x="50%%" y="50%%" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16">No wall structures to render</text>
</svg>`, r.config.Width, r.config.Height, r.config.Width, r.config.Height)
}

// renderSVGDefinitions renders SVG definitions section
func (r *SVGRenderer) renderSVGDefinitions(svgBuilder *strings.Builder) {
	svgBuilder.WriteString("  <defs>\n")

	// Wall stroke styles
	svgBuilder.WriteString("    <style>\n")
	svgBuilder.WriteString("      .wall-stroke { stroke-width: 2; stroke-linecap: round; }\n")
	svgBuilder.WriteString("      .confidence-high { stroke: #00FF00; }\n")
	svgBuilder.WriteString("      .confidence-medium { stroke: #FFFF00; }\n")
	svgBuilder.WriteString("      .confidence-low { stroke: #FF0000; }\n")
	svgBuilder.WriteString("      .dimension-text { font-family: Arial; font-size: 12; fill: #333; }\n")
	svgBuilder.WriteString("      .metadata-text { font-family: Arial; font-size: 10; fill: #666; }\n")
	svgBuilder.WriteString("    </style>\n")

	// Arrow marker for dimensions
	svgBuilder.WriteString("    <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"9\" refY=\"3.5\" orient=\"auto\">\n")
	svgBuilder.WriteString("      <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#333\" />\n")
	svgBuilder.WriteString("    </marker>\n")

	svgBuilder.WriteString("  </defs>\n")
}

// renderWallStructure renders a single wall structure
func (r *SVGRenderer) renderWallStructure(structure *types.WallStructure, index int) string {
	var svgBuilder strings.Builder

	// Structure group
	svgBuilder.WriteString(fmt.Sprintf("  <g id=\"wall-structure-%d\" class=\"wall-structure\">\n", index))

	// Render each segment
	for i, segment := range structure.Segments {
		segmentSVG := r.renderWallSegment(&segment, i)
		svgBuilder.WriteString(segmentSVG)
		svgBuilder.WriteString("\n")
	}

	// Render structure metadata if enabled
	if r.config.ShowMetadata {
		metadataSVG := r.renderStructureMetadata(structure, index)
		svgBuilder.WriteString(metadataSVG)
		svgBuilder.WriteString("\n")
	}

	svgBuilder.WriteString("  </g>")

	return svgBuilder.String()
}

// renderWallSegment renders a single wall segment
func (r *SVGRenderer) renderWallSegment(segment *types.WallSegment, index int) string {
	// Convert coordinates to SVG units
	startX := float64(segment.StartPoint.X) * r.config.Scale
	startY := float64(segment.StartPoint.Y) * r.config.Scale
	endX := float64(segment.EndPoint.X) * r.config.Scale
	endY := float64(segment.EndPoint.Y) * r.config.Scale

	// Determine confidence class
	confidenceClass := r.getConfidenceClass(float64(segment.Confidence))

	// Render the wall line
	svg := fmt.Sprintf("    <line x1=\"%.2f\" y1=\"%.2f\" x2=\"%.2f\" y2=\"%.2f\" class=\"wall-stroke %s\" />",
		startX, startY, endX, endY, confidenceClass)

	// Render thickness representation (perpendicular lines at endpoints)
	if segment.Thickness > 0 {
		thicknessSVG := r.renderThicknessRepresentation(segment)
		svg += "\n" + thicknessSVG
	}

	return svg
}

// renderThicknessRepresentation renders wall thickness as perpendicular lines
func (r *SVGRenderer) renderThicknessRepresentation(segment *types.WallSegment) string {
	// Calculate perpendicular vector
	dx := float64(segment.EndPoint.X - segment.StartPoint.X)
	dy := float64(segment.EndPoint.Y - segment.StartPoint.Y)

	// Normalize and rotate 90 degrees
	length := math.Sqrt(dx*dx + dy*dy)
	if length == 0 {
		return ""
	}

	// Perpendicular vector (rotated 90 degrees)
	perpX := -dy / length
	perpY := dx / length

	// Scale by half thickness
	halfThickness := segment.Thickness / 2.0
	perpX *= halfThickness * r.config.Scale
	perpY *= halfThickness * r.config.Scale

	// Start point perpendicular lines
	startX1 := float64(segment.StartPoint.X)*r.config.Scale - perpX
	startY1 := float64(segment.StartPoint.Y)*r.config.Scale - perpY
	startX2 := float64(segment.StartPoint.X)*r.config.Scale + perpX
	startY2 := float64(segment.StartPoint.Y)*r.config.Scale + perpY

	// End point perpendicular lines
	endX1 := float64(segment.EndPoint.X)*r.config.Scale - perpX
	endY1 := float64(segment.EndPoint.Y)*r.config.Scale - perpY
	endX2 := float64(segment.EndPoint.X)*r.config.Scale + perpX
	endY2 := float64(segment.EndPoint.Y)*r.config.Scale + perpY

	// Render thickness lines
	svg := fmt.Sprintf("    <line x1=\"%.2f\" y1=\"%.2f\" x2=\"%.2f\" y2=\"%.2f\" class=\"wall-stroke\" stroke-width=\"1\" />",
		startX1, startY1, startX2, startY2)
	svg += fmt.Sprintf("\n    <line x1=\"%.2f\" y1=\"%.2f\" x2=\"%.2f\" y2=\"%.2f\" class=\"wall-stroke\" stroke-width=\"1\" />",
		endX1, endY1, endX2, endY2)

	return svg
}

// renderStructureMetadata renders metadata for a wall structure
func (r *SVGRenderer) renderStructureMetadata(structure *types.WallStructure, index int) string {
	// Calculate center point for metadata placement (placeholder implementation)
	centerX := 100.0 * r.config.Scale // Placeholder center X
	centerY := 100.0 * r.config.Scale // Placeholder center Y

	var svgBuilder strings.Builder

	// Structure name
	svgBuilder.WriteString(fmt.Sprintf("    <text x=\"%.2f\" y=\"%.2f\" class=\"metadata-text\" text-anchor=\"middle\">%s</text>",
		centerX, centerY-20, structure.Metadata.BuildingID))
	svgBuilder.WriteString("\n")

	// Structure description
	svgBuilder.WriteString(fmt.Sprintf("    <text x=\"%.2f\" y=\"%.2f\" class=\"metadata-text\" text-anchor=\"middle\">%s</text>",
		centerX, centerY-5, structure.Metadata.Notes))
	svgBuilder.WriteString("\n")

	// Confidence score
	svgBuilder.WriteString(fmt.Sprintf("    <text x=\"%.2f\" y=\"%.2f\" class=\"metadata-text\" text-anchor=\"middle\">Confidence: %.1f%%</text>",
		centerX, centerY+10, structure.Confidence*100))

	return svgBuilder.String()
}

// renderConfidenceIndicators renders confidence level indicators
func (r *SVGRenderer) renderConfidenceIndicators(svgBuilder *strings.Builder, structures []*types.WallStructure) {
	svgBuilder.WriteString("  <!-- Confidence Indicators -->\n")

	// Legend
	svgBuilder.WriteString("  <g id=\"confidence-legend\" transform=\"translate(20, 20)\">\n")
	svgBuilder.WriteString("    <text x=\"0\" y=\"0\" class=\"dimension-text\" font-weight=\"bold\">Confidence Levels:</text>\n")
	svgBuilder.WriteString("    <line x1=\"0\" y1=\"15\" x2=\"20\" y2=\"15\" class=\"confidence-high\" stroke-width=\"3\" />\n")
	svgBuilder.WriteString("    <text x=\"25\" y=\"20\" class=\"dimension-text\">High (≥80%)</text>\n")
	svgBuilder.WriteString("    <line x1=\"0\" y1=\"35\" x2=\"20\" y2=\"35\" class=\"confidence-medium\" stroke-width=\"3\" />\n")
	svgBuilder.WriteString("    <text x=\"25\" y=\"40\" class=\"dimension-text\">Medium (60-80%)</text>\n")
	svgBuilder.WriteString("    <line x1=\"0\" y1=\"55\" x2=\"20\" y2=\"55\" class=\"confidence-low\" stroke-width=\"3\" />\n")
	svgBuilder.WriteString("    <text x=\"25\" y=\"60\" class=\"dimension-text\">Low (&lt;60%)</text>\n")
	svgBuilder.WriteString("  </g>\n")
}

// renderDimensionLabels renders dimension labels for walls
func (r *SVGRenderer) renderDimensionLabels(svgBuilder *strings.Builder, structures []*types.WallStructure) {
	svgBuilder.WriteString("  <!-- Dimension Labels -->\n")

	for _, structure := range structures {
		for _, segment := range structure.Segments {
			dimensionSVG := r.renderSegmentDimension(&segment)
			svgBuilder.WriteString(dimensionSVG)
			svgBuilder.WriteString("\n")
		}
	}
}

// renderSegmentDimension renders dimension label for a wall segment
func (r *SVGRenderer) renderSegmentDimension(segment *types.WallSegment) string {
	// Calculate center point of segment
	centerX := (float64(segment.StartPoint.X) + float64(segment.EndPoint.X)) / 2.0 * r.config.Scale
	centerY := (float64(segment.StartPoint.Y) + float64(segment.EndPoint.Y)) / 2.0 * r.config.Scale

	// Calculate segment length (DistanceTo already returns the result in millimeters)
	lengthMM := segment.StartPoint.DistanceTo(segment.EndPoint)

	// Format length with appropriate units
	var lengthText string
	if lengthMM >= 1000 {
		lengthText = fmt.Sprintf("%.1fm", lengthMM/1000.0)
	} else {
		lengthText = fmt.Sprintf("%.1fmm", lengthMM)
	}

	// Render dimension text
	return fmt.Sprintf("    <text x=\"%.2f\" y=\"%.2f\" class=\"dimension-text\" text-anchor=\"middle\">%s</text>",
		centerX, centerY-10, lengthText)
}

// getConfidenceClass returns the CSS class for a confidence level
func (r *SVGRenderer) getConfidenceClass(confidence float64) string {
	if confidence >= 0.8 {
		return "confidence-high"
	} else if confidence >= 0.6 {
		return "confidence-medium"
	} else {
		return "confidence-low"
	}
}

// calculateBoundingBox calculates the bounding box for all wall structures
func (r *SVGRenderer) calculateBoundingBox(structures []*types.WallStructure) spatial.BoundingBox {
	if len(structures) == 0 {
		// Return default bounding box in nanometers (convert mm to nm)
		widthNM := int64(r.config.Width * 1e6)
		heightNM := int64(r.config.Height * 1e6)
		return spatial.NewBoundingBox(0, 0, widthNM, heightNM)
	}

	// Create a simple bounding box based on the first structure's segments
	// This is a placeholder implementation since WallStructure doesn't have BoundingBox method
	var minX, minY, maxX, maxY int64
	firstStructure := structures[0]

	if len(firstStructure.Segments) > 0 {
		// Initialize with first segment
		segment := firstStructure.Segments[0]
		minX = segment.StartPoint.X
		minY = segment.StartPoint.Y
		maxX = segment.StartPoint.X
		maxY = segment.StartPoint.Y

		// Expand to include all segments
		for _, seg := range firstStructure.Segments {
			if seg.StartPoint.X < minX {
				minX = seg.StartPoint.X
			}
			if seg.StartPoint.Y < minY {
				minY = seg.StartPoint.Y
			}
			if seg.EndPoint.X > maxX {
				maxX = seg.EndPoint.X
			}
			if seg.EndPoint.Y > maxY {
				maxY = seg.EndPoint.Y
			}
		}
	}

	// Expand to include other structures
	for _, structure := range structures[1:] {
		for _, seg := range structure.Segments {
			if seg.StartPoint.X < minX {
				minX = seg.StartPoint.X
			}
			if seg.StartPoint.Y < minY {
				minY = seg.StartPoint.Y
			}
			if seg.EndPoint.X > maxX {
				maxX = seg.EndPoint.X
			}
			if seg.EndPoint.Y > maxY {
				maxY = seg.EndPoint.Y
			}
		}
	}

	return spatial.NewBoundingBox(minX, minY, maxX, maxY)
}

// GetRenderStats returns statistics about the rendering process
func (r *SVGRenderer) GetRenderStats() RenderStats {
	return RenderStats{
		StructuresRendered: 0, // Placeholder
		SegmentsRendered:   0, // Placeholder
		SVGSize:            0, // Placeholder
	}
}

// RenderStats holds statistics about the rendering process
type RenderStats struct {
	StructuresRendered int
	SegmentsRendered   int
	SVGSize            int
}
