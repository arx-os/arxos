package config

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewConfigMigrator(t *testing.T) {
	migrator := NewConfigMigrator("test-configs")
	assert.Equal(t, "test-configs", migrator.configDir)
}

func TestMigrateConfig(t *testing.T) {
	// Create temporary directories
	tmpDir := t.TempDir()
	sourceDir := filepath.Join(tmpDir, "source")
	targetDir := filepath.Join(tmpDir, "target")

	err := os.MkdirAll(sourceDir, 0755)
	require.NoError(t, err)
	err = os.MkdirAll(targetDir, 0755)
	require.NoError(t, err)

	// Create source config file
	sourceConfig := `mode: local
version: "0.1.0"
state_dir: ".arxos"
cache_dir: ".arxos/cache"
postgis:
  host: localhost
  port: 5432
  database: arxos
  user: arxos
  ssl_mode: disable`

	sourcePath := filepath.Join(sourceDir, "config.yml")
	err = os.WriteFile(sourcePath, []byte(sourceConfig), 0644)
	require.NoError(t, err)

	targetPath := filepath.Join(targetDir, "migrated-config.yml")

	// Test migration
	migrator := NewConfigMigrator(tmpDir)
	result, err := migrator.MigrateConfig(sourcePath, targetPath)
	require.NoError(t, err)

	// Verify migration result
	assert.True(t, result.Success)
	assert.Equal(t, sourcePath, result.SourcePath)
	assert.Equal(t, targetPath, result.TargetPath)
	assert.Empty(t, result.Error)
	// No changes expected - config is already in new format
	// Changes only occur when migrating from old format or when path contains specific keywords

	// Verify target file was created
	assert.FileExists(t, targetPath)

	// Verify migrated content
	data, err := os.ReadFile(targetPath)
	require.NoError(t, err)
	content := string(data)
	assert.Contains(t, content, "mode: local")
	// YAML marshaling may or may not include quotes - just check version exists
	assert.Contains(t, content, "version:")
	assert.Contains(t, content, "0.1.0")
	assert.Contains(t, content, "postgis:")
}

func TestMigrateConfig_SourceNotFound(t *testing.T) {
	tmpDir := t.TempDir()
	migrator := NewConfigMigrator(tmpDir)

	sourcePath := filepath.Join(tmpDir, "nonexistent.yml")
	targetPath := filepath.Join(tmpDir, "target.yml")

	result, err := migrator.MigrateConfig(sourcePath, targetPath)
	// Migration returns the error, so we should get an error
	require.Error(t, err)

	// Verify failure result
	assert.False(t, result.Success)
	assert.Error(t, result.Error)
	assert.Contains(t, result.Error.Error(), "source file does not exist")
}

func TestMigrateConfig_InvalidYAML(t *testing.T) {
	// Create temporary directories
	tmpDir := t.TempDir()
	sourceDir := filepath.Join(tmpDir, "source")
	targetDir := filepath.Join(tmpDir, "target")

	err := os.MkdirAll(sourceDir, 0755)
	require.NoError(t, err)
	err = os.MkdirAll(targetDir, 0755)
	require.NoError(t, err)

	// Create invalid YAML file
	invalidYAML := `mode: local
version: "0.1.0"
state_dir: ".arxos"
cache_dir: ".arxos/cache"
postgis:
  host: localhost
  port: 5432
  database: arxos
  user: arxos
  ssl_mode: disable
invalid_yaml: [unclosed`

	sourcePath := filepath.Join(sourceDir, "config.yml")
	err = os.WriteFile(sourcePath, []byte(invalidYAML), 0644)
	require.NoError(t, err)

	targetPath := filepath.Join(targetDir, "migrated-config.yml")

	// Test migration with invalid YAML
	migrator := NewConfigMigrator(tmpDir)
	result, err := migrator.MigrateConfig(sourcePath, targetPath)
	// Migration returns the error when YAML is invalid
	require.Error(t, err)

	// Verify failure result
	assert.False(t, result.Success)
	assert.Error(t, result.Error)
	assert.Contains(t, result.Error.Error(), "failed to parse source file")
}

func TestMigrateAllConfigs(t *testing.T) {
	// Create temporary directory structure
	tmpDir := t.TempDir()

	// Create environment configs
	envDir := filepath.Join(tmpDir, "environments")
	err := os.MkdirAll(envDir, 0755)
	require.NoError(t, err)

	// Create service configs
	servicesDir := filepath.Join(tmpDir, "services")
	err = os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	// Create development config
	devConfig := `mode: local
version: "0.1.0"
state_dir: ".arxos"
cache_dir: ".arxos/cache"`

	err = os.WriteFile(filepath.Join(envDir, "development.yml"), []byte(devConfig), 0644)
	require.NoError(t, err)

	// Create postgis service config
	postgisConfig := `postgis:
  host: localhost
  port: 5432
  database: arxos_dev
  user: arxos
  ssl_mode: disable`

	err = os.WriteFile(filepath.Join(servicesDir, "postgis.yml"), []byte(postgisConfig), 0644)
	require.NoError(t, err)

	// Test migration
	migrator := NewConfigMigrator(tmpDir)
	results, err := migrator.MigrateAllConfigs()
	require.NoError(t, err)

	// Verify results
	assert.Len(t, results, 1) // Only postgis service config should be migrated
	assert.True(t, results[0].Success)
	assert.Contains(t, results[0].SourcePath, "postgis.yml")
	assert.Contains(t, results[0].TargetPath, "postgis.yml")
}

