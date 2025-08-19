// Package cache provides cache warming and invalidation strategies
package cache

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/errors"
	"go.uber.org/zap"
)

// CacheStrategy defines cache management behavior
type CacheStrategy interface {
	Execute(ctx context.Context) error
	GetMetrics() StrategyMetrics
	Stop() error
}

// StrategyMetrics tracks strategy performance
type StrategyMetrics struct {
	ExecutionCount   int64         `json:"execution_count"`
	SuccessCount     int64         `json:"success_count"`
	ErrorCount       int64         `json:"error_count"`
	LastExecution    time.Time     `json:"last_execution"`
	AverageRuntime   time.Duration `json:"average_runtime"`
	ItemsProcessed   int64         `json:"items_processed"`
	CacheHitsAdded   int64         `json:"cache_hits_added"`
	CacheItemsEvicted int64        `json:"cache_items_evicted"`
}

// WarmupStrategy implements intelligent cache warming
type WarmupStrategy struct {
	cache           *ConfidenceCache
	arxEngine       *arxobject.Engine
	logger          *zap.Logger
	config          WarmupConfig
	metrics         StrategyMetrics
	stopCh          chan struct{}
	running         bool
	mutex           sync.RWMutex
}

// WarmupConfig configures cache warming behavior
type WarmupConfig struct {
	Enabled             bool          `yaml:"enabled"`
	Schedule            string        `yaml:"schedule"`           // Cron expression
	BatchSize           int           `yaml:"batch_size"`
	Concurrency         int           `yaml:"concurrency"`
	Timeout             time.Duration `yaml:"timeout"`
	PriorityObjects     []string      `yaml:"priority_objects"`   // Object IDs to prioritize
	ConfidenceThreshold float32       `yaml:"confidence_threshold"` // Only warm objects below this confidence
	MaxAge              time.Duration `yaml:"max_age"`            // Don't warm objects older than this
	WarmupPatterns      bool          `yaml:"warmup_patterns"`    // Whether to warm validation patterns
	WarmupTasks         bool          `yaml:"warmup_tasks"`       // Whether to warm validation tasks
}

// InvalidationStrategy implements intelligent cache invalidation
type InvalidationStrategy struct {
	cache           *ConfidenceCache
	arxEngine       *arxobject.Engine
	logger          *zap.Logger
	config          InvalidationConfig
	metrics         StrategyMetrics
	stopCh          chan struct{}
	running         bool
	mutex           sync.RWMutex
	invalidationQueue chan InvalidationEvent
}

// InvalidationConfig configures cache invalidation behavior
type InvalidationConfig struct {
	Enabled                bool          `yaml:"enabled"`
	ImmediateInvalidation  bool          `yaml:"immediate_invalidation"`
	BatchSize              int           `yaml:"batch_size"`
	ProcessingInterval     time.Duration `yaml:"processing_interval"`
	CascadeRadius          float32       `yaml:"cascade_radius"`        // Spatial radius for cascade invalidation
	ConfidenceChangeThreshold float32    `yaml:"confidence_change_threshold"` // Invalidate if confidence changes by this much
	TTLReduction           time.Duration `yaml:"ttl_reduction"`         // Reduce TTL for related objects
	MaxCascadeDepth        int           `yaml:"max_cascade_depth"`     // Maximum depth for cascade invalidation
}

// InvalidationEvent represents a cache invalidation event
type InvalidationEvent struct {
	Type        string                 `json:"type"`         // confidence_update, object_delete, pattern_change
	ObjectID    string                 `json:"object_id"`
	OldValue    interface{}            `json:"old_value"`
	NewValue    interface{}            `json:"new_value"`
	Timestamp   time.Time              `json:"timestamp"`
	Source      string                 `json:"source"`       // validation, manual, system
	Metadata    map[string]interface{} `json:"metadata"`
	CascadeOptions *CascadeOptions     `json:"cascade_options,omitempty"`
}

// CascadeOptions configures cascade invalidation
type CascadeOptions struct {
	Radius          float32 `json:"radius"`
	MaxObjects      int     `json:"max_objects"`
	ConfidenceThreshold float32 `json:"confidence_threshold"`
	Depth           int     `json:"depth"`
}

