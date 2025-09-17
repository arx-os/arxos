package rendering

import (
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/bim"
)

// SchematicRenderer renders building schematics for building managers
// Focuses on general layout, equipment locations, and status overview
type SchematicRenderer struct {
	width  int
	height int
	config *RendererConfig
}

// SchematicOptions configures schematic rendering
type SchematicOptions struct {
	ShowGrid          bool   // Show coordinate grid
	ShowLegend        bool   // Show symbol legend
	ShowStatusSummary bool   // Show equipment status counts
	FloorFilter       string // Show specific floor only
	StatusFilter      string // Filter by equipment status
}

// NewSchematicRenderer creates a new schematic renderer
func NewSchematicRenderer(config *RendererConfig) *SchematicRenderer {
	return &SchematicRenderer{
		width:  config.Width,
		height: config.Height,
		config: config,
	}
}

// RenderBuilding renders a building schematic from BIM data
func (sr *SchematicRenderer) RenderBuilding(building *bim.Building, options SchematicOptions) (string, error) {
	var sb strings.Builder

	// Header
	sb.WriteString(sr.renderHeader(building))

	// Building overview
	if len(building.Floors) == 0 {
		sb.WriteString(sr.renderEmptyBuilding())
		return sb.String(), nil
	}

	// Render floors
	for _, floor := range building.Floors {
		// Skip if floor filter is set and doesn't match
		if options.FloorFilter != "" && fmt.Sprintf("%d", floor.Level) != options.FloorFilter {
			continue
		}

		sb.WriteString(sr.renderFloor(floor, options))
	}

	// Footer with legend and summary
	if options.ShowLegend {
		sb.WriteString(sr.renderLegend())
	}

	if options.ShowStatusSummary {
		sb.WriteString(sr.renderStatusSummary(building, options))
	}

	return sb.String(), nil
}

// renderHeader renders the building header information
func (sr *SchematicRenderer) renderHeader(building *bim.Building) string {
	var sb strings.Builder

	title := building.Name
	if title == "" {
		title = "ArxOS Building"
	}

	sb.WriteString(fmt.Sprintf("%s\n", title))
	sb.WriteString(strings.Repeat("═", len(title)) + "\n")

	if building.FileVersion != "" {
		sb.WriteString(fmt.Sprintf("Version: %s\n", building.FileVersion))
	}

	if !building.Generated.IsZero() {
		sb.WriteString(fmt.Sprintf("Generated: %s\n", building.Generated.Format("2006-01-02 15:04")))
	}

	sb.WriteString("\n")
	return sb.String()
}

// renderFloor renders a single floor schematic
func (sr *SchematicRenderer) renderFloor(floor bim.Floor, options SchematicOptions) string {
	var sb strings.Builder

	// Floor header
	floorTitle := fmt.Sprintf("Floor %d", floor.Level)
	if floor.Name != "" {
		floorTitle += fmt.Sprintf(" - %s", floor.Name)
	}

	sb.WriteString(fmt.Sprintf("\n%s\n", floorTitle))
	sb.WriteString(strings.Repeat("─", len(floorTitle)) + "\n")

	// Floor dimensions if available
	if floor.Dimensions.Width > 0 && floor.Dimensions.Height > 0 {
		sb.WriteString(fmt.Sprintf("Dimensions: %.1f × %.1f %s\n",
			floor.Dimensions.Width, floor.Dimensions.Height, "units"))
	}

	// Equipment count
	equipmentCount := len(floor.Equipment)
	if equipmentCount > 0 {
		sb.WriteString(fmt.Sprintf("Equipment: %d items\n", equipmentCount))

		// Equipment grid (simplified ASCII layout)
		sb.WriteString(sr.renderEquipmentGrid(floor.Equipment, options))
	} else {
		sb.WriteString("No equipment on this floor\n")
	}

	return sb.String()
}

