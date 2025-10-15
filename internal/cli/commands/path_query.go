package commands

import (
	"context"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/spf13/cobra"
)

// CreatePathGetCommand creates the path-based get command
// Usage: arx get /B1/3/301/HVAC/VAV-301
//        arx get /B1/3/*/HVAC/*
func CreatePathGetCommand() *cobra.Command {
	var (
		verbose bool
		format  string
	)

	cmd := &cobra.Command{
		Use:   "get <path-pattern>",
		Short: "Get equipment by path",
		Long: `Get equipment using universal path notation.
Supports exact paths and wildcard patterns.

Path format: /BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT

Examples:
  Exact match:     /B1/3/301/HVAC/VAV-301
  With wildcards:  /B1/3/*/HVAC/*
  Any floor:       /B1/*/NETWORK/SW-*
  All fire safety: /*/*/SAFETY/EXTING-*`,
		Example: `  # Get specific equipment
  arx get /B1/3/301/HVAC/VAV-301

  # Get all HVAC on floor 3
  arx get /B1/3/*/HVAC/*

  # Get all network switches
  arx get /B1/*/NETWORK/SW-*

  # Get all fire extinguishers
  arx get /*/*/SAFETY/EXTING-*`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			pathPattern := args[0]

			// Validate path starts with /
			if !strings.HasPrefix(pathPattern, "/") {
				return fmt.Errorf("path must start with / (e.g., /B1/3/301/HVAC/VAV-301)")
			}

			// Get container from context
			container, ok := cmd.Context().Value("container").(*app.Container)
			if !ok {
				return fmt.Errorf("service container not available")
			}

			equipmentRepo := container.GetEquipmentRepository()
			if equipmentRepo == nil {
				return fmt.Errorf("equipment repository not available")
			}

			// Check if pattern contains wildcards
			hasWildcard := strings.Contains(pathPattern, "*")

			if hasWildcard {
				// Find by pattern
				equipment, err := equipmentRepo.FindByPath(ctx, pathPattern)
				if err != nil {
					return fmt.Errorf("failed to query equipment: %w", err)
				}

				if len(equipment) == 0 {
					fmt.Printf("No equipment found matching pattern: %s\n", pathPattern)
					return nil
				}

				// Display results
				if format == "table" || format == "" {
					displayEquipmentTable(equipment, verbose)
				} else if format == "list" {
					displayEquipmentList(equipment, verbose)
				} else {
					return fmt.Errorf("unsupported format: %s (use 'table' or 'list')", format)
				}

				fmt.Printf("\nFound %d equipment matching pattern: %s\n", len(equipment), pathPattern)
			} else {
				// Get by exact path
				eq, err := equipmentRepo.GetByPath(ctx, pathPattern)
				if err != nil {
					if strings.Contains(err.Error(), "not found") {
						return fmt.Errorf("equipment not found at path: %s", pathPattern)
					}
					return fmt.Errorf("failed to get equipment: %w", err)
				}

				// Display single equipment details
				displayEquipmentDetails(eq, verbose)
			}

			return nil
		},
	}

	cmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Show detailed information")
	cmd.Flags().StringVarP(&format, "format", "f", "table", "Output format: table, list")

	return cmd
}

// displayEquipmentTable displays equipment in table format
func displayEquipmentTable(equipment []*domain.Equipment, verbose bool) {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	defer w.Flush()

	// Header
	if verbose {
		fmt.Fprintln(w, "PATH\tNAME\tTYPE\tSTATUS\tLOCATION")
		fmt.Fprintln(w, "────\t────\t────\t──────\t────────")
	} else {
		fmt.Fprintln(w, "PATH\tNAME\tTYPE\tSTATUS")
		fmt.Fprintln(w, "────\t────\t────\t──────")
	}

	// Rows
	for _, eq := range equipment {
		path := eq.Path
		if path == "" {
			path = "(no path)"
		}

		if verbose {
			location := "-"
			if eq.Location != nil {
				location = fmt.Sprintf("(%.1f, %.1f, %.1f)", eq.Location.X, eq.Location.Y, eq.Location.Z)
			}
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\n",
				path, eq.Name, eq.Type, eq.Status, location)
		} else {
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
				path, eq.Name, eq.Type, eq.Status)
		}
	}
}

// displayEquipmentList displays equipment in simple list format
func displayEquipmentList(equipment []*domain.Equipment, verbose bool) {
	for _, eq := range equipment {
		path := eq.Path
		if path == "" {
			path = "(no path)"
		}

		if verbose {
			fmt.Printf("%s\n", path)
			fmt.Printf("  Name:     %s\n", eq.Name)
			fmt.Printf("  Type:     %s\n", eq.Type)
			fmt.Printf("  Status:   %s\n", eq.Status)
			if eq.Location != nil {
				fmt.Printf("  Location: (%.2f, %.2f, %.2f)\n", eq.Location.X, eq.Location.Y, eq.Location.Z)
			}
			fmt.Println()
		} else {
			fmt.Printf("%s - %s (%s)\n", path, eq.Name, eq.Type)
		}
	}
}

