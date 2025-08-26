package commands

import (
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// ArxObjectCmd represents the arx arxobject command
var ArxObjectCmd = &cobra.Command{
	Use:   "arxobject",
	Short: "Manage ArxObjects in the building",
	Long: `ArxObject commands provide advanced management capabilities for building elements.
	
This includes metadata persistence, relationship management, validation, and lifecycle tracking.
Think of it as 'git' for building components.

Examples:
  arx arxobject show building:main
  arx arxobject validate building:main:floor:1 --method photo --confidence 0.9
  arx arxobject relate building:main:floor:1 building:main:system:electrical --type contains
  arx arxobject lifecycle building:main:system:hvac --status active --phase operational
  arx arxobject search "electrical" --type system --floor 1
  arx arxobject stats building:main
  arx arxobject export building:main --format csv --type system`,
}

// ArxObjectShowCmd shows detailed information about an ArxObject
var ArxObjectShowCmd = &cobra.Command{
	Use:   "show [object-id]",
	Short: "Show detailed information about an ArxObject",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		objectID := args[0]
		buildingID := extractBuildingID(objectID)

		manager := NewArxObjectManager(buildingID)
		obj, err := manager.LoadArxObject(objectID)
		if err != nil {
			return fmt.Errorf("failed to load ArxObject: %w", err)
		}

		// Display object information
		fmt.Printf("📋 ArxObject: %s\n", obj.ID)
		fmt.Printf("   Name: %s\n", obj.Name)
		fmt.Printf("   Type: %s\n", obj.Type)
		fmt.Printf("   Description: %s\n", obj.Description)
		fmt.Printf("   Status: %s\n", obj.Status)
		fmt.Printf("   Created: %s\n", obj.Created.Format("2006-01-02 15:04:05"))
		fmt.Printf("   Updated: %s\n", obj.Updated.Format("2006-01-02 15:04:05"))

		if obj.Location != nil {
			fmt.Printf("   Location: Floor %d, Room %s\n", obj.Location.Floor, obj.Location.Room)
		}

		if obj.ValidationStatus != "" {
			fmt.Printf("   Validation: %s (%.2f%% confidence)\n", obj.ValidationStatus, obj.Confidence*100)
		}

		if len(obj.Tags) > 0 {
			fmt.Printf("   Tags: %s\n", strings.Join(obj.Tags, ", "))
		}

		// Show properties
		if len(obj.Properties) > 0 {
			fmt.Printf("   Properties:\n")
			for key, value := range obj.Properties {
				fmt.Printf("     %s: %v\n", key, value)
			}
		}

		// Show relationships
		if len(obj.Relationships) > 0 {
			fmt.Printf("   Relationships:\n")
			for _, rel := range obj.Relationships {
				fmt.Printf("     %s -> %s (%s, %.2f%% confidence)\n",
					rel.Type, rel.TargetID, rel.Direction, rel.Confidence*100)
			}
		}

		// Show validations
		if len(obj.Validations) > 0 {
			fmt.Printf("   Validations:\n")
			for _, val := range obj.Validations {
				fmt.Printf("     %s by %s (%s, %.2f%% confidence)\n",
					val.Method, val.ValidatedBy, val.Status, val.Confidence*100)
			}
		}

		return nil
	},
}

// ArxObjectValidateCmd validates an ArxObject
var ArxObjectValidateCmd = &cobra.Command{
	Use:   "validate [object-id]",
	Short: "Validate an ArxObject",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		objectID := args[0]
		buildingID := extractBuildingID(objectID)

		method, _ := cmd.Flags().GetString("method")
		confidence, _ := cmd.Flags().GetFloat64("confidence")
		validatedBy, _ := cmd.Flags().GetString("by")
		notes, _ := cmd.Flags().GetString("notes")
		evidenceFile, _ := cmd.Flags().GetString("evidence")

		if method == "" {
			return fmt.Errorf("validation method is required (--method)")
		}

		if confidence <= 0 || confidence > 1 {
			return fmt.Errorf("confidence must be between 0 and 1 (--confidence)")
		}

		if validatedBy == "" {
			validatedBy = "cli_user"
		}

		// Prepare evidence
		evidence := make(map[string]interface{})
		if evidenceFile != "" {
			evidence["file"] = evidenceFile
			evidence["timestamp"] = time.Now().UTC()
		}

		manager := NewArxObjectManager(buildingID)
		if err := manager.ValidateArxObject(objectID, validatedBy, method, confidence, notes, evidence); err != nil {
			return fmt.Errorf("failed to validate ArxObject: %w", err)
		}

		fmt.Printf("✅ ArxObject %s validated successfully\n", objectID)
		fmt.Printf("   Method: %s\n", method)
		fmt.Printf("   Confidence: %.2f%%\n", confidence*100)
		fmt.Printf("   Validated by: %s\n", validatedBy)
		if notes != "" {
			fmt.Printf("   Notes: %s\n", notes)
		}

		return nil
	},
}

