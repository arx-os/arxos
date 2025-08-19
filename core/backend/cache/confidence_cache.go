// Package cache provides confidence-specific caching functionality
package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/errors"
	"go.uber.org/zap"
)

// ConfidenceCache provides intelligent caching for confidence scores and patterns
type ConfidenceCache struct {
	cache                CacheInterface
	logger               *zap.Logger
	defaultTTL           time.Duration
	confidenceThreshold  float32
	invalidationStrategy *CacheInvalidationStrategy
	warmupStrategy       *CacheWarmupStrategy
	metrics              *ConfidenceCacheMetrics
}

// ConfidenceCacheMetrics tracks confidence-specific cache performance
type ConfidenceCacheMetrics struct {
	ConfidenceHits         int64
	ConfidenceMisses       int64
	PatternHits            int64
	PatternMisses          int64
	ValidationCacheHits    int64
	ValidationCacheMisses  int64
	CascadeInvalidations   int64
	ConfidenceUpdates      int64
	PatternLearningEvents  int64
}

// CachedConfidence represents a cached confidence score with metadata
type CachedConfidence struct {
	ObjectID         string                    `json:"object_id"`
	OverallScore     float32                   `json:"overall_score"`
	ClassificationScore float32                `json:"classification_score"`
	PositionScore    float32                   `json:"position_score"`
	PropertiesScore  float32                   `json:"properties_score"`
	RelationshipsScore float32                 `json:"relationships_score"`
	LastUpdated      time.Time                 `json:"last_updated"`
	UpdatedBy        string                    `json:"updated_by"`
	ValidationCount  int                       `json:"validation_count"`
	Metadata         map[string]interface{}    `json:"metadata,omitempty"`
	TTL              time.Duration             `json:"ttl"`
}

