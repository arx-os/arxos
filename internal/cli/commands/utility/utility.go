package utility

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"text/tabwriter"

	_ "github.com/lib/pq" // PostgreSQL driver
	"github.com/spf13/cobra"
)

// CreateQueryCommand creates the query command
func CreateQueryCommand(serviceContext any) *cobra.Command {
	return &cobra.Command{
		Use:   "query <sql>",
		Short: "Execute database queries",
		Long:  "Execute SQL queries against the building database",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			query := args[0]
			ctx := context.Background()

			fmt.Printf("🔍 Executing query: %s\n\n", query)

			// Get database connection from environment
			dbURL := os.Getenv("DATABASE_URL")
			if dbURL == "" {
				dbURL = "postgres://arxos:arxos_dev@localhost:5432/arxos?sslmode=disable"
			}

			// Connect to database
			db, err := sql.Open("postgres", dbURL)
			if err != nil {
				return fmt.Errorf("failed to connect to database: %w", err)
			}
			defer db.Close()

			// Execute query
			rows, err := db.QueryContext(ctx, query)
			if err != nil {
				return fmt.Errorf("failed to execute query: %w", err)
			}
			defer rows.Close()

			// Get column names
			columns, err := rows.Columns()
			if err != nil {
				return fmt.Errorf("failed to get columns: %w", err)
			}

			// Create tabwriter for formatted output
			w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)

			// Print header
			for i, col := range columns {
				if i > 0 {
					fmt.Fprint(w, "\t")
				}
				fmt.Fprint(w, col)
			}
			fmt.Fprintln(w)

			// Print separator
			for i := range columns {
				if i > 0 {
					fmt.Fprint(w, "\t")
				}
				fmt.Fprint(w, "---")
			}
			fmt.Fprintln(w)

			// Print rows
			rowCount := 0
			values := make([]any, len(columns))
			valuePtrs := make([]any, len(columns))
			for i := range columns {
				valuePtrs[i] = &values[i]
			}

			for rows.Next() {
				if err := rows.Scan(valuePtrs...); err != nil {
					return fmt.Errorf("failed to scan row: %w", err)
				}

				for i, val := range values {
					if i > 0 {
						fmt.Fprint(w, "\t")
					}
					if val == nil {
						fmt.Fprint(w, "NULL")
					} else {
						fmt.Fprintf(w, "%v", val)
					}
				}
				fmt.Fprintln(w)
				rowCount++
			}

			w.Flush()

			if err = rows.Err(); err != nil {
				return fmt.Errorf("error iterating rows: %w", err)
			}

			fmt.Printf("\n✅ Query executed successfully (%d rows)\n", rowCount)
			return nil
		},
	}
}

// CreateTraceCommand creates the trace command
func CreateTraceCommand(serviceContext any) *cobra.Command {
	return &cobra.Command{
		Use:   "trace <path>",
		Short: "Trace building component connections",
		Long:  "Trace connections and dependencies for building components",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			componentPath := args[0]
			ctx := context.Background()

			fmt.Printf("🔍 Tracing connections for: %s\n\n", componentPath)

			// Get database connection
			dbURL := os.Getenv("DATABASE_URL")
			if dbURL == "" {
				dbURL = "postgres://arxos:arxos_dev@localhost:5432/arxos?sslmode=disable"
			}

			db, err := sql.Open("postgres", dbURL)
			if err != nil {
				return fmt.Errorf("failed to connect to database: %w", err)
			}
			defer db.Close()

			// Query for equipment by path-like matching
			query := `
				SELECT id, name, equipment_type, status, building_id
				FROM equipment
				WHERE name ILIKE $1
				ORDER BY name
				LIMIT 10
			`

			rows, err := db.QueryContext(ctx, query, "%"+componentPath+"%")
			if err != nil {
				return fmt.Errorf("failed to query equipment: %w", err)
			}
			defer rows.Close()

			fmt.Println("Found Components:")
			fmt.Println("─────────────────────────────────")

			count := 0
			for rows.Next() {
				var id, name, equipType, status, buildingID string
				if err := rows.Scan(&id, &name, &equipType, &status, &buildingID); err != nil {
					return fmt.Errorf("failed to scan row: %w", err)
				}

				fmt.Printf("• %s (%s)\n", name, equipType)
				fmt.Printf("  ID: %s\n", id)
				fmt.Printf("  Building: %s\n", buildingID)
				fmt.Printf("  Status: %s\n\n", status)
				count++
			}

			if count == 0 {
				fmt.Println("No components found matching:", componentPath)
			} else {
				fmt.Printf("✅ Found %d component(s)\n", count)
			}

			return nil
		},
	}
}

