package cgo

import (
	"testing"
	"time"
)

// ============================================================================
// CGO BRIDGE COMPREHENSIVE TESTS
// ============================================================================

// TestArxObjectOperations tests basic ArxObject operations
func TestArxObjectOperations(t *testing.T) {
	// Test object creation
	obj, err := CreateArxObject("test_obj", "wall", "Test Wall", 1)
	if err != nil {
		t.Fatalf("Failed to create ArxObject: %v", err)
	}
	defer obj.Destroy()

	// Test property operations
	err = obj.SetProperty("material", "concrete")
	if err != nil {
		t.Errorf("Failed to set property: %v", err)
	}

	value, err := obj.GetProperty("material")
	if err != nil {
		t.Errorf("Failed to get property: %v", err)
	}
	if value != "concrete" {
		t.Errorf("Expected 'concrete', got '%s'", value)
	}

	// Test position operations
	obj.SetPosition(10.5, 20.3, 5.0)
	x, y, z := obj.GetPosition()
	if x != 10.5 || y != 20.3 || z != 5.0 {
		t.Errorf("Position mismatch: expected (10.5, 20.3, 5.0), got (%f, %f, %f)", x, y, z)
	}
}

// TestBuildingManagement tests building operations
func TestBuildingManagement(t *testing.T) {
	// Create building
	building, err := CreateArxBuilding("Test Building", "Test Description")
	if err != nil {
		t.Fatalf("Failed to create building: %v", err)
	}
	defer building.Destroy()

	// Create objects
	wall1, _ := CreateArxObject("wall1", "wall", "North Wall", 1)
	wall2, _ := CreateArxObject("wall2", "wall", "South Wall", 1)
	defer wall1.Destroy()
	defer wall2.Destroy()

	// Add objects to building
	err = building.AddObject(wall1)
	if err != nil {
		t.Errorf("Failed to add wall1: %v", err)
	}

	err = building.AddObject(wall2)
	if err != nil {
		t.Errorf("Failed to add wall2: %v", err)
	}

	// Get building summary
	summary, err := building.GetSummary()
	if err != nil {
		t.Errorf("Failed to get summary: %v", err)
	}
	if summary == "" {
		t.Error("Empty building summary")
	}
}

// TestASCIIGeneration tests ASCII art generation
func TestASCIIGeneration(t *testing.T) {
	// Create test objects
	var objects []*ArxObject
	for i := 0; i < 5; i++ {
		obj, _ := CreateArxObject(
			fmt.Sprintf("obj_%d", i),
			"wall",
			fmt.Sprintf("Wall %d", i),
			1,
		)
		obj.SetPosition(float64(i*10), float64(i*5), 0)
		objects = append(objects, obj)
		defer obj.Destroy()
	}

	// Test 2D floor plan generation
	floorPlan, err := Generate2DFloorPlan(objects, 80, 40, 1.0)
	if err != nil {
		t.Errorf("Failed to generate 2D floor plan: %v", err)
	}
	if len(floorPlan) == 0 {
		t.Error("Empty floor plan generated")
	}

	// Test 3D building view generation
	building3D, err := Generate3DBuildingView(objects, 60, 30, 20, 1.0)
	if err != nil {
		t.Errorf("Failed to generate 3D view: %v", err)
	}
	if len(building3D) == 0 {
		t.Error("Empty 3D view generated")
	}
}

// TestSpatialIndexing tests spatial index operations
func TestSpatialIndexing(t *testing.T) {
	// Create spatial index
	index, err := CreateSpatialIndex(8, true)
	if err != nil {
		t.Fatalf("Failed to create spatial index: %v", err)
	}
	defer index.Destroy()

	// Create and add objects
	for i := 0; i < 10; i++ {
		obj, _ := CreateArxObject(
			fmt.Sprintf("spatial_obj_%d", i),
			"equipment",
			fmt.Sprintf("Equipment %d", i),
			40,
		)
		obj.SetPosition(float64(i*10), float64(i*10), 0)
		err = index.AddObject(obj)
		if err != nil {
			t.Errorf("Failed to add object to index: %v", err)
		}
		defer obj.Destroy()
	}

	// Test range query
	results, err := index.Query(QueryTypeRange, 0, 0, 0, 50, 50, 10, 0, 10)
	if err != nil {
		t.Errorf("Range query failed: %v", err)
	}
	if len(results) == 0 {
		t.Error("No results from range query")
	}

	// Test radius query
	results, err := index.Query(QueryTypeRadius, 25, 25, 0, 30, 0, 0, 0, 10)
	if err != nil {
		t.Errorf("Radius query failed: %v", err)
	}

	// Get statistics
	stats, err := index.GetStatistics()
	if err != nil {
		t.Errorf("Failed to get statistics: %v", err)
	}
	if stats == "" {
		t.Error("Empty statistics")
	}
}

