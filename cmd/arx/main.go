package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/database"
)

var (
	// Version information (set during build)
	Version   = "dev"
	BuildTime = "unknown"
	Commit    = "unknown"
)

var rootCmd = &cobra.Command{
	Use:   "arx",
	Short: "ArxOS - Building Operating System",
	Long: `ArxOS is a universal building operating system that manages building data
with Git-like version control, spatial precision, and multi-interface support.

Core features:
  • Import/Export - Convert between PDF, IFC, and BIM formats
  • Repository Management - Git-like version control for buildings
  • Query & Search - Powerful database queries across all equipment
  • CRUD Operations - Direct manipulation of building components
  • File Monitoring - Auto-import with directory watching
  • REST API - HTTP server for web and mobile clients
  • Universal Addressing - Access any component with paths like:
    ARXOS-001/3/A/301/E/OUTLET_01

For detailed help on any command, use: arx <command> --help`,
	SilenceUsage:  true,
	SilenceErrors: true,
}

func main() {
	// Initialize system
	if err := initializeSystem(); err != nil {
		logger.Error("Failed to initialize: %v", err)
		os.Exit(1)
	}

	// Set up logging
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

	// Wire all commands
	rootCmd.AddCommand(
		// System management
		installCmd,
		daemonCmd,

		// Repository management
		repoCmd,

		// Import/Export
		importCmd,
		exportCmd,
		convertCmd,

		// Data operations
		queryCmd,

		// CRUD operations
		addCmd,
		getCmd,
		updateCmd,
		removeCmd,
		listCmd,
		traceCmd,

		// Services
		watchCmd,
		serveCmd,

		// Visualization
		visualizeCmd,
		reportCmd,

		// Utility
		versionCmd,
	)

	// Execute
	if err := rootCmd.Execute(); err != nil {
		logger.Error("%v", err)
		os.Exit(1)
	}
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print version information",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("ArxOS %s\n", Version)
		fmt.Printf("Built: %s\n", BuildTime)
		fmt.Printf("Commit: %s\n", Commit)
	},
}

func init() {
	// Global flags
	rootCmd.PersistentFlags().BoolP("verbose", "v", false, "verbose output")
	rootCmd.PersistentFlags().BoolP("quiet", "q", false, "suppress non-error output")
	rootCmd.PersistentFlags().String("config", "", "config file path")
	rootCmd.PersistentFlags().String("database", "", "database connection string")
}

// Global variables for system components
var (
	appConfig *config.Config
	dbConn    database.DB
	hybridDB  *database.PostGISHybridDB
)

// initializeSystem sets up core components
func initializeSystem() error {
	ctx := context.Background()

	// Load configuration
	appConfig = loadConfiguration()

	// Initialize database connections
	if err := initializeDatabases(ctx); err != nil {
		return fmt.Errorf("database initialization failed: %w", err)
	}

	// Create necessary directories
	if err := ensureDirectories(); err != nil {
		return fmt.Errorf("directory setup failed: %w", err)
	}

	return nil
}

// loadConfiguration loads config from file or environment
func loadConfiguration() *config.Config {
	cfg := &config.Config{
		Mode:     config.ModeHybrid,
		Version:  Version,
		StateDir: ".arxos",
		CacheDir: ".arxos/cache",
	}

	// Check for config file
	configFile, _ := rootCmd.PersistentFlags().GetString("config")
	if configFile == "" {
		// Check standard locations
		for _, path := range []string{
			".arxos/config.yaml",
			"arxos.config.yaml",
			os.ExpandEnv("$HOME/.arxos/config.yaml"),
		} {
			if _, err := os.Stat(path); err == nil {
				configFile = path
				break
			}
		}
	}

	if configFile != "" {
		if err := cfg.LoadFromFile(configFile); err != nil {
			logger.Warn("Failed to load config file %s: %v", configFile, err)
		}
	}

	// Override with environment variables
	loadConfigFromEnv(cfg)

	return cfg
}

