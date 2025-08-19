// Package cache provides distributed caching functionality using Redis
package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/arxos/arxos/core/backend/config"
	"github.com/arxos/arxos/core/backend/errors"
	"github.com/go-redis/redis/v8"
	"go.uber.org/zap"
)

// CacheInterface defines the caching contract
type CacheInterface interface {
	Get(ctx context.Context, key string) ([]byte, error)
	Set(ctx context.Context, key string, value interface{}, expiration time.Duration) error
	Delete(ctx context.Context, key string) error
	Exists(ctx context.Context, key string) (bool, error)
	Expire(ctx context.Context, key string, expiration time.Duration) error
	GetPattern(ctx context.Context, pattern string) (map[string][]byte, error)
	DeletePattern(ctx context.Context, pattern string) error
	Increment(ctx context.Context, key string) (int64, error)
	Decrement(ctx context.Context, key string) (int64, error)
	SetHash(ctx context.Context, key string, field string, value interface{}) error
	GetHash(ctx context.Context, key string, field string) ([]byte, error)
	GetAllHash(ctx context.Context, key string) (map[string]string, error)
	Close() error
	Health(ctx context.Context) error
}

// RedisCache implements distributed caching using Redis
type RedisCache struct {
	client        *redis.Client
	clusterClient *redis.ClusterClient
	config        *config.RedisConfig
	logger        *zap.Logger
	isCluster     bool
	keyPrefix     string
	metrics       *CacheMetrics
}

// CacheMetrics tracks cache performance
type CacheMetrics struct {
	hits       int64
	misses     int64
	errors     int64
	operations int64
}

