package commands

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/simulation"
)

// ExecuteSimulate runs simulations on a building
func ExecuteSimulate(opts SimulateOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewSQLiteDBFromPath("arxos.db")
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Load building
	building, err := db.GetFloorPlan(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to load building: %w", err)
	}

	// Create simulation engine
	engine := simulation.NewEngine()

	logger.Info("Running simulations: %v", opts.Simulations)

	// Run simulations
	results, err := engine.Analyze(building)
	if err != nil {
		return fmt.Errorf("simulation failed: %w", err)
	}

	// Display results
	fmt.Printf("\n=== Simulation Results for %s ===\n", opts.BuildingID)
	fmt.Printf("Timestamp: %s\n", results.Timestamp.Format("2006-01-02 15:04:05"))
	fmt.Printf("Total Energy Flow: %.2f kW\n", results.TotalEnergyFlow)
	fmt.Printf("Average Efficiency: %.1f%%\n", results.AverageEfficiency*100)
	fmt.Printf("Critical Issues: %d\n", len(results.CriticalIssues))

	if len(results.CriticalIssues) > 0 {
		fmt.Println("\nCritical Issues:")
		for _, issue := range results.CriticalIssues {
			fmt.Printf("  [%s] %s: %s\n", issue.Severity, issue.Equipment, issue.Description)
		}
	}

	if len(results.Recommendations) > 0 {
		fmt.Println("\nRecommendations:")
		for _, rec := range results.Recommendations {
			fmt.Printf("  • %s\n", rec)
		}
	}

	// Save results if requested
	if opts.SaveResults {
		// TODO: Implement saving to database
		logger.Info("Saving simulation results to database...")
	}

	return nil
}
