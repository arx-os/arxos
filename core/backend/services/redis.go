package services

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/go-redis/redis/extra/redisotel/v8"
	"github.com/go-redis/redis/v8"
)

// RedisService provides Redis caching functionality with connection pooling and health checks
type RedisService struct {
	client *redis.Client
	ctx    context.Context
	logger *log.Logger
}

// RedisConfig holds configuration for Redis connection
type RedisConfig struct {
	Addr         string
	Password     string
	DB           int
	PoolSize     int
	MinIdleConns int
	MaxRetries   int
	DialTimeout  time.Duration
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration
}

// DefaultRedisConfig returns a default Redis configuration
func DefaultRedisConfig() *RedisConfig {
	return &RedisConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           0,
		PoolSize:     10,
		MinIdleConns: 5,
		MaxRetries:   3,
		DialTimeout:  5 * time.Second,
		ReadTimeout:  3 * time.Second,
		WriteTimeout: 3 * time.Second,
		IdleTimeout:  5 * time.Minute,
	}
}

// NewRedisService creates a new Redis service with the given configuration
func NewRedisService(config *RedisConfig, logger *log.Logger) (*RedisService, error) {
	if config == nil {
		config = DefaultRedisConfig()
	}

	// Create Redis client with connection pooling
	client := redis.NewClient(&redis.Options{
		Addr:         config.Addr,
		Password:     config.Password,
		DB:           config.DB,
		PoolSize:     config.PoolSize,
		MinIdleConns: config.MinIdleConns,
		MaxRetries:   config.MaxRetries,
		DialTimeout:  config.DialTimeout,
		ReadTimeout:  config.ReadTimeout,
		WriteTimeout: config.WriteTimeout,
		IdleTimeout:  config.IdleTimeout,
		// Enable connection pooling metrics
		OnConnect: func(ctx context.Context, cn *redis.Conn) error {
			if logger != nil {
				logger.Printf("DEBUG: Redis connection established - addr: %s", config.Addr)
			}
			return nil
		},
	})

	// Add OpenTelemetry instrumentation
	client.AddHook(redisotel.NewTracingHook())

	// Create service instance
	service := &RedisService{
		client: client,
		ctx:    context.Background(),
		logger: logger,
	}

	// Test connection
	if err := service.Ping(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	if logger != nil {
		logger.Printf("INFO: Redis service initialized successfully - addr: %s, pool_size: %d, min_idle_conns: %d",
			config.Addr, config.PoolSize, config.MinIdleConns)
	}

	return service, nil
}

// Ping tests the Redis connection
func (r *RedisService) Ping() error {
	ctx, cancel := context.WithTimeout(r.ctx, 5*time.Second)
	defer cancel()

	_, err := r.client.Ping(ctx).Result()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis ping failed - error: %v", err)
		}
		return fmt.Errorf("redis ping failed: %w", err)
	}

	return nil
}

// Get retrieves a value from Redis
func (r *RedisService) Get(key string) (string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.Get(ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			if r.logger != nil {
				r.logger.Printf("DEBUG: Redis key not found - key: %s", key)
			}
			return "", nil
		}
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis get failed - key: %s, error: %v", key, err)
		}
		return "", fmt.Errorf("redis get failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis get successful - key: %s", key)
	}
	return val, nil
}

// Set stores a value in Redis with optional expiration
func (r *RedisService) Set(key string, value interface{}, expiration time.Duration) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.Set(ctx, key, value, expiration).Err()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis set failed - key: %s, error: %v", key, err)
		}
		return fmt.Errorf("redis set failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis set successful - key: %s, expiration: %v", key, expiration)
	}
	return nil
}

// Delete removes a key from Redis
func (r *RedisService) Delete(key string) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.Del(ctx, key).Err()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis delete failed - key: %s, error: %v", key, err)
		}
		return fmt.Errorf("redis delete failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis delete successful - key: %s", key)
	}
	return nil
}

// Exists checks if a key exists in Redis
func (r *RedisService) Exists(key string) (bool, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	result, err := r.client.Exists(ctx, key).Result()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis exists check failed - key: %s, error: %v", key, err)
		}
		return false, fmt.Errorf("redis exists check failed for key %s: %w", key, err)
	}

	exists := result > 0
	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis exists check - key: %s, exists: %v", key, exists)
	}
	return exists, nil
}