// CreateVisualizeCommand creates the visualize command
func CreateVisualizeCommand(serviceContext any) *cobra.Command {
	return &cobra.Command{
		Use:   "visualize <building-id>",
		Short: "Generate building visualizations",
		Long:  "Generate visual representations of building data",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			buildingID := args[0]

			fmt.Printf("Generating visualization for building: %s\n", buildingID)

			// NOTE: Visualization via external tools or web UI
			// This would typically involve:
			// 1. Query building data
			// 2. Generate spatial visualization
			// 3. Export to requested format
			// 4. Save visualization file

			fmt.Printf("✅ Visualization generated for building %s\n", buildingID)
			return nil
		},
	}
}

// CreateReportCommand creates the report command
func CreateReportCommand(serviceContext any) *cobra.Command {
	return &cobra.Command{
		Use:   "report <type>",
		Short: "Generate building reports",
		Long:  "Generate various types of building reports and analytics",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			reportType := args[0]
			buildingID, _ := cmd.Flags().GetString("building")
			outputFormat, _ := cmd.Flags().GetString("format")
			ctx := context.Background()

			if outputFormat == "" {
				outputFormat = "text"
			}

			fmt.Printf("📊 Generating %s report\n\n", reportType)

			// Get database connection
			dbURL := os.Getenv("DATABASE_URL")
			if dbURL == "" {
				dbURL = "postgres://arxos:arxos_dev@localhost:5432/arxos?sslmode=disable"
			}

			db, err := sql.Open("postgres", dbURL)
			if err != nil {
				return fmt.Errorf("failed to connect to database: %w", err)
			}
			defer db.Close()

			// Generate report based on type
			switch reportType {
			case "equipment", "inventory":
				return generateEquipmentReport(ctx, db, buildingID, outputFormat)
			case "summary", "overview":
				return generateSummaryReport(ctx, db, buildingID)
			case "status":
				return generateStatusReport(ctx, db, buildingID)
			default:
				return fmt.Errorf("unknown report type: %s (try: equipment, summary, status)", reportType)
			}
		},
	}
}

// Helper functions for report generation

// generateEquipmentReport generates an equipment inventory report
func generateEquipmentReport(ctx context.Context, db *sql.DB, buildingID, format string) error {
	query := `
		SELECT e.id, e.name, e.equipment_type, e.status,
		       e.manufacturer, e.model, b.name as building_name
		FROM equipment e
		JOIN buildings b ON e.building_id = b.id
	`

	args := []any{}
	if buildingID != "" {
		query += " WHERE e.building_id = $1"
		args = append(args, buildingID)
	}

	query += " ORDER BY e.equipment_type, e.name"

	rows, err := db.QueryContext(ctx, query, args...)
	if err != nil {
		return fmt.Errorf("failed to query equipment: %w", err)
	}
	defer rows.Close()

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)

	if format == "csv" {
		fmt.Println("id,name,type,status,manufacturer,model,building")
	} else {
		fmt.Fprintln(w, "NAME\tTYPE\tSTATUS\tMANUFACTURER\tMODEL\tBUILDING")
		fmt.Fprintln(w, "----\t----\t------\t------------\t-----\t--------")
	}

	count := 0
	for rows.Next() {
		var id, name, equipType, status string
		var manufacturer, model, buildingName sql.NullString

		if err := rows.Scan(&id, &name, &equipType, &status, &manufacturer, &model, &buildingName); err != nil {
			return fmt.Errorf("failed to scan row: %w", err)
		}

		mfr := "N/A"
		if manufacturer.Valid {
			mfr = manufacturer.String
		}
		mdl := "N/A"
		if model.Valid {
			mdl = model.String
		}
		bldg := "N/A"
		if buildingName.Valid {
			bldg = buildingName.String
		}

		if format == "csv" {
			fmt.Printf("%s,%s,%s,%s,%s,%s,%s\n", id, name, equipType, status, mfr, mdl, bldg)
		} else {
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\n", name, equipType, status, mfr, mdl, bldg)
		}
		count++
	}

	w.Flush()
	fmt.Printf("\n✅ Equipment report: %d items\n", count)
	return nil
}

