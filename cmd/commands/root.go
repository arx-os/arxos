package commands

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/arxos/arxos/cmd/commands/query"
	"github.com/arxos/arxos/cmd/commands/ingest"
	// "github.com/arxos/arxos/cmd/commands/export"    // TODO: Implement
	// "github.com/arxos/arxos/cmd/commands/validate"  // TODO: Implement
	// "github.com/arxos/arxos/cmd/commands/analyze"   // TODO: Implement
	// "github.com/arxos/arxos/cmd/commands/serve"     // TODO: Implement
	"github.com/arxos/arxos/cmd/commands/ai"
	"github.com/arxos/arxos/cmd/commands/support"
	"github.com/arxos/arxos/cmd/commands/state"
	"github.com/arxos/arxos/cmd/commands/deploy"
	"github.com/arxos/arxos/cmd/commands/gitops"
	"github.com/arxos/arxos/cmd/config"
	"github.com/arxos/arxos/cmd/display"
)

var (
	cfgFile string
	verbose bool
	format  string
	
	// Version info
	Version   string
	BuildDate string
	GitCommit string
)

// RootCmd represents the base command
var RootCmd = &cobra.Command{
	Use:   "arxos",
	Short: "Arxos CLI - Building Infrastructure as Code",
	Long: `Arxos CLI provides a powerful interface for managing building information models,
querying architectural data, and bridging digital twins with physical reality.

Use 'arxos [command] --help' for more information about a command.`,
	PersistentPreRunE: initializeConfig,
}

// Execute adds all child commands and executes the root command
func Execute() {
	if err := RootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func init() {
	// Global flags
	RootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default: ~/.arxos/config.yaml)")
	RootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "verbose output")
	RootCmd.PersistentFlags().StringVarP(&format, "format", "f", "table", "output format (table|json|yaml)")

	// Add command categories
	RootCmd.AddCommand(
		query.QueryCmd,
		ingest.IngestCmd,
		// export.ExportCmd,      // TODO: Implement
		// validate.ValidateCmd,  // TODO: Implement
		// analyze.AnalyzeCmd,    // TODO: Implement
		// serve.ServeCmd,        // TODO: Implement
		ai.AICmd,
		support.SupportCmd,  // Support operations (admin only)
		state.StateCmd,      // Building state management (BIaC)
		deploy.DeployCmd,    // Deployment engine (BIaC)
		gitops.GitOpsCmd,    // GitOps features (BIaC)
		interactiveCmd,
		versionCmd,
	)
}

// Interactive mode command
var interactiveCmd = &cobra.Command{
	Use:   "interactive",
	Short: "Start interactive AQL shell",
	Aliases: []string{"shell", "repl"},
	RunE: func(cmd *cobra.Command, args []string) error {
		return runInteractiveMode()
	},
}

// Version command
var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print version information",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("Arxos CLI v%s\n", Version)
		fmt.Printf("Build Date: %s\n", BuildDate)
		fmt.Printf("Git Commit: %s\n", GitCommit)
	},
}

// SetVersion sets the version information
func SetVersion(version, buildDate, gitCommit string) {
	Version = version
	BuildDate = buildDate
	GitCommit = gitCommit
}

func initializeConfig(cmd *cobra.Command, args []string) error {
	// Load configuration
	if err := config.Load(cfgFile); err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	// Set display format
	display.SetFormat(format)
	display.SetVerbose(verbose)

	return nil
}

func runInteractiveMode() error {
	// This will be implemented in interactive.go
	// For now, call the existing main.go logic
	fmt.Println("Starting interactive AQL shell...")
	return nil
}