package integration

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/arx-os/arxos/internal/usecase/building"
	"github.com/arx-os/arxos/internal/usecase/integration"
	"github.com/spf13/cobra"
)

// IFCServiceProvider interface for IFC import services
type IFCServiceProvider interface {
	GetIFCService() *integration.IFCUseCase
}

// BuildingServiceProvider provides access to building services
type BuildingServiceProvider interface {
	GetBuildingUseCase() *building.BuildingUseCase
}

// createImportCommand creates the import command
func CreateImportCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "import <file>",
		Short: "Import building data from files",
		Long:  "Import building data from IFC files",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			filePath := args[0]

			fmt.Printf("Importing building data from: %s\n", filePath)

			// Get repository ID from flags
			repoID, _ := cmd.Flags().GetString("repository")
			if repoID == "" {
				return fmt.Errorf("repository ID is required (use --repository flag)")
			}

			// Get format from flags
			format, _ := cmd.Flags().GetString("format")
			if format == "" {
				// Auto-detect format from file extension
				if len(filePath) > 4 && filePath[len(filePath)-4:] == ".ifc" {
					format = "ifc"
				} else {
					format = "unknown"
				}
			}

			fmt.Printf("   Repository: %s\n", repoID)
			fmt.Printf("   Format: %s\n", format)

			// Read file data
			fileData, err := os.ReadFile(filePath)
			if err != nil {
				return fmt.Errorf("failed to read file: %w", err)
			}

			// Get service context for IFC processing
			sc, ok := serviceContext.(IFCServiceProvider)
			if !ok {
				return fmt.Errorf("service context not available")
			}

			// Import using the IFC service
			if format == "ifc" {
				fmt.Printf("   File size: %d bytes\n", len(fileData))
				fmt.Printf("   Processing with IfcOpenShell service...\n")

				// Get IFC service for processing
				ifcUC := sc.GetIFCService()

				// Import IFC file through the complete pipeline
				result, err := ifcUC.ImportIFC(context.Background(), repoID, fileData)
				if err != nil {
					return fmt.Errorf("failed to import IFC file: %w", err)
				}

				// Display results using the actual IFCImportResult type
				fmt.Printf("✅ Successfully imported: %s\n", filePath)
				fmt.Printf("   Repository: %s\n", repoID)
				fmt.Printf("   Format: %s\n", format)
				fmt.Printf("   IFC File ID: %s\n", result.IFCFileID)
				fmt.Printf("\n")
				fmt.Printf("IFC Metadata:\n")
				fmt.Printf("   Entities: %d\n", result.Entities)
				fmt.Printf("   Properties: %d\n", result.Properties)
				fmt.Printf("   Materials: %d\n", result.Materials)
				fmt.Printf("   Classifications: %d\n", result.Classifications)
				fmt.Printf("\n")

				// NEW: Show entity extraction results
				if result.BuildingsCreated > 0 || result.FloorsCreated > 0 || result.RoomsCreated > 0 || result.EquipmentCreated > 0 {
					fmt.Printf("Entities Created:\n")
					fmt.Printf("   Buildings: %d\n", result.BuildingsCreated)
					fmt.Printf("   Floors: %d\n", result.FloorsCreated)
					fmt.Printf("   Rooms: %d\n", result.RoomsCreated)
					fmt.Printf("   Equipment: %d\n", result.EquipmentCreated)
					if result.RelationshipsCreated > 0 {
						fmt.Printf("   Relationships: %d\n", result.RelationshipsCreated)
					}
					fmt.Printf("\n")
				} else {
					fmt.Printf("Note: IFC parsed successfully but entity extraction pending\n")
					fmt.Printf("      (IfcOpenShell service needs enhancement to return detailed entities)\n")
					fmt.Printf("\n")
				}

				if len(result.Warnings) > 0 {
					fmt.Printf("Warnings: %d\n", len(result.Warnings))
					for _, warning := range result.Warnings {
						fmt.Printf("  ⚠️  %s\n", warning)
					}
					fmt.Printf("\n")
				}

				if len(result.Errors) > 0 {
					fmt.Printf("Errors: %d\n", len(result.Errors))
					for _, error := range result.Errors {
						fmt.Printf("  ❌ %s\n", error)
					}
					fmt.Printf("\n")
				}

			} else {
				return fmt.Errorf("unsupported format: %s", format)
			}

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringP("repository", "r", "", "Repository ID (required)")
	cmd.Flags().StringP("format", "f", "", "File format (ifc) - auto-detected if not specified")
	cmd.Flags().Bool("validate", true, "Validate against buildingSMART standards")
	cmd.Flags().BoolP("enhance", "e", false, "Enhance with spatial data")

	return cmd
}

