package charts

import (
	"fmt"
	"sort"
	"strings"

	"github.com/arx-os/arxos/internal/visualization/core"
)

// BarData represents data for a bar chart
type BarData struct {
	Items []BarItem
	Title string
	Unit  string
}

// BarItem represents a single bar in the chart
type BarItem struct {
	Label string
	Value float64
	Color core.Color
}

// GetType implements DataSet interface
func (b *BarData) GetType() string {
	return "bar"
}

// Validate implements DataSet interface
func (b *BarData) Validate() error {
	if len(b.Items) == 0 {
		return fmt.Errorf("no data items provided")
	}
	return nil
}

// BarChart renders horizontal bar charts
type BarChart struct {
	renderer *core.TerminalRenderer
}

// NewBarChart creates a new bar chart
func NewBarChart() *BarChart {
	return &BarChart{
		renderer: core.NewTerminalRenderer(),
	}
}

// Render renders a bar chart to the terminal
func (bc *BarChart) Render(data *BarData, options core.RenderOptions) string {
	if err := data.Validate(); err != nil {
		return fmt.Sprintf("Error: %v", err)
	}

	// Get terminal dimensions if not specified
	if options.Width == 0 || options.Height == 0 {
		options.Width, options.Height = bc.renderer.GetDimensions()
	}

	// Apply defaults
	if options.SymbolSet.IsEmpty() {
		if bc.renderer.SupportsUnicode() {
			options.SymbolSet = core.UnicodeSymbols
		} else {
			options.SymbolSet = core.ASCIISymbols
		}
	}

	if options.ColorScheme.IsEmpty() {
		if bc.renderer.SupportsColors() {
			options.ColorScheme = core.DefaultColorScheme
		} else {
			options.ColorScheme = core.MonochromeScheme
		}
	}

	// Create canvas
	canvas := core.NewCanvas(options.Width, options.Height)

	// Find maximum value for scaling
	maxValue := 0.0
	for _, item := range data.Items {
		if item.Value > maxValue {
			maxValue = item.Value
		}
	}

	// Calculate dimensions
	labelWidth := bc.calculateLabelWidth(data.Items)
	valueWidth := 10                                        // Space for value display
	barWidth := options.Width - labelWidth - valueWidth - 4 // Margins and spacing

	if barWidth < 10 {
		barWidth = 10 // Minimum bar width
	}

	// Render title if provided
	currentY := 0
	if data.Title != "" {
		titleX := (options.Width - len(data.Title)) / 2
		if titleX < 0 {
			titleX = 0
		}
		canvas.DrawText(titleX, currentY, data.Title, options.ColorScheme.Primary, core.NoColor)
		currentY += 2
	}

	// Render each bar
	for i, item := range data.Items {
		if currentY >= options.Height {
			break
		}

		// Draw label
		label := bc.formatLabel(item.Label, labelWidth)
		canvas.DrawText(0, currentY, label, options.ColorScheme.Text, core.NoColor)

		// Draw bar
		barX := labelWidth + 2
		fillRatio := 0.0
		if maxValue > 0 {
			fillRatio = item.Value / maxValue
		}

		// Get color for this bar
		barColor := item.Color
		if barColor == core.NoColor {
			barColor = options.ColorScheme.GetBarColor(i)
		}

		canvas.DrawHorizontalBar(barX, currentY, barWidth, fillRatio, options.SymbolSet, barColor, core.NoColor)

		// Draw value
		valueStr := bc.formatValue(item.Value, data.Unit, options.ShowValues)
		valueX := barX + barWidth + 1
		canvas.DrawText(valueX, currentY, valueStr, options.ColorScheme.Text, core.NoColor)

		currentY++
	}

	return canvas.ToString()
}

// RenderSimple renders a simple bar chart as a string
func (bc *BarChart) RenderSimple(data map[string]float64, width int) string {
	var items []BarItem
	for label, value := range data {
		items = append(items, BarItem{
			Label: label,
			Value: value,
		})
	}

	// Sort by value (descending)
	sort.Slice(items, func(i, j int) bool {
		return items[i].Value > items[j].Value
	})

	barData := &BarData{
		Items: items,
	}

	options := core.RenderOptions{
		Width:      width,
		ShowValues: true,
	}

	return bc.Render(barData, options)
}

