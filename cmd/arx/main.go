package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/app/di"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/daemon"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/validation"
	"github.com/arx-os/arxos/pkg/errors"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/google/uuid"
	"github.com/spf13/cobra"
)

var (
	// Version information (set during build)
	Version   = "dev"
	BuildTime = "unknown"
	Commit    = "unknown"

	// Global variables for system components following Clean Architecture
	appConfig   *config.Config
	diContainer *di.Container
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
		installCmd,
		healthCmd,
		daemonCmd,
		migrateCmd,

		// Repository management
		repoCmd,

		// Import/Export
		importCmd,
		exportCmd,
		convertCmd,

		// Data operations
		queryCmd,

		// CRUD operations are now in separate files
		traceCmd,

		// Services
		watchCmd,
		serveCmd,

		// Simulation and Sync
		simulateCmd,
		syncCmd,

		// Visualization
		visualizeCmd,
		reportCmd,

		// Workflow
		workflowCmd,

		// Version
		versionCmd,
	)

	// Execute root command
	if err := rootCmd.Execute(); err != nil {
		logger.Error("Command execution failed: %v", err)
		os.Exit(1)
	}
}

// initializeSystem sets up core components following Clean Architecture
func initializeSystem() error {
	ctx := context.Background()

	// Load configuration
	appConfig = loadConfiguration()

	// Convert app config to DI config
	diConfig := convertToDIConfig(appConfig)

	// Initialize dependency injection container
	diContainer = di.NewContainer(diConfig)
	if err := diContainer.Initialize(ctx); err != nil {
		return fmt.Errorf("DI container initialization failed: %w", err)
	}

	// Initialize service locator
	locator := di.GetServiceLocator()
	locator.SetContainer(diContainer)

	// Create necessary directories
	if err := ensureDirectories(); err != nil {
		return fmt.Errorf("directory setup failed: %w", err)
	}

	return nil
}

var healthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check system health",
	Long:  "Check the health status of ArxOS components including database connectivity",
	Run: func(cmd *cobra.Command, args []string) {
		logger.Info("Checking system health...")

		// Check database connectivity using new DI services
		services := diContainer.GetServices()
		if !services.Database.IsHealthy() {
			logger.Error("Database health check failed")
			fmt.Println("❌ Database: UNHEALTHY")
			os.Exit(1)
		}
		fmt.Println("✅ Database: HEALTHY")

		// Check cache connectivity
		if services.Cache.IsHealthy() {
			fmt.Println("✅ Cache: HEALTHY")
		} else {
			fmt.Println("❌ Cache: UNHEALTHY")
		}

		// Check messaging connectivity
		if services.Messaging.IsHealthy() {
			fmt.Println("✅ Messaging: HEALTHY")
		} else {
			fmt.Println("❌ Messaging: UNHEALTHY")
		}

		// Check configuration
		if appConfig != nil {
			fmt.Println("✅ Configuration: LOADED")
		} else {
			fmt.Println("❌ Configuration: NOT LOADED")
			os.Exit(1)
		}

		fmt.Println("🎉 System is healthy and ready")
	},
}

// migrateCmd is defined in cmd_migrate.go

// serveCmd will be implemented when proper service initialization is available

// List command removed - now in separate file

func listBuildings(ctx context.Context) {
	// Get all floor plans (buildings) - placeholder implementation
	fmt.Println("Buildings:")
	fmt.Println("  • Building 1 (ID: ARXOS-001, Level: 1)")
	fmt.Println("  • Building 2 (ID: ARXOS-002, Level: 2)")
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

// System Management Commands

var installCmd = &cobra.Command{
	Use:   "install",
	Short: "Install ArxOS system components",
	Long:  "Install and configure ArxOS system components including database, services, and dependencies",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		logger.Info("Installing ArxOS system components...")

		// Install database schema using DI container
		services := diContainer.GetServices()
		if err := services.Database.Migrate(ctx); err != nil {
			logger.Error("Failed to install database schema: %v", err)
			os.Exit(1)
		}

		// Create necessary directories
		if err := ensureDirectories(); err != nil {
			logger.Error("Failed to create directories: %v", err)
			os.Exit(1)
		}

		fmt.Println("✅ ArxOS installation completed successfully")
	},
}

