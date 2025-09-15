package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/joelpate/arxos/internal/common/logger"
)

var (
	// Version information (set during build)
	Version   = "dev"
	BuildTime = "unknown"
	Commit    = "unknown"
)

var rootCmd = &cobra.Command{
	Use:   "arx",
	Short: "ArxOS - Building File Converter",
	Long: `ArxOS converts building files to the universal BIM text format.

Supported formats:
  - IFC (Industry Foundation Classes)
  - PDF (Floor plans, as-builts)

Convert any building file to .bim.txt format for version control,
analysis, and integration with building management systems.`,
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

	// Add only essential commands
	rootCmd.AddCommand(
		convertCmd,
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