// calculateLabelWidth calculates the maximum label width
func (bc *BarChart) calculateLabelWidth(items []BarItem) int {
	maxWidth := 0
	for _, item := range items {
		if len(item.Label) > maxWidth {
			maxWidth = len(item.Label)
		}
	}

	// Cap at reasonable maximum
	if maxWidth > 20 {
		maxWidth = 20
	}

	return maxWidth
}

// formatLabel formats a label to fit within the specified width
func (bc *BarChart) formatLabel(label string, width int) string {
	if len(label) > width {
		if width > 3 {
			return label[:width-3] + "..."
		}
		return label[:width]
	}

	// Pad with spaces
	return fmt.Sprintf("%-*s", width, label)
}

// formatValue formats a numeric value with optional unit
func (bc *BarChart) formatValue(value float64, unit string, show bool) string {
	if !show {
		return ""
	}

	valueStr := ""
	if value >= 1000000 {
		valueStr = fmt.Sprintf("%.1fM", value/1000000)
	} else if value >= 1000 {
		valueStr = fmt.Sprintf("%.1fK", value/1000)
	} else if value == float64(int(value)) {
		valueStr = fmt.Sprintf("%.0f", value)
	} else {
		valueStr = fmt.Sprintf("%.1f", value)
	}

	if unit != "" {
		valueStr += " " + unit
	}

	return valueStr
}

// RenderEquipmentStatus renders equipment status as a bar chart
func RenderEquipmentStatus(buildingID string, floors map[string][]string) string {
	chart := NewBarChart()

	var items []BarItem
	for floor, equipment := range floors {
		operational := 0
		for _, status := range equipment {
			if status == "operational" {
				operational++
			}
		}

		percentage := float64(operational) / float64(len(equipment)) * 100
		items = append(items, BarItem{
			Label: fmt.Sprintf("Floor %s", floor),
			Value: percentage,
		})
	}

	// Sort by floor number
	sort.Slice(items, func(i, j int) bool {
		return items[i].Label < items[j].Label
	})

	data := &BarData{
		Title: fmt.Sprintf("Equipment Status - Building %s", buildingID),
		Items: items,
		Unit:  "%",
	}

	options := core.RenderOptions{
		Width:      80,
		Height:     20,
		ShowValues: true,
	}

	return chart.Render(data, options)
}

// RenderEnergyUsage renders energy usage as a bar chart
func RenderEnergyUsage(data map[string]float64) string {
	chart := NewBarChart()

	var items []BarItem
	for day, kwh := range data {
		items = append(items, BarItem{
			Label: day,
			Value: kwh,
		})
	}

	barData := &BarData{
		Title: "Energy Usage - Past 7 Days",
		Items: items,
		Unit:  "kWh",
	}

	options := core.RenderOptions{
		Width:      80,
		Height:     15,
		ShowValues: true,
	}

	return chart.Render(barData, options)
}

// Example usage function
func ExampleBarChart() {
	chart := NewBarChart()

	// Sample data
	data := &BarData{
		Title: "Building Energy Consumption",
		Unit:  "kWh",
		Items: []BarItem{
			{Label: "Monday", Value: 450},
			{Label: "Tuesday", Value: 380},
			{Label: "Wednesday", Value: 420},
			{Label: "Thursday", Value: 410},
			{Label: "Friday", Value: 290},
			{Label: "Saturday", Value: 150},
			{Label: "Sunday", Value: 140},
		},
	}

	options := core.RenderOptions{
		Width:      80,
		Height:     12,
		ShowValues: true,
	}

	output := chart.Render(data, options)
	fmt.Println(output)
}

// BuildingStatusBar creates a status bar for building metrics
func BuildingStatusBar(metric string, current, max float64) string {
	symbols := core.UnicodeSymbols
	percentage := (current / max) * 100

	var output strings.Builder
	output.WriteString(fmt.Sprintf("%-15s ", metric))

	// Create bar
	barWidth := 30
	filled := int(float64(barWidth) * (current / max))

	for i := 0; i < barWidth; i++ {
		if i < filled {
			output.WriteRune(symbols.BarFull)
		} else {
			output.WriteRune(symbols.BarEmpty)
		}
	}

	// Add percentage and values
	output.WriteString(fmt.Sprintf(" %5.1f%% (%.0f/%.0f)", percentage, current, max))

	return output.String()
}
