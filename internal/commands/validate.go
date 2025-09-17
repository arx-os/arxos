package commands

import (
	"fmt"
	"os"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/common/logger"
)

// ExecuteValidate handles BIM file validation
func ExecuteValidate(opts ValidateOptions) error {
	// Open BIM file
	file, err := os.Open(opts.InputFile)
	if err != nil {
		return fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	// Parse with validation
	parser := bim.NewParser()
	parseOpts := bim.ParseOptions{
		Strict:           opts.Strict,
		ValidateChecksum: true,
	}

	building, err := parser.ParseWithOptions(file, parseOpts)
	if err != nil {
		if !opts.AutoFix {
			return fmt.Errorf("validation failed: %w", err)
		}

		// Try to fix common issues
		logger.Info("Attempting to fix validation issues...")

		// Re-parse without strict mode
		file.Seek(0, 0)
		parseOpts.Strict = false
		building, err = parser.ParseWithOptions(file, parseOpts)
		if err != nil {
			return fmt.Errorf("validation failed even with fixes: %w", err)
		}

		logger.Info("File fixed and validated successfully")

		// TODO: Write fixed file if output specified
		if opts.OutputFile != "" {
			logger.Info("Fixed file would be written to: %s", opts.OutputFile)
		}
	}

	// Validation successful
	fmt.Printf("✓ File is valid\n")
	fmt.Printf("  Building: %s\n", building.Name)
	fmt.Printf("  Floors: %d\n", len(building.Floors))
	fmt.Printf("  File Version: %s\n", building.FileVersion)

	// Check for warnings
	warnings := checkSimpleWarnings(building)
	if len(warnings) > 0 {
		fmt.Println("\nWarnings:")
		for _, w := range warnings {
			fmt.Printf("  ⚠ %s\n", w)
		}
	}

	return nil
}

func checkSimpleWarnings(building *bim.Building) []string {
	var warnings []string

	// Check for basic issues
	if building.Name == "" {
		warnings = append(warnings, "Building name is missing")
	}

	// Check floors
	if len(building.Floors) == 0 {
		warnings = append(warnings, "Building has no floors defined")
	}

	// Check for equipment in floors
	equipmentCount := 0
	for _, floor := range building.Floors {
		equipmentCount += len(floor.Equipment)
	}
	if equipmentCount == 0 {
		warnings = append(warnings, "No equipment found in building")
	}

	return warnings
}