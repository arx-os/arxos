package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/converter"
	"github.com/spf13/cobra"
)

var convertCmd = &cobra.Command{
	Use:   "convert <input-file> [output-file]",
	Short: "Convert between building file formats",
	Long: `Convert between building file formats and ArxOS BIM format.

Supported input formats:
  - IFC (Industry Foundation Classes)
  - PDF (floor plans, as-builts)

The converter automatically detects the input format and converts to .bim.txt
If no output file is specified, it uses the input filename with .bim.txt extension.`,
	Args: cobra.RangeArgs(1, 2),
	RunE: runConvert,
}

var convertListCmd = &cobra.Command{
	Use:   "list",
	Short: "List supported file formats",
	RunE:  runConvertList,
}

var (
	convertForce bool
	convertMerge bool
)

func init() {
	convertCmd.AddCommand(convertListCmd)

	convertCmd.Flags().BoolVar(&convertForce, "force", false, "Overwrite output file if it exists")
	convertCmd.Flags().BoolVar(&convertMerge, "merge", false, "Merge with existing BIM file")
}

func runConvert(cmd *cobra.Command, args []string) error {
	inputFile := args[0]
	outputFile := ""

	if len(args) > 1 {
		outputFile = args[1]
	} else {
		// Generate output filename
		base := strings.TrimSuffix(filepath.Base(inputFile), filepath.Ext(inputFile))
		outputFile = base + ".bim.txt"
	}

	// Check if input file exists
	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		return fmt.Errorf("input file not found: %s\n\nPlease check that:\n  • The file path is correct\n  • You have read permissions\n  • The file exists in the specified location", inputFile)
	}

	// Check if output file exists
	if !convertForce {
		if _, err := os.Stat(outputFile); err == nil {
			return fmt.Errorf("output file already exists: %s\n\nTo continue, either:\n  • Use --force to overwrite: arx convert %s %s --force\n  • Choose a different output file: arx convert %s new_name.bim.txt\n  • Remove the existing file first", outputFile, inputFile, outputFile, inputFile)
		}
	}

	// Create converter registry
	registry := converter.NewRegistry()

	// Get appropriate converter
	conv, err := registry.GetConverter(inputFile)
	if err != nil {
		ext := strings.ToLower(filepath.Ext(inputFile))
		return fmt.Errorf("unsupported file format: %s\n\nCurrently supported formats:\n  • PDF (.pdf) - Floor plans and as-built drawings\n  • IFC (.ifc, .ifcxml, .ifczip) - Building Information Models\n\nTo see all supported formats: arx convert list", ext)
	}

	logger.Info("Converting %s to BIM format...", inputFile)
	logger.Info("Using converter: %s", conv.GetDescription())

	// Open input file
	input, err := os.Open(inputFile)
	if err != nil {
		return fmt.Errorf("failed to open input file: %w", err)
	}
	defer input.Close()

	// Handle merge if requested
	if convertMerge && fileExists(outputFile) {
		// Create temp file for conversion
		tempFile := outputFile + ".tmp"
		tempOutput, err := os.Create(tempFile)
		if err != nil {
			return fmt.Errorf("failed to create temp file: %w", err)
		}

		// Convert to temp file
		if err := conv.ConvertToBIM(input, tempOutput); err != nil {
			tempOutput.Close()
			os.Remove(tempFile)
			return fmt.Errorf("conversion failed: %w", err)
		}
		tempOutput.Close()

		// Merge files
		if err := mergeBIMFiles(outputFile, tempFile, outputFile); err != nil {
			os.Remove(tempFile)
			return fmt.Errorf("merge failed: %w", err)
		}

		os.Remove(tempFile)
		logger.Info("✅ Merged into %s", outputFile)
	} else {
		// Create output file
		output, err := os.Create(outputFile)
		if err != nil {
			return fmt.Errorf("failed to create output file: %w", err)
		}
		defer output.Close()

		// Convert
		if err := conv.ConvertToBIM(input, output); err != nil {
			return fmt.Errorf("conversion failed: %w", err)
		}

		logger.Info("✅ Converted to %s", outputFile)
	}

	// Show summary
	info, _ := os.Stat(outputFile)
	if info != nil {
		logger.Info("Output file size: %.2f KB", float64(info.Size())/1024)
	}

	logger.Info("Conversion complete")

	return nil
}

func runConvertList(cmd *cobra.Command, args []string) error {
	fmt.Println("\nSupported File Formats for Conversion:")

	formats := []struct {
		name string
		exts string
		desc string
	}{
		{"IFC", ".ifc, .ifcxml, .ifczip", "Industry Foundation Classes - Open BIM standard"},
		{"PDF", ".pdf", "Floor plans, as-builts with text extraction"},
	}

	for _, f := range formats {
		fmt.Printf("  \033[1;33m%-12s\033[0m %s\n", f.name, f.exts)
		fmt.Printf("               %s\n\n", f.desc)
	}

	fmt.Println("\nConversion Examples:")
	fmt.Println("  arx convert floor_plan.pdf")
	fmt.Println("  arx convert model.ifc building.bim.txt")
	fmt.Println("  arx convert file.pdf --force")

	return nil
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func mergeBIMFiles(file1, file2, output string) error {
	// Read both files
	content1, err := os.ReadFile(file1)
	if err != nil {
		return err
	}

	content2, err := os.ReadFile(file2)
	if err != nil {
		return err
	}

	// Simple merge: append content2 to content1
	merged := string(content1) + "\n\n# === Merged from " + file2 + " ===\n\n" + string(content2)

	return os.WriteFile(output, []byte(merged), 0644)
}
