package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
)

// CacheLayer represents different cache tiers
type CacheLayer int

const (
	L1Memory  CacheLayer = iota // In-memory cache (fastest, smallest)
	L2Local                     // Local disk cache (fast, persistent)
	L3Network                   // Network cache (Redis, slower but shared)
)

// UnifiedCache implements a proper multi-tier caching strategy
type UnifiedCache struct {
	config *config.Config
	logger domain.Logger

	// L1: In-memory cache
	l1Cache map[string]*CacheEntry
	l1Mu    sync.RWMutex

	// L2: Local disk cache
	l2Path string
	l2Mu   sync.RWMutex

	// L3: Network cache (Redis)
	l3Cache *RedisL3Cache

	// Statistics
	stats   *CacheStats
	statsMu sync.RWMutex
}

// CacheEntry represents a cached item with metadata
type CacheEntry struct {
	Key      string      `json:"key"`
	Value    interface{} `json:"value"`
	Created  time.Time   `json:"created"`
	Expires  time.Time   `json:"expires"`
	Layer    CacheLayer  `json:"layer"`
	HitCount int64       `json:"hit_count"`
	LastHit  time.Time   `json:"last_hit"`
	Size     int64       `json:"size"`
	Tags     []string    `json:"tags,omitempty"`
}

// CacheStats tracks cache performance
type CacheStats struct {
	L1Hits      int64     `json:"l1_hits"`
	L1Misses    int64     `json:"l1_misses"`
	L2Hits      int64     `json:"l2_hits"`
	L2Misses    int64     `json:"l2_misses"`
	L3Hits      int64     `json:"l3_hits"`
	L3Misses    int64     `json:"l3_misses"`
	TotalHits   int64     `json:"total_hits"`
	TotalMisses int64     `json:"total_misses"`
	LastReset   time.Time `json:"last_reset"`
}

// CacheConfig defines cache behavior per layer
type CacheConfig struct {
	L1Enabled    bool          `json:"l1_enabled"`
	L1MaxSize    int64         `json:"l1_max_size"` // Max entries in L1
	L1DefaultTTL time.Duration `json:"l1_default_ttl"`

	L2Enabled    bool          `json:"l2_enabled"`
	L2MaxSize    int64         `json:"l2_max_size"` // Max disk usage
	L2DefaultTTL time.Duration `json:"l2_default_ttl"`
	L2Path       string        `json:"l2_path"`

	L3Enabled    bool          `json:"l3_enabled"`
	L3DefaultTTL time.Duration `json:"l3_default_ttl"`
}

// NewUnifiedCache creates a new unified cache instance
func NewUnifiedCache(cfg *config.Config, logger domain.Logger) (*UnifiedCache, error) {
	cache := &UnifiedCache{
		config:  cfg,
		logger:  logger,
		l1Cache: make(map[string]*CacheEntry),
		l2Path:  filepath.Join(cfg.GetCachePath(), "l2"),
		stats:   &CacheStats{LastReset: time.Now()},
	}

	// Initialize L2 directory
	if err := os.MkdirAll(cache.l2Path, 0755); err != nil {
		return nil, fmt.Errorf("failed to create L2 cache directory: %w", err)
	}

	// Initialize L3 if configured
	if cfg.UnifiedCache.L3.Enabled {
		l3Cache, err := NewRedisL3Cache(&cfg.UnifiedCache, logger)
		if err != nil {
			cache.logger.Warn("Failed to initialize L3 cache", "error", err)
		} else {
			cache.l3Cache = l3Cache
			cache.logger.Info("L3 cache (Redis) initialized successfully")
		}
	}

	return cache, nil
}

