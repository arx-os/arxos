package config

import (
	"os"
	"strings"
)

// Environment represents the deployment environment
type Environment string

const (
	EnvDevelopment Environment = "development"
	EnvStaging     Environment = "staging"
	EnvInternal    Environment = "internal"
	EnvProduction  Environment = "production"
)

// EnvironmentConfig contains environment-specific settings
type EnvironmentConfig struct {
	Name        Environment
	APIBaseURL  string
	WebBaseURL  string
	CORSOrigins []string
	SecureCookie bool
	Debug       bool
}

// GetEnvironmentConfig returns configuration for the current environment
func GetEnvironmentConfig() *EnvironmentConfig {
	env := strings.ToLower(os.Getenv("ARXOS_ENV"))
	if env == "" {
		env = "development"
	}

	switch Environment(env) {
	case EnvProduction:
		return &EnvironmentConfig{
			Name:       EnvProduction,
			APIBaseURL: "https://api.arxos.io",
			WebBaseURL: "https://arxos.io",
			CORSOrigins: []string{
				"https://arxos.io",
				"https://www.arxos.io",
			},
			SecureCookie: true,
			Debug:        false,
		}

	case EnvInternal:
		return &EnvironmentConfig{
			Name:       EnvInternal,
			APIBaseURL: "https://api.arxos.dev",
			WebBaseURL: "https://arxos.dev",
			CORSOrigins: []string{
				"https://arxos.dev",
				"https://www.arxos.dev",
				"https://arxos.io", // Allow production site to access internal API for testing
			},
			SecureCookie: true,
			Debug:        true,
		}

	case EnvStaging:
		return &EnvironmentConfig{
			Name:       EnvStaging,
			APIBaseURL: "https://staging-api.arxos.dev",
			WebBaseURL: "https://staging.arxos.dev",
			CORSOrigins: []string{
				"https://staging.arxos.dev",
			},
			SecureCookie: true,
			Debug:        true,
		}

	default: // Development
		return &EnvironmentConfig{
			Name:       EnvDevelopment,
			APIBaseURL: "http://localhost:8080",
			WebBaseURL: "http://localhost:8080",
			CORSOrigins: []string{
				"http://localhost:8080",
				"http://localhost:3000",
				"http://127.0.0.1:8080",
			},
			SecureCookie: false,
			Debug:        true,
		}
	}
}

// IsDevelopment returns true if running in development
func (ec *EnvironmentConfig) IsDevelopment() bool {
	return ec.Name == EnvDevelopment
}

// IsProduction returns true if running in production or internal production
func (ec *EnvironmentConfig) IsProduction() bool {
	return ec.Name == EnvProduction || ec.Name == EnvInternal
}

// GetAPIURL constructs a full API URL with the given path
func (ec *EnvironmentConfig) GetAPIURL(path string) string {
	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}
	return ec.APIBaseURL + path
}

// GetWebURL constructs a full web URL with the given path
func (ec *EnvironmentConfig) GetWebURL(path string) string {
	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}
	return ec.WebBaseURL + path
}