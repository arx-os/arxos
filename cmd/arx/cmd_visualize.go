package main

import (
	"fmt"
	"math/rand"
	"strings"
	"time"

	"github.com/spf13/cobra"
	"github.com/arx-os/arxos/internal/visualization/charts"
	"github.com/arx-os/arxos/internal/visualization/core"
	"github.com/arx-os/arxos/internal/visualization/export"
)

var visualizeCmd = &cobra.Command{
	Use:   "visualize",
	Short: "Visualize building data in the terminal",
	Long: `Display rich data visualizations directly in the terminal using ASCII and Unicode characters.

Supports various chart types including bar charts, sparklines, heatmaps, and dashboards.`,
	Aliases: []string{"viz", "chart"},
}

// visualize demo - shows all visualization capabilities
var vizDemoCmd = &cobra.Command{
	Use:   "demo",
	Short: "Run visualization demo",
	Long:  "Display examples of all available visualization types",
	RunE:  runVizDemo,
}

// visualize energy - show energy consumption
var vizEnergyCmd = &cobra.Command{
	Use:   "energy [building]",
	Short: "Visualize energy consumption",
	RunE:  runVizEnergy,
}

// visualize status - show equipment status
var vizStatusCmd = &cobra.Command{
	Use:   "status [building]",
	Short: "Visualize equipment status by floor",
	RunE:  runVizStatus,
}

// visualize metrics - show real-time metrics
var vizMetricsCmd = &cobra.Command{
	Use:   "metrics [building]",
	Short: "Show real-time metrics as sparklines",
	RunE:  runVizMetrics,
}

// visualize dashboard - full dashboard view
var vizDashboardCmd = &cobra.Command{
	Use:   "dashboard [building]",
	Short: "Display full terminal dashboard",
	RunE:  runVizDashboard,
}

var (
	vizChartType   string
	vizWidth       int
	vizHeight      int
	vizRefresh     int
	vizUnicode     bool
	vizColors      bool
	vizShowValues  bool
	vizShowLegend  bool
	vizExportPath  string
	vizExportFormat string
)

func init() {
	// Global visualization flags
	visualizeCmd.PersistentFlags().StringVar(&vizChartType, "type", "auto", "Chart type (bar, sparkline, heatmap, tree)")
	visualizeCmd.PersistentFlags().IntVar(&vizWidth, "width", 0, "Chart width (0=auto)")
	visualizeCmd.PersistentFlags().IntVar(&vizHeight, "height", 0, "Chart height (0=auto)")
	visualizeCmd.PersistentFlags().IntVar(&vizRefresh, "refresh", 0, "Refresh interval in seconds (0=once)")
	visualizeCmd.PersistentFlags().BoolVar(&vizUnicode, "unicode", true, "Use Unicode characters")
	visualizeCmd.PersistentFlags().BoolVar(&vizColors, "colors", true, "Use colors")
	visualizeCmd.PersistentFlags().BoolVar(&vizShowValues, "values", true, "Show numeric values")
	visualizeCmd.PersistentFlags().BoolVar(&vizShowLegend, "legend", true, "Show legend")
	visualizeCmd.PersistentFlags().StringVar(&vizExportPath, "export", "", "Export visualization to file")
	visualizeCmd.PersistentFlags().StringVar(&vizExportFormat, "export-format", "text", "Export format (text, ansi, markdown, html)")

	// Add subcommands
	visualizeCmd.AddCommand(
		vizDemoCmd,
		vizEnergyCmd,
		vizStatusCmd,
		vizMetricsCmd,
		vizDashboardCmd,
	)
}

func runVizDemo(cmd *cobra.Command, args []string) error {
	fmt.Println("ArxOS Terminal Visualization Demo")
	fmt.Println(strings.Repeat("═", 80))
	fmt.Println()

	// Demo 1: Bar Chart
	fmt.Println("1. BAR CHART - Energy Usage by Day")
	fmt.Println(strings.Repeat("─", 80))
	demoBarChart()
	fmt.Println()

	// Demo 2: Sparklines
	fmt.Println("2. SPARKLINES - Real-time Metrics")
	fmt.Println(strings.Repeat("─", 80))
	demoSparklines()
	fmt.Println()

	// Demo 3: Equipment Status
	fmt.Println("3. EQUIPMENT STATUS - By Floor")
	fmt.Println(strings.Repeat("─", 80))
	demoEquipmentStatus()
	fmt.Println()

	// Demo 4: ASCII Symbols
	fmt.Println("4. SYMBOL SETS")
	fmt.Println(strings.Repeat("─", 80))
	demoSymbols()
	fmt.Println()

	return nil
}

