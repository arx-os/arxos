package cache

import (
	"context"
	"path/filepath"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// MockLogger implements domain.Logger for testing
type MockLogger struct{}

func (m *MockLogger) Debug(msg string, fields ...any) {}
func (m *MockLogger) Info(msg string, fields ...any)  {}
func (m *MockLogger) Warn(msg string, fields ...any)  {}
func (m *MockLogger) Error(msg string, fields ...any) {}
func (m *MockLogger) Fatal(msg string, fields ...any) {}

func TestUnifiedCacheBasicOperations(t *testing.T) {
	// Create temporary directory for testing
	tempDir := t.TempDir()
	cfg := &config.Config{
		UnifiedCache: config.UnifiedCacheConfig{
			L1: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxEntries int64         `json:"max_entries" yaml:"max_entries"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
			}{
				Enabled:    true,
				MaxEntries: 1000,
				DefaultTTL: 5 * time.Minute,
			},
			L2: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxSizeMB  int64         `json:"max_size_mb" yaml:"max_size_mb"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Path       string        `json:"path" yaml:"path"`
			}{
				Enabled:    true,
				MaxSizeMB:  100,
				DefaultTTL: time.Hour,
				Path:       filepath.Join(tempDir, "l2"),
			},
			L3: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Host       string        `json:"host" yaml:"host"`
				Port       int           `json:"port" yaml:"port"`
				Password   string        `json:"password" yaml:"password"`
				DB         int           `json:"db" yaml:"db"`
			}{
				Enabled: false,
			},
		},
	}

	logger := &MockLogger{}
	cache, err := NewUnifiedCache(cfg, logger)
	require.NoError(t, err)
	defer cache.Close()

	ctx := context.Background()

	// Test Set and Get
	err = cache.Set(ctx, "key1", "value1", time.Minute)
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

func TestUnifiedCacheExpiration(t *testing.T) {
	tempDir := t.TempDir()
	cfg := &config.Config{
		UnifiedCache: config.UnifiedCacheConfig{
			L1: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxEntries int64         `json:"max_entries" yaml:"max_entries"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
			}{
				Enabled:    true,
				MaxEntries: 1000,
				DefaultTTL: 5 * time.Minute,
			},
			L2: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxSizeMB  int64         `json:"max_size_mb" yaml:"max_size_mb"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Path       string        `json:"path" yaml:"path"`
			}{
				Enabled:    true,
				MaxSizeMB:  100,
				DefaultTTL: time.Hour,
				Path:       filepath.Join(tempDir, "l2"),
			},
			L3: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Host       string        `json:"host" yaml:"host"`
				Port       int           `json:"port" yaml:"port"`
				Password   string        `json:"password" yaml:"password"`
				DB         int           `json:"db" yaml:"db"`
			}{
				Enabled: false,
			},
		},
	}

	logger := &MockLogger{}
	cache, err := NewUnifiedCache(cfg, logger)
	require.NoError(t, err)
	defer cache.Close()

	ctx := context.Background()

	// Set with very short TTL
	err = cache.Set(ctx, "expired", "value", 10*time.Millisecond)
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

func TestUnifiedCacheDelete(t *testing.T) {
	tempDir := t.TempDir()
	cfg := &config.Config{
		UnifiedCache: config.UnifiedCacheConfig{
			L1: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxEntries int64         `json:"max_entries" yaml:"max_entries"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
			}{
				Enabled:    true,
				MaxEntries: 1000,
				DefaultTTL: 5 * time.Minute,
			},
			L2: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxSizeMB  int64         `json:"max_size_mb" yaml:"max_size_mb"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Path       string        `json:"path" yaml:"path"`
			}{
				Enabled:    true,
				MaxSizeMB:  100,
				DefaultTTL: time.Hour,
				Path:       filepath.Join(tempDir, "l2"),
			},
			L3: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Host       string        `json:"host" yaml:"host"`
				Port       int           `json:"port" yaml:"port"`
				Password   string        `json:"password" yaml:"password"`
				DB         int           `json:"db" yaml:"db"`
			}{
				Enabled: false,
			},
		},
	}

	logger := &MockLogger{}
	cache, err := NewUnifiedCache(cfg, logger)
	require.NoError(t, err)
	defer cache.Close()

	ctx := context.Background()

	// Set a value
	err = cache.Set(ctx, "key1", "value1", time.Minute)
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

