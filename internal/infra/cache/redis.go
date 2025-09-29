package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/redis/go-redis/v9"
)

// RedisService implements the cache interface using Redis
type RedisService struct {
	client  *redis.Client
	mu      sync.RWMutex
	healthy bool
	stats   map[string]interface{}
}

// NewRedisService creates a new Redis cache service
func NewRedisService() *RedisService {
	return &RedisService{
		healthy: false,
		stats:   make(map[string]interface{}),
	}
}

// Connect establishes a connection to Redis
func (r *RedisService) Connect(ctx context.Context, host string, port int, password string, db int) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.client != nil {
		return fmt.Errorf("Redis already connected")
	}

	// Create Redis client
	r.client = redis.NewClient(&redis.Options{
		Addr:         fmt.Sprintf("%s:%d", host, port),
		Password:     password,
		DB:           db,
		PoolSize:     10,
		MinIdleConns: 5,
		MaxRetries:   3,
		DialTimeout:  5 * time.Second,
		ReadTimeout:  3 * time.Second,
		WriteTimeout: 3 * time.Second,
	})

	// Test connection
	if err := r.client.Ping(ctx).Err(); err != nil {
		r.client = nil
		return fmt.Errorf("failed to connect to Redis: %w", err)
	}

	r.healthy = true
	r.updateStats()
	logger.Info("Connected to Redis at %s:%d", host, port)
	return nil
}

// Disconnect closes the Redis connection
func (r *RedisService) Disconnect(ctx context.Context) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.client == nil {
		return nil
	}

	if err := r.client.Close(); err != nil {
		return fmt.Errorf("failed to close Redis connection: %w", err)
	}

	r.client = nil
	r.healthy = false
	logger.Info("Disconnected from Redis")
	return nil
}

// Get retrieves a value from the cache
func (r *RedisService) Get(ctx context.Context, key string) (interface{}, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return nil, fmt.Errorf("Redis not connected")
	}

	val, err := r.client.Get(ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, fmt.Errorf("key not found: %s", key)
		}
		return nil, fmt.Errorf("failed to get key %s: %w", key, err)
	}

	// Try to unmarshal as JSON first
	var result interface{}
	if err := json.Unmarshal([]byte(val), &result); err != nil {
		// If not JSON, return as string
		return val, nil
	}

	return result, nil
}

// Set stores a value in the cache
func (r *RedisService) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return fmt.Errorf("Redis not connected")
	}

	// Marshal value to JSON
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("failed to marshal value: %w", err)
	}

	if err := r.client.Set(ctx, key, data, ttl).Err(); err != nil {
		return fmt.Errorf("failed to set key %s: %w", key, err)
	}

	return nil
}

// Delete removes a key from the cache
func (r *RedisService) Delete(ctx context.Context, key string) error {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return fmt.Errorf("Redis not connected")
	}

	if err := r.client.Del(ctx, key).Err(); err != nil {
		return fmt.Errorf("failed to delete key %s: %w", key, err)
	}

	return nil
}

// Exists checks if a key exists in the cache
func (r *RedisService) Exists(ctx context.Context, key string) (bool, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return false, fmt.Errorf("Redis not connected")
	}

	count, err := r.client.Exists(ctx, key).Result()
	if err != nil {
		return false, fmt.Errorf("failed to check existence of key %s: %w", key, err)
	}

	return count > 0, nil
}

// GetMultiple retrieves multiple values from the cache
func (r *RedisService) GetMultiple(ctx context.Context, keys []string) (map[string]interface{}, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return nil, fmt.Errorf("Redis not connected")
	}

	if len(keys) == 0 {
		return make(map[string]interface{}), nil
	}

	vals, err := r.client.MGet(ctx, keys...).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to get multiple keys: %w", err)
	}

	result := make(map[string]interface{})
	for i, val := range vals {
		if val != nil {
			// Try to unmarshal as JSON first
			var parsed interface{}
			if err := json.Unmarshal([]byte(val.(string)), &parsed); err != nil {
				// If not JSON, use as string
				result[keys[i]] = val
			} else {
				result[keys[i]] = parsed
			}
		}
	}

	return result, nil
}

// SetMultiple stores multiple values in the cache
func (r *RedisService) SetMultiple(ctx context.Context, items map[string]interface{}, ttl time.Duration) error {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return fmt.Errorf("Redis not connected")
	}

	if len(items) == 0 {
		return nil
	}

	pipe := r.client.Pipeline()
	for key, value := range items {
		data, err := json.Marshal(value)
		if err != nil {
			return fmt.Errorf("failed to marshal value for key %s: %w", key, err)
		}
		pipe.Set(ctx, key, data, ttl)
	}

	if _, err := pipe.Exec(ctx); err != nil {
		return fmt.Errorf("failed to set multiple keys: %w", err)
	}

	return nil
}

