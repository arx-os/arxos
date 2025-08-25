package cache

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"testing"
	"time"

	"github.com/arxos/arxos/core/internal/db"
)

// BenchmarkCacheSet measures SET operation performance
func BenchmarkCacheSet(b *testing.B) {
	// Initialize test database
	if err := db.InitTestDB(); err != nil {
		b.Fatalf("Failed to initialize test database: %v", err)
	}
	defer db.Close()

	cache, err := NewCacheService(nil, nil)
	if err != nil {
		b.Fatalf("Failed to create cache service: %v", err)
	}
	defer cache.Close()

	// Prepare test data
	testData := make([]string, 1000)
	for i := range testData {
		testData[i] = fmt.Sprintf("test_value_%d_%s", i, generateRandomString(100))
	}

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		i := 0
		for pb.Next() {
			key := fmt.Sprintf("bench_set_%d_%d", b.N, i)
			value := testData[i%len(testData)]
			if err := cache.Set(key, value, 5*time.Minute); err != nil {
				b.Errorf("Set failed: %v", err)
			}
			i++
		}
	})

	b.StopTimer()
	
	// Cleanup
	cache.InvalidatePattern("bench_set_*")
}

// BenchmarkCacheGet measures GET operation performance
func BenchmarkCacheGet(b *testing.B) {
	// Initialize test database
	if err := db.InitTestDB(); err != nil {
		b.Fatalf("Failed to initialize test database: %v", err)
	}
	defer db.Close()

	cache, err := NewCacheService(nil, nil)
	if err != nil {
		b.Fatalf("Failed to create cache service: %v", err)
	}
	defer cache.Close()

	// Populate cache with test data
	numKeys := 1000
	keys := make([]string, numKeys)
	for i := 0; i < numKeys; i++ {
		keys[i] = fmt.Sprintf("bench_get_%d", i)
		value := fmt.Sprintf("value_%d", i)
		if err := cache.Set(keys[i], value, 5*time.Minute); err != nil {
			b.Fatalf("Failed to set test data: %v", err)
		}
	}

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		i := 0
		for pb.Next() {
			key := keys[i%numKeys]
			if _, err := cache.Get(key); err != nil {
				b.Errorf("Get failed: %v", err)
			}
			i++
		}
	})

	b.StopTimer()
	
	// Cleanup
	cache.InvalidatePattern("bench_get_*")
}

// BenchmarkCacheSetGet measures mixed SET/GET operations
func BenchmarkCacheSetGet(b *testing.B) {
	// Initialize test database
	if err := db.InitTestDB(); err != nil {
		b.Fatalf("Failed to initialize test database: %v", err)
	}
	defer db.Close()

	cache, err := NewCacheService(nil, nil)
	if err != nil {
		b.Fatalf("Failed to create cache service: %v", err)
	}
	defer cache.Close()

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		i := 0
		for pb.Next() {
			key := fmt.Sprintf("bench_mixed_%d", i%1000)
			
			// 80% reads, 20% writes (typical cache pattern)
			if rand.Float32() < 0.8 {
				cache.Get(key)
			} else {
				value := fmt.Sprintf("value_%d_%d", b.N, i)
				cache.Set(key, value, 5*time.Minute)
			}
			i++
		}
	})

	b.StopTimer()
	
	// Cleanup
	cache.InvalidatePattern("bench_mixed_*")
}

// BenchmarkCacheIncr measures counter increment performance
func BenchmarkCacheIncr(b *testing.B) {
	// Initialize test database
	if err := db.InitTestDB(); err != nil {
		b.Fatalf("Failed to initialize test database: %v", err)
	}
	defer db.Close()

	cache, err := NewCacheService(nil, nil)
	if err != nil {
		b.Fatalf("Failed to create cache service: %v", err)
	}
	defer cache.Close()

	// Use multiple counters to reduce contention
	numCounters := 10
	counters := make([]string, numCounters)
	for i := 0; i < numCounters; i++ {
		counters[i] = fmt.Sprintf("bench_counter_%d", i)
	}

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		i := 0
		for pb.Next() {
			counter := counters[i%numCounters]
			if _, err := cache.Incr(counter); err != nil {
				b.Errorf("Incr failed: %v", err)
			}
			i++
		}
	})

	b.StopTimer()
	
	// Cleanup
	cache.InvalidatePattern("bench_counter_*")
}

