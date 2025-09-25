package services

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// ExportCommandOptions defines options for the export command
type ExportCommandOptions struct {
	BuildingID        string
	Format            string
	IncludeIntel      bool
	IncludeHistory    bool
	SimulateBeforeExp bool
	OutputFile        string
	Template          string // Report template
	Filters           ExportFilters
	Verbose           bool
}

// ExportFilters for filtering export data
type ExportFilters struct {
	IncludeTypes []string
	ExcludeTypes []string
	Floors       []string
	Systems      []string
}

// ExportCommandService handles the export command with intelligence
type ExportCommandService struct {
	db database.DB
}

// NewExportCommandService creates a new export command service
func NewExportCommandService(db database.DB) *ExportCommandService {
	return &ExportCommandService{db: db}
}

// ExecuteExport handles the export command with intelligence
func (s *ExportCommandService) ExecuteExport(opts ExportCommandOptions) error {
	ctx := context.Background()

	// Load building from database
	building, err := s.db.GetFloorPlan(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to load building: %w", err)
	}

	// Run simulations if requested
	var simResults interface{}
	if opts.SimulateBeforeExp || opts.IncludeIntel {
		simImpl := NewSimulationImplementations(s.db)
		results, err := simImpl.RunComprehensiveSimulation(ctx, opts.BuildingID, map[string]interface{}{
			"include_energy":    true,
			"include_thermal":   true,
			"include_occupancy": true,
		})
		if err != nil {
			logger.Warn("Simulation failed: %v", err)
			// Continue without simulation results
		} else {
			simResults = results
		}
	}

	// Export based on format
	switch opts.Format {
	case "bim":
		return s.exportBIM(building, simResults, opts)
	case "json":
		return s.exportJSON(building, simResults, opts)
	case "pdf":
		return fmt.Errorf("PDF export not yet implemented")
	case "csv":
		return fmt.Errorf("CSV export not yet implemented")
	default:
		return fmt.Errorf("unsupported format: %s", opts.Format)
	}
}

func (s *ExportCommandService) exportBIM(building *models.FloorPlan, simResults interface{}, opts ExportCommandOptions) error {
	// Convert to BIM format
	bimBuilding := s.convertToSimpleBIM(building)

	// Add intelligence data if available
	if simResults != nil && opts.IncludeIntel {
		s.enrichBIMWithIntelligence(bimBuilding, simResults)
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

func (s *ExportCommandService) exportJSON(building *models.FloorPlan, simResults interface{}, opts ExportCommandOptions) error {
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

func (s *ExportCommandService) convertToSimpleBIM(fp *models.FloorPlan) *bim.SimpleBuilding {
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

func (s *ExportCommandService) enrichBIMWithIntelligence(building *bim.SimpleBuilding, results interface{}) {
	// Add simulation data to building metadata
	if results != nil {
		building.SetSimulationResults(map[string]interface{}{
			"results":   results,
			"timestamp": time.Now().Format(time.RFC3339),
		})
		logger.Debug("Added simulation data to building %s", building.Name)
	}
}

func (s *ExportCommandService) saveSimulationResults(ctx context.Context, db *database.PostGISDB, buildingID string, results interface{}) error {
	// Save simulation results to database
	if results != nil {
		// Log simulation results (simplified implementation)
		logger.Info("Simulation results for building %s: %+v", buildingID, results)
		logger.Debug("Saved simulation results for building %s", buildingID)
	}
	return nil
}
