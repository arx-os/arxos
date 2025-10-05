package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestDefaultConfig(t *testing.T) {
	config := Default()

	assert.Equal(t, ModeLocal, config.Mode)
	assert.Equal(t, "0.1.0", config.Version)
	assert.NotEmpty(t, config.StateDir)
	assert.NotEmpty(t, config.CacheDir)

	assert.False(t, config.Cloud.Enabled)
	assert.Equal(t, "https://api.arxos.io", config.Cloud.BaseURL)

	assert.Equal(t, "local", config.Storage.Backend)
	assert.NotEmpty(t, config.Storage.LocalPath)

	assert.Equal(t, 30*time.Second, config.API.Timeout)
	assert.Equal(t, 3, config.API.RetryAttempts)

	assert.False(t, config.Telemetry.Enabled)
	assert.False(t, config.Features.CloudSync)
	assert.True(t, config.Features.OfflineMode)
}

func TestLoadFromFile(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "test-config.json")

	testConfig := &Config{
		Mode:     ModeCloud,
		Version:  "1.0.0",
		StateDir: "/test/state",
		CacheDir: "/test/cache",
		Cloud: CloudConfig{
			Enabled: true,
			BaseURL: "https://test.arxos.io",
			APIKey:  "test-key-123",
			OrgID:   "org-456",
		},
		Storage: StorageConfig{
			Backend:     "s3",
			CloudBucket: "test-bucket",
			CloudRegion: "us-east-1",
		},
		Features: FeatureFlags{
			CloudSync:     true,
			AIIntegration: true,
		},
	}

	// Write test config to file
	data, err := json.Marshal(testConfig)
	require.NoError(t, err)
	err = os.WriteFile(configPath, data, 0644)
	require.NoError(t, err)

	// Load config from file
	config := Default()
	err = config.LoadFromFile(configPath)
	require.NoError(t, err)

	assert.Equal(t, ModeCloud, config.Mode)
	assert.Equal(t, "1.0.0", config.Version)
	assert.Equal(t, "/test/state", config.StateDir)
	assert.True(t, config.Cloud.Enabled)
	assert.Equal(t, "https://test.arxos.io", config.Cloud.BaseURL)
	// APIKey is not serialized to JSON (json:"-" tag) so it won't round-trip
	assert.Equal(t, "", config.Cloud.APIKey)
	assert.Equal(t, "s3", config.Storage.Backend)
	assert.Equal(t, "test-bucket", config.Storage.CloudBucket)
	assert.True(t, config.Features.CloudSync)
	assert.True(t, config.Features.AIIntegration)
}

func TestLoadFromEnv(t *testing.T) {
	// Set environment variables
	os.Setenv("ARXOS_MODE", "cloud")
	os.Setenv("ARXOS_CLOUD_URL", "https://env.arxos.io")
	os.Setenv("ARXOS_API_KEY", "env-key-789")
	os.Setenv("ARXOS_ORG_ID", "env-org-123")
	os.Setenv("ARXOS_STORAGE_BACKEND", "gcs")
	os.Setenv("ARXOS_STORAGE_BUCKET", "env-bucket")
	os.Setenv("ARXOS_STORAGE_REGION", "us-central1")
	os.Setenv("ARXOS_CLOUD_SYNC", "true")
	os.Setenv("ARXOS_AI_ENABLED", "true")
	os.Setenv("ARXOS_TELEMETRY", "true")

	defer func() {
		// Clean up environment variables
		os.Unsetenv("ARXOS_MODE")
		os.Unsetenv("ARXOS_CLOUD_URL")
		os.Unsetenv("ARXOS_API_KEY")
		os.Unsetenv("ARXOS_ORG_ID")
		os.Unsetenv("ARXOS_STORAGE_BACKEND")
		os.Unsetenv("ARXOS_STORAGE_BUCKET")
		os.Unsetenv("ARXOS_STORAGE_REGION")
		os.Unsetenv("ARXOS_CLOUD_SYNC")
		os.Unsetenv("ARXOS_AI_ENABLED")
		os.Unsetenv("ARXOS_TELEMETRY")
	}()

	config := Default()
	config.LoadFromEnv()

	assert.Equal(t, ModeCloud, config.Mode)
	assert.Equal(t, "https://env.arxos.io", config.Cloud.BaseURL)
	assert.Equal(t, "env-key-789", config.Cloud.APIKey)
	assert.Equal(t, "env-org-123", config.Cloud.OrgID)
	assert.Equal(t, "gcs", config.Storage.Backend)
	assert.Equal(t, "env-bucket", config.Storage.CloudBucket)
	assert.Equal(t, "us-central1", config.Storage.CloudRegion)
	assert.True(t, config.Features.CloudSync)
	assert.True(t, config.Cloud.Enabled)
	assert.True(t, config.Features.AIIntegration)
	assert.True(t, config.Telemetry.Enabled)
}

