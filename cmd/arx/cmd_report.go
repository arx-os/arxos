package main

import (
	"context"
	"fmt"
	"path/filepath"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/visualization/export"
	"github.com/spf13/cobra"
)

var reportCmd = &cobra.Command{
	Use:   "report [building]",
	Short: "Generate comprehensive building reports",
	Long: `Generate detailed reports containing visualizations, metrics, and status information.

Reports can include:
- Equipment status by floor
- Energy consumption charts  
- Real-time metrics trends
- System hierarchy diagrams
- Anomaly detection heatmaps`,
	Args: cobra.MaximumNArgs(1),
	RunE: runReport,
}

var (
	reportOutput   string
	reportFormat   string
	reportSections []string
	reportPeriod   string
	reportBatch    bool
)

func init() {
	reportCmd.Flags().StringVarP(&reportOutput, "output", "o", "", "Output file path (default: report_<building>_<timestamp>.txt)")
	reportCmd.Flags().StringVarP(&reportFormat, "format", "f", "text", "Output format (text, html, markdown)")
	reportCmd.Flags().StringSliceVarP(&reportSections, "sections", "s", []string{"all"}, "Report sections to include")
	reportCmd.Flags().StringVar(&reportPeriod, "period", "week", "Time period for metrics (day, week, month)")
	reportCmd.Flags().BoolVar(&reportBatch, "batch", false, "Export all visualizations as separate files")
}

func runReport(cmd *cobra.Command, args []string) error {
	building := "ARXOS-001"
	if len(args) > 0 {
		building = args[0]
	}

	// Generate output filename if not specified
	if reportOutput == "" {
		timestamp := time.Now().Format("20060102_150405")
		ext := ".txt"
		if reportFormat == "html" {
			ext = ".html"
		} else if reportFormat == "markdown" {
			ext = ".md"
		}
		reportOutput = fmt.Sprintf("report_%s_%s%s", building, timestamp, ext)
	}

	logger.Info("Generating report for building %s", building)

	if reportBatch {
		// Export all visualizations separately
		return runBatchExport(building)
	}

	// Generate single comprehensive report
	exporter := export.NewExporter(dbConn)
	ctx := cmd.Context()
	if ctx == nil {
		ctx = context.Background()
	}

	return exporter.GenerateReport(ctx, building, reportFormat, reportOutput)
}

func runBatchExport(building string) error {
	// Create batch exporter
	exporter := export.NewExporter(dbConn)
	ctx := context.Background()

	// Determine output directory
	baseDir := "./exports"
	if reportOutput != "" {
		baseDir = filepath.Dir(reportOutput)
	}

	// Create timestamped subdirectory
	timestamp := time.Now().Format("20060102_150405")
	outputDir := filepath.Join(baseDir, fmt.Sprintf("%s_%s", building, timestamp))

	// Export visualizations
	if err := exporter.ExportVisualizations(ctx, building, outputDir); err != nil {
		return fmt.Errorf("failed to export visualizations: %w", err)
	}

	fmt.Printf("Dashboard exported to: %s\n", outputDir)
	fmt.Println("\nExported files:")
	fmt.Println("  - equipment_status.txt")
	fmt.Println("  - energy_usage.txt")
	fmt.Println("  - occupancy_heatmap.txt")
	fmt.Println("  - index.txt")

	return nil
}
