package database

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Migration represents a database migration
type Migration struct {
	Version     int
	Description string
	UpSQL       string
	DownSQL     string
	AppliedAt   *time.Time
}

// Migrator handles database migrations
type Migrator struct {
	db            *sql.DB
	migrations    []Migration
	migrationsDir string
}

// NewMigrator creates a new migrator instance
func NewMigrator(db *sql.DB, migrationsDir string) *Migrator {
	return &Migrator{
		db:            db,
		migrationsDir: migrationsDir,
	}
}

// LoadMigrations loads migration files from the migrations directory
func (m *Migrator) LoadMigrations() error {
	if m.migrationsDir == "" {
		return fmt.Errorf("migrations directory not specified")
	}

	// Read migration files
	files, err := os.ReadDir(m.migrationsDir)
	if err != nil {
		return fmt.Errorf("failed to read migrations directory: %w", err)
	}

	// Parse migration files
	migrationMap := make(map[int]*Migration)
	for _, file := range files {
		if file.IsDir() {
			continue
		}

		// Parse filename: 001_initial_schema.up.sql
		parts := strings.Split(file.Name(), "_")
		if len(parts) < 3 {
			continue
		}

		version, err := strconv.Atoi(parts[0])
		if err != nil {
			logger.Warn("Invalid migration filename: %s", file.Name())
			continue
		}

		// Get description from filename
		description := strings.Join(parts[1:len(parts)-2], "_") // Remove version and .up.sql/.down.sql
		if strings.HasSuffix(file.Name(), ".up.sql") {
			description = strings.TrimSuffix(description, ".up")
		} else if strings.HasSuffix(file.Name(), ".down.sql") {
			description = strings.TrimSuffix(description, ".down")
		}

		// Initialize migration if not exists
		if migrationMap[version] == nil {
			migrationMap[version] = &Migration{
				Version:     version,
				Description: description,
			}
		}

		// Read file content
		filePath := filepath.Join(m.migrationsDir, file.Name())
		content, err := os.ReadFile(filePath)
		if err != nil {
			return fmt.Errorf("failed to read migration file %s: %w", filePath, err)
		}

		// Assign content based on file type
		if strings.HasSuffix(file.Name(), ".up.sql") {
			migrationMap[version].UpSQL = string(content)
		} else if strings.HasSuffix(file.Name(), ".down.sql") {
			migrationMap[version].DownSQL = string(content)
		}
	}

	// Convert map to slice and sort by version
	m.migrations = make([]Migration, 0, len(migrationMap))
	for _, migration := range migrationMap {
		m.migrations = append(m.migrations, *migration)
	}
	sort.Slice(m.migrations, func(i, j int) bool {
		return m.migrations[i].Version < m.migrations[j].Version
	})

	logger.Info("Loaded %d migrations", len(m.migrations))
	return nil
}

// GetCurrentVersion returns the current database version
func (m *Migrator) GetCurrentVersion(ctx context.Context) (int, error) {
	// Create migrations table if it doesn't exist
	createTableSQL := `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version INTEGER PRIMARY KEY,
			description TEXT NOT NULL,
			applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			checksum VARCHAR(64)
		)`

	_, err := m.db.ExecContext(ctx, createTableSQL)
	if err != nil {
		return 0, fmt.Errorf("failed to create migrations table: %w", err)
	}

	// Get latest applied migration
	query := `SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1`
	var version int
	err = m.db.QueryRowContext(ctx, query).Scan(&version)
	if err != nil {
		if err == sql.ErrNoRows {
			return 0, nil // No migrations applied yet
		}
		return 0, fmt.Errorf("failed to get current version: %w", err)
	}

	return version, nil
}

// Migrate applies pending migrations
func (m *Migrator) Migrate(ctx context.Context) error {
	if len(m.migrations) == 0 {
		return fmt.Errorf("no migrations loaded")
	}

	currentVersion, err := m.GetCurrentVersion(ctx)
	if err != nil {
		return fmt.Errorf("failed to get current version: %w", err)
	}

	logger.Info("Current database version: %d", currentVersion)

	// Find pending migrations
	pendingMigrations := make([]Migration, 0)
	for _, migration := range m.migrations {
		if migration.Version > currentVersion {
			pendingMigrations = append(pendingMigrations, migration)
		}
	}

	if len(pendingMigrations) == 0 {
		logger.Info("Database is up to date")
		return nil
	}

	logger.Info("Applying %d pending migrations", len(pendingMigrations))

	// Apply each pending migration
	for _, migration := range pendingMigrations {
		if err := m.applyMigration(ctx, migration); err != nil {
			return fmt.Errorf("failed to apply migration %d: %w", migration.Version, err)
		}
		logger.Info("Applied migration %d: %s", migration.Version, migration.Description)
	}

	logger.Info("All migrations applied successfully")
	return nil
}

