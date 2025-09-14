package daemon

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"sync"
	"syscall"
	"time"

	"github.com/fsnotify/fsnotify"

	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/importer"
	"github.com/joelpate/arxos/internal/common/state"
	"github.com/joelpate/arxos/pkg/models"
)

// Daemon represents the ArxOS background service
type Daemon struct {
	config   *Config
	db       database.DB
	watcher  *fsnotify.Watcher
	server   *Server
	queue    *WorkQueue
	stopCh   chan struct{}
	wg       sync.WaitGroup
	mu       sync.RWMutex
	
	// Statistics
	stats    Statistics
}

// Config holds daemon configuration
type Config struct {
	// Paths
	WatchDirs    []string      `json:"watch_dirs"`
	StateDir     string        `json:"state_dir"`
	DatabasePath string        `json:"database_path"`
	SocketPath   string        `json:"socket_path"`
	
	// Behavior
	AutoImport   bool          `json:"auto_import"`
	AutoExport   bool          `json:"auto_export"`
	SyncInterval time.Duration `json:"sync_interval"`
	
	// File patterns
	WatchPatterns []string     `json:"watch_patterns"` // e.g., "*.pdf", "*.ifc"
	IgnorePatterns []string    `json:"ignore_patterns"`
	
	// Performance
	MaxWorkers   int           `json:"max_workers"`
	QueueSize    int           `json:"queue_size"`
}

// Statistics tracks daemon metrics
type Statistics struct {
	StartTime        time.Time
	FilesProcessed   int64
	ImportSuccesses  int64
	ImportFailures   int64
	LastProcessedFile string
	LastProcessedTime time.Time
	mu               sync.RWMutex
}

// NewDaemon creates a new daemon instance
func NewDaemon(config *Config) (*Daemon, error) {
	// Set defaults
	if config.MaxWorkers <= 0 {
		config.MaxWorkers = 4
	}
	if config.QueueSize <= 0 {
		config.QueueSize = 100
	}
	if config.SyncInterval <= 0 {
		config.SyncInterval = 5 * time.Minute
	}
	if config.SocketPath == "" {
		config.SocketPath = "/tmp/arxos.sock"
	}
	
	// Create file watcher
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return nil, fmt.Errorf("failed to create watcher: %w", err)
	}
	
	// Initialize database
	dbConfig := database.NewConfig(config.DatabasePath)
	db := database.NewSQLiteDB(dbConfig)
	
	d := &Daemon{
		config:  config,
		db:      db,
		watcher: watcher,
		queue:   NewWorkQueue(config.QueueSize),
		stopCh:  make(chan struct{}),
		stats: Statistics{
			StartTime: time.Now(),
		},
	}
	
	// Create server for IPC
	d.server = NewServer(d, config.SocketPath)
	
	return d, nil
}

// Start begins daemon operation
func (d *Daemon) Start(ctx context.Context) error {
	logger.Info("Starting ArxOS daemon...")
	
	// Connect to database
	if err := d.db.Connect(ctx, d.config.DatabasePath); err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	
	// Add watch directories
	for _, dir := range d.config.WatchDirs {
		if err := d.addWatchDir(dir); err != nil {
			logger.Error("Failed to watch directory %s: %v", dir, err)
		} else {
			logger.Info("Watching directory: %s", dir)
		}
	}
	
	// Start workers
	for i := 0; i < d.config.MaxWorkers; i++ {
		d.wg.Add(1)
		go d.worker(ctx, i)
	}
	
	// Start file watcher
	d.wg.Add(1)
	go d.watchFiles(ctx)
	
	// Start periodic sync
	d.wg.Add(1)
	go d.periodicSync(ctx)
	
	// Start IPC server
	d.wg.Add(1)
	go d.server.Start(ctx, &d.wg)
	
	logger.Info("ArxOS daemon started successfully")
	
	// Wait for shutdown signal
	d.waitForShutdown(ctx)
	
	return nil
}

// Stop gracefully stops the daemon
func (d *Daemon) Stop() {
	logger.Info("Stopping ArxOS daemon...")
	
	// Signal stop
	close(d.stopCh)
	
	// Close watcher
	if d.watcher != nil {
		d.watcher.Close()
	}
	
	// Close queue
	d.queue.Close()
	
	// Stop server
	if d.server != nil {
		d.server.Stop()
	}
	
	// Wait for workers to finish
	d.wg.Wait()
	
	// Close database
	if d.db != nil {
		d.db.Close()
	}
	
	logger.Info("ArxOS daemon stopped")
}

