package main

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/arx-os/arxos/internal/commands"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/visualization/charts"
	"github.com/arx-os/arxos/internal/visualization/core"
	"github.com/arx-os/arxos/internal/visualization/export"
)

var queryCmd = &cobra.Command{
	Use:   "query",
	Short: "Query building data",
	Long: `Query building database for equipment, rooms, systems, and more.
Supports filtering by building, floor, type, status, and custom SQL.`,
	RunE: runQuery,
}

var (
	queryBuilding   string
	queryFloor      int
	queryType       string
	queryStatus     string
	querySystem     string
	queryRoom       string
	querySQL        string
	queryOutput     string
	queryLimit      int
	queryOffset     int
	queryCount      bool
	queryFields     []string
	queryVisualize  string
	queryGroupBy    string
	queryMetric     string
	queryExport     string
)

func init() {
	queryCmd.Flags().StringVar(&queryBuilding, "building", "", "Filter by building ID")
	queryCmd.Flags().IntVar(&queryFloor, "floor", 0, "Filter by floor number")
	queryCmd.Flags().StringVar(&queryType, "type", "", "Filter by equipment type")
	queryCmd.Flags().StringVar(&queryStatus, "status", "", "Filter by status (operational/failed/maintenance)")
	queryCmd.Flags().StringVar(&querySystem, "system", "", "Filter by system type")
	queryCmd.Flags().StringVar(&queryRoom, "room", "", "Filter by room ID or name")
	queryCmd.Flags().StringVar(&querySQL, "sql", "", "Raw SQL query")
	queryCmd.Flags().StringVar(&queryOutput, "output", "table", "Output format (table/json/csv)")
	queryCmd.Flags().IntVar(&queryLimit, "limit", 50, "Maximum results to return")
	queryCmd.Flags().IntVar(&queryOffset, "offset", 0, "Offset for pagination")
	queryCmd.Flags().BoolVar(&queryCount, "count", false, "Show count only")
	queryCmd.Flags().StringSliceVar(&queryFields, "fields", []string{}, "Fields to display")

	// Visualization flags
	queryCmd.Flags().StringVar(&queryVisualize, "visualize", "", "Visualize results (bar, sparkline, heatmap, tree)")
	queryCmd.Flags().StringVar(&queryGroupBy, "group-by", "", "Group results by field for visualization")
	queryCmd.Flags().StringVar(&queryMetric, "metric", "", "Metric to visualize (count, sum, avg)")
	queryCmd.Flags().StringVar(&queryExport, "export", "", "Export visualization to file")
}

func runQuery(cmd *cobra.Command, args []string) error {
	// Check if visualization is requested
	if queryVisualize != "" {
		return runQueryWithVisualization(cmd, args)
	}

	// Create query options
	opts := commands.QueryOptions{
		Building: queryBuilding,
		Floor:    queryFloor,
		Type:     queryType,
		Status:   queryStatus,
		System:   querySystem,
		Room:     queryRoom,
		SQL:      querySQL,
		Output:   queryOutput,
		Limit:    queryLimit,
		Offset:   queryOffset,
		Count:    queryCount,
		Fields:   queryFields,
	}

	// Validate output format
	validFormats := []string{"table", "json", "csv"}
	if !contains(validFormats, queryOutput) {
		return fmt.Errorf("invalid output format: %s (supported: %s)",
			queryOutput, strings.Join(validFormats, ", "))
	}

	// Log query parameters if verbose
	if verbose, _ := cmd.Flags().GetBool("verbose"); verbose {
		logger.Debug("Query parameters:")
		if queryBuilding != "" {
			logger.Debug("  Building: %s", queryBuilding)
		}
		if queryFloor != 0 {
			logger.Debug("  Floor: %d", queryFloor)
		}
		if queryType != "" {
			logger.Debug("  Type: %s", queryType)
		}
		if queryStatus != "" {
			logger.Debug("  Status: %s", queryStatus)
		}
		if querySystem != "" {
			logger.Debug("  System: %s", querySystem)
		}
		if queryRoom != "" {
			logger.Debug("  Room: %s", queryRoom)
		}
	}

	// Execute query - for now this returns error only
	// TODO: Update ExecuteQuery to return results properly
	err := commands.ExecuteQuery(opts)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}

	// Placeholder for when ExecuteQuery returns results
	fmt.Println("Query executed successfully")

	return nil
}

