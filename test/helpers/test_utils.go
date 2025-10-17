package helpers

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/jmoiron/sqlx"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestConfigFile creates a temporary config file for testing
func TestConfigFile(t *testing.T, content string) string {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "test-config.yml")

	err := os.WriteFile(configPath, []byte(content), 0644)
	require.NoError(t, err)

	return configPath
}

// TestServiceConfigFile creates a temporary service config file for testing
func TestServiceConfigFile(t *testing.T, serviceName, content string) string {
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")

	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	configPath := filepath.Join(servicesDir, serviceName+".yml")
	err = os.WriteFile(configPath, []byte(content), 0644)
	require.NoError(t, err)

	return configPath
}

// TestEnvironmentConfigFile creates a temporary environment config file for testing
func TestEnvironmentConfigFile(t *testing.T, environment, content string) string {
	tmpDir := t.TempDir()
	envDir := filepath.Join(tmpDir, "environments")

	err := os.MkdirAll(envDir, 0755)
	require.NoError(t, err)

	configPath := filepath.Join(envDir, environment+".yml")
	err = os.WriteFile(configPath, []byte(content), 0644)
	require.NoError(t, err)

	return configPath
}

// AssertConfigEqual asserts that two configurations are equal
func AssertConfigEqual(t *testing.T, expected, actual *config.Config) {
	assert.Equal(t, expected.Mode, actual.Mode)
	assert.Equal(t, expected.Version, actual.Version)
	assert.Equal(t, expected.StateDir, actual.StateDir)
	assert.Equal(t, expected.CacheDir, actual.CacheDir)

	// Cloud config
	assert.Equal(t, expected.Cloud.Enabled, actual.Cloud.Enabled)
	assert.Equal(t, expected.Cloud.BaseURL, actual.Cloud.BaseURL)
	assert.Equal(t, expected.Cloud.SyncEnabled, actual.Cloud.SyncEnabled)

	// PostGIS config
	assert.Equal(t, expected.PostGIS.Host, actual.PostGIS.Host)
	assert.Equal(t, expected.PostGIS.Port, actual.PostGIS.Port)
	assert.Equal(t, expected.PostGIS.Database, actual.PostGIS.Database)
	assert.Equal(t, expected.PostGIS.User, actual.PostGIS.User)
	assert.Equal(t, expected.PostGIS.SSLMode, actual.PostGIS.SSLMode)
	assert.Equal(t, expected.PostGIS.SRID, actual.PostGIS.SRID)

	// TUI config
	assert.Equal(t, expected.TUI.Enabled, actual.TUI.Enabled)
	assert.Equal(t, expected.TUI.Theme, actual.TUI.Theme)
	assert.Equal(t, expected.TUI.UpdateInterval, actual.TUI.UpdateInterval)

	// Security config
	assert.Equal(t, expected.Security.JWTExpiry, actual.Security.JWTExpiry)
	assert.Equal(t, expected.Security.EnableAuth, actual.Security.EnableAuth)
	assert.Equal(t, expected.Security.EnableTLS, actual.Security.EnableTLS)

	// Feature flags
	assert.Equal(t, expected.Features.CloudSync, actual.Features.CloudSync)
	assert.Equal(t, expected.Features.OfflineMode, actual.Features.OfflineMode)
	assert.Equal(t, expected.Features.BetaFeatures, actual.Features.BetaFeatures)
	assert.Equal(t, expected.Features.Analytics, actual.Features.Analytics)
}

// AssertConfigValid asserts that a configuration is valid
func AssertConfigValid(t *testing.T, cfg *config.Config) {
	err := cfg.Validate()
	assert.NoError(t, err, "Configuration should be valid")
}

// AssertConfigInvalid asserts that a configuration is invalid
func AssertConfigInvalid(t *testing.T, cfg *config.Config, expectedError string) {
	err := cfg.Validate()
	assert.Error(t, err, "Configuration should be invalid")
	if expectedError != "" {
		assert.Contains(t, err.Error(), expectedError)
	}
}

// TestEnvironment sets up environment variables for testing
func TestEnvironment(t *testing.T, envVars map[string]string) func() {
	// Store original values
	original := make(map[string]string)

	// Set test values
	for key, value := range envVars {
		original[key] = os.Getenv(key)
		os.Setenv(key, value)
	}

	// Return cleanup function
	return func() {
		// Restore original values
		for key, originalValue := range original {
			if originalValue == "" {
				os.Unsetenv(key)
			} else {
				os.Setenv(key, originalValue)
			}
		}
	}
}

