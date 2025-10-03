package database

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq" // PostgreSQL driver
	"github.com/arx-os/arxos/internal/config"
)

// ConnectionPool manages database connections with advanced pooling
type ConnectionPool struct {
	config     *config.Config
	primary    *sqlx.DB
	readOnly   *sqlx.DB
	mu         sync.RWMutex
	stats      *PoolStats
	healthCheck *HealthChecker
}

// PoolStats tracks connection pool statistics
type PoolStats struct {
	MaxOpenConns     int           `json:"max_open_conns"`
	OpenConns        int           `json:"open_conns"`
	InUse            int           `json:"in_use"`
	Idle             int           `json:"idle"`
	WaitCount        int64         `json:"wait_count"`
	WaitDuration     time.Duration `json:"wait_duration"`
	MaxIdleClosed    int64         `json:"max_idle_closed"`
	MaxIdleTimeClosed int64        `json:"max_idle_time_closed"`
	MaxLifetimeClosed int64        `json:"max_lifetime_closed"`
	LastChecked      time.Time     `json:"last_checked"`
}

// HealthChecker performs database health checks
type HealthChecker struct {
	lastCheck    time.Time
	checkInterval time.Duration
	isHealthy    bool
	mu           sync.RWMutex
}

// NewConnectionPool creates a new connection pool with read/write separation
func NewConnectionPool(cfg *config.Config) (*ConnectionPool, error) {
	pool := &ConnectionPool{
		config: cfg,
		stats:  &PoolStats{},
		healthCheck: &HealthChecker{
			checkInterval: 30 * time.Second,
			isHealthy:     false,
		},
	}

	// Initialize primary (write) connection
	if err := pool.initPrimaryConnection(); err != nil {
		return nil, fmt.Errorf("failed to initialize primary connection: %w", err)
	}

	// Initialize read-only connection if configured
	// Note: ReadOnlyDSN would need to be added to DatabaseConfig
	// For now, we'll skip read-only connection initialization

	// Start health check routine
	go pool.startHealthCheck()

	return pool, nil
}

// initPrimaryConnection initializes the primary database connection
func (cp *ConnectionPool) initPrimaryConnection() error {
	dsn := cp.config.BuildPostGISConnectionString()
	
	conn, err := sqlx.ConnectContext(context.Background(), "postgres", dsn)
	if err != nil {
		return fmt.Errorf("failed to connect to primary database: %w", err)
	}

	// Configure connection pool for primary
	cp.configureConnectionPool(conn, cp.config.Database.MaxOpenConns, cp.config.Database.MaxIdleConns)
	
	cp.primary = conn
	return nil
}

// initReadOnlyConnection initializes the read-only database connection
func (cp *ConnectionPool) initReadOnlyConnection() error {
	// Note: This would require ReadOnlyDSN to be added to DatabaseConfig
	// For now, return nil to skip read-only connection
	return nil
}

// configureConnectionPool configures connection pool settings
func (cp *ConnectionPool) configureConnectionPool(conn *sqlx.DB, maxOpen, maxIdle int) {
	conn.SetMaxOpenConns(maxOpen)
	conn.SetMaxIdleConns(maxIdle)
	conn.SetConnMaxLifetime(cp.config.Database.ConnMaxLifetime)
	
	// Set connection timeout
	conn.SetConnMaxIdleTime(5 * time.Minute)
}

// GetPrimaryConnection returns the primary database connection
func (cp *ConnectionPool) GetPrimaryConnection() *sqlx.DB {
	cp.mu.RLock()
	defer cp.mu.RUnlock()
	return cp.primary
}

// GetReadOnlyConnection returns the read-only database connection
func (cp *ConnectionPool) GetReadOnlyConnection() *sqlx.DB {
	cp.mu.RLock()
	defer cp.mu.RUnlock()
	if cp.readOnly != nil {
		return cp.readOnly
	}
	return cp.primary // Fallback to primary if read-only not available
}

// GetConnectionForRead returns appropriate connection for read operations
func (cp *ConnectionPool) GetConnectionForRead() *sqlx.DB {
	return cp.GetReadOnlyConnection()
}

// GetConnectionForWrite returns appropriate connection for write operations
func (cp *ConnectionPool) GetConnectionForWrite() *sqlx.DB {
	return cp.GetPrimaryConnection()
}