func displayResultsAsTable(results *commands.QueryResults) {
	if len(results.Rows) == 0 {
		fmt.Println("No results found")
		return
	}

	// Calculate column widths
	widths := make(map[string]int)
	for _, col := range results.Columns {
		widths[col] = len(col)
	}
	for _, row := range results.Rows {
		for col, val := range row {
			strVal := fmt.Sprintf("%v", val)
			if len(strVal) > widths[col] {
				widths[col] = len(strVal)
			}
		}
	}

	// Print header
	fmt.Print("┌")
	for i, col := range results.Columns {
		if i > 0 {
			fmt.Print("┬")
		}
		fmt.Print(strings.Repeat("─", widths[col]+2))
	}
	fmt.Println("┐")

	fmt.Print("│")
	for _, col := range results.Columns {
		fmt.Printf(" %-*s │", widths[col], col)
	}
	fmt.Println()

	fmt.Print("├")
	for i, col := range results.Columns {
		if i > 0 {
			fmt.Print("┼")
		}
		fmt.Print(strings.Repeat("─", widths[col]+2))
	}
	fmt.Println("┤")

	// Print rows
	for _, row := range results.Rows {
		fmt.Print("│")
		for _, col := range results.Columns {
			val := row[col]
			strVal := fmt.Sprintf("%v", val)
			if val == nil {
				strVal = ""
			}
			fmt.Printf(" %-*s │", widths[col], strVal)
		}
		fmt.Println()
	}

	// Print footer
	fmt.Print("└")
	for i, col := range results.Columns {
		if i > 0 {
			fmt.Print("┴")
		}
		fmt.Print(strings.Repeat("─", widths[col]+2))
	}
	fmt.Println("┘")
}

func displayResultsAsJSON(results *commands.QueryResults) {
	// The ExecuteQuery function already returns JSON-formatted output
	// when output format is "json"
	fmt.Println(results.JSONOutput)
}

func displayResultsAsCSV(results *commands.QueryResults) {
	// Print CSV header
	fmt.Println(strings.Join(results.Columns, ","))

	// Print CSV rows
	for _, row := range results.Rows {
		values := make([]string, len(results.Columns))
		for i, col := range results.Columns {
			val := row[col]
			if val == nil {
				values[i] = ""
			} else {
				strVal := fmt.Sprintf("%v", val)
				// Escape quotes and wrap in quotes if contains comma
				if strings.Contains(strVal, ",") || strings.Contains(strVal, "\"") {
					strVal = strings.ReplaceAll(strVal, "\"", "\"\"")
					strVal = fmt.Sprintf("\"%s\"", strVal)
				}
				values[i] = strVal
			}
		}
		fmt.Println(strings.Join(values, ","))
	}
}

// runQueryWithVisualization runs query and visualizes results
func runQueryWithVisualization(cmd *cobra.Command, args []string) error {
	// For demo purposes, generate sample data based on query parameters
	// In production, this would execute actual database query

	switch queryVisualize {
	case "bar":
		return visualizeAsBar()
	case "sparkline":
		return visualizeAsSparkline()
	case "heatmap":
		return visualizeAsHeatmap()
	case "tree":
		return visualizeAsTree()
	default:
		return fmt.Errorf("unsupported visualization type: %s", queryVisualize)
	}
}

func visualizeAsBar() error {
	chart := charts.NewBarChart()

	// Generate sample data based on query parameters
	data := &charts.BarData{
		Title: fmt.Sprintf("Query Results - %s", queryBuilding),
	}

	if queryGroupBy == "floor" && queryMetric == "count" {
		// Equipment count by floor
		data.Title = "Equipment Count by Floor"
		data.Unit = "units"
		for floor := 1; floor <= 5; floor++ {
			count := 10 + floor*3 // Sample data
			data.Items = append(data.Items, charts.BarItem{
				Label: fmt.Sprintf("Floor %d", floor),
				Value: float64(count),
			})
		}
	} else if queryGroupBy == "status" {
		// Equipment by status
		data.Title = "Equipment by Status"
		data.Unit = "units"
		statuses := map[string]float64{
			"Operational": 85,
			"Maintenance": 12,
			"Failed":      3,
		}
		for status, count := range statuses {
			data.Items = append(data.Items, charts.BarItem{
				Label: status,
				Value: count,
			})
		}
	} else {
		// Default: Show sample energy data
		data.Title = "Energy Consumption"
		data.Unit = "kWh"
		days := []string{"Mon", "Tue", "Wed", "Thu", "Fri"}
		for _, day := range days {
			data.Items = append(data.Items, charts.BarItem{
				Label: day,
				Value: 300 + float64(len(day)*20),
			})
		}
	}

	options := core.RenderOptions{
		Width:      80,
		Height:     15,
		ShowValues: true,
	}

	output := chart.Render(data, options)
	fmt.Println(output)

	// Export if requested
	if queryExport != "" {
		err := export.QuickExport(output, queryExport)
		if err != nil {
			return fmt.Errorf("failed to export: %w", err)
		}
		fmt.Printf("\nVisualization exported to: %s\n", queryExport)
	}

	return nil
}

