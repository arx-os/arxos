package services

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"go.uber.org/zap"
)

// MemoryCache provides in-memory caching

// MemoryCache provides in-memory caching
type MemoryCache struct {
	data           map[string]*CacheEntry
	mu             sync.RWMutex
	maxSize        int64
	currentSize    int64
	evictionPolicy CachePolicy
	accessOrder    []string         // For LRU tracking
	accessCount    map[string]int64 // For LFU tracking
	logger         *zap.Logger
}

// DiskCache provides disk-based caching
type DiskCache struct {
	cacheDir       string
	maxSize        int64
	currentSize    int64
	evictionPolicy CachePolicy
	index          map[string]*DiskCacheEntry
	indexMutex     sync.RWMutex
	logger         *zap.Logger
}

// DatabaseCache provides database-based caching
type DatabaseCache struct {
	db          interface{} // Placeholder for database connection
	maxSize     int64
	currentSize int64
	tableName   string
	logger      *zap.Logger
}

// DiskCacheEntry represents an entry in disk cache
type DiskCacheEntry struct {
	Key        string    `json:"key"`
	FilePath   string    `json:"file_path"`
	Size       int64     `json:"size"`
	CreatedAt  time.Time `json:"created_at"`
	AccessedAt time.Time `json:"accessed_at"`
	ExpiresAt  time.Time `json:"expires_at"`
	Compressed bool      `json:"compressed"`
}

// NewMemoryCache creates a new memory cache
func NewMemoryCache(maxSize int64, evictionPolicy CachePolicy, logger *zap.Logger) *MemoryCache {
	return &MemoryCache{
		data:           make(map[string]*CacheEntry),
		maxSize:        maxSize,
		evictionPolicy: evictionPolicy,
		accessOrder:    make([]string, 0),
		accessCount:    make(map[string]int64),
		logger:         logger,
	}
}

// NewDiskCache creates a new disk cache
func NewDiskCache(cacheDir string, maxSize int64, evictionPolicy CachePolicy, logger *zap.Logger) (*DiskCache, error) {
	// Create cache directory if it doesn't exist
	if err := os.MkdirAll(cacheDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create cache directory: %w", err)
	}

	dc := &DiskCache{
		cacheDir:       cacheDir,
		maxSize:        maxSize,
		evictionPolicy: evictionPolicy,
		index:          make(map[string]*DiskCacheEntry),
		logger:         logger,
	}

	// Load existing cache index
	if err := dc.loadIndex(); err != nil {
		logger.Warn("Failed to load disk cache index", zap.Error(err))
	}

	return dc, nil
}

// NewDatabaseCache creates a new database cache
func NewDatabaseCache(db interface{}, maxSize int64, tableName string, logger *zap.Logger) *DatabaseCache {
	return &DatabaseCache{
		db:        db,
		maxSize:   maxSize,
		tableName: tableName,
		logger:    logger,
	}
}

// MemoryCache methods

func (mc *MemoryCache) Get(key string) (*CacheEntry, bool) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	entry, exists := mc.data[key]
	if !exists {
		return nil, false
	}

	// Check expiration
	if !entry.ExpiresAt.IsZero() && time.Now().After(entry.ExpiresAt) {
		delete(mc.data, key)
		mc.removeFromAccessTracking(key)
		return nil, false
	}

	// Update access tracking
	mc.updateAccessTracking(key)
	entry.LastAccess = time.Now()

	return entry, true
}

func (mc *MemoryCache) Set(key string, entry *CacheEntry) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	// Check if entry already exists
	if existing, exists := mc.data[key]; exists {
		mc.currentSize -= existing.SizeBytes
		mc.removeFromAccessTracking(key)
	}

	// Check if we need to evict entries
	entrySize := entry.SizeBytes
	for mc.currentSize+entrySize > mc.maxSize {
		if !mc.evictEntry() {
			return fmt.Errorf("failed to evict entry, cache full")
		}
	}

	// Add entry
	mc.data[key] = entry
	mc.currentSize += entrySize
	mc.addToAccessTracking(key)

	return nil
}

func (mc *MemoryCache) Delete(key string) bool {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	entry, exists := mc.data[key]
	if !exists {
		return false
	}

	mc.currentSize -= entry.SizeBytes
	delete(mc.data, key)
	mc.removeFromAccessTracking(key)

	return true
}

func (mc *MemoryCache) Clear() {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.data = make(map[string]*CacheEntry)
	mc.currentSize = 0
	mc.accessOrder = make([]string, 0)
	mc.accessCount = make(map[string]int64)
}

func (mc *MemoryCache) GetStats() map[string]interface{} {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	return map[string]interface{}{
		"entries_count":   len(mc.data),
		"current_size_mb": mc.currentSize / (1024 * 1024),
		"max_size_mb":     mc.maxSize / (1024 * 1024),
		"utilization":     float64(mc.currentSize) / float64(mc.maxSize) * 100,
		"eviction_policy": mc.evictionPolicy,
	}
}

