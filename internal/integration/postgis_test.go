//go:build integration
// +build integration

package integration

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/converter"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestPostGISIntegration tests the complete PostGIS integration pipeline
func TestPostGISIntegration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()

	// Check if PostGIS is available
	pgHost := os.Getenv("POSTGIS_HOST")
	if pgHost == "" {
		pgHost = "localhost"
	}

	pgConfig := &database.DatabaseConfig{
		Type:     "postgis",
		Host:     pgHost,
		Port:     5432,
		Database: "arxos_test",
		User:     "arxos",
		Password: "arxos",
	}

	// Create PostGIS connection
	pgDB := database.NewPostGISDB(pgConfig)
	err := pgDB.Connect(ctx)
	if err != nil {
		t.Skip("PostGIS not available:", err)
	}
	defer pgDB.Close()

	// Create hybrid database
	hybridDB, err := database.NewPostGISHybridDB(pgConfig)
	require.NoError(t, err, "Failed to create hybrid database")
	defer hybridDB.Close()

	t.Run("SpatialDataStorage", func(t *testing.T) {
		testSpatialDataStorage(t, ctx, hybridDB)
	})

	t.Run("SpatialQueries", func(t *testing.T) {
		testSpatialQueries(t, ctx, hybridDB)
	})

	t.Run("IFCImportToPostGIS", func(t *testing.T) {
		testIFCImportToPostGIS(t, ctx, hybridDB)
	})

	t.Run("ExportFromPostGIS", func(t *testing.T) {
		testExportFromPostGIS(t, ctx, hybridDB)
	})

	t.Run("ConcurrentAccess", func(t *testing.T) {
		testConcurrentAccess(t, ctx, hybridDB)
	})
}

// testSpatialDataStorage tests storing and retrieving spatial data
func testSpatialDataStorage(t *testing.T, ctx context.Context, db *database.PostGISHybridDB) {
	spatialDB, err := db.GetSpatialDB()
	require.NoError(t, err, "Failed to get spatial database")

	// Test data
	equipmentID := fmt.Sprintf("TEST-EQUIP-%d", time.Now().Unix())
	position := spatial.Point3D{
		X: 5000.0, // 5m in mm
		Y: 3000.0, // 3m in mm
		Z: 2700.0, // 2.7m in mm
	}

	// Store position
	err = spatialDB.UpdateEquipmentPosition(
		equipmentID,
		position,
		spatial.ConfidenceHigh,
		"Integration Test",
	)
	assert.NoError(t, err, "Failed to store equipment position")

	// Retrieve position
	equipment, err := spatialDB.GetEquipmentPosition(equipmentID)
	assert.NoError(t, err, "Failed to retrieve equipment position")
	assert.NotNil(t, equipment, "Equipment should not be nil")

	if equipment != nil && equipment.SpatialData != nil {
		assert.Equal(t, position.X, equipment.SpatialData.Position.X, "X coordinate mismatch")
		assert.Equal(t, position.Y, equipment.SpatialData.Position.Y, "Y coordinate mismatch")
		assert.Equal(t, position.Z, equipment.SpatialData.Position.Z, "Z coordinate mismatch")
		assert.Equal(t, spatial.ConfidenceHigh, equipment.SpatialData.PositionConfidence, "Confidence mismatch")
		assert.Equal(t, "Integration Test", equipment.SpatialData.PositionSource, "Source mismatch")
	}
}

