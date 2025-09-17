package charts

import (
	"fmt"
	"math"
	"strings"

	"github.com/arx-os/arxos/internal/visualization/core"
)

// HeatmapData represents 2D matrix data for heatmaps
type HeatmapData struct {
	Matrix      [][]float64
	RowLabels   []string
	ColLabels   []string
	Title       string
	Unit        string
	Min         float64
	Max         float64
	ShowValues  bool
	ColorInvert bool // Invert color scheme (low=hot, high=cool)
}

// GetType implements DataSet interface
func (h *HeatmapData) GetType() string {
	return "heatmap"
}

// Validate implements DataSet interface
func (h *HeatmapData) Validate() error {
	if len(h.Matrix) == 0 {
		return fmt.Errorf("no data matrix provided")
	}

	// Check matrix is rectangular
	cols := len(h.Matrix[0])
	for i, row := range h.Matrix {
		if len(row) != cols {
			return fmt.Errorf("irregular matrix: row %d has %d columns, expected %d", i, len(row), cols)
		}
	}

	return nil
}

// Heatmap renders 2D data matrices
type Heatmap struct {
	renderer *core.TerminalRenderer
}

// NewHeatmap creates a new heatmap renderer
func NewHeatmap() *Heatmap {
	return &Heatmap{
		renderer: core.NewTerminalRenderer(),
	}
}

// Render renders a heatmap
func (h *Heatmap) Render(data *HeatmapData, options core.RenderOptions) string {
	if err := data.Validate(); err != nil {
		return fmt.Sprintf("Error: %v", err)
	}

	// Apply defaults
	if options.SymbolSet.IsEmpty() {
		if h.renderer.SupportsUnicode() {
			options.SymbolSet = core.UnicodeSymbols
		} else {
			options.SymbolSet = core.ASCIISymbols
		}
	}

	if options.ColorScheme.IsEmpty() {
		if h.renderer.SupportsColors() {
			options.ColorScheme = core.DefaultColorScheme
		} else {
			options.ColorScheme = core.MonochromeScheme
		}
	}

	// Find min/max if not provided
	min, max := data.Min, data.Max
	if min == 0 && max == 0 {
		min, max = findMatrixMinMax(data.Matrix)
	}

	// Handle edge case
	if min == max {
		max = min + 1
	}

	var output strings.Builder

	// Render title
	if data.Title != "" {
		output.WriteString(data.Title)
		if data.Unit != "" {
			output.WriteString(fmt.Sprintf(" (%s)", data.Unit))
		}
		output.WriteString("\n")
		output.WriteString(strings.Repeat("─", len(data.Title)+len(data.Unit)+3))
		output.WriteString("\n\n")
	}

	// Calculate cell dimensions
	maxLabelWidth := 0
	if len(data.RowLabels) > 0 {
		for _, label := range data.RowLabels {
			if len(label) > maxLabelWidth {
				maxLabelWidth = len(label)
			}
		}
	}

	cellWidth := 5 // Default cell width
	if data.ShowValues {
		cellWidth = 8 // Wider cells for values
	}

	// Render column headers
	if len(data.ColLabels) > 0 {
		// Spacing for row labels
		output.WriteString(strings.Repeat(" ", maxLabelWidth+2))

		for _, label := range data.ColLabels {
			output.WriteString(fmt.Sprintf("%-*s", cellWidth, truncateString(label, cellWidth-1)))
		}
		output.WriteString("\n")
	}

	// Render matrix rows
	for i, row := range data.Matrix {
		// Row label
		if i < len(data.RowLabels) {
			output.WriteString(fmt.Sprintf("%-*s  ", maxLabelWidth, data.RowLabels[i]))
		} else {
			output.WriteString(strings.Repeat(" ", maxLabelWidth+2))
		}

		// Render cells
		for _, value := range row {
			cell := h.renderCell(value, min, max, data.ShowValues, options.SymbolSet, data.ColorInvert)
			output.WriteString(fmt.Sprintf("%-*s", cellWidth, cell))
		}

		output.WriteString("\n")
	}

	// Render legend
	output.WriteString("\n")
	output.WriteString(h.renderLegend(min, max, options.SymbolSet))

	return output.String()
}

// renderCell renders a single heatmap cell
func (h *Heatmap) renderCell(value, min, max float64, showValue bool, symbols core.SymbolSet, invert bool) string {
	normalized := (value - min) / (max - min)
	if invert {
		normalized = 1 - normalized
	}

	if showValue {
		// Show actual value with background
		return fmt.Sprintf("%.1f", value)
	}

	// Use block characters for intensity
	blockChar := symbols.GetBlockChar(normalized)

	// Create cell with intensity
	cell := strings.Repeat(string(blockChar), 3)

	return cell
}

// renderLegend renders the heatmap legend
func (h *Heatmap) renderLegend(min, max float64, symbols core.SymbolSet) string {
	var legend strings.Builder

	legend.WriteString("Legend: ")

	// Show gradient
	steps := 8
	for i := 0; i < steps; i++ {
		normalized := float64(i) / float64(steps-1)
		legend.WriteRune(symbols.GetBlockChar(normalized))
	}

	legend.WriteString(fmt.Sprintf(" [%.1f - %.1f]", min, max))

	return legend.String()
}

// findMatrixMinMax finds min and max values in a 2D matrix
func findMatrixMinMax(matrix [][]float64) (min, max float64) {
	if len(matrix) == 0 || len(matrix[0]) == 0 {
		return 0, 0
	}

	min = matrix[0][0]
	max = matrix[0][0]

	for _, row := range matrix {
		for _, val := range row {
			if val < min {
				min = val
			}
			if val > max {
				max = val
			}
		}
	}

	return min, max
}

