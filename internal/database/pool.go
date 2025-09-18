package database

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ConnectionPool manages database connections
type ConnectionPool struct {
	db           *sql.DB
	config       PoolConfig
	mu           sync.RWMutex
	stats        PoolStats
	healthTicker *time.Ticker
	done         chan struct{}
}

// PoolConfig holds connection pool configuration
type PoolConfig struct {
	MaxOpenConns        int           // Maximum number of open connections
	MaxIdleConns        int           // Maximum number of idle connections
	ConnMaxLifetime     time.Duration // Maximum lifetime of a connection
	ConnMaxIdleTime     time.Duration // Maximum idle time of a connection
	HealthCheckInterval time.Duration // Interval for health checks
}

// PoolStats tracks pool statistics
type PoolStats struct {
	OpenConnections   int
	InUse             int
	Idle              int
	WaitCount         int64
	WaitDuration      time.Duration
	MaxIdleClosed     int64
	MaxLifetimeClosed int64
	TotalConnections  int64
	TotalRequests     int64
	TotalErrors       int64
}

// DefaultPoolConfig returns default pool configuration
func DefaultPoolConfig() PoolConfig {
	return PoolConfig{
		MaxOpenConns:        25,
		MaxIdleConns:        10,
		ConnMaxLifetime:     30 * time.Minute,
		ConnMaxIdleTime:     5 * time.Minute,
		HealthCheckInterval: 1 * time.Minute,
	}
}

// NewConnectionPool creates a new connection pool
func NewConnectionPool(db *sql.DB, config PoolConfig) *ConnectionPool {
	// Apply configuration to database
	db.SetMaxOpenConns(config.MaxOpenConns)
	db.SetMaxIdleConns(config.MaxIdleConns)
	db.SetConnMaxLifetime(config.ConnMaxLifetime)
	db.SetConnMaxIdleTime(config.ConnMaxIdleTime)

	pool := &ConnectionPool{
		db:     db,
		config: config,
		done:   make(chan struct{}),
	}

	// Start health check routine
	if config.HealthCheckInterval > 0 {
		pool.healthTicker = time.NewTicker(config.HealthCheckInterval)
		go pool.runHealthChecks()
	}

	return pool
}

// GetConnection gets a connection from the pool
func (p *ConnectionPool) GetConnection(ctx context.Context) (*sql.Conn, error) {
	p.mu.Lock()
	p.stats.TotalRequests++
	p.mu.Unlock()

	conn, err := p.db.Conn(ctx)
	if err != nil {
		p.mu.Lock()
		p.stats.TotalErrors++
		p.mu.Unlock()
		return nil, fmt.Errorf("failed to get connection: %w", err)
	}

	return conn, nil
}

// Execute executes a query with automatic connection management
func (p *ConnectionPool) Execute(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	p.mu.Lock()
	p.stats.TotalRequests++
	p.mu.Unlock()

	result, err := p.db.ExecContext(ctx, query, args...)
	if err != nil {
		p.mu.Lock()
		p.stats.TotalErrors++
		p.mu.Unlock()
		return nil, err
	}

	return result, nil
}

// Query executes a query and returns rows
func (p *ConnectionPool) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	p.mu.Lock()
	p.stats.TotalRequests++
	p.mu.Unlock()

	rows, err := p.db.QueryContext(ctx, query, args...)
	if err != nil {
		p.mu.Lock()
		p.stats.TotalErrors++
		p.mu.Unlock()
		return nil, err
	}

	return rows, nil
}

// QueryRow executes a query and returns a single row
func (p *ConnectionPool) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	p.mu.Lock()
	p.stats.TotalRequests++
	p.mu.Unlock()

	return p.db.QueryRowContext(ctx, query, args...)
}

