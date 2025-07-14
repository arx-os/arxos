package gateway

import (
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.uber.org/zap"
)

// CacheManager manages response caching and cache operations
type CacheManager struct {
	config  CacheConfig
	logger  *zap.Logger
	cache   map[string]*CacheEntry
	mu      sync.RWMutex
	metrics *CacheMetrics
}

// CacheConfig defines cache configuration
type CacheConfig struct {
	Enabled         bool               `yaml:"enabled"`
	DefaultTTL      time.Duration      `yaml:"default_ttl"`
	MaxSize         int                `yaml:"max_size"`
	MaxMemory       int64              `yaml:"max_memory"`
	CleanupInterval time.Duration      `yaml:"cleanup_interval"`
	Compression     bool               `yaml:"compression"`
	CacheWarming    CacheWarmingConfig `yaml:"cache_warming"`
	Invalidation    InvalidationConfig `yaml:"invalidation"`
}

// CacheWarmingConfig defines cache warming configuration
type CacheWarmingConfig struct {
	Enabled     bool          `yaml:"enabled"`
	URLs        []string      `yaml:"urls"`
	Interval    time.Duration `yaml:"interval"`
	Concurrency int           `yaml:"concurrency"`
}

// InvalidationConfig defines cache invalidation configuration
type InvalidationConfig struct {
	Enabled       bool     `yaml:"enabled"`
	Patterns      []string `yaml:"patterns"`
	Headers       []string `yaml:"headers"`
	Methods       []string `yaml:"methods"`
	InvalidateAll bool     `yaml:"invalidate_all"`
}

// CacheEntry represents a cached response
type CacheEntry struct {
	Key         string
	Response    *CachedResponse
	CreatedAt   time.Time
	LastAccess  time.Time
	AccessCount int64
	Size        int64
	TTL         time.Duration
	mu          sync.RWMutex
}

// CachedResponse represents a cached HTTP response
type CachedResponse struct {
	StatusCode    int               `json:"status_code"`
	Headers       map[string]string `json:"headers"`
	Body          []byte            `json:"body"`
	ContentLength int64             `json:"content_length"`
	ContentType   string            `json:"content_type"`
	Compressed    bool              `json:"compressed"`
}

// CacheMetrics holds cache metrics
type CacheMetrics struct {
	hitsCounter          *prometheus.CounterVec
	missesCounter        *prometheus.CounterVec
	sizeGauge            *prometheus.GaugeVec
	evictionsCounter     *prometheus.CounterVec
	invalidationsCounter *prometheus.CounterVec
}

// NewCacheManager creates a new cache manager
func NewCacheManager(config CacheConfig) (*CacheManager, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	cm := &CacheManager{
		config: config,
		logger: logger,
		cache:  make(map[string]*CacheEntry),
	}

	// Initialize metrics
	cm.initializeMetrics()

	// Start cleanup goroutine if enabled
	if config.Enabled && config.CleanupInterval > 0 {
		go cm.startCleanup()
	}

	// Start cache warming if enabled
	if config.CacheWarming.Enabled {
		go cm.startCacheWarming()
	}

	return cm, nil
}

// initializeMetrics initializes cache metrics
func (cm *CacheManager) initializeMetrics() {
	cm.metrics = &CacheMetrics{
		hitsCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_cache_hits_total",
				Help: "Total cache hits",
			},
			[]string{"service", "path"},
		),
		missesCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_cache_misses_total",
				Help: "Total cache misses",
			},
			[]string{"service", "path"},
		),
		sizeGauge: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_cache_size",
				Help: "Cache size in bytes",
			},
			[]string{"service"},
		),
		evictionsCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_cache_evictions_total",
				Help: "Total cache evictions",
			},
			[]string{"service", "reason"},
		),
		invalidationsCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_cache_invalidations_total",
				Help: "Total cache invalidations",
			},
			[]string{"service", "pattern"},
		),
	}
}