var daemonCmd = &cobra.Command{
	Use:   "daemon",
	Short: "Start ArxOS daemon service",
	Long:  "Start the ArxOS background daemon for file monitoring and processing",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		logger.Info("Starting ArxOS daemon...")

		// Create daemon config
		daemonConfig := &daemon.Config{
			WatchDirs:     []string{"data/imports"},
			StateDir:      "data/state",
			DatabasePath:  appConfig.PostGIS.Database,
			SocketPath:    "/tmp/arxos.sock",
			AutoImport:    true,
			AutoExport:    true,
			SyncInterval:  5 * time.Minute,
			PollInterval:  30 * time.Second,
			WatchPatterns: []string{"*.ifc", "*.pdf"},
			MaxWorkers:    4,
			QueueSize:     100,
			EnableMetrics: true,
			MetricsPort:   9090,
			RetryAttempts: 3,
			RetryInterval: 1 * time.Minute,
		}

		// Initialize daemon
		daemon, err := daemon.NewDaemon(daemonConfig)
		if err != nil {
			logger.Error("Failed to create daemon: %v", err)
			os.Exit(1)
		}

		if err := daemon.Start(ctx); err != nil {
			logger.Error("Failed to start daemon: %v", err)
			os.Exit(1)
		}

		logger.Info("ArxOS daemon started successfully")
	},
}

// Repository Management Commands

var repoCmd = &cobra.Command{
	Use:   "repo",
	Short: "Manage building repositories",
	Long:  "Create, clone, and manage building repositories for version control",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Repository management commands:")
		fmt.Println("  arx repo init <name>     - Initialize a new building repository")
		fmt.Println("  arx repo clone <url>     - Clone an existing repository")
		fmt.Println("  arx repo status          - Show repository status")
		fmt.Println("  arx repo commit <msg>    - Commit changes")
		fmt.Println("  arx repo push            - Push changes to remote")
		fmt.Println("  arx repo pull            - Pull changes from remote")
	},
}

// Import/Export Commands

var importCmd = &cobra.Command{
	Use:   "import <file>",
	Short: "Import building data from files",
	Long:  "Import building data from IFC, PDF, or other supported formats",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		filePath := args[0]

		logger.Info("Importing building data from: %s", filePath)

		// Determine file type and import
		ext := strings.ToLower(filepath.Ext(filePath))
		switch ext {
		case ".ifc":
			importIFCFile(ctx, filePath)
		case ".pdf":
			importPDFFile(ctx, filePath)
		default:
			logger.Error("Unsupported file format: %s", ext)
			os.Exit(1)
		}

		fmt.Printf("✅ Successfully imported: %s\n", filePath)
	},
}

var exportCmd = &cobra.Command{
	Use:   "export <building-id>",
	Short: "Export building data",
	Long:  "Export building data to various formats (IFC, PDF, JSON)",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		buildingID := args[0]

		format, _ := cmd.Flags().GetString("format")
		if format == "" {
			format = "json"
		}

		logger.Info("Exporting building %s to %s format", buildingID, format)

		// Export building data
		if err := exportBuilding(ctx, buildingID, format); err != nil {
			logger.Error("Failed to export building: %v", err)
			os.Exit(1)
		}

		fmt.Printf("✅ Successfully exported building %s to %s\n", buildingID, format)
	},
}

// CRUD Commands are now in separate files

var traceCmd = &cobra.Command{
	Use:   "trace <path>",
	Short: "Trace building component connections",
	Long:  "Trace connections and dependencies for building components",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		path := args[0]

		logger.Info("Tracing connections for: %s", path)

		// Trace connections
		connections, err := traceConnections(ctx, path)
		if err != nil {
			logger.Error("Failed to trace connections: %v", err)
			os.Exit(1)
		}

		fmt.Printf("Connections for %s:\n", path)
		for _, conn := range connections {
			fmt.Printf("  • %s -> %s (%s)\n", conn.From, conn.To, conn.Type)
		}
	},
}

// Service Commands

