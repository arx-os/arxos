package services

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/arxos/core/arxobject"
)

// ConfidenceCache provides high-performance caching for confidence scores
type ConfidenceCache struct {
	// In-memory cache for hot data
	memCache      map[uint64]*CachedConfidence
	memCacheMutex sync.RWMutex
	
	// Redis connection for distributed cache
	redisService *RedisService
	
	// Cache statistics
	stats CacheStats
	
	// Configuration
	config CacheConfig
}

// CachedConfidence represents cached confidence data
type CachedConfidence struct {
	ObjectID         uint64                   `json:"object_id"`
	Confidence       arxobject.ConfidenceScore `json:"confidence"`
	LastValidated    time.Time                `json:"last_validated"`
	ValidationCount  int                      `json:"validation_count"`
	CachedAt         time.Time                `json:"cached_at"`
	ExpiresAt        time.Time                `json:"expires_at"`
	AccessCount      int64                    `json:"access_count"`
	PropagationDepth int                      `json:"propagation_depth"`
}

// CacheStats tracks cache performance
type CacheStats struct {
	Hits              int64     `json:"hits"`
	Misses            int64     `json:"misses"`
	Evictions         int64     `json:"evictions"`
	TotalObjects      int64     `json:"total_objects"`
	MemoryUsage       int64     `json:"memory_usage_bytes"`
	LastEviction      time.Time `json:"last_eviction"`
	AverageAccessTime float64   `json:"average_access_time_ms"`
	mu                sync.RWMutex
}

// CacheConfig defines cache configuration
type CacheConfig struct {
	MaxMemoryObjects   int           `json:"max_memory_objects"`
	DefaultTTL         time.Duration `json:"default_ttl"`
	HighConfidenceTTL  time.Duration `json:"high_confidence_ttl"`
	LowConfidenceTTL   time.Duration `json:"low_confidence_ttl"`
	EvictionPolicy     string        `json:"eviction_policy"` // LRU, LFU, FIFO
	EnableRedis        bool          `json:"enable_redis"`
	RedisKeyPrefix     string        `json:"redis_key_prefix"`
	WarmupOnStart      bool          `json:"warmup_on_start"`
}

// NewConfidenceCache creates a new confidence cache
func NewConfidenceCache(redisService *RedisService, config *CacheConfig) *ConfidenceCache {
	if config == nil {
		config = &CacheConfig{
			MaxMemoryObjects:  10000,
			DefaultTTL:        5 * time.Minute,
			HighConfidenceTTL: 15 * time.Minute,
			LowConfidenceTTL:  2 * time.Minute,
			EvictionPolicy:    "LRU",
			EnableRedis:       redisService != nil,
			RedisKeyPrefix:    "confidence:",
			WarmupOnStart:     true,
		}
	}
	
	cache := &ConfidenceCache{
		memCache:     make(map[uint64]*CachedConfidence),
		redisService: redisService,
		config:       *config,
		stats:        CacheStats{},
	}
	
	// Start background maintenance
	go cache.maintenanceLoop()
	
	return cache
}

// Get retrieves confidence from cache
func (cc *ConfidenceCache) Get(objectID uint64) (*arxobject.ConfidenceScore, bool) {
	startTime := time.Now()
	defer cc.updateAccessTime(time.Since(startTime))
	
	// Check memory cache first
	cc.memCacheMutex.RLock()
	if cached, exists := cc.memCache[objectID]; exists {
		cc.memCacheMutex.RUnlock()
		
		// Check if expired
		if time.Now().Before(cached.ExpiresAt) {
			cached.AccessCount++
			cc.recordHit()
			return &cached.Confidence, true
		}
		
		// Expired - remove from cache
		cc.memCacheMutex.Lock()
		delete(cc.memCache, objectID)
		cc.memCacheMutex.Unlock()
	} else {
		cc.memCacheMutex.RUnlock()
	}
	
	// Check Redis if enabled
	if cc.config.EnableRedis && cc.redisService != nil {
		confidence, found := cc.getFromRedis(objectID)
		if found {
			// Populate memory cache
			cc.populateMemCache(objectID, confidence)
			cc.recordHit()
			return confidence, true
		}
	}
	
	cc.recordMiss()
	return nil, false
}

// Set stores confidence in cache
func (cc *ConfidenceCache) Set(objectID uint64, confidence *arxobject.ConfidenceScore, validated bool) {
	ttl := cc.calculateTTL(confidence)
	
	cached := &CachedConfidence{
		ObjectID:        objectID,
		Confidence:      *confidence,
		LastValidated:   time.Now(),
		ValidationCount: 0,
		CachedAt:        time.Now(),
		ExpiresAt:       time.Now().Add(ttl),
		AccessCount:     0,
	}
	
	if validated {
		cached.ValidationCount = 1
	}
	
	// Store in memory cache
	cc.memCacheMutex.Lock()
	
	// Check if we need to evict
	if len(cc.memCache) >= cc.config.MaxMemoryObjects {
		cc.evictOne()
	}
	
	cc.memCache[objectID] = cached
	cc.memCacheMutex.Unlock()
	
	// Store in Redis if enabled
	if cc.config.EnableRedis && cc.redisService != nil {
		cc.setInRedis(objectID, cached)
	}
	
	cc.updateStats()
}

