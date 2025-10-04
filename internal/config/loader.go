package config

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

// ConfigLoader loads configuration from various sources
type ConfigLoader struct {
	sources   []ConfigSource
	validator *ConfigValidator
}

// ConfigSource represents a configuration source
type ConfigSource interface {
	Load() (*Config, error)
	Priority() int // Higher priority sources override lower priority ones
	Name() string
}

// FileConfigSource loads configuration from a file
type FileConfigSource struct {
	path     string
	priority int
}

// EnvironmentConfigSource loads configuration from environment variables
type EnvironmentConfigSource struct {
	prefix   string
	priority int
}

// DefaultConfigSource provides default configuration values
type DefaultConfigSource struct {
	priority int
}

// NewConfigLoader creates a new configuration loader
func NewConfigLoader() *ConfigLoader {
	return &ConfigLoader{
		sources:   make([]ConfigSource, 0),
		validator: NewConfigValidator(),
	}
}

// AddSource adds a configuration source
func (cl *ConfigLoader) AddSource(source ConfigSource) {
	cl.sources = append(cl.sources, source)
}

// Load loads configuration from all sources, merging them by priority
func (cl *ConfigLoader) Load() (*Config, error) {
	// Sort sources by priority (highest first)
	cl.sortSourcesByPriority()

	// Start with default configuration
	config := cl.getDefaultConfig()

	// Load from each source, merging with existing config
	for _, source := range cl.sources {
		sourceConfig, err := source.Load()
		if err != nil {
			return nil, fmt.Errorf("failed to load from source %s: %w", source.Name(), err)
		}

		// Merge configurations
		config = cl.mergeConfigs(config, sourceConfig)
	}

	// Validate the final configuration
	if errors := cl.validator.Validate(config); len(errors) > 0 {
		return nil, fmt.Errorf("configuration validation failed: %v", errors)
	}

	return config, nil
}

// LoadFromFile loads configuration from a specific file
func (cl *ConfigLoader) LoadFromFile(filePath string) (*Config, error) {
	source := &FileConfigSource{
		path:     filePath,
		priority: 100, // High priority for explicit file loading
	}

	cl.sources = []ConfigSource{source}
	return cl.Load()
}

// LoadFromEnvironment loads configuration from environment variables
func (cl *ConfigLoader) LoadFromEnvironment(prefix string) (*Config, error) {
	source := &EnvironmentConfigSource{
		prefix:   prefix,
		priority: 50, // Medium priority for environment variables
	}

	cl.sources = []ConfigSource{source}
	return cl.Load()
}

// LoadFromMultipleSources loads configuration from multiple sources
func (cl *ConfigLoader) LoadFromMultipleSources(sources []ConfigSource) (*Config, error) {
	cl.sources = sources
	return cl.Load()
}

// Private methods

func (cl *ConfigLoader) sortSourcesByPriority() {
	// Simple bubble sort by priority (highest first)
	for i := 0; i < len(cl.sources)-1; i++ {
		for j := 0; j < len(cl.sources)-i-1; j++ {
			if cl.sources[j].Priority() < cl.sources[j+1].Priority() {
				cl.sources[j], cl.sources[j+1] = cl.sources[j+1], cl.sources[j]
			}
		}
	}
}