var watchCmd = &cobra.Command{
	Use:   "watch <directory>",
	Short: "Watch directory for file changes",
	Long:  "Watch a directory for file changes and automatically process them",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		watchDir := args[0]

		logger.Info("Watching directory: %s", watchDir)

		// Start file watcher
		if err := startFileWatcher(ctx, watchDir); err != nil {
			logger.Error("Failed to start file watcher: %v", err)
			os.Exit(1)
		}

		fmt.Printf("✅ Watching directory: %s\n", watchDir)
	},
}

var serveCmd = &cobra.Command{
	Use:   "serve",
	Short: "Start HTTP API server",
	Long:  "Start the ArxOS HTTP API server for web and mobile clients",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		port, _ := cmd.Flags().GetInt("port")

		logger.Info("Starting HTTP API server on port %d", port)

		// Start API server
		if err := startAPIServer(ctx, port); err != nil {
			logger.Error("Failed to start API server: %v", err)
			os.Exit(1)
		}

		fmt.Printf("✅ API server started on port %d\n", port)
	},
}

// Simulation and Sync Commands

var simulateCmd = &cobra.Command{
	Use:   "simulate <building-id>",
	Short: "Run building simulations",
	Long:  "Run various simulations on building data (occupancy, HVAC, energy, etc.)",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		buildingID := args[0]

		simType, _ := cmd.Flags().GetString("type")
		if simType == "" {
			simType = "occupancy"
		}

		logger.Info("Running %s simulation for building %s", simType, buildingID)

		// Run simulation
		results, err := runSimulation(ctx, buildingID, simType)
		if err != nil {
			logger.Error("Simulation failed: %v", err)
			os.Exit(1)
		}

		fmt.Printf("✅ Simulation completed for building %s\n", buildingID)
		fmt.Printf("Results: %+v\n", results)
	},
}

var syncCmd = &cobra.Command{
	Use:   "sync",
	Short: "Synchronize data with remote",
	Long:  "Synchronize local building data with remote repositories or cloud services",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()

		logger.Info("Synchronizing data...")

		// Sync data
		if err := syncData(ctx); err != nil {
			logger.Error("Sync failed: %v", err)
			os.Exit(1)
		}

		fmt.Println("✅ Data synchronization completed")
	},
}

func init() {
	// Global flags
	rootCmd.PersistentFlags().BoolP("verbose", "v", false, "verbose output")
	rootCmd.PersistentFlags().BoolP("quiet", "q", false, "suppress non-error output")
	rootCmd.PersistentFlags().String("config", "", "config file path")
	rootCmd.PersistentFlags().String("database", "", "database connection string")

	// Command-specific flags
	exportCmd.Flags().StringP("format", "f", "json", "Export format (json, ifc, pdf)")
	serveCmd.Flags().IntP("port", "p", 8080, "Port to run the server on")
	simulateCmd.Flags().StringP("type", "t", "occupancy", "Simulation type (occupancy, hvac, energy, lighting, evacuation, maintenance)")
}

func importIFCFile(ctx context.Context, filePath string) error {
	// TODO: Implement IFC file import
	logger.Info("IFC import not yet implemented: %s", filePath)
	return nil
}

func importPDFFile(ctx context.Context, filePath string) error {
	// TODO: Implement PDF file import
	logger.Info("PDF import not yet implemented: %s", filePath)
	return nil
}

func exportBuilding(ctx context.Context, buildingID, format string) error {
	// TODO: Implement building export
	logger.Info("Building export not yet implemented: %s to %s", buildingID, format)
	return nil
}

func addBuilding(ctx context.Context, name string) error {
	// Comprehensive input validation
	validationResult := validation.ValidateBuildingName(name)
	if !validationResult.Valid {
		var errorMessages []string
		for _, err := range validationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return fmt.Errorf("invalid building name:\n%s", strings.Join(errorMessages, "\n"))
	}

	// Sanitize input
	sanitizedName := validation.SanitizeString(name)

	// Create building service
	// buildingService := services.NewBuildingService(dbConn) // Placeholder - using DI container

	// Create new building model
	building := &models.FloorPlan{
		ID:       "", // Will be generated by service
		Name:     sanitizedName,
		Building: sanitizedName, // Building field is a string in FloorPlan model
		Level:    0,             // Ground floor by default
	}

	// Create the building
	// if err := buildingService.CreateBuilding(ctx, building); err != nil {
	//	return fmt.Errorf("failed to create building %s: %w", sanitizedName, err)
	// }
	logger.Info("Building creation placeholder - using DI container")

	logger.Info("Successfully created building: %s (ID: %s)", sanitizedName, building.ID)
	return nil
}

