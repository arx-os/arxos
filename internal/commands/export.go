package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	// "github.com/arx-os/arxos/internal/simulation" // TODO: Implement simulation package
	"github.com/arx-os/arxos/pkg/models"
)

// ExecuteExport handles the export command with intelligence
func ExecuteExport(opts ExportOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewPostGISConnection(ctx)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Load building from database
	building, err := db.GetFloorPlan(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to load building: %w", err)
	}

	// Run simulations if requested
	// TODO: Implement simulation when package is available
	if opts.SimulateBeforeExp || opts.IncludeIntel {
		logger.Warn("Simulation feature not yet implemented")
		return fmt.Errorf("simulation feature not yet implemented")
	}

	// Export based on format
	switch opts.Format {
	case "bim":
		return exportBIM(building, nil, opts)
	case "json":
		return exportJSON(building, nil, opts)
	case "pdf":
		return fmt.Errorf("PDF export not yet implemented")
	case "csv":
		return fmt.Errorf("CSV export not yet implemented")
	default:
		return fmt.Errorf("unsupported format: %s", opts.Format)
	}
}

func exportBIM(building *models.FloorPlan, simResults interface{}, opts ExportOptions) error {
	// Convert to BIM format
	bimBuilding := convertToSimpleBIM(building)

	// Add intelligence data if available
	if simResults != nil && opts.IncludeIntel {
		enrichBIMWithIntelligence(bimBuilding, simResults)
	}

	// Write output
	output := os.Stdout
	if opts.OutputFile != "" {
		var err error
		output, err = os.Create(opts.OutputFile)
		if err != nil {
			return fmt.Errorf("failed to create output file: %w", err)
		}
		defer output.Close()
	}

	// Write as JSON for SimpleBuilding
	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(bimBuilding); err != nil {
		return fmt.Errorf("failed to write BIM: %w", err)
	}

	logger.Info("Exported building %s to BIM format", opts.BuildingID)
	return nil
}

func exportJSON(building *models.FloorPlan, simResults interface{}, opts ExportOptions) error {
	// Create export structure
	export := map[string]interface{}{
		"building": building,
	}

	if simResults != nil && opts.IncludeIntel {
		export["intelligence"] = simResults
	}

	// Write JSON
	output := os.Stdout
	if opts.OutputFile != "" {
		var err error
		output, err = os.Create(opts.OutputFile)
		if err != nil {
			return fmt.Errorf("failed to create output file: %w", err)
		}
		defer output.Close()
	}

	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")

	if err := encoder.Encode(export); err != nil {
		return fmt.Errorf("failed to write JSON: %w", err)
	}

	return nil
}

func convertToSimpleBIM(fp *models.FloorPlan) *bim.SimpleBuilding {
	building := bim.NewSimpleBuilding(fp.Name, fp.ID)

	for _, eq := range fp.Equipment {
		path := eq.Path
		if path == "" && eq.Location != nil {
			// Generate path from location if not set
			path = fmt.Sprintf("N/1/%d/%d", int(eq.Location.X), int(eq.Location.Y))
		}
		building.AddEquipment(eq.ID, eq.Type, path, eq.Status)
	}

	return building
}

func enrichBIMWithIntelligence(building *bim.SimpleBuilding, results interface{}) {
	// TODO: Add simulation data when simulation package is implemented
	logger.Debug("Simulation enrichment not yet implemented")
}

func saveSimulationResults(ctx context.Context, db *database.PostGISDB, buildingID string, results interface{}) error {
	// TODO: Save simulation results when simulation package is implemented
	logger.Debug("Simulation results saving not yet implemented")
	return nil
}
