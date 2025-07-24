package services

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// CacheLevel represents different cache levels
type CacheLevel string

const (
	LevelL1 CacheLevel = "L1" // Memory cache (fastest, limited size)
	LevelL2 CacheLevel = "L2" // Redis cache (fast, larger size)
	LevelL3 CacheLevel = "L3" // Disk cache (slower, unlimited size)
	LevelL4 CacheLevel = "L4" // Database cache (persistent, queryable)
)

// CachePolicy represents cache eviction policies
type CachePolicy string

const (
	PolicyLRU  CachePolicy = "lru"  // Least Recently Used
	PolicyLFU  CachePolicy = "lfu"  // Least Frequently Used
	PolicyTTL  CachePolicy = "ttl"  // Time To Live
	PolicyFIFO CachePolicy = "fifo" // First In First Out
)

// CacheService provides a high-level caching abstraction with multi-level caching
type CacheService struct {
	redis       *RedisService
	logger      *zap.Logger
	ctx         context.Context
	config      *CacheConfig
	memoryCache *MemoryCache
	diskCache   *DiskCache
	dbCache     *DatabaseCache
	strategies  *CacheStrategies
	metrics     *CacheMetrics
	mu          sync.RWMutex
}

// CacheConfig holds configuration for the cache service
type CacheConfig struct {
	DefaultTTL        time.Duration
	MaxTTL            time.Duration
	EnableMetrics     bool
	KeyPrefix         string
	MemoryCacheSize   int64 // MB
	DiskCacheSize     int64 // MB
	EnableCompression bool
	CacheLevels       []CacheLevel
	EvictionPolicy    CachePolicy
	WarmupEnabled     bool
}

// DefaultCacheConfig returns a default cache configuration
func DefaultCacheConfig() *CacheConfig {
	return &CacheConfig{
		DefaultTTL:        15 * time.Minute,
		MaxTTL:            24 * time.Hour,
		EnableMetrics:     true,
		KeyPrefix:         "arx:cache:",
		MemoryCacheSize:   100,  // 100MB
		DiskCacheSize:     1000, // 1GB
		EnableCompression: true,
		CacheLevels:       []CacheLevel{LevelL1, LevelL2, LevelL3, LevelL4},
		EvictionPolicy:    PolicyLRU,
		WarmupEnabled:     true,
	}
}

