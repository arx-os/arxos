package cache

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// CacheStrategy defines cache invalidation and management strategies
type CacheStrategy struct {
	cache  domain.Cache
	logger domain.Logger
	rules  []CacheRule
}

// CacheRule defines a cache rule
type CacheRule struct {
	Pattern      string                 `json:"pattern"`
	TTL          time.Duration          `json:"ttl"`
	InvalidateOn []string               `json:"invalidate_on"`
	Priority     int                    `json:"priority"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// CacheEvent represents a cache event
type CacheEvent struct {
	Type      string                 `json:"type"`
	Entity    string                 `json:"entity"`
	EntityID  string                 `json:"entity_id"`
	Operation string                 `json:"operation"`
	Timestamp time.Time              `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// NewCacheStrategy creates a new cache strategy manager
func NewCacheStrategy(cache domain.Cache, logger domain.Logger) *CacheStrategy {
	return &CacheStrategy{
		cache:  cache,
		logger: logger,
		rules:  getDefaultCacheRules(),
	}
}

// AddRule adds a new cache rule
func (cs *CacheStrategy) AddRule(rule CacheRule) {
	cs.rules = append(cs.rules, rule)
	cs.logger.Info("Cache rule added", "pattern", rule.Pattern, "ttl", rule.TTL)
}

// GetTTL returns the TTL for a given key
func (cs *CacheStrategy) GetTTL(key string) time.Duration {
	for _, rule := range cs.rules {
		if cs.matchesPattern(key, rule.Pattern) {
			return rule.TTL
		}
	}

	// Default TTL
	return 5 * time.Minute
}

// ShouldCache determines if a key should be cached
func (cs *CacheStrategy) ShouldCache(key string) bool {
	for _, rule := range cs.rules {
		if cs.matchesPattern(key, rule.Pattern) {
			return true
		}
	}

	// Default: cache everything
	return true
}

// ProcessCacheEvent processes a cache event and invalidates relevant keys
func (cs *CacheStrategy) ProcessCacheEvent(ctx context.Context, event CacheEvent) error {
	cs.logger.Info("Processing cache event", "type", event.Type, "entity", event.Entity, "operation", event.Operation)

	// Find rules that should be invalidated
	var keysToInvalidate []string

	for _, rule := range cs.rules {
		for _, invalidatePattern := range rule.InvalidateOn {
			if cs.matchesPattern(event.Entity, invalidatePattern) {
				// Generate keys to invalidate based on the pattern
				keys := cs.generateInvalidationKeys(event, rule.Pattern)
				keysToInvalidate = append(keysToInvalidate, keys...)
			}
		}
	}

	// Remove duplicates
	keysToInvalidate = cs.removeDuplicates(keysToInvalidate)

	// Invalidate keys
	if len(keysToInvalidate) > 0 {
		if err := cs.invalidateKeys(ctx, keysToInvalidate); err != nil {
			return fmt.Errorf("failed to invalidate cache keys: %w", err)
		}

		cs.logger.Info("Cache keys invalidated", "count", len(keysToInvalidate), "keys", keysToInvalidate)
	}

	return nil
}

// matchesPattern checks if a key matches a pattern
func (cs *CacheStrategy) matchesPattern(key, pattern string) bool {
	// Simple pattern matching - can be enhanced with regex
	if pattern == "*" {
		return true
	}

	if strings.Contains(pattern, "*") {
		// Convert pattern to regex-like matching
		regexPattern := strings.ReplaceAll(pattern, "*", ".*")
		return strings.Contains(key, strings.ReplaceAll(regexPattern, ".*", ""))
	}

	return key == pattern
}

// generateInvalidationKeys generates keys to invalidate based on an event
func (cs *CacheStrategy) generateInvalidationKeys(event CacheEvent, pattern string) []string {
	var keys []string

	// Generate keys based on the pattern and event
	if strings.Contains(pattern, "{entity}") {
		key := strings.ReplaceAll(pattern, "{entity}", event.Entity)
		keys = append(keys, key)
	}

	if strings.Contains(pattern, "{entity_id}") {
		key := strings.ReplaceAll(pattern, "{entity_id}", event.EntityID)
		keys = append(keys, key)
	}

	if strings.Contains(pattern, "{operation}") {
		key := strings.ReplaceAll(pattern, "{operation}", event.Operation)
		keys = append(keys, key)
	}

	// Add specific entity-based keys
	switch event.Entity {
	case "building":
		keys = append(keys, fmt.Sprintf("building:%s", event.EntityID))
		keys = append(keys, fmt.Sprintf("buildings:list:*"))
		keys = append(keys, fmt.Sprintf("equipment:building:%s:*", event.EntityID))
		keys = append(keys, fmt.Sprintf("components:building:%s:*", event.EntityID))
	case "equipment":
		keys = append(keys, fmt.Sprintf("equipment:%s", event.EntityID))
		keys = append(keys, fmt.Sprintf("equipment:list:*"))
		if buildingID, ok := event.Metadata["building_id"].(string); ok {
			keys = append(keys, fmt.Sprintf("equipment:building:%s:*", buildingID))
		}
	case "component":
		keys = append(keys, fmt.Sprintf("component:%s", event.EntityID))
		keys = append(keys, fmt.Sprintf("components:list:*"))
		if buildingID, ok := event.Metadata["building_id"].(string); ok {
			keys = append(keys, fmt.Sprintf("components:building:%s:*", buildingID))
		}
	case "user":
		keys = append(keys, fmt.Sprintf("user:%s", event.EntityID))
		keys = append(keys, fmt.Sprintf("users:list:*"))
	case "organization":
		keys = append(keys, fmt.Sprintf("organization:%s", event.EntityID))
		keys = append(keys, fmt.Sprintf("organizations:list:*"))
		keys = append(keys, fmt.Sprintf("users:organization:%s:*", event.EntityID))
	}

	return keys
}

// invalidateKeys invalidates multiple cache keys
func (cs *CacheStrategy) invalidateKeys(ctx context.Context, keys []string) error {
	for _, key := range keys {
		if err := cs.cache.Delete(ctx, key); err != nil {
			cs.logger.Warn("Failed to invalidate cache key", "key", key, "error", err)
		}
	}
	return nil
}

// removeDuplicates removes duplicate strings from a slice
func (cs *CacheStrategy) removeDuplicates(slice []string) []string {
	keys := make(map[string]bool)
	var result []string

	for _, item := range slice {
		if !keys[item] {
			keys[item] = true
			result = append(result, item)
		}
	}

	return result
}

// getDefaultCacheRules returns default cache rules
func getDefaultCacheRules() []CacheRule {
	return []CacheRule{
		{
			Pattern:      "building:*",
			TTL:          30 * time.Minute,
			InvalidateOn: []string{"building"},
			Priority:     1,
		},
		{
			Pattern:      "buildings:list:*",
			TTL:          10 * time.Minute,
			InvalidateOn: []string{"building"},
			Priority:     2,
		},
		{
			Pattern:      "equipment:*",
			TTL:          20 * time.Minute,
			InvalidateOn: []string{"equipment", "building"},
			Priority:     1,
		},
		{
			Pattern:      "equipment:list:*",
			TTL:          5 * time.Minute,
			InvalidateOn: []string{"equipment", "building"},
			Priority:     2,
		},
		{
			Pattern:      "equipment:building:*",
			TTL:          15 * time.Minute,
			InvalidateOn: []string{"equipment", "building"},
			Priority:     1,
		},
		{
			Pattern:      "component:*",
			TTL:          20 * time.Minute,
			InvalidateOn: []string{"component", "building"},
			Priority:     1,
		},
		{
			Pattern:      "components:list:*",
			TTL:          5 * time.Minute,
			InvalidateOn: []string{"component", "building"},
			Priority:     2,
		},
		{
			Pattern:      "components:building:*",
			TTL:          15 * time.Minute,
			InvalidateOn: []string{"component", "building"},
			Priority:     1,
		},
		{
			Pattern:      "user:*",
			TTL:          60 * time.Minute,
			InvalidateOn: []string{"user"},
			Priority:     1,
		},
		{
			Pattern:      "users:list:*",
			TTL:          10 * time.Minute,
			InvalidateOn: []string{"user", "organization"},
			Priority:     2,
		},
		{
			Pattern:      "organization:*",
			TTL:          60 * time.Minute,
			InvalidateOn: []string{"organization"},
			Priority:     1,
		},
		{
			Pattern:      "organizations:list:*",
			TTL:          15 * time.Minute,
			InvalidateOn: []string{"organization"},
			Priority:     2,
		},
		{
			Pattern:      "users:organization:*",
			TTL:          30 * time.Minute,
			InvalidateOn: []string{"user", "organization"},
			Priority:     1,
		},
		{
			Pattern:      "ifc:*",
			TTL:          2 * time.Hour,
			InvalidateOn: []string{"ifc", "building"},
			Priority:     1,
		},
		{
			Pattern:      "analytics:*",
			TTL:          1 * time.Hour,
			InvalidateOn: []string{"building", "equipment", "component"},
			Priority:     3,
		},
	}
}

// CacheMetrics tracks cache performance metrics
type CacheMetrics struct {
	Hits      int64     `json:"hits"`
	Misses    int64     `json:"misses"`
	Sets      int64     `json:"sets"`
	Deletes   int64     `json:"deletes"`
	HitRate   float64   `json:"hit_rate"`
	TotalOps  int64     `json:"total_ops"`
	LastReset time.Time `json:"last_reset"`
}

// CacheMetricsCollector collects cache performance metrics
type CacheMetricsCollector struct {
	metrics CacheMetrics
	logger  domain.Logger
}

// NewCacheMetricsCollector creates a new cache metrics collector
func NewCacheMetricsCollector(logger domain.Logger) *CacheMetricsCollector {
	return &CacheMetricsCollector{
		metrics: CacheMetrics{
			LastReset: time.Now(),
		},
		logger: logger,
	}
}

// RecordHit records a cache hit
func (cmc *CacheMetricsCollector) RecordHit() {
	cmc.metrics.Hits++
	cmc.metrics.TotalOps++
	cmc.updateHitRate()
}

// RecordMiss records a cache miss
func (cmc *CacheMetricsCollector) RecordMiss() {
	cmc.metrics.Misses++
	cmc.metrics.TotalOps++
	cmc.updateHitRate()
}

// RecordSet records a cache set operation
func (cmc *CacheMetricsCollector) RecordSet() {
	cmc.metrics.Sets++
	cmc.metrics.TotalOps++
}

// RecordDelete records a cache delete operation
func (cmc *CacheMetricsCollector) RecordDelete() {
	cmc.metrics.Deletes++
	cmc.metrics.TotalOps++
}

// GetMetrics returns current cache metrics
func (cmc *CacheMetricsCollector) GetMetrics() CacheMetrics {
	return cmc.metrics
}

// ResetMetrics resets all metrics
func (cmc *CacheMetricsCollector) ResetMetrics() {
	cmc.metrics = CacheMetrics{
		LastReset: time.Now(),
	}
}

// updateHitRate updates the hit rate percentage
func (cmc *CacheMetricsCollector) updateHitRate() {
	if cmc.metrics.TotalOps > 0 {
		cmc.metrics.HitRate = float64(cmc.metrics.Hits) / float64(cmc.metrics.TotalOps) * 100
	}
}