func (cl *ConfigLoader) getDefaultConfig() *Config {
	return &Config{
		Mode:     ModeLocal,
		Version:  "1.0.0",
		StateDir: "./state",
		CacheDir: "./cache",
		Cloud: CloudConfig{
			Enabled:      false,
			BaseURL:      "",
			APIKey:       "",
			OrgID:        "",
			SyncEnabled:  false,
			SyncInterval: 5 * time.Minute,
		},
		Storage: StorageConfig{
			Backend:     "local",
			LocalPath:   "./data",
			CloudBucket: "",
			CloudRegion: "",
			CloudPrefix: "",
			Credentials: make(map[string]string),
		},
		Database: DatabaseConfig{
			Type:            "postgres",
			Driver:          "postgres",
			DataSourceName:  "",
			MaxOpenConns:    10,
			MaxConnections:  10,
			MaxIdleConns:    5,
			ConnLifetime:    3600 * time.Second,
			ConnMaxLifetime: 3600 * time.Second,
			MigrationsPath:  "./internal/migrations",
			AutoMigrate:     true,
		},
		PostGIS: PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos",
			User:     "arxos",
			Password: "",
			SSLMode:  "disable",
			SRID:     900913,
		},
		API: APIConfig{
			Timeout:       30 * time.Second,
			RetryAttempts: 3,
			RetryDelay:    1 * time.Second,
			UserAgent:     "ArxOS/1.0",
		},
		Telemetry: TelemetryConfig{
			Enabled:     false,
			Endpoint:    "",
			SampleRate:  0.1,
			Debug:       false,
			AnonymousID: "",
		},
		Features: FeatureFlags{
			CloudSync:     false,
			AIIntegration: false,
			OfflineMode:   true,
			BetaFeatures:  false,
			Analytics:     false,
			AutoUpdate:    false,
		},
		Security: SecurityConfig{
			JWTSecret:          "",
			JWTExpiry:          24 * time.Hour,
			SessionTimeout:     24 * time.Hour,
			APIRateLimit:       1000,
			APIRateLimitWindow: 1 * time.Minute,
			EnableAuth:         false,
			EnableTLS:          false,
			TLSCertPath:        "",
			TLSKeyPath:         "",
			AllowedOrigins:     []string{"*"},
			BcryptCost:         10,
		},
		TUI: TUIConfig{
			Enabled:              true,
			Theme:                "auto",
			UpdateInterval:       "1s",
			MaxEquipmentDisplay:  100,
			RealTimeEnabled:      true,
			AnimationsEnabled:    true,
			SpatialPrecision:     "1cm",
			GridScale:            "1:20",
			ShowCoordinates:      true,
			ShowConfidence:       true,
			CompactMode:          false,
			CustomSymbols:        make(map[string]string),
			ColorScheme:          "default",
			Keybindings:          make(map[string]string),
			ViewportSize:         50,
			RefreshRate:          30,
			EnableMouse:          true,
			EnableBracketedPaste: true,
		},
	}
}

func (cl *ConfigLoader) mergeConfigs(base, override *Config) *Config {
	if override == nil {
		return base
	}

	if base == nil {
		return override
	}

	// Create a deep copy of base
	merged := cl.deepCopyConfig(base)

	// Merge each section
	if override.Mode != "" {
		merged.Mode = override.Mode
	}

	if override.Version != "" {
		merged.Version = override.Version
	}

	if override.StateDir != "" {
		merged.StateDir = override.StateDir
	}

	if override.CacheDir != "" {
		merged.CacheDir = override.CacheDir
	}

	// Merge PostGIS config
	merged.PostGIS = cl.mergePostGISConfig(merged.PostGIS, override.PostGIS)

	// Merge API config
	merged.API = cl.mergeAPIConfig(merged.API, override.API)

	// Merge Features
	merged.Features = cl.mergeFeatureFlags(merged.Features, override.Features)

	// Merge Telemetry
	merged.Telemetry = cl.mergeTelemetryConfig(merged.Telemetry, override.Telemetry)

	// Merge Security
	merged.Security = cl.mergeSecurityConfig(merged.Security, override.Security)

	// Merge Storage
	merged.Storage = cl.mergeStorageConfig(merged.Storage, override.Storage)

	// Merge TUI
	merged.TUI = cl.mergeTUIConfig(merged.TUI, override.TUI)

	return merged
}

func (cl *ConfigLoader) deepCopyConfig(config *Config) *Config {
	// Simple deep copy using JSON marshaling/unmarshaling
	data, err := json.Marshal(config)
	if err != nil {
		return config // Return original if copy fails
	}

	var copy Config
	if err := json.Unmarshal(data, &copy); err != nil {
		return config // Return original if copy fails
	}

	return &copy
}

