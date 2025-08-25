package cache

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/lib/pq"
	"gorm.io/gorm"
)

// ConfidenceScore represents confidence metrics for an ArxObject
type ConfidenceScore struct {
	Overall          float64 `json:"overall"`
	Geometry         float64 `json:"geometry"`
	Attributes       float64 `json:"attributes"`
	Relationships    float64 `json:"relationships"`
	ValidationStatus string  `json:"validation_status"`
}

// ConfidenceCache provides high-performance caching for confidence scores using PostgreSQL
type ConfidenceCache struct {
	// In-memory cache for hot data
	memCache      map[uint64]*CachedConfidence
	memCacheMutex sync.RWMutex

	// PostgreSQL connection
	db *gorm.DB

	// Cache statistics
	stats ConfidenceCacheStats

	// Configuration
	config ConfidenceCacheConfig
}

// ConfidenceCacheEntry represents the PostgreSQL table for confidence cache
type ConfidenceCacheEntry struct {
	ObjectID         uint64                    `gorm:"primaryKey"`
	BuildingID       string                    `gorm:"type:varchar(36);index"`
	ConfidenceScore  json.RawMessage           `gorm:"type:jsonb;not null"`
	ValidationCount  int                       `gorm:"default:0"`
	LastValidatedAt  *time.Time                `gorm:"index"`
	PropagationDepth int                       `gorm:"default:0"`
	RelatedObjects   pq.Int64Array             `gorm:"type:bigint[]"`
	PatternSignature string                    `gorm:"type:varchar(255);index"`
	ExpiresAt        time.Time                 `gorm:"not null;index"`
	CreatedAt        time.Time                 `gorm:"default:CURRENT_TIMESTAMP"`
	UpdatedAt        time.Time                 `gorm:"default:CURRENT_TIMESTAMP"`
	AccessCount      int64                     `gorm:"default:0"`
	Metadata         json.RawMessage           `gorm:"type:jsonb;default:'{}'"`
}

// TableName specifies the table name for GORM
func (ConfidenceCacheEntry) TableName() string {
	return "confidence_cache"
}

// CachedConfidence represents cached confidence data
type CachedConfidence struct {
	ObjectID         uint64                    `json:"object_id"`
	Confidence       ConfidenceScore `json:"confidence"`
	LastValidated    time.Time                 `json:"last_validated"`
	ValidationCount  int                       `json:"validation_count"`
	CachedAt         time.Time                 `json:"cached_at"`
	ExpiresAt        time.Time                 `json:"expires_at"`
	AccessCount      int64                     `json:"access_count"`
	PropagationDepth int                       `json:"propagation_depth"`
}

// ConfidenceCacheStats tracks cache performance
type ConfidenceCacheStats struct {
	Hits              int64     `json:"hits"`
	Misses            int64     `json:"misses"`
	Evictions         int64     `json:"evictions"`
	TotalObjects      int64     `json:"total_objects"`
	MemoryUsage       int64     `json:"memory_usage_bytes"`
	LastEviction      time.Time `json:"last_eviction"`
	AverageAccessTime float64   `json:"average_access_time_ms"`
	mu                sync.RWMutex
}

// ConfidenceCacheConfig defines cache configuration
type ConfidenceCacheConfig struct {
	MaxMemoryObjects  int           `json:"max_memory_objects"`
	DefaultTTL        time.Duration `json:"default_ttl"`
	HighConfidenceTTL time.Duration `json:"high_confidence_ttl"`
	LowConfidenceTTL  time.Duration `json:"low_confidence_ttl"`
	EvictionPolicy    string        `json:"eviction_policy"` // LRU, LFU, FIFO
	WarmupOnStart     bool          `json:"warmup_on_start"`
}

// NewConfidenceCache creates a new confidence cache using PostgreSQL
func NewConfidenceCache(config *ConfidenceCacheConfig) *ConfidenceCache {
	if config == nil {
		config = &ConfidenceCacheConfig{
			MaxMemoryObjects:  10000,
			DefaultTTL:        5 * time.Minute,
			HighConfidenceTTL: 15 * time.Minute,
			LowConfidenceTTL:  2 * time.Minute,
			EvictionPolicy:    "LRU",
			WarmupOnStart:     true,
		}
	}

	cache := &ConfidenceCache{
		memCache: make(map[uint64]*CachedConfidence),
		db:       db.GormDB,
		config:   *config,
		stats:    ConfidenceCacheStats{},
	}

	// Warm up cache if configured
	if config.WarmupOnStart {
		go cache.warmupCache()
	}

	// Start background maintenance
	go cache.maintenanceLoop()

	return cache
}

