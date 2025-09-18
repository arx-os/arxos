//go:build integration
// +build integration

package integration

import (
	"context"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/converter"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/exporter"
	"github.com/arx-os/arxos/internal/spatial"
)

// BenchmarkPostGISOperations benchmarks various PostGIS operations
func BenchmarkPostGISOperations(b *testing.B) {
	ctx := context.Background()

	// Setup PostGIS connection
	pgConfig := &database.DatabaseConfig{
		Type:     "postgis",
		Host:     getBenchmarkPGHost(),
		Port:     5432,
		Database: "arxos_benchmark",
		User:     "arxos",
		Password: "arxos",
	}

	hybridDB, err := database.NewPostGISHybridDB(pgConfig)
	if err != nil {
		b.Skip("PostGIS not available for benchmark:", err)
	}
	defer hybridDB.Close()

	spatialDB, err := hybridDB.GetSpatialDB()
	if err != nil {
		b.Skip("Spatial DB not available:", err)
	}

	b.Run("SpatialInsert", func(b *testing.B) {
		benchmarkSpatialInsert(b, spatialDB)
	})

	b.Run("SpatialQuery", func(b *testing.B) {
		benchmarkSpatialQuery(b, spatialDB)
	})

	b.Run("IFCImport", func(b *testing.B) {
		benchmarkIFCImport(b, ctx, hybridDB)
	})

	b.Run("BIMExport", func(b *testing.B) {
		benchmarkBIMExport(b, ctx, hybridDB)
	})

	b.Run("ConcurrentQueries", func(b *testing.B) {
		benchmarkConcurrentQueries(b, spatialDB)
	})
}

// benchmarkSpatialInsert measures the performance of spatial data insertion
func benchmarkSpatialInsert(b *testing.B, spatialDB database.SpatialDB) {
	baseTime := time.Now().Unix()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		equipID := fmt.Sprintf("BENCH-INSERT-%d-%d", baseTime, i)
		position := spatial.Point3D{
			X: float64(i%1000) * 1000.0,
			Y: float64(i/1000) * 1000.0,
			Z: float64(i%10) * 3500.0,
		}

		err := spatialDB.UpdateEquipmentPosition(
			equipID,
			position,
			spatial.ConfidenceHigh,
			"Benchmark",
		)
		if err != nil {
			b.Fatalf("Insert failed: %v", err)
		}
	}
}

// benchmarkSpatialQuery measures spatial proximity query performance
func benchmarkSpatialQuery(b *testing.B, spatialDB database.SpatialDB) {
	// Pre-populate with test data
	baseTime := time.Now().Unix()
	numTestData := 10000

	for i := 0; i < numTestData; i++ {
		equipID := fmt.Sprintf("BENCH-QUERY-%d-%d", baseTime, i)
		position := spatial.Point3D{
			X: float64(i%100) * 1000.0,
			Y: float64(i/100) * 1000.0,
			Z: float64(i%10) * 3500.0,
		}

		_ = spatialDB.UpdateEquipmentPosition(equipID, position, spatial.ConfidenceMedium, "Benchmark")
	}

	// Query variations
	queryTests := []struct {
		name   string
		center spatial.Point3D
		radius float64
	}{
		{"SmallRadius", spatial.Point3D{X: 50000, Y: 50000, Z: 0}, 1.0},
		{"MediumRadius", spatial.Point3D{X: 50000, Y: 50000, Z: 0}, 10.0},
		{"LargeRadius", spatial.Point3D{X: 50000, Y: 50000, Z: 0}, 100.0},
	}

	for _, test := range queryTests {
		b.Run(test.name, func(b *testing.B) {
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				_, err := spatialDB.QueryBySpatialProximity(test.center, test.radius)
				if err != nil {
					b.Fatalf("Query failed: %v", err)
				}
			}
		})
	}
}

// benchmarkIFCImport measures IFC file import performance
func benchmarkIFCImport(b *testing.B, ctx context.Context, db *database.PostGISHybridDB) {
	converter := converter.NewImprovedIFCConverter()

	// Test different IFC file sizes
	testCases := []struct {
		name             string
		floors           int
		equipmentPerFloor int
	}{
		{"Small", 2, 10},
		{"Medium", 5, 50},
		{"Large", 10, 100},
	}

	for _, tc := range testCases {
		b.Run(tc.name, func(b *testing.B) {
			ifcContent := generateBenchmarkIFC(tc.name, tc.floors, tc.equipmentPerFloor)

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				reader := strings.NewReader(ifcContent)
				err := converter.ConvertToDB(reader, db)
				if err != nil {
					b.Fatalf("IFC import failed: %v", err)
				}
			}
		})
	}
}

// benchmarkBIMExport measures BIM export performance
func benchmarkBIMExport(b *testing.B, ctx context.Context, db *database.PostGISHybridDB) {
	// Pre-populate with test data
	converter := converter.NewImprovedIFCConverter()
	ifcContent := generateBenchmarkIFC("EXPORT-BENCH", 5, 50)
	reader := strings.NewReader(ifcContent)
	_ = converter.ConvertToDB(reader, db)

	generator := exporter.NewBIMGenerator()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		var output strings.Builder
		err := generator.GenerateFromDatabase(ctx, db, "EXPORT-BENCH", &output)
		if err != nil {
			b.Fatalf("BIM export failed: %v", err)
		}
	}
}

