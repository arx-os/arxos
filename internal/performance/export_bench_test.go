package performance_test

import (
	"bytes"
	"fmt"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/exporter"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/require"
)

// BenchmarkBIMTextGeneration benchmarks .bim.txt export performance
func BenchmarkBIMTextGeneration(b *testing.B) {
	generator := exporter.NewBIMGenerator()

	b.Run("Small_10Equipment", func(b *testing.B) {
		floorPlans := generateTestBuilding(1, 10)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := generator.GenerateFromFloorPlans(floorPlans, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("Medium_100Equipment", func(b *testing.B) {
		floorPlans := generateTestBuilding(5, 100)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := generator.GenerateFromFloorPlans(floorPlans, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("Large_1000Equipment", func(b *testing.B) {
		floorPlans := generateTestBuilding(10, 1000)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := generator.GenerateFromFloorPlans(floorPlans, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("VeryLarge_10000Equipment", func(b *testing.B) {
		floorPlans := generateTestBuilding(20, 10000)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := generator.GenerateFromFloorPlans(floorPlans, &buf)
			require.NoError(b, err)
		}
	})
}

// BenchmarkCSVExport benchmarks CSV export performance
func BenchmarkCSVExport(b *testing.B) {
	exporter := exporter.NewCSVExporter()

	b.Run("Small_10Equipment", func(b *testing.B) {
		equipment := generateEquipmentList(10)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportEquipment(equipment, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("Medium_100Equipment", func(b *testing.B) {
		equipment := generateEquipmentList(100)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportEquipment(equipment, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("Large_1000Equipment", func(b *testing.B) {
		equipment := generateEquipmentList(1000)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportEquipment(equipment, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("VeryLarge_10000Equipment", func(b *testing.B) {
		equipment := generateEquipmentList(10000)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportEquipment(equipment, &buf)
			require.NoError(b, err)
		}
	})
}

// BenchmarkJSONExport benchmarks JSON export performance
func BenchmarkJSONExport(b *testing.B) {
	exporter := exporter.NewJSONExporter()

	b.Run("Small_1Floor", func(b *testing.B) {
		floorPlans := generateTestBuilding(1, 50)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportBuilding(floorPlans, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("Medium_5Floors", func(b *testing.B) {
		floorPlans := generateTestBuilding(5, 250)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportBuilding(floorPlans, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("Large_20Floors", func(b *testing.B) {
		floorPlans := generateTestBuilding(20, 2000)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportBuilding(floorPlans, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("WithoutPrettyPrint", func(b *testing.B) {
		exporter.PrettyPrint = false
		floorPlans := generateTestBuilding(10, 1000)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportBuilding(floorPlans, &buf)
			require.NoError(b, err)
		}
	})
}

// BenchmarkMaintenanceScheduleExport benchmarks maintenance export
func BenchmarkMaintenanceScheduleExport(b *testing.B) {
	exporter := exporter.NewCSVExporter()

	b.Run("Mixed_100Equipment", func(b *testing.B) {
		equipment := generateEquipmentWithMaintenance(100)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportMaintenanceSchedule(equipment, &buf)
			require.NoError(b, err)
		}
	})

	b.Run("AllNeedMaintenance_1000", func(b *testing.B) {
		equipment := generateEquipmentWithMaintenance(1000)
		b.ResetTimer()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			err := exporter.ExportMaintenanceSchedule(equipment, &buf)
			require.NoError(b, err)
		}
	})
}

// TestExportPerformanceTargets verifies export performance meets targets
func TestExportPerformanceTargets(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance target tests in short mode")
	}

	// Test BIM export target: <15s for typical building
	t.Run("BIMExportTarget_15s", func(t *testing.T) {
		generator := exporter.NewBIMGenerator()
		floorPlans := generateTestBuilding(10, 5000) // Typical building

		var buf bytes.Buffer
		start := time.Now()
		err := generator.GenerateFromFloorPlans(floorPlans, &buf)
		duration := time.Since(start)

		require.NoError(t, err)

		// Target: <15s for .bim.txt generation
		if duration > 15*time.Second {
			t.Errorf("BIM export took %v, target is <15s", duration)
		}
		t.Logf("BIM export completed in %v (target: <15s)", duration)
		t.Logf("Generated %d bytes", buf.Len())
	})

	// Test CSV export performance
	t.Run("CSVExportTarget_5s", func(t *testing.T) {
		exporter := exporter.NewCSVExporter()
		equipment := generateEquipmentList(10000)

		var buf bytes.Buffer
		start := time.Now()
		err := exporter.ExportEquipment(equipment, &buf)
		duration := time.Since(start)

		require.NoError(t, err)

		// Target: <5s for 10K equipment CSV
		if duration > 5*time.Second {
			t.Errorf("CSV export took %v, target is <5s", duration)
		}
		t.Logf("CSV export of 10K items completed in %v (target: <5s)", duration)
	})

	// Test JSON export performance
	t.Run("JSONExportTarget_10s", func(t *testing.T) {
		exporter := exporter.NewJSONExporter()
		floorPlans := generateTestBuilding(10, 5000)

		var buf bytes.Buffer
		start := time.Now()
		err := exporter.ExportBuilding(floorPlans, &buf)
		duration := time.Since(start)

		require.NoError(t, err)

		// Target: <10s for building JSON
		if duration > 10*time.Second {
			t.Errorf("JSON export took %v, target is <10s", duration)
		}
		t.Logf("JSON export completed in %v (target: <10s)", duration)
		t.Logf("Generated %d bytes of JSON", buf.Len())
	})
}

// BenchmarkMemoryUsage benchmarks memory usage during exports
func BenchmarkMemoryUsage(b *testing.B) {
	b.Run("BIM_MemoryUsage", func(b *testing.B) {
		generator := exporter.NewBIMGenerator()
		floorPlans := generateTestBuilding(10, 5000)

		b.ResetTimer()
		b.ReportAllocs()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			_ = generator.GenerateFromFloorPlans(floorPlans, &buf)
		}
	})

	b.Run("CSV_MemoryUsage", func(b *testing.B) {
		exporter := exporter.NewCSVExporter()
		equipment := generateEquipmentList(5000)

		b.ResetTimer()
		b.ReportAllocs()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			_ = exporter.ExportEquipment(equipment, &buf)
		}
	})

	b.Run("JSON_MemoryUsage", func(b *testing.B) {
		exporter := exporter.NewJSONExporter()
		floorPlans := generateTestBuilding(10, 5000)

		b.ResetTimer()
		b.ReportAllocs()

		for i := 0; i < b.N; i++ {
			var buf bytes.Buffer
			_ = exporter.ExportBuilding(floorPlans, &buf)
		}
	})
}

// Helper functions to generate test data

func generateTestBuilding(floors, totalEquipment int) []*models.FloorPlan {
	plans := make([]*models.FloorPlan, floors)
	equipmentPerFloor := totalEquipment / floors

	for i := 0; i < floors; i++ {
		plans[i] = &models.FloorPlan{
			UUID:        "TEST-001",
			Building:    "Test Building",
			Description: "Performance test building",
			Level:       i + 1,
			Name:        fmt.Sprintf("Floor %d", i+1),
			Rooms:       generateRooms(10),
			Equipment:   generateEquipmentList(equipmentPerFloor),
		}
	}

	return plans
}

func generateRooms(count int) []*models.Room {
	rooms := make([]*models.Room, count)
	for i := 0; i < count; i++ {
		rooms[i] = &models.Room{
			ID:   fmt.Sprintf("R%03d", i+1),
			Name: fmt.Sprintf("Room %d", i+1),
			Bounds: models.Bounds{
				MinX: float64(i * 10),
				MinY: 0,
				MaxX: float64((i + 1) * 10),
				MaxY: 10,
			},
		}
	}
	return rooms
}

func generateEquipmentList(count int) []*models.Equipment {
	equipment := make([]*models.Equipment, count)
	for i := 0; i < count; i++ {
		equipment[i] = &models.Equipment{
			ID:     fmt.Sprintf("EQ-%06d", i+1),
			Name:   fmt.Sprintf("Equipment %d", i+1),
			Type:   equipmentTypes[i%len(equipmentTypes)],
			Status: equipmentStatuses[i%len(equipmentStatuses)],
			RoomID: fmt.Sprintf("R%03d", (i%10)+1),
			Path:   fmt.Sprintf("/1/A/%03d/E/EQ_%06d", (i%10)+1, i+1),
			Model:  fmt.Sprintf("Model-%d", i%5),
			Serial: fmt.Sprintf("SN%08d", i+1),
		}
	}
	return equipment
}

func generateEquipmentWithMaintenance(count int) []*models.Equipment {
	equipment := generateEquipmentList(count)
	now := time.Now()

	for i, eq := range equipment {
		// Vary maintenance dates
		daysAgo := (i % 365) + 1
		maintDate := now.AddDate(0, 0, -daysAgo)
		eq.Maintained = &maintDate

		// Set some as needing maintenance
		if daysAgo > 180 {
			eq.Status = "DEGRADED"
		}
		if daysAgo > 365 {
			eq.Status = "FAILED"
		}
	}

	return equipment
}

var equipmentTypes = []string{
	"HVAC", "ELECTRICAL", "PLUMBING", "LIGHTING", "SAFETY",
	"NETWORK", "SECURITY", "ELEVATOR", "FIRE", "ACCESS",
}

var equipmentStatuses = []string{
	"OPERATIONAL", "OPERATIONAL", "OPERATIONAL", "OPERATIONAL",
	"MAINTENANCE", "DEGRADED", "FAILED",
}