// Get retrieves a value from the cache using the multi-tier strategy
func (uc *UnifiedCache) Get(ctx context.Context, key string) (interface{}, error) {
	// Try L1 (in-memory) first
	if value, found := uc.getFromL1(key); found {
		uc.incrementStats("l1_hit")
		return value, nil
	}
	uc.incrementStats("l1_miss")

	// Try L2 (local disk)
	if value, found := uc.getFromL2(key); found {
		// Promote to L1
		uc.setInL1(key, value, uc.getDefaultTTL(L1Memory))
		uc.incrementStats("l2_hit")
		return value, nil
	}
	uc.incrementStats("l2_miss")

	// Try L3 (network/Redis) if enabled
	if uc.l3Cache != nil {
		if value, err := uc.l3Cache.Get(ctx, key); err == nil && value != nil {
			// Promote to L2 and L1
			uc.setInL2(key, value, uc.getDefaultTTL(L2Local))
			uc.setInL1(key, value, uc.getDefaultTTL(L1Memory))
			uc.incrementStats("l3_hit")
			return value, nil
		}
		uc.incrementStats("l3_miss")
	}

	uc.incrementStats("total_miss")
	return nil, nil // Cache miss
}

// Set stores a value in the appropriate cache layers
func (uc *UnifiedCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	// Determine which layers to use based on TTL and size
	entry := &CacheEntry{
		Key:      key,
		Value:    value,
		Created:  time.Now(),
		Expires:  time.Now().Add(ttl),
		Layer:    L1Memory,
		HitCount: 0,
		LastHit:  time.Now(),
	}

	// Calculate size
	if data, err := json.Marshal(value); err == nil {
		entry.Size = int64(len(data))
	}

	// Store in appropriate layers based on TTL
	if ttl <= 5*time.Minute { // Very short TTL -> L1 only
		return uc.setInL1(key, value, ttl)
	} else if ttl <= 24*time.Hour { // Medium to long TTL -> L1 + L2
		uc.setInL2(key, value, ttl)
		return uc.setInL1(key, value, ttl)
	} else { // Very long TTL -> All layers
		if uc.l3Cache != nil {
			uc.l3Cache.Set(ctx, key, value, ttl)
		}
		uc.setInL2(key, value, ttl)
		return uc.setInL1(key, value, ttl)
	}
}

// Delete removes a value from all cache layers
func (uc *UnifiedCache) Delete(ctx context.Context, key string) error {
	// Remove from all layers
	uc.deleteFromL1(key)
	uc.deleteFromL2(key)

	if uc.l3Cache != nil {
		uc.l3Cache.Delete(ctx, key)
	}

	return nil
}

// Clear removes all values from all cache layers
func (uc *UnifiedCache) Clear(ctx context.Context) error {
	uc.l1Mu.Lock()
	uc.l1Cache = make(map[string]*CacheEntry)
	uc.l1Mu.Unlock()

	// Clear L2 directory
	if err := uc.clearL2(); err != nil {
		return err
	}

	// Clear L3
	if uc.l3Cache != nil {
		uc.l3Cache.Clear(ctx)
	}

	// Reset stats
	uc.statsMu.Lock()
	uc.stats = &CacheStats{LastReset: time.Now()}
	uc.statsMu.Unlock()

	return nil
}

// Close closes the cache connection
func (uc *UnifiedCache) Close() error {
	if uc.l3Cache != nil {
		return uc.l3Cache.Close()
	}
	return nil
}

// GetStats returns cache statistics
func (uc *UnifiedCache) GetStats(ctx context.Context) (*CacheStats, error) {
	uc.statsMu.RLock()
	defer uc.statsMu.RUnlock()

	// Copy stats to avoid race conditions
	stats := *uc.stats
	return &stats, nil
}

// InvalidateByTags removes all entries with specified tags
func (uc *UnifiedCache) InvalidateByTags(ctx context.Context, tags []string) error {
	// This would require iterating through all cache entries
	// For now, implement a simple approach
	uc.logger.Info("Invalidating cache by tags", "tags", tags)

	// Clear all caches for now - in production, you'd implement tag-based invalidation
	return uc.Clear(ctx)
}

// L1 Cache Methods (In-Memory)

func (uc *UnifiedCache) getFromL1(key string) (interface{}, bool) {
	uc.l1Mu.RLock()
	defer uc.l1Mu.RUnlock()

	entry, exists := uc.l1Cache[key]
	if !exists {
		return nil, false
	}

	// Check if expired
	if time.Now().After(entry.Expires) {
		uc.l1Mu.RUnlock()
		uc.l1Mu.Lock()
		delete(uc.l1Cache, key)
		uc.l1Mu.Unlock()
		uc.l1Mu.RLock()
		return nil, false
	}

	// Update hit count
	entry.HitCount++
	entry.LastHit = time.Now()

	return entry.Value, true
}

