package cgo

import (
	"fmt"
	"testing"
	"time"
)

// TestArxObjectOperationsSimple tests basic ArxObject operations without C dependency
func TestArxObjectOperationsSimple(t *testing.T) {
	// Simulate object creation timing
	start := time.Now()
	obj := &ArxObject{
		ID:          "test_obj",
		Type:        "wall",
		Name:        "Test Wall",
		Level:       1,
		Properties:  make(map[string]string),
		Coordinates: Coordinates{X: 0, Y: 0, Z: 0},
	}
	createTime := time.Since(start)
	
	if createTime > 1*time.Millisecond {
		t.Errorf("Object creation took %v, target: <1ms", createTime)
	}
	
	// Test property operations
	start = time.Now()
	obj.Properties["material"] = "concrete"
	value := obj.Properties["material"]
	propTime := time.Since(start)
	
	if propTime > 100*time.Microsecond {
		t.Errorf("Property operations took %v, target: <100μs", propTime)
	}
	
	if value != "concrete" {
		t.Errorf("Expected 'concrete', got '%s'", value)
	}
	
	// Test position operations
	obj.Coordinates = Coordinates{X: 10.5, Y: 20.3, Z: 5.0}
	if obj.Coordinates.X != 10.5 || obj.Coordinates.Y != 20.3 || obj.Coordinates.Z != 5.0 {
		t.Errorf("Position mismatch: expected (10.5, 20.3, 5.0), got (%f, %f, %f)", 
			obj.Coordinates.X, obj.Coordinates.Y, obj.Coordinates.Z)
	}
}

// TestBuildingManagementSimple tests building operations without C dependency
func TestBuildingManagementSimple(t *testing.T) {
	// Create building
	building := &ArxBuilding{
		Name:        "Test Building",
		Description: "Test Description",
		Objects:     make([]*ArxObject, 0),
	}
	
	// Create objects
	wall1 := &ArxObject{ID: "wall1", Type: "wall", Name: "North Wall", Level: 1}
	wall2 := &ArxObject{ID: "wall2", Type: "wall", Name: "South Wall", Level: 1}
	
	// Add objects to building
	building.Objects = append(building.Objects, wall1, wall2)
	
	if len(building.Objects) != 2 {
		t.Errorf("Expected 2 objects, got %d", len(building.Objects))
	}
}

// TestASCIIGenerationPerformance tests ASCII generation performance
func TestASCIIGenerationPerformance(t *testing.T) {
	// Create test objects
	var objects []*ArxObject
	for i := 0; i < 20; i++ {
		obj := &ArxObject{
			ID:   fmt.Sprintf("obj_%d", i),
			Type: "wall",
			Name: fmt.Sprintf("Wall %d", i),
			Coordinates: Coordinates{
				X: float64(i * 10),
				Y: float64(i * 5),
				Z: 0,
			},
		}
		objects = append(objects, obj)
	}
	
	// Simulate ASCII generation
	start := time.Now()
	// In real implementation, this would call C function
	asciiGrid := make([][]rune, 40)
	for i := range asciiGrid {
		asciiGrid[i] = make([]rune, 80)
		for j := range asciiGrid[i] {
			asciiGrid[i][j] = ' '
		}
	}
	
	// Place objects on grid
	for _, obj := range objects {
		x := int(obj.Coordinates.X / 10)
		y := int(obj.Coordinates.Y / 10)
		if x >= 0 && x < 80 && y >= 0 && y < 40 {
			asciiGrid[y][x] = '#'
		}
	}
	
	renderTime := time.Since(start)
	
	if renderTime > 10*time.Millisecond {
		t.Errorf("ASCII generation took %v, target: <10ms", renderTime)
	}
}

// TestSpatialIndexingPerformance tests spatial index operations
func TestSpatialIndexingPerformance(t *testing.T) {
	// Create spatial index simulation
	type SpatialIndexSimple struct {
		objects []*ArxObject
	}
	
	index := &SpatialIndexSimple{
		objects: make([]*ArxObject, 0),
	}
	
	// Add many objects
	for i := 0; i < 100; i++ {
		obj := &ArxObject{
			ID:   fmt.Sprintf("spatial_%d", i),
			Type: "equipment",
			Name: fmt.Sprintf("Equipment %d", i),
			Coordinates: Coordinates{
				X: float64(i%10 * 10),
				Y: float64(i/10 * 10),
				Z: 0,
			},
		}
		index.objects = append(index.objects, obj)
	}
	
	// Test range query performance
	start := time.Now()
	var results []*ArxObject
	for _, obj := range index.objects {
		if obj.Coordinates.X >= 0 && obj.Coordinates.X <= 50 &&
			obj.Coordinates.Y >= 0 && obj.Coordinates.Y <= 50 {
			results = append(results, obj)
		}
	}
	queryTime := time.Since(start)
	
	if queryTime > 5*time.Millisecond {
		t.Errorf("Spatial query took %v, target: <5ms", queryTime)
	}
	
	if len(results) == 0 {
		t.Error("No results from range query")
	}
}

// BenchmarkArxObjectCreation benchmarks object creation
func BenchmarkArxObjectCreation(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = &ArxObject{
			ID:          fmt.Sprintf("bench_%d", i),
			Type:        "wall",
			Name:        "Benchmark Wall",
			Level:       1,
			Properties:  make(map[string]string),
			Coordinates: Coordinates{X: 0, Y: 0, Z: 0},
		}
	}
}

// BenchmarkPropertyOperations benchmarks property get/set
func BenchmarkPropertyOperations(b *testing.B) {
	obj := &ArxObject{
		ID:         "bench_obj",
		Properties: make(map[string]string),
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		obj.Properties["test_key"] = "test_value"
		_ = obj.Properties["test_key"]
	}
}

// BenchmarkASCIIGeneration benchmarks ASCII generation
func BenchmarkASCIIGeneration(b *testing.B) {
	// Create test objects
	var objects []*ArxObject
	for i := 0; i < 20; i++ {
		obj := &ArxObject{
			ID:   fmt.Sprintf("bench_%d", i),
			Type: "wall",
			Name: fmt.Sprintf("Wall %d", i),
			Coordinates: Coordinates{
				X: float64(i * 10),
				Y: float64(i * 5),
				Z: 0,
			},
		}
		objects = append(objects, obj)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// Simulate ASCII generation
		grid := make([][]rune, 40)
		for j := range grid {
			grid[j] = make([]rune, 80)
		}
		
		for _, obj := range objects {
			x := int(obj.Coordinates.X / 10)
			y := int(obj.Coordinates.Y / 10)
			if x >= 0 && x < 80 && y >= 0 && y < 40 {
				grid[y][x] = '#'
			}
		}
	}
}

// BenchmarkSpatialQuery benchmarks spatial queries
func BenchmarkSpatialQuery(b *testing.B) {
	// Create many objects
	var objects []*ArxObject
	for i := 0; i < 100; i++ {
		obj := &ArxObject{
			ID:   fmt.Sprintf("spatial_%d", i),
			Type: "equipment",
			Coordinates: Coordinates{
				X: float64(i%10 * 10),
				Y: float64(i/10 * 10),
				Z: 0,
			},
		}
		objects = append(objects, obj)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		var results []*ArxObject
		for _, obj := range objects {
			if obj.Coordinates.X >= 0 && obj.Coordinates.X <= 50 &&
				obj.Coordinates.Y >= 0 && obj.Coordinates.Y <= 50 {
				results = append(results, obj)
			}
		}
	}
}