// ArxObjectRelateCmd manages relationships between ArxObjects
var ArxObjectRelateCmd = &cobra.Command{
	Use:   "relate [source-id] [target-id]",
	Short: "Manage relationships between ArxObjects",
	Args:  cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		sourceID := args[0]
		targetID := args[1]
		buildingID := extractBuildingID(sourceID)

		relType, _ := cmd.Flags().GetString("type")
		confidence, _ := cmd.Flags().GetFloat64("confidence")
		action, _ := cmd.Flags().GetString("action")

		if relType == "" {
			return fmt.Errorf("relationship type is required (--type)")
		}

		if confidence <= 0 || confidence > 1 {
			confidence = 0.8 // Default confidence
		}

		manager := NewArxObjectManager(buildingID)

		switch action {
		case "add", "":
			// Prepare properties
			properties := make(map[string]interface{})
			properties["created_by"] = "cli_user"
			properties["created_at"] = time.Now().UTC()

			if err := manager.AddRelationship(sourceID, targetID, relType, confidence, properties); err != nil {
				return fmt.Errorf("failed to add relationship: %w", err)
			}

			fmt.Printf("✅ Added relationship: %s %s -> %s\n", relType, sourceID, targetID)
			fmt.Printf("   Confidence: %.2f%%\n", confidence*100)

		case "remove":
			if err := manager.RemoveRelationship(sourceID, targetID, relType); err != nil {
				return fmt.Errorf("failed to remove relationship: %w", err)
			}

			fmt.Printf("✅ Removed relationship: %s %s -> %s\n", relType, sourceID, targetID)

		default:
			return fmt.Errorf("invalid action: %s. Use 'add' or 'remove'", action)
		}

		return nil
	},
}

// ArxObjectLifecycleCmd manages ArxObject lifecycle
var ArxObjectLifecycleCmd = &cobra.Command{
	Use:   "lifecycle [object-id]",
	Short: "Manage ArxObject lifecycle",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		objectID := args[0]
		buildingID := extractBuildingID(objectID)

		status, _ := cmd.Flags().GetString("status")
		phase, _ := cmd.Flags().GetString("phase")
		notes, _ := cmd.Flags().GetString("notes")

		if status == "" {
			return fmt.Errorf("status is required (--status)")
		}

		// Validate status
		validStatuses := []string{"active", "inactive", "retired", "maintenance", "testing"}
		statusValid := false
		for _, validStatus := range validStatuses {
			if status == validStatus {
				statusValid = true
				break
			}
		}
		if !statusValid {
			return fmt.Errorf("invalid status: %s. Valid statuses: %v", status, validStatuses)
		}

		manager := NewArxObjectManager(buildingID)
		if err := manager.UpdateArxObjectLifecycle(objectID, status, phase, notes); err != nil {
			return fmt.Errorf("failed to update lifecycle: %w", err)
		}

		fmt.Printf("✅ Updated lifecycle for ArxObject %s\n", objectID)
		fmt.Printf("   Status: %s\n", status)
		if phase != "" {
			fmt.Printf("   Phase: %s\n", phase)
		}
		if notes != "" {
			fmt.Printf("   Notes: %s\n", notes)
		}

		return nil
	},
}

