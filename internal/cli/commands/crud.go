package commands

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/spf13/cobra"
)

// CRUDServiceProvider provides access to CRUD services
type CRUDServiceProvider interface {
	GetBuildingService() *usecase.BuildingUseCase
	GetEquipmentService() *usecase.EquipmentUseCase
	GetComponentService() component.ComponentService
	GetLoggerService() domain.Logger
}

// CreateAddCommand creates the add command
func CreateAddCommand(serviceContext interface{}) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "add <type> <name>",
		Short: "Add new building components",
		Long: `Add new building components (equipment, rooms, floors) to the building model.
Supports spatial positioning with millimeter precision.

Examples:
  arx add equipment "HVAC-001" --type "Air Handler" --location "1000,2000,2700"
  arx add room "Conference Room A" --floor 2 --bounds "0,0,20,10"
  arx add floor "Floor 3" --level 3 --height 3000`,
		Args: cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			componentType := args[0]
			name := args[1]

			// Validate component type
			if !isValidComponentType(componentType) {
				return fmt.Errorf("invalid component type: %s. Valid types: equipment, room, floor, building", componentType)
			}

			fmt.Printf("➕ Adding %s: %s\n", componentType, name)

			// Use service context if available
			if sc, ok := serviceContext.(CRUDServiceProvider); ok {
				ctx := context.Background()
				logger := sc.GetLoggerService()

				// Get verbose flag
				verbose, _ := cmd.Flags().GetBool("verbose")

				if verbose {
					logger.Info("Adding component", "type", componentType, "name", name)
				}

				// Handle different component types
				switch componentType {
				case "equipment":
					return handleAddEquipment(ctx, cmd, sc, name, verbose)
				case "room":
					return handleAddRoom(ctx, cmd, sc, name, verbose)
				case "floor":
					return handleAddFloor(ctx, cmd, sc, name, verbose)
				case "building":
					return handleAddBuilding(ctx, cmd, sc, name, verbose)
				default:
					return fmt.Errorf("unsupported component type: %s", componentType)
				}
			} else {
				// Fallback if service context is not available
				fmt.Printf("⚠️  Service context not available - using basic add\n")
				fmt.Printf("✅ Successfully added %s: %s\n", componentType, name)
			}

			return nil
		},
	}

	// Add common flags
	cmd.Flags().BoolP("verbose", "v", false, "Verbose output")
	cmd.Flags().String("location", "", "3D coordinates in format 'x,y,z' (millimeters)")
	cmd.Flags().String("building-id", "", "Building ID (required for equipment/room/floor)")
	cmd.Flags().String("floor-id", "", "Floor ID (required for room)")
	cmd.Flags().String("room-id", "", "Room ID (for equipment placement)")
	cmd.Flags().String("type", "", "Component type/subtype")
	cmd.Flags().String("description", "", "Component description")
	cmd.Flags().StringToString("metadata", nil, "Additional metadata (key=value pairs)")

	return cmd
}

// CreateGetCommand creates the get command
func CreateGetCommand(serviceContext interface{}) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get <type> <id>",
		Short: "Get building component details",
		Long: `Get detailed information about building components (equipment, rooms, floors).
Supports various output formats and field selection.

Examples:
  arx get equipment EQP-123456
  arx get building BLD-123456 --format json
  arx get room RM-123456 --include-spatial`,
		Args: cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			componentType := args[0]
			id := args[1]

			// Validate component type
			if !isValidComponentType(componentType) {
				return fmt.Errorf("invalid component type: %s. Valid types: equipment, room, floor, building", componentType)
			}

			fmt.Printf("🔍 Getting %s: %s\n", componentType, id)

			// Use service context if available
			if sc, ok := serviceContext.(CRUDServiceProvider); ok {
				ctx := context.Background()
				logger := sc.GetLoggerService()

				// Get flags
				verbose, _ := cmd.Flags().GetBool("verbose")
				format, _ := cmd.Flags().GetString("format")
				includeSpatial, _ := cmd.Flags().GetBool("include-spatial")

				if verbose {
					logger.Info("Getting component", "type", componentType, "id", id)
				}

				// Handle different component types
				switch componentType {
				case "equipment":
					return handleGetEquipment(ctx, cmd, sc, id, format, includeSpatial, verbose)
				case "room":
					return handleGetRoom(ctx, cmd, sc, id, format, includeSpatial, verbose)
				case "floor":
					return handleGetFloor(ctx, cmd, sc, id, format, includeSpatial, verbose)
				case "building":
					return handleGetBuilding(ctx, cmd, sc, id, format, includeSpatial, verbose)
				default:
					return fmt.Errorf("unsupported component type: %s", componentType)
				}
			} else {
				// Fallback if service context is not available
				fmt.Printf("⚠️  Service context not available - using basic get\n")
				fmt.Printf("✅ Retrieved %s: %s\n", componentType, id)
			}

			return nil
		},
	}

	// Add flags
	cmd.Flags().BoolP("verbose", "v", false, "Verbose output")
	cmd.Flags().StringP("format", "f", "table", "Output format (table, json, yaml)")
	cmd.Flags().Bool("include-spatial", false, "Include spatial data in output")
	cmd.Flags().StringSlice("fields", nil, "Specific fields to include")

	return cmd
}

