package database

import (
	"context"
	"fmt"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

// Migration represents a database migration
type Migration struct {
	Version     int
	Name        string
	Description string
	Up          string
	Down        string
	ExecutedAt  *time.Time
}

// migrations defines all database migrations in order
var migrations = []Migration{
	{
		Version:     1,
		Description: "Create initial schema",
		Up: `
			-- Schema version tracking
			CREATE TABLE IF NOT EXISTS schema_version (
				version INTEGER PRIMARY KEY,
				description TEXT,
				applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			);

			-- Floor plans table
			CREATE TABLE IF NOT EXISTS floor_plans (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				building TEXT NOT NULL,
				level INTEGER NOT NULL,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			);

			-- Rooms table
			CREATE TABLE IF NOT EXISTS rooms (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				min_x REAL NOT NULL,
				min_y REAL NOT NULL,
				max_x REAL NOT NULL,
				max_y REAL NOT NULL,
				floor_plan_id TEXT NOT NULL,
				FOREIGN KEY (floor_plan_id) REFERENCES floor_plans(id) ON DELETE CASCADE
			);

			-- Equipment table
			CREATE TABLE IF NOT EXISTS equipment (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				type TEXT NOT NULL,
				room_id TEXT,
				location_x REAL,
				location_y REAL,
				status TEXT DEFAULT 'normal',
				notes TEXT,
				marked_by TEXT,
				marked_at TIMESTAMP,
				floor_plan_id TEXT NOT NULL,
				FOREIGN KEY (floor_plan_id) REFERENCES floor_plans(id) ON DELETE CASCADE,
				FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
			);

			-- Indexes for performance
			CREATE INDEX IF NOT EXISTS idx_rooms_floor_plan ON rooms(floor_plan_id);
			CREATE INDEX IF NOT EXISTS idx_equipment_floor_plan ON equipment(floor_plan_id);
			CREATE INDEX IF NOT EXISTS idx_equipment_room ON equipment(room_id);
			CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);
			CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(type);

			-- Case-insensitive lookups
			CREATE INDEX IF NOT EXISTS idx_equipment_id_lower ON equipment(LOWER(id));
			CREATE INDEX IF NOT EXISTS idx_rooms_id_lower ON rooms(LOWER(id));
		`,
		Down: `
			DROP TABLE IF EXISTS equipment;
			DROP TABLE IF EXISTS rooms;
			DROP TABLE IF EXISTS floor_plans;
			DROP TABLE IF EXISTS schema_version;
		`,
	},
	{
		Version:     2,
		Description: "Add connections and spatial indexing",
		Up: `
			-- Connections table for equipment relationships
			CREATE TABLE IF NOT EXISTS connections (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				from_equipment_id TEXT NOT NULL,
				to_equipment_id TEXT NOT NULL,
				connection_type TEXT NOT NULL,
				metadata TEXT, -- JSON
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (from_equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
				FOREIGN KEY (to_equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
				UNIQUE(from_equipment_id, to_equipment_id, connection_type)
			);

			-- Spatial index for proximity queries
			CREATE INDEX IF NOT EXISTS idx_equipment_spatial ON equipment(location_x, location_y);
			CREATE INDEX IF NOT EXISTS idx_rooms_spatial ON rooms(min_x, min_y, max_x, max_y);

			-- Full-text search
			CREATE VIRTUAL TABLE IF NOT EXISTS equipment_fts USING fts5(
				id, name, type, notes, status,
				content=equipment
			);

			-- Trigger to keep FTS index updated
			CREATE TRIGGER IF NOT EXISTS equipment_ai AFTER INSERT ON equipment BEGIN
				INSERT INTO equipment_fts(id, name, type, notes, status) 
				VALUES (new.id, new.name, new.type, new.notes, new.status);
			END;

			CREATE TRIGGER IF NOT EXISTS equipment_ad AFTER DELETE ON equipment BEGIN
				DELETE FROM equipment_fts WHERE id = old.id;
			END;

			CREATE TRIGGER IF NOT EXISTS equipment_au AFTER UPDATE ON equipment BEGIN
				UPDATE equipment_fts 
				SET name = new.name, type = new.type, notes = new.notes, status = new.status
				WHERE id = new.id;
			END;
		`,
		Down: `
			DROP TRIGGER IF EXISTS equipment_au;
			DROP TRIGGER IF EXISTS equipment_ad;
			DROP TRIGGER IF EXISTS equipment_ai;
			DROP TABLE IF EXISTS equipment_fts;
			DROP TABLE IF EXISTS connections;
		`,
	},
	{
		Version:     3,
		Description: "Add audit trail and conflict tracking",
		Up: `
			-- Audit trail for all changes
			CREATE TABLE IF NOT EXISTS audit_log (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				object_id TEXT NOT NULL,
				object_type TEXT NOT NULL,
				operation TEXT NOT NULL, -- create, update, delete
				old_value TEXT, -- JSON
				new_value TEXT, -- JSON
				user TEXT,
				branch TEXT DEFAULT 'main',
				commit_hash TEXT,
				timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			);

			-- Conflict tracking for merge operations
			CREATE TABLE IF NOT EXISTS conflicts (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				object_id TEXT NOT NULL,
				object_type TEXT NOT NULL,
				source TEXT NOT NULL,
				our_value TEXT, -- JSON
				their_value TEXT, -- JSON
				resolved BOOLEAN DEFAULT 0,
				resolution TEXT, -- JSON
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				resolved_at TIMESTAMP
			);

			-- Query cache for expensive operations
			CREATE TABLE IF NOT EXISTS query_cache (
				query_hash TEXT PRIMARY KEY,
				query_text TEXT NOT NULL,
				result TEXT, -- JSON
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				expires_at TIMESTAMP
			);

			-- Indexes
			CREATE INDEX IF NOT EXISTS idx_audit_object ON audit_log(object_id, object_type);
			CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
			CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user);
			CREATE INDEX IF NOT EXISTS idx_conflicts_unresolved ON conflicts(resolved, object_id);
			CREATE INDEX IF NOT EXISTS idx_query_cache_expires ON query_cache(expires_at);
		`,
		Down: `
			DROP TABLE IF EXISTS query_cache;
			DROP TABLE IF EXISTS conflicts;
			DROP TABLE IF EXISTS audit_log;
		`,
	},
	{
		Version:     4,
		Description: "Add users and authentication tables",
		Up: `
			-- Users table
			CREATE TABLE IF NOT EXISTS users (
				id TEXT PRIMARY KEY,
				email TEXT UNIQUE NOT NULL,
				name TEXT NOT NULL,
				password_hash TEXT NOT NULL,
				avatar TEXT,
				phone TEXT,
				status TEXT DEFAULT 'active',
				email_verified BOOLEAN DEFAULT 0,
				phone_verified BOOLEAN DEFAULT 0,
				mfa_enabled BOOLEAN DEFAULT 0,
				mfa_secret TEXT,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				last_login_at TIMESTAMP
			);

			-- User sessions table
			CREATE TABLE IF NOT EXISTS user_sessions (
				id TEXT PRIMARY KEY,
				user_id TEXT NOT NULL,
				organization_id TEXT,
				token TEXT UNIQUE NOT NULL,
				refresh_token TEXT UNIQUE NOT NULL,
				ip_address TEXT,
				user_agent TEXT,
				expires_at TIMESTAMP NOT NULL,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				last_access_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
			);

			-- Password reset tokens
			CREATE TABLE IF NOT EXISTS password_resets (
				id TEXT PRIMARY KEY,
				user_id TEXT NOT NULL,
				token TEXT UNIQUE NOT NULL,
				expires_at TIMESTAMP NOT NULL,
				used_at TIMESTAMP,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
			);

			-- Email verification tokens
			CREATE TABLE IF NOT EXISTS email_verifications (
				id TEXT PRIMARY KEY,
				user_id TEXT NOT NULL,
				email TEXT NOT NULL,
				token TEXT UNIQUE NOT NULL,
				expires_at TIMESTAMP NOT NULL,
				verified_at TIMESTAMP,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
			);

			-- Password reset tokens
			CREATE TABLE IF NOT EXISTS password_reset_tokens (
				id TEXT PRIMARY KEY,
				user_id TEXT NOT NULL,
				token TEXT UNIQUE NOT NULL,
				expires_at TIMESTAMP NOT NULL,
				used BOOLEAN DEFAULT FALSE,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				used_at TIMESTAMP,
				FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
			);
			CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
			CREATE INDEX idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

			-- User preferences
			CREATE TABLE IF NOT EXISTS user_preferences (
				user_id TEXT PRIMARY KEY,
				theme TEXT DEFAULT 'light',
				language TEXT DEFAULT 'en',
				timezone TEXT DEFAULT 'UTC',
				date_format TEXT DEFAULT 'YYYY-MM-DD',
				email_notifications BOOLEAN DEFAULT 1,
				push_notifications BOOLEAN DEFAULT 1,
				default_org_id TEXT,
				FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
			);

			-- Indexes for users
			CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
			CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
			CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
			CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
			CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token);
			CREATE INDEX IF NOT EXISTS idx_password_resets_expires ON password_resets(expires_at);
			CREATE INDEX IF NOT EXISTS idx_email_verifications_token ON email_verifications(token);
			CREATE INDEX IF NOT EXISTS idx_email_verifications_expires ON email_verifications(expires_at);
		`,
		Down: `
			DROP TABLE IF EXISTS user_preferences;
			DROP TABLE IF EXISTS email_verifications;
			DROP TABLE IF EXISTS password_resets;
			DROP TABLE IF EXISTS user_sessions;
			DROP TABLE IF EXISTS users;
		`,
	},
	{
		Version:     5,
		Description: "Add organizations and multi-tenancy",
		Up: `
			-- Organizations table
			CREATE TABLE IF NOT EXISTS organizations (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				slug TEXT UNIQUE NOT NULL,
				plan TEXT DEFAULT 'free',
				max_users INTEGER DEFAULT 5,
				max_buildings INTEGER DEFAULT 1,
				status TEXT DEFAULT 'active',
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			);

			-- Organization members
			CREATE TABLE IF NOT EXISTS organization_members (
				organization_id TEXT NOT NULL,
				user_id TEXT NOT NULL,
				role TEXT NOT NULL DEFAULT 'member',
				joined_at TIMESTAMP,
				PRIMARY KEY (organization_id, user_id),
				FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
				FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
			);

			-- Organization invitations
			CREATE TABLE IF NOT EXISTS organization_invitations (
				id TEXT PRIMARY KEY,
				organization_id TEXT NOT NULL,
				email TEXT NOT NULL,
				role TEXT NOT NULL DEFAULT 'member',
				token TEXT UNIQUE NOT NULL,
				invited_by TEXT NOT NULL,
				expires_at TIMESTAMP NOT NULL,
				accepted_at TIMESTAMP,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
				FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE CASCADE
			);

			-- Organization settings
			CREATE TABLE IF NOT EXISTS organization_settings (
				organization_id TEXT PRIMARY KEY,
				settings TEXT, -- JSON
				FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
			);

			-- Add organization context to existing tables
			ALTER TABLE floor_plans ADD COLUMN organization_id TEXT;
			ALTER TABLE audit_log ADD COLUMN organization_id TEXT;

			-- Indexes for organizations
			CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
			CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(status);
			CREATE INDEX IF NOT EXISTS idx_org_members_user ON organization_members(user_id);
			CREATE INDEX IF NOT EXISTS idx_org_members_role ON organization_members(role);
			CREATE INDEX IF NOT EXISTS idx_org_invitations_email ON organization_invitations(email);
			CREATE INDEX IF NOT EXISTS idx_org_invitations_token ON organization_invitations(token);
			CREATE INDEX IF NOT EXISTS idx_org_invitations_expires ON organization_invitations(expires_at);
			CREATE INDEX IF NOT EXISTS idx_floor_plans_org ON floor_plans(organization_id);
			CREATE INDEX IF NOT EXISTS idx_audit_log_org ON audit_log(organization_id);
		`,
		Down: `
			-- Remove organization context from existing tables
			-- Note: SQLite doesn't support DROP COLUMN, would need table recreation
			
			DROP TABLE IF EXISTS organization_settings;
			DROP TABLE IF EXISTS organization_invitations;
			DROP TABLE IF EXISTS organization_members;
			DROP TABLE IF EXISTS organizations;
		`,
	},
}

// Migrate runs all pending migrations
func (s *SQLiteDB) Migrate(ctx context.Context) error {
	// Create schema_version table if it doesn't exist
	if err := s.createSchemaVersionTable(ctx); err != nil {
		return fmt.Errorf("failed to create schema version table: %w", err)
	}
	
	// Get current version
	currentVersion, err := s.GetVersion(ctx)
	if err != nil {
		return fmt.Errorf("failed to get current version: %w", err)
	}
	
	logger.Debug("Current database version: %d", currentVersion)
	
	// Run pending migrations
	for _, migration := range migrations {
		if migration.Version <= currentVersion {
			continue
		}
		
		logger.Info("Running migration %d: %s", migration.Version, migration.Description)
		
		if err := s.runMigration(ctx, migration); err != nil {
			return fmt.Errorf("failed to run migration %d: %w", migration.Version, err)
		}
		
		logger.Info("Successfully applied migration %d", migration.Version)
	}
	
	return nil
}

// createSchemaVersionTable creates the schema version table if it doesn't exist
func (s *SQLiteDB) createSchemaVersionTable(ctx context.Context) error {
	query := `
		CREATE TABLE IF NOT EXISTS schema_version (
			version INTEGER PRIMARY KEY,
			description TEXT,
			applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`
	_, err := s.db.ExecContext(ctx, query)
	return err
}

// runMigration executes a single migration
func (s *SQLiteDB) runMigration(ctx context.Context, migration Migration) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	
	// Execute migration
	if _, err := tx.ExecContext(ctx, migration.Up); err != nil {
		return fmt.Errorf("failed to execute migration: %w", err)
	}
	
	// Record migration
	query := `INSERT INTO schema_version (version, description, applied_at) VALUES (?, ?, ?)`
	if _, err := tx.ExecContext(ctx, query, migration.Version, migration.Description, time.Now()); err != nil {
		return fmt.Errorf("failed to record migration: %w", err)
	}
	
	return tx.Commit()
}

