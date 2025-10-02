package postgis

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	_ "github.com/lib/pq" // PostgreSQL driver
)

// PostGISConfig holds configuration for PostGIS database
type PostGISConfig struct {
	Host            string
	Port            int
	Database        string
	User            string
	Password        string
	SSLMode         string
	MaxConnections  int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	ConnMaxIdleTime time.Duration
}

// PostGIS represents a PostGIS database connection following Clean Architecture
type PostGIS struct {
	db     *sql.DB
	config *PostGISConfig
	logger domain.Logger
}

// NewPostGIS creates a new PostGIS connection
func NewPostGIS(config *PostGISConfig, logger domain.Logger) (*PostGIS, error) {
	dsn := fmt.Sprintf("host=%s port=%d user=%s dbname=%s sslmode=%s",
		config.Host,
		config.Port,
		config.User,
		config.Database,
		config.SSLMode,
	)

	// Add password only if it's not empty
	if config.Password != "" {
		dsn = fmt.Sprintf("%s password=%s", dsn, config.Password)
	}

	logger.Info("PostGIS connection attempt", "dsn", dsn, "host", config.Host, "port", config.Port, "user", config.User, "database", config.Database)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open PostGIS connection: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(config.MaxConnections)
	db.SetMaxIdleConns(config.MaxIdleConns)
	db.SetConnMaxLifetime(config.ConnMaxLifetime)
	db.SetConnMaxIdleTime(config.ConnMaxIdleTime)

	pg := &PostGIS{
		db:     db,
		config: config,
		logger: logger,
	}

	// Test connection
	if err := pg.Ping(context.Background()); err != nil {
		return nil, fmt.Errorf("failed to ping PostGIS: %w", err)
	}

	// Initialize PostGIS extensions
	if err := pg.initializeExtensions(); err != nil {
		return nil, fmt.Errorf("failed to initialize PostGIS extensions: %w", err)
	}

	logger.Info("PostGIS connection established successfully")
	return pg, nil
}

// Ping tests the database connection
func (pg *PostGIS) Ping(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	return pg.db.PingContext(ctx)
}

// Close closes the database connection
func (pg *PostGIS) Close() error {
	if pg.db != nil {
		return pg.db.Close()
	}
	return nil
}

// GetDB returns the underlying database connection
func (pg *PostGIS) GetDB() *sql.DB {
	return pg.db
}

// initializeExtensions initializes PostGIS extensions
func (pg *PostGIS) initializeExtensions() error {
	extensions := []string{
		"CREATE EXTENSION IF NOT EXISTS postgis;",
		"CREATE EXTENSION IF NOT EXISTS postgis_topology;",
		"CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;",
		"CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;",
	}

	for _, ext := range extensions {
		if _, err := pg.db.Exec(ext); err != nil {
			pg.logger.Warn("Failed to create extension: %s, error: %v", ext, err)
			// Continue with other extensions even if one fails
		}
	}

	return nil
}

// CreateSchema creates the database schema
func (pg *PostGIS) CreateSchema(ctx context.Context) error {
	schema := `
	-- Buildings table with PostGIS geometry
	CREATE TABLE IF NOT EXISTS buildings (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		name VARCHAR(255) NOT NULL,
		address TEXT NOT NULL,
		coordinates GEOMETRY(POINT, 4326),
		created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
	);
	
	-- Equipment table with spatial reference
	CREATE TABLE IF NOT EXISTS equipment (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
		name VARCHAR(255) NOT NULL,
		type VARCHAR(100) NOT NULL,
		model VARCHAR(255),
		location GEOMETRY(POINT, 4326),
		status VARCHAR(50) DEFAULT 'operational',
		created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
	);
	
	-- Users table
	CREATE TABLE IF NOT EXISTS users (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		email VARCHAR(255) UNIQUE NOT NULL,
		name VARCHAR(255) NOT NULL,
		role VARCHAR(50) NOT NULL,
		active BOOLEAN DEFAULT true,
		created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
	);
	
	-- Organizations table
	CREATE TABLE IF NOT EXISTS organizations (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		name VARCHAR(255) UNIQUE NOT NULL,
		description TEXT,
		plan VARCHAR(50) NOT NULL,
		active BOOLEAN DEFAULT true,
		created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
	);
	
	-- Create spatial indexes
	CREATE INDEX IF NOT EXISTS idx_buildings_coordinates ON buildings USING GIST (coordinates);
	CREATE INDEX IF NOT EXISTS idx_equipment_location ON equipment USING GIST (location);
	CREATE INDEX IF NOT EXISTS idx_equipment_building_id ON equipment (building_id);
	`

	_, err := pg.db.ExecContext(ctx, schema)
	if err != nil {
		pg.logger.Error("Failed to create schema: %v", err)
		return fmt.Errorf("failed to create schema: %w", err)
	}

	pg.logger.Info("Database schema created successfully")
	return nil
}

// DropSchema drops the database schema
func (pg *PostGIS) DropSchema(ctx context.Context) error {
	schema := `
		DROP TABLE IF EXISTS equipment CASCADE;
		DROP TABLE IF EXISTS buildings CASCADE;
		DROP TABLE IF EXISTS users CASCADE;
		DROP TABLE IF EXISTS organizations CASCADE;
	`

	_, err := pg.db.ExecContext(ctx, schema)
	if err != nil {
		pg.logger.Error("Failed to drop schema: %v", err)
		return fmt.Errorf("failed to drop schema: %w", err)
	}

	pg.logger.Info("Database schema dropped successfully")
	return nil
}

// Health checks the database health
func (pg *PostGIS) Health(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	// Test basic connectivity
	if err := pg.Ping(ctx); err != nil {
		return fmt.Errorf("database ping failed: %w", err)
	}

	// Test PostGIS functionality
	var version string
	err := pg.db.QueryRowContext(ctx, "SELECT PostGIS_Version()").Scan(&version)
	if err != nil {
		return fmt.Errorf("PostGIS version check failed: %w", err)
	}

	pg.logger.Debug("PostGIS health check passed, version: %s", version)
	return nil
}
