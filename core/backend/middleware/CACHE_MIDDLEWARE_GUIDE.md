# Cache Middleware Guide

## Overview

The cache middleware provides automatic HTTP response caching for the Arxos backend. It intercepts requests, checks the cache first, and either serves cached responses or proceeds to the handler and caches the result.

## Features

- **Automatic Response Caching**: Caches HTTP responses with configurable TTL
- **Smart Cache Key Generation**: Creates unique keys based on request parameters
- **Flexible Configuration**: Customizable caching behavior per route
- **Cache Invalidation**: Automatic cache invalidation on specific operations
- **Performance Monitoring**: Cache statistics and hit/miss tracking
- **Graceful Degradation**: Continues working when cache service is unavailable

## Basic Usage

### Simple Cache Middleware

```go
import "arx/middleware"

// Use default configuration (5-minute TTL)
r.Use(middleware.CacheMiddleware(nil))

// Use custom TTL
r.Use(middleware.CacheMiddlewareWithTTL(10 * time.Minute))
```

### Custom Configuration

```go
config := &middleware.CacheConfig{
    TTL:           10 * time.Minute,
    KeyPrefix:     "api:cache:",
    IncludeQuery:  true,
    IncludeBody:   false,
    IncludeHeaders: []string{"Authorization", "User-Agent"},
    MaxBodySize:   2 * 1024 * 1024, // 2MB
    Logger:        logger,
}

r.Use(middleware.CacheMiddleware(config))
```

## Configuration Options

### CacheConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `TTL` | `time.Duration` | `5 * time.Minute` | Time-to-live for cached responses |
| `KeyPrefix` | `string` | `"middleware:cache:"` | Prefix for cache keys |
| `IncludeQuery` | `bool` | `true` | Include query parameters in cache key |
| `IncludeBody` | `bool` | `false` | Include request body in cache key |
| `IncludeHeaders` | `[]string` | `["Authorization", "Content-Type"]` | Headers to include in cache key |
| `MaxBodySize` | `int64` | `1024 * 1024` | Maximum body size to include in cache key |
| `Logger` | `*zap.Logger` | `nil` | Logger for cache operations |

## Advanced Usage

### Path-Specific Caching

```go
// Cache only specific paths
paths := []string{"/api/buildings", "/api/assets", "/api/symbols"}
r.Use(middleware.CacheMiddlewareForPaths(paths, nil))

// Exclude specific paths from caching
exclusions := []string{"/api/admin", "/api/health", "/api/metrics"}
r.Use(middleware.CacheMiddlewareWithExclusions(exclusions, nil))
```

### Cache Invalidation

```go
// Invalidate cache on specific operations
invalidationPatterns := []string{
    "/api/buildings",    // Invalidate building-related caches
    "/api/assets",       // Invalidate asset-related caches
    "/api/version",      // Invalidate version-related caches
}

r.Use(middleware.CacheInvalidationMiddleware(invalidationPatterns, nil))
```

### Cache Statistics

```go
// Add cache statistics to response headers
r.Use(middleware.CacheStatsMiddleware(nil))
```

## Cache Key Generation

The middleware generates cache keys based on:

1. **HTTP Method**: GET, POST, etc.
2. **URL Path**: `/api/buildings/123`
3. **Query Parameters**: `?page=1&size=20` (if enabled)
4. **Headers**: Authorization, Content-Type, etc. (if specified)
5. **Request Body**: MD5 hash of body (if enabled and within size limit)

### Example Cache Keys

```
GET /api/buildings?page=1&size=20
→ middleware:cache:GET:/api/buildings:query:page=1&size=20

GET /api/assets/123 with Authorization header
→ middleware:cache:GET:/api/assets/123:header:Authorization:Bearer token123

POST /api/buildings with JSON body
→ middleware:cache:POST:/api/buildings:body:a1b2c3d4e5f6...
```

## Response Headers

The middleware adds the following headers to responses:

### Cache Hit
```
X-Cache: HIT
X-Cache-Key: a1b2c3d4e5f6...
X-Cache-Expires: 2024-01-15T10:30:00Z
```

### Cache Miss
```
X-Cache: MISS
X-Cache-Key: a1b2c3d4e5f6...
X-Cache-Expires: 2024-01-15T10:30:00Z
```

### Cache Statistics (if enabled)
```
X-Cache-Hits: 150
X-Cache-Misses: 25
X-Cache-Hit-Rate: 0.86
X-Cache-Total-Keys: 45
```

## Caching Rules

### What Gets Cached
- **HTTP Methods**: Only GET requests (configurable)
- **Status Codes**: Only 2xx responses
- **Content Types**: JSON, text, XML responses
- **Response Size**: No limit (handled by Redis)

### What Doesn't Get Cached
- **Non-GET requests**: POST, PUT, DELETE, etc.
- **Error responses**: 4xx, 5xx status codes
- **Binary responses**: Images, PDFs, etc.
- **Large responses**: Configurable size limit

## Integration Examples

### Main Application Setup