func TestValidate(t *testing.T) {
	tests := []struct {
		name    string
		config  *Config
		wantErr bool
		errMsg  string
	}{
		{
			name:    "valid local config",
			config:  Default(),
			wantErr: false,
		},
		{
			name: "valid cloud config",
			config: &Config{
				Mode: ModeCloud,
				Cloud: CloudConfig{
					Enabled: true,
					BaseURL: "https://api.arxos.io",
					APIKey:  "test-key",
				},
				Storage: StorageConfig{
					Backend:     "s3",
					CloudBucket: "test-bucket",
				},
				Database: DatabaseConfig{
					Type:           "postgis",
					DataSourceName: "postgres://localhost/arxos?sslmode=disable",
				},
				PostGIS: PostGISConfig{
					Host:     "localhost",
					Port:     5432,
					Database: "arxos",
					User:     "arxos",
					Password: "test",
				},
				Security: SecurityConfig{
					JWTSecret: "test-jwt-secret-123",
				},
				TUI: TUIConfig{
					Enabled:             true,
					Theme:               "dark",
					UpdateInterval:      "1s",
					MaxEquipmentDisplay: 1000,
				},
			},
			wantErr: false,
		},
		{
			name: "invalid mode",
			config: &Config{
				Mode:    "invalid",
				Storage: StorageConfig{Backend: "local"},
			},
			wantErr: true,
			errMsg:  "invalid mode",
		},
		{
			name: "cloud mode without URL",
			config: &Config{
				Mode: ModeCloud,
				Cloud: CloudConfig{
					Enabled: true,
					BaseURL: "",
				},
				Storage: StorageConfig{Backend: "local"},
			},
			wantErr: true,
			errMsg:  "cloud URL required",
		},
		{
			name: "invalid storage backend",
			config: &Config{
				Mode: ModeLocal,
				Storage: StorageConfig{
					Backend: "invalid",
				},
			},
			wantErr: true,
			errMsg:  "invalid storage backend",
		},
		{
			name: "cloud storage without bucket",
			config: &Config{
				Mode: ModeLocal,
				Storage: StorageConfig{
					Backend:     "s3",
					CloudBucket: "",
				},
			},
			wantErr: true,
			errMsg:  "cloud bucket required",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.config.Validate()
			if tt.wantErr {
				assert.Error(t, err)
				if tt.errMsg != "" {
					assert.Contains(t, err.Error(), tt.errMsg)
				}
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestEnsureDirectories(t *testing.T) {
	tmpDir := t.TempDir()

	config := &Config{
		StateDir: filepath.Join(tmpDir, "state"),
		CacheDir: filepath.Join(tmpDir, "cache"),
		Storage: StorageConfig{
			LocalPath: filepath.Join(tmpDir, "data"),
		},
	}

	err := config.EnsureDirectories()
	require.NoError(t, err)

	// Check directories were created
	assert.DirExists(t, config.StateDir)
	assert.DirExists(t, config.CacheDir)
	assert.DirExists(t, config.Storage.LocalPath)
}

func TestSaveConfig(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "saved-config.json")

	config := &Config{
		Mode:     ModeCloud,
		Version:  "1.0.0",
		StateDir: "/test/state",
		Cloud: CloudConfig{
			Enabled: true,
			BaseURL: "https://api.arxos.io",
			APIKey:  "secret-key-12345678",
		},
		Storage: StorageConfig{
			Backend: "s3",
			Credentials: map[string]string{
				"aws_access_key_id":     "ACCESS_KEY",
				"aws_secret_access_key": "SECRET_KEY",
			},
		},
	}

	err := config.Save(configPath)
	require.NoError(t, err)

	// Load saved config
	data, err := os.ReadFile(configPath)
	require.NoError(t, err)

	var savedConfig Config
	err = json.Unmarshal(data, &savedConfig)
	require.NoError(t, err)

	// Check sensitive data was removed for security
	assert.Equal(t, "", savedConfig.Cloud.APIKey)
	assert.Nil(t, savedConfig.Storage.Credentials)

	// Check other data was preserved
	assert.Equal(t, ModeCloud, savedConfig.Mode)
	assert.Equal(t, "1.0.0", savedConfig.Version)
	assert.Equal(t, "s3", savedConfig.Storage.Backend)
}

func TestLoadFromEnv_Extended(t *testing.T) {
	// Set environment variables
	os.Setenv("ARXOS_MODE", "cloud")
	os.Setenv("ARXOS_VERSION", "1.0.0")
	os.Setenv("ARXOS_STATE_DIR", "/tmp/test-state")
	os.Setenv("ARXOS_CACHE_DIR", "/tmp/test-cache")
	os.Setenv("ARXOS_POSTGIS_HOST", "env-host")
	os.Setenv("ARXOS_POSTGIS_PORT", "5433")
	os.Setenv("ARXOS_POSTGIS_DATABASE", "env-db")
	os.Setenv("ARXOS_POSTGIS_USER", "env-user")
	os.Setenv("ARXOS_POSTGIS_SSL_MODE", "require")
	defer func() {
		os.Unsetenv("ARXOS_MODE")
		os.Unsetenv("ARXOS_VERSION")
		os.Unsetenv("ARXOS_STATE_DIR")
		os.Unsetenv("ARXOS_CACHE_DIR")
		os.Unsetenv("ARXOS_POSTGIS_HOST")
		os.Unsetenv("ARXOS_POSTGIS_PORT")
		os.Unsetenv("ARXOS_POSTGIS_DATABASE")
		os.Unsetenv("ARXOS_POSTGIS_USER")
		os.Unsetenv("ARXOS_POSTGIS_SSL_MODE")
	}()

	config := Default()
	config.LoadFromEnv()

	assert.Equal(t, ModeCloud, config.Mode)
	assert.Equal(t, "1.0.0", config.Version)
	assert.Equal(t, "/tmp/test-state", config.StateDir)
	assert.Equal(t, "/tmp/test-cache", config.CacheDir)
	assert.Equal(t, "env-host", config.PostGIS.Host)
	assert.Equal(t, 5433, config.PostGIS.Port)
	assert.Equal(t, "env-db", config.PostGIS.Database)
	assert.Equal(t, "env-user", config.PostGIS.User)
	assert.Equal(t, "require", config.PostGIS.SSLMode)
}

func TestLoadFromFile_JSON(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.json")

	configData := `{
		"mode": "cloud",
		"version": "1.0.0",
		"state_dir": "/tmp/test-state",
		"cache_dir": "/tmp/test-cache",
		"cloud": {
			"enabled": true,
			"base_url": "https://api.test.com"
		},
		"postgis": {
			"host": "test-host",
			"port": 5433,
			"database": "test-db",
			"user": "test-user",
			"ssl_mode": "require"
		}
	}`

	err := os.WriteFile(configPath, []byte(configData), 0644)
	require.NoError(t, err)

	config, err := Load(configPath)
	require.NoError(t, err)

	assert.Equal(t, ModeCloud, config.Mode)
	assert.Equal(t, "1.0.0", config.Version)
	assert.Equal(t, "/tmp/test-state", config.StateDir)
	assert.Equal(t, "/tmp/test-cache", config.CacheDir)
	assert.True(t, config.Cloud.Enabled)
	assert.Equal(t, "https://api.test.com", config.Cloud.BaseURL)
	assert.Equal(t, "test-host", config.PostGIS.Host)
	assert.Equal(t, 5433, config.PostGIS.Port)
	assert.Equal(t, "test-db", config.PostGIS.Database)
	assert.Equal(t, "test-user", config.PostGIS.User)
	assert.Equal(t, "require", config.PostGIS.SSLMode)
}

func TestLoadFromFile_YAML(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yml")

	configData := `mode: cloud
version: "1.0.0"
state_dir: /tmp/test-state
cache_dir: /tmp/test-cache
cloud:
  enabled: true
  base_url: https://api.test.com
postgis:
  host: test-host
  port: 5433
  database: test-db
  user: test-user
  ssl_mode: require`

	err := os.WriteFile(configPath, []byte(configData), 0644)
	require.NoError(t, err)

	config, err := Load(configPath)
	require.NoError(t, err)

	assert.Equal(t, ModeCloud, config.Mode)
	assert.Equal(t, "1.0.0", config.Version)
	assert.Equal(t, "/tmp/test-state", config.StateDir)
	assert.Equal(t, "/tmp/test-cache", config.CacheDir)
	assert.True(t, config.Cloud.Enabled)
	assert.Equal(t, "https://api.test.com", config.Cloud.BaseURL)
	assert.Equal(t, "test-host", config.PostGIS.Host)
	assert.Equal(t, 5433, config.PostGIS.Port)
	assert.Equal(t, "test-db", config.PostGIS.Database)
	assert.Equal(t, "test-user", config.PostGIS.User)
	assert.Equal(t, "require", config.PostGIS.SSLMode)
}

func TestLoadFromFile_InvalidFormat(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.txt")

	configData := `This is not a valid config file`

	err := os.WriteFile(configPath, []byte(configData), 0644)
	require.NoError(t, err)

	config, err := Load(configPath)
	require.NoError(t, err) // Should not error, just use defaults

	// Should use default values
	assert.Equal(t, ModeLocal, config.Mode)
	assert.Equal(t, "0.1.0", config.Version)
}

func TestLoadFromFile_NotFound(t *testing.T) {
	config, err := Load("/nonexistent/config.yml")
	require.NoError(t, err) // Should not error, just use defaults

	// Should use default values
	assert.Equal(t, ModeLocal, config.Mode)
	assert.Equal(t, "0.1.0", config.Version)
}

func TestLoadServiceConfigs_Integration(t *testing.T) {
	// Create temporary directory structure
	tmpDir := t.TempDir()
	servicesDir := filepath.Join(tmpDir, "services")
	err := os.MkdirAll(servicesDir, 0755)
	require.NoError(t, err)

	// Create test service config
	postgisConfig := `postgis:
  host: service-host
  port: 5434
  database: service-db
  user: service-user
  ssl_mode: require`

	err = os.WriteFile(filepath.Join(servicesDir, "postgis.yml"), []byte(postgisConfig), 0644)
	require.NoError(t, err)

	// Test loading with service configs
	config, err := Load("") // Load with empty path to test service loading
	require.NoError(t, err)

	// The service config should be loaded and applied
	// Note: This test depends on the Load function calling LoadServiceConfigs
	assert.Equal(t, "service-host", config.PostGIS.Host)
	assert.Equal(t, 5434, config.PostGIS.Port)
	assert.Equal(t, "service-db", config.PostGIS.Database)
	assert.Equal(t, "service-user", config.PostGIS.User)
	assert.Equal(t, "require", config.PostGIS.SSLMode)
}

func TestBuildPostGISConnectionString(t *testing.T) {
	config := &Config{
		PostGIS: PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos",
			User:     "arxos",
			Password: "password",
			SSLMode:  "disable",
		},
	}

	dsn := config.BuildPostGISConnectionString()
	expected := "host=localhost port=5432 user=arxos database=arxos sslmode=disable"
	assert.Equal(t, expected, dsn)
}

func TestGetDatabaseConfig(t *testing.T) {
	config := Default()
	dbConfig := config.GetDatabaseConfig()

	assert.Equal(t, "postgis", dbConfig.Type)
	assert.Equal(t, "postgres", dbConfig.Driver)
}

func TestGetPostGISConfig(t *testing.T) {
	config := Default()
	postgisConfig := config.GetPostGISConfig()

	assert.Equal(t, "localhost", postgisConfig.Host)
	assert.Equal(t, 5432, postgisConfig.Port)
	assert.Equal(t, "arxos", postgisConfig.Database)
	assert.Equal(t, "arxos", postgisConfig.User)
}

func TestGetRepositoriesPath(t *testing.T) {
	config := &Config{
		Storage: StorageConfig{
			Data: DataConfig{
				BasePath:        "/test/base",
				RepositoriesDir: "repos",
			},
		},
	}

	path := config.GetRepositoriesPath()
	expected := filepath.Join("/test/base", "repos")
	assert.Equal(t, expected, path)
}

func TestGetCachePath(t *testing.T) {
	config := &Config{
		Storage: StorageConfig{
			Data: DataConfig{
				BasePath: "/test/base",
				CacheDir: "cache",
			},
		},
	}

	path := config.GetCachePath()
	expected := filepath.Join("/test/base", "cache")
	assert.Equal(t, expected, path)
}

func TestGetLogsPath(t *testing.T) {
	config := &Config{
		Storage: StorageConfig{
			Data: DataConfig{
				BasePath: "/test/base",
				LogsDir:  "logs",
			},
		},
	}

	path := config.GetLogsPath()
	expected := filepath.Join("/test/base", "logs")
	assert.Equal(t, expected, path)
}

func TestGetTempPath(t *testing.T) {
	config := &Config{
		Storage: StorageConfig{
			Data: DataConfig{
				BasePath: "/test/base",
				TempDir:  "temp",
			},
		},
	}

	path := config.GetTempPath()
	expected := filepath.Join("/test/base", "temp")
	assert.Equal(t, expected, path)
}

func TestIsCloudEnabled(t *testing.T) {
	tests := []struct {
		name     string
		mode     Mode
		enabled  bool
		expected bool
	}{
		{"local mode", ModeLocal, false, false},
		{"cloud mode", ModeCloud, false, true},
		{"hybrid mode", ModeHybrid, false, true},
		{"local with cloud enabled", ModeLocal, true, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			config := &Config{
				Mode: tt.mode,
				Cloud: CloudConfig{
					Enabled: tt.enabled,
				},
			}
			assert.Equal(t, tt.expected, config.IsCloudEnabled())
		})
	}
}

func TestIsOfflineMode(t *testing.T) {
	tests := []struct {
		name     string
		mode     Mode
		offline  bool
		expected bool
	}{
		{"local mode", ModeLocal, false, true},
		{"cloud mode", ModeCloud, false, false},
		{"hybrid online", ModeHybrid, false, false},
		{"hybrid offline", ModeHybrid, true, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			config := &Config{
				Mode: tt.mode,
				Features: FeatureFlags{
					OfflineMode: tt.offline,
				},
			}
			assert.Equal(t, tt.expected, config.IsOfflineMode())
		})
	}
}

