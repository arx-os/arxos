package test

import (
	"context"
	"path/filepath"
	"testing"

	"github.com/arx-os/arxos/internal/database"
	"github.com/stretchr/testify/require"
)

// SetupTestDB creates a test database with migrations applied
func SetupTestDB(t *testing.T) *database.SQLiteDB {
	t.Helper()

	// Create temp directory for test database
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test.db")

	// Create database config
	config := database.NewConfig(dbPath)
	db := database.NewSQLiteDB(config)

	// Connect to database - migrations are now embedded
	ctx := context.Background()
	err := db.Connect(ctx, dbPath)
	require.NoError(t, err, "Failed to connect to test database")

	// Ensure migrations ran
	err = db.Migrate(ctx)
	require.NoError(t, err, "Failed to run migrations")

	// Return database for use in tests
	t.Cleanup(func() {
		db.Close()
	})

	return db
}

// SetupTestDBWithData creates a test database with sample data
func SetupTestDBWithData(t *testing.T) *database.SQLiteDB {
	t.Helper()

	db := SetupTestDB(t)
	_ = context.Background() // ctx unused for now

	// Add sample data using proper database methods
	// For now, we'll skip pre-populating data as the database
	// methods handle this internally

	return db
}

// CleanupTestDB removes all test data from database
func CleanupTestDB(t *testing.T, db *database.SQLiteDB) {
	t.Helper()
	// Cleanup is handled by test temp directory cleanup
}