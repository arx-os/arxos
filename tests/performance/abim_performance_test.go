package performance

import (
	"context"
	"fmt"
	"runtime"
	"testing"
	"time"

	"github.com/joelpate/arxos/internal/ascii/abim"
	"github.com/joelpate/arxos/internal/ascii/layers"
	"github.com/joelpate/arxos/internal/connections"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/energy"
	"github.com/joelpate/arxos/internal/maintenance"
	"github.com/joelpate/arxos/pkg/models"
)

// BenchmarkABIMFullPipeline benchmarks the complete ABIM rendering pipeline
func BenchmarkABIMFullPipeline(b *testing.B) {
	plan := createLargeBuildingPlan(100) // 100 equipment pieces
	db := createTestDB(b)
	defer db.Close()
	
	connManager := connections.NewManager(db)
	predictor := maintenance.NewPredictor(db, connManager)
	
	// Create renderer with realistic size
	renderer := abim.NewRenderer(120, 40)
	
	// Add all layers
	renderer.AddLayer("structure", layers.NewStructureLayer(plan))
	renderer.AddLayer("equipment", layers.NewEquipmentLayer(plan.Equipment))
	renderer.AddLayer("connections", layers.NewConnectionLayer(connManager))
	
	energySystem := energy.NewFlowSystem(energy.FlowElectrical, connManager)
	renderer.AddLayer("energy", layers.NewEnergyLayer(energySystem))
	renderer.AddLayer("failure", layers.NewFailureLayer(connManager, predictor))
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		renderer.Update(1.0/30.0)
		output := renderer.Render()
		
		// Simulate using the output to prevent optimization
		_ = len(output)
	}
}

// BenchmarkLayerRendering benchmarks individual layer rendering performance
func BenchmarkLayerRendering(b *testing.B) {
	plan := createLargeBuildingPlan(50)
	
	viewport := abim.Viewport{
		X: 0, Y: 0,
		Width: 100, Height: 50,
		Zoom: 1.0,
	}
	
	b.Run("Structure", func(b *testing.B) {
		layer := layers.NewStructureLayer(plan)
		b.ResetTimer()
		
		for i := 0; i < b.N; i++ {
			output := layer.Render(viewport)
			_ = len(output) // Prevent optimization
		}
	})
	
	b.Run("Equipment", func(b *testing.B) {
		layer := layers.NewEquipmentLayer(plan.Equipment)
		b.ResetTimer()
		
		for i := 0; i < b.N; i++ {
			output := layer.Render(viewport)
			_ = len(output) // Prevent optimization
		}
	})
	
	b.Run("Connections", func(b *testing.B) {
		db := createTestDB(b)
		defer db.Close()
		
		connManager := connections.NewManager(db)
		layer := layers.NewConnectionLayer(connManager)
		b.ResetTimer()
		
		for i := 0; i < b.N; i++ {
			output := layer.Render(viewport)
			_ = len(output) // Prevent optimization
		}
	})
}

// BenchmarkMemoryUsage benchmarks memory usage patterns
func BenchmarkMemoryUsage(b *testing.B) {
	plan := createLargeBuildingPlan(200)
	
	b.Run("MemoryGrowth", func(b *testing.B) {
		var renderers []*abim.Renderer
		
		for i := 0; i < b.N; i++ {
			renderer := abim.NewRenderer(80, 30)
			renderer.AddLayer("structure", layers.NewStructureLayer(plan))
			renderer.AddLayer("equipment", layers.NewEquipmentLayer(plan.Equipment))
			
			renderers = append(renderers, renderer)
			
			// Force rendering to allocate buffers
			renderer.Render()
		}
		
		// Prevent optimization
		_ = len(renderers)
	})
}

