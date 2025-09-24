package migration

import (
	"context"
	"embed"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

//go:embed all:*.sql
var migrationFiles embed.FS

// Manager handles database migrations
type Manager struct {
	db         *sqlx.DB
	migrations []Migration
}

// Migration represents a single migration
type Migration struct {
	Version   int
	Name      string
	UpSQL     string
	DownSQL   string
	AppliedAt *time.Time
}

// NewManager creates a new migration manager
func NewManager(db *sqlx.DB) (*Manager, error) {
	m := &Manager{
		db: db,
	}

	// Create migrations table if not exists
	if err := m.createMigrationsTable(); err != nil {
		return nil, fmt.Errorf("failed to create migrations table: %w", err)
	}

	// Load migrations from embedded files
	if err := m.loadMigrations(); err != nil {
		return nil, fmt.Errorf("failed to load migrations: %w", err)
	}

	return m, nil
}

// createMigrationsTable creates the schema_migrations table
func (m *Manager) createMigrationsTable() error {
	query := `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version INTEGER PRIMARY KEY,
			name VARCHAR(255) NOT NULL,
			applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
		)
	`
	_, err := m.db.Exec(query)
	return err
}

// loadMigrations loads migration files from embedded filesystem
func (m *Manager) loadMigrations() error {
	entries, err := migrationFiles.ReadDir(".")
	if err != nil {
		return fmt.Errorf("failed to read migration files: %w", err)
	}

	migrations := make(map[int]*Migration)

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		name := entry.Name()
		if !strings.HasSuffix(name, ".sql") {
			continue
		}

		// Parse migration version and direction from filename
		// Format: 001_migration_name.up.sql or 001_migration_name.down.sql
		parts := strings.Split(name, "_")
		if len(parts) < 2 {
			continue
		}

		var version int
		if _, err := fmt.Sscanf(parts[0], "%03d", &version); err != nil {
			logger.Warn("Skipping file %s: invalid version format", name)
			continue
		}

		// Read file content
		content, err := migrationFiles.ReadFile(name)
		if err != nil {
			return fmt.Errorf("failed to read migration file %s: %w", name, err)
		}

		// Get or create migration
		if _, exists := migrations[version]; !exists {
			migrations[version] = &Migration{
				Version: version,
				Name:    strings.TrimSuffix(name, ".up.sql"),
			}
		}

		// Set up or down SQL
		if strings.Contains(name, ".up.sql") {
			migrations[version].UpSQL = string(content)
		} else if strings.Contains(name, ".down.sql") {
			migrations[version].DownSQL = string(content)
		}
	}

	// Convert map to sorted slice
	for _, mig := range migrations {
		m.migrations = append(m.migrations, *mig)
	}

	// Sort by version
	sort.Slice(m.migrations, func(i, j int) bool {
		return m.migrations[i].Version < m.migrations[j].Version
	})

	return nil
}

// Up runs all pending migrations
func (m *Manager) Up(ctx context.Context) error {
	applied, err := m.getAppliedMigrations()
	if err != nil {
		return fmt.Errorf("failed to get applied migrations: %w", err)
	}

	pending := m.getPendingMigrations(applied)
	if len(pending) == 0 {
		logger.Info("No pending migrations")
		return nil
	}

	logger.Info("Found %d pending migrations", len(pending))

	for _, mig := range pending {
		if err := m.runMigration(ctx, mig, true); err != nil {
			return fmt.Errorf("failed to run migration %d: %w", mig.Version, err)
		}
	}

	return nil
}

// Down rolls back the last migration
func (m *Manager) Down(ctx context.Context) error {
	applied, err := m.getAppliedMigrations()
	if err != nil {
		return fmt.Errorf("failed to get applied migrations: %w", err)
	}

	if len(applied) == 0 {
		logger.Info("No migrations to roll back")
		return nil
	}

	// Get the last applied migration
	lastVersion := 0
	for v := range applied {
		if v > lastVersion {
			lastVersion = v
		}
	}

	// Find the migration
	var migration *Migration
	for _, mig := range m.migrations {
		if mig.Version == lastVersion {
			migration = &mig
			break
		}
	}

	if migration == nil {
		return fmt.Errorf("migration %d not found", lastVersion)
	}

	return m.runMigration(ctx, *migration, false)
}