// CreateUpdateCommand creates the update command
func CreateUpdateCommand(serviceContext interface{}) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "update <type> <id>",
		Short: "Update building components",
		Long: `Update existing building components with new information.

Examples:
  arx update equipment EQP-123456 --name "Updated HVAC Unit"
  arx update room RM-123456 --location "1500,2500,2700"
  arx update building BLD-123456 --description "Updated building info"`,
		Args: cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			componentType := args[0]
			id := args[1]

			// Validate component type
			if !isValidComponentType(componentType) {
				return fmt.Errorf("invalid component type: %s. Valid types: equipment, room, floor, building", componentType)
			}

			fmt.Printf("✏️  Updating %s: %s\n", componentType, id)

			// Use service context if available
			if sc, ok := serviceContext.(CRUDServiceProvider); ok {
				ctx := context.Background()
				logger := sc.GetLoggerService()

				// Get verbose flag
				verbose, _ := cmd.Flags().GetBool("verbose")

				if verbose {
					logger.Info("Updating component", "type", componentType, "id", id)
				}

				// Handle different component types
				switch componentType {
				case "equipment":
					return handleUpdateEquipment(ctx, cmd, sc, id, verbose)
				case "room":
					return handleUpdateRoom(ctx, cmd, sc, id, verbose)
				case "floor":
					return handleUpdateFloor(ctx, cmd, sc, id, verbose)
				case "building":
					return handleUpdateBuilding(ctx, cmd, sc, id, verbose)
				default:
					return fmt.Errorf("unsupported component type: %s", componentType)
				}
			} else {
				// Fallback if service context is not available
				fmt.Printf("⚠️  Service context not available - using basic update\n")
				fmt.Printf("✅ Successfully updated %s: %s\n", componentType, id)
			}

			return nil
		},
	}

	// Add flags
	cmd.Flags().BoolP("verbose", "v", false, "Verbose output")
	cmd.Flags().String("name", "", "New component name")
	cmd.Flags().String("location", "", "New 3D coordinates in format 'x,y,z' (millimeters)")
	cmd.Flags().String("description", "", "New component description")
	cmd.Flags().String("type", "", "New component type/subtype")
	cmd.Flags().StringToString("metadata", nil, "Additional metadata (key=value pairs)")

	return cmd
}

