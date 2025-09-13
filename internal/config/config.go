// Package config provides configuration management for ArxOS applications.
// It handles loading, validation, and management of configuration settings from
// files and environment variables, supporting development and production modes.
package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

// Mode represents the operational mode of ArxOS
type Mode string

const (
	// ModeLocal operates entirely on local filesystem
	ModeLocal Mode = "local"
	// ModeCloud operates with cloud synchronization
	ModeCloud Mode = "cloud"
	// ModeHybrid operates locally with optional cloud sync
	ModeHybrid Mode = "hybrid"
)

// Config represents the complete ArxOS configuration
type Config struct {
	// Core settings
	Mode      Mode   `json:"mode"`
	Version   string `json:"version"`
	StateDir  string `json:"state_dir"`
	CacheDir  string `json:"cache_dir"`
	
	// Cloud settings
	Cloud CloudConfig `json:"cloud"`
	
	// Storage settings
	Storage StorageConfig `json:"storage"`
	
	// API settings
	API APIConfig `json:"api"`
	
	// Telemetry settings
	Telemetry TelemetryConfig `json:"telemetry"`
	
	// Feature flags
	Features FeatureFlags `json:"features"`
}

// CloudConfig contains cloud-specific configuration
type CloudConfig struct {
	Enabled     bool   `json:"enabled"`
	BaseURL     string `json:"base_url"`
	APIKey      string `json:"api_key"`
	OrgID       string `json:"org_id"`
	SyncEnabled bool   `json:"sync_enabled"`
	SyncInterval time.Duration `json:"sync_interval"`
}

// StorageConfig defines storage backend configuration
type StorageConfig struct {
	Backend      string            `json:"backend"` // local, s3, gcs, azure
	LocalPath    string            `json:"local_path"`
	CloudBucket  string            `json:"cloud_bucket"`
	CloudRegion  string            `json:"cloud_region"`
	CloudPrefix  string            `json:"cloud_prefix"`
	Credentials  map[string]string `json:"-"` // Sensitive, not serialized
}

// APIConfig contains API client configuration
type APIConfig struct {
	Timeout       time.Duration `json:"timeout"`
	RetryAttempts int          `json:"retry_attempts"`
	RetryDelay    time.Duration `json:"retry_delay"`
	UserAgent     string        `json:"user_agent"`
}

// TelemetryConfig controls metrics and analytics
type TelemetryConfig struct {
	Enabled       bool   `json:"enabled"`
	Endpoint      string `json:"endpoint"`
	SampleRate    float64 `json:"sample_rate"`
	Debug         bool   `json:"debug"`
	AnonymousID   string `json:"anonymous_id"`
}

// FeatureFlags controls feature availability
type FeatureFlags struct {
	CloudSync        bool `json:"cloud_sync"`
	AIIntegration    bool `json:"ai_integration"`
	OfflineMode      bool `json:"offline_mode"`
	BetaFeatures     bool `json:"beta_features"`
	Analytics        bool `json:"analytics"`
	AutoUpdate       bool `json:"auto_update"`
}

// Default returns a default configuration for local mode
func Default() *Config {
	homeDir, _ := os.UserHomeDir()
	
	return &Config{
		Mode:     ModeLocal,
		Version:  "0.1.0",
		StateDir: filepath.Join(homeDir, ".arxos"),
		CacheDir: filepath.Join(homeDir, ".arxos", "cache"),
		
		Cloud: CloudConfig{
			Enabled:      false,
			BaseURL:      "https://api.arxos.io",
			SyncEnabled:  false,
			SyncInterval: 5 * time.Minute,
		},
		
		Storage: StorageConfig{
			Backend:   "local",
			LocalPath: filepath.Join(homeDir, ".arxos", "data"),
		},
		
		API: APIConfig{
			Timeout:       30 * time.Second,
			RetryAttempts: 3,
			RetryDelay:    1 * time.Second,
			UserAgent:     "ArxOS-CLI/0.1.0",
		},
		
		Telemetry: TelemetryConfig{
			Enabled:    false,
			Endpoint:   "https://telemetry.arxos.io",
			SampleRate: 0.1,
			Debug:      false,
		},
		
		Features: FeatureFlags{
			CloudSync:     false,
			AIIntegration: false,
			OfflineMode:   true,
			BetaFeatures:  false,
			Analytics:     false,
			AutoUpdate:    false,
		},
	}
}

// Load loads configuration from file or environment
func Load(configPath string) (*Config, error) {
	config := Default()
	
	// Load from file if it exists
	if configPath != "" {
		if err := config.LoadFromFile(configPath); err != nil {
			logger.Warn("Failed to load config file, using defaults: %v", err)
		}
	}
	
	// Override with environment variables
	config.LoadFromEnv()
	
	// Validate configuration
	if err := config.Validate(); err != nil {
		return nil, fmt.Errorf("invalid configuration: %w", err)
	}
	
	// Ensure directories exist
	if err := config.EnsureDirectories(); err != nil {
		return nil, fmt.Errorf("failed to create directories: %w", err)
	}
	
	return config, nil
}

// LoadFromFile loads configuration from a JSON file
func (c *Config) LoadFromFile(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("failed to read config file: %w", err)
	}
	
	if err := json.Unmarshal(data, c); err != nil {
		return fmt.Errorf("failed to parse config file: %w", err)
	}
	
	return nil
}

