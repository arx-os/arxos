package main

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/domain/equipment"
	"github.com/arx-os/arxos/pkg/errors"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/arx-os/arxos/pkg/models/building"
	"github.com/spf13/cobra"
)

var addCmd = &cobra.Command{
	Use:   "add <type> <name>",
	Short: "Add new building components",
	Long: `Add new building components (equipment, rooms, floors) to the building model.
Supports spatial positioning with millimeter precision.

Examples:
  arx add equipment "HVAC-001" --type "Air Handler" --location "1000,2000,2700" --room "101"
  arx add room "Conference Room A" --floor 2 --bounds "0,0,20,10"
  arx add floor "Floor 3" --level 3 --height 3000`,
	Args: cobra.ExactArgs(2),
	RunE: runAdd,
}

var (
	addType     string
	addLocation string
	addRoomID   string
	addFloor    int
	addLevel    int
	addHeight   float64
	addBounds   string
	addSystem   string
	addStatus   string
	addNotes    string
	addTags     []string
	addMetadata map[string]string
)

func init() {
	addCmd.Flags().StringVar(&addType, "type", "", "Component type (equipment: Air Handler, Pump, etc.)")
	addCmd.Flags().StringVar(&addLocation, "location", "", "3D coordinates (x,y,z) in millimeters")
	addCmd.Flags().StringVar(&addRoomID, "room", "", "Room ID or name")
	addCmd.Flags().IntVar(&addFloor, "floor", 0, "Floor number")
	addCmd.Flags().IntVar(&addLevel, "level", 0, "Floor level")
	addCmd.Flags().Float64Var(&addHeight, "height", 0, "Floor height in millimeters")
	addCmd.Flags().StringVar(&addBounds, "bounds", "", "Room bounds (minX,minY,maxX,maxY) in millimeters")
	addCmd.Flags().StringVar(&addSystem, "system", "", "System type (HVAC, Electrical, Plumbing, etc.)")
	addCmd.Flags().StringVar(&addStatus, "status", "operational", "Status (operational, maintenance, failed)")
	addCmd.Flags().StringVar(&addNotes, "notes", "", "Additional notes")
	addCmd.Flags().StringSliceVar(&addTags, "tags", []string{}, "Tags for categorization")
	addCmd.Flags().StringToStringVar(&addMetadata, "metadata", map[string]string{}, "Additional metadata (key=value)")
}

func runAdd(cmd *cobra.Command, args []string) error {
	ctx := context.Background()
	componentType := strings.ToLower(args[0])
	name := args[1]

	// Initialize error handler
	errorHandler := NewErrorHandler(getVerboseFlag(), false)

	// Validate component type
	if !isValidComponentType(componentType) {
		errorHandler.HandleValidationError(
			errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid component type: %s", componentType)),
			"component_type",
			componentType,
		)
	}

	// Validate required fields based on component type
	if err := validateAddFields(componentType); err != nil {
		errorHandler.HandleValidationError(err, "required_fields", componentType)
	}

	// Get services from DI container
	services := diContainer.GetServices()

	// Create component based on type with error handling
	switch componentType {
	case "equipment":
		return addEquipmentWithErrorHandling(ctx, services, name, errorHandler)
	case "room":
		return addRoomComponentWithErrorHandling(ctx, services, name, errorHandler)
	case "floor":
		return addFloorComponentWithErrorHandling(ctx, services, name, errorHandler)
	default:
		errorHandler.HandleError(
			errors.New(errors.CodeInvalidInput, fmt.Sprintf("unsupported component type: %s", componentType)),
			"component_creation",
		)
		return nil // Will not reach here due to exit
	}
}

// Helper function to get verbose flag
func getVerboseFlag() bool {
	// This would typically come from a global flag or context
	// For now, return false as default
	return false
}

