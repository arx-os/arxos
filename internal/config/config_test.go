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
					Type:           "sqlite",
					DataSourceName: "/tmp/test.db",
				},
				Security: SecurityConfig{
					JWTSecret: "test-jwt-secret-123",
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

	// Create arxos.json in current directory
	os.WriteFile("arxos.json", []byte("{}"), 0644)
	path = GetConfigPath()
	assert.Equal(t, "arxos.json", path)

	// Test default path
	os.Remove("arxos.json")
	path = GetConfigPath()
	homeDir, _ := os.UserHomeDir()
	expected := filepath.Join(homeDir, ".arxos", "config.json")
	assert.Equal(t, expected, path)
}
