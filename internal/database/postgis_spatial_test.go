// +build integration

package database_test

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

type PostGISSpatialTestSuite struct {
	suite.Suite
	db        *database.PostGISDB
	ctx       context.Context
	testBuildingID string
	testEquipmentIDs []string
}

func (suite *PostGISSpatialTestSuite) SetupSuite() {
	// Get database configuration from environment
	config := database.PostGISConfig{
		Host:     getEnvOrDefault("TEST_POSTGIS_HOST", "localhost"),
		Port:     5432,
		Database: getEnvOrDefault("TEST_POSTGIS_DB", "arxos_test"),
		User:     getEnvOrDefault("TEST_POSTGIS_USER", "arxos"),
		Password: getEnvOrDefault("TEST_POSTGIS_PASSWORD", "arxos"),
		SSLMode:  "disable",
	}

	// Create database connection
	db := database.NewPostGISDB(config)
	err := db.Connect(context.Background(), "")
	require.NoError(suite.T(), err, "Failed to connect to test database")

	suite.db = db
	suite.ctx = context.Background()

	// Initialize test schema
	err = suite.initializeTestSchema()
	require.NoError(suite.T(), err, "Failed to initialize test schema")
}

func (suite *PostGISSpatialTestSuite) SetupTest() {
	// Create test building
	suite.testBuildingID = suite.createTestBuilding()

	// Create test equipment
	suite.testEquipmentIDs = suite.createTestEquipment()
}

func (suite *PostGISSpatialTestSuite) TearDownTest() {
	// Clean up test data
	_, err := suite.db.Exec(suite.ctx, "DELETE FROM equipment WHERE building_id = $1", suite.testBuildingID)
	suite.NoError(err)

	_, err = suite.db.Exec(suite.ctx, "DELETE FROM buildings WHERE id = $1", suite.testBuildingID)
	suite.NoError(err)
}

func (suite *PostGISSpatialTestSuite) TearDownSuite() {
	// Close database connection
	if suite.db != nil {
		suite.db.Close()
	}
}

// Test Equipment Position Operations

func (suite *PostGISSpatialTestSuite) TestUpdateEquipmentPosition() {
	equipmentID := suite.testEquipmentIDs[0]
	position := spatial.Point3D{X: -122.4194, Y: 37.7749, Z: 10.5}
	confidence := spatial.ConfidenceHigh
	source := "integration_test"

	err := suite.db.UpdateEquipmentPosition(equipmentID, position, confidence, source)
	suite.NoError(err)

	// Verify position was updated
	equipment, err := suite.db.GetEquipmentPosition(equipmentID)
	suite.NoError(err)
	suite.NotNil(equipment.SpatialData)
	suite.InDelta(position.X, equipment.SpatialData.Position.X, 0.0001)
	suite.InDelta(position.Y, equipment.SpatialData.Position.Y, 0.0001)
	suite.InDelta(position.Z, equipment.SpatialData.Position.Z, 0.0001)
	suite.Equal(confidence, equipment.SpatialData.Confidence)
	suite.Equal(source, equipment.SpatialData.Source)
}

func (suite *PostGISSpatialTestSuite) TestQueryBySpatialProximity() {
	// Update positions for test equipment
	positions := []spatial.Point3D{
		{X: -122.4194, Y: 37.7749, Z: 10.0}, // Equipment 1
		{X: -122.4195, Y: 37.7750, Z: 10.0}, // Equipment 2 (nearby)
		{X: -122.4300, Y: 37.7800, Z: 10.0}, // Equipment 3 (far)
	}

	for i, id := range suite.testEquipmentIDs[:3] {
		err := suite.db.UpdateEquipmentPosition(id, positions[i], spatial.ConfidenceHigh, "test")
		suite.NoError(err)
	}

	// Query for equipment within 100 meters of first position
	center := positions[0]
	radiusMeters := 100.0

	results, err := suite.db.QueryBySpatialProximity(center, radiusMeters)
	suite.NoError(err)
	suite.Len(results, 2, "Should find 2 equipment within radius")

	// Verify results are sorted by distance
	if len(results) >= 2 {
		suite.Less(*results[0].SpatialData.Distance, *results[1].SpatialData.Distance)
	}
}

