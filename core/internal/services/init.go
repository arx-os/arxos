package services

import (
	"fmt"
	"log"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/services/cache"
)

var (
	// Global service instances
	globalCacheService      *cache.CacheService
	globalConfidenceCache   *cache.ConfidenceCache
	globalSessionService    *SessionService
	globalLoggingService    *LoggingService
	globalCleanupStopChan   chan bool
)

// ServiceConfig holds configuration for all services
type ServiceConfig struct {
	EnableCache      bool
	EnableSessions   bool
	EnableLogging    bool
	CacheCleanupInterval time.Duration
	Logger          *log.Logger
}

// DefaultServiceConfig returns default service configuration
func DefaultServiceConfig() *ServiceConfig {
	return &ServiceConfig{
		EnableCache:          true,
		EnableSessions:       true,
		EnableLogging:        true,
		CacheCleanupInterval: 1 * time.Hour,
		Logger:              log.Default(),
	}
}

// InitializeServices initializes all application services
func InitializeServices(config *ServiceConfig) error {
	if config == nil {
		config = DefaultServiceConfig()
	}

	// Initialize database first
	if err := db.InitDB(); err != nil {
		return fmt.Errorf("failed to initialize database: %w", err)
	}

	// Initialize cache service
	if config.EnableCache {
		cacheConfig := cache.DefaultCacheConfig()
		cacheService, err := cache.NewCacheService(cacheConfig, config.Logger)
		if err != nil {
			// Cache is optional, log error but continue
			config.Logger.Printf("WARNING: Failed to initialize cache service: %v", err)
			config.Logger.Println("Continuing without cache...")
		} else {
			globalCacheService = cacheService
			cache.SetCacheService(cacheService)
			config.Logger.Println("✅ Cache service initialized (PostgreSQL backend)")

			// Initialize confidence cache
			confidenceCache := cache.NewConfidenceCache(nil)
			globalConfidenceCache = confidenceCache
			config.Logger.Println("✅ Confidence cache initialized")
		}
	}

	// Initialize session service
	if config.EnableSessions {
		globalSessionService = NewSessionService()
		config.Logger.Println("✅ Session service initialized")
	}

	// Initialize logging service
	if config.EnableLogging {
		globalLoggingService = NewLoggingService(config.Logger)
		config.Logger.Println("✅ Logging service initialized")
	}

	// Start background cleanup worker
	if config.EnableCache && globalCacheService != nil {
		globalCleanupStopChan = make(chan bool)
		go startCleanupWorker(config.CacheCleanupInterval, config.Logger)
		config.Logger.Printf("✅ Cache cleanup worker started (interval: %v)", config.CacheCleanupInterval)
	}

	config.Logger.Println("✅ All services initialized successfully")
	return nil
}

// startCleanupWorker runs periodic cleanup of expired cache entries
func startCleanupWorker(interval time.Duration, logger *log.Logger) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if err := CleanupExpiredCache(); err != nil {
				if logger != nil {
					logger.Printf("ERROR: Cache cleanup failed: %v", err)
				}
			} else {
				if logger != nil {
					logger.Println("Cache cleanup completed successfully")
				}
			}
		case <-globalCleanupStopChan:
			if logger != nil {
				logger.Println("Cache cleanup worker stopped")
			}
			return
		}
	}
}