func runVizEnergy(cmd *cobra.Command, args []string) error {
	building := "ARXOS-001"
	if len(args) > 0 {
		building = args[0]
	}

	// In production, this would query the database
	data := generateEnergyData()

	chart := charts.NewBarChart()
	barData := &charts.BarData{
		Title: fmt.Sprintf("Energy Consumption - Building %s", building),
		Unit:  "kWh",
	}

	for day, kwh := range data {
		barData.Items = append(barData.Items, charts.BarItem{
			Label: day,
			Value: kwh,
		})
	}

	options := core.RenderOptions{
		Width:      getChartWidth(),
		Height:     20,
		ShowValues: vizShowValues,
	}

	output := chart.Render(barData, options)
	fmt.Println(output)

	// Export if requested
	if vizExportPath != "" {
		err := exportVisualization(output, vizExportPath, vizExportFormat)
		if err != nil {
			return fmt.Errorf("failed to export: %w", err)
		}
		fmt.Printf("\nExported to: %s\n", vizExportPath)
	}

	// Handle refresh
	if vizRefresh > 0 {
		ticker := time.NewTicker(time.Duration(vizRefresh) * time.Second)
		defer ticker.Stop()

		for range ticker.C {
			// Clear screen (ANSI escape sequence)
			fmt.Print("\033[H\033[2J")

			// Update data and re-render
			data = generateEnergyData()
			barData.Items = nil
			for day, kwh := range data {
				barData.Items = append(barData.Items, charts.BarItem{
					Label: day,
					Value: kwh,
				})
			}

			output = chart.Render(barData, options)
			fmt.Println(output)
		}
	}

	return nil
}

func runVizStatus(cmd *cobra.Command, args []string) error {
	building := "ARXOS-001"
	if len(args) > 0 {
		building = args[0]
	}

	// In production, this would query the database
	floors := generateFloorStatus()

	output := charts.RenderEquipmentStatus(building, floors)
	fmt.Println(output)

	// Export if requested
	if vizExportPath != "" {
		err := exportVisualization(output, vizExportPath, vizExportFormat)
		if err != nil {
			return fmt.Errorf("failed to export: %w", err)
		}
		fmt.Printf("\nExported to: %s\n", vizExportPath)
	}

	return nil
}

func runVizMetrics(cmd *cobra.Command, args []string) error {
	building := "ARXOS-001"
	if len(args) > 0 {
		building = args[0]
	}

	fmt.Printf("Building %s - Real-time Metrics\n", building)
	fmt.Println(strings.Repeat("═", 80))
	fmt.Println()

	// Generate sample metrics
	metrics := map[string][]float64{
		"Power (kW)":    generateTimeSeriesData(48, 50, 100),
		"Temperature":   generateTimeSeriesData(48, 68, 76),
		"Humidity (%)":  generateTimeSeriesData(48, 30, 60),
		"CO2 (ppm)":     generateTimeSeriesData(48, 350, 600),
		"Occupancy (%)": generateTimeSeriesData(48, 0, 100),
	}

	spark := charts.NewSparkline()
	var datasets []charts.SparklineData

	for name, values := range metrics {
		datasets = append(datasets, charts.SparklineData{
			Label:  name,
			Values: values,
		})
	}

	output := spark.RenderMultiple(datasets, 50)
	fmt.Println(output)

	// Add legend
	legend := "\nTrend Indicators: ↑ Rising  ↓ Falling  → Stable"
	fmt.Println(legend)

	// Export if requested
	if vizExportPath != "" {
		fullOutput := output + legend
		err := exportVisualization(fullOutput, vizExportPath, vizExportFormat)
		if err != nil {
			return fmt.Errorf("failed to export: %w", err)
		}
		fmt.Printf("\nExported to: %s\n", vizExportPath)
	}

	return nil
}