// Rollback rolls back to a specific version
func (s *SQLiteDB) Rollback(ctx context.Context, targetVersion int) error {
	currentVersion, err := s.GetVersion(ctx)
	if err != nil {
		return fmt.Errorf("failed to get current version: %w", err)
	}
	
	if targetVersion >= currentVersion {
		return fmt.Errorf("target version %d is not less than current version %d", targetVersion, currentVersion)
	}
	
	// Roll back migrations in reverse order
	for i := len(migrations) - 1; i >= 0; i-- {
		migration := migrations[i]
		
		if migration.Version <= targetVersion || migration.Version > currentVersion {
			continue
		}
		
		logger.Info("Rolling back migration %d: %s", migration.Version, migration.Description)
		
		tx, err := s.db.BeginTx(ctx, nil)
		if err != nil {
			return err
		}
		defer tx.Rollback()
		
		// Execute rollback
		if _, err := tx.ExecContext(ctx, migration.Down); err != nil {
			return fmt.Errorf("failed to rollback migration %d: %w", migration.Version, err)
		}
		
		// Remove migration record
		query := `DELETE FROM schema_version WHERE version = ?`
		if _, err := tx.ExecContext(ctx, query, migration.Version); err != nil {
			return fmt.Errorf("failed to remove migration record: %w", err)
		}
		
		if err := tx.Commit(); err != nil {
			return err
		}
		
		logger.Info("Successfully rolled back migration %d", migration.Version)
	}
	
	return nil
}