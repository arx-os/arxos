// Package config provides configuration management for ArxOS applications.
// It handles loading, validation, and management of configuration settings from
// files and environment variables, supporting development and production modes.
package config

import (
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
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
	Mode     Mode   `json:"mode" yaml:"mode"`
	Version  string `json:"version" yaml:"version"`
	StateDir string `json:"state_dir" yaml:"state_dir"`
	CacheDir string `json:"cache_dir" yaml:"cache_dir"`

	// Cloud settings
	Cloud CloudConfig `json:"cloud" yaml:"cloud"`

	// Storage settings
	Storage StorageConfig `json:"storage" yaml:"storage"`

	// Database settings
	Database DatabaseConfig `json:"database" yaml:"database"`
	PostGIS  PostGISConfig  `json:"postgis" yaml:"postgis"`

	// API settings
	API APIConfig `json:"api" yaml:"api"`

	// Telemetry settings
	Telemetry TelemetryConfig `json:"telemetry" yaml:"telemetry"`

	// Feature flags
	Features FeatureFlags `json:"features" yaml:"features"`

	// Security settings
	Security SecurityConfig `json:"security" yaml:"security"`

	// TUI settings
	TUI TUIConfig `json:"tui" yaml:"tui"`

	// IFC settings
	IFC IFCConfig `json:"ifc" yaml:"ifc"`
}

// CloudConfig contains cloud-specific configuration
type CloudConfig struct {
	Enabled      bool          `json:"enabled" yaml:"enabled"`
	BaseURL      string        `json:"base_url" yaml:"base_url"`
	APIKey       string        `json:"-" yaml:"-"` // Never serialize API keys
	OrgID        string        `json:"org_id" yaml:"org_id"`
	SyncEnabled  bool          `json:"sync_enabled" yaml:"sync_enabled"`
	SyncInterval time.Duration `json:"sync_interval" yaml:"sync_interval"`
}

// StorageConfig defines storage backend configuration
type StorageConfig struct {
	Backend     string            `json:"backend" yaml:"backend"` // local, s3, gcs, azure
	LocalPath   string            `json:"local_path" yaml:"local_path"`
	CloudBucket string            `json:"cloud_bucket" yaml:"cloud_bucket"`
	CloudRegion string            `json:"cloud_region" yaml:"cloud_region"`
	CloudPrefix string            `json:"cloud_prefix" yaml:"cloud_prefix"`
	Credentials map[string]string `json:"-" yaml:"-"` // Sensitive, not serialized

	// Data directory configuration
	Data DataConfig `json:"data" yaml:"data"`

	// S3-specific configuration
	S3 S3Config `json:"s3,omitempty" yaml:"s3,omitempty"`

	// Azure-specific configuration
	Azure AzureConfig `json:"azure,omitempty" yaml:"azure,omitempty"`
}

// DataConfig defines data directory configuration for building repositories
type DataConfig struct {
	BasePath        string `json:"base_path"`        // Base directory for all ArxOS data
	RepositoriesDir string `json:"repositories_dir"` // Subdirectory for building repositories
	CacheDir        string `json:"cache_dir"`        // Subdirectory for cache data
	LogsDir         string `json:"logs_dir"`         // Subdirectory for log files
	TempDir         string `json:"temp_dir"`         // Subdirectory for temporary files
}

// S3Config contains S3-specific configuration
type S3Config struct {
	Region          string `json:"region"`
	Bucket          string `json:"bucket"`
	AccessKeyID     string `json:"-"` // Sensitive
	SecretAccessKey string `json:"-"` // Sensitive
	Endpoint        string `json:"endpoint,omitempty"`
	UseSSL          bool   `json:"use_ssl"`
}

// AzureConfig contains Azure-specific configuration
type AzureConfig struct {
	AccountName      string `json:"account_name"`
	AccountKey       string `json:"-"` // Sensitive
	ContainerName    string `json:"container_name"`
	SASToken         string `json:"-"` // Sensitive
	ConnectionString string `json:"-"` // Sensitive
}

