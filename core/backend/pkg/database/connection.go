package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	_ "github.com/lib/pq"
	"arxos/config"
	"arxos/pkg/logger"
)

// DB wraps the SQL database with additional functionality
type DB struct {
	*sql.DB
	config *config.DatabaseConfig
	logger logger.Logger
}

// NewConnection creates a new database connection with proper pooling
func NewConnection(cfg *config.DatabaseConfig) (*DB, error) {
	log := logger.GetLogger().WithField("component", "database")
	
	// Build connection string
	connStr := buildConnectionString(cfg)
	
	// Open database connection
	sqlDB, err := sql.Open("postgres", connStr)
	if err != nil {
		log.WithError(err).Error("Failed to open database connection")
		return nil, fmt.Errorf("failed to open database: %w", err)
	}
	
	// Configure connection pool
	sqlDB.SetMaxOpenConns(cfg.MaxOpenConns)
	sqlDB.SetMaxIdleConns(cfg.MaxIdleConns)
	sqlDB.SetConnMaxLifetime(cfg.ConnMaxLifetime)
	sqlDB.SetConnMaxIdleTime(cfg.ConnMaxIdleTime)
	
	// Test the connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	if err := sqlDB.PingContext(ctx); err != nil {
		log.WithError(err).Error("Failed to ping database")
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}
	
	db := &DB{
		DB:     sqlDB,
		config: cfg,
		logger: log,
	}
	
	// Run migrations if needed
	if err := db.runMigrations(); err != nil {
		log.WithError(err).Warn("Failed to run migrations")
		// Don't fail - migrations might already be applied
	}
	
	// Start monitoring goroutine
	go db.monitorHealth()
	
	log.Info("Database connection established",
		logger.String("host", cfg.Host),
		logger.String("database", cfg.DBName),
		logger.Int("max_connections", cfg.MaxOpenConns),
	)
	
	return db, nil
}

// buildConnectionString creates the PostgreSQL connection string
func buildConnectionString(cfg *config.DatabaseConfig) string {
	if cfg.Password == "" {
		return fmt.Sprintf(
			"host=%s port=%d user=%s dbname=%s sslmode=%s",
			cfg.Host, cfg.Port, cfg.User, cfg.DBName, cfg.SSLMode,
		)
	}
	
	return fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		cfg.Host, cfg.Port, cfg.User, cfg.Password, cfg.DBName, cfg.SSLMode,
	)
}

// runMigrations applies database migrations
func (db *DB) runMigrations() error {
	// Check if migrations table exists
	var exists bool
	err := db.QueryRow(`
		SELECT EXISTS (
			SELECT FROM information_schema.tables 
			WHERE table_schema = 'public' 
			AND table_name = 'schema_migrations'
		)
	`).Scan(&exists)
	
	if err != nil {
		return err
	}
	
	if !exists {
		// Create migrations table
		_, err = db.Exec(`
			CREATE TABLE schema_migrations (
				version INTEGER PRIMARY KEY,
				applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
			)
		`)
		if err != nil {
			return err
		}
	}
	
	// Get latest applied version
	var latestVersion int
	err = db.QueryRow(`
		SELECT COALESCE(MAX(version), 0) FROM schema_migrations
	`).Scan(&latestVersion)
	
	if err != nil {
		return err
	}
	
	db.logger.Info("Database migration check",
		logger.Int("current_version", latestVersion),
	)
	
	// In production, would apply migrations from files here
	
	return nil
}

// monitorHealth periodically checks database health
func (db *DB) monitorHealth() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	
	for range ticker.C {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		
		// Check connection
		if err := db.PingContext(ctx); err != nil {
			db.logger.Error("Database health check failed", logger.Err(err))
		}
		
		// Check pool stats
		stats := db.Stats()
		
		// Log if we're running low on connections
		if stats.OpenConnections > db.config.MaxOpenConns*8/10 {
			db.logger.Warn("Database connection pool usage high",
				logger.Int("open_connections", stats.OpenConnections),
				logger.Int("max_connections", db.config.MaxOpenConns),
				logger.Int("in_use", stats.InUse),
				logger.Int("idle", stats.Idle),
			)
		}
		
		cancel()
	}
}