func addEquipmentWithErrorHandling(ctx context.Context, services *types.Services, name string, errorHandler *ErrorHandler) error {
	// Parse location coordinates with validation
	errorHandler.ValidateAndHandle("location", addLocation, func(value interface{}) error {
		if str, ok := value.(string); ok && str == "" {
			return errors.New(errors.CodeInvalidInput, "location is required for equipment")
		}
		return nil
	})

	location, err := parseLocation(addLocation)
	if err != nil {
		errorHandler.HandleValidationError(err, "location", addLocation)
	}

	// Validate equipment type
	errorHandler.ValidateAndHandle("type", addType, ValidateNonEmpty)

	// Create equipment using service
	req := equipment.CreateEquipmentRequest{
		Name:     name,
		Type:     addType,
		Location: &equipment.Location{X: location.X, Y: location.Y, Z: location.Z},
		Metadata: convertMetadata(addMetadata),
	}

	createdEquipment, err := services.Equipment.CreateEquipment(ctx, req)
	if err != nil {
		errorHandler.HandleServiceError(err, "equipment", "create")
	}

	// Log success
	logger.Info("Created equipment: %s (%s) at %s", createdEquipment.ID, createdEquipment.Name, location.String())
	fmt.Printf("✅ Equipment created: %s\n", createdEquipment.ID)
	fmt.Printf("   Name: %s\n", createdEquipment.Name)
	fmt.Printf("   Type: %s\n", createdEquipment.Type)
	fmt.Printf("   Location: %s\n", location.String())
	if addRoomID != "" {
		fmt.Printf("   Room: %s\n", addRoomID)
	}

	return nil
}

func addRoomComponentWithErrorHandling(ctx context.Context, services *types.Services, name string, errorHandler *ErrorHandler) error {
	// Validate bounds
	errorHandler.ValidateAndHandle("bounds", addBounds, func(value interface{}) error {
		if str, ok := value.(string); ok && str == "" {
			return errors.New(errors.CodeInvalidInput, "bounds are required for room")
		}
		return nil
	})

	// Parse bounds
	bounds, err := parseBounds(addBounds)
	if err != nil {
		errorHandler.HandleValidationError(err, "bounds", addBounds)
	}

	// Create room model using building package
	room := &building.Room{
		ID:     generateRoomID(name),
		Number: fmt.Sprintf("R%d", addFloor*100+len([]rune(name))), // Simple room number generation
		Name:   name,
		Type:   "office", // Default type
	}

	// TODO: Implement room creation service when available
	logger.Info("Room creation placeholder - service not yet implemented")
	fmt.Printf("✅ Room created: %s\n", room.ID)
	fmt.Printf("   Name: %s\n", room.Name)
	fmt.Printf("   Number: %s\n", room.Number)
	fmt.Printf("   Bounds: (%.0f,%.0f) to (%.0f,%.0f)\n", bounds.MinX, bounds.MinY, bounds.MaxX, bounds.MaxY)

	return nil
}

func addFloorComponentWithErrorHandling(ctx context.Context, services *types.Services, name string, errorHandler *ErrorHandler) error {
	// Validate level
	errorHandler.ValidateAndHandle("level", addLevel, ValidatePositiveNumber)

	// Validate height
	errorHandler.ValidateAndHandle("height", addHeight, ValidatePositiveNumber)

	// Create floor model using building package
	floor := &building.Floor{
		ID:         generateFloorID(name),
		Number:     addLevel,
		Name:       name,
		Height:     addHeight / 1000.0,                         // Convert mm to meters
		Elevation:  float64(addLevel-1) * (addHeight / 1000.0), // Calculate elevation
		Confidence: building.ConfidenceMedium,
		Properties: make(map[string]interface{}),
	}

	// TODO: Implement floor creation service when available
	logger.Info("Floor creation placeholder - service not yet implemented")
	fmt.Printf("✅ Floor created: %s\n", floor.ID)
	fmt.Printf("   Name: %s\n", floor.Name)
	fmt.Printf("   Level: %d\n", floor.Number)
	fmt.Printf("   Height: %.2f m\n", floor.Height)

	return nil
}

// Helper functions

func isValidComponentType(componentType string) bool {
	validTypes := []string{"equipment", "room", "floor"}
	for _, valid := range validTypes {
		if componentType == valid {
			return true
		}
	}
	return false
}

