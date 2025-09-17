package test

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestDatabaseOperations tests basic database CRUD operations
func TestDatabaseOperations(t *testing.T) {
	ctx := context.Background()

	// Use helper to setup test database with embedded migrations
	db := SetupTestDB(t)

	t.Run("SaveAndGetEquipment", func(t *testing.T) {
		// Create test equipment
		equipment := &models.Equipment{
			ID:     "TEST_EQ_001",
			Name:   "Test Equipment",
			Type:   "HVAC",
			Status: models.StatusOperational,
			Location: &models.Point{
				X: 100.5,
				Y: 200.3,
			},
			Model:  "Model X",
			Serial: "SN12345",
		}

		// Save equipment
		err := db.SaveEquipment(ctx, equipment)
		assert.NoError(t, err)

		// Retrieve equipment
		retrieved, err := db.GetEquipment(ctx, "TEST_EQ_001")
		assert.NoError(t, err)
		assert.NotNil(t, retrieved)
		assert.Equal(t, equipment.Name, retrieved.Name)
		assert.Equal(t, equipment.Type, retrieved.Type)
		assert.Equal(t, equipment.Status, retrieved.Status)
		assert.NotNil(t, retrieved.Location)
		assert.InDelta(t, equipment.Location.X, retrieved.Location.X, 0.001)
		assert.InDelta(t, equipment.Location.Y, retrieved.Location.Y, 0.001)
	})

	t.Run("UpdateEquipment", func(t *testing.T) {
		// Create initial equipment
		equipment := &models.Equipment{
			ID:     "TEST_EQ_002",
			Name:   "Original Name",
			Type:   "ELECTRICAL",
			Status: models.StatusOperational,
		}

		// Save equipment
		err := db.SaveEquipment(ctx, equipment)
		require.NoError(t, err)

		// Update equipment
		equipment.Name = "Updated Name"
		equipment.Status = models.StatusMaintenance
		err = db.UpdateEquipment(ctx, equipment)
		assert.NoError(t, err)

		// Verify update
		retrieved, err := db.GetEquipment(ctx, "TEST_EQ_002")
		assert.NoError(t, err)
		assert.Equal(t, "Updated Name", retrieved.Name)
		assert.Equal(t, models.StatusMaintenance, retrieved.Status)
	})

	t.Run("DeleteEquipment", func(t *testing.T) {
		// Create equipment
		equipment := &models.Equipment{
			ID:     "TEST_EQ_003",
			Name:   "To Be Deleted",
			Type:   "PLUMBING",
			Status: models.StatusOperational,
		}

		// Save equipment
		err := db.SaveEquipment(ctx, equipment)
		require.NoError(t, err)

		// Delete equipment
		err = db.DeleteEquipment(ctx, "TEST_EQ_003")
		assert.NoError(t, err)

		// Verify deletion
		retrieved, err := db.GetEquipment(ctx, "TEST_EQ_003")
		assert.Error(t, err)
		assert.Nil(t, retrieved)
	})

	t.Run("FloorPlanOperations", func(t *testing.T) {
		// Create floor plan
		floorPlan := &models.FloorPlan{
			ID:       "TEST_FLOOR_001",
			Name:     "Test Floor",
			Building: "Test Building",
			Level:    1,
		}

		// Save floor plan
		err := db.SaveFloorPlan(ctx, floorPlan)
		assert.NoError(t, err)

		// Get floor plan
		retrieved, err := db.GetFloorPlan(ctx, "TEST_FLOOR_001")
		assert.NoError(t, err)
		assert.NotNil(t, retrieved)
		assert.Equal(t, floorPlan.Name, retrieved.Name)
		assert.Equal(t, floorPlan.Level, retrieved.Level)

		// Get all floor plans
		allPlans, err := db.GetAllFloorPlans(ctx)
		assert.NoError(t, err)
		assert.NotEmpty(t, allPlans)
	})
}

// TestSpatialQueries tests spatial database functionality
func TestSpatialQueries(t *testing.T) {
	// Skip if PostGIS is not available
	if os.Getenv("SKIP_SPATIAL_TESTS") == "true" {
		t.Skip("Skipping spatial tests")
	}

	ctx := context.Background()

	// This would test PostGIS spatial queries
	// For now, we'll just test the hybrid database pattern

	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test.db")

	// Initialize hybrid database
	dbConfig := database.NewConfig(dbPath)
	db := database.NewSQLiteDB(dbConfig)

	err := db.Connect(ctx, dbPath)
	require.NoError(t, err)
	defer db.Close()

	// Check spatial support
	hasSpatial := db.HasSpatialSupport()
	t.Logf("Spatial support available: %v", hasSpatial)

	if hasSpatial {
		// Test spatial queries
		spatialDB, err := db.GetSpatialDB()
		assert.NoError(t, err)
		assert.NotNil(t, spatialDB)

		// Would add more spatial tests here
	}
}

// TestIFCImport tests IFC file import functionality
func TestIFCImport(t *testing.T) {
	// Skip if no test files available
	testIFCFile := "test_data/sample.ifc"
	if _, err := os.Stat(testIFCFile); os.IsNotExist(err) {
		t.Skip("Test IFC file not found")
	}

	// This would test the IFC import pipeline
	// Implementation depends on having test IFC files
}

