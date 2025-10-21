package integration

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain/bas"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/spf13/cobra"
)

// newBASImportCommand creates the bas import subcommand
func newBASImportCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "import <file>",
		Short: "Import BAS points from CSV export",
		Long: `Import BAS control points from a CSV export file.

Supported formats:
  - Johnson Controls Metasys CSV exports
  - Siemens Desigo point lists
  - Honeywell EBI exports
  - Tridium Niagara CSV exports
  - Generic CSV with columns: Point Name, Device, Type, Description, Location

Examples:
  arx bas import metasys-export.csv --building bldg-001 --system metasys
  arx bas import points.csv --building bldg-001 --system desigo --auto-map
  arx bas import hvac-points.csv --building bldg-001 --repo repo-001 --commit`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			filePath := args[0]
			buildingID, _ := cmd.Flags().GetString("building")
			systemType, _ := cmd.Flags().GetString("system")
			autoMap, _ := cmd.Flags().GetBool("auto-map")
			autoCommit, _ := cmd.Flags().GetBool("commit")
			repoID, _ := cmd.Flags().GetString("repo")

			// Validate required flags
			if buildingID == "" {
				return fmt.Errorf("--building flag is required")
			}

			// Try to use real implementation via container
			return runBASImportReal(cmd.Context(), serviceContext, filePath, buildingID, systemType, autoMap, autoCommit, repoID)
		},
	}

	cmd.Flags().String("building", "", "Building ID (required)")
	cmd.Flags().String("system", "generic_bas", "BAS system type (metasys, desigo, honeywell, niagara, generic_bas)")
	cmd.Flags().Bool("auto-map", true, "Auto-map points to rooms/equipment")
	cmd.Flags().Bool("commit", false, "Auto-commit changes")
	cmd.Flags().String("repo", "", "Repository ID (optional, will be inferred from building)")

	return cmd
}

// runBASImportReal executes the real BAS import using the container
func runBASImportReal(ctx context.Context, container any, filePath, buildingID, systemType string, autoMap, autoCommit bool, repoID string) error {
	// Cast to container provider
	cp, ok := container.(ContainerProvider)
	if !ok {
		return fmt.Errorf("container doesn't implement BAS interface - database not initialized properly")
	}

	// Get BASImportUseCase from container
	basImportUC := cp.GetBASImportUseCase()
	if basImportUC == nil {
		return fmt.Errorf("BAS import use case not initialized - check database connection")
	}

	fmt.Printf("   ✅ Using BAS import system\n")

	// Get or create BAS system
	basSystemRepo := cp.GetBASSystemRepository()
	if basSystemRepo == nil {
		fmt.Printf("   ❌ BAS system repository not available\n")
		return fmt.Errorf("BAS system repository not available")
	}
	fmt.Printf("   ℹ️  Creating/getting BAS system...\n")

	basSystemID, err := getOrCreateBASSystem(ctx, basSystemRepo, types.FromString(buildingID), parseBASSystemType(systemType), systemType)
	if err != nil {
		fmt.Printf("   ❌ Failed to create BAS system: %v\n", err)
		return fmt.Errorf("failed to get/create BAS system: %w", err)
	}
	fmt.Printf("   ℹ️  BAS System ID: %s\n", basSystemID)

	// Build import request
	req := bas.ImportBASPointsRequest{
		FilePath:    filePath,
		BuildingID:  types.FromString(buildingID),
		BASSystemID: basSystemID,
		SystemType:  parseBASSystemType(systemType),
		AutoMap:     autoMap,
		AutoCommit:  autoCommit,
	}

	// Set repository ID if provided
	if repoID != "" {
		rid := types.FromString(repoID)
		req.RepositoryID = &rid
	}

	fmt.Printf("🔍 Analyzing BAS export file...\n")
	fmt.Printf("   File: %s\n", filepath.Base(filePath))
	fmt.Printf("   Building: %s\n", buildingID)
	fmt.Printf("   System: %s\n", systemType)
	fmt.Printf("\n")

	// Execute import
	fmt.Printf("\n")
	result, err := basImportUC.ImportBASPoints(ctx, req)
	if err != nil {
		fmt.Printf("❌ BAS import failed: %v\n", err)
		return fmt.Errorf("BAS import failed: %w", err)
	}

	// Display results
	fmt.Printf("✅ BAS import complete!\n")
	fmt.Printf("\n")
	fmt.Printf("Results:\n")
	fmt.Printf("   Points added: %d\n", result.PointsAdded)
	fmt.Printf("   Points modified: %d\n", result.PointsModified)
	fmt.Printf("   Points deleted: %d\n", result.PointsDeleted)
	fmt.Printf("   Points mapped: %d\n", result.PointsMapped)
	fmt.Printf("   Points unmapped: %d\n", result.PointsUnmapped)
	fmt.Printf("   Duration: %dms\n", result.DurationMS)
	fmt.Printf("   Status: %s\n", result.Status)
	fmt.Printf("\n")

	if result.PointsUnmapped > 0 {
		fmt.Printf("Next steps:\n")
		fmt.Printf("  • Map unmapped points: arx bas unmapped --building %s\n", buildingID)
		fmt.Printf("  • Map specific point: arx bas map <point-id> --room <room-id>\n")
	}

	return nil
}

// parseBASSystemType converts string to BASSystemType
func parseBASSystemType(systemType string) bas.BASSystemType {
	switch strings.ToLower(systemType) {
	case "metasys", "johnson_controls_metasys":
		return bas.BASSystemTypeMetasys
	case "desigo", "siemens_desigo":
		return bas.BASSystemTypeDesigo
	case "honeywell", "honeywell_ebi":
		return bas.BASSystemTypeHoneywell
	case "niagara", "tridium_niagara":
		return bas.BASSystemTypeNiagara
	case "schneider", "schneider_electric":
		return bas.BASSystemTypeSchneiderElectric
	default:
		return bas.BASSystemTypeOther
	}
}

// getOrCreateBASSystem gets an existing BAS system or creates a new one
func getOrCreateBASSystem(ctx context.Context, repo bas.BASSystemRepository, buildingID types.ID, systemType bas.BASSystemType, systemTypeStr string) (types.ID, error) {
	// List systems for building using the List method
	systems, err := repo.List(buildingID)
	if err != nil {
		return types.ID{}, fmt.Errorf("failed to list BAS systems: %w", err)
	}

	// Find system by type
	for _, system := range systems {
		if system.SystemType == systemType {
			fmt.Printf("   ✅ Using existing BAS system: %s (ID: %s)\n", system.Name, system.ID.String())
			return system.ID, nil
		}
	}

	// Create new system
	systemID := types.NewID()
	now := time.Now()

	// Create a safe name that includes timestamp to ensure uniqueness
	systemName := fmt.Sprintf("%s System - %s", strings.Title(systemTypeStr), time.Now().Format("2006-01-02"))

	system := &bas.BASSystem{
		ID:         systemID,
		BuildingID: buildingID,
		Name:       systemName,
		SystemType: systemType,
		Enabled:    true,
		ReadOnly:   true,
		Metadata:   make(map[string]any), // Initialize empty map
		CreatedAt:  now,
		UpdatedAt:  now,
	}

	if err := repo.Create(system); err != nil {
		return types.ID{}, fmt.Errorf("failed to create BAS system: %w", err)
	}

	fmt.Printf("   ✅ Created BAS system: %s\n", system.Name)
	return systemID, nil
}
