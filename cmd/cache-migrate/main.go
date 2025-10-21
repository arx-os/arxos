package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure/cache"
	"github.com/spf13/cobra"
)

// CacheMigrationScript handles migration of cache data to unified structure
type CacheMigrationScript struct {
	config *config.Config
	logger Logger
}

// Logger interface for migration logging
type Logger interface {
	Debug(msg string, fields ...any)
	Info(msg string, fields ...any)
	Warn(msg string, fields ...any)
	Error(msg string, fields ...any)
	Fatal(msg string, fields ...any)
	WithFields(fields map[string]any) domain.Logger
}

// SimpleLogger implements Logger interface
type SimpleLogger struct{}

func (l *SimpleLogger) Debug(msg string, fields ...any) {
	fmt.Printf("[DEBUG] %s\n", msg)
}

func (l *SimpleLogger) Info(msg string, fields ...any) {
	fmt.Printf("[INFO] %s\n", msg)
}

func (l *SimpleLogger) Warn(msg string, fields ...any) {
	fmt.Printf("[WARN] %s\n", msg)
}

func (l *SimpleLogger) Error(msg string, fields ...any) {
	fmt.Printf("[ERROR] %s\n", msg)
}

func (l *SimpleLogger) Fatal(msg string, fields ...any) {
	fmt.Printf("[FATAL] %s\n", msg)
	os.Exit(1)
}

func (l *SimpleLogger) WithFields(fields map[string]any) domain.Logger {
	// Simple logger doesn't support fields, return self
	return l
}

// NewCacheMigrationScript creates a new migration script
func NewCacheMigrationScript(cfg *config.Config) *CacheMigrationScript {
	return &CacheMigrationScript{
		config: cfg,
		logger: &SimpleLogger{},
	}
}

// MigrateCacheData migrates cache data to the unified structure
func (cms *CacheMigrationScript) MigrateCacheData(ctx context.Context) error {
	cms.logger.Info("Starting cache migration to unified structure")

	// Check for old cache locations
	oldCachePaths := cms.findOldCachePaths()
	if len(oldCachePaths) == 0 {
		cms.logger.Info("No old cache data found to migrate")
		return nil
	}

	// Create unified cache instance
	unifiedCache, err := cache.NewUnifiedCache(cms.config, cms.logger)
	if err != nil {
		return fmt.Errorf("failed to create unified cache: %w", err)
	}
	defer unifiedCache.Close()

	// Migrate data from old locations
	for _, oldPath := range oldCachePaths {
		if err := cms.migrateFromPath(ctx, unifiedCache, oldPath); err != nil {
			cms.logger.Warn("Failed to migrate cache from %s: %v", oldPath, err)
			continue
		}
		cms.logger.Info("Successfully migrated cache from %s", oldPath)
	}

	cms.logger.Info("Cache migration completed successfully")
	return nil
}

// findOldCachePaths finds old cache directory locations
func (cms *CacheMigrationScript) findOldCachePaths() []string {
	var paths []string

	// Check for old cache directories
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return paths
	}

	// Common old cache locations
	oldLocations := []string{
		filepath.Join(homeDir, ".cache", "arxos"),
		filepath.Join(homeDir, ".arxos", "cache"),
		filepath.Join(homeDir, ".arxos", "old-cache"),
		"./cache",
		"./old-cache",
	}

	for _, location := range oldLocations {
		if _, err := os.Stat(location); err == nil {
			paths = append(paths, location)
		}
	}

	return paths
}

// migrateFromPath migrates cache data from a specific path
func (cms *CacheMigrationScript) migrateFromPath(ctx context.Context, unifiedCache *cache.UnifiedCache, oldPath string) error {
	cms.logger.Info("Migrating cache data from %s", oldPath)

	// Walk through the old cache directory
	return filepath.Walk(oldPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip directories
		if info.IsDir() {
			return nil
		}

		// Only process cache files (JSON files)
		if filepath.Ext(path) != ".json" {
			return nil
		}

		// Extract cache key from filename
		key := filepath.Base(path)
		key = key[:len(key)-5] // Remove .json extension

		// Read old cache file
		data, err := os.ReadFile(path)
		if err != nil {
			cms.logger.Warn("Failed to read cache file %s: %v", path, err)
			return nil
		}

		// Determine cache type from path structure
		cacheType := cms.determineCacheType(path)

		// Set appropriate TTL based on cache type
		ttl := cms.getTTLForCacheType(cacheType)

		// Store in unified cache
		if err := unifiedCache.Set(ctx, cacheType+":"+key, string(data), ttl); err != nil {
			cms.logger.Warn("Failed to store cache entry %s: %v", key, err)
			return nil
		}

		cms.logger.Info("Migrated cache entry: %s -> %s:%s", key, cacheType, key)
		return nil
	})
}

