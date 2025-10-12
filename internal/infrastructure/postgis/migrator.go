package postgis

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// Migrator handles database migrations
type Migrator struct {
	db             *sql.DB
	migrationsPath string
}

// NewMigrator creates a new database migrator
func NewMigrator(db *sql.DB, migrationsPath string) *Migrator {
	return &Migrator{
		db:             db,
		migrationsPath: migrationsPath,
	}
}

// MigrationInfo holds information about a migration
type MigrationInfo struct {
	Version   int
	Name      string
	AppliedAt time.Time
}

// ensureMigrationsTable creates the schema_migrations table if it doesn't exist
func (m *Migrator) ensureMigrationsTable() error {
	query := `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version INTEGER PRIMARY KEY,
			name TEXT NOT NULL,
			applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);
	`
	_, err := m.db.Exec(query)
	return err
}

// GetCurrentVersion returns the current migration version
func (m *Migrator) GetCurrentVersion() (int, error) {
	if err := m.ensureMigrationsTable(); err != nil {
		return 0, err
	}

	var version int
	err := m.db.QueryRow("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").Scan(&version)
	if err != nil {
		return 0, err
	}
	return version, nil
}

// GetAppliedMigrations returns list of applied migrations
func (m *Migrator) GetAppliedMigrations() ([]MigrationInfo, error) {
	if err := m.ensureMigrationsTable(); err != nil {
		return nil, err
	}

	rows, err := m.db.Query("SELECT version, name, applied_at FROM schema_migrations ORDER BY version")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var migrations []MigrationInfo
	for rows.Next() {
		var m MigrationInfo
		if err := rows.Scan(&m.Version, &m.Name, &m.AppliedAt); err != nil {
			return nil, err
		}
		migrations = append(migrations, m)
	}
	return migrations, nil
}

// GetPendingMigrations returns list of pending migrations
func (m *Migrator) GetPendingMigrations() ([]string, error) {
	currentVersion, err := m.GetCurrentVersion()
	if err != nil {
		return nil, err
	}

	files, err := filepath.Glob(filepath.Join(m.migrationsPath, "*_*.up.sql"))
	if err != nil {
		return nil, err
	}

	var pending []string
	for _, file := range files {
		basename := filepath.Base(file)
		parts := strings.SplitN(basename, "_", 2)
		if len(parts) < 2 {
			continue
		}

		var version int
		if _, err := fmt.Sscanf(parts[0], "%d", &version); err != nil {
			continue
		}

		if version > currentVersion {
			pending = append(pending, file)
		}
	}

	sort.Strings(pending)
	return pending, nil
}

// Up runs all pending migrations
func (m *Migrator) Up(ctx context.Context) error {
	if err := m.ensureMigrationsTable(); err != nil {
		return fmt.Errorf("failed to ensure migrations table: %w", err)
	}

	pending, err := m.GetPendingMigrations()
	if err != nil {
		return fmt.Errorf("failed to get pending migrations: %w", err)
	}

	if len(pending) == 0 {
		return nil // No pending migrations
	}

	for _, file := range pending {
		if err := m.applyMigration(ctx, file); err != nil {
			return fmt.Errorf("failed to apply migration %s: %w", file, err)
		}
	}

	return nil
}

// applyMigration applies a single migration file
func (m *Migrator) applyMigration(ctx context.Context, file string) error {
	// Read migration file
	content, err := os.ReadFile(file)
	if err != nil {
		return fmt.Errorf("failed to read migration file: %w", err)
	}

	// Parse version and name from filename
	basename := filepath.Base(file)
	parts := strings.SplitN(basename, "_", 2)
	if len(parts) < 2 {
		return fmt.Errorf("invalid migration filename: %s", basename)
	}

	var version int
	if _, err := fmt.Sscanf(parts[0], "%d", &version); err != nil {
		return fmt.Errorf("invalid version in filename: %s", basename)
	}

	name := strings.TrimSuffix(parts[1], ".up.sql")

	// Start transaction
	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Execute migration
	if _, err := tx.ExecContext(ctx, string(content)); err != nil {
		return fmt.Errorf("failed to execute migration: %w", err)
	}

	// Record migration
	if _, err := tx.ExecContext(ctx,
		"INSERT INTO schema_migrations (version, name, applied_at) VALUES ($1, $2, $3)",
		version, name, time.Now()); err != nil {
		return fmt.Errorf("failed to record migration: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	fmt.Printf("✅ Applied migration %03d: %s\n", version, name)
	return nil
}

// Down rolls back the last applied migration
func (m *Migrator) Down(ctx context.Context) error {
	if err := m.ensureMigrationsTable(); err != nil {
		return fmt.Errorf("failed to ensure migrations table: %w", err)
	}

	// Get current version
	var version int
	var name string
	err := m.db.QueryRow("SELECT version, name FROM schema_migrations ORDER BY version DESC LIMIT 1").
		Scan(&version, &name)
	if err == sql.ErrNoRows {
		return fmt.Errorf("no migrations to roll back")
	}
	if err != nil {
		return fmt.Errorf("failed to get current migration: %w", err)
	}

	// Find down migration file
	downFile := filepath.Join(m.migrationsPath, fmt.Sprintf("%03d_*.down.sql", version))
	matches, err := filepath.Glob(downFile)
	if err != nil || len(matches) == 0 {
		return fmt.Errorf("down migration file not found for version %d", version)
	}

	// Read migration file
	content, err := os.ReadFile(matches[0])
	if err != nil {
		return fmt.Errorf("failed to read down migration: %w", err)
	}

	// Start transaction
	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Execute down migration
	if _, err := tx.ExecContext(ctx, string(content)); err != nil {
		return fmt.Errorf("failed to execute down migration: %w", err)
	}

	// Remove migration record
	if _, err := tx.ExecContext(ctx, "DELETE FROM schema_migrations WHERE version = $1", version); err != nil {
		return fmt.Errorf("failed to remove migration record: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	fmt.Printf("✅ Rolled back migration %03d: %s\n", version, name)
	return nil
}

// Status returns the current migration status
func (m *Migrator) Status() (current int, pending int, err error) {
	currentVersion, err := m.GetCurrentVersion()
	if err != nil {
		return 0, 0, err
	}

	pendingMigrations, err := m.GetPendingMigrations()
	if err != nil {
		return 0, 0, err
	}

	return currentVersion, len(pendingMigrations), nil
}
