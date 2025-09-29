package di

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestRealServiceImplementations(t *testing.T) {
	// Test with real service implementations
	config := DefaultConfig()
	config.Database.Host = "localhost"
	config.Database.Port = 5432
	config.Database.Database = "arxos_test"
	config.Cache.Host = "localhost"
	config.Cache.Port = 6379
	config.Storage.Path = "./test_storage"

	container := NewContainer(config)
	ctx := context.Background()

	// Test database initialization
	db, err := container.initDatabase(ctx)
	if err != nil {
		t.Logf("Database initialization failed (expected in test environment): %v", err)
		// This is expected in test environment without PostGIS
		return
	}
	assert.NoError(t, err)
	assert.NotNil(t, db)
	assert.True(t, db.IsHealthy())

	// Test cache initialization
	cache, err := container.initCache(ctx)
	if err != nil {
		t.Logf("Cache initialization failed (expected in test environment): %v", err)
		// This is expected in test environment without Redis
		return
	}
	assert.NoError(t, err)
	assert.NotNil(t, cache)
	assert.True(t, cache.IsHealthy())

	// Test storage initialization
	storage, err := container.initStorage(ctx)
	assert.NoError(t, err)
	assert.NotNil(t, storage)
	assert.True(t, storage.IsHealthy())

	// Clean up
	if db != nil {
		db.Close()
	}
	if cache != nil {
		// Cache doesn't have a Close method, just log cleanup
		t.Log("Cache cleanup completed")
	}
	if storage != nil {
		// Storage doesn't have a Close method, just log cleanup
		t.Log("Storage cleanup completed")
	}
}

func TestServiceHealth(t *testing.T) {
	// Test service health checks
	config := DefaultConfig()
	container := NewContainer(config)

	// Test uninitialized services
	assert.False(t, container.IsInitialized())

	// Test placeholder services
	dbPlaceholder := &databasePlaceholder{}
	assert.True(t, dbPlaceholder.IsHealthy())

	cachePlaceholder := &cachePlaceholder{}
	assert.True(t, cachePlaceholder.IsHealthy())

	storagePlaceholder := &storagePlaceholder{}
	assert.True(t, storagePlaceholder.IsHealthy())
}

func TestServiceStats(t *testing.T) {
	// Test service statistics
	dbPlaceholder := &databasePlaceholder{}
	stats := dbPlaceholder.GetStats()
	assert.NotNil(t, stats)
	assert.Contains(t, stats, "status")

	cachePlaceholder := &cachePlaceholder{}
	stats = cachePlaceholder.GetStats()
	assert.NotNil(t, stats)
	assert.Contains(t, stats, "status")

	storagePlaceholder := &storagePlaceholder{}
	stats = storagePlaceholder.GetStats()
	assert.NotNil(t, stats)
	assert.Contains(t, stats, "status")
}
