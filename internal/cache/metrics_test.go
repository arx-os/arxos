package cache

import (
	"testing"
	"time"
)

func TestCacheMetrics(t *testing.T) {
	opts := &CacheOptions{
		EnableMetrics: true,
	}

	cache := NewLRUCacheWithMetrics(3, opts)

	// Test hits and misses
	cache.Set("key1", "value1", 1*time.Hour)

	// This should be a hit
	_, exists := cache.Get("key1")
	if !exists {
		t.Error("Expected key1 to exist")
	}

	// This should be a miss
	_, exists = cache.Get("nonexistent")
	if exists {
		t.Error("Expected nonexistent key to not exist")
	}

	metrics := cache.GetMetrics()
	stats := metrics.GetStats()

	if stats.Hits != 1 {
		t.Errorf("Expected 1 hit, got %d", stats.Hits)
	}

	if stats.Misses != 1 {
		t.Errorf("Expected 1 miss, got %d", stats.Misses)
	}

	if stats.Sets != 1 {
		t.Errorf("Expected 1 set, got %d", stats.Sets)
	}

	// Test hit rate
	if stats.HitRate != 50.0 {
		t.Errorf("Expected 50%% hit rate, got %.2f%%", stats.HitRate)
	}
}

func TestCacheEvictionCallback(t *testing.T) {
	evictedKeys := make([]string, 0)

	opts := &CacheOptions{
		EnableMetrics: true,
		OnEviction: func(key string, value interface{}) {
			evictedKeys = append(evictedKeys, key)
		},
	}

	cache := NewLRUCacheWithMetrics(2, opts)

	// Fill cache
	cache.Set("key1", "value1", 1*time.Hour)
	cache.Set("key2", "value2", 1*time.Hour)

	// This should evict key1
	cache.Set("key3", "value3", 1*time.Hour)

	if len(evictedKeys) != 1 {
		t.Errorf("Expected 1 eviction, got %d", len(evictedKeys))
	}

	if len(evictedKeys) > 0 && evictedKeys[0] != "key1" {
		t.Errorf("Expected key1 to be evicted, got %s", evictedKeys[0])
	}

	metrics := cache.GetMetrics()
	stats := metrics.GetStats()

	if stats.Evictions != 1 {
		t.Errorf("Expected 1 eviction in metrics, got %d", stats.Evictions)
	}
}

func TestMemoryCacheWithCustomInterval(t *testing.T) {
	opts := &CacheOptions{
		CleanupInterval: 50 * time.Millisecond, // Fast cleanup for testing
		EnableMetrics:   true,
	}

	cache := NewMemoryCacheWithOptions(opts)
	defer cache.Close()

	// Set item with short TTL
	cache.Set("key1", "value1", 25*time.Millisecond)

	// Item should exist initially
	_, exists := cache.Get("key1")
	if !exists {
		t.Error("Expected key1 to exist initially")
	}

	// Wait for cleanup cycle
	time.Sleep(100 * time.Millisecond)

	// Item should be cleaned up
	_, exists = cache.Get("key1")
	if exists {
		t.Error("Expected key1 to be cleaned up")
	}

	// Check expiration metric
	metrics := cache.GetMetrics()
	stats := metrics.GetStats()
	if stats.Expirations == 0 {
		t.Error("Expected at least one expiration to be tracked")
	}
}

func TestMetricsReset(t *testing.T) {
	metrics := &CacheMetrics{}

	// Increment various counters
	metrics.IncrementHits()
	metrics.IncrementHits()
	metrics.IncrementMisses()
	metrics.IncrementSets()

	stats := metrics.GetStats()
	if stats.Hits != 2 || stats.Misses != 1 || stats.Sets != 1 {
		t.Error("Metrics not incremented correctly")
	}

	// Reset metrics
	metrics.Reset()

	stats = metrics.GetStats()
	if stats.Hits != 0 || stats.Misses != 0 || stats.Sets != 0 {
		t.Error("Metrics not reset correctly")
	}

	if stats.HitRate != 0 {
		t.Errorf("Expected 0%% hit rate after reset, got %.2f%%", stats.HitRate)
	}
}

func BenchmarkLRUCacheWithMetrics(b *testing.B) {
	opts := &CacheOptions{
		EnableMetrics: true,
	}

	cache := NewLRUCacheWithMetrics(1000, opts)

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		key := string(rune(i % 256))
		cache.Set(key, i, 1*time.Hour)
		cache.Get(key)
	}

	stats := cache.GetMetrics().GetStats()
	b.Logf("Cache stats: Hits=%d, Misses=%d, HitRate=%.2f%%",
		stats.Hits, stats.Misses, stats.HitRate)
}