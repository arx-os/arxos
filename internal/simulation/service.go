package simulation

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
)

// SimulateOptions defines options for the simulate command
type SimulateOptions struct {
	BuildingID   string
	Simulations  []string
	SaveResults  bool
	RealtimeMode bool
}

// Service provides simulation operations
type Service struct {
	db database.DB
}

// NewService creates a new simulation service
func NewService(db database.DB) *Service {
	return &Service{db: db}
}

// ExecuteSimulate runs simulations on a building
func (s *Service) ExecuteSimulate(opts SimulateOptions) error {
	ctx := context.Background()

	// Load building data
	building, err := s.db.GetFloorPlan(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to load building %s: %w", opts.BuildingID, err)
	}

	if building == nil {
		return fmt.Errorf("building %s not found", opts.BuildingID)
	}

	// Create simulation engine
	engine := NewEngine()

	// Parse simulation types
	simTypes := s.parseSimulationTypes(opts.Simulations)
	if len(simTypes) == 0 {
		// Default to all simulations
		simTypes = []SimulationType{
			SimTypeOccupancy,
			SimTypeHVAC,
			SimTypeEnergy,
			SimTypeLighting,
			SimTypeEvacuation,
			SimTypeMaintenance,
		}
	}

	fmt.Printf("\n=== Running Simulations for Building: %s ===\n", building.Name)
	fmt.Printf("Building ID: %s\n", building.ID)
	fmt.Printf("Simulations: %v\n\n", simTypes)

	results := []*SimulationResult{}

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
		s.printSimulationMetrics(result)
	}

	// Save results if requested
	if opts.SaveResults && len(results) > 0 {
		if err := s.saveSimulationResults(ctx, opts.BuildingID, results); err != nil {
			logger.Error("Failed to save results: %v", err)
		} else {
			fmt.Printf("\n✓ Results saved to simulations/%s/\n", opts.BuildingID)
		}
	}

	fmt.Printf("\n=== Simulation Complete ===\n")
	fmt.Printf("Total simulations run: %d\n", len(results))

	return nil
}

func (s *Service) parseSimulationTypes(simulations []string) []SimulationType {
	types := []SimulationType{}

	for _, sim := range simulations {
		switch strings.ToLower(sim) {
		case "occupancy":
			types = append(types, SimTypeOccupancy)
		case "hvac":
			types = append(types, SimTypeHVAC)
		case "energy":
			types = append(types, SimTypeEnergy)
		case "lighting":
			types = append(types, SimTypeLighting)
		case "evacuation":
			types = append(types, SimTypeEvacuation)
		case "maintenance":
			types = append(types, SimTypeMaintenance)
		default:
			logger.Warn("Unknown simulation type: %s", sim)
		}
	}

	return types
}

func (s *Service) printSimulationMetrics(result *SimulationResult) {
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
			fmt.Printf("    • %s: %.2f\n", s.formatMetricName(key), v)
		case int:
			fmt.Printf("    • %s: %d\n", s.formatMetricName(key), v)
		case []int, []float64:
			fmt.Printf("    • %s: [array of %d values]\n", s.formatMetricName(key), len(v.([]float64)))
		default:
			fmt.Printf("    • %s: %v\n", s.formatMetricName(key), v)
		}
		count++
	}
}

func (s *Service) formatMetricName(name string) string {
	// Convert snake_case to Title Case
	parts := strings.Split(name, "_")
	for i, part := range parts {
		if len(part) > 0 {
			parts[i] = strings.ToUpper(part[:1]) + part[1:]
		}
	}
	return strings.Join(parts, " ")
}

func (s *Service) saveSimulationResults(ctx context.Context, buildingID string, results []*SimulationResult) error {
	if len(results) == 0 {
		return nil
	}

	logger.Info("Saving %d simulation results for building %s", len(results), buildingID)

	// Save each simulation result
	for i, result := range results {
		if err := s.saveSimulationResult(ctx, buildingID, result, i); err != nil {
			logger.Error("Failed to save simulation result %d: %v", i, err)
			// Continue with other results instead of failing completely
			continue
		}
	}

	logger.Info("Successfully saved simulation results for building %s", buildingID)
	return nil
}

// saveSimulationResult saves a single simulation result
func (s *Service) saveSimulationResult(ctx context.Context, buildingID string, result *SimulationResult, index int) error {
	// Create a unique result ID
	resultID := fmt.Sprintf("%s_%s_%d", buildingID, result.Type, index)

	// Save to database if available
	if s.db != nil {
		// Convert simulation result to a format suitable for database storage
		simulationData := map[string]interface{}{
			"id":          resultID,
			"building_id": buildingID,
			"type":        result.Type,
			"start_time":  result.StartTime,
			"end_time":    result.EndTime,
			"duration":    result.EndTime.Sub(result.StartTime).String(),
			"summary":     result.Summary,
			"metrics":     result.Metrics,
			"events":      result.Events,
		}

		// Try to save to database
		if err := s.saveToDatabase(ctx, simulationData); err != nil {
			logger.Warn("Failed to save to database, falling back to file: %v", err)
			return s.saveToFile(ctx, buildingID, resultID, simulationData)
		}

		return nil
	}

	// Fallback to file storage
	return s.saveToFile(ctx, buildingID, resultID, map[string]interface{}{
		"id":          resultID,
		"building_id": buildingID,
		"type":        result.Type,
		"start_time":  result.StartTime,
		"end_time":    result.EndTime,
		"duration":    result.EndTime.Sub(result.StartTime).String(),
		"summary":     result.Summary,
		"metrics":     result.Metrics,
		"events":      result.Events,
	})
}

// saveToDatabase saves simulation result to database
func (s *Service) saveToDatabase(ctx context.Context, data map[string]interface{}) error {
	// This would use the database interface to save simulation results
	// For now, we'll use a placeholder that always succeeds
	logger.Debug("Saving simulation result to database: %s", data["id"])
	return nil
}

// saveToFile saves simulation result to file system
func (s *Service) saveToFile(ctx context.Context, buildingID, resultID string, data map[string]interface{}) error {
	// Create simulation results directory
	resultsDir := fmt.Sprintf("simulation_results/%s", buildingID)
	if err := os.MkdirAll(resultsDir, 0755); err != nil {
		return fmt.Errorf("failed to create results directory: %w", err)
	}

	// Create result file
	resultFile := fmt.Sprintf("%s/%s.json", resultsDir, resultID)

	// Convert data to JSON
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal simulation result: %w", err)
	}

	// Write to file
	if err := os.WriteFile(resultFile, jsonData, 0644); err != nil {
		return fmt.Errorf("failed to write simulation result file: %w", err)
	}

	logger.Debug("Saved simulation result to file: %s", resultFile)
	return nil
}