// addWatchDir adds a directory to watch
func (d *Daemon) addWatchDir(dir string) error {
	// Ensure directory exists
	info, err := os.Stat(dir)
	if err != nil {
		return fmt.Errorf("directory not accessible: %w", err)
	}
	if !info.IsDir() {
		return fmt.Errorf("not a directory: %s", dir)
	}
	
	// Add to watcher
	if err := d.watcher.Add(dir); err != nil {
		return fmt.Errorf("failed to watch directory: %w", err)
	}
	
	// Walk subdirectories if needed
	err = filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors
		}
		if info.IsDir() && path != dir {
			// Optionally watch subdirectories
			// d.watcher.Add(path)
		}
		return nil
	})
	
	return nil
}

// watchFiles monitors file system events
func (d *Daemon) watchFiles(ctx context.Context) {
	defer d.wg.Done()
	
	for {
		select {
		case <-ctx.Done():
			return
		case <-d.stopCh:
			return
		case event, ok := <-d.watcher.Events:
			if !ok {
				return
			}
			d.handleFileEvent(ctx, event)
		case err, ok := <-d.watcher.Errors:
			if !ok {
				return
			}
			logger.Error("Watcher error: %v", err)
		}
	}
}

// handleFileEvent processes a file system event
func (d *Daemon) handleFileEvent(ctx context.Context, event fsnotify.Event) {
	// Check if we should process this file
	if !d.shouldProcess(event.Name) {
		return
	}
	
	// Create work item based on event type
	var workType WorkType
	switch {
	case event.Op&fsnotify.Create == fsnotify.Create:
		workType = WorkTypeImport
		logger.Info("New file detected: %s", event.Name)
	case event.Op&fsnotify.Write == fsnotify.Write:
		workType = WorkTypeUpdate
		logger.Info("File modified: %s", event.Name)
	case event.Op&fsnotify.Remove == fsnotify.Remove:
		workType = WorkTypeRemove
		logger.Info("File removed: %s", event.Name)
	default:
		return
	}
	
	// Queue work item
	item := &WorkItem{
		Type:      workType,
		FilePath:  event.Name,
		Timestamp: time.Now(),
	}
	
	if err := d.queue.Add(item); err != nil {
		logger.Error("Failed to queue work item: %v", err)
	}
}

// shouldProcess checks if a file should be processed
func (d *Daemon) shouldProcess(filePath string) bool {
	// Check ignore patterns
	base := filepath.Base(filePath)
	for _, pattern := range d.config.IgnorePatterns {
		if matched, _ := filepath.Match(pattern, base); matched {
			return false
		}
	}
	
	// Check watch patterns
	if len(d.config.WatchPatterns) == 0 {
		// No patterns specified, process all
		return true
	}
	
	for _, pattern := range d.config.WatchPatterns {
		if matched, _ := filepath.Match(pattern, base); matched {
			return true
		}
	}
	
	return false
}

// worker processes work items from the queue
func (d *Daemon) worker(ctx context.Context, id int) {
	defer d.wg.Done()
	logger.Debug("Worker %d started", id)
	
	for {
		select {
		case <-ctx.Done():
			return
		case <-d.stopCh:
			return
		case item := <-d.queue.Items():
			if item == nil {
				return // Queue closed
			}
			d.processWorkItem(ctx, item)
		}
	}
}

// processWorkItem processes a single work item
func (d *Daemon) processWorkItem(ctx context.Context, item *WorkItem) {
	logger.Debug("Processing work item: %s (%s)", item.FilePath, item.Type)
	
	start := time.Now()
	var err error
	
	switch item.Type {
	case WorkTypeImport:
		err = d.importFile(ctx, item.FilePath)
	case WorkTypeUpdate:
		err = d.updateFile(ctx, item.FilePath)
	case WorkTypeRemove:
		err = d.removeFile(ctx, item.FilePath)
	case WorkTypeSync:
		err = d.syncDatabase(ctx)
	}
	
	// Update statistics
	d.updateStats(item, err, time.Since(start))
	
	if err != nil {
		logger.Error("Failed to process %s: %v", item.FilePath, err)
	} else {
		logger.Info("Successfully processed %s in %v", item.FilePath, time.Since(start))
	}
}

// importFile imports a new file
func (d *Daemon) importFile(ctx context.Context, filePath string) error {
	ext := filepath.Ext(filePath)
	
	switch ext {
	case ".pdf":
		return d.importPDF(ctx, filePath)
	case ".ifc":
		// TODO: Implement IFC import
		return fmt.Errorf("IFC import not yet implemented")
	default:
		return fmt.Errorf("unsupported file type: %s", ext)
	}
}

