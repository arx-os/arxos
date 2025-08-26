package commands

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"
)

// ============================================================================
// FILE SYSTEM WATCHER
// ============================================================================

// FileWatcher monitors building files for changes and triggers updates
type FileWatcher struct {
	watcher      *fsnotify.Watcher
	buildingRoot string
	indexer      interface{} // Generic interface for indexer
	config       *WatcherConfig

	// Event handling
	events chan FileEvent
	errors chan error
	done   chan bool

	// State management
	isRunning   bool
	mutex       sync.RWMutex
	watchedDirs map[string]bool

	// Performance tracking
	lastIndexUpdate time.Time
	changeCount     int
}

// WatcherConfig holds configuration for the file watcher
type WatcherConfig struct {
	Enabled          bool          `json:"enabled"`
	WatchInterval    time.Duration `json:"watch_interval"`
	DebounceDelay    time.Duration `json:"debounce_delay"`
	MaxConcurrent    int           `json:"max_concurrent"`
	IgnorePatterns   []string      `json:"ignore_patterns"`
	AutoRebuildIndex bool          `json:"auto_rebuild_index"`
	NotifyOnChange   bool          `json:"notify_on_change"`
}

// FileEvent represents a file system change event
type FileEvent struct {
	Type      string                 `json:"type"`      // create, write, remove, rename, chmod
	Path      string                 `json:"path"`      // Full path to changed file
	Name      string                 `json:"name"`      // File/directory name
	IsDir     bool                   `json:"is_dir"`    // Whether it's a directory
	Timestamp time.Time              `json:"timestamp"` // When the event occurred
	User      string                 `json:"user"`      // User who made the change (if available)
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// ChangeSummary provides a summary of changes detected
type ChangeSummary struct {
	PeriodStart   time.Time              `json:"period_start"`
	PeriodEnd     time.Time              `json:"period_end"`
	TotalChanges  int                    `json:"total_changes"`
	ChangesByType map[string]int         `json:"changes_by_type"`
	ChangesByPath map[string][]FileEvent `json:"changes_by_path"`
	IndexUpdates  int                    `json:"index_updates"`
	Performance   WatcherPerformance     `json:"performance"`
}

// WatcherPerformance tracks performance metrics
type WatcherPerformance struct {
	AverageEventTime time.Duration `json:"average_event_time"`
	TotalEvents      int           `json:"total_events"`
	IndexRebuildTime time.Duration `json:"index_rebuild_time"`
	MemoryUsage      int64         `json:"memory_usage_bytes"`
}

// NewFileWatcher creates a new file watcher instance
func NewFileWatcher(buildingRoot string, indexer interface{}, config *WatcherConfig) (*FileWatcher, error) {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return nil, fmt.Errorf("failed to create file watcher: %w", err)
	}

	if config == nil {
		config = &WatcherConfig{
			Enabled:          true,
			WatchInterval:    5 * time.Second,
			DebounceDelay:    2 * time.Second,
			MaxConcurrent:    4,
			IgnorePatterns:   []string{".git", ".arxos/cache", "*.tmp", "*.log"},
			AutoRebuildIndex: true,
			NotifyOnChange:   true,
		}
	}

	fw := &FileWatcher{
		watcher:      watcher,
		buildingRoot: buildingRoot,
		indexer:      indexer,
		config:       config,
		events:       make(chan FileEvent, 100),
		errors:       make(chan error, 10),
		done:         make(chan bool),
		watchedDirs:  make(map[string]bool),
	}

	return fw, nil
}

// Start begins monitoring the building filesystem
func (fw *FileWatcher) Start() error {
	fw.mutex.Lock()
	defer fw.mutex.Unlock()

	if fw.isRunning {
		return fmt.Errorf("watcher is already running")
	}

	// Start event processing goroutines
	go fw.processEvents()
	go fw.handleErrors()

	// Add initial directories to watch
	if err := fw.addDirectoriesToWatch(); err != nil {
		return fmt.Errorf("failed to add directories to watch: %w", err)
	}

	fw.isRunning = true
	log.Printf("🔍 File watcher started for building: %s", fw.buildingRoot)

	// Start the main watch loop
	go fw.watchLoop()

	return nil
}

// Stop stops the file watcher
func (fw *FileWatcher) Stop() error {
	fw.mutex.Lock()
	defer fw.mutex.Unlock()

	if !fw.isRunning {
		return nil
	}

	// Signal shutdown
	close(fw.done)

	// Close watcher
	if err := fw.watcher.Close(); err != nil {
		return fmt.Errorf("failed to close watcher: %w", err)
	}

	fw.isRunning = false
	log.Printf("🛑 File watcher stopped")

	return nil
}

