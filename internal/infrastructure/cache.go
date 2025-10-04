package infrastructure

import (
	"context"
	"encoding/json"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
)

// Cache implements the cache interface following Clean Architecture
type Cache struct {
	config *config.Config
	imc    *InMemoryCache
}

// NewCache creates a new cache instance
func NewCache(cfg *config.Config) (domain.Cache, error) {
	cache := &Cache{
		config: cfg,
		imc:    NewInMemoryCache().(*InMemoryCache),
	}

	return cache, nil
}

// Get retrieves a value from cache
func (c *Cache) Get(ctx context.Context, key string) (interface{}, error) {
	return c.imc.Get(ctx, key)
}

// Set stores a value in cache with TTL
func (c *Cache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	return c.imc.Set(ctx, key, value, ttl)
}

// Delete removes a value from cache
func (c *Cache) Delete(ctx context.Context, key string) error {
	return c.imc.Delete(ctx, key)
}

// Clear removes all values from cache
func (c *Cache) Clear(ctx context.Context) error {
	return c.imc.Clear(ctx)
}

// Close closes the cache connection
func (c *Cache) Close() error {
	return c.imc.Close()
}

// Helper methods for serialization

// serialize converts a value to JSON bytes
func (c *Cache) serialize(value interface{}) ([]byte, error) {
	return json.Marshal(value)
}

// deserialize converts JSON bytes to a value
func (c *Cache) deserialize(data []byte, value interface{}) error {
	return json.Unmarshal(data, value)
}

// RedisCache extends Cache with Redis-specific functionality
type RedisCache struct {
	*Cache
}

// NewRedisCache creates a new Redis cache instance
func NewRedisCache(cfg *config.Config) (domain.Cache, error) {
	baseCache, err := NewCache(cfg)
	if err != nil {
		return nil, err
	}

	return &RedisCache{
		Cache: baseCache.(*Cache),
	}, nil
}

// SetWithTags stores a value with tags for cache invalidation
func (rc *RedisCache) SetWithTags(ctx context.Context, key string, value interface{}, ttl time.Duration, tags []string) error {
	// TODO: Implement Redis-specific set with tags logic
	return nil
}

// InvalidateByTags removes all keys with specified tags
func (rc *RedisCache) InvalidateByTags(ctx context.Context, tags []string) error {
	// TODO: Implement Redis-specific tag invalidation logic
	return nil
}

// InMemoryCache implements an in-memory cache for development/testing
type InMemoryCache struct {
	data map[string]cacheEntry
	mu   sync.RWMutex
}

type cacheEntry struct {
	value     interface{}
	expiresAt time.Time
}

// NewInMemoryCache creates a new in-memory cache instance
func NewInMemoryCache() domain.Cache {
	return &InMemoryCache{
		data: make(map[string]cacheEntry),
	}
}

// Get retrieves a value from in-memory cache
func (imc *InMemoryCache) Get(ctx context.Context, key string) (interface{}, error) {
	imc.mu.RLock()
	entry, exists := imc.data[key]
	imc.mu.RUnlock()

	if !exists {
		return nil, nil // Cache miss
	}

	// Check if expired
	if time.Now().After(entry.expiresAt) {
		imc.mu.Lock()
		delete(imc.data, key)
		imc.mu.Unlock()
		return nil, nil // Cache miss
	}

	return entry.value, nil
}

// Set stores a value in in-memory cache with TTL
func (imc *InMemoryCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	imc.mu.Lock()
	defer imc.mu.Unlock()

	imc.data[key] = cacheEntry{
		value:     value,
		expiresAt: time.Now().Add(ttl),
	}
	return nil
}

// Delete removes a value from in-memory cache
func (imc *InMemoryCache) Delete(ctx context.Context, key string) error {
	imc.mu.Lock()
	defer imc.mu.Unlock()

	delete(imc.data, key)
	return nil
}

// Clear removes all values from in-memory cache
func (imc *InMemoryCache) Clear(ctx context.Context) error {
	imc.mu.Lock()
	defer imc.mu.Unlock()

	imc.data = make(map[string]cacheEntry)
	return nil
}

// Close is a no-op for in-memory cache
func (imc *InMemoryCache) Close() error {
	return nil
}
