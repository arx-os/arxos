package commands

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/infrastructure/filesystem"
	"github.com/spf13/cobra"
)

// InitServiceProvider provides access to initialization services
type InitServiceProvider interface {
	GetDataManager() *filesystem.DataManager
	GetLoggerService() interface {
		Info(msg string, fields ...interface{})
		Error(msg string, fields ...interface{})
		Debug(msg string, fields ...interface{})
	}
}

// CreateInitCommand creates the init command
func CreateInitCommand(serviceContext interface{}) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "init",
		Short: "Initialize ArxOS configuration and directories",
		Long: `Initialize ArxOS by creating the necessary directory structure, 
configuration files, and setting up the local environment.

This command will:
- Create ~/.arxos directory structure
- Generate default configuration files
- Set up cache and data directories
- Initialize logging system
- Create initial state files
- Validate the installation

Examples:
  arx init                    # Initialize with default settings
  arx init --config custom.yml # Initialize with custom config
  arx init --force            # Force reinitialization`,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runInitCommand(cmd, serviceContext)
		},
	}

	// Add flags
	cmd.Flags().String("config", "", "Custom configuration file path")
	cmd.Flags().Bool("force", false, "Force reinitialization even if already initialized")
	cmd.Flags().Bool("verbose", false, "Verbose output")
	cmd.Flags().String("mode", "local", "Initialization mode (local, cloud, hybrid)")
	cmd.Flags().String("data-dir", "", "Custom data directory path")

	return cmd
}

// runInitCommand executes the initialization process
func runInitCommand(cmd *cobra.Command, serviceContext interface{}) error {
	fmt.Println("🚀 Initializing ArxOS...")
	fmt.Println("================================")

	// Get flags
	configPath, _ := cmd.Flags().GetString("config")
	force, _ := cmd.Flags().GetBool("force")
	verbose, _ := cmd.Flags().GetBool("verbose")
	mode, _ := cmd.Flags().GetString("mode")
	dataDir, _ := cmd.Flags().GetString("data-dir")

	// Validate mode
	if mode != "local" && mode != "cloud" && mode != "hybrid" {
		return fmt.Errorf("invalid mode: %s. Must be one of: local, cloud, hybrid", mode)
	}

	// Initialize context
	ctx := context.Background()

	// Step 1: Load or create configuration
	fmt.Println("📋 Step 1: Setting up configuration...")
	cfg, err := setupConfiguration(configPath, mode, dataDir, force, verbose)
	if err != nil {
		return fmt.Errorf("failed to setup configuration: %w", err)
	}
	fmt.Println("✅ Configuration setup complete")

	// Step 2: Create directory structure
	fmt.Println("📁 Step 2: Creating directory structure...")
	if err := createDirectoryStructure(ctx, cfg, force, verbose); err != nil {
		return fmt.Errorf("failed to create directory structure: %w", err)
	}
	fmt.Println("✅ Directory structure created")

	// Step 3: Initialize cache system
	fmt.Println("💾 Step 3: Setting up cache system...")
	if err := initializeCacheSystem(ctx, cfg, verbose); err != nil {
		return fmt.Errorf("failed to initialize cache system: %w", err)
	}
	fmt.Println("✅ Cache system initialized")

	// Step 4: Setup logging
	fmt.Println("📝 Step 4: Setting up logging system...")
	if err := setupLoggingSystem(ctx, cfg, verbose); err != nil {
		return fmt.Errorf("failed to setup logging system: %w", err)
	}
	fmt.Println("✅ Logging system setup complete")

	// Step 5: Create initial state files
	fmt.Println("🔄 Step 5: Creating initial state files...")
	if err := createInitialStateFiles(ctx, cfg, verbose); err != nil {
		return fmt.Errorf("failed to create initial state files: %w", err)
	}
	fmt.Println("✅ Initial state files created")

	// Step 6: Validate installation
	fmt.Println("🔍 Step 6: Validating installation...")
	if err := validateInstallation(ctx, cfg, verbose); err != nil {
		return fmt.Errorf("installation validation failed: %w", err)
	}
	fmt.Println("✅ Installation validation passed")

	// Success message
	fmt.Println("\n🎉 ArxOS initialization completed successfully!")
	fmt.Println("================================================")
	fmt.Printf("📁 Data directory: %s\n", cfg.Storage.Data.BasePath)
	fmt.Printf("💾 Cache directory: %s\n", cfg.GetCachePath())
	fmt.Printf("📝 Logs directory: %s\n", cfg.GetLogsPath())
	fmt.Printf("⚙️  Config file: %s\n", config.GetConfigPath())
	fmt.Printf("🌐 Mode: %s\n", cfg.Mode)
	fmt.Println("\nNext steps:")
	fmt.Println("  • Run 'arx health' to check system status")
	fmt.Println("  • Run 'arx repo init <name>' to create your first building repository")
	fmt.Println("  • Run 'arx serve' to start the API server")

	return nil
}