// BenchmarkCacheHash measures hash operations performance
func BenchmarkCacheHash(b *testing.B) {
	// Initialize test database
	if err := db.InitTestDB(); err != nil {
		b.Fatalf("Failed to initialize test database: %v", err)
	}
	defer db.Close()

	cache, err := NewCacheService(nil, nil)
	if err != nil {
		b.Fatalf("Failed to create cache service: %v", err)
	}
	defer cache.Close()

	// Create test hash
	hashKey := "bench_hash"
	fields := make([]string, 100)
	for i := range fields {
		fields[i] = fmt.Sprintf("field_%d", i)
	}

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		i := 0
		for pb.Next() {
			field := fields[i%len(fields)]
			
			// Mix of hash operations
			switch i % 3 {
			case 0:
				cache.HSet(hashKey, field, fmt.Sprintf("value_%d", i))
			case 1:
				cache.HGet(hashKey, field)
			case 2:
				if i%10 == 0 { // Less frequent to avoid overhead
					cache.HGetAll(hashKey)
				}
			}
			i++
		}
	})

	b.StopTimer()
	
	// Cleanup
	cache.Delete(hashKey)
}

// BenchmarkCachePattern measures pattern invalidation performance
func BenchmarkCachePattern(b *testing.B) {
	// Initialize test database
	if err := db.InitTestDB(); err != nil {
		b.Fatalf("Failed to initialize test database: %v", err)
	}
	defer db.Close()

	cache, err := NewCacheService(nil, nil)
	if err != nil {
		b.Fatalf("Failed to create cache service: %v", err)
	}
	defer cache.Close()

	// Populate cache with hierarchical keys
	for i := 0; i < 100; i++ {
		for j := 0; j < 10; j++ {
			key := fmt.Sprintf("bench_pattern:user:%d:session:%d", i, j)
			value := fmt.Sprintf("value_%d_%d", i, j)
			if err := cache.Set(key, value, 5*time.Minute); err != nil {
				b.Fatalf("Failed to set test data: %v", err)
			}
		}
	}

	patterns := []string{
		"bench_pattern:user:1:*",
		"bench_pattern:user:*:session:1",
		"bench_pattern:*",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		pattern := patterns[i%len(patterns)]
		if err := cache.InvalidatePattern(pattern); err != nil {
			b.Errorf("Pattern invalidation failed: %v", err)
		}
		
		// Re-populate for next iteration
		if i%10 == 0 {
			for j := 0; j < 10; j++ {
				key := fmt.Sprintf("bench_pattern:user:%d:session:%d", i, j)
				cache.Set(key, fmt.Sprintf("value_%d", j), 5*time.Minute)
			}
		}
	}

	b.StopTimer()
	
	// Cleanup
	cache.InvalidatePattern("bench_pattern:*")
}

// BenchmarkCacheConcurrency measures performance under high concurrency
func BenchmarkCacheConcurrency(b *testing.B) {
	// Initialize test database
	if err := db.InitTestDB(); err != nil {
		b.Fatalf("Failed to initialize test database: %v", err)
	}
	defer db.Close()

	cache, err := NewCacheService(nil, nil)
	if err != nil {
		b.Fatalf("Failed to create cache service: %v", err)
	}
	defer cache.Close()

	// Simulate realistic workload with multiple goroutines
	numWorkers := 100
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	b.ResetTimer()
	
	var wg sync.WaitGroup
	wg.Add(numWorkers)
	
	for w := 0; w < numWorkers; w++ {
		go func(workerID int) {
			defer wg.Done()
			
			for i := 0; i < b.N/numWorkers; i++ {
				select {
				case <-ctx.Done():
					return
				default:
					// Simulate mixed operations
					key := fmt.Sprintf("bench_concurrent:%d:%d", workerID, i%100)
					
					switch rand.Intn(5) {
					case 0: // SET
						cache.Set(key, fmt.Sprintf("value_%d", i), 5*time.Minute)
					case 1, 2, 3: // GET (more frequent)
						cache.Get(key)
					case 4: // DELETE
						cache.Delete(key)
					}
				}
			}
		}(w)
	}
	
	wg.Wait()
	b.StopTimer()
	
	// Cleanup
	cache.InvalidatePattern("bench_concurrent:*")
}

