package main

import (
	"context"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/errors"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/spf13/cobra"
)

var updateCmd = &cobra.Command{
	Use:   "update <type> <id>",
	Short: "Update building component",
	Long: `Update building component properties with validation and change tracking.
Supports partial updates and maintains change history.

Examples:
  arx update equipment HVAC-001 --status maintenance --notes "Scheduled maintenance"
  arx update equipment HVAC-001 --location "1000,2000,2700" --confidence high
  arx update room CONF-001 --bounds "0,0,20,10" --height 3000
  arx update floor FL-001 --name "Floor 2 - Updated" --height 3000`,
	Args: cobra.ExactArgs(2),
	RunE: runUpdate,
}

var (
	updateName       string
	updateType       string
	updateLocation   string
	updateRoomID     string
	updateStatus     string
	updateSystem     string
	updateNotes      string
	updateTags       []string
	updateMetadata   map[string]string
	updateBounds     string
	updateHeight     float64
	updateLevel      int
	updateConfidence string
	updateSource     string
	updateForce      bool
	updateDryRun     bool
)

func init() {
	// General update flags
	updateCmd.Flags().StringVar(&updateName, "name", "", "Update component name")
	updateCmd.Flags().StringVar(&updateType, "type", "", "Update component type")
	updateCmd.Flags().StringVar(&updateStatus, "status", "", "Update status")
	updateCmd.Flags().StringVar(&updateSystem, "system", "", "Update system type")
	updateCmd.Flags().StringVar(&updateNotes, "notes", "", "Update notes")
	updateCmd.Flags().StringSliceVar(&updateTags, "tags", []string{}, "Update tags")
	updateCmd.Flags().StringToStringVar(&updateMetadata, "metadata", map[string]string{}, "Update metadata (key=value)")

	// Spatial update flags
	updateCmd.Flags().StringVar(&updateLocation, "location", "", "Update 3D coordinates (x,y,z)")
	updateCmd.Flags().StringVar(&updateRoomID, "room", "", "Update room assignment")
	updateCmd.Flags().StringVar(&updateConfidence, "confidence", "", "Update confidence level (low, medium, high, precise)")
	updateCmd.Flags().StringVar(&updateSource, "source", "", "Update data source")

	// Room/Floor specific flags
	updateCmd.Flags().StringVar(&updateBounds, "bounds", "", "Update room bounds (minX,minY,maxX,maxY)")
	updateCmd.Flags().Float64Var(&updateHeight, "height", 0, "Update height in millimeters")
	updateCmd.Flags().IntVar(&updateLevel, "level", 0, "Update floor level")

	// Control flags
	updateCmd.Flags().BoolVar(&updateForce, "force", false, "Force update without validation")
	updateCmd.Flags().BoolVar(&updateDryRun, "dry-run", false, "Show what would be updated without making changes")
}

func runUpdate(cmd *cobra.Command, args []string) error {
	ctx := context.Background()
	componentType := strings.ToLower(args[0])
	id := args[1]

	// Get services from DI container
	services := diContainer.GetServices()

	// Validate component type
	if !isValidComponentType(componentType) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid component type: %s (supported: equipment, room, floor)", componentType))
	}

	// Check if any update fields are provided
	if !hasUpdateFields() {
		return errors.New(errors.CodeInvalidInput, "no update fields provided")
	}

	// Update component based on type
	switch componentType {
	case "equipment":
		return updateEquipment(ctx, services, id)
	case "room":
		return updateRoomComponent(ctx, services, id)
	case "floor":
		return updateFloor(ctx, services, id)
	default:
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("unsupported component type: %s", componentType))
	}
}

func updateEquipment(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement equipment update when service is available
	logger.Info("Updating equipment", "id", id)

	// For now, just log the update request
	logger.Info("Equipment update requested", 
		"id", id,
		"name", updateName,
		"type", updateType,
		"status", updateStatus,
		"room", updateRoomID,
		"notes", updateNotes)

	fmt.Printf("Equipment %s update requested (service not implemented yet)\n", id)
	fmt.Printf("Updates: name=%s, type=%s, status=%s, room=%s\n", 
		updateName, updateType, updateStatus, updateRoomID)

	return nil
}

func updateRoomComponent(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement room update when service is available
	logger.Info("Updating room", "id", id)

	// For now, just log the update request
	logger.Info("Room update requested", 
		"id", id,
		"name", updateName,
		"bounds", updateBounds)

	fmt.Printf("Room %s update requested (service not implemented yet)\n", id)
	fmt.Printf("Updates: name=%s, bounds=%s\n", updateName, updateBounds)

	return nil
}

func updateFloor(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement floor update when service is available
	logger.Info("Updating floor", "id", id)
	fmt.Printf("Floor %s update requested (service not implemented yet)\n", id)
	return nil
}

// Validation functions

func validateEquipmentUpdate(existing *models.Equipment, updateData *EquipmentUpdateData) error {
	// Validate status transition
	if updateData.Status != "" && !isValidStatusTransition(existing.Status, updateData.Status) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid status transition: %s -> %s", existing.Status, updateData.Status))
	}

	// Validate location if provided
	if updateData.Location != nil {
		if !updateData.Location.IsValid() {
			return errors.New(errors.CodeInvalidInput, "invalid location coordinates")
		}
	}

	return nil
}