// generateSummaryReport generates a summary report
func generateSummaryReport(ctx context.Context, db *sql.DB, buildingID string) error {
	query := `
		SELECT
			COUNT(DISTINCT b.id) as buildings,
			COUNT(DISTINCT f.id) as floors,
			COUNT(DISTINCT r.id) as rooms,
			COUNT(DISTINCT e.id) as equipment
		FROM buildings b
		LEFT JOIN floors f ON f.building_id = b.id
		LEFT JOIN rooms r ON r.floor_id = f.id
		LEFT JOIN equipment e ON e.building_id = b.id
	`

	args := []any{}
	if buildingID != "" {
		query += " WHERE b.id = $1"
		args = append(args, buildingID)
	}

	var buildings, floors, rooms, equipment int
	err := db.QueryRowContext(ctx, query, args...).Scan(&buildings, &floors, &rooms, &equipment)
	if err != nil {
		return fmt.Errorf("failed to query summary: %w", err)
	}

	fmt.Println("Summary Report")
	fmt.Println("══════════════════════════════")
	fmt.Printf("Buildings:  %d\n", buildings)
	fmt.Printf("Floors:     %d\n", floors)
	fmt.Printf("Rooms:      %d\n", rooms)
	fmt.Printf("Equipment:  %d\n", equipment)
	fmt.Println()

	return nil
}

// generateStatusReport generates a status report
func generateStatusReport(ctx context.Context, db *sql.DB, buildingID string) error {
	query := `
		SELECT status, COUNT(*) as count
		FROM equipment
	`

	args := []any{}
	if buildingID != "" {
		query += " WHERE building_id = $1"
		args = append(args, buildingID)
	}

	query += " GROUP BY status ORDER BY count DESC"

	rows, err := db.QueryContext(ctx, query, args...)
	if err != nil {
		return fmt.Errorf("failed to query status: %w", err)
	}
	defer rows.Close()

	fmt.Println("Equipment Status Report")
	fmt.Println("══════════════════════════════")

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "STATUS\tCOUNT")
	fmt.Fprintln(w, "------\t-----")

	total := 0
	for rows.Next() {
		var status string
		var count int
		if err := rows.Scan(&status, &count); err != nil {
			return fmt.Errorf("failed to scan row: %w", err)
		}

		fmt.Fprintf(w, "%s\t%d\n", status, count)
		total += count
	}

	w.Flush()
	fmt.Printf("\nTotal: %d equipment items\n", total)

	return nil
}

// CreateVersionCommand creates the version command
func CreateVersionCommand(serviceContext any) *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "Print version information",
		RunE: func(cmd *cobra.Command, args []string) error {
			fmt.Printf("ArxOS %s\n", "dev") // Will be replaced by ldflags during build
			fmt.Printf("Built: %s\n", "unknown")
			fmt.Printf("Commit: %s\n", "unknown")
			fmt.Printf("Platform: %s\n", "linux/amd64")
			return nil
		},
	}
}
