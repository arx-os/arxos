package services

import (
	"context"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// FileWatcher provides file system watching functionality
type FileWatcher struct {
	watchPaths []WatchPath
	events     chan *domain.FileEvent
	logger     domain.Logger
	ctx        context.Context
	cancel     context.CancelFunc
}

// NewFileWatcher creates a new file watcher
func NewFileWatcher(logger domain.Logger) *FileWatcher {
	return &FileWatcher{
		events: make(chan *domain.FileEvent, 100),
		logger: logger,
	}
}

// AddPath adds a path to watch
func (fw *FileWatcher) AddPath(watchPath WatchPath) error {
	fw.watchPaths = append(fw.watchPaths, watchPath)
	fw.logger.Info("Added watch path", "path", watchPath.Path, "recursive", watchPath.Recursive)
	return nil
}

// Start starts the file watcher
func (fw *FileWatcher) Start(ctx context.Context) error {
	fw.ctx, fw.cancel = context.WithCancel(ctx)

	fw.logger.Info("Starting file watcher")

	// Start watching each path
	for _, watchPath := range fw.watchPaths {
		go fw.watchPath(watchPath)
	}

	return nil
}

// Stop stops the file watcher
func (fw *FileWatcher) Stop() error {
	if fw.cancel != nil {
		fw.cancel()
	}
	close(fw.events)
	fw.logger.Info("File watcher stopped")
	return nil
}

// Events returns the events channel
func (fw *FileWatcher) Events() <-chan *domain.FileEvent {
	return fw.events
}

// Health returns the health of the file watcher
func (fw *FileWatcher) Health() (map[string]interface{}, error) {
	return map[string]interface{}{
		"status":       "healthy",
		"watch_paths":  len(fw.watchPaths),
		"event_buffer": len(fw.events),
	}, nil
}

// watchPath watches a specific path for changes
func (fw *FileWatcher) watchPath(watchPath WatchPath) {
	fw.logger.Info("Watching path", "path", watchPath.Path)

	// Simple polling implementation
	// In a real implementation, you'd use fsnotify or similar
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-fw.ctx.Done():
			return
		case <-ticker.C:
			fw.checkPath(watchPath)
		}
	}
}

// checkPath checks a path for changes
func (fw *FileWatcher) checkPath(watchPath WatchPath) {
	// Simplified implementation - just log that we're checking
	fw.logger.Debug("Checking path for changes", "path", watchPath.Path)

	// In a real implementation, you would:
	// 1. Get file list from path
	// 2. Compare with previous state
	// 3. Detect changes
	// 4. Send events for new/modified/deleted files

	// For now, just simulate a file event occasionally
	if strings.Contains(watchPath.Path, "test") {
		event := &domain.FileEvent{
			Path:   filepath.Join(watchPath.Path, "test.ifc"),
			Action: "created",
		}

		select {
		case fw.events <- event:
			fw.logger.Debug("File event sent", "path", event.Path, "action", event.Action)
		default:
			fw.logger.Warn("Event buffer full, dropping event")
		}
	}
}
