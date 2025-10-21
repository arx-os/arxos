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

// EquipmentServiceProvider provides access to equipment services
type EquipmentServiceProvider interface {
	GetEquipmentUseCase() *building.EquipmentUseCase
}

// CreateEquipmentCommands creates equipment management commands
func CreateEquipmentCommands(serviceContext any) *cobra.Command {
	equipmentCmd := &cobra.Command{
		Use:   "equipment",
		Short: "Manage building equipment",
		Long:  `Create, list, get, update, and delete equipment in buildings`,
	}

	equipmentCmd.AddCommand(createEquipmentCreateCommand(serviceContext))
	equipmentCmd.AddCommand(createEquipmentListCommand(serviceContext))
	equipmentCmd.AddCommand(createEquipmentGetCommand(serviceContext))
	equipmentCmd.AddCommand(createEquipmentUpdateCommand(serviceContext))
	equipmentCmd.AddCommand(createEquipmentDeleteCommand(serviceContext))
	equipmentCmd.AddCommand(createEquipmentMoveCommand(serviceContext))

	return equipmentCmd
}

// createEquipmentCreateCommand creates the equipment create command
func createEquipmentCreateCommand(serviceContext any) *cobra.Command {
	var (
		name       string
		eqType     string
		model      string
		buildingID string
		floorID    string
		roomID     string
		x          float64
		y          float64
		z          float64
	)

	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create new equipment",
		Long:  "Create new equipment in a building with specified type and location",
		Example: `  # Create HVAC equipment
  arx equipment create --name "HVAC-01" --type hvac --building abc123

  # Create equipment with location
  arx equipment create --name "Light-A1" --type lighting \
    --building abc123 --floor def456 --room ghi789 \
    --x 10.5 --y 20.3 --z 3.0`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get service from context
			sc, ok := serviceContext.(EquipmentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			equipmentUC := sc.GetEquipmentUseCase()

			// Validate required fields
			if name == "" {
				return fmt.Errorf("equipment name is required (--name)")
			}
			if eqType == "" {
				return fmt.Errorf("equipment type is required (--type)")
			}
			if buildingID == "" {
				return fmt.Errorf("building ID is required (--building)")
			}

			// Create request
			req := &domain.CreateEquipmentRequest{
				BuildingID: types.FromString(buildingID),
				Name:       name,
				Type:       eqType,
				Model:      model,
			}

			// Add optional floor and room
			if floorID != "" {
				req.FloorID = types.FromString(floorID)
			}
			if roomID != "" {
				req.RoomID = types.FromString(roomID)
			}

			// Add location if coordinates provided
			if x != 0 || y != 0 || z != 0 {
				req.Location = &domain.Location{
					X: x,
					Y: y,
					Z: z,
				}
			}

			// Create equipment
			equipment, err := equipmentUC.CreateEquipment(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to create equipment: %w", err)
			}

			// Print success
			fmt.Printf("✅ Equipment created successfully!\n\n")
			fmt.Printf("   ID:       %s\n", equipment.ID.String())
			fmt.Printf("   Name:     %s\n", equipment.Name)
			fmt.Printf("   Type:     %s\n", equipment.Type)
			if equipment.Path != "" {
				fmt.Printf("   Path:     %s  🎯 (Auto-generated)\n", equipment.Path)
			}
			if equipment.Model != "" {
				fmt.Printf("   Model:    %s\n", equipment.Model)
			}
			fmt.Printf("   Building: %s\n", equipment.BuildingID.String())
			if !equipment.FloorID.IsEmpty() {
				fmt.Printf("   Floor:    %s\n", equipment.FloorID.String())
			}
			if !equipment.RoomID.IsEmpty() {
				fmt.Printf("   Room:     %s\n", equipment.RoomID.String())
			}
			if equipment.Location != nil {
				fmt.Printf("   Location: (%.2f, %.2f, %.2f)\n", equipment.Location.X, equipment.Location.Y, equipment.Location.Z)
			}
			fmt.Printf("   Status:   %s\n", equipment.Status)
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&name, "name", "n", "", "Equipment name (required)")
	cmd.Flags().StringVarP(&eqType, "type", "t", "", "Equipment type: hvac, electrical, plumbing, security, fire_safety, elevator, lighting (required)")
	cmd.Flags().StringVar(&model, "model", "", "Equipment model (optional)")
	cmd.Flags().StringVarP(&buildingID, "building", "b", "", "Building ID (required)")
	cmd.Flags().StringVar(&floorID, "floor", "", "Floor ID (optional)")
	cmd.Flags().StringVar(&roomID, "room", "", "Room ID (optional)")
	cmd.Flags().Float64Var(&x, "x", 0, "X coordinate (optional)")
	cmd.Flags().Float64Var(&y, "y", 0, "Y coordinate (optional)")
	cmd.Flags().Float64Var(&z, "z", 0, "Z coordinate/altitude (optional)")

	cmd.MarkFlagRequired("name")
	cmd.MarkFlagRequired("type")
	cmd.MarkFlagRequired("building")

	return cmd
}

