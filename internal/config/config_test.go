package config_test

import (
	"path/filepath"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestConfigValidation(t *testing.T) {
	tests := []struct {
		name     string
		config   *config.Config
		expected bool
	}{
		{
			name: "valid local config",
			config: &config.Config{
				Mode:     config.ModeLocal,
				Version:  "0.1.0",
				StateDir: "/tmp/test",
				CacheDir: "/tmp/test/cache",
				Database: config.DatabaseConfig{
					Type:     "postgis",
					Host:     "localhost",
					Port:     5432,
					Database: "test_db",
					Username: "test_user",
					Password: "test_pass",
				},
			},
			expected: true,
		},
		{
			name: "invalid mode",
			config: &config.Config{
				Mode:    "invalid",
				Version: "0.1.0",
			},
			expected: false,
		},
		{
			name: "missing version",
			config: &config.Config{
				Mode: config.ModeLocal,
			},
			expected: false,
		},
		{
			name: "missing state dir",
			config: &config.Config{
				Mode:    config.ModeLocal,
				Version: "0.1.0",
			},
			expected: false,
		},
		{
			name: "invalid database port",
			config: &config.Config{
				Mode:     config.ModeLocal,
				Version:  "0.1.0",
				StateDir: "/tmp/test",
				CacheDir: "/tmp/test/cache",
				Database: config.DatabaseConfig{
					Type:     "postgis",
					Host:     "localhost",
					Port:     99999, // Invalid port
					Database: "test_db",
				},
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			validator := config.NewConfigValidator()
			result := validator.ValidateConfiguration(tt.config)

			if tt.expected {
				assert.True(t, result.Valid, "Config should be valid")
				assert.Empty(t, result.Errors, "Should have no errors")
			} else {
				assert.False(t, result.Valid, "Config should be invalid")
				assert.NotEmpty(t, result.Errors, "Should have errors")
			}
		})
	}
}

func TestConfigTemplates(t *testing.T) {
	templates := config.GetConfigTemplates()

	// Verify we have expected templates
	expectedTemplates := []string{"local", "cloud", "hybrid", "production"}
	templateNames := make([]string, len(templates))
	for i, template := range templates {
		templateNames[i] = template.Name
	}

	for _, expected := range expectedTemplates {
		assert.Contains(t, templateNames, expected, "Should have %s template", expected)
	}

	// Verify each template has valid configuration
	for _, template := range templates {
		t.Run(template.Name, func(t *testing.T) {
			assert.NotEmpty(t, template.Name)
			assert.NotEmpty(t, template.Description)
			assert.NotNil(t, template.Config)

			// Validate template config
			validator := config.NewConfigValidator()
			result := validator.ValidateConfiguration(template.Config)
			assert.True(t, result.Valid, "Template %s should be valid", template.Name)
		})
	}
}

func TestCreateConfigFromTemplate(t *testing.T) {
	tempDir := t.TempDir()

	tests := []struct {
		name         string
		templateName string
		dataDir      string
		expectedMode config.Mode
	}{
		{
			name:         "local template",
			templateName: "local",
			dataDir:      tempDir,
			expectedMode: config.ModeLocal,
		},
		{
			name:         "cloud template",
			templateName: "cloud",
			dataDir:      tempDir,
			expectedMode: config.ModeCloud,
		},
		{
			name:         "hybrid template",
			templateName: "hybrid",
			dataDir:      tempDir,
			expectedMode: config.ModeHybrid,
		},
		{
			name:         "production template",
			templateName: "production",
			dataDir:      tempDir,
			expectedMode: config.ModeProduction,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg, err := config.CreateConfigFromTemplate(tt.templateName, tt.dataDir)
			require.NoError(t, err)
			assert.Equal(t, tt.expectedMode, cfg.Mode)
			assert.Equal(t, tt.dataDir, cfg.Storage.Data.BasePath)
		})
	}

	// Test invalid template
	_, err := config.CreateConfigFromTemplate("invalid", tempDir)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "unknown template")
}