// CleanupExpiredCache removes expired entries from all cache tables
func CleanupExpiredCache() error {
	if db.GormDB == nil {
		return fmt.Errorf("database not initialized")
	}

	// Clean cache_entries table
	result := db.GormDB.Exec(`
		DELETE FROM cache_entries 
		WHERE expires_at < CURRENT_TIMESTAMP
	`)
	if result.Error != nil {
		return fmt.Errorf("failed to clean cache_entries: %w", result.Error)
	}
	deletedEntries := result.RowsAffected

	// Clean http_cache table
	result = db.GormDB.Exec(`
		DELETE FROM http_cache 
		WHERE expires_at < CURRENT_TIMESTAMP
	`)
	if result.Error != nil {
		return fmt.Errorf("failed to clean http_cache: %w", result.Error)
	}
	deletedHTTP := result.RowsAffected

	// Clean confidence_cache table
	result = db.GormDB.Exec(`
		DELETE FROM confidence_cache 
		WHERE expires_at < CURRENT_TIMESTAMP
	`)
	if result.Error != nil {
		return fmt.Errorf("failed to clean confidence_cache: %w", result.Error)
	}
	deletedConfidence := result.RowsAffected

	// Log statistics
	if deletedEntries > 0 || deletedHTTP > 0 || deletedConfidence > 0 {
		db.GormDB.Exec(`
			INSERT INTO cache_statistics (cache_type, period_start, period_end, evictions)
			VALUES ('cleanup', CURRENT_TIMESTAMP - INTERVAL '1 hour', CURRENT_TIMESTAMP, $1)
		`, deletedEntries+deletedHTTP+deletedConfidence)
	}

	return nil
}

// ShutdownServices gracefully shuts down all services
func ShutdownServices() error {
	var errors []error

	// Stop cleanup worker
	if globalCleanupStopChan != nil {
		close(globalCleanupStopChan)
	}

	// Close cache service
	if globalCacheService != nil {
		if err := globalCacheService.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close cache service: %w", err))
		}
	}

	// Close database connections
	if err := db.Close(); err != nil {
		errors = append(errors, fmt.Errorf("failed to close database: %w", err))
	}

	if len(errors) > 0 {
		return fmt.Errorf("shutdown errors: %v", errors)
	}

	return nil
}

// GetCacheService returns the global cache service instance
func GetCacheService() *cache.CacheService {
	return globalCacheService
}

// GetConfidenceCache returns the global confidence cache instance
func GetConfidenceCache() *cache.ConfidenceCache {
	return globalConfidenceCache
}

// GetSessionService returns the global session service instance
func GetSessionService() *SessionService {
	return globalSessionService
}

// GetLoggingService returns the global logging service instance
func GetLoggingService() *LoggingService {
	return globalLoggingService
}

// ServiceHealth represents the health status of a service
type ServiceHealth struct {
	Name    string                 `json:"name"`
	Status  string                 `json:"status"`
	Details map[string]interface{} `json:"details,omitempty"`
}

// GetServicesHealth returns health status of all services
func GetServicesHealth() []ServiceHealth {
	health := []ServiceHealth{}

	// Database health
	dbHealth := ServiceHealth{
		Name:   "database",
		Status: "healthy",
	}
	if db.GormDB == nil {
		dbHealth.Status = "unavailable"
	} else {
		sqlDB, err := db.GormDB.DB()
		if err != nil || sqlDB.Ping() != nil {
			dbHealth.Status = "unhealthy"
		} else {
			stats := sqlDB.Stats()
			dbHealth.Details = map[string]interface{}{
				"open_connections": stats.OpenConnections,
				"in_use":          stats.InUse,
				"idle":            stats.Idle,
			}
		}
	}
	health = append(health, dbHealth)

	// Cache health
	cacheHealth := ServiceHealth{
		Name:   "cache",
		Status: "healthy",
	}
	if globalCacheService == nil {
		cacheHealth.Status = "disabled"
	} else if err := globalCacheService.HealthCheck(); err != nil {
		cacheHealth.Status = "unhealthy"
		cacheHealth.Details = map[string]interface{}{
			"error": err.Error(),
		}
	} else {
		if stats, err := globalCacheService.GetStats(); err == nil {
			cacheHealth.Details = map[string]interface{}{
				"total_keys": stats.TotalKeys,
				"hit_rate":   stats.HitRate,
			}
		}
	}
	health = append(health, cacheHealth)

	// Session health
	sessionHealth := ServiceHealth{
		Name:   "sessions",
		Status: "healthy",
	}
	if globalSessionService == nil {
		sessionHealth.Status = "disabled"
	}
	health = append(health, sessionHealth)

	return health
}