func TestGetConfigPath(t *testing.T) {
	// Test with environment variable
	os.Setenv("ARXOS_CONFIG", "/custom/path/config.json")
	path := GetConfigPath()
	assert.Equal(t, "/custom/path/config.json", path)
	os.Unsetenv("ARXOS_CONFIG")

	// Test with current directory file
	tmpDir := t.TempDir()
	oldWd, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldWd)

	// Create arxos.yml in current directory (should be preferred over JSON)
	os.WriteFile("arxos.yml", []byte("{}"), 0644)
	path = GetConfigPath()
	assert.Equal(t, "arxos.yml", path)

	// Create arxos.json in current directory
	os.WriteFile("arxos.json", []byte("{}"), 0644)
	path = GetConfigPath()
	assert.Equal(t, "arxos.yml", path) // YAML should still be preferred

	// Test default path
	os.Remove("arxos.yml")
	os.Remove("arxos.json")
	path = GetConfigPath()
	homeDir, _ := os.UserHomeDir()
	expected := filepath.Join(homeDir, ".arxos", "config.json")
	assert.Equal(t, expected, path)
}

func TestLoadFromYAMLFile(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "test-config.yml")

	yamlConfig := `
mode: cloud
version: "1.0.0"
state_dir: "/test/state"
cache_dir: "/test/cache"
cloud:
  enabled: true
  base_url: "https://test.arxos.io"
  api_key: "test-key-123"
  org_id: "org-456"
storage:
  backend: "s3"
  cloud_bucket: "test-bucket"
  cloud_region: "us-east-1"
features:
  cloud_sync: true
  ai_integration: true
`

	// Write test config to file
	err := os.WriteFile(configPath, []byte(yamlConfig), 0644)
	require.NoError(t, err)

	// Load config from file
	config := Default()
	err = config.LoadFromFile(configPath)
	require.NoError(t, err)

	assert.Equal(t, ModeCloud, config.Mode)
	assert.Equal(t, "1.0.0", config.Version)
	assert.Equal(t, "/test/state", config.StateDir)
	assert.True(t, config.Cloud.Enabled)
	assert.Equal(t, "https://test.arxos.io", config.Cloud.BaseURL)
	// APIKey is not serialized to JSON (json:"-" tag) so it won't round-trip
	assert.Equal(t, "", config.Cloud.APIKey)
	assert.Equal(t, "s3", config.Storage.Backend)
	assert.Equal(t, "test-bucket", config.Storage.CloudBucket)
	assert.True(t, config.Features.CloudSync)
	assert.True(t, config.Features.AIIntegration)
}

