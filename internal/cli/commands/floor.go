package commands

import (
	"context"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/spf13/cobra"
)

// FloorServiceProvider provides access to floor services
type FloorServiceProvider interface {
	GetFloorUseCase() *usecase.FloorUseCase
}

// CreateFloorCommands creates floor management commands
func CreateFloorCommands(serviceContext any) *cobra.Command {
	floorCmd := &cobra.Command{
		Use:   "floor",
		Short: "Manage building floors",
		Long:  `Create, list, get, update, and delete floors in buildings`,
	}

	floorCmd.AddCommand(createFloorCreateCommand(serviceContext))
	floorCmd.AddCommand(createFloorListCommand(serviceContext))
	floorCmd.AddCommand(createFloorGetCommand(serviceContext))
	floorCmd.AddCommand(createFloorDeleteCommand(serviceContext))

	return floorCmd
}

// createFloorCreateCommand creates the floor create command
func createFloorCreateCommand(serviceContext any) *cobra.Command {
	var (
		name       string
		level      int
		buildingID string
	)

	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new floor",
		Long:  "Create a new floor in a building with specified level",
		Example: `  # Create ground floor
  arx floor create --building abc123 --name "Ground Floor" --level 0

  # Create second floor
  arx floor create --building abc123 --name "Second Floor" --level 2`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get service from context
			sc, ok := serviceContext.(FloorServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			floorUC := sc.GetFloorUseCase()

			// Validate required fields
			if name == "" {
				return fmt.Errorf("floor name is required (--name)")
			}
			if buildingID == "" {
				return fmt.Errorf("building ID is required (--building)")
			}

			// Create request
			req := &domain.CreateFloorRequest{
				BuildingID: types.FromString(buildingID),
				Name:       name,
				Level:      level,
			}

			// Create floor
			floor, err := floorUC.CreateFloor(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to create floor: %w", err)
			}

			// Print success
			fmt.Printf("✅ Floor created successfully!\n\n")
			fmt.Printf("   ID:       %s\n", floor.ID.String())
			fmt.Printf("   Name:     %s\n", floor.Name)
			fmt.Printf("   Level:    %d\n", floor.Level)
			fmt.Printf("   Building: %s\n", floor.BuildingID.String())
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&name, "name", "n", "", "Floor name (required)")
	cmd.Flags().IntVarP(&level, "level", "l", 0, "Floor level (0=ground, 1=first, etc.)")
	cmd.Flags().StringVarP(&buildingID, "building", "b", "", "Building ID (required)")

	cmd.MarkFlagRequired("name")
	cmd.MarkFlagRequired("building")

	return cmd
}

// createFloorListCommand creates the floor list command
func createFloorListCommand(serviceContext any) *cobra.Command {
	var (
		buildingID string
		limit      int
		offset     int
	)

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List floors",
		Long:  "List floors in a building",
		Example: `  # List all floors in a building
  arx floor list --building abc123`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Validate required fields
			if buildingID == "" {
				return fmt.Errorf("building ID is required (--building)")
			}

			// Get service from context
			sc, ok := serviceContext.(FloorServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			floorUC := sc.GetFloorUseCase()

			// List floors
			floors, err := floorUC.ListFloors(ctx, types.FromString(buildingID), limit, offset)
			if err != nil {
				return fmt.Errorf("failed to list floors: %w", err)
			}

			if len(floors) == 0 {
				fmt.Println("No floors found.")
				return nil
			}

			// Print results in table format
			w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
			fmt.Fprintf(w, "ID\tNAME\tLEVEL\tCREATED\n")
			fmt.Fprintf(w, "--\t----\t-----\t-------\n")

			for _, floor := range floors {
				fmt.Fprintf(w, "%s\t%s\t%d\t%s\n",
					floor.ID.String()[:8]+"...",
					floor.Name,
					floor.Level,
					floor.CreatedAt.Format("2006-01-02"),
				)
			}
			w.Flush()

			fmt.Printf("\n%d floor(s) found\n", len(floors))

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&buildingID, "building", "b", "", "Building ID (required)")
	cmd.Flags().IntVarP(&limit, "limit", "l", 100, "Maximum number of results")
	cmd.Flags().IntVarP(&offset, "offset", "o", 0, "Offset for pagination")

	cmd.MarkFlagRequired("building")

	return cmd
}

// createFloorGetCommand creates the floor get command
func createFloorGetCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get <floor-id>",
		Short: "Get floor details",
		Long:  "Get detailed information about a specific floor by ID",
		Example: `  # Get floor details
  arx floor get abc123def456`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			floorID := args[0]

			// Get service from context
			sc, ok := serviceContext.(FloorServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			floorUC := sc.GetFloorUseCase()

			// Get floor
			floor, err := floorUC.GetFloor(ctx, types.FromString(floorID))
			if err != nil {
				return fmt.Errorf("failed to get floor: %w", err)
			}

			// Print floor details
			fmt.Printf("Floor Details:\n\n")
			fmt.Printf("   ID:       %s\n", floor.ID.String())
			fmt.Printf("   Name:     %s\n", floor.Name)
			fmt.Printf("   Level:    %d\n", floor.Level)
			fmt.Printf("   Building: %s\n", floor.BuildingID.String())
			fmt.Printf("   Created:  %s\n", floor.CreatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("   Updated:  %s\n", floor.UpdatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// createFloorDeleteCommand creates the floor delete command
func createFloorDeleteCommand(serviceContext any) *cobra.Command {
	var force bool

	cmd := &cobra.Command{
		Use:   "delete <floor-id>",
		Short: "Delete a floor",
		Long:  "Delete a floor from the system (requires confirmation unless --force is used)",
		Example: `  # Delete with confirmation
  arx floor delete abc123

  # Delete without confirmation
  arx floor delete abc123 --force`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			floorID := args[0]

			// Get service from context
			sc, ok := serviceContext.(FloorServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			floorUC := sc.GetFloorUseCase()

			// Confirmation prompt unless --force
			if !force {
				fmt.Printf("⚠️  Are you sure you want to delete floor %s? (yes/no): ", floorID)
				var response string
				fmt.Scanln(&response)
				if response != "yes" && response != "y" {
					fmt.Println("Deletion cancelled.")
					return nil
				}
			}

			// Delete floor
			err := floorUC.DeleteFloor(ctx, floorID)
			if err != nil {
				return fmt.Errorf("failed to delete floor: %w", err)
			}

			// Print success
			fmt.Printf("✅ Floor deleted successfully!\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().BoolVarP(&force, "force", "f", false, "Skip confirmation prompt")

	return cmd
}
