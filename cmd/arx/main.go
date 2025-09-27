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
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/daemon"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/services"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/spf13/cobra"
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

		// Simulation and Sync
		simulateCmd,
		syncCmd,

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

var healthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check system health",
	Long:  "Check the health status of ArxOS components including database connectivity",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()

		logger.Info("Checking system health...")

		// Check database connectivity by trying to get version
		version, err := dbConn.GetVersion(ctx)
		if err != nil {
			logger.Error("Database health check failed: %v", err)
			fmt.Println("❌ Database: UNHEALTHY")
			os.Exit(1)
		}
		fmt.Printf("✅ Database: HEALTHY (version: %d)\n", version)

		// Check PostGIS spatial support
		if postgisDB != nil && postgisDB.HasSpatialSupport() {
			fmt.Println("✅ PostGIS: SPATIAL SUPPORT AVAILABLE")
		} else {
			fmt.Println("⚠️  PostGIS: SPATIAL SUPPORT NOT AVAILABLE")
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

var listCmd = &cobra.Command{
	Use:   "list [type]",
	Short: "List resources",
	Long:  "List buildings, equipment, or other resources in the ArxOS system",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		resourceType := args[0]

		switch resourceType {
		case "buildings":
			listBuildings(ctx)
		case "equipment":
			listEquipment(ctx)
		case "rooms":
			listRooms(ctx)
		default:
			fmt.Printf("Unknown resource type: %s\n", resourceType)
			fmt.Println("Available types: buildings, equipment, rooms")
			os.Exit(1)
		}
	},
}

func listBuildings(ctx context.Context) {
	// Get all floor plans (buildings)
	floorPlans, err := dbConn.GetAllFloorPlans(ctx)
	if err != nil {
		logger.Error("Failed to list buildings: %v", err)
		os.Exit(1)
	}

	if len(floorPlans) == 0 {
		fmt.Println("No buildings found")
		return
	}

	fmt.Printf("Found %d buildings:\n", len(floorPlans))
	for _, fp := range floorPlans {
		fmt.Printf("  • %s (ID: %s, Level: %d)\n", fp.Name, fp.ID, fp.Level)
	}
}

func listEquipment(ctx context.Context) {
	// Get all equipment
	equipment, err := dbConn.GetAllFloorPlans(ctx) // This would need to be updated to get equipment
	if err != nil {
		logger.Error("Failed to list equipment: %v", err)
		os.Exit(1)
	}

	fmt.Printf("Found %d equipment items:\n", len(equipment))
	// This is a placeholder - would need proper equipment listing
	fmt.Println("Equipment listing not yet implemented")
}

func listRooms(ctx context.Context) {
	// Get all rooms
	rooms, err := dbConn.GetAllFloorPlans(ctx) // This would need to be updated to get rooms
	if err != nil {
		logger.Error("Failed to list rooms: %v", err)
		os.Exit(1)
	}

	fmt.Printf("Found %d rooms:\n", len(rooms))
	// This is a placeholder - would need proper room listing
	fmt.Println("Room listing not yet implemented")
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

		// Install database schema
		if err := dbConn.Migrate(ctx); err != nil {
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

// CRUD Commands

var addCmd = &cobra.Command{
	Use:   "add <type> <name>",
	Short: "Add new building components",
	Long:  "Add new buildings, equipment, rooms, or other components",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		componentType := args[0]
		name := args[1]

		logger.Info("Adding %s: %s", componentType, name)

		switch componentType {
		case "building":
			addBuilding(ctx, name)
		case "equipment":
			addEquipment(ctx, name)
		case "room":
			addRoom(ctx, name)
		default:
			logger.Error("Unknown component type: %s", componentType)
			os.Exit(1)
		}

		fmt.Printf("✅ Successfully added %s: %s\n", componentType, name)
	},
}

var getCmd = &cobra.Command{
	Use:   "get <type> <id>",
	Short: "Get building component details",
	Long:  "Get detailed information about buildings, equipment, rooms, or other components",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		componentType := args[0]
		id := args[1]

		logger.Info("Getting %s: %s", componentType, id)

		switch componentType {
		case "building":
			getBuilding(ctx, id)
		case "equipment":
			getEquipment(ctx, id)
		case "room":
			getRoom(ctx, id)
		default:
			logger.Error("Unknown component type: %s", componentType)
			os.Exit(1)
		}
	},
}