// truncateString truncates a string to fit within width
func truncateString(s string, width int) string {
	if len(s) <= width {
		return s
	}
	if width > 3 {
		return s[:width-3] + "..."
	}
	return s[:width]
}

// RenderFloorOccupancy renders a floor occupancy heatmap
func RenderFloorOccupancy(buildingID string, floors int, zones int) string {
	heatmap := NewHeatmap()

	// Generate sample occupancy data
	matrix := make([][]float64, floors)
	rowLabels := make([]string, floors)
	colLabels := make([]string, zones)

	for f := 0; f < floors; f++ {
		matrix[f] = make([]float64, zones)
		rowLabels[f] = fmt.Sprintf("Floor %d", f+1)

		for z := 0; z < zones; z++ {
			if f == 0 {
				colLabels[z] = fmt.Sprintf("Zone %c", 'A'+z)
			}
			// Sample occupancy percentage
			matrix[f][z] = math.Min(100, 20+float64(f*10)+float64(z*15)+math.Sin(float64(f*z))*20)
		}
	}

	data := &HeatmapData{
		Matrix:     matrix,
		RowLabels:  rowLabels,
		ColLabels:  colLabels,
		Title:      fmt.Sprintf("Occupancy Heatmap - %s", buildingID),
		Unit:       "%",
		Min:        0,
		Max:        100,
		ShowValues: false,
	}

	options := core.RenderOptions{
		Width:  80,
		Height: 20,
	}

	return heatmap.Render(data, options)
}

// RenderEnergyHeatmap renders energy usage heatmap by floor and time
func RenderEnergyHeatmap(buildingID string, hours int) string {
	heatmap := NewHeatmap()

	// Create matrix for floors (rows) x hours (columns)
	floors := 5
	matrix := make([][]float64, floors)
	rowLabels := make([]string, floors)
	colLabels := make([]string, hours)

	for f := 0; f < floors; f++ {
		matrix[f] = make([]float64, hours)
		rowLabels[f] = fmt.Sprintf("F%d", f+1)

		for h := 0; h < hours; h++ {
			if f == 0 {
				colLabels[h] = fmt.Sprintf("%02d", h)
			}
			// Simulate energy usage pattern
			baseUsage := 50.0
			timeEffect := math.Sin(float64(h)*math.Pi/12) * 30 // Peak at noon
			floorEffect := float64(floors-f) * 5                // Higher floors use less
			matrix[f][h] = baseUsage + timeEffect + floorEffect
		}
	}

	data := &HeatmapData{
		Matrix:     matrix,
		RowLabels:  rowLabels,
		ColLabels:  colLabels,
		Title:      fmt.Sprintf("Energy Usage by Floor/Hour - %s", buildingID),
		Unit:       "kW",
		ShowValues: false,
	}

	options := core.RenderOptions{
		Width:  80,
		Height: 20,
	}

	return heatmap.Render(data, options)
}

// RenderTemperatureMap renders a temperature distribution map
func RenderTemperatureMap(zones []string, sensors []string, readings [][]float64) string {
	heatmap := NewHeatmap()

	data := &HeatmapData{
		Matrix:      readings,
		RowLabels:   zones,
		ColLabels:   sensors,
		Title:       "Temperature Distribution",
		Unit:        "°F",
		ShowValues:  true,
		ColorInvert: false, // Red = hot, Blue = cool
	}

	options := core.RenderOptions{
		Width:  80,
		Height: 25,
	}

	return heatmap.Render(data, options)
}

// Example usage
func ExampleHeatmap() {
	heatmap := NewHeatmap()

	// Sample correlation matrix
	data := &HeatmapData{
		Title: "System Correlation Matrix",
		Matrix: [][]float64{
			{1.00, 0.85, 0.32, 0.15},
			{0.85, 1.00, 0.45, 0.22},
			{0.32, 0.45, 1.00, 0.67},
			{0.15, 0.22, 0.67, 1.00},
		},
		RowLabels:  []string{"HVAC", "Power", "Water", "Security"},
		ColLabels:  []string{"HVAC", "Power", "Water", "Security"},
		ShowValues: true,
		Min:        0,
		Max:        1,
	}

	options := core.RenderOptions{
		Width:  60,
		Height: 15,
	}

	fmt.Println(heatmap.Render(data, options))
}

// RenderAnomalyMap renders an anomaly detection heatmap
func RenderAnomalyMap(buildingID string, days int, hours int) string {
	heatmap := NewHeatmap()

	matrix := make([][]float64, days)
	rowLabels := make([]string, days)
	colLabels := make([]string, hours)

	daysOfWeek := []string{"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

	for d := 0; d < days; d++ {
		matrix[d] = make([]float64, hours)
		rowLabels[d] = daysOfWeek[d%7]

		for h := 0; h < hours; h++ {
			if d == 0 {
				colLabels[h] = fmt.Sprintf("%02d", h)
			}

			// Normal value
			normal := 0.0

			// Add anomalies
			if (d == 2 && h >= 14 && h <= 16) || // Wednesday afternoon
				(d == 4 && h >= 22) || // Friday night
				(d == 5 && h >= 8 && h <= 12) { // Saturday morning
				normal = 0.8 + math.Min(0.2, math.Abs(math.Sin(float64(h))))
			}

			matrix[d][h] = normal
		}
	}

	data := &HeatmapData{
		Matrix:      matrix,
		RowLabels:   rowLabels,
		ColLabels:   colLabels,
		Title:       fmt.Sprintf("Anomaly Detection - %s", buildingID),
		Unit:        "severity",
		ShowValues:  false,
		ColorInvert: false,
		Min:         0,
		Max:         1,
	}

	options := core.RenderOptions{
		Width:  80,
		Height: 20,
	}

	return heatmap.Render(data, options)
}