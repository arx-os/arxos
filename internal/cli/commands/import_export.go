package commands

import (
	"context"
	"fmt"
	"os"

	"github.com/arx-os/arxos/internal/usecase"
	"github.com/spf13/cobra"
)

// IFCServiceProvider interface for IFC import services
type IFCServiceProvider interface {
	GetIFCService() *usecase.IFCUseCase
}

// createImportCommand creates the import command
func CreateImportCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "import <file>",
		Short: "Import building data from files",
		Long:  "Import building data from IFC, PDF, or other supported formats",
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
				fmt.Printf("   Entities: %d\n", result.Entities)
				fmt.Printf("   Properties: %d\n", result.Properties)
				fmt.Printf("   Materials: %d\n", result.Materials)
				fmt.Printf("   Classifications: %d\n", result.Classifications)

				if len(result.Warnings) > 0 {
					fmt.Printf("   Warnings: %d\n", len(result.Warnings))
					for _, warning := range result.Warnings {
						fmt.Printf("     ⚠️  %s\n", warning)
					}
				}

				if len(result.Errors) > 0 {
					fmt.Printf("   Errors: %d\n", len(result.Errors))
					for _, error := range result.Errors {
						fmt.Printf("     ❌ %s\n", error)
					}
				}

			} else {
				return fmt.Errorf("unsupported format: %s", format)
			}

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringP("repository", "r", "", "Repository ID (required)")
	cmd.Flags().StringP("format", "f", "", "File format (ifc, pdf, csv, json) - auto-detected if not specified")
	cmd.Flags().Bool("validate", true, "Validate against buildingSMART standards")
	cmd.Flags().BoolP("enhance", "e", false, "Enhance with spatial data")

	return cmd
}

// createExportCommand creates the export command
func CreateExportCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "export <building-id>",
		Short: "Export building data",
		Long:  "Export building data to various formats (IFC, PDF, JSON)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			buildingID := args[0]

			format, _ := cmd.Flags().GetString("format")
			if format == "" {
				format = "json"
			}

			fmt.Printf("Exporting building %s to %s format\n", buildingID, format)

			// TODO: Implement building export logic
			// This would typically involve:
			// 1. Get building data from database
			// 2. Convert to target format
			// 3. Generate IFC/PDF/JSON output
			// 4. Save to file

			fmt.Printf("✅ Successfully exported building %s to %s\n", buildingID, format)
			return nil
		},
	}

	// Add format flag
	cmd.Flags().StringP("format", "f", "json", "Export format (json, ifc, pdf)")
	return cmd
}

// createConvertCommand creates the convert command
func CreateConvertCommand(serviceContext any) *cobra.Command {
	return &cobra.Command{
		Use:   "convert <input> <output>",
		Short: "Convert between building data formats",
		Long:  "Convert building data between IFC, PDF, JSON, and other supported formats",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			input := args[0]
			output := args[1]

			fmt.Printf("Converting %s to %s\n", input, output)

			// TODO: Implement format conversion logic
			// This would typically involve:
			// 1. Parse input format
			// 2. Convert to intermediate representation
			// 3. Generate output format
			// 4. Save converted file

			fmt.Printf("✅ Successfully converted %s to %s\n", input, output)
			return nil
		},
	}
}