// loadConfigFromEnv loads configuration from environment variables
func loadConfigFromEnv(cfg *config.Config) {
	// PostGIS configuration
	if host := os.Getenv("POSTGIS_HOST"); host != "" {
		cfg.PostGIS.Host = host
	}
	if port := os.Getenv("POSTGIS_PORT"); port != "" {
		fmt.Sscanf(port, "%d", &cfg.PostGIS.Port)
	}
	if db := os.Getenv("POSTGIS_DB"); db != "" {
		cfg.PostGIS.Database = db
	}
	if user := os.Getenv("POSTGIS_USER"); user != "" {
		cfg.PostGIS.User = user
	}
	if pass := os.Getenv("POSTGIS_PASSWORD"); pass != "" {
		cfg.PostGIS.Password = pass
	}

	// Database configuration
	if dbType := os.Getenv("ARX_DB_TYPE"); dbType != "" {
		cfg.Database.Type = dbType
	}
	if dbPath := os.Getenv("ARX_DB_PATH"); dbPath != "" {
		cfg.Database.Path = dbPath
	}
}

// initializeDatabases sets up database connections
func initializeDatabases(ctx context.Context) error {
	// Default database path
	dbPath := "arxos.db"
	if appConfig.Database.Path != "" {
		dbPath = appConfig.Database.Path
	}

	// Check if PostGIS is configured
	if appConfig.PostGIS.Host != "" {
		// Create PostGIS configuration
		pgConfig := database.PostGISConfig{
			Host:     appConfig.PostGIS.Host,
			Port:     appConfig.PostGIS.Port,
			Database: appConfig.PostGIS.Database,
			User:     appConfig.PostGIS.User,
			Password: appConfig.PostGIS.Password,
			SSLMode:  appConfig.PostGIS.SSLMode,
		}

		if pgConfig.Port == 0 {
			pgConfig.Port = 5432
		}
		if pgConfig.SSLMode == "" {
			pgConfig.SSLMode = "prefer"
		}

		// Create hybrid database with PostGIS primary and SQLite fallback
		sqliteConfig := database.NewConfig(dbPath)
		hybridDB = database.NewPostGISHybridDB(pgConfig, sqliteConfig)

		if err := hybridDB.Connect(ctx, dbPath); err != nil {
			logger.Warn("PostGIS connection failed, using SQLite: %v", err)
			// Fall back to SQLite only
			dbConn = database.NewSQLiteDB(sqliteConfig)
		} else {
			logger.Info("Connected to PostGIS database")
			dbConn = hybridDB

			// Initialize PostGIS extensions if needed
			if spatialDB, err := hybridDB.GetSpatialDB(); err == nil {
				if err := spatialDB.InitializeSpatialExtensions(ctx); err != nil {
					logger.Warn("Failed to initialize spatial extensions: %v", err)
				}
			}
		}
	} else {
		// SQLite only mode
		sqliteConfig := database.NewConfig(dbPath)
		dbConn = database.NewSQLiteDB(sqliteConfig)
		logger.Info("Using SQLite database: %s", dbPath)
	}

	// Connect to database
	if dbConn != nil {
		if err := dbConn.Connect(ctx, dbPath); err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}

		// Initialize schema
		if err := dbConn.InitSchema(ctx); err != nil {
			logger.Warn("Failed to initialize schema: %v", err)
		}
	}

	return nil
}

// ensureDirectories creates necessary directories
func ensureDirectories() error {
	dirs := []string{
		appConfig.StateDir,
		appConfig.CacheDir,
		filepath.Join(appConfig.StateDir, "exports"),
		filepath.Join(appConfig.StateDir, "imports"),
		filepath.Join(appConfig.StateDir, "logs"),
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return nil
}

// GetDatabase returns the active database connection
func GetDatabase() database.DB {
	return dbConn
}

// GetConfig returns the application configuration
func GetConfig() *config.Config {
	return appConfig
}