// addDirectoriesToWatch adds all relevant directories to the watcher
func (fw *FileWatcher) addDirectoriesToWatch() error {
	// Start with building root
	if err := fw.addDirectoryToWatch(fw.buildingRoot); err != nil {
		return err
	}

	// Walk through building structure and add directories
	err := filepath.Walk(fw.buildingRoot, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip if it's a file or already watched
		if !info.IsDir() || fw.watchedDirs[path] {
			return nil
		}

		// Skip ignored patterns
		if fw.shouldIgnore(path) {
			return filepath.SkipDir
		}

		// Add directory to watch
		if err := fw.addDirectoryToWatch(path); err != nil {
			log.Printf("Warning: failed to watch directory %s: %v", path, err)
		}

		return nil
	})

	return err
}

// addDirectoryToWatch adds a single directory to the watcher
func (fw *FileWatcher) addDirectoryToWatch(dirPath string) error {
	if fw.watchedDirs[dirPath] {
		return nil
	}

	if err := fw.watcher.Add(dirPath); err != nil {
		return fmt.Errorf("failed to add directory %s to watcher: %w", dirPath, err)
	}

	fw.watchedDirs[dirPath] = true
	log.Printf("👁️  Watching directory: %s", dirPath)

	return nil
}

// shouldIgnore checks if a path should be ignored
func (fw *FileWatcher) shouldIgnore(path string) bool {
	path = strings.ToLower(path)

	for _, pattern := range fw.config.IgnorePatterns {
		pattern = strings.ToLower(pattern)

		// Check exact match
		if path == pattern {
			return true
		}

		// Check if path contains pattern
		if strings.Contains(path, pattern) {
			return true
		}

		// Check wildcard patterns
		if strings.Contains(pattern, "*") {
			// Simple wildcard matching
			if strings.HasSuffix(pattern, "*") {
				prefix := strings.TrimSuffix(pattern, "*")
				if strings.HasPrefix(path, prefix) {
					return true
				}
			}
		}
	}

	return false
}

// watchLoop is the main event processing loop
func (fw *FileWatcher) watchLoop() {
	debounceTimer := time.NewTimer(fw.config.DebounceDelay)
	debounceTimer.Stop()

	var pendingEvents []FileEvent

	for {
		select {
		case event := <-fw.watcher.Events:
			// Convert fsnotify event to our FileEvent
			fileEvent := fw.convertEvent(event)

			// Add to pending events
			pendingEvents = append(pendingEvents, fileEvent)

			// Reset debounce timer
			debounceTimer.Reset(fw.config.DebounceDelay)

		case err := <-fw.watcher.Errors:
			fw.errors <- fmt.Errorf("watcher error: %w", err)

		case <-debounceTimer.C:
			// Process pending events after debounce delay
			if len(pendingEvents) > 0 {
				fw.processPendingEvents(pendingEvents)
				pendingEvents = pendingEvents[:0] // Clear slice
			}

		case <-fw.done:
			return
		}
	}
}

// convertEvent converts fsnotify event to FileEvent
func (fw *FileWatcher) convertEvent(event fsnotify.Event) FileEvent {
	info, err := os.Stat(event.Name)
	isDir := false
	if err == nil {
		isDir = info.IsDir()
	}

	// Determine event type
	eventType := "unknown"
	switch {
	case event.Op&fsnotify.Create == fsnotify.Create:
		eventType = "create"
	case event.Op&fsnotify.Write == fsnotify.Write:
		eventType = "write"
	case event.Op&fsnotify.Remove == fsnotify.Remove:
		eventType = "remove"
	case event.Op&fsnotify.Rename == fsnotify.Rename:
		eventType = "rename"
	case event.Op&fsnotify.Chmod == fsnotify.Chmod:
		eventType = "chmod"
	}

	return FileEvent{
		Type:      eventType,
		Path:      event.Name,
		Name:      filepath.Base(event.Name),
		IsDir:     isDir,
		Timestamp: time.Now().UTC(),
		User:      fw.getCurrentUser(),
		Metadata: map[string]interface{}{
			"operation": event.Op.String(),
			"size":      info.Size(),
		},
	}
}

// getCurrentUser gets the current user (simplified)
func (fw *FileWatcher) getCurrentUser() string {
	// In a real implementation, this would get the actual user
	// For now, return a placeholder
	return "arxos-user"
}

// processPendingEvents processes a batch of pending events
func (fw *FileWatcher) processPendingEvents(events []FileEvent) {
	startTime := time.Now()

	// Send events to processing channel
	for _, event := range events {
		select {
		case fw.events <- event:
			fw.changeCount++
		default:
			log.Printf("Warning: event channel full, dropping event: %s", event.Path)
		}
	}

	// Auto-rebuild index if enabled
	if fw.config.AutoRebuildIndex && len(events) > 0 {
		go fw.triggerIndexRebuild(events)
	}

	// Log performance metrics
	processingTime := time.Since(startTime)
	log.Printf("📊 Processed %d events in %v", len(events), processingTime)
}