// Get retrieves a cached response
func (cm *CacheManager) Get(key string) (*CachedResponse, bool) {
	if !cm.config.Enabled {
		return nil, false
	}

	cm.mu.RLock()
	entry, exists := cm.cache[key]
	cm.mu.RUnlock()

	if !exists {
		return nil, false
	}

	entry.mu.Lock()
	defer entry.mu.Unlock()

	// Check if entry is expired
	if time.Since(entry.CreatedAt) > entry.TTL {
		cm.mu.Lock()
		delete(cm.cache, key)
		cm.mu.Unlock()
		return nil, false
	}

	// Update access statistics
	entry.LastAccess = time.Now()
	entry.AccessCount++

	cm.logger.Debug("Cache hit",
		zap.String("key", key),
		zap.Int64("access_count", entry.AccessCount),
	)

	return entry.Response, true
}

// Set stores a response in the cache
func (cm *CacheManager) Set(key string, response *CachedResponse, ttl time.Duration) error {
	if !cm.config.Enabled {
		return nil
	}

	// Check cache size limits
	if err := cm.checkSizeLimits(); err != nil {
		cm.logger.Warn("Cache size limit reached, evicting entries",
			zap.Error(err),
		)
		cm.evictEntries()
	}

	entry := &CacheEntry{
		Key:         key,
		Response:    response,
		CreatedAt:   time.Now(),
		LastAccess:  time.Now(),
		AccessCount: 1,
		Size:        int64(len(response.Body)),
		TTL:         ttl,
	}

	cm.mu.Lock()
	cm.cache[key] = entry
	cm.mu.Unlock()

	cm.logger.Debug("Cache entry stored",
		zap.String("key", key),
		zap.Int64("size", entry.Size),
		zap.Duration("ttl", ttl),
	)

	return nil
}

// Invalidate removes entries from the cache
func (cm *CacheManager) Invalidate(pattern string) int {
	if !cm.config.Enabled {
		return 0
	}

	cm.mu.Lock()
	defer cm.mu.Unlock()

	count := 0
	for key := range cm.cache {
		if cm.matchesPattern(key, pattern) {
			delete(cm.cache, key)
			count++
		}
	}

	if count > 0 {
		cm.metrics.invalidationsCounter.WithLabelValues("all", pattern).Add(float64(count))
		cm.logger.Info("Cache entries invalidated",
			zap.String("pattern", pattern),
			zap.Int("count", count),
		)
	}

	return count
}

// InvalidateAll removes all entries from the cache
func (cm *CacheManager) InvalidateAll() int {
	if !cm.config.Enabled {
		return 0
	}

	cm.mu.Lock()
	count := len(cm.cache)
	cm.cache = make(map[string]*CacheEntry)
	cm.mu.Unlock()

	if count > 0 {
		cm.metrics.invalidationsCounter.WithLabelValues("all", "all").Add(float64(count))
		cm.logger.Info("All cache entries invalidated",
			zap.Int("count", count),
		)
	}

	return count
}

// GenerateCacheKey generates a cache key from request
func (cm *CacheManager) GenerateCacheKey(request *http.Request, service string) string {
	// Create a hash of the request
	hash := md5.New()

	// Include method and path
	hash.Write([]byte(request.Method))
	hash.Write([]byte(request.URL.Path))

	// Include query parameters
	hash.Write([]byte(request.URL.RawQuery))

	// Include relevant headers
	relevantHeaders := []string{"Accept", "Accept-Encoding", "Authorization", "Content-Type"}
	for _, header := range relevantHeaders {
		if value := request.Header.Get(header); value != "" {
			hash.Write([]byte(header))
			hash.Write([]byte(value))
		}
	}

	// Include service name
	hash.Write([]byte(service))

	// Return hex string
	return hex.EncodeToString(hash.Sum(nil))
}

