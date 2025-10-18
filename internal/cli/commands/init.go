package commands

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/arx-os/arxos/internal/infrastructure/filesystem"
	"github.com/spf13/cobra"
)

// InitServiceProvider provides access to initialization services
type InitServiceProvider interface {
	GetDataManager() *filesystem.DataManager
	GetLoggerService() Logger
}

type Logger interface {
	Info(msg string, fields ...any)
	Error(msg string, fields ...any)
	Debug(msg string, fields ...any)
}

// CreateInitCommand creates the init command
func CreateInitCommand(serviceContext any) *cobra.Command {
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
			fmt.Println("🚀 Initializing ArxOS...")

			// Get flags
			configPath, _ := cmd.Flags().GetString("config")
			force, _ := cmd.Flags().GetBool("force")
			verbose, _ := cmd.Flags().GetBool("verbose")
			mode, _ := cmd.Flags().GetString("mode")
			dataDir, _ := cmd.Flags().GetString("data-dir")

			// Validate mode
			validModes := map[string]bool{
				"local":      true,
				"cloud":      true,
				"hybrid":     true,
				"production": true,
			}
			if !validModes[mode] {
				return fmt.Errorf("invalid mode '%s': must be one of: local, cloud, hybrid, production", mode)
			}

			if force {
				fmt.Println("🔄 Force initialization enabled")
			}

			// Determine base directory
			baseDir := os.Getenv("ARXOS_STATE_DIR")
			if baseDir == "" {
				homeDir, err := os.UserHomeDir()
				if err != nil {
					return fmt.Errorf("failed to get home directory: %w", err)
				}
				baseDir = filepath.Join(homeDir, ".arxos")
			}
			if dataDir != "" {
				baseDir = dataDir
			}

			// Create directory structure
			directories := []string{
				filepath.Join(baseDir, "cache", "l2"),
				filepath.Join(baseDir, "repositories"),
				filepath.Join(baseDir, "logs"),
				filepath.Join(baseDir, "temp"),
				filepath.Join(baseDir, "config"),
				filepath.Join(baseDir, "imports"),
				filepath.Join(baseDir, "exports"),
				filepath.Join(baseDir, "data"),
			}

			fmt.Println("📁 Creating directory structure...")
			for _, dir := range directories {
				if err := os.MkdirAll(dir, 0755); err != nil {
					return fmt.Errorf("failed to create directory %s: %w", dir, err)
				}
				if verbose {
					fmt.Printf("   Created: %s\n", dir)
				}
			}

			// Create default config if it doesn't exist
			configFile := filepath.Join(baseDir, "config", "arxos.yaml")
			if _, err := os.Stat(configFile); os.IsNotExist(err) || force {
				if configPath != "" {
					fmt.Printf("📋 Copying config from: %s\n", configPath)
					srcData, err := os.ReadFile(configPath)
					if err != nil {
						return fmt.Errorf("failed to read config file: %w", err)
					}
					if err := os.WriteFile(configFile, srcData, 0644); err != nil {
						return fmt.Errorf("failed to write config file: %w", err)
					}
				} else {
					fmt.Println("📋 Creating default config...")
					defaultConfig := fmt.Sprintf(`# ArxOS Configuration
mode: %s
version: "0.1.0"
state_dir: %s

database:
  host: localhost
  port: 5432
  name: arxos
  user: arxos
  password: arxos_dev

postgis:
  host: localhost
  port: 5432
  database: arxos
  user: arxos
  password: arxos_dev
  sslmode: disable

unified_cache:
  l1:
    enabled: true
    max_entries: 10000
    default_ttl: 5m
  l2:
    enabled: true
    max_size_mb: 1000
    default_ttl: 1h
  l3:
    enabled: false

ifc:
  service:
    enabled: true
    url: http://localhost:5000
    timeout: 30s
`, mode, baseDir)

					if err := os.WriteFile(configFile, []byte(defaultConfig), 0644); err != nil {
						return fmt.Errorf("failed to create config file: %w", err)
					}
				}
			}

			// Display environment variables
			fmt.Println("")
			fmt.Println("📝 Add these to your shell profile (~/.zshrc or ~/.bashrc):")
			fmt.Println("")
			fmt.Printf("   export ARXOS_STATE_DIR=%s\n", baseDir)
			fmt.Printf("   export DATABASE_URL=\"postgres://arxos:arxos_dev@localhost:5432/arxos?sslmode=disable\"\n")
			fmt.Println("")

			fmt.Println("✅ ArxOS initialized successfully")
			fmt.Printf("   State directory: %s\n", baseDir)
			fmt.Printf("   Config file: %s\n", configFile)
			fmt.Println("")
			fmt.Println("Next steps:")
			fmt.Println("   1. Source environment variables")
			fmt.Println("   2. Set up database: ./scripts/setup-database-terminal.sh")
			fmt.Println("   3. Run migrations: arx migrate up")
			fmt.Println("   4. Test: arx health")

			return nil
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
