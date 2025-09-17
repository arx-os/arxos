package test

import (
	"context"
	"fmt"
	"path/filepath"
	"testing"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// BenchmarkEquipmentOperations benchmarks equipment CRUD operations
func BenchmarkEquipmentOperations(b *testing.B) {
	ctx := context.Background()

	// Setup test database with embedded migrations
	tempDir := b.TempDir()
	dbPath := filepath.Join(tempDir, "bench.db")

	dbConfig := database.NewConfig(dbPath)
	db := database.NewSQLiteDB(dbConfig)

	err := db.Connect(ctx, dbPath)
	if err != nil {
		b.Fatal(err)
	}
	defer db.Close()

	b.Run("SaveEquipment", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			equipment := &models.Equipment{
				ID:     fmt.Sprintf("BENCH_EQ_%d", i),
				Name:   fmt.Sprintf("Benchmark Equipment %d", i),
				Type:   "HVAC",
				Status: models.StatusOperational,
				Location: &models.Point{
					X: float64(i * 10),
					Y: float64(i * 20),
				},
			}

			err := db.SaveEquipment(ctx, equipment)
			if err != nil {
				b.Fatal(err)
			}
		}
	})

	b.Run("GetEquipment", func(b *testing.B) {
		// Pre-populate some equipment
		for i := 0; i < 100; i++ {
			equipment := &models.Equipment{
				ID:     fmt.Sprintf("GET_EQ_%d", i),
				Name:   fmt.Sprintf("Get Equipment %d", i),
				Type:   "ELECTRICAL",
				Status: models.StatusOperational,
			}
			db.SaveEquipment(ctx, equipment)
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			id := fmt.Sprintf("GET_EQ_%d", i%100)
			_, err := db.GetEquipment(ctx, id)
			if err != nil {
				b.Fatal(err)
			}
		}
	})

	b.Run("UpdateEquipment", func(b *testing.B) {
		// Pre-populate equipment
		equipment := &models.Equipment{
			ID:     "UPDATE_EQ",
			Name:   "Update Equipment",
			Type:   "PLUMBING",
			Status: models.StatusOperational,
		}
		db.SaveEquipment(ctx, equipment)

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			equipment.Name = fmt.Sprintf("Updated Name %d", i)
			err := db.UpdateEquipment(ctx, equipment)
			if err != nil {
				b.Fatal(err)
			}
		}
	})
}

// BenchmarkFloorPlanQueries benchmarks floor plan queries
func BenchmarkFloorPlanQueries(b *testing.B) {
	ctx := context.Background()

	// Setup test database with embedded migrations
	tempDir := b.TempDir()
	dbPath := filepath.Join(tempDir, "bench.db")

	dbConfig := database.NewConfig(dbPath)
	db := database.NewSQLiteDB(dbConfig)

	err := db.Connect(ctx, dbPath)
	if err != nil {
		b.Fatal(err)
	}
	defer db.Close()

	// Pre-populate floor plans
	for i := 0; i < 10; i++ {
		floorPlan := &models.FloorPlan{
			ID:       fmt.Sprintf("FLOOR_%d", i),
			Name:     fmt.Sprintf("Floor %d", i),
			Building: "Benchmark Building",
			Level:    i,
		}
		db.SaveFloorPlan(ctx, floorPlan)

		// Add equipment to each floor
		for j := 0; j < 100; j++ {
			equipment := &models.Equipment{
				ID:     fmt.Sprintf("FLOOR_%d_EQ_%d", i, j),
				Name:   fmt.Sprintf("Equipment %d-%d", i, j),
				Type:   "MIXED",
				Status: models.StatusOperational,
			}
			db.SaveEquipment(ctx, equipment)
		}
	}

	b.Run("GetAllFloorPlans", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			_, err := db.GetAllFloorPlans(ctx)
			if err != nil {
				b.Fatal(err)
			}
		}
	})

	b.Run("GetFloorPlanWithEquipment", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			floorID := fmt.Sprintf("FLOOR_%d", i%10)
			floorPlan, err := db.GetFloorPlan(ctx, floorID)
			if err != nil {
				b.Fatal(err)
			}

			// Simulate loading equipment
			_, err = db.GetEquipmentByFloorPlan(ctx, floorPlan.ID)
			if err != nil {
				b.Fatal(err)
			}
		}
	})
}

// BenchmarkConcurrentOperations benchmarks concurrent database operations
func BenchmarkConcurrentOperations(b *testing.B) {
	ctx := context.Background()

	// Setup test database with embedded migrations
	tempDir := b.TempDir()
	dbPath := filepath.Join(tempDir, "bench.db")

	dbConfig := database.NewConfig(dbPath)
	db := database.NewSQLiteDB(dbConfig)

	err := db.Connect(ctx, dbPath)
	if err != nil {
		b.Fatal(err)
	}
	defer db.Close()

	b.Run("ConcurrentReads", func(b *testing.B) {
		// Pre-populate data
		for i := 0; i < 100; i++ {
			equipment := &models.Equipment{
				ID:     fmt.Sprintf("CONC_EQ_%d", i),
				Name:   fmt.Sprintf("Concurrent Equipment %d", i),
				Type:   "CONCURRENT",
				Status: models.StatusOperational,
			}
			db.SaveEquipment(ctx, equipment)
		}

		b.ResetTimer()
		b.RunParallel(func(pb *testing.PB) {
			i := 0
			for pb.Next() {
				id := fmt.Sprintf("CONC_EQ_%d", i%100)
				_, err := db.GetEquipment(ctx, id)
				if err != nil {
					b.Fatal(err)
				}
				i++
			}
		})
	})

	b.Run("ConcurrentWrites", func(b *testing.B) {
		b.RunParallel(func(pb *testing.PB) {
			i := 0
			for pb.Next() {
				equipment := &models.Equipment{
					ID:     fmt.Sprintf("WRITE_EQ_%d_%d", b.N, i),
					Name:   fmt.Sprintf("Write Equipment %d", i),
					Type:   "WRITE_TEST",
					Status: models.StatusOperational,
				}
				err := db.SaveEquipment(ctx, equipment)
				if err != nil {
					b.Fatal(err)
				}
				i++
			}
		})
	})
}