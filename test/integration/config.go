package integration

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"testing"
	"time"

	_ "github.com/lib/pq"
	"github.com/stretchr/testify/require"
)

// TestConfig holds test database configuration
type TestConfig struct {
	Host     string
	Port     string
	User     string
	Password string
	Database string
	SSLMode  string
}

// GetTestConfig returns test database configuration from environment
func GetTestConfig() *TestConfig {
	return &TestConfig{
		Host:     getEnv("TEST_DB_HOST", "localhost"),
		Port:     getEnv("TEST_DB_PORT", "5432"),
		User:     getEnv("TEST_DB_USER", "postgres"),
		Password: getEnv("TEST_DB_PASSWORD", "postgres"),
		Database: getEnv("TEST_DB_NAME", "arxos_test"),
		SSLMode:  getEnv("TEST_DB_SSLMODE", "disable"),
	}
}

// DSN returns PostgreSQL connection string
func (c *TestConfig) DSN() string {
	return fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		c.Host, c.Port, c.User, c.Password, c.Database, c.SSLMode,
	)
}

// SetupTestDB creates a test database connection with proper cleanup
func SetupTestDB(t *testing.T) *sql.DB {
	t.Helper()

	config := GetTestConfig()

	// Connect to database
	db, err := sql.Open("postgres", config.DSN())
	if err != nil {
		t.Skipf("Failed to connect to test database: %v (set TEST_DB_* env vars or use docker-compose)", err)
		return nil
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		t.Skipf("Test database not available: %v", err)
		return nil
	}

	// Set connection pool settings for tests
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Hour)

	// Register cleanup
	t.Cleanup(func() {
		if err := db.Close(); err != nil {
			t.Logf("Warning: failed to close test database: %v", err)
		}
	})

	t.Logf("Connected to test database: %s:%s/%s", config.Host, config.Port, config.Database)
	return db
}

// SetupTestDBWithTransaction creates a test database connection wrapped in a transaction
// The transaction will be rolled back on cleanup, ensuring test isolation
func SetupTestDBWithTransaction(t *testing.T) (*sql.DB, *sql.Tx) {
	t.Helper()

	db := SetupTestDB(t)
	if db == nil {
		return nil, nil
	}

	// Start transaction for test isolation
	tx, err := db.BeginTx(context.Background(), nil)
	require.NoError(t, err, "Failed to start test transaction")

	// Register rollback on cleanup
	t.Cleanup(func() {
		if err := tx.Rollback(); err != nil && err != sql.ErrTxDone {
			t.Logf("Warning: failed to rollback test transaction: %v", err)
		}
	})

	t.Log("Test transaction started (will rollback on cleanup)")
	return db, tx
}

// RunMigrations runs database migrations for tests
// Note: In production tests, migrations should already be run
func RunMigrations(t *testing.T, db *sql.DB) {
	t.Helper()

	// Check if migrations table exists
	var exists bool
	err := db.QueryRow(`
		SELECT EXISTS (
			SELECT FROM information_schema.tables 
			WHERE table_schema = 'public' 
			AND table_name = 'schema_migrations'
		)
	`).Scan(&exists)

	if err != nil {
		t.Logf("Warning: Could not check migrations: %v", err)
		return
	}

	if !exists {
		t.Skip("Database migrations not run. Run migrations first: make migrate-up")
	}

	t.Log("Database migrations verified")
}

// CleanupTestData removes test data from database
func CleanupTestData(t *testing.T, db *sql.DB, tables ...string) {
	t.Helper()

	if len(tables) == 0 {
		// Default cleanup order (respects foreign keys)
		tables = []string{
			"equipment",
			"rooms",
			"floors",
			"buildings",
			"bas_points",
			"bas_systems",
		}
	}

	for _, table := range tables {
		_, err := db.Exec(fmt.Sprintf("DELETE FROM %s WHERE true", table))
		if err != nil {
			t.Logf("Warning: failed to cleanup table %s: %v", table, err)
		}
	}

	t.Log("Test data cleaned up")
}

// Helper to get environment variable with default
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// IsTestDBAvailable checks if test database is available
func IsTestDBAvailable() bool {
	config := GetTestConfig()
	db, err := sql.Open("postgres", config.DSN())
	if err != nil {
		return false
	}
	defer db.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	return db.PingContext(ctx) == nil
}
