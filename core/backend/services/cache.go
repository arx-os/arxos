package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"go.uber.org/zap"
)

// CacheService provides a high-level caching abstraction with TTL and invalidation
type CacheService struct {
	redis  *RedisService
	logger *zap.Logger
	ctx    context.Context
}

// CacheConfig holds configuration for the cache service
type CacheConfig struct {
	DefaultTTL    time.Duration
	MaxTTL        time.Duration
	EnableMetrics bool
	KeyPrefix     string
}

// DefaultCacheConfig returns a default cache configuration
func DefaultCacheConfig() *CacheConfig {
	return &CacheConfig{
		DefaultTTL:    15 * time.Minute,
		MaxTTL:        24 * time.Hour,
		EnableMetrics: true,
		KeyPrefix:     "arx:cache:",
	}
}

// CacheEntry represents a cached item with metadata
type CacheEntry struct {
	Value       interface{} `json:"value"`
	CreatedAt   time.Time   `json:"created_at"`
	ExpiresAt   time.Time   `json:"expires_at"`
	AccessCount int64       `json:"access_count"`
	LastAccess  time.Time   `json:"last_access"`
}

// CacheStats holds cache statistics
type CacheStats struct {
	Hits        int64
	Misses      int64
	HitRate     float64
	TotalKeys   int64
	MemoryUsage int64
}

// NewCacheService creates a new cache service
func NewCacheService(redisService *RedisService, config *CacheConfig, logger *zap.Logger) *CacheService {
	if config == nil {
		config = DefaultCacheConfig()
	}

	service := &CacheService{
		redis:  redisService,
		logger: logger,
		ctx:    context.Background(),
	}

	logger.Info("Cache service initialized",
		zap.Duration("default_ttl", config.DefaultTTL),
		zap.Duration("max_ttl", config.MaxTTL),
		zap.String("key_prefix", config.KeyPrefix),
	)

	return service
}

// Get retrieves a value from cache
func (c *CacheService) Get(key string) (interface{}, error) {
	fullKey := c.buildKey(key)

	// Get raw value from Redis
	rawValue, err := c.redis.Get(fullKey)
	if err != nil {
		c.logger.Debug("Cache miss", zap.String("key", key), zap.Error(err))
		return nil, fmt.Errorf("cache get failed for key %s: %w", key, err)
	}

	if rawValue == "" {
		c.logger.Debug("Cache miss - key not found", zap.String("key", key))
		return nil, nil
	}

	// Unmarshal cache entry
	var entry CacheEntry
	if err := json.Unmarshal([]byte(rawValue), &entry); err != nil {
		c.logger.Error("Failed to unmarshal cache entry", zap.String("key", key), zap.Error(err))
		return nil, fmt.Errorf("failed to unmarshal cache entry for key %s: %w", key, err)
	}

	// Check if entry has expired
	if time.Now().After(entry.ExpiresAt) {
		c.logger.Debug("Cache entry expired", zap.String("key", key))
		c.Delete(key) // Clean up expired entry
		return nil, nil
	}

	// Update access statistics
	entry.AccessCount++
	entry.LastAccess = time.Now()

	// Update the entry in cache
	if err := c.updateEntry(fullKey, entry); err != nil {
		c.logger.Warn("Failed to update cache entry stats", zap.String("key", key), zap.Error(err))
	}

	c.logger.Debug("Cache hit", zap.String("key", key), zap.Int64("access_count", entry.AccessCount))
	return entry.Value, nil
}