// Get retrieves confidence from cache
func (cc *ConfidenceCache) Get(objectID uint64) (*ConfidenceScore, bool) {
	startTime := time.Now()
	defer cc.updateAccessTime(time.Since(startTime))

	// Check memory cache first
	cc.memCacheMutex.RLock()
	if cached, exists := cc.memCache[objectID]; exists {
		cc.memCacheMutex.RUnlock()
		
		// Check expiration
		if time.Now().Before(cached.ExpiresAt) {
			cc.recordHit()
			return &cached.Confidence, true
		}
		
		// Remove expired entry
		cc.memCacheMutex.Lock()
		delete(cc.memCache, objectID)
		cc.memCacheMutex.Unlock()
	} else {
		cc.memCacheMutex.RUnlock()
	}

	// Check PostgreSQL
	var entry ConfidenceCacheEntry
	err := cc.db.Transaction(func(tx *gorm.DB) error {
		// Get entry and check expiration
		if err := tx.Where("object_id = ? AND expires_at > ?", objectID, time.Now()).
			First(&entry).Error; err != nil {
			return err
		}

		// Update access count
		return tx.Model(&ConfidenceCacheEntry{}).
			Where("object_id = ?", objectID).
			Updates(map[string]interface{}{
				"access_count": gorm.Expr("access_count + 1"),
			}).Error
	})

	if err != nil {
		cc.recordMiss()
		return nil, false
	}

	// Unmarshal confidence score
	var confidence ConfidenceScore
	if err := json.Unmarshal(entry.ConfidenceScore, &confidence); err != nil {
		cc.recordMiss()
		return nil, false
	}

	// Add to memory cache
	cc.addToMemCache(objectID, &confidence, entry.ValidationCount, entry.PropagationDepth, entry.ExpiresAt)

	cc.recordHit()
	return &confidence, true
}

// Set stores confidence in cache
func (cc *ConfidenceCache) Set(objectID uint64, confidence *ConfidenceScore, validationCount int, propagationDepth int) error {
	// Calculate TTL based on confidence level
	ttl := cc.calculateTTL(confidence)
	expiresAt := time.Now().Add(ttl)

	// Marshal confidence score
	confJSON, err := json.Marshal(confidence)
	if err != nil {
		return fmt.Errorf("failed to marshal confidence: %w", err)
	}

	// Store in PostgreSQL
	entry := ConfidenceCacheEntry{
		ObjectID:         objectID,
		ConfidenceScore:  confJSON,
		ValidationCount:  validationCount,
		PropagationDepth: propagationDepth,
		ExpiresAt:        expiresAt,
		CreatedAt:        time.Now(),
		UpdatedAt:        time.Now(),
	}

	if validationCount > 0 {
		now := time.Now()
		entry.LastValidatedAt = &now
	}

	// Use UPSERT
	result := cc.db.Save(&entry)
	if result.Error != nil {
		return fmt.Errorf("failed to save confidence cache: %w", result.Error)
	}

	// Add to memory cache
	cc.addToMemCache(objectID, confidence, validationCount, propagationDepth, expiresAt)

	return nil
}

// Delete removes confidence from cache
func (cc *ConfidenceCache) Delete(objectID uint64) error {
	// Remove from memory cache
	cc.memCacheMutex.Lock()
	delete(cc.memCache, objectID)
	cc.memCacheMutex.Unlock()

	// Remove from PostgreSQL
	result := cc.db.Where("object_id = ?", objectID).Delete(&ConfidenceCacheEntry{})
	if result.Error != nil {
		return fmt.Errorf("failed to delete confidence cache: %w", result.Error)
	}

	return nil
}

// BatchGet retrieves multiple confidence scores
func (cc *ConfidenceCache) BatchGet(objectIDs []uint64) map[uint64]*ConfidenceScore {
	results := make(map[uint64]*ConfidenceScore)
	
	// Check memory cache first
	cc.memCacheMutex.RLock()
	var missingIDs []uint64
	for _, id := range objectIDs {
		if cached, exists := cc.memCache[id]; exists && time.Now().Before(cached.ExpiresAt) {
			results[id] = &cached.Confidence
		} else {
			missingIDs = append(missingIDs, id)
		}
	}
	cc.memCacheMutex.RUnlock()

	// Fetch missing from PostgreSQL
	if len(missingIDs) > 0 {
		var entries []ConfidenceCacheEntry
		cc.db.Where("object_id IN ? AND expires_at > ?", missingIDs, time.Now()).Find(&entries)
		
		for _, entry := range entries {
			var confidence ConfidenceScore
			if err := json.Unmarshal(entry.ConfidenceScore, &confidence); err == nil {
				results[entry.ObjectID] = &confidence
				// Add to memory cache
				cc.addToMemCache(entry.ObjectID, &confidence, entry.ValidationCount, entry.PropagationDepth, entry.ExpiresAt)
			}
		}
	}

	return results
}