func (cl *ConfigLoader) mergePostGISConfig(base, override PostGISConfig) PostGISConfig {
	merged := base

	if override.Host != "" {
		merged.Host = override.Host
	}

	if override.Port != 0 {
		merged.Port = override.Port
	}

	if override.Database != "" {
		merged.Database = override.Database
	}

	if override.User != "" {
		merged.User = override.User
	}

	if override.Password != "" {
		merged.Password = override.Password
	}

	if override.SSLMode != "" {
		merged.SSLMode = override.SSLMode
	}

	if override.SRID != 0 {
		merged.SRID = override.SRID
	}

	return merged
}

func (cl *ConfigLoader) mergeAPIConfig(base, override APIConfig) APIConfig {
	merged := base

	if override.Timeout != 0 {
		merged.Timeout = override.Timeout
	}

	if override.RetryAttempts != 0 {
		merged.RetryAttempts = override.RetryAttempts
	}

	if override.RetryDelay != 0 {
		merged.RetryDelay = override.RetryDelay
	}

	if override.UserAgent != "" {
		merged.UserAgent = override.UserAgent
	}

	return merged
}

func (cl *ConfigLoader) mergeFeatureFlags(base, override FeatureFlags) FeatureFlags {
	merged := base

	// Override boolean flags
	merged.CloudSync = override.CloudSync
	merged.AIIntegration = override.AIIntegration
	merged.OfflineMode = override.OfflineMode
	merged.BetaFeatures = override.BetaFeatures
	merged.Analytics = override.Analytics
	merged.AutoUpdate = override.AutoUpdate

	return merged
}

func (cl *ConfigLoader) mergeTelemetryConfig(base, override TelemetryConfig) TelemetryConfig {
	merged := base

	if override.Endpoint != "" {
		merged.Endpoint = override.Endpoint
	}

	if override.SampleRate != 0 {
		merged.SampleRate = override.SampleRate
	}

	if override.AnonymousID != "" {
		merged.AnonymousID = override.AnonymousID
	}

	merged.Enabled = override.Enabled
	merged.Debug = override.Debug

	return merged
}

func (cl *ConfigLoader) mergeSecurityConfig(base, override SecurityConfig) SecurityConfig {
	merged := base

	if override.JWTSecret != "" {
		merged.JWTSecret = override.JWTSecret
	}

	if override.JWTExpiry != 0 {
		merged.JWTExpiry = override.JWTExpiry
	}

	if override.SessionTimeout != 0 {
		merged.SessionTimeout = override.SessionTimeout
	}

	if override.APIRateLimit != 0 {
		merged.APIRateLimit = override.APIRateLimit
	}

	if override.APIRateLimitWindow != 0 {
		merged.APIRateLimitWindow = override.APIRateLimitWindow
	}

	if override.TLSCertPath != "" {
		merged.TLSCertPath = override.TLSCertPath
	}

	if override.TLSKeyPath != "" {
		merged.TLSKeyPath = override.TLSKeyPath
	}

	if len(override.AllowedOrigins) > 0 {
		merged.AllowedOrigins = override.AllowedOrigins
	}

	if override.BcryptCost != 0 {
		merged.BcryptCost = override.BcryptCost
	}

	merged.EnableAuth = override.EnableAuth
	merged.EnableTLS = override.EnableTLS

	return merged
}

func (cl *ConfigLoader) mergeStorageConfig(base, override StorageConfig) StorageConfig {
	merged := base

	if override.Backend != "" {
		merged.Backend = override.Backend
	}

	if override.LocalPath != "" {
		merged.LocalPath = override.LocalPath
	}

	if override.CloudBucket != "" {
		merged.CloudBucket = override.CloudBucket
	}

	if override.CloudRegion != "" {
		merged.CloudRegion = override.CloudRegion
	}

	if override.CloudPrefix != "" {
		merged.CloudPrefix = override.CloudPrefix
	}

	if len(override.Credentials) > 0 {
		merged.Credentials = override.Credentials
	}

	merged.S3 = override.S3
	merged.Azure = override.Azure

	return merged
}