func TestConfigSaveAndLoad(t *testing.T) {
	tempDir := t.TempDir()
	configPath := filepath.Join(tempDir, "test.yml")

	// Create a test config
	cfg := &config.Config{
		Mode:     config.ModeLocal,
		Version:  "0.1.0",
		StateDir: tempDir,
		CacheDir: filepath.Join(tempDir, "cache"),
		Database: config.DatabaseConfig{
			Type:     "postgis",
			Host:     "localhost",
			Port:     5432,
			Database: "test_db",
		},
	}

	// Save config
	err := cfg.Save(configPath)
	require.NoError(t, err)
	assert.FileExists(t, configPath)

	// Load config
	loadedCfg, err := config.Load(configPath)
	require.NoError(t, err)
	assert.Equal(t, cfg.Mode, loadedCfg.Mode)
	assert.Equal(t, cfg.Version, loadedCfg.Version)
	assert.Equal(t, cfg.StateDir, loadedCfg.StateDir)
	assert.Equal(t, cfg.Database.Type, loadedCfg.Database.Type)
}

func TestConfigSaveJSON(t *testing.T) {
	tempDir := t.TempDir()
	configPath := filepath.Join(tempDir, "test.json")

	cfg := &config.Config{
		Mode:     config.ModeLocal,
		Version:  "0.1.0",
		StateDir: tempDir,
		CacheDir: filepath.Join(tempDir, "cache"),
	}

	err := cfg.Save(configPath)
	require.NoError(t, err)
	assert.FileExists(t, configPath)

	// Verify it's valid JSON
	loadedCfg, err := config.Load(configPath)
	require.NoError(t, err)
	assert.Equal(t, cfg.Mode, loadedCfg.Mode)
}

func TestConfigValidationErrors(t *testing.T) {
	cfg := &config.Config{
		Mode:    "invalid_mode",
		Version: "",
		Database: config.DatabaseConfig{
			Port: 99999,
		},
		Security: config.SecurityConfig{
			JWTExpiry: -1 * time.Hour,
		},
	}

	validator := config.NewConfigValidator()
	result := validator.ValidateConfiguration(cfg)

	assert.False(t, result.Valid)
	assert.NotEmpty(t, result.Errors)

	// Check specific errors
	errorCodes := make([]string, len(result.Errors))
	for i, err := range result.Errors {
		errorCodes[i] = err.Code
	}

	assert.Contains(t, errorCodes, "INVALID_MODE")
	assert.Contains(t, errorCodes, "MISSING_VERSION")
	assert.Contains(t, errorCodes, "INVALID_DATABASE_PORT")
	assert.Contains(t, errorCodes, "INVALID_JWT_EXPIRY")
}

func TestConfigValidationWarnings(t *testing.T) {
	cfg := &config.Config{
		Mode:     config.ModeLocal,
		Version:  "0.1.0",
		StateDir: "/tmp/test",
		CacheDir: "/tmp/test/cache",
		Database: config.DatabaseConfig{
			Type:         "postgis",
			Host:         "localhost",
			Port:         5432,
			Database:     "test_db",
			MaxOpenConns: 0, // Should generate warning
		},
		Security: config.SecurityConfig{
			JWTExpiry:  2 * time.Minute, // Very short, should generate warning
			BcryptCost: 3,               // Very low, should generate warning
		},
	}

	validator := config.NewConfigValidator()
	result := validator.ValidateConfiguration(cfg)

	assert.True(t, result.Valid) // Should still be valid
	assert.NotEmpty(t, result.Warnings)

	// Check specific warnings
	warningCodes := make([]string, len(result.Warnings))
	for i, warning := range result.Warnings {
		warningCodes[i] = warning.Code
	}

	assert.Contains(t, warningCodes, "INVALID_MAX_OPEN_CONNS")
	assert.Contains(t, warningCodes, "SHORT_JWT_EXPIRY")
	assert.Contains(t, warningCodes, "LOW_BCRYPT_COST")
}