// NewWarmupStrategy creates a new cache warming strategy
func NewWarmupStrategy(
	cache *ConfidenceCache,
	arxEngine *arxobject.Engine,
	logger *zap.Logger,
	config WarmupConfig,
) *WarmupStrategy {
	return &WarmupStrategy{
		cache:     cache,
		arxEngine: arxEngine,
		logger:    logger,
		config:    config,
		stopCh:    make(chan struct{}),
	}
}

// Start begins the warmup strategy
func (ws *WarmupStrategy) Start(ctx context.Context) error {
	ws.mutex.Lock()
	if ws.running {
		ws.mutex.Unlock()
		return nil
	}
	ws.running = true
	ws.mutex.Unlock()

	if !ws.config.Enabled {
		ws.logger.Info("Cache warmup strategy disabled")
		return nil
	}

	// Start scheduled warming
	go ws.runScheduledWarmup(ctx)

	ws.logger.Info("Cache warmup strategy started",
		zap.Int("batch_size", ws.config.BatchSize),
		zap.Int("concurrency", ws.config.Concurrency),
		zap.String("schedule", ws.config.Schedule))

	return nil
}

// Stop halts the warmup strategy
func (ws *WarmupStrategy) Stop() error {
	ws.mutex.Lock()
	defer ws.mutex.Unlock()

	if !ws.running {
		return nil
	}

	ws.running = false
	close(ws.stopCh)

	ws.logger.Info("Cache warmup strategy stopped")
	return nil
}

// Execute performs cache warming
func (ws *WarmupStrategy) Execute(ctx context.Context) error {
	start := time.Now()
	ws.metrics.ExecutionCount++

	defer func() {
		runtime := time.Since(start)
		ws.metrics.AverageRuntime = (ws.metrics.AverageRuntime*time.Duration(ws.metrics.ExecutionCount-1) + runtime) / time.Duration(ws.metrics.ExecutionCount)
		ws.metrics.LastExecution = time.Now()
	}()

	// Get objects that need warming
	objectsToWarm, err := ws.getObjectsToWarm(ctx)
	if err != nil {
		ws.metrics.ErrorCount++
		return err
	}

	if len(objectsToWarm) == 0 {
		ws.logger.Debug("No objects need warming")
		return nil
	}

	ws.logger.Info("Starting cache warmup", zap.Int("objects", len(objectsToWarm)))

	// Warm objects in batches
	err = ws.warmObjectsBatch(ctx, objectsToWarm)
	if err != nil {
		ws.metrics.ErrorCount++
		return err
	}

	// Warm validation patterns if enabled
	if ws.config.WarmupPatterns {
		if err := ws.warmValidationPatterns(ctx); err != nil {
			ws.logger.Error("Failed to warm validation patterns", zap.Error(err))
		}
	}

	// Warm validation tasks if enabled
	if ws.config.WarmupTasks {
		if err := ws.warmValidationTasks(ctx); err != nil {
			ws.logger.Error("Failed to warm validation tasks", zap.Error(err))
		}
	}

	ws.metrics.SuccessCount++
	ws.metrics.ItemsProcessed += int64(len(objectsToWarm))

	ws.logger.Info("Cache warmup completed",
		zap.Int("objects_warmed", len(objectsToWarm)),
		zap.Duration("duration", time.Since(start)))

	return nil
}

// runScheduledWarmup runs warming on a schedule
func (ws *WarmupStrategy) runScheduledWarmup(ctx context.Context) {
	// For simplicity, run every hour if schedule is not specified
	interval := time.Hour
	if ws.config.Schedule != "" {
		// In production, parse cron expression
		// interval = parseCronExpression(ws.config.Schedule)
	}

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if err := ws.Execute(ctx); err != nil {
				ws.logger.Error("Scheduled cache warmup failed", zap.Error(err))
			}
		case <-ws.stopCh:
			return
		case <-ctx.Done():
			return
		}
	}
}

