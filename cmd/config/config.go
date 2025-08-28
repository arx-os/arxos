package config

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"github.com/spf13/viper"
)

// Config represents the complete Arxos CLI configuration
type Config struct {
	// CLI settings
	CLI CLIConfig `yaml:"cli" json:"cli"`
	
	// Backend connection
	Backend BackendConfig `yaml:"backend" json:"backend"`
	
	// Database connection
	Database DatabaseConfig `yaml:"database" json:"database"`
	
	// Display settings
	Display DisplayConfig `yaml:"display" json:"display"`
	
	// Building defaults
	Defaults DefaultsConfig `yaml:"defaults" json:"defaults"`
	
	// AI configuration
	AI AIConfig `yaml:"ai" json:"ai"`
	
	// Computed fields (not in YAML)
	DatabaseURL string `yaml:"-" json:"-"`
}

// CLIConfig contains CLI-specific settings
type CLIConfig struct {
	DefaultFormat string `yaml:"default_format" json:"default_format"`
	Verbose       bool   `yaml:"verbose" json:"verbose"`
	ColorOutput   bool   `yaml:"color_output" json:"color_output"`
	PageSize      int    `yaml:"page_size" json:"page_size"`
	Timeout       int    `yaml:"timeout" json:"timeout"` // in seconds
}

// BackendConfig for backend connection
type BackendConfig struct {
	URL      string `yaml:"url" json:"url"`
	Token    string `yaml:"token" json:"token"`
	Timeout  int    `yaml:"timeout" json:"timeout"`
	Insecure bool   `yaml:"insecure" json:"insecure"`
}

// DatabaseConfig contains database connection settings
type DatabaseConfig struct {
	Host     string `yaml:"host" json:"host"`
	Port     int    `yaml:"port" json:"port"`
	User     string `yaml:"user" json:"user"`
	Password string `yaml:"password" json:"password"`
	Database string `yaml:"database" json:"database"`
	SSLMode  string `yaml:"ssl_mode" json:"ssl_mode"`
}

// DisplayConfig for output formatting
type DisplayConfig struct {
	Format    string `yaml:"format"`    // table, json, yaml
	Color     bool   `yaml:"color"`
	PageSize  int    `yaml:"page_size"`
	Precision int    `yaml:"precision"` // Decimal places for confidence
}

// DefaultsConfig for default values
type DefaultsConfig struct {
	ConfidenceThreshold float64 `yaml:"confidence_threshold"`
	ValidationRequired  bool    `yaml:"validation_required"`
	AutoPropagate      bool    `yaml:"auto_propagate"`
	DefaultBuilding    string  `yaml:"default_building"`
}

// AIConfig for AI service settings
type AIConfig struct {
	ServiceURL      string  `yaml:"service_url"`
	ModelPath       string  `yaml:"model_path"`
	ConfidenceMin   float64 `yaml:"confidence_min"`
	StreamingPort   int     `yaml:"streaming_port"`
}

var (
	cfg *Config
	cfgOnce sync.Once
	cfgFile string
)

// Load loads the configuration
func Load(configFile string) error {
	if configFile != "" {
		// Use config file from flag
		viper.SetConfigFile(configFile)
	} else {
		// Default config locations
		home, err := os.UserHomeDir()
		if err != nil {
			return err
		}

		// Search for config in these locations
		viper.AddConfigPath(filepath.Join(home, ".arxos"))
		viper.AddConfigPath(".")
		viper.SetConfigName("config")
		viper.SetConfigType("yaml")
	}

	// Environment variables
	viper.SetEnvPrefix("ARXOS")
	viper.AutomaticEnv()

	// Defaults
	setDefaults()

	// Read config
	if err := viper.ReadInConfig(); err != nil {
		// Create default config if not found
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			if err := createDefaultConfig(); err != nil {
				return fmt.Errorf("failed to create default config: %w", err)
			}
		} else {
			return fmt.Errorf("failed to read config: %w", err)
		}
	}

	// Unmarshal into struct
	if cfg == nil {
		cfg = &Config{}
	}
	if err := viper.Unmarshal(cfg); err != nil {
		return fmt.Errorf("failed to unmarshal config: %w", err)
	}

	return nil
}