func TestConfigCloudValidation(t *testing.T) {
	tests := []struct {
		name          string
		cloudEnabled  bool
		baseURL       string
		syncEnabled   bool
		syncInterval  time.Duration
		expectedValid bool
		expectedError string
	}{
		{
			name:          "valid cloud config",
			cloudEnabled:  true,
			baseURL:       "https://api.arxos.io",
			syncEnabled:   true,
			syncInterval:  5 * time.Minute,
			expectedValid: true,
		},
		{
			name:          "cloud enabled but no URL",
			cloudEnabled:  true,
			baseURL:       "",
			syncEnabled:   true,
			syncInterval:  5 * time.Minute,
			expectedValid: false,
			expectedError: "MISSING_CLOUD_BASE_URL",
		},
		{
			name:          "invalid URL",
			cloudEnabled:  true,
			baseURL:       "invalid-url",
			syncEnabled:   true,
			syncInterval:  5 * time.Minute,
			expectedValid: false,
			expectedError: "INVALID_CLOUD_BASE_URL",
		},
		{
			name:          "sync enabled but no interval",
			cloudEnabled:  true,
			baseURL:       "https://api.arxos.io",
			syncEnabled:   true,
			syncInterval:  0,
			expectedValid: false,
			expectedError: "INVALID_SYNC_INTERVAL",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg := &config.Config{
				Mode:     config.ModeCloud,
				Version:  "0.1.0",
				StateDir: "/tmp/test",
				CacheDir: "/tmp/test/cache",
				Cloud: config.CloudConfig{
					Enabled:      tt.cloudEnabled,
					BaseURL:      tt.baseURL,
					SyncEnabled:  tt.syncEnabled,
					SyncInterval: tt.syncInterval,
				},
			}

			validator := config.NewConfigValidator()
			result := validator.ValidateConfiguration(cfg)

			if tt.expectedValid {
				assert.True(t, result.Valid)
			} else {
				assert.False(t, result.Valid)
				if tt.expectedError != "" {
					errorCodes := make([]string, len(result.Errors))
					for i, err := range result.Errors {
						errorCodes[i] = err.Code
					}
					assert.Contains(t, errorCodes, tt.expectedError)
				}
			}
		})
	}
}

func TestConfigFeatureValidation(t *testing.T) {
	tests := []struct {
		name             string
		cloudEnabled     bool
		cloudSync        bool
		offlineMode      bool
		expectedWarnings []string
	}{
		{
			name:         "no conflicts",
			cloudEnabled: true,
			cloudSync:    true,
			offlineMode:  false,
		},
		{
			name:             "cloud sync without cloud",
			cloudEnabled:     false,
			cloudSync:        true,
			offlineMode:      false,
			expectedWarnings: []string{"CONFLICTING_FEATURES"},
		},
		{
			name:             "offline mode with cloud sync",
			cloudEnabled:     true,
			cloudSync:        true,
			offlineMode:      true,
			expectedWarnings: []string{"CONFLICTING_FEATURES"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg := &config.Config{
				Mode:     config.ModeLocal,
				Version:  "0.1.0",
				StateDir: "/tmp/test",
				CacheDir: "/tmp/test/cache",
				Cloud: config.CloudConfig{
					Enabled: tt.cloudEnabled,
				},
				Features: config.FeatureFlags{
					CloudSync:   tt.cloudSync,
					OfflineMode: tt.offlineMode,
				},
			}

			validator := config.NewConfigValidator()
			result := validator.ValidateConfiguration(cfg)

			if len(tt.expectedWarnings) > 0 {
				assert.NotEmpty(t, result.Warnings)
				warningCodes := make([]string, len(result.Warnings))
				for i, warning := range result.Warnings {
					warningCodes[i] = warning.Code
				}
				for _, expectedWarning := range tt.expectedWarnings {
					assert.Contains(t, warningCodes, expectedWarning)
				}
			}
		})
	}
}