// CacheEntry represents a cached item with metadata
type CacheEntry struct {
	Value       interface{}            `json:"value"`
	CreatedAt   time.Time              `json:"created_at"`
	ExpiresAt   time.Time              `json:"expires_at"`
	AccessCount int64                  `json:"access_count"`
	LastAccess  time.Time              `json:"last_access"`
	SizeBytes   int64                  `json:"size_bytes"`
	Compressed  bool                   `json:"compressed"`
	Level       CacheLevel             `json:"level"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// CacheStats holds cache statistics
type CacheStats struct {
	Hits              int64
	Misses            int64
	HitRate           float64
	TotalKeys         int64
	MemoryUsage       int64
	CompressionRatio  float64
	AverageAccessTime float64
}

// NewCacheService creates a new enhanced cache service
func NewCacheService(redisService *RedisService, config *CacheConfig, logger *zap.Logger) *CacheService {
	if config == nil {
		config = DefaultCacheConfig()
	}

	service := &CacheService{
		redis:  redisService,
		logger: logger,
		ctx:    context.Background(),
		config: config,
	}

	// Initialize cache levels
	service.initializeCacheLevels()

	// Initialize strategies and metrics
	service.strategies = NewCacheStrategies(service, logger)
	service.metrics = NewCacheMetrics(service, logger)

	logger.Info("Enhanced cache service initialized",
		zap.Duration("default_ttl", config.DefaultTTL),
		zap.Duration("max_ttl", config.MaxTTL),
		zap.String("key_prefix", config.KeyPrefix),
		zap.Int64("memory_cache_size_mb", config.MemoryCacheSize),
		zap.Int64("disk_cache_size_mb", config.DiskCacheSize),
		zap.Bool("compression_enabled", config.EnableCompression),
	)

	return service
}

// initializeCacheLevels initializes all cache levels
func (c *CacheService) initializeCacheLevels() {
	// Initialize memory cache (L1)
	c.memoryCache = NewMemoryCache(c.config.MemoryCacheSize, c.config.EvictionPolicy, c.logger)

	// Initialize disk cache (L3)
	c.diskCache = NewDiskCache("cache", c.config.DiskCacheSize, c.logger)

	// Initialize database cache (L4)
	c.dbCache = NewDatabaseCache("cache.db", c.logger)
}

// Get retrieves a value from cache using multi-level strategy
func (c *CacheService) Get(key string) (interface{}, error) {
	startTime := time.Now()
	fullKey := c.buildKey(key)

	// Try each cache level in order
	for _, level := range c.config.CacheLevels {
		value, err := c.getFromLevel(key, fullKey, level)
		if err != nil {
			c.logger.Debug("Cache miss at level", zap.String("key", key), zap.String("level", string(level)), zap.Error(err))
			continue
		}

		if value != nil {
			// Cache hit - update metrics and promote to higher levels
			accessTime := time.Since(startTime)
			c.metrics.RecordHit(level, accessTime)
			c.promoteToHigherLevels(key, value, level)
			return value, nil
		}
	}

	// Cache miss
	c.metrics.RecordMiss()
	c.logger.Debug("Cache miss across all levels", zap.String("key", key))
	return nil, nil
}

// getFromLevel retrieves a value from a specific cache level
func (c *CacheService) getFromLevel(key, fullKey string, level CacheLevel) (interface{}, error) {
	switch level {
	case LevelL1:
		return c.memoryCache.Get(key)
	case LevelL2:
		return c.getFromRedis(fullKey)
	case LevelL3:
		return c.diskCache.Get(key)
	case LevelL4:
		return c.dbCache.Get(key)
	default:
		return nil, fmt.Errorf("unknown cache level: %s", level)
	}
}

// getFromRedis retrieves a value from Redis (L2)
func (c *CacheService) getFromRedis(fullKey string) (interface{}, error) {
	rawValue, err := c.redis.Get(fullKey)
	if err != nil {
		return nil, err
	}

	if rawValue == "" {
		return nil, nil
	}

	var entry CacheEntry
	if err := json.Unmarshal([]byte(rawValue), &entry); err != nil {
		return nil, err
	}

	// Check if entry has expired
	if time.Now().After(entry.ExpiresAt) {
		c.Delete(fullKey) // Clean up expired entry
		return nil, nil
	}

	// Update access statistics
	entry.AccessCount++
	entry.LastAccess = time.Now()

	// Update the entry in cache
	c.updateEntry(fullKey, entry)

	return entry.Value, nil
}

// Set stores a value in cache across all levels
func (c *CacheService) Set(key string, value interface{}, ttl time.Duration) error {
	fullKey := c.buildKey(key)

	// Validate TTL
	if ttl <= 0 {
		ttl = c.config.DefaultTTL
	}
	if ttl > c.config.MaxTTL {
		ttl = c.config.MaxTTL
	}

	// Create cache entry
	entry := CacheEntry{
		Value:       value,
		CreatedAt:   time.Now(),
		ExpiresAt:   time.Now().Add(ttl),
		AccessCount: 0,
		LastAccess:  time.Now(),
		Level:       LevelL1, // Start at L1
		Metadata:    make(map[string]interface{}),
	}

	// Store in all cache levels
	for _, level := range c.config.CacheLevels {
		if err := c.setInLevel(key, fullKey, entry, level, ttl); err != nil {
			c.logger.Warn("Failed to set in cache level", zap.String("key", key), zap.String("level", string(level)), zap.Error(err))
		}
	}

	c.logger.Debug("Cache entry set across all levels", zap.String("key", key), zap.Duration("ttl", ttl))
	return nil
}

// setInLevel stores a value in a specific cache level
func (c *CacheService) setInLevel(key, fullKey string, entry CacheEntry, level CacheLevel, ttl time.Duration) error {
	switch level {
	case LevelL1:
		return c.memoryCache.Set(key, entry.Value, ttl)
	case LevelL2:
		return c.setInRedis(fullKey, entry, ttl)
	case LevelL3:
		return c.diskCache.Set(key, entry.Value, ttl)
	case LevelL4:
		return c.dbCache.Set(key, entry.Value, ttl)
	default:
		return fmt.Errorf("unknown cache level: %s", level)
	}
}

// setInRedis stores a value in Redis (L2)
func (c *CacheService) setInRedis(fullKey string, entry CacheEntry, ttl time.Duration) error {
	entryData, err := json.Marshal(entry)
	if err != nil {
		return err
	}

	// Compress if enabled
	if c.config.EnableCompression {
		entryData = c.strategies.Compress(entryData)
		entry.Compressed = true
	}

	return c.redis.Set(fullKey, string(entryData), ttl)
}

// Delete removes a key from all cache levels
func (c *CacheService) Delete(key string) error {
	fullKey := c.buildKey(key)

	// Delete from all levels
	for _, level := range c.config.CacheLevels {
		switch level {
		case LevelL1:
			c.memoryCache.Delete(key)
		case LevelL2:
			c.redis.Delete(fullKey)
		case LevelL3:
			c.diskCache.Delete(key)
		case LevelL4:
			c.dbCache.Delete(key)
		}
	}

	c.logger.Debug("Cache entry deleted from all levels", zap.String("key", key))
	return nil
}

// InvalidatePattern removes all keys matching a pattern across all levels
func (c *CacheService) InvalidatePattern(pattern string) error {
	fullPattern := c.buildKey(pattern)

	// Invalidate from all levels
	for _, level := range c.config.CacheLevels {
		switch level {
		case LevelL1:
			c.memoryCache.InvalidatePattern(pattern)
		case LevelL2:
			c.invalidateRedisPattern(fullPattern)
		case LevelL3:
			c.diskCache.InvalidatePattern(pattern)
		case LevelL4:
			c.dbCache.InvalidatePattern(pattern)
		}
	}

	return nil
}

// invalidateRedisPattern removes Redis keys matching a pattern
func (c *CacheService) invalidateRedisPattern(pattern string) error {
	var keys []string
	var cursor uint64
	var err error

	for {
		keys, cursor, err = c.redis.GetClient().Scan(c.ctx, cursor, pattern, 100).Result()
		if err != nil {
			return err
		}

		if len(keys) > 0 {
			if err := c.redis.GetClient().Del(c.ctx, keys...).Err(); err != nil {
				return err
			}
		}

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
		return value, 0, nil
	}

	return value, ttl, nil
}

// SetWithMetadata stores a value with custom metadata
func (c *CacheService) SetWithMetadata(key string, value interface{}, ttl time.Duration, metadata map[string]interface{}) error {
	fullKey := c.buildKey(key)

	entry := CacheEntry{
		Value:       value,
		CreatedAt:   time.Now(),
		ExpiresAt:   time.Now().Add(ttl),
		AccessCount: 0,
		LastAccess:  time.Now(),
		Level:       LevelL1,
		Metadata:    metadata,
	}

	entryData := map[string]interface{}{
		"entry":    entry,
		"metadata": metadata,
	}

	data, err := json.Marshal(entryData)
	if err != nil {
		return err
	}

	return c.redis.Set(fullKey, string(data), ttl)
}

// GetOrSet retrieves a value from cache or sets it using a function
func (c *CacheService) GetOrSet(key string, ttl time.Duration, setter func() (interface{}, error)) (interface{}, error) {
	value, err := c.Get(key)
	if err != nil {
		c.logger.Warn("Failed to get from cache, will use setter", zap.String("key", key), zap.Error(err))
	} else if value != nil {
		return value, nil
	}

	value, err = setter()
	if err != nil {
		return nil, err
	}

	if err := c.Set(key, value, ttl); err != nil {
		c.logger.Warn("Failed to store value in cache", zap.String("key", key), zap.Error(err))
	}

	return value, nil
}

// MGet retrieves multiple values from cache
func (c *CacheService) MGet(keys ...string) (map[string]interface{}, error) {
	if len(keys) == 0 {
		return make(map[string]interface{}), nil
	}

	result := make(map[string]interface{})

	for _, key := range keys {
		value, err := c.Get(key)
		if err != nil {
			c.logger.Warn("Failed to get key in MGet", zap.String("key", key), zap.Error(err))
			continue
		}
		if value != nil {
			result[key] = value
		}
	}

	return result, nil
}

// MSet stores multiple values in cache
func (c *CacheService) MSet(entries map[string]interface{}, ttl time.Duration) error {
	for key, value := range entries {
		if err := c.Set(key, value, ttl); err != nil {
			c.logger.Warn("Failed to set key in MSet", zap.String("key", key), zap.Error(err))
		}
	}

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

// Clear removes all cache entries from all levels
func (c *CacheService) Clear() error {
	for _, level := range c.config.CacheLevels {
		switch level {
		case LevelL1:
			c.memoryCache.Clear()
		case LevelL2:
			c.Clear()
		case LevelL3:
			c.diskCache.Clear()
		case LevelL4:
			c.dbCache.Clear()
		}
	}

	return nil
}

// GetStats returns comprehensive cache statistics
func (c *CacheService) GetStats() (*CacheStats, error) {
	stats := &CacheStats{}

	// Get stats from all levels
	for _, level := range c.config.CacheLevels {
		levelStats := c.getLevelStats(level)
		stats.Hits += levelStats.Hits
		stats.Misses += levelStats.Misses
		stats.TotalKeys += levelStats.TotalKeys
		stats.MemoryUsage += levelStats.MemoryUsage
	}

	// Calculate overall hit rate
	totalRequests := stats.Hits + stats.Misses
	if totalRequests > 0 {
		stats.HitRate = float64(stats.Hits) / float64(totalRequests) * 100
	}

	// Get average access time from metrics
	stats.AverageAccessTime = c.metrics.GetAverageAccessTime()

	return stats, nil
}

// getLevelStats returns statistics for a specific cache level
func (c *CacheService) getLevelStats(level CacheLevel) *CacheStats {
	switch level {
	case LevelL1:
		return c.memoryCache.GetStats()
	case LevelL2:
		return c.getRedisStats()
	case LevelL3:
		return c.diskCache.GetStats()
	case LevelL4:
		return c.dbCache.GetStats()
	default:
		return &CacheStats{}
	}
}

// getRedisStats returns Redis cache statistics
func (c *CacheService) getRedisStats() *CacheStats {
	poolStats := c.redis.GetStats()
	return &CacheStats{
		Hits:   poolStats.Hits,
		Misses: poolStats.Misses,
	}
}

// HealthCheck performs a health check on the cache service
func (c *CacheService) HealthCheck() error {
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

	// Clean up
	c.Delete(testKey)

	return nil
}

// promoteToHigherLevels promotes a value to higher cache levels
func (c *CacheService) promoteToHigherLevels(key string, value interface{}, currentLevel CacheLevel) {
	// Find higher levels
	var higherLevels []CacheLevel
	for _, level := range c.config.CacheLevels {
		if level != currentLevel {
			higherLevels = append(higherLevels, level)
		}
	}

	// Promote to higher levels asynchronously
	go func() {
		for _, level := range higherLevels {
			switch level {
			case LevelL1:
				c.memoryCache.Set(key, value, c.config.DefaultTTL)
			case LevelL2:
				// Already in Redis
			case LevelL3:
				c.diskCache.Set(key, value, c.config.DefaultTTL)
			case LevelL4:
				c.dbCache.Set(key, value, c.config.DefaultTTL)
			}
		}
	}()
}

// buildKey builds a full cache key with prefix
func (c *CacheService) buildKey(key string) string {
	return c.config.KeyPrefix + key
}

// updateEntry updates a cache entry with new access statistics
func (c *CacheService) updateEntry(fullKey string, entry CacheEntry) error {
	entryData, err := json.Marshal(entry)
	if err != nil {
		return err
	}

	ttl, err := c.redis.TTL(fullKey)
	if err != nil {
		return err
	}

	return c.redis.Set(fullKey, string(entryData), ttl)
}

// GetCacheEntry retrieves the full cache entry with metadata
func (c *CacheService) GetCacheEntry(key string) (*CacheEntry, error) {
	fullKey := c.buildKey(key)

	rawValue, err := c.redis.Get(fullKey)
	if err != nil {
		return nil, err
	}

	if rawValue == "" {
		return nil, nil
	}

	var entry CacheEntry
	if err := json.Unmarshal([]byte(rawValue), &entry); err != nil {
		return nil, err
	}

	if time.Now().After(entry.ExpiresAt) {
		c.Delete(key)
		return nil, nil
	}

	return &entry, nil
}

// WarmCache warms the cache with common operations
func (c *CacheService) WarmCache(operations []CacheWarmupOperation) error {
	if !c.config.WarmupEnabled {
		return nil
	}

	c.logger.Info("Starting cache warmup", zap.Int("operations", len(operations)))

	for _, op := range operations {
		if err := c.strategies.WarmupOperation(op); err != nil {
			c.logger.Warn("Failed to warmup operation", zap.String("key", op.Key), zap.Error(err))
		}
	}

	return nil
}

// CacheWarmupOperation represents a cache warmup operation
type CacheWarmupOperation struct {
	Key         string
	Value       interface{}
	TTL         time.Duration
	Priority    int
	Description string
}

// Close closes the cache service and all underlying connections
func (c *CacheService) Close() error {
	c.memoryCache.Close()
	c.diskCache.Close()
	c.dbCache.Close()
	return c.redis.Close()
}
