package cli

import (
	"context"
	"fmt"
	"os"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/cli/commands/building"
	"github.com/arx-os/arxos/internal/cli/commands/component"
	"github.com/arx-os/arxos/internal/cli/commands/integration"
	"github.com/arx-os/arxos/internal/cli/commands/spatial"
	"github.com/arx-os/arxos/internal/cli/commands/system"
	"github.com/arx-os/arxos/internal/cli/commands/user"
	"github.com/arx-os/arxos/internal/cli/commands/utility"
	"github.com/arx-os/arxos/internal/cli/commands/versioncontrol"
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
	a.rootCmd.AddCommand(system.CreateInitCommand(serviceContext))
	a.rootCmd.AddCommand(system.CreateInstallCommand(serviceContext))
	a.rootCmd.AddCommand(system.CreateHealthCommand(serviceContext))
	a.rootCmd.AddCommand(system.CreateMigrateCommand(serviceContext))
	a.rootCmd.AddCommand(system.CreateConfigCommand(serviceContext))

	// Repository management commands
	a.rootCmd.AddCommand(versioncontrol.CreateRepoCommand(serviceContext))

	// Building management commands
	a.rootCmd.AddCommand(building.CreateBuildingCommands(serviceContext))

	// Floor management commands
	a.rootCmd.AddCommand(building.CreateFloorCommands(serviceContext))

	// Room management commands
	a.rootCmd.AddCommand(building.CreateRoomCommands(serviceContext))

	// Equipment management commands
	a.rootCmd.AddCommand(building.CreateEquipmentCommands(serviceContext))

	// User management commands
	a.rootCmd.AddCommand(user.CreateUserCommands(serviceContext))

	// Spatial query commands
	a.rootCmd.AddCommand(spatial.CreateSpatialCommands(serviceContext))

	// Component management commands
	a.rootCmd.AddCommand(component.CreateComponentCommands(serviceContext))

	// BAS/BMS integration commands
	a.rootCmd.AddCommand(integration.NewBASCommand(serviceContext))

	// Git workflow commands
	a.rootCmd.AddCommand(versioncontrol.NewBranchCommand(serviceContext))
	a.rootCmd.AddCommand(versioncontrol.NewCheckoutCommand(serviceContext))
	a.rootCmd.AddCommand(versioncontrol.NewMergeCommand(serviceContext))
	a.rootCmd.AddCommand(versioncontrol.NewLogCommand(serviceContext))
	a.rootCmd.AddCommand(versioncontrol.NewDiffCommand(serviceContext))

	// Pull request commands (CMMS workflow)
	a.rootCmd.AddCommand(versioncontrol.NewPRCommand(serviceContext))
	a.rootCmd.AddCommand(versioncontrol.NewIssueCommand(serviceContext))

	// Contributor management commands
	a.rootCmd.AddCommand(user.NewContributorCommand(serviceContext))
	a.rootCmd.AddCommand(user.NewTeamCommand(serviceContext))

	// CADTUI command
	a.rootCmd.AddCommand(component.CreateCADTUICommand(serviceContext))

	// Import/Export commands
	a.rootCmd.AddCommand(integration.CreateImportCommand(serviceContext))
	a.rootCmd.AddCommand(integration.CreateExportCommand(serviceContext))
	a.rootCmd.AddCommand(integration.CreateConvertCommand(serviceContext))

	// Data operations
	a.rootCmd.AddCommand(utility.CreateQueryCommand(serviceContext))

	// Path-based query commands (universal naming convention)
	a.rootCmd.AddCommand(spatial.CreatePathGetCommand(serviceContext))
	a.rootCmd.AddCommand(spatial.CreatePathQueryCommand(serviceContext))

	// CRUD operations
	a.rootCmd.AddCommand(utility.CreateAddCommand(serviceContext))
	a.rootCmd.AddCommand(utility.CreateUpdateCommand(serviceContext))
	a.rootCmd.AddCommand(utility.CreateRemoveCommand(serviceContext))

	// Service commands
	a.rootCmd.AddCommand(system.CreateServeCommand(serviceContext))
	a.rootCmd.AddCommand(utility.CreateWatchCommand(serviceContext))

	// Utility commands
	a.rootCmd.AddCommand(utility.CreateTraceCommand(serviceContext))
	a.rootCmd.AddCommand(utility.CreateVisualizeCommand(serviceContext))
	a.rootCmd.AddCommand(utility.CreateRenderCommand(serviceContext))
	a.rootCmd.AddCommand(utility.CreateReportCommand(serviceContext))
	a.rootCmd.AddCommand(utility.CreateVersionCommand(serviceContext))
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