// ArxObjectSearchCmd searches ArxObjects
var ArxObjectSearchCmd = &cobra.Command{
	Use:   "search [query]",
	Short: "Search ArxObjects",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		query := args[0]
		buildingID, _ := cmd.Flags().GetString("building")

		if buildingID == "" {
			return fmt.Errorf("building ID is required (--building)")
		}

		// Build filters
		filters := make(map[string]interface{})

		if objType, _ := cmd.Flags().GetString("type"); objType != "" {
			filters["type"] = objType
		}

		if status, _ := cmd.Flags().GetString("status"); status != "" {
			filters["status"] = status
		}

		if validationStatus, _ := cmd.Flags().GetString("validation"); validationStatus != "" {
			filters["validation_status"] = validationStatus
		}

		if floor, _ := cmd.Flags().GetInt("floor"); floor > 0 {
			filters["floor"] = floor
		}

		if confidenceMin, _ := cmd.Flags().GetFloat64("confidence-min"); confidenceMin > 0 {
			filters["confidence_min"] = confidenceMin
		}

		if tags, _ := cmd.Flags().GetStringSlice("tags"); len(tags) > 0 {
			filters["tags"] = tags
		}

		manager := NewArxObjectManager(buildingID)
		results, err := manager.SearchArxObjects(query, filters)
		if err != nil {
			return fmt.Errorf("failed to search ArxObjects: %w", err)
		}

		fmt.Printf("🔍 Search results for '%s': %d ArxObjects found\n", query, len(results))
		fmt.Println()

		for i, obj := range results {
			fmt.Printf("%d. %s (%s)\n", i+1, obj.Name, obj.ID)
			fmt.Printf("   Type: %s, Status: %s\n", obj.Type, obj.Status)
			if obj.Location != nil {
				fmt.Printf("   Location: Floor %d\n", obj.Location.Floor)
			}
			if obj.ValidationStatus != "" {
				fmt.Printf("   Validation: %s (%.2f%% confidence)\n", obj.ValidationStatus, obj.Confidence*100)
			}
			fmt.Println()
		}

		return nil
	},
}

// ArxObjectStatsCmd shows ArxObject statistics
var ArxObjectStatsCmd = &cobra.Command{
	Use:   "stats [building-id]",
	Short: "Show ArxObject statistics",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		buildingID := args[0]

		manager := NewArxObjectManager(buildingID)
		stats, err := manager.GetArxObjectStats()
		if err != nil {
			return fmt.Errorf("failed to get ArxObject stats: %w", err)
		}

		fmt.Printf("📊 ArxObject Statistics for %s\n", buildingID)
		fmt.Printf("   Total Count: %d\n", stats["total_count"])
		fmt.Printf("   Average Confidence: %.2f%%\n", stats["avg_confidence"].(float64)*100)
		fmt.Printf("   Validation Coverage: %.2f%%\n", stats["validation_coverage"].(float64)*100)
		fmt.Println()

		// Show breakdown by type
		if byType, ok := stats["by_type"].(map[string]int); ok {
			fmt.Println("   By Type:")
			for objType, count := range byType {
				fmt.Printf("     %s: %d\n", objType, count)
			}
			fmt.Println()
		}

		// Show breakdown by status
		if byStatus, ok := stats["by_status"].(map[string]int); ok {
			fmt.Println("   By Status:")
			for status, count := range byStatus {
				fmt.Printf("     %s: %d\n", status, count)
			}
			fmt.Println()
		}

		// Show breakdown by floor
		if byFloor, ok := stats["by_floor"].(map[int]int); ok {
			fmt.Println("   By Floor:")
			for floor, count := range byFloor {
				fmt.Printf("     Floor %d: %d\n", floor, count)
			}
		}

		return nil
	},
}

