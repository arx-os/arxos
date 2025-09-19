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
}

// Client manages PostGIS database connections
type Client struct {
	db *sqlx.DB
}

// NewClient creates a new PostGIS client with connection verification
func NewClient(config Config) (*Client, error) {
	// Build connection string
	dsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		config.Host, config.Port, config.User, config.Password, config.Database, config.SSLMode)

	// Connect to database
	db, err := sqlx.Connect("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to PostGIS: %w", err)
	}

	// Configure connection pool
	if config.MaxConnections > 0 {
		db.SetMaxOpenConns(config.MaxConnections)
	}
	if config.MaxIdleConns > 0 {
		db.SetMaxIdleConns(config.MaxIdleConns)
	}
	if config.ConnMaxLifetime > 0 {
		db.SetConnMaxLifetime(config.ConnMaxLifetime)
	}

	// Verify PostGIS extension is available
	var version string
	err = db.Get(&version, "SELECT PostGIS_Version()")
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("PostGIS extension not available: %w", err)
	}

	return &Client{db: db}, nil
}

// InitializeSchema creates the necessary tables and indices
func (c *Client) InitializeSchema(ctx context.Context) error {
	schema := `
	-- Enable PostGIS if not already enabled
	CREATE EXTENSION IF NOT EXISTS postgis;
	CREATE EXTENSION IF NOT EXISTS postgis_topology;

	-- Buildings table with GPS origin
	CREATE TABLE IF NOT EXISTS buildings (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		arxos_id TEXT UNIQUE NOT NULL,
		name TEXT NOT NULL,
		address TEXT,
		origin GEOMETRY(Point, 4326),
		rotation FLOAT DEFAULT 0,
		metadata JSONB DEFAULT '{}',
		created_at TIMESTAMPTZ DEFAULT NOW(),
		updated_at TIMESTAMPTZ DEFAULT NOW()
	);

	-- Equipment table with 3D spatial data
	CREATE TABLE IF NOT EXISTS equipment (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
		path TEXT NOT NULL,
		name TEXT NOT NULL,
		type TEXT NOT NULL,
		position GEOMETRY(PointZ, 4326),
		position_local JSONB, -- Building-relative coordinates in mm
		confidence SMALLINT DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 3),
		status TEXT DEFAULT 'UNKNOWN',
		metadata JSONB DEFAULT '{}',
		created_at TIMESTAMPTZ DEFAULT NOW(),
		updated_at TIMESTAMPTZ DEFAULT NOW(),
		UNIQUE(building_id, path)
	);

	-- Floors table
	CREATE TABLE IF NOT EXISTS floors (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
		number INTEGER NOT NULL,
		name TEXT,
		elevation FLOAT, -- meters
		boundary GEOMETRY(Polygon, 4326),
		created_at TIMESTAMPTZ DEFAULT NOW(),
		UNIQUE(building_id, number)
	);

	-- Rooms table
	CREATE TABLE IF NOT EXISTS rooms (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		floor_id UUID REFERENCES floors(id) ON DELETE CASCADE,
		number TEXT NOT NULL,
		name TEXT,
		type TEXT,
		boundary GEOMETRY(Polygon, 4326),
		area FLOAT, -- square meters
		created_at TIMESTAMPTZ DEFAULT NOW()
	);

	-- Spatial indices for performance
	CREATE INDEX IF NOT EXISTS idx_buildings_origin ON buildings USING GIST(origin);
	CREATE INDEX IF NOT EXISTS idx_equipment_position ON equipment USING GIST(position);
	CREATE INDEX IF NOT EXISTS idx_equipment_building ON equipment(building_id);
	CREATE INDEX IF NOT EXISTS idx_floors_boundary ON floors USING GIST(boundary);
	CREATE INDEX IF NOT EXISTS idx_rooms_boundary ON rooms USING GIST(boundary);

	-- Text search indices
	CREATE INDEX IF NOT EXISTS idx_equipment_name ON equipment USING GIN(to_tsvector('english', name));
	CREATE INDEX IF NOT EXISTS idx_equipment_path ON equipment(path);
	CREATE INDEX IF NOT EXISTS idx_buildings_arxos_id ON buildings(arxos_id);

	-- Users table
	CREATE TABLE IF NOT EXISTS users (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		email TEXT UNIQUE NOT NULL,
		full_name TEXT NOT NULL,
		password_hash TEXT NOT NULL,
		role TEXT NOT NULL DEFAULT 'viewer',
		status TEXT NOT NULL DEFAULT 'active',
		last_login TIMESTAMPTZ,
		created_at TIMESTAMPTZ DEFAULT NOW(),
		updated_at TIMESTAMPTZ DEFAULT NOW()
	);

	-- User sessions table
	CREATE TABLE IF NOT EXISTS user_sessions (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		user_id UUID REFERENCES users(id) ON DELETE CASCADE,
		token TEXT UNIQUE NOT NULL,
		refresh_token TEXT UNIQUE NOT NULL,
		expires_at TIMESTAMPTZ NOT NULL,
		created_at TIMESTAMPTZ DEFAULT NOW(),
		updated_at TIMESTAMPTZ DEFAULT NOW()
	);

	-- Password reset tokens table
	CREATE TABLE IF NOT EXISTS password_reset_tokens (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		user_id UUID REFERENCES users(id) ON DELETE CASCADE,
		token TEXT UNIQUE NOT NULL,
		used BOOLEAN DEFAULT FALSE,
		expires_at TIMESTAMPTZ NOT NULL,
		created_at TIMESTAMPTZ DEFAULT NOW()
	);

	-- Organizations table
	CREATE TABLE IF NOT EXISTS organizations (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		name TEXT NOT NULL,
		description TEXT,
		created_by UUID REFERENCES users(id),
		created_at TIMESTAMPTZ DEFAULT NOW(),
		updated_at TIMESTAMPTZ DEFAULT NOW()
	);

	-- Organization members table
	CREATE TABLE IF NOT EXISTS organization_members (
		organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
		user_id UUID REFERENCES users(id) ON DELETE CASCADE,
		role TEXT NOT NULL DEFAULT 'member',
		joined_at TIMESTAMPTZ DEFAULT NOW(),
		PRIMARY KEY (organization_id, user_id)
	);

	-- Organization invitations table
	CREATE TABLE IF NOT EXISTS organization_invitations (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
		email TEXT NOT NULL,
		role TEXT NOT NULL DEFAULT 'member',
		token TEXT UNIQUE NOT NULL,
		invited_by UUID REFERENCES users(id),
		accepted_at TIMESTAMPTZ,
		expires_at TIMESTAMPTZ NOT NULL,
		created_at TIMESTAMPTZ DEFAULT NOW()
	);

	-- User indices
	CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
	CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
	CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
	CREATE INDEX IF NOT EXISTS idx_password_reset_expires ON password_reset_tokens(expires_at);
	CREATE INDEX IF NOT EXISTS idx_org_members_user ON organization_members(user_id);
	CREATE INDEX IF NOT EXISTS idx_org_invitations_email ON organization_invitations(email);
	`

	_, err := c.db.ExecContext(ctx, schema)
	if err != nil {
		return fmt.Errorf("failed to initialize schema: %w", err)
	}

	return nil
}

// Close closes the database connection
func (c *Client) Close() error {
	return c.db.Close()
}

// DB returns the underlying sqlx.DB for direct access if needed
func (c *Client) DB() *sqlx.DB {
	return c.db
}

// Ping verifies the database connection is alive
func (c *Client) Ping(ctx context.Context) error {
	return c.db.PingContext(ctx)
}

// InTransaction executes a function within a database transaction
func (c *Client) InTransaction(ctx context.Context, fn func(*sqlx.Tx) error) error {
	tx, err := c.db.BeginTxx(ctx, nil)
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
			return fmt.Errorf("tx error: %v, rollback error: %v", err, rbErr)
		}
		return err
	}

	return tx.Commit()
}