package cli

import (
	"context"
	"fmt"
	"os"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/cli/commands"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/spf13/cobra"
)

// App represents the CLI application following Go Blueprint standards
type App struct {
	config    *config.Config
	rootCmd   *cobra.Command
	logger    domain.Logger
	container *app.Container
}

// VersionInfo holds version information
type VersionInfo struct {
	Version   string
	BuildTime string
	Commit    string
}

// NewApp creates a new CLI application
func NewApp(cfg *config.Config) *App {
	app := &App{
		config: cfg,
		logger: &Logger{}, // Placeholder logger
	}

	// Initialize dependency injection container
	app.container = app.NewContainer()

	// Setup root command
	app.setupRootCommand()

	return app
}

// NewAppWithVersion creates a new CLI application with version information
func NewAppWithVersion(cfg *config.Config, version, buildTime, commit string) *App {
	app := &App{
		config: cfg,
		logger: &Logger{}, // Placeholder logger
	}

	// Initialize dependency injection container
	app.container = app.NewContainer()

	// Setup root command with version info
	app.setupRootCommand()

	// Version info is available via the main package variables
	// Commands can access version info through cmd/arx/main.go variables

	return app
}

// NewContainer creates and initializes the dependency injection container
func (a *App) NewContainer() *app.Container {
	container := app.NewContainer()

	// Initialize container with context
	ctx := context.Background()
	if err := container.Initialize(ctx, a.config); err != nil {
		// FAIL FAST - Don't continue with broken container
		fmt.Fprintf(os.Stderr, "❌ FATAL: Failed to initialize ArxOS container\n")
		fmt.Fprintf(os.Stderr, "\nError: %v\n\n", err)
		fmt.Fprintf(os.Stderr, "Common causes:\n")
		fmt.Fprintf(os.Stderr, "  1. PostgreSQL not running (check: psql -h localhost -U postgres)\n")
		fmt.Fprintf(os.Stderr, "  2. Database not created (run: createdb arxos_dev)\n")
		fmt.Fprintf(os.Stderr, "  3. PostGIS extension not installed (run: CREATE EXTENSION postgis;)\n")
		fmt.Fprintf(os.Stderr, "  4. Invalid connection settings in config\n\n")
		fmt.Fprintf(os.Stderr, "Quick fix:\n")
		fmt.Fprintf(os.Stderr, "  ./scripts/setup-dev-database.sh\n\n")
		os.Exit(1)
	}

	return container
}

// Execute runs the CLI application
func (a *App) Execute() error {
	return a.rootCmd.Execute()
}

// setupRootCommand configures the root command and all subcommands
func (a *App) setupRootCommand() {
	a.rootCmd = &cobra.Command{
		Use:   "arx",
		Short: "ArxOS - Building Operating System",
		Long: `ArxOS is a universal building operating system that manages building data
with Git-like version control, spatial precision, and multi-interface support.

Core features:
  • Building Repository - Git-like version control for buildings
  • IFC Import - Industry-standard building data import
  • Spatial Operations - Millimeter-precision coordinate management
  • Multi-Platform - CLI, Web, and Mobile interfaces
  • Real-time Sync - Live updates across all platforms

For detailed help on any command, use: arx <command> --help`,
		SilenceUsage:  true,
		SilenceErrors: true,
	}

	// Add global flags
	a.rootCmd.PersistentFlags().BoolP("verbose", "v", false, "verbose output")
	a.rootCmd.PersistentFlags().BoolP("quiet", "q", false, "suppress non-error output")
	a.rootCmd.PersistentFlags().String("config", "", "config file path")
	a.rootCmd.PersistentFlags().String("database", "", "database connection string")

	// Wire all commands
	a.wireCommands()
}

