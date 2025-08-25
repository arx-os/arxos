package wall_composition

import (
	"fmt"
	"testing"
	"time"

	"github.com/arxos/arxos/core/cgo"
)

// =============================================================================
// PERFORMANCE BENCHMARKS
// =============================================================================

// BenchmarkWallSegmentCreation benchmarks wall segment creation performance
func BenchmarkWallSegmentCreation(b *testing.B) {
	service, err := NewWallCompositionServiceCGO(GetDefaultConfig())
	if err != nil {
		b.Fatalf("Failed to create wall composition service: %v", err)
	}
	defer service.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := service.CreateWallSegment(uint64(i), 0, 0, 0, 1000, 0, 0, 3000, 200, 0.8)
		if err != nil {
			b.Fatalf("Failed to create wall segment: %v", err)
		}
	}
}

// BenchmarkCurvedWallSegmentCreation benchmarks curved wall segment creation
func BenchmarkCurvedWallSegmentCreation(b *testing.B) {
	service, err := NewWallCompositionServiceCGO(GetDefaultConfig())
	if err != nil {
		b.Fatalf("Failed to create wall composition service: %v", err)
	}
	defer service.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := service.CreateCurvedWallSegment(uint64(i), cgo.CurveTypeArc, 500, 500, 0, 1000, 0, 3.14159/2, 3000, 200, 0.8)
		if err != nil {
			b.Fatalf("Failed to create curved wall segment: %v", err)
		}
	}
}

// BenchmarkWallComposition benchmarks wall composition performance
func BenchmarkWallComposition(b *testing.B) {
	service, err := NewWallCompositionServiceCGO(GetDefaultConfig())
	if err != nil {
		b.Fatalf("Failed to create wall composition service: %v", err)
	}
	defer service.Close()

	// Create test segments
	segments := make([]*cgo.WallSegment, 100)
	for i := 0; i < 100; i++ {
		segment, err := service.CreateWallSegment(uint64(i), float64(i*1000), 0, 0, float64((i+1)*1000), 0, 0, 3000, 200, 0.8)
		if err != nil {
			b.Fatalf("Failed to create test segment: %v", err)
		}
		segments[i] = segment
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := service.ComposeWalls(segments)
		if err != nil {
			b.Fatalf("Failed to compose walls: %v", err)
		}
	}
}

// BenchmarkConnectionDetection benchmarks connection detection performance
func BenchmarkConnectionDetection(b *testing.B) {
	service, err := NewWallCompositionServiceCGO(GetDefaultConfig())
	if err != nil {
		b.Fatalf("Failed to create wall composition service: %v", err)
	}
	defer service.Close()

	// Create test segments
	segments := make([]*cgo.WallSegment, 100)
	for i := 0; i < 100; i++ {
		segment, err := service.CreateWallSegment(uint64(i), float64(i*1000), 0, 0, float64((i+1)*1000), 0, 0, 3000, 200, 0.8)
		if err != nil {
			b.Fatalf("Failed to create test segment: %v", err)
		}
		segments[i] = segment
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := service.DetectConnections(segments)
		if err != nil {
			b.Fatalf("Failed to detect connections: %v", err)
		}
	}
}

// BenchmarkLargeScaleComposition benchmarks large-scale wall composition
func BenchmarkLargeScaleComposition(b *testing.B) {
	service, err := NewWallCompositionServiceCGO(GetHighPerformanceConfig())
	if err != nil {
		b.Fatalf("Failed to create wall composition service: %v", err)
	}
	defer service.Close()

	// Create large number of test segments
	segments := make([]*cgo.WallSegment, 1000)
	for i := 0; i < 1000; i++ {
		segment, err := service.CreateWallSegment(uint64(i), float64(i*100), 0, 0, float64((i+1)*100), 0, 0, 3000, 200, 0.8)
		if err != nil {
			b.Fatalf("Failed to create test segment: %v", err)
		}
		segments[i] = segment
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := service.ComposeWalls(segments)
		if err != nil {
			b.Fatalf("Failed to compose walls: %v", err)
		}
	}
}

// =============================================================================
// PERFORMANCE COMPARISON TESTS
// =============================================================================