func runVizDashboard(cmd *cobra.Command, args []string) error {
	building := "ARXOS-001"
	if len(args) > 0 {
		building = args[0]
	}

	// Clear screen
	fmt.Print("\033[H\033[2J")

	// Dashboard header
	fmt.Printf("╔════════════════════════════════════════════════════════════════════════════╗\n")
	fmt.Printf("║                     ArxOS Building Dashboard - %s                     ║\n", building)
	fmt.Printf("╠════════════════════════════════════════════════════════════════════════════╣\n")

	// Section 1: Equipment Status
	fmt.Printf("║ EQUIPMENT STATUS BY FLOOR                                                 ║\n")
	fmt.Printf("╟────────────────────────────────────────────────────────────────────────────╢\n")

	floors := generateFloorStatus()
	for floor := 1; floor <= 5; floor++ {
		floorStr := fmt.Sprintf("%d", floor)
		equipment := floors[floorStr]
		operational := 0
		for _, status := range equipment {
			if status == "operational" {
				operational++
			}
		}
		bar := charts.BuildingStatusBar(
			fmt.Sprintf("Floor %d", floor),
			float64(operational),
			float64(len(equipment)),
		)
		fmt.Printf("║ %s ║\n", padRight(bar, 74))
	}

	// Section 2: Real-time Metrics
	fmt.Printf("╟────────────────────────────────────────────────────────────────────────────╢\n")
	fmt.Printf("║ REAL-TIME METRICS (24HR)                                                  ║\n")
	fmt.Printf("╟────────────────────────────────────────────────────────────────────────────╢\n")

	spark := charts.NewSparkline()
	metrics := []charts.SparklineData{
		{Label: "Power", Values: generateTimeSeriesData(24, 50, 100)},
		{Label: "Temp", Values: generateTimeSeriesData(24, 68, 76)},
		{Label: "CO2", Values: generateTimeSeriesData(24, 350, 600)},
	}

	for _, metric := range metrics {
		line := spark.Render(&metric, 50)
		fmt.Printf("║ %s ║\n", padRight(line, 74))
	}

	// Section 3: Alerts
	fmt.Printf("╟────────────────────────────────────────────────────────────────────────────╢\n")
	fmt.Printf("║ ACTIVE ALERTS                                                             ║\n")
	fmt.Printf("╟────────────────────────────────────────────────────────────────────────────╢\n")

	alerts := []string{
		"⚠ Floor 3 - HVAC/AHU-02 requires maintenance",
		"✓ Floor 1 - All systems operational",
		"⚠ Floor 5 - High energy consumption detected",
	}

	for _, alert := range alerts {
		fmt.Printf("║ %s ║\n", padRight(alert, 74))
	}

	// Footer
	fmt.Printf("╚════════════════════════════════════════════════════════════════════════════╝\n")
	fmt.Printf("\nLast Updated: %s | Press Ctrl+C to exit\n", time.Now().Format("15:04:05"))

	// Auto-refresh if specified
	if vizRefresh > 0 {
		time.Sleep(time.Duration(vizRefresh) * time.Second)
		return runVizDashboard(cmd, args)
	}

	return nil
}