// Set stores a value in cache with TTL
func (c *CacheService) Set(key string, value interface{}, ttl time.Duration) error {
	fullKey := c.buildKey(key)

	// Validate TTL
	if ttl <= 0 {
		ttl = 15 * time.Minute // Default TTL
	}
	if ttl > 24*time.Hour {
		ttl = 24 * time.Hour // Max TTL
	}

	// Create cache entry
	entry := CacheEntry{
		Value:       value,
		CreatedAt:   time.Now(),
		ExpiresAt:   time.Now().Add(ttl),
		AccessCount: 0,
		LastAccess:  time.Now(),
	}

	// Marshal entry to JSON
	entryData, err := json.Marshal(entry)
	if err != nil {
		c.logger.Error("Failed to marshal cache entry", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("failed to marshal cache entry for key %s: %w", key, err)
	}

	// Store in Redis with TTL
	if err := c.redis.Set(fullKey, string(entryData), ttl); err != nil {
		c.logger.Error("Failed to set cache entry", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("failed to set cache entry for key %s: %w", key, err)
	}

	c.logger.Debug("Cache entry set", zap.String("key", key), zap.Duration("ttl", ttl))
	return nil
}

// Delete removes a key from cache
func (c *CacheService) Delete(key string) error {
	fullKey := c.buildKey(key)

	if err := c.redis.Delete(fullKey); err != nil {
		c.logger.Error("Failed to delete cache entry", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("failed to delete cache entry for key %s: %w", key, err)
	}

	c.logger.Debug("Cache entry deleted", zap.String("key", key))
	return nil
}

// InvalidatePattern removes all keys matching a pattern
func (c *CacheService) InvalidatePattern(pattern string) error {
	fullPattern := c.buildKey(pattern)

	// Use Redis SCAN to find matching keys
	var keys []string
	var cursor uint64
	var err error

	for {
		// Scan for keys matching pattern
		keys, cursor, err = c.redis.GetClient().Scan(c.ctx, cursor, fullPattern, 100).Result()
		if err != nil {
			c.logger.Error("Failed to scan for cache keys", zap.String("pattern", pattern), zap.Error(err))
			return fmt.Errorf("failed to scan for cache keys with pattern %s: %w", pattern, err)
		}

		// Delete matching keys
		if len(keys) > 0 {
			if err := c.redis.GetClient().Del(c.ctx, keys...).Err(); err != nil {
				c.logger.Error("Failed to delete cache keys", zap.Strings("keys", keys), zap.Error(err))
				return fmt.Errorf("failed to delete cache keys: %w", err)
			}
			c.logger.Info("Invalidated cache keys", zap.String("pattern", pattern), zap.Int("count", len(keys)))
		}

		// Continue scanning if there are more keys
		if cursor == 0 {
			break
		}
	}

	return nil
}

// GetWithTTL retrieves a value and its remaining TTL
func (c *CacheService) GetWithTTL(key string) (interface{}, time.Duration, error) {
	value, err := c.Get(key)
	if err != nil {
		return nil, 0, err
	}

	if value == nil {
		return nil, 0, nil
	}

	fullKey := c.buildKey(key)
	ttl, err := c.redis.TTL(fullKey)
	if err != nil {
		c.logger.Warn("Failed to get TTL for cache key", zap.String("key", key), zap.Error(err))
		return value, 0, nil
	}

	return value, ttl, nil
}

// SetWithMetadata stores a value with custom metadata
func (c *CacheService) SetWithMetadata(key string, value interface{}, ttl time.Duration, metadata map[string]interface{}) error {
	fullKey := c.buildKey(key)

	// Create cache entry with metadata
	entry := CacheEntry{
		Value:       value,
		CreatedAt:   time.Now(),
		ExpiresAt:   time.Now().Add(ttl),
		AccessCount: 0,
		LastAccess:  time.Now(),
	}

	// Add metadata to entry
	entryData := map[string]interface{}{
		"entry":    entry,
		"metadata": metadata,
	}

	// Marshal to JSON
	data, err := json.Marshal(entryData)
	if err != nil {
		c.logger.Error("Failed to marshal cache entry with metadata", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("failed to marshal cache entry with metadata for key %s: %w", key, err)
	}

	// Store in Redis
	if err := c.redis.Set(fullKey, string(data), ttl); err != nil {
		c.logger.Error("Failed to set cache entry with metadata", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("failed to set cache entry with metadata for key %s: %w", key, err)
	}

	c.logger.Debug("Cache entry with metadata set", zap.String("key", key), zap.Duration("ttl", ttl))
	return nil
}

// GetOrSet retrieves a value from cache or sets it using a function
func (c *CacheService) GetOrSet(key string, ttl time.Duration, setter func() (interface{}, error)) (interface{}, error) {
	// Try to get from cache first
	value, err := c.Get(key)
	if err != nil {
		c.logger.Warn("Failed to get from cache, will use setter", zap.String("key", key), zap.Error(err))
	} else if value != nil {
		return value, nil
	}

	// Value not in cache, use setter function
	value, err = setter()
	if err != nil {
		c.logger.Error("Setter function failed", zap.String("key", key), zap.Error(err))
		return nil, fmt.Errorf("setter function failed for key %s: %w", key, err)
	}

	// Store in cache
	if err := c.Set(key, value, ttl); err != nil {
		c.logger.Warn("Failed to store value in cache", zap.String("key", key), zap.Error(err))
		// Don't return error, just log warning
	}

	return value, nil
}

// MGet retrieves multiple values from cache
func (c *CacheService) MGet(keys ...string) (map[string]interface{}, error) {
	if len(keys) == 0 {
		return make(map[string]interface{}), nil
	}

	// Build full keys
	fullKeys := make([]string, len(keys))
	for i, key := range keys {
		fullKeys[i] = c.buildKey(key)
	}

	// Get values from Redis
	values, err := c.redis.GetClient().MGet(c.ctx, fullKeys...).Result()
	if err != nil {
		c.logger.Error("Failed to MGet from cache", zap.Strings("keys", keys), zap.Error(err))
		return nil, fmt.Errorf("failed to MGet from cache: %w", err)
	}

	// Process results
	result := make(map[string]interface{})
	for i, key := range keys {
		if i < len(values) && values[i] != nil {
			// Unmarshal cache entry
			var entry CacheEntry
			if err := json.Unmarshal([]byte(values[i].(string)), &entry); err != nil {
				c.logger.Warn("Failed to unmarshal cache entry", zap.String("key", key), zap.Error(err))
				continue
			}

			// Check if entry has expired
			if time.Now().After(entry.ExpiresAt) {
				c.Delete(key) // Clean up expired entry
				continue
			}

			result[key] = entry.Value
		}
	}

	c.logger.Debug("MGet completed", zap.Strings("keys", keys), zap.Int("found", len(result)))
	return result, nil
}

// MSet stores multiple values in cache
func (c *CacheService) MSet(entries map[string]interface{}, ttl time.Duration) error {
	if len(entries) == 0 {
		return nil
	}

	// Use pipeline for better performance
	pipe := c.redis.GetClient().Pipeline()

	for key, value := range entries {
		fullKey := c.buildKey(key)

		// Create cache entry
		entry := CacheEntry{
			Value:       value,
			CreatedAt:   time.Now(),
			ExpiresAt:   time.Now().Add(ttl),
			AccessCount: 0,
			LastAccess:  time.Now(),
		}

		// Marshal entry
		entryData, err := json.Marshal(entry)
		if err != nil {
			c.logger.Error("Failed to marshal cache entry", zap.String("key", key), zap.Error(err))
			continue
		}

		// Add to pipeline
		pipe.Set(c.ctx, fullKey, string(entryData), ttl)
	}

	// Execute pipeline
	_, err := pipe.Exec(c.ctx)
	if err != nil {
		c.logger.Error("Failed to execute MSet pipeline", zap.Error(err))
		return fmt.Errorf("failed to execute MSet pipeline: %w", err)
	}

	c.logger.Debug("MSet completed", zap.Int("count", len(entries)))
	return nil
}

// Exists checks if a key exists in cache
func (c *CacheService) Exists(key string) (bool, error) {
	fullKey := c.buildKey(key)
	return c.redis.Exists(fullKey)
}

// Expire sets an expiration time for a key
func (c *CacheService) Expire(key string, ttl time.Duration) error {
	fullKey := c.buildKey(key)
	return c.redis.Expire(fullKey, ttl)
}

// Clear removes all cache entries
func (c *CacheService) Clear() error {
	return c.InvalidatePattern("*")
}

// GetStats returns cache statistics
func (c *CacheService) GetStats() (*CacheStats, error) {
	// Get Redis pool stats
	poolStats := c.redis.GetStats()

	// Count total keys
	pattern := c.buildKey("*")
	var totalKeys int64
	var cursor uint64
	var err error

	for {
		var keys []string
		keys, cursor, err = c.redis.GetClient().Scan(c.ctx, cursor, pattern, 1000).Result()
		if err != nil {
			c.logger.Error("Failed to scan for cache keys during stats", zap.Error(err))
			break
		}

		totalKeys += int64(len(keys))

		if cursor == 0 {
			break
		}
	}

	// Calculate hit rate
	var hitRate float64
	totalRequests := poolStats.Hits + poolStats.Misses
	if totalRequests > 0 {
		hitRate = float64(poolStats.Hits) / float64(totalRequests) * 100
	}

	stats := &CacheStats{
		Hits:      int64(poolStats.Hits),
		Misses:    int64(poolStats.Misses),
		HitRate:   hitRate,
		TotalKeys: totalKeys,
	}

	c.logger.Debug("Cache stats retrieved",
		zap.Int64("hits", stats.Hits),
		zap.Int64("misses", stats.Misses),
		zap.Float64("hit_rate", stats.HitRate),
		zap.Int64("total_keys", stats.TotalKeys),
	)

	return stats, nil
}

// HealthCheck performs a health check on the cache service
func (c *CacheService) HealthCheck() error {
	// Test basic operations
	testKey := "health_check_test"
	testValue := "test_value"
	testTTL := 10 * time.Second

	// Test set
	if err := c.Set(testKey, testValue, testTTL); err != nil {
		return fmt.Errorf("cache health check failed - set: %w", err)
	}

	// Test get
	value, err := c.Get(testKey)
	if err != nil {
		return fmt.Errorf("cache health check failed - get: %w", err)
	}

	if value != testValue {
		return fmt.Errorf("cache health check failed - value mismatch: expected %s, got %v", testValue, value)
	}

	// Test exists
	exists, err := c.Exists(testKey)
	if err != nil {
		return fmt.Errorf("cache health check failed - exists: %w", err)
	}

	if !exists {
		return fmt.Errorf("cache health check failed - key should exist")
	}

	// Clean up
	if err := c.Delete(testKey); err != nil {
		c.logger.Warn("Failed to clean up health check test key", zap.Error(err))
	}

	c.logger.Debug("Cache health check passed")
	return nil
}

// buildKey builds a full cache key with prefix
func (c *CacheService) buildKey(key string) string {
	return "arx:cache:" + key
}

// updateEntry updates a cache entry with new access statistics
func (c *CacheService) updateEntry(fullKey string, entry CacheEntry) error {
	// Marshal updated entry
	entryData, err := json.Marshal(entry)
	if err != nil {
		return err
	}

	// Get current TTL
	ttl, err := c.redis.TTL(fullKey)
	if err != nil {
		return err
	}

	// Update entry with same TTL
	return c.redis.Set(fullKey, string(entryData), ttl)
}

// GetCacheEntry retrieves the full cache entry with metadata
func (c *CacheService) GetCacheEntry(key string) (*CacheEntry, error) {
	fullKey := c.buildKey(key)

	rawValue, err := c.redis.Get(fullKey)
	if err != nil {
		return nil, fmt.Errorf("failed to get cache entry for key %s: %w", key, err)
	}

	if rawValue == "" {
		return nil, nil
	}

	var entry CacheEntry
	if err := json.Unmarshal([]byte(rawValue), &entry); err != nil {
		return nil, fmt.Errorf("failed to unmarshal cache entry for key %s: %w", key, err)
	}

	// Check if entry has expired
	if time.Now().After(entry.ExpiresAt) {
		c.Delete(key) // Clean up expired entry
		return nil, nil
	}

	return &entry, nil
}

// Close closes the cache service and underlying Redis connection
func (c *CacheService) Close() error {
	return c.redis.Close()
}