func (suite *PostGISSpatialTestSuite) TestQueryByBoundingBox() {
	// Update positions for test equipment
	positions := []spatial.Point3D{
		{X: -122.420, Y: 37.775, Z: 10.0},
		{X: -122.419, Y: 37.776, Z: 11.0},
		{X: -122.418, Y: 37.774, Z: 12.0},
	}

	for i, id := range suite.testEquipmentIDs[:3] {
		err := suite.db.UpdateEquipmentPosition(id, positions[i], spatial.ConfidenceHigh, "test")
		suite.NoError(err)
	}

	// Define bounding box
	bbox := spatial.BoundingBox{
		Min: spatial.Point3D{X: -122.421, Y: 37.773, Z: 9.0},
		Max: spatial.Point3D{X: -122.417, Y: 37.777, Z: 13.0},
	}

	results, err := suite.db.QueryByBoundingBox(bbox)
	suite.NoError(err)
	suite.Len(results, 3, "Should find all 3 equipment in bounding box")
}

// Test Building Transform Operations

func (suite *PostGISSpatialTestSuite) TestSetAndGetBuildingOrigin() {
	gps := spatial.GPSCoordinate{
		Latitude:  37.7749,
		Longitude: -122.4194,
		Altitude:  50.0,
	}
	rotation := 45.0
	gridScale := 1.5

	// Set building origin
	err := suite.db.SetBuildingOrigin(suite.testBuildingID, gps, rotation, gridScale)
	suite.NoError(err)

	// Get building origin
	retrievedGPS, err := suite.db.GetBuildingOrigin(suite.testBuildingID)
	suite.NoError(err)
	suite.InDelta(gps.Latitude, retrievedGPS.Latitude, 0.0001)
	suite.InDelta(gps.Longitude, retrievedGPS.Longitude, 0.0001)
	suite.InDelta(gps.Altitude, retrievedGPS.Altitude, 0.0001)

	// Get building transform
	transform, err := suite.db.GetBuildingTransform(suite.testBuildingID)
	suite.NoError(err)
	suite.InDelta(rotation, transform.Rotation, 0.01)
	suite.InDelta(gridScale, transform.Scale, 0.01)
}

// Test Coverage Operations

func (suite *PostGISSpatialTestSuite) TestAddScannedRegion() {
	region := spatial.ScannedRegion{
		ID:         uuid.New().String(),
		BuildingID: suite.testBuildingID,
		Floor:      1,
		Boundary: []spatial.Point3D{
			{X: -122.420, Y: 37.774},
			{X: -122.419, Y: 37.774},
			{X: -122.419, Y: 37.775},
			{X: -122.420, Y: 37.775},
		},
		Confidence: spatial.ConfidenceHigh,
		ScanType:   "lidar",
		ScannerID:  "scanner_001",
		ScannedAt:  time.Now(),
	}

	err := suite.db.AddScannedRegion(region)
	suite.NoError(err)

	// Get coverage map
	coverageMap, err := suite.db.GetCoverageMap(suite.testBuildingID)
	suite.NoError(err)
	suite.NotNil(coverageMap)
	suite.Equal(suite.testBuildingID, coverageMap.BuildingID)
	suite.GreaterOrEqual(len(coverageMap.Regions), 1)
}

