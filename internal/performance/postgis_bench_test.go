package performance_test

import (
	"context"
	"fmt"
	"math/rand"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/stretchr/testify/require"
)

// BenchmarkPostGISSpatialQueries benchmarks various spatial queries
func BenchmarkPostGISSpatialQueries(b *testing.B) {
	ctx := context.Background()

	// Setup PostGIS connection
	pgConfig := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_bench",
		User:     "postgres",
		Password: "",
		SSLMode:  "disable",
	}

	db := database.NewPostGISDB(pgConfig)
	if err := db.Connect(ctx); err != nil {
		b.Skip("PostGIS not available:", err)
	}
	defer db.Close()

	// Generate test data
	equipmentCount := 10000
	generateTestEquipment(b, db, equipmentCount)

	// Benchmark proximity queries
	b.Run("ProximityQuery_1m", func(b *testing.B) {
		center := database.Point3D{X: 50, Y: 50, Z: 5}
		radius := 1.0 // 1 meter

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryBySpatialProximity(center, radius)
			require.NoError(b, err)
			_ = results
		}
	})

	b.Run("ProximityQuery_10m", func(b *testing.B) {
		center := database.Point3D{X: 50, Y: 50, Z: 5}
		radius := 10.0 // 10 meters

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryBySpatialProximity(center, radius)
			require.NoError(b, err)
			_ = results
		}
	})

	b.Run("ProximityQuery_50m", func(b *testing.B) {
		center := database.Point3D{X: 50, Y: 50, Z: 5}
		radius := 50.0 // 50 meters

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryBySpatialProximity(center, radius)
			require.NoError(b, err)
			_ = results
		}
	})

	// Benchmark containment queries
	b.Run("ContainmentQuery_SmallBox", func(b *testing.B) {
		bounds := database.BoundingBox{
			Min: database.Point3D{X: 40, Y: 40, Z: 0},
			Max: database.Point3D{X: 60, Y: 60, Z: 10},
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryByBoundingBox(bounds)
			require.NoError(b, err)
			_ = results
		}
	})

	b.Run("ContainmentQuery_LargeBox", func(b *testing.B) {
		bounds := database.BoundingBox{
			Min: database.Point3D{X: 0, Y: 0, Z: 0},
			Max: database.Point3D{X: 100, Y: 100, Z: 20},
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryByBoundingBox(bounds)
			require.NoError(b, err)
			_ = results
		}
	})

	// Benchmark floor queries
	b.Run("FloorQuery", func(b *testing.B) {
		floorZ := 5.0
		tolerance := 0.5

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryByFloor(floorZ, tolerance)
			require.NoError(b, err)
			_ = results
		}
	})

	// Benchmark nearest neighbor queries
	b.Run("NearestNeighbor_5", func(b *testing.B) {
		point := database.Point3D{X: 50, Y: 50, Z: 5}
		limit := 5

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryNearestNeighbors(point, limit)
			require.NoError(b, err)
			_ = results
		}
	})

	b.Run("NearestNeighbor_50", func(b *testing.B) {
		point := database.Point3D{X: 50, Y: 50, Z: 5}
		limit := 50

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryNearestNeighbors(point, limit)
			require.NoError(b, err)
			_ = results
		}
	})
}

// BenchmarkPostGISInsertPerformance benchmarks insert operations
func BenchmarkPostGISInsertPerformance(b *testing.B) {
	ctx := context.Background()

	// Setup PostGIS connection
	pgConfig := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_bench",
		User:     "postgres",
		Password: "",
		SSLMode:  "disable",
	}

	db := database.NewPostGISDB(pgConfig)
	if err := db.Connect(ctx); err != nil {
		b.Skip("PostGIS not available:", err)
	}
	defer db.Close()

	// Benchmark single inserts
	b.Run("SingleInsert", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			eq := generateRandomEquipment(i)
			err := db.InsertEquipment(ctx, eq)
			require.NoError(b, err)
		}
	})

	// Benchmark batch inserts
	b.Run("BatchInsert_10", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			batch := make([]*database.SpatialEquipment, 10)
			for j := 0; j < 10; j++ {
				batch[j] = generateRandomEquipment(i*10 + j)
			}
			err := db.BatchInsertEquipment(ctx, batch)
			require.NoError(b, err)
		}
	})

	b.Run("BatchInsert_100", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			batch := make([]*database.SpatialEquipment, 100)
			for j := 0; j < 100; j++ {
				batch[j] = generateRandomEquipment(i*100 + j)
			}
			err := db.BatchInsertEquipment(ctx, batch)
			require.NoError(b, err)
		}
	})

	b.Run("BatchInsert_1000", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			batch := make([]*database.SpatialEquipment, 1000)
			for j := 0; j < 1000; j++ {
				batch[j] = generateRandomEquipment(i*1000 + j)
			}
			err := db.BatchInsertEquipment(ctx, batch)
			require.NoError(b, err)
		}
	})
}

