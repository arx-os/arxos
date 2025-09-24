package integration

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/internal/adapters/postgis"
	"github.com/arx-os/arxos/internal/core/building"
	"github.com/arx-os/arxos/internal/core/equipment"
	"github.com/arx-os/arxos/internal/core/spatial"
)

// TestPostGISIntegration tests the complete PostGIS integration
func TestPostGISIntegration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test")
	}

	// Check for PostGIS connection environment variables
	host := os.Getenv("POSTGIS_HOST")
	if host == "" {
		host = "localhost"
	}

	port := 5432
	database := os.Getenv("POSTGIS_DB")
	if database == "" {
		database = "arxos_test"
	}

	user := os.Getenv("POSTGIS_USER")
	if user == "" {
		user = "postgres"
	}

	password := os.Getenv("POSTGIS_PASSWORD")
	if password == "" {
		t.Skip("POSTGIS_PASSWORD not set, skipping integration test")
	}

	// Create PostGIS client
	config := postgis.Config{
		Host:            host,
		Port:            port,
		Database:        database,
		User:            user,
		Password:        password,
		SSLMode:         "disable",
		MaxConnections:  10,
		MaxIdleConns:    5,
		ConnMaxLifetime: time.Hour,
	}

	client, err := postgis.NewClient(config)
	require.NoError(t, err)
	defer client.Close()

	ctx := context.Background()

	// Initialize schema
	err = client.InitializeSchema(ctx)
	require.NoError(t, err)

	// Create repositories
	buildingRepo := postgis.NewBuildingRepository(client)
	equipmentRepo := postgis.NewEquipmentRepository(client)

	// Test building operations
	t.Run("BuildingOperations", func(t *testing.T) {
		// Create building
		bldg := building.NewBuilding("TEST-001", "Test Building")
		bldg.Address = "123 Test St"
		bldg.SetOrigin(37.7749, -122.4194, 0) // San Francisco

		err := buildingRepo.Create(ctx, bldg)
		assert.NoError(t, err)

		// Retrieve building
		retrieved, err := buildingRepo.GetByArxosID(ctx, "TEST-001")
		assert.NoError(t, err)
		assert.NotNil(t, retrieved)
		assert.Equal(t, "Test Building", retrieved.Name)
		assert.Equal(t, "123 Test St", retrieved.Address)

		// Update building
		retrieved.Name = "Updated Test Building"
		err = buildingRepo.Update(ctx, retrieved)
		assert.NoError(t, err)

		// List buildings
		filter := building.Filter{
			Limit:  10,
			Offset: 0,
		}
		buildings, err := buildingRepo.List(ctx, filter)
		assert.NoError(t, err)
		assert.Greater(t, len(buildings), 0)

		// Clean up
		defer buildingRepo.Delete(ctx, retrieved.ID)
	})

	// Test equipment operations
	t.Run("EquipmentOperations", func(t *testing.T) {
		// Create building first
		bldg := building.NewBuilding("TEST-002", "Equipment Test Building")
		err := buildingRepo.Create(ctx, bldg)
		require.NoError(t, err)
		defer buildingRepo.Delete(ctx, bldg.ID)

		// Create equipment
		eq := equipment.NewEquipment(bldg.ID, "1/101/OUTLET-001", "Main Outlet", "electrical.outlet")
		eq.Status = "operational"
		eq.Position = &equipment.Position{
			X: -122.4194,
			Y: 37.7749,
			Z: 10.5,
		}
		eq.Confidence = equipment.ConfidenceSurveyed

		err = equipmentRepo.Create(ctx, eq)
		assert.NoError(t, err)

		// Retrieve equipment
		retrieved, err := equipmentRepo.GetByPath(ctx, bldg.ID, "1/101/OUTLET-001")
		assert.NoError(t, err)
		assert.NotNil(t, retrieved)
		assert.Equal(t, "Main Outlet", retrieved.Name)
		assert.Equal(t, "electrical.outlet", retrieved.Type)

		// Update equipment
		retrieved.Status = "maintenance"
		err = equipmentRepo.Update(ctx, retrieved)
		assert.NoError(t, err)

		// List equipment for building
		filter := equipment.Filter{
			BuildingID: bldg.ID,
			Limit:      100,
			Offset:     0,
		}
		equipmentList, err := equipmentRepo.List(ctx, filter)
		assert.NoError(t, err)
		assert.Equal(t, 1, len(equipmentList))

		// Clean up
		err = equipmentRepo.Delete(ctx, retrieved.ID)
		assert.NoError(t, err)
	})

	// Test spatial queries
	t.Run("SpatialQueries", func(t *testing.T) {
		// Create building with known location
		bldg := building.NewBuilding("TEST-003", "Spatial Test Building")
		bldg.SetOrigin(37.7749, -122.4194, 0)
		err := buildingRepo.Create(ctx, bldg)
		require.NoError(t, err)
		defer buildingRepo.Delete(ctx, bldg.ID)

		// Create equipment with positions
		eq1 := equipment.NewEquipment(bldg.ID, "spatial/eq1", "Equipment 1", "sensor")
		eq1.Position = &equipment.Position{X: -122.4194, Y: 37.7749, Z: 0}
		err = equipmentRepo.Create(ctx, eq1)
		require.NoError(t, err)
		defer equipmentRepo.Delete(ctx, eq1.ID)

		eq2 := equipment.NewEquipment(bldg.ID, "spatial/eq2", "Equipment 2", "sensor")
		eq2.Position = &equipment.Position{X: -122.4190, Y: 37.7750, Z: 0}
		err = equipmentRepo.Create(ctx, eq2)
		require.NoError(t, err)
		defer equipmentRepo.Delete(ctx, eq2.ID)

		// Test FindNearby
		spatialQueries := postgis.NewSpatialQueries(client)
		nearby, err := spatialQueries.FindEquipmentNearby(ctx,
			spatial.WGS84Coordinate{Longitude: -122.4194, Latitude: 37.7749, Altitude: 0},
			1000) // 1km radius
		assert.NoError(t, err)
		assert.GreaterOrEqual(t, len(nearby), 2)

		// Test FindWithinBounds
		inBounds, err := spatialQueries.FindEquipmentWithinBounds(ctx,
			-122.42, 37.77, -122.41, 37.78)
		assert.NoError(t, err)
		assert.GreaterOrEqual(t, len(inBounds), 2)
	})
}

// TestBuildingService tests the building service layer
func TestBuildingService(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test")
	}

	// Similar setup as above...
	// This would test the service layer that uses the repositories
}

// TestImportExportPipeline tests the import/export functionality
func TestImportExportPipeline(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test")
	}

	// Test importing and exporting various formats
	// This would test the complete pipeline
}