// getObjectsToWarm identifies objects that should be warmed
func (ws *WarmupStrategy) getObjectsToWarm(ctx context.Context) ([]string, error) {
	var objectsToWarm []string

	// Priority objects always get warmed
	objectsToWarm = append(objectsToWarm, ws.config.PriorityObjects...)

	// Get recently accessed objects with low cache hit rates
	recentObjects, err := ws.getRecentlyAccessedObjects(ctx)
	if err != nil {
		return nil, err
	}

	// Get objects with low confidence scores
	lowConfidenceObjects, err := ws.getLowConfidenceObjects(ctx)
	if err != nil {
		return nil, err
	}

	// Combine and deduplicate
	allObjects := append(recentObjects, lowConfidenceObjects...)
	objectsToWarm = append(objectsToWarm, ws.deduplicateObjects(allObjects)...)

	return objectsToWarm, nil
}

// warmObjectsBatch warms objects in parallel batches
func (ws *WarmupStrategy) warmObjectsBatch(ctx context.Context, objectIDs []string) error {
	// Process in batches
	for i := 0; i < len(objectIDs); i += ws.config.BatchSize {
		end := i + ws.config.BatchSize
		if end > len(objectIDs) {
			end = len(objectIDs)
		}

		batch := objectIDs[i:end]
		if err := ws.warmBatch(ctx, batch); err != nil {
			ws.logger.Error("Failed to warm batch", zap.Error(err), zap.Strings("batch", batch))
			continue
		}
	}

	return nil
}

// warmBatch warms a single batch of objects
func (ws *WarmupStrategy) warmBatch(ctx context.Context, objectIDs []string) error {
	// Use semaphore to limit concurrency
	semaphore := make(chan struct{}, ws.config.Concurrency)
	errCh := make(chan error, len(objectIDs))
	var wg sync.WaitGroup

	for _, objectID := range objectIDs {
		wg.Add(1)
		go func(id string) {
			defer wg.Done()
			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			if err := ws.warmSingleObject(ctx, id); err != nil {
				errCh <- err
			} else {
				ws.metrics.CacheHitsAdded++
			}
		}(objectID)
	}

	wg.Wait()
	close(errCh)

	// Collect errors
	var errors []error
	for err := range errCh {
		errors = append(errors, err)
	}

	if len(errors) > 0 {
		return fmt.Errorf("warming batch failed with %d errors: %v", len(errors), errors[0])
	}

	return nil
}

// warmSingleObject warms cache for a single object
func (ws *WarmupStrategy) warmSingleObject(ctx context.Context, objectID string) error {
	// Check if already cached
	if cached, err := ws.cache.GetConfidence(ctx, objectID); err == nil && cached != nil {
		return nil // Already cached
	}

	// Get object from engine
	obj, exists := ws.arxEngine.GetObject(parseObjectID(objectID))
	if !exists {
		return fmt.Errorf("object %s not found in engine", objectID)
	}

	// Cache the confidence score
	return ws.cache.SetConfidence(ctx, objectID, &obj.Confidence, "warmup_strategy")
}

// warmValidationPatterns warms frequently used validation patterns
func (ws *WarmupStrategy) warmValidationPatterns(ctx context.Context) error {
	// Get common object types
	objectTypes := []string{"wall", "door", "window", "electrical_outlet", "hvac_unit"}

	for _, objectType := range objectTypes {
		patterns, err := ws.cache.GetPatternsByType(ctx, objectType)
		if err != nil {
			continue
		}

		// Patterns are already cached by the get operation
		ws.logger.Debug("Warmed validation patterns", 
			zap.String("object_type", objectType),
			zap.Int("pattern_count", len(patterns)))
	}

	return nil
}

// warmValidationTasks warms pending validation tasks
func (ws *WarmupStrategy) warmValidationTasks(ctx context.Context) error {
	// Common filter combinations
	filters := []map[string]interface{}{
		{"priority": "8", "limit": "20"},
		{"priority": "7", "limit": "50"},
		{"object_type": "wall", "limit": "30"},
		{"object_type": "door", "limit": "20"},
		{}, // No filters - get all
	}

	for _, filter := range filters {
		tasks, err := ws.cache.GetPendingValidationTasks(ctx, filter)
		if err != nil {
			continue
		}

		ws.logger.Debug("Warmed validation tasks",
			zap.Any("filters", filter),
			zap.Int("task_count", len(tasks)))
	}

	return nil
}