// InvalidatePattern removes all entries matching a building or pattern
func (cc *ConfidenceCache) InvalidatePattern(buildingID string, pattern string) error {
	// Clear from memory cache
	cc.memCacheMutex.Lock()
	for id := range cc.memCache {
		delete(cc.memCache, id)
	}
	cc.memCacheMutex.Unlock()

	// Clear from PostgreSQL
	query := cc.db.Model(&ConfidenceCacheEntry{})
	if buildingID != "" {
		query = query.Where("building_id = ?", buildingID)
	}
	if pattern != "" {
		query = query.Where("pattern_signature = ?", pattern)
	}
	
	result := query.Delete(&ConfidenceCacheEntry{})
	if result.Error != nil {
		return fmt.Errorf("failed to invalidate pattern: %w", result.Error)
	}

	cc.stats.mu.Lock()
	cc.stats.Evictions += result.RowsAffected
	cc.stats.mu.Unlock()

	return nil
}

// GetStats returns cache statistics
func (cc *ConfidenceCache) GetStats() ConfidenceCacheStats {
	cc.stats.mu.RLock()
	defer cc.stats.mu.RUnlock()
	
	// Get database stats
	var dbCount int64
	cc.db.Model(&ConfidenceCacheEntry{}).Count(&dbCount)
	
	cc.stats.TotalObjects = dbCount
	return cc.stats
}

// Helper methods

func (cc *ConfidenceCache) calculateTTL(confidence *ConfidenceScore) time.Duration {
	if confidence.Overall > 0.9 {
		return cc.config.HighConfidenceTTL
	} else if confidence.Overall < 0.5 {
		return cc.config.LowConfidenceTTL
	}
	return cc.config.DefaultTTL
}

func (cc *ConfidenceCache) addToMemCache(objectID uint64, confidence *ConfidenceScore, validationCount int, propagationDepth int, expiresAt time.Time) {
	cc.memCacheMutex.Lock()
	defer cc.memCacheMutex.Unlock()

	// Check cache size limit
	if len(cc.memCache) >= cc.config.MaxMemoryObjects {
		// Evict oldest entry (simple LRU)
		var oldestID uint64
		var oldestTime time.Time = time.Now()
		
		for id, cached := range cc.memCache {
			if cached.CachedAt.Before(oldestTime) {
				oldestTime = cached.CachedAt
				oldestID = id
			}
		}
		
		if oldestID != 0 {
			delete(cc.memCache, oldestID)
			cc.stats.Evictions++
		}
	}

	cc.memCache[objectID] = &CachedConfidence{
		ObjectID:         objectID,
		Confidence:       *confidence,
		ValidationCount:  validationCount,
		PropagationDepth: propagationDepth,
		CachedAt:         time.Now(),
		ExpiresAt:        expiresAt,
	}
}

func (cc *ConfidenceCache) warmupCache() {
	// Load frequently accessed entries into memory
	var entries []ConfidenceCacheEntry
	cc.db.Where("expires_at > ?", time.Now()).
		Order("access_count DESC").
		Limit(cc.config.MaxMemoryObjects / 2).
		Find(&entries)

	for _, entry := range entries {
		var confidence ConfidenceScore
		if err := json.Unmarshal(entry.ConfidenceScore, &confidence); err == nil {
			cc.addToMemCache(entry.ObjectID, &confidence, entry.ValidationCount, entry.PropagationDepth, entry.ExpiresAt)
		}
	}
}

func (cc *ConfidenceCache) maintenanceLoop() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		// Clean expired entries from PostgreSQL
		result := cc.db.Where("expires_at < ?", time.Now()).Delete(&ConfidenceCacheEntry{})
		if result.RowsAffected > 0 {
			cc.stats.mu.Lock()
			cc.stats.Evictions += result.RowsAffected
			cc.stats.LastEviction = time.Now()
			cc.stats.mu.Unlock()
		}

		// Clean expired entries from memory cache
		cc.memCacheMutex.Lock()
		for id, cached := range cc.memCache {
			if time.Now().After(cached.ExpiresAt) {
				delete(cc.memCache, id)
			}
		}
		cc.memCacheMutex.Unlock()
	}
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
	// Simple moving average
	cc.stats.AverageAccessTime = (cc.stats.AverageAccessTime*0.9) + (float64(duration.Microseconds())/1000.0)*0.1
	cc.stats.mu.Unlock()
}