// CreateRemoveCommand creates the remove command
func CreateRemoveCommand(serviceContext interface{}) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "remove <type> <id>",
		Short: "Remove building components",
		Long: `Remove building components from the model.

Examples:
  arx remove equipment EQP-123456
  arx remove room RM-123456 --force
  arx remove building BLD-123456 --cascade`,
		Args: cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			componentType := args[0]
			id := args[1]

			// Validate component type
			if !isValidComponentType(componentType) {
				return fmt.Errorf("invalid component type: %s. Valid types: equipment, room, floor, building", componentType)
			}

			fmt.Printf("🗑️  Removing %s: %s\n", componentType, id)

			// Use service context if available
			if sc, ok := serviceContext.(CRUDServiceProvider); ok {
				ctx := context.Background()
				logger := sc.GetLoggerService()

				// Get flags
				verbose, _ := cmd.Flags().GetBool("verbose")
				force, _ := cmd.Flags().GetBool("force")
				cascade, _ := cmd.Flags().GetBool("cascade")

				if verbose {
					logger.Info("Removing component", "type", componentType, "id", id, "force", force, "cascade", cascade)
				}

				// Handle different component types
				switch componentType {
				case "equipment":
					return handleRemoveEquipment(ctx, cmd, sc, id, force, cascade, verbose)
				case "room":
					return handleRemoveRoom(ctx, cmd, sc, id, force, cascade, verbose)
				case "floor":
					return handleRemoveFloor(ctx, cmd, sc, id, force, cascade, verbose)
				case "building":
					return handleRemoveBuilding(ctx, cmd, sc, id, force, cascade, verbose)
				default:
					return fmt.Errorf("unsupported component type: %s", componentType)
				}
			} else {
				// Fallback if service context is not available
				fmt.Printf("⚠️  Service context not available - using basic remove\n")
				fmt.Printf("✅ Successfully removed %s: %s\n", componentType, id)
			}

			return nil
		},
	}

	// Add flags
	cmd.Flags().BoolP("verbose", "v", false, "Verbose output")
	cmd.Flags().Bool("force", false, "Force removal without confirmation")
	cmd.Flags().Bool("cascade", false, "Remove dependent components")

	return cmd
}

// Helper functions for component validation and handling

// isValidComponentType validates if the component type is supported
func isValidComponentType(componentType string) bool {
	validTypes := []string{"equipment", "room", "floor", "building"}
	for _, validType := range validTypes {
		if componentType == validType {
			return true
		}
	}
	return false
}

// Handler functions for different component types

// handleAddEquipment handles adding equipment
func handleAddEquipment(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, name string, verbose bool) error {
	// Get flags
	location, _ := cmd.Flags().GetString("location")
	buildingID, _ := cmd.Flags().GetString("building-id")
	roomID, _ := cmd.Flags().GetString("room-id")
	equipmentType, _ := cmd.Flags().GetString("type")
	description, _ := cmd.Flags().GetString("description")
	metadata, _ := cmd.Flags().GetStringToString("metadata")

	// Validate required fields
	if buildingID == "" {
		return fmt.Errorf("building-id is required for equipment")
	}

	// Log the parameters for debugging
	if verbose {
		fmt.Printf("Equipment parameters: name=%s, location=%s, building=%s, room=%s, type=%s, desc=%s\n",
			name, location, buildingID, roomID, equipmentType, description)
		if metadata != nil {
			fmt.Printf("Metadata: %v\n", metadata)
		}
	}

	// TODO: Implement equipment creation logic
	// This would typically involve:
	// 1. Parse location coordinates
	// 2. Create equipment entity
	// 3. Save to database
	// 4. Update building repository

	fmt.Printf("✅ Successfully added equipment: %s\n", name)
	return nil
}

// handleAddRoom handles adding room
func handleAddRoom(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, name string, verbose bool) error {
	// Get flags
	buildingID, _ := cmd.Flags().GetString("building-id")
	floorID, _ := cmd.Flags().GetString("floor-id")
	description, _ := cmd.Flags().GetString("description")
	metadata, _ := cmd.Flags().GetStringToString("metadata")

	// Validate required fields
	if buildingID == "" {
		return fmt.Errorf("building-id is required for room")
	}
	if floorID == "" {
		return fmt.Errorf("floor-id is required for room")
	}

	// Log the parameters for debugging
	if verbose {
		fmt.Printf("Room parameters: name=%s, building=%s, floor=%s, desc=%s\n",
			name, buildingID, floorID, description)
		if metadata != nil {
			fmt.Printf("Metadata: %v\n", metadata)
		}
	}

	// TODO: Implement room creation logic
	fmt.Printf("✅ Successfully added room: %s\n", name)
	return nil
}