// TestDirectory creates a temporary directory for testing
func TestDirectory(t *testing.T, name string) string {
	tmpDir := t.TempDir()
	testDir := filepath.Join(tmpDir, name)

	err := os.MkdirAll(testDir, 0755)
	require.NoError(t, err)

	return testDir
}

// TestFile creates a temporary file for testing
func TestFile(t *testing.T, name, content string) string {
	tmpDir := t.TempDir()
	filePath := filepath.Join(tmpDir, name)

	err := os.WriteFile(filePath, []byte(content), 0644)
	require.NoError(t, err)

	return filePath
}

// AssertFileExists asserts that a file exists
func AssertFileExists(t *testing.T, filePath string) {
	_, err := os.Stat(filePath)
	assert.NoError(t, err, "File should exist: %s", filePath)
}

// AssertFileNotExists asserts that a file does not exist
func AssertFileNotExists(t *testing.T, filePath string) {
	_, err := os.Stat(filePath)
	assert.Error(t, err, "File should not exist: %s", filePath)
}

// AssertDirectoryExists asserts that a directory exists
func AssertDirectoryExists(t *testing.T, dirPath string) {
	info, err := os.Stat(dirPath)
	assert.NoError(t, err, "Directory should exist: %s", dirPath)
	assert.True(t, info.IsDir(), "Path should be a directory: %s", dirPath)
}

// AssertDirectoryNotExists asserts that a directory does not exist
func AssertDirectoryNotExists(t *testing.T, dirPath string) {
	_, err := os.Stat(dirPath)
	assert.Error(t, err, "Directory should not exist: %s", dirPath)
}

// AssertFileContent asserts that a file contains expected content
func AssertFileContent(t *testing.T, filePath, expectedContent string) {
	content, err := os.ReadFile(filePath)
	require.NoError(t, err)
	assert.Equal(t, expectedContent, string(content))
}

// AssertFileContains asserts that a file contains expected content
func AssertFileContains(t *testing.T, filePath, expectedContent string) {
	content, err := os.ReadFile(filePath)
	require.NoError(t, err)
	assert.Contains(t, string(content), expectedContent)
}

// AssertFileNotContains asserts that a file does not contain expected content
func AssertFileNotContains(t *testing.T, filePath, unexpectedContent string) {
	content, err := os.ReadFile(filePath)
	require.NoError(t, err)
	assert.NotContains(t, string(content), unexpectedContent)
}

// TestConfigPath returns a test configuration path
func TestConfigPath(t *testing.T) string {
	tmpDir := t.TempDir()
	return filepath.Join(tmpDir, "test-config.yml")
}

// TestServiceConfigPath returns a test service configuration path
func TestServiceConfigPath(t *testing.T, serviceName string) string {
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")

	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	return filepath.Join(servicesDir, serviceName+".yml")
}

// TestEnvironmentConfigPath returns a test environment configuration path
func TestEnvironmentConfigPath(t *testing.T, environment string) string {
	tmpDir := t.TempDir()
	envDir := filepath.Join(tmpDir, "environments")

	err := os.MkdirAll(envDir, 0755)
	require.NoError(t, err)

	return filepath.Join(envDir, environment+".yml")
}

// FindTestConfigFile finds the test configuration file regardless of working directory
func FindTestConfigFile() (string, error) {
	// Try different possible locations for the test config file
	possiblePaths := []string{
		"test/config/test_config.yaml",  // From project root
		"../../config/test_config.yaml", // From test/integration/services
		"../config/test_config.yaml",    // From test/integration
		"config/test_config.yaml",       // From test directory
	}

	for _, path := range possiblePaths {
		if _, err := os.Stat(path); err == nil {
			return path, nil
		}
	}

	return "", os.ErrNotExist
}

// LoadTestConfig loads the test configuration file
func LoadTestConfig(t *testing.T) *config.Config {
	configPath, err := FindTestConfigFile()
	require.NoError(t, err, "Test config file not found")

	cfg, err := config.Load(configPath)
	require.NoError(t, err, "Failed to load test config")

	return cfg
}

