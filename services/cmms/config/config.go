package config

import (
	"os"
	"strconv"
	"time"
)

// Config holds all configuration for the CMMS service
type Config struct {
	// Database configuration
	DatabaseURL string

	// Server configuration
	Port         string
	Host         string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration

	// CMMS service configuration
	DefaultSyncInterval int
	MaxRetryAttempts    int
	RetryDelay          time.Duration
	RequestTimeout      time.Duration

	// Logging configuration
	LogLevel string
	LogFile  string

	// Security configuration
	JWTSecret     string
	AllowedOrigins []string

	// Rate limiting
	RateLimitRequests int
	RateLimitWindow   time.Duration

	// Monitoring
	MetricsEnabled bool
	MetricsPort    string
}

// Load loads configuration from environment variables
func Load() *Config {
	config := &Config{
		// Database
		DatabaseURL: getEnv("DATABASE_URL", "postgres://user:password@localhost:5432/arxos?sslmode=disable"),

		// Server
		Port:         getEnv("PORT", "8080"),
		Host:         getEnv("HOST", "0.0.0.0"),
		ReadTimeout:  getDurationEnv("READ_TIMEOUT", 30*time.Second),
		WriteTimeout: getDurationEnv("WRITE_TIMEOUT", 30*time.Second),

		// CMMS service
		DefaultSyncInterval: getIntEnv("DEFAULT_SYNC_INTERVAL", 60),
		MaxRetryAttempts:    getIntEnv("MAX_RETRY_ATTEMPTS", 3),
		RetryDelay:          getDurationEnv("RETRY_DELAY", 5*time.Second),
		RequestTimeout:      getDurationEnv("REQUEST_TIMEOUT", 15*time.Second),

		// Logging
		LogLevel: getEnv("LOG_LEVEL", "info"),
		LogFile:  getEnv("LOG_FILE", ""),

		// Security
		JWTSecret:      getEnv("JWT_SECRET", "your-secret-key"),
		AllowedOrigins: getStringSliceEnv("ALLOWED_ORIGINS", []string{"*"}),

		// Rate limiting
		RateLimitRequests: getIntEnv("RATE_LIMIT_REQUESTS", 100),
		RateLimitWindow:   getDurationEnv("RATE_LIMIT_WINDOW", time.Minute),

		// Monitoring
		MetricsEnabled: getBoolEnv("METRICS_ENABLED", false),
		MetricsPort:    getEnv("METRICS_PORT", "9090"),
	}

	return config
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getIntEnv gets an integer environment variable or returns a default value
func getIntEnv(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// getBoolEnv gets a boolean environment variable or returns a default value
func getBoolEnv(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}

// getDurationEnv gets a duration environment variable or returns a default value
func getDurationEnv(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}

// getStringSliceEnv gets a string slice environment variable or returns a default value
func getStringSliceEnv(key string, defaultValue []string) []string {
	if value := os.Getenv(key); value != "" {
		// Simple comma-separated values
		// In a real implementation, you might want more sophisticated parsing
		return []string{value}
	}
	return defaultValue
}

// Validate validates the configuration
func (c *Config) Validate() error {
	// Add validation logic here
	// For example, check if required fields are set
	if c.DatabaseURL == "" {
		return &ConfigError{Field: "DATABASE_URL", Message: "Database URL is required"}
	}

	if c.JWTSecret == "your-secret-key" {
		return &ConfigError{Field: "JWT_SECRET", Message: "JWT secret should be changed from default"}
	}

	return nil
}

// ConfigError represents a configuration error
type ConfigError struct {
	Field   string
	Message string
}

func (e *ConfigError) Error() string {
	return "config error: " + e.Field + " - " + e.Message
} 