// Transaction starts a new transaction
func (p *ConnectionPool) Transaction(ctx context.Context, fn func(*sql.Tx) error) error {
	p.mu.Lock()
	p.stats.TotalRequests++
	p.mu.Unlock()

	tx, err := p.db.BeginTx(ctx, nil)
	if err != nil {
		p.mu.Lock()
		p.stats.TotalErrors++
		p.mu.Unlock()
		return fmt.Errorf("failed to begin transaction: %w", err)
	}

	err = fn(tx)
	if err != nil {
		if rbErr := tx.Rollback(); rbErr != nil {
			logger.Error("Failed to rollback transaction: %v", rbErr)
		}
		p.mu.Lock()
		p.stats.TotalErrors++
		p.mu.Unlock()
		return err
	}

	if err := tx.Commit(); err != nil {
		p.mu.Lock()
		p.stats.TotalErrors++
		p.mu.Unlock()
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// GetStats returns current pool statistics
func (p *ConnectionPool) GetStats() PoolStats {
	p.mu.RLock()
	defer p.mu.RUnlock()

	// Get real-time stats from database
	dbStats := p.db.Stats()

	stats := p.stats
	stats.OpenConnections = dbStats.OpenConnections
	stats.InUse = dbStats.InUse
	stats.Idle = dbStats.Idle
	stats.WaitCount = dbStats.WaitCount
	stats.WaitDuration = dbStats.WaitDuration
	stats.MaxIdleClosed = dbStats.MaxIdleClosed
	stats.MaxLifetimeClosed = dbStats.MaxLifetimeClosed

	return stats
}

// runHealthChecks performs periodic health checks
func (p *ConnectionPool) runHealthChecks() {
	for {
		select {
		case <-p.healthTicker.C:
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			if err := p.db.PingContext(ctx); err != nil {
				logger.Error("Database health check failed: %v", err)
				p.mu.Lock()
				p.stats.TotalErrors++
				p.mu.Unlock()
			} else {
				logger.Debug("Database health check passed")
			}
			cancel()

		case <-p.done:
			return
		}
	}
}

// Close closes the connection pool
func (p *ConnectionPool) Close() error {
	close(p.done)
	if p.healthTicker != nil {
		p.healthTicker.Stop()
	}
	return p.db.Close()
}

// PreparedStatement represents a prepared statement with caching
type PreparedStatement struct {
	stmt  *sql.Stmt
	query string
	uses  int64
	mu    sync.Mutex
}

// StatementCache caches prepared statements
type StatementCache struct {
	statements map[string]*PreparedStatement
	maxSize    int
	mu         sync.RWMutex
}

// NewStatementCache creates a new statement cache
func NewStatementCache(maxSize int) *StatementCache {
	return &StatementCache{
		statements: make(map[string]*PreparedStatement),
		maxSize:    maxSize,
	}
}

// Prepare prepares a statement or returns a cached one
func (sc *StatementCache) Prepare(ctx context.Context, db *sql.DB, query string) (*sql.Stmt, error) {
	sc.mu.RLock()
	if ps, exists := sc.statements[query]; exists {
		ps.mu.Lock()
		ps.uses++
		ps.mu.Unlock()
		sc.mu.RUnlock()
		return ps.stmt, nil
	}
	sc.mu.RUnlock()

	// Prepare new statement
	stmt, err := db.PrepareContext(ctx, query)
	if err != nil {
		return nil, err
	}

	sc.mu.Lock()
	defer sc.mu.Unlock()

	// Check size limit
	if len(sc.statements) >= sc.maxSize {
		// Evict least used statement
		sc.evictLeastUsed()
	}

	sc.statements[query] = &PreparedStatement{
		stmt:  stmt,
		query: query,
		uses:  1,
	}

	return stmt, nil
}

// evictLeastUsed removes the least used statement
func (sc *StatementCache) evictLeastUsed() {
	var leastUsedKey string
	var leastUses int64 = -1

	for key, ps := range sc.statements {
		if leastUses == -1 || ps.uses < leastUses {
			leastUsedKey = key
			leastUses = ps.uses
		}
	}

	if leastUsedKey != "" {
		if ps, exists := sc.statements[leastUsedKey]; exists {
			ps.stmt.Close()
			delete(sc.statements, leastUsedKey)
		}
	}
}

// Clear closes all cached statements
func (sc *StatementCache) Clear() {
	sc.mu.Lock()
	defer sc.mu.Unlock()

	for _, ps := range sc.statements {
		ps.stmt.Close()
	}
	sc.statements = make(map[string]*PreparedStatement)
}

// ConnectionRetry implements retry logic for database operations
type ConnectionRetry struct {
	MaxRetries    int
	RetryDelay    time.Duration
	MaxRetryDelay time.Duration
	BackoffFactor float64
}

// DefaultRetryConfig returns default retry configuration
func DefaultRetryConfig() ConnectionRetry {
	return ConnectionRetry{
		MaxRetries:    3,
		RetryDelay:    100 * time.Millisecond,
		MaxRetryDelay: 5 * time.Second,
		BackoffFactor: 2.0,
	}
}

// ExecuteWithRetry executes an operation with retry logic
func (cr *ConnectionRetry) ExecuteWithRetry(ctx context.Context, operation func() error) error {
	var err error
	delay := cr.RetryDelay

	for attempt := 0; attempt <= cr.MaxRetries; attempt++ {
		if attempt > 0 {
			logger.Debug("Retrying database operation (attempt %d/%d)", attempt, cr.MaxRetries)
			select {
			case <-time.After(delay):
			case <-ctx.Done():
				return ctx.Err()
			}

			// Exponential backoff
			delay = time.Duration(float64(delay) * cr.BackoffFactor)
			if delay > cr.MaxRetryDelay {
				delay = cr.MaxRetryDelay
			}
		}

		err = operation()
		if err == nil {
			return nil
		}

		// Check if error is retryable
		if !isRetryableError(err) {
			return err
		}
	}

	return fmt.Errorf("operation failed after %d retries: %w", cr.MaxRetries, err)
}

// isRetryableError determines if an error is retryable
func isRetryableError(err error) bool {
	// Check for common retryable database errors
	errStr := err.Error()

	retryablePatterns := []string{
		"connection refused",
		"connection reset",
		"broken pipe",
		"database is locked",
		"too many connections",
		"timeout",
		"deadlock",
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
				(s[:len(substr)] == substr ||
					s[len(s)-len(substr):] == substr ||
					len(substr) < len(s) && findSubstring(s, substr)))
}

// findSubstring searches for a substring
func findSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