// Get returns the current configuration (thread-safe singleton)
func Get() *Config {
	cfgOnce.Do(func() {
		if cfg == nil {
			if err := Load(""); err != nil {
				// Use defaults if config load fails
				cfg = getDefaultConfig()
			}
		}
	})
	
	// Compute DatabaseURL if not set
	if cfg != nil && cfg.DatabaseURL == "" {
		cfg.DatabaseURL = fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=%s",
			cfg.Database.User,
			cfg.Database.Password,
			cfg.Database.Host,
			cfg.Database.Port,
			cfg.Database.Database,
			cfg.Database.SSLMode,
		)
	}
	
	return cfg
}

// GetConfig is an alias for Get() to match expected function name
func GetConfig() *Config {
	return Get()
}

// Save saves the current configuration
func Save() error {
	return viper.WriteConfig()
}

func setDefaults() {
	// CLI defaults
	viper.SetDefault("cli.default_format", "table")
	viper.SetDefault("cli.verbose", false)
	viper.SetDefault("cli.color_output", true)
	viper.SetDefault("cli.page_size", 100)
	viper.SetDefault("cli.timeout", 30)

	// Backend defaults
	viper.SetDefault("backend.url", "http://localhost:8080")
	viper.SetDefault("backend.timeout", 30)
	viper.SetDefault("backend.insecure", false)

	// Database defaults
	viper.SetDefault("database.host", "localhost")
	viper.SetDefault("database.port", 5432)
	viper.SetDefault("database.user", "arxos")
	viper.SetDefault("database.password", "")
	viper.SetDefault("database.database", "arxos")
	viper.SetDefault("database.ssl_mode", "prefer")

	// Display defaults
	viper.SetDefault("display.format", "table")
	viper.SetDefault("display.color", true)
	viper.SetDefault("display.page_size", 50)
	viper.SetDefault("display.precision", 2)

	// Operation defaults
	viper.SetDefault("defaults.confidence_threshold", 0.7)
	viper.SetDefault("defaults.validation_required", true)
	viper.SetDefault("defaults.auto_propagate", true)

	// AI defaults
	viper.SetDefault("ai.service_url", "http://localhost:8000")
	viper.SetDefault("ai.model_path", "~/.arxos/models")
	viper.SetDefault("ai.confidence_min", 0.5)
	viper.SetDefault("ai.streaming_port", 8081)
}

func createDefaultConfig() error {
	home, err := os.UserHomeDir()
	if err != nil {
		return err
	}

	configDir := filepath.Join(home, ".arxos")
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return err
	}

	configFile := filepath.Join(configDir, "config.yaml")
	
	// Write default config
	viper.SetConfigFile(configFile)
	return viper.WriteConfig()
}

// getDefaultConfig returns a default configuration struct
func getDefaultConfig() *Config {
	return &Config{
		CLI: CLIConfig{
			DefaultFormat: "table",
			Verbose:       false,
			ColorOutput:   true,
			PageSize:      100,
			Timeout:       30,
		},
		Backend: BackendConfig{
			URL:      "http://localhost:8080",
			Token:    "",
			Timeout:  30,
			Insecure: false,
		},
		Database: DatabaseConfig{
			Host:     "localhost",
			Port:     5432,
			User:     "arxos",
			Password: "",
			Database: "arxos",
			SSLMode:  "prefer",
		},
		Display: DisplayConfig{
			Format:    "table",
			Color:     true,
			PageSize:  50,
			Precision: 2,
		},
		Defaults: DefaultsConfig{
			ConfidenceThreshold: 0.7,
			ValidationRequired:  true,
			AutoPropagate:      true,
			DefaultBuilding:    "",
		},
		AI: AIConfig{
			ServiceURL:    "http://localhost:8000",
			ModelPath:     "~/.arxos/models",
			ConfidenceMin: 0.5,
			StreamingPort: 8081,
		},
	}
}

// GetDatabaseURL constructs the PostgreSQL connection URL
func (c *DatabaseConfig) GetDatabaseURL() string {
	return fmt.Sprintf(
		"postgres://%s:%s@%s:%d/%s?sslmode=%s",
		c.User,
		c.Password,
		c.Host,
		c.Port,
		c.Database,
		c.SSLMode,
	)
}