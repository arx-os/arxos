//go:build integration
// +build integration

package database

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func getTestPostGISConfig() *PostGISConfig {
	url := os.Getenv("ARXOS_POSTGIS_URL")
	if url == "" {
		url = "postgres://arxos:testpass@localhost:5432/arxos_test?sslmode=disable"
	}

	return &PostGISConfig{
		Host:     getEnvOrDefault("POSTGIS_HOST", "localhost"),
		Port:     5432,
		Database: getEnvOrDefault("POSTGIS_DB", "arxos_test"),
		User:     getEnvOrDefault("POSTGIS_USER", "arxos"),
		Password: getEnvOrDefault("POSTGIS_PASSWORD", "testpass"),
		SSLMode:  "disable",
	}
}

func getEnvOrDefault(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func TestPostGISConnection(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test")
	}

	config := getTestPostGISConfig()
	db := NewPostGISDB(*config)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	err := db.Connect(ctx)
	require.NoError(t, err, "Failed to connect to PostGIS")
	defer db.Close()

	// Verify PostGIS is available
	var version string
	err = db.db.QueryRowContext(ctx, "SELECT PostGIS_Version()").Scan(&version)
	require.NoError(t, err, "Failed to get PostGIS version")
	assert.NotEmpty(t, version, "PostGIS version should not be empty")
	t.Logf("Connected to PostGIS version: %s", version)
}

