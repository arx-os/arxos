package cache

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestPostgresCacheService tests the PostgreSQL-based cache implementation
func TestPostgresCacheService(t *testing.T) {
	// Note: These tests require a PostgreSQL database connection
	// Run with: go test -tags=integration

	t.Run("BasicOperations", func(t *testing.T) {
		cache, err := NewPostgresCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		// Test Set and Get
		key := "test_key"
		value := "test_value"
		err = cache.Set(key, value, 5*time.Second)
		require.NoError(t, err)

		retrieved, err := cache.Get(key)
		require.NoError(t, err)
		assert.Equal(t, value, retrieved)

		// Test Exists
		exists, err := cache.Exists(key)
		require.NoError(t, err)
		assert.True(t, exists)

		// Test Delete
		err = cache.Delete(key)
		require.NoError(t, err)

		exists, err = cache.Exists(key)
		require.NoError(t, err)
		assert.False(t, exists)
	})

	t.Run("Expiration", func(t *testing.T) {
		cache, err := NewPostgresCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		key := "expiring_key"
		value := "expiring_value"
		
		// Set with 1 second TTL
		err = cache.Set(key, value, 1*time.Second)
		require.NoError(t, err)

		// Should exist immediately
		exists, err := cache.Exists(key)
		require.NoError(t, err)
		assert.True(t, exists)

		// Wait for expiration
		time.Sleep(2 * time.Second)

		// Should not exist after expiration
		retrieved, err := cache.Get(key)
		require.NoError(t, err)
		assert.Empty(t, retrieved)
	})

	t.Run("Counter", func(t *testing.T) {
		cache, err := NewPostgresCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		key := "counter_key"
		
		// Increment new counter
		val, err := cache.Incr(key)
		require.NoError(t, err)
		assert.Equal(t, int64(1), val)

		// Increment again
		val, err = cache.Incr(key)
		require.NoError(t, err)
		assert.Equal(t, int64(2), val)

		// Increment by specific amount
		val, err = cache.IncrBy(key, 5)
		require.NoError(t, err)
		assert.Equal(t, int64(7), val)

		// Clean up
		cache.Delete(key)
	})

	t.Run("HashOperations", func(t *testing.T) {
		cache, err := NewPostgresCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		key := "hash_key"
		
		// Set hash fields
		err = cache.HSet(key, "field1", "value1")
		require.NoError(t, err)
		
		err = cache.HSet(key, "field2", "value2")
		require.NoError(t, err)

		// Get specific field
		val, err := cache.HGet(key, "field1")
		require.NoError(t, err)
		assert.Equal(t, "value1", val)

		// Get all fields
		allFields, err := cache.HGetAll(key)
		require.NoError(t, err)
		assert.Len(t, allFields, 2)
		assert.Equal(t, "value1", allFields["field1"])
		assert.Equal(t, "value2", allFields["field2"])

		// Clean up
		cache.Delete(key)
	})

	t.Run("PatternInvalidation", func(t *testing.T) {
		cache, err := NewPostgresCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		// Set multiple keys with pattern
		cache.Set("user:1:profile", "profile1", 1*time.Hour)
		cache.Set("user:1:settings", "settings1", 1*time.Hour)
		cache.Set("user:2:profile", "profile2", 1*time.Hour)
		cache.Set("other:key", "value", 1*time.Hour)

		// Invalidate pattern
		err = cache.InvalidatePattern("user:1:*")
		require.NoError(t, err)

		// Check keys
		exists1, _ := cache.Exists("user:1:profile")
		exists2, _ := cache.Exists("user:1:settings")
		exists3, _ := cache.Exists("user:2:profile")
		exists4, _ := cache.Exists("other:key")

		assert.False(t, exists1)
		assert.False(t, exists2)
		assert.True(t, exists3)
		assert.True(t, exists4)

		// Clean up
		cache.FlushDB()
	})

	t.Run("HealthCheck", func(t *testing.T) {
		cache, err := NewPostgresCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		err = cache.HealthCheck()
		assert.NoError(t, err)
	})

	t.Run("Statistics", func(t *testing.T) {
		cache, err := NewPostgresCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		// Perform some operations
		cache.Set("stat_key1", "value1", 1*time.Hour)
		cache.Get("stat_key1")
		cache.Get("non_existent")

		// Get statistics
		stats, err := cache.GetStats()
		require.NoError(t, err)
		assert.NotNil(t, stats)
		assert.GreaterOrEqual(t, stats.TotalKeys, int64(1))
	})
}

// TestCacheServiceAdapter tests the cache service adapter
func TestCacheServiceAdapter(t *testing.T) {
	t.Run("AdapterOperations", func(t *testing.T) {
		cache, err := NewCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		// Test Set and Get
		key := "adapter_key"
		value := map[string]interface{}{
			"field1": "value1",
			"field2": 123,
		}

		err = cache.Set(key, value, 5*time.Second)
		require.NoError(t, err)

		retrieved, err := cache.Get(key)
		require.NoError(t, err)
		assert.NotNil(t, retrieved)

		// Test GetOrSet
		key2 := "getorset_key"
		fetchCalled := false
		result, err := cache.GetOrSet(key2, 5*time.Second, func() (interface{}, error) {
			fetchCalled = true
			return "fetched_value", nil
		})
		require.NoError(t, err)
		assert.Equal(t, "fetched_value", result)
		assert.True(t, fetchCalled)

		// Second call should not trigger fetch
		fetchCalled = false
		result, err = cache.GetOrSet(key2, 5*time.Second, func() (interface{}, error) {
			fetchCalled = true
			return "new_value", nil
		})
		require.NoError(t, err)
		assert.Equal(t, "fetched_value", result)
		assert.False(t, fetchCalled)

		// Clean up
		cache.Delete(key)
		cache.Delete(key2)
	})

	t.Run("BatchOperations", func(t *testing.T) {
		cache, err := NewCacheService(nil, nil)
		if err != nil {
			t.Skip("PostgreSQL not available, skipping integration test")
		}
		defer cache.Close()

		// Batch set
		items := map[string]interface{}{
			"batch1": "value1",
			"batch2": "value2",
			"batch3": "value3",
		}

		err = cache.MSet(items, 5*time.Second)
		require.NoError(t, err)

		// Batch get
		keys := []string{"batch1", "batch2", "batch3", "non_existent"}
		results, err := cache.MGet(keys)
		require.NoError(t, err)
		assert.Len(t, results, 3)
		assert.Equal(t, "value1", results["batch1"])
		assert.Equal(t, "value2", results["batch2"])
		assert.Equal(t, "value3", results["batch3"])

		// Clean up
		for key := range items {
			cache.Delete(key)
		}
	})
}

// BenchmarkPostgresCache benchmarks the PostgreSQL cache
func BenchmarkPostgresCache(b *testing.B) {
	cache, err := NewPostgresCacheService(nil, nil)
	if err != nil {
		b.Skip("PostgreSQL not available, skipping benchmark")
	}
	defer cache.Close()

	b.Run("Set", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			key := fmt.Sprintf("bench_key_%d", i)
			cache.Set(key, "value", 1*time.Hour)
		}
	})

	b.Run("Get", func(b *testing.B) {
		// Pre-populate
		key := "bench_get_key"
		cache.Set(key, "value", 1*time.Hour)

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			cache.Get(key)
		}
	})

	b.Run("Incr", func(b *testing.B) {
		key := "bench_counter"
		
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			cache.Incr(key)
		}
	})
}