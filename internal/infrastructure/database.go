package infrastructure

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq" // PostgreSQL driver
)

// Database implements the database interface following Clean Architecture
type Database struct {
	config *config.Config
	conn   *sqlx.DB
}

// NewDatabase creates a new database instance
func NewDatabase(cfg *config.Config) (domain.Database, error) {
	db := &Database{
		config: cfg,
	}

	// Initialize database connection
	if err := db.Connect(context.Background()); err != nil {
		return nil, fmt.Errorf("failed to initialize database: %w", err)
	}

	return db, nil
}

// Connect establishes a connection to the database
func (db *Database) Connect(ctx context.Context) error {
	// Build connection string from PostGIS config
	dsn := db.config.BuildPostGISConnectionString()

	// Open database connection with sqlx
	conn, err := sqlx.ConnectContext(ctx, "postgres", dsn)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	// Configure connection pool
	conn.SetMaxOpenConns(db.config.Database.MaxOpenConns)
	conn.SetMaxIdleConns(db.config.Database.MaxIdleConns)
	conn.SetConnMaxLifetime(db.config.Database.ConnMaxLifetime)

	// Test the connection
	if err := conn.PingContext(ctx); err != nil {
		conn.Close()
		return fmt.Errorf("failed to ping database: %w", err)
	}

	db.conn = conn
	return nil
}

// Close closes the database connection
func (db *Database) Close() error {
	if db.conn != nil {
		return db.conn.Close()
	}
	return nil
}

// Health checks the health of the database connection
func (db *Database) Health(ctx context.Context) error {
	if db.conn == nil {
		return fmt.Errorf("database connection is nil")
	}

	// Create a context with timeout for health check
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	// Ping the database
	if err := db.conn.PingContext(ctx); err != nil {
		return fmt.Errorf("database ping failed: %w", err)
	}

	// Check connection pool status
	stats := db.conn.Stats()
	if stats.OpenConnections == 0 && stats.InUse == 0 {
		return fmt.Errorf("no database connections available")
	}

	// Verify database is accessible with a simple query
	var result int
	if err := db.conn.GetContext(ctx, &result, "SELECT 1"); err != nil {
		return fmt.Errorf("database query test failed: %w", err)
	}

	return nil
}

// BeginTx starts a new transaction
func (db *Database) BeginTx(ctx context.Context) (interface{}, error) {
	if db.conn == nil {
		return nil, fmt.Errorf("database connection is nil")
	}

	tx, err := db.conn.BeginTxx(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}

	return tx, nil
}

// CommitTx commits a transaction
func (db *Database) CommitTx(tx interface{}) error {
	if tx == nil {
		return fmt.Errorf("transaction is nil")
	}

	sqlTx, ok := tx.(*sqlx.Tx)
	if !ok {
		return fmt.Errorf("invalid transaction type")
	}

	if err := sqlTx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// RollbackTx rolls back a transaction
func (db *Database) RollbackTx(tx interface{}) error {
	if tx == nil {
		return fmt.Errorf("transaction is nil")
	}

	sqlTx, ok := tx.(*sqlx.Tx)
	if !ok {
		return fmt.Errorf("invalid transaction type")
	}

	if err := sqlTx.Rollback(); err != nil {
		return fmt.Errorf("failed to rollback transaction: %w", err)
	}

	return nil
}

// PostGISDatabase extends Database with PostGIS-specific functionality
type PostGISDatabase struct {
	*Database
}

// NewPostGISDatabase creates a new PostGIS database instance
func NewPostGISDatabase(cfg *config.Config) (domain.Database, error) {
	baseDB, err := NewDatabase(cfg)
	if err != nil {
		return nil, err
	}

	return &PostGISDatabase{
		Database: baseDB.(*Database),
	}, nil
}

// SpatialQueries provides PostGIS spatial query functionality
func (db *PostGISDatabase) SpatialQueries() *SpatialQueries {
	return &SpatialQueries{
		db: db,
	}
}

// SpatialQueries handles spatial operations
type SpatialQueries struct {
	db *PostGISDatabase
}

// QueryWithinBounds queries for objects within spatial bounds
func (sq *SpatialQueries) QueryWithinBounds(ctx context.Context, bounds *domain.Location, radius float64) ([]*domain.Equipment, error) {
	// TODO: Implement PostGIS spatial queries
	return nil, fmt.Errorf("not implemented")
}

// QueryNearest queries for nearest objects to a point
func (sq *SpatialQueries) QueryNearest(ctx context.Context, point *domain.Location, limit int) ([]*domain.Equipment, error) {
	// TODO: Implement PostGIS nearest neighbor queries
	return nil, fmt.Errorf("not implemented")
}
