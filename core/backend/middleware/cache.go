package middleware

import (
	"bytes"
	"crypto/md5"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/arxos/arxos/core/backend/services"

	"go.uber.org/zap"
)

// CacheConfig holds configuration for the cache middleware
type CacheConfig struct {
	TTL            time.Duration
	KeyPrefix      string
	IncludeQuery   bool
	IncludeBody    bool
	IncludeHeaders []string
	MaxBodySize    int64
	Logger         *zap.Logger
}

// DefaultCacheConfig returns a default cache configuration
func DefaultCacheConfig() *CacheConfig {
	return &CacheConfig{
		TTL:            5 * time.Minute,
		KeyPrefix:      "middleware:cache:",
		IncludeQuery:   true,
		IncludeBody:    false,
		IncludeHeaders: []string{"Authorization", "Content-Type"},
		MaxBodySize:    1024 * 1024, // 1MB
		Logger:         nil,
	}
}

// CachedResponse represents a cached HTTP response
type CachedResponse struct {
	StatusCode    int               `json:"status_code"`
	Headers       map[string]string `json:"headers"`
	Body          []byte            `json:"body"`
	ContentType   string            `json:"content_type"`
	ContentLength int64             `json:"content_length"`
	CachedAt      time.Time         `json:"cached_at"`
	ExpiresAt     time.Time         `json:"expires_at"`
}

// responseWriter wraps http.ResponseWriter to capture the response
type responseWriter struct {
	http.ResponseWriter
	statusCode    int
	headers       map[string]string
	body          *bytes.Buffer
	contentType   string
	contentLength int64
}

// WriteHeader captures the status code
func (rw *responseWriter) WriteHeader(statusCode int) {
	rw.statusCode = statusCode
	rw.ResponseWriter.WriteHeader(statusCode)
}

// Write captures the response body
func (rw *responseWriter) Write(data []byte) (int, error) {
	if rw.body == nil {
		rw.body = &bytes.Buffer{}
	}
	rw.body.Write(data)
	rw.contentLength += int64(len(data))
	return rw.ResponseWriter.Write(data)
}

// Header returns the response headers
func (rw *responseWriter) Header() http.Header {
	return rw.ResponseWriter.Header()
}

// generateCacheKey creates a unique cache key based on request parameters
func generateCacheKey(r *http.Request, config *CacheConfig) (string, error) {
	var keyParts []string

	// Add key prefix
	keyParts = append(keyParts, config.KeyPrefix)

	// Add method and path
	keyParts = append(keyParts, r.Method, r.URL.Path)

	// Add query parameters if enabled
	if config.IncludeQuery && r.URL.RawQuery != "" {
		keyParts = append(keyParts, "query", r.URL.RawQuery)
	}

	// Add specified headers if enabled
	if len(config.IncludeHeaders) > 0 {
		for _, headerName := range config.IncludeHeaders {
			if headerValue := r.Header.Get(headerName); headerValue != "" {
				keyParts = append(keyParts, fmt.Sprintf("header:%s:%s", headerName, headerValue))
			}
		}
	}

	// Add request body if enabled and within size limit
	if config.IncludeBody && r.Body != nil {
		body, err := io.ReadAll(r.Body)
		if err != nil {
			return "", fmt.Errorf("failed to read request body: %w", err)
		}
		// Restore the body for the handler
		r.Body = io.NopCloser(bytes.NewBuffer(body))

		if int64(len(body)) <= config.MaxBodySize {
			// Create MD5 hash of body for shorter key
			bodyHash := md5.Sum(body)
			keyParts = append(keyParts, fmt.Sprintf("body:%x", bodyHash))
		}
	}

	// Join all parts and create final key
	key := strings.Join(keyParts, ":")

	// Create MD5 hash of the key to ensure it's not too long
	keyHash := md5.Sum([]byte(key))
	return fmt.Sprintf("%x", keyHash), nil
}

