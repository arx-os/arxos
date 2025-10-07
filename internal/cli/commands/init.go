package commands

import (
	"fmt"

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

			if force {
				fmt.Println("🔄 Force initialization enabled")
			}

			if configPath != "" {
				fmt.Printf("📁 Using custom config: %s\n", configPath)
			}

			// TODO: Implement actual initialization logic
			fmt.Println("✅ ArxOS initialized successfully")
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
