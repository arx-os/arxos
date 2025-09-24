package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/database"
	"github.com/spf13/cobra"
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
		// installCmd,    // TODO: Implement
		// healthCmd,    // TODO: Implement
		// daemonCmd,    // TODO: Implement
		migrateCmd,

		// Repository management
		// repoCmd,      // TODO: Implement

		// Import/Export
		// importCmd,    // TODO: Implement
		// exportCmd,    // TODO: Implement
		convertCmd,

		// Data operations
		queryCmd,

		// CRUD operations
		// addCmd,       // TODO: Implement
		// getCmd,       // TODO: Implement
		// updateCmd,    // TODO: Implement
		// removeCmd,    // TODO: Implement
		// listCmd,      // TODO: Implement
		// traceCmd,     // TODO: Implement

		// Services
		// watchCmd,     // TODO: Implement
		// serveCmd,     // TODO: Implement

		// Simulation and Sync
		// simulateCmd,   // TODO: Implement
		// syncCmd,      // TODO: Implement

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
	postgisDB *database.PostGISDB
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
	// Start with defaults
	cfg := config.Default()
	cfg.Version = Version

	// Check for config file from command line
	configFile, _ := rootCmd.PersistentFlags().GetString("config")
	if configFile == "" {
		configFile = config.GetConfigPath()
	}

	// Load configuration using the enhanced config system
	loadedCfg, err := config.Load(configFile)
	if err != nil {
		logger.Warn("Failed to load configuration: %v", err)
		// Use defaults with environment overrides
		cfg.LoadFromEnv()
	} else {
		cfg = loadedCfg
	}

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

	// Database configuration (deprecated - using PostGIS only)
	if dbType := os.Getenv("ARX_DB_TYPE"); dbType != "" {
		cfg.Database.Type = dbType
	}
	// Path field no longer used with PostGIS-only architecture
}

// initializeDatabases sets up database connections
func initializeDatabases(ctx context.Context) error {
	// Always use PostGIS as the sole database
	return initializePostGISDatabase(ctx)
}

// initializePostGISDatabase initializes PostGIS as the sole database
func initializePostGISDatabase(ctx context.Context) error {
	pgConfig := appConfig.GetPostGISConfig()

	dbConfig := database.PostGISConfig{
		Host:     pgConfig.Host,
		Port:     pgConfig.Port,
		Database: pgConfig.Database,
		User:     pgConfig.User,
		Password: pgConfig.Password,
		SSLMode:  pgConfig.SSLMode,
	}
	postgisDB = database.NewPostGISDB(dbConfig)

	if err := postgisDB.Connect(ctx, ""); err != nil {
		return fmt.Errorf("failed to connect to PostGIS: %w", err)
	}

	dbConn = postgisDB
	logger.Info("Connected to PostGIS database: %s:%d/%s",
		pgConfig.Host, pgConfig.Port, pgConfig.Database)

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