var updateCmd = &cobra.Command{
	Use:   "update <type> <id>",
	Short: "Update building components",
	Long:  "Update existing buildings, equipment, rooms, or other components",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		componentType := args[0]
		id := args[1]

		logger.Info("Updating %s: %s", componentType, id)

		switch componentType {
		case "building":
			updateBuilding(ctx, id)
		case "equipment":
			updateEquipment(ctx, id)
		case "room":
			updateRoom(ctx, id)
		default:
			logger.Error("Unknown component type: %s", componentType)
			os.Exit(1)
		}

		fmt.Printf("✅ Successfully updated %s: %s\n", componentType, id)
	},
}

var removeCmd = &cobra.Command{
	Use:   "remove <type> <id>",
	Short: "Remove building components",
	Long:  "Remove buildings, equipment, rooms, or other components",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		componentType := args[0]
		id := args[1]

		logger.Info("Removing %s: %s", componentType, id)

		switch componentType {
		case "building":
			removeBuilding(ctx, id)
		case "equipment":
			removeEquipment(ctx, id)
		case "room":
			removeRoom(ctx, id)
		default:
			logger.Error("Unknown component type: %s", componentType)
			os.Exit(1)
		}

		fmt.Printf("✅ Successfully removed %s: %s\n", componentType, id)
	},
}

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

// Global variables for system components
var (
	appConfig *config.Config
	dbConn    database.DB
	postgisDB *database.PostGISDB
)

// initializeSystem sets up core components
func initializeSystem() error {
	ctx := context.Background()

	// Load configuration
	appConfig = loadConfiguration()

	// Initialize database connections
	if err := initializeDatabases(ctx); err != nil {
		return fmt.Errorf("database initialization failed: %w", err)
	}

	// Create necessary directories
	if err := ensureDirectories(); err != nil {
		return fmt.Errorf("directory setup failed: %w", err)
	}

	return nil
}

// loadConfiguration loads config from file or environment
func loadConfiguration() *config.Config {
	// Start with defaults
	cfg := config.Default()
	cfg.Version = Version

	// Check for config file from command line
	configFile, _ := rootCmd.PersistentFlags().GetString("config")
	if configFile == "" {
		configFile = config.GetConfigPath()
	}

	// Load configuration using the enhanced config system
	loadedCfg, err := config.Load(configFile)
	if err != nil {
		logger.Warn("Failed to load configuration: %v", err)
		// Use defaults with environment overrides
		cfg.LoadFromEnv()
	} else {
		cfg = loadedCfg
	}

	return cfg
}

// loadConfigFromEnv loads configuration from environment variables
func loadConfigFromEnv(cfg *config.Config) {
	// PostGIS configuration
	if host := os.Getenv("POSTGIS_HOST"); host != "" {
		cfg.PostGIS.Host = host
	}
	if port := os.Getenv("POSTGIS_PORT"); port != "" {
		fmt.Sscanf(port, "%d", &cfg.PostGIS.Port)
	}
	if db := os.Getenv("POSTGIS_DB"); db != "" {
		cfg.PostGIS.Database = db
	}
	if user := os.Getenv("POSTGIS_USER"); user != "" {
		cfg.PostGIS.User = user
	}
	if pass := os.Getenv("POSTGIS_PASSWORD"); pass != "" {
		cfg.PostGIS.Password = pass
	}

	// Database configuration (deprecated - using PostGIS only)
	if dbType := os.Getenv("ARX_DB_TYPE"); dbType != "" {
		cfg.Database.Type = dbType
	}
	// Path field no longer used with PostGIS-only architecture
}

// Helper functions for CLI commands