// ArxObjectExportCmd exports ArxObjects
var ArxObjectExportCmd = &cobra.Command{
	Use:   "export [building-id]",
	Short: "Export ArxObjects",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		buildingID := args[0]
		format, _ := cmd.Flags().GetString("format")
		outputFile, _ := cmd.Flags().GetString("output")

		if format == "" {
			format = "json"
		}

		// Build filters
		filters := make(map[string]interface{})

		if objType, _ := cmd.Flags().GetString("type"); objType != "" {
			filters["type"] = objType
		}

		if status, _ := cmd.Flags().GetString("status"); status != "" {
			filters["status"] = status
		}

		if floor, _ := cmd.Flags().GetInt("floor"); floor > 0 {
			filters["floor"] = floor
		}

		manager := NewArxObjectManager(buildingID)
		data, err := manager.ExportArxObjects(format, filters)
		if err != nil {
			return fmt.Errorf("failed to export ArxObjects: %w", err)
		}

		if outputFile != "" {
			// Write to file
			if err := os.WriteFile(outputFile, data, 0644); err != nil {
				return fmt.Errorf("failed to write output file: %w", err)
			}
			fmt.Printf("✅ Exported ArxObjects to %s (%s format)\n", outputFile, format)
		} else {
			// Write to stdout
			fmt.Println(string(data))
		}

		return nil
	},
}

// extractBuildingID extracts the building ID from an object ID
func extractBuildingID(objectID string) string {
	parts := strings.Split(objectID, ":")
	if len(parts) >= 2 {
		return fmt.Sprintf("%s:%s", parts[0], parts[1])
	}
	return objectID
}

func init() {
	// Add ArxObject command to root
	ArxObjectCmd.AddCommand(ArxObjectShowCmd)
	ArxObjectCmd.AddCommand(ArxObjectValidateCmd)
	ArxObjectCmd.AddCommand(ArxObjectRelateCmd)
	ArxObjectCmd.AddCommand(ArxObjectLifecycleCmd)
	ArxObjectCmd.AddCommand(ArxObjectSearchCmd)
	ArxObjectCmd.AddCommand(ArxObjectStatsCmd)
	ArxObjectCmd.AddCommand(ArxObjectExportCmd)

	// ArxObjectValidateCmd flags
	ArxObjectValidateCmd.Flags().String("method", "", "Validation method (photo, lidar, manual, etc.)")
	ArxObjectValidateCmd.Flags().Float64("confidence", 0.9, "Confidence level (0.0 to 1.0)")
	ArxObjectValidateCmd.Flags().String("by", "", "Who performed the validation")
	ArxObjectValidateCmd.Flags().String("notes", "", "Validation notes")
	ArxObjectValidateCmd.Flags().String("evidence", "", "Evidence file path")

	// ArxObjectRelateCmd flags
	ArxObjectRelateCmd.Flags().String("type", "", "Relationship type (contains, connects_to, adjacent_to, etc.)")
	ArxObjectRelateCmd.Flags().Float64("confidence", 0.8, "Relationship confidence (0.0 to 1.0)")
	ArxObjectRelateCmd.Flags().String("action", "add", "Action to perform (add, remove)")

	// ArxObjectLifecycleCmd flags
	ArxObjectLifecycleCmd.Flags().String("status", "", "Lifecycle status (active, inactive, retired, maintenance, testing)")
	ArxObjectLifecycleCmd.Flags().String("phase", "", "Lifecycle phase")
	ArxObjectLifecycleCmd.Flags().String("notes", "", "Lifecycle notes")

	// ArxObjectSearchCmd flags
	ArxObjectSearchCmd.Flags().String("building", "", "Building ID to search in")
	ArxObjectSearchCmd.Flags().String("type", "", "Filter by object type")
	ArxObjectSearchCmd.Flags().String("status", "", "Filter by status")
	ArxObjectSearchCmd.Flags().String("validation", "", "Filter by validation status")
	ArxObjectSearchCmd.Flags().Int("floor", 0, "Filter by floor number")
	ArxObjectSearchCmd.Flags().Float64("confidence-min", 0.0, "Minimum confidence threshold")
	ArxObjectSearchCmd.Flags().StringSlice("tags", []string{}, "Filter by tags")

	// ArxObjectExportCmd flags
	ArxObjectExportCmd.Flags().String("format", "json", "Export format (json, csv)")
	ArxObjectExportCmd.Flags().String("output", "", "Output file path (default: stdout)")
	ArxObjectExportCmd.Flags().String("type", "", "Filter by object type")
	ArxObjectExportCmd.Flags().String("status", "", "Filter by status")
	ArxObjectExportCmd.Flags().Int("floor", 0, "Filter by floor number")
}
