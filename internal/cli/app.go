package cli

import (
	"context"
	"fmt"

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

// NewContainer creates and initializes the dependency injection container
func (a *App) NewContainer() *app.Container {
	container := app.NewContainer()

	// Initialize container with context
	ctx := context.Background()
	if err := container.Initialize(ctx, a.config); err != nil {
		// Log error but don't fail - container will be initialized lazily
		fmt.Printf("Warning: Failed to initialize container: %v\n", err)
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
	serviceContext := NewServiceContext(a.container)

	// System management commands
	a.rootCmd.AddCommand(commands.CreateInstallCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateHealthCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateMigrateCommand(serviceContext))

	// Repository management commands
	a.rootCmd.AddCommand(commands.CreateRepoCommand(serviceContext))

	// Component management commands
	a.rootCmd.AddCommand(commands.CreateComponentCommands(serviceContext))

	// CADTUI command
	a.rootCmd.AddCommand(commands.CreateCADTUICommand(serviceContext))

	// Import/Export commands
	a.rootCmd.AddCommand(commands.CreateImportCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateExportCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateConvertCommand(serviceContext))

	// Data operations
	a.rootCmd.AddCommand(commands.CreateQueryCommand(serviceContext))

	// CRUD operations
	a.rootCmd.AddCommand(commands.CreateAddCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateGetCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateUpdateCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateRemoveCommand(serviceContext))

	// Service commands
	a.rootCmd.AddCommand(commands.CreateServeCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateServeV2Command(serviceContext))
	a.rootCmd.AddCommand(commands.CreateWatchCommand(serviceContext))

	// Utility commands
	a.rootCmd.AddCommand(commands.CreateTraceCommand(serviceContext))
	a.rootCmd.AddCommand(commands.CreateVisualizeCommand(serviceContext))
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

func (l *Logger) Debug(msg string, fields ...interface{}) {
	fmt.Printf("[DEBUG] %s %v\n", msg, fields)
}

func (l *Logger) Info(msg string, fields ...interface{}) {
	fmt.Printf("[INFO] %s %v\n", msg, fields)
}

func (l *Logger) Warn(msg string, fields ...interface{}) {
	fmt.Printf("[WARN] %s %v\n", msg, fields)
}

func (l *Logger) Error(msg string, fields ...interface{}) {
	fmt.Printf("[ERROR] %s %v\n", msg, fields)
}

func (l *Logger) Fatal(msg string, fields ...interface{}) {
	fmt.Printf("[FATAL] %s %v\n", msg, fields)
}
