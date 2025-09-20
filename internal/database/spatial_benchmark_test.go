//go:build integration
// +build integration

package database

import (
	"context"
	"fmt"
	"math/rand"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
	"github.com/stretchr/testify/require"
)

// BenchmarkSpatialQueries benchmarks spatial query performance
func BenchmarkSpatialQueries(b *testing.B) {
	// Setup test database with large dataset
	ctx := context.Background()
	db, cleanup := setupBenchmarkDB(b)
	defer cleanup()

	// Create test dataset
	setupLargeDataset(b, db, 100000) // 100k equipment items

	// Create standard queries
	standardQueries := &PostGISDB{db: db.db}

	// Create optimized queries
	optimizedQueries, err := NewOptimizedSpatialQueries(db)
	require.NoError(b, err)

	// Create indices for optimized queries
	err = optimizedQueries.CreateSpatialIndices(ctx)
	require.NoError(b, err)

	// Benchmark proximity searches
	b.Run("StandardProximity", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			center := randomPoint()
			_, _ = standardQueries.FindEquipmentNear(center, 100)
		}
	})

	b.Run("OptimizedProximity", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			center := randomPoint()
			_, _ = optimizedQueries.FindEquipmentNearOptimized(ctx, center, 100)
		}
	})

	b.Run("CachedProximity", func(b *testing.B) {
		// Pre-warm cache
		centers := make([]spatial.Point3D, 100)
		for i := range centers {
			centers[i] = randomPoint()
			_, _ = optimizedQueries.FindEquipmentNearOptimized(ctx, centers[i], 100)
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			// Use cached centers
			center := centers[i%len(centers)]
			_, _ = optimizedQueries.FindEquipmentNearOptimized(ctx, center, 100)
		}
	})

	// Benchmark bounding box searches
	b.Run("StandardBoundingBox", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			bbox := randomBBox()
			_, _ = standardQueries.FindEquipmentInBoundingBox(bbox)
		}
	})

	b.Run("OptimizedBoundingBox", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			bbox := randomBBox()
			_, _ = optimizedQueries.FindEquipmentInBoundingBoxOptimized(ctx, bbox)
		}
	})

	// Benchmark bulk operations
	b.Run("BulkProximity", func(b *testing.B) {
		centers := make([]spatial.Point3D, 10)
		for i := range centers {
			centers[i] = randomPoint()
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_, _ = optimizedQueries.BulkProximitySearch(ctx, centers, 100)
		}
	})

	// Benchmark KNN searches
	b.Run("StandardKNN", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			center := randomPoint()
			// Standard implementation would query and sort
			query := `
				SELECT equipment_id,
				       ST_Distance(position, ST_SetSRID(ST_MakePoint($1, $2, $3), 4326)) as distance
				FROM equipment_positions
				ORDER BY distance
				LIMIT 10
			`
			_, _ = db.db.QueryContext(ctx, query, center.X, center.Y, center.Z)
		}
	})

	b.Run("OptimizedKNN", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			center := randomPoint()
			_, _ = optimizedQueries.FindKNearestNeighbors(ctx, center, 10)
		}
	})

	// Benchmark clustering
	b.Run("SpatialClustering", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_, _ = optimizedQueries.ClusterEquipment(ctx, 50, 5)
		}
	})

	// Report cache metrics
	b.Logf("Cache Metrics: %+v", optimizedQueries.GetCacheMetrics())

	// Report query metrics
	metrics := optimizedQueries.GetQueryMetrics()
	for query, metric := range metrics {
		b.Logf("Query: %s - Count: %d, Avg: %v, Min: %v, Max: %v",
			query, metric.Count, metric.AvgTime, metric.MinTime, metric.MaxTime)
	}
}