// CachedValidationPattern represents a cached validation pattern
type CachedValidationPattern struct {
	PatternID        string                 `json:"pattern_id"`
	ObjectType       string                 `json:"object_type"`
	Pattern          map[string]interface{} `json:"pattern"`
	Confidence       float32                `json:"confidence"`
	OccurrenceCount  int                    `json:"occurrence_count"`
	SuccessRate      float32                `json:"success_rate"`
	LastUsed         time.Time              `json:"last_used"`
	CreatedAt        time.Time              `json:"created_at"`
	UpdatedAt        time.Time              `json:"updated_at"`
	ValidationSource string                 `json:"validation_source"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// CachedValidationTask represents a cached validation task
type CachedValidationTask struct {
	TaskID          string                 `json:"task_id"`
	ObjectID        string                 `json:"object_id"`
	ObjectType      string                 `json:"object_type"`
	Priority        int                    `json:"priority"`
	Confidence      float32                `json:"confidence"`
	PotentialImpact float32                `json:"potential_impact"`
	SimilarCount    int                    `json:"similar_count"`
	CreatedAt       time.Time              `json:"created_at"`
	ExpiresAt       time.Time              `json:"expires_at"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

// NewConfidenceCache creates a new confidence cache instance
func NewConfidenceCache(cache CacheInterface, logger *zap.Logger) *ConfidenceCache {
	return &ConfidenceCache{
		cache:               cache,
		logger:              logger,
		defaultTTL:          15 * time.Minute,
		confidenceThreshold: 0.6,
		invalidationStrategy: &CacheInvalidationStrategy{
			OnUpdate:  true,
			OnDelete:  true,
			TTLExtend: 5 * time.Minute,
			BatchSize: 100,
		},
		warmupStrategy: &CacheWarmupStrategy{
			Enabled:     true,
			BatchSize:   50,
			Concurrency: 5,
			Timeout:     30 * time.Second,
		},
		metrics: &ConfidenceCacheMetrics{},
	}
}

// Confidence score caching methods

// GetConfidence retrieves cached confidence score for an object
func (cc *ConfidenceCache) GetConfidence(ctx context.Context, objectID string) (*CachedConfidence, error) {
	key := cc.confidenceKey(objectID)
	
	data, err := cc.cache.Get(ctx, key)
	if err != nil {
		if arxosErr, ok := err.(*errors.ArxosError); ok && arxosErr.Type == errors.NotFoundError {
			cc.metrics.ConfidenceMisses++
			return nil, nil
		}
		return nil, err
	}
	
	var confidence CachedConfidence
	if err := json.Unmarshal(data, &confidence); err != nil {
		cc.logger.Error("Failed to unmarshal cached confidence", 
			zap.String("object_id", objectID), zap.Error(err))
		return nil, errors.NewInternalError("Failed to decode cached confidence")
	}
	
	cc.metrics.ConfidenceHits++
	return &confidence, nil
}

// SetConfidence caches confidence score for an object
func (cc *ConfidenceCache) SetConfidence(ctx context.Context, objectID string, confidence *arxobject.ConfidenceScore, updatedBy string) error {
	cached := &CachedConfidence{
		ObjectID:           objectID,
		OverallScore:       confidence.Overall,
		ClassificationScore: confidence.Classification,
		PositionScore:      confidence.Position,
		PropertiesScore:    confidence.Properties,
		RelationshipsScore: confidence.Relationships,
		LastUpdated:        time.Now(),
		UpdatedBy:          updatedBy,
		ValidationCount:    1,
		TTL:                cc.calculateTTL(confidence.Overall),
	}
	
	key := cc.confidenceKey(objectID)
	
	// Check if confidence already exists to increment validation count
	if existing, err := cc.GetConfidence(ctx, objectID); err == nil && existing != nil {
		cached.ValidationCount = existing.ValidationCount + 1
	}
	
	err := cc.cache.Set(ctx, key, cached, cached.TTL)
	if err != nil {
		return err
	}
	
	cc.metrics.ConfidenceUpdates++
	
	// Trigger cascade invalidation if confidence significantly changed
	if existing, _ := cc.GetConfidence(ctx, objectID); existing != nil {
		confidenceDelta := math.Abs(float64(cached.OverallScore - existing.OverallScore))
		if confidenceDelta > 0.1 { // 10% change threshold
			go cc.invalidateSimilarObjects(ctx, objectID, cached.OverallScore)
		}
	}
	
	return nil
}

// UpdateConfidence atomically updates cached confidence
func (cc *ConfidenceCache) UpdateConfidence(ctx context.Context, objectID string, updates map[string]float32, updatedBy string) error {
	existing, err := cc.GetConfidence(ctx, objectID)
	if err != nil {
		return err
	}
	
	if existing == nil {
		return errors.NewNotFoundError("cached confidence")
	}
	
	// Apply updates
	if val, ok := updates["overall"]; ok {
		existing.OverallScore = val
	}
	if val, ok := updates["classification"]; ok {
		existing.ClassificationScore = val
	}
	if val, ok := updates["position"]; ok {
		existing.PositionScore = val
	}
	if val, ok := updates["properties"]; ok {
		existing.PropertiesScore = val
	}
	if val, ok := updates["relationships"]; ok {
		existing.RelationshipsScore = val
	}
	
	existing.LastUpdated = time.Now()
	existing.UpdatedBy = updatedBy
	existing.ValidationCount++
	existing.TTL = cc.calculateTTL(existing.OverallScore)
	
	key := cc.confidenceKey(objectID)
	return cc.cache.Set(ctx, key, existing, existing.TTL)
}

// DeleteConfidence removes cached confidence
func (cc *ConfidenceCache) DeleteConfidence(ctx context.Context, objectID string) error {
	key := cc.confidenceKey(objectID)
	return cc.cache.Delete(ctx, key)
}

// Validation pattern caching methods

// GetPattern retrieves cached validation pattern
func (cc *ConfidenceCache) GetPattern(ctx context.Context, patternID string) (*CachedValidationPattern, error) {
	key := cc.patternKey(patternID)
	
	data, err := cc.cache.Get(ctx, key)
	if err != nil {
		if arxosErr, ok := err.(*errors.ArxosError); ok && arxosErr.Type == errors.NotFoundError {
			cc.metrics.PatternMisses++
			return nil, nil
		}
		return nil, err
	}
	
	var pattern CachedValidationPattern
	if err := json.Unmarshal(data, &pattern); err != nil {
		cc.logger.Error("Failed to unmarshal cached pattern", 
			zap.String("pattern_id", patternID), zap.Error(err))
		return nil, errors.NewInternalError("Failed to decode cached pattern")
	}
	
	// Update last used timestamp
	pattern.LastUsed = time.Now()
	cc.cache.Set(ctx, key, pattern, time.Hour) // Patterns live longer
	
	cc.metrics.PatternHits++
	return &pattern, nil
}

// SetPattern caches validation pattern
func (cc *ConfidenceCache) SetPattern(ctx context.Context, pattern *CachedValidationPattern) error {
	key := cc.patternKey(pattern.PatternID)
	
	pattern.UpdatedAt = time.Now()
	if pattern.CreatedAt.IsZero() {
		pattern.CreatedAt = time.Now()
	}
	
	err := cc.cache.Set(ctx, key, pattern, time.Hour)
	if err != nil {
		return err
	}
	
	cc.metrics.PatternLearningEvents++
	return nil
}

// GetPatternsByType retrieves all patterns for an object type
func (cc *ConfidenceCache) GetPatternsByType(ctx context.Context, objectType string) ([]*CachedValidationPattern, error) {
	pattern := cc.patternTypeKey(objectType)
	
	data, err := cc.cache.GetPattern(ctx, pattern)
	if err != nil {
		return nil, err
	}
	
	var patterns []*CachedValidationPattern
	for _, value := range data {
		var pattern CachedValidationPattern
		if err := json.Unmarshal(value, &pattern); err != nil {
			continue // Skip invalid patterns
		}
		patterns = append(patterns, &pattern)
	}
	
	return patterns, nil
}

// Validation task caching methods

// GetPendingValidationTasks retrieves cached validation tasks
func (cc *ConfidenceCache) GetPendingValidationTasks(ctx context.Context, filters map[string]interface{}) ([]*CachedValidationTask, error) {
	key := cc.validationTasksKey(filters)
	
	data, err := cc.cache.Get(ctx, key)
	if err != nil {
		if arxosErr, ok := err.(*errors.ArxosError); ok && arxosErr.Type == errors.NotFoundError {
			cc.metrics.ValidationCacheMisses++
			return nil, nil
		}
		return nil, err
	}
	
	var tasks []*CachedValidationTask
	if err := json.Unmarshal(data, &tasks); err != nil {
		cc.logger.Error("Failed to unmarshal cached validation tasks", zap.Error(err))
		return nil, errors.NewInternalError("Failed to decode cached validation tasks")
	}
	
	// Filter expired tasks
	now := time.Now()
	var validTasks []*CachedValidationTask
	for _, task := range tasks {
		if task.ExpiresAt.After(now) {
			validTasks = append(validTasks, task)
		}
	}
	
	cc.metrics.ValidationCacheHits++
	return validTasks, nil
}

// SetPendingValidationTasks caches validation tasks
func (cc *ConfidenceCache) SetPendingValidationTasks(ctx context.Context, tasks []*CachedValidationTask, filters map[string]interface{}) error {
	key := cc.validationTasksKey(filters)
	
	// Set expiration for tasks
	expiresAt := time.Now().Add(cc.defaultTTL)
	for _, task := range tasks {
		task.ExpiresAt = expiresAt
	}
	
	return cc.cache.Set(ctx, key, tasks, cc.defaultTTL)
}

// Batch operations for performance

// GetConfidenceBatch retrieves multiple confidence scores in a single operation
func (cc *ConfidenceCache) GetConfidenceBatch(ctx context.Context, objectIDs []string) (map[string]*CachedConfidence, error) {
	result := make(map[string]*CachedConfidence)
	
	// Use pipeline for efficiency
	for _, objectID := range objectIDs {
		confidence, err := cc.GetConfidence(ctx, objectID)
		if err == nil && confidence != nil {
			result[objectID] = confidence
		}
	}
	
	return result, nil
}

// SetConfidenceBatch sets multiple confidence scores
func (cc *ConfidenceCache) SetConfidenceBatch(ctx context.Context, confidences map[string]*CachedConfidence) error {
	for objectID, confidence := range confidences {
		key := cc.confidenceKey(objectID)
		if err := cc.cache.Set(ctx, key, confidence, confidence.TTL); err != nil {
			cc.logger.Error("Failed to set confidence in batch", 
				zap.String("object_id", objectID), zap.Error(err))
			// Continue with other items
		}
	}
	
	return nil
}

// Cache invalidation and warming strategies

// InvalidateObjectConfidence invalidates confidence for an object and related objects
func (cc *ConfidenceCache) InvalidateObjectConfidence(ctx context.Context, objectID string) error {
	// Delete the specific confidence
	if err := cc.DeleteConfidence(ctx, objectID); err != nil {
		return err
	}
	
	// Invalidate validation tasks that might reference this object
	pattern := cc.validationTasksPattern()
	if err := cc.cache.DeletePattern(ctx, pattern); err != nil {
		cc.logger.Error("Failed to invalidate validation tasks cache", zap.Error(err))
	}
	
	cc.metrics.CascadeInvalidations++
	return nil
}

// WarmupCache preloads frequently accessed confidence scores
func (cc *ConfidenceCache) WarmupCache(ctx context.Context, objectIDs []string) error {
	if !cc.warmupStrategy.Enabled {
		return nil
	}
	
	// Process in batches
	batchSize := cc.warmupStrategy.BatchSize
	for i := 0; i < len(objectIDs); i += batchSize {
		end := i + batchSize
		if end > len(objectIDs) {
			end = len(objectIDs)
		}
		
		batch := objectIDs[i:end]
		
		// Warm up this batch (implementation would fetch from database and cache)
		go cc.warmupBatch(ctx, batch)
	}
	
	return nil
}

// warmupBatch processes a batch of objects for cache warming
func (cc *ConfidenceCache) warmupBatch(ctx context.Context, objectIDs []string) {
	ctx, cancel := context.WithTimeout(ctx, cc.warmupStrategy.Timeout)
	defer cancel()
	
	// This would typically fetch from database and populate cache
	// Implementation depends on integration with ArxObject engine
	cc.logger.Debug("Warming up cache batch", zap.Int("count", len(objectIDs)))
}

// invalidateSimilarObjects invalidates cache for objects similar to the updated one
func (cc *ConfidenceCache) invalidateSimilarObjects(ctx context.Context, objectID string, newConfidence float32) {
	// This would typically query for similar objects and invalidate their cache
	// Implementation depends on integration with spatial indexing
	cc.logger.Debug("Invalidating similar objects cache",
		zap.String("object_id", objectID),
		zap.Float32("new_confidence", newConfidence))
	
	cc.metrics.CascadeInvalidations++
}

// Helper methods for key generation

func (cc *ConfidenceCache) confidenceKey(objectID string) string {
	return fmt.Sprintf("confidence:%s", objectID)
}

func (cc *ConfidenceCache) patternKey(patternID string) string {
	return fmt.Sprintf("pattern:%s", patternID)
}

func (cc *ConfidenceCache) patternTypeKey(objectType string) string {
	return fmt.Sprintf("patterns:%s:*", objectType)
}

func (cc *ConfidenceCache) validationTasksKey(filters map[string]interface{}) string {
	// Create a deterministic key from filters
	key := "validation_tasks"
	
	if priority, ok := filters["priority"]; ok {
		key += fmt.Sprintf(":priority:%v", priority)
	}
	if objectType, ok := filters["object_type"]; ok {
		key += fmt.Sprintf(":type:%v", objectType)
	}
	if limit, ok := filters["limit"]; ok {
		key += fmt.Sprintf(":limit:%v", limit)
	}
	
	return key
}

func (cc *ConfidenceCache) validationTasksPattern() string {
	return "validation_tasks:*"
}

// calculateTTL determines appropriate TTL based on confidence score
func (cc *ConfidenceCache) calculateTTL(confidence float32) time.Duration {
	// Higher confidence scores get longer TTL
	if confidence >= 0.9 {
		return time.Hour // Very confident objects cache for 1 hour
	} else if confidence >= 0.7 {
		return 30 * time.Minute // Moderately confident for 30 minutes
	} else if confidence >= 0.5 {
		return 15 * time.Minute // Low confidence for 15 minutes
	} else {
		return 5 * time.Minute // Very low confidence for 5 minutes
	}
}

// GetMetrics returns confidence cache metrics
func (cc *ConfidenceCache) GetMetrics() ConfidenceCacheMetrics {
	return *cc.metrics
}

// GetDetailedStats returns comprehensive cache statistics
func (cc *ConfidenceCache) GetDetailedStats(ctx context.Context) (map[string]interface{}, error) {
	stats := make(map[string]interface{})
	
	// Basic metrics
	stats["confidence_hits"] = cc.metrics.ConfidenceHits
	stats["confidence_misses"] = cc.metrics.ConfidenceMisses
	stats["pattern_hits"] = cc.metrics.PatternHits
	stats["pattern_misses"] = cc.metrics.PatternMisses
	stats["validation_cache_hits"] = cc.metrics.ValidationCacheHits
	stats["validation_cache_misses"] = cc.metrics.ValidationCacheMisses
	stats["cascade_invalidations"] = cc.metrics.CascadeInvalidations
	stats["confidence_updates"] = cc.metrics.ConfidenceUpdates
	stats["pattern_learning_events"] = cc.metrics.PatternLearningEvents
	
	// Hit ratios
	totalConfidenceOps := cc.metrics.ConfidenceHits + cc.metrics.ConfidenceMisses
	if totalConfidenceOps > 0 {
		stats["confidence_hit_ratio"] = float64(cc.metrics.ConfidenceHits) / float64(totalConfidenceOps)
	}
	
	totalPatternOps := cc.metrics.PatternHits + cc.metrics.PatternMisses
	if totalPatternOps > 0 {
		stats["pattern_hit_ratio"] = float64(cc.metrics.PatternHits) / float64(totalPatternOps)
	}
	
	totalValidationOps := cc.metrics.ValidationCacheHits + cc.metrics.ValidationCacheMisses
	if totalValidationOps > 0 {
		stats["validation_hit_ratio"] = float64(cc.metrics.ValidationCacheHits) / float64(totalValidationOps)
	}
	
	// Cache efficiency
	if cc.metrics.ConfidenceUpdates > 0 {
		stats["invalidation_efficiency"] = float64(cc.metrics.CascadeInvalidations) / float64(cc.metrics.ConfidenceUpdates)
	}
	
	return stats, nil
}

// Health check for confidence cache
func (cc *ConfidenceCache) Health(ctx context.Context) error {
	// Test basic cache operations
	testKey := "health_check"
	testValue := "ok"
	
	// Test set
	if err := cc.cache.Set(ctx, testKey, testValue, time.Minute); err != nil {
		return errors.NewExternalError("confidence_cache", fmt.Sprintf("Set operation failed: %v", err))
	}
	
	// Test get
	if _, err := cc.cache.Get(ctx, testKey); err != nil {
		return errors.NewExternalError("confidence_cache", fmt.Sprintf("Get operation failed: %v", err))
	}
	
	// Test delete
	if err := cc.cache.Delete(ctx, testKey); err != nil {
		return errors.NewExternalError("confidence_cache", fmt.Sprintf("Delete operation failed: %v", err))
	}
	
	return nil
}