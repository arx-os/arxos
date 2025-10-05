# Unified Cache Architecture for ArxOS

## Overview

ArxOS implements a **multi-tier caching strategy** that provides optimal performance across different data types and access patterns. This document outlines the proper caching architecture and migration plan.

## Current Problems

### Redundant Implementations
- `internal/infrastructure/cache.go` - Basic in-memory cache
- `internal/infrastructure/cache/cache_manager.go` - File-based cache manager  
- `internal/infrastructure/cache/redis_cache.go` - Placeholder Redis implementation
- `internal/infrastructure/cache/cache_strategy.go` - Cache strategy management
- Query optimizer has separate caching logic
- Mobile app has independent caching

### Confusing Directory Structure
- `~/.arxos/cache/` - Local file cache
- `~/.cache/` - System cache (standard Unix location)
- Multiple cache implementations in `internal/`

### No Clear Layering
- No distinction between L1 (memory), L2 (disk), L3 (network)
- No unified cache key strategy
- No consistent TTL management

## Proper Multi-Tier Cache Architecture

### L1 Cache (In-Memory)
- **Purpose**: Fastest access for frequently used data
- **Storage**: Go map in memory
- **Capacity**: ~10,000 entries
- **TTL**: 5 minutes (short-lived)
- **Use Cases**: 
  - API response caching
  - User session data
  - Real-time TUI data
  - Query results

### L2 Cache (Local Disk)
- **Purpose**: Persistent cache for medium-term data
- **Storage**: JSON files in `~/.arxos/cache/l2/`
- **Capacity**: ~1GB disk space
- **TTL**: 1 hour (medium-lived)
- **Use Cases**:
  - IFC file processing results
  - Building geometry data
  - Spatial queries
  - Configuration templates

### L3 Cache (Network/Redis)
- **Purpose**: Shared cache across multiple instances
- **Storage**: Redis (when enabled)
- **Capacity**: Configurable (typically 10GB+)
- **TTL**: 24 hours (long-lived)
- **Use Cases**:
  - Shared building data across team
  - Large IFC processing results
  - Cross-instance synchronization
  - Production deployment scaling

## Cache Key Strategy

### Hierarchical Naming
```
{service}:{entity}:{id}:{version}
```

### Examples
```
ifc:building:abc123:v1
spatial:query:floor_plan:def456:v2
api:response:equipment_list:ghi789:v1
config:template:local:v1
```

## Cache Invalidation Strategy

### Event-Driven Invalidation
- **Building Updates**: Invalidate all building-related caches
- **IFC Processing**: Invalidate spatial and equipment caches
- **Configuration Changes**: Invalidate template and config caches
- **User Actions**: Invalidate session and preference caches

### TTL-Based Expiration
- Automatic cleanup based on time-to-live
- Background cleanup process
- Configurable per cache layer

## Migration Plan

### Phase 1: Implement Unified Cache ✅
- [x] Create `UnifiedCache` implementation
- [x] Add configuration support
- [x] Update container to use unified cache

### Phase 2: Migrate Existing Usage
- [ ] Update query optimizer to use unified cache
- [ ] Migrate IFC service caching
- [ ] Update TUI caching
- [ ] Consolidate mobile app caching

### Phase 3: Remove Redundant Code
- [ ] Remove old cache implementations
- [ ] Clean up unused cache files
- [ ] Update documentation

### Phase 4: Add Advanced Features
- [ ] Implement Redis L3 cache
- [ ] Add cache warming strategies
- [ ] Implement cache analytics
- [ ] Add cache monitoring

## Configuration

### Development (Local Mode)
```yaml
unified_cache:
  l1:
    enabled: true
    max_entries: 1000
    default_ttl: "5m"
  l2:
    enabled: true
    max_size_mb: 100
    default_ttl: "1h"
    path: "cache/l2"
  l3:
    enabled: false
```

### Production (Cloud Mode)
```yaml
unified_cache:
  l1:
    enabled: true
    max_entries: 10000
    default_ttl: "5m"
  l2:
    enabled: true
    max_size_mb: 1000
    default_ttl: "1h"
    path: "cache/l2"
  l3:
    enabled: true
    default_ttl: "24h"
    host: "redis.production.arxos.io"
    port: 6379
    password: "${REDIS_PASSWORD}"
    db: 0
```

## Performance Benefits

### Latency Reduction
- **L1 Hit**: ~1μs (in-memory)
- **L2 Hit**: ~1ms (local disk)
- **L3 Hit**: ~10ms (network)
- **Cache Miss**: ~100ms+ (database/API)

### Throughput Improvement
- Reduced database load
- Faster API responses
- Better user experience
- Lower resource usage

### Scalability
- Horizontal scaling with L3 cache
- Reduced memory pressure with L2 cache
- Efficient data sharing across instances

## Best Practices

### Cache Key Design
- Use consistent naming conventions
- Include version information
- Consider key length limits
- Avoid special characters

### TTL Selection
- **Frequently changing data**: Short TTL (5 minutes)
- **Stable data**: Medium TTL (1 hour)
- **Reference data**: Long TTL (24 hours)

### Memory Management
- Monitor L1 cache size
- Implement LRU eviction
- Regular cleanup of expired entries
- Memory usage alerts

### Error Handling
- Graceful degradation on cache failures
- Fallback to next cache layer
- Log cache errors for monitoring
- Circuit breaker for L3 cache

## Monitoring and Analytics

### Key Metrics
- Cache hit/miss ratios per layer
- Cache size and memory usage
- TTL effectiveness
- Cleanup frequency

### Alerts
- High cache miss rates
- Memory usage thresholds
- Disk space limits
- Network connectivity (L3)

## Conclusion

The unified cache architecture provides:
- **Performance**: Multi-tier strategy optimizes for different access patterns
- **Scalability**: L3 cache enables horizontal scaling
- **Maintainability**: Single implementation reduces complexity
- **Flexibility**: Configurable per environment and use case

This architecture follows industry best practices and provides a solid foundation for ArxOS's caching needs.