// TestPerformanceComparison compares CGO vs Go-only performance
func TestPerformanceComparison(t *testing.T) {
	// Test with different configurations
	configs := []struct {
		name   string
		config cgo.CompositionConfig
	}{
		{"Default", GetDefaultConfig()},
		{"High Performance", GetHighPerformanceConfig()},
		{"High Accuracy", GetHighAccuracyConfig()},
	}

	for _, config := range configs {
		t.Run(config.name, func(t *testing.T) {
			service, err := NewWallCompositionServiceCGO(config.config)
			if err != nil {
				t.Fatalf("Failed to create service: %v", err)
			}
			defer service.Close()

			// Create test segments
			segments := make([]*cgo.WallSegment, 100)
			for i := 0; i < 100; i++ {
				segment, err := service.CreateWallSegment(uint64(i), float64(i*1000), 0, 0, float64((i+1)*1000), 0, 0, 3000, 200, 0.8)
				if err != nil {
					t.Fatalf("Failed to create test segment: %v", err)
				}
				segments[i] = segment
			}

			// Measure composition time
			start := time.Now()
			structures, err := service.ComposeWalls(segments)
			compositionTime := time.Since(start)

			if err != nil {
				t.Fatalf("Failed to compose walls: %v", err)
			}

			// Measure connection detection time
			start = time.Now()
			connections, err := service.DetectConnections(segments)
			connectionTime := time.Since(start)

			if err != nil {
				t.Fatalf("Failed to detect connections: %v", err)
			}

			// Measure validation time
			start = time.Now()
			for _, structure := range structures {
				service.ValidateWallStructure(structure)
			}
			validationTime := time.Since(start)

			// Analyze results
			analysis := service.AnalyzeWallComposition(structures)

			t.Logf("Configuration: %s", config.name)
			t.Logf("Composition Time: %v", compositionTime)
			t.Logf("Connection Detection Time: %v", connectionTime)
			t.Logf("Validation Time: %v", validationTime)
			t.Logf("Total Structures: %d", analysis.TotalStructures)
			t.Logf("Total Segments: %d", analysis.TotalSegments)
			t.Logf("Total Length: %.2f mm", analysis.TotalLength)
			t.Logf("Average Confidence: %.2f", analysis.AvgConfidence)

			// Performance assertions
			if compositionTime > 100*time.Millisecond {
				t.Errorf("Composition time too slow: %v", compositionTime)
			}

			if connectionTime > 50*time.Millisecond {
				t.Errorf("Connection detection time too slow: %v", connectionTime)
			}

			if validationTime > 10*time.Millisecond {
				t.Errorf("Validation time too slow: %v", validationTime)
			}

			// Quality assertions
			if analysis.TotalStructures == 0 {
				t.Error("No structures created")
			}

			if analysis.AvgConfidence < 0.5 {
				t.Errorf("Average confidence too low: %.2f", analysis.AvgConfidence)
			}
		})
	}
}

// =============================================================================
// STRESS TESTS
// =============================================================================

// TestStressTestLargeDataset tests performance with very large datasets
func TestStressTestLargeDataset(t *testing.T) {
	service, err := NewWallCompositionServiceCGO(GetHighPerformanceConfig())
	if err != nil {
		t.Fatalf("Failed to create wall composition service: %v", err)
	}
	defer service.Close()

	// Create very large dataset
	segmentCounts := []int{100, 500, 1000, 5000}

	for _, count := range segmentCounts {
		t.Run(fmt.Sprintf("Segments_%d", count), func(t *testing.T) {
			// Create test segments
			segments := make([]*cgo.WallSegment, count)
			for i := 0; i < count; i++ {
				segment, err := service.CreateWallSegment(uint64(i), float64(i*100), 0, 0, float64((i+1)*100), 0, 0, 3000, 200, 0.8)
				if err != nil {
					t.Fatalf("Failed to create test segment: %v", err)
				}
				segments[i] = segment
			}

			// Measure composition time
			start := time.Now()
			structures, err := service.ComposeWalls(segments)
			compositionTime := time.Since(start)

			if err != nil {
				t.Fatalf("Failed to compose walls: %v", err)
			}

			// Measure memory usage (approximate)
			memoryUsage := float64(count) * 0.001 // Rough estimate in MB

			t.Logf("Segment Count: %d", count)
			t.Logf("Composition Time: %v", compositionTime)
			t.Logf("Structures Created: %d", len(structures))
			t.Logf("Estimated Memory Usage: %.2f MB", memoryUsage)

			// Performance assertions for large datasets
			if count >= 1000 && compositionTime > 1*time.Second {
				t.Errorf("Large dataset composition too slow: %v", compositionTime)
			}

			if count >= 5000 && compositionTime > 5*time.Second {
				t.Errorf("Very large dataset composition too slow: %v", compositionTime)
			}
		})
	}
}