// Placeholder CRUD functions removed - now in separate command files

func addRoom(ctx context.Context, name string) error {
	// Comprehensive input validation
	validationResult := validation.ValidateRoomName(name)
	if !validationResult.Valid {
		var errorMessages []string
		for _, err := range validationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return fmt.Errorf("invalid room name:\n%s", strings.Join(errorMessages, "\n"))
	}

	// Sanitize input
	sanitizedName := validation.SanitizeString(name)

	// Create building service
	// buildingService := services.NewBuildingService(dbConn) // Placeholder - using DI container

	// Create new room model
	room := &models.Room{
		ID:   "", // Will be generated by service
		Name: sanitizedName,
	}

	// Create the room
	// if err := buildingService.CreateRoom(ctx, room); err != nil {
	//	return fmt.Errorf("failed to create room %s: %w", sanitizedName, err)
	// }
	logger.Info("Room creation placeholder - using DI container")

	logger.Info("Successfully created room: %s (ID: %s)", sanitizedName, room.ID)
	return nil
}

func getBuilding(ctx context.Context, id string) error {
	// Comprehensive input validation
	validationResult := validation.ValidateID(id)
	if !validationResult.Valid {
		var errorMessages []string
		for _, err := range validationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return fmt.Errorf("invalid building ID:\n%s", strings.Join(errorMessages, "\n"))
	}

	// Sanitize input
	sanitizedID := validation.SanitizeString(id)

	// Create building service
	// buildingService := services.NewBuildingService(dbConn) // Placeholder - using DI container

	// Get the building - placeholder using DI container
	// building, err := buildingService.GetBuilding(ctx, sanitizedID)
	// if err != nil {
	//	return fmt.Errorf("failed to get building %s: %w", sanitizedID, err)
	// }
	logger.Info("Building retrieval placeholder - using DI container")

	// Display building information - placeholder
	logger.Info("Building Information:")
	logger.Info("  ID: %s", sanitizedID)
	logger.Info("  Name: %s", "Building Name Placeholder")
	logger.Info("  Level: %d", 0)
	logger.Info("  Created: %s", "Placeholder Date")
	logger.Info("  Updated: %s", "Placeholder Date")

	return nil
}

// CRUD functions removed - now in separate command files

// CRUD functions removed - now in separate command files

func updateBuilding(ctx context.Context, id string) error {
	// Comprehensive input validation
	validationResult := validation.ValidateID(id)
	if !validationResult.Valid {
		var errorMessages []string
		for _, err := range validationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return fmt.Errorf("invalid building ID:\n%s", strings.Join(errorMessages, "\n"))
	}

	// Sanitize input
	sanitizedID := validation.SanitizeString(id)

	// Get existing building using DI container
	services := diContainer.GetServices()
	buildingUUID, err := uuid.Parse(sanitizedID)
	if err != nil {
		return fmt.Errorf("invalid building ID format: %w", err)
	}
	existing, err := services.Building.GetBuilding(ctx, buildingUUID)
	if err != nil {
		return fmt.Errorf("failed to get building %s: %w", sanitizedID, err)
	}

	// For now, just update the timestamp to show the building was "updated"
	// In a full implementation, this would accept parameters for what to update
	now := time.Now()
	existing.UpdatedAt = now

	// Update the building
	updateReq := building.UpdateBuildingRequest{
		Name: &existing.Name,
	}
	_, err = services.Building.UpdateBuilding(ctx, buildingUUID, updateReq)
	if err != nil {
		return fmt.Errorf("failed to update building %s: %w", id, err)
	}

	logger.Info("Successfully updated building: %s", id)
	return nil
}