// shouldCache determines if the response should be cached
func shouldCache(statusCode int, contentType string) bool {
	// Only cache successful responses
	if statusCode < 200 || statusCode >= 300 {
		return false
	}

	// Only cache JSON and text responses
	contentType = strings.ToLower(contentType)
	return strings.Contains(contentType, "application/json") ||
		strings.Contains(contentType, "text/") ||
		strings.Contains(contentType, "application/xml")
}

// extractHeaders extracts relevant headers from the response
func extractHeaders(headers http.Header, includeHeaders []string) map[string]string {
	result := make(map[string]string)

	// Always include Content-Type
	if contentType := headers.Get("Content-Type"); contentType != "" {
		result["Content-Type"] = contentType
	}

	// Include specified headers
	for _, headerName := range includeHeaders {
		if headerValue := headers.Get(headerName); headerValue != "" {
			result[headerName] = headerValue
		}
	}

	return result
}

// CacheMiddleware creates a middleware that automatically caches HTTP responses
func CacheMiddleware(config *CacheConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultCacheConfig()
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip caching for non-GET requests (configurable)
			if r.Method != http.MethodGet {
				next.ServeHTTP(w, r)
				return
			}

			// Get cache service
			cacheService := services.GetCacheService()
			if cacheService == nil {
				// Cache service not available, proceed without caching
				next.ServeHTTP(w, r)
				return
			}

			// Generate cache key
			cacheKey, err := generateCacheKey(r, config)
			if err != nil {
				if config.Logger != nil {
					config.Logger.Warn("Failed to generate cache key",
						zap.String("path", r.URL.Path),
						zap.Error(err))
				}
				next.ServeHTTP(w, r)
				return
			}

			// Try to get from cache first
			if cached, err := cacheService.Get(cacheKey); err == nil && cached != nil {
				if cachedResponse, ok := cached.(CachedResponse); ok {
					// Check if cache entry has expired
					if time.Now().Before(cachedResponse.ExpiresAt) {
						// Set response headers
						for key, value := range cachedResponse.Headers {
							w.Header().Set(key, value)
						}
						w.Header().Set("X-Cache", "HIT")
						w.Header().Set("X-Cache-Key", cacheKey)
						w.Header().Set("X-Cache-Expires", cachedResponse.ExpiresAt.Format(time.RFC3339))

						// Write cached response
						w.WriteHeader(cachedResponse.StatusCode)
						w.Write(cachedResponse.Body)

						if config.Logger != nil {
							config.Logger.Debug("Cache hit",
								zap.String("path", r.URL.Path),
								zap.String("cache_key", cacheKey),
								zap.Int("status_code", cachedResponse.StatusCode))
						}
						return
					}
				}
			}

			// Cache miss or expired, proceed with handler
			rw := &responseWriter{
				ResponseWriter: w,
				statusCode:     200, // Default status code
				headers:        make(map[string]string),
			}

			// Call the next handler
			next.ServeHTTP(rw, r)

			// Check if response should be cached
			if shouldCache(rw.statusCode, rw.contentType) && rw.body != nil {
				// Extract headers
				headers := extractHeaders(rw.ResponseWriter.Header(), config.IncludeHeaders)

				// Create cached response
				cachedResponse := CachedResponse{
					StatusCode:    rw.statusCode,
					Headers:       headers,
					Body:          rw.body.Bytes(),
					ContentType:   rw.contentType,
					ContentLength: rw.contentLength,
					CachedAt:      time.Now(),
					ExpiresAt:     time.Now().Add(config.TTL),
				}

				// Cache the response
				if err := cacheService.Set(cacheKey, cachedResponse, config.TTL); err != nil {
					if config.Logger != nil {
						config.Logger.Error("Failed to cache response",
							zap.String("path", r.URL.Path),
							zap.String("cache_key", cacheKey),
							zap.Error(err))
					}
				} else {
					// Set cache headers
					w.Header().Set("X-Cache", "MISS")
					w.Header().Set("X-Cache-Key", cacheKey)
					w.Header().Set("X-Cache-Expires", cachedResponse.ExpiresAt.Format(time.RFC3339))

					if config.Logger != nil {
						config.Logger.Debug("Cache miss - response cached",
							zap.String("path", r.URL.Path),
							zap.String("cache_key", cacheKey),
							zap.Int("status_code", rw.statusCode),
							zap.Duration("ttl", config.TTL))
					}
				}
			}
		})
	}
}

