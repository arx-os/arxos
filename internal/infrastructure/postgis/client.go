package postgis

import (
	"context"
	"fmt"
	"time"

	_ "github.com/lib/pq"
	"github.com/jmoiron/sqlx"
)

// Config holds PostGIS connection configuration
type Config struct {
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

// Client represents a PostGIS database client
type Client struct {
	db     *sqlx.DB
	config *Config
}

// NewClient creates a new PostGIS client
func NewClient(config *Config) (*Client, error) {
	dsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		config.Host,
		config.Port,
		config.User,
		config.Password,
		config.Database,
		config.SSLMode,
	)
	
	db, err := sqlx.Connect("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to PostGIS: %w", err)
	}
	
	// Configure connection pool
	db.SetMaxOpenConns(config.MaxConnections)
	db.SetMaxIdleConns(config.MaxIdleConns)
	db.SetConnMaxLifetime(config.ConnMaxLifetime)
	db.SetConnMaxIdleTime(config.ConnMaxIdleTime)
	
	client := &Client{
		db:     db,
		config: config,
	}
	
	// Initialize PostGIS extensions
	if err := client.initializePostGIS(); err != nil {
		return nil, fmt.Errorf("failed to initialize PostGIS: %w", err)
	}
	
	return client, nil
}

// GetDB returns the underlying database connection
func (c *Client) GetDB() *sqlx.DB {
	return c.db
}

// Close closes the database connection
func (c *Client) Close() error {
	return c.db.Close()
}

// Health checks the database connection health
func (c *Client) Health(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	
	return c.db.PingContext(ctx)
}

// initializePostGIS initializes PostGIS extensions
func (c *Client) initializePostGIS() error {
	extensions := []string{
		"CREATE EXTENSION IF NOT EXISTS postgis;",
		"CREATE EXTENSION IF NOT EXISTS postgis_topology;",
		"CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;",
		"CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;",
	}
	
	for _, ext := range extensions {
		if _, err := c.db.Exec(ext); err != nil {
			return fmt.Errorf("failed to create extension: %w", err)
		}
	}
	
	return nil
}

// CreateSchema creates the database schema
func (c *Client) CreateSchema(ctx context.Context) error {
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
	
	_, err := c.db.ExecContext(ctx, schema)
	return err
}

// DropSchema drops the database schema
func (c *Client) DropSchema(ctx context.Context) error {
	schema := `
		DROP TABLE IF EXISTS equipment CASCADE;
		DROP TABLE IF EXISTS buildings CASCADE;
		DROP TABLE IF EXISTS users CASCADE;
		DROP TABLE IF EXISTS organizations CASCADE;
	`
	
	_, err := c.db.ExecContext(ctx, schema)
	return err
}