// testSpatialQueries tests spatial proximity queries
func testSpatialQueries(t *testing.T, ctx context.Context, db *database.PostGISHybridDB) {
	spatialDB, err := db.GetSpatialDB()
	require.NoError(t, err, "Failed to get spatial database")

	// Create test equipment in a grid pattern
	baseTime := time.Now().Unix()
	var testEquipment []string

	// Create 3x3 grid of equipment (1m spacing)
	for x := 0; x < 3; x++ {
		for y := 0; y < 3; y++ {
			equipID := fmt.Sprintf("GRID-%d-%d-%d", baseTime, x, y)
			testEquipment = append(testEquipment, equipID)

			position := spatial.Point3D{
				X: float64(x * 1000), // Convert to mm
				Y: float64(y * 1000),
				Z: 0,
			}

			err := spatialDB.UpdateEquipmentPosition(
				equipID,
				position,
				spatial.ConfidenceHigh,
				"Grid Test",
			)
			require.NoError(t, err, "Failed to create test equipment at (%d,%d)", x, y)
		}
	}

	// Test proximity query from center (1,1)
	center := spatial.Point3D{X: 1000, Y: 1000, Z: 0}

	// Query within 1.5m radius (should get center + 4 adjacent)
	nearby, err := spatialDB.QueryBySpatialProximity(center, 1.5)
	assert.NoError(t, err, "Failed to query by proximity")

	// Count how many of our test equipment are in results
	foundCount := 0
	for _, eq := range nearby {
		for _, testID := range testEquipment {
			if eq.ID == testID {
				foundCount++
				break
			}
		}
	}

	// Should find at least 5 (center + 4 adjacent)
	assert.GreaterOrEqual(t, foundCount, 5, "Should find at least 5 equipment within 1.5m")

	// Test with smaller radius (0.5m - should only get center point)
	nearby, err = spatialDB.QueryBySpatialProximity(center, 0.5)
	assert.NoError(t, err, "Failed to query with small radius")

	foundCount = 0
	for _, eq := range nearby {
		if eq.ID == fmt.Sprintf("GRID-%d-1-1", baseTime) {
			foundCount++
		}
	}
	assert.Equal(t, 1, foundCount, "Should find exactly 1 equipment at center")
}

// testIFCImportToPostGIS tests importing IFC files directly to PostGIS
func testIFCImportToPostGIS(t *testing.T, ctx context.Context, db *database.PostGISHybridDB) {
	// Create sample IFC content
	ifcContent := `ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',(),(),'ArxOS Test','','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#1=IFCPROJECT('1234567890abcdef',$,'Test Project',$,$,$,$,$,$);
#2=IFCBUILDING('building123',$,'Test Building',$,$,$,$,$,$,$,$);
#3=IFCBUILDINGSTOREY('floor1',$,'Ground Floor',$,$,$,$,$,$);
#4=IFCCARTESIANPOINT((0.,0.,0.));
#5=IFCCARTESIANPOINT((5000.,3000.,2700.));
#6=IFCAXIS2PLACEMENT3D(#5,$,$);
#7=IFCLOCALPLACEMENT($,#6);
#8=IFCBUILDINGELEMENTPROXY('equip1',$,'Test Equipment','HVAC Unit',$,#7,$,$,$);
ENDSEC;
END-ISO-10303-21;`

	// Create converter
	converter := converter.NewImprovedIFCConverter()

	// Import to database
	reader := strings.NewReader(ifcContent)
	err := converter.ConvertToDB(reader, db)
	assert.NoError(t, err, "Failed to import IFC to PostGIS")

	// Verify spatial data was stored
	spatialDB, err := db.GetSpatialDB()
	require.NoError(t, err, "Failed to get spatial database")

	// Query for imported equipment
	allEquipment, err := spatialDB.QueryBySpatialProximity(
		spatial.Point3D{X: 0, Y: 0, Z: 0},
		10000, // 10m radius
	)
	assert.NoError(t, err, "Failed to query imported equipment")

	// Should have at least one equipment from import
	assert.Greater(t, len(allEquipment), 0, "Should have imported equipment")
}

