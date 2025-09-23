package cache

import (
	"sync/atomic"
	"time"
)

// CacheMetrics tracks cache performance metrics
type CacheMetrics struct {
	Hits       atomic.Uint64
	Misses     atomic.Uint64
	Sets       atomic.Uint64
	Deletes    atomic.Uint64
	Evictions  atomic.Uint64
	Expirations atomic.Uint64
}

// IncrementHits increments the hit counter
func (m *CacheMetrics) IncrementHits() {
	m.Hits.Add(1)
}

// IncrementMisses increments the miss counter
func (m *CacheMetrics) IncrementMisses() {
	m.Misses.Add(1)
}

// IncrementSets increments the set counter
func (m *CacheMetrics) IncrementSets() {
	m.Sets.Add(1)
}

// IncrementDeletes increments the delete counter
func (m *CacheMetrics) IncrementDeletes() {
	m.Deletes.Add(1)
}

// IncrementEvictions increments the eviction counter
func (m *CacheMetrics) IncrementEvictions() {
	m.Evictions.Add(1)
}

// IncrementExpirations increments the expiration counter
func (m *CacheMetrics) IncrementExpirations() {
	m.Expirations.Add(1)
}

// GetHitRate returns the cache hit rate as a percentage
func (m *CacheMetrics) GetHitRate() float64 {
	hits := m.Hits.Load()
	misses := m.Misses.Load()
	total := hits + misses
	if total == 0 {
		return 0
	}
	return float64(hits) / float64(total) * 100
}

// Stats returns a snapshot of current metrics
type Stats struct {
	Hits        uint64
	Misses      uint64
	Sets        uint64
	Deletes     uint64
	Evictions   uint64
	Expirations uint64
	HitRate     float64
}

// GetStats returns current cache statistics
func (m *CacheMetrics) GetStats() Stats {
	return Stats{
		Hits:        m.Hits.Load(),
		Misses:      m.Misses.Load(),
		Sets:        m.Sets.Load(),
		Deletes:     m.Deletes.Load(),
		Evictions:   m.Evictions.Load(),
		Expirations: m.Expirations.Load(),
		HitRate:     m.GetHitRate(),
	}
}

// Reset resets all metrics to zero
func (m *CacheMetrics) Reset() {
	m.Hits.Store(0)
	m.Misses.Store(0)
	m.Sets.Store(0)
	m.Deletes.Store(0)
	m.Evictions.Store(0)
	m.Expirations.Store(0)
}

// CacheOptions configures cache behavior
type CacheOptions struct {
	// CleanupInterval specifies how often to clean up expired items
	// Default is 1 minute if not specified
	CleanupInterval time.Duration

	// EnableMetrics enables metrics collection
	EnableMetrics bool

	// OnEviction is called when an item is evicted
	OnEviction func(key string, value interface{})
}