// NewRedisCache creates a new Redis cache instance
func NewRedisCache(cfg *config.RedisConfig, logger *zap.Logger) (*RedisCache, error) {
	cache := &RedisCache{
		config:    cfg,
		logger:    logger,
		keyPrefix: "arxos:",
		metrics:   &CacheMetrics{},
	}

	// Check if cluster mode is configured
	addresses := strings.Split(cfg.Host, ",")
	if len(addresses) > 1 {
		cache.isCluster = true
		cache.clusterClient = redis.NewClusterClient(&redis.ClusterOptions{
			Addrs:              addresses,
			Password:           cfg.Password,
			MaxRetries:         cfg.MaxRetries,
			MinRetryBackoff:    cfg.MinRetryBackoff,
			MaxRetryBackoff:    cfg.MaxRetryBackoff,
			DialTimeout:        cfg.DialTimeout,
			ReadTimeout:        cfg.ReadTimeout,
			WriteTimeout:       cfg.WriteTimeout,
			PoolSize:           cfg.PoolSize,
			MinIdleConns:       cfg.MinIdleConns,
			MaxConnAge:         cfg.MaxConnAge,
			PoolTimeout:        cfg.PoolTimeout,
			IdleTimeout:        cfg.IdleTimeout,
			IdleCheckFrequency: cfg.IdleCheckFrequency,
		})
	} else {
		cache.client = redis.NewClient(&redis.Options{
			Addr:               fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
			Password:           cfg.Password,
			DB:                 cfg.Database,
			MaxRetries:         cfg.MaxRetries,
			MinRetryBackoff:    cfg.MinRetryBackoff,
			MaxRetryBackoff:    cfg.MaxRetryBackoff,
			DialTimeout:        cfg.DialTimeout,
			ReadTimeout:        cfg.ReadTimeout,
			WriteTimeout:       cfg.WriteTimeout,
			PoolSize:           cfg.PoolSize,
			MinIdleConns:       cfg.MinIdleConns,
			MaxConnAge:         cfg.MaxConnAge,
			PoolTimeout:        cfg.PoolTimeout,
			IdleTimeout:        cfg.IdleTimeout,
			IdleCheckFrequency: cfg.IdleCheckFrequency,
		})
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := cache.Health(ctx); err != nil {
		return nil, errors.NewExternalError("redis", fmt.Sprintf("Failed to connect: %v", err))
	}

	logger.Info("Redis cache initialized successfully",
		zap.Bool("cluster_mode", cache.isCluster),
		zap.String("address", cfg.Host),
		zap.Int("database", cfg.Database))

	return cache, nil
}

// Get retrieves a value from cache
func (r *RedisCache) Get(ctx context.Context, key string) ([]byte, error) {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var result *redis.StringCmd
	
	if r.isCluster {
		result = r.clusterClient.Get(ctx, fullKey)
	} else {
		result = r.client.Get(ctx, fullKey)
	}
	
	value, err := result.Bytes()
	if err != nil {
		if err == redis.Nil {
			r.metrics.misses++
			return nil, errors.NewNotFoundError("cache key")
		}
		r.metrics.errors++
		r.logger.Error("Cache get error", zap.String("key", key), zap.Error(err))
		return nil, errors.NewExternalError("redis", err.Error())
	}
	
	r.metrics.hits++
	return value, nil
}

// Set stores a value in cache with expiration
func (r *RedisCache) Set(ctx context.Context, key string, value interface{}, expiration time.Duration) error {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var serialized []byte
	var err error
	
	// Serialize value
	switch v := value.(type) {
	case []byte:
		serialized = v
	case string:
		serialized = []byte(v)
	default:
		serialized, err = json.Marshal(value)
		if err != nil {
			r.metrics.errors++
			return errors.NewInternalError(fmt.Sprintf("Failed to serialize cache value: %v", err))
		}
	}
	
	var result *redis.StatusCmd
	if r.isCluster {
		result = r.clusterClient.Set(ctx, fullKey, serialized, expiration)
	} else {
		result = r.client.Set(ctx, fullKey, serialized, expiration)
	}
	
	if err := result.Err(); err != nil {
		r.metrics.errors++
		r.logger.Error("Cache set error", zap.String("key", key), zap.Error(err))
		return errors.NewExternalError("redis", err.Error())
	}
	
	return nil
}

// Delete removes a key from cache
func (r *RedisCache) Delete(ctx context.Context, key string) error {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var result *redis.IntCmd
	
	if r.isCluster {
		result = r.clusterClient.Del(ctx, fullKey)
	} else {
		result = r.client.Del(ctx, fullKey)
	}
	
	if err := result.Err(); err != nil {
		r.metrics.errors++
		r.logger.Error("Cache delete error", zap.String("key", key), zap.Error(err))
		return errors.NewExternalError("redis", err.Error())
	}
	
	return nil
}

// Exists checks if a key exists in cache
func (r *RedisCache) Exists(ctx context.Context, key string) (bool, error) {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var result *redis.IntCmd
	
	if r.isCluster {
		result = r.clusterClient.Exists(ctx, fullKey)
	} else {
		result = r.client.Exists(ctx, fullKey)
	}
	
	count, err := result.Result()
	if err != nil {
		r.metrics.errors++
		r.logger.Error("Cache exists error", zap.String("key", key), zap.Error(err))
		return false, errors.NewExternalError("redis", err.Error())
	}
	
	return count > 0, nil
}

// Expire sets expiration for a key
func (r *RedisCache) Expire(ctx context.Context, key string, expiration time.Duration) error {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var result *redis.BoolCmd
	
	if r.isCluster {
		result = r.clusterClient.Expire(ctx, fullKey, expiration)
	} else {
		result = r.client.Expire(ctx, fullKey, expiration)
	}
	
	if err := result.Err(); err != nil {
		r.metrics.errors++
		r.logger.Error("Cache expire error", zap.String("key", key), zap.Error(err))
		return errors.NewExternalError("redis", err.Error())
	}
	
	return nil
}

// GetPattern retrieves all keys matching a pattern
func (r *RedisCache) GetPattern(ctx context.Context, pattern string) (map[string][]byte, error) {
	r.metrics.operations++
	
	fullPattern := r.keyPrefix + pattern
	result := make(map[string][]byte)
	
	var keys []string
	var err error
	
	if r.isCluster {
		// For cluster, we need to scan all nodes
		err = r.clusterClient.ForEachMaster(ctx, func(ctx context.Context, client *redis.Client) error {
			nodeKeys, err := client.Keys(ctx, fullPattern).Result()
			if err != nil {
				return err
			}
			keys = append(keys, nodeKeys...)
			return nil
		})
	} else {
		keys, err = r.client.Keys(ctx, fullPattern).Result()
	}
	
	if err != nil {
		r.metrics.errors++
		r.logger.Error("Cache pattern scan error", zap.String("pattern", pattern), zap.Error(err))
		return nil, errors.NewExternalError("redis", err.Error())
	}
	
	// Get values for all keys
	for _, key := range keys {
		value, err := r.Get(ctx, strings.TrimPrefix(key, r.keyPrefix))
		if err != nil {
			continue // Skip errors for individual keys
		}
		result[strings.TrimPrefix(key, r.keyPrefix)] = value
	}
	
	return result, nil
}

// DeletePattern deletes all keys matching a pattern
func (r *RedisCache) DeletePattern(ctx context.Context, pattern string) error {
	r.metrics.operations++
	
	fullPattern := r.keyPrefix + pattern
	var keys []string
	var err error
	
	if r.isCluster {
		// For cluster, we need to scan all nodes
		err = r.clusterClient.ForEachMaster(ctx, func(ctx context.Context, client *redis.Client) error {
			nodeKeys, err := client.Keys(ctx, fullPattern).Result()
			if err != nil {
				return err
			}
			keys = append(keys, nodeKeys...)
			return nil
		})
	} else {
		keys, err = r.client.Keys(ctx, fullPattern).Result()
	}
	
	if err != nil {
		r.metrics.errors++
		r.logger.Error("Cache pattern delete scan error", zap.String("pattern", pattern), zap.Error(err))
		return errors.NewExternalError("redis", err.Error())
	}
	
	if len(keys) == 0 {
		return nil
	}
	
	// Delete all keys
	var result *redis.IntCmd
	if r.isCluster {
		result = r.clusterClient.Del(ctx, keys...)
	} else {
		result = r.client.Del(ctx, keys...)
	}
	
	if err := result.Err(); err != nil {
		r.metrics.errors++
		r.logger.Error("Cache pattern delete error", zap.String("pattern", pattern), zap.Error(err))
		return errors.NewExternalError("redis", err.Error())
	}
	
	return nil
}

// Increment atomically increments a counter
func (r *RedisCache) Increment(ctx context.Context, key string) (int64, error) {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var result *redis.IntCmd
	
	if r.isCluster {
		result = r.clusterClient.Incr(ctx, fullKey)
	} else {
		result = r.client.Incr(ctx, fullKey)
	}
	
	value, err := result.Result()
	if err != nil {
		r.metrics.errors++
		r.logger.Error("Cache increment error", zap.String("key", key), zap.Error(err))
		return 0, errors.NewExternalError("redis", err.Error())
	}
	
	return value, nil
}

// Decrement atomically decrements a counter
func (r *RedisCache) Decrement(ctx context.Context, key string) (int64, error) {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var result *redis.IntCmd
	
	if r.isCluster {
		result = r.clusterClient.Decr(ctx, fullKey)
	} else {
		result = r.client.Decr(ctx, fullKey)
	}
	
	value, err := result.Result()
	if err != nil {
		r.metrics.errors++
		r.logger.Error("Cache decrement error", zap.String("key", key), zap.Error(err))
		return 0, errors.NewExternalError("redis", err.Error())
	}
	
	return value, nil
}

// SetHash sets a field in a hash
func (r *RedisCache) SetHash(ctx context.Context, key string, field string, value interface{}) error {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var serialized string
	
	// Serialize value
	switch v := value.(type) {
	case string:
		serialized = v
	default:
		data, err := json.Marshal(value)
		if err != nil {
			r.metrics.errors++
			return errors.NewInternalError(fmt.Sprintf("Failed to serialize hash value: %v", err))
		}
		serialized = string(data)
	}
	
	var result *redis.IntCmd
	if r.isCluster {
		result = r.clusterClient.HSet(ctx, fullKey, field, serialized)
	} else {
		result = r.client.HSet(ctx, fullKey, field, serialized)
	}
	
	if err := result.Err(); err != nil {
		r.metrics.errors++
		r.logger.Error("Cache hash set error", zap.String("key", key), zap.String("field", field), zap.Error(err))
		return errors.NewExternalError("redis", err.Error())
	}
	
	return nil
}

// GetHash gets a field from a hash
func (r *RedisCache) GetHash(ctx context.Context, key string, field string) ([]byte, error) {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var result *redis.StringCmd
	
	if r.isCluster {
		result = r.clusterClient.HGet(ctx, fullKey, field)
	} else {
		result = r.client.HGet(ctx, fullKey, field)
	}
	
	value, err := result.Bytes()
	if err != nil {
		if err == redis.Nil {
			r.metrics.misses++
			return nil, errors.NewNotFoundError("hash field")
		}
		r.metrics.errors++
		r.logger.Error("Cache hash get error", zap.String("key", key), zap.String("field", field), zap.Error(err))
		return nil, errors.NewExternalError("redis", err.Error())
	}
	
	r.metrics.hits++
	return value, nil
}

// GetAllHash gets all fields from a hash
func (r *RedisCache) GetAllHash(ctx context.Context, key string) (map[string]string, error) {
	r.metrics.operations++
	
	fullKey := r.keyPrefix + key
	var result *redis.StringStringMapCmd
	
	if r.isCluster {
		result = r.clusterClient.HGetAll(ctx, fullKey)
	} else {
		result = r.client.HGetAll(ctx, fullKey)
	}
	
	value, err := result.Result()
	if err != nil {
		r.metrics.errors++
		r.logger.Error("Cache hash get all error", zap.String("key", key), zap.Error(err))
		return nil, errors.NewExternalError("redis", err.Error())
	}
	
	return value, nil
}

// Health checks Redis connectivity
func (r *RedisCache) Health(ctx context.Context) error {
	var err error
	
	if r.isCluster {
		err = r.clusterClient.Ping(ctx).Err()
	} else {
		err = r.client.Ping(ctx).Err()
	}
	
	if err != nil {
		return errors.NewExternalError("redis", fmt.Sprintf("Health check failed: %v", err))
	}
	
	return nil
}

// Close closes the Redis connection
func (r *RedisCache) Close() error {
	if r.isCluster {
		return r.clusterClient.Close()
	}
	return r.client.Close()
}

// GetMetrics returns cache performance metrics
func (r *RedisCache) GetMetrics() CacheMetrics {
	return *r.metrics
}

// GetStats returns detailed cache statistics
func (r *RedisCache) GetStats(ctx context.Context) (map[string]interface{}, error) {
	stats := make(map[string]interface{})
	
	// Basic metrics
	stats["hits"] = r.metrics.hits
	stats["misses"] = r.metrics.misses
	stats["errors"] = r.metrics.errors
	stats["operations"] = r.metrics.operations
	
	// Hit ratio
	if r.metrics.operations > 0 {
		stats["hit_ratio"] = float64(r.metrics.hits) / float64(r.metrics.hits+r.metrics.misses)
		stats["error_ratio"] = float64(r.metrics.errors) / float64(r.metrics.operations)
	}
	
	// Redis-specific stats
	var info *redis.StringCmd
	if r.isCluster {
		// For cluster, get info from first master
		r.clusterClient.ForEachMaster(ctx, func(ctx context.Context, client *redis.Client) error {
			info = client.Info(ctx, "memory", "stats")
			return nil // Break after first
		})
	} else {
		info = r.client.Info(ctx, "memory", "stats")
	}
	
	if info != nil && info.Err() == nil {
		infoStr := info.Val()
		lines := strings.Split(infoStr, "\r\n")
		for _, line := range lines {
			if strings.Contains(line, ":") && !strings.HasPrefix(line, "#") {
				parts := strings.SplitN(line, ":", 2)
				if len(parts) == 2 {
					stats["redis_"+parts[0]] = parts[1]
				}
			}
		}
	}
	
	return stats, nil
}

// GetRedisAddress returns the Redis address for configuration
func GetRedisAddress(cfg *config.RedisConfig) string {
	return fmt.Sprintf("%s:%d", cfg.Host, cfg.Port)
}

// CacheWarmupStrategy defines cache warming behavior
type CacheWarmupStrategy struct {
	Enabled     bool          `yaml:"enabled"`
	Schedule    string        `yaml:"schedule"`     // Cron expression
	BatchSize   int           `yaml:"batch_size"`
	Concurrency int           `yaml:"concurrency"`
	Timeout     time.Duration `yaml:"timeout"`
}

// CacheInvalidationStrategy defines cache invalidation behavior
type CacheInvalidationStrategy struct {
	OnUpdate    bool          `yaml:"on_update"`
	OnDelete    bool          `yaml:"on_delete"`
	TTLExtend   time.Duration `yaml:"ttl_extend"`
	BatchSize   int           `yaml:"batch_size"`
}

// Advanced caching patterns and strategies will be implemented in the confidence cache