package infrastructure

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestInMemoryCache(t *testing.T) {
	cache := NewInMemoryCache()
	ctx := context.Background()

	// Test Set and Get
	err := cache.Set(ctx, "key1", "value1", time.Minute)
	require.NoError(t, err)

	value, err := cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Equal(t, "value1", value)

	// Test Get with non-existent key
	value, err = cache.Get(ctx, "nonexistent")
	require.NoError(t, err)
	assert.Nil(t, value)

	// Test Set with different types
	err = cache.Set(ctx, "key2", 42, time.Minute)
	require.NoError(t, err)

	value, err = cache.Get(ctx, "key2")
	require.NoError(t, err)
	assert.Equal(t, 42, value)

	// Test Set with struct
	type TestStruct struct {
		Name  string
		Value int
	}
	testStruct := TestStruct{Name: "test", Value: 123}
	err = cache.Set(ctx, "key3", testStruct, time.Minute)
	require.NoError(t, err)

	value, err = cache.Get(ctx, "key3")
	require.NoError(t, err)
	assert.Equal(t, testStruct, value)
}

func TestInMemoryCacheExpiration(t *testing.T) {
	cache := NewInMemoryCache()
	ctx := context.Background()

	// Set with very short TTL
	err := cache.Set(ctx, "expired", "value", 10*time.Millisecond)
	require.NoError(t, err)

	// Should be available immediately
	value, err := cache.Get(ctx, "expired")
	require.NoError(t, err)
	assert.Equal(t, "value", value)

	// Wait for expiration
	time.Sleep(20 * time.Millisecond)

	// Should be expired now
	value, err = cache.Get(ctx, "expired")
	require.NoError(t, err)
	assert.Nil(t, value)
}

func TestInMemoryCacheDelete(t *testing.T) {
	cache := NewInMemoryCache()
	ctx := context.Background()

	// Set a value
	err := cache.Set(ctx, "key1", "value1", time.Minute)
	require.NoError(t, err)

	// Verify it exists
	value, err := cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Equal(t, "value1", value)

	// Delete it
	err = cache.Delete(ctx, "key1")
	require.NoError(t, err)

	// Verify it's gone
	value, err = cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Nil(t, value)

	// Delete non-existent key should not error
	err = cache.Delete(ctx, "nonexistent")
	require.NoError(t, err)
}

func TestInMemoryCacheClear(t *testing.T) {
	cache := NewInMemoryCache()
	ctx := context.Background()

	// Set multiple values
	err := cache.Set(ctx, "key1", "value1", time.Minute)
	require.NoError(t, err)
	err = cache.Set(ctx, "key2", "value2", time.Minute)
	require.NoError(t, err)
	err = cache.Set(ctx, "key3", "value3", time.Minute)
	require.NoError(t, err)

	// Verify they exist
	value, err := cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Equal(t, "value1", value)

	value, err = cache.Get(ctx, "key2")
	require.NoError(t, err)
	assert.Equal(t, "value2", value)

	value, err = cache.Get(ctx, "key3")
	require.NoError(t, err)
	assert.Equal(t, "value3", value)

	// Clear all
	err = cache.Clear(ctx)
	require.NoError(t, err)

	// Verify all are gone
	value, err = cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Nil(t, value)

	value, err = cache.Get(ctx, "key2")
	require.NoError(t, err)
	assert.Nil(t, value)

	value, err = cache.Get(ctx, "key3")
	require.NoError(t, err)
	assert.Nil(t, value)
}

func TestInMemoryCacheClose(t *testing.T) {
	cache := NewInMemoryCache()
	ctx := context.Background()

	// Set a value
	err := cache.Set(ctx, "key1", "value1", time.Minute)
	require.NoError(t, err)

	// Verify value is accessible
	value, err := cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Equal(t, "value1", value)
}

func TestCacheWrapper(t *testing.T) {
	cfg := &config.Config{}
	cache, err := NewCache(cfg)
	require.NoError(t, err)
	ctx := context.Background()

	// Test that the wrapper delegates to in-memory cache
	err = cache.Set(ctx, "key1", "value1", time.Minute)
	require.NoError(t, err)

	value, err := cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Equal(t, "value1", value)

	// Test delete
	err = cache.Delete(ctx, "key1")
	require.NoError(t, err)

	value, err = cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Nil(t, value)

	// Test clear
	err = cache.Set(ctx, "key2", "value2", time.Minute)
	require.NoError(t, err)
	err = cache.Clear(ctx)
	require.NoError(t, err)

	value, err = cache.Get(ctx, "key2")
	require.NoError(t, err)
	assert.Nil(t, value)
}

func TestConcurrentCacheAccess(t *testing.T) {
	cache := NewInMemoryCache()
	ctx := context.Background()

	// Test concurrent access
	done := make(chan bool, 10)
	
	for i := 0; i < 10; i++ {
		go func(i int) {
			key := fmt.Sprintf("key%d", i)
			value := fmt.Sprintf("value%d", i)
			
			// Set
			err := cache.Set(ctx, key, value, time.Minute)
			assert.NoError(t, err)
			
			// Get
			retrieved, err := cache.Get(ctx, key)
			assert.NoError(t, err)
			assert.Equal(t, value, retrieved)
			
			done <- true
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify all values are still accessible
	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("key%d", i)
		expectedValue := fmt.Sprintf("value%d", i)
		
		value, err := cache.Get(ctx, key)
		require.NoError(t, err)
		assert.Equal(t, expectedValue, value)
	}
}