// benchmarkConcurrentQueries measures performance under concurrent load
func benchmarkConcurrentQueries(b *testing.B, spatialDB database.SpatialDB) {
	// Pre-populate with test data
	baseTime := time.Now().Unix()
	numTestData := 5000

	for i := 0; i < numTestData; i++ {
		equipID := fmt.Sprintf("BENCH-CONCURRENT-%d-%d", baseTime, i)
		position := spatial.Point3D{
			X: float64(i%50) * 2000.0,
			Y: float64(i/50) * 2000.0,
			Z: float64(i%5) * 3500.0,
		}
		_ = spatialDB.UpdateEquipmentPosition(equipID, position, spatial.ConfidenceMedium, "Concurrent Benchmark")
	}

	center := spatial.Point3D{X: 50000, Y: 50000, Z: 0}
	radius := 25.0

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			_, err := spatialDB.QueryBySpatialProximity(center, radius)
			if err != nil {
				b.Fatalf("Concurrent query failed: %v", err)
			}
		}
	})
}

// BenchmarkMemoryUsage benchmarks memory usage patterns
func BenchmarkMemoryUsage(b *testing.B) {
	ctx := context.Background()

	pgConfig := &database.DatabaseConfig{
		Type:     "postgis",
		Host:     getBenchmarkPGHost(),
		Port:     5432,
		Database: "arxos_memory_bench",
		User:     "arxos",
		Password: "arxos",
	}

	b.Run("DatabaseConnections", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			db, err := database.NewPostGISHybridDB(pgConfig)
			if err != nil {
				b.Skip("PostGIS not available")
			}
			db.Close()
		}
	})

	b.Run("LargeDatasetProcessing", func(b *testing.B) {
		hybridDB, err := database.NewPostGISHybridDB(pgConfig)
		if err != nil {
			b.Skip("PostGIS not available")
		}
		defer hybridDB.Close()

		spatialDB, err := hybridDB.GetSpatialDB()
		if err != nil {
			b.Skip("Spatial DB not available")
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			// Process large dataset
			center := spatial.Point3D{X: 0, Y: 0, Z: 0}
			_, err := spatialDB.QueryBySpatialProximity(center, 1000.0)
			if err != nil {
				b.Fatalf("Large dataset query failed: %v", err)
			}
		}
	})
}

// BenchmarkRealWorldScenarios benchmarks realistic usage patterns
func BenchmarkRealWorldScenarios(b *testing.B) {
	ctx := context.Background()

	pgConfig := &database.DatabaseConfig{
		Type:     "postgis",
		Host:     getBenchmarkPGHost(),
		Port:     5432,
		Database: "arxos_real_world_bench",
		User:     "arxos",
		Password: "arxos",
	}

	hybridDB, err := database.NewPostGISHybridDB(pgConfig)
	if err != nil {
		b.Skip("PostGIS not available")
	}
	defer hybridDB.Close()

	b.Run("TypicalOfficeBuilding", func(b *testing.B) {
		benchmarkTypicalOfficeBuilding(b, ctx, hybridDB)
	})

	b.Run("LargeHospitalComplex", func(b *testing.B) {
		benchmarkLargeHospitalComplex(b, ctx, hybridDB)
	})

	b.Run("IndustrialFacility", func(b *testing.B) {
		benchmarkIndustrialFacility(b, ctx, hybridDB)
	})
}

// benchmarkTypicalOfficeBuilding simulates a typical office building workflow
func benchmarkTypicalOfficeBuilding(b *testing.B, ctx context.Context, db *database.PostGISHybridDB) {
	// 20-story office building, 50 rooms per floor, 5 equipment per room
	ifcContent := generateBenchmarkIFC("OFFICE", 20, 5000)
	converter := converter.NewImprovedIFCConverter()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		reader := strings.NewReader(ifcContent)
		err := converter.ConvertToDB(reader, db)
		if err != nil {
			b.Fatalf("Office building import failed: %v", err)
		}

		// Simulate typical queries
		spatialDB, _ := db.GetSpatialDB()
		center := spatial.Point3D{X: 25000, Y: 25000, Z: 35000} // Mid-building
		_, _ = spatialDB.QueryBySpatialProximity(center, 50.0)

		// Export report
		generator := exporter.NewBIMGenerator()
		var output strings.Builder
		_ = generator.GenerateFromDatabase(ctx, db, "OFFICE", &output)
	}
}