// createEquipmentListCommand creates the equipment list command
func createEquipmentListCommand(serviceContext any) *cobra.Command {
	var (
		limit      int
		offset     int
		buildingID string
		eqType     string
		status     string
	)

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List equipment",
		Long:  "List equipment with optional filtering by building, type, or status",
		Example: `  # List all equipment
  arx equipment list

  # List equipment in a specific building
  arx equipment list --building abc123

  # Filter by type
  arx equipment list --type hvac

  # Filter by status
  arx equipment list --status operational`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get service from context
			sc, ok := serviceContext.(EquipmentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			equipmentUC := sc.GetEquipmentUseCase()

			// Create filter
			filter := &domain.EquipmentFilter{
				Limit:  limit,
				Offset: offset,
			}
			if buildingID != "" {
				bID := types.FromString(buildingID)
				filter.BuildingID = &bID
			}
			if eqType != "" {
				filter.Type = &eqType
			}
			if status != "" {
				filter.Status = &status
			}

			// List equipment
			equipment, err := equipmentUC.ListEquipment(ctx, filter)
			if err != nil {
				return fmt.Errorf("failed to list equipment: %w", err)
			}

			if len(equipment) == 0 {
				fmt.Println("No equipment found.")
				return nil
			}

			// Print results in table format
			w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
			fmt.Fprintf(w, "ID\tNAME\tTYPE\tSTATUS\tBUILDING\n")
			fmt.Fprintf(w, "--\t----\t----\t------\t--------\n")

			for _, eq := range equipment {
				fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\n",
					eq.ID.String()[:8]+"...",
					eq.Name,
					eq.Type,
					eq.Status,
					eq.BuildingID.String()[:8]+"...",
				)
			}
			w.Flush()

			fmt.Printf("\n%d equipment item(s) found (showing %d-%d)\n", len(equipment), offset+1, offset+len(equipment))

			return nil
		},
	}

	// Add flags
	cmd.Flags().IntVarP(&limit, "limit", "l", 100, "Maximum number of results")
	cmd.Flags().IntVarP(&offset, "offset", "o", 0, "Offset for pagination")
	cmd.Flags().StringVarP(&buildingID, "building", "b", "", "Filter by building ID")
	cmd.Flags().StringVarP(&eqType, "type", "t", "", "Filter by equipment type")
	cmd.Flags().StringVar(&status, "status", "", "Filter by status (operational, maintenance, failed, inactive)")

	return cmd
}

