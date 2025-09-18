package export

import (
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/visualization/charts"
	"github.com/arx-os/arxos/internal/visualization/core"
)

// BatchExporter handles exporting multiple visualizations
type BatchExporter struct {
	baseDir   string
	format    Format
	timestamp bool
}

// NewBatchExporter creates a batch exporter
func NewBatchExporter(baseDir string, format Format) *BatchExporter {
	return &BatchExporter{
		baseDir:   baseDir,
		format:    format,
		timestamp: true,
	}
}

// ExportDashboard exports a complete dashboard
func (b *BatchExporter) ExportDashboard(buildingID string) error {
	timestamp := time.Now().Format("20060102_150405")
	dashboardDir := filepath.Join(b.baseDir, fmt.Sprintf("dashboard_%s_%s", buildingID, timestamp))

	// Generate all visualizations
	visualizations := b.generateDashboardVisualizations(buildingID)

	// Export each visualization
	for name, content := range visualizations {
		filename := b.generateFilename(dashboardDir, name)
		options := Options{
			Format:    b.format,
			FilePath:  filename,
			Timestamp: b.timestamp,
			Metadata: map[string]string{
				"Building":      buildingID,
				"Visualization": name,
			},
		}

		exporter := NewExporter(options)
		if err := exporter.Export(content); err != nil {
			return fmt.Errorf("failed to export %s: %w", name, err)
		}
	}

	// Create index file
	indexPath := filepath.Join(dashboardDir, "index.txt")
	if err := b.createIndexFile(indexPath, visualizations); err != nil {
		return fmt.Errorf("failed to create index: %w", err)
	}

	return nil
}

// generateDashboardVisualizations generates all dashboard charts
func (b *BatchExporter) generateDashboardVisualizations(buildingID string) map[string]string {
	visualizations := make(map[string]string)

	// 1. Equipment Status
	floors := map[string][]string{
		"1": generateSampleStatuses(15),
		"2": generateSampleStatuses(20),
		"3": generateSampleStatuses(18),
	}
	visualizations["equipment_status"] = charts.RenderEquipmentStatus(buildingID, floors)

	// 2. Energy Bar Chart
	barChart := charts.NewBarChart()
	barData := &charts.BarData{
		Title: "Weekly Energy Consumption",
		Unit:  "kWh",
	}
	days := []string{"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
	for _, day := range days {
		barData.Items = append(barData.Items, charts.BarItem{
			Label: day,
			Value: 300 + float64(len(day)*50),
		})
	}
	options := core.RenderOptions{Width: 60, Height: 15, ShowValues: true}
	visualizations["energy_weekly"] = barChart.Render(barData, options)

	// 3. Metrics Sparklines
	spark := charts.NewSparkline()
	datasets := []charts.SparklineData{
		{Label: "Power", Values: generateTimeSeries(24)},
		{Label: "Temp", Values: generateTimeSeries(24)},
		{Label: "CO2", Values: generateTimeSeries(24)},
	}
	visualizations["metrics_sparklines"] = spark.RenderMultiple(datasets, 50)

	// 4. Occupancy Heatmap
	visualizations["occupancy_heatmap"] = charts.RenderFloorOccupancy(buildingID, 5, 4)

	// 5. System Hierarchy Tree
	visualizations["system_hierarchy"] = charts.RenderBuildingHierarchy(buildingID)

	return visualizations
}

// generateFilename creates appropriate filename based on format
func (b *BatchExporter) generateFilename(dir, name string) string {
	ext := ".txt"
	switch b.format {
	case FormatHTML:
		ext = ".html"
	case FormatMarkdown:
		ext = ".md"
	case FormatANSI:
		ext = ".ansi"
	}
	return filepath.Join(dir, name+ext)
}

// createIndexFile creates an index of exported files
func (b *BatchExporter) createIndexFile(path string, visualizations map[string]string) error {
	var content strings.Builder

	content.WriteString("ArxOS Visualization Export Index\n")
	content.WriteString("=================================\n\n")
	content.WriteString(fmt.Sprintf("Generated: %s\n\n", time.Now().Format("2006-01-02 15:04:05")))
	content.WriteString("Files:\n")

	for name := range visualizations {
		filename := filepath.Base(b.generateFilename("", name))
		content.WriteString(fmt.Sprintf("  - %s\n", filename))
	}

	options := Options{
		Format:   FormatPlainText,
		FilePath: path,
	}
	exporter := NewExporter(options)
	return exporter.Export(content.String())
}

// Helper functions
func generateSampleStatuses(count int) []string {
	statuses := make([]string, count)
	for i := 0; i < count; i++ {
		if i%10 < 8 {
			statuses[i] = "operational"
		} else if i%10 == 8 {
			statuses[i] = "maintenance"
		} else {
			statuses[i] = "failed"
		}
	}
	return statuses
}

func generateTimeSeries(points int) []float64 {
	data := make([]float64, points)
	for i := 0; i < points; i++ {
		data[i] = 50 + float64(i%10)*3
	}
	return data
}

// ExportReport generates a comprehensive building report
func ExportReport(buildingID, outputPath string) error {
	var report strings.Builder

	// Header
	report.WriteString(fmt.Sprintf("Building Report: %s\n", buildingID))
	report.WriteString(fmt.Sprintf("Generated: %s\n", time.Now().Format("2006-01-02 15:04:05")))
	report.WriteString(strings.Repeat("=", 80) + "\n\n")

	// Equipment Status Section
	report.WriteString("EQUIPMENT STATUS\n")
	report.WriteString(strings.Repeat("-", 40) + "\n")
	floors := map[string][]string{
		"1": generateSampleStatuses(15),
		"2": generateSampleStatuses(20),
	}
	report.WriteString(charts.RenderEquipmentStatus(buildingID, floors))
	report.WriteString("\n\n")

	// Energy Usage Section
	report.WriteString("ENERGY USAGE (LAST 7 DAYS)\n")
	report.WriteString(strings.Repeat("-", 40) + "\n")
	barChart := charts.NewBarChart()
	barData := &charts.BarData{
		Unit: "kWh",
	}
	days := []string{"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
	for _, day := range days {
		barData.Items = append(barData.Items, charts.BarItem{
			Label: day,
			Value: 300 + float64(len(day)*50),
		})
	}
	options := core.RenderOptions{Width: 60, Height: 10, ShowValues: true}
	report.WriteString(barChart.Render(barData, options))
	report.WriteString("\n\n")

	// Metrics Section
	report.WriteString("REAL-TIME METRICS\n")
	report.WriteString(strings.Repeat("-", 40) + "\n")
	spark := charts.NewSparkline()
	datasets := []charts.SparklineData{
		{Label: "Power", Values: generateTimeSeries(24)},
		{Label: "Temperature", Values: generateTimeSeries(24)},
	}
	report.WriteString(spark.RenderMultiple(datasets, 50))
	report.WriteString("\n\n")

	// System Hierarchy Section
	report.WriteString("SYSTEM HIERARCHY\n")
	report.WriteString(strings.Repeat("-", 40) + "\n")
	report.WriteString(charts.RenderBuildingHierarchy(buildingID))

	// Export report
	return QuickExport(report.String(), outputPath)
}