// setupConfiguration loads or creates the configuration
func setupConfiguration(configPath, mode, dataDir string, force, verbose bool) (*config.Config, error) {
	var cfg *config.Config
	var err error

	// If custom config path provided, load it
	if configPath != "" {
		if verbose {
			fmt.Printf("  Loading custom configuration from: %s\n", configPath)
		}
		cfg, err = config.Load(configPath)
		if err != nil {
			return nil, fmt.Errorf("failed to load custom config: %w", err)
		}
	} else {
		// Check if config already exists
		defaultConfigPath := config.GetConfigPath()
		if _, err := os.Stat(defaultConfigPath); err == nil && !force {
			if verbose {
				fmt.Printf("  Loading existing configuration from: %s\n", defaultConfigPath)
			}
			cfg, err = config.Load(defaultConfigPath)
			if err != nil {
				return nil, fmt.Errorf("failed to load existing config: %w", err)
			}
		} else {
			// Create new configuration
			if verbose {
				fmt.Printf("  Creating new configuration\n")
			}
			cfg = createDefaultConfiguration(mode, dataDir)
		}
	}

	// Override mode if specified
	if mode != "" {
		cfg.Mode = config.Mode(mode)
	}

	// Override data directory if specified
	if dataDir != "" {
		cfg.Storage.Data.BasePath = dataDir
		cfg.StateDir = dataDir
		cfg.CacheDir = filepath.Join(dataDir, "cache")
		cfg.Storage.LocalPath = filepath.Join(dataDir, "data")
	}

	// Save configuration
	if err := saveConfiguration(cfg); err != nil {
		return nil, fmt.Errorf("failed to save configuration: %w", err)
	}

	return cfg, nil
}