func TestSpatialOperations(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test")
	}

	config := getTestPostGISConfig()
	db := NewPostGISDB(*config)

	ctx := context.Background()
	err := db.Connect(ctx)
	require.NoError(t, err)
	defer db.Close()

	// Initialize schema
	err = db.InitializeSchema(ctx)
	require.NoError(t, err)

	t.Run("StoreAndRetrieveEquipmentPosition", func(t *testing.T) {
		equipmentID := fmt.Sprintf("TEST_EQ_%d", time.Now().UnixNano())
		position := spatial.Point3D{
			X: 1000.5, // mm
			Y: 2000.3, // mm
			Z: 3000.0, // mm
		}

		// Store position
		err := db.UpdateEquipmentPosition(equipmentID, position, spatial.ConfidenceHigh, "Test")
		assert.NoError(t, err)

		// Retrieve position
		retrieved, confidence, err := db.GetEquipmentPosition(equipmentID)
		assert.NoError(t, err)
		assert.InDelta(t, position.X, retrieved.X, 0.001)
		assert.InDelta(t, position.Y, retrieved.Y, 0.001)
		assert.InDelta(t, position.Z, retrieved.Z, 0.001)
		assert.Equal(t, spatial.ConfidenceHigh, confidence)
	})

	t.Run("ProximitySearch", func(t *testing.T) {
		// Create test equipment at known positions
		testData := []struct {
			id  string
			pos spatial.Point3D
		}{
			{"PROX_1", spatial.Point3D{X: 0, Y: 0, Z: 0}},
			{"PROX_2", spatial.Point3D{X: 100, Y: 0, Z: 0}},
			{"PROX_3", spatial.Point3D{X: 500, Y: 0, Z: 0}},
			{"PROX_4", spatial.Point3D{X: 1000, Y: 0, Z: 0}},
		}

		for _, td := range testData {
			err := db.UpdateEquipmentPosition(td.id, td.pos, spatial.ConfidenceMedium, "Test")
			require.NoError(t, err)
		}

		// Search within 200mm of origin
		results, err := db.FindEquipmentNear(spatial.Point3D{X: 0, Y: 0, Z: 0}, 200)
		assert.NoError(t, err)
		assert.Len(t, results, 2, "Should find 2 equipment within 200mm")

		// Search within 600mm of origin
		results, err = db.FindEquipmentNear(spatial.Point3D{X: 0, Y: 0, Z: 0}, 600)
		assert.NoError(t, err)
		assert.Len(t, results, 3, "Should find 3 equipment within 600mm")
	})

	t.Run("BoundingBoxSearch", func(t *testing.T) {
		// Create test equipment in a grid
		for i := 0; i < 5; i++ {
			for j := 0; j < 5; j++ {
				id := fmt.Sprintf("GRID_%d_%d", i, j)
				pos := spatial.Point3D{
					X: float64(i * 1000),
					Y: float64(j * 1000),
					Z: 0,
				}
				err := db.UpdateEquipmentPosition(id, pos, spatial.ConfidenceLow, "Grid")
				require.NoError(t, err)
			}
		}

		// Search in bounding box
		bbox := spatial.BoundingBox{
			Min: spatial.Point3D{X: 1500, Y: 1500, Z: -100},
			Max: spatial.Point3D{X: 3500, Y: 3500, Z: 100},
		}

		results, err := db.FindEquipmentInBoundingBox(bbox)
		assert.NoError(t, err)
		assert.Len(t, results, 4, "Should find 4 equipment in 2x2 grid area")
	})

	t.Run("FloorContainmentSearch", func(t *testing.T) {
		// Create a floor polygon (rectangle)
		floorID := "TEST_FLOOR_1"
		corners := []spatial.Point3D{
			{X: 0, Y: 0, Z: 0},
			{X: 5000, Y: 0, Z: 0},
			{X: 5000, Y: 3000, Z: 0},
			{X: 0, Y: 3000, Z: 0},
			{X: 0, Y: 0, Z: 0}, // Close polygon
		}

		err := db.StoreFloorBoundary(floorID, corners)
		require.NoError(t, err)

		// Add equipment inside and outside the floor
		testEquipment := []struct {
			id     string
			pos    spatial.Point3D
			inside bool
		}{
			{"INSIDE_1", spatial.Point3D{X: 2500, Y: 1500, Z: 0}, true},
			{"INSIDE_2", spatial.Point3D{X: 1000, Y: 1000, Z: 0}, true},
			{"OUTSIDE_1", spatial.Point3D{X: 6000, Y: 1500, Z: 0}, false},
			{"OUTSIDE_2", spatial.Point3D{X: 2500, Y: 4000, Z: 0}, false},
		}

		for _, eq := range testEquipment {
			err := db.UpdateEquipmentPosition(eq.id, eq.pos, spatial.ConfidenceHigh, "Floor test")
			require.NoError(t, err)
		}

		// Find equipment on floor
		results, err := db.FindEquipmentOnFloor(floorID)
		assert.NoError(t, err)

		// Count how many we expect to find
		expectedCount := 0
		for _, eq := range testEquipment {
			if eq.inside {
				expectedCount++
			}
		}

		assert.Len(t, results, expectedCount, "Should find only equipment inside floor boundary")
	})

	t.Run("EquipmentMovementHistory", func(t *testing.T) {
		equipmentID := "MOVING_EQ"
		positions := []spatial.Point3D{
			{X: 0, Y: 0, Z: 0},
			{X: 100, Y: 100, Z: 0},
			{X: 200, Y: 200, Z: 0},
		}

		// Record movements
		for i, pos := range positions {
			time.Sleep(10 * time.Millisecond) // Ensure different timestamps
			source := fmt.Sprintf("Movement %d", i+1)
			err := db.UpdateEquipmentPosition(equipmentID, pos, spatial.ConfidenceMedium, source)
			require.NoError(t, err)
		}

		// Get movement history
		history, err := db.GetEquipmentMovementHistory(equipmentID, 10)
		assert.NoError(t, err)
		assert.Len(t, history, 3, "Should have 3 position records")

		// Verify positions are in reverse chronological order
		for i := 0; i < len(history)-1; i++ {
			assert.True(t, history[i].Timestamp.After(history[i+1].Timestamp) ||
				history[i].Timestamp.Equal(history[i+1].Timestamp),
				"History should be in reverse chronological order")
		}
	})

	t.Run("SpatialIndexPerformance", func(t *testing.T) {
		// Create many equipment positions
		numEquipment := 1000
		for i := 0; i < numEquipment; i++ {
			id := fmt.Sprintf("PERF_%d", i)
			pos := spatial.Point3D{
				X: float64(i%100) * 100,
				Y: float64(i/100) * 100,
				Z: 0,
			}
			err := db.UpdateEquipmentPosition(id, pos, spatial.ConfidenceLow, "Performance test")
			require.NoError(t, err)
		}

		// Measure proximity search performance
		start := time.Now()
		results, err := db.FindEquipmentNear(spatial.Point3D{X: 5000, Y: 5000, Z: 0}, 1000)
		duration := time.Since(start)

		assert.NoError(t, err)
		assert.NotEmpty(t, results)
		assert.Less(t, duration, 100*time.Millisecond, "Proximity search should be fast with spatial index")
		t.Logf("Found %d equipment in %v", len(results), duration)
	})
}

