// db/db.go
package db

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"

	"arx/models"

	"github.com/spf13/viper"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var (
	DB *gorm.DB
	
	// Connection pool statistics
	poolStats struct {
		sync.RWMutex
		MaxOpenConnections     int           `json:"max_open_connections"`
		OpenConnections        int           `json:"open_connections"`
		InUseConnections       int           `json:"in_use_connections"`
		IdleConnections        int           `json:"idle_connections"`
		WaitCount              int64         `json:"wait_count"`
		WaitDuration           time.Duration `json:"wait_duration"`
		MaxIdleClosed          int64         `json:"max_idle_closed"`
		MaxLifetimeClosed      int64         `json:"max_lifetime_closed"`
		LastStatsUpdate        time.Time     `json:"last_stats_update"`
	}
	
	// Configuration
	config struct {
		MaxOpenConns        int           `json:"max_open_conns"`
		MaxIdleConns        int           `json:"max_idle_conns"`
		ConnMaxLifetime     time.Duration `json:"conn_max_lifetime"`
		ConnMaxIdleTime     time.Duration `json:"conn_max_idle_time"`
		PrepareStmt         bool          `json:"prepare_stmt"`
		SlowThreshold       time.Duration `json:"slow_threshold"`
		LogLevel            logger.LogLevel `json:"log_level"`
		EnableMetrics       bool          `json:"enable_metrics"`
	}
)

// Connect initializes the database connection with optimized pooling settings.
func Connect() {
	// Load environment variables
	viper.AutomaticEnv()
	
	// Get database configuration
	dsn := viper.GetString("DATABASE_URL")
	if dsn == "" {
		log.Fatal("DATABASE_URL is not set")
	}

	// Load connection pool configuration from environment
	loadConnectionConfig()

	// Configure GORM logger with optimized settings
	newLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags),
		logger.Config{
			SlowThreshold:             config.SlowThreshold,
			LogLevel:                  config.LogLevel,
			IgnoreRecordNotFoundError: true,
			Colorful:                  true,
			ParameterizedQueries:      true, // Enable parameterized queries for security
		},
	)

	// Open database connection with optimized configuration
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger:                                   newLogger,
		PrepareStmt:                              config.PrepareStmt,
		DisableForeignKeyConstraintWhenMigrating: true,
		SkipDefaultTransaction:                   true, // Disable default transaction for better performance
		DryRun:                                   false,
	})
	if err != nil {
		log.Fatalf("Failed to connect to DB: %v", err)
	}

	// Get underlying SQL database for connection pooling configuration
	sqlDB, err := db.DB()
	if err != nil {
		log.Fatalf("Failed to get SQL DB instance: %v", err)
	}

	// Configure optimized connection pooling
	sqlDB.SetMaxOpenConns(config.MaxOpenConns)
	sqlDB.SetMaxIdleConns(config.MaxIdleConns)
	sqlDB.SetConnMaxLifetime(config.ConnMaxLifetime)
	sqlDB.SetConnMaxIdleTime(config.ConnMaxIdleTime)

	// Store database instance
	DB = db
	models.DB = DB

	// Initialize pool statistics
	updatePoolStats(sqlDB)

	// Start connection pool monitoring if enabled
	if config.EnableMetrics {
		go monitorConnectionPool(sqlDB)
	}

	log.Printf("✅ Database connected successfully with optimized pooling")
	log.Printf("📊 Connection Pool Config: MaxOpen=%d, MaxIdle=%d, MaxLifetime=%v, MaxIdleTime=%v",
		config.MaxOpenConns, config.MaxIdleConns, config.ConnMaxLifetime, config.ConnMaxIdleTime)
}