// createEquipmentGetCommand creates the equipment get command
func createEquipmentGetCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get <equipment-id>",
		Short: "Get equipment details",
		Long:  "Get detailed information about specific equipment by ID",
		Example: `  # Get equipment details
  arx equipment get abc123def456`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			equipmentID := args[0]

			// Get service from context
			sc, ok := serviceContext.(EquipmentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			equipmentUC := sc.GetEquipmentUseCase()

			// Get equipment
			equipment, err := equipmentUC.GetEquipment(ctx, equipmentID)
			if err != nil {
				return fmt.Errorf("failed to get equipment: %w", err)
			}

			// Print equipment details
			fmt.Printf("Equipment Details:\n\n")
			fmt.Printf("   ID:       %s\n", equipment.ID.String())
			fmt.Printf("   Name:     %s\n", equipment.Name)
			fmt.Printf("   Type:     %s\n", equipment.Type)
			if equipment.Model != "" {
				fmt.Printf("   Model:    %s\n", equipment.Model)
			}
			fmt.Printf("   Status:   %s\n", equipment.Status)
			fmt.Printf("   Building: %s\n", equipment.BuildingID.String())

			if !equipment.FloorID.IsEmpty() {
				fmt.Printf("   Floor:    %s\n", equipment.FloorID.String())
			}
			if !equipment.RoomID.IsEmpty() {
				fmt.Printf("   Room:     %s\n", equipment.RoomID.String())
			}

			if equipment.Location != nil {
				fmt.Printf("   Location: (%.2f, %.2f, %.2f)\n",
					equipment.Location.X, equipment.Location.Y, equipment.Location.Z)
			}

			fmt.Printf("   Created:  %s\n", equipment.CreatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("   Updated:  %s\n", equipment.UpdatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// createEquipmentUpdateCommand creates the equipment update command
func createEquipmentUpdateCommand(serviceContext any) *cobra.Command {
	var (
		name   string
		model  string
		status string
	)

	cmd := &cobra.Command{
		Use:   "update <equipment-id>",
		Short: "Update equipment",
		Long:  "Update equipment information (name, model, and/or status)",
		Example: `  # Update equipment name
  arx equipment update abc123 --name "New Name"

  # Update status
  arx equipment update abc123 --status maintenance

  # Update multiple fields
  arx equipment update abc123 --name "HVAC-02" --model "Model-XYZ" --status operational`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			equipmentID := args[0]

			// Validate at least one field is provided
			if name == "" && model == "" && status == "" {
				return fmt.Errorf("at least one field to update is required (--name, --model, or --status)")
			}

			// Get service from context
			sc, ok := serviceContext.(EquipmentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			equipmentUC := sc.GetEquipmentUseCase()

			// Create update request
			req := &domain.UpdateEquipmentRequest{
				ID: types.FromString(equipmentID),
			}
			if name != "" {
				req.Name = &name
			}
			if model != "" {
				req.Model = &model
			}
			if status != "" {
				req.Status = &status
			}

			// Update equipment
			equipment, err := equipmentUC.UpdateEquipment(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to update equipment: %w", err)
			}

			// Print success
			fmt.Printf("✅ Equipment updated successfully!\n\n")
			fmt.Printf("   ID:     %s\n", equipment.ID.String())
			fmt.Printf("   Name:   %s\n", equipment.Name)
			fmt.Printf("   Model:  %s\n", equipment.Model)
			fmt.Printf("   Status: %s\n", equipment.Status)
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&name, "name", "n", "", "New equipment name")
	cmd.Flags().StringVar(&model, "model", "", "New equipment model")
	cmd.Flags().StringVar(&status, "status", "", "New status (operational, maintenance, failed, inactive)")

	return cmd
}

// createEquipmentDeleteCommand creates the equipment delete command
func createEquipmentDeleteCommand(serviceContext any) *cobra.Command {
	var force bool

	cmd := &cobra.Command{
		Use:   "delete <equipment-id>",
		Short: "Delete equipment",
		Long:  "Delete equipment from the system (requires confirmation unless --force is used)",
		Example: `  # Delete with confirmation prompt
  arx equipment delete abc123

  # Delete without confirmation
  arx equipment delete abc123 --force`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			equipmentID := args[0]

			// Get service from context
			sc, ok := serviceContext.(EquipmentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			equipmentUC := sc.GetEquipmentUseCase()

			// Confirmation prompt unless --force
			if !force {
				fmt.Printf("⚠️  Are you sure you want to delete equipment %s? (yes/no): ", equipmentID)
				var response string
				fmt.Scanln(&response)
				if response != "yes" && response != "y" {
					fmt.Println("Deletion cancelled.")
					return nil
				}
			}

			// Delete equipment
			err := equipmentUC.DeleteEquipment(ctx, equipmentID)
			if err != nil {
				return fmt.Errorf("failed to delete equipment: %w", err)
			}

			// Print success
			fmt.Printf("✅ Equipment deleted successfully!\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().BoolVarP(&force, "force", "f", false, "Skip confirmation prompt")

	return cmd
}

// createEquipmentMoveCommand creates the equipment move command
func createEquipmentMoveCommand(serviceContext any) *cobra.Command {
	var (
		x float64
		y float64
		z float64
	)

	cmd := &cobra.Command{
		Use:   "move <equipment-id>",
		Short: "Move equipment to new location",
		Long:  "Update equipment location coordinates",
		Example: `  # Move equipment to new coordinates
  arx equipment move abc123 --x 15.5 --y 25.3 --z 4.0`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			equipmentID := args[0]

			// Validate at least one coordinate is provided
			if x == 0 && y == 0 && z == 0 {
				return fmt.Errorf("at least one coordinate is required (--x, --y, or --z)")
			}

			// Get service from context
			sc, ok := serviceContext.(EquipmentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			equipmentUC := sc.GetEquipmentUseCase()

			// Create new location
			newLocation := &domain.Location{
				X: x,
				Y: y,
				Z: z,
			}

			// Move equipment
			err := equipmentUC.MoveEquipment(ctx, equipmentID, newLocation)
			if err != nil {
				return fmt.Errorf("failed to move equipment: %w", err)
			}

			// Print success
			fmt.Printf("✅ Equipment moved successfully!\n\n")
			fmt.Printf("   New Location: (%.2f, %.2f, %.2f)\n", x, y, z)
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().Float64Var(&x, "x", 0, "X coordinate")
	cmd.Flags().Float64Var(&y, "y", 0, "Y coordinate")
	cmd.Flags().Float64Var(&z, "z", 0, "Z coordinate/altitude")

	return cmd
}