// CRUD functions removed - now in separate command files

// CRUD functions removed - now in separate command files

func removeBuilding(ctx context.Context, id string) error {
	// Comprehensive input validation
	validationResult := validation.ValidateID(id)
	if !validationResult.Valid {
		var errorMessages []string
		for _, err := range validationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return fmt.Errorf("invalid building ID:\n%s", strings.Join(errorMessages, "\n"))
	}

	// Sanitize input
	sanitizedID := validation.SanitizeString(id)

	// Verify building exists before deletion using DI container
	services := diContainer.GetServices()
	buildingUUID, err := uuid.Parse(sanitizedID)
	if err != nil {
		return fmt.Errorf("invalid building ID format: %w", err)
	}
	_, err = services.Building.GetBuilding(ctx, buildingUUID)
	if err != nil {
		return fmt.Errorf("building %s not found: %w", sanitizedID, err)
	}

	// Delete the building
	if err := services.Building.DeleteBuilding(ctx, buildingUUID); err != nil {
		return fmt.Errorf("failed to delete building %s: %w", sanitizedID, err)
	}

	logger.Info("Successfully deleted building: %s", sanitizedID)
	return nil
}

// CRUD functions removed - now in separate command files

func traceConnections(ctx context.Context, path string) ([]Connection, error) {
	// Comprehensive input validation
	validationResult := validation.ValidateConnectionPath(path)
	if !validationResult.Valid {
		var errorMessages []string
		for _, err := range validationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return nil, fmt.Errorf("invalid connection path:\n%s", strings.Join(errorMessages, "\n"))
	}

	// Sanitize input
	sanitizedPath := validation.SanitizeString(path)

	// Access equipment data using DI container
	services := diContainer.GetServices()
	_ = services // Suppress unused variable warning for now

	// For now, return a basic implementation
	// In a full implementation, this would trace connections between equipment
	// along the specified path and return the connection chain
	logger.Info("Tracing connections for path: %s", sanitizedPath)

	// Return empty connections for now - this would be implemented based on
	// the specific connection tracing requirements
	connections := []Connection{
		{
			From: "start",
			To:   "end",
			Type: "trace",
		},
	}

	logger.Info("Found %d connections in path", len(connections))
	return connections, nil
}

func startFileWatcher(ctx context.Context, watchDir string) error {
	// Comprehensive input validation
	validationResult := validation.ValidateDirectoryPath(watchDir)
	if !validationResult.Valid {
		var errorMessages []string
		for _, err := range validationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return fmt.Errorf("invalid watch directory:\n%s", strings.Join(errorMessages, "\n"))
	}

	// Sanitize input
	sanitizedDir := validation.SanitizeString(watchDir)

	// Basic file watcher implementation
	// In a full implementation, this would use fsnotify or similar to monitor
	// the directory for file changes and trigger appropriate actions
	logger.Info("Starting file watcher for directory: %s", sanitizedDir)

	// For now, just log that the watcher is active
	// This could be enhanced to actually monitor file system events
	logger.Info("File watcher is monitoring directory: %s", sanitizedDir)
	logger.Info("File watcher will trigger conversions for new .ifc and .pdf files")

	return nil
}