// GetStats returns current connection pool statistics
func (cp *ConnectionPool) GetStats() *PoolStats {
	cp.mu.Lock()
	defer cp.mu.Unlock()

	// Update stats from primary connection
	if cp.primary != nil {
		stats := cp.primary.Stats()
		cp.stats.MaxOpenConns = stats.MaxOpenConnections
		cp.stats.OpenConns = stats.OpenConnections
		cp.stats.InUse = stats.InUse
		cp.stats.Idle = stats.Idle
		cp.stats.WaitCount = stats.WaitCount
		cp.stats.WaitDuration = stats.WaitDuration
		cp.stats.MaxIdleClosed = stats.MaxIdleClosed
		cp.stats.MaxIdleTimeClosed = stats.MaxIdleTimeClosed
		cp.stats.MaxLifetimeClosed = stats.MaxLifetimeClosed
		cp.stats.LastChecked = time.Now()
	}

	return cp.stats
}

// IsHealthy returns the current health status
func (cp *ConnectionPool) IsHealthy() bool {
	cp.healthCheck.mu.RLock()
	defer cp.healthCheck.mu.RUnlock()
	return cp.healthCheck.isHealthy
}

// startHealthCheck starts the health check routine
func (cp *ConnectionPool) startHealthCheck() {
	ticker := time.NewTicker(cp.healthCheck.checkInterval)
	defer ticker.Stop()

	for range ticker.C {
		cp.performHealthCheck()
	}
}

// performHealthCheck performs a health check on all connections
func (cp *ConnectionPool) performHealthCheck() {
	cp.healthCheck.mu.Lock()
	defer cp.healthCheck.mu.Unlock()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Check primary connection
	if cp.primary != nil {
		if err := cp.primary.PingContext(ctx); err != nil {
			cp.healthCheck.isHealthy = false
			cp.healthCheck.lastCheck = time.Now()
			return
		}
	}

	// Check read-only connection if available
	if cp.readOnly != nil {
		if err := cp.readOnly.PingContext(ctx); err != nil {
			cp.healthCheck.isHealthy = false
			cp.healthCheck.lastCheck = time.Now()
			return
		}
	}

	cp.healthCheck.isHealthy = true
	cp.healthCheck.lastCheck = time.Now()
}

// Close closes all database connections
func (cp *ConnectionPool) Close() error {
	cp.mu.Lock()
	defer cp.mu.Unlock()

	var errs []error

	if cp.primary != nil {
		if err := cp.primary.Close(); err != nil {
			errs = append(errs, fmt.Errorf("failed to close primary connection: %w", err))
		}
	}

	if cp.readOnly != nil {
		if err := cp.readOnly.Close(); err != nil {
			errs = append(errs, fmt.Errorf("failed to close read-only connection: %w", err))
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("errors closing connections: %v", errs)
	}

	return nil
}

// RefreshConnections refreshes database connections
func (cp *ConnectionPool) RefreshConnections() error {
	cp.mu.Lock()
	defer cp.mu.Unlock()

	// Close existing connections
	if cp.primary != nil {
		cp.primary.Close()
	}
	if cp.readOnly != nil {
		cp.readOnly.Close()
	}

	// Reinitialize connections
	if err := cp.initPrimaryConnection(); err != nil {
		return fmt.Errorf("failed to refresh primary connection: %w", err)
	}

	// Note: ReadOnlyDSN would need to be added to DatabaseConfig
	// For now, skip read-only connection refresh

	return nil
}

// GetConnectionInfo returns detailed connection information
func (cp *ConnectionPool) GetConnectionInfo() map[string]interface{} {
	cp.mu.RLock()
	defer cp.mu.RUnlock()

	info := map[string]interface{}{
		"primary_available": cp.primary != nil,
		"readonly_available": cp.readOnly != nil,
		"health_status": cp.healthCheck.isHealthy,
		"last_health_check": cp.healthCheck.lastCheck,
		"stats": cp.stats,
	}

	if cp.primary != nil {
		info["primary_stats"] = cp.primary.Stats()
	}

	if cp.readOnly != nil {
		info["readonly_stats"] = cp.readOnly.Stats()
	}

	return info
}