// BatchSet stores multiple confidences efficiently
func (cc *ConfidenceCache) BatchSet(confidences map[uint64]*arxobject.ConfidenceScore) {
	cc.memCacheMutex.Lock()
	defer cc.memCacheMutex.Unlock()
	
	for objectID, confidence := range confidences {
		// Check if we need to evict
		if len(cc.memCache) >= cc.config.MaxMemoryObjects {
			cc.evictOne()
		}
		
		ttl := cc.calculateTTL(confidence)
		
		cc.memCache[objectID] = &CachedConfidence{
			ObjectID:      objectID,
			Confidence:    *confidence,
			CachedAt:      time.Now(),
			ExpiresAt:     time.Now().Add(ttl),
			AccessCount:   0,
		}
	}
	
	// Batch store in Redis if enabled
	if cc.config.EnableRedis && cc.redisService != nil {
		cc.batchSetInRedis(confidences)
	}
	
	cc.updateStats()
}

// Invalidate removes an object from cache
func (cc *ConfidenceCache) Invalidate(objectID uint64) {
	cc.memCacheMutex.Lock()
	delete(cc.memCache, objectID)
	cc.memCacheMutex.Unlock()
	
	// Remove from Redis if enabled
	if cc.config.EnableRedis && cc.redisService != nil {
		cc.removeFromRedis(objectID)
	}
}

// InvalidatePattern invalidates objects matching a pattern
func (cc *ConfidenceCache) InvalidatePattern(objectType arxobject.ArxObjectType) {
	cc.memCacheMutex.Lock()
	defer cc.memCacheMutex.Unlock()
	
	toRemove := []uint64{}
	
	// Find matching objects
	// In production, would need object type stored in cache
	for id := range cc.memCache {
		// This is simplified - would need actual type checking
		toRemove = append(toRemove, id)
	}
	
	// Remove matching objects
	for _, id := range toRemove {
		delete(cc.memCache, id)
	}
	
	// Clear Redis pattern if enabled
	if cc.config.EnableRedis && cc.redisService != nil {
		// Pattern-based deletion in Redis
		pattern := fmt.Sprintf("%s*", cc.config.RedisKeyPrefix)
		cc.redisService.DeletePattern(pattern)
	}
}

// UpdateAfterValidation updates cache after validation
func (cc *ConfidenceCache) UpdateAfterValidation(
	objectID uint64,
	newConfidence *arxobject.ConfidenceScore,
	cascadedObjects []uint64,
) {
	// Update validated object with extended TTL
	cc.memCacheMutex.Lock()
	if cached, exists := cc.memCache[objectID]; exists {
		cached.Confidence = *newConfidence
		cached.LastValidated = time.Now()
		cached.ValidationCount++
		cached.ExpiresAt = time.Now().Add(cc.config.HighConfidenceTTL)
		cached.PropagationDepth = 0
	} else {
		// Create new cache entry
		cc.memCache[objectID] = &CachedConfidence{
			ObjectID:         objectID,
			Confidence:       *newConfidence,
			LastValidated:    time.Now(),
			ValidationCount:  1,
			CachedAt:         time.Now(),
			ExpiresAt:        time.Now().Add(cc.config.HighConfidenceTTL),
			PropagationDepth: 0,
		}
	}
	cc.memCacheMutex.Unlock()
	
	// Mark cascaded objects with shorter TTL
	for _, cascadedID := range cascadedObjects {
		cc.memCacheMutex.Lock()
		if cached, exists := cc.memCache[cascadedID]; exists {
			cached.PropagationDepth++
			// Shorter TTL for propagated confidence
			cached.ExpiresAt = time.Now().Add(cc.config.DefaultTTL)
		}
		cc.memCacheMutex.Unlock()
	}
	
	// Update Redis if enabled
	if cc.config.EnableRedis && cc.redisService != nil {
		cc.updateRedisAfterValidation(objectID, newConfidence, cascadedObjects)
	}
}