// runMigration executes a single migration
func (m *Manager) runMigration(ctx context.Context, mig Migration, up bool) error {
	tx, err := m.db.BeginTxx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to start transaction: %w", err)
	}
	defer tx.Rollback()

	var sqlContent string
	if up {
		sqlContent = mig.UpSQL
		logger.Info("Applying migration %d: %s", mig.Version, mig.Name)
	} else {
		sqlContent = mig.DownSQL
		logger.Info("Rolling back migration %d: %s", mig.Version, mig.Name)
	}

	if sqlContent == "" {
		return fmt.Errorf("migration %d has no %s SQL", mig.Version, map[bool]string{true: "up", false: "down"}[up])
	}

	// Execute migration SQL
	if _, err := tx.ExecContext(ctx, sqlContent); err != nil {
		return fmt.Errorf("failed to execute migration SQL: %w", err)
	}

	// Update migrations table
	if up {
		query := `INSERT INTO schema_migrations (version, name) VALUES ($1, $2)`
		if _, err := tx.ExecContext(ctx, query, mig.Version, mig.Name); err != nil {
			return fmt.Errorf("failed to record migration: %w", err)
		}
	} else {
		query := `DELETE FROM schema_migrations WHERE version = $1`
		if _, err := tx.ExecContext(ctx, query, mig.Version); err != nil {
			return fmt.Errorf("failed to remove migration record: %w", err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	if up {
		logger.Info("Successfully applied migration %d", mig.Version)
	} else {
		logger.Info("Successfully rolled back migration %d", mig.Version)
	}

	return nil
}

// getAppliedMigrations returns a map of applied migration versions
func (m *Manager) getAppliedMigrations() (map[int]time.Time, error) {
	query := `SELECT version, applied_at FROM schema_migrations`
	rows, err := m.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query migrations: %w", err)
	}
	defer rows.Close()

	applied := make(map[int]time.Time)
	for rows.Next() {
		var version int
		var appliedAt time.Time
		if err := rows.Scan(&version, &appliedAt); err != nil {
			return nil, fmt.Errorf("failed to scan migration row: %w", err)
		}
		applied[version] = appliedAt
	}

	return applied, nil
}

// getPendingMigrations returns migrations that haven't been applied
func (m *Manager) getPendingMigrations(applied map[int]time.Time) []Migration {
	var pending []Migration
	for _, mig := range m.migrations {
		if _, isApplied := applied[mig.Version]; !isApplied {
			pending = append(pending, mig)
		}
	}
	return pending
}

// Status shows the current migration status
func (m *Manager) Status() error {
	applied, err := m.getAppliedMigrations()
	if err != nil {
		return fmt.Errorf("failed to get applied migrations: %w", err)
	}

	fmt.Println("Migration Status:")
	fmt.Println("-----------------")

	for _, mig := range m.migrations {
		status := "pending"
		appliedAt := ""
		if t, isApplied := applied[mig.Version]; isApplied {
			status = "applied"
			appliedAt = t.Format("2006-01-02 15:04:05")
		}
		fmt.Printf("%03d | %-50s | %-8s | %s\n", mig.Version, mig.Name, status, appliedAt)
	}

	pending := m.getPendingMigrations(applied)
	fmt.Printf("\nTotal: %d migrations, %d applied, %d pending\n",
		len(m.migrations), len(applied), len(pending))

	return nil
}

// Reset drops all tables and reruns all migrations
func (m *Manager) Reset(ctx context.Context) error {
	logger.Warn("WARNING: Resetting database - all data will be lost!")

	// Drop all tables
	query := `
		SELECT tablename
		FROM pg_tables
		WHERE schemaname = 'public'
		AND tablename != 'schema_migrations'
	`
	var tables []string
	err := m.db.Select(&tables, query)
	if err != nil {
		return fmt.Errorf("failed to get table list: %w", err)
	}

	for _, table := range tables {
		logger.Info("Dropping table %s", table)
		if _, err := m.db.Exec(fmt.Sprintf("DROP TABLE IF EXISTS %s CASCADE", table)); err != nil {
			return fmt.Errorf("failed to drop table %s: %w", table, err)
		}
	}

	// Clear migrations table
	if _, err := m.db.Exec("TRUNCATE schema_migrations"); err != nil {
		return fmt.Errorf("failed to clear migrations table: %w", err)
	}

	// Run all migrations
	return m.Up(ctx)
}

// Validate checks that all applied migrations match their files
func (m *Manager) Validate() error {
	applied, err := m.getAppliedMigrations()
	if err != nil {
		return fmt.Errorf("failed to get applied migrations: %w", err)
	}

	for version := range applied {
		found := false
		for _, mig := range m.migrations {
			if mig.Version == version {
				found = true
				break
			}
		}
		if !found {
			return fmt.Errorf("applied migration %d not found in files", version)
		}
	}

	logger.Info("All applied migrations are valid")
	return nil
}

// GetAppliedMigrations returns a map of applied migration versions (public method)
func (m *Manager) GetAppliedMigrations() (map[int]time.Time, error) {
	return m.getAppliedMigrations()
}

// GetMigrations returns all available migrations
func (m *Manager) GetMigrations() []Migration {
	return m.migrations
}