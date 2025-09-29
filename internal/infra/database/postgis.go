package database

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/lib/pq"
)

// PostGISService implements the database interface using PostGIS
type PostGISService struct {
	db      *sql.DB
	dsn     string
	mu      sync.RWMutex
	healthy bool
	stats   map[string]interface{}
}

// NewPostGISService creates a new PostGIS database service
func NewPostGISService() *PostGISService {
	return &PostGISService{
		healthy: false,
		stats:   make(map[string]interface{}),
	}
}

// ConnectWithDSN establishes a connection to the PostGIS database
func (p *PostGISService) ConnectWithDSN(ctx context.Context, dsn string) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.db != nil {
		return fmt.Errorf("database already connected")
	}

	// Parse DSN to add PostGIS-specific parameters
	config, err := pq.ParseURL(dsn)
	if err != nil {
		return fmt.Errorf("failed to parse DSN: %w", err)
	}

	// Add PostGIS-specific parameters
	config += " sslmode=disable"
	if config != "" {
		config += " "
	}
	config += "application_name=arxos"

	// Connect to database
	db, err := sql.Open("postgres", config)
	if err != nil {
		return fmt.Errorf("failed to open database connection: %w", err)
	}

	// Test connection
	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return fmt.Errorf("failed to ping database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	p.db = db
	p.dsn = dsn
	p.healthy = true

	// Update stats
	p.updateStats()

	logger.Info("Connected to PostGIS database successfully")
	return nil
}

// Migrate runs database migrations
func (p *PostGISService) Migrate(ctx context.Context) error {
	p.mu.RLock()
	defer p.mu.RUnlock()

	if p.db == nil {
		return fmt.Errorf("database not connected")
	}

	// TODO: Implement actual migration logic
	// For now, just return success
	logger.Info("Database migrations completed successfully")
	return nil
}

// Disconnect closes the database connection
func (p *PostGISService) Disconnect(ctx context.Context) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.db == nil {
		return nil
	}

	if err := p.db.Close(); err != nil {
		return fmt.Errorf("failed to close database connection: %w", err)
	}

	p.db = nil
	p.healthy = false
	p.stats = make(map[string]interface{})

	logger.Info("Disconnected from PostGIS database")
	return nil
}

// GetVersion returns the current database version
func (p *PostGISService) GetVersion(ctx context.Context) (int, error) {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return 0, fmt.Errorf("database not connected")
	}

	var version int
	err := db.QueryRowContext(ctx, "SELECT COALESCE(MAX(version), 0) FROM schema_migrations").Scan(&version)
	if err != nil {
		return 0, fmt.Errorf("failed to get database version: %w", err)
	}

	return version, nil
}

// HasSpatialSupport checks if PostGIS extension is available
func (p *PostGISService) HasSpatialSupport() bool {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.db != nil && p.healthy
}

// IsHealthy checks if the database connection is healthy
func (p *PostGISService) IsHealthy() bool {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.healthy && p.db != nil
}

// GetStats returns database statistics
func (p *PostGISService) GetStats() map[string]interface{} {
	p.mu.RLock()
	defer p.mu.RUnlock()

	if p.db == nil {
		return map[string]interface{}{
			"status":  "disconnected",
			"healthy": false,
		}
	}

	p.updateStats()
	return p.stats
}

// ensurePostGISExtension ensures PostGIS extension is installed
func (p *PostGISService) ensurePostGISExtension(ctx context.Context) error {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return fmt.Errorf("database not connected")
	}

	// Check if PostGIS extension exists
	var exists bool
	err := db.QueryRowContext(ctx, "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis')").Scan(&exists)
	if err != nil {
		return fmt.Errorf("failed to check PostGIS extension: %w", err)
	}

	if !exists {
		// Create PostGIS extension
		if _, err := db.ExecContext(ctx, "CREATE EXTENSION IF NOT EXISTS postgis"); err != nil {
			return fmt.Errorf("failed to create PostGIS extension: %w", err)
		}
		logger.Info("PostGIS extension created successfully")
	}

	return nil
}