func (suite *PostGISSpatialTestSuite) TestCalculateCoveragePercentage() {
	// Add some equipment positions
	positions := []spatial.Point3D{
		{X: -122.420, Y: 37.774, Z: 10.0},
		{X: -122.419, Y: 37.775, Z: 10.0},
		{X: -122.418, Y: 37.776, Z: 10.0},
	}

	for i, id := range suite.testEquipmentIDs[:3] {
		err := suite.db.UpdateEquipmentPosition(id, positions[i], spatial.ConfidenceHigh, "test")
		suite.NoError(err)
	}

	// Add a scanned region
	region := spatial.ScannedRegion{
		ID:         uuid.New().String(),
		BuildingID: suite.testBuildingID,
		Floor:      1,
		Boundary: []spatial.Point3D{
			{X: -122.420, Y: 37.774},
			{X: -122.419, Y: 37.774},
			{X: -122.419, Y: 37.775},
			{X: -122.420, Y: 37.775},
		},
		Confidence: spatial.ConfidenceHigh,
		ScanType:   "lidar",
		ScannerID:  "scanner_001",
		ScannedAt:  time.Now(),
	}

	err := suite.db.AddScannedRegion(region)
	suite.NoError(err)

	// Calculate coverage percentage
	percentage, err := suite.db.CalculateCoveragePercentage(suite.testBuildingID)
	suite.NoError(err)
	suite.GreaterOrEqual(percentage, 0.0)
	suite.LessOrEqual(percentage, 100.0)
}

// Test Distance Calculations

func (suite *PostGISSpatialTestSuite) TestCalculateDistance() {
	// Set positions for two equipment
	pos1 := spatial.Point3D{X: -122.4194, Y: 37.7749, Z: 10.0}
	pos2 := spatial.Point3D{X: -122.4195, Y: 37.7750, Z: 10.0}

	err := suite.db.UpdateEquipmentPosition(suite.testEquipmentIDs[0], pos1, spatial.ConfidenceHigh, "test")
	suite.NoError(err)

	err = suite.db.UpdateEquipmentPosition(suite.testEquipmentIDs[1], pos2, spatial.ConfidenceHigh, "test")
	suite.NoError(err)

	// Calculate distance
	distance, err := suite.db.CalculateDistance(suite.testEquipmentIDs[0], suite.testEquipmentIDs[1])
	suite.NoError(err)
	suite.Greater(distance, 0.0)
	suite.Less(distance, 200.0, "Distance should be less than 200 meters")
}

func (suite *PostGISSpatialTestSuite) TestFindNearestEquipment() {
	// Set positions for test equipment with different types
	positions := []spatial.Point3D{
		{X: -122.4194, Y: 37.7749, Z: 10.0},
		{X: -122.4195, Y: 37.7750, Z: 10.0},
		{X: -122.4196, Y: 37.7751, Z: 10.0},
	}

	types := []string{"outlet", "outlet", "switch"}

	for i, id := range suite.testEquipmentIDs[:3] {
		err := suite.db.UpdateEquipmentPosition(id, positions[i], spatial.ConfidenceHigh, "test")
		suite.NoError(err)

		// Update equipment type
		_, err = suite.db.Exec(suite.ctx, "UPDATE equipment SET type = $1 WHERE id = $2", types[i], id)
		suite.NoError(err)
	}

	// Find nearest outlet from a position
	queryPos := spatial.Point3D{X: -122.4193, Y: 37.7748, Z: 10.0}
	nearest, err := suite.db.FindNearestEquipment(queryPos, "outlet")

	suite.NoError(err)
	suite.NotNil(nearest)
	suite.Equal("outlet", nearest.Type)
	suite.NotNil(nearest.SpatialData.Distance)
}

// Helper Functions