// displayEquipmentDetails displays detailed information for a single equipment
func displayEquipmentDetails(eq *domain.Equipment, verbose bool) {
	fmt.Printf("Equipment Details:\n\n")
	
	if eq.Path != "" {
		fmt.Printf("   Path:     %s\n", eq.Path)
	}
	fmt.Printf("   ID:       %s\n", eq.ID.String())
	fmt.Printf("   Name:     %s\n", eq.Name)
	fmt.Printf("   Type:     %s\n", eq.Type)
	
	if eq.Category != "" {
		fmt.Printf("   Category: %s\n", eq.Category)
	}
	if eq.Model != "" {
		fmt.Printf("   Model:    %s\n", eq.Model)
	}
	
	fmt.Printf("   Status:   %s\n", eq.Status)
	fmt.Printf("   Building: %s\n", eq.BuildingID.String())

	if !eq.FloorID.IsEmpty() {
		fmt.Printf("   Floor:    %s\n", eq.FloorID.String())
	}
	if !eq.RoomID.IsEmpty() {
		fmt.Printf("   Room:     %s\n", eq.RoomID.String())
	}

	if eq.Location != nil {
		fmt.Printf("   Location: (%.2f, %.2f, %.2f)\n",
			eq.Location.X, eq.Location.Y, eq.Location.Z)
	}

	if verbose {
		fmt.Printf("\n   Created:  %s\n", eq.CreatedAt.Format("2006-01-02 15:04:05"))
		fmt.Printf("   Updated:  %s\n", eq.UpdatedAt.Format("2006-01-02 15:04:05"))
	}

	fmt.Printf("\n")
}

// CreatePathQueryCommand creates a query command with path patterns and filters
// Usage: arx query /B1/3/*/HVAC/* --status active
func CreatePathQueryCommand() *cobra.Command {
	var (
		status    string
		eqType    string
		building  string
		verbose   bool
		format    string
		limit     int
	)

	cmd := &cobra.Command{
		Use:   "query",
		Short: "Query equipment with filters",
		Long: `Query equipment using path patterns and additional filters.
Combines the power of path-based queries with status, type, and location filters.

Path format: /BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT

Supports wildcards in paths and additional filtering by status, type, etc.`,
		Example: `  # Query all HVAC on floor 3 that needs maintenance
  arx query --path "/B1/3/*/HVAC/*" --status maintenance

  # Query all network equipment
  arx query --path "/B1/*/NETWORK/*"

  # Query by type across all buildings
  arx query --type hvac --status active

  # Query specific building
  arx query --building <id> --type network`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get path pattern from args if provided
			pathPattern := ""
			if len(args) > 0 {
				pathPattern = args[0]
			} else {
				// Use flags to build query
				pathPattern, _ = cmd.Flags().GetString("path")
			}

			// Get container from context
			container, ok := cmd.Context().Value("container").(*app.Container)
			if !ok {
				return fmt.Errorf("service container not available")
			}

			equipmentRepo := container.GetEquipmentRepository()
			if equipmentRepo == nil {
				return fmt.Errorf("equipment repository not available")
			}

			var equipment []*domain.Equipment
			var err error

			// If path pattern provided, use path-based query
			if pathPattern != "" && strings.HasPrefix(pathPattern, "/") {
				equipment, err = equipmentRepo.FindByPath(ctx, pathPattern)
				if err != nil {
					return fmt.Errorf("failed to query by path: %w", err)
				}
			} else {
				// Use filter-based query
				filter := &domain.EquipmentFilter{
					Limit: limit,
				}

				if building != "" {
					bID := types.FromString(building)
					filter.BuildingID = &bID
				}
				if eqType != "" {
					filter.Type = &eqType
				}
				if status != "" {
					filter.Status = &status
				}

				equipment, err = equipmentRepo.List(ctx, filter)
				if err != nil {
					return fmt.Errorf("failed to query equipment: %w", err)
				}
			}

			// Filter results by additional criteria if specified
			if status != "" {
				filtered := make([]*domain.Equipment, 0)
				for _, eq := range equipment {
					if eq.Status == status {
						filtered = append(filtered, eq)
					}
				}
				equipment = filtered
			}

			if eqType != "" {
				filtered := make([]*domain.Equipment, 0)
				for _, eq := range equipment {
					if eq.Type == eqType {
						filtered = append(filtered, eq)
					}
				}
				equipment = filtered
			}

			if len(equipment) == 0 {
				fmt.Println("No equipment found matching query criteria")
				return nil
			}

			// Display results
			if format == "table" || format == "" {
				displayEquipmentTable(equipment, verbose)
			} else if format == "list" {
				displayEquipmentList(equipment, verbose)
			} else {
				return fmt.Errorf("unsupported format: %s (use 'table' or 'list')", format)
			}

			fmt.Printf("\nFound %d equipment\n", len(equipment))
			return nil
		},
	}

	cmd.Flags().StringP("path", "p", "", "Path pattern (e.g., /B1/3/*/HVAC/*)")
	cmd.Flags().StringP("status", "s", "", "Filter by status (active, maintenance, failed)")
	cmd.Flags().StringP("type", "t", "", "Filter by equipment type")
	cmd.Flags().StringP("building", "b", "", "Filter by building ID")
	cmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Show detailed information")
	cmd.Flags().StringVarP(&format, "format", "f", "table", "Output format: table, list")
	cmd.Flags().IntVarP(&limit, "limit", "l", 100, "Maximum number of results")

	return cmd
}

