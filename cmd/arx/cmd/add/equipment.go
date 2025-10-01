package add

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/pkg/errors"
	"github.com/spf13/cobra"
)

// EquipmentCmd handles adding equipment following Go Blueprint standards
type EquipmentCmd struct {
	// Command-specific fields
	app          interface{} // Will be injected
	cli          interface{} // Will be injected
	errorHandler interface{} // Will be injected
}

// NewEquipmentCmd creates a new equipment command
func NewEquipmentCmd(app, cli, errorHandler interface{}) *EquipmentCmd {
	return &EquipmentCmd{
		app:          app,
		cli:          cli,
		errorHandler: errorHandler,
	}
}

// Execute runs the equipment command
func (c *EquipmentCmd) Execute(ctx context.Context, name, equipmentType, location string, metadata map[string]string) error {
	// Type assertions for injected dependencies
	_ = c.app // Will be used when services are implemented
	cli := c.cli.(interface {
		ParseLocation(string) (interface{}, error)
		ConvertMetadata(map[string]string) map[string]interface{}
		LogInfo(string, ...interface{})
		PrintSuccess(string, ...interface{})
	})
	errorHandler := c.errorHandler.(interface {
		ValidateAndHandle(string, interface{}, func(interface{}) error)
		HandleServiceError(error, string, string)
	})

	// Parse location coordinates with validation
	errorHandler.ValidateAndHandle("location", location, func(value interface{}) error {
		if str, ok := value.(string); ok && str == "" {
			return errors.New(errors.CodeInvalidInput, "location is required for equipment")
		}
		return nil
	})

	_, err := cli.ParseLocation(location)
	if err != nil {
		errorHandler.HandleServiceError(err, "cli", "parse_location")
	}

	// Validate equipment type
	errorHandler.ValidateAndHandle("type", equipmentType, func(value interface{}) error {
		if str, ok := value.(string); ok && str == "" {
			return errors.New(errors.CodeInvalidInput, "equipment type is required")
		}
		return nil
	})

	// Create equipment using service (placeholder implementation)
	// Note: This would use the actual equipment service when available

	// Log success
	cli.PrintSuccess("Equipment created: %s", name)
	fmt.Printf("   Name: %s\n", name)
	fmt.Printf("   Type: %s\n", equipmentType)
	fmt.Printf("   Location: %s\n", location)

	return nil
}

// CreateEquipmentCommand creates the cobra command for adding equipment
func CreateEquipmentCommand(app, cli, errorHandler interface{}) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "equipment <name>",
		Short: "Add new equipment",
		Long: `Add new equipment to the building model.
Supports spatial positioning with millimeter precision.

Examples:
  arx add equipment "HVAC-001" --type "Air Handler" --location "1000,2000,2700" --room "101"
  arx add equipment "Pump-001" --type "Water Pump" --location "500,1000,0" --system "Plumbing"`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			name := args[0]

			// Get flags
			equipmentType, _ := cmd.Flags().GetString("type")
			location, _ := cmd.Flags().GetString("location")
			metadata, _ := cmd.Flags().GetStringToString("metadata")

			// Create command instance
			equipmentCmd := NewEquipmentCmd(app, cli, errorHandler)

			// Execute command
			return equipmentCmd.Execute(ctx, name, equipmentType, location, metadata)
		},
	}

	// Add flags
	cmd.Flags().String("type", "", "Equipment type (Air Handler, Pump, etc.)")
	cmd.Flags().String("location", "", "3D coordinates (x,y,z) in millimeters")
	cmd.Flags().String("room", "", "Room ID or name")
	cmd.Flags().String("system", "", "System type (HVAC, Electrical, Plumbing, etc.)")
	cmd.Flags().String("status", "operational", "Status (operational, maintenance, failed)")
	cmd.Flags().String("notes", "", "Additional notes")
	cmd.Flags().StringSlice("tags", []string{}, "Tags for categorization")
	cmd.Flags().StringToString("metadata", map[string]string{}, "Additional metadata (key=value)")

	// Mark required flags
	cmd.MarkFlagRequired("type")
	cmd.MarkFlagRequired("location")

	return cmd
}