// createDefaultConfiguration creates a default configuration based on mode
func createDefaultConfiguration(mode, dataDir string) *config.Config {
	homeDir, _ := os.UserHomeDir()

	// Use custom data directory if provided, otherwise use default
	var basePath string
	if dataDir != "" {
		basePath = dataDir
	} else {
		basePath = filepath.Join(homeDir, ".arxos")
	}

	cfg := &config.Config{
		Mode:     config.Mode(mode),
		Version:  "0.1.0",
		StateDir: basePath,
		CacheDir: filepath.Join(basePath, "cache"),

		Cloud: config.CloudConfig{
			Enabled:      mode == "cloud" || mode == "hybrid",
			BaseURL:      "https://api.arxos.io",
			SyncEnabled:  mode == "cloud" || mode == "hybrid",
			SyncInterval: 5 * time.Minute,
		},

		Storage: config.StorageConfig{
			Backend:   "local",
			LocalPath: filepath.Join(basePath, "data"),
			Data: config.DataConfig{
				BasePath:        basePath,
				RepositoriesDir: "repositories",
				CacheDir:        "cache",
				LogsDir:         "logs",
				TempDir:         "temp",
			},
		},

		API: config.APIConfig{
			Timeout:       30 * time.Second,
			RetryAttempts: 3,
			RetryDelay:    1 * time.Second,
			UserAgent:     "ArxOS-CLI/0.1.0",
		},

		Telemetry: config.TelemetryConfig{
			Enabled:    false,
			Endpoint:   "https://telemetry.arxos.io",
			SampleRate: 0.1,
			Debug:      false,
		},

		Features: config.FeatureFlags{
			CloudSync:     mode == "cloud" || mode == "hybrid",
			AIIntegration: false,
			OfflineMode:   true,
			BetaFeatures:  false,
			Analytics:     false,
			AutoUpdate:    false,
		},

		Security: config.SecurityConfig{
			JWTExpiry:          24 * time.Hour,
			SessionTimeout:     30 * time.Minute,
			APIRateLimit:       100,
			APIRateLimitWindow: time.Minute,
			EnableAuth:         true,
			EnableTLS:          false,
			AllowedOrigins:     []string{"http://localhost:3000", "http://localhost:8080"},
			BcryptCost:         10,
		},

		TUI: config.TUIConfig{
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

		IFC: config.IFCConfig{
			Service: config.IFCServiceConfig{
				Enabled: true,
				URL:     "http://localhost:5000",
				Timeout: "30s",
				Retries: 3,
				CircuitBreaker: config.IFCCircuitBreakerConfig{
					Enabled:          true,
					FailureThreshold: 5,
					RecoveryTimeout:  "60s",
				},
			},
			Fallback: config.IFCFallbackConfig{
				Enabled: true,
				Parser:  "native",
			},
			Performance: config.IFCPerformanceConfig{
				CacheEnabled: true,
				CacheTTL:     "1h",
				MaxFileSize:  "100MB",
			},
		},

		Database: config.DatabaseConfig{
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

		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_dev",
			User:     "arxos",
			Password: "arxos_dev",
			SSLMode:  "disable",
			SRID:     900913,
		},
	}

	return cfg
}

// saveConfiguration saves the configuration to disk
func saveConfiguration(cfg *config.Config) error {
	configPath := config.GetConfigPath()

	// Ensure directory exists
	if err := os.MkdirAll(filepath.Dir(configPath), 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// Save as YAML (preferred format)
	return cfg.Save(configPath)
}

// createDirectoryStructure creates all necessary directories
func createDirectoryStructure(ctx context.Context, cfg *config.Config, force, verbose bool) error {
	dm := filesystem.NewDataManager(cfg)

	if verbose {
		fmt.Printf("  Creating directories in: %s\n", cfg.Storage.Data.BasePath)
	}

	// Ensure all data directories exist
	if err := dm.EnsureDataDirectories(ctx); err != nil {
		return fmt.Errorf("failed to ensure data directories: %w", err)
	}

	// Create additional directories
	additionalDirs := []string{
		filepath.Join(cfg.Storage.Data.BasePath, "state"),
		filepath.Join(cfg.Storage.Data.BasePath, "state", "sessions"),
		filepath.Join(cfg.Storage.Data.BasePath, "state", "sync"),
		filepath.Join(cfg.GetCachePath(), "ifc"),
		filepath.Join(cfg.GetCachePath(), "spatial"),
		filepath.Join(cfg.GetCachePath(), "api"),
	}

	for _, dir := range additionalDirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
		if verbose {
			fmt.Printf("  Created directory: %s\n", dir)
		}
	}

	return nil
}

// initializeCacheSystem sets up the cache system
func initializeCacheSystem(ctx context.Context, cfg *config.Config, verbose bool) error {
	cacheDir := cfg.GetCachePath()

	// Create cache configuration file
	cacheConfigContent := `{
  "version": "1.0",
  "created_at": "` + time.Now().Format(time.RFC3339) + `",
  "cache_types": {
    "ifc": {
      "enabled": true,
      "ttl": "2h",
      "max_size": "1GB"
    },
    "spatial": {
      "enabled": true,
      "ttl": "1h",
      "max_size": "500MB"
    },
    "api": {
      "enabled": true,
      "ttl": "30m",
      "max_size": "100MB"
    }
  }
}`

	cacheConfigPath := filepath.Join(cacheDir, "config.json")
	if verbose {
		fmt.Printf("  Creating cache configuration: %s\n", cacheConfigPath)
	}

	if err := os.WriteFile(cacheConfigPath, []byte(cacheConfigContent), 0644); err != nil {
		return fmt.Errorf("failed to create cache configuration: %w", err)
	}

	return nil
}

// setupLoggingSystem initializes the logging system
func setupLoggingSystem(ctx context.Context, cfg *config.Config, verbose bool) error {
	logsDir := cfg.GetLogsPath()

	// Create log configuration
	logConfigContent := `{
  "version": "1.0",
  "created_at": "` + time.Now().Format(time.RFC3339) + `",
  "loggers": {
    "application": {
      "level": "info",
      "file": "application.log",
      "max_size": "100MB",
      "max_backups": 5,
      "max_age": 30
    },
    "error": {
      "level": "error",
      "file": "error.log",
      "max_size": "50MB",
      "max_backups": 10,
      "max_age": 90
    },
    "debug": {
      "level": "debug",
      "file": "debug.log",
      "max_size": "200MB",
      "max_backups": 3,
      "max_age": 7
    }
  }
}`

	logConfigPath := filepath.Join(logsDir, "config.json")
	if verbose {
		fmt.Printf("  Creating log configuration: %s\n", logConfigPath)
	}

	if err := os.WriteFile(logConfigPath, []byte(logConfigContent), 0644); err != nil {
		return fmt.Errorf("failed to create log configuration: %w", err)
	}

	// Create initial log files
	logFiles := []string{"application.log", "error.log", "debug.log"}
	for _, logFile := range logFiles {
		logPath := filepath.Join(logsDir, logFile)
		initialContent := fmt.Sprintf("# ArxOS %s Log\n# Created: %s\n# Level: %s\n\n",
			logFile, time.Now().Format(time.RFC3339), getLogLevel(logFile))

		if err := os.WriteFile(logPath, []byte(initialContent), 0644); err != nil {
			return fmt.Errorf("failed to create log file %s: %w", logFile, err)
		}
		if verbose {
			fmt.Printf("  Created log file: %s\n", logPath)
		}
	}

	return nil
}

// getLogLevel returns the appropriate log level for a log file
func getLogLevel(filename string) string {
	switch filename {
	case "application.log":
		return "info"
	case "error.log":
		return "error"
	case "debug.log":
		return "debug"
	default:
		return "info"
	}
}

// createInitialStateFiles creates initial state files
func createInitialStateFiles(ctx context.Context, cfg *config.Config, verbose bool) error {
	stateDir := filepath.Join(cfg.Storage.Data.BasePath, "state")

	// Create application state file
	appStateContent := `{
  "version": "1.0",
  "created_at": "` + time.Now().Format(time.RFC3339) + `",
  "initialized": true,
  "mode": "` + string(cfg.Mode) + `",
  "last_sync": null,
  "repositories": [],
  "settings": {
    "auto_sync": ` + fmt.Sprintf("%t", cfg.Cloud.SyncEnabled) + `,
    "sync_interval": "` + cfg.Cloud.SyncInterval.String() + `",
    "offline_mode": ` + fmt.Sprintf("%t", cfg.Features.OfflineMode) + `
  }
}`

	appStatePath := filepath.Join(stateDir, "app.json")
	if verbose {
		fmt.Printf("  Creating application state: %s\n", appStatePath)
	}

	if err := os.WriteFile(appStatePath, []byte(appStateContent), 0644); err != nil {
		return fmt.Errorf("failed to create application state: %w", err)
	}

	// Create sync state file
	syncStatePath := filepath.Join(stateDir, "sync", "state.json")
	syncStateContent := `{
  "version": "1.0",
  "created_at": "` + time.Now().Format(time.RFC3339) + `",
  "last_sync": null,
  "sync_enabled": ` + fmt.Sprintf("%t", cfg.Cloud.SyncEnabled) + `,
  "sync_interval": "` + cfg.Cloud.SyncInterval.String() + `",
  "pending_changes": [],
  "conflict_resolution": "manual"
}`

	if err := os.WriteFile(syncStatePath, []byte(syncStateContent), 0644); err != nil {
		return fmt.Errorf("failed to create sync state: %w", err)
	}

	if verbose {
		fmt.Printf("  Created sync state: %s\n", syncStatePath)
	}

	return nil
}

// validateInstallation validates the installation
func validateInstallation(ctx context.Context, cfg *config.Config, verbose bool) error {
	dm := filesystem.NewDataManager(cfg)

	// Validate directory structure
	if err := dm.ValidateDataDirectories(ctx); err != nil {
		return fmt.Errorf("directory validation failed: %w", err)
	}

	// Check configuration validity
	if err := cfg.Validate(); err != nil {
		return fmt.Errorf("configuration validation failed: %w", err)
	}

	// Check file permissions
	requiredFiles := []string{
		config.GetConfigPath(),
		filepath.Join(cfg.GetCachePath(), "config.json"),
		filepath.Join(cfg.GetLogsPath(), "config.json"),
		filepath.Join(cfg.Storage.Data.BasePath, "state", "app.json"),
	}

	for _, file := range requiredFiles {
		if _, err := os.Stat(file); err != nil {
			return fmt.Errorf("required file missing: %s", file)
		}
		if verbose {
			fmt.Printf("  Validated file: %s\n", file)
		}
	}

	return nil
}
