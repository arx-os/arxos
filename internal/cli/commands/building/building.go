package building

import (
	"context"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase/building"
	"github.com/spf13/cobra"
)

// BuildingServiceProvider provides access to building services
type BuildingServiceProvider interface {
	GetBuildingUseCase() *building.BuildingUseCase
}

// CreateBuildingCommands creates building management commands
func CreateBuildingCommands(serviceContext any) *cobra.Command {
	buildingCmd := &cobra.Command{
		Use:   "building",
		Short: "Manage buildings",
		Long:  `Create, list, get, update, and delete buildings in the ArxOS system`,
	}

	buildingCmd.AddCommand(createBuildingCreateCommand(serviceContext))
	buildingCmd.AddCommand(createBuildingListCommand(serviceContext))
	buildingCmd.AddCommand(createBuildingGetCommand(serviceContext))
	buildingCmd.AddCommand(createBuildingUpdateCommand(serviceContext))
	buildingCmd.AddCommand(createBuildingDeleteCommand(serviceContext))

	return buildingCmd
}

// createBuildingCreateCommand creates the building create command
func createBuildingCreateCommand(serviceContext any) *cobra.Command {
	var (
		name    string
		address string
		lat     float64
		lon     float64
		alt     float64
	)

	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new building",
		Long:  "Create a new building with the specified name, address, and optional coordinates",
		Example: `  # Create a simple building
  arx building create --name "Main Office" --address "123 Main St, San Francisco, CA"

  # Create a building with GPS coordinates
  arx building create --name "Main Office" --address "123 Main St" --lat 37.7749 --lon -122.4194`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get service from context
			sc, ok := serviceContext.(BuildingServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			buildingUC := sc.GetBuildingUseCase()

			// Validate required fields
			if name == "" {
				return fmt.Errorf("building name is required (--name)")
			}
			if address == "" {
				return fmt.Errorf("building address is required (--address)")
			}

			// Create request
			req := &domain.CreateBuildingRequest{
				Name:    name,
				Address: address,
			}

			// Add coordinates if provided
			if lat != 0 || lon != 0 {
				req.Coordinates = &domain.Location{
					X: lon, // Longitude is X
					Y: lat, // Latitude is Y
					Z: alt, // Altitude
				}
			}

			// Create building
			building, err := buildingUC.CreateBuilding(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to create building: %w", err)
			}

			// Print success
			fmt.Printf("✅ Building created successfully!\n\n")
			fmt.Printf("   ID:      %s\n", building.ID.String())
			fmt.Printf("   Name:    %s\n", building.Name)
			fmt.Printf("   Address: %s\n", building.Address)
			if building.Coordinates != nil {
				fmt.Printf("   Location: %.6f°N, %.6f°E", building.Coordinates.Y, building.Coordinates.X)
				if building.Coordinates.Z != 0 {
					fmt.Printf(", %.1fm altitude", building.Coordinates.Z)
				}
				fmt.Printf("\n")
			}
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&name, "name", "n", "", "Building name (required)")
	cmd.Flags().StringVarP(&address, "address", "a", "", "Building address (required)")
	cmd.Flags().Float64Var(&lat, "lat", 0, "Latitude (optional)")
	cmd.Flags().Float64Var(&lon, "lon", 0, "Longitude (optional)")
	cmd.Flags().Float64Var(&alt, "alt", 0, "Altitude in meters (optional)")

	cmd.MarkFlagRequired("name")
	cmd.MarkFlagRequired("address")

	return cmd
}

// createBuildingListCommand creates the building list command
func createBuildingListCommand(serviceContext any) *cobra.Command {
	var (
		limit      int
		offset     int
		nameFilter string
	)

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List all buildings",
		Long:  "List all buildings in the system with optional filtering and pagination",
		Example: `  # List all buildings
  arx building list

  # List with pagination
  arx building list --limit 10 --offset 20

  # Filter by name
  arx building list --name "Office"`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get service from context
			sc, ok := serviceContext.(BuildingServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			buildingUC := sc.GetBuildingUseCase()

			// Create filter
			filter := &domain.BuildingFilter{
				Limit:  limit,
				Offset: offset,
			}
			if nameFilter != "" {
				filter.Name = &nameFilter
			}

			// List buildings
			buildings, err := buildingUC.ListBuildings(ctx, filter)
			if err != nil {
				return fmt.Errorf("failed to list buildings: %w", err)
			}

			if len(buildings) == 0 {
				fmt.Println("No buildings found.")
				return nil
			}

			// Print results in table format
			w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
			fmt.Fprintf(w, "ID\tNAME\tADDRESS\tCREATED\n")
			fmt.Fprintf(w, "--\t----\t-------\t-------\n")

			for _, building := range buildings {
				fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
					building.ID.String()[:8]+"...",
					building.Name,
					building.Address,
					building.CreatedAt.Format("2006-01-02"),
				)
			}
			w.Flush()

			fmt.Printf("\n%d building(s) found (showing %d-%d)\n", len(buildings), offset+1, offset+len(buildings))

			return nil
		},
	}

	// Add flags
	cmd.Flags().IntVarP(&limit, "limit", "l", 100, "Maximum number of results")
	cmd.Flags().IntVarP(&offset, "offset", "o", 0, "Offset for pagination")
	cmd.Flags().StringVar(&nameFilter, "name", "", "Filter by name (case-insensitive)")

	return cmd
}