// BenchmarkIndexComparison compares different index strategies
func BenchmarkIndexComparison(b *testing.B) {
	ctx := context.Background()
	db, cleanup := setupBenchmarkDB(b)
	defer cleanup()

	// Create test dataset
	setupLargeDataset(b, db, 50000)

	testCases := []struct {
		name        string
		indexSetup  func(*PostGISDB) error
		queryRadius float64
	}{
		{
			name: "NoIndex",
			indexSetup: func(db *PostGISDB) error {
				_, err := db.db.Exec("DROP INDEX IF EXISTS idx_equipment_position")
				return err
			},
			queryRadius: 100,
		},
		{
			name: "BasicGIST",
			indexSetup: func(db *PostGISDB) error {
				_, err := db.db.Exec(`
					CREATE INDEX idx_equipment_position
					ON equipment_positions USING GIST (position)
				`)
				return err
			},
			queryRadius: 100,
		},
		{
			name: "MultiResolution",
			indexSetup: func(db *PostGISDB) error {
				queries := []string{
					`CREATE INDEX idx_coarse ON equipment_positions USING GIST (ST_SnapToGrid(position, 10.0))`,
					`CREATE INDEX idx_medium ON equipment_positions USING GIST (ST_SnapToGrid(position, 1.0))`,
					`CREATE INDEX idx_fine ON equipment_positions USING GIST (ST_SnapToGrid(position, 0.1))`,
				}
				for _, q := range queries {
					if _, err := db.db.Exec(q); err != nil {
						return err
					}
				}
				return nil
			},
			queryRadius: 100,
		},
	}

	for _, tc := range testCases {
		b.Run(tc.name, func(b *testing.B) {
			// Setup index
			err := tc.indexSetup(db)
			require.NoError(b, err)

			// Analyze table
			_, _ = db.db.Exec("ANALYZE equipment_positions")

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				center := randomPoint()
				query := `
					SELECT equipment_id
					FROM equipment_positions
					WHERE ST_DWithin(position, ST_SetSRID(ST_MakePoint($1, $2, $3), 4326), $4)
				`
				_, _ = db.db.QueryContext(ctx, query, center.X, center.Y, center.Z, tc.queryRadius)
			}
		})
	}
}

// BenchmarkCacheEffectiveness measures cache impact
func BenchmarkCacheEffectiveness(b *testing.B) {
	ctx := context.Background()
	db, cleanup := setupBenchmarkDB(b)
	defer cleanup()

	setupLargeDataset(b, db, 10000)

	optimized, err := NewOptimizedSpatialQueries(db)
	require.NoError(b, err)

	// Fixed set of query centers
	centers := make([]spatial.Point3D, 100)
	for i := range centers {
		centers[i] = randomPoint()
	}

	b.Run("ColdCache", func(b *testing.B) {
		// Clear cache before each run
		optimized.optimizer.cache, _ = NewQueryCache(100*1024*1024, 5*time.Minute)

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			center := centers[rand.Intn(len(centers))]
			_, _ = optimized.FindEquipmentNearOptimized(ctx, center, 100)
		}
	})

	b.Run("WarmCache", func(b *testing.B) {
		// Pre-warm cache
		for _, center := range centers {
			_, _ = optimized.FindEquipmentNearOptimized(ctx, center, 100)
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			center := centers[rand.Intn(len(centers))]
			_, _ = optimized.FindEquipmentNearOptimized(ctx, center, 100)
		}

		metrics := optimized.GetCacheMetrics()
		b.Logf("Cache hit rate: %.2f%%", metrics.HitRate)
	})
}

