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

	"github.com/arx-os/arxos/internal/common/logger"
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
	Mode     Mode   `json:"mode"`
	Version  string `json:"version"`
	StateDir string `json:"state_dir"`
	CacheDir string `json:"cache_dir"`

	// Cloud settings
	Cloud CloudConfig `json:"cloud"`

	// Storage settings
	Storage StorageConfig `json:"storage"`

	// Database settings
	Database DatabaseConfig `json:"database"`
	PostGIS  PostGISConfig  `json:"postgis"`

	// API settings
	API APIConfig `json:"api"`

	// Telemetry settings
	Telemetry TelemetryConfig `json:"telemetry"`

	// Feature flags
	Features FeatureFlags `json:"features"`

	// Security settings
	Security SecurityConfig `json:"security"`
}

// CloudConfig contains cloud-specific configuration
type CloudConfig struct {
	Enabled      bool          `json:"enabled"`
	BaseURL      string        `json:"base_url"`
	APIKey       string        `json:"-"` // Never serialize API keys
	OrgID        string        `json:"org_id"`
	SyncEnabled  bool          `json:"sync_enabled"`
	SyncInterval time.Duration `json:"sync_interval"`
}

// StorageConfig defines storage backend configuration
type StorageConfig struct {
	Backend     string            `json:"backend"` // local, s3, gcs, azure
	LocalPath   string            `json:"local_path"`
	CloudBucket string            `json:"cloud_bucket"`
	CloudRegion string            `json:"cloud_region"`
	CloudPrefix string            `json:"cloud_prefix"`
	Credentials map[string]string `json:"-"` // Sensitive, not serialized
}

// DatabaseConfig defines database configuration (DEPRECATED - use PostGISConfig)
type DatabaseConfig struct {
	Type            string        `json:"type"`   // postgres only
	Driver          string        `json:"driver"` // Legacy field
	DataSourceName  string        `json:"-"`      // Never serialize connection strings
	MaxOpenConns    int           `json:"max_open_conns"`
	MaxConnections  int           `json:"max_connections"` // Alias for MaxOpenConns
	MaxIdleConns    int           `json:"max_idle_conns"`
	ConnLifetime    time.Duration `json:"conn_lifetime"`
	ConnMaxLifetime time.Duration `json:"conn_max_lifetime"` // Alias for ConnLifetime
	MigrationsPath  string        `json:"migrations_path"`
	AutoMigrate     bool          `json:"auto_migrate"`
}

// PostGISConfig defines PostGIS spatial database configuration
type PostGISConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Database string `json:"database"`
	User     string `json:"user"`
	Password string `json:"-"` // Sensitive
	SSLMode  string `json:"ssl_mode"`
	SRID     int    `json:"srid"` // Spatial reference ID (default: 900913)
}

// APIConfig contains API client configuration
type APIConfig struct {
	Timeout       time.Duration `json:"timeout"`
	RetryAttempts int           `json:"retry_attempts"`
	RetryDelay    time.Duration `json:"retry_delay"`
	UserAgent     string        `json:"user_agent"`
}

// TelemetryConfig controls metrics and analytics
type TelemetryConfig struct {
	Enabled     bool    `json:"enabled"`
	Endpoint    string  `json:"endpoint"`
	SampleRate  float64 `json:"sample_rate"`
	Debug       bool    `json:"debug"`
	AnonymousID string  `json:"anonymous_id"`
}

// FeatureFlags controls feature availability
type FeatureFlags struct {
	CloudSync     bool `json:"cloud_sync"`
	AIIntegration bool `json:"ai_integration"`
	OfflineMode   bool `json:"offline_mode"`
	BetaFeatures  bool `json:"beta_features"`
	Analytics     bool `json:"analytics"`
	AutoUpdate    bool `json:"auto_update"`
}

