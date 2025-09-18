package cache

import (
	"container/list"
	"sync"
	"time"
)

// Cache interface defines cache operations
type Cache interface {
	Get(key string) (interface{}, bool)
	Set(key string, value interface{}, ttl time.Duration)
	Delete(key string)
	Clear()
	Size() int
}

// LRUCache implements a thread-safe LRU cache with TTL
type LRUCache struct {
	capacity int
	items    map[string]*cacheItem
	list     *list.List
	mu       sync.RWMutex
}

type cacheItem struct {
	key        string
	value      interface{}
	expireTime time.Time
	element    *list.Element
}

// NewLRUCache creates a new LRU cache with specified capacity
func NewLRUCache(capacity int) *LRUCache {
	return &LRUCache{
		capacity: capacity,
		items:    make(map[string]*cacheItem),
		list:     list.New(),
	}
}

// Get retrieves a value from cache
func (c *LRUCache) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	item, exists := c.items[key]
	c.mu.RUnlock()

	if !exists {
		return nil, false
	}

	// Check if expired
	if time.Now().After(item.expireTime) {
		c.Delete(key)
		return nil, false
	}

	// Move to front (most recently used)
	c.mu.Lock()
	c.list.MoveToFront(item.element)
	c.mu.Unlock()

	return item.value, true
}

// Set adds or updates a value in cache
func (c *LRUCache) Set(key string, value interface{}, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

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
			c.removeElement(oldest)
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
func (c *LRUCache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if item, exists := c.items[key]; exists {
		c.removeElement(item.element)
	}
}

// Clear removes all items from cache
func (c *LRUCache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.items = make(map[string]*cacheItem)
	c.list = list.New()
}

// Size returns the number of items in cache
func (c *LRUCache) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.list.Len()
}

// removeElement removes an element from the list (must be called with lock held)
func (c *LRUCache) removeElement(e *list.Element) {
	c.list.Remove(e)
	item := e.Value.(*cacheItem)
	delete(c.items, item.key)
}

// MemoryCache provides a simple in-memory cache with expiration
type MemoryCache struct {
	data map[string]*memoryCacheItem
	mu   sync.RWMutex
}

type memoryCacheItem struct {
	value      interface{}
	expireTime time.Time
}

// NewMemoryCache creates a new memory cache
func NewMemoryCache() *MemoryCache {
	cache := &MemoryCache{
		data: make(map[string]*memoryCacheItem),
	}
	// Start cleanup goroutine
	go cache.cleanupExpired()
	return cache
}

// Get retrieves a value from cache
func (c *MemoryCache) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	item, exists := c.data[key]
	if !exists {
		return nil, false
	}

	if time.Now().After(item.expireTime) {
		return nil, false
	}

	return item.value, true
}

// Set adds a value to cache with TTL
func (c *MemoryCache) Set(key string, value interface{}, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.data[key] = &memoryCacheItem{
		value:      value,
		expireTime: time.Now().Add(ttl),
	}
}

// Delete removes a key from cache
func (c *MemoryCache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.data, key)
}

// Clear removes all items from cache
func (c *MemoryCache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data = make(map[string]*memoryCacheItem)
}

// Size returns the number of items in cache
func (c *MemoryCache) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.data)
}

// cleanupExpired removes expired items periodically
func (c *MemoryCache) cleanupExpired() {
	ticker := time.NewTicker(1 * time.Minute)
	for range ticker.C {
		now := time.Now()
		c.mu.Lock()
		for key, item := range c.data {
			if now.After(item.expireTime) {
				delete(c.data, key)
			}
		}
		c.mu.Unlock()
	}
}