// loadConnectionConfig loads connection pool configuration from environment variables
func loadConnectionConfig() {
	// Default configuration
	config.MaxOpenConns = 100
	config.MaxIdleConns = 25
	config.ConnMaxLifetime = 1 * time.Hour
	config.ConnMaxIdleTime = 30 * time.Minute
	config.PrepareStmt = true
	config.SlowThreshold = 1 * time.Second
	config.LogLevel = logger.Info
	config.EnableMetrics = true

	// Override with environment variables
	if maxOpen := viper.GetString("DB_MAX_OPEN_CONNS"); maxOpen != "" {
		if val, err := strconv.Atoi(maxOpen); err == nil && val > 0 {
			config.MaxOpenConns = val
		}
	}

	if maxIdle := viper.GetString("DB_MAX_IDLE_CONNS"); maxIdle != "" {
		if val, err := strconv.Atoi(maxIdle); err == nil && val > 0 {
			config.MaxIdleConns = val
		}
	}

	if maxLifetime := viper.GetString("DB_CONN_MAX_LIFETIME"); maxLifetime != "" {
		if val, err := time.ParseDuration(maxLifetime); err == nil && val > 0 {
			config.ConnMaxLifetime = val
		}
	}

	if maxIdleTime := viper.GetString("DB_CONN_MAX_IDLE_TIME"); maxIdleTime != "" {
		if val, err := time.ParseDuration(maxIdleTime); err == nil && val > 0 {
			config.ConnMaxIdleTime = val
		}
	}

	if prepareStmt := viper.GetString("DB_PREPARE_STMT"); prepareStmt != "" {
		config.PrepareStmt = prepareStmt == "true"
	}

	if slowThreshold := viper.GetString("DB_SLOW_THRESHOLD"); slowThreshold != "" {
		if val, err := time.ParseDuration(slowThreshold); err == nil && val > 0 {
			config.SlowThreshold = val
		}
	}

	if logLevel := viper.GetString("DB_LOG_LEVEL"); logLevel != "" {
		switch logLevel {
		case "silent":
			config.LogLevel = logger.Silent
		case "error":
			config.LogLevel = logger.Error
		case "warn":
			config.LogLevel = logger.Warn
		case "info":
			config.LogLevel = logger.Info
		}
	}

	if enableMetrics := viper.GetString("DB_ENABLE_METRICS"); enableMetrics != "" {
		config.EnableMetrics = enableMetrics == "true"
	}

	// Validate configuration
	if config.MaxIdleConns > config.MaxOpenConns {
		config.MaxIdleConns = config.MaxOpenConns
		log.Println("⚠️  MaxIdleConns adjusted to MaxOpenConns")
	}
}

// updatePoolStats updates connection pool statistics
func updatePoolStats(sqlDB *sql.DB) {
	poolStats.Lock()
	defer poolStats.Unlock()

	poolStats.MaxOpenConnections = sqlDB.Stats().MaxOpenConnections
	poolStats.OpenConnections = sqlDB.Stats().OpenConnections
	poolStats.InUseConnections = sqlDB.Stats().InUse
	poolStats.IdleConnections = sqlDB.Stats().Idle
	poolStats.WaitCount = sqlDB.Stats().WaitCount
	poolStats.WaitDuration = sqlDB.Stats().WaitDuration
	poolStats.MaxIdleClosed = sqlDB.Stats().MaxIdleClosed
	poolStats.MaxLifetimeClosed = sqlDB.Stats().MaxLifetimeClosed
	poolStats.LastStatsUpdate = time.Now()
}

// monitorConnectionPool continuously monitors connection pool statistics
func monitorConnectionPool(sqlDB *sql.DB) {
	ticker := time.NewTicker(30 * time.Second) // Update every 30 seconds
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			updatePoolStats(sqlDB)
			
			// Log warnings for high connection usage
			stats := sqlDB.Stats()
			usagePercent := float64(stats.InUse) / float64(stats.MaxOpenConnections) * 100
			
			if usagePercent > 80 {
				log.Printf("⚠️  High connection pool usage: %.1f%% (%d/%d connections in use)",
					usagePercent, stats.InUse, stats.MaxOpenConnections)
			}
			
			if stats.WaitCount > 0 {
				log.Printf("⚠️  Connection pool wait detected: %d waits, total duration: %v",
					stats.WaitCount, stats.WaitDuration)
			}
		}
	}
}

