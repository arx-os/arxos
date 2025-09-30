package main

import (
	"context"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/errors"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/arx-os/arxos/pkg/models/building"
	"github.com/spf13/cobra"
)

var getCmd = &cobra.Command{
	Use:   "get <type> <id>",
	Short: "Get building component details",
	Long: `Get detailed information about building components (equipment, rooms, floors).
Supports various output formats and field selection.

Examples:
  arx get equipment HVAC-001
  arx get room CONF-001 --format json
  arx get floor FL-001 --fields name,level,height
  arx get equipment HVAC-001 --include-spatial`,
	Args: cobra.ExactArgs(2),
	RunE: runGet,
}

var (
	getFormat           string
	getFields           []string
	getIncludeSpatial   bool
	getIncludeHistory   bool
	getIncludeRelations bool
	getVerbose          bool
)

func init() {
	getCmd.Flags().StringVar(&getFormat, "format", "table", "Output format (table, json, yaml)")
	getCmd.Flags().StringSliceVar(&getFields, "fields", []string{}, "Specific fields to display")
	getCmd.Flags().BoolVar(&getIncludeSpatial, "include-spatial", false, "Include spatial data and coordinates")
	getCmd.Flags().BoolVar(&getIncludeHistory, "include-history", false, "Include change history")
	getCmd.Flags().BoolVar(&getIncludeRelations, "include-relations", false, "Include related components")
	getCmd.Flags().BoolVar(&getVerbose, "verbose", false, "Show detailed information")
}

func runGet(cmd *cobra.Command, args []string) error {
	ctx := context.Background()
	componentType := strings.ToLower(args[0])
	id := args[1]

	// Get services from DI container
	services := diContainer.GetServices()

	// Validate component type
	if !isValidComponentType(componentType) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid component type: %s (supported: equipment, room, floor)", componentType))
	}

	// Validate output format
	if !isValidOutputFormat(getFormat) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid output format: %s (supported: table, json, yaml)", getFormat))
	}

	// Get component based on type
	switch componentType {
	case "equipment":
		return getEquipment(ctx, services, id)
	case "room":
		return getRoom(ctx, services, id)
	case "floor":
		return getFloor(ctx, services, id)
	default:
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("unsupported component type: %s", componentType))
	}
}

func getEquipment(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement equipment retrieval when service is available
	logger.Info("Getting equipment", "id", id)

	// For now, create a placeholder equipment object
	equipment := &models.Equipment{
		ID:     id,
		Name:   "Placeholder Equipment",
		Type:   "unknown",
		Status: "unknown",
		Notes:  "This is a placeholder - service not implemented yet",
	}

	// Display equipment information
	return displayEquipment(equipment, nil, nil, nil)
}

func getRoom(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement room retrieval when service is available
	logger.Info("Getting room", "id", id)

	// For now, create a placeholder room object
	room := &building.Room{
		ID:   id,
		Name: "Placeholder Room",
		Type: "unknown",
		Area: 0,
	}

	// Display room information
	return displayRoom(room, nil, nil)
}

func getFloor(ctx context.Context, services *types.Services, id string) error {
	// TODO: Implement floor retrieval when service is available
	logger.Info("Getting floor", "id", id)

	// For now, create a placeholder floor object
	floor := &building.Floor{
		ID:     id,
		Number: 1,
		Name:   "Placeholder Floor",
		Height: 3.0,
	}

	// Display floor information
	return displayFloor(floor, nil, nil)
}

// Display functions

func displayEquipment(equipment *models.Equipment, spatialData interface{}, history []interface{}, relations []models.Equipment) error {
	switch getFormat {
	case "json":
		return displayEquipmentJSON(equipment, spatialData, history, relations)
	case "yaml":
		return displayEquipmentYAML(equipment, spatialData, history, relations)
	default:
		return displayEquipmentTable(equipment, spatialData, history, relations)
	}
}