// Demo functions
func demoBarChart() {
	chart := charts.NewBarChart()

	data := &charts.BarData{
		Unit: "kWh",
		Items: []charts.BarItem{
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
		Width:      60,
		Height:     10,
		ShowValues: true,
	}

	fmt.Println(chart.Render(data, options))
}

func demoSparklines() {
	spark := charts.NewSparkline()

	datasets := []charts.SparklineData{
		{
			Label:  "Power (kW)",
			Values: generateTimeSeriesData(24, 50, 100),
		},
		{
			Label:  "Temp (°F)",
			Values: generateTimeSeriesData(24, 68, 76),
		},
		{
			Label:  "Humidity",
			Values: generateTimeSeriesData(24, 30, 60),
		},
	}

	fmt.Println(spark.RenderMultiple(datasets, 40))
}

func demoEquipmentStatus() {
	floors := map[string][]string{
		"1": generateEquipmentStatuses(15),
		"2": generateEquipmentStatuses(20),
		"3": generateEquipmentStatuses(18),
		"4": generateEquipmentStatuses(22),
		"5": generateEquipmentStatuses(16),
	}

	for floor := 1; floor <= 5; floor++ {
		floorStr := fmt.Sprintf("%d", floor)
		equipment := floors[floorStr]
		operational := 0
		for _, status := range equipment {
			if status == "operational" {
				operational++
			}
		}

		bar := charts.BuildingStatusBar(
			fmt.Sprintf("Floor %d", floor),
			float64(operational),
			float64(len(equipment)),
		)
		fmt.Println(bar)
	}
}

func demoSymbols() {
	fmt.Println("ASCII Symbols:")
	ascii := core.ASCIISymbols
	fmt.Printf("  Bars: Full[%c] Empty[%c]\n", ascii.BarFull, ascii.BarEmpty)
	fmt.Printf("  Box:  %c%c%c%c%c\n", ascii.BoxTopLeft, ascii.BoxHoriz, ascii.BoxTopRight, ascii.BoxVert, ascii.BoxBottomRight)
	fmt.Printf("  Status: OK[%c] Warn[%c] Error[%c]\n", ascii.CheckMark, ascii.Warning, ascii.Error)

	fmt.Println("\nUnicode Symbols:")
	unicode := core.UnicodeSymbols
	fmt.Printf("  Bars: Full[%c] Empty[%c] Partial[", unicode.BarFull, unicode.BarEmpty)
	for _, p := range unicode.BarPartial {
		fmt.Printf("%c", p)
	}
	fmt.Println("]")
	fmt.Printf("  Box:  %c%c%c%c%c\n", unicode.BoxTopLeft, unicode.BoxHoriz, unicode.BoxTopRight, unicode.BoxVert, unicode.BoxBottomRight)
	fmt.Printf("  Status: OK[%c] Warn[%c] Error[%c]\n", unicode.CheckMark, unicode.Warning, unicode.Error)
	fmt.Printf("  Sparkline: ")
	for _, s := range unicode.Sparkline {
		fmt.Printf("%c", s)
	}
	fmt.Println()
}

// Helper functions
func getChartWidth() int {
	if vizWidth > 0 {
		return vizWidth
	}
	// Default width
	return 80
}

func generateEnergyData() map[string]float64 {
	days := []string{"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
	data := make(map[string]float64)

	for _, day := range days {
		// Generate realistic energy usage (higher on weekdays)
		base := 300.0
		if day == "Sat" || day == "Sun" {
			base = 150.0
		}
		data[day] = base + rand.Float64()*200
	}

	return data
}

func generateFloorStatus() map[string][]string {
	floors := make(map[string][]string)

	for floor := 1; floor <= 5; floor++ {
		equipmentCount := 15 + rand.Intn(10)
		floors[fmt.Sprintf("%d", floor)] = generateEquipmentStatuses(equipmentCount)
	}

	return floors
}

func generateEquipmentStatuses(count int) []string {
	statuses := make([]string, count)
	for i := 0; i < count; i++ {
		r := rand.Float64()
		if r < 0.8 {
			statuses[i] = "operational"
		} else if r < 0.95 {
			statuses[i] = "maintenance"
		} else {
			statuses[i] = "failed"
		}
	}
	return statuses
}

func generateTimeSeriesData(points int, min, max float64) []float64 {
	data := make([]float64, points)
	current := min + (max-min)/2

	for i := 0; i < points; i++ {
		// Random walk with bounds
		change := (rand.Float64() - 0.5) * (max - min) / 10
		current += change

		if current < min {
			current = min
		}
		if current > max {
			current = max
		}

		data[i] = current
	}

	return data
}

func padRight(s string, length int) string {
	if len(s) >= length {
		return s[:length]
	}
	return s + strings.Repeat(" ", length-len(s))
}

func exportVisualization(content, path, format string) error {
	var exportFormat export.Format
	switch format {
	case "text", "plain":
		exportFormat = export.FormatPlainText
	case "ansi":
		exportFormat = export.FormatANSI
	case "markdown", "md":
		exportFormat = export.FormatMarkdown
	case "html":
		exportFormat = export.FormatHTML
	default:
		exportFormat = export.FormatPlainText
	}

	options := export.Options{
		Format:    exportFormat,
		FilePath:  path,
		Timestamp: true,
		Metadata: map[string]string{
			"Generator": "ArxOS Visualization",
			"Version":   "1.0.0",
		},
	}

	exporter := export.NewExporter(options)
	return exporter.Export(content)
}