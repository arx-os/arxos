package config

import (
	"os"
)

// Settings holds application configuration
type Settings struct {
	Port         string
	DatabaseURL  string
	LogLevel     string
	Environment  string
	SVGXEndpoint string
}

// LoadSettings loads configuration from environment variables
func LoadSettings() *Settings {
	return &Settings{
		Port:         getEnv("PORT", "8080"),
		DatabaseURL:  getEnv("DATABASE_URL", "postgres://localhost/arxos_construction"),
		LogLevel:     getEnv("LOG_LEVEL", "info"),
		Environment:  getEnv("ENVIRONMENT", "development"),
		SVGXEndpoint: getEnv("SVGX_ENDPOINT", "http://localhost:8081"),
	}
}

// getEnv gets environment variable with fallback
func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

// IsDevelopment returns true if running in development mode
func (s *Settings) IsDevelopment() bool {
	return s.Environment == "development"
}

// IsProduction returns true if running in production mode
func (s *Settings) IsProduction() bool {
	return s.Environment == "production"
}