// createBuildingGetCommand creates the building get command
func createBuildingGetCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get <building-id>",
		Short: "Get building details",
		Long:  "Get detailed information about a specific building by ID",
		Example: `  # Get building details
  arx building get abc123def456`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			buildingID := args[0]

			// Get service from context
			sc, ok := serviceContext.(BuildingServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			buildingUC := sc.GetBuildingUseCase()

			// Get building
			building, err := buildingUC.GetBuilding(ctx, types.FromString(buildingID))
			if err != nil {
				return fmt.Errorf("failed to get building: %w", err)
			}

			// Print building details
			fmt.Printf("Building Details:\n\n")
			fmt.Printf("   ID:         %s\n", building.ID.String())
			fmt.Printf("   Name:       %s\n", building.Name)
			fmt.Printf("   Address:    %s\n", building.Address)

			if building.Coordinates != nil {
				fmt.Printf("   Latitude:   %.6f°N\n", building.Coordinates.Y)
				fmt.Printf("   Longitude:  %.6f°E\n", building.Coordinates.X)
				if building.Coordinates.Z != 0 {
					fmt.Printf("   Altitude:   %.1fm\n", building.Coordinates.Z)
				}
			}

			fmt.Printf("   Created:    %s\n", building.CreatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("   Updated:    %s\n", building.UpdatedAt.Format("2006-01-02 15:04:05"))

			if len(building.Floors) > 0 {
				fmt.Printf("   Floors:     %d\n", len(building.Floors))
			}
			if len(building.Equipment) > 0 {
				fmt.Printf("   Equipment:  %d item(s)\n", len(building.Equipment))
			}

			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// createBuildingUpdateCommand creates the building update command
func createBuildingUpdateCommand(serviceContext any) *cobra.Command {
	var (
		name    string
		address string
	)

	cmd := &cobra.Command{
		Use:   "update <building-id>",
		Short: "Update a building",
		Long:  "Update building information (name and/or address)",
		Example: `  # Update building name
  arx building update abc123 --name "New Building Name"

  # Update address
  arx building update abc123 --address "456 New Address"

  # Update both
  arx building update abc123 --name "New Name" --address "New Address"`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			buildingID := args[0]

			// Validate at least one field is provided
			if name == "" && address == "" {
				return fmt.Errorf("at least one field to update is required (--name or --address)")
			}

			// Get service from context
			sc, ok := serviceContext.(BuildingServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			buildingUC := sc.GetBuildingUseCase()

			// Create update request
			req := &domain.UpdateBuildingRequest{
				ID: types.FromString(buildingID),
			}
			if name != "" {
				req.Name = &name
			}
			if address != "" {
				req.Address = &address
			}

			// Update building
			building, err := buildingUC.UpdateBuilding(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to update building: %w", err)
			}

			// Print success
			fmt.Printf("✅ Building updated successfully!\n\n")
			fmt.Printf("   ID:      %s\n", building.ID.String())
			fmt.Printf("   Name:    %s\n", building.Name)
			fmt.Printf("   Address: %s\n", building.Address)
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&name, "name", "n", "", "New building name")
	cmd.Flags().StringVarP(&address, "address", "a", "", "New building address")

	return cmd
}

// createBuildingDeleteCommand creates the building delete command
func createBuildingDeleteCommand(serviceContext any) *cobra.Command {
	var force bool

	cmd := &cobra.Command{
		Use:   "delete <building-id>",
		Short: "Delete a building",
		Long:  "Delete a building from the system (requires confirmation unless --force is used)",
		Example: `  # Delete with confirmation prompt
  arx building delete abc123

  # Delete without confirmation
  arx building delete abc123 --force`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			buildingID := args[0]

			// Get service from context
			sc, ok := serviceContext.(BuildingServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			buildingUC := sc.GetBuildingUseCase()

			// Confirmation prompt unless --force
			if !force {
				fmt.Printf("⚠️  Are you sure you want to delete building %s? (yes/no): ", buildingID)
				var response string
				fmt.Scanln(&response)
				if response != "yes" && response != "y" {
					fmt.Println("Deletion cancelled.")
					return nil
				}
			}

			// Delete building
			err := buildingUC.DeleteBuilding(ctx, buildingID)
			if err != nil {
				return fmt.Errorf("failed to delete building: %w", err)
			}

			// Print success
			fmt.Printf("✅ Building deleted successfully!\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().BoolVarP(&force, "force", "f", false, "Skip confirmation prompt")

	return cmd
}