// ShouldCache determines if a response should be cached
func (cm *CacheManager) ShouldCache(request *http.Request, response *http.Response) bool {
	if !cm.config.Enabled {
		return false
	}

	// Check if method is cacheable
	if request.Method != "GET" && request.Method != "HEAD" {
		return false
	}

	// Check if status code is cacheable
	if response.StatusCode < 200 || response.StatusCode >= 400 {
		return false
	}

	// Check cache control headers
	cacheControl := response.Header.Get("Cache-Control")
	if cacheControl == "no-cache" || cacheControl == "no-store" {
		return false
	}

	// Check content type
	contentType := response.Header.Get("Content-Type")
	if contentType == "" {
		return false
	}

	// Only cache certain content types
	cacheableTypes := []string{"application/json", "text/html", "text/plain", "application/xml"}
	cacheable := false
	for _, cacheableType := range cacheableTypes {
		if contentType == cacheableType || (len(contentType) > len(cacheableType) && contentType[:len(cacheableType)] == cacheableType) {
			cacheable = true
			break
		}
	}

	return cacheable
}

// GetTTL gets the TTL for a response
func (cm *CacheManager) GetTTL(response *http.Response) time.Duration {
	// Check Cache-Control max-age
	if cacheControl := response.Header.Get("Cache-Control"); cacheControl != "" {
		// Parse max-age directive
		// This is a simplified implementation
		if maxAge := cm.parseMaxAge(cacheControl); maxAge > 0 {
			return maxAge
		}
	}

	// Check Expires header
	if expires := response.Header.Get("Expires"); expires != "" {
		if t, err := time.Parse(time.RFC1123, expires); err == nil {
			return time.Until(t)
		}
	}

	// Return default TTL
	return cm.config.DefaultTTL
}

// parseMaxAge parses max-age from Cache-Control header
func (cm *CacheManager) parseMaxAge(cacheControl string) time.Duration {
	// This is a simplified implementation
	// In a real implementation, you would properly parse the Cache-Control header
	if len(cacheControl) > 8 && cacheControl[:8] == "max-age=" {
		// Extract max-age value
		// This is a simplified implementation
		return cm.config.DefaultTTL
	}
	return 0
}

// checkSizeLimits checks if cache size limits are exceeded
func (cm *CacheManager) checkSizeLimits() error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	// Check entry count limit
	if cm.config.MaxSize > 0 && len(cm.cache) >= cm.config.MaxSize {
		return fmt.Errorf("cache size limit reached: %d entries", cm.config.MaxSize)
	}

	// Check memory limit
	if cm.config.MaxMemory > 0 {
		totalSize := int64(0)
		for _, entry := range cm.cache {
			entry.mu.RLock()
			totalSize += entry.Size
			entry.mu.RUnlock()
		}
		if totalSize >= cm.config.MaxMemory {
			return fmt.Errorf("cache memory limit reached: %d bytes", cm.config.MaxMemory)
		}
	}

	return nil
}

// evictEntries evicts entries from the cache
func (cm *CacheManager) evictEntries() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Simple LRU eviction
	// In a real implementation, you might use a more sophisticated algorithm
	var oldestKey string
	var oldestTime time.Time

	for key, entry := range cm.cache {
		entry.mu.RLock()
		if oldestKey == "" || entry.LastAccess.Before(oldestTime) {
			oldestKey = key
			oldestTime = entry.LastAccess
		}
		entry.mu.RUnlock()
	}

	if oldestKey != "" {
		delete(cm.cache, oldestKey)
		cm.metrics.evictionsCounter.WithLabelValues("all", "lru").Inc()
		cm.logger.Debug("Cache entry evicted",
			zap.String("key", oldestKey),
		)
	}
}

// matchesPattern checks if a key matches a pattern
func (cm *CacheManager) matchesPattern(key, pattern string) bool {
	// This is a simplified pattern matching
	// In a real implementation, you might use regex or glob patterns
	return key == pattern || (len(pattern) > 0 && len(key) >= len(pattern) && key[:len(pattern)] == pattern)
}

// startCleanup starts the cache cleanup process
func (cm *CacheManager) startCleanup() {
	ticker := time.NewTicker(cm.config.CleanupInterval)
	defer ticker.Stop()

	for range ticker.C {
		cm.cleanup()
	}
}