func (mc *MemoryCache) updateAccessTracking(key string) {
	switch mc.evictionPolicy {
	case PolicyLRU:
		// Move to end of access order
		mc.removeFromAccessOrder(key)
		mc.accessOrder = append(mc.accessOrder, key)
	case PolicyLFU:
		// Increment access count
		mc.accessCount[key]++
	}
}

func (mc *MemoryCache) addToAccessTracking(key string) {
	switch mc.evictionPolicy {
	case PolicyLRU:
		mc.accessOrder = append(mc.accessOrder, key)
	case PolicyLFU:
		mc.accessCount[key] = 1
	}
}

func (mc *MemoryCache) removeFromAccessTracking(key string) {
	switch mc.evictionPolicy {
	case PolicyLRU:
		mc.removeFromAccessOrder(key)
	case PolicyLFU:
		delete(mc.accessCount, key)
	}
}

func (mc *MemoryCache) removeFromAccessOrder(key string) {
	for i, k := range mc.accessOrder {
		if k == key {
			mc.accessOrder = append(mc.accessOrder[:i], mc.accessOrder[i+1:]...)
			break
		}
	}
}

func (mc *MemoryCache) evictEntry() bool {
	switch mc.evictionPolicy {
	case PolicyLRU:
		return mc.evictLRU()
	case PolicyLFU:
		return mc.evictLFU()
	case PolicyFIFO:
		return mc.evictFIFO()
	default:
		return mc.evictLRU() // Default to LRU
	}
}

func (mc *MemoryCache) evictLRU() bool {
	if len(mc.accessOrder) == 0 {
		return false
	}

	keyToEvict := mc.accessOrder[0]
	mc.accessOrder = mc.accessOrder[1:]

	if entry, exists := mc.data[keyToEvict]; exists {
		mc.currentSize -= entry.SizeBytes
		delete(mc.data, keyToEvict)
		delete(mc.accessCount, keyToEvict)
		return true
	}

	return false
}

func (mc *MemoryCache) evictLFU() bool {
	if len(mc.accessCount) == 0 {
		return false
	}

	var keyToEvict string
	var minCount int64 = -1

	for key, count := range mc.accessCount {
		if minCount == -1 || count < minCount {
			minCount = count
			keyToEvict = key
		}
	}

	if keyToEvict != "" {
		if entry, exists := mc.data[keyToEvict]; exists {
			mc.currentSize -= entry.SizeBytes
			delete(mc.data, keyToEvict)
			delete(mc.accessCount, keyToEvict)
			mc.removeFromAccessOrder(keyToEvict)
			return true
		}
	}

	return false
}

func (mc *MemoryCache) evictFIFO() bool {
	// For FIFO, we can use the same logic as LRU since we add to the end
	return mc.evictLRU()
}

// DiskCache methods

func (dc *DiskCache) Get(key string) (*CacheEntry, bool) {
	dc.indexMutex.RLock()
	entry, exists := dc.index[key]
	dc.indexMutex.RUnlock()

	if !exists {
		return nil, false
	}

	// Check expiration
	if !entry.ExpiresAt.IsZero() && time.Now().After(entry.ExpiresAt) {
		dc.Delete(key)
		return nil, false
	}

	// Check if file exists
	if _, err := os.Stat(entry.FilePath); os.IsNotExist(err) {
		dc.Delete(key)
		return nil, false
	}

	// Read file content
	content, err := os.ReadFile(entry.FilePath)
	if err != nil {
		dc.logger.Error("Failed to read disk cache file", zap.String("key", key), zap.Error(err))
		dc.Delete(key)
		return nil, false
	}

	// Update access time
	entry.AccessedAt = time.Now()
	dc.saveIndex()

	// Create cache entry
	cacheEntry := &CacheEntry{
		Value:      content,
		SizeBytes:  entry.Size,
		CreatedAt:  entry.CreatedAt,
		LastAccess: entry.AccessedAt,
		ExpiresAt:  entry.ExpiresAt,
		Compressed: entry.Compressed,
		Level:      LevelL3,
	}

	return cacheEntry, true
}

func (dc *DiskCache) Set(key string, entry *CacheEntry) error {
	// Check if we need to evict entries
	entrySize := entry.SizeBytes
	for dc.currentSize+entrySize > dc.maxSize {
		if !dc.evictEntry() {
			return fmt.Errorf("failed to evict entry, disk cache full")
		}
	}

	// Create file path
	fileName := fmt.Sprintf("%s.cache", key)
	filePath := filepath.Join(dc.cacheDir, fileName)

	// Write content to file
	err := os.WriteFile(filePath, entry.Value.([]byte), 0644)
	if err != nil {
		return fmt.Errorf("failed to write cache file: %w", err)
	}

	// Update index
	dc.indexMutex.Lock()
	defer dc.indexMutex.Unlock()

	// Remove old entry if exists
	if oldEntry, exists := dc.index[key]; exists {
		dc.currentSize -= oldEntry.Size
		os.Remove(oldEntry.FilePath) // Ignore error
	}

	// Add new entry
	dc.index[key] = &DiskCacheEntry{
		Key:        key,
		FilePath:   filePath,
		Size:       entrySize,
		CreatedAt:  entry.CreatedAt,
		AccessedAt: entry.LastAccess,
		ExpiresAt:  entry.ExpiresAt,
		Compressed: entry.Compressed,
	}

	dc.currentSize += entrySize
	dc.saveIndex()

	return nil
}