func (cl *ConfigLoader) mergeTUIConfig(base, override TUIConfig) TUIConfig {
	merged := base

	if override.Theme != "" {
		merged.Theme = override.Theme
	}

	if override.UpdateInterval != "" {
		merged.UpdateInterval = override.UpdateInterval
	}

	if override.SpatialPrecision != "" {
		merged.SpatialPrecision = override.SpatialPrecision
	}

	if override.GridScale != "" {
		merged.GridScale = override.GridScale
	}

	if override.ColorScheme != "" {
		merged.ColorScheme = override.ColorScheme
	}

	if override.MaxEquipmentDisplay != 0 {
		merged.MaxEquipmentDisplay = override.MaxEquipmentDisplay
	}

	if override.ViewportSize != 0 {
		merged.ViewportSize = override.ViewportSize
	}

	if override.RefreshRate != 0 {
		merged.RefreshRate = override.RefreshRate
	}

	if len(override.CustomSymbols) > 0 {
		merged.CustomSymbols = override.CustomSymbols
	}

	if len(override.Keybindings) > 0 {
		merged.Keybindings = override.Keybindings
	}

	merged.Enabled = override.Enabled
	merged.RealTimeEnabled = override.RealTimeEnabled
	merged.AnimationsEnabled = override.AnimationsEnabled
	merged.ShowCoordinates = override.ShowCoordinates
	merged.ShowConfidence = override.ShowConfidence
	merged.CompactMode = override.CompactMode
	merged.EnableMouse = override.EnableMouse
	merged.EnableBracketedPaste = override.EnableBracketedPaste

	return merged
}

// FileConfigSource implementation

