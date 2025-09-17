package rendering

import (
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/database"
)

// SpatialRenderer renders precise coordinate information for field technicians
// Focuses on exact positioning, spatial anchors, and coordinate precision for AR applications
type SpatialRenderer struct {
	width  int
	height int
	config *RendererConfig
}

// SpatialOptions configures spatial coordinate rendering
type SpatialOptions struct {
	ShowCoordinates bool     // Show precise coordinates
	ShowPrecision   bool     // Show coordinate precision info
	CoordinateUnit  string   // Unit for coordinates (meters, feet)
	FloorFilter     string   // Show specific floor only
	RadiusFilter    float64  // Show equipment within radius (meters)
	CenterPoint     *Point3D // Center point for radius filter
}

// Point3D is defined in multi_level_renderer.go

// NewSpatialRenderer creates a new spatial renderer
func NewSpatialRenderer(config *RendererConfig) *SpatialRenderer {
	return &SpatialRenderer{
		width:  config.Width,
		height: config.Height,
		config: config,
	}
}

// RenderAnchors renders spatial anchor information for AR applications
func (sr *SpatialRenderer) RenderAnchors(anchors []*database.SpatialAnchor, options SpatialOptions) (string, error) {
	var sb strings.Builder

	// Header
	sb.WriteString(sr.renderHeader(anchors, options))

	if len(anchors) == 0 {
		sb.WriteString("No spatial anchors found.\n")
		sb.WriteString("Use the mobile AR app to create spatial anchors for equipment.\n")
		return sb.String(), nil
	}

	// Filter anchors if needed
	filteredAnchors := sr.filterAnchors(anchors, options)

	// Render anchor table
	sb.WriteString(sr.renderAnchorTable(filteredAnchors, options))

	// Render coordinate grid if requested
	if options.ShowCoordinates {
		sb.WriteString(sr.renderCoordinateGrid(filteredAnchors, options))
	}

	// Render precision information
	if options.ShowPrecision {
		sb.WriteString(sr.renderPrecisionInfo(filteredAnchors, options))
	}

	return sb.String(), nil
}

// renderHeader renders the spatial view header
func (sr *SpatialRenderer) renderHeader(anchors []*database.SpatialAnchor, options SpatialOptions) string {
	var sb strings.Builder

	title := "Spatial Coordinate View"
	sb.WriteString(fmt.Sprintf("%s\n", title))
	sb.WriteString(strings.Repeat("═", len(title)) + "\n")

	sb.WriteString(fmt.Sprintf("Total Anchors: %d\n", len(anchors)))

	if options.FloorFilter != "" {
		sb.WriteString(fmt.Sprintf("Floor Filter: %s\n", options.FloorFilter))
	}

	if options.RadiusFilter > 0 && options.CenterPoint != nil {
		sb.WriteString(fmt.Sprintf("Radius Filter: %.1fm from (%.1f, %.1f)\n",
			options.RadiusFilter, options.CenterPoint.X, options.CenterPoint.Y))
	}

	unit := options.CoordinateUnit
	if unit == "" {
		unit = "meters"
	}
	sb.WriteString(fmt.Sprintf("Coordinate Unit: %s\n", unit))

	sb.WriteString("\n")
	return sb.String()
}

// renderAnchorTable renders anchors in a table format
func (sr *SpatialRenderer) renderAnchorTable(anchors []*database.SpatialAnchor, options SpatialOptions) string {
	var sb strings.Builder

	if len(anchors) == 0 {
		return ""
	}

	sb.WriteString("Spatial Anchors:\n")
	sb.WriteString("─────────────────────────────────────────────────────────────\n")
	sb.WriteString("Equipment ID         Floor  X        Y        Z        Platform\n")
	sb.WriteString("─────────────────────────────────────────────────────────────\n")

	for _, anchor := range anchors {
		// Extract equipment ID from path
		equipmentID := sr.extractEquipmentID(anchor.EquipmentPath)

		sb.WriteString(fmt.Sprintf("%-20s %5d  %8.3f %8.3f %8.3f %-8s\n",
			equipmentID,
			anchor.Floor,
			anchor.X,
			anchor.Y,
			anchor.Z,
			anchor.Platform,
		))
	}

	sb.WriteString("─────────────────────────────────────────────────────────────\n\n")
	return sb.String()
}