func (suite *PostGISSpatialTestSuite) initializeTestSchema() error {
	schema := `
	CREATE EXTENSION IF NOT EXISTS postgis;

	CREATE TABLE IF NOT EXISTS buildings (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		arxos_id TEXT UNIQUE NOT NULL,
		name TEXT NOT NULL,
		origin GEOMETRY(Point, 4326),
		created_at TIMESTAMPTZ DEFAULT NOW()
	);

	CREATE TABLE IF NOT EXISTS equipment (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id),
		name TEXT NOT NULL,
		type TEXT NOT NULL,
		status TEXT DEFAULT 'UNKNOWN',
		floor INTEGER DEFAULT 1,
		position GEOMETRY(PointZ, 4326),
		created_at TIMESTAMPTZ DEFAULT NOW()
	);

	CREATE TABLE IF NOT EXISTS equipment_positions (
		equipment_id UUID PRIMARY KEY REFERENCES equipment(id),
		position GEOMETRY(PointZ, 4326) NOT NULL,
		confidence SMALLINT DEFAULT 0,
		source TEXT,
		updated_at TIMESTAMPTZ DEFAULT NOW()
	);

	CREATE TABLE IF NOT EXISTS building_transforms (
		building_id UUID PRIMARY KEY REFERENCES buildings(id),
		origin GEOMETRY(PointZ, 4326) NOT NULL,
		rotation FLOAT DEFAULT 0,
		grid_scale FLOAT DEFAULT 1,
		updated_at TIMESTAMPTZ DEFAULT NOW()
	);

	CREATE TABLE IF NOT EXISTS scanned_regions (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id),
		floor INTEGER,
		region GEOMETRY(Polygon, 4326) NOT NULL,
		confidence SMALLINT DEFAULT 0,
		scan_type TEXT,
		scanner_id TEXT,
		scanned_at TIMESTAMPTZ DEFAULT NOW()
	);
	`

	_, err := suite.db.Exec(suite.ctx, schema)
	return err
}

func (suite *PostGISSpatialTestSuite) createTestBuilding() string {
	buildingID := uuid.New().String()
	arxosID := "TEST-BUILDING-" + buildingID[:8]

	query := `
		INSERT INTO buildings (id, arxos_id, name)
		VALUES ($1, $2, $3)
	`

	_, err := suite.db.Exec(suite.ctx, query, buildingID, arxosID, "Test Building")
	suite.NoError(err)

	return buildingID
}

func (suite *PostGISSpatialTestSuite) createTestEquipment() []string {
	var ids []string

	for i := 0; i < 5; i++ {
		equipmentID := uuid.New().String()
		name := fmt.Sprintf("Test Equipment %d", i+1)

		query := `
			INSERT INTO equipment (id, building_id, name, type, status)
			VALUES ($1, $2, $3, $4, $5)
		`

		_, err := suite.db.Exec(suite.ctx, query,
			equipmentID, suite.testBuildingID, name, "test_type", "operational")
		suite.NoError(err)

		ids = append(ids, equipmentID)
	}

	return ids
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// Run the test suite
func TestPostGISSpatialTestSuite(t *testing.T) {
	// Skip if not running integration tests
	if os.Getenv("RUN_INTEGRATION_TESTS") != "true" {
		t.Skip("Skipping integration tests. Set RUN_INTEGRATION_TESTS=true to run.")
	}

	suite.Run(t, new(PostGISSpatialTestSuite))
}

// Benchmark tests

func BenchmarkSpatialProximityQuery(b *testing.B) {
	if os.Getenv("RUN_INTEGRATION_TESTS") != "true" {
		b.Skip("Skipping integration benchmarks")
	}

	// Setup
	config := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_test",
		User:     "arxos",
		Password: "arxos",
		SSLMode:  "disable",
	}

	db := database.NewPostGISDB(config)
	err := db.Connect(context.Background(), "")
	require.NoError(b, err)
	defer db.Close()

	center := spatial.Point3D{X: -122.4194, Y: 37.7749, Z: 10.0}
	radius := 1000.0 // 1km

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_, err := db.QueryBySpatialProximity(center, radius)
		if err != nil {
			b.Fatal(err)
		}
	}
}

func BenchmarkBoundingBoxQuery(b *testing.B) {
	if os.Getenv("RUN_INTEGRATION_TESTS") != "true" {
		b.Skip("Skipping integration benchmarks")
	}

	// Setup
	config := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_test",
		User:     "arxos",
		Password: "arxos",
		SSLMode:  "disable",
	}

	db := database.NewPostGISDB(config)
	err := db.Connect(context.Background(), "")
	require.NoError(b, err)
	defer db.Close()

	bbox := spatial.BoundingBox{
		Min: spatial.Point3D{X: -122.430, Y: 37.760, Z: 0.0},
		Max: spatial.Point3D{X: -122.410, Y: 37.780, Z: 100.0},
	}

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_, err := db.QueryByBoundingBox(bbox)
		if err != nil {
			b.Fatal(err)
		}
	}
}