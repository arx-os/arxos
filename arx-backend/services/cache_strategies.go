package services

import (
	"bytes"
	"compress/gzip"
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"io"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	"go.uber.org/zap"
)

// CacheStrategy represents different caching strategies
type CacheStrategy string

const (
	StrategyWriteThrough CacheStrategy = "write_through"
	StrategyWriteBack    CacheStrategy = "write_back"
	StrategyWriteAround  CacheStrategy = "write_around"
	StrategyCopyOnWrite  CacheStrategy = "copy_on_write"
)

// CompressionLevel represents compression levels
type CompressionLevel int

const (
	CompressionNone CompressionLevel = iota
	CompressionFast
	CompressionBest
)

// CacheStrategies provides advanced caching strategies and optimizations
type CacheStrategies struct {
	cacheService *CacheService
	logger       *zap.Logger
	mu           sync.RWMutex

	// Compression settings
	compressionEnabled   bool
	compressionLevel     CompressionLevel
	compressionThreshold int64 // Minimum size to compress

	// Cache warming
	warmupQueue    []CacheWarmupOperation
	warmupInterval time.Duration
	warmupRunning  bool

	// Access patterns
	accessPatterns map[string]*AccessPattern
	patternMutex   sync.RWMutex

	// Predictive caching
	predictionModel *PredictionModel
}

// AccessPattern tracks access patterns for optimization
type AccessPattern struct {
	Key             string
	AccessCount     int64
	LastAccess      time.Time
	AverageInterval time.Duration
	Predictions     []time.Time
}

// PredictionModel provides predictive caching capabilities
type PredictionModel struct {
	patterns    map[string]*AccessPattern
	confidence  float64
	lastUpdated time.Time
	mu          sync.RWMutex
}

// NewCacheStrategies creates a new cache strategies service
func NewCacheStrategies(cacheService *CacheService, logger *zap.Logger) *CacheStrategies {
	cs := &CacheStrategies{
		cacheService:         cacheService,
		logger:               logger,
		compressionEnabled:   true,
		compressionLevel:     CompressionFast,
		compressionThreshold: 1024, // 1KB
		warmupInterval:       5 * time.Minute,
		accessPatterns:       make(map[string]*AccessPattern),
		predictionModel: &PredictionModel{
			patterns:   make(map[string]*AccessPattern),
			confidence: 0.8,
		},
	}

	// Start warmup goroutine
	go cs.warmupWorker()

	return cs
}

// Compress compresses data using gzip
func (cs *CacheStrategies) Compress(data []byte) []byte {
	if !cs.compressionEnabled || int64(len(data)) < cs.compressionThreshold {
		return data
	}

	var buf bytes.Buffer
	var writer *gzip.Writer

	switch cs.compressionLevel {
	case CompressionFast:
		writer = gzip.NewWriter(&buf)
	case CompressionBest:
		writer, _ = gzip.NewWriterLevel(&buf, gzip.BestCompression)
	default:
		return data
	}

	if _, err := writer.Write(data); err != nil {
		cs.logger.Warn("Failed to compress data", zap.Error(err))
		return data
	}

	if err := writer.Close(); err != nil {
		cs.logger.Warn("Failed to close compression writer", zap.Error(err))
		return data
	}

	compressed := buf.Bytes()
	compressionRatio := float64(len(compressed)) / float64(len(data))

	cs.logger.Debug("Data compressed",
		zap.Int("original_size", len(data)),
		zap.Int("compressed_size", len(compressed)),
		zap.Float64("compression_ratio", compressionRatio),
	)

	return compressed
}

// Decompress decompresses data using gzip
func (cs *CacheStrategies) Decompress(data []byte) ([]byte, error) {
	if !cs.isCompressed(data) {
		return data, nil
	}

	reader, err := gzip.NewReader(bytes.NewReader(data))
	if err != nil {
		return nil, fmt.Errorf("failed to create gzip reader: %w", err)
	}
	defer reader.Close()

	decompressed, err := io.ReadAll(reader)
	if err != nil {
		return nil, fmt.Errorf("failed to decompress data: %w", err)
	}

	return decompressed, nil
}

