package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/simulation"
)

// ExecuteSimulate runs simulations on a building
func ExecuteSimulate(opts SimulateOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewPostGISConnection(ctx)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Load building data
	building, err := db.GetFloorPlan(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to load building %s: %w", opts.BuildingID, err)
	}

	if building == nil {
		return fmt.Errorf("building %s not found", opts.BuildingID)
	}

	// Create simulation engine
	engine := simulation.NewEngine()

	// Parse simulation types
	simTypes := parseSimulationTypes(opts.Simulations)
	if len(simTypes) == 0 {
		// Default to all simulations
		simTypes = []simulation.SimulationType{
			simulation.SimTypeOccupancy,
			simulation.SimTypeHVAC,
			simulation.SimTypeEnergy,
			simulation.SimTypeLighting,
			simulation.SimTypeEvacuation,
			simulation.SimTypeMaintenance,
		}
	}

	fmt.Printf("\n=== Running Simulations for Building: %s ===\n", building.Name)
	fmt.Printf("Building ID: %s\n", building.ID)
	fmt.Printf("Total Area: %.2f sq meters\n", building.TotalArea)
	fmt.Printf("Floors: %d\n", building.Floors)
	fmt.Printf("Simulations: %v\n\n", simTypes)

	results := []*simulation.SimulationResult{}

	// Run each simulation
	for _, simType := range simTypes {
		fmt.Printf("Running %s simulation...\n", simType)

		result, err := engine.RunSimulation(ctx, building, simType, opts.RealtimeMode)
		if err != nil {
			logger.Error("Simulation %s failed: %v", simType, err)
			fmt.Printf("  ❌ Failed: %v\n", err)
			continue
		}

		results = append(results, result)
		fmt.Printf("  ✓ Completed: %s\n", result.Summary)

		// Print key metrics
		printSimulationMetrics(result)
	}

	// Save results if requested
	if opts.SaveResults && len(results) > 0 {
		if err := saveSimulationResults(opts.BuildingID, results); err != nil {
			logger.Error("Failed to save results: %v", err)
		} else {
			fmt.Printf("\n✓ Results saved to simulations/%s/\n", opts.BuildingID)
		}
	}

	fmt.Printf("\n=== Simulation Complete ===\n")
	fmt.Printf("Total simulations run: %d\n", len(results))

	return nil
}

func parseSimulationTypes(simulations []string) []simulation.SimulationType {
	types := []simulation.SimulationType{}

	for _, sim := range simulations {
		switch strings.ToLower(sim) {
		case "occupancy":
			types = append(types, simulation.SimTypeOccupancy)
		case "hvac":
			types = append(types, simulation.SimTypeHVAC)
		case "energy":
			types = append(types, simulation.SimTypeEnergy)
		case "lighting":
			types = append(types, simulation.SimTypeLighting)
		case "evacuation":
			types = append(types, simulation.SimTypeEvacuation)
		case "maintenance":
			types = append(types, simulation.SimTypeMaintenance)
		default:
			logger.Warn("Unknown simulation type: %s", sim)
		}
	}

	return types
}

func printSimulationMetrics(result *simulation.SimulationResult) {
	fmt.Printf("\n  Key Metrics:\n")

	// Print top 5 metrics
	count := 0
	for key, value := range result.Metrics {
		if count >= 5 {
			break
		}

		// Format the metric for display
		switch v := value.(type) {
		case float64:
			fmt.Printf("    • %s: %.2f\n", formatMetricName(key), v)
		case int:
			fmt.Printf("    • %s: %d\n", formatMetricName(key), v)
		case []int, []float64:
			fmt.Printf("    • %s: [array of %d values]\n", formatMetricName(key), len(v.([]float64)))
		default:
			fmt.Printf("    • %s: %v\n", formatMetricName(key), v)
		}
		count++
	}
}

func formatMetricName(name string) string {
	// Convert snake_case to Title Case
	parts := strings.Split(name, "_")
	for i, part := range parts {
		if len(part) > 0 {
			parts[i] = strings.ToUpper(part[:1]) + part[1:]
		}
	}
	return strings.Join(parts, " ")
}

func saveSimulationResults(buildingID string, results []*simulation.SimulationResult) error {
	// Create output directory
	outDir := filepath.Join("simulations", buildingID)
	if err := os.MkdirAll(outDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Save each result to a separate file
	for _, result := range results {
		filename := fmt.Sprintf("%s_%s.json",
			result.Type,
			result.StartTime.Format("20060102_150405"))

		filepath := filepath.Join(outDir, filename)

		file, err := os.Create(filepath)
		if err != nil {
			return fmt.Errorf("failed to create file %s: %w", filepath, err)
		}

		encoder := json.NewEncoder(file)
		encoder.SetIndent("", "  ")
		if err := encoder.Encode(result); err != nil {
			file.Close()
			return fmt.Errorf("failed to write results: %w", err)
		}
		file.Close()

		logger.Info("Saved simulation results to %s", filepath)
	}

	// Create summary file
	summaryFile := filepath.Join(outDir, "summary.json")
	summary := map[string]interface{}{
		"building_id": buildingID,
		"timestamp":   time.Now(),
		"simulations": len(results),
		"results":     results,
	}

	file, err := os.Create(summaryFile)
	if err != nil {
		return fmt.Errorf("failed to create summary file: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	return encoder.Encode(summary)
}
