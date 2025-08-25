package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"
)

// CacheService provides a high-level caching abstraction
// This adapter allows seamless transition from Redis to PostgreSQL
type CacheService struct {
	postgres *PostgresCacheService
	logger   *log.Logger
	ctx      context.Context
	config   *CacheConfig
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

// NewCacheService creates a new cache service using PostgreSQL backend
func NewCacheService(config *CacheConfig, logger *log.Logger) (*CacheService, error) {
	if config == nil {
		config = DefaultCacheConfig()
	}

	// Create PostgreSQL cache service
	pgCache, err := NewPostgresCacheService(config, logger)
	if err != nil {
		return nil, fmt.Errorf("failed to create PostgreSQL cache service: %w", err)
	}

	service := &CacheService{
		postgres: pgCache,
		logger:   logger,
		ctx:      context.Background(),
		config:   config,
	}

	if logger != nil {
		logger.Printf("Cache service initialized with PostgreSQL backend - default_ttl: %v, max_ttl: %v, key_prefix: %s",
			config.DefaultTTL, config.MaxTTL, config.KeyPrefix)
	}

	return service, nil
}

// Get retrieves a value from cache
func (c *CacheService) Get(key string) (interface{}, error) {
	rawValue, err := c.postgres.Get(key)
	if err != nil {
		return nil, err
	}

	if rawValue == "" {
		if c.logger != nil {
			c.logger.Printf("DEBUG: Cache miss - key not found: %s", key)
		}
		return nil, nil
	}

	// Try to unmarshal as CacheEntry for compatibility
	var entry CacheEntry
	if err := json.Unmarshal([]byte(rawValue), &entry); err == nil {
		// Check if entry is expired
		if time.Now().After(entry.ExpiresAt) {
			if c.logger != nil {
				c.logger.Printf("DEBUG: Cache entry expired - key: %s", key)
			}
			c.postgres.Delete(key)
			return nil, nil
		}
		return entry.Value, nil
	}

	// Return raw value if not a CacheEntry
	return rawValue, nil
}

// Set stores a value in cache with TTL
func (c *CacheService) Set(key string, value interface{}, ttl time.Duration) error {
	// Validate TTL
	if ttl <= 0 {
		ttl = c.config.DefaultTTL
	}
	if ttl > c.config.MaxTTL {
		ttl = c.config.MaxTTL
	}

	// Create cache entry
	entry := CacheEntry{
		Value:      value,
		CreatedAt:  time.Now(),
		ExpiresAt:  time.Now().Add(ttl),
		LastAccess: time.Now(),
	}

	// Store in PostgreSQL
	return c.postgres.Set(key, entry, ttl)
}

// Delete removes a key from cache
func (c *CacheService) Delete(key string) error {
	return c.postgres.Delete(key)
}

// InvalidatePattern removes all keys matching a pattern
func (c *CacheService) InvalidatePattern(pattern string) error {
	return c.postgres.InvalidatePattern(pattern)
}

// Exists checks if a key exists
func (c *CacheService) Exists(key string) (bool, error) {
	return c.postgres.Exists(key)
}

// Expire sets a new expiration time for a key
func (c *CacheService) Expire(key string, expiration time.Duration) error {
	return c.postgres.Expire(key, expiration)
}

// TTL gets the remaining time to live for a key
func (c *CacheService) TTL(key string) (time.Duration, error) {
	return c.postgres.TTL(key)
}

// GetStats returns cache statistics
func (c *CacheService) GetStats() (*CacheStats, error) {
	return c.postgres.GetStats()
}

// Incr increments a counter
func (c *CacheService) Incr(key string) (int64, error) {
	return c.postgres.Incr(key)
}

// IncrBy increments a counter by a specific amount
func (c *CacheService) IncrBy(key string, value int64) (int64, error) {
	return c.postgres.IncrBy(key, value)
}

// HGet retrieves a field from a hash
func (c *CacheService) HGet(key, field string) (string, error) {
	return c.postgres.HGet(key, field)
}

// HSet sets a field in a hash
func (c *CacheService) HSet(key, field string, value interface{}) error {
	return c.postgres.HSet(key, field, value)
}

// HGetAll retrieves all fields from a hash
func (c *CacheService) HGetAll(key string) (map[string]string, error) {
	return c.postgres.HGetAll(key)
}

// Close closes the cache service
func (c *CacheService) Close() error {
	return c.postgres.Close()
}

// HealthCheck performs a health check
func (c *CacheService) HealthCheck() error {
	return c.postgres.HealthCheck()
}

// GetClient returns nil (no Redis client)
func (c *CacheService) GetClient() interface{} {
	return nil
}

// buildKey constructs the full cache key with prefix
func (c *CacheService) buildKey(key string) string {
	if c.config.KeyPrefix != "" {
		return c.config.KeyPrefix + key
	}
	return key
}

// Batch operations for performance

// MGet retrieves multiple values at once
func (c *CacheService) MGet(keys []string) (map[string]interface{}, error) {
	result := make(map[string]interface{})
	
	for _, key := range keys {
		value, err := c.Get(key)
		if err != nil {
			if c.logger != nil {
				c.logger.Printf("WARN: Failed to get key %s in batch: %v", key, err)
			}
			continue
		}
		if value != nil {
			result[key] = value
		}
	}
	
	return result, nil
}

// MSet sets multiple key-value pairs at once
func (c *CacheService) MSet(items map[string]interface{}, ttl time.Duration) error {
	for key, value := range items {
		if err := c.Set(key, value, ttl); err != nil {
			return fmt.Errorf("failed to set key %s in batch: %w", key, err)
		}
	}
	return nil
}

// Touch updates the last access time of a key
func (c *CacheService) Touch(key string) error {
	// This is handled automatically in PostgreSQL implementation
	_, err := c.postgres.Get(key)
	return err
}

// GetOrSet retrieves a value or sets it if not found
func (c *CacheService) GetOrSet(key string, ttl time.Duration, fetchFunc func() (interface{}, error)) (interface{}, error) {
	// Try to get from cache
	value, err := c.Get(key)
	if err != nil {
		return nil, err
	}
	
	if value != nil {
		return value, nil
	}
	
	// Fetch new value
	newValue, err := fetchFunc()
	if err != nil {
		return nil, fmt.Errorf("fetch function failed: %w", err)
	}
	
	// Store in cache
	if err := c.Set(key, newValue, ttl); err != nil {
		// Log error but return value anyway
		if c.logger != nil {
			c.logger.Printf("WARN: Failed to cache value for key %s: %v", key, err)
		}
	}
	
	return newValue, nil
}

// Clear removes all entries of a specific type
func (c *CacheService) Clear(cacheType string) error {
	pattern := fmt.Sprintf("%s%s:*", c.config.KeyPrefix, cacheType)
	return c.InvalidatePattern(pattern)
}

// GetContext returns the service context
func (c *CacheService) GetContext() context.Context {
	return c.ctx
}