// TestVersionControl tests version control operations
func TestVersionControl(t *testing.T) {
	// Create temporary directory for testing
	tmpDir := t.TempDir()

	// Initialize repository
	vc, err := InitRepo(tmpDir, "Test User", "test@example.com")
	if err != nil {
		t.Fatalf("Failed to init repo: %v", err)
	}
	defer vc.Destroy()

	// Create initial commit
	hash1, err := vc.Commit("Initial commit", "", "")
	if err != nil {
		t.Errorf("Failed to create commit: %v", err)
	}
	if hash1 == "" {
		t.Error("Empty commit hash")
	}

	// Create another commit
	hash2, err := vc.Commit("Second commit", "", "")
	if err != nil {
		t.Errorf("Failed to create second commit: %v", err)
	}

	// Get history
	history, err := vc.GetHistory(10)
	if err != nil {
		t.Errorf("Failed to get history: %v", err)
	}
	if history == "" {
		t.Error("Empty history")
	}

	// Get diff
	diff, err := vc.GetDiff(hash1, hash2)
	if err != nil {
		t.Errorf("Failed to get diff: %v", err)
	}
	if diff == "" {
		t.Error("Empty diff")
	}
}

// ============================================================================
// PERFORMANCE BENCHMARKS
// ============================================================================

// BenchmarkArxObjectCreation benchmarks object creation
func BenchmarkArxObjectCreation(b *testing.B) {
	for i := 0; i < b.N; i++ {
		obj, err := CreateArxObject("bench_obj", "wall", "Benchmark Wall", 1)
		if err != nil {
			b.Fatal(err)
		}
		obj.Destroy()
	}
}

// BenchmarkPropertyOperations benchmarks property get/set
func BenchmarkPropertyOperations(b *testing.B) {
	obj, _ := CreateArxObject("bench_obj", "wall", "Benchmark Wall", 1)
	defer obj.Destroy()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		obj.SetProperty("test_key", "test_value")
		obj.GetProperty("test_key")
	}
}

// BenchmarkASCIIGeneration benchmarks ASCII generation
func BenchmarkASCIIGeneration(b *testing.B) {
	// Create test objects
	var objects []*ArxObject
	for i := 0; i < 20; i++ {
		obj, _ := CreateArxObject(
			fmt.Sprintf("bench_%d", i),
			"wall",
			fmt.Sprintf("Wall %d", i),
			1,
		)
		obj.SetPosition(float64(i*10), float64(i*5), 0)
		objects = append(objects, obj)
		defer obj.Destroy()
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Generate2DFloorPlan(objects, 80, 40, 1.0)
	}
}

// BenchmarkSpatialQuery benchmarks spatial queries
func BenchmarkSpatialQuery(b *testing.B) {
	index, _ := CreateSpatialIndex(8, true)
	defer index.Destroy()

	// Add many objects
	for i := 0; i < 100; i++ {
		obj, _ := CreateArxObject(
			fmt.Sprintf("spatial_%d", i),
			"equipment",
			fmt.Sprintf("Equipment %d", i),
			40,
		)
		obj.SetPosition(float64(i%10*10), float64(i/10*10), 0)
		index.AddObject(obj)
		defer obj.Destroy()
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		index.Query(QueryTypeRange, 0, 0, 0, 50, 50, 10, 0, 10)
	}
}

// ============================================================================
// FALLBACK TESTS
// ============================================================================

// TestFallbackBehavior tests behavior when CGO is unavailable
func TestFallbackBehavior(t *testing.T) {
	// This would test the fallback behavior
	// In a real scenario, we'd simulate CGO being unavailable
	// For now, we just ensure the bridge handles errors gracefully

	// Test with invalid parameters
	obj, err := CreateArxObject("", "", "", -1)
	if err == nil {
		t.Error("Expected error for invalid parameters")
		if obj != nil {
			obj.Destroy()
		}
	}

	// Test spatial index with invalid parameters
	index, err := CreateSpatialIndex(0, false)
	if err == nil {
		t.Error("Expected error for invalid spatial index parameters")
		if index != nil {
			index.Destroy()
		}
	}
}

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