// applyMigration applies a single migration
func (m *Migrator) applyMigration(ctx context.Context, migration Migration) error {
	// Start transaction
	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to start transaction: %w", err)
	}
	defer tx.Rollback()

	// Execute migration SQL
	if migration.UpSQL == "" {
		return fmt.Errorf("no up SQL for migration %d", migration.Version)
	}

	// Split SQL into individual statements
	statements := m.splitSQL(migration.UpSQL)
	for _, statement := range statements {
		statement = strings.TrimSpace(statement)
		if statement == "" || strings.HasPrefix(statement, "--") {
			continue
		}

		_, err := tx.ExecContext(ctx, statement)
		if err != nil {
			return fmt.Errorf("failed to execute migration statement: %w\nStatement: %s", err, statement)
		}
	}

	// Record migration
	checksum := m.calculateChecksum(migration.UpSQL)
	_, err = tx.ExecContext(ctx,
		"INSERT INTO schema_migrations (version, description, checksum) VALUES ($1, $2, $3)",
		migration.Version, migration.Description, checksum,
	)
	if err != nil {
		return fmt.Errorf("failed to record migration: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit migration: %w", err)
	}

	return nil
}

// Rollback rolls back the last migration
func (m *Migrator) Rollback(ctx context.Context) error {
	currentVersion, err := m.GetCurrentVersion(ctx)
	if err != nil {
		return fmt.Errorf("failed to get current version: %w", err)
	}

	if currentVersion == 0 {
		return fmt.Errorf("no migrations to rollback")
	}

	// Find migration to rollback
	var migrationToRollback *Migration
	for _, migration := range m.migrations {
		if migration.Version == currentVersion {
			migrationToRollback = &migration
			break
		}
	}

	if migrationToRollback == nil {
		return fmt.Errorf("migration %d not found", currentVersion)
	}

	if migrationToRollback.DownSQL == "" {
		return fmt.Errorf("no down SQL for migration %d", currentVersion)
	}

	// Start transaction
	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to start transaction: %w", err)
	}
	defer tx.Rollback()

	// Execute rollback SQL
	statements := m.splitSQL(migrationToRollback.DownSQL)
	for _, statement := range statements {
		statement = strings.TrimSpace(statement)
		if statement == "" || strings.HasPrefix(statement, "--") {
			continue
		}

		_, err := tx.ExecContext(ctx, statement)
		if err != nil {
			return fmt.Errorf("failed to execute rollback statement: %w\nStatement: %s", err, statement)
		}
	}

	// Remove migration record
	_, err = tx.ExecContext(ctx, "DELETE FROM schema_migrations WHERE version = $1", currentVersion)
	if err != nil {
		return fmt.Errorf("failed to remove migration record: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit rollback: %w", err)
	}

	logger.Info("Rolled back migration %d: %s", currentVersion, migrationToRollback.Description)
	return nil
}

// GetMigrationStatus returns the status of all migrations
func (m *Migrator) GetMigrationStatus(ctx context.Context) ([]MigrationStatus, error) {
	// Get applied migrations
	appliedMigrations := make(map[int]time.Time)
	rows, err := m.db.QueryContext(ctx, "SELECT version, applied_at FROM schema_migrations ORDER BY version")
	if err != nil {
		return nil, fmt.Errorf("failed to query applied migrations: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var version int
		var appliedAt time.Time
		if err := rows.Scan(&version, &appliedAt); err != nil {
			return nil, fmt.Errorf("failed to scan migration: %w", err)
		}
		appliedMigrations[version] = appliedAt
	}

	// Build status list
	status := make([]MigrationStatus, len(m.migrations))
	for i, migration := range m.migrations {
		status[i] = MigrationStatus{
			Version:     migration.Version,
			Description: migration.Description,
			Applied:     false,
		}

		if appliedAt, exists := appliedMigrations[migration.Version]; exists {
			status[i].Applied = true
			status[i].AppliedAt = &appliedAt
		}
	}

	return status, nil
}

// MigrationStatus represents the status of a migration
type MigrationStatus struct {
	Version     int
	Description string
	Applied     bool
	AppliedAt   *time.Time
}

// splitSQL splits SQL content into individual statements
func (m *Migrator) splitSQL(sql string) []string {
	// Simple split on semicolon - in production, you'd want a proper SQL parser
	statements := strings.Split(sql, ";")
	result := make([]string, 0, len(statements))

	for _, stmt := range statements {
		stmt = strings.TrimSpace(stmt)
		if stmt != "" && !strings.HasPrefix(stmt, "--") {
			result = append(result, stmt)
		}
	}

	return result
}

// calculateChecksum calculates a simple checksum for migration content
func (m *Migrator) calculateChecksum(content string) string {
	// Simple checksum - in production, use a proper hash
	return fmt.Sprintf("%x", len(content))
}

// ValidateMigrations validates that all migrations are properly formatted
func (m *Migrator) ValidateMigrations() error {
	for _, migration := range m.migrations {
		if migration.UpSQL == "" {
			return fmt.Errorf("migration %d has no up SQL", migration.Version)
		}
		if migration.Description == "" {
			return fmt.Errorf("migration %d has no description", migration.Version)
		}
	}
	return nil
}

// GetPendingMigrations returns migrations that haven't been applied yet
func (m *Migrator) GetPendingMigrations(ctx context.Context) ([]Migration, error) {
	currentVersion, err := m.GetCurrentVersion(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get current version: %w", err)
	}

	pending := make([]Migration, 0)
	for _, migration := range m.migrations {
		if migration.Version > currentVersion {
			pending = append(pending, migration)
		}
	}

	return pending, nil
}
