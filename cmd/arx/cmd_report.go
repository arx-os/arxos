package main

import (
	"fmt"
	"path/filepath"
	"time"

	"github.com/spf13/cobra"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/visualization/export"
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
	err := export.ExportReport(building, reportOutput)
	if err != nil {
		return fmt.Errorf("failed to generate report: %w", err)
	}

	fmt.Printf("Report generated successfully: %s\n", reportOutput)

	// Show file info
	absPath, _ := filepath.Abs(reportOutput)
	fmt.Printf("Full path: %s\n", absPath)

	return nil
}

func runBatchExport(building string) error {
	// Determine format
	var format export.Format
	switch reportFormat {
	case "html":
		format = export.FormatHTML
	case "markdown", "md":
		format = export.FormatMarkdown
	case "ansi":
		format = export.FormatANSI
	default:
		format = export.FormatPlainText
	}

	// Create batch exporter
	baseDir := "./exports"
	if reportOutput != "" {
		baseDir = filepath.Dir(reportOutput)
	}

	exporter := export.NewBatchExporter(baseDir, format)
	err := exporter.ExportDashboard(building)
	if err != nil {
		return fmt.Errorf("batch export failed: %w", err)
	}

	fmt.Printf("Dashboard exported to: %s\n", baseDir)
	fmt.Println("\nExported files:")
	fmt.Println("  - equipment_status")
	fmt.Println("  - energy_weekly")
	fmt.Println("  - metrics_sparklines")
	fmt.Println("  - occupancy_heatmap")
	fmt.Println("  - system_hierarchy")
	fmt.Println("  - index.txt")

	return nil
}