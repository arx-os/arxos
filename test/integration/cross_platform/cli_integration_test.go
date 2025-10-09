package integration

import (
	"context"
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// testLogger implements domain.Logger for tests
type testLogger struct{}

func (l *testLogger) Debug(msg string, fields ...any) {}
func (l *testLogger) Info(msg string, fields ...any)  {}
func (l *testLogger) Warn(msg string, fields ...any)  {}
func (l *testLogger) Error(msg string, fields ...any) {}
func (l *testLogger) Fatal(msg string, fields ...any) {}

// setupTestDB creates a test database connection and runs migrations
func setupTestDB(t *testing.T) *sqlx.DB {
	t.Helper()

	dsn := "host=localhost port=5432 user=arxos_test dbname=arxos_test sslmode=disable password=test_password"
	db, err := sqlx.Connect("postgres", dsn)
	if err != nil {
		t.Skipf("Cannot connect to test database: %v", err)
		return nil
	}

	// Check if tables exist, if not skip test
	var tableCount int
	err = db.Get(&tableCount, "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='buildings'")
	if err != nil || tableCount == 0 {
		db.Close()
		t.Skipf("Test database not migrated. Run: go run cmd/arx/main.go migrate up (set ARXOS_DB_NAME=arxos_test)")
		return nil
	}

	t.Cleanup(func() {
		db.Close()
	})

	return db
}

// TestCLI_BuildingCommands tests CLI building commands integration
func TestCLI_BuildingCommands(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}

	// Setup repositories and use cases
	buildingRepo := postgis.NewBuildingRepository(db.DB)
	equipmentRepo := postgis.NewEquipmentRepository(db.DB)
	logger := &testLogger{}

	buildingUC := usecase.NewBuildingUseCase(buildingRepo, equipmentRepo, logger)

	t.Run("CreateBuilding_ViaUseCase", func(t *testing.T) {
		req := &domain.CreateBuildingRequest{
			Name:    "CLI Test Building",
			Address: "123 CLI Test Street",
			Coordinates: &domain.Location{
				X: -122.4194,
				Y: 37.7749,
				Z: 0,
			},
		}

		building, err := buildingUC.CreateBuilding(context.Background(), req)

		require.NoError(t, err)
		assert.NotNil(t, building)
		assert.Equal(t, req.Name, building.Name)
		assert.Equal(t, req.Address, building.Address)
		assert.NotEmpty(t, building.ID)

		t.Logf("Created building: %s (ID: %s)", building.Name, building.ID)
	})

	t.Run("ListBuildings_ViaUseCase", func(t *testing.T) {
		filter := &domain.BuildingFilter{
			Limit: 10,
		}

		buildings, err := buildingUC.ListBuildings(context.Background(), filter)

		require.NoError(t, err)
		assert.NotNil(t, buildings)
		assert.GreaterOrEqual(t, len(buildings), 1, "Should have at least the building we created")

		t.Logf("Found %d buildings", len(buildings))
	})
}