// TestABIMStressTest tests the system under stress conditions
func TestABIMStressTest(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping stress test in short mode")
	}
	
	plan := createLargeBuildingPlan(500) // Large building
	db := createTestDB(t)
	defer db.Close()
	
	connManager := connections.NewManager(db)
	predictor := maintenance.NewPredictor(db, connManager)
	
	// Create multiple renderers (simulating multiple clients)
	renderers := make([]*abim.Renderer, 5)
	for i := range renderers {
		renderer := abim.NewRenderer(100, 50)
		
		// Add all layers
		renderer.AddLayer("structure", layers.NewStructureLayer(plan))
		renderer.AddLayer("equipment", layers.NewEquipmentLayer(plan.Equipment))
		renderer.AddLayer("connections", layers.NewConnectionLayer(connManager))
		
		energySystem := energy.NewFlowSystem(energy.FlowElectrical, connManager)
		renderer.AddLayer("energy", layers.NewEnergyLayer(energySystem))
		
		failureLayer := layers.NewFailureLayer(connManager, predictor)
		failureLayer.SetSimulationMode(true) // Generate random failures
		renderer.AddLayer("failure", failureLayer)
		
		renderers[i] = renderer
	}
	
	// Run stress test for 10 seconds
	duration := 10 * time.Second
	start := time.Now()
	frames := 0
	
	ticker := time.NewTicker(33 * time.Millisecond) // ~30 FPS
	defer ticker.Stop()
	
	for time.Since(start) < duration {
		select {
		case <-ticker.C:
			// Update and render all instances
			for _, renderer := range renderers {
				renderer.Update(1.0/30.0)
				output := renderer.Render()
				
				// Verify output integrity
				if len(output) != 50 {
					t.Errorf("Invalid output height: %d", len(output))
				}
				
				for i, row := range output {
					if len(row) != 100 {
						t.Errorf("Row %d: invalid width %d", i, len(row))
					}
				}
			}
			frames++
		}
	}
	
	actualDuration := time.Since(start)
	fps := float64(frames) / actualDuration.Seconds()
	
	t.Logf("Stress test completed:")
	t.Logf("  Duration: %v", actualDuration)
	t.Logf("  Frames: %d", frames)
	t.Logf("  FPS: %.2f", fps)
	t.Logf("  Renderers: %d", len(renderers))
	t.Logf("  Equipment: %d", len(plan.Equipment))
	
	// Should maintain at least 20 FPS under stress
	if fps < 20.0 {
		t.Errorf("Performance too low: %.2f FPS", fps)
	}
}

// TestMemoryLeaks tests for memory leaks in long-running scenarios
func TestMemoryLeaks(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping memory leak test in short mode")
	}
	
	plan := createLargeBuildingPlan(100)
	db := createTestDB(t)
	defer db.Close()
	
	connManager := connections.NewManager(db)
	renderer := abim.NewRenderer(80, 30)
	renderer.AddLayer("structure", layers.NewStructureLayer(plan))
	renderer.AddLayer("equipment", layers.NewEquipmentLayer(plan.Equipment))
	renderer.AddLayer("connections", layers.NewConnectionLayer(connManager))
	
	// Record initial memory
	runtime.GC()
	var m1 runtime.MemStats
	runtime.ReadMemStats(&m1)
	
	// Run for many iterations
	iterations := 1000
	for i := 0; i < iterations; i++ {
		renderer.Update(1.0/30.0)
		output := renderer.Render()
		_ = len(output)
		
		// Occasionally force GC
		if i%100 == 0 {
			runtime.GC()
		}
	}
	
	// Record final memory
	runtime.GC()
	var m2 runtime.MemStats
	runtime.ReadMemStats(&m2)
	
	// Calculate memory growth
	initialMB := float64(m1.Alloc) / 1024 / 1024
	finalMB := float64(m2.Alloc) / 1024 / 1024
	growthMB := finalMB - initialMB
	
	t.Logf("Memory usage:")
	t.Logf("  Initial: %.2f MB", initialMB)
	t.Logf("  Final: %.2f MB", finalMB)
	t.Logf("  Growth: %.2f MB", growthMB)
	t.Logf("  Iterations: %d", iterations)
	
	// Memory growth should be reasonable (less than 10MB for 1000 iterations)
	if growthMB > 10.0 {
		t.Errorf("Excessive memory growth: %.2f MB", growthMB)
	}
}