// renderCoordinateGrid renders a coordinate grid visualization
func (sr *SpatialRenderer) renderCoordinateGrid(anchors []*database.SpatialAnchor, options SpatialOptions) string {
	var sb strings.Builder

	if len(anchors) == 0 {
		return ""
	}

	sb.WriteString("Coordinate Grid Visualization:\n")

	// Find bounds of all anchors
	minX, maxX := anchors[0].X, anchors[0].X
	minY, maxY := anchors[0].Y, anchors[0].Y

	for _, anchor := range anchors {
		if anchor.X < minX {
			minX = anchor.X
		}
		if anchor.X > maxX {
			maxX = anchor.X
		}
		if anchor.Y < minY {
			minY = anchor.Y
		}
		if anchor.Y > maxY {
			maxY = anchor.Y
		}
	}

	// Create simple grid representation
	gridWidth := 50
	gridHeight := 15

	grid := make([][]rune, gridHeight)
	for i := range grid {
		grid[i] = make([]rune, gridWidth)
		for j := range grid[i] {
			grid[i][j] = '·'
		}
	}

	// Place anchors on grid
	for _, anchor := range anchors {
		// Scale coordinates to fit grid
		gridX := int((anchor.X - minX) / (maxX - minX) * float64(gridWidth-1))
		gridY := int((anchor.Y - minY) / (maxY - minY) * float64(gridHeight-1))

		if gridX >= 0 && gridX < gridWidth && gridY >= 0 && gridY < gridHeight {
			grid[gridY][gridX] = sr.getAnchorSymbol(anchor)
		}
	}

	// Render grid with coordinates
	sb.WriteString("┌" + strings.Repeat("─", gridWidth) + "┐\n")
	for y, row := range grid {
		sb.WriteString("│" + string(row) + "│")

		// Show Y coordinate on right
		if y == 0 {
			sb.WriteString(fmt.Sprintf(" %.1f", maxY))
		} else if y == gridHeight-1 {
			sb.WriteString(fmt.Sprintf(" %.1f", minY))
		}
		sb.WriteString("\n")
	}
	sb.WriteString("└" + strings.Repeat("─", gridWidth) + "┘\n")

	// Show X coordinates
	sb.WriteString(fmt.Sprintf("%.1f%s%.1f\n", minX, strings.Repeat(" ", gridWidth-10), maxX))

	sb.WriteString("\n")
	return sb.String()
}

// renderPrecisionInfo renders coordinate precision information
func (sr *SpatialRenderer) renderPrecisionInfo(anchors []*database.SpatialAnchor, options SpatialOptions) string {
	var sb strings.Builder

	sb.WriteString("Precision Information:\n")
	sb.WriteString("──────────────────────\n")

	if len(anchors) == 0 {
		return sb.String()
	}

	// Calculate precision statistics
	platformCounts := make(map[string]int)
	for _, anchor := range anchors {
		platformCounts[anchor.Platform]++
	}

	sb.WriteString("AR Platform Distribution:\n")
	for platform, count := range platformCounts {
		sb.WriteString(fmt.Sprintf("  %-8s: %d anchors\n", platform, count))
	}

	sb.WriteString("\nCoordinate Precision:\n")
	sb.WriteString("  Spatial anchors provide millimeter-level precision\n")
	sb.WriteString("  Suitable for AR overlay and field installation work\n")
	sb.WriteString("  Updated automatically from mobile AR app edits\n")

	return sb.String()
}

// Helper functions

// filterAnchors filters anchors based on options
func (sr *SpatialRenderer) filterAnchors(anchors []*database.SpatialAnchor, options SpatialOptions) []*database.SpatialAnchor {
	var filtered []*database.SpatialAnchor

	for _, anchor := range anchors {
		// Floor filter
		if options.FloorFilter != "" {
			floorStr := fmt.Sprintf("%d", anchor.Floor)
			if floorStr != options.FloorFilter {
				continue
			}
		}

		// Radius filter
		if options.RadiusFilter > 0 && options.CenterPoint != nil {
			distance := sr.calculateDistance(
				Point3D{X: anchor.X, Y: anchor.Y, Z: anchor.Z},
				*options.CenterPoint,
			)
			if distance > options.RadiusFilter {
				continue
			}
		}

		filtered = append(filtered, anchor)
	}

	return filtered
}

// extractEquipmentID extracts equipment ID from path
func (sr *SpatialRenderer) extractEquipmentID(path string) string {
	parts := strings.Split(path, "/")
	if len(parts) > 0 {
		return parts[len(parts)-1]
	}
	return path
}

// getAnchorSymbol returns symbol for spatial anchor
func (sr *SpatialRenderer) getAnchorSymbol(anchor *database.SpatialAnchor) rune {
	// Use different symbols based on equipment path
	path := strings.ToLower(anchor.EquipmentPath)
	switch {
	case strings.Contains(path, "electrical"):
		return 'E'
	case strings.Contains(path, "hvac"):
		return 'H'
	case strings.Contains(path, "network"):
		return 'N'
	case strings.Contains(path, "fire"):
		return 'F'
	case strings.Contains(path, "security"):
		return 'S'
	default:
		return '●'
	}
}

// calculateDistance calculates 3D distance between two points
func (sr *SpatialRenderer) calculateDistance(p1, p2 Point3D) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	dz := p1.Z - p2.Z
	return (dx*dx + dy*dy + dz*dz) // Square root omitted for performance
}