// BenchmarkPostGISIndexEffectiveness tests the effectiveness of spatial indices
func BenchmarkPostGISIndexEffectiveness(b *testing.B) {
	ctx := context.Background()

	// Setup PostGIS connection
	pgConfig := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_bench",
		User:     "postgres",
		Password: "",
		SSLMode:  "disable",
	}

	db := database.NewPostGISDB(pgConfig)
	if err := db.Connect(ctx); err != nil {
		b.Skip("PostGIS not available:", err)
	}
	defer db.Close()

	// Test with index
	b.Run("WithSpatialIndex", func(b *testing.B) {
		// Ensure index exists
		db.CreateSpatialIndex(ctx, "equipment", "location")

		center := database.Point3D{X: 50, Y: 50, Z: 5}
		radius := 10.0

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryBySpatialProximity(center, radius)
			require.NoError(b, err)
			_ = results
		}
	})

	// Test without index (if possible to drop/disable)
	b.Run("WithoutSpatialIndex", func(b *testing.B) {
		// Drop index temporarily
		db.DropSpatialIndex(ctx, "equipment", "location")
		defer db.CreateSpatialIndex(ctx, "equipment", "location") // Restore

		center := database.Point3D{X: 50, Y: 50, Z: 5}
		radius := 10.0

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results, err := db.QueryBySpatialProximity(center, radius)
			require.NoError(b, err)
			_ = results
		}
	})
}

// Helper functions

func generateTestEquipment(b *testing.B, db *database.PostGISDB, count int) {
	ctx := context.Background()
	b.Helper()

	// Clear existing data
	db.TruncateEquipment(ctx)

	// Generate equipment distributed across a 100x100x20 meter building
	batch := make([]*database.SpatialEquipment, count)
	for i := 0; i < count; i++ {
		batch[i] = &database.SpatialEquipment{
			ID:   fmt.Sprintf("EQ_%06d", i),
			Name: fmt.Sprintf("Equipment %d", i),
			Type: randomType(),
			Location: database.Point3D{
				X: rand.Float64() * 100,
				Y: rand.Float64() * 100,
				Z: rand.Float64() * 20,
			},
			FloorLevel: int(rand.Float64() * 5),
			RoomID:     fmt.Sprintf("R%03d", rand.Intn(50)),
			Status:     "OPERATIONAL",
		}
	}

	// Insert in batches of 1000
	for i := 0; i < count; i += 1000 {
		end := i + 1000
		if end > count {
			end = count
		}
		if err := db.BatchInsertEquipment(ctx, batch[i:end]); err != nil {
			b.Fatal("Failed to insert test data:", err)
		}
	}

	// Create spatial index
	if err := db.CreateSpatialIndex(ctx, "equipment", "location"); err != nil {
		b.Fatal("Failed to create spatial index:", err)
	}

	b.Logf("Generated %d test equipment items", count)
}

func generateRandomEquipment(seed int) *database.SpatialEquipment {
	rand.Seed(int64(seed))
	return &database.SpatialEquipment{
		ID:   fmt.Sprintf("EQ_%d_%d", time.Now().Unix(), seed),
		Name: fmt.Sprintf("Equipment %d", seed),
		Type: randomType(),
		Location: database.Point3D{
			X: rand.Float64() * 100,
			Y: rand.Float64() * 100,
			Z: rand.Float64() * 20,
		},
		FloorLevel: rand.Intn(5),
		RoomID:     fmt.Sprintf("R%03d", rand.Intn(50)),
		Status:     "OPERATIONAL",
	}
}

func randomType() string {
	types := []string{"HVAC", "ELECTRICAL", "PLUMBING", "LIGHTING", "SAFETY", "NETWORK"}
	return types[rand.Intn(len(types))]
}

// Performance test results tracking
type PerformanceResult struct {
	TestName      string
	Operations    int
	TotalTime     time.Duration
	OpsPerSecond  float64
	AvgLatency    time.Duration
	P50Latency    time.Duration
	P95Latency    time.Duration
	P99Latency    time.Duration
}

// TestPostGISPerformanceTargets verifies performance meets targets
func TestPostGISPerformanceTargets(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance target tests in short mode")
	}

	ctx := context.Background()

	// Setup PostGIS connection
	pgConfig := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_bench",
		User:     "postgres",
		Password: "",
		SSLMode:  "disable",
	}

	db := database.NewPostGISDB(pgConfig)
	if err := db.Connect(ctx); err != nil {
		t.Skip("PostGIS not available:", err)
	}
	defer db.Close()

	// Generate 10K equipment items
	generateTestEquipment(&testing.B{}, db, 10000)

	// Test spatial query performance
	t.Run("SpatialQueryTarget_50ms", func(t *testing.T) {
		center := database.Point3D{X: 50, Y: 50, Z: 5}
		radius := 10.0

		start := time.Now()
		results, err := db.QueryBySpatialProximity(center, radius)
		duration := time.Since(start)

		require.NoError(t, err)
		require.NotNil(t, results)

		// Target: <50ms for 10K equipment
		if duration > 50*time.Millisecond {
			t.Errorf("Spatial query took %v, target is <50ms", duration)
		}
		t.Logf("Spatial query completed in %v (target: <50ms)", duration)
	})

	// Test batch insert performance
	t.Run("BatchInsertTarget_1000items", func(t *testing.T) {
		batch := make([]*database.SpatialEquipment, 1000)
		for i := 0; i < 1000; i++ {
			batch[i] = generateRandomEquipment(i)
		}

		start := time.Now()
		err := db.BatchInsertEquipment(ctx, batch)
		duration := time.Since(start)

		require.NoError(t, err)

		// Target: <1s for 1000 items
		if duration > 1*time.Second {
			t.Errorf("Batch insert took %v, target is <1s", duration)
		}
		t.Logf("Batch insert of 1000 items completed in %v (target: <1s)", duration)
	})
}