package database

import (
	"database/sql"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/joelpate/arxos/internal/common/logger"
)

// Migration represents a database migration
type Migration struct {
	Version string
	Name    string
	UpSQL   string
	DownSQL string
}

// MigrationRunner handles database migrations
type MigrationRunner struct {
	db             *sql.DB
	migrationsPath string
}

// NewMigrationRunner creates a new migration runner
func NewMigrationRunner(db *sql.DB, migrationsPath string) *MigrationRunner {
	return &MigrationRunner{
		db:             db,
		migrationsPath: migrationsPath,
	}
}

// Run executes all pending migrations
func (m *MigrationRunner) Run() error {
	// Ensure migrations table exists
	if err := m.ensureMigrationsTable(); err != nil {
		return fmt.Errorf("failed to create migrations table: %w", err)
	}

	// Load all migrations
	migrations, err := m.loadMigrations()
	if err != nil {
		return fmt.Errorf("failed to load migrations: %w", err)
	}

	// Get applied migrations
	applied, err := m.getAppliedMigrations()
	if err != nil {
		return fmt.Errorf("failed to get applied migrations: %w", err)
	}

	// Apply pending migrations
	for _, migration := range migrations {
		if applied[migration.Version] {
			logger.Debug("Migration %s already applied", migration.Version)
			continue
		}

		logger.Info("Applying migration %s: %s", migration.Version, migration.Name)
		if err := m.applyMigration(migration); err != nil {
			return fmt.Errorf("failed to apply migration %s: %w", migration.Version, err)
		}
	}

	return nil
}

// Rollback rolls back the last n migrations
func (m *MigrationRunner) Rollback(n int) error {
	// Ensure migrations table exists
	if err := m.ensureMigrationsTable(); err != nil {
		return fmt.Errorf("failed to create migrations table: %w", err)
	}

	// Load all migrations
	migrations, err := m.loadMigrations()
	if err != nil {
		return fmt.Errorf("failed to load migrations: %w", err)
	}

	// Get applied migrations in reverse order
	appliedVersions, err := m.getAppliedMigrationsOrdered()
	if err != nil {
		return fmt.Errorf("failed to get applied migrations: %w", err)
	}

	// Create version to migration map
	migrationMap := make(map[string]*Migration)
	for _, m := range migrations {
		migrationMap[m.Version] = m
	}

	// Rollback migrations
	count := 0
	for i := len(appliedVersions) - 1; i >= 0 && count < n; i-- {
		version := appliedVersions[i]
		migration, exists := migrationMap[version]
		if !exists {
			logger.Warn("Migration %s not found in filesystem", version)
			continue
		}

		logger.Info("Rolling back migration %s: %s", migration.Version, migration.Name)
		if err := m.rollbackMigration(migration); err != nil {
			return fmt.Errorf("failed to rollback migration %s: %w", migration.Version, err)
		}
		count++
	}

	return nil
}

// Status returns the current migration status
func (m *MigrationRunner) Status() ([]MigrationStatus, error) {
	// Ensure migrations table exists
	if err := m.ensureMigrationsTable(); err != nil {
		return nil, fmt.Errorf("failed to create migrations table: %w", err)
	}

	// Load all migrations
	migrations, err := m.loadMigrations()
	if err != nil {
		return nil, fmt.Errorf("failed to load migrations: %w", err)
	}

	// Get applied migrations
	applied, err := m.getAppliedMigrations()
	if err != nil {
		return nil, fmt.Errorf("failed to get applied migrations: %w", err)
	}

	// Build status list
	var status []MigrationStatus
	for _, migration := range migrations {
		s := MigrationStatus{
			Version: migration.Version,
			Name:    migration.Name,
			Applied: applied[migration.Version],
		}
		status = append(status, s)
	}

	return status, nil
}

// MigrationStatus represents the status of a migration
type MigrationStatus struct {
	Version string
	Name    string
	Applied bool
}

// ensureMigrationsTable creates the migrations tracking table if it doesn't exist
func (m *MigrationRunner) ensureMigrationsTable() error {
	query := `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version TEXT PRIMARY KEY,
			name TEXT NOT NULL,
			applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`
	_, err := m.db.Exec(query)
	return err
}