// Utility methods

func (ws *WarmupStrategy) getRecentlyAccessedObjects(ctx context.Context) ([]string, error) {
	// This would typically query access logs or metrics
	// Simplified implementation
	return []string{}, nil
}

func (ws *WarmupStrategy) getLowConfidenceObjects(ctx context.Context) ([]string, error) {
	// This would query the ArxObject engine for low confidence objects
	// Simplified implementation
	return []string{}, nil
}

func (ws *WarmupStrategy) deduplicateObjects(objects []string) []string {
	seen := make(map[string]bool)
	result := []string{}

	for _, obj := range objects {
		if !seen[obj] {
			seen[obj] = true
			result = append(result, obj)
		}
	}

	return result
}

// GetMetrics returns warmup strategy metrics
func (ws *WarmupStrategy) GetMetrics() StrategyMetrics {
	return ws.metrics
}

// InvalidationStrategy implementation

// NewInvalidationStrategy creates a new cache invalidation strategy
func NewInvalidationStrategy(
	cache *ConfidenceCache,
	arxEngine *arxobject.Engine,
	logger *zap.Logger,
	config InvalidationConfig,
) *InvalidationStrategy {
	return &InvalidationStrategy{
		cache:             cache,
		arxEngine:         arxEngine,
		logger:            logger,
		config:            config,
		stopCh:            make(chan struct{}),
		invalidationQueue: make(chan InvalidationEvent, 1000),
	}
}

// Start begins the invalidation strategy
func (is *InvalidationStrategy) Start(ctx context.Context) error {
	is.mutex.Lock()
	if is.running {
		is.mutex.Unlock()
		return nil
	}
	is.running = true
	is.mutex.Unlock()

	if !is.config.Enabled {
		is.logger.Info("Cache invalidation strategy disabled")
		return nil
	}

	// Start invalidation processor
	go is.processInvalidations(ctx)

	is.logger.Info("Cache invalidation strategy started",
		zap.Int("batch_size", is.config.BatchSize),
		zap.Duration("processing_interval", is.config.ProcessingInterval))

	return nil
}

// Stop halts the invalidation strategy
func (is *InvalidationStrategy) Stop() error {
	is.mutex.Lock()
	defer is.mutex.Unlock()

	if !is.running {
		return nil
	}

	is.running = false
	close(is.stopCh)
	close(is.invalidationQueue)

	is.logger.Info("Cache invalidation strategy stopped")
	return nil
}

// Execute processes pending invalidations
func (is *InvalidationStrategy) Execute(ctx context.Context) error {
	start := time.Now()
	is.metrics.ExecutionCount++

	defer func() {
		runtime := time.Since(start)
		is.metrics.AverageRuntime = (is.metrics.AverageRuntime*time.Duration(is.metrics.ExecutionCount-1) + runtime) / time.Duration(is.metrics.ExecutionCount)
		is.metrics.LastExecution = time.Now()
	}()

	// Process batched invalidations
	events := is.collectPendingEvents()
	if len(events) == 0 {
		return nil
	}

	for _, event := range events {
		if err := is.processInvalidationEvent(ctx, event); err != nil {
			is.logger.Error("Failed to process invalidation event", zap.Error(err), zap.Any("event", event))
			is.metrics.ErrorCount++
		} else {
			is.metrics.ItemsProcessed++
		}
	}

	is.metrics.SuccessCount++
	return nil
}

// QueueInvalidation adds an invalidation event to the queue
func (is *InvalidationStrategy) QueueInvalidation(event InvalidationEvent) error {
	if !is.config.Enabled {
		return nil
	}

	select {
	case is.invalidationQueue <- event:
		return nil
	default:
		return errors.NewInternalError("Invalidation queue is full")
	}
}