func (fcs *FileConfigSource) Load() (*Config, error) {
	file, err := os.Open(fcs.path)
	if err != nil {
		return nil, fmt.Errorf("failed to open config file: %w", err)
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var config Config

	// Determine format based on file extension
	if strings.HasSuffix(strings.ToLower(fcs.path), ".yml") || strings.HasSuffix(strings.ToLower(fcs.path), ".yaml") {
		if err := yaml.Unmarshal(data, &config); err != nil {
			return nil, fmt.Errorf("failed to parse YAML config file: %w", err)
		}
	} else {
		if err := json.Unmarshal(data, &config); err != nil {
			return nil, fmt.Errorf("failed to parse JSON config file: %w", err)
		}
	}

	return &config, nil
}

func (fcs *FileConfigSource) Priority() int {
	return fcs.priority
}

func (fcs *FileConfigSource) Name() string {
	return fmt.Sprintf("file:%s", fcs.path)
}

// EnvironmentConfigSource implementation

func (ecs *EnvironmentConfigSource) Load() (*Config, error) {
	config := &Config{}

	// Load basic settings
	config.Mode = Mode(os.Getenv(ecs.prefix + "MODE"))
	config.Version = os.Getenv(ecs.prefix + "VERSION")
	config.StateDir = os.Getenv(ecs.prefix + "STATE_DIR")
	config.CacheDir = os.Getenv(ecs.prefix + "CACHE_DIR")

	// Load PostGIS settings
	if os.Getenv(ecs.prefix+"POSTGIS_HOST") != "" {
		config.PostGIS = PostGISConfig{
			Host:     os.Getenv(ecs.prefix + "POSTGIS_HOST"),
			Port:     ecs.getEnvInt(ecs.prefix+"POSTGIS_PORT", 5432),
			Database: os.Getenv(ecs.prefix + "POSTGIS_DATABASE"),
			User:     os.Getenv(ecs.prefix + "POSTGIS_USER"),
			Password: os.Getenv(ecs.prefix + "POSTGIS_PASSWORD"),
			SSLMode:  os.Getenv(ecs.prefix + "POSTGIS_SSL_MODE"),
			SRID:     ecs.getEnvInt(ecs.prefix+"POSTGIS_SRID", 900913),
		}
	}

	// Load API settings
	if os.Getenv(ecs.prefix+"API_TIMEOUT") != "" {
		config.API = APIConfig{
			Timeout:       ecs.getEnvDuration(ecs.prefix+"API_TIMEOUT", 30*time.Second),
			RetryAttempts: ecs.getEnvInt(ecs.prefix+"API_RETRY_ATTEMPTS", 3),
			RetryDelay:    ecs.getEnvDuration(ecs.prefix+"API_RETRY_DELAY", 1*time.Second),
			UserAgent:     os.Getenv(ecs.prefix + "API_USER_AGENT"),
		}
	}

	// Load feature flags
	config.Features = FeatureFlags{
		CloudSync:     ecs.getEnvBool(ecs.prefix+"CLOUD_SYNC", false),
		AIIntegration: ecs.getEnvBool(ecs.prefix+"AI_INTEGRATION", false),
		OfflineMode:   ecs.getEnvBool(ecs.prefix+"OFFLINE_MODE", true),
		BetaFeatures:  ecs.getEnvBool(ecs.prefix+"BETA_FEATURES", false),
		Analytics:     ecs.getEnvBool(ecs.prefix+"ANALYTICS", false),
		AutoUpdate:    ecs.getEnvBool(ecs.prefix+"AUTO_UPDATE", false),
	}

	// Load telemetry settings
	if os.Getenv(ecs.prefix+"TELEMETRY_ENABLED") != "" {
		config.Telemetry = TelemetryConfig{
			Enabled:     ecs.getEnvBool(ecs.prefix+"TELEMETRY_ENABLED", false),
			Endpoint:    os.Getenv(ecs.prefix + "TELEMETRY_ENDPOINT"),
			SampleRate:  ecs.getEnvFloat(ecs.prefix+"TELEMETRY_SAMPLE_RATE", 0.1),
			Debug:       ecs.getEnvBool(ecs.prefix+"TELEMETRY_DEBUG", false),
			AnonymousID: os.Getenv(ecs.prefix + "TELEMETRY_ANONYMOUS_ID"),
		}
	}

	return config, nil
}

func (ecs *EnvironmentConfigSource) Priority() int {
	return ecs.priority
}

func (ecs *EnvironmentConfigSource) Name() string {
	return fmt.Sprintf("environment:%s", ecs.prefix)
}

// DefaultConfigSource implementation

func (dcs *DefaultConfigSource) Load() (*Config, error) {
	loader := NewConfigLoader()
	return loader.getDefaultConfig(), nil
}

func (dcs *DefaultConfigSource) Priority() int {
	return dcs.priority
}

func (dcs *DefaultConfigSource) Name() string {
	return "default"
}

// Helper functions for environment variable parsing

func (ecs *EnvironmentConfigSource) getEnvInt(key string, defaultValue int) int {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}

	if intValue, err := strconv.Atoi(value); err == nil {
		return intValue
	}

	return defaultValue
}

func (ecs *EnvironmentConfigSource) getEnvBool(key string, defaultValue bool) bool {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}

	switch strings.ToLower(value) {
	case "true", "1", "yes", "on":
		return true
	case "false", "0", "no", "off":
		return false
	default:
		return defaultValue
	}
}

func (ecs *EnvironmentConfigSource) getEnvDuration(key string, defaultValue time.Duration) time.Duration {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}

	if duration, err := time.ParseDuration(value); err == nil {
		return duration
	}

	return defaultValue
}

func (ecs *EnvironmentConfigSource) getEnvFloat(key string, defaultValue float64) float64 {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}

	if floatValue, err := strconv.ParseFloat(value, 64); err == nil {
		return floatValue
	}

	return defaultValue
}
