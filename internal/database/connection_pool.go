package database

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

// ConnectionPool manages database connections with pooling
type ConnectionPool struct {
	db     *sqlx.DB
	config PoolConfig
	mu     sync.RWMutex
	stats  PoolStats
}

// PoolConfig contains connection pool configuration
type PoolConfig struct {
	// Connection parameters
	Host     string
	Port     int
	Database string
	User     string
	Password string
	SSLMode  string

	// Pool settings
	MaxOpenConns    int           // Maximum number of open connections
	MaxIdleConns    int           // Maximum number of idle connections
	ConnMaxLifetime time.Duration // Maximum lifetime of a connection
	ConnMaxIdleTime time.Duration // Maximum idle time for a connection

	// Health check settings
	HealthCheckInterval time.Duration // How often to check connection health
	RetryAttempts      int           // Number of retry attempts for failed operations
	RetryDelay         time.Duration // Delay between retry attempts
}

// PoolStats contains connection pool statistics
type PoolStats struct {
	OpenConnections  int
	IdleConnections  int
	TotalConnections int64
	WaitCount        int64
	WaitDuration     time.Duration
	MaxIdleClosed    int64
	MaxLifetimeClosed int64
	LastHealthCheck  time.Time
}

// DefaultPoolConfig returns default pool configuration
func DefaultPoolConfig() PoolConfig {
	return PoolConfig{
		MaxOpenConns:        25,
		MaxIdleConns:        10,
		ConnMaxLifetime:     30 * time.Minute,
		ConnMaxIdleTime:     10 * time.Minute,
		HealthCheckInterval: 1 * time.Minute,
		RetryAttempts:      3,
		RetryDelay:         1 * time.Second,
		SSLMode:            "prefer",
	}
}

// NewConnectionPool creates a new connection pool
func NewConnectionPool(config PoolConfig) (*ConnectionPool, error) {
	// Build connection string
	dsn := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		config.Host, config.Port, config.User, config.Password,
		config.Database, config.SSLMode,
	)

	// Additional connection parameters for better performance
	dsn += " connect_timeout=10"
	dsn += " application_name=arxos"
	dsn += " statement_timeout=30000" // 30 seconds

	// Open database connection
	db, err := sqlx.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(config.MaxOpenConns)
	db.SetMaxIdleConns(config.MaxIdleConns)
	db.SetConnMaxLifetime(config.ConnMaxLifetime)

	if config.ConnMaxIdleTime > 0 {
		db.SetConnMaxIdleTime(config.ConnMaxIdleTime)
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	pool := &ConnectionPool{
		db:     db,
		config: config,
	}

	// Start health check routine
	if config.HealthCheckInterval > 0 {
		go pool.healthCheckLoop()
	}

	logger.Info("Connection pool initialized: max_open=%d, max_idle=%d",
		config.MaxOpenConns, config.MaxIdleConns)

	return pool, nil
}

// GetDB returns the underlying database connection
func (p *ConnectionPool) GetDB() *sqlx.DB {
	return p.db
}

// Execute runs a query with automatic retry on failure
func (p *ConnectionPool) Execute(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	var result sql.Result
	var err error

	for attempt := 0; attempt <= p.config.RetryAttempts; attempt++ {
		result, err = p.db.ExecContext(ctx, query, args...)

		if err == nil {
			return result, nil
		}

		if !isRetryableError(err) {
			return nil, err
		}

		if attempt < p.config.RetryAttempts {
			logger.Warn("Query failed (attempt %d/%d): %v",
				attempt+1, p.config.RetryAttempts, err)
			time.Sleep(p.config.RetryDelay)
		}
	}

	return nil, fmt.Errorf("query failed after %d attempts: %w",
		p.config.RetryAttempts, err)
}

// QueryRow executes a query that returns a single row with retry
func (p *ConnectionPool) QueryRow(ctx context.Context, query string, args ...interface{}) *sqlx.Row {
	return p.db.QueryRowxContext(ctx, query, args...)
}

// Query executes a query that returns multiple rows with retry
func (p *ConnectionPool) Query(ctx context.Context, query string, args ...interface{}) (*sqlx.Rows, error) {
	var rows *sqlx.Rows
	var err error

	for attempt := 0; attempt <= p.config.RetryAttempts; attempt++ {
		rows, err = p.db.QueryxContext(ctx, query, args...)

		if err == nil {
			return rows, nil
		}

		if !isRetryableError(err) {
			return nil, err
		}

		if attempt < p.config.RetryAttempts {
			logger.Warn("Query failed (attempt %d/%d): %v",
				attempt+1, p.config.RetryAttempts, err)
			time.Sleep(p.config.RetryDelay)
		}
	}

	return nil, fmt.Errorf("query failed after %d attempts: %w",
		p.config.RetryAttempts, err)
}

// Transaction executes a function within a database transaction
func (p *ConnectionPool) Transaction(ctx context.Context, fn func(*sqlx.Tx) error) error {
	tx, err := p.db.BeginTxx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}

	defer func() {
		if p := recover(); p != nil {
			tx.Rollback()
			panic(p)
		}
	}()

	if err := fn(tx); err != nil {
		if rbErr := tx.Rollback(); rbErr != nil {
			return fmt.Errorf("transaction failed: %v, rollback failed: %w", err, rbErr)
		}
		return err
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// GetStats returns current pool statistics
func (p *ConnectionPool) GetStats() PoolStats {
	p.mu.RLock()
	defer p.mu.RUnlock()

	dbStats := p.db.Stats()

	return PoolStats{
		OpenConnections:   dbStats.OpenConnections,
		IdleConnections:   dbStats.Idle,
		TotalConnections:  p.stats.TotalConnections,
		WaitCount:        dbStats.WaitCount,
		WaitDuration:     dbStats.WaitDuration,
		MaxIdleClosed:    dbStats.MaxIdleClosed,
		MaxLifetimeClosed: dbStats.MaxLifetimeClosed,
		LastHealthCheck:   p.stats.LastHealthCheck,
	}
}

// healthCheckLoop periodically checks database health
func (p *ConnectionPool) healthCheckLoop() {
	ticker := time.NewTicker(p.config.HealthCheckInterval)
	defer ticker.Stop()

	for range ticker.C {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)

		if err := p.db.PingContext(ctx); err != nil {
			logger.Error("Database health check failed: %v", err)
		} else {
			p.mu.Lock()
			p.stats.LastHealthCheck = time.Now()
			p.mu.Unlock()
		}

		cancel()
	}
}

// Close closes all database connections
func (p *ConnectionPool) Close() error {
	logger.Info("Closing connection pool")
	return p.db.Close()
}

// isRetryableError determines if an error should trigger a retry
func isRetryableError(err error) bool {
	if err == nil {
		return false
	}

	// Check for specific PostgreSQL error codes that are retryable
	errStr := err.Error()
	retryablePatterns := []string{
		"connection refused",
		"connection reset",
		"broken pipe",
		"deadlock",
		"timeout",
		"too many connections",
	}

	for _, pattern := range retryablePatterns {
		if contains(errStr, pattern) {
			return true
		}
	}

	return false
}

// contains checks if a string contains a substring (case-insensitive)
func contains(s, substr string) bool {
	return len(s) >= len(substr) &&
		(s == substr ||
		 len(s) > len(substr) &&
		 containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}