// LoadFromEnv loads configuration from environment variables
func (c *Config) LoadFromEnv() {
	// Mode
	if mode := os.Getenv("ARXOS_MODE"); mode != "" {
		c.Mode = Mode(mode)
	}
	
	// Cloud settings
	if url := os.Getenv("ARXOS_CLOUD_URL"); url != "" {
		c.Cloud.BaseURL = url
	}
	if key := os.Getenv("ARXOS_API_KEY"); key != "" {
		c.Cloud.APIKey = key
	}
	if org := os.Getenv("ARXOS_ORG_ID"); org != "" {
		c.Cloud.OrgID = org
	}
	
	// Storage settings
	if backend := os.Getenv("ARXOS_STORAGE_BACKEND"); backend != "" {
		c.Storage.Backend = backend
	}
	if bucket := os.Getenv("ARXOS_STORAGE_BUCKET"); bucket != "" {
		c.Storage.CloudBucket = bucket
	}
	if region := os.Getenv("ARXOS_STORAGE_REGION"); region != "" {
		c.Storage.CloudRegion = region
	}
	
	// Feature flags
	if enabled := os.Getenv("ARXOS_CLOUD_SYNC"); enabled == "true" {
		c.Features.CloudSync = true
		c.Cloud.Enabled = true
	}
	if enabled := os.Getenv("ARXOS_AI_ENABLED"); enabled == "true" {
		c.Features.AIIntegration = true
	}
	if enabled := os.Getenv("ARXOS_TELEMETRY"); enabled == "true" {
		c.Telemetry.Enabled = true
	}
	
	// Storage credentials from environment
	c.Storage.Credentials = make(map[string]string)
	if key := os.Getenv("AWS_ACCESS_KEY_ID"); key != "" {
		c.Storage.Credentials["aws_access_key_id"] = key
	}
	if secret := os.Getenv("AWS_SECRET_ACCESS_KEY"); secret != "" {
		c.Storage.Credentials["aws_secret_access_key"] = secret
	}
	if token := os.Getenv("GOOGLE_APPLICATION_CREDENTIALS"); token != "" {
		c.Storage.Credentials["gcp_credentials"] = token
	}
}

// Validate checks if the configuration is valid
func (c *Config) Validate() error {
	// Validate mode
	switch c.Mode {
	case ModeLocal, ModeCloud, ModeHybrid:
		// Valid modes
	default:
		return fmt.Errorf("invalid mode: %s", c.Mode)
	}
	
	// Validate cloud configuration if enabled
	if c.Cloud.Enabled || c.Mode == ModeCloud {
		if c.Cloud.BaseURL == "" {
			return fmt.Errorf("cloud URL required when cloud is enabled")
		}
		if c.Cloud.APIKey == "" && c.Mode == ModeCloud {
			logger.Warn("No API key configured for cloud mode")
		}
	}
	
	// Validate storage backend
	switch c.Storage.Backend {
	case "local", "s3", "gcs", "azure":
		// Valid backends
	default:
		return fmt.Errorf("invalid storage backend: %s", c.Storage.Backend)
	}
	
	// Validate storage configuration for cloud backends
	if c.Storage.Backend != "local" {
		if c.Storage.CloudBucket == "" {
			return fmt.Errorf("cloud bucket required for %s backend", c.Storage.Backend)
		}
	}
	
	return nil
}

// EnsureDirectories creates necessary directories
func (c *Config) EnsureDirectories() error {
	dirs := []string{
		c.StateDir,
		c.CacheDir,
		c.Storage.LocalPath,
	}
	
	for _, dir := range dirs {
		if dir == "" {
			continue
		}
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}
	
	return nil
}

// Save saves the configuration to a file
func (c *Config) Save(path string) error {
	// Don't save sensitive data
	configCopy := *c
	configCopy.Storage.Credentials = nil
	
	// Mask API key if present
	if len(c.Cloud.APIKey) > 4 {
		configCopy.Cloud.APIKey = strings.Repeat("*", 8) + c.Cloud.APIKey[len(c.Cloud.APIKey)-4:]
	} else if c.Cloud.APIKey != "" {
		configCopy.Cloud.APIKey = strings.Repeat("*", len(c.Cloud.APIKey))
	}
	
	data, err := json.MarshalIndent(configCopy, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}
	
	if err := os.WriteFile(path, data, 0600); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}
	
	return nil
}

// IsCloudEnabled returns true if cloud features are enabled
func (c *Config) IsCloudEnabled() bool {
	return c.Cloud.Enabled || c.Mode == ModeCloud || c.Mode == ModeHybrid
}

// IsOfflineMode returns true if operating in offline mode
func (c *Config) IsOfflineMode() bool {
	return c.Mode == ModeLocal || (c.Mode == ModeHybrid && c.Features.OfflineMode)
}

// GetConfigPath returns the default configuration file path
func GetConfigPath() string {
	// Check environment variable first
	if path := os.Getenv("ARXOS_CONFIG"); path != "" {
		return path
	}
	
	// Check current directory
	if _, err := os.Stat("arxos.json"); err == nil {
		return "arxos.json"
	}
	
	// Use home directory
	homeDir, _ := os.UserHomeDir()
	return filepath.Join(homeDir, ".arxos", "config.json")
}