// benchmarkLargeHospitalComplex simulates a large hospital complex
func benchmarkLargeHospitalComplex(b *testing.B, ctx context.Context, db *database.PostGISHybridDB) {
	// 8-story hospital, 100 rooms per floor, 20 equipment per room
	ifcContent := generateBenchmarkIFC("HOSPITAL", 8, 16000)
	converter := converter.NewImprovedIFCConverter()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		reader := strings.NewReader(ifcContent)
		err := converter.ConvertToDB(reader, db)
		if err != nil {
			b.Fatalf("Hospital import failed: %v", err)
		}

		// Simulate critical equipment queries
		spatialDB, _ := db.GetSpatialDB()
		emergencyCenter := spatial.Point3D{X: 50000, Y: 50000, Z: 0}
		_, _ = spatialDB.QueryBySpatialProximity(emergencyCenter, 100.0)
	}
}

// benchmarkIndustrialFacility simulates an industrial facility
func benchmarkIndustrialFacility(b *testing.B, ctx context.Context, db *database.PostGISHybridDB) {
	// 3-story industrial facility, 200 equipment per floor
	ifcContent := generateBenchmarkIFC("INDUSTRIAL", 3, 600)
	converter := converter.NewImprovedIFCConverter()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		reader := strings.NewReader(ifcContent)
		err := converter.ConvertToDB(reader, db)
		if err != nil {
			b.Fatalf("Industrial facility import failed: %v", err)
		}

		// Simulate maintenance proximity queries
		spatialDB, _ := db.GetSpatialDB()
		productionFloor := spatial.Point3D{X: 100000, Y: 50000, Z: 3500}
		_, _ = spatialDB.QueryBySpatialProximity(productionFloor, 200.0)
	}
}

// Helper functions

func getBenchmarkPGHost() string {
	if host := os.Getenv("POSTGIS_HOST"); host != "" {
		return host
	}
	return "localhost"
}

func generateBenchmarkIFC(buildingID string, floors, totalEquipment int) string {
	equipmentPerFloor := totalEquipment / floors
	if equipmentPerFloor == 0 {
		equipmentPerFloor = 1
	}

	var builder strings.Builder

	// IFC Header
	builder.WriteString("ISO-10303-21;\n")
	builder.WriteString("HEADER;\n")
	builder.WriteString("FILE_DESCRIPTION(('Benchmark Test'),'2;1');\n")
	builder.WriteString(fmt.Sprintf("FILE_NAME('benchmark.ifc','%s',(),(),'ArxOS Benchmark','','');\n",
		time.Now().Format("2006-01-02T15:04:05")))
	builder.WriteString("FILE_SCHEMA(('IFC4'));\n")
	builder.WriteString("ENDSEC;\n")
	builder.WriteString("DATA;\n")

	entityID := 1

	// Project
	builder.WriteString(fmt.Sprintf("#%d=IFCPROJECT('%s',$,'Benchmark Project',$,$,$,$,$,$);\n",
		entityID, buildingID))
	entityID++

	// Building
	builder.WriteString(fmt.Sprintf("#%d=IFCBUILDING('%s',$,'%s Building',$,$,$,$,$,.ELEMENT.,$,$,$);\n",
		entityID, buildingID, buildingID))
	entityID++

	// Generate floors and equipment
	for f := 0; f < floors; f++ {
		// Building storey
		builder.WriteString(fmt.Sprintf("#%d=IFCBUILDINGSTOREY('FLOOR-%d',$,'Level %d',$,$,$,$,$,.ELEMENT.,%f);\n",
			entityID, f, f, float64(f)*3.5))
		entityID++

		// Equipment on each floor
		for e := 0; e < equipmentPerFloor; e++ {
			// Position (spread equipment across floor)
			gridSize := int(float64(equipmentPerFloor) / 10.0)
			if gridSize == 0 {
				gridSize = 1
			}
			x := float64(e%gridSize) * 3000.0
			y := float64(e/gridSize) * 3000.0
			z := float64(f) * 3500.0

			// Cartesian point
			builder.WriteString(fmt.Sprintf("#%d=IFCCARTESIANPOINT((%.1f,%.1f,%.1f));\n",
				entityID, x, y, z))
			pointID := entityID
			entityID++

			// Placement
			builder.WriteString(fmt.Sprintf("#%d=IFCAXIS2PLACEMENT3D(#%d,$,$);\n",
				entityID, pointID))
			placementID := entityID
			entityID++

			builder.WriteString(fmt.Sprintf("#%d=IFCLOCALPLACEMENT($,#%d);\n",
				entityID, placementID))
			localPlacementID := entityID
			entityID++

			// Equipment
			equipTypes := []string{"HVAC", "ELECTRICAL", "PLUMBING", "FIRE", "SECURITY", "TELECOM", "LIGHTING", "CONTROLS"}
			equipType := equipTypes[e%len(equipTypes)]
			builder.WriteString(fmt.Sprintf("#%d=IFCDISTRIBUTIONELEMENT('%s-F%d-E%d',$,'%s Unit %d','%s',",
				entityID, buildingID, f, e, equipType, e, equipType))
			builder.WriteString(fmt.Sprintf("$,#%d,$,$);\n", localPlacementID))
			entityID++
		}
	}

	builder.WriteString("ENDSEC;\n")
	builder.WriteString("END-ISO-10303-21;")

	return builder.String()
}