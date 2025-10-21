package infrastructure

import (
	"context"
	"fmt"
	"time"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq" // PostgreSQL driver

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
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

// DB returns the underlying *sql.DB for direct access
// This is needed for repositories that require *sql.DB
func (db *Database) DB() *sqlx.DB {
	return db.conn
}

// Ping checks if the database connection is alive
// Implements domain.Database interface
func (db *Database) Ping() error {
	return db.Health(context.Background())
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
func (db *Database) BeginTx(ctx context.Context) (any, error) {
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
func (db *Database) CommitTx(tx any) error {
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
func (db *Database) RollbackTx(tx any) error {
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

// GetDB returns the underlying database connection for direct SQL operations
// This is useful for repository initialization
func (db *Database) GetDB() *sqlx.DB {
	return db.conn
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
	query := `
		SELECT
			id, building_id, floor_id, room_id,
			name, equipment_type as type, model,
			location_x, location_y, location_z,
			status, created_at, updated_at
		FROM equipment
		WHERE location_x IS NOT NULL
		  AND location_y IS NOT NULL
		  AND SQRT(
				POW(location_x - $1, 2) +
				POW(location_y - $2, 2) +
				POW(COALESCE(location_z, 0) - $3, 2)
			  ) <= $4
		ORDER BY SQRT(
				POW(location_x - $1, 2) +
				POW(location_y - $2, 2) +
				POW(COALESCE(location_z, 0) - $3, 2)
			  )
		LIMIT 1000
	`

	rows, err := sq.db.DB().QueryContext(ctx, query, bounds.X, bounds.Y, bounds.Z, radius)
	if err != nil {
		return nil, fmt.Errorf("failed to query equipment within bounds: %w", err)
	}
	defer rows.Close()

	var equipment []*domain.Equipment
	for rows.Next() {
		var e domain.Equipment
		var locX, locY, locZ *float64
		var floorID, roomID *string

		err := rows.Scan(
			&e.ID, &e.BuildingID, &floorID, &roomID,
			&e.Name, &e.Type, &e.Model,
			&locX, &locY, &locZ,
			&e.Status, &e.CreatedAt, &e.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}

		// Set optional fields
		if floorID != nil {
			e.FloorID = types.ID{Legacy: *floorID}
		}
		if roomID != nil {
			e.RoomID = types.ID{Legacy: *roomID}
		}

		// Set location if all coordinates are present
		if locX != nil && locY != nil {
			e.Location = &domain.Location{
				X: *locX,
				Y: *locY,
				Z: 0,
			}
			if locZ != nil {
				e.Location.Z = *locZ
			}
		}

		equipment = append(equipment, &e)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating equipment rows: %w", err)
	}

	return equipment, nil
}

// QueryNearest queries for nearest objects to a point
func (sq *SpatialQueries) QueryNearest(ctx context.Context, point *domain.Location, limit int) ([]*domain.Equipment, error) {
	if limit <= 0 {
		limit = 10 // default limit
	}
	if limit > 1000 {
		limit = 1000 // max limit for performance
	}

	query := `
		SELECT
			id, building_id, floor_id, room_id,
			name, equipment_type as type, model,
			location_x, location_y, location_z,
			status, created_at, updated_at,
			SQRT(
				POW(location_x - $1, 2) +
				POW(location_y - $2, 2) +
				POW(COALESCE(location_z, 0) - $3, 2)
			) as distance
		FROM equipment
		WHERE location_x IS NOT NULL
		  AND location_y IS NOT NULL
		ORDER BY distance
		LIMIT $4
	`

	rows, err := sq.db.DB().QueryContext(ctx, query, point.X, point.Y, point.Z, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query nearest equipment: %w", err)
	}
	defer rows.Close()

	var equipment []*domain.Equipment
	for rows.Next() {
		var e domain.Equipment
		var locX, locY, locZ *float64
		var floorID, roomID *string
		var distance float64

		err := rows.Scan(
			&e.ID, &e.BuildingID, &floorID, &roomID,
			&e.Name, &e.Type, &e.Model,
			&locX, &locY, &locZ,
			&e.Status, &e.CreatedAt, &e.UpdatedAt,
			&distance,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}

		// Set optional fields
		if floorID != nil {
			e.FloorID = types.ID{Legacy: *floorID}
		}
		if roomID != nil {
			e.RoomID = types.ID{Legacy: *roomID}
		}

		// Set location if all coordinates are present
		if locX != nil && locY != nil {
			e.Location = &domain.Location{
				X: *locX,
				Y: *locY,
				Z: 0,
			}
			if locZ != nil {
				e.Location.Z = *locZ
			}
		}

		equipment = append(equipment, &e)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating equipment rows: %w", err)
	}

	return equipment, nil
}
