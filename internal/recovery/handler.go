package recovery

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime/debug"
	"time"
	
	"github.com/joelpate/arxos/internal/logger"
)

// Handler provides panic recovery and error handling
type Handler struct {
	logDir     string
	maxRetries int
}

// NewHandler creates a new recovery handler
func NewHandler(logDir string) *Handler {
	return &Handler{
		logDir:     logDir,
		maxRetries: 3,
	}
}

// Recover handles panic recovery and logs the error
func (h *Handler) Recover(context string) {
	if r := recover(); r != nil {
		h.logPanic(context, r)
		logger.Error("PANIC in %s: %v", context, r)
		logger.Error("Stack trace:\n%s", debug.Stack())
	}
}

// RecoverWithCallback handles panic recovery with a callback function
func (h *Handler) RecoverWithCallback(context string, callback func(error)) {
	if r := recover(); r != nil {
		err := h.logPanic(context, r)
		logger.Error("PANIC in %s: %v", context, r)
		
		if callback != nil {
			callback(err)
		}
	}
}

// WithRetry executes a function with automatic retry on failure
func (h *Handler) WithRetry(fn func() error, context string) error {
	var lastErr error
	
	for attempt := 1; attempt <= h.maxRetries; attempt++ {
		// Set up panic recovery for this attempt
		func() {
			defer h.Recover(fmt.Sprintf("%s (attempt %d)", context, attempt))
			lastErr = fn()
		}()
		
		if lastErr == nil {
			return nil
		}
		
		logger.Warn("Attempt %d/%d failed for %s: %v", attempt, h.maxRetries, context, lastErr)
		
		if attempt < h.maxRetries {
			// Exponential backoff
			waitTime := time.Duration(attempt) * time.Second
			logger.Info("Retrying in %v...", waitTime)
			time.Sleep(waitTime)
		}
	}
	
	return fmt.Errorf("all %d attempts failed for %s: %w", h.maxRetries, context, lastErr)
}

// SaveState saves the current state to a backup file
func (h *Handler) SaveState(data interface{}, filename string) error {
	backupPath := filepath.Join(h.logDir, "backups", filename)
	
	// Ensure backup directory exists
	if err := os.MkdirAll(filepath.Dir(backupPath), 0755); err != nil {
		return fmt.Errorf("failed to create backup directory: %w", err)
	}
	
	// Add timestamp to filename
	timestamp := time.Now().Format("20060102_150405")
	ext := filepath.Ext(filename)
	base := filename[:len(filename)-len(ext)]
	backupFile := fmt.Sprintf("%s_%s%s", base, timestamp, ext)
	fullPath := filepath.Join(h.logDir, "backups", backupFile)
	
	// Save state (implementation depends on data type)
	logger.Info("Saving backup state to: %s", fullPath)
	
	// TODO: Implement actual serialization based on data type
	return nil
}

// RestoreState restores state from the most recent backup
func (h *Handler) RestoreState(filename string) (interface{}, error) {
	backupDir := filepath.Join(h.logDir, "backups")
	pattern := filepath.Join(backupDir, fmt.Sprintf("%s_*", filename[:len(filename)-len(filepath.Ext(filename))]))
	
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return nil, fmt.Errorf("failed to find backup files: %w", err)
	}
	
	if len(matches) == 0 {
		return nil, fmt.Errorf("no backup files found for %s", filename)
	}
	
	// Get the most recent backup
	mostRecent := matches[len(matches)-1]
	logger.Info("Restoring from backup: %s", mostRecent)
	
	// TODO: Implement actual deserialization
	return nil, nil
}

// logPanic logs panic information to a file
func (h *Handler) logPanic(context string, r interface{}) error {
	timestamp := time.Now().Format("20060102_150405")
	crashFile := filepath.Join(h.logDir, fmt.Sprintf("crash_%s_%s.log", context, timestamp))
	
	// Ensure log directory exists
	if err := os.MkdirAll(h.logDir, 0755); err != nil {
		return fmt.Errorf("failed to create log directory: %w", err)
	}
	
	// Create crash log
	content := fmt.Sprintf("Panic in: %s\nTime: %s\nError: %v\n\nStack Trace:\n%s\n",
		context, time.Now().Format(time.RFC3339), r, debug.Stack())
	
	if err := os.WriteFile(crashFile, []byte(content), 0644); err != nil {
		return fmt.Errorf("failed to write crash log: %w", err)
	}
	
	return fmt.Errorf("panic in %s: %v", context, r)
}

// SetMaxRetries sets the maximum number of retry attempts
func (h *Handler) SetMaxRetries(max int) {
	h.maxRetries = max
}

// CleanupOldLogs removes log files older than the specified duration
func (h *Handler) CleanupOldLogs(maxAge time.Duration) error {
	now := time.Now()
	
	err := filepath.Walk(h.logDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		if !info.IsDir() && info.ModTime().Before(now.Add(-maxAge)) {
			logger.Debug("Removing old log file: %s", path)
			if err := os.Remove(path); err != nil {
				logger.Warn("Failed to remove old log: %v", err)
			}
		}
		
		return nil
	})
	
	return err
}

// Validate checks if critical components are functioning
func (h *Handler) Validate() error {
	// Check if log directory is writable
	testFile := filepath.Join(h.logDir, ".test")
	if err := os.WriteFile(testFile, []byte("test"), 0644); err != nil {
		return fmt.Errorf("log directory not writable: %w", err)
	}
	os.Remove(testFile)
	
	return nil
}