func TestUnifiedCacheClear(t *testing.T) {
	tempDir := t.TempDir()
	cfg := &config.Config{
		UnifiedCache: config.UnifiedCacheConfig{
			L1: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxEntries int64         `json:"max_entries" yaml:"max_entries"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
			}{
				Enabled:    true,
				MaxEntries: 1000,
				DefaultTTL: 5 * time.Minute,
			},
			L2: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxSizeMB  int64         `json:"max_size_mb" yaml:"max_size_mb"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Path       string        `json:"path" yaml:"path"`
			}{
				Enabled:    true,
				MaxSizeMB:  100,
				DefaultTTL: time.Hour,
				Path:       filepath.Join(tempDir, "l2"),
			},
			L3: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Host       string        `json:"host" yaml:"host"`
				Port       int           `json:"port" yaml:"port"`
				Password   string        `json:"password" yaml:"password"`
				DB         int           `json:"db" yaml:"db"`
			}{
				Enabled: false,
			},
		},
	}

	logger := &MockLogger{}
	cache, err := NewUnifiedCache(cfg, logger)
	require.NoError(t, err)
	defer cache.Close()

	ctx := context.Background()

	// Set multiple values
	err = cache.Set(ctx, "key1", "value1", time.Minute)
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

func TestUnifiedCacheStats(t *testing.T) {
	tempDir := t.TempDir()
	cfg := &config.Config{
		UnifiedCache: config.UnifiedCacheConfig{
			L1: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxEntries int64         `json:"max_entries" yaml:"max_entries"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
			}{
				Enabled:    true,
				MaxEntries: 1000,
				DefaultTTL: 5 * time.Minute,
			},
			L2: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxSizeMB  int64         `json:"max_size_mb" yaml:"max_size_mb"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Path       string        `json:"path" yaml:"path"`
			}{
				Enabled:    true,
				MaxSizeMB:  100,
				DefaultTTL: time.Hour,
				Path:       filepath.Join(tempDir, "l2"),
			},
			L3: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Host       string        `json:"host" yaml:"host"`
				Port       int           `json:"port" yaml:"port"`
				Password   string        `json:"password" yaml:"password"`
				DB         int           `json:"db" yaml:"db"`
			}{
				Enabled: false,
			},
		},
	}

	logger := &MockLogger{}
	cache, err := NewUnifiedCache(cfg, logger)
	require.NoError(t, err)
	defer cache.Close()

	ctx := context.Background()

	// Get initial stats
	stats, err := cache.GetStats(ctx)
	require.NoError(t, err)
	assert.Equal(t, int64(0), stats.TotalHits)
	assert.Equal(t, int64(0), stats.TotalMisses)

	// Set and get a value to generate stats
	err = cache.Set(ctx, "key1", "value1", time.Minute)
	require.NoError(t, err)

	value, err := cache.Get(ctx, "key1")
	require.NoError(t, err)
	assert.Equal(t, "value1", value)

	// Check stats after hit
	stats, err = cache.GetStats(ctx)
	require.NoError(t, err)
	assert.Equal(t, int64(1), stats.TotalHits)
	assert.Equal(t, int64(0), stats.TotalMisses)

	// Try to get non-existent key to generate miss
	value, err = cache.Get(ctx, "nonexistent")
	require.NoError(t, err)
	assert.Nil(t, value)

	// Check stats after miss
	stats, err = cache.GetStats(ctx)
	require.NoError(t, err)
	assert.Equal(t, int64(1), stats.TotalHits)
	assert.Equal(t, int64(1), stats.TotalMisses)
}

func TestUnifiedCacheL2Persistence(t *testing.T) {
	tempDir := t.TempDir()
	cfg := &config.Config{
		UnifiedCache: config.UnifiedCacheConfig{
			L1: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxEntries int64         `json:"max_entries" yaml:"max_entries"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
			}{
				Enabled:    true,
				MaxEntries: 1000,
				DefaultTTL: 5 * time.Minute,
			},
			L2: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				MaxSizeMB  int64         `json:"max_size_mb" yaml:"max_size_mb"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Path       string        `json:"path" yaml:"path"`
			}{
				Enabled:    true,
				MaxSizeMB:  100,
				DefaultTTL: time.Hour,
				Path:       filepath.Join(tempDir, "l2"),
			},
			L3: struct {
				Enabled    bool          `json:"enabled" yaml:"enabled"`
				DefaultTTL time.Duration `json:"default_ttl" yaml:"default_ttl"`
				Host       string        `json:"host" yaml:"host"`
				Port       int           `json:"port" yaml:"port"`
				Password   string        `json:"password" yaml:"password"`
				DB         int           `json:"db" yaml:"db"`
			}{
				Enabled: false,
			},
		},
	}

	logger := &MockLogger{}
	cache, err := NewUnifiedCache(cfg, logger)
	require.NoError(t, err)

	ctx := context.Background()

	// Set a value with long TTL to ensure it goes to L2
	err = cache.Set(ctx, "persistent_key", "persistent_value", 2*time.Hour)
	require.NoError(t, err)

	// Verify it's accessible
	value, err := cache.Get(ctx, "persistent_key")
	require.NoError(t, err)
	assert.Equal(t, "persistent_value", value)

	// Close the cache
	cache.Close()

	// Create a new cache instance (simulating restart)
	cache2, err := NewUnifiedCache(cfg, logger)
	require.NoError(t, err)
	defer cache2.Close()

	// The value should still be accessible from L2
	value, err = cache2.Get(ctx, "persistent_key")
	require.NoError(t, err)
	assert.Equal(t, "persistent_value", value)
}