func TestSpatialAggregations(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test")
	}

	config := getTestPostGISConfig()
	db := NewPostGISDB(*config)

	ctx := context.Background()
	err := db.Connect(ctx)
	require.NoError(t, err)
	defer db.Close()

	err = db.InitializeSchema(ctx)
	require.NoError(t, err)

	t.Run("CalculateCenterOfMass", func(t *testing.T) {
		// Create equipment in a pattern
		positions := []spatial.Point3D{
			{X: 0, Y: 0, Z: 0},
			{X: 1000, Y: 0, Z: 0},
			{X: 1000, Y: 1000, Z: 0},
			{X: 0, Y: 1000, Z: 0},
		}

		equipmentIDs := []string{}
		for i, pos := range positions {
			id := fmt.Sprintf("CENTER_%d", i)
			equipmentIDs = append(equipmentIDs, id)
			err := db.UpdateEquipmentPosition(id, pos, spatial.ConfidenceHigh, "Center test")
			require.NoError(t, err)
		}

		// Calculate center
		center, err := db.CalculateEquipmentCenterOfMass(equipmentIDs)
		assert.NoError(t, err)
		assert.InDelta(t, 500, center.X, 0.001, "Center X should be 500")
		assert.InDelta(t, 500, center.Y, 0.001, "Center Y should be 500")
		assert.InDelta(t, 0, center.Z, 0.001, "Center Z should be 0")
	})

	t.Run("CalculateConvexHull", func(t *testing.T) {
		// Create equipment forming a triangle
		positions := []spatial.Point3D{
			{X: 0, Y: 0, Z: 0},
			{X: 1000, Y: 0, Z: 0},
			{X: 500, Y: 866, Z: 0}, // Approximately equilateral triangle
			{X: 500, Y: 300, Z: 0}, // Point inside the triangle
		}

		equipmentIDs := []string{}
		for i, pos := range positions {
			id := fmt.Sprintf("HULL_%d", i)
			equipmentIDs = append(equipmentIDs, id)
			err := db.UpdateEquipmentPosition(id, pos, spatial.ConfidenceHigh, "Hull test")
			require.NoError(t, err)
		}

		// Calculate convex hull
		hull, err := db.CalculateConvexHull(equipmentIDs)
		assert.NoError(t, err)
		assert.Len(t, hull, 4, "Convex hull should have 4 points (3 vertices + closing point)")
	})
}

func TestTransactionSupport(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test")
	}

	config := getTestPostGISConfig()
	db := NewPostGISDB(*config)

	ctx := context.Background()
	err := db.Connect(ctx)
	require.NoError(t, err)
	defer db.Close()

	err = db.InitializeSchema(ctx)
	require.NoError(t, err)

	t.Run("RollbackOnError", func(t *testing.T) {
		equipmentID := "TRANSACTION_TEST"

		// Start transaction
		tx, err := db.db.BeginTx(ctx, nil)
		require.NoError(t, err)

		// Insert position within transaction
		_, err = tx.ExecContext(ctx, `
			INSERT INTO equipment_positions (equipment_id, position, confidence, source)
			VALUES ($1, ST_GeomFromText('POINT(100 200 300)', 900913), $2, $3)
		`, equipmentID, spatial.ConfidenceHigh, "Transaction test")
		require.NoError(t, err)

		// Rollback transaction
		err = tx.Rollback()
		require.NoError(t, err)

		// Verify position was not saved
		_, _, err = db.GetEquipmentPosition(equipmentID)
		assert.Error(t, err, "Position should not exist after rollback")
	})

	t.Run("CommitSuccess", func(t *testing.T) {
		equipmentID := "COMMIT_TEST"

		// Start transaction
		tx, err := db.db.BeginTx(ctx, nil)
		require.NoError(t, err)

		// Insert position within transaction
		_, err = tx.ExecContext(ctx, `
			INSERT INTO equipment_positions (equipment_id, position, confidence, source)
			VALUES ($1, ST_GeomFromText('POINT(100 200 300)', 900913), $2, $3)
		`, equipmentID, spatial.ConfidenceHigh, "Commit test")
		require.NoError(t, err)

		// Commit transaction
		err = tx.Commit()
		require.NoError(t, err)

		// Verify position was saved
		pos, confidence, err := db.GetEquipmentPosition(equipmentID)
		assert.NoError(t, err)
		assert.InDelta(t, 100, pos.X, 0.001)
		assert.InDelta(t, 200, pos.Y, 0.001)
		assert.InDelta(t, 300, pos.Z, 0.001)
		assert.Equal(t, spatial.ConfidenceHigh, confidence)
	})
}