func TestConfigTUIValidation(t *testing.T) {
	tests := []struct {
		name           string
		tuiEnabled     bool
		theme          string
		updateInterval string
		maxEquipment   int
		expectedValid  bool
		expectedError  string
	}{
		{
			name:           "valid TUI config",
			tuiEnabled:     true,
			theme:          "dark",
			updateInterval: "1s",
			maxEquipment:   1000,
			expectedValid:  true,
		},
		{
			name:           "invalid theme",
			tuiEnabled:     true,
			theme:          "invalid",
			updateInterval: "1s",
			maxEquipment:   1000,
			expectedValid:  true, // Should be valid but with warning
		},
		{
			name:           "invalid update interval",
			tuiEnabled:     true,
			theme:          "dark",
			updateInterval: "0s",
			maxEquipment:   1000,
			expectedValid:  false,
			expectedError:  "INVALID_TUI_UPDATE_INTERVAL",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg := &config.Config{
				Mode:     config.ModeLocal,
				Version:  "0.1.0",
				StateDir: "/tmp/test",
				CacheDir: "/tmp/test/cache",
				TUI: config.TUIConfig{
					Enabled:             tt.tuiEnabled,
					Theme:               tt.theme,
					UpdateInterval:      tt.updateInterval,
					MaxEquipmentDisplay: tt.maxEquipment,
				},
			}

			validator := config.NewConfigValidator()
			result := validator.ValidateConfiguration(cfg)

			if tt.expectedValid {
				assert.True(t, result.Valid)
			} else {
				assert.False(t, result.Valid)
				if tt.expectedError != "" {
					errorCodes := make([]string, len(result.Errors))
					for i, err := range result.Errors {
						errorCodes[i] = err.Code
					}
					assert.Contains(t, errorCodes, tt.expectedError)
				}
			}
		})
	}
}

func TestConfigInstallationValidation(t *testing.T) {
	tempDir := t.TempDir()

	cfg := &config.Config{
		Mode:     config.ModeLocal,
		Version:  "0.1.0",
		StateDir: tempDir,
		CacheDir: filepath.Join(tempDir, "cache"),
		Storage: config.StorageConfig{
			Data: config.DataConfig{
				BasePath: tempDir,
			},
		},
	}

	validator := config.NewConfigValidator()
	result := validator.ValidateInstallation(cfg)

	// Should be valid since we can create directories
	assert.True(t, result.Valid)
	assert.Empty(t, result.Errors)
}

func TestGetDefaultDataPath(t *testing.T) {
	path := config.GetDefaultDataPath()
	assert.NotEmpty(t, path)
	assert.Contains(t, path, "arxos")
}

func TestConfigValidationIntegration(t *testing.T) {
	// Test a complete, realistic configuration
	tempDir := t.TempDir()

	cfg := &config.Config{
		Mode:     config.ModeHybrid,
		Version:  "0.1.0",
		StateDir: tempDir,
		CacheDir: filepath.Join(tempDir, "cache"),
		Cloud: config.CloudConfig{
			Enabled:      true,
			BaseURL:      "https://api.arxos.io",
			SyncEnabled:  true,
			SyncInterval: 5 * time.Minute,
		},
		Database: config.DatabaseConfig{
			Type:         "postgis",
			Host:         "localhost",
			Port:         5432,
			Database:     "arxos_dev",
			Username:     "arxos",
			Password:     "arxos_dev",
			MaxOpenConns: 25,
			MaxIdleConns: 5,
		},
		Security: config.SecurityConfig{
			JWTExpiry:      24 * time.Hour,
			SessionTimeout: 30 * time.Minute,
			APIRateLimit:   100,
			BcryptCost:     10,
		},
		Features: config.FeatureFlags{
			CloudSync:    true,
			OfflineMode:  true,
			BetaFeatures: false,
		},
		TUI: config.TUIConfig{
			Enabled:             true,
			Theme:               "dark",
			UpdateInterval:      "1s",
			MaxEquipmentDisplay: 1000,
		},
		IFC: config.IFCConfig{
			Service: config.IFCServiceConfig{
				Enabled: true,
				URL:     "http://localhost:5000",
				Timeout: "30s",
				Retries: 3,
			},
		},
	}

	validator := config.NewConfigValidator()
	result := validator.ValidateConfiguration(cfg)

	assert.True(t, result.Valid, "Complete config should be valid")
	assert.Empty(t, result.Errors, "Should have no errors")

	// May have some warnings, but that's okay
	if len(result.Warnings) > 0 {
		t.Logf("Warnings: %v", result.Warnings)
	}
}
