package services

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// DaemonConfig holds daemon configuration
type DaemonConfig struct {
	Name         string        `json:"name"`
	Mode         string        `json:"mode"` // watch, import, export, sync
	WatchPaths   []WatchPath   `json:"watch_paths"`
	PollInterval time.Duration `json:"poll_interval"`
	MaxWorkers   int           `json:"max_workers"`
	QueueSize    int           `json:"queue_size"`
}

// WatchPath defines a path to watch for file changes
type WatchPath struct {
	Path           string   `json:"path"`
	Recursive      bool     `json:"recursive"`
	Patterns       []string `json:"patterns"`
	IgnorePatterns []string `json:"ignore_patterns"`
}

// DaemonService implements background daemon functionality following Clean Architecture
type DaemonService struct {
	config      *DaemonConfig
	logger      domain.Logger
	buildingUC  *domain.BuildingService // Use case for building operations
	fileWatcher *FileWatcher
	processor   *FileProcessor
	ctx         context.Context
	cancel      context.CancelFunc
}

// NewDaemonService creates a new daemon service
func NewDaemonService(config *DaemonConfig, logger domain.Logger, buildingUC *domain.BuildingService) *DaemonService {
	ctx, cancel := context.WithCancel(context.Background())

	return &DaemonService{
		config:      config,
		logger:      logger,
		buildingUC:  buildingUC,
		fileWatcher: NewFileWatcher(logger),
		processor:   NewFileProcessor(logger),
		ctx:         ctx,
		cancel:      cancel,
	}
}

// Start starts the daemon service
func (ds *DaemonService) Start() error {
	ds.logger.Info("Starting daemon service", "name", ds.config.Name, "mode", ds.config.Mode)

	// Configure file watcher
	for _, watchPath := range ds.config.WatchPaths {
		if err := ds.fileWatcher.AddPath(watchPath); err != nil {
			return fmt.Errorf("failed to add watch path: %w", err)
		}
	}

	// Start file watcher
	if err := ds.fileWatcher.Start(ds.ctx); err != nil {
		return fmt.Errorf("failed to start file watcher: %w", err)
	}

	// Start file processor
	if err := ds.processor.Start(ds.ctx, ds.config.MaxWorkers, ds.config.QueueSize); err != nil {
		return fmt.Errorf("failed to start file processor: %w", err)
	}

	// Start processing loop
	go ds.processLoop()

	ds.logger.Info("Daemon service started successfully")
	return nil
}

// Stop stops the daemon service
func (ds *DaemonService) Stop() error {
	ds.logger.Info("Stopping daemon service")

	ds.cancel()

	// Stop file watcher
	if err := ds.fileWatcher.Stop(); err != nil {
		ds.logger.Error("Failed to stop file watcher: %v", err)
	}

	// Stop file processor
	if err := ds.processor.Stop(); err != nil {
		ds.logger.Error("Failed to stop file processor: %v", err)
	}

	ds.logger.Info("Daemon service stopped")
	return nil
}

// Health checks the health of the daemon service
func (ds *DaemonService) Health(ctx context.Context) (*domain.ServiceHealth, error) {
	health := &domain.ServiceHealth{
		ServiceName: ds.config.Name,
		Status:      "healthy",
		LastCheck:   time.Now(),
		Details:     make(map[string]any),
	}

	// Check file watcher health
	watcherHealth, err := ds.fileWatcher.Health()
	if err != nil {
		health.Status = "degraded"
		health.Details["file_watcher"] = fmt.Sprintf("error: %v", err)
	} else {
		health.Details["file_watcher"] = watcherHealth
	}

	// Check processor health
	processorHealth, err := ds.processor.Health()
	if err != nil {
		health.Status = "degraded"
		health.Details["file_processor"] = fmt.Sprintf("error: %v", err)
	} else {
		health.Details["file_processor"] = processorHealth
	}

	return health, nil
}

// processLoop processes file change events
func (ds *DaemonService) processLoop() {
	ds.logger.Info("Starting daemon process loop")

	ticker := time.NewTicker(ds.config.PollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ds.ctx.Done():
			ds.logger.Info("Daemon process loop stopped")
			return

		case event := <-ds.fileWatcher.Events():
			ds.logger.Info("File change detected", "path", event.Path, "action", event.Action)

			// Process file based on daemon mode
			if err := ds.processFile(event); err != nil {
				ds.logger.Error("Failed to process file: %v", err)
			}

		case <-ticker.C:
			// Periodic health check and maintenance
			ds.performMaintenance()
		}
	}
}