// CacheMiddlewareWithTTL creates a middleware with a specific TTL
func CacheMiddlewareWithTTL(ttl time.Duration) func(http.Handler) http.Handler {
	config := DefaultCacheConfig()
	config.TTL = ttl
	return CacheMiddleware(config)
}

// CacheMiddlewareForPaths creates a middleware that only caches specific paths
func CacheMiddlewareForPaths(paths []string, config *CacheConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultCacheConfig()
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if path should be cached
			shouldCachePath := false
			for _, path := range paths {
				if strings.HasPrefix(r.URL.Path, path) {
					shouldCachePath = true
					break
				}
			}

			if !shouldCachePath {
				next.ServeHTTP(w, r)
				return
			}

			// Use the main cache middleware
			CacheMiddleware(config)(next).ServeHTTP(w, r)
		})
	}
}

// CacheMiddlewareWithExclusions creates a middleware that excludes specific paths
func CacheMiddlewareWithExclusions(exclusions []string, config *CacheConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultCacheConfig()
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if path should be excluded
			for _, exclusion := range exclusions {
				if strings.HasPrefix(r.URL.Path, exclusion) {
					next.ServeHTTP(w, r)
					return
				}
			}

			// Use the main cache middleware
			CacheMiddleware(config)(next).ServeHTTP(w, r)
		})
	}
}

// CacheInvalidationMiddleware creates a middleware that invalidates cache on specific operations
func CacheInvalidationMiddleware(patterns []string, config *CacheConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultCacheConfig()
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Call the next handler first
			next.ServeHTTP(w, r)

			// Check if this request should trigger cache invalidation
			shouldInvalidate := false
			for _, pattern := range patterns {
				if strings.Contains(r.URL.Path, pattern) {
					shouldInvalidate = true
					break
				}
			}

			if shouldInvalidate {
				cacheService := services.GetCacheService()
				if cacheService != nil {
					// Invalidate cache based on the operation
					for _, pattern := range patterns {
						if strings.Contains(r.URL.Path, pattern) {
							invalidationPattern := fmt.Sprintf("%s*", pattern)
							if err := cacheService.InvalidatePattern(invalidationPattern); err != nil {
								if config.Logger != nil {
									config.Logger.Error("Failed to invalidate cache",
										zap.String("path", r.URL.Path),
										zap.String("pattern", invalidationPattern),
										zap.Error(err))
								}
							} else {
								if config.Logger != nil {
									config.Logger.Info("Cache invalidated",
										zap.String("path", r.URL.Path),
										zap.String("pattern", invalidationPattern))
								}
							}
						}
					}
				}
			}
		})
	}
}

// CacheStatsMiddleware creates a middleware that provides cache statistics
func CacheStatsMiddleware(config *CacheConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultCacheConfig()
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Add cache stats to response headers
			cacheService := services.GetCacheService()
			if cacheService != nil {
				if stats, err := cacheService.GetStats(); err == nil {
					w.Header().Set("X-Cache-Hits", fmt.Sprintf("%d", stats.Hits))
					w.Header().Set("X-Cache-Misses", fmt.Sprintf("%d", stats.Misses))
					w.Header().Set("X-Cache-Hit-Rate", fmt.Sprintf("%.2f", stats.HitRate))
					w.Header().Set("X-Cache-Total-Keys", fmt.Sprintf("%d", stats.TotalKeys))
				}
			}

			next.ServeHTTP(w, r)
		})
	}
}