// cleanup removes expired entries from the cache
func (cm *CacheManager) cleanup() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	now := time.Now()
	expiredCount := 0

	for key, entry := range cm.cache {
		entry.mu.RLock()
		if now.Sub(entry.CreatedAt) > entry.TTL {
			delete(cm.cache, key)
			expiredCount++
		}
		entry.mu.RUnlock()
	}

	if expiredCount > 0 {
		cm.metrics.evictionsCounter.WithLabelValues("all", "expired").Add(float64(expiredCount))
		cm.logger.Info("Expired cache entries cleaned up",
			zap.Int("count", expiredCount),
		)
	}
}

// startCacheWarming starts the cache warming process
func (cm *CacheManager) startCacheWarming() {
	if len(cm.config.CacheWarming.URLs) == 0 {
		return
	}

	ticker := time.NewTicker(cm.config.CacheWarming.Interval)
	defer ticker.Stop()

	for range ticker.C {
		cm.warmCache()
	}
}

// warmCache warms the cache by pre-fetching URLs
func (cm *CacheManager) warmCache() {
	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	for _, url := range cm.config.CacheWarming.URLs {
		go func(url string) {
			req, err := http.NewRequest("GET", url, nil)
			if err != nil {
				cm.logger.Error("Failed to create cache warming request",
					zap.String("url", url),
					zap.Error(err),
				)
				return
			}

			resp, err := client.Do(req)
			if err != nil {
				cm.logger.Error("Failed to warm cache",
					zap.String("url", url),
					zap.Error(err),
				)
				return
			}
			defer resp.Body.Close()

			// Read response body
			body, err := io.ReadAll(resp.Body)
			if err != nil {
				cm.logger.Error("Failed to read cache warming response",
					zap.String("url", url),
					zap.Error(err),
				)
				return
			}

			// Create cached response
			cachedResp := &CachedResponse{
				StatusCode:    resp.StatusCode,
				Headers:       make(map[string]string),
				Body:          body,
				ContentLength: int64(len(body)),
				ContentType:   resp.Header.Get("Content-Type"),
			}

			// Copy headers
			for key, values := range resp.Header {
				if len(values) > 0 {
					cachedResp.Headers[key] = values[0]
				}
			}

			// Store in cache
			key := cm.GenerateCacheKey(req, "cache-warming")
			cm.Set(key, cachedResp, cm.config.DefaultTTL)

			cm.logger.Info("Cache warmed",
				zap.String("url", url),
				zap.String("key", key),
			)
		}(url)
	}
}

// GetStats returns cache statistics
func (cm *CacheManager) GetStats() map[string]interface{} {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	totalSize := int64(0)
	totalAccess := int64(0)
	oldestEntry := time.Now()
	newestEntry := time.Time{}

	for _, entry := range cm.cache {
		entry.mu.RLock()
		totalSize += entry.Size
		totalAccess += entry.AccessCount
		if entry.CreatedAt.Before(oldestEntry) {
			oldestEntry = entry.CreatedAt
		}
		if entry.CreatedAt.After(newestEntry) {
			newestEntry = entry.CreatedAt
		}
		entry.mu.RUnlock()
	}

	return map[string]interface{}{
		"enabled":       cm.config.Enabled,
		"total_entries": len(cm.cache),
		"total_size":    totalSize,
		"total_access":  totalAccess,
		"oldest_entry":  oldestEntry,
		"newest_entry":  newestEntry,
		"max_size":      cm.config.MaxSize,
		"max_memory":    cm.config.MaxMemory,
		"default_ttl":   cm.config.DefaultTTL,
		"compression":   cm.config.Compression,
	}
}

// UpdateConfig updates the cache configuration
func (cm *CacheManager) UpdateConfig(config CacheConfig) error {
	cm.config = config
	cm.logger.Info("Cache configuration updated")
	return nil
}