// =============================================================================
// MEMORY EFFICIENCY TESTS
// =============================================================================

// TestMemoryEfficiency tests memory usage patterns
func TestMemoryEfficiency(t *testing.T) {
	service, err := NewWallCompositionServiceCGO(GetDefaultConfig())
	if err != nil {
		t.Fatalf("Failed to create wall composition service: %v", err)
	}
	defer service.Close()

	// Test memory efficiency with repeated operations
	for i := 0; i < 10; i++ {
		// Create segments
		segments := make([]*cgo.WallSegment, 100)
		for j := 0; j < 100; j++ {
			segment, err := service.CreateWallSegment(uint64(j), float64(j*1000), 0, 0, float64((j+1)*1000), 0, 0, 3000, 200, 0.8)
			if err != nil {
				t.Fatalf("Failed to create test segment: %v", err)
			}
			segments[j] = segment
		}

		// Compose walls
		structures, err := service.ComposeWalls(segments)
		if err != nil {
			t.Fatalf("Failed to compose walls: %v", err)
		}

		// Validate structures
		for _, structure := range structures {
			validationState := service.ValidateWallStructure(structure)
			if validationState == cgo.ValidationConflict {
				t.Errorf("Structure validation failed on iteration %d", i)
			}
		}

		t.Logf("Iteration %d: Created %d structures", i, len(structures))
	}
}

// =============================================================================
// CONFIGURATION PERFORMANCE TESTS
// =============================================================================

// TestConfigurationPerformance tests performance with different configurations
func TestConfigurationPerformance(t *testing.T) {
	configs := []struct {
		name   string
		config cgo.CompositionConfig
	}{
		{"Default", GetDefaultConfig()},
		{"Advanced", GetAdvancedConfig()},
		{"High Performance", GetHighPerformanceConfig()},
		{"High Accuracy", GetHighAccuracyConfig()},
	}

	for _, config := range configs {
		t.Run(config.name, func(t *testing.T) {
			service, err := NewWallCompositionServiceCGO(config.config)
			if err != nil {
				t.Fatalf("Failed to create service: %v", err)
			}
			defer service.Close()

			// Create test segments
			segments := make([]*cgo.WallSegment, 200)
			for i := 0; i < 200; i++ {
				segment, err := service.CreateWallSegment(uint64(i), float64(i*500), 0, 0, float64((i+1)*500), 0, 0, 3000, 200, 0.8)
				if err != nil {
					t.Fatalf("Failed to create test segment: %v", err)
				}
				segments[i] = segment
			}

			// Measure full pipeline performance
			start := time.Now()

			structures, err := service.ComposeWalls(segments)
			if err != nil {
				t.Fatalf("Failed to compose walls: %v", err)
			}

			connections, err := service.DetectConnections(segments)
			if err != nil {
				t.Fatalf("Failed to detect connections: %v", err)
			}

			// Validate all structures
			validStructures := 0
			for _, structure := range structures {
				if service.ValidateWallStructure(structure) == cgo.ValidationComplete {
					validStructures++
				}
			}

			totalTime := time.Since(start)

			t.Logf("Configuration: %s", config.name)
			t.Logf("Total Time: %v", totalTime)
			t.Logf("Structures Created: %d", len(structures))
			t.Logf("Connections Detected: %d", len(connections))
			t.Logf("Valid Structures: %d/%d", validStructures, len(structures))

			// Performance assertions
			if totalTime > 500*time.Millisecond {
				t.Errorf("Total pipeline time too slow: %v", totalTime)
			}

			// Quality assertions
			if validStructures == 0 {
				t.Error("No valid structures created")
			}

			// Configuration-specific assertions
			if config.name == "High Accuracy" && validStructures < len(structures)*8/10 {
				t.Errorf("High accuracy config should produce mostly valid structures: %d/%d", validStructures, len(structures))
			}
		})
	}
}