func displayEquipmentTable(equipment *models.Equipment, spatialData interface{}, history []interface{}, relations []models.Equipment) error {
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
	if getIncludeSpatial && equipment.Location != nil {
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

	// Relations
	if getIncludeRelations && len(relations) > 0 {
		fmt.Printf("\nRelated Equipment (%d):\n", len(relations))
		for _, rel := range relations {
			fmt.Printf("  - %s (%s) - %s\n", rel.ID, rel.Name, rel.Status)
		}
	}

	// History
	if getIncludeHistory && len(history) > 0 {
		fmt.Printf("\nChange History (%d entries):\n", len(history))
		fmt.Printf("History display not implemented yet\n")
	}

	return nil
}

func displayEquipmentJSON(equipment *models.Equipment, spatialData interface{}, history []interface{}, relations []models.Equipment) error {
	result := map[string]interface{}{
		"equipment": equipment,
	}

	if getIncludeSpatial && spatialData != nil {
		result["spatial"] = spatialData
	}

	if getIncludeRelations && len(relations) > 0 {
		result["relations"] = relations
	}

	if getIncludeHistory && len(history) > 0 {
		result["history"] = history
	}

	// Use JSON marshaling (would need to import encoding/json)
	fmt.Printf("JSON output not implemented yet\n")
	return nil
}

func displayEquipmentYAML(equipment *models.Equipment, spatialData interface{}, history []interface{}, relations []models.Equipment) error {
	fmt.Printf("YAML output not implemented yet\n")
	return nil
}

func displayRoom(room *building.Room, equipment []building.Equipment, history []interface{}) error {
	switch getFormat {
	case "json":
		return displayRoomJSON(room, equipment, history)
	case "yaml":
		return displayRoomYAML(room, equipment, history)
	default:
		return displayRoomTable(room, equipment, history)
	}
}

func displayRoomTable(room *building.Room, equipment []building.Equipment, history []interface{}) error {
	fmt.Printf("Room Details\n")
	fmt.Printf("===========\n\n")

	fmt.Printf("ID: %s\n", room.ID)
	fmt.Printf("Name: %s\n", room.Name)
	fmt.Printf("Type: %s\n", room.Type)
	fmt.Printf("Area: %.2f m²\n", room.Area)
	if room.Height > 0 {
		fmt.Printf("Height: %.2f m\n", room.Height)
	}

	if getIncludeRelations && len(equipment) > 0 {
		fmt.Printf("\nEquipment (%d):\n", len(equipment))
		for _, eq := range equipment {
			fmt.Printf("  - %s (%s) - %s\n", eq.ID, eq.Name, eq.Status)
		}
	}

	if getIncludeHistory && len(history) > 0 {
		fmt.Printf("\nChange History (%d entries):\n", len(history))
		fmt.Printf("History display not implemented yet\n")
	}

	return nil
}

func displayRoomJSON(room *building.Room, equipment []building.Equipment, history []interface{}) error {
	fmt.Printf("JSON output not implemented yet\n")
	return nil
}

func displayRoomYAML(room *building.Room, equipment []building.Equipment, history []interface{}) error {
	fmt.Printf("YAML output not implemented yet\n")
	return nil
}

func displayFloor(floor *building.Floor, rooms []building.Room, history []interface{}) error {
	switch getFormat {
	case "json":
		return displayFloorJSON(floor, rooms, history)
	case "yaml":
		return displayFloorYAML(floor, rooms, history)
	default:
		return displayFloorTable(floor, rooms, history)
	}
}

func displayFloorTable(floor *building.Floor, rooms []building.Room, history []interface{}) error {
	fmt.Printf("Floor Details\n")
	fmt.Printf("============\n\n")

	fmt.Printf("ID: %s\n", floor.ID)
	fmt.Printf("Name: %s\n", floor.Name)
	fmt.Printf("Number: %d\n", floor.Number)
	if floor.Height > 0 {
		fmt.Printf("Height: %.2f m\n", floor.Height)
	}
	if floor.Elevation > 0 {
		fmt.Printf("Elevation: %.2f m\n", floor.Elevation)
	}

	if getIncludeRelations && len(rooms) > 0 {
		fmt.Printf("\nRooms (%d):\n", len(rooms))
		for _, room := range rooms {
			fmt.Printf("  - %s (%s)\n", room.ID, room.Name)
		}
	}

	if getIncludeHistory && len(history) > 0 {
		fmt.Printf("\nChange History (%d entries):\n", len(history))
		fmt.Printf("History display not implemented yet\n")
	}

	return nil
}

func displayFloorJSON(floor *building.Floor, rooms []building.Room, history []interface{}) error {
	fmt.Printf("JSON output not implemented yet\n")
	return nil
}

func displayFloorYAML(floor *building.Floor, rooms []building.Room, history []interface{}) error {
	fmt.Printf("YAML output not implemented yet\n")
	return nil
}

// Helper functions

func isValidOutputFormat(format string) bool {
	validFormats := []string{"table", "json", "yaml"}
	for _, valid := range validFormats {
		if format == valid {
			return true
		}
	}
	return false
}
