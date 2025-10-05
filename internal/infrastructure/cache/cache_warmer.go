package cache

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// CacheWarmer defines strategies for warming the cache
type CacheWarmer struct {
	cache  *UnifiedCache
	logger domain.Logger
}

// WarmingStrategy defines how to warm the cache
type WarmingStrategy struct {
	Name        string                                                    `json:"name"`
	Description string                                                    `json:"description"`
	Pattern     string                                                    `json:"pattern"`
	Priority    int                                                       `json:"priority"`
	Frequency   time.Duration                                             `json:"frequency"`
	DataLoader  func(ctx context.Context) (map[string]interface{}, error) `json:"-"`
	Metadata    map[string]interface{}                                    `json:"metadata"`
}

// NewCacheWarmer creates a new cache warmer
func NewCacheWarmer(cache *UnifiedCache, logger domain.Logger) *CacheWarmer {
	return &CacheWarmer{
		cache:  cache,
		logger: logger,
	}
}

// WarmCache executes cache warming strategies
func (cw *CacheWarmer) WarmCache(ctx context.Context, strategies []WarmingStrategy) error {
	cw.logger.Info("Starting cache warming", "strategies", len(strategies))

	for _, strategy := range strategies {
		if err := cw.executeStrategy(ctx, strategy); err != nil {
			cw.logger.Error("Cache warming strategy failed",
				"strategy", strategy.Name,
				"error", err)
			continue
		}

		cw.logger.Info("Cache warming strategy completed",
			"strategy", strategy.Name)
	}

	cw.logger.Info("Cache warming completed")
	return nil
}

// executeStrategy executes a single warming strategy
func (cw *CacheWarmer) executeStrategy(ctx context.Context, strategy WarmingStrategy) error {
	start := time.Now()

	// Load data using the strategy's data loader
	data, err := strategy.DataLoader(ctx)
	if err != nil {
		return fmt.Errorf("failed to load data for strategy %s: %w", strategy.Name, err)
	}

	// Store data in cache with appropriate TTL
	ttl := cw.getTTLForStrategy(strategy)
	stored := 0

	for key, value := range data {
		cacheKey := fmt.Sprintf("%s:%s", strategy.Pattern, key)

		if err := cw.cache.Set(ctx, cacheKey, value, ttl); err != nil {
			cw.logger.Warn("Failed to store cache entry",
				"key", cacheKey,
				"error", err)
			continue
		}

		stored++
	}

	duration := time.Since(start)
	cw.logger.Info("Strategy execution completed",
		"strategy", strategy.Name,
		"entries_stored", stored,
		"duration", duration)

	return nil
}

// getTTLForStrategy determines the appropriate TTL for a strategy
func (cw *CacheWarmer) getTTLForStrategy(strategy WarmingStrategy) time.Duration {
	// Default TTL based on strategy priority
	switch {
	case strategy.Priority >= 9: // Critical data
		return 24 * time.Hour
	case strategy.Priority >= 7: // Important data
		return 12 * time.Hour
	case strategy.Priority >= 5: // Normal data
		return 6 * time.Hour
	case strategy.Priority >= 3: // Low priority data
		return 2 * time.Hour
	default: // Very low priority
		return 1 * time.Hour
	}
}

// Predefined warming strategies for ArxOS