// Expire sets an expiration time for a key
func (r *RedisService) Expire(key string, expiration time.Duration) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.Expire(ctx, key, expiration).Err()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis expire failed - key: %s, error: %v", key, err)
		}
		return fmt.Errorf("redis expire failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis expire set - key: %s, expiration: %v", key, expiration)
	}
	return nil
}

// TTL gets the remaining time to live for a key
func (r *RedisService) TTL(key string) (time.Duration, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	ttl, err := r.client.TTL(ctx, key).Result()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis TTL check failed - key: %s, error: %v", key, err)
		}
		return 0, fmt.Errorf("redis TTL check failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis TTL - key: %s, ttl: %v", key, ttl)
	}
	return ttl, nil
}

// Incr increments a counter in Redis
func (r *RedisService) Incr(key string) (int64, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.Incr(ctx, key).Result()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis incr failed - key: %s, error: %v", key, err)
		}
		return 0, fmt.Errorf("redis incr failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis incr successful - key: %s, value: %d", key, val)
	}
	return val, nil
}

// IncrBy increments a counter by a specific amount
func (r *RedisService) IncrBy(key string, value int64) (int64, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.IncrBy(ctx, key, value).Result()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis incrby failed - key: %s, value: %d, error: %v", key, value, err)
		}
		return 0, fmt.Errorf("redis incrby failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis incrby successful - key: %s, value: %d", key, val)
	}
	return val, nil
}

// HGet retrieves a field from a Redis hash
func (r *RedisService) HGet(key, field string) (string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.HGet(ctx, key, field).Result()
	if err != nil {
		if err == redis.Nil {
			if r.logger != nil {
				r.logger.Printf("DEBUG: Redis hash field not found - key: %s, field: %s", key, field)
			}
			return "", nil
		}
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis hget failed - key: %s, field: %s, error: %v", key, field, err)
		}
		return "", fmt.Errorf("redis hget failed for key %s field %s: %w", key, field, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis hget successful - key: %s, field: %s", key, field)
	}
	return val, nil
}

// HSet sets a field in a Redis hash
func (r *RedisService) HSet(key, field string, value interface{}) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.HSet(ctx, key, field, value).Err()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis hset failed - key: %s, field: %s, error: %v", key, field, err)
		}
		return fmt.Errorf("redis hset failed for key %s field %s: %w", key, field, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis hset successful - key: %s, field: %s", key, field)
	}
	return nil
}

// HGetAll retrieves all fields from a Redis hash
func (r *RedisService) HGetAll(key string) (map[string]string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.HGetAll(ctx, key).Result()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis hgetall failed - key: %s, error: %v", key, err)
		}
		return nil, fmt.Errorf("redis hgetall failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis hgetall successful - key: %s, field_count: %d", key, len(val))
	}
	return val, nil
}

// LPush pushes a value to the left of a Redis list
func (r *RedisService) LPush(key string, values ...interface{}) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.LPush(ctx, key, values...).Err()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis lpush failed - key: %s, error: %v", key, err)
		}
		return fmt.Errorf("redis lpush failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis lpush successful - key: %s, value_count: %d", key, len(values))
	}
	return nil
}

// RPop pops a value from the right of a Redis list
func (r *RedisService) RPop(key string) (string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.RPop(ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			if r.logger != nil {
				r.logger.Printf("DEBUG: Redis list is empty - key: %s", key)
			}
			return "", nil
		}
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis rpop failed - key: %s, error: %v", key, err)
		}
		return "", fmt.Errorf("redis rpop failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis rpop successful - key: %s", key)
	}
	return val, nil
}

// SAdd adds members to a Redis set
func (r *RedisService) SAdd(key string, members ...interface{}) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.SAdd(ctx, key, members...).Err()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis sadd failed - key: %s, error: %v", key, err)
		}
		return fmt.Errorf("redis sadd failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis sadd successful - key: %s, member_count: %d", key, len(members))
	}
	return nil
}