// importPDF imports a PDF file
func (d *Daemon) importPDF(ctx context.Context, filePath string) error {
	// Use existing PDF extraction logic
	extractor := importer.NewSimplePDFExtractor()

	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	extractedData, err := extractor.ExtractText(file)
	if err != nil {
		return fmt.Errorf("failed to extract floor plan: %w", err)
	}
	
	// Convert to floor plan
	equipment := make([]*models.Equipment, 0, len(extractedData.Equipment))
	for _, e := range extractedData.Equipment {
		equipment = append(equipment, &models.Equipment{
			ID:     e.ID,
			Name:   e.ID,
			Type:   e.Type,
			Status: models.StatusOperational,
		})
	}

	rooms := make([]*models.Room, 0, len(extractedData.Rooms))
	for _, r := range extractedData.Rooms {
		rooms = append(rooms, &models.Room{
			ID:   r.ID,
			Name: r.Name,
		})
	}

	plan := &models.FloorPlan{
		ID:        filepath.Base(filePath),
		Name:      filepath.Base(filePath),
		Building:  filepath.Base(filePath),
		Equipment: equipment,
		Rooms:     rooms,
	}

	// Save to database
	if err := d.db.SaveFloorPlan(ctx, plan); err != nil {
		// Try update if save fails
		if err := d.db.UpdateFloorPlan(ctx, plan); err != nil {
			return fmt.Errorf("failed to save floor plan: %w", err)
		}
	}
	
	// Also save to JSON for backward compatibility
	if d.config.StateDir != "" {
		stateManager, err := state.NewManager(d.config.StateDir)
		if err == nil {
			baseName := filepath.Base(filePath)
			stateFile := baseName[:len(baseName)-len(filepath.Ext(baseName))] + ".json"
			stateManager.LoadFloorPlan(stateFile)
			stateManager.SetFloorPlan(plan)
			stateManager.SaveFloorPlan()
		}
	}
	
	return nil
}

// updateFile handles file updates
func (d *Daemon) updateFile(ctx context.Context, filePath string) error {
	// Re-import the file
	return d.importFile(ctx, filePath)
}

// removeFile handles file removal
func (d *Daemon) removeFile(ctx context.Context, filePath string) error {
	// Extract floor plan ID from filename
	baseName := filepath.Base(filePath)
	planID := baseName[:len(baseName)-len(filepath.Ext(baseName))]
	
	// Mark as deleted in database (don't actually delete, for safety)
	logger.Info("File removed: %s (floor plan: %s)", filePath, planID)
	
	// Could implement soft delete or archiving here
	return nil
}

// syncDatabase performs periodic database sync
func (d *Daemon) syncDatabase(ctx context.Context) error {
	if d.config.StateDir == "" {
		return nil
	}
	
	migrator := database.NewJSONMigrator(d.db, d.config.StateDir)
	return migrator.SyncJSONToDatabase(ctx)
}

// periodicSync runs periodic synchronization
func (d *Daemon) periodicSync(ctx context.Context) {
	defer d.wg.Done()
	
	ticker := time.NewTicker(d.config.SyncInterval)
	defer ticker.Stop()
	
	for {
		select {
		case <-ctx.Done():
			return
		case <-d.stopCh:
			return
		case <-ticker.C:
			logger.Debug("Running periodic sync")
			if err := d.syncDatabase(ctx); err != nil {
				logger.Error("Periodic sync failed: %v", err)
			}
		}
	}
}

// updateStats updates daemon statistics
func (d *Daemon) updateStats(item *WorkItem, err error, duration time.Duration) {
	d.stats.mu.Lock()
	defer d.stats.mu.Unlock()
	
	d.stats.FilesProcessed++
	if err == nil {
		d.stats.ImportSuccesses++
	} else {
		d.stats.ImportFailures++
	}
	
	d.stats.LastProcessedFile = item.FilePath
	d.stats.LastProcessedTime = time.Now()
}

// GetStats returns current daemon statistics
func (d *Daemon) GetStats() Statistics {
	d.stats.mu.RLock()
	defer d.stats.mu.RUnlock()
	
	return d.stats
}

// waitForShutdown waits for shutdown signal
func (d *Daemon) waitForShutdown(ctx context.Context) {
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	
	select {
	case <-ctx.Done():
		logger.Info("Context cancelled, shutting down")
	case sig := <-sigCh:
		logger.Info("Received signal %v, shutting down", sig)
	}
	
	d.Stop()
}

// GetStatus returns daemon status information
func (d *Daemon) GetStatus() map[string]interface{} {
	stats := d.GetStats()
	
	return map[string]interface{}{
		"running":           true,
		"uptime":            time.Since(stats.StartTime).String(),
		"files_processed":   stats.FilesProcessed,
		"import_successes":  stats.ImportSuccesses,
		"import_failures":   stats.ImportFailures,
		"last_processed":    stats.LastProcessedFile,
		"last_processed_at": stats.LastProcessedTime.Format(time.RFC3339),
		"watch_dirs":        d.config.WatchDirs,
		"auto_import":       d.config.AutoImport,
		"workers":           d.config.MaxWorkers,
		"queue_size":        d.queue.Size(),
	}
}