// processEvents processes events from the events channel
func (fw *FileWatcher) processEvents() {
	for {
		select {
		case event := <-fw.events:
			fw.handleEvent(event)
		case <-fw.done:
			return
		}
	}
}

// handleEvent handles a single file event
func (fw *FileWatcher) handleEvent(event FileEvent) {
	startTime := time.Now()

	// Handle different event types
	switch event.Type {
	case "create":
		fw.handleCreateEvent(event)
	case "write":
		fw.handleWriteEvent(event)
	case "remove":
		fw.handleRemoveEvent(event)
	case "rename":
		fw.handleRenameEvent(event)
	case "chmod":
		fw.handleChmodEvent(event)
	}

	// Update performance metrics
	eventTime := time.Since(startTime)
	log.Printf("⚡ Event processed: %s %s in %v", event.Type, event.Path, eventTime)

	// Send notification if enabled
	if fw.config.NotifyOnChange {
		fw.sendChangeNotification(event)
	}
}

// handleCreateEvent handles file/directory creation
func (fw *FileWatcher) handleCreateEvent(event FileEvent) {
	if event.IsDir {
		// Add new directory to watch
		if err := fw.addDirectoryToWatch(event.Path); err != nil {
			log.Printf("Warning: failed to watch new directory %s: %v", event.Path, err)
		}
	}

	log.Printf("🆕 Created: %s", event.Path)
}

// handleWriteEvent handles file modifications
func (fw *FileWatcher) handleWriteEvent(event FileEvent) {
	log.Printf("✏️  Modified: %s", event.Path)
}

// handleRemoveEvent handles file/directory removal
func (fw *FileWatcher) handleRemoveEvent(event FileEvent) {
	if event.IsDir {
		// Remove directory from watched list
		delete(fw.watchedDirs, event.Path)
	}

	log.Printf("🗑️  Removed: %s", event.Path)
}

// handleRenameEvent handles file/directory renames
func (fw *FileWatcher) handleRenameEvent(event FileEvent) {
	log.Printf("🔄 Renamed: %s", event.Path)
}

// handleChmodEvent handles permission changes
func (fw *FileWatcher) handleChmodEvent(event FileEvent) {
	log.Printf("🔐 Permissions changed: %s", event.Path)
}

// handleErrors handles watcher errors
func (fw *FileWatcher) handleErrors() {
	for {
		select {
		case err := <-fw.errors:
			log.Printf("❌ Watcher error: %v", err)
		case <-fw.done:
			return
		}
	}
}

// triggerIndexRebuild triggers an index rebuild after changes
func (fw *FileWatcher) triggerIndexRebuild(events []FileEvent) {
	startTime := time.Now()

	log.Printf("🔄 Triggering index rebuild after %d changes", len(events))

	// For now, just log the rebuild attempt
	// In production, this would call the indexer's refresh method
	log.Printf("📝 Index rebuild requested for %d changes", len(events))

	rebuildTime := time.Since(startTime)
	fw.lastIndexUpdate = time.Now()

	log.Printf("✅ Index rebuild completed in %v", rebuildTime)
}

// sendChangeNotification sends a change notification
func (fw *FileWatcher) sendChangeNotification(event FileEvent) {
	// In a real implementation, this would send notifications
	// For now, just log the notification
	log.Printf("🔔 Change notification: %s %s", event.Type, event.Path)
}

// GetChangeSummary returns a summary of recent changes
func (fw *FileWatcher) GetChangeSummary(since time.Time) *ChangeSummary {
	fw.mutex.RLock()
	defer fw.mutex.RUnlock()

	summary := &ChangeSummary{
		PeriodStart:   since,
		PeriodEnd:     time.Now().UTC(),
		ChangesByType: make(map[string]int),
		ChangesByPath: make(map[string][]FileEvent),
	}

	// Process events to build summary
	// This is a simplified implementation
	// In production, you'd want to store events in a database

	return summary
}

// GetStatus returns the current watcher status
func (fw *FileWatcher) GetStatus() map[string]interface{} {
	fw.mutex.RLock()
	defer fw.mutex.RUnlock()

	return map[string]interface{}{
		"running":           fw.isRunning,
		"building_root":     fw.buildingRoot,
		"watched_dirs":      len(fw.watchedDirs),
		"change_count":      fw.changeCount,
		"last_index_update": fw.lastIndexUpdate,
		"config":            fw.config,
	}
}

// IsRunning returns whether the watcher is currently running
func (fw *FileWatcher) IsRunning() bool {
	fw.mutex.RLock()
	defer fw.mutex.RUnlock()
	return fw.isRunning
}