// TestTimeout creates a context with a test timeout
func TestTimeout(t *testing.T, duration time.Duration) context.Context {
	timeout := duration
	if timeout == 0 {
		timeout = 30 * time.Second // Default test timeout
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	t.Cleanup(cancel)
	return ctx
}

// TestTimeoutShort creates a short timeout context for quick operations
func TestTimeoutShort(t *testing.T) context.Context {
	return TestTimeout(t, 10*time.Second)
}

// TestTimeoutLong creates a long timeout context for heavy operations
func TestTimeoutLong(t *testing.T) context.Context {
	return TestTimeout(t, 2*time.Minute)
}

// TestTimeoutVeryLong creates a very long timeout context for database migrations
func TestTimeoutVeryLong(t *testing.T) context.Context {
	return TestTimeout(t, 5*time.Minute)
}

// AssertNoTimeout asserts that a context hasn't timed out
func AssertNoTimeout(t *testing.T, ctx context.Context, operation string) {
	select {
	case <-ctx.Done():
		if ctx.Err() == context.DeadlineExceeded {
			t.Fatalf("Operation '%s' timed out: %v", operation, ctx.Err())
		}
		t.Fatalf("Operation '%s' was cancelled: %v", operation, ctx.Err())
	default:
		// Context is still valid
	}
}

// TestDatabaseSetup sets up a test database connection
func TestDatabaseSetup(t *testing.T) (context.Context, *sqlx.DB) {
	ctx := TestTimeoutLong(t)

	// Load test config
	cfg := LoadTestConfig(t)

	// Build connection string
	dsn := fmt.Sprintf("host=%s port=%d user=%s dbname=%s sslmode=%s password=%s",
		cfg.PostGIS.Host,
		cfg.PostGIS.Port,
		cfg.PostGIS.User,
		cfg.PostGIS.Database,
		cfg.PostGIS.SSLMode,
		cfg.PostGIS.Password,
	)

	// Connect to database
	db, err := sqlx.ConnectContext(ctx, "postgres", dsn)
	require.NoError(t, err, "Failed to connect to test database")

	// Test connection
	err = db.PingContext(ctx)
	require.NoError(t, err, "Failed to ping test database")

	// Set up cleanup
	t.Cleanup(func() {
		if err := db.Close(); err != nil {
			t.Logf("Warning: Failed to close database connection: %v", err)
		}
	})

	return ctx, db
}

// TestDatabaseCleanup cleans up test database
func TestDatabaseCleanup(t *testing.T, db *sqlx.DB) {
	ctx := TestTimeoutShort(t)

	// Drop all tables in public schema
	rows, err := db.QueryContext(ctx, `
		SELECT tablename FROM pg_tables
		WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%'
	`)
	require.NoError(t, err, "Failed to query tables")
	defer rows.Close()

	var tables []string
	for rows.Next() {
		var tableName string
		err := rows.Scan(&tableName)
		require.NoError(t, err, "Failed to scan table name")
		tables = append(tables, tableName)
	}

	// Drop tables
	for _, table := range tables {
		_, err := db.ExecContext(ctx, fmt.Sprintf("DROP TABLE IF EXISTS %s CASCADE", table))
		if err != nil {
			t.Logf("Warning: Failed to drop table %s: %v", table, err)
		}
	}
}

// SetupTestDB sets up a test database and returns cleanup function
func SetupTestDB(t *testing.T) (*sqlx.DB, func()) {
	_, db := TestDatabaseSetup(t)

	cleanup := func() {
		if db != nil {
			db.Close()
		}
	}

	return db, cleanup
}

// TestLogger is a simple logger for testing
type TestLogger struct{}

// NewTestLogger creates a new test logger
func NewTestLogger() *TestLogger {
	return &TestLogger{}
}

// Debug logs a debug message
func (l *TestLogger) Debug(msg string, fields ...any) {
	// Silent in tests
}

// Info logs an info message
func (l *TestLogger) Info(msg string, fields ...any) {
	// Silent in tests
}

// Warn logs a warning message
func (l *TestLogger) Warn(msg string, fields ...any) {
	// Silent in tests
}

// Error logs an error message
func (l *TestLogger) Error(msg string, fields ...any) {
	// Silent in tests
}

// Fatal logs a fatal message
func (l *TestLogger) Fatal(msg string, fields ...any) {
	// Silent in tests
}

// SetupTestEnvironment sets up test database and logger for integration tests
func SetupTestEnvironment(t *testing.T) (*sql.DB, func()) {
	cfg := &config.Config{
		Mode: "test",
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_test",
			User:     "arxos",
			Password: "",
			SSLMode:  "disable",
		},
	}

	dbInterface, err := infrastructure.NewDatabase(cfg)
	require.NoError(t, err, "Failed to connect to test database")

	// Get the underlying *sql.DB
	db, ok := dbInterface.(*infrastructure.Database)
	require.True(t, ok, "Failed to cast database to concrete type")

	cleanup := func() {
		if db != nil {
			db.GetDB().Close()
		}
	}

	return db.GetDB().DB, cleanup
}

