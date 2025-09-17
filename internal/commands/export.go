package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/simulation"
	"github.com/arx-os/arxos/pkg/models"
)

// ExecuteExport handles the export command with intelligence
func ExecuteExport(opts ExportOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewSQLiteDBFromPath("arxos.db")
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
	var simResults *simulation.Results
	if opts.SimulateBeforeExp || opts.IncludeIntel {
		logger.Info("Running simulations for building %s...", opts.BuildingID)

		engine := simulation.NewEngine()
		simResults, err = engine.Analyze(building)
		if err != nil {
			return fmt.Errorf("simulation failed: %w", err)
		}

		// Save simulation results to database
		if err := saveSimulationResults(ctx, db, opts.BuildingID, simResults); err != nil {
			logger.Warn("Failed to save simulation results: %v", err)
		}
	}

	// Export based on format
	switch opts.Format {
	case "bim":
		return exportBIM(building, simResults, opts)
	case "json":
		return exportJSON(building, simResults, opts)
	case "pdf":
		return fmt.Errorf("PDF export not yet implemented")
	case "csv":
		return fmt.Errorf("CSV export not yet implemented")
	default:
		return fmt.Errorf("unsupported format: %s", opts.Format)
	}
}

func exportBIM(building *models.FloorPlan, simResults *simulation.Results, opts ExportOptions) error {
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

func exportJSON(building *models.FloorPlan, simResults *simulation.Results, opts ExportOptions) error {
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

func enrichBIMWithIntelligence(building *bim.SimpleBuilding, results *simulation.Results) {
	// Add simulation data to each equipment
	for i := range building.Equipment {
		eq := &building.Equipment[i]

		// Find matching simulation data
		if eqSim, ok := results.EquipmentAnalysis[eq.ID]; ok {
			// Add intelligence fields
			if eq.Extensions == nil {
				eq.Extensions = make(map[string]interface{})
			}

			eq.Extensions["intelligence"] = map[string]interface{}{
				"energy_flow":          eqSim.EnergyFlow,
				"particle_load":        eqSim.ParticleLoad,
				"maintenance_due":      eqSim.NextMaintenance,
				"failure_probability":  eqSim.FailureProbability,
				"efficiency_score":     eqSim.EfficiencyScore,
			}

			// Update status based on simulation
			if eqSim.FailureProbability > 0.5 {
				eq.Status = models.StatusFailed
			} else if eqSim.FailureProbability > 0.3 {
				eq.Status = models.StatusDegraded
			}
		}
	}

	// Add overall building intelligence
	if building.Metadata == nil {
		building.Metadata = make(map[string]interface{})
	}

	building.Metadata["simulation_results"] = map[string]interface{}{
		"timestamp":           results.Timestamp,
		"total_energy_flow":   results.TotalEnergyFlow,
		"average_efficiency":  results.AverageEfficiency,
		"critical_issues":     results.CriticalIssues,
		"recommendations":     results.Recommendations,
	}
}

func saveSimulationResults(ctx context.Context, db *database.SQLiteDB, buildingID string, results *simulation.Results) error {
	// This would save simulation results to a dedicated table
	// For now, we'll just log it
	logger.Info("Simulation complete: %d critical issues found", len(results.CriticalIssues))
	return nil
}