```go
// main.go
func main() {
    // Initialize cache service
    cacheService := services.NewCacheService(redisService, nil, logger)
    handlers.SetCacheService(cacheService)

    // Set up router
    r := chi.NewRouter()

    // Global cache middleware
    r.Use(middleware.CacheMiddlewareWithTTL(5 * time.Minute))

    // Path-specific caching
    r.Group(func(r chi.Router) {
        r.Use(middleware.CacheMiddlewareForPaths([]string{"/api/buildings"}, nil))
        r.Get("/api/buildings", handlers.ListBuildings)
        r.Get("/api/buildings/{id}", handlers.GetBuilding)
    })

    // Cache invalidation for write operations
    r.Group(func(r chi.Router) {
        r.Use(middleware.CacheInvalidationMiddleware([]string{"/api/buildings"}, nil))
        r.Post("/api/buildings", handlers.CreateBuilding)
        r.Put("/api/buildings/{id}", handlers.UpdateBuilding)
        r.Delete("/api/buildings/{id}", handlers.DeleteBuilding)
    })
}
```

### Route-Specific Configuration

```go
// Different TTL for different endpoints
r.Group(func(r chi.Router) {
    // Short TTL for frequently changing data
    r.Use(middleware.CacheMiddlewareWithTTL(1 * time.Minute))
    r.Get("/api/version/history", handlers.GetVersionHistory)
})

r.Group(func(r chi.Router) {
    // Long TTL for static data
    r.Use(middleware.CacheMiddlewareWithTTL(1 * time.Hour))
    r.Get("/api/symbols", handlers.ListSymbols)
    r.Get("/api/symbols/{id}", handlers.GetSymbol)
})
```

### Custom Cache Configuration

```go
// Custom configuration for specific endpoints
config := &middleware.CacheConfig{
    TTL:           15 * time.Minute,
    KeyPrefix:     "assets:cache:",
    IncludeQuery:  true,
    IncludeBody:   false,
    IncludeHeaders: []string{"Authorization", "X-User-Role"},
    MaxBodySize:   512 * 1024, // 512KB
    Logger:        logger,
}

r.Group(func(r chi.Router) {
    r.Use(middleware.CacheMiddleware(config))
    r.Get("/api/assets", handlers.GetBuildingAssets)
    r.Get("/api/assets/{id}", handlers.GetBuildingAsset)
})
```

## Performance Monitoring

### Cache Statistics

```go
// Enable cache statistics middleware
r.Use(middleware.CacheStatsMiddleware(nil))

// Monitor cache performance
// Headers will include: X-Cache-Hits, X-Cache-Misses, X-Cache-Hit-Rate, X-Cache-Total-Keys
```

### Logging

```go
config := &middleware.CacheConfig{
    TTL:    5 * time.Minute,
    Logger: logger, // Zap logger instance
}

r.Use(middleware.CacheMiddleware(config))

// Logs will include:
// - Cache hits and misses
// - Cache key generation errors
// - Cache invalidation events
// - Performance metrics
```

## Best Practices

### 1. TTL Selection
- **Static Data**: 1 hour or more (symbols, configurations)
- **Semi-Static Data**: 15-30 minutes (buildings, assets)
- **Dynamic Data**: 1-5 minutes (version history, real-time data)

### 2. Cache Key Design
- Include user context for personalized data
- Include query parameters for filtered results
- Use consistent key prefixes for easy invalidation

### 3. Cache Invalidation
- Invalidate related caches on data changes
- Use pattern-based invalidation for efficiency
- Consider cache warming for critical data

### 4. Monitoring
- Monitor cache hit rates
- Track cache memory usage
- Alert on cache service failures

### 5. Security
- Don't cache sensitive data
- Include authentication headers in cache keys
- Use appropriate TTL for security-sensitive data

## Troubleshooting

### Common Issues

#### Cache Not Working
1. Check if Redis service is running
2. Verify cache service initialization
3. Check cache key generation
4. Review TTL settings

#### High Memory Usage
1. Reduce TTL for frequently accessed data
2. Implement cache size limits
3. Use cache compression
4. Monitor cache statistics

#### Stale Data
1. Review cache invalidation patterns
2. Reduce TTL for dynamic data
3. Implement cache warming
4. Use conditional requests (ETag, Last-Modified)

### Debug Mode

```go
config := &middleware.CacheConfig{
    TTL:    5 * time.Minute,
    Logger: logger, // Enable detailed logging
}

r.Use(middleware.CacheMiddleware(config))
```

## Migration Guide

### From Manual Caching

1. **Remove manual cache calls** from handlers
2. **Add cache middleware** to routes
3. **Configure TTL** based on data characteristics
4. **Test cache behavior** and adjust as needed

### Example Migration

```go
// Before: Manual caching in handler
func GetBuilding(w http.ResponseWriter, r *http.Request) {
    cacheKey := fmt.Sprintf("building:%s", buildingID)
    if cached, err := cacheService.Get(cacheKey); err == nil && cached != nil {
        json.NewEncoder(w).Encode(cached)
        return
    }
    // ... database query and response
    cacheService.Set(cacheKey, building, 10*time.Minute)
}

// After: Automatic caching with middleware
func GetBuilding(w http.ResponseWriter, r *http.Request) {
    // ... database query and response
    // Caching handled automatically by middleware
}
```

## Conclusion

The cache middleware provides a powerful, flexible solution for HTTP response caching. It automatically handles cache key generation, response caching, and cache invalidation while providing comprehensive monitoring and configuration options.

Key benefits:
- **Automatic Caching**: No manual cache management required
- **Flexible Configuration**: Customizable per route and endpoint
- **Performance Monitoring**: Built-in statistics and logging
- **Graceful Degradation**: Continues working without cache service
- **Security**: Proper isolation and authentication handling

The middleware is production-ready and can significantly improve application performance while reducing database load.