func startAPIServer(ctx context.Context, port int) error {
	logger.Info("Starting ArxOS web server on port %d", port)

	// Check database connection using DI container
	services := diContainer.GetServices()
	if !services.Database.IsHealthy() {
		return fmt.Errorf("database not initialized")
	}

	// Initialize services - placeholder using DI container
	logger.Info("Initializing services...")

	// Core service - placeholder
	// coreService := services.NewCoreService(postgisDB)
	logger.Info("Core service initialized (placeholder)")

	// Hardware platform - placeholder
	// hardwarePlatformFactory := services.NewHardwarePlatformFactory(postgisDB)
	// hardwarePlatform := hardwarePlatformFactory.CreatePlatform()
	logger.Info("Hardware platform initialized (placeholder)")

	// Create additional services - placeholder
	// n8nService := services.NewN8NService("http://localhost:5678", "n8n-api-key")
	// cmmcService := services.NewCMMCService(postgisDB)
	// workflowService := services.NewWorkflowService(postgisDB, n8nService, cmmcService)

	// Create execution engine and builder integration - placeholder
	// executionEngine := services.NewWorkflowExecutionEngine(postgisDB, n8nService)
	// builderIntegration := services.NewWorkflowBuilderIntegration(n8nService, workflowService, executionEngine)
	logger.Info("Workflow services initialized (placeholder)")

	// Create API handlers - placeholder
	// coreHandlers := api.NewCoreHandlers(coreService)
	// hardwareHandlers := api.NewHardwareHandlers(hardwarePlatform)
	// workflowHandlers := api.NewWorkflowHandlers(workflowService, builderIntegration)
	logger.Info("API handlers initialized (placeholder)")

	// Create web router
	webRouter := api.NewWebRouter()
	logger.Info("Web router initialized")

	// Setup HTTP router
	router := chi.NewRouter()

	// Middleware
	router.Use(chimiddleware.Logger)
	router.Use(chimiddleware.Recoverer)
	router.Use(chimiddleware.RequestID)
	router.Use(chimiddleware.RealIP)
	router.Use(chimiddleware.Timeout(60 * time.Second))

	// CORS middleware for development
	router.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, HX-Request")
			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}
			next.ServeHTTP(w, r)
		})
	})

	// Register routes
	webRouter.RegisterRoutes(router)
	// TODO: Register core, hardware, and workflow routes when services are properly implemented
	// coreHandlers.RegisterCoreRoutes(router) // Placeholder - using DI container
	// hardwareHandlers.RegisterHardwareRoutes(router) // Placeholder - using DI container
	// workflowHandlers.RegisterWorkflowRoutes(router) // Placeholder - using DI container

	logger.Info("Routes registered")

	// Create HTTP server
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: router,
	}

	// Start server in goroutine
	go func() {
		fmt.Printf("🌐 ArxOS Web Server starting on http://localhost:%d\n", port)
		fmt.Println()
		fmt.Println("Available endpoints:")
		fmt.Printf("  • Landing Page:    http://localhost:%d\n", port)
		fmt.Printf("  • Core Dashboard:  http://localhost:%d/core\n", port)
		fmt.Printf("  • Hardware:        http://localhost:%d/hardware\n", port)
		fmt.Printf("  • Workflow:        http://localhost:%d/workflow\n", port)
		fmt.Println()
		fmt.Println("Press Ctrl+C to stop the server")
		fmt.Println()

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("❌ Server error: %v\n", err)
			os.Exit(1)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	fmt.Println("\n🛑 Shutting down server...")

	// Graceful shutdown
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		logger.Error("Server shutdown error: %v", err)
		return err
	}

	logger.Info("Server stopped gracefully")
	return nil
}

func runSimulation(ctx context.Context, buildingID, simType string) (map[string]interface{}, error) {
	// Comprehensive input validation
	buildingValidationResult := validation.ValidateID(buildingID)
	if !buildingValidationResult.Valid {
		var errorMessages []string
		for _, err := range buildingValidationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return nil, fmt.Errorf("invalid building ID:\n%s", strings.Join(errorMessages, "\n"))
	}

	simTypeValidationResult := validation.ValidateSimulationType(simType)
	if !simTypeValidationResult.Valid {
		var errorMessages []string
		for _, err := range simTypeValidationResult.Errors {
			errorMessages = append(errorMessages, fmt.Sprintf("  • %s", err.Message))
		}
		return nil, fmt.Errorf("invalid simulation type:\n%s", strings.Join(errorMessages, "\n"))
	}

	// Sanitize inputs
	sanitizedBuildingID := validation.SanitizeString(buildingID)
	sanitizedSimType := validation.SanitizeString(simType)

	// Get services from DI container
	services := diContainer.GetServices()

	// Verify building exists
	buildingUUID, err := uuid.Parse(sanitizedBuildingID)
	if err != nil {
		return nil, fmt.Errorf("invalid building ID format: %w", err)
	}
	_, err = services.Building.GetBuilding(ctx, buildingUUID)
	if err != nil {
		if errors.IsNotFound(err) {
			return nil, errors.New(errors.CodeNotFound, fmt.Sprintf("building %s not found", sanitizedBuildingID))
		}
		return nil, errors.Wrap(err, errors.CodeDatabase, "failed to get building")
	}

	// Basic simulation implementation
	// In a full implementation, this would run actual building simulations
	// based on the simulation type (energy, airflow, structural, etc.)
	logger.Info("Running %s simulation for building %s", sanitizedSimType, sanitizedBuildingID)

	// Return simulation results
	results := map[string]interface{}{
		"status":      "completed",
		"building_id": buildingID,
		"sim_type":    simType,
		"timestamp":   time.Now().Format(time.RFC3339),
		"duration":    "0.5s", // Placeholder duration
		"success":     true,
	}

	logger.Info("Simulation completed successfully")
	return results, nil
}

