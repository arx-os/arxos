package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"hash/fnv"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// CacheStrategy defines different caching strategies
type CacheStrategy string

const (
	StrategyLRU          CacheStrategy = "lru"
	StrategyLFU          CacheStrategy = "lfu"
	StrategyTTL          CacheStrategy = "ttl"
	StrategyWriteThrough CacheStrategy = "write_through"
	StrategyWriteBack    CacheStrategy = "write_back"
)

// CacheConfig defines configuration for advanced caching
type CacheConfig struct {
	Strategy          CacheStrategy `json:"strategy"`
	MaxEntries        int64         `json:"max_entries"`
	MaxSizeBytes      int64         `json:"max_size_bytes"`
	DefaultTTL        time.Duration `json:"default_ttl"`
	CleanupInterval   time.Duration `json:"cleanup_interval"`
	EnableMetrics     bool          `json:"enable_metrics"`
	EnablePersistence bool          `json:"enable_persistence"`
	PersistencePath   string        `json:"persistence_path"`
}

// CacheEntry represents a cached item with metadata
type CacheEntry struct {
	Key         string                 `json:"key"`
	Value       interface{}            `json:"value"`
	CreatedAt   time.Time              `json:"created_at"`
	AccessedAt  time.Time              `json:"accessed_at"`
	TTL         time.Duration          `json:"ttl"`
	AccessCount int64                  `json:"access_count"`
	Size        int64                  `json:"size"`
	Tags        []string               `json:"tags"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// CacheMetrics tracks cache performance
type CacheMetrics struct {
	Hits              int64         `json:"hits"`
	Misses            int64         `json:"misses"`
	Evictions         int64         `json:"evictions"`
	TotalSize         int64         `json:"total_size"`
	EntryCount        int64         `json:"entry_count"`
	HitRate           float64       `json:"hit_rate"`
	AverageAccessTime time.Duration `json:"average_access_time"`
}

// AdvancedCache provides sophisticated caching capabilities
type AdvancedCache struct {
	mu       sync.RWMutex
	entries  map[string]*CacheEntry
	config   *CacheConfig
	metrics  *CacheMetrics
	stopChan chan struct{}

	// Strategy-specific data structures
	lruOrder []string                   // For LRU strategy
	lfuCount map[string]int64           // For LFU strategy
	tags     map[string]map[string]bool // Tag-based indexing

	// Persistence
	persistence *CachePersistence
}

// CachePersistence handles cache persistence
type CachePersistence struct {
	filePath string
	enabled  bool
}

// NewAdvancedCache creates a new advanced cache instance
func NewAdvancedCache(config *CacheConfig) *AdvancedCache {
	if config == nil {
		config = &CacheConfig{
			Strategy:        StrategyLRU,
			MaxEntries:      10000,
			MaxSizeBytes:    100 * 1024 * 1024, // 100MB
			DefaultTTL:      5 * time.Minute,
			CleanupInterval: 1 * time.Minute,
			EnableMetrics:   true,
		}
	}

	cache := &AdvancedCache{
		entries:  make(map[string]*CacheEntry),
		config:   config,
		metrics:  &CacheMetrics{},
		stopChan: make(chan struct{}),
		lruOrder: make([]string, 0),
		lfuCount: make(map[string]int64),
		tags:     make(map[string]map[string]bool),
	}

	if config.EnablePersistence {
		cache.persistence = &CachePersistence{
			filePath: config.PersistencePath,
			enabled:  true,
		}
	}

	// Start cleanup goroutine
	go cache.cleanupRoutine()

	// Load from persistence if enabled
	if cache.persistence != nil && cache.persistence.enabled {
		cache.loadFromPersistence()
	}

	return cache
}

// Get retrieves a value from the cache
func (c *AdvancedCache) Get(ctx context.Context, key string) (interface{}, bool) {
	start := time.Now()
	defer func() {
		c.updateAccessTime(time.Since(start))
	}()

	c.mu.RLock()
	entry, exists := c.entries[key]
	c.mu.RUnlock()

	if !exists {
		c.metrics.Misses++
		return nil, false
	}

	// Check TTL
	if c.isExpired(entry) {
		c.mu.Lock()
		delete(c.entries, key)
		c.removeFromStrategy(key)
		c.mu.Unlock()
		c.metrics.Misses++
		return nil, false
	}

	// Update access metadata
	c.mu.Lock()
	entry.AccessedAt = time.Now()
	entry.AccessCount++
	c.updateStrategyAccess(key)
	c.mu.Unlock()

	c.metrics.Hits++
	return entry.Value, true
}

// Set stores a value in the cache
func (c *AdvancedCache) Set(ctx context.Context, key string, value interface{}, options *CacheOptions) error {
	if options == nil {
		options = &CacheOptions{}
	}

	// Calculate size
	size := c.calculateSize(value)

	// Check if we need to evict
	c.mu.Lock()
	defer c.mu.Unlock()

	if size > c.config.MaxSizeBytes {
		return fmt.Errorf("value size %d exceeds max cache size %d", size, c.config.MaxSizeBytes)
	}

	// Evict if necessary
	for c.getTotalSize()+size > c.config.MaxSizeBytes || int64(len(c.entries)) >= c.config.MaxEntries {
		if !c.evictEntry() {
			break
		}
	}

	// Create entry
	entry := &CacheEntry{
		Key:         key,
		Value:       value,
		CreatedAt:   time.Now(),
		AccessedAt:  time.Now(),
		TTL:         options.TTL,
		AccessCount: 0,
		Size:        size,
		Tags:        options.Tags,
		Metadata:    options.Metadata,
	}

	if entry.TTL == 0 {
		entry.TTL = c.config.DefaultTTL
	}

	// Store entry
	c.entries[key] = entry
	c.addToStrategy(key)
	c.updateTags(key, options.Tags)

	// Persist if enabled
	if c.persistence != nil && c.persistence.enabled {
		go c.persistEntry(entry)
	}

	return nil
}

// Delete removes a value from the cache
func (c *AdvancedCache) Delete(ctx context.Context, key string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	entry, exists := c.entries[key]
	if !exists {
		return nil
	}

	delete(c.entries, key)
	c.removeFromStrategy(key)
	c.removeFromTags(key, entry.Tags)

	return nil
}

// InvalidateByTag removes all entries with a specific tag
func (c *AdvancedCache) InvalidateByTag(ctx context.Context, tag string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	keys, exists := c.tags[tag]
	if !exists {
		return nil
	}

	for key := range keys {
		if entry, exists := c.entries[key]; exists {
			delete(c.entries, key)
			c.removeFromStrategy(key)
			c.removeFromTags(key, entry.Tags)
		}
	}

	return nil
}

// GetMetrics returns cache performance metrics
func (c *AdvancedCache) GetMetrics() *CacheMetrics {
	c.mu.RLock()
	defer c.mu.RUnlock()

	metrics := *c.metrics
	metrics.EntryCount = int64(len(c.entries))
	metrics.TotalSize = c.getTotalSize()

	if metrics.Hits+metrics.Misses > 0 {
		metrics.HitRate = float64(metrics.Hits) / float64(metrics.Hits+metrics.Misses)
	}

	return &metrics
}

// Clear removes all entries from the cache
func (c *AdvancedCache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.entries = make(map[string]*CacheEntry)
	c.lruOrder = make([]string, 0)
	c.lfuCount = make(map[string]int64)
	c.tags = make(map[string]map[string]bool)
	c.metrics = &CacheMetrics{}
}

// Close gracefully shuts down the cache
func (c *AdvancedCache) Close() error {
	close(c.stopChan)

	if c.persistence != nil && c.persistence.enabled {
		return c.saveToPersistence()
	}

	return nil
}

// CacheOptions defines options for cache operations
type CacheOptions struct {
	TTL      time.Duration          `json:"ttl"`
	Tags     []string               `json:"tags"`
	Metadata map[string]interface{} `json:"metadata"`
}

// Helper methods

func (c *AdvancedCache) isExpired(entry *CacheEntry) bool {
	return time.Since(entry.CreatedAt) > entry.TTL
}

func (c *AdvancedCache) calculateSize(value interface{}) int64 {
	data, err := json.Marshal(value)
	if err != nil {
		return 0
	}
	return int64(len(data))
}

func (c *AdvancedCache) getTotalSize() int64 {
	var total int64
	for _, entry := range c.entries {
		total += entry.Size
	}
	return total
}

func (c *AdvancedCache) updateAccessTime(duration time.Duration) {
	if c.config.EnableMetrics {
		c.metrics.AverageAccessTime = (c.metrics.AverageAccessTime + duration) / 2
	}
}

func (c *AdvancedCache) addToStrategy(key string) {
	switch c.config.Strategy {
	case StrategyLRU:
		c.lruOrder = append(c.lruOrder, key)
	case StrategyLFU:
		c.lfuCount[key] = 0
	}
}

func (c *AdvancedCache) removeFromStrategy(key string) {
	switch c.config.Strategy {
	case StrategyLRU:
		for i, k := range c.lruOrder {
			if k == key {
				c.lruOrder = append(c.lruOrder[:i], c.lruOrder[i+1:]...)
				break
			}
		}
	case StrategyLFU:
		delete(c.lfuCount, key)
	}
}

func (c *AdvancedCache) updateStrategyAccess(key string) {
	switch c.config.Strategy {
	case StrategyLRU:
		// Move to end of LRU order
		for i, k := range c.lruOrder {
			if k == key {
				// Remove from current position
				c.lruOrder = append(c.lruOrder[:i], c.lruOrder[i+1:]...)
				// Add to end
				c.lruOrder = append(c.lruOrder, key)
				break
			}
		}
	case StrategyLFU:
		c.lfuCount[key]++
	}
}

func (c *AdvancedCache) evictEntry() bool {
	switch c.config.Strategy {
	case StrategyLRU:
		if len(c.lruOrder) == 0 {
			return false
		}
		key := c.lruOrder[0]
		c.lruOrder = c.lruOrder[1:]
		if entry, exists := c.entries[key]; exists {
			delete(c.entries, key)
			c.removeFromTags(key, entry.Tags)
			c.metrics.Evictions++
			return true
		}
	case StrategyLFU:
		var minKey string
		var minCount int64 = -1
		for k, count := range c.lfuCount {
			if minCount == -1 || count < minCount {
				minKey = k
				minCount = count
			}
		}
		if minKey != "" {
			if entry, exists := c.entries[minKey]; exists {
				delete(c.entries, minKey)
				c.removeFromTags(minKey, entry.Tags)
				delete(c.lfuCount, minKey)
				c.metrics.Evictions++
				return true
			}
		}
	}
	return false
}

func (c *AdvancedCache) updateTags(key string, tags []string) {
	for _, tag := range tags {
		if c.tags[tag] == nil {
			c.tags[tag] = make(map[string]bool)
		}
		c.tags[tag][key] = true
	}
}

func (c *AdvancedCache) removeFromTags(key string, tags []string) {
	for _, tag := range tags {
		if c.tags[tag] != nil {
			delete(c.tags[tag], key)
			if len(c.tags[tag]) == 0 {
				delete(c.tags, tag)
			}
		}
	}
}

func (c *AdvancedCache) cleanupRoutine() {
	interval := c.config.CleanupInterval
	if interval <= 0 {
		interval = 1 * time.Minute // Default cleanup interval
	}

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.cleanupExpired()
		case <-c.stopChan:
			return
		}
	}
}

func (c *AdvancedCache) cleanupExpired() {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	for key, entry := range c.entries {
		if now.Sub(entry.CreatedAt) > entry.TTL {
			delete(c.entries, key)
			c.removeFromStrategy(key)
			c.removeFromTags(key, entry.Tags)
			c.metrics.Evictions++
		}
	}
}

// Persistence methods
func (c *AdvancedCache) persistEntry(entry *CacheEntry) {
	// Implementation would save to disk
	logger.Debug("Persisting cache entry: %s", entry.Key)
}

func (c *AdvancedCache) loadFromPersistence() {
	// Implementation would load from disk
	logger.Debug("Loading cache from persistence")
}

func (c *AdvancedCache) saveToPersistence() error {
	// Implementation would save all entries to disk
	logger.Debug("Saving cache to persistence")
	return nil
}

// GenerateCacheKey creates a consistent cache key from components
func GenerateCacheKey(components ...string) string {
	h := fnv.New32a()
	for _, component := range components {
		h.Write([]byte(component))
		h.Write([]byte(":"))
	}
	return fmt.Sprintf("%x", h.Sum32())
}