// wireCommands wires all commands following Go Blueprint standards
func (a *App) wireCommands() {
	// Create service context for commands
	serviceContext := a.container

	// System management commands
	a.rootCmd.AddCommand(commands.CreateInitCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateInstallCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateHealthCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateMigrateCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateConfigCommand(serviceContext))

	// Repository management commands
	a.rootCmd.AddCommand(commands.CreateRepoCommand(serviceContext))

	// Building management commands
	a.rootCmd.AddCommand(commands.CreateBuildingCommands(serviceContext))

	// Floor management commands
	a.rootCmd.AddCommand(commands.CreateFloorCommands(serviceContext))

	// Room management commands
	a.rootCmd.AddCommand(commands.CreateRoomCommands(serviceContext))

	// Equipment management commands
	a.rootCmd.AddCommand(commands.CreateEquipmentCommands(serviceContext))

	// User management commands
	a.rootCmd.AddCommand(commands.CreateUserCommands(serviceContext))

	// Spatial query commands
	a.rootCmd.AddCommand(commands.CreateSpatialCommands(serviceContext))

	// Component management commands
	a.rootCmd.AddCommand(commands.CreateComponentCommands(serviceContext))

	// BAS/BMS integration commands
	a.rootCmd.AddCommand(commands.NewBASCommand(serviceContext))

	// Git workflow commands
	a.rootCmd.AddCommand(commands.NewBranchCommand(serviceContext))
	a.rootCmd.AddCommand(commands.NewCheckoutCommand(serviceContext))
	a.rootCmd.AddCommand(commands.NewMergeCommand(serviceContext))
	a.rootCmd.AddCommand(commands.NewLogCommand(serviceContext))
	a.rootCmd.AddCommand(commands.NewDiffCommand(serviceContext))

	// Pull request commands (CMMS workflow)
	a.rootCmd.AddCommand(commands.NewPRCommand(serviceContext))
	a.rootCmd.AddCommand(commands.NewIssueCommand(serviceContext))

	// Contributor management commands
	a.rootCmd.AddCommand(commands.NewContributorCommand(serviceContext))
	a.rootCmd.AddCommand(commands.NewTeamCommand(serviceContext))

	// CADTUI command
	a.rootCmd.AddCommand(commands.CreateCADTUICommand(serviceContext))

	// Import/Export commands
	a.rootCmd.AddCommand(commands.CreateImportCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateExportCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateConvertCommand(serviceContext))

	// Data operations
	a.rootCmd.AddCommand(commands.CreateQueryCommand(serviceContext))

	// Path-based query command (primary get command using universal paths)
	a.rootCmd.AddCommand(commands.CreatePathGetCommand())
	
	// CRUD operations
	a.rootCmd.AddCommand(commands.CreateAddCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateUpdateCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateRemoveCommand(serviceContext))

	// Service commands
	a.rootCmd.AddCommand(commands.CreateServeCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateWatchCommand(serviceContext))

	// Utility commands
	a.rootCmd.AddCommand(commands.CreateTraceCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateVisualizeCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateRenderCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateReportCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateVersionCommand(serviceContext))
}

// GetConfig returns the application configuration
func (a *App) GetConfig() *config.Config {
	return a.config
}

// GetContainer returns the dependency injection container
func (a *App) GetContainer() *app.Container {
	return a.container
}

// GetLogger returns the logger
func (a *App) GetLogger() domain.Logger {
	return a.logger
}

// Logger is a placeholder logger implementation
type Logger struct{}

func (l *Logger) Debug(msg string, fields ...any) {
	fmt.Printf("[DEBUG] %s %v\n", msg, fields)
}

func (l *Logger) Info(msg string, fields ...any) {
	fmt.Printf("[INFO] %s %v\n", msg, fields)
}

func (l *Logger) Warn(msg string, fields ...any) {
	fmt.Printf("[WARN] %s %v\n", msg, fields)
}

func (l *Logger) Error(msg string, fields ...any) {
	fmt.Printf("[ERROR] %s %v\n", msg, fields)
}

func (l *Logger) Fatal(msg string, fields ...any) {
	fmt.Printf("[FATAL] %s %v\n", msg, fields)
}
