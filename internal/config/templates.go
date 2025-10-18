package config

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

// ConfigTemplate represents a configuration template
type ConfigTemplate struct {
	Name        string
	Description string
	Mode        Mode
	Config      *Config
	Environment Environment
	Variables   []TemplateVariable
}

// TemplateVariable represents a template variable
type TemplateVariable struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Type        string `json:"type"`
	Default     string `json:"default"`
	Required    bool   `json:"required"`
}

// GetConfigTemplates returns available configuration templates
func GetConfigTemplates() []ConfigTemplate {
	homeDir, _ := os.UserHomeDir()
	basePath := filepath.Join(homeDir, ".arxos")

	return []ConfigTemplate{
		{
			Name:        "local",
			Description: "Local development with no cloud sync",
			Mode:        ModeLocal,
			Config:      createLocalTemplate(basePath),
			Environment: EnvDevelopment,
			Variables:   getLocalTemplateVariables(),
		},
		{
			Name:        "cloud",
			Description: "Cloud-first with automatic sync",
			Mode:        ModeCloud,
			Config:      createCloudTemplate(basePath),
			Environment: EnvStaging,
			Variables:   getCloudTemplateVariables(),
		},
		{
			Name:        "hybrid",
			Description: "Local database with cloud sync",
			Mode:        ModeHybrid,
			Config:      createHybridTemplate(basePath),
			Environment: EnvInternal,
			Variables:   getHybridTemplateVariables(),
		},
		{
			Name:        "production",
			Description: "Production-ready configuration",
			Mode:        ModeHybrid, // Use hybrid as production mode
			Config:      createProductionTemplate(basePath),
			Environment: EnvProduction,
			Variables:   getProductionTemplateVariables(),
		},
	}
}