func validateRoomUpdate(existing *models.Room, updateData *RoomUpdateData) error {
	// Validate bounds if provided
	if updateData.Bounds != nil {
		if updateData.Bounds.Width() <= 0 || updateData.Bounds.Height() <= 0 {
			return errors.New(errors.CodeInvalidInput, "invalid bounds: width and height must be positive")
		}
	}

	return nil
}

func validateFloorUpdate(existing *models.FloorPlan, updateData *FloorUpdateData) error {
	// Validate level if provided
	if updateData.Level != 0 && updateData.Level < 0 {
		return errors.New(errors.CodeInvalidInput, "floor level must be non-negative")
	}

	// Validate height if provided
	if updateData.Height != 0 && updateData.Height <= 0 {
		return errors.New(errors.CodeInvalidInput, "floor height must be positive")
	}

	return nil
}

// Preview functions

func showEquipmentUpdatePreview(existing *models.Equipment, updateData *EquipmentUpdateData) error {
	fmt.Printf("Equipment Update Preview\n")
	fmt.Printf("=======================\n\n")
	fmt.Printf("ID: %s\n", existing.ID)

	if updateData.Name != "" {
		fmt.Printf("Name: %s -> %s\n", existing.Name, updateData.Name)
	}
	if updateData.Type != "" {
		fmt.Printf("Type: %s -> %s\n", existing.Type, updateData.Type)
	}
	if updateData.Status != "" {
		fmt.Printf("Status: %s -> %s\n", existing.Status, updateData.Status)
	}
	if updateData.Location != nil {
		fmt.Printf("Location: %s -> %s\n", existing.Location.String(), updateData.Location.String())
	}
	if updateData.Room != "" {
		fmt.Printf("Room: %s -> %s\n", existing.RoomID, updateData.Room)
	}

	fmt.Printf("\n[DRY RUN] No changes were made\n")
	return nil
}

func showRoomUpdatePreview(existing *models.Room, updateData *RoomUpdateData) error {
	fmt.Printf("Room Update Preview\n")
	fmt.Printf("==================\n\n")
	fmt.Printf("ID: %s\n", existing.ID)

	if updateData.Name != "" {
		fmt.Printf("Name: %s -> %s\n", existing.Name, updateData.Name)
	}
	if updateData.Bounds != nil {
		fmt.Printf("Bounds: (%.0f,%.0f)-(%.0f,%.0f) -> (%.0f,%.0f)-(%.0f,%.0f)\n", 
			existing.Bounds.MinX, existing.Bounds.MinY, existing.Bounds.MaxX, existing.Bounds.MaxY,
			updateData.Bounds.MinX, updateData.Bounds.MinY, updateData.Bounds.MaxX, updateData.Bounds.MaxY)
	}
	// Height field not available in models.Room

	fmt.Printf("\n[DRY RUN] No changes were made\n")
	return nil
}

func showFloorUpdatePreview(existing *models.FloorPlan, updateData *FloorUpdateData) error {
	fmt.Printf("Floor Update Preview\n")
	fmt.Printf("====================\n\n")
	fmt.Printf("ID: %s\n", existing.ID)

	if updateData.Name != "" {
		fmt.Printf("Name: %s -> %s\n", existing.Name, updateData.Name)
	}
	if updateData.Level != 0 {
		fmt.Printf("Level: %d -> %d\n", existing.Level, updateData.Level)
	}
	// Height field not available in models.Room

	fmt.Printf("\n[DRY RUN] No changes were made\n")
	return nil
}

// Helper functions

func hasUpdateFields() bool {
	return updateName != "" ||
		updateType != "" ||
		updateLocation != "" ||
		updateRoomID != "" ||
		updateStatus != "" ||
		updateSystem != "" ||
		updateNotes != "" ||
		len(updateTags) > 0 ||
		len(updateMetadata) > 0 ||
		updateBounds != "" ||
		updateHeight != 0 ||
		updateLevel != 0 ||
		updateConfidence != "" ||
		updateSource != ""
}

func isValidStatusTransition(from, to string) bool {
	// Define valid status transitions
	validTransitions := map[string][]string{
		"operational": {"maintenance", "failed"},
		"maintenance": {"operational", "failed"},
		"failed":      {"maintenance", "operational"},
	}

	if transitions, exists := validTransitions[from]; exists {
		for _, valid := range transitions {
			if to == valid {
				return true
			}
		}
	}
	return false
}

func parseConfidenceLevel(confidence string) (models.ConfidenceLevel, error) {
	switch strings.ToLower(confidence) {
	case "low":
		return models.ConfidenceLow, nil
	case "medium":
		return models.ConfidenceMedium, nil
	case "high":
		return models.ConfidenceHigh, nil
	case "precise":
		return models.ConfidencePrecise, nil
	default:
		return models.ConfidenceUnknown, errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid confidence level: %s", confidence))
	}
}

// Placeholder types - these would be defined in the actual service interfaces
type EquipmentUpdateData struct {
	Name       string
	Type       string
	Status     string
	System     string
	Notes      string
	Tags       []string
	Metadata   map[string]string
	Location   *models.Point3D
	Room       string
	Confidence *models.ConfidenceLevel
	Source     string
}

type RoomUpdateData struct {
	Name     string
	Notes    string
	Tags     []string
	Metadata map[string]string
	Bounds   *models.Bounds
	Height   float64
}

type FloorUpdateData struct {
	Name     string
	Notes    string
	Tags     []string
	Metadata map[string]string
	Height   float64
	Level    int
}
