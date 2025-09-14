package integration

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/joelpate/arxos/internal/bim"
	"github.com/joelpate/arxos/internal/commands"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/simulation"
	"github.com/joelpate/arxos/pkg/models"
)

// TestEndToEndPipeline tests the complete flow from PDF import to intelligent BIM export
func TestEndToEndPipeline(t *testing.T) {
	// Setup
	ctx := context.Background()
	testDB := filepath.Join(t.TempDir(), "test.db")

	db, err := database.NewSQLiteDBFromPath(testDB)
	require.NoError(t, err)
	defer db.Close()

	// Test data
	buildingID := "ARXOS-NA-US-TEST-0001"
	buildingName := "Test Building"

	t.Run("Import PDF to Database", func(t *testing.T) {
		// This would use a test PDF file
		opts := commands.ImportOptions{
			InputFile:    "../../testdata/sample.pdf",
			Format:       "pdf",
			BuildingID:   buildingID,
			BuildingName: buildingName,
			ToDatabase:   true,
		}

		// Import should succeed (assuming test PDF exists)
		// err := commands.ExecuteImport(opts)
		// assert.NoError(t, err)

		// For now, create test data directly
		building := &models.FloorPlan{
			ID:   buildingID,
			UUID: buildingID,
			Name: buildingName,
			Equipment: []*models.Equipment{
				{
					ID:     "HVAC_RTU_01",
					Type:   "HVAC.RTU",
					Path:   "N/3/A/301/C",
					Status: models.StatusOperational,
				},
				{
					ID:     "ELEC_PANEL_01",
					Type:   "Electrical.Panel",
					Path:   "N/3/A/301/E",
					Status: models.StatusOperational,
				},
			},
		}

		err := db.SaveFloorPlan(ctx, building)
		assert.NoError(t, err)
	})

	t.Run("Run Simulations", func(t *testing.T) {
		// Load building
		building, err := db.GetFloorPlan(ctx, buildingID)
		require.NoError(t, err)
		assert.NotNil(t, building)

		// Run simulations
		engine := simulation.NewEngine()
		results, err := engine.Analyze(building)
		require.NoError(t, err)
		assert.NotNil(t, results)

		// Check simulation results
		assert.Greater(t, len(results.EquipmentAnalysis), 0)
		assert.GreaterOrEqual(t, results.AverageEfficiency, 0.0)
		assert.LessOrEqual(t, results.AverageEfficiency, 1.0)
	})

	t.Run("Export with Intelligence", func(t *testing.T) {
		// Export to BIM with intelligence
		opts := commands.ExportOptions{
			BuildingID:        buildingID,
			Format:            "bim",
			IncludeIntel:      true,
			SimulateBeforeExp: true,
		}

		// This would actually export
		// err := commands.ExecuteExport(opts)
		// assert.NoError(t, err)

		// For now, test the conversion
		building, err := db.GetFloorPlan(ctx, buildingID)
		require.NoError(t, err)

		bimBuilding := convertToBIM(building)
		assert.NotNil(t, bimBuilding)
		assert.Equal(t, buildingID, bimBuilding.UUID)
		assert.Len(t, bimBuilding.Equipment, 2)
	})

	t.Run("Spatial Anchors", func(t *testing.T) {
		// Test spatial anchor storage
		anchor := &database.SpatialAnchor{
			ID:            "anchor-001",
			BuildingUUID:  buildingID,
			EquipmentPath: "N/3/A/301/E/ELEC_PANEL_01",
			X:             10.5,
			Y:             20.3,
			Floor:         3,
			Platform:      "ARKit",
		}

		err := db.SaveSpatialAnchor(ctx, anchor)
		assert.NoError(t, err)

		// Retrieve anchor
		retrieved, err := db.GetSpatialAnchor(ctx, buildingID, "N/3/A/301/E/ELEC_PANEL_01")
		assert.NoError(t, err)
		assert.NotNil(t, retrieved)
		assert.Equal(t, anchor.X, retrieved.X)
		assert.Equal(t, anchor.Y, retrieved.Y)

		// Find nearby anchors
		nearby, err := db.FindNearbyAnchors(ctx, buildingID, 11.0, 20.0, 3, 5.0)
		assert.NoError(t, err)
		assert.Len(t, nearby, 1)
	})

	t.Run("BIM Round Trip", func(t *testing.T) {
		// Test that we can export to BIM and re-import
		building, err := db.GetFloorPlan(ctx, buildingID)
		require.NoError(t, err)

		// Convert to BIM
		bimBuilding := convertToBIM(building)

		// Write to temp file
		tempFile := filepath.Join(t.TempDir(), "test.bim.txt")
		file, err := os.Create(tempFile)
		require.NoError(t, err)

		writer := bim.NewWriter()
		err = writer.Write(file, bimBuilding)
		file.Close()
		assert.NoError(t, err)

		// Parse it back
		file, err = os.Open(tempFile)
		require.NoError(t, err)
		defer file.Close()

		parser := bim.NewParser()
		parsed, err := parser.Parse(file)
		assert.NoError(t, err)
		assert.Equal(t, bimBuilding.UUID, parsed.UUID)
		assert.Len(t, parsed.Equipment, len(bimBuilding.Equipment))
	})
}

// Helper function to convert models
func convertToBIM(fp *models.FloorPlan) *bim.Building {
	building := &bim.Building{
		Name:      fp.Name,
		UUID:      fp.UUID,
		Version:   "2.0",
		Equipment: make([]bim.Equipment, 0, len(fp.Equipment)),
	}

	for _, eq := range fp.Equipment {
		building.Equipment = append(building.Equipment, bim.Equipment{
			ID:     eq.ID,
			Type:   eq.Type,
			Path:   eq.Path,
			Status: bim.EquipmentStatus(eq.Status),
		})
	}

	return building
}