func (dc *DiskCache) Delete(key string) bool {
	dc.indexMutex.Lock()
	defer dc.indexMutex.Unlock()

	entry, exists := dc.index[key]
	if !exists {
		return false
	}

	// Remove file
	os.Remove(entry.FilePath) // Ignore error

	// Update size and remove from index
	dc.currentSize -= entry.Size
	delete(dc.index, key)
	dc.saveIndex()

	return true
}

func (dc *DiskCache) Clear() {
	dc.indexMutex.Lock()
	defer dc.indexMutex.Unlock()

	// Remove all files
	for _, entry := range dc.index {
		os.Remove(entry.FilePath) // Ignore error
	}

	// Clear index
	dc.index = make(map[string]*DiskCacheEntry)
	dc.currentSize = 0
	dc.saveIndex()
}

func (dc *DiskCache) GetStats() map[string]interface{} {
	dc.indexMutex.RLock()
	defer dc.indexMutex.RUnlock()

	return map[string]interface{}{
		"entries_count":   len(dc.index),
		"current_size_mb": dc.currentSize / (1024 * 1024),
		"max_size_mb":     dc.maxSize / (1024 * 1024),
		"utilization":     float64(dc.currentSize) / float64(dc.maxSize) * 100,
		"eviction_policy": dc.evictionPolicy,
		"cache_dir":       dc.cacheDir,
	}
}

func (dc *DiskCache) loadIndex() error {
	indexPath := filepath.Join(dc.cacheDir, "index.json")

	data, err := os.ReadFile(indexPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil // Index doesn't exist yet
		}
		return err
	}

	var index map[string]*DiskCacheEntry
	if err := json.Unmarshal(data, &index); err != nil {
		return err
	}

	// Validate and calculate current size
	dc.currentSize = 0
	for key, entry := range index {
		if _, err := os.Stat(entry.FilePath); os.IsNotExist(err) {
			delete(index, key)
			continue
		}
		dc.currentSize += entry.Size
	}

	dc.index = index
	return nil
}

func (dc *DiskCache) saveIndex() error {
	indexPath := filepath.Join(dc.cacheDir, "index.json")

	data, err := json.MarshalIndent(dc.index, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(indexPath, data, 0644)
}

func (dc *DiskCache) evictEntry() bool {
	switch dc.evictionPolicy {
	case PolicyLRU:
		return dc.evictLRU()
	case PolicyLFU:
		return dc.evictLFU()
	case PolicyFIFO:
		return dc.evictFIFO()
	default:
		return dc.evictLRU() // Default to LRU
	}
}

func (dc *DiskCache) evictLRU() bool {
	var oldestKey string
	var oldestTime time.Time

	for key, entry := range dc.index {
		if oldestKey == "" || entry.AccessedAt.Before(oldestTime) {
			oldestKey = key
			oldestTime = entry.AccessedAt
		}
	}

	if oldestKey != "" {
		return dc.Delete(oldestKey)
	}

	return false
}

func (dc *DiskCache) evictLFU() bool {
	// For disk cache, we'll use access count from the index
	// This is a simplified implementation
	return dc.evictLRU()
}

func (dc *DiskCache) evictFIFO() bool {
	var oldestKey string
	var oldestTime time.Time

	for key, entry := range dc.index {
		if oldestKey == "" || entry.CreatedAt.Before(oldestTime) {
			oldestKey = key
			oldestTime = entry.CreatedAt
		}
	}

	if oldestKey != "" {
		return dc.Delete(oldestKey)
	}

	return false
}

// DatabaseCache methods

func (dc *DatabaseCache) Get(key string) (*CacheEntry, bool) {
	// Placeholder implementation
	// In a real implementation, this would query the database
	dc.logger.Debug("Database cache get", zap.String("key", key))
	return nil, false
}

func (dc *DatabaseCache) Set(key string, entry *CacheEntry) error {
	// Placeholder implementation
	// In a real implementation, this would insert/update in the database
	dc.logger.Debug("Database cache set", zap.String("key", key))
	return nil
}

func (dc *DatabaseCache) Delete(key string) bool {
	// Placeholder implementation
	// In a real implementation, this would delete from the database
	dc.logger.Debug("Database cache delete", zap.String("key", key))
	return false
}

func (dc *DatabaseCache) Clear() {
	// Placeholder implementation
	// In a real implementation, this would clear the database table
	dc.logger.Debug("Database cache clear")
}

func (dc *DatabaseCache) GetStats() map[string]interface{} {
	// Placeholder implementation
	// In a real implementation, this would query database statistics
	return map[string]interface{}{
		"entries_count":   0,
		"current_size_mb": 0,
		"max_size_mb":     dc.maxSize / (1024 * 1024),
		"utilization":     0.0,
		"table_name":      dc.tableName,
	}
}