// Transaction starts a new database transaction with context
func (db *DB) Transaction(ctx context.Context, fn func(*sql.Tx) error) error {
	tx, err := db.BeginTx(ctx, nil)
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
			return fmt.Errorf("tx failed: %v, rb failed: %v", err, rbErr)
		}
		return err
	}
	
	return tx.Commit()
}

// QueryRowContext executes a query with logging
func (db *DB) QueryRowContext(ctx context.Context, query string, args ...interface{}) *sql.Row {
	start := time.Now()
	row := db.DB.QueryRowContext(ctx, query, args...)
	
	if db.config.EnableLogging {
		db.logger.Debug("Query executed",
			logger.String("query", truncateQuery(query)),
			logger.Duration("duration", time.Since(start)),
		)
	}
	
	return row
}

// QueryContext executes a query with logging
func (db *DB) QueryContext(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	start := time.Now()
	rows, err := db.DB.QueryContext(ctx, query, args...)
	
	if db.config.EnableLogging {
		db.logger.Debug("Query executed",
			logger.String("query", truncateQuery(query)),
			logger.Duration("duration", time.Since(start)),
			logger.Err(err),
		)
	}
	
	return rows, err
}

// ExecContext executes a statement with logging
func (db *DB) ExecContext(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	start := time.Now()
	result, err := db.DB.ExecContext(ctx, query, args...)
	
	if db.config.EnableLogging {
		var affected int64
		if result != nil && err == nil {
			affected, _ = result.RowsAffected()
		}
		
		db.logger.Debug("Statement executed",
			logger.String("query", truncateQuery(query)),
			logger.Duration("duration", time.Since(start)),
			logger.Int64("rows_affected", affected),
			logger.Err(err),
		)
	}
	
	return result, err
}

// Close closes the database connection
func (db *DB) Close() error {
	db.logger.Info("Closing database connection")
	return db.DB.Close()
}

// Helper functions

func truncateQuery(query string) string {
	const maxLen = 200
	if len(query) <= maxLen {
		return query
	}
	return query[:maxLen] + "..."
}

// ConnectionPool provides database connection pooling
type ConnectionPool struct {
	primary   *DB
	replicas  []*DB
	roundRobin int
}

// NewConnectionPool creates a connection pool with primary and replicas
func NewConnectionPool(primaryCfg *config.DatabaseConfig, replicaCfgs ...*config.DatabaseConfig) (*ConnectionPool, error) {
	primary, err := NewConnection(primaryCfg)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to primary: %w", err)
	}
	
	pool := &ConnectionPool{
		primary:  primary,
		replicas: make([]*DB, 0, len(replicaCfgs)),
	}
	
	// Connect to replicas
	for i, cfg := range replicaCfgs {
		replica, err := NewConnection(cfg)
		if err != nil {
			logger.GetLogger().WithError(err).Warn("Failed to connect to replica",
				logger.Int("replica_index", i),
			)
			continue
		}
		pool.replicas = append(pool.replicas, replica)
	}
	
	return pool, nil
}

// Primary returns the primary database connection
func (p *ConnectionPool) Primary() *DB {
	return p.primary
}

// Replica returns a replica connection using round-robin
func (p *ConnectionPool) Replica() *DB {
	if len(p.replicas) == 0 {
		return p.primary // Fallback to primary if no replicas
	}
	
	p.roundRobin = (p.roundRobin + 1) % len(p.replicas)
	return p.replicas[p.roundRobin]
}

// Close closes all connections in the pool
func (p *ConnectionPool) Close() error {
	if err := p.primary.Close(); err != nil {
		return err
	}
	
	for _, replica := range p.replicas {
		if err := replica.Close(); err != nil {
			logger.GetLogger().WithError(err).Error("Failed to close replica connection")
		}
	}
	
	return nil
}