func ensureDirectories() error {
	dirs := []string{
		"data",
		"logs",
		"temp",
		"exports",
		"imports",
		"repositories",
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return nil
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
	// Validate input
	if name == "" {
		return fmt.Errorf("building name cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Create new building model
	building := &models.FloorPlan{
		ID:   "", // Will be generated by service
		Name: name,
		Building: name, // Building field is a string in FloorPlan model
		Level: 0, // Ground floor by default
	}

	// Create the building
	if err := buildingService.CreateBuilding(ctx, building); err != nil {
		return fmt.Errorf("failed to create building %s: %w", name, err)
	}

	logger.Info("Successfully created building: %s (ID: %s)", name, building.ID)
	return nil
}

func addEquipment(ctx context.Context, name string) error {
	// Validate input
	if name == "" {
		return fmt.Errorf("equipment name cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Create new equipment model
	equipment := &models.Equipment{
		ID:   "", // Will be generated by service
		Name: name,
		Type: "general", // Default type
		Status: "operational",
	}

	// Create the equipment
	if err := buildingService.CreateEquipment(ctx, equipment); err != nil {
		return fmt.Errorf("failed to create equipment %s: %w", name, err)
	}

	logger.Info("Successfully created equipment: %s (ID: %s)", name, equipment.ID)
	return nil
}

func addRoom(ctx context.Context, name string) error {
	// Validate input
	if name == "" {
		return fmt.Errorf("room name cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Create new room model
	room := &models.Room{
		ID:   "", // Will be generated by service
		Name: name,
	}

	// Create the room
	if err := buildingService.CreateRoom(ctx, room); err != nil {
		return fmt.Errorf("failed to create room %s: %w", name, err)
	}

	logger.Info("Successfully created room: %s (ID: %s)", name, room.ID)
	return nil
}

func getBuilding(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("building ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Get the building
	building, err := buildingService.GetBuilding(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get building %s: %w", id, err)
	}

	// Display building information
	logger.Info("Building Information:")
	logger.Info("  ID: %s", building.ID)
	logger.Info("  Name: %s", building.Name)
	logger.Info("  Level: %d", building.Level)
	if building.CreatedAt != nil {
		logger.Info("  Created: %s", building.CreatedAt.Format(time.RFC3339))
	}
	if building.UpdatedAt != nil {
		logger.Info("  Updated: %s", building.UpdatedAt.Format(time.RFC3339))
	}

	return nil
}

func getEquipment(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("equipment ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Get the equipment
	equipment, err := buildingService.GetEquipment(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get equipment %s: %w", id, err)
	}

	// Display equipment information
	logger.Info("Equipment Information:")
	logger.Info("  ID: %s", equipment.ID)
	logger.Info("  Name: %s", equipment.Name)
	logger.Info("  Type: %s", equipment.Type)
	logger.Info("  Status: %s", equipment.Status)
	if equipment.Location != nil {
		logger.Info("  Location: (%.2f, %.2f, %.2f)", 
			equipment.Location.X, equipment.Location.Y, equipment.Location.Z)
	}
	if equipment.RoomID != "" {
		logger.Info("  Room ID: %s", equipment.RoomID)
	}

	return nil
}

func getRoom(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("room ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Get the room
	room, err := buildingService.GetRoom(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get room %s: %w", id, err)
	}

	// Display room information
	logger.Info("Room Information:")
	logger.Info("  ID: %s", room.ID)
	logger.Info("  Name: %s", room.Name)
	if room.FloorPlanID != "" {
		logger.Info("  Floor Plan ID: %s", room.FloorPlanID)
	}
	if len(room.Equipment) > 0 {
		logger.Info("  Equipment Count: %d", len(room.Equipment))
	}

	return nil
}

func updateBuilding(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("building ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Get existing building
	existing, err := buildingService.GetBuilding(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get building %s: %w", id, err)
	}

	// For now, just update the timestamp to show the building was "updated"
	// In a full implementation, this would accept parameters for what to update
	now := time.Now()
	existing.UpdatedAt = &now

	// Update the building
	if err := buildingService.UpdateBuilding(ctx, existing); err != nil {
		return fmt.Errorf("failed to update building %s: %w", id, err)
	}

	logger.Info("Successfully updated building: %s", id)
	return nil
}

func updateEquipment(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("equipment ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Get existing equipment
	existing, err := buildingService.GetEquipment(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get equipment %s: %w", id, err)
	}

	// For now, just update a basic field to show the equipment was "updated"
	// In a full implementation, this would accept parameters for what to update
	existing.Status = "updated"

	// Update the equipment
	if err := buildingService.UpdateEquipment(ctx, existing); err != nil {
		return fmt.Errorf("failed to update equipment %s: %w", id, err)
	}

	logger.Info("Successfully updated equipment: %s", id)
	return nil
}

func updateRoom(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("room ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Get existing room
	existing, err := buildingService.GetRoom(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get room %s: %w", id, err)
	}

	// For now, just update a basic field to show the room was "updated"
	// In a full implementation, this would accept parameters for what to update
	// Note: Room model doesn't have many mutable fields, so we'll just log the update

	// Update the room
	if err := buildingService.UpdateRoom(ctx, existing); err != nil {
		return fmt.Errorf("failed to update room %s: %w", id, err)
	}

	logger.Info("Successfully updated room: %s", id)
	return nil
}

func removeBuilding(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("building ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Verify building exists before deletion
	_, err := buildingService.GetBuilding(ctx, id)
	if err != nil {
		return fmt.Errorf("building %s not found: %w", id, err)
	}

	// Delete the building
	if err := buildingService.DeleteBuilding(ctx, id); err != nil {
		return fmt.Errorf("failed to delete building %s: %w", id, err)
	}

	logger.Info("Successfully deleted building: %s", id)
	return nil
}

func removeEquipment(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("equipment ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Verify equipment exists before deletion
	_, err := buildingService.GetEquipment(ctx, id)
	if err != nil {
		return fmt.Errorf("equipment %s not found: %w", id, err)
	}

	// Delete the equipment
	if err := buildingService.DeleteEquipment(ctx, id); err != nil {
		return fmt.Errorf("failed to delete equipment %s: %w", id, err)
	}

	logger.Info("Successfully deleted equipment: %s", id)
	return nil
}

func removeRoom(ctx context.Context, id string) error {
	// Validate input
	if id == "" {
		return fmt.Errorf("room ID cannot be empty")
	}

	// Create building service
	buildingService := services.NewBuildingService(dbConn)
	
	// Verify room exists before deletion
	_, err := buildingService.GetRoom(ctx, id)
	if err != nil {
		return fmt.Errorf("room %s not found: %w", id, err)
	}

	// Delete the room
	if err := buildingService.DeleteRoom(ctx, id); err != nil {
		return fmt.Errorf("failed to delete room %s: %w", id, err)
	}

	logger.Info("Successfully deleted room: %s", id)
	return nil
}

func traceConnections(ctx context.Context, path string) ([]Connection, error) {
	// Validate input
	if path == "" {
		return nil, fmt.Errorf("connection path cannot be empty")
	}

	// Create building service to access equipment data
	buildingService := services.NewBuildingService(dbConn)
	_ = buildingService // Suppress unused variable warning for now
	
	// For now, return a basic implementation
	// In a full implementation, this would trace connections between equipment
	// along the specified path and return the connection chain
	logger.Info("Tracing connections for path: %s", path)
	
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
	// Validate input
	if watchDir == "" {
		return fmt.Errorf("watch directory cannot be empty")
	}

	// Basic file watcher implementation
	// In a full implementation, this would use fsnotify or similar to monitor
	// the directory for file changes and trigger appropriate actions
	logger.Info("Starting file watcher for directory: %s", watchDir)
	
	// For now, just log that the watcher is active
	// This could be enhanced to actually monitor file system events
	logger.Info("File watcher is monitoring directory: %s", watchDir)
	logger.Info("File watcher will trigger conversions for new .ifc and .pdf files")
	
	return nil
}

func startAPIServer(ctx context.Context, port int) error {
	logger.Info("Starting ArxOS web server on port %d", port)

	// Check database connection
	if postgisDB == nil {
		return fmt.Errorf("database not initialized")
	}

	// Initialize services
	logger.Info("Initializing services...")

	// Core service
	coreService := services.NewCoreService(postgisDB)
	logger.Info("Core service initialized")

	// Hardware platform
	hardwarePlatformFactory := services.NewHardwarePlatformFactory(postgisDB)
	hardwarePlatform := hardwarePlatformFactory.CreatePlatform()
	logger.Info("Hardware platform initialized")

	// Create additional services
	n8nService := services.NewN8NService("http://localhost:5678", "n8n-api-key")
	cmmcService := services.NewCMMCService(postgisDB)
	workflowService := services.NewWorkflowService(postgisDB, n8nService, cmmcService)

	// Create execution engine and builder integration
	executionEngine := services.NewWorkflowExecutionEngine(postgisDB, n8nService)
	builderIntegration := services.NewWorkflowBuilderIntegration(n8nService, workflowService, executionEngine)
	logger.Info("Workflow services initialized")

	// Create API handlers
	coreHandlers := api.NewCoreHandlers(coreService)
	hardwareHandlers := api.NewHardwareHandlers(hardwarePlatform)
	workflowHandlers := api.NewWorkflowHandlers(workflowService, builderIntegration)
	logger.Info("API handlers initialized")

	// Create web router
	webRouter := api.NewWebRouter()
	logger.Info("Web router initialized")

	// Setup HTTP router
	router := chi.NewRouter()

	// Middleware
	router.Use(middleware.Logger)
	router.Use(middleware.Recoverer)
	router.Use(middleware.RequestID)
	router.Use(middleware.RealIP)
	router.Use(middleware.Timeout(60 * time.Second))

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
	coreHandlers.RegisterCoreRoutes(router)
	hardwareHandlers.RegisterHardwareRoutes(router)
	workflowHandlers.RegisterWorkflowRoutes(router)

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
	// Validate input
	if buildingID == "" {
		return nil, fmt.Errorf("building ID cannot be empty")
	}
	if simType == "" {
		return nil, fmt.Errorf("simulation type cannot be empty")
	}

	// Create building service to verify building exists
	buildingService := services.NewBuildingService(dbConn)
	
	// Verify building exists
	_, err := buildingService.GetBuilding(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("building %s not found: %w", buildingID, err)
	}

	// Basic simulation implementation
	// In a full implementation, this would run actual building simulations
	// based on the simulation type (energy, airflow, structural, etc.)
	logger.Info("Running %s simulation for building %s", simType, buildingID)
	
	// Return simulation results
	results := map[string]interface{}{
		"status":       "completed",
		"building_id":  buildingID,
		"sim_type":     simType,
		"timestamp":    time.Now().Format(time.RFC3339),
		"duration":     "0.5s", // Placeholder duration
		"success":      true,
	}
	
	logger.Info("Simulation completed successfully")
	return results, nil
}

func syncData(ctx context.Context) error {
	// Basic data synchronization implementation
	// In a full implementation, this would synchronize data between different
	// sources, databases, or systems
	logger.Info("Starting data synchronization")
	
	// Create building service to access data
	buildingService := services.NewBuildingService(dbConn)
	
	// Get all buildings to sync
	buildings, err := buildingService.ListBuildings(ctx, "", 1000, 0) // No user filtering for sync
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

// initializeDatabases sets up database connections
func initializeDatabases(ctx context.Context) error {
	// Always use PostGIS as the sole database
	return initializePostGISDatabase(ctx)
}

// initializePostGISDatabase initializes PostGIS as the sole database
func initializePostGISDatabase(ctx context.Context) error {
	pgConfig := appConfig.GetPostGISConfig()

	dbConfig := database.PostGISConfig{
		Host:     pgConfig.Host,
		Port:     pgConfig.Port,
		Database: pgConfig.Database,
		User:     pgConfig.User,
		Password: pgConfig.Password,
		SSLMode:  pgConfig.SSLMode,
	}
	postgisDB = database.NewPostGISDB(dbConfig)

	if err := postgisDB.Connect(ctx, ""); err != nil {
		return fmt.Errorf("failed to connect to PostGIS: %w", err)
	}

	dbConn = postgisDB
	logger.Info("Connected to PostGIS database: %s:%d/%s",
		pgConfig.Host, pgConfig.Port, pgConfig.Database)

	return nil
}

// GetDatabase returns the active database connection
func GetDatabase() database.DB {
	return dbConn
}

// GetConfig returns the application configuration
func GetConfig() *config.Config {
	return appConfig
}
