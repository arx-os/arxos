package get

import (
	"context"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/pkg/errors"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/spf13/cobra"
)

// EquipmentCmd handles getting equipment following Go Blueprint standards
type EquipmentCmd struct {
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
func (c *EquipmentCmd) Execute(ctx context.Context, id string) error {
	// Type assertions for injected dependencies
	cli := c.cli.(interface {
		IsValidOutputFormat(string) bool
		LogInfo(string, ...interface{})
	})
	errorHandler := c.errorHandler.(interface {
		HandleValidationError(error, string, string)
	})

	// Validate output format
	format := "table" // Default format, would come from flags in real implementation
	if !cli.IsValidOutputFormat(format) {
		errorHandler.HandleValidationError(
			errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid output format: %s", format)),
			"format", format)
	}

	// cli.LogInfo("Getting equipment", "id", id) // Logging would be implemented

	// For now, create a placeholder equipment object
	// In a real implementation, this would use the service layer
	equipment := &models.Equipment{
		ID:     id,
		Name:   "Placeholder Equipment",
		Type:   "unknown",
		Status: "unknown",
		Notes:  "This is a placeholder - service not implemented yet",
	}

	// Display equipment information
	return c.displayEquipment(equipment, format)
}

// displayEquipment displays equipment information in the specified format
func (c *EquipmentCmd) displayEquipment(equipment *models.Equipment, format string) error {
	switch format {
	case "json":
		return c.displayEquipmentJSON(equipment)
	case "yaml":
		return c.displayEquipmentYAML(equipment)
	default:
		return c.displayEquipmentTable(equipment)
	}
}

// displayEquipmentTable displays equipment in table format
func (c *EquipmentCmd) displayEquipmentTable(equipment *models.Equipment) error {
	fmt.Printf("Equipment Details\n")
	fmt.Printf("================\n\n")

	// Basic information
	fmt.Printf("ID: %s\n", equipment.ID)
	fmt.Printf("Name: %s\n", equipment.Name)
	fmt.Printf("Type: %s\n", equipment.Type)
	fmt.Printf("Status: %s\n", equipment.Status)
	if equipment.RoomID != "" {
		fmt.Printf("Room: %s\n", equipment.RoomID)
	}
	if equipment.Notes != "" {
		fmt.Printf("Notes: %s\n", equipment.Notes)
	}

	// Spatial information
	if equipment.Location != nil {
		fmt.Printf("\nSpatial Information\n")
		fmt.Printf("------------------\n")
		fmt.Printf("Location: %s\n", equipment.Location.String())
	}

	// Tags and metadata
	if len(equipment.Tags) > 0 {
		fmt.Printf("\nTags: %s\n", strings.Join(equipment.Tags, ", "))
	}
	if len(equipment.Metadata) > 0 {
		fmt.Printf("\nMetadata:\n")
		for key, value := range equipment.Metadata {
			fmt.Printf("  %s: %s\n", key, value)
		}
	}

	return nil
}

// displayEquipmentJSON displays equipment in JSON format
func (c *EquipmentCmd) displayEquipmentJSON(equipment *models.Equipment) error {
	fmt.Printf("JSON output not implemented yet\n")
	fmt.Printf("Equipment ID: %s\n", equipment.ID)
	fmt.Printf("Equipment Name: %s\n", equipment.Name)
	return nil
}

// displayEquipmentYAML displays equipment in YAML format
func (c *EquipmentCmd) displayEquipmentYAML(equipment *models.Equipment) error {
	fmt.Printf("YAML output not implemented yet\n")
	fmt.Printf("Equipment ID: %s\n", equipment.ID)
	fmt.Printf("Equipment Name: %s\n", equipment.Name)
	return nil
}

// CreateEquipmentCommand creates the cobra command for getting equipment
func CreateEquipmentCommand(app, cli, errorHandler interface{}) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "equipment <id>",
		Short: "Get equipment details",
		Long: `Get detailed information about equipment.
Supports various output formats and field selection.

Examples:
  arx get equipment HVAC-001
  arx get equipment HVAC-001 --format json
  arx get equipment HVAC-001 --fields name,type,status
  arx get equipment HVAC-001 --include-spatial`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			id := args[0]

			// Create command instance
			equipmentCmd := NewEquipmentCmd(app, cli, errorHandler)

			// Execute command
			return equipmentCmd.Execute(ctx, id)
		},
	}

	// Add flags
	cmd.Flags().String("format", "table", "Output format (table, json, yaml)")
	cmd.Flags().StringSlice("fields", []string{}, "Specific fields to display")
	cmd.Flags().Bool("include-spatial", false, "Include spatial data and coordinates")
	cmd.Flags().Bool("include-history", false, "Include change history")
	cmd.Flags().Bool("include-relations", false, "Include related components")
	cmd.Flags().Bool("verbose", false, "Show detailed information")

	return cmd
}