// DatabaseConfig defines database configuration (DEPRECATED - use PostGISConfig)
type DatabaseConfig struct {
	Type            string        `json:"type"`   // postgres only
	Driver          string        `json:"driver"` // Legacy field
	DataSourceName  string        `json:"-"`      // Never serialize connection strings
	URL             string        `json:"-"`      // Database URL from environment
	Host            string        `json:"host"`
	Port            int           `json:"port"`
	Database        string        `json:"database"`
	Username        string        `json:"username"`
	Password        string        `json:"-"` // Never serialize passwords
	SSLMode         string        `json:"ssl_mode"`
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
	Host     string `json:"host" yaml:"host"`
	Port     int    `json:"port" yaml:"port"`
	Database string `json:"database" yaml:"database"`
	User     string `json:"user" yaml:"user"`
	Password string `json:"-" yaml:"-"` // Sensitive
	SSLMode  string `json:"ssl_mode" yaml:"ssl_mode"`
	SRID     int    `json:"srid" yaml:"srid"` // Spatial reference ID (default: 900913)
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
	CloudSync     bool `json:"cloud_sync" yaml:"cloud_sync"`
	AIIntegration bool `json:"ai_integration" yaml:"ai_integration"`
	OfflineMode   bool `json:"offline_mode" yaml:"offline_mode"`
	BetaFeatures  bool `json:"beta_features" yaml:"beta_features"`
	Analytics     bool `json:"analytics" yaml:"analytics"`
	AutoUpdate    bool `json:"auto_update" yaml:"auto_update"`
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

// TUIConfig contains Terminal User Interface settings
type TUIConfig struct {
	// Core TUI settings
	Enabled        bool   `json:"enabled"`
	Theme          string `json:"theme"`           // dark, light, auto
	UpdateInterval string `json:"update_interval"` // e.g., "1s", "500ms"

	// Performance settings
	MaxEquipmentDisplay int  `json:"max_equipment_display"`
	RealTimeEnabled     bool `json:"real_time_enabled"`
	AnimationsEnabled   bool `json:"animations_enabled"`

	// Spatial settings
	SpatialPrecision string `json:"spatial_precision"` // e.g., "1mm", "1cm"
	GridScale        string `json:"grid_scale"`        // e.g., "1:10", "1:20"

	// UI settings
	ShowCoordinates bool `json:"show_coordinates"`
	ShowConfidence  bool `json:"show_confidence"`
	CompactMode     bool `json:"compact_mode"`

	// Advanced settings
	CustomSymbols        map[string]string `json:"custom_symbols"`         // Custom equipment symbols
	ColorScheme          string            `json:"color_scheme"`           // Custom color scheme name
	Keybindings          map[string]string `json:"keybindings"`            // Custom key bindings
	ViewportSize         int               `json:"viewport_size"`          // Number of items in viewport
	RefreshRate          int               `json:"refresh_rate"`           // FPS for animations
	EnableMouse          bool              `json:"enable_mouse"`           // Mouse support
	EnableBracketedPaste bool              `json:"enable_bracketed_paste"` // Paste support
}

// IFCConfig contains IFC processing configuration
type IFCConfig struct {
	Service     IFCServiceConfig     `json:"service"`
	Fallback    IFCFallbackConfig    `json:"fallback"`
	Performance IFCPerformanceConfig `json:"performance"`
}

// IFCServiceConfig contains IfcOpenShell service configuration
type IFCServiceConfig struct {
	Enabled        bool                    `json:"enabled"`
	URL            string                  `json:"url"`
	Timeout        string                  `json:"timeout"`
	Retries        int                     `json:"retries"`
	CircuitBreaker IFCCircuitBreakerConfig `json:"circuit_breaker"`
}

// IFCFallbackConfig contains fallback parser configuration
type IFCFallbackConfig struct {
	Enabled bool   `json:"enabled"`
	Parser  string `json:"parser"` // "native"
}

// IFCPerformanceConfig contains performance-related configuration
type IFCPerformanceConfig struct {
	CacheEnabled bool   `json:"cache_enabled"`
	CacheTTL     string `json:"cache_ttl"`
	MaxFileSize  string `json:"max_file_size"`
}

// IFCCircuitBreakerConfig contains circuit breaker configuration
type IFCCircuitBreakerConfig struct {
	Enabled          bool   `json:"enabled"`
	FailureThreshold int    `json:"failure_threshold"`
	RecoveryTimeout  string `json:"recovery_timeout"`
}

// Validate validates the TUI configuration
func (c *TUIConfig) Validate() error {
	// Validate update interval
	if _, err := time.ParseDuration(c.UpdateInterval); err != nil {
		return fmt.Errorf("invalid update_interval: %w", err)
	}

	// Validate theme
	if c.Theme != "dark" && c.Theme != "light" && c.Theme != "auto" {
		return fmt.Errorf("invalid theme: %s (must be dark, light, or auto)", c.Theme)
	}

	// Validate max equipment display
	if c.MaxEquipmentDisplay <= 0 {
		return fmt.Errorf("max_equipment_display must be positive")
	}

	// Validate spatial precision
	if c.SpatialPrecision != "" {
		validPrecisions := []string{"1mm", "1cm", "10cm", "1m"}
		valid := false
		for _, p := range validPrecisions {
			if c.SpatialPrecision == p {
				valid = true
				break
			}
		}
		if !valid {
			return fmt.Errorf("invalid spatial_precision: %s (must be one of: 1mm, 1cm, 10cm, 1m)", c.SpatialPrecision)
		}
	}

	// Validate grid scale
	if c.GridScale != "" {
		validScales := []string{"1:5", "1:10", "1:20", "1:50", "1:100"}
		valid := false
		for _, s := range validScales {
			if c.GridScale == s {
				valid = true
				break
			}
		}
		if !valid {
			return fmt.Errorf("invalid grid_scale: %s (must be one of: 1:5, 1:10, 1:20, 1:50, 1:100)", c.GridScale)
		}
	}

	// Validate viewport size
	if c.ViewportSize <= 0 {
		c.ViewportSize = 20 // Set default
	}

	// Validate refresh rate
	if c.RefreshRate <= 0 {
		c.RefreshRate = 30 // Set default
	}

	return nil
}

// ParseUpdateInterval parses the update interval string into a time.Duration
func (c *TUIConfig) ParseUpdateInterval() (time.Duration, error) {
	return time.ParseDuration(c.UpdateInterval)
}

// IsDarkTheme returns true if the theme is dark
func (c *TUIConfig) IsDarkTheme() bool {
	return c.Theme == "dark" || c.Theme == "auto"
}

// IsLightTheme returns true if the theme is light
func (c *TUIConfig) IsLightTheme() bool {
	return c.Theme == "light"
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
			Data: DataConfig{
				BasePath:        filepath.Join(homeDir, ".arxos"),
				RepositoriesDir: "repositories",
				CacheDir:        "cache",
				LogsDir:         "logs",
				TempDir:         "temp",
			},
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
			Type:            "postgis",                                    // Default to postgis
			Driver:          "postgres",                                   // Legacy field
			DataSourceName:  "postgres://localhost/arxos?sslmode=disable", // Default PostGIS path
			MaxOpenConns:    25,
			MaxConnections:  25, // Alias
			MaxIdleConns:    5,
			ConnLifetime:    30 * time.Minute,
			ConnMaxLifetime: 30 * time.Minute, // Alias
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
			SRID:     900913, // Web Mercator with millimeter precision
		},

		TUI: TUIConfig{
			Enabled:             true,
			Theme:               "dark",
			UpdateInterval:      "1s",
			MaxEquipmentDisplay: 1000,
			RealTimeEnabled:     true,
			AnimationsEnabled:   true,
			SpatialPrecision:    "1mm",
			GridScale:           "1:10",
			ShowCoordinates:     true,
			ShowConfidence:      true,
			CompactMode:         false,
			CustomSymbols: map[string]string{
				"hvac":        "H",
				"electrical":  "E",
				"fire_safety": "F",
				"plumbing":    "P",
				"lighting":    "L",
				"outlet":      "O",
				"sensor":      "S",
				"camera":      "C",
			},
			ColorScheme:          "default",
			Keybindings:          make(map[string]string),
			ViewportSize:         20,
			RefreshRate:          30,
			EnableMouse:          true,
			EnableBracketedPaste: true,
		},

		IFC: IFCConfig{
			Service: IFCServiceConfig{
				Enabled: true,
				URL:     "http://localhost:5000",
				Timeout: "30s",
				Retries: 3,
				CircuitBreaker: IFCCircuitBreakerConfig{
					Enabled:          true,
					FailureThreshold: 5,
					RecoveryTimeout:  "60s",
				},
			},
			Fallback: IFCFallbackConfig{
				Enabled: true,
				Parser:  "native",
			},
			Performance: IFCPerformanceConfig{
				CacheEnabled: true,
				CacheTTL:     "1h",
				MaxFileSize:  "100MB",
			},
		},
	}
}

