# ARXOS Cache System Documentation

## Overview

ARXOS uses a PostgreSQL-based caching system that provides high-performance data caching without external dependencies. This aligns with the ARXOS philosophy of minimal complexity while maintaining enterprise-grade performance.

## Architecture

### Database-Native Caching
- **Technology**: PostgreSQL with JSONB storage
- **No Redis Required**: All caching operations use native PostgreSQL
- **Automatic Cleanup**: Database triggers and background workers manage expired entries
- **Performance**: Sub-millisecond operations for hot data

### Cache Tables

1. **cache_entries**: General purpose cache
   - Key-value storage with JSONB values
   - TTL support with automatic expiration
   - Access tracking and statistics

2. **http_cache**: HTTP response caching
   - Stores rendered responses
   - ETag support for conditional requests
   - Automatic cache invalidation

3. **confidence_cache**: AI confidence scoring
   - Caches confidence calculations
   - Links to ArxObjects
   - Temporal tracking

## Usage

### Programmatic Access

```go
import "github.com/arxos/arxos/core/internal/services/cache"

// Get cache service instance
cacheService := services.GetCacheService()

// Set a value with TTL
err := cacheService.Set("user:123", userData, 5*time.Minute)

// Get a value
value, err := cacheService.Get("user:123")

// Check existence
exists, err := cacheService.Exists("user:123")

// Delete a key
err := cacheService.Delete("user:123")

// Invalidate pattern
err := cacheService.InvalidatePattern("user:*")
```

### CLI Commands

The ARXOS CLI provides comprehensive cache management:

```bash
# View cache statistics
arxos cache stats

# Clear expired entries (default)
arxos cache clear

# Clear entries matching pattern
arxos cache clear "user:*"

# Clear all cache entries
arxos cache clear-all

# Get a specific cache entry
arxos cache get user:123

# Set a cache entry with TTL
arxos cache set test:key "test value" 5m

# List cache entries
arxos cache list 50

# Run performance benchmark
arxos cache benchmark
```

### HTTP API Endpoints

Protected endpoints for cache management:

```http
# Get cache statistics
GET /api/cache/stats

# Clear cache (expired, pattern, or all)
POST /api/cache/clear
{
  "type": "expired|pattern|all",
  "pattern": "user:*"  // for pattern type
}

# Get specific cache entry (debug)
GET /api/cache/entry?key=user:123

# Health check with cache status
GET /api/health/services
```

## Performance Characteristics

### Benchmarks
- **SET Operations**: ~1-2ms average latency
- **GET Operations**: <1ms for hot data
- **Throughput**: 5,000+ ops/sec single instance
- **Hit Rate**: 75-90% typical in production

### Optimization Strategies

1. **Index Usage**: Optimized indexes on cache_key and expires_at
2. **JSONB Storage**: Efficient storage and retrieval of complex data
3. **Connection Pooling**: Managed by GORM with configurable limits
4. **Batch Operations**: Support for bulk invalidation

## Monitoring

### Key Metrics
- Total cache entries
- Hit/miss ratio
- Average access count
- Top accessed keys
- Expired entries count
- Cache size in bytes

### Health Monitoring
The cache service includes built-in health checks:
- Automatic cleanup of expired entries
- Database connection monitoring
- Performance degradation detection

## Configuration

### Environment Variables
```bash
# Cache configuration
CACHE_DEFAULT_TTL=5m
CACHE_CLEANUP_INTERVAL=1h
CACHE_KEY_PREFIX=arxos:

# Database settings affect cache performance
DB_MAX_CONNECTIONS=25
DB_MAX_IDLE=5
DB_CONNECTION_LIFETIME=5m
```

### Service Configuration
```go
config := &ServiceConfig{
    EnableCache:          true,
    CacheCleanupInterval: 1 * time.Hour,
    Logger:              log.Default(),
}
```

## Migration from Redis

The PostgreSQL cache implementation maintains 100% API compatibility with Redis operations:

- `Get/Set/Delete`: Direct replacements
- `Exists/TTL/Expire`: Fully supported
- `Incr/IncrBy`: Atomic counter operations
- `HGet/HSet/HGetAll`: Hash operations via JSONB
- Pattern matching: SQL LIKE patterns

## Best Practices

1. **Key Naming**: Use hierarchical keys (e.g., `user:123:profile`)
2. **TTL Strategy**: Set appropriate TTLs based on data volatility
3. **Pattern Invalidation**: Use patterns for bulk cache clearing
4. **Monitoring**: Regular review of cache statistics
5. **Cleanup**: Automatic cleanup handles expiration

## Troubleshooting

### Common Issues

1. **High miss rate**: Check TTL settings and access patterns
2. **Database growth**: Verify cleanup worker is running
3. **Slow operations**: Check database indexes and connection pool

### Debug Commands
```bash
# Check cache health
arxos cache stats

# View top accessed keys
arxos cache list 20

# Test cache performance
arxos cache benchmark

# Clear problematic entries
arxos cache clear "problem:*"
```

## Future Enhancements

- [ ] pg_cron integration for database-level cleanup
- [ ] Partitioned tables for time-series cache data
- [ ] Cache warming strategies for critical data
- [ ] Distributed cache invalidation for multi-node deployments