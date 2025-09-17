package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/arx-os/arxos/internal/common/logger"
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
}