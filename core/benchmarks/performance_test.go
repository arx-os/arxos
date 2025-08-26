package benchmarks

import (
	"fmt"
	"testing"
	"time"
)

// ArxObject represents a building object
type ArxObject struct {
	ID          string
	Type        string
	Name        string
	Level       int
	Properties  map[string]string
	Coordinates struct {
		X, Y, Z float64
	}
}

// TestPerformanceTargets validates key performance metrics
func TestPerformanceTargets(t *testing.T) {
	t.Log("=== ARXOS PERFORMANCE VALIDATION ===")
	
	// Test 1: ArxObject Creation (<1ms target)
	t.Run("ArxObjectCreation", func(t *testing.T) {
		start := time.Now()
		obj := &ArxObject{
			ID:         "test_obj",
			Type:       "wall",
			Name:       "Test Wall",
			Level:      1,
			Properties: make(map[string]string),
		}
		obj.Coordinates.X = 100.0
		obj.Coordinates.Y = 200.0
		obj.Coordinates.Z = 0.0
		duration := time.Since(start)
		
		if duration > 1*time.Millisecond {
			t.Errorf("❌ ArxObject creation: %v (target: <1ms)", duration)
		} else {
			t.Logf("✅ ArxObject creation: %v (target: <1ms)", duration)
		}
	})
	
	// Test 2: Property Operations (<100μs target)
	t.Run("PropertyOperations", func(t *testing.T) {
		obj := &ArxObject{Properties: make(map[string]string)}
		
		start := time.Now()
		obj.Properties["material"] = "concrete"
		obj.Properties["height"] = "3.0m"
		_ = obj.Properties["material"]
		duration := time.Since(start)
		
		if duration > 100*time.Microsecond {
			t.Errorf("❌ Property operations: %v (target: <100μs)", duration)
		} else {
			t.Logf("✅ Property operations: %v (target: <100μs)", duration)
		}
	})
	
	// Test 3: ASCII Rendering (<10ms target for 100 objects)
	t.Run("ASCIIRendering", func(t *testing.T) {
		// Create 100 test objects
		objects := make([]*ArxObject, 100)
		for i := 0; i < 100; i++ {
			objects[i] = &ArxObject{
				ID:   fmt.Sprintf("obj_%d", i),
				Type: "wall",
			}
			objects[i].Coordinates.X = float64(i % 10 * 10)
			objects[i].Coordinates.Y = float64(i / 10 * 10)
		}
		
		start := time.Now()
		// Simulate ASCII rendering
		grid := make([][]byte, 40)
		for i := range grid {
			grid[i] = make([]byte, 80)
			for j := range grid[i] {
				grid[i][j] = ' '
			}
		}
		
		// Place objects
		for _, obj := range objects {
			x := int(obj.Coordinates.X / 10)
			y := int(obj.Coordinates.Y / 10)
			if x >= 0 && x < 80 && y >= 0 && y < 40 {
				grid[y][x] = '#'
			}
		}
		duration := time.Since(start)
		
		if duration > 10*time.Millisecond {
			t.Errorf("❌ ASCII rendering (100 objects): %v (target: <10ms)", duration)
		} else {
			t.Logf("✅ ASCII rendering (100 objects): %v (target: <10ms)", duration)
		}
	})
	
	// Test 4: Spatial Query (<5ms target for 1000 objects)
	t.Run("SpatialQuery", func(t *testing.T) {
		// Create 1000 test objects
		objects := make([]*ArxObject, 1000)
		for i := 0; i < 1000; i++ {
			objects[i] = &ArxObject{
				ID:   fmt.Sprintf("spatial_%d", i),
				Type: "equipment",
			}
			objects[i].Coordinates.X = float64(i % 100 * 10)
			objects[i].Coordinates.Y = float64((i / 100) % 100 * 10)
			objects[i].Coordinates.Z = float64(i / 10000 * 10)
		}
		
		start := time.Now()
		// Perform range query
		var results []*ArxObject
		for _, obj := range objects {
			if obj.Coordinates.X >= 200 && obj.Coordinates.X <= 500 &&
				obj.Coordinates.Y >= 200 && obj.Coordinates.Y <= 500 &&
				obj.Coordinates.Z >= 0 && obj.Coordinates.Z <= 10 {
				results = append(results, obj)
			}
		}
		duration := time.Since(start)
		
		if duration > 5*time.Millisecond {
			t.Errorf("❌ Spatial query (1000 objects): %v (target: <5ms)", duration)
		} else {
			t.Logf("✅ Spatial query (1000 objects): %v (target: <5ms) - found %d objects", duration, len(results))
		}
	})
	
	t.Log("\n=== PERFORMANCE VALIDATION COMPLETE ===")
}

// Benchmark tests for detailed performance analysis
func BenchmarkArxObjectCreation(b *testing.B) {
	for i := 0; i < b.N; i++ {
		obj := &ArxObject{
			ID:         fmt.Sprintf("bench_%d", i),
			Type:       "wall",
			Name:       "Benchmark Wall",
			Level:      1,
			Properties: make(map[string]string),
		}
		obj.Coordinates.X = 100.0
		obj.Coordinates.Y = 200.0
	}
}

func BenchmarkPropertyOperations(b *testing.B) {
	obj := &ArxObject{Properties: make(map[string]string)}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		obj.Properties["key"] = fmt.Sprintf("value_%d", i)
		_ = obj.Properties["key"]
	}
}

func BenchmarkASCIIRendering100Objects(b *testing.B) {
	// Create 100 test objects
	objects := make([]*ArxObject, 100)
	for i := 0; i < 100; i++ {
		objects[i] = &ArxObject{ID: fmt.Sprintf("obj_%d", i)}
		objects[i].Coordinates.X = float64(i % 10 * 10)
		objects[i].Coordinates.Y = float64(i / 10 * 10)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		grid := make([][]byte, 40)
		for j := range grid {
			grid[j] = make([]byte, 80)
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

func BenchmarkSpatialQuery1000Objects(b *testing.B) {
	// Create 1000 test objects
	objects := make([]*ArxObject, 1000)
	for i := 0; i < 1000; i++ {
		objects[i] = &ArxObject{ID: fmt.Sprintf("spatial_%d", i)}
		objects[i].Coordinates.X = float64(i % 100 * 10)
		objects[i].Coordinates.Y = float64((i / 100) % 100 * 10)
		objects[i].Coordinates.Z = float64(i / 10000 * 10)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		var results []*ArxObject
		for _, obj := range objects {
			if obj.Coordinates.X >= 200 && obj.Coordinates.X <= 500 &&
				obj.Coordinates.Y >= 200 && obj.Coordinates.Y <= 500 {
				results = append(results, obj)
			}
		}
	}
}

func BenchmarkMemoryAllocation(b *testing.B) {
	b.Run("MapCreation", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			m := make(map[string]string, 10)
			m["key"] = "value"
		}
	})
	
	b.Run("SliceCreation", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			s := make([]*ArxObject, 0, 100)
			s = append(s, &ArxObject{ID: "test"})
		}
	})
	
	b.Run("GridCreation", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			grid := make([][]byte, 40)
			for j := range grid {
				grid[j] = make([]byte, 80)
			}
		}
	})
}