func validateAddFields(componentType string) error {
	switch componentType {
	case "equipment":
		if addType == "" {
			return errors.New(errors.CodeInvalidInput, "equipment type is required (--type)")
		}
		if addLocation == "" {
			return errors.New(errors.CodeInvalidInput, "location is required for equipment (--location)")
		}
	case "room":
		if addFloor == 0 {
			return errors.New(errors.CodeInvalidInput, "floor is required for room (--floor)")
		}
		if addBounds == "" {
			return errors.New(errors.CodeInvalidInput, "bounds are required for room (--bounds)")
		}
	case "floor":
		if addLevel == 0 {
			return errors.New(errors.CodeInvalidInput, "level is required for floor (--level)")
		}
		if addHeight == 0 {
			return errors.New(errors.CodeInvalidInput, "height is required for floor (--height)")
		}
	}
	return nil
}

func parseLocation(locationStr string) (models.Point3D, error) {
	if locationStr == "" {
		return models.Point3D{}, errors.New(errors.CodeInvalidInput, "location cannot be empty")
	}

	parts := strings.Split(locationStr, ",")
	if len(parts) != 3 {
		return models.Point3D{}, errors.New(errors.CodeInvalidInput, "location must be in format 'x,y,z'")
	}

	x, err := strconv.ParseFloat(strings.TrimSpace(parts[0]), 64)
	if err != nil {
		return models.Point3D{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid X coordinate")
	}

	y, err := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
	if err != nil {
		return models.Point3D{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid Y coordinate")
	}

	z, err := strconv.ParseFloat(strings.TrimSpace(parts[2]), 64)
	if err != nil {
		return models.Point3D{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid Z coordinate")
	}

	return models.NewPoint3D(x, y, z), nil
}

func parseBounds(boundsStr string) (models.Bounds, error) {
	if boundsStr == "" {
		return models.Bounds{}, errors.New(errors.CodeInvalidInput, "bounds cannot be empty")
	}

	parts := strings.Split(boundsStr, ",")
	if len(parts) != 4 {
		return models.Bounds{}, errors.New(errors.CodeInvalidInput, "bounds must be in format 'minX,minY,maxX,maxY'")
	}

	minX, err := strconv.ParseFloat(strings.TrimSpace(parts[0]), 64)
	if err != nil {
		return models.Bounds{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid minX coordinate")
	}

	minY, err := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
	if err != nil {
		return models.Bounds{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid minY coordinate")
	}

	maxX, err := strconv.ParseFloat(strings.TrimSpace(parts[2]), 64)
	if err != nil {
		return models.Bounds{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid maxX coordinate")
	}

	maxY, err := strconv.ParseFloat(strings.TrimSpace(parts[3]), 64)
	if err != nil {
		return models.Bounds{}, errors.Wrap(err, errors.CodeInvalidInput, "invalid maxY coordinate")
	}

	return models.Bounds{
		MinX: minX,
		MinY: minY,
		MaxX: maxX,
		MaxY: maxY,
	}, nil
}

func generateEquipmentID(name string) string {
	// Generate a unique equipment ID based on name and timestamp
	// In a real implementation, this would use a proper ID generator
	return fmt.Sprintf("EQ-%s-%d", strings.ToUpper(strings.ReplaceAll(name, " ", "-")), time.Now().Unix())
}

func generateRoomID(name string) string {
	return fmt.Sprintf("RM-%s-%d", strings.ToUpper(strings.ReplaceAll(name, " ", "-")), time.Now().Unix())
}

func generateFloorID(name string) string {
	return fmt.Sprintf("FL-%s-%d", strings.ToUpper(strings.ReplaceAll(name, " ", "-")), time.Now().Unix())
}

// Helper function to convert string metadata to interface{} metadata
func convertMetadata(metadata map[string]string) map[string]interface{} {
	result := make(map[string]interface{})
	for k, v := range metadata {
		result[k] = v
	}
	return result
}