// isCompressed checks if data is compressed
func (cs *CacheStrategies) isCompressed(data []byte) bool {
	return len(data) >= 2 && data[0] == 0x1f && data[1] == 0x8b
}

// GenerateCacheKey generates a cache key based on input parameters
func (cs *CacheStrategies) GenerateCacheKey(prefix string, params map[string]interface{}) string {
	if len(params) == 0 {
		return prefix
	}

	// Sort keys for consistent ordering
	keys := make([]string, 0, len(params))
	for key := range params {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	// Build key string
	var keyParts []string
	keyParts = append(keyParts, prefix)

	for _, key := range keys {
		value := params[key]
		keyParts = append(keyParts, fmt.Sprintf("%s:%v", key, value))
	}

	keyString := strings.Join(keyParts, "|")

	// Generate MD5 hash for long keys
	if len(keyString) > 100 {
		hash := md5.Sum([]byte(keyString))
		return prefix + ":" + hex.EncodeToString(hash[:])
	}

	return keyString
}

// WarmupOperation performs a cache warmup operation
func (cs *CacheStrategies) WarmupOperation(operation CacheWarmupOperation) error {
	cs.mu.Lock()
	defer cs.mu.Unlock()

	// Add to warmup queue
	cs.warmupQueue = append(cs.warmupQueue, operation)

	// Set in cache
	if err := cs.cacheService.Set(operation.Key, operation.Value, operation.TTL); err != nil {
		return fmt.Errorf("failed to warmup cache for key %s: %w", operation.Key, err)
	}

	cs.logger.Debug("Cache warmup completed", zap.String("key", operation.Key))
	return nil
}

// warmupWorker runs the cache warmup worker
func (cs *CacheStrategies) warmupWorker() {
	ticker := time.NewTicker(cs.warmupInterval)
	defer ticker.Stop()

	for range ticker.C {
		cs.processWarmupQueue()
	}
}

// processWarmupQueue processes the warmup queue
func (cs *CacheStrategies) processWarmupQueue() {
	cs.mu.Lock()
	queue := cs.warmupQueue
	cs.warmupQueue = nil
	cs.mu.Unlock()

	if len(queue) == 0 {
		return
	}

	cs.logger.Info("Processing warmup queue", zap.Int("operations", len(queue)))

	// Sort by priority (higher priority first)
	sort.Slice(queue, func(i, j int) bool {
		return queue[i].Priority > queue[j].Priority
	})

	for _, operation := range queue {
		if err := cs.WarmupOperation(operation); err != nil {
			cs.logger.Warn("Failed to process warmup operation", zap.String("key", operation.Key), zap.Error(err))
		}
	}
}

// RecordAccessPattern records an access pattern for prediction
func (cs *CacheStrategies) RecordAccessPattern(key string) {
	cs.patternMutex.Lock()
	defer cs.patternMutex.Unlock()

	now := time.Now()
	pattern, exists := cs.accessPatterns[key]

	if !exists {
		pattern = &AccessPattern{
			Key:         key,
			AccessCount: 0,
			LastAccess:  now,
		}
		cs.accessPatterns[key] = pattern
	}

	// Update access count and timing
	pattern.AccessCount++
	if pattern.LastAccess != (time.Time{}) {
		interval := now.Sub(pattern.LastAccess)
		if pattern.AverageInterval == 0 {
			pattern.AverageInterval = interval
		} else {
			// Exponential moving average
			pattern.AverageInterval = (pattern.AverageInterval + interval) / 2
		}
	}
	pattern.LastAccess = now

	// Generate predictions
	cs.generatePredictions(pattern)
}

// generatePredictions generates access predictions
func (cs *CacheStrategies) generatePredictions(pattern *AccessPattern) {
	if pattern.AverageInterval == 0 {
		return
	}

	// Generate next 3 predicted access times
	pattern.Predictions = nil
	nextAccess := pattern.LastAccess.Add(pattern.AverageInterval)

	for i := 0; i < 3; i++ {
		pattern.Predictions = append(pattern.Predictions, nextAccess)
		nextAccess = nextAccess.Add(pattern.AverageInterval)
	}
}

// GetPredictiveWarmupOperations returns operations for predictive cache warming
func (cs *CacheStrategies) GetPredictiveWarmupOperations() []CacheWarmupOperation {
	cs.patternMutex.RLock()
	defer cs.patternMutex.RUnlock()

	var operations []CacheWarmupOperation
	now := time.Now()

	for key, pattern := range cs.accessPatterns {
		// Check if we should warmup based on predictions
		for _, prediction := range pattern.Predictions {
			if prediction.Sub(now) <= 5*time.Minute && prediction.Sub(now) > 0 {
				operations = append(operations, CacheWarmupOperation{
					Key:         key,
					Value:       nil, // Will be populated by caller
					TTL:         15 * time.Minute,
					Priority:    int(pattern.AccessCount),
					Description: "predictive_warmup",
				})
				break
			}
		}
	}

	return operations
}

// OptimizeCache optimizes cache based on access patterns
func (cs *CacheStrategies) OptimizeCache() error {
	cs.patternMutex.RLock()
	patterns := make(map[string]*AccessPattern)
	for key, pattern := range cs.accessPatterns {
		patterns[key] = pattern
	}
	cs.patternMutex.RUnlock()

	// Analyze patterns and optimize
	for key, pattern := range patterns {
		if pattern.AccessCount > 100 && pattern.AverageInterval > 0 {
			// High-frequency access pattern
			cs.optimizeHighFrequencyPattern(key, pattern)
		} else if pattern.AccessCount < 5 {
			// Low-frequency access pattern
			cs.optimizeLowFrequencyPattern(key, pattern)
		}
	}

	return nil
}

// optimizeHighFrequencyPattern optimizes high-frequency access patterns
func (cs *CacheStrategies) optimizeHighFrequencyPattern(key string, pattern *AccessPattern) {
	// Extend TTL for frequently accessed items
	entry, err := cs.cacheService.GetCacheEntry(key)
	if err == nil && entry != nil {
		extendedTTL := 30 * time.Minute
		cs.cacheService.Expire(key, extendedTTL)
		cs.logger.Debug("Extended TTL for high-frequency pattern", zap.String("key", key))
	}
}

// optimizeLowFrequencyPattern optimizes low-frequency access patterns
func (cs *CacheStrategies) optimizeLowFrequencyPattern(key string, pattern *AccessPattern) {
	// Reduce TTL for infrequently accessed items
	entry, err := cs.cacheService.GetCacheEntry(key)
	if err == nil && entry != nil {
		reducedTTL := 5 * time.Minute
		cs.cacheService.Expire(key, reducedTTL)
		cs.logger.Debug("Reduced TTL for low-frequency pattern", zap.String("key", key))
	}
}

// InvalidateByPattern invalidates cache entries by pattern
func (cs *CacheStrategies) InvalidateByPattern(pattern string) error {
	// Convert pattern to regex
	regexPattern := strings.ReplaceAll(pattern, "*", ".*")
	regex, err := regexp.Compile(regexPattern)
	if err != nil {
		return fmt.Errorf("invalid pattern: %w", err)
	}

	// Find matching keys
	var matchingKeys []string
	cs.patternMutex.RLock()
	for key := range cs.accessPatterns {
		if regex.MatchString(key) {
			matchingKeys = append(matchingKeys, key)
		}
	}
	cs.patternMutex.RUnlock()

	// Invalidate matching keys
	for _, key := range matchingKeys {
		cs.cacheService.Delete(key)
		cs.logger.Debug("Invalidated cache entry by pattern", zap.String("key", key), zap.String("pattern", pattern))
	}

	return nil
}

// GetCacheStats returns detailed cache statistics
func (cs *CacheStrategies) GetCacheStats() map[string]interface{} {
	cs.patternMutex.RLock()
	defer cs.patternMutex.RUnlock()

	stats := map[string]interface{}{
		"total_patterns":      len(cs.accessPatterns),
		"compression_enabled": cs.compressionEnabled,
		"compression_level":   cs.compressionLevel,
		"warmup_queue_size":   len(cs.warmupQueue),
	}

	// Pattern statistics
	var highFreqCount, lowFreqCount int
	var totalAccessCount int64

	for _, pattern := range cs.accessPatterns {
		totalAccessCount += pattern.AccessCount
		if pattern.AccessCount > 100 {
			highFreqCount++
		} else if pattern.AccessCount < 5 {
			lowFreqCount++
		}
	}

	stats["high_frequency_patterns"] = highFreqCount
	stats["low_frequency_patterns"] = lowFreqCount
	stats["total_access_count"] = totalAccessCount

	return stats
}

// SetCompressionSettings configures compression settings
func (cs *CacheStrategies) SetCompressionSettings(enabled bool, level CompressionLevel, threshold int64) {
	cs.mu.Lock()
	defer cs.mu.Unlock()

	cs.compressionEnabled = enabled
	cs.compressionLevel = level
	cs.compressionThreshold = threshold

	cs.logger.Info("Compression settings updated",
		zap.Bool("enabled", enabled),
		zap.Int("level", int(level)),
		zap.Int64("threshold", threshold),
	)
}

// GetCompressionRatio calculates compression ratio for data
func (cs *CacheStrategies) GetCompressionRatio(original, compressed []byte) float64 {
	if len(original) == 0 {
		return 1.0
	}
	return float64(len(compressed)) / float64(len(original))
}

// BatchOperations performs batch cache operations
func (cs *CacheStrategies) BatchOperations(operations []CacheOperation) error {
	if len(operations) == 0 {
		return nil
	}

	// Group operations by type
	sets := make(map[string]interface{})
	var deletes []string

	for _, op := range operations {
		switch op.Type {
		case "set":
			sets[op.Key] = op.Value
		case "delete":
			deletes = append(deletes, op.Key)
		}
	}

	// Execute batch operations
	if len(sets) > 0 {
		if err := cs.cacheService.MSet(sets, 15*time.Minute); err != nil {
			cs.logger.Warn("Failed to execute batch sets", zap.Error(err))
		}
	}

	for _, key := range deletes {
		cs.cacheService.Delete(key)
	}

	cs.logger.Debug("Batch operations completed",
		zap.Int("sets", len(sets)),
		zap.Int("deletes", len(deletes)),
	)

	return nil
}

// CacheOperation represents a cache operation
type CacheOperation struct {
	Type  string        `json:"type"` // set, delete
	Key   string        `json:"key"`
	Value interface{}   `json:"value,omitempty"`
	TTL   time.Duration `json:"ttl,omitempty"`
}

// GetAccessPatterns returns access patterns for analysis
func (cs *CacheStrategies) GetAccessPatterns() map[string]*AccessPattern {
	cs.patternMutex.RLock()
	defer cs.patternMutex.RUnlock()

	patterns := make(map[string]*AccessPattern)
	for key, pattern := range cs.accessPatterns {
		patterns[key] = pattern
	}

	return patterns
}

// ClearAccessPatterns clears all access patterns
func (cs *CacheStrategies) ClearAccessPatterns() {
	cs.patternMutex.Lock()
	defer cs.patternMutex.Unlock()

	cs.accessPatterns = make(map[string]*AccessPattern)
	cs.logger.Info("Access patterns cleared")
}

// GetWarmupQueue returns the current warmup queue
func (cs *CacheStrategies) GetWarmupQueue() []CacheWarmupOperation {
	cs.mu.RLock()
	defer cs.mu.RUnlock()

	queue := make([]CacheWarmupOperation, len(cs.warmupQueue))
	copy(queue, cs.warmupQueue)

	return queue
}

// ClearWarmupQueue clears the warmup queue
func (cs *CacheStrategies) ClearWarmupQueue() {
	cs.mu.Lock()
	defer cs.mu.Unlock()

	cs.warmupQueue = nil
	cs.logger.Info("Warmup queue cleared")
}