func TestMigrateEnvironmentConfig(t *testing.T) {
	// Create temporary directory
	tmpDir := t.TempDir()
	migrator := NewConfigMigrator(tmpDir)

	// Test config with hybrid mode (should be changed to local)
	config := map[string]any{
		"mode": "hybrid",
	}

	_, changes := migrator.migrateEnvironmentConfig(config)

	// Verify changes
	assert.Contains(t, changes, "Changed mode from 'hybrid' to 'local'")
	assert.Equal(t, "local", config["mode"])

	// Test config with missing required fields
	config = map[string]any{
		"mode": "local",
	}

	_, changes = migrator.migrateEnvironmentConfig(config)

	// Verify changes
	assert.Contains(t, changes, "Added default version")
	assert.Contains(t, changes, "Added default state_dir")
	assert.Contains(t, changes, "Added default cache_dir")
	assert.Equal(t, "0.1.0", config["version"])
	assert.Equal(t, ".arxos", config["state_dir"])
	assert.Equal(t, ".arxos/cache", config["cache_dir"])
}

func TestMigratePostGISConfig(t *testing.T) {
	// Create temporary directory
	tmpDir := t.TempDir()
	migrator := NewConfigMigrator(tmpDir)

	// Test config with missing postgis section
	config := map[string]any{
		"mode": "local",
	}

	_, changes := migrator.migratePostGISConfig(config)

	// Verify changes
	assert.Contains(t, changes, "Added postgis section")
	assert.Contains(t, changes, "Added default PostGIS host")
	assert.Contains(t, changes, "Added default PostGIS port")
	assert.Contains(t, changes, "Added default PostGIS database")
	assert.Contains(t, changes, "Added default PostGIS user")
	assert.Contains(t, changes, "Added default PostGIS SSL mode")
	assert.Contains(t, changes, "Added default PostGIS SRID")

	// Verify postgis section was created
	postgis, ok := config["postgis"].(map[string]any)
	require.True(t, ok)
	assert.Equal(t, "localhost", postgis["host"])
	assert.Equal(t, 5432, postgis["port"])
	assert.Equal(t, "arxos", postgis["database"])
	assert.Equal(t, "arxos", postgis["user"])
	assert.Equal(t, "disable", postgis["ssl_mode"])
	assert.Equal(t, 900913, postgis["srid"])
}

func TestMigrateRedisConfig(t *testing.T) {
	// Create temporary directory
	tmpDir := t.TempDir()
	migrator := NewConfigMigrator(tmpDir)

	// Test config with missing redis section
	config := map[string]any{
		"mode": "local",
	}

	_, changes := migrator.migrateRedisConfig(config)

	// Verify changes
	assert.Contains(t, changes, "Added redis section")
	assert.Contains(t, changes, "Added default Redis host")
	assert.Contains(t, changes, "Added default Redis port")
	assert.Contains(t, changes, "Added default Redis database")

	// Verify redis section was created
	redis, ok := config["redis"].(map[string]any)
	require.True(t, ok)
	assert.Equal(t, "localhost", redis["host"])
	assert.Equal(t, 6379, redis["port"])
	assert.Equal(t, 0, redis["db"])
}

func TestMigrateIFCConfig(t *testing.T) {
	// Create temporary directory
	tmpDir := t.TempDir()
	migrator := NewConfigMigrator(tmpDir)

	// Test config with missing ifc_service section
	config := map[string]any{
		"mode": "local",
	}

	_, changes := migrator.migrateIFCConfig(config)

	// Verify changes
	assert.Contains(t, changes, "Added ifc_service section")
	assert.Contains(t, changes, "Added default IFC service enabled")
	assert.Contains(t, changes, "Added default IFC service URL")
	assert.Contains(t, changes, "Added default IFC service timeout")
	assert.Contains(t, changes, "Added default IFC service retries")

	// Verify ifc_service section was created
	ifc, ok := config["ifc_service"].(map[string]any)
	require.True(t, ok)
	assert.Equal(t, true, ifc["enabled"])
	assert.Equal(t, "http://localhost:5000", ifc["url"])
	assert.Equal(t, "30s", ifc["timeout"])
	assert.Equal(t, 3, ifc["retries"])
}

func TestMigrateConfigData(t *testing.T) {
	// Create temporary directory
	tmpDir := t.TempDir()
	migrator := NewConfigMigrator(tmpDir)

	// Test migration with development config
	source := map[string]any{
		"mode": "hybrid",
		"postgis": map[string]any{
			"host": "localhost",
			"port": 5432,
		},
	}

	migrated, _, changes, err := migrator.migrateConfigData(source, "development.yml")
	require.NoError(t, err)

	// Verify changes were applied
	assert.Contains(t, changes, "Changed mode from 'hybrid' to 'local'")
	assert.Equal(t, "local", migrated["mode"])

	// Test migration with postgis config
	source = map[string]any{
		"postgis": map[string]any{
			"host": "localhost",
		},
	}

	migrated, _, _, err = migrator.migrateConfigData(source, "postgis.yml")
	require.NoError(t, err)

	// Verify postgis defaults were added
	postgis, ok := migrated["postgis"].(map[string]any)
	require.True(t, ok)
	assert.Equal(t, "localhost", postgis["host"])
	assert.Equal(t, 5432, postgis["port"])        // Default added
	assert.Equal(t, "arxos", postgis["database"]) // Default added
}