func visualizeAsSparkline() error {
	spark := charts.NewSparkline()

	// Generate time-series data based on query
	var datasets []charts.SparklineData

	if queryMetric == "energy" {
		datasets = append(datasets, charts.SparklineData{
			Label:  "Energy (kWh)",
			Values: generateSampleTimeSeries(24),
		})
	} else if queryMetric == "temperature" {
		datasets = append(datasets, charts.SparklineData{
			Label:  "Temp (°F)",
			Values: generateSampleTimeSeries(24),
		})
	} else {
		// Default: multiple metrics
		datasets = []charts.SparklineData{
			{Label: "Power", Values: generateSampleTimeSeries(24)},
			{Label: "Temp", Values: generateSampleTimeSeries(24)},
			{Label: "Humidity", Values: generateSampleTimeSeries(24)},
		}
	}

	fmt.Printf("Time Series Data - Building %s\n", queryBuilding)
	fmt.Println(strings.Repeat("─", 60))
	output := spark.RenderMultiple(datasets, 40)
	fmt.Println(output)

	// Export if requested
	if queryExport != "" {
		fullOutput := fmt.Sprintf("Time Series Data - Building %s\n%s\n%s", queryBuilding, strings.Repeat("─", 60), output)
		err := export.QuickExport(fullOutput, queryExport)
		if err != nil {
			return fmt.Errorf("failed to export: %w", err)
		}
		fmt.Printf("\nVisualization exported to: %s\n", queryExport)
	}

	return nil
}

func visualizeAsHeatmap() error {
	// Generate sample data based on query parameters
	if queryGroupBy == "floor" && queryMetric == "energy" {
		// Energy usage by floor and hour
		output := charts.RenderEnergyHeatmap(queryBuilding, 24)
		fmt.Println(output)

		if queryExport != "" {
			err := export.QuickExport(output, queryExport)
			if err != nil {
				return fmt.Errorf("failed to export: %w", err)
			}
			fmt.Printf("\nVisualization exported to: %s\n", queryExport)
		}
	} else {
		// Default: Occupancy heatmap
		output := charts.RenderFloorOccupancy(queryBuilding, 5, 4)
		fmt.Println(output)

		if queryExport != "" {
			err := export.QuickExport(output, queryExport)
			if err != nil {
				return fmt.Errorf("failed to export: %w", err)
			}
			fmt.Printf("\nVisualization exported to: %s\n", queryExport)
		}
	}

	return nil
}

func visualizeAsTree() error {
	var output string

	if queryGroupBy == "hierarchy" {
		// Building system hierarchy
		output = charts.RenderBuildingHierarchy(queryBuilding)
	} else if queryGroupBy == "equipment" && queryFloor != 0 {
		// Equipment tree for specific floor
		output = charts.RenderEquipmentTree(queryBuilding, queryFloor)
	} else if queryGroupBy == "dependencies" && queryType != "" {
		// Dependency tree for component
		output = charts.RenderDependencyTree(queryType)
	} else {
		// Default: Building hierarchy
		output = charts.RenderBuildingHierarchy(queryBuilding)
	}

	fmt.Println(output)

	// Export if requested
	if queryExport != "" {
		err := export.QuickExport(output, queryExport)
		if err != nil {
			return fmt.Errorf("failed to export: %w", err)
		}
		fmt.Printf("\nVisualization exported to: %s\n", queryExport)
	}

	return nil
}

func generateSampleTimeSeries(points int) []float64 {
	data := make([]float64, points)
	base := 50.0
	for i := 0; i < points; i++ {
		data[i] = base + float64(i%10)*2
	}
	return data
}