func (uc *UnifiedCache) setInL1(key string, value interface{}, ttl time.Duration) error {
	uc.l1Mu.Lock()
	defer uc.l1Mu.Unlock()

	entry := &CacheEntry{
		Key:      key,
		Value:    value,
		Created:  time.Now(),
		Expires:  time.Now().Add(ttl),
		Layer:    L1Memory,
		HitCount: 0,
		LastHit:  time.Now(),
	}

	if data, err := json.Marshal(value); err == nil {
		entry.Size = int64(len(data))
	}

	uc.l1Cache[key] = entry
	return nil
}

func (uc *UnifiedCache) deleteFromL1(key string) {
	uc.l1Mu.Lock()
	defer uc.l1Mu.Unlock()
	delete(uc.l1Cache, key)
}

// L2 Cache Methods (Local Disk)

func (uc *UnifiedCache) getFromL2(key string) (interface{}, bool) {
	uc.l2Mu.RLock()
	defer uc.l2Mu.RUnlock()

	entryPath := filepath.Join(uc.l2Path, key+".json")
	data, err := os.ReadFile(entryPath)
	if err != nil {
		return nil, false
	}

	var entry CacheEntry
	if err := json.Unmarshal(data, &entry); err != nil {
		return nil, false
	}

	// Check if expired
	if time.Now().After(entry.Expires) {
		os.Remove(entryPath)
		return nil, false
	}

	return entry.Value, true
}

func (uc *UnifiedCache) setInL2(key string, value interface{}, ttl time.Duration) error {
	uc.l2Mu.Lock()
	defer uc.l2Mu.Unlock()

	entry := &CacheEntry{
		Key:      key,
		Value:    value,
		Created:  time.Now(),
		Expires:  time.Now().Add(ttl),
		Layer:    L2Local,
		HitCount: 0,
		LastHit:  time.Now(),
	}

	if data, err := json.Marshal(value); err == nil {
		entry.Size = int64(len(data))
	}

	entryPath := filepath.Join(uc.l2Path, key+".json")
	data, err := json.Marshal(entry)
	if err != nil {
		return err
	}

	return os.WriteFile(entryPath, data, 0644)
}

func (uc *UnifiedCache) deleteFromL2(key string) error {
	uc.l2Mu.Lock()
	defer uc.l2Mu.Unlock()

	entryPath := filepath.Join(uc.l2Path, key+".json")
	return os.Remove(entryPath)
}

func (uc *UnifiedCache) clearL2() error {
	uc.l2Mu.Lock()
	defer uc.l2Mu.Unlock()

	entries, err := os.ReadDir(uc.l2Path)
	if err != nil {
		return err
	}

	for _, entry := range entries {
		if err := os.Remove(filepath.Join(uc.l2Path, entry.Name())); err != nil {
			return err
		}
	}

	return nil
}

// Helper methods

func (uc *UnifiedCache) getDefaultTTL(layer CacheLayer) time.Duration {
	switch layer {
	case L1Memory:
		return 5 * time.Minute
	case L2Local:
		return time.Hour
	case L3Network:
		return 24 * time.Hour
	default:
		return time.Hour
	}
}

func (uc *UnifiedCache) incrementStats(stat string) {
	uc.statsMu.Lock()
	defer uc.statsMu.Unlock()

	switch stat {
	case "l1_hit":
		uc.stats.L1Hits++
		uc.stats.TotalHits++
	case "l1_miss":
		uc.stats.L1Misses++
	case "l2_hit":
		uc.stats.L2Hits++
		uc.stats.TotalHits++
	case "l2_miss":
		uc.stats.L2Misses++
	case "l3_hit":
		uc.stats.L3Hits++
		uc.stats.TotalHits++
	case "l3_miss":
		uc.stats.L3Misses++
	case "total_miss":
		uc.stats.TotalMisses++
	}
}