// UniqueTestID generates a unique test ID using timestamp
func UniqueTestID() types.ID {
	return types.FromString(fmt.Sprintf("test-%d", time.Now().UnixNano()))
}

// RepositoryCollection holds all repositories for testing
type RepositoryCollection struct {
	BuildingRepo  domain.BuildingRepository
	FloorRepo     domain.FloorRepository
	RoomRepo      domain.RoomRepository
	EquipmentRepo domain.EquipmentRepository
	BranchRepo    domain.BranchRepository
	CommitRepo    domain.CommitRepository
	PRRepo        domain.PullRequestRepository
	IssueRepo     domain.IssueRepository
}

// SetupRepositories creates all repository instances for testing
func SetupRepositories(db *sql.DB) *RepositoryCollection {
	return &RepositoryCollection{
		BuildingRepo:  postgis.NewBuildingRepository(db),
		FloorRepo:     postgis.NewFloorRepository(db),
		RoomRepo:      postgis.NewRoomRepository(db),
		EquipmentRepo: postgis.NewEquipmentRepository(db),
		BranchRepo:    postgis.NewBranchRepository(db),
		CommitRepo:    postgis.NewCommitRepository(db),
		PRRepo:        postgis.NewPullRequestRepository(db),
		IssueRepo:     postgis.NewIssueRepository(db),
	}
}

// SetupBuildingUseCase creates a BuildingUseCase for testing
func SetupBuildingUseCase(repos *RepositoryCollection, logger domain.Logger) *usecase.BuildingUseCase {
	return usecase.NewBuildingUseCase(
		repos.BuildingRepo,
		repos.EquipmentRepo,
		logger,
	)
}

// SetupEquipmentUseCase creates an EquipmentUseCase for testing
func SetupEquipmentUseCase(repos *RepositoryCollection, logger domain.Logger) *usecase.EquipmentUseCase {
	return usecase.NewEquipmentUseCase(
		repos.EquipmentRepo,
		repos.BuildingRepo,
		repos.FloorRepo,
		repos.RoomRepo,
		logger,
	)
}

// SetupBranchUseCase creates a BranchUseCase for testing
func SetupBranchUseCase(repos *RepositoryCollection, logger domain.Logger) *usecase.BranchUseCase {
	return usecase.NewBranchUseCase(
		repos.BranchRepo,
		repos.CommitRepo,
		logger,
	)
}

// SetupCommitUseCase creates a CommitUseCase for testing
func SetupCommitUseCase(repos *RepositoryCollection, logger domain.Logger) *usecase.CommitUseCase {
	return usecase.NewCommitUseCase(
		repos.CommitRepo,
		repos.BranchRepo,
		logger,
	)
}

// SetupPullRequestUseCase creates a PullRequestUseCase for testing
func SetupPullRequestUseCase(repos *RepositoryCollection, db *sql.DB, logger domain.Logger) *usecase.PullRequestUseCase {
	return usecase.NewPullRequestUseCase(
		repos.PRRepo,
		repos.BranchRepo,
		repos.CommitRepo,
		nil, // PR assignment repo - not needed for basic testing
		logger,
	)
}

// SetupIssueUseCase creates an IssueUseCase for testing
func SetupIssueUseCase(
	repos *RepositoryCollection,
	prUC *usecase.PullRequestUseCase,
	branchUC *usecase.BranchUseCase,
	logger domain.Logger,
) *usecase.IssueUseCase {
	return usecase.NewIssueUseCase(
		repos.IssueRepo,
		branchUC,
		prUC,
		logger,
	)
}