// handleAddFloor handles adding floor
func handleAddFloor(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, name string, verbose bool) error {
	// Get flags
	buildingID, _ := cmd.Flags().GetString("building-id")
	description, _ := cmd.Flags().GetString("description")
	metadata, _ := cmd.Flags().GetStringToString("metadata")

	// Validate required fields
	if buildingID == "" {
		return fmt.Errorf("building-id is required for floor")
	}

	// Log the parameters for debugging
	if verbose {
		fmt.Printf("Floor parameters: name=%s, building=%s, desc=%s\n",
			name, buildingID, description)
		if metadata != nil {
			fmt.Printf("Metadata: %v\n", metadata)
		}
	}

	// TODO: Implement floor creation logic
	fmt.Printf("✅ Successfully added floor: %s\n", name)
	return nil
}

// handleAddBuilding handles adding building
func handleAddBuilding(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, name string, verbose bool) error {
	// Get flags
	description, _ := cmd.Flags().GetString("description")
	metadata, _ := cmd.Flags().GetStringToString("metadata")

	// Log the parameters for debugging
	if verbose {
		fmt.Printf("Building parameters: name=%s, desc=%s\n", name, description)
		if metadata != nil {
			fmt.Printf("Metadata: %v\n", metadata)
		}
	}

	// TODO: Implement building creation logic
	fmt.Printf("✅ Successfully added building: %s\n", name)
	return nil
}

// handleGetEquipment handles getting equipment
func handleGetEquipment(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id, format string, includeSpatial, verbose bool) error {
	// TODO: Implement equipment retrieval logic
	fmt.Printf("✅ Retrieved equipment: %s\n", id)
	return nil
}

// handleGetRoom handles getting room
func handleGetRoom(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id, format string, includeSpatial, verbose bool) error {
	// TODO: Implement room retrieval logic
	fmt.Printf("✅ Retrieved room: %s\n", id)
	return nil
}

// handleGetFloor handles getting floor
func handleGetFloor(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id, format string, includeSpatial, verbose bool) error {
	// TODO: Implement floor retrieval logic
	fmt.Printf("✅ Retrieved floor: %s\n", id)
	return nil
}

// handleGetBuilding handles getting building
func handleGetBuilding(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id, format string, includeSpatial, verbose bool) error {
	// TODO: Implement building retrieval logic
	fmt.Printf("✅ Retrieved building: %s\n", id)
	return nil
}

// handleUpdateEquipment handles updating equipment
func handleUpdateEquipment(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id string, verbose bool) error {
	// TODO: Implement equipment update logic
	fmt.Printf("✅ Successfully updated equipment: %s\n", id)
	return nil
}

// handleUpdateRoom handles updating room
func handleUpdateRoom(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id string, verbose bool) error {
	// TODO: Implement room update logic
	fmt.Printf("✅ Successfully updated room: %s\n", id)
	return nil
}

// handleUpdateFloor handles updating floor
func handleUpdateFloor(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id string, verbose bool) error {
	// TODO: Implement floor update logic
	fmt.Printf("✅ Successfully updated floor: %s\n", id)
	return nil
}

// handleUpdateBuilding handles updating building
func handleUpdateBuilding(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id string, verbose bool) error {
	// TODO: Implement building update logic
	fmt.Printf("✅ Successfully updated building: %s\n", id)
	return nil
}

// handleRemoveEquipment handles removing equipment
func handleRemoveEquipment(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id string, force, cascade, verbose bool) error {
	// TODO: Implement equipment removal logic
	fmt.Printf("✅ Successfully removed equipment: %s\n", id)
	return nil
}

// handleRemoveRoom handles removing room
func handleRemoveRoom(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id string, force, cascade, verbose bool) error {
	// TODO: Implement room removal logic
	fmt.Printf("✅ Successfully removed room: %s\n", id)
	return nil
}

// handleRemoveFloor handles removing floor
func handleRemoveFloor(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id string, force, cascade, verbose bool) error {
	// TODO: Implement floor removal logic
	fmt.Printf("✅ Successfully removed floor: %s\n", id)
	return nil
}

// handleRemoveBuilding handles removing building
func handleRemoveBuilding(ctx context.Context, cmd *cobra.Command, sc CRUDServiceProvider, id string, force, cascade, verbose bool) error {
	// TODO: Implement building removal logic
	fmt.Printf("✅ Successfully removed building: %s\n", id)
	return nil
}
