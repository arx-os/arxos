package cache

import (
	"context"
	"time"
)

// Interface defines the cache interface following Clean Architecture principles
type Interface interface {
	// Basic operations
	Get(ctx context.Context, key string) (interface{}, error)
	Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error
	Delete(ctx context.Context, key string) error
	Exists(ctx context.Context, key string) (bool, error)

	// Batch operations
	GetMultiple(ctx context.Context, keys []string) (map[string]interface{}, error)
	SetMultiple(ctx context.Context, items map[string]interface{}, ttl time.Duration) error
	DeleteMultiple(ctx context.Context, keys []string) error

	// Advanced operations
	Increment(ctx context.Context, key string, delta int64) (int64, error)
	Decrement(ctx context.Context, key string, delta int64) (int64, error)
	Expire(ctx context.Context, key string, ttl time.Duration) error

	// Health check
	Ping() error
	IsHealthy() bool
	GetStats() map[string]interface{}

	// Cache management
	Clear(ctx context.Context) error
	ClearPattern(ctx context.Context, pattern string) error
}