// TestConcurrentAccess tests concurrent access to ABIM system
func TestConcurrentAccess(t *testing.T) {
	plan := createLargeBuildingPlan(50)
	db := createTestDB(t)
	defer db.Close()
	
	connManager := connections.NewManager(db)
	renderer := abim.NewRenderer(80, 30)
	renderer.AddLayer("structure", layers.NewStructureLayer(plan))
	renderer.AddLayer("equipment", layers.NewEquipmentLayer(plan.Equipment))
	renderer.AddLayer("connections", layers.NewConnectionLayer(connManager))
	
	// Number of concurrent goroutines
	concurrency := 10
	iterations := 100
	
	// Channel to collect results
	results := make(chan error, concurrency)
	
	// Start concurrent workers
	for i := 0; i < concurrency; i++ {
		go func(workerID int) {
			defer func() {
				if r := recover(); r != nil {
					results <- fmt.Errorf("worker %d panicked: %v", workerID, r)
					return
				}
				results <- nil
			}()
			
			for j := 0; j < iterations; j++ {
				// Concurrent rendering
				output := renderer.Render()
				
				// Concurrent layer visibility changes
				if j%10 == 0 {
					renderer.SetLayerVisible("equipment", j%20 == 0)
				}
				
				// Verify output
				if len(output) != 30 {
					results <- fmt.Errorf("worker %d: invalid output height", workerID)
					return
				}
			}
		}(i)
	}
	
	// Wait for all workers to complete
	for i := 0; i < concurrency; i++ {
		if err := <-results; err != nil {
			t.Errorf("Concurrent access error: %v", err)
		}
	}
}

// Helper functions

func createLargeBuildingPlan(equipmentCount int) *models.FloorPlan {
	plan := &models.FloorPlan{
		Name:     "Large Test Building",
		Building: "Performance Test",
		Level:    1,
		Rooms:    []models.Room{},
		Equipment: []models.Equipment{},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	
	// Create multiple rooms
	roomCount := equipmentCount / 10
	if roomCount < 1 {
		roomCount = 1
	}
	
	for i := 0; i < roomCount; i++ {
		room := models.Room{
			ID:   fmt.Sprintf("room_%03d", i+1),
			Name: fmt.Sprintf("Room %d", i+1),
			Bounds: models.Bounds{
				MinX: float64(i%10) * 20,
				MinY: float64(i/10) * 15,
				MaxX: float64(i%10)*20 + 18,
				MaxY: float64(i/10)*15 + 13,
			},
			Equipment: []string{},
		}
		plan.Rooms = append(plan.Rooms, room)
	}
	
	// Create equipment distributed across rooms
	equipmentTypes := []string{"panel", "outlet", "switch", "breaker", "hvac", "server", "router"}
	
	for i := 0; i < equipmentCount; i++ {
		roomIndex := i % len(plan.Rooms)
		room := &plan.Rooms[roomIndex]
		
		equipment := models.Equipment{
			ID:   fmt.Sprintf("eq_%04d", i+1),
			Name: fmt.Sprintf("Equipment %d", i+1),
			Type: equipmentTypes[i%len(equipmentTypes)],
			Location: models.Point{
				X: room.Bounds.MinX + float64(i%5)*3 + 2,
				Y: room.Bounds.MinY + float64((i/5)%3)*3 + 2,
			},
			RoomID: room.ID,
			Status: models.StatusNormal,
		}
		
		plan.Equipment = append(plan.Equipment, equipment)
		room.Equipment = append(room.Equipment, equipment.ID)
	}
	
	return plan
}

func createTestDB(tb testing.TB) database.DB {
	config := database.NewConfig(":memory:")
	db := database.NewSQLiteDB(config)
	
	ctx := context.Background()
	err := db.Connect(ctx, "")
	if err != nil {
		tb.Fatalf("Failed to create test database: %v", err)
	}
	
	return db
}