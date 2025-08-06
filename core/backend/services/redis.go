package services

import (
	"context"
	"fmt"
	"time"

	"github.com/go-redis/redis/extra/redisotel/v8"
	"github.com/go-redis/redis/v8"
	"go.uber.org/zap"
)

// RedisService provides Redis caching functionality with connection pooling and health checks
type RedisService struct {
	client *redis.Client
	ctx    context.Context
	logger *zap.Logger
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
func NewRedisService(config *RedisConfig, logger *zap.Logger) (*RedisService, error) {
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
			logger.Debug("Redis connection established", zap.String("addr", config.Addr))
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

	logger.Info("Redis service initialized successfully",
		zap.String("addr", config.Addr),
		zap.Int("pool_size", config.PoolSize),
		zap.Int("min_idle_conns", config.MinIdleConns),
	)

	return service, nil
}

// Ping tests the Redis connection
func (r *RedisService) Ping() error {
	ctx, cancel := context.WithTimeout(r.ctx, 5*time.Second)
	defer cancel()

	_, err := r.client.Ping(ctx).Result()
	if err != nil {
		r.logger.Error("Redis ping failed", zap.Error(err))
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
			r.logger.Debug("Redis key not found", zap.String("key", key))
			return "", nil
		}
		r.logger.Error("Redis get failed", zap.String("key", key), zap.Error(err))
		return "", fmt.Errorf("redis get failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis get successful", zap.String("key", key))
	return val, nil
}

// Set stores a value in Redis with optional expiration
func (r *RedisService) Set(key string, value interface{}, expiration time.Duration) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.Set(ctx, key, value, expiration).Err()
	if err != nil {
		r.logger.Error("Redis set failed", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("redis set failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis set successful", zap.String("key", key), zap.Duration("expiration", expiration))
	return nil
}

// Delete removes a key from Redis
func (r *RedisService) Delete(key string) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.Del(ctx, key).Err()
	if err != nil {
		r.logger.Error("Redis delete failed", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("redis delete failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis delete successful", zap.String("key", key))
	return nil
}

// Exists checks if a key exists in Redis
func (r *RedisService) Exists(key string) (bool, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	result, err := r.client.Exists(ctx, key).Result()
	if err != nil {
		r.logger.Error("Redis exists check failed", zap.String("key", key), zap.Error(err))
		return false, fmt.Errorf("redis exists check failed for key %s: %w", key, err)
	}

	exists := result > 0
	r.logger.Debug("Redis exists check", zap.String("key", key), zap.Bool("exists", exists))
	return exists, nil
}

// Expire sets an expiration time for a key
func (r *RedisService) Expire(key string, expiration time.Duration) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.Expire(ctx, key, expiration).Err()
	if err != nil {
		r.logger.Error("Redis expire failed", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("redis expire failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis expire set", zap.String("key", key), zap.Duration("expiration", expiration))
	return nil
}

// TTL gets the remaining time to live for a key
func (r *RedisService) TTL(key string) (time.Duration, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	ttl, err := r.client.TTL(ctx, key).Result()
	if err != nil {
		r.logger.Error("Redis TTL check failed", zap.String("key", key), zap.Error(err))
		return 0, fmt.Errorf("redis TTL check failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis TTL", zap.String("key", key), zap.Duration("ttl", ttl))
	return ttl, nil
}

// Incr increments a counter in Redis
func (r *RedisService) Incr(key string) (int64, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.Incr(ctx, key).Result()
	if err != nil {
		r.logger.Error("Redis incr failed", zap.String("key", key), zap.Error(err))
		return 0, fmt.Errorf("redis incr failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis incr successful", zap.String("key", key), zap.Int64("value", val))
	return val, nil
}

// IncrBy increments a counter by a specific amount
func (r *RedisService) IncrBy(key string, value int64) (int64, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.IncrBy(ctx, key, value).Result()
	if err != nil {
		r.logger.Error("Redis incrby failed", zap.String("key", key), zap.Int64("value", value), zap.Error(err))
		return 0, fmt.Errorf("redis incrby failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis incrby successful", zap.String("key", key), zap.Int64("value", val))
	return val, nil
}

// HGet retrieves a field from a Redis hash
func (r *RedisService) HGet(key, field string) (string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.HGet(ctx, key, field).Result()
	if err != nil {
		if err == redis.Nil {
			r.logger.Debug("Redis hash field not found", zap.String("key", key), zap.String("field", field))
			return "", nil
		}
		r.logger.Error("Redis hget failed", zap.String("key", key), zap.String("field", field), zap.Error(err))
		return "", fmt.Errorf("redis hget failed for key %s field %s: %w", key, field, err)
	}

	r.logger.Debug("Redis hget successful", zap.String("key", key), zap.String("field", field))
	return val, nil
}

// HSet sets a field in a Redis hash
func (r *RedisService) HSet(key, field string, value interface{}) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.HSet(ctx, key, field, value).Err()
	if err != nil {
		r.logger.Error("Redis hset failed", zap.String("key", key), zap.String("field", field), zap.Error(err))
		return fmt.Errorf("redis hset failed for key %s field %s: %w", key, field, err)
	}

	r.logger.Debug("Redis hset successful", zap.String("key", key), zap.String("field", field))
	return nil
}

// HGetAll retrieves all fields from a Redis hash
func (r *RedisService) HGetAll(key string) (map[string]string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.HGetAll(ctx, key).Result()
	if err != nil {
		r.logger.Error("Redis hgetall failed", zap.String("key", key), zap.Error(err))
		return nil, fmt.Errorf("redis hgetall failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis hgetall successful", zap.String("key", key), zap.Int("field_count", len(val)))
	return val, nil
}

// LPush pushes a value to the left of a Redis list
func (r *RedisService) LPush(key string, values ...interface{}) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.LPush(ctx, key, values...).Err()
	if err != nil {
		r.logger.Error("Redis lpush failed", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("redis lpush failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis lpush successful", zap.String("key", key), zap.Int("value_count", len(values)))
	return nil
}

// RPop pops a value from the right of a Redis list
func (r *RedisService) RPop(key string) (string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.RPop(ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			r.logger.Debug("Redis list is empty", zap.String("key", key))
			return "", nil
		}
		r.logger.Error("Redis rpop failed", zap.String("key", key), zap.Error(err))
		return "", fmt.Errorf("redis rpop failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis rpop successful", zap.String("key", key))
	return val, nil
}

// SAdd adds members to a Redis set
func (r *RedisService) SAdd(key string, members ...interface{}) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.SAdd(ctx, key, members...).Err()
	if err != nil {
		r.logger.Error("Redis sadd failed", zap.String("key", key), zap.Error(err))
		return fmt.Errorf("redis sadd failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis sadd successful", zap.String("key", key), zap.Int("member_count", len(members)))
	return nil
}

// SMembers retrieves all members from a Redis set
func (r *RedisService) SMembers(key string) ([]string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.SMembers(ctx, key).Result()
	if err != nil {
		r.logger.Error("Redis smembers failed", zap.String("key", key), zap.Error(err))
		return nil, fmt.Errorf("redis smembers failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis smembers successful", zap.String("key", key), zap.Int("member_count", len(val)))
	return val, nil
}

// ZAdd adds members to a Redis sorted set
func (r *RedisService) ZAdd(key string, score float64, member string) error {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	err := r.client.ZAdd(ctx, key, &redis.Z{Score: score, Member: member}).Err()
	if err != nil {
		r.logger.Error("Redis zadd failed", zap.String("key", key), zap.Float64("score", score), zap.Error(err))
		return fmt.Errorf("redis zadd failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis zadd successful", zap.String("key", key), zap.Float64("score", score), zap.String("member", member))
	return nil
}

// ZRange retrieves members from a Redis sorted set by rank
func (r *RedisService) ZRange(key string, start, stop int64) ([]string, error) {
	ctx, cancel := context.WithTimeout(r.ctx, 3*time.Second)
	defer cancel()

	val, err := r.client.ZRange(ctx, key, start, stop).Result()
	if err != nil {
		r.logger.Error("Redis zrange failed", zap.String("key", key), zap.Int64("start", start), zap.Int64("stop", stop), zap.Error(err))
		return nil, fmt.Errorf("redis zrange failed for key %s: %w", key, err)
	}

	r.logger.Debug("Redis zrange successful", zap.String("key", key), zap.Int64("start", start), zap.Int64("stop", stop), zap.Int("member_count", len(val)))
	return val, nil
}

// FlushDB clears all keys from the current database
func (r *RedisService) FlushDB() error {
	ctx, cancel := context.WithTimeout(r.ctx, 10*time.Second)
	defer cancel()

	err := r.client.FlushDB(ctx).Err()
	if err != nil {
		r.logger.Error("Redis flushdb failed", zap.Error(err))
		return fmt.Errorf("redis flushdb failed: %w", err)
	}

	r.logger.Info("Redis database flushed successfully")
	return nil
}

// GetStats returns Redis connection pool statistics
func (r *RedisService) GetStats() *redis.PoolStats {
	stats := r.client.PoolStats()
	r.logger.Debug("Redis pool stats",
		zap.Int("hits", int(stats.Hits)),
		zap.Int("misses", int(stats.Misses)),
		zap.Int("timeouts", int(stats.Timeouts)),
		zap.Int("total_conns", int(stats.TotalConns)),
		zap.Int("idle_conns", int(stats.IdleConns)),
		zap.Int("stale_conns", int(stats.StaleConns)),
	)
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
		r.logger.Warn("Failed to clean up health check test key", zap.Error(err))
	}

	r.logger.Debug("Redis health check passed")
	return nil
}

// Close closes the Redis connection and cleans up resources
func (r *RedisService) Close() error {
	if r.client != nil {
		err := r.client.Close()
		if err != nil {
			r.logger.Error("Failed to close Redis connection", zap.Error(err))
			return fmt.Errorf("failed to close Redis connection: %w", err)
		}
		r.logger.Info("Redis connection closed successfully")
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