// WarmUp pre-loads cache with frequently accessed objects
func (cc *ConfidenceCache) WarmUp(objectIDs []uint64, loader func(uint64) *arxobject.ConfidenceScore) {
	cc.memCacheMutex.Lock()
	defer cc.memCacheMutex.Unlock()
	
	for _, id := range objectIDs {
		if len(cc.memCache) >= cc.config.MaxMemoryObjects {
			break
		}
		
		confidence := loader(id)
		if confidence != nil {
			ttl := cc.calculateTTL(confidence)
			
			cc.memCache[id] = &CachedConfidence{
				ObjectID:    id,
				Confidence:  *confidence,
				CachedAt:    time.Now(),
				ExpiresAt:   time.Now().Add(ttl),
				AccessCount: 0,
			}
		}
	}
}

// GetStats returns cache statistics
func (cc *ConfidenceCache) GetStats() CacheStats {
	cc.stats.mu.RLock()
	defer cc.stats.mu.RUnlock()
	
	cc.memCacheMutex.RLock()
	cc.stats.TotalObjects = int64(len(cc.memCache))
	cc.stats.MemoryUsage = cc.estimateMemoryUsage()
	cc.memCacheMutex.RUnlock()
	
	hitRate := float64(0)
	if cc.stats.Hits+cc.stats.Misses > 0 {
		hitRate = float64(cc.stats.Hits) / float64(cc.stats.Hits+cc.stats.Misses) * 100
	}
	
	return CacheStats{
		Hits:              cc.stats.Hits,
		Misses:            cc.stats.Misses,
		Evictions:         cc.stats.Evictions,
		TotalObjects:      cc.stats.TotalObjects,
		MemoryUsage:       cc.stats.MemoryUsage,
		LastEviction:      cc.stats.LastEviction,
		AverageAccessTime: cc.stats.AverageAccessTime,
	}
}

// Private methods

func (cc *ConfidenceCache) calculateTTL(confidence *arxobject.ConfidenceScore) time.Duration {
	if confidence.IsHighConfidence() {
		return cc.config.HighConfidenceTTL
	} else if confidence.IsLowConfidence() {
		return cc.config.LowConfidenceTTL
	}
	return cc.config.DefaultTTL
}

func (cc *ConfidenceCache) evictOne() {
	if cc.config.EvictionPolicy == "LRU" {
		cc.evictLRU()
	} else if cc.config.EvictionPolicy == "LFU" {
		cc.evictLFU()
	} else {
		cc.evictFIFO()
	}
	
	cc.stats.mu.Lock()
	cc.stats.Evictions++
	cc.stats.LastEviction = time.Now()
	cc.stats.mu.Unlock()
}

func (cc *ConfidenceCache) evictLRU() {
	var oldestID uint64
	var oldestTime time.Time
	
	for id, cached := range cc.memCache {
		accessTime := cached.CachedAt.Add(time.Duration(cached.AccessCount) * time.Second)
		if oldestTime.IsZero() || accessTime.Before(oldestTime) {
			oldestTime = accessTime
			oldestID = id
		}
	}
	
	if oldestID != 0 {
		delete(cc.memCache, oldestID)
	}
}

func (cc *ConfidenceCache) evictLFU() {
	var leastID uint64
	var leastCount int64 = -1
	
	for id, cached := range cc.memCache {
		if leastCount == -1 || cached.AccessCount < leastCount {
			leastCount = cached.AccessCount
			leastID = id
		}
	}
	
	if leastID != 0 {
		delete(cc.memCache, leastID)
	}
}

func (cc *ConfidenceCache) evictFIFO() {
	var oldestID uint64
	var oldestTime time.Time
	
	for id, cached := range cc.memCache {
		if oldestTime.IsZero() || cached.CachedAt.Before(oldestTime) {
			oldestTime = cached.CachedAt
			oldestID = id
		}
	}
	
	if oldestID != 0 {
		delete(cc.memCache, oldestID)
	}
}

func (cc *ConfidenceCache) maintenanceLoop() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()
	
	for range ticker.C {
		cc.cleanupExpired()
		cc.updateStats()
	}
}

func (cc *ConfidenceCache) cleanupExpired() {
	cc.memCacheMutex.Lock()
	defer cc.memCacheMutex.Unlock()
	
	now := time.Now()
	toRemove := []uint64{}
	
	for id, cached := range cc.memCache {
		if now.After(cached.ExpiresAt) {
			toRemove = append(toRemove, id)
		}
	}
	
	for _, id := range toRemove {
		delete(cc.memCache, id)
	}
}

func (cc *ConfidenceCache) estimateMemoryUsage() int64 {
	// Rough estimate: ~200 bytes per cached object
	return int64(len(cc.memCache)) * 200
}

func (cc *ConfidenceCache) recordHit() {
	cc.stats.mu.Lock()
	cc.stats.Hits++
	cc.stats.mu.Unlock()
}

func (cc *ConfidenceCache) recordMiss() {
	cc.stats.mu.Lock()
	cc.stats.Misses++
	cc.stats.mu.Unlock()
}