// TestCachePerformanceMetrics runs comprehensive performance tests
func TestCachePerformanceMetrics(t *testing.T) {
	// Initialize test database
	if err := db.InitTestDB(); err != nil {
		t.Fatalf("Failed to initialize test database: %v", err)
	}
	defer db.Close()

	cache, err := NewCacheService(nil, nil)
	if err != nil {
		t.Fatalf("Failed to create cache service: %v", err)
	}
	defer cache.Close()

	// Performance targets
	targets := struct {
		SetLatency   time.Duration
		GetLatency   time.Duration
		OpsPerSecond int
		HitRate      float64
	}{
		SetLatency:   5 * time.Millisecond,
		GetLatency:   2 * time.Millisecond,
		OpsPerSecond: 1000,
		HitRate:      0.75,
	}

	// Test SET performance
	t.Run("SET_Performance", func(t *testing.T) {
		iterations := 1000
		start := time.Now()
		
		for i := 0; i < iterations; i++ {
			key := fmt.Sprintf("perf_test_set_%d", i)
			value := fmt.Sprintf("value_%d", i)
			if err := cache.Set(key, value, 5*time.Minute); err != nil {
				t.Errorf("Set failed: %v", err)
			}
		}
		
		duration := time.Since(start)
		avgLatency := duration / time.Duration(iterations)
		
		if avgLatency > targets.SetLatency {
			t.Errorf("SET latency too high: %v (target: %v)", avgLatency, targets.SetLatency)
		}
		
		t.Logf("SET performance: %d ops in %v (avg: %v)", iterations, duration, avgLatency)
		
		// Cleanup
		cache.InvalidatePattern("perf_test_set_*")
	})

	// Test GET performance
	t.Run("GET_Performance", func(t *testing.T) {
		// Pre-populate cache
		for i := 0; i < 1000; i++ {
			key := fmt.Sprintf("perf_test_get_%d", i)
			cache.Set(key, fmt.Sprintf("value_%d", i), 5*time.Minute)
		}
		
		iterations := 10000
		hits := 0
		start := time.Now()
		
		for i := 0; i < iterations; i++ {
			key := fmt.Sprintf("perf_test_get_%d", i%1000)
			if value, err := cache.Get(key); err == nil && value != "" {
				hits++
			}
		}
		
		duration := time.Since(start)
		avgLatency := duration / time.Duration(iterations)
		hitRate := float64(hits) / float64(iterations)
		
		if avgLatency > targets.GetLatency {
			t.Errorf("GET latency too high: %v (target: %v)", avgLatency, targets.GetLatency)
		}
		
		if hitRate < targets.HitRate {
			t.Errorf("Hit rate too low: %.2f (target: %.2f)", hitRate, targets.HitRate)
		}
		
		t.Logf("GET performance: %d ops in %v (avg: %v, hit rate: %.2f%%)", 
			iterations, duration, avgLatency, hitRate*100)
		
		// Cleanup
		cache.InvalidatePattern("perf_test_get_*")
	})

	// Test throughput
	t.Run("Throughput", func(t *testing.T) {
		duration := 1 * time.Second
		ops := 0
		
		ctx, cancel := context.WithTimeout(context.Background(), duration)
		defer cancel()
		
		start := time.Now()
		for {
			select {
			case <-ctx.Done():
				goto done
			default:
				key := fmt.Sprintf("perf_test_throughput_%d", ops)
				cache.Set(key, "value", 5*time.Minute)
				ops++
			}
		}
		
	done:
		elapsed := time.Since(start)
		opsPerSec := float64(ops) / elapsed.Seconds()
		
		if opsPerSec < float64(targets.OpsPerSecond) {
			t.Errorf("Throughput too low: %.0f ops/sec (target: %d)", opsPerSec, targets.OpsPerSecond)
		}
		
		t.Logf("Throughput: %.0f ops/sec", opsPerSec)
		
		// Cleanup
		cache.InvalidatePattern("perf_test_throughput_*")
	})

	// Get final statistics
	if stats, err := cache.GetStats(); err == nil {
		t.Logf("Final cache statistics: Keys=%d, Hits=%d, Misses=%d, HitRate=%.2f%%",
			stats.TotalKeys, stats.Hits, stats.Misses, stats.HitRate*100)
	}
}

// generateRandomString generates a random string of specified length
func generateRandomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[rand.Intn(len(charset))]
	}
	return string(b)
}