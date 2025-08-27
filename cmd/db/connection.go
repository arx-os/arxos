package db

import (
	"database/sql"
	"fmt"
	"sync"
	"time"

	"github.com/arxos/arxos/cmd/config"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq" // PostgreSQL driver
)

var (
	db     *sqlx.DB
	dbOnce sync.Once
	dbErr  error
)

// Connection options
type Options struct {
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	ConnMaxIdleTime time.Duration
}

// DefaultOptions returns default connection pool options
func DefaultOptions() *Options {
	return &Options{
		MaxOpenConns:    25,
		MaxIdleConns:    5,
		ConnMaxLifetime: time.Hour,
		ConnMaxIdleTime: 5 * time.Minute,
	}
}

// GetDB returns the database connection (singleton)
func GetDB() (*sqlx.DB, error) {
	dbOnce.Do(func() {
		cfg := config.Get()
		db, dbErr = Connect(cfg.Database.GetDatabaseURL(), DefaultOptions())
	})
	return db, dbErr
}

// Connect establishes a database connection
func Connect(dsn string, opts *Options) (*sqlx.DB, error) {
	// Open database connection
	conn, err := sqlx.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool
	if opts != nil {
		conn.SetMaxOpenConns(opts.MaxOpenConns)
		conn.SetMaxIdleConns(opts.MaxIdleConns)
		conn.SetConnMaxLifetime(opts.ConnMaxLifetime)
		conn.SetConnMaxIdleTime(opts.ConnMaxIdleTime)
	}

	// Test connection
	if err := conn.Ping(); err != nil {
		conn.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return conn, nil
}

// Close closes the database connection
func Close() error {
	if db != nil {
		return db.Close()
	}
	return nil
}

// InitSchema initializes the database schema
func InitSchema(db *sqlx.DB) error {
	schema := `
	-- Buildings table
	CREATE TABLE IF NOT EXISTS buildings (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		name VARCHAR(255) NOT NULL UNIQUE,
		type VARCHAR(50),
		floors INTEGER,
		area VARCHAR(100),
		location TEXT,
		metadata JSONB,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- ArxObjects table with PostGIS geometry
	CREATE TABLE IF NOT EXISTS arxobjects (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
		object_id VARCHAR(255) NOT NULL,
		type VARCHAR(100) NOT NULL,
		name VARCHAR(255),
		path TEXT,
		parent_id UUID REFERENCES arxobjects(id) ON DELETE CASCADE,
		
		-- Spatial data
		geometry GEOMETRY(PointZ, 4326),
		world_x_mm DOUBLE PRECISION,
		world_y_mm DOUBLE PRECISION,
		world_z_mm DOUBLE PRECISION,
		width_mm INTEGER,
		height_mm INTEGER,
		depth_mm INTEGER,
		
		-- Properties
		properties JSONB,
		metadata JSONB,
		
		-- Confidence and validation
		confidence FLOAT DEFAULT 0.0,
		validation_status VARCHAR(50) DEFAULT 'unvalidated',
		validated_at TIMESTAMP,
		validated_by VARCHAR(255),
		
		-- Timestamps
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		
		-- Indexes
		UNIQUE(building_id, object_id)
	);

	-- Create spatial index
	CREATE INDEX IF NOT EXISTS idx_arxobjects_geometry 
		ON arxobjects USING GIST (geometry);

	-- Create other indexes
	CREATE INDEX IF NOT EXISTS idx_arxobjects_building 
		ON arxobjects(building_id);
	CREATE INDEX IF NOT EXISTS idx_arxobjects_type 
		ON arxobjects(type);
	CREATE INDEX IF NOT EXISTS idx_arxobjects_confidence 
		ON arxobjects(confidence);
	CREATE INDEX IF NOT EXISTS idx_arxobjects_path 
		ON arxobjects(path);

	-- Floors table
	CREATE TABLE IF NOT EXISTS floors (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
		floor_number INTEGER NOT NULL,
		name VARCHAR(255),
		height_mm INTEGER,
		area_sqm FLOAT,
		metadata JSONB,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		UNIQUE(building_id, floor_number)
	);

	-- Systems table
	CREATE TABLE IF NOT EXISTS systems (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
		system_type VARCHAR(100) NOT NULL,
		name VARCHAR(255),
		description TEXT,
		properties JSONB,
		metadata JSONB,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Session table for navigation state
	CREATE TABLE IF NOT EXISTS sessions (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id),
		current_path TEXT DEFAULT '/',
		previous_path TEXT,
		user_id VARCHAR(255),
		metadata JSONB,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Validation history
	CREATE TABLE IF NOT EXISTS validations (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		arxobject_id UUID REFERENCES arxobjects(id) ON DELETE CASCADE,
		validator_id VARCHAR(255),
		confidence_before FLOAT,
		confidence_after FLOAT,
		validation_type VARCHAR(50),
		evidence_url TEXT,
		notes TEXT,
		metadata JSONB,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Version history (for git-like operations)
	CREATE TABLE IF NOT EXISTS version_history (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
		version_number INTEGER NOT NULL,
		commit_message TEXT,
		author VARCHAR(255),
		changes JSONB,
		snapshot JSONB,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		UNIQUE(building_id, version_number)
	);

	-- Update triggers for updated_at
	CREATE OR REPLACE FUNCTION update_updated_at_column()
	RETURNS TRIGGER AS $$
	BEGIN
		NEW.updated_at = CURRENT_TIMESTAMP;
		RETURN NEW;
	END;
	$$ language 'plpgsql';

	-- Apply update trigger to all tables
	DO $$ 
	DECLARE
		t text;
	BEGIN
		FOREACH t IN ARRAY ARRAY['buildings', 'arxobjects', 'floors', 'systems', 'sessions']
		LOOP
			EXECUTE format('
				DROP TRIGGER IF EXISTS update_%I_updated_at ON %I;
				CREATE TRIGGER update_%I_updated_at 
					BEFORE UPDATE ON %I 
					FOR EACH ROW 
					EXECUTE FUNCTION update_updated_at_column();
			', t, t, t, t);
		END LOOP;
	END $$;
	`

	// Execute schema creation
	if _, err := db.Exec(schema); err != nil {
		return fmt.Errorf("failed to create schema: %w", err)
	}

	return nil
}

// Transaction wraps a function in a database transaction
func Transaction(db *sqlx.DB, fn func(*sqlx.Tx) error) error {
	tx, err := db.Beginx()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	
	defer func() {
		if p := recover(); p != nil {
			_ = tx.Rollback()
			panic(p) // Re-panic
		}
	}()
	
	if err := fn(tx); err != nil {
		if rbErr := tx.Rollback(); rbErr != nil {
			return fmt.Errorf("tx error: %w, rollback error: %v", err, rbErr)
		}
		return err
	}
	
	return tx.Commit()
}

// EnablePostGIS enables PostGIS extension
func EnablePostGIS(db *sqlx.DB) error {
	_, err := db.Exec("CREATE EXTENSION IF NOT EXISTS postgis;")
	if err != nil {
		return fmt.Errorf("failed to enable PostGIS: %w", err)
	}
	return nil
}

// CheckConnection verifies database connectivity
func CheckConnection(db *sqlx.DB) error {
	var result int
	err := db.Get(&result, "SELECT 1")
	return err
}