// GetPoolStats returns current connection pool statistics
func GetPoolStats() map[string]interface{} {
	poolStats.RLock()
	defer poolStats.RUnlock()

	return map[string]interface{}{
		"max_open_connections": poolStats.MaxOpenConnections,
		"open_connections":     poolStats.OpenConnections,
		"in_use_connections":   poolStats.InUseConnections,
		"idle_connections":     poolStats.IdleConnections,
		"wait_count":           poolStats.WaitCount,
		"wait_duration":        poolStats.WaitDuration.String(),
		"max_idle_closed":      poolStats.MaxIdleClosed,
		"max_lifetime_closed":  poolStats.MaxLifetimeClosed,
		"last_update":          poolStats.LastStatsUpdate,
		"usage_percentage":     float64(poolStats.InUseConnections) / float64(poolStats.MaxOpenConnections) * 100,
		"configuration":        config,
	}
}

// HealthCheck performs a database health check
func HealthCheck() error {
	if DB == nil {
		return fmt.Errorf("database connection is not initialized")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	sqlDB, err := DB.DB()
	if err != nil {
		return fmt.Errorf("failed to get SQL DB instance: %v", err)
	}

	// Ping the database
	if err := sqlDB.PingContext(ctx); err != nil {
		return fmt.Errorf("database ping failed: %v", err)
	}

	// Check connection pool health
	stats := sqlDB.Stats()
	if stats.OpenConnections >= stats.MaxOpenConnections {
		return fmt.Errorf("connection pool is at maximum capacity")
	}

	return nil
}

// Migrate runs database migrations with optimized settings.
func Migrate() {
	if DB == nil {
		log.Fatal("Database connection is not initialized")
	}

	// Disable foreign key constraints during migration for better performance
	err := DB.Session(&gorm.Session{
		DisableForeignKeyConstraintWhenMigrating: true,
	}).AutoMigrate(
		&models.User{},
		&models.Project{},
		&models.Drawing{},
		&models.Building{},
		&models.Floor{},
		&models.Markup{},
		&models.Log{},
		&models.SymbolLibraryCache{},
		&models.BuildingAsset{},
		&models.AssetHistory{},
		&models.AssetMaintenance{},
		&models.AssetValuation{},
		&models.DrawingVersion{},
		&models.AuditLog{},
		&models.ExportActivity{},
		&models.DataVendorAPIKey{},
		&models.DataVendorRequest{},
		&models.DataVendorUsage{},
		&models.ExportAnalytics{},
		&models.DataRetentionPolicy{},
		&models.ArchivedAuditLog{},
		&models.ComplianceReport{},
		&models.DataAccessLog{},
		&models.SecurityAlert{},
		&models.APIKeyUsage{},
	)
	if err != nil {
		log.Fatalf("Failed to run migrations: %v", err)
	}

	log.Println("✅ Database migrations completed successfully")
}

// Close gracefully shuts down the database connection.
func Close() {
	if DB == nil {
		return
	}

	sqlDB, err := DB.DB()
	if err != nil {
		log.Printf("Failed to get SQL DB instance for closing: %v", err)
		return
	}

	// Log final statistics before closing
	stats := sqlDB.Stats()
	log.Printf("📊 Final Connection Pool Stats: Open=%d, InUse=%d, Idle=%d, WaitCount=%d",
		stats.OpenConnections, stats.InUse, stats.Idle, stats.WaitCount)

	err = sqlDB.Close()
	if err != nil {
		log.Printf("Failed to close database connection: %v", err)
	} else {
		log.Println("✅ Database connection closed successfully")
	}
}

// ListMarkups retrieves markups with optimized querying
func ListMarkups(w http.ResponseWriter, r *http.Request) {
	floorID := r.URL.Query().Get("floor_id")
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}
	offset := (page - 1) * pageSize

	var total int64
	query := DB.Model(&models.Markup{})
	if floorID != "" {
		query = query.Where("floor_id = ?", floorID)
	}
	query.Count(&total)

	var markups []models.Markup
	query.Offset(offset).Limit(pageSize).Find(&markups)

	resp := map[string]interface{}{
		"results":     markups,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

// GetConnectionPoolStatsHandler returns connection pool statistics via HTTP
func GetConnectionPoolStatsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(GetPoolStats())
}

// HealthCheckHandler returns database health status via HTTP
func HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
	err := HealthCheck()
	if err != nil {
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":  "unhealthy",
			"error":   err.Error(),
			"pool_stats": GetPoolStats(),
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":     "healthy",
		"timestamp":  time.Now(),
		"pool_stats": GetPoolStats(),
	})
}