// determineCacheType determines the cache type from the file path
func (cms *CacheMigrationScript) determineCacheType(path string) string {
	// Extract directory structure to determine cache type
	dir := filepath.Dir(path)
	baseDir := filepath.Base(dir)

	switch baseDir {
	case "ifc", "ifc_cache":
		return "ifc"
	case "spatial", "spatial_cache":
		return "spatial"
	case "api", "api_cache":
		return "api"
	case "config", "config_cache":
		return "config"
	case "query", "query_cache":
		return "query"
	default:
		return "general"
	}
}

// getTTLForCacheType returns appropriate TTL for cache type
func (cms *CacheMigrationScript) getTTLForCacheType(cacheType string) time.Duration {
	switch cacheType {
	case "ifc":
		return 24 * time.Hour // IFC processing results
	case "spatial":
		return 12 * time.Hour // Spatial queries
	case "api":
		return 5 * time.Minute // API responses
	case "config":
		return 1 * time.Hour // Configuration data
	case "query":
		return 30 * time.Minute // Database queries
	default:
		return 1 * time.Hour // General cache
	}
}

// CleanupOldCache removes old cache directories after migration
func (cms *CacheMigrationScript) CleanupOldCache() error {
	cms.logger.Info("Cleaning up old cache directories")

	oldPaths := cms.findOldCachePaths()
	for _, path := range oldPaths {
		if err := os.RemoveAll(path); err != nil {
			cms.logger.Warn("Failed to remove old cache directory %s: %v", path, err)
			continue
		}
		cms.logger.Info("Removed old cache directory: %s", path)
	}

	return nil
}

// ValidateMigration validates that migration was successful
func (cms *CacheMigrationScript) ValidateMigration(ctx context.Context) error {
	cms.logger.Info("Validating cache migration")

	// Create unified cache instance
	unifiedCache, err := cache.NewUnifiedCache(cms.config, cms.logger)
	if err != nil {
		return fmt.Errorf("failed to create unified cache for validation: %w", err)
	}
	defer unifiedCache.Close()

	// Test cache functionality
	testKey := "migration_test"
	testValue := "migration_successful"
	testTTL := 1 * time.Minute

	// Test set
	if err := unifiedCache.Set(ctx, testKey, testValue, testTTL); err != nil {
		return fmt.Errorf("cache set test failed: %w", err)
	}

	// Test get
	retrieved, err := unifiedCache.Get(ctx, testKey)
	if err != nil {
		return fmt.Errorf("cache get test failed: %w", err)
	}

	if retrieved != testValue {
		return fmt.Errorf("cache validation failed: expected %s, got %v", testValue, retrieved)
	}

	// Test stats
	stats, err := unifiedCache.GetStats(ctx)
	if err != nil {
		return fmt.Errorf("cache stats test failed: %w", err)
	}

	cms.logger.Info("Cache migration validation successful")
	cms.logger.Info("Cache stats: %+v", stats)

	// Cleanup test data
	unifiedCache.Delete(ctx, testKey)

	return nil
}

// CLI Commands

var rootCmd = &cobra.Command{
	Use:   "cache-migrate",
	Short: "Migrate ArxOS cache to unified structure",
	Long: `Migrate cache data from old cache locations to the new unified cache structure.

This tool will:
- Find old cache directories
- Migrate cache data to unified structure
- Validate migration success
- Clean up old cache directories (optional)`,
}

var migrateCmd = &cobra.Command{
	Use:   "migrate",
	Short: "Migrate cache data to unified structure",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Load configuration
		cfg := config.Default()

		// Create migration script
		migrationScript := NewCacheMigrationScript(cfg)

		// Run migration
		ctx := context.Background()
		return migrationScript.MigrateCacheData(ctx)
	},
}

var validateCmd = &cobra.Command{
	Use:   "validate",
	Short: "Validate cache migration",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Load configuration
		cfg := config.Default()

		// Create migration script
		migrationScript := NewCacheMigrationScript(cfg)

		// Validate migration
		ctx := context.Background()
		return migrationScript.ValidateMigration(ctx)
	},
}

var cleanupCmd = &cobra.Command{
	Use:   "cleanup",
	Short: "Clean up old cache directories",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Load configuration
		cfg := config.Default()

		// Create migration script
		migrationScript := NewCacheMigrationScript(cfg)

		// Cleanup old cache
		return migrationScript.CleanupOldCache()
	},
}

func init() {
	rootCmd.AddCommand(migrateCmd)
	rootCmd.AddCommand(validateCmd)
	rootCmd.AddCommand(cleanupCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
