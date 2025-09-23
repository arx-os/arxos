package cache

import (
	"container/list"
	"sync"
	"time"
)

// LRUCacheWithMetrics extends LRUCache with metrics tracking
type LRUCacheWithMetrics struct {
	capacity   int
	items      map[string]*cacheItem
	list       *list.List
	mu         sync.RWMutex
	metrics    *CacheMetrics
	onEviction func(key string, value interface{})
}

// NewLRUCacheWithMetrics creates a new LRU cache with metrics
func NewLRUCacheWithMetrics(capacity int, opts *CacheOptions) *LRUCacheWithMetrics {
	cache := &LRUCacheWithMetrics{
		capacity: capacity,
		items:    make(map[string]*cacheItem),
		list:     list.New(),
	}

	if opts != nil {
		if opts.EnableMetrics {
			cache.metrics = &CacheMetrics{}
		}
		cache.onEviction = opts.OnEviction
	}

	return cache
}

// Get retrieves a value from cache
func (c *LRUCacheWithMetrics) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	item, exists := c.items[key]
	c.mu.RUnlock()

	if !exists {
		if c.metrics != nil {
			c.metrics.IncrementMisses()
		}
		return nil, false
	}

	// Check if expired
	if time.Now().After(item.expireTime) {
		c.Delete(key)
		if c.metrics != nil {
			c.metrics.IncrementExpirations()
			c.metrics.IncrementMisses()
		}
		return nil, false
	}

	// Move to front (most recently used)
	c.mu.Lock()
	c.list.MoveToFront(item.element)
	c.mu.Unlock()

	if c.metrics != nil {
		c.metrics.IncrementHits()
	}

	return item.value, true
}

// Set adds or updates a value in cache
func (c *LRUCacheWithMetrics) Set(key string, value interface{}, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.metrics != nil {
		c.metrics.IncrementSets()
	}

	// Update existing item
	if item, exists := c.items[key]; exists {
		item.value = value
		item.expireTime = time.Now().Add(ttl)
		c.list.MoveToFront(item.element)
		return
	}

	// Add new item
	if c.list.Len() >= c.capacity {
		// Evict least recently used
		oldest := c.list.Back()
		if oldest != nil {
			c.removeElementWithMetrics(oldest)
		}
	}

	item := &cacheItem{
		key:        key,
		value:      value,
		expireTime: time.Now().Add(ttl),
	}
	element := c.list.PushFront(item)
	item.element = element
	c.items[key] = item
}

// Delete removes a key from cache
func (c *LRUCacheWithMetrics) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if item, exists := c.items[key]; exists {
		c.removeElement(item.element)
		if c.metrics != nil {
			c.metrics.IncrementDeletes()
		}
	}
}

// Clear removes all items from cache
func (c *LRUCacheWithMetrics) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.items = make(map[string]*cacheItem)
	c.list = list.New()
}

// Size returns the number of items in cache
func (c *LRUCacheWithMetrics) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.list.Len()
}

// GetMetrics returns cache metrics
func (c *LRUCacheWithMetrics) GetMetrics() *CacheMetrics {
	return c.metrics
}

// removeElement removes an element from the list (must be called with lock held)
func (c *LRUCacheWithMetrics) removeElement(e *list.Element) {
	c.list.Remove(e)
	item := e.Value.(*cacheItem)
	delete(c.items, item.key)
}

// removeElementWithMetrics removes an element and tracks eviction
func (c *LRUCacheWithMetrics) removeElementWithMetrics(e *list.Element) {
	item := e.Value.(*cacheItem)

	if c.metrics != nil {
		c.metrics.IncrementEvictions()
	}

	if c.onEviction != nil {
		c.onEviction(item.key, item.value)
	}

	c.removeElement(e)
}

// MemoryCacheWithOptions provides a memory cache with configurable options
type MemoryCacheWithOptions struct {
	data            map[string]*memoryCacheItem
	mu              sync.RWMutex
	stopCh          chan struct{}
	wg              sync.WaitGroup
	cleanupInterval time.Duration
	metrics         *CacheMetrics
}

// NewMemoryCacheWithOptions creates a new memory cache with options
func NewMemoryCacheWithOptions(opts *CacheOptions) *MemoryCacheWithOptions {
	cleanupInterval := 1 * time.Minute
	var metrics *CacheMetrics

	if opts != nil {
		if opts.CleanupInterval > 0 {
			cleanupInterval = opts.CleanupInterval
		}
		if opts.EnableMetrics {
			metrics = &CacheMetrics{}
		}
	}

	cache := &MemoryCacheWithOptions{
		data:            make(map[string]*memoryCacheItem),
		stopCh:          make(chan struct{}),
		cleanupInterval: cleanupInterval,
		metrics:         metrics,
	}

	// Start cleanup goroutine
	cache.wg.Add(1)
	go cache.cleanupExpired()
	return cache
}

// Get retrieves a value from cache
func (c *MemoryCacheWithOptions) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	item, exists := c.data[key]
	if !exists {
		if c.metrics != nil {
			c.metrics.IncrementMisses()
		}
		return nil, false
	}

	if time.Now().After(item.expireTime) {
		if c.metrics != nil {
			c.metrics.IncrementExpirations()
			c.metrics.IncrementMisses()
		}
		return nil, false
	}

	if c.metrics != nil {
		c.metrics.IncrementHits()
	}

	return item.value, true
}

// Set adds a value to cache with TTL
func (c *MemoryCacheWithOptions) Set(key string, value interface{}, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.metrics != nil {
		c.metrics.IncrementSets()
	}

	c.data[key] = &memoryCacheItem{
		value:      value,
		expireTime: time.Now().Add(ttl),
	}
}

// Delete removes a key from cache
func (c *MemoryCacheWithOptions) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if _, exists := c.data[key]; exists {
		delete(c.data, key)
		if c.metrics != nil {
			c.metrics.IncrementDeletes()
		}
	}
}

// Clear removes all items from cache
func (c *MemoryCacheWithOptions) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data = make(map[string]*memoryCacheItem)
}

// Size returns the number of items in cache
func (c *MemoryCacheWithOptions) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.data)
}

// GetMetrics returns cache metrics
func (c *MemoryCacheWithOptions) GetMetrics() *CacheMetrics {
	return c.metrics
}

// cleanupExpired removes expired items periodically
func (c *MemoryCacheWithOptions) cleanupExpired() {
	defer c.wg.Done()
	ticker := time.NewTicker(c.cleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-c.stopCh:
			return
		case <-ticker.C:
			now := time.Now()
			expired := 0
			c.mu.Lock()
			for key, item := range c.data {
				if now.After(item.expireTime) {
					delete(c.data, key)
					expired++
				}
			}
			c.mu.Unlock()

			if c.metrics != nil && expired > 0 {
				for i := 0; i < expired; i++ {
					c.metrics.IncrementExpirations()
				}
			}
		}
	}
}

// Close gracefully shuts down the cache
func (c *MemoryCacheWithOptions) Close() error {
	close(c.stopCh)
	c.wg.Wait()
	return nil
}