// BenchmarkBulkOperations benchmarks bulk spatial operations
func BenchmarkBulkOperations(b *testing.B) {
	ctx := context.Background()
	db, cleanup := setupBenchmarkDB(b)
	defer cleanup()

	setupLargeDataset(b, db, 10000)

	optimized, err := NewOptimizedSpatialQueries(db)
	require.NoError(b, err)

	b.Run("SequentialQueries", func(b *testing.B) {
		centers := make([]spatial.Point3D, 10)
		for i := range centers {
			centers[i] = randomPoint()
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			results := make(map[string][]string)
			for j, center := range centers {
				equipment, _ := optimized.FindEquipmentNearOptimized(ctx, center, 100)
				results[fmt.Sprintf("center_%d", j)] = equipment
			}
		}
	})

	b.Run("BulkQuery", func(b *testing.B) {
		centers := make([]spatial.Point3D, 10)
		for i := range centers {
			centers[i] = randomPoint()
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_, _ = optimized.BulkProximitySearch(ctx, centers, 100)
		}
	})

	b.Run("BulkUpdate", func(b *testing.B) {
		updates := make([]PositionUpdate, 100)
		for i := range updates {
			updates[i] = PositionUpdate{
				EquipmentID: fmt.Sprintf("BENCH_%d", i),
				Position:    randomPoint(),
				Confidence:  spatial.ConfidenceMedium,
				Source:      "benchmark",
			}
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = optimized.optimizer.bulkOps.BulkUpdatePositions(ctx, updates)
		}
	})
}

// Helper functions for benchmarking

func setupBenchmarkDB(b *testing.B) (*PostGISDB, func()) {
	config := PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_bench",
		User:     "bench",
		Password: "bench",
		SSLMode:  "disable",
	}

	db := NewPostGISDB(config)
	ctx := context.Background()

	if err := db.Connect(ctx); err != nil {
		b.Fatalf("Failed to connect: %v", err)
	}

	if err := db.InitializeSchema(ctx); err != nil {
		b.Fatalf("Failed to initialize schema: %v", err)
	}

	cleanup := func() {
		// Clean up test data
		queries := []string{
			"DELETE FROM equipment_positions WHERE equipment_id LIKE 'BENCH_%'",
			"DELETE FROM equipment WHERE id LIKE 'BENCH_%'",
		}
		for _, q := range queries {
			db.db.Exec(q)
		}
		db.Close()
	}

	return db, cleanup
}

func setupLargeDataset(b *testing.B, db *PostGISDB, numItems int) {
	b.Logf("Creating dataset with %d items...", numItems)
	ctx := context.Background()

	// Batch insert for performance
	batchSize := 1000
	for i := 0; i < numItems; i += batchSize {
		tx, _ := db.db.BeginTx(ctx, nil)

		stmt, _ := tx.Prepare(`
			INSERT INTO equipment_positions (equipment_id, position, confidence, source)
			VALUES ($1, ST_SetSRID(ST_MakePoint($2, $3, $4), 4326), $5, $6)
			ON CONFLICT (equipment_id) DO NOTHING
		`)

		for j := i; j < i+batchSize && j < numItems; j++ {
			pos := randomPointInRange(100000)
			stmt.Exec(
				fmt.Sprintf("BENCH_%d", j),
				pos.X, pos.Y, pos.Z,
				"medium",
				"benchmark",
			)
		}

		stmt.Close()
		tx.Commit()
	}

	// Analyze table for query planner
	db.db.Exec("ANALYZE equipment_positions")
	b.Logf("Dataset created")
}

func randomPoint() spatial.Point3D {
	return spatial.Point3D{
		X: rand.Float64() * 10000,
		Y: rand.Float64() * 10000,
		Z: rand.Float64() * 100,
	}
}

func randomPointInRange(maxRange float64) spatial.Point3D {
	return spatial.Point3D{
		X: rand.Float64() * maxRange,
		Y: rand.Float64() * maxRange,
		Z: rand.Float64() * 1000,
	}
}

func randomBBox() spatial.BoundingBox {
	minX := rand.Float64() * 5000
	minY := rand.Float64() * 5000
	size := rand.Float64()*2000 + 100

	return spatial.BoundingBox{
		Min: spatial.Point3D{X: minX, Y: minY, Z: 0},
		Max: spatial.Point3D{X: minX + size, Y: minY + size, Z: 100},
	}
}