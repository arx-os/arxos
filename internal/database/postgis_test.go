package database

import (
	"context"
	"os"
	"testing"

	"github.com/arx-os/arxos/internal/spatial"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func getTestPostGISConfig() PostGISConfig {
	// Get config from environment variables or use defaults
	return PostGISConfig{
		Host:     getEnvOrDefault("POSTGIS_HOST", "localhost"),
		Port:     5432,
		Database: getEnvOrDefault("POSTGIS_DB", "arxos_test"),
		User:     getEnvOrDefault("POSTGIS_USER", "postgres"),
		Password: getEnvOrDefault("POSTGIS_PASSWORD", "postgres"),
		SSLMode:  "disable",
	}
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func skipIfNoPostGIS(t *testing.T) {
	if os.Getenv("SKIP_POSTGIS_TESTS") == "true" {
		t.Skip("Skipping PostGIS tests (SKIP_POSTGIS_TESTS=true)")
	}
}

func TestPostGISConnection(t *testing.T) {
	skipIfNoPostGIS(t)

	config := getTestPostGISConfig()
	db := NewPostGISDB(config)

	ctx := context.Background()
	err := db.Connect(ctx)
	if err != nil {
		t.Skipf("Cannot connect to PostGIS (this is expected in CI): %v", err)
	}
	defer db.Close()

	// Test that we can ping the database
	err = db.db.PingContext(ctx)
	assert.NoError(t, err, "Should be able to ping PostGIS")
}

func TestPostGISEquipmentPosition(t *testing.T) {
	skipIfNoPostGIS(t)

	config := getTestPostGISConfig()
	db := NewPostGISDB(config)

	ctx := context.Background()
	err := db.Connect(ctx)
	if err != nil {
		t.Skipf("Cannot connect to PostGIS: %v", err)
	}
	defer db.Close()

	// Test data
	equipmentID := "TEST-BUILDING/3/A/301/E/OUTLET_01"
	position := spatial.Point3D{X: 10.5, Y: 20.3, Z: 3.0}
	confidence := spatial.CONFIDENCE_HIGH

	// Update equipment position
	err = db.UpdateEquipmentPosition(equipmentID, position, confidence, "test")
	require.NoError(t, err, "Should update equipment position")

	// Get equipment position
	spatialEq, err := db.GetEquipmentPosition(equipmentID)
	require.NoError(t, err, "Should get equipment position")
	assert.NotNil(t, spatialEq)
	assert.Equal(t, equipmentID, spatialEq.Equipment.ID)
	assert.NotNil(t, spatialEq.SpatialData)
	assert.InDelta(t, position.X, spatialEq.SpatialData.Position.X, 0.001)
	assert.InDelta(t, position.Y, spatialEq.SpatialData.Position.Y, 0.001)
	assert.InDelta(t, position.Z, spatialEq.SpatialData.Position.Z, 0.001)
	assert.Equal(t, confidence, spatialEq.SpatialData.PositionConfidence)
}

func TestPostGISProximityQuery(t *testing.T) {
	skipIfNoPostGIS(t)

	config := getTestPostGISConfig()
	db := NewPostGISDB(config)

	ctx := context.Background()
	err := db.Connect(ctx)
	if err != nil {
		t.Skipf("Cannot connect to PostGIS: %v", err)
	}
	defer db.Close()

	// Create test equipment at different locations
	equipment := []struct {
		id       string
		position spatial.Point3D
	}{
		{"TEST/1/A/100/E/01", spatial.Point3D{X: 0, Y: 0, Z: 0}},
		{"TEST/1/A/100/E/02", spatial.Point3D{X: 1, Y: 0, Z: 0}},
		{"TEST/1/A/100/E/03", spatial.Point3D{X: 5, Y: 0, Z: 0}},
		{"TEST/1/A/100/E/04", spatial.Point3D{X: 10, Y: 0, Z: 0}},
	}

	// Insert test equipment
	for _, eq := range equipment {
		err := db.UpdateEquipmentPosition(eq.id, eq.position, spatial.CONFIDENCE_HIGH, "test")
		require.NoError(t, err)
	}

	// Query equipment within 3 meters of origin
	center := spatial.Point3D{X: 0, Y: 0, Z: 0}
	results, err := db.QueryBySpatialProximity(center, 3.0)
	require.NoError(t, err)

	// Should find equipment within radius
	assert.GreaterOrEqual(t, len(results), 2, "Should find at least 2 equipment within 3m")

	// Verify distance ordering
	if len(results) >= 2 {
		assert.LessOrEqual(t,
			results[0].SpatialData.DistanceFromQuery,
			results[1].SpatialData.DistanceFromQuery,
			"Results should be ordered by distance")
	}
}

func TestPostGISBoundingBox(t *testing.T) {
	skipIfNoPostGIS(t)

	config := getTestPostGISConfig()
	db := NewPostGISDB(config)

	ctx := context.Background()
	err := db.Connect(ctx)
	if err != nil {
		t.Skipf("Cannot connect to PostGIS: %v", err)
	}
	defer db.Close()

	// Create a bounding box
	bbox := spatial.BoundingBox{
		Min: spatial.Point3D{X: -5, Y: -5, Z: -1},
		Max: spatial.Point3D{X: 5, Y: 5, Z: 1},
	}

	// Create test equipment
	equipment := []struct {
		id       string
		position spatial.Point3D
		inside   bool
	}{
		{"TEST/BB/01", spatial.Point3D{X: 0, Y: 0, Z: 0}, true},
		{"TEST/BB/02", spatial.Point3D{X: 4, Y: 4, Z: 0}, true},
		{"TEST/BB/03", spatial.Point3D{X: 10, Y: 0, Z: 0}, false},
		{"TEST/BB/04", spatial.Point3D{X: -4, Y: -4, Z: 0}, true},
	}

	// Insert test equipment
	for _, eq := range equipment {
		err := db.UpdateEquipmentPosition(eq.id, eq.position, spatial.CONFIDENCE_MEDIUM, "test")
		require.NoError(t, err)
	}

	// Query by bounding box
	results, err := db.QueryByBoundingBox(bbox)
	require.NoError(t, err)

	// Count equipment inside bounding box
	insideCount := 0
	for _, eq := range equipment {
		if eq.inside {
			insideCount++
		}
	}

	// Results might include equipment from other tests, so check minimum
	assert.GreaterOrEqual(t, len(results), insideCount,
		"Should find at least the equipment inside the bounding box")
}

func TestPostGISBuildingTransform(t *testing.T) {
	skipIfNoPostGIS(t)

	config := getTestPostGISConfig()
	db := NewPostGISDB(config)

	ctx := context.Background()
	err := db.Connect(ctx)
	if err != nil {
		t.Skipf("Cannot connect to PostGIS: %v", err)
	}
	defer db.Close()

	// Test building data
	buildingID := "ARXOS-NA-US-NY-NYC-TEST"
	origin := spatial.GPSCoordinate{
		Latitude:  40.7128,
		Longitude: -74.0060,
		Altitude:  10.0,
	}
	rotation := 45.0
	gridScale := 0.5

	// Set building origin
	err = db.SetBuildingOrigin(buildingID, origin, rotation, gridScale)
	require.NoError(t, err, "Should set building origin")

	// Get building transform
	transform, err := db.GetBuildingTransform(buildingID)
	require.NoError(t, err, "Should get building transform")
	assert.NotNil(t, transform)
	assert.InDelta(t, origin.Latitude, transform.Origin.Latitude, 0.0001)
	assert.InDelta(t, origin.Longitude, transform.Origin.Longitude, 0.0001)
	assert.InDelta(t, rotation, transform.Rotation, 0.01)
	assert.InDelta(t, gridScale, transform.GridScale, 0.01)

	// Get just the origin
	gps, err := db.GetBuildingOrigin(buildingID)
	require.NoError(t, err, "Should get building origin")
	assert.NotNil(t, gps)
	assert.InDelta(t, origin.Latitude, gps.Latitude, 0.0001)
	assert.InDelta(t, origin.Longitude, gps.Longitude, 0.0001)
}

func TestPostGISConfidenceTracking(t *testing.T) {
	skipIfNoPostGIS(t)

	config := getTestPostGISConfig()
	db := NewPostGISDB(config)

	ctx := context.Background()
	err := db.Connect(ctx)
	if err != nil {
		t.Skipf("Cannot connect to PostGIS: %v", err)
	}
	defer db.Close()

	// Test equipment
	equipmentID := "TEST/CONF/01"

	// Update confidence for position
	err = db.UpdateConfidence(equipmentID, "position", spatial.CONFIDENCE_HIGH, "lidar_scan")
	require.NoError(t, err, "Should update position confidence")

	// Update confidence for semantic data
	err = db.UpdateConfidence(equipmentID, "semantic", spatial.CONFIDENCE_MEDIUM, "manual_entry")
	require.NoError(t, err, "Should update semantic confidence")

	// Get confidence record
	record, err := db.GetConfidenceRecord(equipmentID)
	require.NoError(t, err, "Should get confidence record")
	assert.NotNil(t, record)
	assert.Equal(t, equipmentID, record.EquipmentID)
	assert.Equal(t, spatial.CONFIDENCE_HIGH, record.PositionConfidence)
	assert.Equal(t, "lidar_scan", record.PositionSource)
	assert.Equal(t, spatial.CONFIDENCE_MEDIUM, record.SemanticConfidence)
	assert.Equal(t, "manual_entry", record.SemanticSource)
}

func TestPostGISHybridDB(t *testing.T) {
	skipIfNoPostGIS(t)

	// Create hybrid database
	pgConfig := getTestPostGISConfig()
	sqliteConfig := NewConfig(":memory:")

	hybrid, err := NewPostGISHybridDB(pgConfig)
	require.NoError(t, err)

	ctx := context.Background()
	err = hybrid.Connect(ctx, ":memory:")
	if err != nil {
		t.Skipf("Cannot setup hybrid database: %v", err)
	}
	defer hybrid.Close()

	// Check spatial support
	hasSpatial := hybrid.HasSpatialSupport()
	t.Logf("Hybrid DB has spatial support: %v", hasSpatial)

	// If PostGIS connected, test spatial operations
	if hasSpatial {
		spatialDB, err := hybrid.GetSpatialDB()
		assert.NoError(t, err, "Should get spatial DB when PostGIS connected")
		assert.NotNil(t, spatialDB)

		// Test spatial operation through hybrid
		equipmentID := "HYBRID/TEST/01"
		position := spatial.Point3D{X: 5, Y: 10, Z: 1}

		err = spatialDB.UpdateEquipmentPosition(
			equipmentID,
			position,
			spatial.CONFIDENCE_MEDIUM,
			"hybrid_test",
		)
		assert.NoError(t, err, "Should update equipment position through hybrid")
	}
}