// TestEndToEndWorkflow tests a complete workflow
func TestEndToEndWorkflow(t *testing.T) {
	// 1. Create building
	building, err := CreateArxBuilding("Integration Test Building", "Full workflow test")
	if err != nil {
		t.Fatalf("Failed to create building: %v", err)
	}
	defer building.Destroy()

	// 2. Create spatial index
	index, err := CreateSpatialIndex(8, true)
	if err != nil {
		t.Fatalf("Failed to create spatial index: %v", err)
	}
	defer index.Destroy()

	// 3. Create objects with properties
	objects := make([]*ArxObject, 0)
	for i := 0; i < 5; i++ {
		obj, err := CreateArxObject(
			fmt.Sprintf("integration_obj_%d", i),
			"wall",
			fmt.Sprintf("Wall %d", i),
			1,
		)
		if err != nil {
			t.Fatalf("Failed to create object %d: %v", i, err)
		}

		// Set properties
		obj.SetProperty("material", "concrete")
		obj.SetProperty("height", "3.0m")
		obj.SetPosition(float64(i*10), float64(i*5), 0)

		// Add to building and spatial index
		building.AddObject(obj)
		index.AddObject(obj)

		objects = append(objects, obj)
		defer obj.Destroy()
	}

	// 4. Generate ASCII representations
	floorPlan, err := Generate2DFloorPlan(objects, 80, 40, 1.0)
	if err != nil {
		t.Errorf("Failed to generate floor plan: %v", err)
	}

	building3D, err := Generate3DBuildingView(objects, 60, 30, 20, 1.0)
	if err != nil {
		t.Errorf("Failed to generate 3D view: %v", err)
	}

	// 5. Perform spatial queries
	results, err := index.Query(QueryTypeRange, 0, 0, 0, 50, 50, 10, 0, 10)
	if err != nil {
		t.Errorf("Spatial query failed: %v", err)
	}

	// 6. Version control
	tmpDir := t.TempDir()
	vc, err := InitRepo(tmpDir, "Integration Test", "test@arxos.io")
	if err != nil {
		t.Fatalf("Failed to init repo: %v", err)
	}
	defer vc.Destroy()

	// Save building state
	commitHash, err := vc.Commit("Save building state", floorPlan, building3D)
	if err != nil {
		t.Errorf("Failed to commit: %v", err)
	}

	// Verify everything worked
	if len(floorPlan) == 0 || len(building3D) == 0 {
		t.Error("Empty ASCII generation")
	}
	if len(results) != 5 {
		t.Errorf("Expected 5 objects in spatial query, got %d", len(results))
	}
	if commitHash == "" {
		t.Error("Empty commit hash")
	}

	// Get final statistics
	stats, _ := index.GetStatistics()
	t.Logf("Final spatial index stats: %s", stats)

	summary, _ := building.GetSummary()
	t.Logf("Final building summary: %s", summary)
}

// ============================================================================
// STRESS TESTS
// ============================================================================

// TestHighVolumeOperations tests system under high load
func TestHighVolumeOperations(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping stress test in short mode")
	}

	const numObjects = 1000
	const numQueries = 100

	// Create spatial index
	index, err := CreateSpatialIndex(10, true) // More levels for many objects
	if err != nil {
		t.Fatalf("Failed to create spatial index: %v", err)
	}
	defer index.Destroy()

	// Create many objects
	start := time.Now()
	objects := make([]*ArxObject, 0, numObjects)
	for i := 0; i < numObjects; i++ {
		obj, err := CreateArxObject(
			fmt.Sprintf("stress_obj_%d", i),
			"equipment",
			fmt.Sprintf("Equipment %d", i),
			40,
		)
		if err != nil {
			t.Fatalf("Failed to create object %d: %v", i, err)
		}

		// Distribute objects in 3D space
		x := float64(i % 100 * 10)
		y := float64((i / 100) % 100 * 10)
		z := float64(i / 10000 * 10)
		obj.SetPosition(x, y, z)

		index.AddObject(obj)
		objects = append(objects, obj)
	}
	createTime := time.Since(start)

	// Perform many queries
	start = time.Now()
	for i := 0; i < numQueries; i++ {
		// Random range query
		x1 := float64(i * 10 % 1000)
		y1 := float64(i * 5 % 1000)
		index.Query(QueryTypeRange, x1, y1, 0, x1+100, y1+100, 10, 0, 50)
	}
	queryTime := time.Since(start)

	// Clean up
	for _, obj := range objects {
		obj.Destroy()
	}

	// Report performance
	t.Logf("Created %d objects in %v (%.2f objects/sec)",
		numObjects, createTime, float64(numObjects)/createTime.Seconds())
	t.Logf("Performed %d queries in %v (%.2f queries/sec)",
		numQueries, queryTime, float64(numQueries)/queryTime.Seconds())

	// Performance assertions
	avgCreateTime := createTime.Nanoseconds() / int64(numObjects) / 1e6 // ms per object
	if avgCreateTime > 1 {
		t.Errorf("Object creation too slow: %dms per object (target: <1ms)", avgCreateTime)
	}

	avgQueryTime := queryTime.Nanoseconds() / int64(numQueries) / 1e6 // ms per query
	if avgQueryTime > 5 {
		t.Errorf("Spatial query too slow: %dms per query (target: <5ms)", avgQueryTime)
	}
}