// testExportFromPostGIS tests exporting data from PostGIS
func testExportFromPostGIS(t *testing.T, ctx context.Context, db *database.PostGISHybridDB) {
	// Add test equipment with spatial data
	spatialDB, err := db.GetSpatialDB()
	require.NoError(t, err, "Failed to get spatial database")

	testID := fmt.Sprintf("EXPORT-TEST-%d", time.Now().Unix())
	position := spatial.Point3D{X: 1234.5, Y: 6789.0, Z: 2500.0}

	err = spatialDB.UpdateEquipmentPosition(
		testID,
		position,
		spatial.ConfidenceHigh,
		"Export Test",
	)
	require.NoError(t, err, "Failed to create test equipment for export")

	// Test BIM export
	var bimOutput strings.Builder
	generator := exporter.NewBIMGenerator()
	err = generator.GenerateFromDatabase(ctx, db, "TEST-BUILDING", &bimOutput)

	// May fail if no building data, but should not panic
	if err == nil {
		output := bimOutput.String()
		assert.Contains(t, output, "PostGIS", "BIM export should mention PostGIS")
		assert.Contains(t, output, "900913", "Should mention SRID")
	}

	// Test spatial query for export
	equipment, err := spatialDB.GetEquipmentPosition(testID)
	assert.NoError(t, err, "Failed to get equipment for export")
	assert.NotNil(t, equipment, "Equipment should exist")

	if equipment != nil && equipment.SpatialData != nil {
		assert.Equal(t, position.X, equipment.SpatialData.Position.X)
		assert.Equal(t, position.Y, equipment.SpatialData.Position.Y)
		assert.Equal(t, position.Z, equipment.SpatialData.Position.Z)
	}
}

// testConcurrentAccess tests concurrent database access
func testConcurrentAccess(t *testing.T, ctx context.Context, db *database.PostGISHybridDB) {
	spatialDB, err := db.GetSpatialDB()
	require.NoError(t, err, "Failed to get spatial database")

	// Number of concurrent operations
	numGoroutines := 10
	numOperations := 5

	// Use channels to coordinate
	done := make(chan bool, numGoroutines)
	errors := make(chan error, numGoroutines*numOperations)

	// Launch concurrent goroutines
	for i := 0; i < numGoroutines; i++ {
		go func(routineID int) {
			for j := 0; j < numOperations; j++ {
				equipID := fmt.Sprintf("CONCURRENT-%d-%d-%d", time.Now().Unix(), routineID, j)
				position := spatial.Point3D{
					X: float64(routineID * 100),
					Y: float64(j * 100),
					Z: 0,
				}

				// Store position
				err := spatialDB.UpdateEquipmentPosition(
					equipID,
					position,
					spatial.ConfidenceMedium,
					fmt.Sprintf("Routine-%d", routineID),
				)
				if err != nil {
					errors <- fmt.Errorf("routine %d op %d: %w", routineID, j, err)
					continue
				}

				// Read it back
				equipment, err := spatialDB.GetEquipmentPosition(equipID)
				if err != nil {
					errors <- fmt.Errorf("routine %d op %d read: %w", routineID, j, err)
					continue
				}
				if equipment == nil {
					errors <- fmt.Errorf("routine %d op %d: equipment not found", routineID, j)
				}
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < numGoroutines; i++ {
		<-done
	}
	close(errors)

	// Check for errors
	var allErrors []error
	for err := range errors {
		allErrors = append(allErrors, err)
	}

	assert.Empty(t, allErrors, "Concurrent operations should not produce errors")
}

// Benchmark tests
func BenchmarkPostGISSpatialQuery(b *testing.B) {
	ctx := context.Background()

	// Setup
	pgConfig := &database.DatabaseConfig{
		Type:     "postgis",
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_bench",
		User:     "arxos",
		Password: "arxos",
	}

	hybridDB, err := database.NewPostGISHybridDB(pgConfig)
	if err != nil {
		b.Skip("PostGIS not available for benchmark")
	}
	defer hybridDB.Close()

	spatialDB, _ := hybridDB.GetSpatialDB()
	if spatialDB == nil {
		b.Skip("Spatial DB not available")
	}

	// Create test data
	for i := 0; i < 10000; i++ {
		equipID := fmt.Sprintf("BENCH-%d", i)
		position := spatial.Point3D{
			X: float64(i % 100 * 1000),
			Y: float64(i / 100 * 1000),
			Z: float64((i % 10) * 1000),
		}
		_ = spatialDB.UpdateEquipmentPosition(equipID, position, spatial.ConfidenceMedium, "Benchmark")
	}

	center := spatial.Point3D{X: 50000, Y: 50000, Z: 5000}

	// Benchmark
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = spatialDB.QueryBySpatialProximity(center, 10.0)
	}
}
