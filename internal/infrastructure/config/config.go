package config

import (
	"fmt"
	"os"
	"strings"
)

// Config holds application configuration
type Config struct {
	Database DatabaseConfig
	Server   ServerConfig
	App      AppConfig
}

// DatabaseConfig holds database configuration
type DatabaseConfig struct {
	Host     string
	Port     string
	User     string
	Password string
	Name     string
	SSLMode  string
	URL      string // Full connection string
}

// ServerConfig holds server configuration
type ServerConfig struct {
	Port     string
	Host     string
	LogLevel string
}

// AppConfig holds application-specific configuration
type AppConfig struct {
	Environment string // development, staging, production
	Version     string
}

// Load loads configuration from environment variables
func Load() (*Config, error) {
	cfg := &Config{
		Database: DatabaseConfig{
			Host:     getEnv("DB_HOST", "localhost"),
			Port:     getEnv("DB_PORT", "5432"),
			User:     getEnv("DB_USER", "arxos"),
			Password: getEnv("DB_PASSWORD", ""),
			Name:     getEnv("DB_NAME", "arxos_dev"),
			SSLMode:  getEnv("DB_SSLMODE", "disable"),
		},
		Server: ServerConfig{
			Port:     getEnv("SERVER_PORT", "8080"),
			Host:     getEnv("SERVER_HOST", "0.0.0.0"),
			LogLevel: getEnv("LOG_LEVEL", "info"),
		},
		App: AppConfig{
			Environment: getEnv("ENVIRONMENT", "development"),
			Version:     getEnv("APP_VERSION", "0.1.0"),
		},
	}

	// Build database URL if not provided
	if dbURL := getEnv("DATABASE_URL", ""); dbURL != "" {
		cfg.Database.URL = dbURL
	} else {
		cfg.Database.URL = buildDatabaseURL(cfg.Database)
	}

	return cfg, nil
}

// buildDatabaseURL builds a PostgreSQL connection string
func buildDatabaseURL(db DatabaseConfig) string {
	return fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=%s",
		db.User,
		db.Password,
		db.Host,
		db.Port,
		db.Name,
		db.SSLMode,
	)
}

// getEnv gets an environment variable with a default value
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return strings.TrimSpace(value)
}