// SecurityConfig contains security-related settings
type SecurityConfig struct {
	JWTSecret          string        `json:"-"` // Never serialize
	JWTExpiry          time.Duration `json:"jwt_expiry"`
	SessionTimeout     time.Duration `json:"session_timeout"`
	APIRateLimit       int           `json:"api_rate_limit"`
	APIRateLimitWindow time.Duration `json:"api_rate_limit_window"`
	EnableAuth         bool          `json:"enable_auth"`
	EnableTLS          bool          `json:"enable_tls"`
	TLSCertPath        string        `json:"tls_cert_path"`
	TLSKeyPath         string        `json:"-"` // Never serialize
	AllowedOrigins     []string      `json:"allowed_origins"`
	BcryptCost         int           `json:"bcrypt_cost"`
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

		Security: SecurityConfig{
			JWTExpiry:          24 * time.Hour,
			SessionTimeout:     30 * time.Minute,
			APIRateLimit:       100,
			APIRateLimitWindow: 1 * time.Minute,
			EnableAuth:         true,
			EnableTLS:          false,
			AllowedOrigins:     []string{"http://localhost:3000"},
			BcryptCost:         12,
		},

		Database: DatabaseConfig{
			Type:            "postgres",
			Driver:          "postgres", // Legacy field
			DataSourceName:  "",         // Set from environment
			MaxOpenConns:    25,
			MaxConnections:  25, // Alias
			MaxIdleConns:    5,
			ConnLifetime:    30 * time.Minute,
			ConnMaxLifetime: 30 * time.Minute, // Alias
			MigrationsPath:  "./migrations",
			AutoMigrate:     true,
		},

		PostGIS: PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos",
			User:     "arxos",
			Password: "",
			SSLMode:  "disable",
			SRID:     900913, // Web Mercator with millimeter precision
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

	// Security settings from environment
	if secret := os.Getenv("ARXOS_JWT_SECRET"); secret != "" {
		c.Security.JWTSecret = secret
	} else {
		// Generate a random secret if not provided (development only)
		if c.Mode == ModeLocal {
			c.Security.JWTSecret = generateDevSecret()
		}
	}

	if auth := os.Getenv("ARXOS_ENABLE_AUTH"); auth == "false" {
		c.Security.EnableAuth = false
	}

	if tls := os.Getenv("ARXOS_ENABLE_TLS"); tls == "true" {
		c.Security.EnableTLS = true
	}

	if cert := os.Getenv("ARXOS_TLS_CERT"); cert != "" {
		c.Security.TLSCertPath = cert
	}

	if key := os.Getenv("ARXOS_TLS_KEY"); key != "" {
		c.Security.TLSKeyPath = key
	}

	if origins := os.Getenv("ARXOS_ALLOWED_ORIGINS"); origins != "" {
		c.Security.AllowedOrigins = strings.Split(origins, ",")
	}

	// Database settings from environment
	if dbType := os.Getenv("ARXOS_DB_TYPE"); dbType != "" {
		c.Database.Type = dbType
	}
	if driver := os.Getenv("ARXOS_DB_DRIVER"); driver != "" {
		c.Database.Driver = driver
	}
	// Path field removed - PostGIS only uses DataSourceName

	if dsn := os.Getenv("ARXOS_DATABASE_URL"); dsn != "" {
		c.Database.DataSourceName = dsn
	} else if c.Database.Driver == "postgres" {
		// Build PostgreSQL DSN from individual components
		c.Database.DataSourceName = buildPostgresDSN()
	}

	if maxConn := os.Getenv("ARXOS_DB_MAX_CONNECTIONS"); maxConn != "" {
		if val, err := parseIntEnv(maxConn); err == nil {
			c.Database.MaxConnections = val
			c.Database.MaxOpenConns = val
		}
	}

	// PostGIS settings from environment
	if host := os.Getenv("POSTGIS_HOST"); host != "" {
		c.PostGIS.Host = host
	}
	if port := os.Getenv("POSTGIS_PORT"); port != "" {
		if val, err := parseIntEnv(port); err == nil {
			c.PostGIS.Port = val
		}
	}
	if database := os.Getenv("POSTGIS_DATABASE"); database != "" {
		c.PostGIS.Database = database
	}
	if user := os.Getenv("POSTGIS_USER"); user != "" {
		c.PostGIS.User = user
	}
	if password := os.Getenv("POSTGIS_PASSWORD"); password != "" {
		c.PostGIS.Password = password
	}
	if sslMode := os.Getenv("POSTGIS_SSLMODE"); sslMode != "" {
		c.PostGIS.SSLMode = sslMode
	}
	if srid := os.Getenv("POSTGIS_SRID"); srid != "" {
		if val, err := parseIntEnv(srid); err == nil {
			c.PostGIS.SRID = val
		}
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

	// Validate security settings
	if c.Mode != ModeLocal && c.Security.JWTSecret == "" {
		return fmt.Errorf("JWT secret required for non-local modes (set ARXOS_JWT_SECRET)")
	}

	if c.Security.EnableTLS {
		if c.Security.TLSCertPath == "" || c.Security.TLSKeyPath == "" {
			return fmt.Errorf("TLS certificate and key paths required when TLS is enabled")
		}
	}

	// Validate database settings
	switch c.Database.Type {
	case "sqlite", "postgis", "hybrid":
		// Valid types
	case "": // Default to checking driver for backward compatibility
		switch c.Database.Driver {
		case "sqlite", "postgres":
			// Valid drivers
		default:
			return fmt.Errorf("invalid database driver: %s", c.Database.Driver)
		}
	default:
		return fmt.Errorf("invalid database type: %s", c.Database.Type)
	}

	// Validate PostGIS configuration if using PostGIS
	if c.Database.Type == "postgis" || c.Database.Type == "hybrid" {
		if c.PostGIS.Host == "" {
			return fmt.Errorf("PostGIS host required when using PostGIS database")
		}
		if c.PostGIS.Port == 0 {
			c.PostGIS.Port = 5432 // Set default
		}
		if c.PostGIS.Database == "" {
			return fmt.Errorf("PostGIS database name required")
		}
		if c.PostGIS.User == "" {
			return fmt.Errorf("PostGIS user required")
		}
		if c.PostGIS.SRID == 0 {
			c.PostGIS.SRID = 900913 // Set default
		}
	}

	// Validate SQLite path for SQLite or hybrid
	if c.Database.Type == "sqlite" || c.Database.Type == "hybrid" || c.Database.Type == "" {
		if c.Database.DataSourceName == "" {
			return fmt.Errorf("database path or connection string required")
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
	configCopy.Cloud.APIKey = ""            // Never save API keys
	configCopy.Security.JWTSecret = ""      // Never save JWT secrets
	configCopy.Security.TLSKeyPath = ""     // Never save TLS key paths
	configCopy.Database.DataSourceName = "" // Never save connection strings

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

// GetDatabaseConfig returns a database.DatabaseConfig from the main config
func (c *Config) GetDatabaseConfig() *DatabaseConfig {
	return &DatabaseConfig{
		Type:            c.Database.Type,
		Driver:          c.Database.Driver,
		DataSourceName:  c.Database.DataSourceName,
		MaxOpenConns:    c.Database.MaxOpenConns,
		MaxConnections:  c.Database.MaxConnections,
		MaxIdleConns:    c.Database.MaxIdleConns,
		ConnLifetime:    c.Database.ConnLifetime,
		ConnMaxLifetime: c.Database.ConnMaxLifetime,
		MigrationsPath:  c.Database.MigrationsPath,
		AutoMigrate:     c.Database.AutoMigrate,
	}
}

// GetPostGISConfig returns the PostGIS configuration
func (c *Config) GetPostGISConfig() *PostGISConfig {
	return &PostGISConfig{
		Host:     c.PostGIS.Host,
		Port:     c.PostGIS.Port,
		Database: c.PostGIS.Database,
		User:     c.PostGIS.User,
		Password: c.PostGIS.Password,
		SSLMode:  c.PostGIS.SSLMode,
		SRID:     c.PostGIS.SRID,
	}
}

// BuildPostGISConnectionString builds a PostgreSQL connection string from PostGIS config
func (c *Config) BuildPostGISConnectionString() string {
	dsn := fmt.Sprintf("host=%s port=%d user=%s dbname=%s sslmode=%s",
		c.PostGIS.Host, c.PostGIS.Port, c.PostGIS.User, c.PostGIS.Database, c.PostGIS.SSLMode)

	if c.PostGIS.Password != "" {
		dsn = fmt.Sprintf("%s password=%s", dsn, c.PostGIS.Password)
	}

	return dsn
}

// Helper functions

// generateDevSecret generates a random JWT secret for development
func generateDevSecret() string {
	logger.Warn("Generating random JWT secret for development mode. Set ARXOS_JWT_SECRET for production.")
	// Simple dev secret (in production, this would use crypto/rand)
	return fmt.Sprintf("dev-secret-%d", time.Now().UnixNano())
}

// buildPostgresDSN builds a PostgreSQL connection string from environment variables
func buildPostgresDSN() string {
	host := getEnvOrDefault("ARXOS_DB_HOST", "localhost")
	port := getEnvOrDefault("ARXOS_DB_PORT", "5432")
	user := getEnvOrDefault("ARXOS_DB_USER", "arxos")
	password := os.Getenv("ARXOS_DB_PASSWORD")
	dbname := getEnvOrDefault("ARXOS_DB_NAME", "arxos")
	sslmode := getEnvOrDefault("ARXOS_DB_SSLMODE", "disable")

	dsn := fmt.Sprintf("host=%s port=%s user=%s dbname=%s sslmode=%s",
		host, port, user, dbname, sslmode)

	if password != "" {
		dsn = fmt.Sprintf("%s password=%s", dsn, password)
	}

	return dsn
}

// getEnvOrDefault returns environment variable value or default
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// parseIntEnv parses integer from environment variable
func parseIntEnv(value string) (int, error) {
	var result int
	_, err := fmt.Sscanf(value, "%d", &result)
	return result, err
}
