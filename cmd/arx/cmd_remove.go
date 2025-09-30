package main

import (
	"context"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/pkg/errors"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/spf13/cobra"
)

var removeCmd = &cobra.Command{
	Use:   "remove <type> <id>",
	Short: "Remove building component",
	Long: `Remove building component with dependency checking and cascade options.
Supports soft delete and hard delete with proper cleanup.

Examples:
  arx remove equipment HVAC-001
  arx remove equipment HVAC-001 --cascade --force
  arx remove room CONF-001 --check-dependencies
  arx remove floor FL-001 --dry-run
  arx remove equipment HVAC-001 --soft --reason "End of life"`,
	Args: cobra.ExactArgs(2),
	RunE: runRemove,
}

var (
	removeCascade     bool
	removeForce       bool
	removeDryRun      bool
	removeSoft        bool
	removeReason      string
	removeCheckDeps   bool
	removeConfirm     bool
	removeRecursive   bool
	removeKeepHistory bool
)

func init() {
	removeCmd.Flags().BoolVar(&removeCascade, "cascade", false, "Remove dependent components")
	removeCmd.Flags().BoolVar(&removeForce, "force", false, "Force removal without confirmation")
	removeCmd.Flags().BoolVar(&removeDryRun, "dry-run", false, "Show what would be removed without making changes")
	removeCmd.Flags().BoolVar(&removeSoft, "soft", false, "Soft delete (mark as deleted but keep data)")
	removeCmd.Flags().StringVar(&removeReason, "reason", "", "Reason for removal")
	removeCmd.Flags().BoolVar(&removeCheckDeps, "check-dependencies", true, "Check for dependencies before removal")
	removeCmd.Flags().BoolVar(&removeConfirm, "confirm", false, "Skip interactive confirmation")
	removeCmd.Flags().BoolVar(&removeRecursive, "recursive", false, "Remove recursively (for hierarchical components)")
	removeCmd.Flags().BoolVar(&removeKeepHistory, "keep-history", true, "Keep change history after removal")
}

func runRemove(cmd *cobra.Command, args []string) error {
	ctx := context.Background()
	componentType := strings.ToLower(args[0])
	id := args[1]

	// Get services from DI container
	services := diContainer.GetServices()

	// Validate component type
	if !isValidComponentType(componentType) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid component type: %s (supported: equipment, room, floor)", componentType))
	}

	// Remove component based on type
	switch componentType {
	case "equipment":
		return removeEquipment(ctx, services, id)
	case "room":
		return removeRoom(ctx, services, id)
	case "floor":
		return removeFloor(ctx, services, id)
	default:
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("unsupported component type: %s", componentType))
	}
}

func removeEquipment(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement equipment removal when service is available
	// For now, just log the request
	fmt.Printf("Equipment removal requested for ID: %s\n", id)
	fmt.Printf("This feature will be implemented when the equipment service is available.\n")

	return nil
}

func removeRoom(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement room removal when service is available
	// For now, just log the request
	fmt.Printf("Room removal requested for ID: %s\n", id)
	fmt.Printf("This feature will be implemented when the room service is available.\n")

	return nil
}

func removeFloor(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement floor removal when service is available
	// For now, just log the request
	fmt.Printf("Floor removal requested for ID: %s\n", id)
	fmt.Printf("This feature will be implemented when the floor service is available.\n")

	return nil
}

// Preview functions

func showEquipmentRemovalPreview(existing *models.Equipment, options *EquipmentRemovalOptions) error {
	fmt.Printf("Equipment Removal Preview\n")
	fmt.Printf("========================\n\n")
	fmt.Printf("ID: %s\n", existing.ID)
	fmt.Printf("Name: %s\n", existing.Name)
	fmt.Printf("Type: %s\n", existing.Type)
	fmt.Printf("Status: %s\n", existing.Status)
	fmt.Printf("Room: %s\n", existing.RoomID)

	if options.Cascade {
		fmt.Printf("\nCascade removal: ENABLED\n")
		fmt.Printf("Dependent components will also be removed\n")
	}

	if options.Soft {
		fmt.Printf("\nSoft delete: ENABLED\n")
		fmt.Printf("Data will be marked as deleted but preserved\n")
	} else {
		fmt.Printf("\nHard delete: ENABLED\n")
		fmt.Printf("Data will be permanently removed\n")
	}

	if options.Reason != "" {
		fmt.Printf("\nReason: %s\n", options.Reason)
	}

	fmt.Printf("\n[DRY RUN] No changes were made\n")
	return nil
}

func showRoomRemovalPreview(existing *models.Room, options *RoomRemovalOptions) error {
	fmt.Printf("Room Removal Preview\n")
	fmt.Printf("===================\n\n")
	fmt.Printf("ID: %s\n", existing.ID)
	fmt.Printf("Name: %s\n", existing.Name)
	fmt.Printf("Bounds: %.2f,%.2f to %.2f,%.2f\n",
		existing.Bounds.MinX, existing.Bounds.MinY,
		existing.Bounds.MaxX, existing.Bounds.MaxY)

	if options.Cascade {
		fmt.Printf("\nCascade removal: ENABLED\n")
		fmt.Printf("Equipment in this room will also be removed\n")
	}

	if options.Soft {
		fmt.Printf("\nSoft delete: ENABLED\n")
		fmt.Printf("Data will be marked as deleted but preserved\n")
	} else {
		fmt.Printf("\nHard delete: ENABLED\n")
		fmt.Printf("Data will be permanently removed\n")
	}

	if options.Reason != "" {
		fmt.Printf("\nReason: %s\n", options.Reason)
	}

	fmt.Printf("\n[DRY RUN] No changes were made\n")
	return nil
}

func showFloorRemovalPreview(existing *models.FloorPlan, options *FloorRemovalOptions) error {
	fmt.Printf("Floor Removal Preview\n")
	fmt.Printf("====================\n\n")
	fmt.Printf("ID: %s\n", existing.ID)
	fmt.Printf("Name: %s\n", existing.Name)
	fmt.Printf("Level: %d\n", existing.Level)

	if options.Cascade {
		fmt.Printf("\nCascade removal: ENABLED\n")
		fmt.Printf("Rooms on this floor will also be removed\n")
	}

	if options.Soft {
		fmt.Printf("\nSoft delete: ENABLED\n")
		fmt.Printf("Data will be marked as deleted but preserved\n")
	} else {
		fmt.Printf("\nHard delete: ENABLED\n")
		fmt.Printf("Data will be permanently removed\n")
	}

	if options.Reason != "" {
		fmt.Printf("\nReason: %s\n", options.Reason)
	}

	fmt.Printf("\n[DRY RUN] No changes were made\n")
	return nil
}

// Helper functions

func confirmRemoval(componentType, id, name string) bool {
	fmt.Printf("Are you sure you want to remove %s '%s' (%s)? [y/N]: ", componentType, name, id)

	var response string
	fmt.Scanln(&response)

	return strings.ToLower(response) == "y" || strings.ToLower(response) == "yes"
}

// Placeholder types - these would be defined in the actual service interfaces
type EquipmentRemovalOptions struct {
	Cascade     bool
	Force       bool
	Soft        bool
	Reason      string
	KeepHistory bool
}

type RoomRemovalOptions struct {
	Cascade     bool
	Force       bool
	Soft        bool
	Reason      string
	KeepHistory bool
}

type FloorRemovalOptions struct {
	Cascade     bool
	Force       bool
	Soft        bool
	Reason      string
	KeepHistory bool
}