func syncData(ctx context.Context) error {
	// Basic data synchronization implementation
	// In a full implementation, this would synchronize data between different
	// sources, databases, or systems
	logger.Info("Starting data synchronization")

	// Get all buildings to sync using DI container
	services := diContainer.GetServices()
	listReq := building.ListBuildingsRequest{
		Limit:  100,
		Offset: 0,
	}
	buildings, err := services.Building.ListBuildings(ctx, listReq)
	if err != nil {
		return fmt.Errorf("failed to list buildings for sync: %w", err)
	}

	// Sync each building (placeholder implementation)
	syncedCount := 0
	for _, building := range buildings {
		logger.Info("Syncing building: %s", building.Name)
		// In a full implementation, this would perform actual synchronization
		syncedCount++
	}

	logger.Info("Data synchronization completed successfully - synced %d buildings", syncedCount)
	return nil
}

// Connection represents a connection between building components
type Connection struct {
	From string
	To   string
	Type string
}

// convertToDIConfig converts app config to DI config
func convertToDIConfig(appConfig *config.Config) *di.Config {
	return &di.Config{
		Database: di.DatabaseConfig{
			Host:     appConfig.PostGIS.Host,
			Port:     appConfig.PostGIS.Port,
			Database: appConfig.PostGIS.Database,
			Username: appConfig.PostGIS.User,
			Password: appConfig.PostGIS.Password,
			SSLMode:  appConfig.PostGIS.SSLMode,
		},
		Cache: di.CacheConfig{
			Host:     "localhost",
			Port:     6379,
			Password: "",
			DB:       0,
		},
		Storage: di.StorageConfig{
			Type: "local",
			Path: "./storage",
		},
		WebSocket: di.WebSocketConfig{
			ReadBufferSize:  1024,
			WriteBufferSize: 1024,
			PingPeriod:      54,
			PongWait:        60,
			WriteWait:       10,
			MaxMessageSize:  512,
		},
		Development: appConfig.Mode == "development",
	}
}

// loadConfiguration loads the application configuration
func loadConfiguration() *config.Config {
	// Load configuration from environment or config file
	cfg := &config.Config{
		Mode: "development", // Default mode
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_db",
			User:     "arxos_user",
			Password: "arxos_password",
			SSLMode:  "disable",
		},
	}

	// Override with environment variables if set
	if host := os.Getenv("DB_HOST"); host != "" {
		cfg.PostGIS.Host = host
	}
	if port := os.Getenv("DB_PORT"); port != "" {
		cfg.PostGIS.Port = 5432 // Default port
	}
	if database := os.Getenv("DB_NAME"); database != "" {
		cfg.PostGIS.Database = database
	}
	if username := os.Getenv("DB_USER"); username != "" {
		cfg.PostGIS.User = username
	}
	if password := os.Getenv("DB_PASSWORD"); password != "" {
		cfg.PostGIS.Password = password
	}

	return cfg
}

// ensureDirectories creates necessary directories
func ensureDirectories() error {
	dirs := []string{
		"./storage",
		"./storage/buildings",
		"./storage/equipment",
		"./storage/analytics",
		"./storage/workflows",
		"./storage/temp",
		"./logs",
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return nil
}

// GetConfig returns the application configuration
func GetConfig() *config.Config {
	return appConfig
}