func TestEnvironmentVariableSubstitution(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "test-config.yml")

	// Set environment variables
	os.Setenv("TEST_DB_HOST", "test-host")
	os.Setenv("TEST_DB_PORT", "5433")
	os.Setenv("TEST_API_URL", "https://api.test.com")
	os.Setenv("TEST_BUCKET", "test-bucket")

	defer func() {
		os.Unsetenv("TEST_DB_HOST")
		os.Unsetenv("TEST_DB_PORT")
		os.Unsetenv("TEST_API_URL")
		os.Unsetenv("TEST_BUCKET")
	}()

	yamlConfig := `
mode: cloud
version: "1.0.0"
postgis:
  host: "${TEST_DB_HOST}"
  port: ${TEST_DB_PORT}
  database: "arxos"
  user: "arxos"
cloud:
  base_url: "${TEST_API_URL}"
storage:
  backend: "s3"
  cloud_bucket: "${TEST_BUCKET}"
  cloud_region: "us-east-1"
`

	// Write test config to file
	err := os.WriteFile(configPath, []byte(yamlConfig), 0644)
	require.NoError(t, err)

	// Load config from file
	config := Default()
	err = config.LoadFromFile(configPath)
	require.NoError(t, err)

	assert.Equal(t, "test-host", config.PostGIS.Host)
	assert.Equal(t, 5433, config.PostGIS.Port)
	assert.Equal(t, "https://api.test.com", config.Cloud.BaseURL)
	assert.Equal(t, "test-bucket", config.Storage.CloudBucket)
}

func TestEnvironmentVariableSubstitutionWithDefaults(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "test-config.yml")

	yamlConfig := `
mode: cloud
version: "1.0.0"
postgis:
  host: "${MISSING_VAR:-localhost}"
  port: ${MISSING_PORT:-5432}
  database: "arxos"
  user: "arxos"
cloud:
  base_url: "${MISSING_API_URL:-https://api.arxos.io}"
storage:
  backend: "s3"
  cloud_bucket: "${MISSING_BUCKET:-default-bucket}"
  cloud_region: "us-east-1"
`

	// Write test config to file
	err := os.WriteFile(configPath, []byte(yamlConfig), 0644)
	require.NoError(t, err)

	// Load config from file
	config := Default()
	err = config.LoadFromFile(configPath)
	require.NoError(t, err)

	assert.Equal(t, "localhost", config.PostGIS.Host)
	assert.Equal(t, 5432, config.PostGIS.Port)
	assert.Equal(t, "https://api.arxos.io", config.Cloud.BaseURL)
	assert.Equal(t, "default-bucket", config.Storage.CloudBucket)
}
