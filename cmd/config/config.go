package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/viper"
)

// Config represents the CLI configuration
type Config struct {
	Backend  BackendConfig  `yaml:"backend"`
	Display  DisplayConfig  `yaml:"display"`
	Defaults DefaultsConfig `yaml:"defaults"`
	AI       AIConfig       `yaml:"ai"`
}

// BackendConfig for backend connection
type BackendConfig struct {
	URL     string `yaml:"url"`
	Token   string `yaml:"token"`
	Timeout int    `yaml:"timeout"`
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
	cfg = &Config{}
	if err := viper.Unmarshal(cfg); err != nil {
		return fmt.Errorf("failed to unmarshal config: %w", err)
	}

	return nil
}

// Get returns the current configuration
func Get() *Config {
	if cfg == nil {
		Load("")
	}
	return cfg
}

// Save saves the current configuration
func Save() error {
	return viper.WriteConfig()
}

func setDefaults() {
	// Backend defaults
	viper.SetDefault("backend.url", "http://localhost:8080")
	viper.SetDefault("backend.timeout", 30)

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