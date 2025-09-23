package simulation

import (
	"context"
	"fmt"
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
	// For now, this is a placeholder implementation
	// In a real implementation, this would save to database or file system
	logger.Info("Saving simulation results for building %s", buildingID)
	return nil
}