// loadMigrations loads all migration files from the migrations directory
func (m *MigrationRunner) loadMigrations() ([]*Migration, error) {
	var migrations []*Migration

	// Check if migrations directory exists
	if _, err := os.Stat(m.migrationsPath); os.IsNotExist(err) {
		logger.Warn("Migrations directory does not exist: %s", m.migrationsPath)
		return migrations, nil
	}

	// Read migration files
	err := filepath.WalkDir(m.migrationsPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		if d.IsDir() {
			return nil
		}

		// Parse migration files (format: 001_migration_name.up.sql or 001_migration_name.down.sql)
		filename := d.Name()
		if !strings.HasSuffix(filename, ".sql") {
			return nil
		}

		parts := strings.Split(filename, "_")
		if len(parts) < 2 {
			return nil
		}

		version := parts[0]

		// Determine if this is an up or down migration
		isUp := strings.Contains(filename, ".up.sql")
		isDown := strings.Contains(filename, ".down.sql")

		if !isUp && !isDown {
			return nil
		}

		// Read file content
		content, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("failed to read migration file %s: %w", filename, err)
		}

		// Find or create migration
		var migration *Migration
		for _, m := range migrations {
			if m.Version == version {
				migration = m
				break
			}
		}

		if migration == nil {
			// Extract name from filename
			nameEnd := strings.LastIndex(filename, ".up.sql")
			if nameEnd < 0 {
				nameEnd = strings.LastIndex(filename, ".down.sql")
			}
			name := filename[len(version)+1 : nameEnd]

			migration = &Migration{
				Version: version,
				Name:    name,
			}
			migrations = append(migrations, migration)
		}

		// Set SQL content
		if isUp {
			migration.UpSQL = string(content)
		} else {
			migration.DownSQL = string(content)
		}

		return nil
	})

	if err != nil {
		return nil, err
	}

	// Sort migrations by version
	sort.Slice(migrations, func(i, j int) bool {
		return migrations[i].Version < migrations[j].Version
	})

	return migrations, nil
}

// getAppliedMigrations returns a map of applied migration versions
func (m *MigrationRunner) getAppliedMigrations() (map[string]bool, error) {
	applied := make(map[string]bool)

	query := `SELECT version FROM schema_migrations`
	rows, err := m.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var version string
		if err := rows.Scan(&version); err != nil {
			return nil, err
		}
		applied[version] = true
	}

	return applied, rows.Err()
}

// getAppliedMigrationsOrdered returns a list of applied migration versions in order
func (m *MigrationRunner) getAppliedMigrationsOrdered() ([]string, error) {
	var versions []string

	query := `SELECT version FROM schema_migrations ORDER BY version`
	rows, err := m.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var version string
		if err := rows.Scan(&version); err != nil {
			return nil, err
		}
		versions = append(versions, version)
	}

	return versions, rows.Err()
}

// applyMigration applies a single migration
func (m *MigrationRunner) applyMigration(migration *Migration) error {
	// Begin transaction
	tx, err := m.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Execute migration SQL
	if _, err := tx.Exec(migration.UpSQL); err != nil {
		return fmt.Errorf("failed to execute migration SQL: %w", err)
	}

	// Record migration
	query := `INSERT INTO schema_migrations (version, name) VALUES (?, ?)`
	if _, err := tx.Exec(query, migration.Version, migration.Name); err != nil {
		return fmt.Errorf("failed to record migration: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit migration: %w", err)
	}

	logger.Info("Successfully applied migration %s", migration.Version)
	return nil
}

// rollbackMigration rolls back a single migration
func (m *MigrationRunner) rollbackMigration(migration *Migration) error {
	// Begin transaction
	tx, err := m.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Execute rollback SQL
	if migration.DownSQL != "" {
		if _, err := tx.Exec(migration.DownSQL); err != nil {
			return fmt.Errorf("failed to execute rollback SQL: %w", err)
		}
	} else {
		logger.Warn("No rollback SQL for migration %s", migration.Version)
	}

	// Remove migration record
	query := `DELETE FROM schema_migrations WHERE version = ?`
	if _, err := tx.Exec(query, migration.Version); err != nil {
		return fmt.Errorf("failed to remove migration record: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit rollback: %w", err)
	}

	logger.Info("Successfully rolled back migration %s", migration.Version)
	return nil
}

// RunMigrations is a convenience function to run migrations
func RunMigrations(db *sql.DB, migrationsPath string) error {
	runner := NewMigrationRunner(db, migrationsPath)
	return runner.Run()
}

// GetMigrationStatus is a convenience function to get migration status
func GetMigrationStatus(db *sql.DB, migrationsPath string) ([]MigrationStatus, error) {
	runner := NewMigrationRunner(db, migrationsPath)
	return runner.Status()
}