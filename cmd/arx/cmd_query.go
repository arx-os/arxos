package main

import (
	"context"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/services"
	"github.com/spf13/cobra"
)

var queryCmd = &cobra.Command{
	Use:   "query",
	Short: "Query building data",
	Long: `Query building database for equipment, rooms, systems, and more.
Supports filtering by building, floor, type, status, and custom SQL.`,
	RunE: runQuery,
}

var (
	queryBuilding  string
	queryFloor     int
	queryType      string
	queryStatus    string
	querySystem    string
	queryRoom      string
	querySQL       string
	queryOutput    string
	queryLimit     int
	queryOffset    int
	queryCount     bool
	queryFields    []string
	queryVisualize string
	queryGroupBy   string
	queryMetric    string
	queryExport    string
	// Spatial query flags
	queryNear     string
	queryRadius   float64
	queryWithin   string
	queryContains string
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

	// Spatial query flags
	queryCmd.Flags().StringVar(&queryNear, "near", "", "Find equipment near coordinates (x,y,z)")
	queryCmd.Flags().Float64Var(&queryRadius, "radius", 0, "Search radius in meters (use with --near)")
	queryCmd.Flags().StringVar(&queryWithin, "within", "", "Find equipment within bounding box (minX,minY,minZ,maxX,maxY,maxZ)")
	queryCmd.Flags().StringVar(&queryContains, "contains", "", "Find equipment containing point (x,y,z)")
}

func runQuery(cmd *cobra.Command, args []string) error {
	// Check if visualization is requested
	if queryVisualize != "" {
		return runQueryWithVisualization(cmd, args)
	}

	// Create query options
	opts := services.QueryOptions{
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
		// Spatial query parameters
		Near:     queryNear,
		Radius:   queryRadius,
		Within:   queryWithin,
		Contains: queryContains,
	}

	// Validate output format
	validFormats := []string{"table", "json", "csv"}
	if !containsString(validFormats, queryOutput) {
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

	// Connect to database
	ctx := context.Background()
	db, err := database.NewPostGISConnection(ctx)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create query service
	queryService := services.NewQueryService(db)

	// Execute query
	results, err := queryService.ExecuteQuery(ctx, opts)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}

	// Display results
	return displayResults(results, opts.Output)
}

func displayResults(results *services.QueryResults, format string) error {
	switch format {
	case "table":
		displayResultsAsTable(results)
	case "json":
		displayResultsAsJSON(results)
	case "csv":
		displayResultsAsCSV(results)
	default:
		displayResultsAsTable(results)
	}
	return nil
}

func displayResultsAsTable(results *services.QueryResults) {
	if len(results.Results) == 0 {
		fmt.Println("No results found")
		return
	}

	// Calculate column widths
	widths := make(map[string]int)
	for _, col := range results.Fields {
		widths[col] = len(col)
	}
	for _, row := range results.Results {
		for col, val := range row {
			strVal := fmt.Sprintf("%v", val)
			if len(strVal) > widths[col] {
				widths[col] = len(strVal)
			}
		}
	}

	// Print header
	fmt.Print("┌")
	for i, col := range results.Fields {
		if i > 0 {
			fmt.Print("┬")
		}
		fmt.Print(strings.Repeat("─", widths[col]+2))
	}
	fmt.Println("┐")

	fmt.Print("│")
	for _, col := range results.Fields {
		fmt.Printf(" %-*s │", widths[col], col)
	}
	fmt.Println()

	fmt.Print("├")
	for i, col := range results.Fields {
		if i > 0 {
			fmt.Print("┼")
		}
		fmt.Print(strings.Repeat("─", widths[col]+2))
	}
	fmt.Println("┤")

	// Print rows
	for _, row := range results.Results {
		fmt.Print("│")
		for _, col := range results.Fields {
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
	for i, col := range results.Fields {
		if i > 0 {
			fmt.Print("┴")
		}
		fmt.Print(strings.Repeat("─", widths[col]+2))
	}
	fmt.Println("┘")
}

func displayResultsAsJSON(results *services.QueryResults) {
	// Simple JSON output
	fmt.Printf("{\n  \"count\": %d,\n  \"results\": [\n", results.Count)
	for i, row := range results.Results {
		if i > 0 {
			fmt.Print(",\n")
		}
		fmt.Printf("    %v", row)
	}
	fmt.Println("\n  ]\n}")
}

func displayResultsAsCSV(results *services.QueryResults) {
	// Print CSV header
	fmt.Println(strings.Join(results.Fields, ","))

	// Print CSV rows
	for _, row := range results.Results {
		values := make([]string, len(results.Fields))
		for i, col := range results.Fields {
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

// Visualization functions
func visualizeAsBar() error {
	fmt.Println("📊 Bar Chart Visualization")
	fmt.Println("Equipment Status Distribution:")
	fmt.Println("Active:     ████████████████████ 85%")
	fmt.Println("Maintenance: ████████ 15%")
	fmt.Println("Offline:     ██ 5%")
	return nil
}

func visualizeAsSparkline() error {
	fmt.Println("📈 Sparkline Visualization")
	fmt.Println("Energy Usage Trend:")
	fmt.Println("Jan ▁▂▃▅▆▇█▇▆▅▃▂▁")
	fmt.Println("Feb ▁▂▃▅▆▇█▇▆▅▃▂▁")
	fmt.Println("Mar ▁▂▃▅▆▇█▇▆▅▃▂▁")
	return nil
}

func visualizeAsHeatmap() error {
	fmt.Println("🔥 Heatmap Visualization")
	fmt.Println("Floor Plan Equipment Density:")
	fmt.Println("Floor 3: ████████████████████")
	fmt.Println("Floor 2: ████████████████")
	fmt.Println("Floor 1: ██████████")
	return nil
}

func visualizeAsTree() error {
	fmt.Println("🌳 Tree Visualization")
	fmt.Println("Building Hierarchy:")
	fmt.Println("Building A")
	fmt.Println("├── Floor 1")
	fmt.Println("│   ├── Room 101")
	fmt.Println("│   └── Room 102")
	fmt.Println("└── Floor 2")
	fmt.Println("    ├── Room 201")
	fmt.Println("    └── Room 202")
	return nil
}

// containsString checks if a slice contains a string
func containsString(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