// TestIntegration_CompleteWorkflow tests a complete workflow
func TestIntegration_CompleteWorkflow(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}

	// Setup all repositories
	buildingRepo := postgis.NewBuildingRepository(db.DB)
	equipmentRepo := postgis.NewEquipmentRepository(db.DB)
	floorRepo := postgis.NewFloorRepository(db.DB)
	logger := &testLogger{}

	// Setup use cases
	buildingUC := usecase.NewBuildingUseCase(buildingRepo, equipmentRepo, logger)
	equipmentUC := usecase.NewEquipmentUseCase(equipmentRepo, buildingRepo, logger)

	ctx := context.Background()

	t.Run("CompleteWorkflow", func(t *testing.T) {
		// Step 1: Create a building
		building, err := buildingUC.CreateBuilding(ctx, &domain.CreateBuildingRequest{
			Name:    "Workflow Test Building",
			Address: "999 Workflow Street",
		})
		require.NoError(t, err)
		require.NotNil(t, building)
		t.Logf("✓ Step 1: Created building %s", building.ID)

		// Step 2: Create a floor
		floor := &domain.Floor{
			BuildingID: building.ID,
			Name:       "Ground Floor",
			Level:      0,
		}
		err = floorRepo.Create(ctx, floor)
		require.NoError(t, err)
		t.Logf("✓ Step 2: Created floor %s", floor.ID)

		// Step 3: Add equipment to the building
		equipment, err := equipmentUC.CreateEquipment(ctx, &domain.CreateEquipmentRequest{
			BuildingID: building.ID,
			FloorID:    floor.ID,
			Name:       "Main HVAC Unit",
			Type:       "hvac",
			Model:      "HV-2000",
			Location: &domain.Location{
				X: 10.0,
				Y: 20.0,
				Z: 2.5,
			},
		})
		require.NoError(t, err)
		require.NotNil(t, equipment)
		t.Logf("✓ Step 3: Created equipment %s", equipment.ID)

		// Step 4: Retrieve the building with equipment
		retrievedBuilding, err := buildingUC.GetBuilding(ctx, building.ID)
		require.NoError(t, err)
		assert.Equal(t, building.ID, retrievedBuilding.ID)
		t.Logf("✓ Step 4: Retrieved building successfully")

		// Step 5: List equipment for the building
		buildingEquipment, err := equipmentUC.GetEquipmentByBuilding(ctx, building.ID.String())
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(buildingEquipment), 1)
		t.Logf("✓ Step 5: Found %d equipment items", len(buildingEquipment))

		// Step 6: Move equipment
		newLocation := &domain.Location{X: 15.0, Y: 25.0, Z: 3.0}
		err = equipmentUC.MoveEquipment(ctx, equipment.ID.String(), newLocation)
		require.NoError(t, err)
		t.Logf("✓ Step 6: Moved equipment to new location")

		// Step 7: Verify the move
		movedEquipment, err := equipmentUC.GetEquipment(ctx, equipment.ID.String())
		require.NoError(t, err)
		assert.Equal(t, 15.0, movedEquipment.Location.X)
		assert.Equal(t, 25.0, movedEquipment.Location.Y)
		t.Logf("✓ Step 7: Verified equipment location updated")

		// Step 8: Try to delete building with equipment (should fail)
		err = buildingUC.DeleteBuilding(ctx, building.ID.String())
		assert.Error(t, err, "Should not delete building with equipment")
		assert.Contains(t, err.Error(), "cannot delete building with existing equipment")
		t.Logf("✓ Step 8: Business rule enforced - cannot delete building with equipment")

		// Step 9: Delete equipment first
		equipment.Status = "inactive" // Change status so it can be deleted
		err = equipmentRepo.Update(ctx, equipment)
		require.NoError(t, err)

		err = equipmentUC.DeleteEquipment(ctx, equipment.ID.String())
		require.NoError(t, err)
		t.Logf("✓ Step 9: Deleted equipment")

		// Step 10: Now delete building (should succeed)
		err = buildingUC.DeleteBuilding(ctx, building.ID.String())
		require.NoError(t, err)
		t.Logf("✓ Step 10: Deleted building successfully")

		t.Log("✅ Complete workflow executed successfully!")
	})
}

// TestIntegration_SpatialOperations tests spatial operations integration
func TestIntegration_SpatialOperations(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}

	buildingRepo := postgis.NewBuildingRepository(db.DB)
	equipmentRepo := postgis.NewEquipmentRepository(db.DB)
	logger := &testLogger{}

	buildingUC := usecase.NewBuildingUseCase(buildingRepo, equipmentRepo, logger)
	equipmentUC := usecase.NewEquipmentUseCase(equipmentRepo, buildingRepo, logger)

	ctx := context.Background()

	t.Run("SpatialWorkflow", func(t *testing.T) {
		// Create building with coordinates
		building, err := buildingUC.CreateBuilding(ctx, &domain.CreateBuildingRequest{
			Name:    "Spatial Test Building",
			Address: "555 Spatial Avenue",
			Coordinates: &domain.Location{
				X: -122.4194,
				Y: 37.7749,
				Z: 0,
			},
		})
		require.NoError(t, err)
		t.Logf("✓ Created building with coordinates: (%.4f, %.4f)",
			building.Coordinates.X, building.Coordinates.Y)

		// Add equipment with spatial coordinates
		equipment1, err := equipmentUC.CreateEquipment(ctx, &domain.CreateEquipmentRequest{
			BuildingID: building.ID,
			Name:       "HVAC North Wing",
			Type:       "hvac",
			Location: &domain.Location{
				X: 10.0,
				Y: 20.0,
				Z: 2.5,
			},
		})
		require.NoError(t, err)
		t.Logf("✓ Created equipment 1 at (%.1f, %.1f, %.1f)",
			equipment1.Location.X, equipment1.Location.Y, equipment1.Location.Z)

		equipment2, err := equipmentUC.CreateEquipment(ctx, &domain.CreateEquipmentRequest{
			BuildingID: building.ID,
			Name:       "HVAC South Wing",
			Type:       "hvac",
			Location: &domain.Location{
				X: 50.0,
				Y: 60.0,
				Z: 2.5,
			},
		})
		require.NoError(t, err)
		t.Logf("✓ Created equipment 2 at (%.1f, %.1f, %.1f)",
			equipment2.Location.X, equipment2.Location.Y, equipment2.Location.Z)

		// Get all equipment for building
		allEquipment, err := equipmentUC.GetEquipmentByBuilding(ctx, building.ID.String())
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(allEquipment), 2)
		t.Logf("✓ Retrieved %d equipment items with spatial coordinates", len(allEquipment))

		// Verify spatial data is preserved
		for _, eq := range allEquipment {
			assert.NotNil(t, eq.Location, "Equipment should have location data")
			t.Logf("  - %s: (%.1f, %.1f, %.1f)",
				eq.Name,
				eq.Location.X,
				eq.Location.Y,
				eq.Location.Z)
		}

		t.Log("✅ Spatial operations verified successfully!")
	})
}