// DeleteMultiple removes multiple keys from the cache
func (r *RedisService) DeleteMultiple(ctx context.Context, keys []string) error {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return fmt.Errorf("Redis not connected")
	}

	if len(keys) == 0 {
		return nil
	}

	if err := r.client.Del(ctx, keys...).Err(); err != nil {
		return fmt.Errorf("failed to delete multiple keys: %w", err)
	}

	return nil
}

// Increment increments a numeric value in the cache
func (r *RedisService) Increment(ctx context.Context, key string, delta int64) (int64, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return 0, fmt.Errorf("Redis not connected")
	}

	val, err := r.client.IncrBy(ctx, key, delta).Result()
	if err != nil {
		return 0, fmt.Errorf("failed to increment key %s: %w", key, err)
	}

	return val, nil
}

// Decrement decrements a numeric value in the cache
func (r *RedisService) Decrement(ctx context.Context, key string, delta int64) (int64, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return 0, fmt.Errorf("Redis not connected")
	}

	val, err := r.client.DecrBy(ctx, key, delta).Result()
	if err != nil {
		return 0, fmt.Errorf("failed to decrement key %s: %w", key, err)
	}

	return val, nil
}

// Expire sets expiration time for a key
func (r *RedisService) Expire(ctx context.Context, key string, ttl time.Duration) error {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return fmt.Errorf("Redis not connected")
	}

	if err := r.client.Expire(ctx, key, ttl).Err(); err != nil {
		return fmt.Errorf("failed to set expiration for key %s: %w", key, err)
	}

	return nil
}

// Ping tests the Redis connection
func (r *RedisService) Ping() error {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return fmt.Errorf("Redis not connected")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := r.client.Ping(ctx).Err(); err != nil {
		r.healthy = false
		return fmt.Errorf("Redis ping failed: %w", err)
	}

	r.healthy = true
	return nil
}

// IsHealthy returns the health status of the Redis connection
func (r *RedisService) IsHealthy() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.healthy && r.client != nil
}

// GetStats returns Redis connection statistics
func (r *RedisService) GetStats() map[string]interface{} {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return map[string]interface{}{
			"status":  "disconnected",
			"healthy": false,
		}
	}

	// Update stats
	r.updateStats()
	return r.stats
}

// Clear clears all keys from the current database
func (r *RedisService) Clear(ctx context.Context) error {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return fmt.Errorf("Redis not connected")
	}

	if err := r.client.FlushDB(ctx).Err(); err != nil {
		return fmt.Errorf("failed to clear database: %w", err)
	}

	return nil
}

// ClearPattern removes keys matching a pattern
func (r *RedisService) ClearPattern(ctx context.Context, pattern string) error {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.client == nil {
		return fmt.Errorf("Redis not connected")
	}

	keys, err := r.client.Keys(ctx, pattern).Result()
	if err != nil {
		return fmt.Errorf("failed to get keys matching pattern %s: %w", pattern, err)
	}

	if len(keys) > 0 {
		if err := r.client.Del(ctx, keys...).Err(); err != nil {
			return fmt.Errorf("failed to delete keys matching pattern %s: %w", pattern, err)
		}
	}

	return nil
}

// updateStats updates the Redis statistics
func (r *RedisService) updateStats() {
	if r.client == nil {
		r.stats = map[string]interface{}{
			"status":  "disconnected",
			"healthy": false,
		}
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	info, err := r.client.Info(ctx).Result()
	if err != nil {
		r.stats = map[string]interface{}{
			"status":  "connected",
			"healthy": r.healthy,
			"error":   err.Error(),
		}
		return
	}

	// Parse basic info
	stats := map[string]interface{}{
		"status":  "connected",
		"healthy": r.healthy,
	}

	// Parse Redis info
	lines := strings.Split(info, "\n")
	for _, line := range lines {
		if strings.Contains(line, ":") && !strings.HasPrefix(line, "#") {
			parts := strings.SplitN(line, ":", 2)
			if len(parts) == 2 {
				key := strings.TrimSpace(parts[0])
				value := strings.TrimSpace(parts[1])

				switch key {
				case "redis_version":
					stats["redis_version"] = value
				case "connected_clients":
					stats["connected_clients"] = value
				case "used_memory_human":
					stats["used_memory"] = value
				case "uptime_in_seconds":
					stats["uptime_seconds"] = value
				}
			}
		}
	}

	r.stats = stats
}