// Load loads configuration from file or environment
func Load(configPath string) (*Config, error) {
	config := Default()

	// Load from file if it exists
	if configPath != "" {
		if err := config.LoadFromFile(configPath); err != nil {
			fmt.Printf("Warning: Failed to load config file, using defaults: %v\n", err)
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

// LoadFromFile loads configuration from a JSON or YAML file
func (c *Config) LoadFromFile(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("failed to read config file: %w", err)
	}

	// Process environment variable substitution before parsing
	data = []byte(substituteEnvVars(string(data)))

	// Determine format based on file extension
	if strings.HasSuffix(strings.ToLower(path), ".yml") || strings.HasSuffix(strings.ToLower(path), ".yaml") {
		if err := yaml.Unmarshal(data, c); err != nil {
			return fmt.Errorf("failed to parse YAML config file: %w", err)
		}
	} else {
		if err := json.Unmarshal(data, c); err != nil {
			return fmt.Errorf("failed to parse JSON config file: %w", err)
		}
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

	// Database settings
	if dbURL := os.Getenv("ARXOS_DATABASE_URL"); dbURL != "" {
		c.Database.URL = dbURL
		c.Database.DataSourceName = dbURL
		// Parse URL components for individual fields
		c.parseDatabaseURL(dbURL)
	}
	if host := os.Getenv("ARXOS_DB_HOST"); host != "" {
		c.Database.Host = host
	}
	if port := os.Getenv("ARXOS_DB_PORT"); port != "" {
		if p, err := strconv.Atoi(port); err == nil {
			c.Database.Port = p
		}
	}
	if database := os.Getenv("ARXOS_DB_NAME"); database != "" {
		c.Database.Database = database
	}
	if username := os.Getenv("ARXOS_DB_USER"); username != "" {
		c.Database.Username = username
	}
	if password := os.Getenv("ARXOS_DB_PASSWORD"); password != "" {
		c.Database.Password = password
	}
	if sslMode := os.Getenv("ARXOS_DB_SSL_MODE"); sslMode != "" {
		c.Database.SSLMode = sslMode
	}
	if bucket := os.Getenv("ARXOS_STORAGE_BUCKET"); bucket != "" {
		c.Storage.CloudBucket = bucket
	}
	if region := os.Getenv("ARXOS_STORAGE_REGION"); region != "" {
		c.Storage.CloudRegion = region
	}

	// Data directory settings
	if basePath := os.Getenv("ARXOS_DATA_PATH"); basePath != "" {
		c.Storage.Data.BasePath = basePath
	}
	if reposDir := os.Getenv("ARXOS_REPOSITORIES_DIR"); reposDir != "" {
		c.Storage.Data.RepositoriesDir = reposDir
	}
	if cacheDir := os.Getenv("ARXOS_CACHE_DIR"); cacheDir != "" {
		c.Storage.Data.CacheDir = cacheDir
	}
	if logsDir := os.Getenv("ARXOS_LOGS_DIR"); logsDir != "" {
		c.Storage.Data.LogsDir = logsDir
	}
	if tempDir := os.Getenv("ARXOS_TEMP_DIR"); tempDir != "" {
		c.Storage.Data.TempDir = tempDir
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

	// S3 credentials
	if key := os.Getenv("AWS_ACCESS_KEY_ID"); key != "" {
		c.Storage.S3.AccessKeyID = key
		c.Storage.Credentials["aws_access_key_id"] = key
	}
	if secret := os.Getenv("AWS_SECRET_ACCESS_KEY"); secret != "" {
		c.Storage.S3.SecretAccessKey = secret
		c.Storage.Credentials["aws_secret_access_key"] = secret
	}
	if region := os.Getenv("AWS_DEFAULT_REGION"); region != "" {
		c.Storage.S3.Region = region
	}
	if bucket := os.Getenv("AWS_S3_BUCKET"); bucket != "" {
		c.Storage.S3.Bucket = bucket
	}
	if endpoint := os.Getenv("AWS_S3_ENDPOINT"); endpoint != "" {
		c.Storage.S3.Endpoint = endpoint
	}
	if ssl := os.Getenv("AWS_S3_USE_SSL"); ssl == "false" {
		c.Storage.S3.UseSSL = false
	} else {
		c.Storage.S3.UseSSL = true
	}

	// Azure credentials
	if account := os.Getenv("AZURE_STORAGE_ACCOUNT"); account != "" {
		c.Storage.Azure.AccountName = account
	}
	if key := os.Getenv("AZURE_STORAGE_KEY"); key != "" {
		c.Storage.Azure.AccountKey = key
	}
	if container := os.Getenv("AZURE_STORAGE_CONTAINER"); container != "" {
		c.Storage.Azure.ContainerName = container
	}
	if sas := os.Getenv("AZURE_STORAGE_SAS_TOKEN"); sas != "" {
		c.Storage.Azure.SASToken = sas
	}
	if connStr := os.Getenv("AZURE_STORAGE_CONNECTION_STRING"); connStr != "" {
		c.Storage.Azure.ConnectionString = connStr
	}

	// GCP credentials
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

	// TUI settings
	if enabled := os.Getenv("ARXOS_TUI_ENABLED"); enabled == "true" || enabled == "false" {
		c.TUI.Enabled = enabled == "true"
	}
	if theme := os.Getenv("ARXOS_TUI_THEME"); theme != "" {
		c.TUI.Theme = theme
	}
	if interval := os.Getenv("ARXOS_TUI_UPDATE_INTERVAL"); interval != "" {
		c.TUI.UpdateInterval = interval
	}
	if maxEquip := os.Getenv("ARXOS_TUI_MAX_EQUIPMENT"); maxEquip != "" {
		if val, err := parseIntEnv(maxEquip); err == nil {
			c.TUI.MaxEquipmentDisplay = val
		}
	}
	if realtime := os.Getenv("ARXOS_TUI_REALTIME"); realtime == "true" || realtime == "false" {
		c.TUI.RealTimeEnabled = realtime == "true"
	}
	if animations := os.Getenv("ARXOS_TUI_ANIMATIONS"); animations == "true" || animations == "false" {
		c.TUI.AnimationsEnabled = animations == "true"
	}
	if precision := os.Getenv("ARXOS_TUI_SPATIAL_PRECISION"); precision != "" {
		c.TUI.SpatialPrecision = precision
	}
	if scale := os.Getenv("ARXOS_TUI_GRID_SCALE"); scale != "" {
		c.TUI.GridScale = scale
	}
	if coords := os.Getenv("ARXOS_TUI_SHOW_COORDINATES"); coords == "true" || coords == "false" {
		c.TUI.ShowCoordinates = coords == "true"
	}
	if confidence := os.Getenv("ARXOS_TUI_SHOW_CONFIDENCE"); confidence == "true" || confidence == "false" {
		c.TUI.ShowConfidence = confidence == "true"
	}
	if compact := os.Getenv("ARXOS_TUI_COMPACT_MODE"); compact == "true" || compact == "false" {
		c.TUI.CompactMode = compact == "true"
	}
	if colorScheme := os.Getenv("ARXOS_TUI_COLOR_SCHEME"); colorScheme != "" {
		c.TUI.ColorScheme = colorScheme
	}
	if viewport := os.Getenv("ARXOS_TUI_VIEWPORT_SIZE"); viewport != "" {
		if val, err := parseIntEnv(viewport); err == nil {
			c.TUI.ViewportSize = val
		}
	}
	if refreshRate := os.Getenv("ARXOS_TUI_REFRESH_RATE"); refreshRate != "" {
		if val, err := parseIntEnv(refreshRate); err == nil {
			c.TUI.RefreshRate = val
		}
	}
	if mouse := os.Getenv("ARXOS_TUI_ENABLE_MOUSE"); mouse == "true" || mouse == "false" {
		c.TUI.EnableMouse = mouse == "true"
	}
	if paste := os.Getenv("ARXOS_TUI_ENABLE_BRACKETED_PASTE"); paste == "true" || paste == "false" {
		c.TUI.EnableBracketedPaste = paste == "true"
	}

	// IFC settings
	if enabled := os.Getenv("ARXOS_IFC_SERVICE_ENABLED"); enabled == "true" || enabled == "false" {
		c.IFC.Service.Enabled = enabled == "true"
	}
	if url := os.Getenv("ARXOS_IFC_SERVICE_URL"); url != "" {
		c.IFC.Service.URL = url
	}
	if timeout := os.Getenv("ARXOS_IFC_SERVICE_TIMEOUT"); timeout != "" {
		c.IFC.Service.Timeout = timeout
	}
	if retries := os.Getenv("ARXOS_IFC_SERVICE_RETRIES"); retries != "" {
		if val, err := parseIntEnv(retries); err == nil {
			c.IFC.Service.Retries = val
		}
	}
	if enabled := os.Getenv("ARXOS_IFC_FALLBACK_ENABLED"); enabled == "true" || enabled == "false" {
		c.IFC.Fallback.Enabled = enabled == "true"
	}
	if parser := os.Getenv("ARXOS_IFC_FALLBACK_PARSER"); parser != "" {
		c.IFC.Fallback.Parser = parser
	}
	if cacheEnabled := os.Getenv("ARXOS_IFC_CACHE_ENABLED"); cacheEnabled == "true" || cacheEnabled == "false" {
		c.IFC.Performance.CacheEnabled = cacheEnabled == "true"
	}
	if cacheTTL := os.Getenv("ARXOS_IFC_CACHE_TTL"); cacheTTL != "" {
		c.IFC.Performance.CacheTTL = cacheTTL
	}
	if maxFileSize := os.Getenv("ARXOS_IFC_MAX_FILE_SIZE"); maxFileSize != "" {
		c.IFC.Performance.MaxFileSize = maxFileSize
	}
	if enabled := os.Getenv("ARXOS_IFC_CIRCUIT_BREAKER_ENABLED"); enabled == "true" || enabled == "false" {
		c.IFC.Service.CircuitBreaker.Enabled = enabled == "true"
	}
	if threshold := os.Getenv("ARXOS_IFC_CIRCUIT_BREAKER_THRESHOLD"); threshold != "" {
		if val, err := parseIntEnv(threshold); err == nil {
			c.IFC.Service.CircuitBreaker.FailureThreshold = val
		}
	}
	if timeout := os.Getenv("ARXOS_IFC_CIRCUIT_BREAKER_TIMEOUT"); timeout != "" {
		c.IFC.Service.CircuitBreaker.RecoveryTimeout = timeout
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
			fmt.Printf("Warning: No API key configured for cloud mode\n")
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
	case "postgis":
		// Valid types
	case "": // Default to checking driver for backward compatibility
		switch c.Database.Driver {
		case "postgres":
			// Valid drivers
		default:
			return fmt.Errorf("invalid database driver: %s", c.Database.Driver)
		}
	default:
		return fmt.Errorf("invalid database type: %s", c.Database.Type)
	}

	// Validate PostGIS configuration if using PostGIS
	if c.Database.Type == "postgis" {
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

	// Validate PostGIS connection
	if c.Database.Type == "postgis" || c.Database.Type == "" {
		if c.Database.DataSourceName == "" {
			return fmt.Errorf("database path or connection string required")
		}
	}

	// Validate TUI configuration
	if err := c.TUI.Validate(); err != nil {
		return fmt.Errorf("invalid TUI configuration: %w", err)
	}

	return nil
}

// EnsureDirectories creates necessary directories
func (c *Config) EnsureDirectories() error {
	dirs := []string{
		c.StateDir,
		c.CacheDir,
		c.Storage.LocalPath,
		c.Storage.Data.BasePath,
		filepath.Join(c.Storage.Data.BasePath, c.Storage.Data.RepositoriesDir),
		filepath.Join(c.Storage.Data.BasePath, c.Storage.Data.CacheDir),
		filepath.Join(c.Storage.Data.BasePath, c.Storage.Data.LogsDir),
		filepath.Join(c.Storage.Data.BasePath, c.Storage.Data.TempDir),
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

	// Check current directory for YAML files first
	if _, err := os.Stat("arxos.yml"); err == nil {
		return "arxos.yml"
	}
	if _, err := os.Stat("arxos.yaml"); err == nil {
		return "arxos.yaml"
	}
	if _, err := os.Stat("arxos.json"); err == nil {
		return "arxos.json"
	}

	// Use home directory - prefer YAML
	homeDir, _ := os.UserHomeDir()
	yamlPath := filepath.Join(homeDir, ".arxos", "config.yml")
	if _, err := os.Stat(yamlPath); err == nil {
		return yamlPath
	}
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

// GetRepositoriesPath returns the full path to the repositories directory
func (c *Config) GetRepositoriesPath() string {
	return filepath.Join(c.Storage.Data.BasePath, c.Storage.Data.RepositoriesDir)
}

// GetCachePath returns the full path to the cache directory
func (c *Config) GetCachePath() string {
	return filepath.Join(c.Storage.Data.BasePath, c.Storage.Data.CacheDir)
}

// GetLogsPath returns the full path to the logs directory
func (c *Config) GetLogsPath() string {
	return filepath.Join(c.Storage.Data.BasePath, c.Storage.Data.LogsDir)
}

// GetTempPath returns the full path to the temp directory
func (c *Config) GetTempPath() string {
	return filepath.Join(c.Storage.Data.BasePath, c.Storage.Data.TempDir)
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
	fmt.Printf("Warning: Generating random JWT secret for development mode. Set ARXOS_JWT_SECRET for production.\n")
	// Simple dev secret (in production, this would use crypto/rand)
	return fmt.Sprintf("dev-secret-%d", time.Now().UnixNano())
}

// parseDatabaseURL parses a database URL and populates individual fields
func (c *Config) parseDatabaseURL(dbURL string) {
	u, err := url.Parse(dbURL)
	if err != nil {
		return // Ignore parsing errors, use defaults
	}

	// Extract host and port
	if u.Host != "" {
		parts := strings.Split(u.Host, ":")
		if len(parts) > 0 {
			c.Database.Host = parts[0]
		}
		if len(parts) > 1 {
			if port, err := strconv.Atoi(parts[1]); err == nil {
				c.Database.Port = port
			}
		}
	}

	// Extract database name
	if u.Path != "" {
		c.Database.Database = strings.TrimPrefix(u.Path, "/")
	}

	// Extract username and password
	if u.User != nil {
		c.Database.Username = u.User.Username()
		if password, ok := u.User.Password(); ok {
			c.Database.Password = password
		}
	}

	// Extract SSL mode from query parameters
	if sslMode := u.Query().Get("sslmode"); sslMode != "" {
		c.Database.SSLMode = sslMode
	}
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

// substituteEnvVars replaces environment variable references in configuration strings
// Supports ${VAR} and ${VAR:-default} syntax
func substituteEnvVars(content string) string {
	// Pattern to match ${VAR} or ${VAR:-default}
	pattern := regexp.MustCompile(`\$\{([^}:]+)(?::-(.*?))?\}`)
	
	return pattern.ReplaceAllStringFunc(content, func(match string) string {
		// Extract variable name and default value
		start := strings.Index(match, "${") + 2
		end := strings.Index(match, "}")
		if end == -1 {
			return match // Malformed, return as-is
		}
		
		varPart := match[start:end]
		var varName, defaultValue string
		
		// Check for default value syntax ${VAR:-default}
		if colonIndex := strings.Index(varPart, ":-"); colonIndex != -1 {
			varName = varPart[:colonIndex]
			defaultValue = varPart[colonIndex+2:]
		} else {
			varName = varPart
		}
		
		// Get environment variable value
		if value := os.Getenv(varName); value != "" {
			return value
		}
		
		// Return default value if environment variable not set
		return defaultValue
	})
}