// renderEquipmentGrid renders equipment in a simple grid layout
func (sr *SchematicRenderer) renderEquipmentGrid(equipment []bim.Equipment, options SchematicOptions) string {
	var sb strings.Builder

	if len(equipment) == 0 {
		return ""
	}

	sb.WriteString("\nEquipment Layout:\n")

	// Create a simple grid representation
	gridWidth := 60
	gridHeight := 12

	// Initialize grid
	grid := make([][]rune, gridHeight)
	for i := range grid {
		grid[i] = make([]rune, gridWidth)
		for j := range grid[i] {
			grid[i][j] = '·' // Floor space
		}
	}

	// Place equipment on grid
	for _, eq := range equipment {
		// Skip if status filter is set and doesn't match
		if options.StatusFilter != "" && string(eq.Status) != strings.ToUpper(options.StatusFilter) {
			continue
		}

		// Convert equipment location to grid coordinates
		gridX := int(eq.Location.X*0.3) % gridWidth // Scale down to fit
		gridY := int(eq.Location.Y*0.3) % gridHeight

		if gridX >= 0 && gridX < gridWidth && gridY >= 0 && gridY < gridHeight {
			grid[gridY][gridX] = sr.getEquipmentSymbol(eq)
		}
	}

	// Add border
	sb.WriteString("┌" + strings.Repeat("─", gridWidth) + "┐\n")

	// Render grid
	for _, row := range grid {
		sb.WriteString("│" + string(row) + "│\n")
	}

	sb.WriteString("└" + strings.Repeat("─", gridWidth) + "┘\n")

	return sb.String()
}

// getEquipmentSymbol returns ASCII symbol for equipment type
func (sr *SchematicRenderer) getEquipmentSymbol(eq bim.Equipment) rune {
	switch {
	case strings.Contains(strings.ToLower(eq.Type), "electrical"):
		return 'E'
	case strings.Contains(strings.ToLower(eq.Type), "hvac"):
		return 'H'
	case strings.Contains(strings.ToLower(eq.Type), "network"):
		return 'N'
	case strings.Contains(strings.ToLower(eq.Type), "plumbing"):
		return 'P'
	case strings.Contains(strings.ToLower(eq.Type), "fire"):
		return 'F'
	case strings.Contains(strings.ToLower(eq.Type), "security"):
		return 'S'
	default:
		return '?'
	}
}

// renderLegend renders the symbol legend
func (sr *SchematicRenderer) renderLegend() string {
	var sb strings.Builder

	sb.WriteString("\nLegend:\n")
	sb.WriteString("───────\n")
	sb.WriteString("E = Electrical    H = HVAC         N = Network\n")
	sb.WriteString("P = Plumbing      F = Fire Safety  S = Security\n")
	sb.WriteString("? = Other         · = Floor Space\n")

	return sb.String()
}

// renderStatusSummary renders equipment status summary
func (sr *SchematicRenderer) renderStatusSummary(building *bim.Building, options SchematicOptions) string {
	var sb strings.Builder

	// Count equipment by status
	statusCounts := make(map[bim.EquipmentStatus]int)
	totalEquipment := 0

	for _, floor := range building.Floors {
		for _, eq := range floor.Equipment {
			statusCounts[eq.Status]++
			totalEquipment++
		}
	}

	if totalEquipment == 0 {
		return ""
	}

	sb.WriteString("\nEquipment Status Summary:\n")
	sb.WriteString("─────────────────────────\n")

	// Show status counts
	for status, count := range statusCounts {
		percentage := float64(count) / float64(totalEquipment) * 100
		sb.WriteString(fmt.Sprintf("%-12s: %3d (%4.1f%%)\n", status, count, percentage))
	}

	sb.WriteString(fmt.Sprintf("%-12s: %3d\n", "Total", totalEquipment))

	return sb.String()
}

// renderEmptyBuilding renders message for empty building
func (sr *SchematicRenderer) renderEmptyBuilding() string {
	return "\nNo floors defined in this building.\n" +
		"Use 'arx import' to add building data from PDF, IFC, or other formats.\n"
}