func (cc *ConfidenceCache) updateAccessTime(duration time.Duration) {
	cc.stats.mu.Lock()
	// Running average
	alpha := 0.1
	cc.stats.AverageAccessTime = cc.stats.AverageAccessTime*(1-alpha) + 
		float64(duration.Microseconds())/1000*alpha
	cc.stats.mu.Unlock()
}

func (cc *ConfidenceCache) updateStats() {
	cc.stats.mu.Lock()
	cc.memCacheMutex.RLock()
	cc.stats.TotalObjects = int64(len(cc.memCache))
	cc.stats.MemoryUsage = cc.estimateMemoryUsage()
	cc.memCacheMutex.RUnlock()
	cc.stats.mu.Unlock()
}

// Redis operations

func (cc *ConfidenceCache) getFromRedis(objectID uint64) (*arxobject.ConfidenceScore, bool) {
	if cc.redisService == nil {
		return nil, false
	}
	
	key := fmt.Sprintf("%s%d", cc.config.RedisKeyPrefix, objectID)
	data, err := cc.redisService.Get(key)
	if err != nil || data == "" {
		return nil, false
	}
	
	var cached CachedConfidence
	if err := json.Unmarshal([]byte(data), &cached); err != nil {
		return nil, false
	}
	
	// Check if expired
	if time.Now().After(cached.ExpiresAt) {
		cc.redisService.Delete(key)
		return nil, false
	}
	
	return &cached.Confidence, true
}

func (cc *ConfidenceCache) setInRedis(objectID uint64, cached *CachedConfidence) {
	if cc.redisService == nil {
		return
	}
	
	key := fmt.Sprintf("%s%d", cc.config.RedisKeyPrefix, objectID)
	data, err := json.Marshal(cached)
	if err != nil {
		return
	}
	
	ttl := cached.ExpiresAt.Sub(time.Now())
	cc.redisService.SetWithTTL(key, string(data), ttl)
}

func (cc *ConfidenceCache) batchSetInRedis(confidences map[uint64]*arxobject.ConfidenceScore) {
	if cc.redisService == nil {
		return
	}
	
	// Use pipeline for batch operations
	pipeline := make(map[string]string)
	
	for objectID, confidence := range confidences {
		key := fmt.Sprintf("%s%d", cc.config.RedisKeyPrefix, objectID)
		
		cached := CachedConfidence{
			ObjectID:   objectID,
			Confidence: *confidence,
			CachedAt:   time.Now(),
			ExpiresAt:  time.Now().Add(cc.calculateTTL(confidence)),
		}
		
		if data, err := json.Marshal(cached); err == nil {
			pipeline[key] = string(data)
		}
	}
	
	// Execute pipeline
	for key, value := range pipeline {
		cc.redisService.Set(key, value)
	}
}

func (cc *ConfidenceCache) removeFromRedis(objectID uint64) {
	if cc.redisService == nil {
		return
	}
	
	key := fmt.Sprintf("%s%d", cc.config.RedisKeyPrefix, objectID)
	cc.redisService.Delete(key)
}

func (cc *ConfidenceCache) updateRedisAfterValidation(
	objectID uint64,
	newConfidence *arxobject.ConfidenceScore,
	cascadedObjects []uint64,
) {
	if cc.redisService == nil {
		return
	}
	
	// Update validated object
	key := fmt.Sprintf("%s%d", cc.config.RedisKeyPrefix, objectID)
	cached := CachedConfidence{
		ObjectID:        objectID,
		Confidence:      *newConfidence,
		LastValidated:   time.Now(),
		ValidationCount: 1,
		CachedAt:        time.Now(),
		ExpiresAt:       time.Now().Add(cc.config.HighConfidenceTTL),
	}
	
	if data, err := json.Marshal(cached); err == nil {
		cc.redisService.SetWithTTL(key, string(data), cc.config.HighConfidenceTTL)
	}
	
	// Mark cascaded objects
	for _, cascadedID := range cascadedObjects {
		cascadeKey := fmt.Sprintf("%s%d:cascaded", cc.config.RedisKeyPrefix, cascadedID)
		cc.redisService.SetWithTTL(cascadeKey, "1", cc.config.DefaultTTL)
	}
}

func (cc *ConfidenceCache) populateMemCache(objectID uint64, confidence *arxobject.ConfidenceScore) {
	cc.memCacheMutex.Lock()
	defer cc.memCacheMutex.Unlock()
	
	if len(cc.memCache) >= cc.config.MaxMemoryObjects {
		cc.evictOne()
	}
	
	ttl := cc.calculateTTL(confidence)
	
	cc.memCache[objectID] = &CachedConfidence{
		ObjectID:    objectID,
		Confidence:  *confidence,
		CachedAt:    time.Now(),
		ExpiresAt:   time.Now().Add(ttl),
		AccessCount: 1,
	}
}