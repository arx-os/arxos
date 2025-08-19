package middleware

import (
	"bytes"
	"crypto/md5"
	"fmt"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/arxos/arxos/core/backend/services"
)

// CacheConfig holds configuration for the cache middleware
type CacheConfig struct {
	TTL            time.Duration
	KeyPrefix      string
	IncludeQuery   bool
	IncludeHeaders []string
	ExcludePaths   []string
	Logger         interface{} // Keep for compatibility but not used
	GetTTL         func(r *http.Request) time.Duration
}

// CachedResponse represents a cached HTTP response
type CachedResponse struct {
	StatusCode int               `json:"status_code"`
	Headers    map[string]string `json:"headers"`
	Body       []byte            `json:"body"`
	CachedAt   time.Time         `json:"cached_at"`
	ExpiresAt  time.Time         `json:"expires_at"`
}

// responseWriter wraps http.ResponseWriter to capture the response
type responseWriter struct {
	http.ResponseWriter
	statusCode int
	body       bytes.Buffer
	headers    map[string]string
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	rw.body.Write(b)
	return rw.ResponseWriter.Write(b)
}

// DefaultCacheConfig returns a default cache configuration
func DefaultCacheConfig() *CacheConfig {
	return &CacheConfig{
		TTL:          5 * time.Minute,
		KeyPrefix:    "http_cache:",
		IncludeQuery: true,
		ExcludePaths: []string{
			"/api/ws",
			"/api/health",
			"/api/metrics",
		},
		GetTTL: func(r *http.Request) time.Duration {
			// Default TTL based on method
			switch r.Method {
			case http.MethodGet:
				return 5 * time.Minute
			case http.MethodHead:
				return 5 * time.Minute
			default:
				return 0 // Don't cache non-GET/HEAD requests
			}
		},
	}
}

// generateCacheKey generates a unique cache key for the request
func generateCacheKey(r *http.Request, config *CacheConfig) (string, error) {
	parts := []string{
		config.KeyPrefix,
		r.Method,
		r.URL.Path,
	}

	// Include query parameters if configured
	if config.IncludeQuery && r.URL.RawQuery != "" {
		parts = append(parts, r.URL.RawQuery)
	}

	// Include specific headers if configured
	for _, header := range config.IncludeHeaders {
		if value := r.Header.Get(header); value != "" {
			parts = append(parts, fmt.Sprintf("%s:%s", header, value))
		}
	}

	// Create MD5 hash of the key parts
	key := strings.Join(parts, "|")
	hash := md5.Sum([]byte(key))
	return fmt.Sprintf("%x", hash), nil
}

// shouldCache determines if the request/response should be cached
func shouldCache(r *http.Request, statusCode int, config *CacheConfig) bool {
	// Only cache GET and HEAD requests
	if r.Method != http.MethodGet && r.Method != http.MethodHead {
		return false
	}

	// Check excluded paths
	for _, path := range config.ExcludePaths {
		if strings.HasPrefix(r.URL.Path, path) {
			return false
		}
	}

	// Only cache successful responses (2xx) and not modified (304)
	if statusCode < 200 || (statusCode >= 300 && statusCode != 304) {
		return false
	}

	return true
}

// CacheMiddleware creates a caching middleware with the given configuration
func CacheMiddleware(config *CacheConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultCacheConfig()
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip caching if configured TTL is 0
			ttl := config.GetTTL(r)
			if ttl == 0 {
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
				// Log error and continue without caching
				log.Printf("Failed to generate cache key for %s: %v", r.URL.Path, err)
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

						log.Printf("Cache hit for %s (key: %s, status: %d)",
							r.URL.Path, cacheKey, cachedResponse.StatusCode)
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

			// Cache the response if appropriate
			if shouldCache(r, rw.statusCode, config) {
				// Capture response headers
				for key := range rw.Header() {
					rw.headers[key] = rw.Header().Get(key)
				}

				// Create cached response
				cachedResponse := CachedResponse{
					StatusCode: rw.statusCode,
					Headers:    rw.headers,
					Body:       rw.body.Bytes(),
					CachedAt:   time.Now(),
					ExpiresAt:  time.Now().Add(ttl),
				}

				// Store in cache
				if err := cacheService.Set(cacheKey, cachedResponse, ttl); err != nil {
					log.Printf("Failed to cache response for %s: %v", r.URL.Path, err)
				} else {
					log.Printf("Response cached for %s (key: %s, ttl: %v)",
						r.URL.Path, cacheKey, ttl)
				}
			}

			// Set cache headers
			w.Header().Set("X-Cache", "MISS")
			w.Header().Set("X-Cache-Key", cacheKey)
		})
	}
}

// InvalidationMiddleware creates a middleware that invalidates cache on mutations
func InvalidationMiddleware(patterns []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if this is a mutation request
			if r.Method == http.MethodPost || r.Method == http.MethodPut ||
				r.Method == http.MethodPatch || r.Method == http.MethodDelete {

				// Get cache service
				cacheService := services.GetCacheService()
				if cacheService != nil {
					// Invalidate cache patterns
					for _, pattern := range patterns {
						if err := cacheService.Delete(pattern); err != nil {
							log.Printf("Failed to invalidate cache for %s %s: %v",
								r.Method, r.URL.Path, err)
						} else {
							log.Printf("Cache invalidated for %s %s", r.Method, r.URL.Path)
						}
					}
				}
			}

			// Proceed with the request
			next.ServeHTTP(w, r)
		})
	}
}