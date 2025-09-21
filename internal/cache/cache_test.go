package cache

import (
	"runtime"
	"sync"
	"testing"
	"time"
)

func TestMemoryCacheBasicOperations(t *testing.T) {
	cache := NewMemoryCache()
	defer cache.Close()

	// Test Set and Get
	cache.Set("key1", "value1", 1*time.Hour)
	val, exists := cache.Get("key1")
	if !exists {
		t.Error("Expected key1 to exist")
	}
	if val != "value1" {
		t.Errorf("Expected value1, got %v", val)
	}

	// Test non-existent key
	_, exists = cache.Get("nonexistent")
	if exists {
		t.Error("Expected nonexistent key to not exist")
	}

	// Test Delete
	cache.Delete("key1")
	_, exists = cache.Get("key1")
	if exists {
		t.Error("Expected key1 to be deleted")
	}

	// Test Clear
	cache.Set("key2", "value2", 1*time.Hour)
	cache.Set("key3", "value3", 1*time.Hour)
	cache.Clear()
	if cache.Size() != 0 {
		t.Errorf("Expected size 0 after clear, got %d", cache.Size())
	}
}

func TestMemoryCacheExpiration(t *testing.T) {
	cache := NewMemoryCache()
	defer cache.Close()

	// Set item with short TTL
	cache.Set("expire", "value", 100*time.Millisecond)

	// Should exist immediately
	_, exists := cache.Get("expire")
	if !exists {
		t.Error("Expected key to exist immediately after setting")
	}

	// Wait for expiration
	time.Sleep(150 * time.Millisecond)

	// Should not exist after expiration
	_, exists = cache.Get("expire")
	if exists {
		t.Error("Expected key to expire")
	}
}

func TestMemoryCacheConcurrency(t *testing.T) {
	cache := NewMemoryCache()
	defer cache.Close()

	var wg sync.WaitGroup
	iterations := 100
	goroutines := 10

	// Concurrent writes
	for i := 0; i < goroutines; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < iterations; j++ {
				key := string(rune('a' + id))
				cache.Set(key, j, 1*time.Hour)
			}
		}(i)
	}

	// Concurrent reads
	for i := 0; i < goroutines; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < iterations; j++ {
				key := string(rune('a' + id))
				cache.Get(key)
			}
		}(i)
	}

	wg.Wait()
}

func TestMemoryCacheGoroutineCleanup(t *testing.T) {
	// Get initial goroutine count
	initialGoroutines := runtime.NumGoroutine()

	// Create and close multiple caches
	for i := 0; i < 5; i++ {
		cache := NewMemoryCache()
		cache.Set("key", "value", 1*time.Hour)
		cache.Close()
	}

	// Give goroutines time to clean up
	time.Sleep(100 * time.Millisecond)

	// Check that goroutines were cleaned up
	finalGoroutines := runtime.NumGoroutine()
	if finalGoroutines > initialGoroutines+1 {
		t.Errorf("Goroutine leak detected: initial=%d, final=%d",
			initialGoroutines, finalGoroutines)
	}
}

func TestMemoryCacheCleanupRoutine(t *testing.T) {
	cache := NewMemoryCache()
	defer cache.Close()

	// Add items with very short TTL
	for i := 0; i < 10; i++ {
		cache.Set(string(rune('a'+i)), i, 1*time.Millisecond)
	}

	// Items should exist initially
	if cache.Size() != 10 {
		t.Errorf("Expected 10 items, got %d", cache.Size())
	}

	// Force cleanup by waiting longer than cleanup interval
	// Note: In production, cleanup runs every minute, but for testing
	// we rely on Get() to filter expired items
	time.Sleep(10 * time.Millisecond)

	// Try to get expired items (they should not exist)
	for i := 0; i < 10; i++ {
		_, exists := cache.Get(string(rune('a' + i)))
		if exists {
			t.Errorf("Expected item %c to be expired", rune('a'+i))
		}
	}
}