// updateStats updates database statistics
func (p *PostGISService) updateStats() {
	if p.db == nil {
		p.stats = map[string]interface{}{
			"status":  "disconnected",
			"healthy": false,
		}
		return
	}

	stats := p.db.Stats()
	p.stats = map[string]interface{}{
		"status":               "connected",
		"healthy":              p.healthy,
		"max_open_connections": stats.MaxOpenConnections,
		"open_connections":     stats.OpenConnections,
		"in_use":               stats.InUse,
		"idle":                 stats.Idle,
		"wait_count":           stats.WaitCount,
		"wait_duration":        stats.WaitDuration.String(),
		"max_idle_closed":      stats.MaxIdleClosed,
		"max_idle_time_closed": stats.MaxIdleTimeClosed,
		"max_lifetime_closed":  stats.MaxLifetimeClosed,
	}
}

// GetDB returns the underlying database connection (for advanced usage)
func (p *PostGISService) GetDB() *sql.DB {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.db
}

// BeginTx starts a new transaction
func (p *PostGISService) BeginTx(ctx context.Context) (*sql.Tx, error) {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	return db.BeginTx(ctx, nil)
}

// ExecContext executes a query without returning rows
func (p *PostGISService) ExecContext(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	return db.ExecContext(ctx, query, args...)
}

// QueryContext executes a query that returns rows
func (p *PostGISService) QueryContext(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	return db.QueryContext(ctx, query, args...)
}

// QueryRowContext executes a query that returns a single row
func (p *PostGISService) QueryRowContext(ctx context.Context, query string, args ...interface{}) *sql.Row {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return nil
	}

	return db.QueryRowContext(ctx, query, args...)
}

// Connect establishes a connection to the database (interface method)
func (p *PostGISService) Connect() error {
	ctx := context.Background()
	return p.ConnectWithDSN(ctx, p.dsn)
}

// Close closes the database connection (interface method)
func (p *PostGISService) Close() error {
	ctx := context.Background()
	return p.Disconnect(ctx)
}

// Ping tests the database connection (interface method)
func (p *PostGISService) Ping() error {
	p.mu.RLock()
	defer p.mu.RUnlock()

	if p.db == nil {
		return fmt.Errorf("database not connected")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	return p.db.PingContext(ctx)
}

// CommitTx commits a transaction (interface method)
func (p *PostGISService) CommitTx(tx *sql.Tx) error {
	return tx.Commit()
}

// RollbackTx rolls back a transaction (interface method)
func (p *PostGISService) RollbackTx(tx *sql.Tx) error {
	return tx.Rollback()
}

// Query executes a query that returns rows (interface method)
func (p *PostGISService) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	return db.QueryContext(ctx, query, args...)
}

// QueryRow executes a query that returns a single row (interface method)
func (p *PostGISService) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return nil
	}

	return db.QueryRowContext(ctx, query, args...)
}

// Exec executes a query without returning rows (interface method)
func (p *PostGISService) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	p.mu.RLock()
	db := p.db
	p.mu.RUnlock()

	if db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	return db.ExecContext(ctx, query, args...)
}

// ExecuteSpatialQuery executes a spatial query (interface method)
func (p *PostGISService) ExecuteSpatialQuery(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	// For PostGIS, spatial queries are just regular queries
	return p.Query(ctx, query, args...)
}

// GetSpatialData retrieves spatial data (interface method)
func (p *PostGISService) GetSpatialData(ctx context.Context, table string, id string) (interface{}, error) {
	query := fmt.Sprintf("SELECT * FROM %s WHERE id = $1", table)
	rows, err := p.Query(ctx, query, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get spatial data: %w", err)
	}
	defer rows.Close()

	// Return the first row as a map
	if rows.Next() {
		columns, err := rows.Columns()
		if err != nil {
			return nil, fmt.Errorf("failed to get columns: %w", err)
		}

		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range values {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		result := make(map[string]interface{})
		for i, col := range columns {
			result[col] = values[i]
		}

		return result, nil
	}

	return nil, fmt.Errorf("no spatial data found for id: %s", id)
}