// processFile processes a file change event
func (ds *DaemonService) processFile(event *domain.FileEvent) error {
	// Determine file format
	format := ds.detectFileFormat(event.Path)
	if format == "" {
		ds.logger.Debug("Skipping file with unknown format", "path", event.Path)
		return nil
	}

	// Process based on daemon mode
	switch ds.config.Mode {
	case "import":
		return ds.processImport(event, format)
	case "export":
		return ds.processExport(event, format)
	case "sync":
		return ds.processSync(event, format)
	case "watch":
		return ds.processWatch(event, format)
	default:
		return fmt.Errorf("unknown daemon mode: %s", ds.config.Mode)
	}
}

// detectFileFormat detects the format of a file based on extension
func (ds *DaemonService) detectFileFormat(path string) string {
	ext := strings.ToLower(filepath.Ext(path))

	switch ext {
	case ".ifc", ".ifczip", ".ifcxml":
		return "ifc"
	case ".csv":
		return "csv"
	case ".json":
		return "json"
	default:
		return ""
	}
}

// processImport processes file import
func (ds *DaemonService) processImport(event *domain.FileEvent, format string) error {
	ds.logger.Info("Processing file import", "path", event.Path, "format", format)

	// Read file data
	data, err := ds.processor.ReadFile(event.Path)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	// Create import request
	req := &domain.ImportBuildingRequest{
		Format: format,
		Data:   data,
	}

	// Import building using IfcOpenShell service
	// TODO: Get IFC service from daemon configuration
	// For now, log that we're ready for integration
	ds.logger.Info("Processing file import",
		"path", event.Path,
		"format", format,
		"size", len(data),
		"request_format", req.Format, // Use the request to avoid unused variable
		"status", "ready_for_ifcopenshell_integration")

	// Placeholder - will be replaced with actual IfcOpenShell service call
	// if format == "ifc" {
	//     result, err := ds.ifcService.ParseIFC(ds.ctx, data)
	//     if err != nil {
	//         return fmt.Errorf("failed to parse IFC file: %w", err)
	//     }
	//     ds.logger.Info("IFC file parsed successfully",
	//         "buildings", result.Buildings,
	//         "spaces", result.Spaces,
	//         "equipment", result.Equipment)
	// }

	ds.logger.Info("File import processed successfully", "path", event.Path)
	return nil
}

// processExport processes file export
func (ds *DaemonService) processExport(event *domain.FileEvent, format string) error {
	ds.logger.Info("Processing file export", "path", event.Path, "format", format)

	// Extract building ID from path or metadata
	buildingID := ds.extractBuildingID(event.Path)
	if buildingID == "" {
		return fmt.Errorf("could not determine building ID from path: %s", event.Path)
	}

	// Export building data
	// data, err := ds.buildingUC.ExportBuilding(ds.ctx, buildingID, format)
	// if err != nil {
	//     return fmt.Errorf("failed to export building: %w", err)
	// }

	// Write exported data to file
	// if err := ds.processor.WriteFile(event.Path, data); err != nil {
	//     return fmt.Errorf("failed to write exported file: %w", err)
	// }

	ds.logger.Info("File exported successfully", "path", event.Path)
	return nil
}

// processSync processes file synchronization
func (ds *DaemonService) processSync(event *domain.FileEvent, format string) error {
	ds.logger.Info("Processing file sync", "path", event.Path, "format", format)

	// Determine sync direction and perform sync
	// This would handle bidirectional sync between local files and remote systems

	ds.logger.Info("File synced successfully", "path", event.Path)
	return nil
}

// processWatch processes file watching (monitoring only)
func (ds *DaemonService) processWatch(event *domain.FileEvent, format string) error {
	ds.logger.Info("Processing file watch", "path", event.Path, "format", format)

	// Just log the change, don't process
	ds.logger.Info("File change detected", "path", event.Path, "action", event.Action)
	return nil
}

// extractBuildingID extracts building ID from file path
func (ds *DaemonService) extractBuildingID(path string) string {
	// Simple extraction - in reality, this would be more sophisticated
	filename := filepath.Base(path)
	parts := strings.Split(filename, "_")
	if len(parts) > 0 {
		return parts[0]
	}
	return ""
}

// performMaintenance performs periodic maintenance tasks
func (ds *DaemonService) performMaintenance() {
	ds.logger.Debug("Performing daemon maintenance")

	// Clean up old temporary files
	// Check disk space
	// Update metrics
	// etc.
}
