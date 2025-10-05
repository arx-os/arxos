package helpers

import (
	"time"

	"github.com/arx-os/arxos/internal/config"
)

// ConfigBuilder provides a fluent interface for building test configurations
type ConfigBuilder struct {
	config *config.Config
}

// NewConfigBuilder creates a new ConfigBuilder with default values
func NewConfigBuilder() *ConfigBuilder {
	return &ConfigBuilder{
		config: config.Default(),
	}
}

// WithMode sets the mode
func (b *ConfigBuilder) WithMode(mode config.Mode) *ConfigBuilder {
	b.config.Mode = mode
	return b
}

// WithVersion sets the version
func (b *ConfigBuilder) WithVersion(version string) *ConfigBuilder {
	b.config.Version = version
	return b
}

// WithStateDir sets the state directory
func (b *ConfigBuilder) WithStateDir(stateDir string) *ConfigBuilder {
	b.config.StateDir = stateDir
	return b
}

// WithCacheDir sets the cache directory
func (b *ConfigBuilder) WithCacheDir(cacheDir string) *ConfigBuilder {
	b.config.CacheDir = cacheDir
	return b
}

// WithCloudConfig sets the cloud configuration
func (b *ConfigBuilder) WithCloudConfig(cloud config.CloudConfig) *ConfigBuilder {
	b.config.Cloud = cloud
	return b
}

// WithPostGISConfig sets the PostGIS configuration
func (b *ConfigBuilder) WithPostGISConfig(postgis config.PostGISConfig) *ConfigBuilder {
	b.config.PostGIS = postgis
	return b
}

// WithTUIConfig sets the TUI configuration
func (b *ConfigBuilder) WithTUIConfig(tui config.TUIConfig) *ConfigBuilder {
	b.config.TUI = tui
	return b
}

// WithSecurityConfig sets the security configuration
func (b *ConfigBuilder) WithSecurityConfig(security config.SecurityConfig) *ConfigBuilder {
	b.config.Security = security
	return b
}

// WithFeatureFlags sets the feature flags
func (b *ConfigBuilder) WithFeatureFlags(features config.FeatureFlags) *ConfigBuilder {
	b.config.Features = features
	return b
}

// WithTelemetryConfig sets the telemetry configuration
func (b *ConfigBuilder) WithTelemetryConfig(telemetry config.TelemetryConfig) *ConfigBuilder {
	b.config.Telemetry = telemetry
	return b
}

// WithStorageConfig sets the storage configuration
func (b *ConfigBuilder) WithStorageConfig(storage config.StorageConfig) *ConfigBuilder {
	b.config.Storage = storage
	return b
}

// WithAPIConfig sets the API configuration
func (b *ConfigBuilder) WithAPIConfig(api config.APIConfig) *ConfigBuilder {
	b.config.API = api
	return b
}

// WithIFCConfig sets the IFC configuration
func (b *ConfigBuilder) WithIFCConfig(ifc config.IFCConfig) *ConfigBuilder {
	b.config.IFC = ifc
	return b
}

// Build returns the built configuration
func (b *ConfigBuilder) Build() *config.Config {
	return b.config
}

// BuildLocalConfig creates a local configuration for testing
func BuildLocalConfig() *config.Config {
	return NewConfigBuilder().
		WithMode(config.ModeLocal).
		WithVersion("0.1.0-test").
		WithStateDir("/tmp/test-state").
		WithCacheDir("/tmp/test-cache").
		WithPostGISConfig(config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_test",
			User:     "arxos",
			SSLMode:  "disable",
			SRID:     900913,
		}).
		WithTUIConfig(config.TUIConfig{
			Enabled:        true,
			Theme:          "dark",
			UpdateInterval: "1s",
		}).
		WithSecurityConfig(config.SecurityConfig{
			JWTSecret: "test-jwt-secret-12345678901234567890",
			JWTExpiry: 1 * time.Hour,
		}).
		WithFeatureFlags(config.FeatureFlags{
			OfflineMode: true,
		}).
		Build()
}

// BuildCloudConfig creates a cloud configuration for testing
func BuildCloudConfig() *config.Config {
	return NewConfigBuilder().
		WithMode(config.ModeCloud).
		WithVersion("1.0.0-test").
		WithStateDir("/tmp/test-state").
		WithCacheDir("/tmp/test-cache").
		WithCloudConfig(config.CloudConfig{
			Enabled:     true,
			BaseURL:     "https://api.test.arxos.io",
			APIKey:      "test-api-key",
			SyncEnabled: true,
		}).
		WithPostGISConfig(config.PostGISConfig{
			Host:     "test-db-host",
			Port:     5432,
			Database: "arxos_cloud_test",
			User:     "arxos",
			SSLMode:  "require",
			SRID:     900913,
		}).
		WithStorageConfig(config.StorageConfig{
			Backend:     "s3",
			CloudBucket: "test-bucket",
			CloudRegion: "us-east-1",
		}).
		WithSecurityConfig(config.SecurityConfig{
			JWTSecret: "test-jwt-secret-12345678901234567890",
			JWTExpiry: 1 * time.Hour,
		}).
		WithFeatureFlags(config.FeatureFlags{
			CloudSync: true,
		}).
		Build()
}

// BuildTestConfig creates a test configuration for testing
func BuildTestConfig() *config.Config {
	return NewConfigBuilder().
		WithMode(config.ModeLocal).
		WithVersion("0.1.0-test").
		WithStateDir("/tmp/test-state").
		WithCacheDir("/tmp/test-cache").
		WithPostGISConfig(config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_test",
			User:     "arxos_test",
			SSLMode:  "disable",
			SRID:     900913,
		}).
		WithTUIConfig(config.TUIConfig{
			Enabled:        false, // Disabled for testing
			Theme:          "light",
			UpdateInterval: "500ms",
		}).
		WithSecurityConfig(config.SecurityConfig{
			JWTSecret: "test-jwt-secret-12345678901234567890",
			JWTExpiry: 1 * time.Hour,
		}).
		WithFeatureFlags(config.FeatureFlags{
			OfflineMode:  true,
			BetaFeatures: true,
			Analytics:    false,
		}).
		WithTelemetryConfig(config.TelemetryConfig{
			Enabled:    false,
			SampleRate: 0.0,
		}).
		Build()
}

// BuildInvalidConfig creates an invalid configuration for testing error cases
func BuildInvalidConfig() *config.Config {
	return NewConfigBuilder().
		WithMode("invalid-mode").
		WithVersion("").
		WithStateDir("").
		WithCacheDir("").
		WithPostGISConfig(config.PostGISConfig{
			Host:     "",
			Port:     -1,
			Database: "",
			User:     "",
			SSLMode:  "invalid",
		}).
		WithTUIConfig(config.TUIConfig{
			Enabled:        true,
			Theme:          "invalid-theme",
			UpdateInterval: "invalid-duration",
		}).
		WithSecurityConfig(config.SecurityConfig{
			JWTSecret: "",
			JWTExpiry: 0,
		}).
		Build()
}
