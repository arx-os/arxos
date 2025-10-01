package internal

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/config"
)

// Placeholder types for DI container (will be replaced when DI is implemented)
type Container struct{}
type Services struct{}

// App represents the ArxOS application following Go Blueprint standards
type App struct {
	config    *config.Config
	container *Container
	services  *Services
}

// NewApp creates a new ArxOS application instance
func NewApp() *App {
	return &App{}
}

// Initialize sets up the application components following clean architecture
func (a *App) Initialize(ctx context.Context) error {
	// Load configuration
	if err := a.loadConfig(); err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	// Convert app config to DI config (placeholder)
	_ = a.convertToDIConfig()

	// Initialize dependency injection container (placeholder)
	a.container = &Container{}

	// Get services from container (placeholder)
	a.services = &Services{}

	// Create necessary directories
	if err := a.ensureDirectories(); err != nil {
		return fmt.Errorf("directory setup failed: %w", err)
	}

	logger.Info("ArxOS application initialized successfully")
	return nil
}

// GetConfig returns the application configuration
func (a *App) GetConfig() *config.Config {
	return a.config
}

// GetContainer returns the dependency injection container
func (a *App) GetContainer() *Container {
	return a.container
}

// GetServices returns the application services
func (a *App) GetServices() *Services {
	return a.services
}

// loadConfig loads the application configuration
func (a *App) loadConfig() error {
	// Load configuration from environment or config file
	a.config = &config.Config{
		Mode: "development", // Default mode
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_db",
			User:     "arxos_user",
			Password: "arxos_password",
			SSLMode:  "disable",
		},
	}

	// Override with environment variables if set
	if host := os.Getenv("DB_HOST"); host != "" {
		a.config.PostGIS.Host = host
	}
	if port := os.Getenv("DB_PORT"); port != "" {
		a.config.PostGIS.Port = 5432 // Default port
	}
	if database := os.Getenv("DB_NAME"); database != "" {
		a.config.PostGIS.Database = database
	}
	if username := os.Getenv("DB_USER"); username != "" {
		a.config.PostGIS.User = username
	}
	if password := os.Getenv("DB_PASSWORD"); password != "" {
		a.config.PostGIS.Password = password
	}

	return nil
}

// convertToDIConfig converts app config to DI config (placeholder)
func (a *App) convertToDIConfig() interface{} {
	return struct {
		Database    interface{}
		Cache       interface{}
		Storage     interface{}
		WebSocket   interface{}
		Development bool
	}{
		Database: struct {
			Host     string
			Port     int
			Database string
			Username string
			Password string
			SSLMode  string
		}{
			Host:     a.config.PostGIS.Host,
			Port:     a.config.PostGIS.Port,
			Database: a.config.PostGIS.Database,
			Username: a.config.PostGIS.User,
			Password: a.config.PostGIS.Password,
			SSLMode:  a.config.PostGIS.SSLMode,
		},
		Cache: struct {
			Host     string
			Port     int
			Password string
			DB       int
		}{
			Host:     "localhost",
			Port:     6379,
			Password: "",
			DB:       0,
		},
		Storage: struct {
			Type string
			Path string
		}{
			Type: "local",
			Path: "./storage",
		},
		WebSocket: struct {
			ReadBufferSize  int
			WriteBufferSize int
			PingPeriod      int
			PongWait        int
			WriteWait       int
			MaxMessageSize  int
		}{
			ReadBufferSize:  1024,
			WriteBufferSize: 1024,
			PingPeriod:      54,
			PongWait:        60,
			WriteWait:       10,
			MaxMessageSize:  512,
		},
		Development: a.config.Mode == "development",
	}
}

// ensureDirectories creates necessary directories
func (a *App) ensureDirectories() error {
	dirs := []string{
		"./storage",
		"./storage/buildings",
		"./storage/equipment",
		"./storage/analytics",
		"./storage/workflows",
		"./storage/temp",
		"./logs",
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return nil
}

// SetupLogging configures logging based on environment
func (a *App) SetupLogging() {
	logLevel := os.Getenv("ARX_LOG_LEVEL")
	if logLevel == "" {
		logLevel = "info"
	}

	switch strings.ToLower(logLevel) {
	case "debug":
		logger.SetLevel(logger.DEBUG)
	case "info":
		logger.SetLevel(logger.INFO)
	case "warn", "warning":
		logger.SetLevel(logger.WARN)
	case "error":
		logger.SetLevel(logger.ERROR)
	default:
		logger.SetLevel(logger.INFO)
	}
}
