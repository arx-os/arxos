package integration_test

import (
	"context"
	"database/sql"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestBuildingCRUD tests the complete building CRUD workflow end-to-end
// This is the FIRST vertical slice test - proving the system works
func TestBuildingCRUD(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Setup
	ctx := context.Background()
	db, logger := setupTestEnvironment(t)
	defer db.Close()

	// Create repository and use case
	buildingRepo := postgis.NewBuildingRepository(db)
	equipmentRepo := postgis.NewEquipmentRepository(db)
	buildingUC := usecase.NewBuildingUseCase(buildingRepo, equipmentRepo, logger)

	// Test 1: Create Building
	t.Run("Create Building", func(t *testing.T) {
		req := &domain.CreateBuildingRequest{
			Name:    "Test School " + time.Now().Format("150405"),
			Address: "123 Test Street, Test City",
			Coordinates: &domain.Location{
				X: -122.4194, // San Francisco longitude
				Y: 37.7749,   // San Francisco latitude
				Z: 0,
			},
		}

		building, err := buildingUC.CreateBuilding(ctx, req)
		require.NoError(t, err, "Failed to create building")
		require.NotNil(t, building, "Building should not be nil")

		assert.NotEmpty(t, building.ID.String(), "Building ID should be generated")
		assert.Equal(t, req.Name, building.Name, "Building name should match")
		assert.Equal(t, req.Address, building.Address, "Building address should match")
		assert.NotNil(t, building.Coordinates, "Coordinates should be set")
		assert.Equal(t, req.Coordinates.X, building.Coordinates.X, "Longitude should match")
		assert.Equal(t, req.Coordinates.Y, building.Coordinates.Y, "Latitude should match")
		assert.False(t, building.CreatedAt.IsZero(), "CreatedAt should be set")

		t.Logf("✅ Created building: %s (ID: %s)", building.Name, building.ID.String())
	})

	// Test 2: List Buildings
	t.Run("List Buildings", func(t *testing.T) {
		// Create a test building first
		req := &domain.CreateBuildingRequest{
			Name:    "List Test Building " + time.Now().Format("150405"),
			Address: "456 List Test St",
		}
		_, err := buildingUC.CreateBuilding(ctx, req)
		require.NoError(t, err)

		// List all buildings
		filter := &domain.BuildingFilter{
			Limit:  10,
			Offset: 0,
		}

		buildings, err := buildingUC.ListBuildings(ctx, filter)
		require.NoError(t, err, "Failed to list buildings")
		assert.NotEmpty(t, buildings, "Should have at least one building")

		t.Logf("✅ Listed %d building(s)", len(buildings))
		for i, b := range buildings {
			t.Logf("   %d. %s - %s", i+1, b.Name, b.Address)
		}
	})

	// Test 3: Get Building by ID
	t.Run("Get Building by ID", func(t *testing.T) {
		// Create a test building
		req := &domain.CreateBuildingRequest{
			Name:    "Get Test Building " + time.Now().Format("150405"),
			Address: "789 Get Test Ave",
		}
		created, err := buildingUC.CreateBuilding(ctx, req)
		require.NoError(t, err)

		// Get the building
		fetched, err := buildingUC.GetBuilding(ctx, created.ID)
		require.NoError(t, err, "Failed to get building")
		require.NotNil(t, fetched, "Building should not be nil")

		assert.Equal(t, created.ID.String(), fetched.ID.String(), "IDs should match")
		assert.Equal(t, created.Name, fetched.Name, "Names should match")
		assert.Equal(t, created.Address, fetched.Address, "Addresses should match")

		t.Logf("✅ Retrieved building: %s", fetched.Name)
	})

	// Test 4: Update Building
	t.Run("Update Building", func(t *testing.T) {
		// Create a test building
		req := &domain.CreateBuildingRequest{
			Name:    "Update Test Building " + time.Now().Format("150405"),
			Address: "100 Update Test Blvd",
		}
		created, err := buildingUC.CreateBuilding(ctx, req)
		require.NoError(t, err)

		// Update the building
		newName := "Updated Building Name"
		newAddress := "200 Updated Address"
		updateReq := &domain.UpdateBuildingRequest{
			ID:      created.ID,
			Name:    &newName,
			Address: &newAddress,
		}

		updated, err := buildingUC.UpdateBuilding(ctx, updateReq)
		require.NoError(t, err, "Failed to update building")
		require.NotNil(t, updated, "Updated building should not be nil")

		assert.Equal(t, *updateReq.Name, updated.Name, "Name should be updated")
		assert.Equal(t, *updateReq.Address, updated.Address, "Address should be updated")
		assert.True(t, updated.UpdatedAt.After(created.UpdatedAt), "UpdatedAt should be newer")

		t.Logf("✅ Updated building: %s -> %s", created.Name, updated.Name)
	})

	// Test 5: Delete Building
	t.Run("Delete Building", func(t *testing.T) {
		// Create a test building
		req := &domain.CreateBuildingRequest{
			Name:    "Delete Test Building " + time.Now().Format("150405"),
			Address: "300 Delete Test Dr",
		}
		created, err := buildingUC.CreateBuilding(ctx, req)
		require.NoError(t, err)

		// Delete the building
		err = buildingUC.DeleteBuilding(ctx, created.ID.String())
		require.NoError(t, err, "Failed to delete building")

		// Verify it's gone
		_, err = buildingUC.GetBuilding(ctx, created.ID)
		assert.Error(t, err, "Should get error when fetching deleted building")

		t.Logf("✅ Deleted building: %s", created.Name)
	})

	// Test 6: Filter Buildings by Name
	t.Run("Filter Buildings by Name", func(t *testing.T) {
		// Create test buildings with unique prefix
		prefix := "FilterTest" + time.Now().Format("150405")
		for i := 1; i <= 3; i++ {
			req := &domain.CreateBuildingRequest{
				Name:    prefix + " School " + string(rune('A'+i-1)),
				Address: "Address " + string(rune('0'+i)),
			}
			_, err := buildingUC.CreateBuilding(ctx, req)
			require.NoError(t, err)
		}

		// Filter by name
		nameFilter := prefix
		filter := &domain.BuildingFilter{
			Name:   &nameFilter,
			Limit:  10,
			Offset: 0,
		}

		buildings, err := buildingUC.ListBuildings(ctx, filter)
		require.NoError(t, err, "Failed to filter buildings")
		assert.GreaterOrEqual(t, len(buildings), 3, "Should find at least 3 buildings")

		t.Logf("✅ Filtered buildings (found %d matching '%s')", len(buildings), prefix)
	})

	// Test 7: Create Building with Coordinates
	t.Run("Create Building with Coordinates", func(t *testing.T) {
		req := &domain.CreateBuildingRequest{
			Name:    "Coord Test Building " + time.Now().Format("150405"),
			Address: "400 Coordinate Test Ln",
			Coordinates: &domain.Location{
				X: -73.9857, // New York longitude
				Y: 40.7484,  // New York latitude
				Z: 10.5,     // 10.5 meters altitude
			},
		}

		building, err := buildingUC.CreateBuilding(ctx, req)
		require.NoError(t, err, "Failed to create building with coordinates")
		require.NotNil(t, building.Coordinates, "Coordinates should be stored")

		assert.InDelta(t, req.Coordinates.X, building.Coordinates.X, 0.0001, "Longitude should match")
		assert.InDelta(t, req.Coordinates.Y, building.Coordinates.Y, 0.0001, "Latitude should match")
		assert.InDelta(t, req.Coordinates.Z, building.Coordinates.Z, 0.1, "Altitude should match")

		t.Logf("✅ Created building with coordinates: (%.6f, %.6f, %.1fm)",
			building.Coordinates.X, building.Coordinates.Y, building.Coordinates.Z)
	})
}

// TestBuildingValidation tests business logic validation
func TestBuildingValidation(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	db, logger := setupTestEnvironment(t)
	defer db.Close()

	buildingRepo := postgis.NewBuildingRepository(db)
	equipmentRepo := postgis.NewEquipmentRepository(db)
	buildingUC := usecase.NewBuildingUseCase(buildingRepo, equipmentRepo, logger)

	t.Run("Create Building without Name", func(t *testing.T) {
		req := &domain.CreateBuildingRequest{
			Name:    "", // Empty name
			Address: "123 Test St",
		}

		_, err := buildingUC.CreateBuilding(ctx, req)
		assert.Error(t, err, "Should reject empty name")
		t.Logf("✅ Validation correctly rejected empty name")
	})

	t.Run("Create Building without Address", func(t *testing.T) {
		req := &domain.CreateBuildingRequest{
			Name:    "Test Building",
			Address: "", // Empty address
		}

		_, err := buildingUC.CreateBuilding(ctx, req)
		assert.Error(t, err, "Should reject empty address")
		t.Logf("✅ Validation correctly rejected empty address")
	})

	t.Run("Get Building with Empty ID", func(t *testing.T) {
		_, err := buildingUC.GetBuilding(ctx, types.ID{})
		assert.Error(t, err, "Should reject empty ID")
		t.Logf("✅ Validation correctly rejected empty ID")
	})
}

// setupTestEnvironment creates a test database connection and logger
func setupTestEnvironment(t *testing.T) (*sql.DB, domain.Logger) {
	cfg := &config.Config{
		Mode: "test",
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_dev", // Using dev database for now
			User:     "joelpate",
			Password: "",
			SSLMode:  "disable",
		},
	}

	dbInterface, err := infrastructure.NewDatabase(cfg)
	require.NoError(t, err, "Failed to connect to test database")

	// Get the underlying *sql.DB
	db, ok := dbInterface.(*infrastructure.Database)
	require.True(t, ok, "Failed to cast database to concrete type")

	logger := infrastructure.NewLogger(cfg)

	return db.GetDB().DB, logger
}