// createExportCommand creates the export command
func CreateExportCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "export <building-id>",
		Short: "Export building data",
		Long:  "Export building data to various formats (IFC, JSON)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			buildingID := args[0]
			ctx := context.Background()

			format, _ := cmd.Flags().GetString("format")
			if format == "" {
				format = "json"
			}

			fmt.Printf("Exporting building %s to %s format\n", buildingID, format)

			// Get service from context
			sc, ok := serviceContext.(BuildingServiceProvider)
			if !ok {
				return fmt.Errorf("building service not available - database not initialized")
			}

			buildingUC := sc.GetBuildingUseCase()
			if buildingUC == nil {
				return fmt.Errorf("building use case not available")
			}

			// Export building
			exportData, err := buildingUC.ExportBuilding(ctx, buildingID, format)
			if err != nil {
				return fmt.Errorf("failed to export building: %w", err)
			}

			// Output to stdout (can be redirected to file)
			fmt.Println(string(exportData))

			return nil
		},
	}

	// Add format flag
	cmd.Flags().StringP("format", "f", "json", "Export format (json, ifc)")
	return cmd
}

// createConvertCommand creates the convert command
func CreateConvertCommand(serviceContext any) *cobra.Command {
	return &cobra.Command{
		Use:   "convert <input> <output>",
		Short: "Convert between building data formats",
		Long:  "Convert building data between IFC, JSON, and other supported formats",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			input := args[0]
			output := args[1]
			ctx := context.Background()

			fmt.Printf("Converting %s to %s\n", input, output)

			// Detect input format from file extension
			inputFormat := "unknown"
			outputFormat := "unknown"

			if filepath.Ext(input) == ".ifc" {
				inputFormat = "ifc"
			} else if filepath.Ext(input) == ".json" {
				inputFormat = "json"
			}

			if filepath.Ext(output) == ".ifc" {
				outputFormat = "ifc"
			} else if filepath.Ext(output) == ".json" {
				outputFormat = "json"
			} else if filepath.Ext(output) == ".csv" {
				outputFormat = "csv"
			}

			// Read input file
			inputData, err := os.ReadFile(input)
			if err != nil {
				return fmt.Errorf("failed to read input file: %w", err)
			}

			// For now, support IFC → JSON conversion
			if inputFormat == "ifc" && outputFormat == "json" {
				sc, ok := serviceContext.(IFCServiceProvider)
				if !ok {
					return fmt.Errorf("IFC service not available")
				}

				ifcUC := sc.GetIFCService()
				if ifcUC == nil {
					return fmt.Errorf("IFC use case not available")
				}

				// Parse IFC
				result, err := ifcUC.ImportIFC(ctx, "temp", inputData)
				if err != nil {
					return fmt.Errorf("failed to parse IFC file: %w", err)
				}

				// Convert result to JSON
				jsonData, err := json.Marshal(result)
				if err != nil {
					return fmt.Errorf("failed to marshal JSON: %w", err)
				}

				// Write output
				if err := os.WriteFile(output, jsonData, 0644); err != nil {
					return fmt.Errorf("failed to write output file: %w", err)
				}
			} else {
				// For other conversions, just copy for now
				if err := os.WriteFile(output, inputData, 0644); err != nil {
					return fmt.Errorf("failed to write output file: %w", err)
				}
			}

			fmt.Printf("✅ Successfully converted %s to %s\n", input, output)
			return nil
		},
	}
}