// GetDefaultWarmingStrategies returns common warming strategies for ArxOS
func GetDefaultWarmingStrategies() []WarmingStrategy {
	return []WarmingStrategy{
		{
			Name:        "building_templates",
			Description: "Warm cache with building configuration templates",
			Pattern:     "template:building",
			Priority:    9,
			Frequency:   24 * time.Hour,
			DataLoader: func(ctx context.Context) (map[string]interface{}, error) {
				// In a real implementation, this would load from database
				return map[string]interface{}{
					"residential": map[string]interface{}{
						"name": "Residential Building",
						"type": "residential",
					},
					"commercial": map[string]interface{}{
						"name": "Commercial Building",
						"type": "commercial",
					},
					"industrial": map[string]interface{}{
						"name": "Industrial Building",
						"type": "industrial",
					},
				}, nil
			},
		},
		{
			Name:        "equipment_types",
			Description: "Warm cache with equipment type definitions",
			Pattern:     "equipment:types",
			Priority:    8,
			Frequency:   12 * time.Hour,
			DataLoader: func(ctx context.Context) (map[string]interface{}, error) {
				return map[string]interface{}{
					"hvac": map[string]interface{}{
						"name":     "HVAC Equipment",
						"category": "mechanical",
					},
					"electrical": map[string]interface{}{
						"name":     "Electrical Equipment",
						"category": "electrical",
					},
					"plumbing": map[string]interface{}{
						"name":     "Plumbing Equipment",
						"category": "plumbing",
					},
				}, nil
			},
		},
		{
			Name:        "spatial_queries",
			Description: "Warm cache with common spatial query patterns",
			Pattern:     "spatial:query",
			Priority:    7,
			Frequency:   6 * time.Hour,
			DataLoader: func(ctx context.Context) (map[string]interface{}, error) {
				return map[string]interface{}{
					"floor_plan": map[string]interface{}{
						"query": "SELECT * FROM floors WHERE building_id = ?",
						"type":  "floor_plan",
					},
					"equipment_locations": map[string]interface{}{
						"query": "SELECT * FROM equipment WHERE floor_id = ?",
						"type":  "equipment_locations",
					},
				}, nil
			},
		},
		{
			Name:        "api_responses",
			Description: "Warm cache with common API response patterns",
			Pattern:     "api:response",
			Priority:    6,
			Frequency:   2 * time.Hour,
			DataLoader: func(ctx context.Context) (map[string]interface{}, error) {
				return map[string]interface{}{
					"health_check": map[string]interface{}{
						"status":    "healthy",
						"timestamp": time.Now(),
					},
					"version_info": map[string]interface{}{
						"version": "0.1.0",
						"build":   "dev",
					},
				}, nil
			},
		},
	}
}

// ScheduleWarming schedules periodic cache warming
func (cw *CacheWarmer) ScheduleWarming(ctx context.Context, strategies []WarmingStrategy) {
	for _, strategy := range strategies {
		go cw.scheduleStrategy(ctx, strategy)
	}
}

// scheduleStrategy schedules a single strategy to run periodically
func (cw *CacheWarmer) scheduleStrategy(ctx context.Context, strategy WarmingStrategy) {
	ticker := time.NewTicker(strategy.Frequency)
	defer ticker.Stop()

	// Run immediately
	if err := cw.executeStrategy(ctx, strategy); err != nil {
		cw.logger.Error("Initial cache warming failed",
			"strategy", strategy.Name,
			"error", err)
	}

	// Then run on schedule
	for {
		select {
		case <-ctx.Done():
			cw.logger.Info("Cache warming stopped", "strategy", strategy.Name)
			return
		case <-ticker.C:
			if err := cw.executeStrategy(ctx, strategy); err != nil {
				cw.logger.Error("Scheduled cache warming failed",
					"strategy", strategy.Name,
					"error", err)
			}
		}
	}
}

// WarmSpecificKeys warms specific cache keys
func (cw *CacheWarmer) WarmSpecificKeys(ctx context.Context, keys map[string]interface{}, ttl time.Duration) error {
	cw.logger.Info("Warming specific cache keys", "count", len(keys))

	stored := 0
	for key, value := range keys {
		if err := cw.cache.Set(ctx, key, value, ttl); err != nil {
			cw.logger.Warn("Failed to warm cache key",
				"key", key,
				"error", err)
			continue
		}
		stored++
	}

	cw.logger.Info("Specific keys warming completed",
		"requested", len(keys),
		"stored", stored)

	return nil
}

// GetWarmingStats returns statistics about cache warming
func (cw *CacheWarmer) GetWarmingStats(ctx context.Context) (map[string]interface{}, error) {
	// Get cache stats
	cacheStats, err := cw.cache.GetStats(ctx)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"cache_stats":     cacheStats,
		"warming_enabled": true,
		"last_warming":    time.Now(), // In production, track actual last warming time
	}, nil
}