// createLocalTemplate creates a local development template
func createLocalTemplate(basePath string) *Config {
	return &Config{
		Mode:     ModeLocal,
		Version:  "0.1.0",
		StateDir: basePath,
		CacheDir: filepath.Join(basePath, "cache"),

		Cloud: CloudConfig{
			Enabled:      false,
			BaseURL:      "https://api.arxos.io",
			SyncEnabled:  false,
			SyncInterval: 5 * time.Minute,
		},

		Storage: StorageConfig{
			Backend:   "local",
			LocalPath: filepath.Join(basePath, "data"),
			Data: DataConfig{
				BasePath:        basePath,
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
			Debug:      true,
		},

		Features: FeatureFlags{
			CloudSync:     false,
			AIIntegration: false,
			OfflineMode:   true,
			BetaFeatures:  true,
			Analytics:     false,
			AutoUpdate:    false,
		},

		Security: SecurityConfig{
			JWTExpiry:          24 * time.Hour,
			SessionTimeout:     30 * time.Minute,
			APIRateLimit:       1000,
			APIRateLimitWindow: time.Minute,
			EnableAuth:         false,
			EnableTLS:          false,
			AllowedOrigins:     []string{"http://localhost:3000", "http://localhost:8080"},
			BcryptCost:         4, // Lower cost for development
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

		Database: DatabaseConfig{
			Type:            "postgis",
			Driver:          "postgres",
			Host:            "localhost",
			Port:            5432,
			Database:        "arxos_dev",
			Username:        "arxos",
			Password:        "arxos_dev",
			SSLMode:         "disable",
			MaxOpenConns:    25,
			MaxConnections:  25,
			MaxIdleConns:    5,
			ConnLifetime:    30 * time.Minute,
			ConnMaxLifetime: 30 * time.Minute,
			MigrationsPath:  "./internal/migrations",
			AutoMigrate:     true,
		},

		PostGIS: PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_dev",
			User:     "arxos",
			Password: "arxos_dev",
			SSLMode:  "disable",
			SRID:     900913,
		},
	}
}

// createCloudTemplate creates a cloud-first template
func createCloudTemplate(basePath string) *Config {
	cfg := createLocalTemplate(basePath)
	cfg.Mode = ModeCloud
	cfg.Cloud.Enabled = true
	cfg.Cloud.SyncEnabled = true
	cfg.Features.CloudSync = true
	cfg.Features.BetaFeatures = false
	cfg.Security.EnableAuth = true
	cfg.Security.BcryptCost = 10
	cfg.Telemetry.Enabled = true
	cfg.Telemetry.Debug = false
	cfg.Telemetry.AnonymousID = generateAnonymousID() // Required when telemetry is enabled
	return cfg
}

// createHybridTemplate creates a hybrid template
func createHybridTemplate(basePath string) *Config {
	cfg := createLocalTemplate(basePath)
	cfg.Mode = ModeHybrid
	cfg.Cloud.Enabled = true
	cfg.Cloud.SyncEnabled = true
	cfg.Features.CloudSync = true
	cfg.Features.OfflineMode = true
	cfg.Security.EnableAuth = true
	cfg.Security.BcryptCost = 10
	cfg.Telemetry.Enabled = true
	cfg.Telemetry.Debug = false
	cfg.Telemetry.AnonymousID = generateAnonymousID() // Required when telemetry is enabled
	return cfg
}

// createProductionTemplate creates a production template
func createProductionTemplate(basePath string) *Config {
	cfg := createLocalTemplate(basePath)
	cfg.Mode = ModeProduction
	cfg.Cloud.Enabled = true
	cfg.Cloud.SyncEnabled = true
	cfg.Features.CloudSync = true
	cfg.Features.BetaFeatures = false
	cfg.Features.Analytics = true
	cfg.Security.EnableAuth = true
	cfg.Security.EnableTLS = true
	cfg.Security.TLSCertPath = filepath.Join(basePath, "certs", "server.crt")
	cfg.Security.TLSKeyPath = filepath.Join(basePath, "certs", "server.key")
	cfg.Security.BcryptCost = 14
	cfg.Security.APIRateLimit = 100
	cfg.Telemetry.Enabled = true
	cfg.Telemetry.Debug = false
	cfg.Telemetry.SampleRate = 0.01
	cfg.Telemetry.AnonymousID = generateAnonymousID() // Required when telemetry is enabled
	cfg.TUI.Enabled = false                           // Disable TUI in production
	cfg.Database.MaxOpenConns = 100
	cfg.Database.MaxConnections = 100
	cfg.Database.MaxIdleConns = 10
	return cfg
}

// generateAnonymousID generates a random anonymous ID for telemetry
func generateAnonymousID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

// CreateConfigFromTemplate creates a configuration from a template
func CreateConfigFromTemplate(templateName, dataDir string) (*Config, error) {
	templates := GetConfigTemplates()

	var template *ConfigTemplate
	for _, t := range templates {
		if t.Name == templateName {
			template = &t
			break
		}
	}

	if template == nil {
		return nil, fmt.Errorf("unknown template: %s", templateName)
	}

	// Create a copy of the template config
	cfg := *template.Config

	// Override data directory if provided
	if dataDir != "" {
		cfg.Storage.Data.BasePath = dataDir
		cfg.StateDir = dataDir
		cfg.CacheDir = filepath.Join(dataDir, "cache")
		cfg.Storage.LocalPath = filepath.Join(dataDir, "data")
	}

	return &cfg, nil
}

// getLocalTemplateVariables returns variables for local template
func getLocalTemplateVariables() []TemplateVariable {
	return []TemplateVariable{
		{
			Name:        "data_dir",
			Description: "Directory for local data storage",
			Type:        "string",
			Default:     "~/.arxos",
			Required:    false,
		},
		{
			Name:        "database_host",
			Description: "Database host",
			Type:        "string",
			Default:     "localhost",
			Required:    true,
		},
		{
			Name:        "database_port",
			Description: "Database port",
			Type:        "int",
			Default:     "5432",
			Required:    true,
		},
	}
}

// getCloudTemplateVariables returns variables for cloud template
func getCloudTemplateVariables() []TemplateVariable {
	return []TemplateVariable{
		{
			Name:        "cloud_url",
			Description: "Cloud API URL",
			Type:        "string",
			Default:     "https://api.arxos.io",
			Required:    true,
		},
		{
			Name:        "api_key",
			Description: "API key for cloud access",
			Type:        "string",
			Default:     "",
			Required:    true,
		},
		{
			Name:        "sync_interval",
			Description: "Sync interval in minutes",
			Type:        "int",
			Default:     "5",
			Required:    false,
		},
	}
}

// getHybridTemplateVariables returns variables for hybrid template
func getHybridTemplateVariables() []TemplateVariable {
	return []TemplateVariable{
		{
			Name:        "data_dir",
			Description: "Directory for local data storage",
			Type:        "string",
			Default:     "~/.arxos",
			Required:    false,
		},
		{
			Name:        "cloud_url",
			Description: "Cloud API URL",
			Type:        "string",
			Default:     "https://api.arxos.io",
			Required:    true,
		},
		{
			Name:        "api_key",
			Description: "API key for cloud access",
			Type:        "string",
			Default:     "",
			Required:    true,
		},
	}
}

// getProductionTemplateVariables returns variables for production template
func getProductionTemplateVariables() []TemplateVariable {
	return []TemplateVariable{
		{
			Name:        "data_dir",
			Description: "Directory for local data storage",
			Type:        "string",
			Default:     "~/.arxos",
			Required:    false,
		},
		{
			Name:        "cloud_url",
			Description: "Cloud API URL",
			Type:        "string",
			Default:     "https://api.arxos.io",
			Required:    true,
		},
		{
			Name:        "api_key",
			Description: "API key for cloud access",
			Type:        "string",
			Default:     "",
			Required:    true,
		},
		{
			Name:        "enable_tls",
			Description: "Enable TLS encryption",
			Type:        "bool",
			Default:     "true",
			Required:    false,
		},
	}
}

// GetDefaultDataPath returns the default data path based on the operating system
func GetDefaultDataPath() string {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		// Fallback to current directory if home directory cannot be determined
		return ".arxos"
	}

	switch runtime.GOOS {
	case "windows":
		// Windows: %APPDATA%\arxos
		return filepath.Join(homeDir, "AppData", "Roaming", "arxos")
	case "darwin":
		// macOS: ~/Library/Application Support/arxos
		return filepath.Join(homeDir, "Library", "Application Support", "arxos")
	default:
		// Linux/Unix: ~/.local/share/arxos (XDG Base Directory)
		return filepath.Join(homeDir, ".local", "share", "arxos")
	}
}