func TestLRUCacheBasicOperations(t *testing.T) {
	cache := NewLRUCache(3)

	// Test Set and Get
	cache.Set("key1", "value1", 1*time.Hour)
	val, exists := cache.Get("key1")
	if !exists {
		t.Error("Expected key1 to exist")
	}
	if val != "value1" {
		t.Errorf("Expected value1, got %v", val)
	}

	// Test capacity eviction
	cache.Set("key1", "value1", 1*time.Hour)
	cache.Set("key2", "value2", 1*time.Hour)
	cache.Set("key3", "value3", 1*time.Hour)
	cache.Set("key4", "value4", 1*time.Hour) // Should evict key1

	if cache.Size() != 3 {
		t.Errorf("Expected size 3, got %d", cache.Size())
	}

	// key1 should have been evicted (it was least recently used)
	_, exists = cache.Get("key1")
	if exists {
		t.Error("Expected key1 to be evicted")
	}
}

func TestLRUCacheLRUOrder(t *testing.T) {
	cache := NewLRUCache(3)

	// Add three items
	cache.Set("a", 1, 1*time.Hour)
	cache.Set("b", 2, 1*time.Hour)
	cache.Set("c", 3, 1*time.Hour)

	// Access 'a' to make it recently used
	cache.Get("a")

	// Add new item, should evict 'b' (least recently used)
	cache.Set("d", 4, 1*time.Hour)

	// Check that 'b' was evicted
	_, exists := cache.Get("b")
	if exists {
		t.Error("Expected 'b' to be evicted")
	}

	// Check that 'a', 'c', 'd' still exist
	_, exists = cache.Get("a")
	if !exists {
		t.Error("Expected 'a' to exist")
	}
	_, exists = cache.Get("c")
	if !exists {
		t.Error("Expected 'c' to exist")
	}
	_, exists = cache.Get("d")
	if !exists {
		t.Error("Expected 'd' to exist")
	}
}

func TestLRUCacheExpiration(t *testing.T) {
	cache := NewLRUCache(10)

	// Set item with short TTL
	cache.Set("expire", "value", 100*time.Millisecond)

	// Should exist immediately
	_, exists := cache.Get("expire")
	if !exists {
		t.Error("Expected key to exist immediately after setting")
	}

	// Wait for expiration
	time.Sleep(150 * time.Millisecond)

	// Should not exist after expiration
	_, exists = cache.Get("expire")
	if exists {
		t.Error("Expected key to expire")
	}
}

func TestLRUCacheConcurrency(t *testing.T) {
	cache := NewLRUCache(100)

	var wg sync.WaitGroup
	iterations := 100
	goroutines := 10

	// Concurrent operations
	for i := 0; i < goroutines; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < iterations; j++ {
				key := string(rune('a' + (j % 26)))
				cache.Set(key, j, 1*time.Hour)
				cache.Get(key)
				if j%10 == 0 {
					cache.Delete(key)
				}
			}
		}(i)
	}

	wg.Wait()

	// Cache should still be functional
	cache.Set("final", "test", 1*time.Hour)
	val, exists := cache.Get("final")
	if !exists || val != "test" {
		t.Error("Cache not functional after concurrent operations")
	}
}

// BenchmarkMemoryCacheSet benchmarks Set operations
func BenchmarkMemoryCacheSet(b *testing.B) {
	cache := NewMemoryCache()
	defer cache.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cache.Set("key", "value", 1*time.Hour)
	}
}

// BenchmarkMemoryCacheGet benchmarks Get operations
func BenchmarkMemoryCacheGet(b *testing.B) {
	cache := NewMemoryCache()
	defer cache.Close()
	cache.Set("key", "value", 1*time.Hour)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cache.Get("key")
	}
}

// BenchmarkLRUCacheSet benchmarks LRU Set operations
func BenchmarkLRUCacheSet(b *testing.B) {
	cache := NewLRUCache(1000)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cache.Set("key", "value", 1*time.Hour)
	}
}

// BenchmarkLRUCacheGet benchmarks LRU Get operations
func BenchmarkLRUCacheGet(b *testing.B) {
	cache := NewLRUCache(1000)
	cache.Set("key", "value", 1*time.Hour)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cache.Get("key")
	}
}