// processInvalidations processes invalidation events
func (is *InvalidationStrategy) processInvalidations(ctx context.Context) {
	ticker := time.NewTicker(is.config.ProcessingInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if err := is.Execute(ctx); err != nil {
				is.logger.Error("Invalidation processing failed", zap.Error(err))
			}
		case <-is.stopCh:
			return
		case <-ctx.Done():
			return
		}
	}
}

// collectPendingEvents collects pending invalidation events
func (is *InvalidationStrategy) collectPendingEvents() []InvalidationEvent {
	var events []InvalidationEvent
	
	for len(events) < is.config.BatchSize {
		select {
		case event := <-is.invalidationQueue:
			events = append(events, event)
		default:
			break
		}
	}
	
	return events
}

// processInvalidationEvent processes a single invalidation event
func (is *InvalidationStrategy) processInvalidationEvent(ctx context.Context, event InvalidationEvent) error {
	switch event.Type {
	case "confidence_update":
		return is.handleConfidenceUpdate(ctx, event)
	case "object_delete":
		return is.handleObjectDelete(ctx, event)
	case "pattern_change":
		return is.handlePatternChange(ctx, event)
	default:
		return fmt.Errorf("unknown invalidation event type: %s", event.Type)
	}
}

// handleConfidenceUpdate handles confidence score updates
func (is *InvalidationStrategy) handleConfidenceUpdate(ctx context.Context, event InvalidationEvent) error {
	// Invalidate the object's confidence cache
	if err := is.cache.InvalidateObjectConfidence(ctx, event.ObjectID); err != nil {
		return err
	}

	is.metrics.CacheItemsEvicted++

	// Cascade invalidation if configured
	if event.CascadeOptions != nil {
		return is.performCascadeInvalidation(ctx, event)
	}

	return nil
}

// handleObjectDelete handles object deletion
func (is *InvalidationStrategy) handleObjectDelete(ctx context.Context, event InvalidationEvent) error {
	// Remove all cache entries for the object
	if err := is.cache.DeleteConfidence(ctx, event.ObjectID); err != nil {
		return err
	}

	is.metrics.CacheItemsEvicted++
	return nil
}

// handlePatternChange handles validation pattern changes
func (is *InvalidationStrategy) handlePatternChange(ctx context.Context, event InvalidationEvent) error {
	// Invalidate pattern caches
	// This would typically invalidate patterns by type or specific pattern ID
	is.logger.Debug("Pattern change invalidation", zap.Any("event", event))
	return nil
}

// performCascadeInvalidation invalidates related objects within a spatial radius
func (is *InvalidationStrategy) performCascadeInvalidation(ctx context.Context, event InvalidationEvent) error {
	if event.CascadeOptions == nil {
		return nil
	}

	// Get the object to find related objects
	obj, exists := is.arxEngine.GetObject(parseObjectID(event.ObjectID))
	if !exists {
		return nil
	}

	// Query for nearby objects
	x, y, _ := obj.GetPositionMeters()
	radius := event.CascadeOptions.Radius
	
	nearbyIDs := is.arxEngine.QueryRegion(
		float32(x-float64(radius)), float32(y-float64(radius)),
		float32(x+float64(radius)), float32(y+float64(radius)),
	)

	// Invalidate related objects
	invalidated := 0
	for _, id := range nearbyIDs {
		if id == obj.ID {
			continue
		}

		if invalidated >= event.CascadeOptions.MaxObjects {
			break
		}

		if err := is.cache.InvalidateObjectConfidence(ctx, fmt.Sprintf("%d", id)); err != nil {
			is.logger.Debug("Failed to invalidate related object", zap.Uint64("object_id", id), zap.Error(err))
			continue
		}

		invalidated++
		is.metrics.CacheItemsEvicted++
	}

	is.logger.Debug("Cascade invalidation completed",
		zap.String("source_object", event.ObjectID),
		zap.Int("objects_invalidated", invalidated))

	return nil
}

// GetMetrics returns invalidation strategy metrics
func (is *InvalidationStrategy) GetMetrics() StrategyMetrics {
	return is.metrics
}

// Utility function for parsing object IDs
func parseObjectID(id string) uint64 {
	// Simple implementation - in production, use proper parsing
	var result uint64
	fmt.Sscanf(id, "%d", &result)
	return result
}