// SMembers retrieves all members from a Redis set
func (r *RedisService) SMembers(key string) ([]string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.SMembers(ctx, key).Result()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis smembers failed - key: %s, error: %v", key, err)
		}
		return nil, fmt.Errorf("redis smembers failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis smembers successful - key: %s, member_count: %d", key, len(val))
	}
	return val, nil
}

// ZAdd adds members to a Redis sorted set
func (r *RedisService) ZAdd(key string, score float64, member string) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.ZAdd(ctx, key, &redis.Z{Score: score, Member: member}).Err()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis zadd failed - key: %s, score: %f, error: %v", key, score, err)
		}
		return fmt.Errorf("redis zadd failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis zadd successful - key: %s, score: %f, member: %s", key, score, member)
	}
	return nil
}

// ZRange retrieves members from a Redis sorted set by rank
func (r *RedisService) ZRange(key string, start, stop int64) ([]string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.ZRange(ctx, key, start, stop).Result()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis zrange failed - key: %s, start: %d, stop: %d, error: %v", key, start, stop, err)
		}
		return nil, fmt.Errorf("redis zrange failed for key %s: %w", key, err)
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis zrange successful - key: %s, start: %d, stop: %d, member_count: %d", key, start, stop, len(val))
	}
	return val, nil
}

// FlushDB clears all keys from the current database
func (r *RedisService) FlushDB() error {
	ctx, cancel := context.WithTimeout(r.ctx, 10*time.Second)
	defer cancel()

	err := r.client.FlushDB(ctx).Err()
	if err != nil {
		if r.logger != nil {
			r.logger.Printf("ERROR: Redis flushdb failed - error: %v", err)
		}
		return fmt.Errorf("redis flushdb failed: %w", err)
	}

	if r.logger != nil {
		r.logger.Printf("INFO: Redis database flushed successfully")
	}
	return nil
}

// GetStats returns Redis connection pool statistics
func (r *RedisService) GetStats() *redis.PoolStats {
	stats := r.client.PoolStats()
	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis pool stats - hits: %d, misses: %d, timeouts: %d, total_conns: %d, idle_conns: %d, stale_conns: %d",
			int(stats.Hits), int(stats.Misses), int(stats.Timeouts),
			int(stats.TotalConns), int(stats.IdleConns), int(stats.StaleConns))
	}
	return stats
}

// HealthCheck performs a comprehensive health check on the Redis service
func (r *RedisService) HealthCheck() error {
	// Test basic connectivity
	if err := r.Ping(); err != nil {
		return fmt.Errorf("redis health check failed - ping: %w", err)
	}

	// Test write operation
	testKey := "health_check_test"
	testValue := "test_value"
	if err := r.Set(testKey, testValue, 10*time.Second); err != nil {
		return fmt.Errorf("redis health check failed - set: %w", err)
	}

	// Test read operation
	val, err := r.Get(testKey)
	if err != nil {
		return fmt.Errorf("redis health check failed - get: %w", err)
	}

	if val != testValue {
		return fmt.Errorf("redis health check failed - value mismatch: expected %s, got %s", testValue, val)
	}

	// Clean up test key
	if err := r.Delete(testKey); err != nil {
		if r.logger != nil {
			r.logger.Printf("WARN: Failed to clean up health check test key - error: %v", err)
		}
	}

	if r.logger != nil {
		r.logger.Printf("DEBUG: Redis health check passed")
	}
	return nil
}

// Close closes the Redis connection and cleans up resources
func (r *RedisService) Close() error {
	if r.client != nil {
		err := r.client.Close()
		if err != nil {
			if r.logger != nil {
				r.logger.Printf("ERROR: Failed to close Redis connection - error: %v", err)
			}
			return fmt.Errorf("failed to close Redis connection: %w", err)
		}
		if r.logger != nil {
			r.logger.Printf("INFO: Redis connection closed successfully")
		}
	}
	return nil
}

// GetClient returns the underlying Redis client for advanced operations
func (r *RedisService) GetClient() *redis.Client {
	return r.client
}

// GetContext returns the service context
func (r *RedisService) GetContext() context.Context {
	return r.ctx
}
